import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

"""POST /alerts/check and POST /alerts — cluster alert detection + SNS publish."""

import uuid
from datetime import datetime, timezone

from common import current_user, parse_body, response
from services import moderation, storage
from services.notifications import publish_alert


def handler(event, context):
    user = current_user(event)
    if not user:
        return response(401, {"error": "Authentication required"})

    payload = parse_body(event)

    # Manual admin alert
    if payload.get("message"):
        if user.get("role") != "ADMIN":
            return response(403, {"error": "Admin role required"})
        area = str(payload.get("area", "")).strip()
        if not area:
            return response(400, {"error": "area is required"})
        alert = {
            "alertId": f"ALT-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:4].upper()}",
            "area": area[:80],
            "category": str(payload.get("category", "OTHER")).upper()[:40],
            "incidentIds": payload.get("incidentIds", []),
            "message": str(payload.get("message", ""))[:500],
            "status": "ACTIVE",
            "createdAt": storage.utcnow(),
        }
        storage.insert_alert(alert)
        publish_alert(alert)
        return response(201, {"alert": alert})

    created = moderation.evaluate_alerts()
    return response(200, {"created": created, "count": len(created)})
