"""Input validation for user supplied data (first line of API security)."""

import re

CATEGORIES = (
    "THEFT", "ROBBERY", "ASSAULT", "VANDALISM", "SUSPICIOUS_ACTIVITY",
    "MISSING_PERSON", "ROAD_INCIDENT", "FIRE", "OTHER",
)
SEVERITIES = ("LOW", "MEDIUM", "HIGH", "CRITICAL")
STATUSES = ("PENDING", "UNDER_REVIEW", "VERIFIED", "RESOLVED", "REJECTED")
SOURCES = ("COMMUNITY", "SAPS_OFFICIAL", "DEMO")

# Rough bounding box for South Africa — keeps junk coordinates out of the map
SA_LAT_MIN, SA_LAT_MAX = -35.0, -22.0
SA_LON_MIN, SA_LON_MAX = 16.0, 33.0

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MAX_DESCRIPTION = 1000


def validate_email(value: str) -> str | None:
    value = (value or "").strip().lower()
    if not EMAIL_RE.match(value) or len(value) > 254:
        return "A valid email address is required"
    return None


def validate_password(value: str) -> str | None:
    if not value or len(value) < 8:
        return "Password must be at least 8 characters"
    if len(value) > 128:
        return "Password must be less than 128 characters"
    return None


def validate_incident(payload: dict) -> tuple[dict | None, list[str]]:
    errors: list[str] = []
    clean: dict = {}

    category = str(payload.get("category", "")).strip().upper()
    if category not in CATEGORIES:
        errors.append(f"category must be one of {', '.join(CATEGORIES)}")
    clean["category"] = category

    description = str(payload.get("description", "")).strip()
    if len(description) < 10:
        errors.append("description must be at least 10 characters")
    elif len(description) > MAX_DESCRIPTION:
        errors.append(f"description must be less than {MAX_DESCRIPTION} characters")
    clean["description"] = description

    area = str(payload.get("area", "")).strip()
    if not area or len(area) > 80:
        errors.append("area is required and must be under 80 characters")
    clean["area"] = area

    severity = str(payload.get("severity", "")).strip().upper()
    if severity not in SEVERITIES:
        errors.append(f"severity must be one of {', '.join(SEVERITIES)}")
    clean["severity"] = severity

    lat = payload.get("latitude")
    lon = payload.get("longitude")
    if lat is None or lon is None:
        errors.append("latitude and longitude are required")
    else:
        try:
            lat, lon = float(lat), float(lon)
        except (TypeError, ValueError):
            errors.append("latitude and longitude must be numbers")
        else:
            if not (SA_LAT_MIN <= lat <= SA_LAT_MAX and SA_LON_MIN <= lon <= SA_LON_MAX):
                errors.append("coordinates must fall within South Africa")
            clean["latitude"], clean["longitude"] = lat, lon

    source = str(payload.get("source", "COMMUNITY")).strip().upper()
    if source not in SOURCES:
        errors.append(f"source must be one of {', '.join(SOURCES)}")
    clean["source"] = source

    image_url = payload.get("imageUrl")
    if image_url:
        image_url = str(image_url)
        if not (image_url.startswith("https://") or image_url.startswith("/")):
            errors.append("imageUrl must be an https URL or an app path")
        clean["imageUrl"] = image_url[:300]

    if errors:
        return None, errors
    return clean, []
