from flask import Blueprint, jsonify, request

from app.auth import token_required
from services import moderation, storage

alert_routes = Blueprint("alert_routes", __name__)


@alert_routes.get("/api/alerts")
def list_alerts():
    area = request.args.get("area")
    return jsonify({"alerts": storage.get_db().list_alerts(area)})


@alert_routes.post("/api/alerts/check")
@token_required()
def check_alerts():
    """Evaluate the last 2 hours of incidents and create any cluster alerts."""
    created = moderation.evaluate_alerts()
    return jsonify({"created": created, "count": len(created)})


@alert_routes.post("/api/alerts")
@token_required(roles=("ADMIN",))
def create_alert():
    payload = request.get_json(silent=True) or {}
    area = str(payload.get("area", "")).strip()
    message = str(payload.get("message", "")).strip()
    if not area or not message:
        return jsonify({"error": "area and message are required"}), 400

    import uuid
    from datetime import datetime, timezone

    alert = {
        "alertId": f"ALT-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:4].upper()}",
        "area": area[:80],
        "category": str(payload.get("category", "OTHER")).upper()[:40],
        "incidentIds": payload.get("incidentIds", []),
        "message": message[:500],
        "status": "ACTIVE",
        "createdAt": storage.utcnow(),
    }
    storage.get_db().insert_alert(alert)
    from services.notifications import publish_alert

    publish_alert(alert)
    return jsonify({"alert": alert}), 201
