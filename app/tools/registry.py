"""Tool definitions the model sees, and the dispatcher that runs them."""
from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session

from ..leads_meta import SOURCES, STAGE_IDS, STATUS_IDS, STATUSES
from . import leads

_STATUS_HELP = "; ".join(f"{s.id} = {s.label}" for s in STATUSES)

TOOLS: list[dict[str, Any]] = [
    {
        "name": "leads_overview",
        "description": (
            "Live numbers for the whole pipeline: totals, leads per stage and per status, hot leads, stale leads "
            "(no update for 3+ days), leads waiting for a reply, conversion and win rate, duplicate phones. "
            "Call it for any question about how many / how the pipeline looks. Never guess a number."
        ),
        "input_schema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "search_leads",
        "description": (
            "Find leads. Free-text query matches name, notes, follow-up text and phone (any format, 3+ digits). "
            "Filter by stage, status, hot_only, stale_only, needs_reply_only. Returns id, name, phone, status, next action. "
            f"Statuses: {_STATUS_HELP}."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "stage": {"type": "string", "enum": STAGE_IDS + ["active"], "description": "active = new+engaged+closing"},
                "status": {"type": "string", "enum": STATUS_IDS},
                "hot_only": {"type": "boolean"},
                "stale_only": {"type": "boolean"},
                "needs_reply_only": {"type": "boolean", "description": "the lead wrote to us and nobody answered yet"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 50, "default": 15},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "get_lead",
        "description": "Full card of one lead: all fields, next action, recommended WhatsApp template and the last 10 activity events. Call it before writing a reply for a specific lead.",
        "input_schema": {"type": "object", "properties": {"lead_id": {"type": "integer"}}, "required": ["lead_id"], "additionalProperties": False},
    },
    {
        "name": "update_lead",
        "description": (
            "Change one lead: set a new status, append a note, or replace the 'last update' text. Only when the user asked for the change "
            "or clearly reported what happened with the lead. Never delete. Reply with what changed."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "lead_id": {"type": "integer"},
                "status": {"type": "string", "enum": STATUS_IDS},
                "append_note": {"type": "string"},
                "last_update": {"type": "string"},
                "name": {"type": "string"},
            },
            "required": ["lead_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "create_lead",
        "description": "Add a new lead. Phone is required; duplicates (same number in any format) are not created – the existing lead id is returned instead.",
        "input_schema": {
            "type": "object",
            "properties": {
                "phone": {"type": "string"},
                "name": {"type": "string"},
                "source": {"type": "string", "enum": SOURCES},
                "notes": {"type": "string"},
            },
            "required": ["phone"],
            "additionalProperties": False,
        },
    },
    {
        "name": "list_templates",
        "description": "The business's WhatsApp message templates by lead type. Use them as the base for any message you draft.",
        "input_schema": {"type": "object", "properties": {"lead_type": {"type": "string"}}, "additionalProperties": False},
    },
]

TOOL_NAMES = {t["name"] for t in TOOLS}
WRITE_TOOLS = {"update_lead", "create_lead"}
MAX_RESULT_CHARS = 12000


def execute(name: str, tool_input: dict[str, Any], db: Session, *, user_id: int | None = None) -> str:
    """Run one tool and return its result as a JSON string for the model."""
    args = _clean(tool_input)
    try:
        if name == "leads_overview":
            result = leads.leads_overview(db)
        elif name == "search_leads":
            result = leads.search_leads(db, **args)
        elif name == "get_lead":
            result = leads.get_lead(db, lead_id=int(args.get("lead_id", 0)))
        elif name == "update_lead":
            result = leads.update_lead(db, user_id=user_id, **args)
        elif name == "create_lead":
            result = leads.create_lead(db, user_id=user_id, **args)
        elif name == "list_templates":
            result = leads.list_templates(db, **args)
        else:
            result = {"error": f"unknown tool '{name}'"}
    except Exception as exc:  # the loop must survive a bad input; the model sees the error
        db.rollback()
        result = {"error": f"{type(exc).__name__}: {exc}"}
    text = json.dumps(result, ensure_ascii=False, default=str)
    if len(text) > MAX_RESULT_CHARS:
        text = text[:MAX_RESULT_CHARS] + '... (truncated)"}'
    return text


def _clean(d: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in d.items() if v is not None}
