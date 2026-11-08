"""The morning digest: the pipeline and today's focus in a few lines.

Runs as a Railway cron service (`python -m app.digest`, schedule in README.md)
or through POST /internal/digest. It only reads; the rows it reports were
written by the chat turns during the day.
"""
from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from .config import settings
from .db import Lead, Message, Run, SessionLocal, init_db, utcnow
from .leads_meta import compute_metrics, format_phone, is_hot, needs_reply


def _local_bounds(day: date) -> tuple[datetime, datetime]:
    tz = ZoneInfo(settings.timezone)
    start = datetime.combine(day, time.min, tzinfo=tz).astimezone(timezone.utc).replace(tzinfo=None)
    end = datetime.combine(day + timedelta(days=1), time.min, tzinfo=tz).astimezone(timezone.utc).replace(tzinfo=None)
    return start, end


def build_digest(db: Session, day: date | None = None) -> str:
    tz = ZoneInfo(settings.timezone)
    day = day or (datetime.now(tz).date() - timedelta(days=1))
    start, end = _local_bounds(day)

    leads = list(db.scalars(select(Lead)))
    m = compute_metrics(leads, utcnow())
    new_yesterday = [l for l in leads if start <= l.created_at < end]
    hot = [l for l in leads if is_hot(l)]
    waiting = [l for l in leads if needs_reply(l)]

    messages = db.scalar(select(func.count()).select_from(Message)
                         .where(Message.role == "user", Message.created_at >= start, Message.created_at < end)) or 0
    runs = db.execute(select(func.count(Run.id), func.coalesce(func.sum(Run.cost_usd), 0.0),
                             func.sum(case((Run.status != "ok", 1), else_=0)))
                      .where(Run.created_at >= start, Run.created_at < end)).one()
    run_count, cost, not_ok = int(runs[0] or 0), float(runs[1] or 0.0), int(runs[2] or 0)

    def names(rows):
        return "; ".join(f"{l.name or format_phone(l.phone_norm)}" for l in rows[:5])

    lines = [f"LeadPilot — סיכום בוקר ל-{day.strftime('%d/%m/%Y')}",
             f"לידים חדשים אתמול: {len(new_yesterday)} · סה״כ {m['total']} · פעילים {m['active']}",
             f"🔥 חמים לטיפול היום: {len(hot)}" + (f" — {names(hot)}" if hot else ""),
             f"💬 ממתינים למענה: {len(waiting)}" + (f" — {names(waiting)}" if waiting else ""),
             f"⏳ לא עודכנו מעל 3 ימים: {m['stale']} · נסגרו: {m['won']} (המרה {m['conversion_rate']:.0%})",
             f"עוזר AI: {messages} הודעות · {run_count} ריצות · ${cost:.2f} מתוך ${settings.daily_cap_usd:.2f}"
             + (f" · {not_ok} ריצות עם תקלה" if not_ok else "")]
    return "\n".join(lines)


def send_digest(text: str) -> bool:
    """POST {"text": ...} to DIGEST_WEBHOOK_URL (Slack-compatible). Returns False when no URL is set."""
    if not settings.digest_webhook_url:
        return False
    import httpx

    r = httpx.post(settings.digest_webhook_url, json={"text": text}, timeout=15)
    r.raise_for_status()
    return True


def main() -> None:
    init_db()
    with SessionLocal() as db:
        body = build_digest(db)
    print(body)
    sent = send_digest(body)
    print(f"\n[sent to webhook: {sent}]")


if __name__ == "__main__":
    main()
