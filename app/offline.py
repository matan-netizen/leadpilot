"""Offline mode: a small rule engine that stands in for the model when no ANTHROPIC_API_KEY is set.

It speaks the same ModelClient protocol as the real client (stream + complete),
so the agent loop, the tools, the run rows and the UI all work unchanged. It
only recognises a handful of intents; the point is that a fresh deploy is
usable and demonstrable before a key is added. Add the key and the real model
takes over with no code change.
"""
from __future__ import annotations

import json
import re
from typing import Iterator

from .costs import Usage

HELP = (
    "אני **LeadPilot** במצב אופליין (בלי מפתח API) – אני מבין בקשות בסיסיות:\n\n"
    "- **מה לטפל היום?** – לידים חמים, ממתינים למענה ולא מעודכנים\n"
    "- **כמה לידים יש? / מה אחוז ההמרה?** – תמונת מצב\n"
    "- **לידים חמים** · **מי ממתין לתשובה?** · **מי לא עודכן?**\n"
    "- **חפש 052-771** או **חפש אורי** – חיפוש ליד\n"
    "- **תבניות** – תבניות הוואטסאפ\n\n"
    "כדי לקבל עוזר AI מלא (ניסוח חופשי, עדכון לידים בשפה טבעית) – מגדירים `ANTHROPIC_API_KEY` ב-Railway."
)


def _user_text(content) -> str:
    if isinstance(content, str):
        return content
    return " ".join(b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text")


def _plan(text: str) -> list[tuple[str, dict]]:
    t = text.strip()
    m = re.search(r"(?:חפש|מצא|חיפוש|search)\s+(.+)", t)
    if m:
        return [("search_leads", {"query": m.group(1).strip(" ?!.")})]
    if re.search(r"\d{3,}", t) and len(re.sub(r"\D", "", t)) >= 6:
        return [("search_leads", {"query": re.sub(r"[^\d]", "", t)})]
    if any(w in t for w in ("היום", "לטפל", "עדיפות", "פוקוס", "focus", "today")):
        return [("search_leads", {"hot_only": True, "limit": 8}), ("search_leads", {"needs_reply_only": True, "limit": 8}),
                ("search_leads", {"stale_only": True, "limit": 8})]
    if "חמ" in t or "hot" in t.lower():
        return [("search_leads", {"hot_only": True})]
    if any(w in t for w in ("ממתינ", "לענות", "תשובה", "מענה", "הודעות")):
        return [("search_leads", {"needs_reply_only": True})]
    if any(w in t for w in ("לא עודכנ", "תקוע", "ישנ", "stale")):
        return [("search_leads", {"stale_only": True})]
    if "תבני" in t or "template" in t.lower():
        return [("list_templates", {})]
    if any(w in t for w in ("כמה", "סיכום", "המרה", "מצב", "סטטיסטיק", "משפך", "overview", "how many")):
        return [("leads_overview", {})]
    return []


def _fmt_leads(title: str, r: dict) -> str:
    if r.get("error"):
        return f"**{title}:** שגיאה – {r['error']}"
    if not r.get("count"):
        return f"**{title}:** אין 🎉"
    lines = [f"**{title} ({r['count']}):**"]
    for l in r["leads"]:
        flags = (" 🔥" if l["hot"] else "") + (" 💬" if l["needs_reply"] else "")
        lines.append(f"- **{l['name'] or 'ללא שם'}**{flags} · {l['phone_display']} · {l['status_label']} – {l['next_action']}")
    return "\n".join(lines)


def _fmt_overview(r: dict) -> str:
    stages = " · ".join(f"{k}: {v}" for k, v in r["by_stage"].items())
    return (f"**תמונת מצב:** {r['total']} לידים, {r['active']} בתהליך פעיל.\n\n"
            f"- 🔥 חמים: **{r['hot']}** · 💬 ממתינים למענה: **{r['waiting_reply']}** · ⏳ לא עודכנו: **{r['stale']}**\n"
            f"- נסגרו: **{r['won']}** (המרה {r['conversion_rate']:.0%}, שיעור זכייה {r['win_rate']:.0%}) · שולמו: {r['paid']}\n"
            f"- לפי שלב: {stages}\n"
            + (f"- מספרים כפולים: {', '.join(r['duplicates'])}" if r["duplicates"] else ""))


def _fmt_templates(r: dict) -> str:
    return "**תבניות וואטסאפ:**\n" + "\n".join(f"- **{t['lead_type']}** – {t['goal']}" for t in r["templates"])


class OfflineModelClient:
    name = "offline"

    def stream(self, *, system, messages, tools) -> Iterator[ModelEvent]:  # noqa: F821 - imported lazily below
        from .agent import ModelEvent

        last = messages[-1]["content"]
        if isinstance(last, list) and last and last[0].get("type") == "tool_result":
            calls = {b["id"]: b for b in messages[-2]["content"] if b.get("type") == "tool_use"}
            parts = []
            titles = iter(["🔥 חמים לטיפול", "💬 ממתינים למענה", "⏳ לא עודכנו מעל 3 ימים"])
            multi = len(last) > 1
            for res in last:
                call = calls.get(res["tool_use_id"], {})
                data = json.loads(res["content"])
                name, args = call.get("name"), call.get("input", {})
                if name == "leads_overview":
                    parts.append(_fmt_overview(data))
                elif name == "list_templates":
                    parts.append(_fmt_templates(data))
                else:
                    title = next(titles) if multi else ("תוצאות חיפוש" if args.get("query") else
                                                        "🔥 לידים חמים" if args.get("hot_only") else
                                                        "💬 ממתינים למענה" if args.get("needs_reply_only") else
                                                        "⏳ לא עודכנו" if args.get("stale_only") else "לידים")
                    parts.append(_fmt_leads(title, data))
            text = "\n\n".join(parts) + "\n\n_מצב אופליין – לניסוח תשובות חכמות פתחו ליד ולחצו \"מענה חכם\"._"
            yield ModelEvent(type="text", text=text)
            yield ModelEvent(type="stop", stop_reason="end_turn", usage=Usage(), content=[{"type": "text", "text": text}])
            return

        plan = _plan(_user_text(last))
        if not plan:
            yield ModelEvent(type="text", text=HELP)
            yield ModelEvent(type="stop", stop_reason="end_turn", usage=Usage(), content=[{"type": "text", "text": HELP}])
            return
        blocks = [{"type": "tool_use", "id": f"off_{i}", "name": n, "input": a} for i, (n, a) in enumerate(plan)]
        yield ModelEvent(type="stop", stop_reason="tool_use", usage=Usage(), content=blocks)

    def complete(self, *, system: str, prompt: str, max_tokens: int = 600) -> tuple[str, Usage]:
        raise NotImplementedError("offline smart replies are built in smart_reply.rules_reply")
