"""SQLite storage layer.

Locally we model the same document shape that the DynamoDB table
`SafeWatchIncidents` uses in AWS (see infrastructure/template.yaml), so the
data can be moved between backends without changing the API contract.
"""

import json
import sqlite3
from datetime import datetime, timezone

SCHEMA = """
CREATE TABLE IF NOT EXISTS incidents (
    incident_id   TEXT PRIMARY KEY,
    user_id       TEXT NOT NULL,
    category      TEXT NOT NULL,
    description   TEXT NOT NULL,
    latitude      REAL,
    longitude     REAL,
    area          TEXT NOT NULL,
    severity      TEXT NOT NULL,
    status        TEXT NOT NULL,
    source        TEXT NOT NULL DEFAULT 'COMMUNITY',
    image_url     TEXT,
    duplicate_of  TEXT,
    created_at    TEXT NOT NULL,
    updated_at    TEXT NOT NULL,
    raw           TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS users (
    user_id        TEXT PRIMARY KEY,
    email          TEXT NOT NULL UNIQUE,
    name           TEXT NOT NULL,
    password_hash  TEXT NOT NULL,
    community      TEXT NOT NULL DEFAULT '',
    role           TEXT NOT NULL DEFAULT 'MEMBER',
    created_at     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS alerts (
    alert_id     TEXT PRIMARY KEY,
    area         TEXT NOT NULL,
    category     TEXT NOT NULL,
    incident_ids TEXT NOT NULL,
    message      TEXT NOT NULL,
    status       TEXT NOT NULL DEFAULT 'ACTIVE',
    created_at   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS report_log (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_incidents_area ON incidents(area);
CREATE INDEX IF NOT EXISTS idx_incidents_category ON incidents(category);
CREATE INDEX IF NOT EXISTS idx_incidents_created ON incidents(created_at);
"""


def utcnow() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class Database:
    def __init__(self, path: str):
        self.path = path

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def init(self):
        with self.connect() as conn:
            conn.executescript(SCHEMA)

    # -- incidents -------------------------------------------------------
    def insert_incident(self, item: dict) -> dict:
        with self.connect() as conn:
            conn.execute(
                """INSERT INTO incidents
                   (incident_id, user_id, category, description, latitude, longitude,
                    area, severity, status, source, image_url, duplicate_of,
                    created_at, updated_at, raw)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    item["incidentId"], item["userId"], item["category"], item["description"],
                    item.get("latitude"), item.get("longitude"), item["area"],
                    item["severity"], item["status"], item.get("source", "COMMUNITY"),
                    item.get("imageUrl"), item.get("duplicateOf"),
                    item["createdAt"], item["updatedAt"], json.dumps(item),
                ),
            )
        return item

    def get_incident(self, incident_id: str):
        with self.connect() as conn:
            row = conn.execute("SELECT raw FROM incidents WHERE incident_id=?", (incident_id,)).fetchone()
        return json.loads(row["raw"]) if row else None

    def list_incidents(self, filters: dict | None = None) -> list[dict]:
        filters = filters or {}
        query = "SELECT raw FROM incidents"
        clauses, params = [], []
        for field in ("category", "severity", "status", "area", "userId", "source"):
            if filters.get(field):
                clauses.append(f"json_extract(raw, '$.{field}') = ?")
                params.append(filters[field])
        if filters.get("since"):
            clauses.append("created_at >= ?")
            params.append(filters["since"])
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY created_at DESC"
        with self.connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [json.loads(r["raw"]) for r in rows]

    def update_incident(self, incident_id: str, updates: dict):
        item = self.get_incident(incident_id)
        if not item:
            return None
        item.update(updates)
        item["updatedAt"] = utcnow()
        with self.connect() as conn:
            conn.execute(
                """UPDATE incidents SET category=?, description=?, latitude=?, longitude=?,
                   area=?, severity=?, status=?, image_url=?, duplicate_of=?,
                   updated_at=?, raw=? WHERE incident_id=?""",
                (
                    item["category"], item["description"], item.get("latitude"),
                    item.get("longitude"), item["area"], item["severity"], item["status"],
                    item.get("imageUrl"), item.get("duplicateOf"), item["updatedAt"],
                    json.dumps(item), incident_id,
                ),
            )
        return item

    def delete_incident(self, incident_id: str) -> bool:
        with self.connect() as conn:
            cur = conn.execute("DELETE FROM incidents WHERE incident_id=?", (incident_id,))
        return cur.rowcount > 0

    # -- users ------------------------------------------------------------
    def insert_user(self, user: dict) -> dict:
        with self.connect() as conn:
            conn.execute(
                """INSERT INTO users (user_id, email, name, password_hash, community, role, created_at)
                   VALUES (?,?,?,?,?,?,?)""",
                (user["userId"], user["email"], user["name"], user["passwordHash"],
                 user.get("community", ""), user.get("role", "MEMBER"), user["createdAt"]),
            )
        return user

    def get_user_by_email(self, email: str):
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM users WHERE email=?", (email.lower(),)).fetchone()
        return dict(row) if row else None

    def get_user(self, user_id: str):
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()
        return dict(row) if row else None

    def update_user(self, user_id: str, updates: dict):
        allowed = {k: v for k, v in updates.items() if k in ("name", "community", "password_hash")}
        if not allowed:
            return self.get_user(user_id)
        cols = ", ".join(f"{k}=?" for k in allowed)
        with self.connect() as conn:
            conn.execute(f"UPDATE users SET {cols} WHERE user_id=?", (*allowed.values(), user_id))
        return self.get_user(user_id)

    # -- alerts -----------------------------------------------------------
    def insert_alert(self, alert: dict) -> dict:
        with self.connect() as conn:
            conn.execute(
                """INSERT INTO alerts (alert_id, area, category, incident_ids, message, status, created_at)
                   VALUES (?,?,?,?,?,?,?)""",
                (alert["alertId"], alert["area"], alert["category"],
                 json.dumps(alert["incidentIds"]), alert["message"], alert["status"], alert["createdAt"]),
            )
        return alert

    def list_alerts(self, area: str | None = None) -> list[dict]:
        query = "SELECT * FROM alerts"
        params = []
        if area:
            query += " WHERE area=?"
            params.append(area)
        query += " ORDER BY created_at DESC"
        with self.connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [
            {
                "alertId": r["alert_id"], "area": r["area"], "category": r["category"],
                "incidentIds": json.loads(r["incident_ids"]), "message": r["message"],
                "status": r["status"], "createdAt": r["created_at"],
            }
            for r in rows
        ]

    def report_count_since(self, user_id: str, since_iso: str) -> int:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT COUNT(*) AS c FROM report_log WHERE user_id=? AND created_at>=?",
                (user_id, since_iso),
            ).fetchone()
        return row["c"]

    def log_report(self, user_id: str):
        with self.connect() as conn:
            conn.execute("INSERT INTO report_log (user_id, created_at) VALUES (?,?)", (user_id, utcnow()))
