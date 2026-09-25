"""Amazon DynamoDB storage backend.

Used when STORAGE_BACKEND=dynamodb. The table design matches
infrastructure/template.yaml:

    SafeWatchIncidents
      PK: incidentId   (string)
      GSI: area-createdAt-index  -> hotspot queries
      GSI: status-index           -> admin open/verified queries
"""

from datetime import datetime, timezone


def utcnow() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class DynamoStorage:
    def __init__(self, region: str, table_name: str):
        import boto3  # imported lazily so local development needs no AWS creds

        self.table_name = table_name
        self.dynamodb = boto3.resource("dynamodb", region_name=region)
        self.table = self.dynamodb.Table(table_name)

    # -- incidents -------------------------------------------------------
    def put_incident(self, item: dict) -> dict:
        self.table.put_item(Item=item)
        return item

    def get_incident(self, incident_id: str):
        res = self.table.get_item(Key={"incidentId": incident_id})
        return res.get("Item")

    def list_incidents(self, filters: dict | None = None) -> list[dict]:
        filters = filters or {}
        if filters.get("area"):
            res = self.table.query(
                IndexName="area-createdAt-index",
                KeyConditionExpression="area = :a",
                ExpressionAttributeValues={":a": filters["area"]},
            )
            items = res.get("Items", [])
        elif filters.get("status"):
            res = self.table.query(
                IndexName="status-index",
                KeyConditionExpression="#s = :s",
                ExpressionAttributeNames={"#s": "status"},
                ExpressionAttributeValues={":s": filters["status"]},
            )
            items = res.get("Items", [])
        else:
            items = []
            paginator = self.table.get_paginator("scan")
            for page in paginator.paginate():
                items.extend(page.get("Items", []))

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
            names[f"#{key}"] = key
            values[f":{key}"] = value
            expr.append(f"#{key} = :{key}")
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
        return res.get("Attributes")

    def delete_incident(self, incident_id: str) -> bool:
        try:
            self.table.delete_item(
                Key={"incidentId": incident_id},
                ConditionExpression="attribute_exists(incidentId)",
            )
        except self.dynamodb.meta.client.exceptions.ConditionalCheckFailedException:
            return False
        return True
