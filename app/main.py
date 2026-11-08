"""LeadPilot backend: the leads API, the smart-reply endpoint, the agent chat, health and digest.

One service does everything (architecture.md, "Where things run"). The agent
loop itself lives in agent.py; this file is doors, locks and plumbing.
"""
from __future__ import annotations

import json
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, Header, HTTPException, Request, Response
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from . import auth, limits
from .agent import get_model_client, run_turn
from .config import ROOT, settings
from . import smart_reply
from .db import Conversation, Lead, LeadEvent, Message, SessionLocal, engine, get_db, init_db, utcnow
from .leads_meta import STATUS_BY_ID, compute_metrics, meta, normalize_phone
from .digest import build_digest, send_digest
from .tools import leads as lead_tools


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.init_report = init_db()
    # One line in the deploy log, so a first deploy can be checked (docs/deploy-railway.md, step 7).
    print("seed report: " + ", ".join(f"{k}: {v}" for k, v in app.state.init_report.items()), flush=True)
    app.state.model_client = get_model_client()
    yield


app = FastAPI(title="LeadPilot", version="0.1.0", lifespan=lifespan, docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory=str(ROOT / "static")), name="static")


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class LoginIn(BaseModel):
    name: str = Field(min_length=2, max_length=40)
    password: str = Field(min_length=1, max_length=200)


class ImageIn(BaseModel):
    media_type: str = Field(pattern=r"^image/(png|jpeg|webp|gif)$")
    data: str  # base64, no data: prefix


class LeadIn(BaseModel):
    phone: str = Field(min_length=7, max_length=40)
    name: str = Field(default="", max_length=80)
    source: str = Field(default="", max_length=30)
    status: str | None = "sent_intro"
    notes: str = Field(default="", max_length=4000)


class LeadPatch(BaseModel):
    name: str | None = Field(default=None, max_length=80)
    phone: str | None = Field(default=None, max_length=40)
    source: str | None = Field(default=None, max_length=30)
    status: str | None = None
    clear_status: bool = False
    first_attempt: str | None = Field(default=None, max_length=4000)
    second_attempt: str | None = Field(default=None, max_length=4000)
    last_update: str | None = Field(default=None, max_length=4000)
    notes: str | None = Field(default=None, max_length=4000)


class IncomingIn(BaseModel):
    text: str = Field(min_length=1, max_length=4000)


class SmartReplyIn(BaseModel):
    incoming: str | None = Field(default=None, max_length=4000)
    tone: str = Field(default="friendly", pattern=r"^(friendly|short|formal)$")


class SentIn(BaseModel):
    reply: str = Field(min_length=1, max_length=4000)
    status: str | None = None


class ChatIn(BaseModel):
    conversation_id: int | None = None
    message: str = Field(default="", max_length=4000)
    image: ImageIn | None = None


# ---------------------------------------------------------------------------
# Pages and health
# ---------------------------------------------------------------------------

@app.get("/", include_in_schema=False)
def index():
    return FileResponse(ROOT / "static" / "index.html")


@app.get("/health")
def health(db: Session = Depends(get_db)):
    """Railway's health check. 200 only when the database answers and a model is configured."""
    problems = []
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:  # pragma: no cover - exercised on a broken deploy, not in tests
        problems.append(f"db: {type(exc).__name__}")
    body = {"status": "ok" if not problems else "degraded", "env": settings.environment, "model": settings.model,
            "provider": settings.model_provider, "db": "sqlite" if settings.is_sqlite else "postgres", "problems": problems,
            "time": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    if problems:
        raise HTTPException(503, body)
    return body


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

@app.post("/api/login")
def login(payload: LoginIn, response: Response, db: Session = Depends(get_db)):
    if not auth.password_ok(payload.password):
        raise HTTPException(401, "סיסמה שגויה.")
    user = auth.get_or_create_user(db, auth.normalise_name(payload.name))
    response.set_cookie(auth.COOKIE_NAME, auth.make_token(user.id, user.name), httponly=True, samesite="lax",
                        secure=settings.is_production, max_age=settings.session_hours * 3600, path="/")
    return {"id": user.id, "name": user.name}


@app.post("/api/logout", status_code=204)
def logout(response: Response):
    response.delete_cookie(auth.COOKIE_NAME, path="/")
    return Response(status_code=204)


@app.get("/api/me")
def me(request: Request, db: Session = Depends(get_db)):
    user = auth.current_user(request, db)
    return {"id": user.id, "name": user.name}


# ---------------------------------------------------------------------------
# Conversations and messages
# ---------------------------------------------------------------------------

@app.get("/api/conversations")
def list_conversations(request: Request, db: Session = Depends(get_db)):
    user = auth.current_user(request, db)
    rows = db.scalars(select(Conversation).where(Conversation.user_id == user.id)
                      .order_by(Conversation.updated_at.desc()).limit(100)).all()
    return [{"id": c.id, "title": c.title, "updated_at": c.updated_at.isoformat(timespec="seconds")} for c in rows]


@app.get("/api/conversations/{conversation_id}/messages")
def list_messages(conversation_id: int, request: Request, db: Session = Depends(get_db)):
    user = auth.current_user(request, db)
    conv = db.get(Conversation, conversation_id)
    if conv is None or conv.user_id != user.id:
        raise HTTPException(404, "השיחה לא נמצאה.")
    rows = db.scalars(select(Message).where(Message.conversation_id == conv.id).order_by(Message.id)).all()
    return [{"id": m.id, "role": m.role, "content": m.content, "has_image": m.has_image,
             "created_at": m.created_at.isoformat(timespec="seconds")} for m in rows]


@app.post("/api/chat")
def chat(payload: ChatIn, request: Request, db: Session = Depends(get_db)):
    """One turn. Checks the three limits, then streams the agent's events as SSE."""
    user = auth.current_user(request, db)
    if not payload.message.strip() and payload.image is None:
        raise HTTPException(400, "כתבו הודעה או צרפו צילום מסך.")
    limits.check_rate_limit(db, user.id)
    limits.check_daily_cap(db)
    limits.check_upload_size(payload.image.data if payload.image else None)

    conv = None
    if payload.conversation_id is not None:
        conv = db.get(Conversation, payload.conversation_id)
        if conv is None or conv.user_id != user.id:
            raise HTTPException(404, "השיחה לא נמצאה.")
    conv_id = conv.id if conv else None
    user_id = user.id
    image = payload.image.model_dump() if payload.image else None
    client = request.app.state.model_client

    def sse():
        # A dedicated session: the request-scoped one may close before the stream ends.
        with SessionLocal() as sdb:
            suser = sdb.get(type(user), user_id)
            sconv = sdb.get(Conversation, conv_id) if conv_id else None
            for event in run_turn(sdb, user=suser, conversation=sconv, text=payload.message, image=image, client=client):
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

    headers = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no", "Connection": "keep-alive"}
    return StreamingResponse(sse(), media_type="text/event-stream", headers=headers)


# ---------------------------------------------------------------------------
# Leads
# ---------------------------------------------------------------------------

def _lead_or_404(db: Session, lead_id: int) -> Lead:
    lead = db.get(Lead, lead_id)
    if lead is None:
        raise HTTPException(404, "הליד לא נמצא.")
    return lead


@app.get("/api/meta")
def get_meta(request: Request, db: Session = Depends(get_db)):
    auth.current_user(request, db)
    return {**meta(), "business": settings.business_name, "ai": request.app.state.model_client.name,
            "model": settings.model if request.app.state.model_client.name == "anthropic" else None}


@app.get("/api/leads")
def get_leads(request: Request, db: Session = Depends(get_db)):
    auth.current_user(request, db)
    return {"leads": lead_tools.leads_payload(db), "synced_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}


@app.get("/api/overview")
def overview(request: Request, db: Session = Depends(get_db)):
    auth.current_user(request, db)
    return compute_metrics(lead_tools.all_leads(db), utcnow())


@app.get("/api/leads/{lead_id}")
def get_one_lead(lead_id: int, request: Request, db: Session = Depends(get_db)):
    auth.current_user(request, db)
    data = lead_tools.get_lead(db, lead_id=lead_id)
    if "error" in data:
        raise HTTPException(404, "הליד לא נמצא.")
    return data


@app.post("/api/leads", status_code=201)
def new_lead(payload: LeadIn, request: Request, db: Session = Depends(get_db)):
    user = auth.current_user(request, db)
    res = lead_tools.create_lead(db, user_id=user.id, **payload.model_dump())
    if "error" in res:
        raise HTTPException(400, "מספר הטלפון לא תקין." if "phone" in res["error"] else res["error"])
    if not res["created"]:
        raise HTTPException(409, f"המספר כבר קיים במערכת (ליד #{res['id']} {res['name']}).".replace("  ", " "))
    return lead_tools.get_lead(db, lead_id=res["id"])


@app.patch("/api/leads/{lead_id}")
def patch_lead(lead_id: int, payload: LeadPatch, request: Request, db: Session = Depends(get_db)):
    """Only the fields sent are changed; each change is written to the activity log."""
    user = auth.current_user(request, db)
    lead = _lead_or_404(db, lead_id)
    data = payload.model_dump(exclude_unset=True)
    if data.get("status") is not None and data["status"] not in STATUS_BY_ID:
        raise HTTPException(400, "סטטוס לא מוכר.")
    changes = []
    if data.pop("clear_status", False):
        data["status"] = None
        changes.append("status")
    for field in ("status",):
        if field in data and data[field] != lead.status:
            old = STATUS_BY_ID[lead.status].label if lead.status in STATUS_BY_ID else "ללא סטטוס"
            new = STATUS_BY_ID[data[field]].label if data[field] in STATUS_BY_ID else "ללא סטטוס"
            lead.status = data[field]
            db.add(LeadEvent(lead_id=lead.id, user_id=user.id, actor=user.name, kind="status", text=f"{old} ← {new}"))
    edited = []
    for field in ("name", "phone", "source", "first_attempt", "second_attempt", "last_update", "notes"):
        if field in data and data[field] is not None and data[field] != getattr(lead, field):
            setattr(lead, field, data[field].strip())
            edited.append(field)
    if "phone" in edited:
        lead.phone_norm = normalize_phone(lead.phone)
    if edited:
        names = {"name": "שם", "phone": "נייד", "source": "מקור", "first_attempt": "ניסיון ראשון", "second_attempt": "ניסיון שני",
                 "last_update": "עדכון אחרון", "notes": "הערות / תשלום"}
        db.add(LeadEvent(lead_id=lead.id, user_id=user.id, actor=user.name, kind="edit", text="עודכנו: " + ", ".join(names[f] for f in edited)))
    lead.updated_at = utcnow()
    db.commit()
    return lead_tools.get_lead(db, lead_id=lead.id)


@app.post("/api/leads/{lead_id}/incoming")
def lead_incoming(lead_id: int, payload: IncomingIn, request: Request, db: Session = Depends(get_db)):
    """Record a message the lead sent (pasted from WhatsApp), so it shows in the reply inbox."""
    user = auth.current_user(request, db)
    lead = _lead_or_404(db, lead_id)
    lead_tools.record_incoming(db, lead, payload.text, user.id)
    return lead_tools.get_lead(db, lead_id=lead.id)


@app.post("/api/leads/{lead_id}/smart-reply")
def lead_smart_reply(lead_id: int, payload: SmartReplyIn, request: Request, db: Session = Depends(get_db)):
    """Draft a WhatsApp reply to the lead's latest (or given) message. Counts toward the limits."""
    user = auth.current_user(request, db)
    lead = _lead_or_404(db, lead_id)
    client = request.app.state.model_client
    if client.name != "offline":
        limits.check_daily_cap(db)
    incoming = (payload.incoming if payload.incoming is not None else lead.last_incoming) or ""
    if payload.incoming and payload.incoming.strip() != (lead.last_incoming or "").strip():
        lead_tools.record_incoming(db, lead, payload.incoming, user.id)
    return smart_reply.generate(db, lead, incoming, client=client, user_id=user.id, tone=payload.tone)


@app.post("/api/leads/{lead_id}/sent")
def lead_sent(lead_id: int, payload: SentIn, request: Request, db: Session = Depends(get_db)):
    """The rep sent the reply from WhatsApp: mark the message answered and optionally apply the status."""
    user = auth.current_user(request, db)
    lead = _lead_or_404(db, lead_id)
    if payload.status is not None and payload.status not in STATUS_BY_ID:
        raise HTTPException(400, "סטטוס לא מוכר.")
    lead_tools.mark_replied(db, lead, payload.reply, user.id)
    if payload.status and payload.status != lead.status:
        lead_tools.update_lead(db, lead_id=lead.id, status=payload.status, user_id=user.id)
    return lead_tools.get_lead(db, lead_id=lead.id)


@app.get("/api/templates")
def templates(request: Request, db: Session = Depends(get_db)):
    auth.current_user(request, db)
    return lead_tools.list_templates(db)["templates"]


@app.get("/api/stats")
def stats(request: Request, db: Session = Depends(get_db)):
    user = auth.current_user(request, db)
    return {"spend_today_usd": round(limits.spend_today_usd(db), 4), "daily_cap_usd": settings.daily_cap_usd,
            "messages_last_hour": limits.messages_last_hour(db, user.id), "rate_limit_per_hour": settings.rate_limit_per_hour}


@app.post("/internal/digest")
def digest(db: Session = Depends(get_db), x_cron_secret: str | None = Header(default=None)):
    """Manual or cron trigger for the morning digest. Protected by CRON_SECRET."""
    if not settings.cron_secret or x_cron_secret != settings.cron_secret:
        raise HTTPException(401, "Bad or missing X-Cron-Secret.")
    body = build_digest(db)
    sent = send_digest(body)
    return {"text": body, "sent": sent}
