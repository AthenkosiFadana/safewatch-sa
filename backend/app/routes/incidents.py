import uuid
from datetime import datetime, timezone

from flask import Blueprint, g, jsonify, request

from app.auth import token_required
from app.validation import CATEGORIES, SEVERITIES, STATUSES, validate_incident
from services import storage
from services import moderation

incident_routes = Blueprint("incident_routes", __name__)

# Incident status workflow: PENDING -> UNDER_REVIEW -> VERIFIED -> RESOLVED
#                                 \-> REJECTED
NEXT_STATUSES = {
    "PENDING": ("UNDER_REVIEW", "REJECTED"),
    "UNDER_REVIEW": ("VERIFIED", "REJECTED"),
    "VERIFIED": ("RESOLVED", "UNDER_REVIEW"),
    "RESOLVED": (),
    "REJECTED": (),
}


@incident_routes.get("/api/incidents")
def list_incidents():
    filters = {
        key: request.args[key]
        for key in ("category", "severity", "status", "area", "source")
        if request.args.get(key)
    }
    if request.args.get("since"):
        filters["since"] = request.args["since"]
    items = storage.list_incidents(filters)
    return jsonify({"incidents": items, "count": len(items)})


@incident_routes.get("/api/incidents/<incident_id>")
def get_incident(incident_id):
    item = storage.get_incident(incident_id)
    if not item:
        return jsonify({"error": "Incident not found"}), 404
    return jsonify({"incident": item})


@incident_routes.post("/api/incidents")
@token_required()
def create_incident():
    payload = request.get_json(silent=True) or {}
    clean, errors = validate_incident(payload)
    if errors:
        return jsonify({"errors": errors}), 400

    if moderation.rate_limited(g.user_id):
        return jsonify({"error": "Report limit reached, try again later"}), 429

    now = storage.utcnow()
    incident = {
        "incidentId": f"INC-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}",
        "userId": g.user_id,
        **clean,
        "status": "PENDING",
        "duplicateOf": None,
        "createdAt": now,
        "updatedAt": now,
    }
    storage.create_incident(incident)
    storage.get_db().log_report(g.user_id)

    duplicates = moderation.find_duplicates(incident)
    moderation.mark_duplicates(incident, duplicates)
    if duplicates:
        incident["duplicateOf"] = min(duplicates, key=lambda i: i["createdAt"])["incidentId"]

    moderation.evaluate_alerts()
    return jsonify({"incident": incident, "flaggedDuplicates": [d["incidentId"] for d in duplicates]}), 201


@incident_routes.put("/api/incidents/<incident_id>")
@token_required()
def update_incident(incident_id):
    existing = storage.get_incident(incident_id)
    if not existing:
        return jsonify({"error": "Incident not found"}), 404
    if g.user_role != "ADMIN" and existing["userId"] != g.user_id:
        return jsonify({"error": "You may only edit your own reports"}), 403

    payload = request.get_json(silent=True) or {}
    allowed = {}
    if payload.get("description") is not None or payload.get("category") is not None:
        merged = {**existing, **payload}
        clean, errors = validate_incident(merged)
        if errors:
            return jsonify({"errors": errors}), 400
        allowed.update(clean)
    if payload.get("severity") and payload["severity"].upper() in SEVERITIES:
        allowed["severity"] = payload["severity"].upper()

    updated = storage.update_incident(incident_id, allowed)
    return jsonify({"incident": updated})


@incident_routes.put("/api/incidents/<incident_id>/status")
@token_required(roles=("ADMIN",))
def moderate_incident(incident_id):
    existing = storage.get_incident(incident_id)
    if not existing:
        return jsonify({"error": "Incident not found"}), 404

    payload = request.get_json(silent=True) or {}
    status = str(payload.get("status", "")).upper()
    if status not in STATUSES:
        return jsonify({"error": f"status must be one of {', '.join(STATUSES)}"}), 400
    if status not in NEXT_STATUSES.get(existing["status"], ()) and status != existing["status"]:
        return jsonify({"error": f"cannot move from {existing['status']} to {status}"}), 409

    updated = storage.update_incident(incident_id, {"status": status})
    return jsonify({"incident": updated})


@incident_routes.delete("/api/incidents/<incident_id>")
@token_required(roles=("ADMIN",))
def delete_incident(incident_id):
    if not storage.delete_incident(incident_id):
        return jsonify({"error": "Incident not found"}), 404
    return jsonify({"deleted": incident_id})


@incident_routes.get("/api/meta/taxonomy")
def taxonomy():
    return jsonify({"categories": list(CATEGORIES), "severities": list(SEVERITIES), "statuses": list(STATUSES)})
