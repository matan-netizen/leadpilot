"""Lead tools: the only door the agent (and the API) has to the leads table.

Structured inputs, no SQL from the model. Writes are narrow: change a status,
append a note, record a follow-up, create a lead (deduplicated by phone).
Nothing here deletes.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import Lead, LeadEvent, Template, User, utcnow
from ..leads_meta import (STAGE_BY_ID, STATUS_BY_ID, compute_metrics, format_phone, is_hot, is_paid, is_stale,
                          lead_text, needs_reply, normalize_phone, stage_of)


def _actor(db: Session, user_id: int | None) -> str:
    if user_id is None:
        return "מערכת"
    user = db.get(User, user_id)
    return user.name if user else "מערכת"


def recommended_template(db: Session, status: str | None) -> Template | None:
    sdef = STATUS_BY_ID.get(status or "sent_intro")
    if not sdef or not sdef.template_type:
        return None
    return db.scalar(select(Template).where(Template.lead_type == sdef.template_type))


def lead_dict(lead: Lead, now: datetime | None = None, *, duplicate: bool = False) -> dict:
    now = now or utcnow()
    sdef = STATUS_BY_ID.get(lead.status or "")
    return {
        "id": lead.id, "name": lead.name, "phone": lead.phone, "phone_norm": lead.phone_norm,
        "phone_display": format_phone(lead.phone_norm), "source": lead.source,
        "status": lead.status if sdef else None, "status_label": sdef.label if sdef else "ללא סטטוס",
        "stage": stage_of(lead.status), "stage_label": STAGE_BY_ID[stage_of(lead.status)].label,
        "next_action": sdef.next_action if sdef else "לקבוע סטטוס לליד",
        "first_attempt": lead.first_attempt, "second_attempt": lead.second_attempt, "last_update": lead.last_update,
        "notes": lead.notes, "last_incoming": lead.last_incoming, "needs_reply": needs_reply(lead),
        "hot": is_hot(lead), "stale": is_stale(lead, now), "paid": is_paid(lead), "duplicate": duplicate,
        "created_at": lead.created_at.isoformat(timespec="seconds"), "updated_at": lead.updated_at.isoformat(timespec="seconds"),
    }


def all_leads(db: Session) -> list[Lead]:
    return list(db.scalars(select(Lead).order_by(Lead.created_at.desc())))


def leads_payload(db: Session) -> list[dict]:
    leads = all_leads(db)
    counts: dict[str, int] = {}
    for lead in leads:
        counts[lead.phone_norm] = counts.get(lead.phone_norm, 0) + 1
    now = utcnow()
    return [lead_dict(l, now, duplicate=counts.get(l.phone_norm, 0) > 1) for l in leads]


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

def leads_overview(db: Session) -> dict:
    m = compute_metrics(all_leads(db), utcnow())
    m["by_stage"] = {STAGE_BY_ID[k].label: v for k, v in m["by_stage"].items()}
    m["by_status"] = {STATUS_BY_ID[k].label: v for k, v in m["by_status"].items() if v}
    return m


def search_leads(db: Session, *, query: str | None = None, stage: str | None = None, status: str | None = None,
                 hot_only: bool = False, stale_only: bool = False, needs_reply_only: bool = False, limit: int = 15) -> dict:
    limit = max(1, min(int(limit or 15), 50))
    if stage and stage not in STAGE_BY_ID and stage != "active":
        return {"error": f"unknown stage '{stage}'", "allowed": list(STAGE_BY_ID) + ["active"]}
    if status and status not in STATUS_BY_ID:
        return {"error": f"unknown status '{status}'", "allowed": list(STATUS_BY_ID)}
    now = utcnow()
    q = (query or "").strip().lower()
    q_digits = normalize_phone(q) if sum(c.isdigit() for c in q) >= 3 else ""
    out = []
    for lead in all_leads(db):
        st = stage_of(lead.status)
        if stage == "active" and st not in ("new", "engaged", "closing"):
            continue
        if stage and stage != "active" and st != stage:
            continue
        if status and lead.status != status:
            continue
        if hot_only and not is_hot(lead):
            continue
        if stale_only and not is_stale(lead, now):
            continue
        if needs_reply_only and not needs_reply(lead):
            continue
        if q:
            hay = (lead.name + " " + lead_text(lead) + " " + lead.source).lower()
            raw_digits = "".join(c for c in q if c.isdigit())
            if q not in hay and not (q_digits and (q_digits in lead.phone_norm or raw_digits in lead.phone_norm)):
                continue
        d = lead_dict(lead, now)
        out.append({k: d[k] for k in ("id", "name", "phone_display", "status_label", "stage_label", "hot", "stale",
                                       "needs_reply", "last_update", "last_incoming", "next_action")})
    return {"count": len(out), "leads": out[:limit], "truncated": len(out) > limit}


def get_lead(db: Session, *, lead_id: int) -> dict:
    lead = db.get(Lead, int(lead_id))
    if lead is None:
        return {"error": f"no lead with id {lead_id}"}
    d = lead_dict(lead)
    tpl = recommended_template(db, lead.status)
    d["recommended_template"] = ({"lead_type": tpl.lead_type, "stage_a": tpl.stage_a, "stage_b": tpl.stage_b} if tpl else None)
    events = db.scalars(select(LeadEvent).where(LeadEvent.lead_id == lead.id).order_by(LeadEvent.id.desc()).limit(10)).all()
    d["activity"] = [{"kind": e.kind, "text": e.text, "by": e.actor, "at": e.created_at.isoformat(timespec="minutes")} for e in events]
    return d


def update_lead(db: Session, *, lead_id: int, status: str | None = None, append_note: str | None = None,
                last_update: str | None = None, name: str | None = None, user_id: int | None = None) -> dict:
    lead = db.get(Lead, int(lead_id))
    if lead is None:
        return {"error": f"no lead with id {lead_id}"}
    if status is not None and status not in STATUS_BY_ID:
        return {"error": f"unknown status '{status}'", "allowed": list(STATUS_BY_ID)}
    actor = _actor(db, user_id)
    changed = []
    if status is not None and status != lead.status:
        old = STATUS_BY_ID[lead.status].label if lead.status in STATUS_BY_ID else "ללא סטטוס"
        lead.status = status
        db.add(LeadEvent(lead_id=lead.id, user_id=user_id, actor=actor, kind="status", text=f"{old} ← {STATUS_BY_ID[status].label}"))
        changed.append("status")
    if append_note:
        lead.notes = (lead.notes + "\n" if lead.notes else "") + append_note.strip()
        db.add(LeadEvent(lead_id=lead.id, user_id=user_id, actor=actor, kind="note", text=append_note.strip()))
        changed.append("notes")
    if last_update:
        lead.last_update = last_update.strip()
        db.add(LeadEvent(lead_id=lead.id, user_id=user_id, actor=actor, kind="edit", text=f"עדכון אחרון: {lead.last_update}"))
        changed.append("last_update")
    if name and name.strip() != lead.name:
        lead.name = name.strip()[:80]
        changed.append("name")
    if changed:
        lead.updated_at = utcnow()
        db.commit()
    return {"id": lead.id, "updated": changed, "status_label": STATUS_BY_ID[lead.status].label if lead.status in STATUS_BY_ID else "ללא סטטוס"}


def create_lead(db: Session, *, phone: str, name: str | None = None, source: str | None = None, notes: str | None = None,
                status: str | None = "sent_intro", user_id: int | None = None) -> dict:
    norm = normalize_phone(phone)
    if len(norm) < 9:
        return {"error": "phone number looks invalid", "phone": phone}
    if status is not None and status not in STATUS_BY_ID:
        return {"error": f"unknown status '{status}'"}
    existing = db.scalar(select(Lead).where(Lead.phone_norm == norm))
    if existing is not None:
        return {"created": False, "reason": "duplicate", "id": existing.id, "name": existing.name}
    lead = Lead(phone=phone.strip(), phone_norm=norm, name=(name or "").strip()[:80], source=(source or "").strip()[:30],
                notes=(notes or "").strip(), status=status)
    db.add(lead)
    db.flush()
    db.add(LeadEvent(lead_id=lead.id, user_id=user_id, actor=_actor(db, user_id), kind="created",
                     text=f"ליד חדש · מקור: {lead.source or 'לא ידוע'}"))
    db.commit()
    return {"created": True, "id": lead.id, "phone_display": format_phone(norm)}


def list_templates(db: Session, *, lead_type: str | None = None) -> dict:
    stmt = select(Template).order_by(Template.id)
    rows = db.scalars(stmt).all()
    if lead_type:
        rows = [t for t in rows if lead_type in t.lead_type]
    return {"templates": [{"id": t.id, "lead_type": t.lead_type, "goal": t.goal, "stage_a": t.stage_a,
                           "stage_b": t.stage_b, "extra": t.extra} for t in rows]}


def record_incoming(db: Session, lead: Lead, text: str, user_id: int | None = None) -> None:
    lead.last_incoming = text.strip()
    lead.replied = False
    lead.updated_at = utcnow()
    db.add(LeadEvent(lead_id=lead.id, user_id=user_id, actor=lead.name or "הליד", kind="incoming", text=lead.last_incoming))
    db.commit()


def mark_replied(db: Session, lead: Lead, reply: str, user_id: int | None = None) -> None:
    lead.replied = True
    lead.updated_at = utcnow()
    db.add(LeadEvent(lead_id=lead.id, user_id=user_id, actor=_actor(db, user_id), kind="ai_reply", text=reply.strip()))
    db.commit()
