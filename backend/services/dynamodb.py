"""Amazon DynamoDB storage backend.

Used when STORAGE_BACKEND=dynamodb. The table design matches
infrastructure/template.yaml:

    SafeWatchIncidents
      PK: incidentId   (string)
      GSI: area-createdAt-index  -> hotspot queries
      GSI: status-index          -> admin open/verified queries

    SafeWatchUsers
      PK: userId       (string)
      GSI: email-index -> login lookup

    SafeWatchAlerts
      PK: alertId      (string)
"""

from datetime import datetime, timezone
from decimal import Decimal


def utcnow() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _to_dynamo(value):
    """DynamoDB has no float type — numbers arrive as Decimal."""
    if isinstance(value, float):
        return Decimal(str(value))
    if isinstance(value, dict):
        return {k: _to_dynamo(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_to_dynamo(v) for v in value]
    return value


def _from_dynamo(value):
    """Turn Decimal back into int/float so Flask can serialise JSON."""
    if isinstance(value, Decimal):
        return int(value) if value % 1 == 0 else float(value)
    if isinstance(value, dict):
        return {k: _from_dynamo(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_from_dynamo(v) for v in value]
    return value


def _clean(item: dict) -> dict:
    """DynamoDB rejects null values, so drop them before writing."""
    return {k: v for k, v in _to_dynamo(item).items() if v is not None}


class DynamoStorage:
    def __init__(self, region: str, table_name: str, users_table: str = "", alerts_table: str = ""):
        import boto3  # imported lazily so local development needs no AWS creds

        self.table_name = table_name
        self.dynamodb = boto3.resource("dynamodb", region_name=region)
        self.table = self.dynamodb.Table(table_name)
        self.users_table = self.dynamodb.Table(users_table) if users_table else None
        self.alerts_table = self.dynamodb.Table(alerts_table) if alerts_table else None

    # -- incidents -------------------------------------------------------
    @staticmethod
    def _scan(table) -> list[dict]:
        """Full table scan (the resource API has no paginator)."""
        items: list[dict] = []
        kwargs = {}
        while True:
            res = table.scan(**kwargs)
            items.extend(res.get("Items", []))
            if "LastEvaluatedKey" not in res:
                return items
            kwargs["ExclusiveStartKey"] = res["LastEvaluatedKey"]

    def put_incident(self, item: dict) -> dict:
        self.table.put_item(Item=_clean(item))
        return item

    def get_incident(self, incident_id: str):
        res = self.table.get_item(Key={"incidentId": incident_id})
        return _from_dynamo(res.get("Item"))

    def list_incidents(self, filters: dict | None = None) -> list[dict]:
        filters = filters or {}
        if filters.get("area"):
            res = self.table.query(
                IndexName="area-createdAt-index",
                KeyConditionExpression="area = :a",
                ExpressionAttributeValues={":a": filters["area"]},
            )
            items = _from_dynamo(res.get("Items", []))
        elif filters.get("status"):
            res = self.table.query(
                IndexName="status-index",
                KeyConditionExpression="#s = :s",
                ExpressionAttributeNames={"#s": "status"},
                ExpressionAttributeValues={":s": filters["status"]},
            )
            items = _from_dynamo(res.get("Items", []))
        else:
            items = _from_dynamo(self._scan(self.table))

        for field in ("category", "severity", "userId", "source"):
            if filters.get(field):
                items = [i for i in items if i.get(field) == filters[field]]
        if filters.get("since"):
            items = [i for i in items if i.get("createdAt", "") >= filters["since"]]
        items.sort(key=lambda i: i.get("createdAt", ""), reverse=True)
        return items

    def update_incident(self, incident_id: str, updates: dict):
        expr, names, values = [], {}, {}
        for key, value in updates.items():
            if value is None:
                continue
            names[f"#{key}"] = key
            values[f":{key}"] = value
            expr.append(f"#{key} = :{key}")
        if not expr:
            return self.get_incident(incident_id)
        names["#updatedAt"] = "updatedAt"
        values[":updatedAt"] = utcnow()
        expr.append("#updatedAt = :updatedAt")
        try:
            res = self.table.update_item(
                Key={"incidentId": incident_id},
                UpdateExpression="SET " + ", ".join(expr),
                ExpressionAttributeNames=names,
                ExpressionAttributeValues=values,
                ConditionExpression="attribute_exists(incidentId)",
                ReturnValues="ALL_NEW",
            )
        except self.dynamodb.meta.client.exceptions.ConditionalCheckFailedException:
            return None
        return _from_dynamo(res.get("Attributes"))

    def delete_incident(self, incident_id: str) -> bool:
        try:
            self.table.delete_item(
                Key={"incidentId": incident_id},
                ConditionExpression="attribute_exists(incidentId)",
            )
        except self.dynamodb.meta.client.exceptions.ConditionalCheckFailedException:
            return False
        return True

    # -- users -------------------------------------------------------------
    def put_user(self, user: dict) -> dict:
        if not self.users_table:
            raise RuntimeError("USERS_TABLE is not configured")
        self.users_table.put_item(Item=_clean(user))
        return user

    def get_user(self, user_id: str):
        if not self.users_table:
            return None
        res = self.users_table.get_item(Key={"user_id": user_id})
        return _from_dynamo(res.get("Item"))

    def get_user_by_email(self, email: str):
        if not self.users_table:
            return None
        res = self.users_table.query(
            IndexName="email-index",
            KeyConditionExpression="email = :e",
            ExpressionAttributeValues={":e": email.lower()},
            Limit=1,
        )
        items = _from_dynamo(res.get("Items", []))
        return items[0] if items else None

    def update_user(self, user_id: str, updates: dict):
        updates = {k: v for k, v in updates.items() if v is not None}
        if not updates:
            return self.get_user(user_id)
        expr, names, values = [], {}, {}
        for key, value in updates.items():
            names[f"#{key}"] = key
            values[f":{key}"] = value
            expr.append(f"#{key} = :{key}")
        res = self.users_table.update_item(
            Key={"user_id": user_id},
            UpdateExpression="SET " + ", ".join(expr),
            ExpressionAttributeNames=names,
            ExpressionAttributeValues=values,
            ReturnValues="ALL_NEW",
        )
        return _from_dynamo(res.get("Attributes"))

    # -- alerts ------------------------------------------------------------
    def put_alert(self, alert: dict) -> dict:
        if not self.alerts_table:
            raise RuntimeError("ALERTS_TABLE is not configured")
        self.alerts_table.put_item(Item=_clean(alert))
        return alert

    def list_alerts(self, area: str | None = None) -> list[dict]:
        if not self.alerts_table:
            return []
        items = _from_dynamo(self._scan(self.alerts_table))
        if area:
            items = [a for a in items if a.get("area") == area]
        items.sort(key=lambda a: a.get("createdAt", ""), reverse=True)
        return items
