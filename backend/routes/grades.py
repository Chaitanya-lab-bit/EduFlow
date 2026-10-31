"""
Grading and Evaluation REST API endpoints.
"""
from datetime import datetime, timezone
from decimal import Decimal
from flask import Blueprint, request, jsonify

from backend.extensions import db
from backend.models.submission import Submission
from backend.models.grade import Grade
from backend.models.grade_criterion_score import GradeCriterionScore
from backend.models.rubric import Rubric
from backend.models.submission_status_history import SubmissionStatusHistory
from backend.models.audit_log import AuditLog
from backend.models.enums import GradeStatus, SubmissionStatus, AuditActionType
from backend.schemas import GradeCreateSchema
from backend.utils import (
    serialize_model, generate_id, validate_payload,
    EntityNotFoundException, ScoreExceedsMaxException, DuplicateEntityException
)

grades_bp = Blueprint("grades", __name__, url_prefix="/api/grades")

@grades_bp.route("", methods=["POST"])
def grade_submission():
    """
    Grade a submission using rubric criteria.
    Enforces:
      - EX-02: Score bounds (HTTP 422 ERR_SCORE_EXCEEDS_MAX)
      - BR-05: Raw score sum & final score calculation
      - EX-03: Single idempotent late penalty deduction
      - Atomic transaction updating Submission, Grade, GradeCriterionScores, History, AuditLog.
    """
    data = request.get_json(silent=True) or {}
    schema = validate_payload(GradeCreateSchema, data)
    
    submission = db.session.get(Submission, schema.submission_id)
    if not submission:
        raise EntityNotFoundException(f"Submission '{schema.submission_id}' not found.")
        
    # Check if already graded (1:1 binding)
    existing_grade = db.session.query(Grade).filter_by(submission_id=schema.submission_id).first()
    if existing_grade:
        raise DuplicateEntityException(f"Submission '{schema.submission_id}' is already graded.")
        
    assignment = submission.assignment
    if not assignment:
        raise EntityNotFoundException("Assignment associated with submission not found.")
        
    # Find active rubric
    active_rubric = next((r for r in assignment.rubrics if r.is_active), None)
    if not active_rubric and assignment.rubrics:
        active_rubric = assignment.rubrics[0]
        
    criteria_map = {c.criterion_id: c for c in (active_rubric.criteria if active_rubric else [])}
    
    # 1. Validate each criterion score against max_points (EX-02)
    raw_score_sum = Decimal("0.00")
    validated_scores = []
    
    for item in schema.criteria_scores:
        crit = criteria_map.get(item.criterion_id)
        if crit:
            crit_max = Decimal(str(crit.max_points))
            if item.score_awarded > crit_max:
                raise ScoreExceedsMaxException(
                    f"Score awarded ({item.score_awarded}) exceeds criterion '{crit.criterion_name}' max_points ({crit_max}).",
                    details={"criterion_id": item.criterion_id, "score_awarded": float(item.score_awarded), "max_points": float(crit_max)}
                )
        raw_score_sum += item.score_awarded
        validated_scores.append(item)
        
    # 2. Check total raw score <= assignment.max_score (EX-02)
    max_score = Decimal(str(assignment.max_score))
    if raw_score_sum > max_score:
        raise ScoreExceedsMaxException(
            f"Total raw score ({raw_score_sum}) exceeds assignment max_score ({max_score}).",
            details={"raw_score": float(raw_score_sum), "max_score": float(max_score)}
        )
        
    # 3. EX-03: Late penalty applied exactly once
    late_pct = Decimal(str(submission.late_penalty_percentage or "0.00"))
    if submission.is_late and late_pct > Decimal("0.00"):
        late_penalty_applied = (raw_score_sum * (late_pct / Decimal("100.00"))).quantize(Decimal("0.01"))
    else:
        late_penalty_applied = Decimal("0.00")
        
    # 4. Final score computation: bounded in [0, max_score]
    bonus = Decimal(str(schema.bonus_points or "0.00"))
    computed_final = raw_score_sum - late_penalty_applied + bonus
    final_score = max(Decimal("0.00"), min(computed_final, max_score)).quantize(Decimal("0.01"))
    
    now = datetime.now(timezone.utc)
    grade_id = schema.grade_id or f"GRD-{submission.submission_id}"
    
    # Atomic transaction
    grade = Grade(
        grade_id=grade_id,
        submission_id=submission.submission_id,
        graded_by=schema.graded_by,
        raw_score=raw_score_sum,
        late_penalty_applied=late_penalty_applied,
        bonus_points=bonus,
        final_score=final_score,
        is_final=schema.is_final,
        grade_status=schema.grade_status or GradeStatus.PUBLISHED,
        graded_at=now,
    )
    db.session.add(grade)
    db.session.flush()
    
    # Save itemized criterion scores
    crit_records = []
    for idx, item in enumerate(validated_scores, start=1):
        score_id = f"GCS-{grade_id}-{idx:02d}"
        gcs = GradeCriterionScore(
            score_id=score_id,
            grade_id=grade_id,
            criterion_id=item.criterion_id,
            score_awarded=item.score_awarded,
            evaluator_comment=item.evaluator_comment,
            created_at=now,
        )
        db.session.add(gcs)
        crit_records.append(gcs)
        
    # Update submission
    old_sub_status = submission.status
    submission.raw_score = raw_score_sum
    submission.final_score = final_score
    submission.status = SubmissionStatus.GRADED
    submission.updated_at = now
    
    # Add status history
    history = SubmissionStatusHistory(
        history_id=generate_id("SSH"),
        submission_id=submission.submission_id,
        old_status=old_sub_status,
        new_status=SubmissionStatus.GRADED,
        changed_by=schema.graded_by,
        change_reason=f"Graded with raw score {raw_score_sum} and final score {final_score}.",
        changed_at=now,
    )
    db.session.add(history)
    
    # Record audit log
    audit_entry = AuditLog(
        audit_id=generate_id("AUD"),
        entity_name="grade",
        entity_id=grade_id,
        action=AuditActionType.INSERT,
        actor_id=schema.graded_by,
        actor_role="instructor",
        timestamp=now,
        new_values={
            "submission_id": submission.submission_id,
            "raw_score": float(raw_score_sum),
            "late_penalty_applied": float(late_penalty_applied),
            "final_score": float(final_score),
            "grade_status": grade.grade_status.value
        },
        client_ip=request.remote_addr,
        user_agent=request.headers.get("User-Agent")
    )
    db.session.add(audit_entry)
    
    db.session.commit()
    
    grade_data = serialize_model(grade)
    grade_data["criterion_scores"] = [serialize_model(c) for c in crit_records]
    return jsonify({
        "message": "Submission graded successfully",
        "grade": grade_data
    }), 201

@grades_bp.route("/<grade_id>", methods=["GET"])
def get_grade_details(grade_id: str):
    """View grade details with itemized criteria scores and deductions."""
    grade = db.session.get(Grade, grade_id)
    if not grade:
        raise EntityNotFoundException(f"Grade '{grade_id}' not found.")
        
    data = serialize_model(grade)
    data["criterion_scores"] = [serialize_model(c) for c in grade.criterion_scores]
    return jsonify({"grade": data}), 200

@grades_bp.route("/submission/<submission_id>", methods=["GET"])
def get_grade_by_submission(submission_id: str):
    """View grade associated with a submission."""
    grade = db.session.query(Grade).filter_by(submission_id=submission_id).first()
    if not grade:
        raise EntityNotFoundException(f"Grade for submission '{submission_id}' not found.")
        
    data = serialize_model(grade)
    data["criterion_scores"] = [serialize_model(c) for c in grade.criterion_scores]
    return jsonify({"grade": data}), 200
