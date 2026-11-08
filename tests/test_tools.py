"""Unit tests: phone rules, flags, metrics and the lead tools. Deterministic, no model."""
import json
from datetime import timedelta

import pytest

from app.db import Lead, LeadEvent, utcnow
from app.leads_meta import compute_metrics, format_phone, is_hot, is_stale, normalize_phone, stage_of
from app.tools import registry
from app.tools.leads import create_lead, get_lead, leads_overview, search_leads, update_lead


@pytest.mark.parametrize("raw,norm", [
    ("050-482-1937", "972504821937"), ("972 50-482-1937", "972504821937"), ("+972-0504821937", "972504821937"),
    ("504821937", "972504821937"), ("03-612-4478", "97236124478"), ("436609622344", "436609622344"), ("", ""),
])
def test_normalize_phone(raw, norm):
    assert normalize_phone(raw) == norm


def test_format_phone():
    assert format_phone("972504821937") == "050-482-1937"
    assert format_phone("97236124478") == "03-612-4478"
    assert format_phone("436609622344") == "+436609622344"


def _lead(**kw):
    base = dict(phone="050", phone_norm="972500000000", name="", status=None, first_attempt="", second_attempt="",
                last_update="", notes="", last_incoming="", replied=True, created_at=utcnow(), updated_at=utcnow())
    base.update(kw)
    return Lead(**base)


def test_hot_rules():
    assert is_hot(_lead(status="callback"))
    assert is_hot(_lead(status="sent_intro", notes="ליד חם!"))
    assert not is_hot(_lead(status="sent_intro", notes="חמישי בבוקר"))  # "חם" only as a whole word
    assert not is_hot(_lead(status="closed", notes="מאוד מעוניין"))  # won leads are not "hot"


def test_stale_only_for_active_stages():
    old = utcnow() - timedelta(days=5)
    assert is_stale(_lead(status="info_sent", updated_at=old), utcnow())
    assert not is_stale(_lead(status="no_response", updated_at=old), utcnow())
    assert stage_of(None) == "new" and stage_of("unknown") == "new"


def test_metrics_counts_duplicates_and_rates():
    leads = [_lead(id=1, status="closed", phone_norm="972500000008"), _lead(id=2, status="not_interested", phone_norm="972500000009"), _lead(id=3, phone_norm="972500000001"),
             _lead(id=4, status="sent_intro", phone_norm="972500000001")]
    m = compute_metrics(leads, utcnow())
    assert m["total"] == 4 and m["won"] == 1 and m["lost"] == 1
    assert m["conversion_rate"] == 0.25 and m["win_rate"] == 0.5
    assert m["no_status"] == 1 and list(m["duplicates"].values()) == [[3, 4]]


def test_seed_loaded(client, db):
    o = leads_overview(db)
    assert o["total"] >= 32 and o["waiting_reply"] >= 1
    assert "050-482-1937" in o["duplicates"]  # the seed has one deliberate duplicate pair


def test_search_by_phone_in_any_format(client, db):
    for q in ("0504821937", "972-50-482", "482-1937"):
        r = search_leads(db, query=q)
        assert r["count"] >= 1, q
        assert all(l["phone_display"] == "050-482-1937" for l in r["leads"])


def test_search_filters(client, db):
    hot = search_leads(db, hot_only=True, limit=50)
    assert hot["count"] > 0 and all(l["hot"] for l in hot["leads"])
    waiting = search_leads(db, needs_reply_only=True, limit=50)
    assert all(l["needs_reply"] for l in waiting["leads"])
    assert search_leads(db, stage="nope")["error"].startswith("unknown stage")


def test_create_lead_dedups_by_normalised_phone(client, db):
    first = create_lead(db, phone="058-111-2233", name="בדיקה")
    again = create_lead(db, phone="+972 58 111 2233")
    assert first["created"] is True
    assert again == {"created": False, "reason": "duplicate", "id": first["id"], "name": "בדיקה"}
    assert create_lead(db, phone="12")["error"] == "phone number looks invalid"


def test_update_lead_logs_activity(client, db):
    lid = create_lead(db, phone="058-111-9999", name="עדכון")["id"]
    r = update_lead(db, lead_id=lid, status="offer_sent", append_note="נשלחה הצעה")
    assert r["updated"] == ["status", "notes"]
    kinds = [e.kind for e in db.query(LeadEvent).filter_by(lead_id=lid).all()]
    assert kinds == ["created", "status", "note"]
    assert update_lead(db, lead_id=lid, status="bad")["error"].startswith("unknown status")
    card = get_lead(db, lead_id=lid)
    assert card["stage"] == "closing" and card["recommended_template"]["lead_type"] == "לקראת סגירה"


def test_registry_survives_bad_input(client, db):
    out = json.loads(registry.execute("get_lead", {"lead_id": 999999}, db))
    assert "error" in out
    assert "unknown tool" in json.loads(registry.execute("drop_table", {}, db))["error"]
