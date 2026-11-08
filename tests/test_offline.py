"""Offline mode: without a key the agent loop still answers basic questions through the tools."""
from app.agent import run_turn
from app.db import SessionLocal, User
from app.offline import OfflineModelClient


def _turn(text):
    with SessionLocal() as s:
        user = s.query(User).filter_by(name="Dana").one()
        return list(run_turn(s, user=user, conversation=None, text=text, image=None, client=OfflineModelClient()))


def test_offline_daily_focus_uses_tools(client, logged_in):
    events = _turn("מה לטפל היום?")
    tools = [e["name"] for e in events if e["type"] == "tool" and e["status"] == "start"]
    assert tools == ["search_leads"] * 3
    text = "".join(e["text"] for e in events if e["type"] == "text")
    assert "חמים לטיפול" in text and "ממתינים למענה" in text and events[-1]["type"] == "done"


def test_offline_overview_and_help(client, logged_in):
    assert "תמונת מצב" in "".join(e.get("text", "") for e in _turn("כמה לידים יש?"))
    assert "ANTHROPIC_API_KEY" in "".join(e.get("text", "") for e in _turn("שלום"))
