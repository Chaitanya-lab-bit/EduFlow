from datetime import datetime, timezone, timedelta
from decimal import Decimal
import numpy as np
from backend.models.enums import (
    SubmissionStatus, GradeStatus, AppealStatus,
    AppealReasonCategory, AuditActionType
)

def generate_anomalies(
    courses: list[dict],
    learners: list[dict],
    enrollments: list[dict],
    assignments: list[dict],
    rubrics: list[dict],
    criteria: list[dict],
    submissions: list[dict],
    grades: list[dict],
    seed: int
) -> tuple[list[dict], dict[str, list[dict]]]:
    """
    Generate the 4 mandatory architectural anomaly scenarios in an isolated ground_truth dataset.
    Never corrupts or injects invalid records into the clean baseline dataset.
    Returns:
        anomaly_manifest: list of labeled anomaly descriptor records
        anomaly_datasets: dict containing invalid entity payloads for edge-case test harnesses
    """
    rng = np.random.default_rng(seed)
    
    anomalies = []
    
    # -------------------------------------------------------------
    # Scenario 1: Unenrolled learner submission (EX-01)
    # Trigger: A learner submits work for an assignment of a course they never enrolled in.
    # -------------------------------------------------------------
    enrolled_pairs = {(e["course_id"], e["learner_id"]) for e in enrollments}
    target_asn = assignments[0]
    target_aid = target_asn["assignment_id"]
    target_cid = target_asn["course_id"]
    
    # Find a learner definitely NOT enrolled in target_cid AND who has no existing submission for target_aid
    existing_sub_learners_for_aid = {s["learner_id"] for s in submissions if s["assignment_id"] == target_aid}
    unenrolled_lid = None
    for l in learners:
        lid_candidate = l["learner_id"]
        if (target_cid, lid_candidate) not in enrolled_pairs and lid_candidate not in existing_sub_learners_for_aid:
            unenrolled_lid = lid_candidate
            break
    if not unenrolled_lid:
        # Fallback: use a synthetic learner ID guaranteed not to exist in any real submission
        unenrolled_lid = "LNR-ANOM-999999"
        
    invalid_sub_id = f"SUB-{target_aid}-{unenrolled_lid}-01"
    invalid_sub = {
        "submission_id": invalid_sub_id,
        "assignment_id": target_aid,
        "learner_id": unenrolled_lid,
        "enrollment_id": "ENR-2026-000000", # Non-existent or mismatched enrollment
        "attempt_number": 1,
        "submitted_at": target_asn["due_date"],
        "status": SubmissionStatus.SUBMITTED.value,
        "is_late": False,
        "late_duration_seconds": 0,
        "late_penalty_percentage": 0.00,
        "raw_score": None,
        "final_score": None,
        "learner_notes": "Attempting submission without active course enrollment.",
        "created_at": target_asn["due_date"],
        "updated_at": target_asn["due_date"],
    }
    
    anomalies.append({
        "anomaly_id": "ANOM-2026-000001",
        "scenario_id": "EX-01",
        "scenario_name": "unenrolled_learner_submission",
        "entity_type": "submission",
        "entity_id": invalid_sub_id,
        "expected_error": "ERR_UNENROLLED_LEARNER",
        "http_status_expected": 403,
        "description": f"Learner {unenrolled_lid} submitted assignment {target_aid} without active enrollment in course {target_cid}.",
        "violation_field": "enrollment_id",
        "mitigation_protocol": "Abort transaction, reject submission with HTTP 403, record security audit entry.",
        "record_payload": invalid_sub
    })
    
    # -------------------------------------------------------------
    # Scenario 2: Grade exceeding rubric maximum (EX-02)
    # Trigger: Criteria scores sum to > 100.00 (e.g. 118.00) or final_score > assignment.max_score.
    # -------------------------------------------------------------
    sample_sub = submissions[0]
    sample_sub_id = sample_sub["submission_id"]
    corrupted_gid = f"GRD-CORRUPT-{sample_sub_id}"
    
    exceeding_grade = {
        "grade_id": corrupted_gid,
        "submission_id": sample_sub_id,
        "graded_by": "USR-INST-0001",
        "raw_score": 118.50, # Exceeds max 100.00!
        "late_penalty_applied": 0.00,
        "bonus_points": 0.00,
        "final_score": 118.50, # Exceeds max score!
        "is_final": True,
        "grade_status": GradeStatus.PUBLISHED.value,
        "graded_at": datetime.now(timezone.utc).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    
    anomalies.append({
        "anomaly_id": "ANOM-2026-000002",
        "scenario_id": "EX-02",
        "scenario_name": "grade_exceeding_rubric_max",
        "entity_type": "grade",
        "entity_id": corrupted_gid,
        "expected_error": "ERR_SCORE_EXCEEDS_MAX",
        "http_status_expected": 422,
        "description": f"Grade {corrupted_gid} has final_score 118.50, exceeding assignment max_score of 100.00.",
        "violation_field": "final_score",
        "mitigation_protocol": "Pydantic validator and DB check constraint chk_grade_scores intercept and abort transaction with HTTP 422.",
        "record_payload": exceeding_grade
    })
    
    # -------------------------------------------------------------
    # Scenario 3: Duplicate late penalty (EX-03)
    # Trigger: Regrading or appeal processing reapplies late penalty to already penalized score.
    # E.g. raw_score = 90.00, penalty = 10.00, final_score = 70.00 (deducted twice!).
    # -------------------------------------------------------------
    late_sub = None
    for s in submissions:
        if s.get("is_late") and float(s.get("late_penalty_percentage", 0)) >= 10.0:
            late_sub = s
            break
    if not late_sub:
        late_sub = submissions[0]
        
    late_sub_id = late_sub["submission_id"]
    dup_penalty_gid = f"GRD-DUPPEN-{late_sub_id}"
    
    # Intentionally subtract penalty twice: raw - (penalty * 2)
    raw_val = 90.00
    penalty_pct = 10.00
    single_penalty = 9.00
    corrupted_final = raw_val - (2 * single_penalty) # 72.00 instead of 81.00!
    
    dup_grade = {
        "grade_id": dup_penalty_gid,
        "submission_id": late_sub_id,
        "graded_by": "USR-INST-0002",
        "raw_score": raw_val,
        "late_penalty_applied": single_penalty * 2, # Compounded penalty deduction!
        "bonus_points": 0.00,
        "final_score": corrupted_final,
        "is_final": True,
        "grade_status": GradeStatus.PUBLISHED.value,
        "graded_at": datetime.now(timezone.utc).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    
    anomalies.append({
        "anomaly_id": "ANOM-2026-000003",
        "scenario_id": "EX-03",
        "scenario_name": "duplicate_late_penalty",
        "entity_type": "grade",
        "entity_id": dup_penalty_gid,
        "expected_error": "ERR_DUPLICATE_LATE_PENALTY",
        "http_status_expected": 422,
        "description": f"Late penalty of {single_penalty} was deducted twice, giving final_score {corrupted_final} instead of {raw_val - single_penalty}.",
        "violation_field": "late_penalty_applied",
        "mitigation_protocol": "Evaluation engine enforces idempotent penalty derivation directly from immutable submission metadata.",
        "record_payload": dup_grade
    })
    
    # -------------------------------------------------------------
    # Scenario 4: Appeal changing grade without audit history (EX-04)
    # Trigger: An appeal is approved and grade changed, but no corresponding AuditLog entry was written.
    # -------------------------------------------------------------
    target_grade = grades[0] if grades else exceeding_grade
    target_gid = target_grade["grade_id"]
    target_sub_id = target_grade["submission_id"]
    
    unadjudicated_appeal_id = "APP-2026-999999"
    unadjudicated_appeal = {
        "appeal_id": unadjudicated_appeal_id,
        "submission_id": target_sub_id,
        "grade_id": target_gid,
        "learner_id": "LNR-2026-000001",
        "reviewed_by": "USR-DEAN-0001",
        "status": AppealStatus.APPROVED.value,
        "reason_category": AppealReasonCategory.CALCULATION_ERROR.value,
        "learner_statement": "Contesting mathematical discrepancy.",
        "contested_criteria": None,
        "original_grade": 80.00,
        "requested_grade": 92.00,
        "final_grade": 92.00,
        "decision_notes": "Grade updated without registering required transactional AuditLog record.",
        "submitted_at": datetime.now(timezone.utc).isoformat(),
        "resolved_at": datetime.now(timezone.utc).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    
    anomalies.append({
        "anomaly_id": "ANOM-2026-000004",
        "scenario_id": "EX-04",
        "scenario_name": "appeal_grade_modification_without_audit",
        "entity_type": "appeal",
        "entity_id": unadjudicated_appeal_id,
        "expected_error": "ERR_MISSING_AUDIT_LOG",
        "http_status_expected": 500,
        "description": f"Appeal {unadjudicated_appeal_id} approved with grade modification to 92.00, but lacks mandatory corresponding AuditLog record.",
        "violation_field": "audit_log",
        "mitigation_protocol": "Atomic transaction manager and PostgreSQL trigger rollback transaction if AuditLog insert is absent.",
        "record_payload": unadjudicated_appeal
    })
    
    anomaly_datasets = {
        "invalid_submission": invalid_sub,
        "exceeding_grade": exceeding_grade,
        "duplicate_penalty_grade": dup_grade,
        "unadjudicated_appeal": unadjudicated_appeal,
    }
    
    return anomalies, anomaly_datasets
