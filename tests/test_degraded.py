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
    text = account_problem(_credit_error())
    assert "קרדיט" in text and "מקור: תשלום" in text and "זו לא תקלה במערכת" in text
    assert account_problem(ValueError("x")) is None


def test_chat_falls_back_to_rules_without_credit(client, logged_in):
    c = NoCreditClient()
    with SessionLocal() as s:
        user = s.query(User).filter_by(name="Dana").one()
        events = list(run_turn(s, user=user, conversation=None, text="מה לטפל היום?", image=None, client=c))
    text = "".join(e["text"] for e in events if e["type"] == "text")
    assert "קרדיט" in text and "זו לא תקלה במערכת" in text and "חמים לטיפול" in text  # explained once, then answered
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
    assert "קרדיט" in r["warning"] and "זו לא תקלה במערכת" in r["warning"] and r["error_code"] == "no_credit"


def test_friendly_message_is_hebrew_not_raw_json():
    assert "{" not in agent_module._friendly(_credit_error())


def test_status_badge_reports_the_reason(client, logged_in):
    c = NoCreditClient()
    c.last_error = None
    assert c.status() == {"ok": True}
    with SessionLocal() as s:
        user = s.query(User).filter_by(name="Dana").one()
        list(run_turn(s, user=user, conversation=None, text="כמה לידים יש?", image=None, client=c))
    st = c.status()
    assert st["ok"] is False and st["code"] == "no_credit" and st["source"] == "תשלום"


def test_every_error_names_its_source():
    import httpx
    from app.errors import explain

    req = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
    resp = lambda code: httpx.Response(code, request=req)  # noqa: E731
    cases = {
        "bad_key": anthropic.AuthenticationError("invalid x-api-key", response=resp(401), body=None),
        "no_permission": anthropic.PermissionDeniedError("forbidden", response=resp(403), body=None),
        "model_not_found": anthropic.NotFoundError("model not found", response=resp(404), body=None),
        "rate_limited": anthropic.RateLimitError("rate limited", response=resp(429), body=None),
        "anthropic_down": anthropic.InternalServerError("boom", response=resp(500), body=None),
        "overloaded": anthropic.APIStatusError("Overloaded", response=resp(529), body=None),
        "no_connection": anthropic.APIConnectionError(request=req),
        "internal": ValueError("our bug"),
    }
    for code, exc in cases.items():
        info = explain(exc)
        assert info.code == code, (code, info.code)
        assert "מקור:" in info.text()
        assert info.not_a_bug == (code != "internal")
