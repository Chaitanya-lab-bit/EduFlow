"""
Enrollment management REST API endpoints.
"""
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify

from backend.extensions import db
from backend.models.course import Course
from backend.models.learner import Learner
from backend.models.enrollment import Enrollment
from backend.models.enums import EnrollmentStatus
from backend.schemas import EnrollmentCreateSchema
from backend.utils import (
    serialize_model, paginate_query, generate_id, validate_payload,
    EntityNotFoundException, DuplicateEntityException
)

enrollments_bp = Blueprint("enrollments", __name__, url_prefix="/api/enrollments")

@enrollments_bp.route("", methods=["POST"])
def enroll_learner():
    """Enroll a learner into a course."""
    data = request.get_json(silent=True) or {}
    schema = validate_payload(EnrollmentCreateSchema, data)
    
    course = db.session.get(Course, schema.course_id)
    if not course:
        raise EntityNotFoundException(f"Course '{schema.course_id}' not found.")
        
    learner = db.session.get(Learner, schema.learner_id)
    if not learner:
        raise EntityNotFoundException(f"Learner '{schema.learner_id}' not found.")
        
    # Check duplicate enrollment
    existing = db.session.query(Enrollment).filter_by(
        course_id=schema.course_id,
        learner_id=schema.learner_id
    ).first()
    if existing:
        raise DuplicateEntityException(f"Learner '{schema.learner_id}' is already enrolled in course '{schema.course_id}'.")
        
    enrollment_id = schema.enrollment_id or generate_id("ENR")
    enrollment = Enrollment(
        enrollment_id=enrollment_id,
        course_id=schema.course_id,
        learner_id=schema.learner_id,
        status=schema.status or EnrollmentStatus.ACTIVE,
        enrolled_at=datetime.now(timezone.utc)
    )
    db.session.add(enrollment)
    db.session.commit()
    
    return jsonify({
        "message": "Learner enrolled successfully",
        "enrollment": serialize_model(enrollment)
    }), 201

@enrollments_bp.route("", methods=["GET"])
def list_enrollments():
    """List enrollments with pagination and filtering."""
    query = db.session.query(Enrollment)
    
    course_id = request.args.get("course_id")
    if course_id:
        query = query.filter(Enrollment.course_id == course_id)
        
    learner_id = request.args.get("learner_id")
    if learner_id:
        query = query.filter(Enrollment.learner_id == learner_id)
        
    status = request.args.get("status")
    if status:
        try:
            status_enum = EnrollmentStatus(status)
            query = query.filter(Enrollment.status == status_enum)
        except ValueError:
            pass
            
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    
    paginated = paginate_query(query.order_by(Enrollment.enrolled_at.desc()), page, per_page)
    
    records = []
    for e in paginated["items"]:
        item = serialize_model(e)
        if e.learner:
            item["learner_name"] = f"{e.learner.first_name} {e.learner.last_name}"
            item["learner_email"] = e.learner.email
        if e.course:
            item["course_code"] = e.course.code
            item["course_title"] = e.course.title
        records.append(item)
        
    return jsonify({
        "enrollments": records,
        "meta": paginated["meta"]
    }), 200

@enrollments_bp.route("/status", methods=["GET"])
def check_enrollment_status():
    """Check enrollment status of a learner in a course."""
    course_id = request.args.get("course_id")
    learner_id = request.args.get("learner_id")
    
    if not course_id or not learner_id:
        return jsonify({"error": "Both 'course_id' and 'learner_id' query parameters are required"}), 400
        
    enrollment = db.session.query(Enrollment).filter_by(
        course_id=course_id,
        learner_id=learner_id
    ).first()
    
    if not enrollment:
        return jsonify({
            "is_enrolled": False,
            "course_id": course_id,
            "learner_id": learner_id,
            "status": None
        }), 200
        
    return jsonify({
        "is_enrolled": True,
        "course_id": course_id,
        "learner_id": learner_id,
        "enrollment_id": enrollment.enrollment_id,
        "status": enrollment.status.value,
        "enrolled_at": enrollment.enrolled_at.isoformat()
    }), 200

@enrollments_bp.route("/<enrollment_id>", methods=["GET"])
def get_enrollment(enrollment_id: str):
    """View enrollment details."""
    enrollment = db.session.get(Enrollment, enrollment_id)
    if not enrollment:
        raise EntityNotFoundException(f"Enrollment '{enrollment_id}' not found.")
        
    item = serialize_model(enrollment)
    if enrollment.learner:
        item["learner_name"] = f"{enrollment.learner.first_name} {enrollment.learner.last_name}"
        item["learner_email"] = enrollment.learner.email
    if enrollment.course:
        item["course_code"] = enrollment.course.code
        item["course_title"] = enrollment.course.title
    return jsonify({"enrollment": item}), 200

@enrollments_bp.route("/<enrollment_id>", methods=["PATCH"])
def update_enrollment_status(enrollment_id: str):
    """Update enrollment status (e.g. drop/complete)."""
    enrollment = db.session.get(Enrollment, enrollment_id)
    if not enrollment:
        raise EntityNotFoundException(f"Enrollment '{enrollment_id}' not found.")
        
    data = request.get_json(silent=True) or {}
    new_status = data.get("status")
    if not new_status:
        return jsonify({"error": "Field 'status' is required"}), 400
        
    try:
        status_enum = EnrollmentStatus(new_status)
        enrollment.status = status_enum
        if status_enum == EnrollmentStatus.DROPPED:
            enrollment.dropped_at = datetime.now(timezone.utc)
        enrollment.updated_at = datetime.now(timezone.utc)
        db.session.commit()
    except ValueError:
        return jsonify({"error": f"Invalid enrollment status '{new_status}'"}), 422
        
    return jsonify({
        "message": "Enrollment status updated",
        "enrollment": serialize_model(enrollment)
    }), 200
