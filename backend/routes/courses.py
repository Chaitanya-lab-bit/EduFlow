"""
Course management REST API endpoints.
"""
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from backend.extensions import db
from backend.models.course import Course
from backend.models.enums import CourseStatus
from backend.schemas import CourseCreateSchema, CourseUpdateSchema
from backend.utils import (
    serialize_model, paginate_query, generate_id, validate_payload,
    EntityNotFoundException, DuplicateEntityException
)

courses_bp = Blueprint("courses", __name__, url_prefix="/api/courses")

@courses_bp.route("", methods=["POST"])
def create_course():
    """Create a new course."""
    data = request.get_json(silent=True) or {}
    schema = validate_payload(CourseCreateSchema, data)
    
    # Check duplicate code
    existing = db.session.query(Course).filter_by(code=schema.code).first()
    if existing:
        raise DuplicateEntityException(f"Course with code '{schema.code}' already exists.")
    
    course_id = schema.course_id or generate_id("CRS")
    course = Course(
        course_id=course_id,
        code=schema.code,
        title=schema.title,
        description=schema.description,
        department=schema.department,
        term=schema.term,
        timezone=schema.timezone,
        status=schema.status or CourseStatus.DRAFT,
        start_date=schema.start_date,
        end_date=schema.end_date,
    )
    db.session.add(course)
    db.session.commit()
    
    return jsonify({
        "message": "Course created successfully",
        "course": serialize_model(course)
    }), 201

@courses_bp.route("", methods=["GET"])
def list_courses():
    """List courses with pagination and filtering."""
    query = db.session.query(Course)
    
    status = request.args.get("status")
    if status:
        try:
            status_enum = CourseStatus(status)
            query = query.filter(Course.status == status_enum)
        except ValueError:
            pass
            
    department = request.args.get("department")
    if department:
        query = query.filter(Course.department.ilike(f"%{department}%"))
        
    term = request.args.get("term")
    if term:
        query = query.filter(Course.term == term)
        
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    
    paginated = paginate_query(query.order_by(Course.created_at.desc()), page, per_page)
    
    return jsonify({
        "courses": [serialize_model(c) for c in paginated["items"]],
        "meta": paginated["meta"]
    }), 200

@courses_bp.route("/<course_id>", methods=["GET"])
def get_course_details(course_id: str):
    """View course details including counts of enrollments and assignments."""
    course = db.session.get(Course, course_id)
    if not course:
        raise EntityNotFoundException(f"Course '{course_id}' not found.")
        
    data = serialize_model(course)
    data["total_enrollments"] = len(course.enrollments)
    data["total_assignments"] = len(course.assignments)
    return jsonify({"course": data}), 200

@courses_bp.route("/<course_id>", methods=["PUT", "PATCH"])
def update_course(course_id: str):
    """Update course attributes."""
    course = db.session.get(Course, course_id)
    if not course:
        raise EntityNotFoundException(f"Course '{course_id}' not found.")
        
    data = request.get_json(silent=True) or {}
    schema = validate_payload(CourseUpdateSchema, data)
    
    update_data = schema.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        if val is not None:
            setattr(course, field, val)
            
    course.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    
    return jsonify({
        "message": "Course updated successfully",
        "course": serialize_model(course)
    }), 200
