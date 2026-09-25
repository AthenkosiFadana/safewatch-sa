import uuid
from datetime import datetime, timezone

from flask import Blueprint, current_app, jsonify, request

from app.auth import hash_password, token_required, verify_password
from app.validation import validate_email, validate_password
from services import storage

auth_routes = Blueprint("auth_routes", __name__)


def _public_user(row: dict) -> dict:
    return {
        "userId": row["user_id"],
        "email": row["email"],
        "name": row["name"],
        "community": row["community"],
        "role": row["role"],
        "createdAt": row["created_at"],
    }


@auth_routes.post("/api/auth/register")
def register():
    payload = request.get_json(silent=True) or {}
    errors = [e for e in (validate_email(payload.get("email")), validate_password(payload.get("password"))) if e]
    name = str(payload.get("name", "")).strip()
    if not name or len(name) > 80:
        errors.append("name is required and must be under 80 characters")
    if errors:
        return jsonify({"errors": errors}), 400
    if storage.get_user_by_email(payload["email"]):
        return jsonify({"errors": ["An account with this email already exists"]}), 409

    user = storage.insert_user({
        "userId": f"USR-{uuid.uuid4().hex[:10].upper()}",
        "email": payload["email"].strip().lower(),
        "name": name,
        "passwordHash": hash_password(payload["password"]),
        "community": str(payload.get("community", "")).strip()[:80],
        "role": "MEMBER",
        "createdAt": storage.utcnow(),
    })
    row = storage.get_user(user.get("userId") or user["user_id"])
    return jsonify({"user": _public_user(row)}), 201


@auth_routes.post("/api/auth/login")
def login():
    payload = request.get_json(silent=True) or {}
    row = storage.get_user_by_email(str(payload.get("email", "")))
    if not row or not verify_password(str(payload.get("password", "")), row["password_hash"]):
        return jsonify({"error": "Invalid email or password"}), 401

    from flask import current_app, g
    from app.auth import create_token

    token = create_token(row["user_id"], row["role"], current_app.config["SECRET_KEY"], current_app.config["TOKEN_EXPIRES_MINUTES"])
    return jsonify({"token": token, "user": _public_user(row)})


@auth_routes.get("/api/auth/me")
@token_required()
def me():
    from flask import current_app, g

    row = storage.get_user(g.user_id)
    if not row:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"user": _public_user(row)})


@auth_routes.put("/api/auth/profile")
@token_required()
def update_profile():
    from flask import current_app, g

    payload = request.get_json(silent=True) or {}
    updates = {}
    if payload.get("name"):
        updates["name"] = str(payload["name"]).strip()[:80]
    if payload.get("community") is not None:
        updates["community"] = str(payload["community"]).strip()[:80]
    if payload.get("password"):
        error = validate_password(payload["password"])
        if error:
            return jsonify({"errors": [error]}), 400
        updates["password_hash"] = hash_password(payload["password"])

    row = storage.update_user(g.user_id, updates)
    return jsonify({"user": _public_user(row)})


@auth_routes.get("/api/users/me/incidents")
@token_required()
def my_incidents():
    from flask import current_app, g

    return jsonify({"incidents": storage.list_incidents({"userId": g.user_id})})
