"""Database layer (Leads Copilot): models, engine, session, startup migration and seeding.

Postgres on Railway (DATABASE_URL from the plugin) or SQLite locally. The
schema is created at start with `create_all`; `schema_version` records which
version is live so a later real migration tool has somewhere to start.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
    func,
    select,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship, sessionmaker

from .config import ROOT, settings

SCHEMA_VERSION = 1


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Base(DeclarativeBase):
    pass


class SchemaVersion(Base):
    __tablename__ = "schema_version"
    version: Mapped[int] = mapped_column(Integer, primary_key=True)
    applied_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Conversation(Base):
    __tablename__ = "conversations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(120), default="New chat")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    messages: Mapped[list["Message"]] = relationship(back_populates="conversation", order_by="Message.id")


class Message(Base):
    __tablename__ = "messages"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    role: Mapped[str] = mapped_column(String(10))  # "user" | "assistant"
    content: Mapped[str] = mapped_column(Text)  # plain text shown in the UI
    has_image: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
    conversation: Mapped[Conversation] = relationship(back_populates="messages")


class Run(Base):
    """One model turn: the record behind the cost cap, the digest and the runbook."""

    __tablename__ = "runs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    conversation_id: Mapped[int | None] = mapped_column(ForeignKey("conversations.id"), nullable=True, index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    model: Mapped[str] = mapped_column(String(60))
    status: Mapped[str] = mapped_column(String(20), default="ok")  # ok | refusal | error | aborted | capped
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    cache_read_tokens: Mapped[int] = mapped_column(Integer, default=0)
    cache_write_tokens: Mapped[int] = mapped_column(Integer, default=0)
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    tool_calls: Mapped[int] = mapped_column(Integer, default=0)
    tool_names: Mapped[str] = mapped_column(String(200), default="")
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)


class Lead(Base):
    """One lead: a phone number, three free-text follow-up fields, a status and notes (the reference sheet's columns)."""

    __tablename__ = "leads"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    phone: Mapped[str] = mapped_column(String(40))
    phone_norm: Mapped[str] = mapped_column(String(20), index=True)
    name: Mapped[str] = mapped_column(String(80), default="")
    source: Mapped[str] = mapped_column(String(30), default="")
    status: Mapped[str | None] = mapped_column(String(30), nullable=True, index=True)
    first_attempt: Mapped[str] = mapped_column(Text, default="")
    second_attempt: Mapped[str] = mapped_column(Text, default="")
    last_update: Mapped[str] = mapped_column(Text, default="")
    notes: Mapped[str] = mapped_column(Text, default="")
    last_incoming: Mapped[str] = mapped_column(Text, default="")  # the latest message the lead sent us
    replied: Mapped[bool] = mapped_column(Boolean, default=True)  # False while last_incoming waits for an answer
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class LeadEvent(Base):
    """The activity log of a lead: created, status changes, notes, smart replies sent."""

    __tablename__ = "lead_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey("leads.id"), index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    actor: Mapped[str] = mapped_column(String(40), default="")
    kind: Mapped[str] = mapped_column(String(20))  # created | status | edit | note | ai_reply | incoming
    text: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)


class Template(Base):
    """A WhatsApp message template, by lead type (read-only reference)."""

    __tablename__ = "templates"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lead_type: Mapped[str] = mapped_column(String(60), index=True)
    goal: Mapped[str] = mapped_column(Text, default="")
    stage_a: Mapped[str] = mapped_column(Text, default="")
    stage_b: Mapped[str] = mapped_column(Text, default="")
    extra: Mapped[str] = mapped_column(Text, default="")


# ---------------------------------------------------------------------------
# Engine and session
# ---------------------------------------------------------------------------

def make_engine(url: str | None = None):
    url = url or settings.database_url
    kwargs: dict = {"pool_pre_ping": True}
    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
    return create_engine(url, **kwargs)


engine = make_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Startup: schema, version, seed data
# ---------------------------------------------------------------------------

def init_db(bind=None, data_dir: Path | None = None) -> dict:
    """Create tables, record the schema version, seed demo leads and templates if empty."""
    bind = bind or engine
    data_dir = data_dir or (ROOT / "data")
    Base.metadata.create_all(bind)
    report = {"schema_version": SCHEMA_VERSION, "templates_seeded": 0, "leads_seeded": 0}
    with Session(bind) as db:
        if db.scalar(select(func.count()).select_from(SchemaVersion)) == 0:
            db.add(SchemaVersion(version=SCHEMA_VERSION))
            db.commit()
        if db.scalar(select(func.count()).select_from(Template)) == 0:
            report["templates_seeded"] = _seed_templates(db, data_dir / "templates.json")
        if db.scalar(select(func.count()).select_from(Lead)) == 0:
            report["leads_seeded"] = _seed_leads(db, data_dir / "leads.json")
    return report


def _seed_templates(db: Session, path: Path) -> int:
    if not path.exists():
        return 0
    rows = [Template(lead_type=r["lead_type"], goal=r.get("goal", ""), stage_a=r.get("stage_a", ""),
                     stage_b=r.get("stage_b", ""), extra=r.get("extra", "")) for r in json.loads(path.read_text("utf-8"))]
    db.add_all(rows)
    db.commit()
    return len(rows)


def _seed_leads(db: Session, path: Path) -> int:
    """Demo leads. Dates are relative (days_ago) so "stale" and "today" stay meaningful on any day."""
    from .leads_meta import normalize_phone

    if not path.exists():
        return 0
    now = utcnow()
    count = 0
    for r in json.loads(path.read_text("utf-8")):
        created = now - timedelta(days=r.get("days_ago", 0), hours=r.get("hours_ago", 0))
        updated = now - timedelta(days=r.get("updated_days_ago", r.get("days_ago", 0)), hours=r.get("hours_ago", 0))
        lead = Lead(phone=r["phone"], phone_norm=normalize_phone(r["phone"]), name=r.get("name", ""), source=r.get("source", ""),
                    status=r.get("status"), first_attempt=r.get("first_attempt", ""), second_attempt=r.get("second_attempt", ""),
                    last_update=r.get("last_update", ""), notes=r.get("notes", ""), last_incoming=r.get("last_incoming", ""),
                    replied=not r.get("last_incoming"), created_at=created, updated_at=updated)
        db.add(lead)
        db.flush()
        db.add(LeadEvent(lead_id=lead.id, actor="מערכת", kind="created", text=f"ליד נוצר ממקור: {lead.source or 'לא ידוע'}", created_at=created))
        if lead.last_incoming:
            db.add(LeadEvent(lead_id=lead.id, actor=lead.name or "הליד", kind="incoming", text=lead.last_incoming, created_at=updated))
        count += 1
    db.commit()
    return count
