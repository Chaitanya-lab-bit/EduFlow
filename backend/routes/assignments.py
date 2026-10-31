"""
Assignment and Rubric management REST API endpoints.
"""
from datetime import datetime, timezone
from decimal import Decimal
from flask import Blueprint, request, jsonify

from backend.extensions import db
from backend.models.course import Course
from backend.models.assignment import Assignment
from backend.models.rubric import Rubric
from backend.models.rubric_criterion import RubricCriterion
from backend.models.enums import AssignmentStatus
from backend.schemas import (
    AssignmentCreateSchema, AssignmentUpdateSchema,
    RubricCreateSchema
)
from backend.utils import (
    serialize_model, paginate_query, generate_id, validate_payload,
    EntityNotFoundException, RubricPointsMismatchException
)

assignments_bp = Blueprint("assignments", __name__, url_prefix="/api/assignments")

@assignments_bp.route("", methods=["POST"])
def create_assignment():
    """Create a new assignment, optionally with an initial rubric."""
    data = request.get_json(silent=True) or {}
    schema = validate_payload(AssignmentCreateSchema, data)
    
    course = db.session.get(Course, schema.course_id)
    if not course:
        raise EntityNotFoundException(f"Course '{schema.course_id}' not found.")
        
    assignment_id = schema.assignment_id or generate_id("ASN")
    assignment = Assignment(
        assignment_id=assignment_id,
        course_id=schema.course_id,
        title=schema.title,
        description=schema.description,
        max_score=schema.max_score,
        due_date=schema.due_date,
        cutoff_date=schema.cutoff_date,
        late_penalty_per_day=schema.late_penalty_per_day,
        max_late_days=schema.max_late_days,
        grace_period_minutes=schema.grace_period_minutes,
        max_resubmissions=schema.max_resubmissions,
        required_artifact_types=schema.required_artifact_types,
        status=schema.status or AssignmentStatus.DRAFT,
    )
    db.session.add(assignment)
    db.session.flush()
    
    # If initial rubric provided
    if schema.rubric:
        r_schema = schema.rubric
        rubric_id = r_schema.rubric_id or f"RUB-{assignment_id}-{r_schema.version:02d}"
        rubric = Rubric(
            rubric_id=rubric_id,
            assignment_id=assignment_id,
            title=r_schema.title,
            description=r_schema.description,
            total_points=r_schema.total_points,
            version=r_schema.version,
            is_active=r_schema.is_active,
        )
        db.session.add(rubric)
        db.session.flush()
        
        for idx, crit in enumerate(r_schema.criteria, start=1):
            crit_id = crit.criterion_id or f"CRT-{rubric_id}-{idx:02d}"
            criterion = RubricCriterion(
                criterion_id=crit_id,
                rubric_id=rubric_id,
                criterion_name=crit.criterion_name,
                description=crit.description,
                max_points=crit.max_points,
                weight=crit.weight,
                display_order=crit.display_order or idx,
            )
            db.session.add(criterion)
            
    db.session.commit()
    
    return jsonify({
        "message": "Assignment created successfully",
        "assignment": serialize_model(assignment)
    }), 201

@assignments_bp.route("", methods=["GET"])
def list_assignments():
    """List assignments with pagination and filtering."""
    query = db.session.query(Assignment)
    
    course_id = request.args.get("course_id")
    if course_id:
        query = query.filter(Assignment.course_id == course_id)
        
    status = request.args.get("status")
    if status:
        try:
            status_enum = AssignmentStatus(status)
            query = query.filter(Assignment.status == status_enum)
        except ValueError:
            pass
            
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    
    paginated = paginate_query(query.order_by(Assignment.due_date.asc()), page, per_page)
    
    return jsonify({
        "assignments": [serialize_model(a) for a in paginated["items"]],
        "meta": paginated["meta"]
    }), 200

@assignments_bp.route("/<assignment_id>", methods=["GET"])
def get_assignment_details(assignment_id: str):
    """View assignment details with associated rubrics and criteria."""
    assignment = db.session.get(Assignment, assignment_id)
    if not assignment:
        raise EntityNotFoundException(f"Assignment '{assignment_id}' not found.")
        
    data = serialize_model(assignment)
    data["rubrics"] = []
    for r in assignment.rubrics:
        r_data = serialize_model(r)
        r_data["criteria"] = [serialize_model(c) for c in r.criteria]
        data["rubrics"].append(r_data)
        
    return jsonify({"assignment": data}), 200

@assignments_bp.route("/<assignment_id>", methods=["PUT", "PATCH"])
def update_assignment(assignment_id: str):
    """Configure due dates, cutoff dates, late penalties, or details."""
    assignment = db.session.get(Assignment, assignment_id)
    if not assignment:
        raise EntityNotFoundException(f"Assignment '{assignment_id}' not found.")
        
    data = request.get_json(silent=True) or {}
    schema = validate_payload(AssignmentUpdateSchema, data)
    
    update_data = schema.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        if val is not None:
            setattr(assignment, field, val)
            
    assignment.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    
    return jsonify({
        "message": "Assignment updated successfully",
        "assignment": serialize_model(assignment)
    }), 200

@assignments_bp.route("/<assignment_id>/publish", methods=["POST", "PATCH"])
def publish_assignment(assignment_id: str):
    """
    Publish an assignment.
    BR-04: Verifies that an active rubric exists and that the sum of criteria points
    equals assignment.max_score before transitioning status to PUBLISHED.
    """
    assignment = db.session.get(Assignment, assignment_id)
    if not assignment:
        raise EntityNotFoundException(f"Assignment '{assignment_id}' not found.")
        
    # Find active rubric
    active_rubric = next((r for r in assignment.rubrics if r.is_active), None)
    if not active_rubric:
        raise RubricPointsMismatchException("Cannot publish assignment: no active rubric is configured.")
        
    # Sum criteria points
    criteria_sum = sum(c.max_points for c in active_rubric.criteria)
    if abs(Decimal(str(criteria_sum)) - Decimal(str(assignment.max_score))) > Decimal("0.02"):
        raise RubricPointsMismatchException(
            f"Cannot publish assignment: active rubric criteria sum ({criteria_sum}) "
            f"does not match assignment max_score ({assignment.max_score})."
        )
        
    assignment.status = AssignmentStatus.PUBLISHED
    assignment.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    
    return jsonify({
        "message": "Assignment published successfully",
        "assignment": serialize_model(assignment)
    }), 200

@assignments_bp.route("/<assignment_id>/rubrics", methods=["POST"])
def configure_rubric(assignment_id: str):
    """Create or configure a new rubric version for an assignment."""
    assignment = db.session.get(Assignment, assignment_id)
    if not assignment:
        raise EntityNotFoundException(f"Assignment '{assignment_id}' not found.")
        
    data = request.get_json(silent=True) or {}
    schema = validate_payload(RubricCreateSchema, data)
    
    # If set as active, deactivate previous active rubrics for this assignment
    if schema.is_active:
        for r in assignment.rubrics:
            r.is_active = False
            
    rubric_id = schema.rubric_id or f"RUB-{assignment_id}-{schema.version:02d}"
    rubric = Rubric(
        rubric_id=rubric_id,
        assignment_id=assignment_id,
        title=schema.title,
        description=schema.description,
        total_points=schema.total_points,
        version=schema.version,
        is_active=schema.is_active,
    )
    db.session.add(rubric)
    db.session.flush()
    
    criteria_list = []
    for idx, crit in enumerate(schema.criteria, start=1):
        crit_id = crit.criterion_id or f"CRT-{rubric_id}-{idx:02d}"
        criterion = RubricCriterion(
            criterion_id=crit_id,
            rubric_id=rubric_id,
            criterion_name=crit.criterion_name,
            description=crit.description,
            max_points=crit.max_points,
            weight=crit.weight,
            display_order=crit.display_order or idx,
        )
        db.session.add(criterion)
        criteria_list.append(criterion)
        
    db.session.commit()
    
    r_data = serialize_model(rubric)
    r_data["criteria"] = [serialize_model(c) for c in criteria_list]
    return jsonify({
        "message": "Rubric configured successfully",
        "rubric": r_data
    }), 201
