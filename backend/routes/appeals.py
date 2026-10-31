"""
Academic Appeal and Audit Governance REST API endpoints.
"""
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from flask import Blueprint, request, jsonify

from backend.extensions import db
from backend.models.submission import Submission
from backend.models.grade import Grade
from backend.models.appeal import Appeal
from backend.models.submission_status_history import SubmissionStatusHistory
from backend.models.audit_log import AuditLog
from backend.models.enums import (
    AppealStatus, SubmissionStatus, GradeStatus, AuditActionType
)
from backend.schemas import AppealCreateSchema, AppealDecisionSchema
from backend.utils import (
    serialize_model, paginate_query, generate_id, validate_payload,
    EntityNotFoundException, AppealWindowExpiredException,
    DuplicateEntityException, APIException
)

appeals_bp = Blueprint("appeals", __name__, url_prefix="/api/appeals")

@appeals_bp.route("", methods=["POST"])
def submit_appeal():
    """
    Submit a formal academic grade appeal.
    Enforces:
      - BR-07 / EX-08: 7-day appeal window check (HTTP 400 ERR_APPEAL_WINDOW_EXPIRED)
      - Single active appeal per submission
    """
    data = request.get_json(silent=True) or {}
    schema = validate_payload(AppealCreateSchema, data)
    
    submission = db.session.get(Submission, schema.submission_id)
    if not submission:
        raise EntityNotFoundException(f"Submission '{schema.submission_id}' not found.")
        
    grade = submission.grade
    if not grade:
        raise EntityNotFoundException(f"No grade published for submission '{schema.submission_id}'.")
        
    # Check learner ownership
    if submission.learner_id != schema.learner_id:
        raise APIException("Learner ID does not match the submission owner.", status_code=403, error_code="ERR_UNAUTHORIZED")
        
    now = datetime.now(timezone.utc)
    graded_at = grade.graded_at
    if graded_at.tzinfo is None:
        graded_at = graded_at.replace(tzinfo=timezone.utc)
        
    # 1. EX-08: 7-day appeal window check
    appeal_window = timedelta(days=7)
    if now > graded_at + appeal_window:
        raise AppealWindowExpiredException(
            f"Appeal window has expired. Grade was published at {graded_at.isoformat()} (7-day window)."
        )
        
    # 2. Check single active appeal
    active_appeal = db.session.query(Appeal).filter(
        Appeal.submission_id == schema.submission_id,
        Appeal.status.in_([AppealStatus.SUBMITTED, AppealStatus.UNDER_REVIEW])
    ).first()
    if active_appeal:
        raise DuplicateEntityException("An active appeal is already pending for this submission.")
        
    appeal_id = schema.appeal_id or generate_id("APP")
    appeal = Appeal(
        appeal_id=appeal_id,
        submission_id=schema.submission_id,
        grade_id=grade.grade_id,
        learner_id=schema.learner_id,
        status=AppealStatus.SUBMITTED,
        reason_category=schema.reason_category,
        learner_statement=schema.learner_statement,
        contested_criteria=schema.contested_criteria,
        original_grade=grade.final_score,
        requested_grade=schema.requested_grade,
        submitted_at=now,
    )
    db.session.add(appeal)
    
    # Transition submission status to APPEALED
    old_sub_status = submission.status
    submission.status = SubmissionStatus.APPEALED
    submission.updated_at = now
    
    history = SubmissionStatusHistory(
        history_id=generate_id("SSH"),
        submission_id=submission.submission_id,
        old_status=old_sub_status,
        new_status=SubmissionStatus.APPEALED,
        changed_by=schema.learner_id,
        change_reason=f"Academic appeal {appeal_id} lodged by learner.",
        changed_at=now
    )
    db.session.add(history)
    db.session.commit()
    
    return jsonify({
        "message": "Appeal lodged successfully",
        "appeal": serialize_model(appeal)
    }), 201

@appeals_bp.route("/<appeal_id>/decision", methods=["POST"])
def adjudicate_appeal(appeal_id: str):
    """
    Adjudicate an appeal (APPROVE or REJECT).
    Enforces:
      - EX-04: Atomic transaction requiring AuditLog insertion when grade is revised.
      - Immutable audit trail linking old and new grade scores.
    """
    appeal = db.session.get(Appeal, appeal_id)
    if not appeal:
        raise EntityNotFoundException(f"Appeal '{appeal_id}' not found.")
        
    data = request.get_json(silent=True) or {}
    schema = validate_payload(AppealDecisionSchema, data)
    
    submission = appeal.submission
    grade = appeal.grade
    if not grade:
        grade = db.session.get(Grade, appeal.grade_id)
        
    now = datetime.now(timezone.utc)
    
    appeal.status = schema.status
    appeal.reviewed_by = schema.reviewed_by
    appeal.decision_notes = schema.decision_notes
    appeal.resolved_at = now
    
    if schema.status == AppealStatus.APPROVED:
        final_grade = Decimal(str(schema.final_grade))
        appeal.final_grade = final_grade
        
        old_grade_score = float(grade.final_score)
        
        # Update grade record
        grade.final_score = final_grade
        grade.grade_status = GradeStatus.REVISED
        grade.updated_at = now
        
        # Update submission
        submission.final_score = final_grade
        submission.status = SubmissionStatus.GRADED
        submission.updated_at = now
        
        # EX-04: Mandatory atomic AuditLog entry
        audit_entry = AuditLog(
            audit_id=generate_id("AUD"),
            entity_name="grade",
            entity_id=grade.grade_id,
            action=AuditActionType.APPEAL_DECISION,
            actor_id=schema.reviewed_by,
            actor_role="reviewer",
            timestamp=now,
            old_values={"final_score": old_grade_score, "grade_status": "published"},
            new_values={"final_score": float(final_grade), "grade_status": "revised", "appeal_id": appeal_id},
            client_ip=request.remote_addr,
            user_agent=request.headers.get("User-Agent")
        )
        db.session.add(audit_entry)
        
        # Status history
        ssh = SubmissionStatusHistory(
            history_id=generate_id("SSH"),
            submission_id=submission.submission_id,
            old_status=SubmissionStatus.APPEALED,
            new_status=SubmissionStatus.GRADED,
            changed_by=schema.reviewed_by,
            change_reason=f"Appeal {appeal_id} APPROVED: Grade updated to {final_grade}.",
            changed_at=now
        )
        db.session.add(ssh)
        
    elif schema.status == AppealStatus.REJECTED:
        submission.status = SubmissionStatus.GRADED
        submission.updated_at = now
        
        ssh = SubmissionStatusHistory(
            history_id=generate_id("SSH"),
            submission_id=submission.submission_id,
            old_status=SubmissionStatus.APPEALED,
            new_status=SubmissionStatus.GRADED,
            changed_by=schema.reviewed_by,
            change_reason=f"Appeal {appeal_id} REJECTED: Original grade upheld.",
            changed_at=now
        )
        db.session.add(ssh)
        
    db.session.commit()
    
    return jsonify({
        "message": f"Appeal {schema.status.value}",
        "appeal": serialize_model(appeal)
    }), 200

@appeals_bp.route("", methods=["GET"])
def list_appeals():
    """List appeals with filtering and pagination."""
    query = db.session.query(Appeal)
    
    status = request.args.get("status")
    if status:
        try:
            status_enum = AppealStatus(status)
            query = query.filter(Appeal.status == status_enum)
        except ValueError:
            pass
            
    learner_id = request.args.get("learner_id")
    if learner_id:
        query = query.filter(Appeal.learner_id == learner_id)
        
    submission_id = request.args.get("submission_id")
    if submission_id:
        query = query.filter(Appeal.submission_id == submission_id)
        
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    
    paginated = paginate_query(query.order_by(Appeal.submitted_at.desc()), page, per_page)
    
    return jsonify({
        "appeals": [serialize_model(a) for a in paginated["items"]],
        "meta": paginated["meta"]
    }), 200

@appeals_bp.route("/<appeal_id>", methods=["GET"])
def get_appeal(appeal_id: str):
    """View details of a specific appeal."""
    appeal = db.session.get(Appeal, appeal_id)
    if not appeal:
        raise EntityNotFoundException(f"Appeal '{appeal_id}' not found.")
        
    return jsonify({"appeal": serialize_model(appeal)}), 200
