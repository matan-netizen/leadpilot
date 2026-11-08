"""Smart reply ("מענה חכם"): a ready-to-send WhatsApp answer for one lead's latest message.

With a key, one short model call (prompts/smart_reply.md) returns JSON: the
reply, the lead's intent, a suggested status and a one-line summary. Without a
key, a keyword classifier picks the intent and fills the matching template.
Either way the result is a draft: the rep edits it and sends it from WhatsApp.
"""
from __future__ import annotations

import json
import re
import time

from sqlalchemy.orm import Session

from .config import ROOT, settings
from .costs import cost_usd
from .db import Lead, Run
from .leads_meta import STATUS_BY_ID, STATUSES, stage_of
from .tools.leads import lead_dict, recommended_template

PROMPT_PATH = ROOT / "app" / "prompts" / "smart_reply.md"

TONES = {"friendly": "חם ואישי", "short": "קצר מאוד ותכליתי", "formal": "מקצועי ורשמי"}

_INTENTS: list[tuple[str, re.Pattern, str | None]] = [
    ("not_interested", re.compile(r"לא מעוניין|לא רלוונטי|תורידו|הסר|לא צריך|stop", re.I), "not_interested"),
    ("hesitation", re.compile(r"מתלבט|לחשוב|אחשוב|מתייעץ|אתייעץ|יקר|גבוה לי|לא בטוח"), "hesitating"),
    ("price", re.compile(r"מחיר|כמה.{0,10}עול|עלות|מה התעריף|תשלומ|הצעת מחיר|₪|שקל", re.I), None),
    ("schedule", re.compile(r"מתי|שעה|לדבר|שיחה|זום|לתאם|מאשר|אחרי \d|ביום"), "call_scheduled"),
    ("interest", re.compile(r"מעוניין|רוצה|נשמע טוב|נראה טוב|מעולה|איך מתקדמים|לסגור|בוא נתקדם"), None),
    ("question", re.compile(r"\?|האם|אפשר|אתם עושים"), None),
]


def _first_name(lead: Lead) -> str:
    name = (lead.name or "").strip()
    if not name or any(w in name for w in ("סטודיו", "מרכז", "משרד", "חנות", "מוסך", "מאפיית", "קונדיטוריית", "מספרת")):
        return ""
    return name.split()[0]


def _fill(text: str, lead: Lead) -> str:
    first = _first_name(lead)
    text = text.replace("{שם}", first).replace("{שירות}", "השירות שביקשת").replace("{מועד}", "המועד שנוח לך")
    text = re.sub(r"\s+,", ",", text).replace("היי ,", "היי,").replace(" ,", ",")
    return re.sub(r"\s{2,}", " ", text).strip()


def classify(incoming: str) -> str:
    for intent, rx, _ in _INTENTS:
        if rx.search(incoming or ""):
            return intent
    return "other"


def rules_reply(db: Session, lead: Lead, incoming: str, tone: str = "friendly") -> dict:
    intent = classify(incoming)
    first = _first_name(lead)
    hi = f"היי {first}" if first else "היי"
    stage = stage_of(lead.status)
    suggested = next((s for i, _, s in _INTENTS if i == intent), None)
    if intent == "price":
        reply = f"{hi}, תודה על הפנייה! 🙂 המחיר תלוי בהיקף ובמה שחשוב לך. בשיחה קצרה של 10 דקות אוכל לתת הצעה מדויקת – מתי נוח לך?"
        suggested = "call_scheduled" if stage == "new" else None
    elif intent == "schedule":
        reply = f"{hi}, מעולה – מאשר! נדבר במועד שציינת. אם משהו משתנה, פשוט תכתוב לי כאן."
    elif intent == "hesitation":
        reply = f"{hi}, לגמרי מבין, זו החלטה שכדאי לשקול 🙂 מה השיקול העיקרי שמעכב – מחיר, זמנים או משהו אחר? אשמח לעזור למצוא פתרון שמתאים."
    elif intent == "not_interested":
        reply = f"{hi}, תודה שעדכנת! אם בעתיד זה יחזור להיות רלוונטי – אני כאן. בהצלחה!"
    elif intent == "interest":
        if stage == "closing":
            reply = f"{hi}, איזה כיף לשמוע! 🙌 אשלח לך עכשיו קישור לאישור ההצעה, ואחרי זה נתאם פגישת פתיחה."
            suggested = "offer_sent"
        else:
            reply = f"{hi}, שמח לשמוע! 🙂 השלב הבא הוא שיחה קצרה כדי להבין בדיוק מה צריך – מתי נוח לך היום או מחר?"
            suggested = "call_scheduled"
    else:
        tpl = recommended_template(db, lead.status)
        base = _fill(tpl.stage_a, lead) if tpl else ""
        reply = (f"{hi}, תודה על ההודעה! " + ("אשמח לענות על הכול בשיחה קצרה – מתי נוח לך?" if intent == "question" else "")).strip()
        if not incoming.strip() and base:
            reply = base
    if tone == "short":
        reply = re.split(r"(?<=[.!?])\s", reply)[0]
    elif tone == "formal":
        reply = reply.replace("היי", "שלום").replace(" 🙂", "").replace(" 🙌", "")
    summaries = {"price": "שואל על מחיר", "schedule": "רוצה לתאם / מאשר שיחה", "hesitation": "מתלבט – יש התנגדות",
                 "not_interested": "לא מעוניין", "interest": "מראה עניין להתקדם", "question": "שאלה כללית", "other": "הודעה כללית"}
    return {"reply": reply, "intent": intent, "suggested_status": suggested if suggested != lead.status else None,
            "summary": summaries[intent], "engine": "rules"}


def _card(db: Session, lead: Lead) -> str:
    d = lead_dict(lead)
    tpl = recommended_template(db, lead.status)
    keep = {k: d[k] for k in ("name", "source", "status_label", "stage_label", "next_action", "first_attempt",
                              "second_attempt", "last_update", "notes")}
    keep["recommended_template"] = {"stage_a": tpl.stage_a, "stage_b": tpl.stage_b} if tpl else None
    return json.dumps(keep, ensure_ascii=False)


def _parse(text: str) -> dict:
    m = re.search(r"\{.*\}", text, re.S)
    data = json.loads(m.group(0) if m else text)
    if not isinstance(data, dict) or not str(data.get("reply", "")).strip():
        raise ValueError("no reply in model output")
    if data.get("suggested_status") not in STATUS_BY_ID:
        data["suggested_status"] = None
    return {"reply": str(data["reply"]).strip(), "intent": str(data.get("intent") or "other"),
            "suggested_status": data["suggested_status"], "summary": str(data.get("summary") or "")}


def generate(db: Session, lead: Lead, incoming: str, *, client, user_id: int | None, tone: str = "friendly") -> dict:
    """Draft the reply. Records a runs row (cost cap, digest) when a model is used."""
    if client.name == "offline":
        return rules_reply(db, lead, incoming, tone)
    started = time.monotonic()
    system = (PROMPT_PATH.read_text(encoding="utf-8").replace("{{BUSINESS}}", settings.business_name)
              .replace("{{STATUSES}}", ", ".join(f"{s.id} ({s.label})" for s in STATUSES)))
    prompt = (f"Lead card:\n{_card(db, lead)}\n\nThe lead's latest message:\n<<<\n{incoming or '(no new message – write a follow-up)'}\n>>>\n\n"
              f"Tone: {TONES.get(tone, TONES['friendly'])}.")
    model = settings.model if client.name == "anthropic" else client.name
    run = Run(user_id=user_id, model=model, status="ok", tool_names="smart_reply")
    try:
        text, usage = client.complete(system=system, prompt=prompt)
        run.input_tokens, run.output_tokens = usage.input_tokens, usage.output_tokens
        run.cache_read_tokens, run.cache_write_tokens = usage.cache_read_tokens, usage.cache_write_tokens
        run.cost_usd = cost_usd(model, usage)
        result = _parse(text)
        result["engine"] = "ai"
    except Exception as exc:  # noqa: BLE001 - fall back to the rules; the rep still gets a draft
        run.status = "error"
        run.error = f"{type(exc).__name__}: {exc}"[:2000]
        result = rules_reply(db, lead, incoming, tone)
        result["warning"] = "המודל לא זמין כרגע – זו טיוטה מבוססת כללים."
    run.duration_ms = int((time.monotonic() - started) * 1000)
    db.add(run)
    db.commit()
    result["cost_usd"] = run.cost_usd
    return result
