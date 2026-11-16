"""When the API account cannot be used (no credit, bad key), the app keeps working in rules mode."""
import anthropic
import httpx

from app import agent as agent_module
from app.agent import AnthropicModelClient, account_problem, run_turn
from app.db import Lead, SessionLocal, User
from app.smart_reply import generate


def _credit_error():
    req = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
    return anthropic.BadRequestError(
        "Your credit balance is too low to access the Anthropic API. Please go to Plans & Billing to upgrade or purchase credits.",
        response=httpx.Response(400, request=req), body=None)


class NoCreditClient(AnthropicModelClient):
    """The real client's fallback logic, with an API that always says 'no credit'."""

    def __init__(self):  # no SDK client needed
        self.unavailable_until = 0.0
        self.unavailable_reason = ""
        self.api_calls = 0

    def _stream_api(self, *, system, messages, tools):
        self.api_calls += 1
        raise _credit_error()
        yield  # pragma: no cover

    def complete(self, *, system, prompt, max_tokens=600):
        raise _credit_error()


def test_account_problem_is_recognised():
    assert "אין קרדיט" in account_problem(_credit_error())
    assert account_problem(ValueError("x")) is None


def test_chat_falls_back_to_rules_without_credit(client, logged_in):
    c = NoCreditClient()
    with SessionLocal() as s:
        user = s.query(User).filter_by(name="Dana").one()
        events = list(run_turn(s, user=user, conversation=None, text="מה לטפל היום?", image=None, client=c))
    text = "".join(e["text"] for e in events if e["type"] == "text")
    assert "אין קרדיט" in text and "חמים לטיפול" in text  # explained once, then answered
    assert events[-1]["type"] == "done" and not any(e["type"] == "error" for e in events)
    assert c.api_calls == 1  # the tool round after the fallback did not hit the API again

    with SessionLocal() as s:  # the next turn, within 5 minutes, goes straight to rules mode
        user = s.query(User).filter_by(name="Dana").one()
        list(run_turn(s, user=user, conversation=None, text="כמה לידים יש?", image=None, client=c))
    assert c.api_calls == 1


def test_smart_reply_without_credit_gives_a_draft_and_a_clear_warning(client, logged_in):
    with SessionLocal() as s:
        lead = s.query(Lead).filter_by(name="מוסך הצפון").first()
        r = generate(s, lead, "מה המחיר לאתר בסיסי?", client=NoCreditClient(), user_id=None)
    assert r["engine"] == "rules" and r["reply"]
    assert "אין קרדיט" in r["warning"]


def test_friendly_message_is_hebrew_not_raw_json():
    assert "{" not in agent_module._friendly(_credit_error())
