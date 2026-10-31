"""
Feedback and Mentoring REST API endpoints.
"""
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify

from backend.extensions import db
from backend.models.grade import Grade
from backend.models.submission import Submission
from backend.models.feedback import Feedback
from backend.models.enums import FeedbackVisibility
from backend.schemas import FeedbackCreateSchema
from backend.utils import (
    serialize_model, paginate_query, generate_id, validate_payload, EntityNotFoundException
)

feedback_bp = Blueprint("feedback", __name__, url_prefix="/api/feedback")

@feedback_bp.route("", methods=["POST"])
def add_feedback():
    """Add instructor qualitative feedback for a graded submission."""
    data = request.get_json(silent=True) or {}
    schema = validate_payload(FeedbackCreateSchema, data)
    
    grade = db.session.get(Grade, schema.grade_id)
    if not grade:
        raise EntityNotFoundException(f"Grade '{schema.grade_id}' not found.")
        
    submission_id = schema.submission_id or grade.submission_id
    submission = db.session.get(Submission, submission_id)
    if not submission:
        raise EntityNotFoundException(f"Submission '{submission_id}' not found.")
        
    feedback_id = schema.feedback_id or f"FBK-{schema.grade_id}-01"
    now = datetime.now(timezone.utc)
    
    feedback = Feedback(
        feedback_id=feedback_id,
        grade_id=schema.grade_id,
        submission_id=submission_id,
        author_id=schema.author_id,
        visibility=schema.visibility or FeedbackVisibility.LEARNER_VISIBLE,
        general_comments=schema.general_comments,
        strengths=schema.strengths,
        areas_for_improvement=schema.areas_for_improvement,
        published_at=now,
    )
    db.session.add(feedback)
    db.session.commit()
    
    return jsonify({
        "message": "Feedback added successfully",
        "feedback": serialize_model(feedback)
    }), 201

@feedback_bp.route("", methods=["GET"])
def list_feedback():
    """List feedback entries with filtering and pagination."""
    query = db.session.query(Feedback)
    
    submission_id = request.args.get("submission_id")
    if submission_id:
        query = query.filter(Feedback.submission_id == submission_id)
        
    grade_id = request.args.get("grade_id")
    if grade_id:
        query = query.filter(Feedback.grade_id == grade_id)
        
    author_id = request.args.get("author_id")
    if author_id:
        query = query.filter(Feedback.author_id == author_id)
        
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    
    paginated = paginate_query(query.order_by(Feedback.published_at.desc()), page, per_page)
    
    return jsonify({
        "feedback": [serialize_model(f) for f in paginated["items"]],
        "meta": paginated["meta"]
    }), 200

@feedback_bp.route("/<feedback_id>", methods=["GET"])
def get_feedback(feedback_id: str):
    """View details of a specific feedback record."""
    fb = db.session.get(Feedback, feedback_id)
    if not fb:
        raise EntityNotFoundException(f"Feedback '{feedback_id}' not found.")
        
    return jsonify({"feedback": serialize_model(fb)}), 200
