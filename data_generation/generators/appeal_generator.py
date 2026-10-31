from datetime import datetime, timedelta
import numpy as np
from backend.models.enums import (
    AppealStatus, AppealReasonCategory, GradeStatus,
    SubmissionStatus, AuditActionType
)

STATEMENT_TEMPLATES = [
    "I believe Criterion 2 was evaluated overly strictly regarding algorithmic efficiency, as my solution exhibits O(N log N) runtime.",
    "A calculation error appears to have occurred in summing the rubric criteria points; the raw scores add up to a higher total.",
    "My documentation clearly details edge case handling for concurrent connections, which was marked as missing in Criterion 4.",
    "Requesting reconsideration of the late penalty; our team experienced an institutional network outage right at the deadline."
]

DECISION_NOTES_REJECTED = [
    "Comprehensive review of deliverable and rubric confirms evaluator's original scoring is accurate and objective.",
    "The rubric guidelines were applied correctly according to course specifications. Original evaluation upheld.",
    "Re-examination of test cases revealed that boundary conditions were indeed omitted. Grade remains unchanged."
]

DECISION_NOTES_APPROVED_CALC = [
    "Verified score tabulation error in Criterion itemization. Score adjusted upwards to reflect true criterion sum.",
    "Mathematical calculation discrepancy confirmed upon audit. Grade adjusted per academic integrity protocol."
]

DECISION_NOTES_APPROVED_RUBRIC = [
    "Academic arbiter review determined that student's alternative architecture satisfies Criterion 2 requirements.",
    "Re-evaluation of supplementary documentation confirms modularity standards were satisfied. Partial points restored."
]

def generate_appeals(
    grades: list[dict],
    submissions: list[dict],
    appeal_rate: float,
    seed: int,
    audit_counter_start: int = 1
) -> tuple[list[dict], list[dict], int]:
    """
    Generate deterministic appeals and corresponding atomic audit log entries for approved appeals.
    Returns:
        appeals: list of appeal dictionaries
        audit_logs: list of audit log dictionaries
        next_audit_counter: updated counter for audit logs
    """
    rng = np.random.default_rng(seed)
    
    submission_lookup = {s["submission_id"]: s for s in submissions}
    
    # Filter eligible grades: published grades on active submissions
    eligible_grades = []
    for g in grades:
        sub = submission_lookup.get(g["submission_id"])
        if sub and sub["status"] in [SubmissionStatus.GRADED.value, SubmissionStatus.APPEALED.value]:
            eligible_grades.append((g, sub))
            
    num_appeals = int(np.round(len(eligible_grades) * appeal_rate))
    
    # Select deterministically using rng permutation
    indices = rng.permutation(len(eligible_grades))[:num_appeals]
    selected_pairs = [eligible_grades[i] for i in indices]
    
    appeals = []
    audit_logs = []
    audit_counter = audit_counter_start
    
    for a_idx, (grade, sub) in enumerate(selected_pairs, start=1):
        appeal_id = f"APP-2026-{a_idx:06d}"
        sub_id = grade["submission_id"]
        gid = grade["grade_id"]
        lid = sub["learner_id"]
        aid = sub["assignment_id"]
        graded_time = datetime.fromisoformat(grade["graded_at"])
        
        # Submitted within 7-day appeal window (e.g., 1 to 5 days after graded)
        days_after = int(rng.integers(1, 6))
        hours_after = int(rng.integers(0, 12))
        appeal_sub_time = graded_time + timedelta(days=days_after, hours=hours_after)
        
        # Resolution time: 1 to 3 days after appeal submission
        resolved_time = appeal_sub_time + timedelta(days=int(rng.integers(1, 4)), hours=int(rng.integers(1, 8)))
        
        arbiter_num = (abs(hash(aid)) % 10) + 1
        reviewed_by = f"USR-DEAN-{arbiter_num:04d}"
        
        orig_grade = float(grade["final_score"])
        requested_grade = round(min(100.0, orig_grade + float(rng.uniform(5.0, 15.0))), 2)
        
        # Outcome distribution: 60% rejected, 30% approved (rubric), 10% approved (calculation)
        roll = rng.random()
        
        if roll < 0.60:
            # REJECTED
            status = AppealStatus.REJECTED.value
            category = AppealReasonCategory.RUBRIC_MISINTERPRETATION.value
            statement = STATEMENT_TEMPLATES[0]
            final_grade = orig_grade
            decision_notes = DECISION_NOTES_REJECTED[int(rng.integers(0, len(DECISION_NOTES_REJECTED)))]
        elif roll < 0.90:
            # APPROVED (minor rubric misinterpretation adjustment)
            status = AppealStatus.APPROVED.value
            category = AppealReasonCategory.RUBRIC_MISINTERPRETATION.value
            statement = STATEMENT_TEMPLATES[2]
            adj = float(rng.uniform(3.0, 8.0))
            final_grade = round(min(100.0, orig_grade + adj), 2)
            decision_notes = DECISION_NOTES_APPROVED_RUBRIC[int(rng.integers(0, len(DECISION_NOTES_APPROVED_RUBRIC)))]
        else:
            # APPROVED (calculation error adjustment)
            status = AppealStatus.APPROVED.value
            category = AppealReasonCategory.CALCULATION_ERROR.value
            statement = STATEMENT_TEMPLATES[1]
            adj = float(rng.uniform(10.0, 15.0))
            final_grade = round(min(100.0, orig_grade + adj), 2)
            decision_notes = DECISION_NOTES_APPROVED_CALC[int(rng.integers(0, len(DECISION_NOTES_APPROVED_CALC)))]
            
        appeal_record = {
            "appeal_id": appeal_id,
            "submission_id": sub_id,
            "grade_id": gid,
            "learner_id": lid,
            "reviewed_by": reviewed_by,
            "status": status,
            "reason_category": category,
            "learner_statement": statement,
            "contested_criteria": None,
            "original_grade": orig_grade,
            "requested_grade": requested_grade,
            "final_grade": final_grade,
            "decision_notes": decision_notes,
            "submitted_at": appeal_sub_time.isoformat(),
            "resolved_at": resolved_time.isoformat(),
            "created_at": appeal_sub_time.isoformat(),
            "updated_at": resolved_time.isoformat(),
        }
        appeals.append(appeal_record)
        
        # When approved: mutate grade and submission atomically, and write AuditLog entry!
        if status == AppealStatus.APPROVED.value:
            old_score = grade["final_score"]
            old_status = grade["grade_status"]
            
            grade["final_score"] = final_grade
            grade["grade_status"] = GradeStatus.REVISED.value
            grade["updated_at"] = resolved_time.isoformat()
            
            sub["final_score"] = final_grade
            sub["status"] = SubmissionStatus.APPEALED.value
            sub["updated_at"] = resolved_time.isoformat()
            
            # Atomic AuditLog entry
            audit_id = f"AUD-2026-{audit_counter:06d}"
            audit_record = {
                "audit_id": audit_id,
                "entity_name": "grade",
                "entity_id": gid,
                "action": AuditActionType.APPEAL_DECISION.value,
                "actor_id": reviewed_by,
                "actor_role": "academic_committee",
                "timestamp": resolved_time.isoformat(),
                "old_values": {"final_score": old_score, "grade_status": old_status},
                "new_values": {"final_score": final_grade, "grade_status": GradeStatus.REVISED.value},
                "client_ip": "192.168.1.105",
                "user_agent": "EduFlow-AdjudicationPanel/1.0",
            }
            audit_logs.append(audit_record)
            audit_counter += 1
            
    return appeals, audit_logs, audit_counter
