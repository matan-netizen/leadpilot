"""Smart reply: the rules engine, the model path (fake) and the API around it."""
from app.db import Lead, LeadEvent, Run
from app.smart_reply import classify, rules_reply


def test_classify_intents():
    assert classify("כמה זה עולה?") == "price"
    assert classify("אני עדיין מתלבט, המחיר גבוה לי") == "hesitation"
    assert classify("אפשר לדבר מחר ב-10?") == "schedule"
    assert classify("לא מעוניין תודה") == "not_interested"
    assert classify("מעולה, איך מתקדמים?") == "interest"


def test_rules_reply_uses_first_name_and_suggests_status(client, db):
    lead = db.query(Lead).filter_by(name="אורי כהן").first()
    r = rules_reply(db, lead, "מה המחיר?")
    assert r["reply"].startswith("היי אורי") and r["intent"] == "price" and r["engine"] == "rules"
    business = db.query(Lead).filter_by(name="מוסך הצפון").first()
    assert business and rules_reply(db, business, "מה המחיר?")["reply"].startswith("היי,")  # no "היי מוסך"


def test_smart_reply_endpoint_with_model(client, db, logged_in, fake):
    lead = db.query(Lead).filter_by(name="דוד מזרחי").first()
    fake.completions.append('```json\n{"reply": "היי דוד, מה הכי מעכב?", "intent": "hesitation", "suggested_status": "hesitating", "summary": "מתלבט"}\n```')
    r = client.post(f"/api/leads/{lead.id}/smart-reply", json={"tone": "friendly"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["reply"] == "היי דוד, מה הכי מעכב?" and body["engine"] == "ai"
    assert body["suggested_status"] == "hesitating"
    assert "אני עדיין מתלבט" in fake.last_messages[0]["content"]  # the lead's last message reached the model
    assert db.query(Run).filter_by(tool_names="smart_reply").count() >= 1


def test_bad_model_output_falls_back_to_rules(client, db, logged_in, fake):
    lead = db.query(Lead).filter_by(name="מוסך הצפון").first()
    fake.completions.append("sorry, no json here")
    body = client.post(f"/api/leads/{lead.id}/smart-reply", json={}).json()
    assert body["engine"] == "rules" and body["warning"] and body["reply"]


def test_sent_marks_replied_and_applies_status(client, db, logged_in):
    lead = db.query(Lead).filter_by(name="מאפיית השכונה").first()
    assert lead.replied is False
    r = client.post(f"/api/leads/{lead.id}/sent", json={"reply": "תודה! זה לוקח שבועיים", "status": "call_scheduled"})
    assert r.status_code == 200
    data = r.json()
    assert data["needs_reply"] is False and data["status"] == "call_scheduled"
    kinds = {e.kind for e in db.query(LeadEvent).filter_by(lead_id=lead.id).all()}
    assert {"ai_reply", "status"} <= kinds


def test_new_incoming_message_reopens_the_lead(client, db, logged_in, fake):
    lead = db.query(Lead).filter_by(name="יוסי לוי").first()
    r = client.post(f"/api/leads/{lead.id}/smart-reply", json={"incoming": "אפשר להזיז את השיחה?"})
    assert r.status_code == 200
    db.refresh(lead)
    assert lead.last_incoming == "אפשר להזיז את השיחה?" and lead.replied is False
