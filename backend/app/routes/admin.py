from collections import Counter
from datetime import datetime, timedelta, timezone

from flask import Blueprint, jsonify

from app.auth import token_required
from services import storage

admin_routes = Blueprint("admin_routes", __name__)


@admin_routes.get("/api/admin/stats")
@token_required(roles=("ADMIN",))
def stats():
    incidents = storage.list_incidents()
    active = [i for i in incidents if i["status"] != "REJECTED"]
    by_category = Counter(i["category"] for i in active)
    total = len(incidents) or 1

    return jsonify({
        "totalIncidents": len(incidents),
        "openIncidents": len([i for i in incidents if i["status"] in ("PENDING", "UNDER_REVIEW")]),
        "resolvedIncidents": len([i for i in incidents if i["status"] == "RESOLVED"]),
        "verifiedIncidents": len([i for i in incidents if i["status"] == "VERIFIED"]),
        "rejectedIncidents": len([i for i in incidents if i["status"] == "REJECTED"]),
        "duplicateFlagged": len([i for i in incidents if i.get("duplicateOf")]),
        "activeAlerts": len([a for a in storage.get_db().list_alerts() if a["status"] == "ACTIVE"]),
        "categoryBreakdown": [
            {"category": c, "count": n, "percent": round(n * 100 / total, 1)}
            for c, n in by_category.most_common()
        ],
        "pendingQueue": sorted(
            [i for i in incidents if i["status"] in ("PENDING", "UNDER_REVIEW")],
            key=lambda i: i["createdAt"],
        )[:25],
    })


@admin_routes.get("/api/admin/reports")
@token_required(roles=("ADMIN",))
def reports():
    """Simple abuse report: users with the most reports in the last 24h."""
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat().replace("+00:00", "Z")
    incidents = [i for i in storage.list_incidents() if i["createdAt"] >= cutoff]
    counts = Counter(i["userId"] for i in incidents)
    return jsonify([
        {"userId": uid, "reports24h": n, "flagged": n >= 5}
        for uid, n in counts.most_common(50)
    ])
