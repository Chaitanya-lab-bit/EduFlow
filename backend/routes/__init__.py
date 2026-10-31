from flask import Blueprint, jsonify

from backend.routes.courses import courses_bp
from backend.routes.learners import learners_bp
from backend.routes.enrollments import enrollments_bp
from backend.routes.assignments import assignments_bp
from backend.routes.submissions import submissions_bp
from backend.routes.grades import grades_bp
from backend.routes.feedback import feedback_bp
from backend.routes.resubmissions import resubmissions_bp
from backend.routes.appeals import appeals_bp
from backend.routes.dashboard import dashboard_bp

health_bp = Blueprint("health", __name__)

@health_bp.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "healthy",
        "service": "EduFlow Backend",
        "database_layer": "PostgreSQL (SQLAlchemy 2.x)",
        "phase": "Phase 4 - Flask REST API"
    }), 200

ALL_BLUEPRINTS = [
    health_bp,
    courses_bp,
    learners_bp,
    enrollments_bp,
    assignments_bp,
    submissions_bp,
    grades_bp,
    feedback_bp,
    resubmissions_bp,
    appeals_bp,
    dashboard_bp,
]

__all__ = [
    "health_bp",
    "courses_bp",
    "learners_bp",
    "enrollments_bp",
    "assignments_bp",
    "submissions_bp",
    "grades_bp",
    "feedback_bp",
    "resubmissions_bp",
    "appeals_bp",
    "dashboard_bp",
    "ALL_BLUEPRINTS",
]
