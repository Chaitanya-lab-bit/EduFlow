"""
Submission and Artifact management REST API endpoints.
"""
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import math
from flask import Blueprint, request, jsonify
from sqlalchemy.exc import IntegrityError

from backend.extensions import db
from backend.models.assignment import Assignment
from backend.models.learner import Learner
from backend.models.enrollment import Enrollment
from backend.models.submission import Submission
from backend.models.submission_artifact import SubmissionArtifact
from backend.models.submission_status_history import SubmissionStatusHistory
from backend.models.enums import SubmissionStatus, EnrollmentStatus, ArtifactType
from backend.schemas import (
    SubmissionCreateSchema, SubmissionArtifactInputSchema
)
from backend.utils import (
    serialize_model, paginate_query, generate_id, validate_payload,
    EntityNotFoundException, UnenrolledLearnerException,
    DeadlineExceededException, MissingArtifactsException,
    DuplicateEntityException
)

submissions_bp = Blueprint("submissions", __name__, url_prefix="/api/submissions")

@submissions_bp.route("", methods=["POST"])
def submit_assignment():
    """
    Submit assignment attempt with artifact verification and lateness calculation.
    Enforces:
      - EX-01: Enrollment check (HTTP 403 ERR_UNENROLLED_LEARNER)
      - EX-06: Cutoff check (HTTP 403 ERR_DEADLINE_EXCEEDED)
      - BR-02: Grace period & late penalty calculation
      - EX-05: Missing artifact verification (HTTP 422 MISSING_REQUIRED_ARTIFACTS)
    """
    data = request.get_json(silent=True) or {}
    schema = validate_payload(SubmissionCreateSchema, data)
    
    assignment = db.session.get(Assignment, schema.assignment_id)
    if not assignment:
        raise EntityNotFoundException(f"Assignment '{schema.assignment_id}' not found.")
        
    learner = db.session.get(Learner, schema.learner_id)
    if not learner:
        raise EntityNotFoundException(f"Learner '{schema.learner_id}' not found.")
        
    # 1. EX-01: Check active enrollment in assignment course
    enrollment = db.session.query(Enrollment).filter_by(
        course_id=assignment.course_id,
        learner_id=schema.learner_id,
        status=EnrollmentStatus.ACTIVE
    ).first()
    if not enrollment:
        raise UnenrolledLearnerException(
            f"Learner '{schema.learner_id}' is not actively enrolled in course '{assignment.course_id}' for assignment '{schema.assignment_id}'."
        )
        
    sub_time = schema.submitted_at or datetime.now(timezone.utc)
    if sub_time.tzinfo is None:
        sub_time = sub_time.replace(tzinfo=timezone.utc)
        
    due_date = assignment.due_date
    if due_date.tzinfo is None:
        due_date = due_date.replace(tzinfo=timezone.utc)
        
    cutoff_date = assignment.cutoff_date
    if cutoff_date.tzinfo is None:
        cutoff_date = cutoff_date.replace(tzinfo=timezone.utc)
        
    # 2. EX-06: Check cutoff date
    if sub_time > cutoff_date:
        raise DeadlineExceededException(
            f"Submission timestamp ({sub_time.isoformat()}) exceeds cutoff date ({cutoff_date.isoformat()})."
        )
        
    # 3. BR-02: Calculate lateness and late penalty percentage
    grace_seconds = assignment.grace_period_minutes * 60
    grace_deadline = due_date + timedelta(seconds=grace_seconds)
    
    if sub_time <= grace_deadline:
        is_late = False
        late_duration_seconds = 0
        late_penalty_percentage = Decimal("0.00")
    else:
        is_late = True
        late_duration_seconds = int((sub_time - due_date).total_seconds())
        # Days late calculation (fractional day past grace ceiling)
        unbuffered_seconds = late_duration_seconds - grace_seconds
        days_late = math.ceil(unbuffered_seconds / 86400.0)
        days_late = max(1, min(days_late, assignment.max_late_days))
        late_penalty_percentage = min(
            Decimal(str(days_late)) * Decimal(str(assignment.late_penalty_per_day)),
            Decimal("100.00")
        )
        
    # 4. Check duplicate attempt
    attempt = schema.attempt_number or 1
    existing_sub = db.session.query(Submission).filter_by(
        assignment_id=schema.assignment_id,
        learner_id=schema.learner_id,
        attempt_number=attempt
    ).first()
    if existing_sub:
        raise DuplicateEntityException(
            f"Submission for assignment '{schema.assignment_id}', learner '{schema.learner_id}', attempt {attempt} already exists."
        )
        
    # 5. EX-05: Missing artifact check if status is SUBMITTED
    target_status = schema.status or SubmissionStatus.SUBMITTED
    if target_status == SubmissionStatus.SUBMITTED and assignment.required_artifact_types:
        provided_types = set()
        if schema.artifacts:
            for art in schema.artifacts:
                provided_types.add(art.artifact_type.value if hasattr(art.artifact_type, 'value') else str(art.artifact_type))
        missing_types = [t for t in assignment.required_artifact_types if t not in provided_types]
        if missing_types:
            raise MissingArtifactsException(missing=missing_types)
            
    submission_id = schema.submission_id or f"SUB-{schema.assignment_id}-{schema.learner_id}-{attempt:02d}"
    submission = Submission(
        submission_id=submission_id,
        assignment_id=schema.assignment_id,
        learner_id=schema.learner_id,
        enrollment_id=enrollment.enrollment_id,
        attempt_number=attempt,
        submitted_at=sub_time,
        status=target_status,
        is_late=is_late,
        late_duration_seconds=late_duration_seconds,
        late_penalty_percentage=late_penalty_percentage,
        learner_notes=schema.learner_notes,
    )
    db.session.add(submission)
    db.session.flush()
    
    # Save artifacts if provided in request
    artifacts_saved = []
    if schema.artifacts:
        for idx, art_input in enumerate(schema.artifacts, start=1):
            art_id = art_input.artifact_id or f"ART-{submission_id}-{idx:02d}"
            art_obj = SubmissionArtifact(
                artifact_id=art_id,
                submission_id=submission_id,
                artifact_type=art_input.artifact_type,
                file_name=art_input.file_name,
                file_size_bytes=art_input.file_size_bytes,
                mime_type=art_input.mime_type,
                storage_uri=art_input.storage_uri,
                checksum_sha256=art_input.checksum_sha256,
                is_verified=art_input.is_verified,
            )
            db.session.add(art_obj)
            artifacts_saved.append(art_obj)
            
    # Add initial status history record
    history_id = generate_id("SSH")
    history = SubmissionStatusHistory(
        history_id=history_id,
        submission_id=submission_id,
        old_status=SubmissionStatus.DRAFT if target_status == SubmissionStatus.SUBMITTED else None,
        new_status=target_status,
        changed_by=schema.learner_id,
        change_reason=f"Submission attempt {attempt} submitted by learner.",
        changed_at=sub_time,
    )
    db.session.add(history)
    db.session.commit()
    
    sub_data = serialize_model(submission)
    sub_data["artifacts"] = [serialize_model(a) for a in artifacts_saved]
    return jsonify({
        "message": "Assignment submitted successfully",
        "submission": sub_data
    }), 201

@submissions_bp.route("/<submission_id>/artifacts", methods=["POST"])
def upload_artifact(submission_id: str):
    """Upload artifact metadata for a submission."""
    submission = db.session.get(Submission, submission_id)
    if not submission:
        raise EntityNotFoundException(f"Submission '{submission_id}' not found.")
        
    data = request.get_json(silent=True) or {}
    schema = validate_payload(SubmissionArtifactInputSchema, data)
    
    # Check duplicate artifact type
    existing = db.session.query(SubmissionArtifact).filter_by(
        submission_id=submission_id,
        artifact_type=schema.artifact_type
    ).first()
    if existing:
        raise DuplicateEntityException(
            f"Artifact of type '{schema.artifact_type.value}' already exists for submission '{submission_id}'."
        )
        
    artifact_id = schema.artifact_id or f"ART-{submission_id}-{schema.artifact_type.value}"
    artifact = SubmissionArtifact(
        artifact_id=artifact_id,
        submission_id=submission_id,
        artifact_type=schema.artifact_type,
        file_name=schema.file_name,
        file_size_bytes=schema.file_size_bytes,
        mime_type=schema.mime_type,
        storage_uri=schema.storage_uri,
        checksum_sha256=schema.checksum_sha256,
        is_verified=schema.is_verified,
    )
    db.session.add(artifact)
    db.session.commit()
    
    return jsonify({
        "message": "Artifact metadata uploaded successfully",
        "artifact": serialize_model(artifact)
    }), 201

@submissions_bp.route("", methods=["GET"])
def list_submissions():
    """List submissions with filtering and pagination."""
    query = db.session.query(Submission)
    
    assignment_id = request.args.get("assignment_id")
    if assignment_id:
        query = query.filter(Submission.assignment_id == assignment_id)
        
    learner_id = request.args.get("learner_id")
    if learner_id:
        query = query.filter(Submission.learner_id == learner_id)
        
    status = request.args.get("status")
    if status:
        try:
            status_enum = SubmissionStatus(status)
            query = query.filter(Submission.status == status_enum)
        except ValueError:
            pass
            
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    
    paginated = paginate_query(query.order_by(Submission.submitted_at.desc()), page, per_page)
    
    return jsonify({
        "submissions": [serialize_model(s) for s in paginated["items"]],
        "meta": paginated["meta"]
    }), 200

@submissions_bp.route("/<submission_id>", methods=["GET"])
def get_submission_details(submission_id: str):
    """View submission details with artifacts, grade, and status history."""
    submission = db.session.get(Submission, submission_id)
    if not submission:
        raise EntityNotFoundException(f"Submission '{submission_id}' not found.")
        
    data = serialize_model(submission)
    data["artifacts"] = [serialize_model(a) for a in submission.artifacts]
    data["grade"] = serialize_model(submission.grade) if submission.grade else None
    data["status_history"] = [serialize_model(h) for h in submission.status_history]
    return jsonify({"submission": data}), 200

@submissions_bp.route("/<submission_id>/history", methods=["GET"])
def get_submission_history(submission_id: str):
    """View submission status history transitions."""
    submission = db.session.get(Submission, submission_id)
    if not submission:
        raise EntityNotFoundException(f"Submission '{submission_id}' not found.")
        
    history = db.session.query(SubmissionStatusHistory).filter_by(
        submission_id=submission_id
    ).order_by(SubmissionStatusHistory.changed_at.asc()).all()
    
    return jsonify({
        "submission_id": submission_id,
        "history": [serialize_model(h) for h in history]
    }), 200

@submissions_bp.route("/<submission_id>/late-status", methods=["GET"])
def check_late_status(submission_id: str):
    """Check late submission status and penalty metadata."""
    submission = db.session.get(Submission, submission_id)
    if not submission:
        raise EntityNotFoundException(f"Submission '{submission_id}' not found.")
        
    assignment = submission.assignment
    return jsonify({
        "submission_id": submission_id,
        "is_late": submission.is_late,
        "late_duration_seconds": submission.late_duration_seconds,
        "late_penalty_percentage": float(submission.late_penalty_percentage),
        "submitted_at": submission.submitted_at.isoformat() if submission.submitted_at else None,
        "due_date": assignment.due_date.isoformat() if assignment and assignment.due_date else None,
        "grace_period_minutes": assignment.grace_period_minutes if assignment else 15,
        "cutoff_date": assignment.cutoff_date.isoformat() if assignment and assignment.cutoff_date else None,
    }), 200
