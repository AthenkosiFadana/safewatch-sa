import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

"""POST /incidents — create a community incident report."""

import uuid
from datetime import datetime, timezone

from common import current_user, parse_body, response
from app.validation import validate_incident
from services import moderation, storage


def handler(event, context):
    user = current_user(event)
    if not user:
        return response(401, {"error": "Authentication required"})

    if moderation.rate_limited(user["userId"]):
        return response(429, {"error": "Report limit reached, try again later"})

    clean, errors = validate_incident(parse_body(event))
    if errors:
        return response(400, {"errors": errors})

    now = storage.utcnow()
    incident = {
        "incidentId": f"INC-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}",
        "userId": user["userId"],
        **clean,
        "status": "PENDING",
        "duplicateOf": None,
        "createdAt": now,
        "updatedAt": now,
    }
    storage.create_incident(incident)
    try:
        storage.log_report(user["userId"])
    except Exception:  # pragma: no cover - rate log is best-effort in serverless mode
        pass

    duplicates = moderation.find_duplicates(incident)
    moderation.mark_duplicates(incident, duplicates)
    moderation.evaluate_alerts()

    return response(201, {
        "incident": incident,
        "flaggedDuplicates": [d["incidentId"] for d in duplicates],
    })
