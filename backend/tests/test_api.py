"""API tests: authentication, incidents, moderation, alerts, analytics."""


def test_health(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json["status"] == "ok"


def test_register_and_login(client):
    res = client.post("/api/auth/register", json={
        "name": "New User",
        "email": "newuser@test.local",
        "password": "Password123",
        "community": "Korsten",
    })
    assert res.status_code == 201
    assert res.json["user"]["role"] == "MEMBER"

    res = client.post("/api/auth/login", json={"email": "newuser@test.local", "password": "Password123"})
    assert res.status_code == 200
    assert "token" in res.json

    bad = client.post("/api/auth/login", json={"email": "newuser@test.local", "password": "wrong"})
    assert bad.status_code == 401


def test_register_validation(client):
    res = client.post("/api/auth/register", json={"name": "", "email": "not-an-email", "password": "123"})
    assert res.status_code == 400
    assert res.json["errors"]


def test_incident_requires_auth(client, sample_incident):
    res = client.post("/api/incidents", json=sample_incident)
    assert res.status_code == 401


def test_create_incident(client, member, sample_incident):
    res = client.post("/api/incidents", json=sample_incident, headers=member)
    assert res.status_code == 201
    incident = res.json["incident"]
    assert incident["status"] == "PENDING"
    assert incident["source"] == "COMMUNITY"
    assert incident["incidentId"].startswith("INC-")

    fetched = client.get(f"/api/incidents/{incident['incidentId']}")
    assert fetched.status_code == 200
    assert fetched.json["incident"]["category"] == "THEFT"


def test_create_incident_validation(client, member, sample_incident):
    bad = {**sample_incident, "category": "NOT_A_CATEGORY", "latitude": 51.5, "longitude": -0.1}
    res = client.post("/api/incidents", json=bad, headers=member)
    assert res.status_code == 400
    assert len(res.json["errors"]) >= 2

    short = {**sample_incident, "description": "no"}
    res = client.post("/api/incidents", json=short, headers=member)
    assert res.status_code == 400


def test_duplicate_flagging(client, member):
    payload = {
        "category": "VANDALISM",
        "description": "Streetlight vandalised on the corner of Main Road",
        "area": "Summerstrand",
        "severity": "LOW",
        "latitude": -33.9953,
        "longitude": 25.6478,
    }
    first = client.post("/api/incidents", json=payload, headers=member)
    second = client.post("/api/incidents", json=payload, headers=member)
    assert first.status_code == 201 and second.status_code == 201
    assert second.json["flaggedDuplicates"]
    assert second.json["incident"]["duplicateOf"]


def test_list_and_filter(client, member, sample_incident):
    client.post("/api/incidents", json=sample_incident, headers=member)
    all_res = client.get("/api/incidents")
    assert all_res.status_code == 200
    assert all_res.json["count"] >= 1

    filtered = client.get("/api/incidents?category=VANDALISM")
    assert filtered.status_code == 200
    assert all(i["category"] == "VANDALISM" for i in filtered.json["incidents"])


def test_member_cannot_moderate(client, member, sample_incident):
    created = client.post("/api/incidents", json=sample_incident, headers=member).json["incident"]
    res = client.put(f"/api/incidents/{created['incidentId']}/status",
                     json={"status": "VERIFIED"}, headers=member)
    assert res.status_code == 403


def test_admin_moderation_workflow(client, admin, member, sample_incident):
    created = client.post("/api/incidents", json=sample_incident, headers=member).json["incident"]
    incident_id = created["incidentId"]

    for status, expected in (("UNDER_REVIEW", "UNDER_REVIEW"), ("VERIFIED", "VERIFIED"), ("RESOLVED", "RESOLVED")):
        res = client.put(f"/api/incidents/{incident_id}/status", json={"status": status}, headers=admin)
        assert res.status_code == 200, res.get_json()
        assert res.json["incident"]["status"] == expected

    # Invalid transition: RESOLVED is terminal
    res = client.put(f"/api/incidents/{incident_id}/status", json={"status": "PENDING"}, headers=admin)
    assert res.status_code == 409


def test_owner_can_edit_but_not_others(client, member, sample_incident):
    created = client.post("/api/incidents", json=sample_incident, headers=member).json["incident"]
    res = client.put(f"/api/incidents/{created['incidentId']}",
                     json={**sample_incident, "description": "Edited description by the owner"},
                     headers=member)
    assert res.status_code == 200
    assert "Edited description" in res.json["incident"]["description"]


def test_analytics_shape(client, member, sample_incident):
    client.post("/api/incidents", json=sample_incident, headers=member)
    res = client.get("/api/analytics")
    assert res.status_code == 200
    data = res.json
    for key in ("total", "byCategory", "bySeverity", "hotspots", "timeBuckets", "byHour", "trend"):
        assert key in data
    assert data["total"] >= 1
    assert data["hotspots"][0]["area"]


def test_admin_stats(client, admin, member, sample_incident):
    client.post("/api/incidents", json=sample_incident, headers=member)
    res = client.get("/api/admin/stats", headers=admin)
    assert res.status_code == 200
    assert res.json["totalIncidents"] >= 1
    assert "pendingQueue" in res.json
    assert "categoryBreakdown" in res.json


def test_member_blocked_from_admin(client, member):
    assert client.get("/api/admin/stats", headers=member).status_code == 403


def test_alert_endpoints(client, admin, member):
    assert client.get("/api/alerts").status_code == 200
    res = client.post("/api/alerts", json={"area": "Korsten", "message": "Test alert"}, headers=admin)
    assert res.status_code == 201
    assert client.get("/api/alerts?area=Korsten").json["alerts"]

    assert client.post("/api/alerts", json={"area": "x", "message": "y"}).status_code == 401


def test_taxonomies(client):
    res = client.get("/api/meta/taxonomy")
    assert res.status_code == 200
    assert "THEFT" in res.json["categories"]
    assert "CRITICAL" in res.json["severities"]


def test_404(client):
    assert client.get("/api/incidents/DOES-NOT-EXIST").status_code == 404
