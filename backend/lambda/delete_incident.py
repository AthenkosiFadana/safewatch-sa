import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

"""DELETE /incidents/{id} — admin only."""

from common import current_user, path_param, response
from services import storage


def handler(event, context):
    user = current_user(event)
    if not user:
        return response(401, {"error": "Authentication required"})
    if user.get("role") != "ADMIN":
        return response(403, {"error": "Admin role required"})

    incident_id = path_param(event, "id")
    if not storage.delete_incident(incident_id):
        return response(404, {"error": "Incident not found"})
    return response(200, {"deleted": incident_id})
