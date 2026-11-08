"""Integration tests: the API with the model replaced by a scripted fake."""
from app import agent as agent_module
from app.agent import ModelEvent, run_turn
from app.costs import Usage
from app.db import Conversation, Lead, LeadEvent, Message, Run, SessionLocal, User
from tests.conftest import read_sse


def test_health_ok(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_login_required_and_wrong_password(client):
    client.cookies.clear()
    assert client.get("/api/conversations").status_code == 401
    bad = client.post("/api/login", json={"name": "Eve", "password": "nope"})
    assert bad.status_code == 401
    assert client.post("/api/login", json={"name": "E", "password": "test-pass"}).status_code in (400, 422)


def test_chat_streams_text_and_saves_once(client, db, logged_in, fake):
    fake.turns.append([
        ModelEvent(type="text", text="יש 8 לידים "),
        ModelEvent(type="text", text="חמים היום."),
        ModelEvent(type="stop", stop_reason="end_turn", usage=Usage(120, 18),
                   content=[{"type": "text", "text": "יש 8 לידים חמים היום."}]),
    ])
    r = client.post("/api/chat", json={"message": "כמה לידים חמים יש?"})
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/event-stream")
    events = read_sse(r)
    kinds = [e["type"] for e in events]
    assert kinds[0] == "meta" and kinds[-1] == "done"
    assert "".join(e["text"] for e in events if e["type"] == "text") == "יש 8 לידים חמים היום."
    conv_id = events[0]["conversation_id"]
    msgs = db.query(Message).filter_by(conversation_id=conv_id).order_by(Message.id).all()
    assert [m.role for m in msgs] == ["user", "assistant"]
    assert msgs[1].content == "יש 8 לידים חמים היום."
    run = db.query(Run).filter_by(conversation_id=conv_id).one()
    assert run.status == "ok" and run.input_tokens == 120 and run.output_tokens == 18
    assert events[-1]["cost_usd"] == 0.0  # fake model has no price table


def test_tool_loop_updates_a_lead(client, db, logged_in, fake):
    lead = db.query(Lead).filter_by(name="רועי אברהם").first()
    tool_turn = [
        ModelEvent(type="text", text="מעדכן. "),
        ModelEvent(type="stop", stop_reason="tool_use", usage=Usage(300, 40), content=[
            {"type": "text", "text": "מעדכן. "},
            {"type": "tool_use", "id": "tu_1", "name": "update_lead",
             "input": {"lead_id": lead.id, "status": "call_scheduled", "append_note": "חזר אלינו, רוצה שיחה"}},
        ]),
    ]
    final_turn = [
        ModelEvent(type="text", text="עודכן: רועי – קבע שיחה."),
        ModelEvent(type="stop", stop_reason="end_turn", usage=Usage(420, 30),
                   content=[{"type": "text", "text": "עודכן: רועי – קבע שיחה."}]),
    ]
    fake.turns.extend([tool_turn, final_turn])
    events = read_sse(client.post("/api/chat", json={"message": "רועי אברהם חזר אלינו ורוצה שיחה"}))
    tools = [e for e in events if e["type"] == "tool"]
    assert [t["status"] for t in tools] == ["start", "done"] and tools[0]["name"] == "update_lead"
    assert "status" in tools[1]["summary"]
    db.refresh(lead)
    assert lead.status == "call_scheduled" and "רוצה שיחה" in lead.notes
    assert db.query(LeadEvent).filter_by(lead_id=lead.id, kind="status", actor="Dana").count() == 1
    run = db.query(Run).filter_by(conversation_id=events[0]["conversation_id"]).one()
    assert run.tool_calls == 1 and run.input_tokens == 720  # both model calls of the turn are summed


def test_refusal_is_reported_not_hidden(client, db, logged_in, fake):
    fake.turns.append([ModelEvent(type="stop", stop_reason="refusal", usage=Usage(50, 0), content=[])])
    events = read_sse(client.post("/api/chat", json={"message": "do something odd"}))
    assert any(e["type"] == "text" and "לא אוכל לעזור" in e["text"] for e in events)
    conv_id = events[0]["conversation_id"]
    assert db.query(Run).filter_by(conversation_id=conv_id).one().status == "refusal"


def test_dropped_connection_leaves_no_half_row(client, db, logged_in, fake):
    fake.turns.append([
        ModelEvent(type="text", text="This reply will be cut "),
        ModelEvent(type="text", text="in the middle."),
        ModelEvent(type="stop", stop_reason="end_turn", usage=Usage(10, 5), content=[{"type": "text", "text": "x"}]),
    ])
    with SessionLocal() as s:
        user = s.query(User).filter_by(name="Dana").one()
        gen = run_turn(s, user=user, conversation=None, text="cut me off", image=None, client=fake)
        meta = next(gen)
        first = next(gen)
        assert meta["type"] == "meta" and first["type"] == "text"
        gen.close()  # the browser went away
        conv_id = meta["conversation_id"]
    roles = [m.role for m in db.query(Message).filter_by(conversation_id=conv_id).all()]
    assert roles == ["user"]  # the user's message is kept, no partial assistant row
    run = db.query(Run).filter_by(conversation_id=conv_id).one()
    assert run.status == "aborted"


def test_image_message_carries_a_reference(client, db, logged_in, fake):
    import base64

    fake.turns.append([ModelEvent(type="stop", stop_reason="end_turn", usage=Usage(10, 2),
                                  content=[{"type": "text", "text": "Got the image."}])])
    png = base64.b64encode(b"\x89PNG\r\n\x1a\nfake").decode()
    events = read_sse(client.post("/api/chat", json={"message": "", "image": {"media_type": "image/png", "data": png}}))
    assert events[-1]["type"] == "done"
    sent = fake.last_messages[-1]["content"]
    assert sent[0]["type"] == "image" and sent[0]["source"]["media_type"] == "image/png"
    assert "image reference: img_" in sent[1]["text"]
    conv_id = events[0]["conversation_id"]
    user_msg = db.query(Message).filter_by(conversation_id=conv_id, role="user").one()
    assert user_msg.has_image is True and "[image img_" in user_msg.content


def test_system_prompt_is_filled(client, db):
    text = agent_module.build_system(db)[0]["text"]
    assert "LeadPilot" in text and "{{" not in text
    assert "סטודיו פיקסל" in text


def test_startup_prints_the_seed_report(client, capsys):
    # Issue #4: the deploy guide checks this line in the logs. The session's first start
    # already seeded, so this second start reports zeros, as a redeploy does.
    from fastapi.testclient import TestClient

    from app.main import app

    capsys.readouterr()
    with TestClient(app):
        pass
    assert "seed report: schema_version: 1, templates_seeded: 0, leads_seeded: 0" in capsys.readouterr().out


def test_digest_endpoint_needs_secret(client, logged_in):
    assert client.post("/internal/digest").status_code == 401
    r = client.post("/internal/digest", headers={"X-Cron-Secret": "cron-test"})
    assert r.status_code == 200
    assert r.json()["text"].startswith("LeadPilot —")
    assert r.json()["sent"] is False
