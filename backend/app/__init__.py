import logging
import os
import sys

from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_cors import CORS

load_dotenv()

# Ensure the backend root (app/ and services/) is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import Config  # noqa: E402
from services.storage import init_db  # noqa: E402


def create_app(config_overrides: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)
    if config_overrides:
        app.config.update(config_overrides)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    CORS(app, resources={r"/api/*": {"origins": app.config.get("CORS_ORIGINS", "*")}})

    app.config["SECRET_KEY"] = Config.SECRET_KEY
    app.config["TOKEN_EXPIRES_MINUTES"] = Config.TOKEN_EXPIRES_MINUTES

    init_db()

    from app.routes.admin import admin_routes
    from app.routes.alerts import alert_routes
    from app.routes.analytics import analytics_routes
    from app.routes.auth_routes import auth_routes
    from app.routes.incidents import incident_routes

    app.register_blueprint(auth_routes)
    app.register_blueprint(incident_routes)
    app.register_blueprint(alert_routes)
    app.register_blueprint(analytics_routes)
    app.register_blueprint(admin_routes)

    @app.get("/api/health")
    def health():
        return jsonify({
            "status": "ok",
            "service": "safewatch-api",
            "storage": app.config.get("STORAGE_BACKEND", "sqlite"),
        })

    @app.errorhandler(404)
    def not_found(_e):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(405)
    def method_not_allowed(_e):
        return jsonify({"error": "Method not allowed"}), 405

    @app.errorhandler(500)
    def server_error(_e):
        logging.exception("Unhandled server error")
        return jsonify({"error": "Internal server error"}), 500

    return app
