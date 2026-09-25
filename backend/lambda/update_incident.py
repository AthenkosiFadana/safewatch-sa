import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

"""PUT /incidents/{id} (owner edit) and PUT /incidents/{id}/status (moderation)."""

from common import current_user, parse_body, path_param, response
from app.validation import SEVERITIES, STATUSES, validate_incident
from services import storage

NEXT_STATUSES = {
    "PENDING": ("UNDER_REVIEW", "REJECTED"),
    "UNDER_REVIEW": ("VERIFIED", "REJECTED"),
    "VERIFIED": ("RESOLVED", "UNDER_REVIEW"),
    "RESOLVED": (),
    "REJECTED": (),
}


def handler(event, context):
    user = current_user(event)
    if not user:
        return response(401, {"error": "Authentication required"})

    incident_id = path_param(event, "id")
    existing = storage.get_incident(incident_id)
    if not existing:
        return response(404, {"error": "Incident not found"})

    payload = parse_body(event)
    resource = event.get("resource", "")

    # Moderation transition (admin only)
    if resource.endswith("/status"):
        if user.get("role") != "ADMIN":
            return response(403, {"error": "Admin role required"})
        status = str(payload.get("status", "")).upper()
        if status not in STATUSES:
            return response(400, {"error": f"status must be one of {', '.join(STATUSES)}"})
        if status not in NEXT_STATUSES.get(existing["status"], ()) and status != existing["status"]:
            return response(409, {"error": f"cannot move from {existing['status']} to {status}"})
        return response(200, {"incident": storage.update_incident(incident_id, {"status": status})})

    # Owner edit
    if user.get("role") != "ADMIN" and existing["userId"] != user["userId"]:
        return response(403, {"error": "You may only edit your own reports"})

    merged = {**existing, **payload}
    clean, errors = validate_incident(merged)
    if errors:
        return response(400, {"errors": errors})
    if str(payload.get("severity", "")).upper() in SEVERITIES:
        clean["severity"] = payload["severity"].upper()
    return response(200, {"incident": storage.update_incident(incident_id, clean)})
