"""Shared helper for AWS Lambda handlers.

Each handler is a thin HTTP adapter around the same service code used by the
local Flask API, so behaviour stays identical between local development and
API Gateway + Lambda in AWS.
"""

import json
import os
import sys
from datetime import datetime, timezone

BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)


def response(status_code: int, body: dict, headers: dict | None = None) -> dict:
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
            **(headers or {}),
        },
        "body": json.dumps(body),
    )


def parse_body(event: dict) -> dict:
    raw = event.get("body") or "{}"
    if event.get("isBase64Encoded"):
        import base64

        raw = base64.b64decode(raw).decode("utf-8")
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


def path_param(event: dict, name: str) -> str | None:
    return (event.get("pathParameters") or {}).get(name)


def utcnow() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def current_user(event: dict) -> dict | None:
    """Read the Cognito/IAM authoriser claims attached by API Gateway."""
    ctx = event.get("requestContext") or {}
    identity = ctx.get("authorizer") or ctx.get("identity") or {}
    claims = identity.get("claims") or identity
    sub = claims.get("sub") or claims.get("user_id")
    if not sub:
        return None
    return {"userId": sub, "role": claims.get("role", "MEMBER")}
