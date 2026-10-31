import os
from flask import Flask, jsonify, send_from_directory
from pydantic import ValidationError
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError

from backend.config import config_by_name
from backend.extensions import db, migrate
from backend import models  # Registers all models and immutability listeners
from backend.routes import ALL_BLUEPRINTS
from backend.utils import APIException

def create_app(config_name: str | None = None) -> Flask:
    """Application factory for EduFlow Backend."""
    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "development")

    app = Flask(__name__)
    config_obj = config_by_name.get(config_name, config_by_name["default"])
    app.config.from_object(config_obj)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # If running against SQLite (e.g. testing), enforce foreign keys strictly
    @event.listens_for(Engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        if dbapi_connection.__class__.__module__.startswith("sqlite3"):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    # CORS support for frontend clients
    @app.after_request
    def add_cors_headers(response):
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
        response.headers["Access-Control-Allow-Methods"] = "GET,PUT,POST,DELETE,OPTIONS"
        return response

    @app.route("/api/health", methods=["OPTIONS"])
    def options_health():
        return "", 200

    # Register blueprints
    for bp in ALL_BLUEPRINTS:
        app.register_blueprint(bp)

    # Static frontend serving
    frontend_dist = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "dist"))
    if os.path.exists(frontend_dist):
        @app.route("/", defaults={"path": ""})
        @app.route("/<path:path>")
        def serve_frontend(path):
            if path.startswith("api"):
                return jsonify({
                    "error": "The requested URL or resource was not found.",
                    "error_code": "ERR_NOT_FOUND"
                }), 404
            if path and os.path.exists(os.path.join(frontend_dist, path)):
                return send_from_directory(frontend_dist, path)
            return send_from_directory(frontend_dist, "index.html")

    # Register error handlers
    @app.errorhandler(APIException)
    def handle_api_exception(exc: APIException):
        response = {
            "error": exc.message,
            "error_code": exc.error_code,
        }
        if exc.details:
            response["details"] = exc.details
        return jsonify(response), exc.status_code

    @app.errorhandler(ValidationError)
    def handle_validation_error(exc: ValidationError):
        return jsonify({
            "error": "Request validation failed",
            "error_code": "ERR_VALIDATION",
            "details": exc.errors()
        }), 422

    @app.errorhandler(IntegrityError)
    def handle_integrity_error(exc: IntegrityError):
        db.session.rollback()
        return jsonify({
            "error": "Database constraint violation or duplicate key",
            "error_code": "ERR_INTEGRITY",
            "details": str(exc.orig) if hasattr(exc, "orig") else str(exc)
        }), 409

    @app.errorhandler(404)
    def handle_not_found(exc):
        return jsonify({
            "error": "The requested URL or resource was not found.",
            "error_code": "ERR_NOT_FOUND"
        }), 404

    @app.errorhandler(405)
    def handle_method_not_allowed(exc):
        return jsonify({
            "error": "HTTP method not allowed for this endpoint.",
            "error_code": "ERR_METHOD_NOT_ALLOWED"
        }), 405

    @app.shell_context_processor
    def make_shell_context():
        return {
            "db": db,
            **{m.__name__: m for m in models.ALL_MODELS}
        }

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=app.config.get("DEBUG", False))
