"""Storage facade.

Routes talk to this module only, so switching between the local SQLite
development database and Amazon DynamoDB in AWS is a configuration change
(STORAGE_BACKEND=sqlite|dynamodb), not a code change.
"""

from app.config import Config
from app.db import Database, utcnow

_db = Database(Config.DATABASE_PATH)


def init_db():
    _db.init()


def get_db() -> Database:
    return _db


def _dynamo():
    from services.dynamodb import DynamoStorage

    return DynamoStorage(Config.AWS_REGION, Config.DYNAMODB_TABLE, Config.USERS_TABLE, Config.ALERTS_TABLE)


def use_dynamodb() -> bool:
    return Config.STORAGE_BACKEND == "dynamodb"


# -- incidents ------------------------------------------------------------
def create_incident(item: dict) -> dict:
    if use_dynamodb():
        return _dynamo().put_incident(item)
    return _db.insert_incident(item)


def get_incident(incident_id: str):
    if use_dynamodb():
        return _dynamo().get_incident(incident_id)
    return _db.get_incident(incident_id)


def list_incidents(filters: dict | None = None) -> list[dict]:
    if use_dynamodb():
        return _dynamo().list_incidents(filters)
    return _db.list_incidents(filters)


def update_incident(incident_id: str, updates: dict):
    if use_dynamodb():
        return _dynamo().update_incident(incident_id, updates)
    return _db.update_incident(incident_id, updates)


def delete_incident(incident_id: str) -> bool:
    if use_dynamodb():
        return _dynamo().delete_incident(incident_id)
    return _db.delete_incident(incident_id)


# -- users ----------------------------------------------------------------
def insert_user(user: dict) -> dict:
    """`user` uses camelCase keys; storage rows are snake_case."""
    if use_dynamodb():
        row = {
            "user_id": user["userId"],
            "email": user["email"].lower(),
            "name": user["name"],
            "password_hash": user["passwordHash"],
            "community": user.get("community", ""),
            "role": user.get("role", "MEMBER"),
            "created_at": user["createdAt"],
        }
        return _dynamo().put_user(row)
    return _db.insert_user(user)


def get_user(user_id: str):
    if use_dynamodb():
        return _dynamo().get_user(user_id)
    return _db.get_user(user_id)


def get_user_by_email(email: str):
    if use_dynamodb():
        return _dynamo().get_user_by_email(email.lower())
    return _db.get_user_by_email(email)


def update_user(user_id: str, updates: dict):
    if use_dynamodb():
        return _dynamo().update_user(user_id, updates)
    return _db.update_user(user_id, updates)


# -- alerts ---------------------------------------------------------------
def insert_alert(alert: dict) -> dict:
    if use_dynamodb():
        import json

        item = dict(alert)
        item["incident_ids"] = json.dumps(alert.get("incidentIds", []))
        item.pop("incidentIds", None)
        return _dynamo().put_alert(item)
    return _db.insert_alert(alert)


def list_alerts(area: str | None = None) -> list[dict]:
    if use_dynamodb():
        import json

        rows = _dynamo().list_alerts(area)
        return [
            {
                "alertId": r.get("alertId"),
                "area": r.get("area"),
                "category": r.get("category"),
                "incidentIds": json.loads(r.get("incident_ids", "[]")),
                "message": r.get("message"),
                "status": r.get("status"),
                "createdAt": r.get("createdAt"),
            }
            for r in rows
        ]
    return _db.list_alerts(area)


# -- report rate limiting (audit log is best-effort) -----------------------
def log_report(user_id: str):
    if use_dynamodb():
        return  # incident records themselves are the source of truth in DynamoDB
    _db.log_report(user_id)


def reports_since(user_id: str, since_iso: str) -> int:
    """Count a user's reports in a window (works on both backends)."""
    return len(list_incidents({"userId": user_id, "since": since_iso}))


__all__ = [
    "init_db", "get_db", "utcnow", "create_incident", "get_incident",
    "list_incidents", "update_incident", "delete_incident", "use_dynamodb",
    "insert_user", "get_user", "get_user_by_email", "update_user",
    "insert_alert", "list_alerts", "log_report", "reports_since",
]
