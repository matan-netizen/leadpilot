"""The leads domain in one place: statuses, stages, phone rules and the computed flags.

Mirrors the reference dashboard's model: 12 statuses grouped into 6 stages,
stages 1-4 are the active funnel, 5-6 are outside it. The UI receives the
same tables from /api/meta, so there is a single source of truth.
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta

STALE_AFTER_DAYS = 3


@dataclass(frozen=True)
class StatusDef:
    id: str
    label: str
    stage: str
    tone: str
    next_action: str
    template_type: str | None = None


@dataclass(frozen=True)
class StageDef:
    id: str
    label: str
    description: str
    default_status: str
    active: bool
    tone: str


# Order = order in the UI.
STATUSES: list[StatusDef] = [
    StatusDef("sent_intro", "נשלחה הודעה לתיאום שיחה", "new", "blue", "אם אין מענה תוך 24 שעות – לשלוח הודעת המשך", "קיבל פניה ולא הגיב"),
    StatusDef("call_scheduled", "קבע / רוצה שיחה", "engaged", "cyan", "לקיים את השיחה בזמן שנקבע ולעדכן את התוצאה", "נקבעה שיחה"),
    StatusDef("info_sent", "נשלח מידע / הקלטה", "engaged", "teal", "לבדוק אחרי 24 שעות אם עבר על המידע והאם יש שאלות", "נשלח מידע"),
    StatusDef("callback", "מעוניין – מנהל מכירות יחזור", "engaged", "purple", "להעביר למנהל המכירות לשיחה חוזרת היום", "נקבעה שיחה"),
    StatusDef("offer_sent", "נשלחה הצעת מחיר", "closing", "orange", "לוודא קבלה ולתאם חתימה", "לקראת סגירה"),
    StatusDef("hesitating", "מתלבט / מתייעץ", "closing", "yellow", "לברר מה מעכב ולטפל בהתנגדות", "רוצה להתקדם - מתעכב"),
    StatusDef("wants_to_wait", "רוצה לחכות", "paused", "gray", "לקבוע תזכורת לחזרה בתאריך שסוכם", "רוצה לחכות"),
    StatusDef("no_response", "לא מגיב!", "paused", "red", "לשלוח הודעת בדיקת רלוונטיות; אחרי 48 שעות – ליד קר", "קיבל 2 פניות ולא הגיב"),
    StatusDef("not_interested", "לא מעוניין", "lost", "red", "אין – לסגור את הליד"),
    StatusDef("not_relevant", "לא רלוונטי", "lost", "gray", "אין – לסגור את הליד"),
    StatusDef("rejected", "לקוח שלא רוצים להכניס", "lost", "pink", "אין – לא להמשיך"),
    StatusDef("closed", "נסגר", "won", "green", "לוודא תשלום ולעדכן בשדה \"הערות / תשלום\""),
]

STAGES: list[StageDef] = [
    StageDef("new", "פנייה ראשונית", "נשלחה הודעה, טרם נוצר קשר", "sent_intro", True, "blue"),
    StageDef("engaged", "בשיחה", "יש קשר – שיחה, מידע או חזרה של מנהל מכירות", "call_scheduled", True, "teal"),
    StageDef("closing", "לקראת סגירה", "הצעת מחיר או מתלבט", "offer_sent", True, "orange"),
    StageDef("won", "נסגר", "עסקה נסגרה", "closed", True, "green"),
    StageDef("paused", "תקוע / מושהה", "לא מגיב או רוצה לחכות", "no_response", False, "yellow"),
    StageDef("lost", "אבוד", "לא מעוניין, לא רלוונטי או נפסל", "not_interested", False, "gray"),
]

SOURCES = ["וואטסאפ", "פייסבוק", "אינסטגרם", "אתר", "גוגל", "הפניה"]

STATUS_BY_ID = {s.id: s for s in STATUSES}
STAGE_BY_ID = {s.id: s for s in STAGES}
STATUS_IDS = [s.id for s in STATUSES]
STAGE_IDS = [s.id for s in STAGES]


def stage_of(status: str | None) -> str:
    return STATUS_BY_ID[status].stage if status in STATUS_BY_ID else "new"


def meta() -> dict:
    return {"statuses": [asdict(s) for s in STATUSES], "stages": [asdict(s) for s in STAGES],
            "sources": SOURCES, "stale_after_days": STALE_AFTER_DAYS}


# ---------------------------------------------------------------------------
# Phones
# ---------------------------------------------------------------------------

def normalize_phone(raw: str | None) -> str:
    """Digits only, international: 0… → 972…, 9720… → 972…, 9 digits starting with 5 → 972…."""
    d = re.sub(r"\D", "", raw or "")
    if d.startswith("9720"):
        d = "972" + d[4:]
    elif d.startswith("0"):
        d = "972" + d[1:]
    elif len(d) == 9 and d.startswith("5"):
        d = "972" + d
    return d


def format_phone(norm: str) -> str:
    if norm.startswith("972") and len(norm) == 12:
        local = "0" + norm[3:]
        return f"{local[:3]}-{local[3:6]}-{local[6:]}"
    if norm.startswith("972") and len(norm) == 11:  # landline: 03-612-4478
        local = "0" + norm[3:]
        return f"{local[:2]}-{local[2:5]}-{local[5:]}"
    return f"+{norm}" if norm else ""


# ---------------------------------------------------------------------------
# Computed flags
# ---------------------------------------------------------------------------

_HOT_WORDS = re.compile(r"(^|[\s,.!?\-])חם($|[\s,.!?\-])|לסגור|מאוד מעוניין|דחוף")


def lead_text(lead) -> str:
    return " ".join(x for x in (lead.first_attempt, lead.second_attempt, lead.last_update, lead.notes, lead.last_incoming) if x)


def is_hot(lead) -> bool:
    stage = stage_of(lead.status)
    if stage in ("won", "lost"):
        return False
    return lead.status in ("callback", "call_scheduled") or bool(_HOT_WORDS.search(lead_text(lead)))


def is_stale(lead, now: datetime) -> bool:
    if stage_of(lead.status) not in ("new", "engaged", "closing"):
        return False
    ref = lead.updated_at or lead.created_at
    return ref is not None and now - ref > timedelta(days=STALE_AFTER_DAYS)


def is_paid(lead) -> bool:
    return "שולם" in (lead.notes or "")


def needs_reply(lead) -> bool:
    """A message from the lead is waiting and nobody answered it since."""
    return bool(lead.last_incoming) and not lead.replied and stage_of(lead.status) not in ("lost",)


def compute_metrics(leads: list, now: datetime) -> dict:
    by_stage = {s: 0 for s in STAGE_IDS}
    by_status = {s: 0 for s in STATUS_IDS}
    no_status = missing_name = hot = stale = paid = waiting = 0
    phones: dict[str, list[int]] = {}
    for lead in leads:
        by_stage[stage_of(lead.status)] += 1
        if lead.status in by_status:
            by_status[lead.status] += 1
        else:
            no_status += 1
        missing_name += not (lead.name or "").strip()
        hot += is_hot(lead)
        stale += is_stale(lead, now)
        paid += is_paid(lead)
        waiting += needs_reply(lead)
        phones.setdefault(lead.phone_norm, []).append(lead.id)
    total = len(leads)
    won, lost = by_stage["won"], by_stage["lost"]
    duplicates = {p: ids for p, ids in phones.items() if p and len(ids) > 1}
    return {
        "total": total, "active": by_stage["new"] + by_stage["engaged"] + by_stage["closing"],
        "hot": hot, "stale": stale, "won": won, "lost": lost, "paused": by_stage["paused"], "paid": paid,
        "waiting_reply": waiting, "missing_name": missing_name, "no_status": no_status,
        "conversion_rate": round(won / total, 4) if total else 0.0,
        "win_rate": round(won / (won + lost), 4) if (won + lost) else 0.0,
        "by_stage": by_stage, "by_status": by_status,
        "duplicates": {format_phone(p): ids for p, ids in duplicates.items()},
    }
