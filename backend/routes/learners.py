"""
Learner management REST API endpoints.
"""
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
from sqlalchemy import or_

from backend.extensions import db
from backend.models.learner import Learner
from backend.models.enums import EnrollmentStatus
from backend.schemas import LearnerCreateSchema, LearnerUpdateSchema
from backend.utils import (
    serialize_model, paginate_query, generate_id, validate_payload,
    EntityNotFoundException, DuplicateEntityException
)

learners_bp = Blueprint("learners", __name__, url_prefix="/api/learners")

@learners_bp.route("", methods=["POST"])
def register_learner():
    """Register a new learner."""
    data = request.get_json(silent=True) or {}
    schema = validate_payload(LearnerCreateSchema, data)
    
    # Check duplicate email or student_number
    existing = db.session.query(Learner).filter(
        or_(Learner.email == schema.email, Learner.student_number == schema.student_number)
    ).first()
    if existing:
        if existing.email == schema.email:
            raise DuplicateEntityException(f"Learner with email '{schema.email}' already exists.")
        raise DuplicateEntityException(f"Learner with student number '{schema.student_number}' already exists.")
        
    learner_id = schema.learner_id or generate_id("LNR")
    learner = Learner(
        learner_id=learner_id,
        student_number=schema.student_number,
        first_name=schema.first_name,
        last_name=schema.last_name,
        email=schema.email,
        timezone=schema.timezone,
        status=schema.status or EnrollmentStatus.ACTIVE,
    )
    db.session.add(learner)
    db.session.commit()
    
    return jsonify({
        "message": "Learner registered successfully",
        "learner": serialize_model(learner)
    }), 201

@learners_bp.route("", methods=["GET"])
def list_learners():
    """List learners with pagination, status filtering, and search."""
    query = db.session.query(Learner)
    
    status = request.args.get("status")
    if status:
        try:
            status_enum = EnrollmentStatus(status)
            query = query.filter(Learner.status == status_enum)
        except ValueError:
            pass
            
    tz = request.args.get("timezone")
    if tz:
        query = query.filter(Learner.timezone == tz)
        
    search = request.args.get("search")
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            or_(
                Learner.first_name.ilike(search_filter),
                Learner.last_name.ilike(search_filter),
                Learner.email.ilike(search_filter),
                Learner.student_number.ilike(search_filter),
            )
        )
        
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    
    paginated = paginate_query(query.order_by(Learner.created_at.desc()), page, per_page)
    
    return jsonify({
        "learners": [serialize_model(l) for l in paginated["items"]],
        "meta": paginated["meta"]
    }), 200

@learners_bp.route("/<learner_id>", methods=["GET"])
def get_learner_details(learner_id: str):
    """View learner details including enrolled courses."""
    learner = db.session.get(Learner, learner_id)
    if not learner:
        raise EntityNotFoundException(f"Learner '{learner_id}' not found.")
        
    data = serialize_model(learner)
    data["enrollments"] = [
        {
            "enrollment_id": e.enrollment_id,
            "course_id": e.course_id,
            "course_title": e.course.title if e.course else None,
            "status": e.status.value,
            "enrolled_at": e.enrolled_at.isoformat() if e.enrolled_at else None,
        }
        for e in learner.enrollments
    ]
    data["total_submissions"] = len(learner.submissions)
    return jsonify({"learner": data}), 200

@learners_bp.route("/<learner_id>", methods=["PUT", "PATCH"])
def update_learner(learner_id: str):
    """Update learner information."""
    learner = db.session.get(Learner, learner_id)
    if not learner:
        raise EntityNotFoundException(f"Learner '{learner_id}' not found.")
        
    data = request.get_json(silent=True) or {}
    schema = validate_payload(LearnerUpdateSchema, data)
    
    if schema.email and schema.email != learner.email:
        conflict = db.session.query(Learner).filter(Learner.email == schema.email, Learner.learner_id != learner_id).first()
        if conflict:
            raise DuplicateEntityException(f"Email '{schema.email}' is already in use by another learner.")
            
    update_data = schema.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        if val is not None:
            setattr(learner, field, val)
            
    learner.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    
    return jsonify({
        "message": "Learner updated successfully",
        "learner": serialize_model(learner)
    }), 200
