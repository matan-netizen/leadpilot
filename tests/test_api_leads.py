"""The leads REST API: auth, list, create, patch, duplicates."""


def test_leads_need_login(client):
    client.cookies.clear()
    assert client.get("/api/leads").status_code == 401


def test_list_and_meta(client, logged_in):
    meta = client.get("/api/meta").json()
    assert len(meta["statuses"]) == 12 and len(meta["stages"]) == 6 and meta["ai"] == "fake"
    leads = client.get("/api/leads").json()["leads"]
    assert len(leads) >= 32
    assert {"phone_display", "stage", "hot", "stale", "needs_reply", "duplicate"} <= set(leads[0])
    assert any(l["duplicate"] for l in leads)


def test_create_patch_and_duplicate(client, logged_in):
    r = client.post("/api/leads", json={"phone": "052-999-0001", "name": "API", "source": "אתר"})
    assert r.status_code == 201
    lead = r.json()
    assert lead["phone_display"] == "052-999-0001" and lead["status"] == "sent_intro"
    assert client.post("/api/leads", json={"phone": "972529990001"}).status_code == 409
    p = client.patch(f"/api/leads/{lead['id']}", json={"status": "closed", "notes": "שולם"}).json()
    assert p["stage"] == "won" and p["paid"] is True
    assert [a["kind"] for a in p["activity"]][:2] == ["edit", "status"]
    c = client.patch(f"/api/leads/{lead['id']}", json={"clear_status": True}).json()
    assert c["status"] is None and c["status_label"] == "ללא סטטוס"
    assert client.patch(f"/api/leads/{lead['id']}", json={"status": "bogus"}).status_code == 400
    assert client.get("/api/leads/999999").status_code == 404


def test_overview_matches_list(client, logged_in):
    o = client.get("/api/overview").json()
    leads = client.get("/api/leads").json()["leads"]
    assert o["total"] == len(leads)
    assert o["hot"] == sum(l["hot"] for l in leads)
