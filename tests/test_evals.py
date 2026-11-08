"""The eval runner's own plumbing, with the fake model: no network, no cost."""
from app.agent import FakeModelClient
from evals import run as evals_run


def test_case_history_reaches_the_model_as_earlier_turns(client):
    fake = FakeModelClient()
    case = {"id": "t", "input": "ומה עם כרטיסי טיסה?",
            "history": [{"role": "user", "content": "כמה לידים חמים יש?"},
                        {"role": "assistant", "content": "יש 8 לידים חמים, בראשם אורי כהן."}]}
    result = evals_run.run_case(case, fake)
    sent = fake.last_messages
    assert [m["role"] for m in sent] == ["user", "assistant", "user"]
    assert sent[0]["content"] == "כמה לידים חמים יש?"
    assert "אורי כהן" in sent[1]["content"]
    assert sent[2]["content"][-1]["text"] == "ומה עם כרטיסי טיסה?"
    assert result["status"] == "ok"


def test_case_without_history_is_a_single_turn(client):
    fake = FakeModelClient()
    evals_run.run_case({"id": "t", "input": "מה לטפל היום?"}, fake)
    assert [m["role"] for m in fake.last_messages] == ["user"]
