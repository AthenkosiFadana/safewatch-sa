"""GET /analytics — category, time-of-day, hotspot and trend aggregation."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common import response  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.routes.analytics import build_analytics  # noqa: E402
from services import storage  # noqa: E402


def handler(event, context):
    incidents = storage.list_incidents()
    return response(200, build_analytics(incidents))
