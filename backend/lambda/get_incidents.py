import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

"""GET /incidents and GET /incidents/{id}."""

from common import path_param, response
from services import storage


def handler(event, context):
    incident_id = path_param(event, "id")
    filters = {
        key: value
        for key, value in (event.get("queryStringParameters") or {}).items()
        if key in ("category", "severity", "status", "area", "source", "since") and value
    }

    if incident_id:
        incident = storage.get_incident(incident_id)
        if not incident:
            return response(404, {"error": "Incident not found"})
        return response(200, {"incident": incident})

    items = storage.list_incidents(filters)
    return response(200, {"incidents": items, "count": len(items)})
