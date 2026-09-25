"""Report moderation: rate limits, duplicate detection and alert generation.

This is the anti-abuse layer that stops the platform being flooded with fake
reports, and the engine behind community safety alerts.
"""

from datetime import datetime, timedelta, timezone

from app.config import Config
from services import storage


ALERT_THRESHOLD = 3  # incidents in one area within 2 hours triggers an alert


def _parse(iso: str) -> datetime:
    return datetime.fromisoformat(iso.replace("Z", "+00:00"))


def rate_limited(user_id: str) -> bool:
    since = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat().replace("+00:00", "Z")
    try:
        return storage.reports_since(user_id, since) >= Config.RATE_LIMIT_PER_HOUR
    except Exception:  # pragma: no cover - rate check is best-effort in serverless mode
        return False


def find_duplicates(candidate: dict, window_minutes: int | None = None) -> list[dict]:
    """Reports in the same area with the same category inside the time window."""
    window = window_minutes or Config.DUPLICATE_WINDOW_MINUTES
    cutoff = (_parse(candidate["createdAt"]) - timedelta(minutes=window)).isoformat().replace("+00:00", "Z")
    matches = storage.list_incidents({"area": candidate["area"], "category": candidate["category"]})
    return [
        m for m in matches
        if m["incidentId"] != candidate["incidentId"]
        and m["createdAt"] >= cutoff
        and m["area"] == candidate["area"]
        and m["category"] == candidate["category"]
    ]


def mark_duplicates(candidate: dict, duplicates: list[dict]):
    if not duplicates:
        return
    primary = min(duplicates, key=lambda i: i["createdAt"])
    storage.update_incident(candidate["incidentId"], {"duplicateOf": primary["incidentId"]})
    for other in duplicates:
        if other["incidentId"] != primary["incidentId"] and not other.get("duplicateOf"):
            storage.update_incident(other["incidentId"], {"duplicateOf": primary["incidentId"]})


def _cluster_alerts(incidents: list[dict]) -> list[dict]:
    """Group recent incidents by area and surface clusters as safety alerts."""
    now = datetime.now(timezone.utc)
    window_start = (now - timedelta(hours=2)).isoformat().replace("+00:00", "Z")
    by_area: dict[str, list[dict]] = {}
    for inc in incidents:
        if inc["status"] in ("REJECTED", "RESOLVED"):
            continue
        if inc["createdAt"] >= window_start:
            by_area.setdefault(inc["area"], []).append(inc)

    alerts = []
    for area, items in by_area.items():
        if len(items) < ALERT_THRESHOLD:
            continue
        counts: dict[str, int] = {}
        for i in items:
            counts[i["category"]] = counts.get(i["category"], 0) + 1
        primary = max(counts, key=counts.get)
        alerts.append({
            "area": area,
            "category": primary,
            "incidentIds": [i["incidentId"] for i in items],
            "message": (
                "Multiple incidents have been reported in your area within the last 2 hours. "
                "Please exercise caution."
            ),
        })
    return alerts


def evaluate_alerts() -> list[dict]:
    """Create (and publish) an alert for any area with 3+ recent incidents."""
    recent = storage.list_incidents({"since": (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat().replace("+00:00", "Z")})
    existing = {(a["area"], a["createdAt"][:13]) for a in storage.list_alerts()}
    created = []
    from services.notifications import publish_alert

    for alert in _cluster_alerts(recent):
        hour_key = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H")
        if (alert["area"], hour_key) in existing:
            continue
        record = {
            "alertId": f"ALT-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{len(alert['area'])}",
            "area": alert["area"],
            "category": alert["category"],
            "incidentIds": alert["incidentIds"],
            "message": alert["message"],
            "status": "ACTIVE",
            "createdAt": storage.utcnow(),
        }
        storage.insert_alert(record)
        publish_alert(record)
        created.append(record)
    return created
