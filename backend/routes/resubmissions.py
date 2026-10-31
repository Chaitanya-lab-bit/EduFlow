"""
Resubmission workflow REST API endpoints.
"""
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify

from backend.extensions import db
from backend.models.submission import Submission
from backend.models.assignment import Assignment
from backend.models.resubmission import Resubmission
from backend.models.submission_status_history import SubmissionStatusHistory
from backend.models.enums import ResubmissionStatus, SubmissionStatus
from backend.schemas import ResubmissionRequestSchema, ResubmissionReviewSchema
from backend.utils import (
    serialize_model, paginate_query, generate_id, validate_payload,
    EntityNotFoundException, DeadlineExceededException,
    ResubmissionLimitReachedException, DuplicateEntityException
)

resubmissions_bp = Blueprint("resubmissions", __name__, url_prefix="/api/resubmissions")

@resubmissions_bp.route("", methods=["POST"])
def request_resubmission():
    """
    Learner requests permission for a resubmission attempt.
    Enforces:
      - EX-06: Cutoff check (HTTP 403 ERR_DEADLINE_EXCEEDED)
      - EX-07: Resubmission attempt limits (HTTP 400 ERR_RESUBMISSION_LIMIT_REACHED)
    """
    data = request.get_json(silent=True) or {}
    schema = validate_payload(ResubmissionRequestSchema, data)
    
    orig_sub = db.session.get(Submission, schema.original_submission_id)
    if not orig_sub:
        raise EntityNotFoundException(f"Original submission '{schema.original_submission_id}' not found.")
        
    assignment = orig_sub.assignment
    if not assignment:
        raise EntityNotFoundException("Assignment associated with submission not found.")
        
    now = datetime.now(timezone.utc)
    cutoff = assignment.cutoff_date
    if cutoff.tzinfo is None:
        cutoff = cutoff.replace(tzinfo=timezone.utc)
        
    # 1. EX-06: Check cutoff date
    if now > cutoff:
        raise DeadlineExceededException(
            f"Cannot request resubmission: assignment cutoff date ({cutoff.isoformat()}) has passed."
        )
        
    # 2. EX-07: Check max resubmissions limit
    existing_attempts_count = db.session.query(Submission).filter_by(
        assignment_id=orig_sub.assignment_id,
        learner_id=orig_sub.learner_id
    ).count()
    allowed_total_attempts = 1 + assignment.max_resubmissions
    if existing_attempts_count >= allowed_total_attempts:
        raise ResubmissionLimitReachedException(
            f"Learner has already executed {existing_attempts_count} attempts. Max allowed attempts: {allowed_total_attempts}."
        )
        
    # Check if there is already a pending resubmission request
    pending = db.session.query(Resubmission).filter_by(
        original_submission_id=orig_sub.submission_id,
        status=ResubmissionStatus.SUBMITTED
    ).first()
    if pending:
        raise DuplicateEntityException(f"An active resubmission request already exists for submission '{orig_sub.submission_id}'.")
        
    resub_id = schema.resubmission_id or generate_id("RSB")
    
    # We will reserve the new submission ID pattern: SUB-<aid>-<lid>-<attempt>
    new_attempt_num = existing_attempts_count + 1
    new_sub_id = f"SUB-{orig_sub.assignment_id}-{orig_sub.learner_id}-{new_attempt_num:02d}"
    
    # Create the pending placeholder or new submission upon approval
    # For relational integrity, new_submission_id references submission.submission_id, so we create the draft submission or reserve it
    # Let's create the new submission in DRAFT status so it satisfies the foreign key
    new_sub = Submission(
        submission_id=new_sub_id,
        assignment_id=orig_sub.assignment_id,
        learner_id=orig_sub.learner_id,
        enrollment_id=orig_sub.enrollment_id,
        attempt_number=new_attempt_num,
        submitted_at=now,
        status=SubmissionStatus.DRAFT,
        is_late=False,
        late_duration_seconds=0,
        late_penalty_percentage=0,
        learner_notes=schema.reason,
    )
    db.session.add(new_sub)
    db.session.flush()
    
    resub = Resubmission(
        resubmission_id=resub_id,
        original_submission_id=orig_sub.submission_id,
        new_submission_id=new_sub.submission_id,
        reason=schema.reason,
        change_summary=schema.change_summary,
        status=ResubmissionStatus.SUBMITTED,
        requested_at=now,
    )
    db.session.add(resub)
    db.session.commit()
    
    return jsonify({
        "message": "Resubmission request submitted successfully",
        "resubmission": serialize_model(resub)
    }), 201

@resubmissions_bp.route("/<resubmission_id>/review", methods=["POST"])
def review_resubmission(resubmission_id: str):
    """
    Approve or reject a resubmission request.
    If APPROVED: Activates the new submission attempt and logs history.
    """
    resub = db.session.get(Resubmission, resubmission_id)
    if not resub:
        raise EntityNotFoundException(f"Resubmission request '{resubmission_id}' not found.")
        
    data = request.get_json(silent=True) or {}
    schema = validate_payload(ResubmissionReviewSchema, data)
    
    now = datetime.now(timezone.utc)
    resub.status = schema.status
    resub.approved_by = schema.reviewed_by
    resub.reviewed_at = now
    if schema.change_summary:
        resub.change_summary = schema.change_summary
        
    if schema.status == ResubmissionStatus.APPROVED:
        # Update new submission status to SUBMITTED or keep DRAFT for learner artifact upload
        new_sub = db.session.get(Submission, resub.new_submission_id)
        if new_sub:
            new_sub.status = SubmissionStatus.SUBMITTED
            new_sub.updated_at = now
            # Add status history for new submission
            ssh = SubmissionStatusHistory(
                history_id=generate_id("SSH"),
                submission_id=new_sub.submission_id,
                old_status=SubmissionStatus.DRAFT,
                new_status=SubmissionStatus.SUBMITTED,
                changed_by=schema.reviewed_by,
                change_reason=f"Resubmission request {resubmission_id} approved by instructor.",
                changed_at=now
            )
            db.session.add(ssh)
            
    db.session.commit()
    
    return jsonify({
        "message": f"Resubmission request {schema.status.value}",
        "resubmission": serialize_model(resub)
    }), 200

@resubmissions_bp.route("", methods=["GET"])
def list_resubmissions():
    """List resubmissions with pagination and status filter."""
    query = db.session.query(Resubmission)
    
    status = request.args.get("status")
    if status:
        try:
            status_enum = ResubmissionStatus(status)
            query = query.filter(Resubmission.status == status_enum)
        except ValueError:
            pass
            
    orig_sub_id = request.args.get("original_submission_id")
    if orig_sub_id:
        query = query.filter(Resubmission.original_submission_id == orig_sub_id)
        
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    
    paginated = paginate_query(query.order_by(Resubmission.requested_at.desc()), page, per_page)
    
    return jsonify({
        "resubmissions": [serialize_model(r) for r in paginated["items"]],
        "meta": paginated["meta"]
    }), 200

@resubmissions_bp.route("/<resubmission_id>", methods=["GET"])
def get_resubmission(resubmission_id: str):
    """View details of a resubmission record."""
    resub = db.session.get(Resubmission, resubmission_id)
    if not resub:
        raise EntityNotFoundException(f"Resubmission '{resubmission_id}' not found.")
        
    return jsonify({"resubmission": serialize_model(resub)}), 200
