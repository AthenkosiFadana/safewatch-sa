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

    return DynamoStorage(Config.AWS_REGION, Config.DYNAMODB_TABLE)


def use_dynamodb() -> bool:
    return Config.STORAGE_BACKEND == "dynamodb"


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


__all__ = [
    "init_db", "get_db", "utcnow", "create_incident", "get_incident",
    "list_incidents", "update_incident", "delete_incident", "use_dynamodb",
]
