"""Unit tests for validation and moderation logic (no HTTP layer)."""

from datetime import datetime, timedelta, timezone

from app.validation import validate_email, validate_incident, validate_password
from services import moderation


VALID = {
    "category": "ROBBERY",
    "description": "Armed robbery reported at a spaza shop on the corner",
    "area": "New Brighton",
    "severity": "CRITICAL",
    "latitude": -33.8866,
    "longitude": 25.5817,
}


def test_valid_incident_passes():
    clean, errors = validate_incident(VALID)
    assert errors == []
    assert clean["category"] == "ROBBERY"
    assert clean["severity"] == "CRITICAL"


def test_category_and_severity_are_normalised():
    clean, errors = validate_incident({**VALID, "category": "theft", "severity": "high"})
    assert errors == []
    assert clean["category"] == "THEFT"
    assert clean["severity"] == "HIGH"


def test_coordinates_must_be_in_south_africa():
    _, errors = validate_incident({**VALID, "latitude": 40.7, "longitude": -74.0})
    assert any("South Africa" in e for e in errors)


def test_missing_coordinates_rejected():
    payload = {k: v for k, v in VALID.items() if k not in ("latitude", "longitude")}
    _, errors = validate_incident(payload)
    assert any("latitude" in e for e in errors)


def test_short_description_rejected():
    _, errors = validate_incident({**VALID, "description": "stolen"})
    assert any("10 characters" in e for e in errors)


def test_email_and_password_rules():
    assert validate_email("person@example.co.za") is None
    assert validate_email("nope") is not None
    assert validate_password("longenough") is None
    assert validate_password("short") is not None


def test_duplicate_detection_uses_area_category_and_window():
    now = datetime.now(timezone.utc)
    iso = now.isoformat().replace("+00:00", "Z")
    recent = {
        "incidentId": "INC-OLD",
        "area": "Korsten",
        "category": "THEFT",
        "createdAt": (now - timedelta(minutes=5)).isoformat().replace("+00:00", "Z"),
    }
    old = {
        "incidentId": "INC-ANCIENT",
        "area": "Korsten",
        "category": "THEFT",
        "createdAt": (now - timedelta(days=3)).isoformat().replace("+00:00", "Z"),
    }
    other_area = {
        "incidentId": "INC-ELSEWHERE",
        "area": "Motherwell",
        "category": "THEFT",
        "createdAt": iso,
    }

    class FakeDb:
        def list_incidents(self, filters=None):
            return [recent, old, other_area]

    class FakeStorage:
        def __init__(self):
            self.db = FakeDb()

        def list_incidents(self, filters=None):
            return self.db.list_incidents(filters)

    original = moderation.storage
    moderation.storage = FakeStorage()
    try:
        candidate = {
            "incidentId": "INC-NEW",
            "area": "Korsten",
            "category": "THEFT",
            "createdAt": iso,
        }
        matches = moderation.find_duplicates(candidate, window_minutes=15)
        assert [m["incidentId"] for m in matches] == ["INC-OLD"]
    finally:
        moderation.storage = original
