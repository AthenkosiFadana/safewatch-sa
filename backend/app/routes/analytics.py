"""Crime analytics: category splits, time-of-day patterns, hotspots, trends."""

from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone

from flask import Blueprint, jsonify

from services import storage

analytics_routes = Blueprint("analytics_routes", __name__)

TIME_BUCKETS = (
    ("00:00 - 06:00", 0, 6),
    ("06:00 - 12:00", 6, 12),
    ("12:00 - 18:00", 12, 18),
    ("18:00 - 00:00", 18, 24),
)


def _parse(iso: str) -> datetime:
    return datetime.fromisoformat(iso.replace("Z", "+00:00"))


def _percent(counter: Counter) -> list[dict]:
    total = sum(counter.values()) or 1
    return [
        {"key": key, "count": count, "percent": round(count * 100 / total, 1)}
        for key, count in counter.most_common()
    ]


def build_analytics(incidents: list[dict]) -> dict:
    verified = [i for i in incidents if i.get("status") != "REJECTED"]

    by_category = Counter(i["category"] for i in verified)
    by_severity = Counter(i["severity"] for i in verified)
    by_status = Counter(i["status"] for i in verified)
    by_area = Counter(i["area"] for i in verified)
    by_source = Counter(i.get("source", "COMMUNITY") for i in verified)

    by_hour = Counter()
    by_time_bucket = Counter()
    by_day = Counter()
    for i in verified:
        ts = _parse(i["createdAt"])
        by_hour[ts.strftime("%H:00")] += 1
        by_day[ts.strftime("%a")] += 1
        for label, start, end in TIME_BUCKETS:
            if start <= ts.hour < end:
                by_time_bucket[label] += 1
                break

    window = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat().replace("+00:00", "Z")
    trend = defaultdict(int)
    for i in verified:
        if i["createdAt"] >= window:
            trend[_parse(i["createdAt"]).strftime("%a %d %b")] += 1

    return {
        "total": len(verified),
        "byCategory": _percent(by_category),
        "bySeverity": _percent(by_severity),
        "byStatus": _percent(by_status),
        "bySource": _percent(by_source),
        "hotspots": [
            {"area": area, "count": count}
            for area, count in by_area.most_common(10)
        ],
        "timeBuckets": [
            {
                "label": label,
                "count": by_time_bucket.get(label, 0),
                "percent": round(by_time_bucket.get(label, 0) * 100 / (len(verified) or 1), 1),
            }
            for label, _, _ in TIME_BUCKETS
        ],
        "byHour": [{"hour": f"{h:02d}:00", "count": by_hour.get(f"{h:02d}:00", 0)} for h in range(24)],
        "trend": [{"day": day, "count": count} for day, count in sorted(trend.items())],
    }


@analytics_routes.get("/api/analytics")
def analytics():
    incidents = storage.list_incidents()
    return jsonify(build_analytics(incidents))
