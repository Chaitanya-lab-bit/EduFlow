from datetime import datetime, timedelta
from decimal import Decimal
import numpy as np
from backend.models.enums import GradeStatus, SubmissionStatus

def generate_grades(
    submissions: list[dict],
    assignments: list[dict],
    rubrics: list[dict],
    criteria: list[dict],
    competency_map: dict[str, float],
    grade_rate: float,
    seed: int,
    ssh_counter_start: int = 1
) -> tuple[list[dict], list[dict], list[dict], int]:
    """
    Generate deterministic grades, itemized criterion scores, and status transitions.
    Returns:
        grades: list of grade dictionaries
        grade_criterion_scores: list of grade_criterion_score dictionaries
        status_histories: additional status history records
        next_ssh_counter: updated counter for status history records
    """
    rng = np.random.default_rng(seed)
    
    assignment_lookup = {a["assignment_id"]: a for a in assignments}
    
    # Map assignment_id -> active rubric
    active_rubric_by_assignment = {}
    for r in rubrics:
        if r.get("is_active", True) and r["assignment_id"] not in active_rubric_by_assignment:
            active_rubric_by_assignment[r["assignment_id"]] = r
            
    # Map rubric_id -> list of criteria sorted by display_order
    criteria_by_rubric = {}
    for c in criteria:
        criteria_by_rubric.setdefault(c["rubric_id"], []).append(c)
    for r_id in criteria_by_rubric:
        criteria_by_rubric[r_id].sort(key=lambda x: x["display_order"])
        
    grades = []
    grade_criterion_scores = []
    status_histories = []
    ssh_counter = ssh_counter_start
    
    # Pre-generate difficulty factor per assignment: Uniform(0.9, 1.1)
    assignment_difficulty = {}
    for a in assignments:
        aid = a["assignment_id"]
        # Seed difficulty deterministically by assignment_id hash
        a_seed = (seed + hash(aid)) % (2**31 - 1)
        a_rng = np.random.default_rng(a_seed)
        assignment_difficulty[aid] = float(a_rng.uniform(0.90, 1.10))
        
    for sub in submissions:
        # Determine if this submission is graded (based on grade_rate)
        if rng.random() > grade_rate:
            continue
            
        sub_id = sub["submission_id"]
        aid = sub["assignment_id"]
        lid = sub["learner_id"]
        sub_time = datetime.fromisoformat(sub["submitted_at"])
        assignment = assignment_lookup[aid]
        cid = assignment["course_id"]
        max_score = float(assignment["max_score"])
        
        rubric = active_rubric_by_assignment.get(aid)
        if not rubric:
            continue
        crit_list = criteria_by_rubric.get(rubric["rubric_id"], [])
        if not crit_list:
            continue
            
        # 1. Calculate Raw Score from competency and assignment difficulty
        base_comp = competency_map.get(lid, 75.0)
        diff = assignment_difficulty.get(aid, 1.0)
        mean_score = base_comp * diff
        sampled_score = float(rng.normal(mean_score, 6.0))
        raw_score = round(max(0.0, min(sampled_score, max_score)), 2)
        
        # 2. Decompose Raw Score into itemized criteria scores
        num_crit = len(crit_list)
        crit_scores = []
        remaining_raw = raw_score
        
        for idx, crit in enumerate(crit_list):
            crit_max = float(crit["max_points"])
            if idx == num_crit - 1:
                # Last criterion gets exact remaining points to ensure sum == raw_score
                c_score = round(remaining_raw, 2)
                # Safeguard against floating clamp edge cases
                if c_score < 0:
                    c_score = 0.0
                elif c_score > crit_max:
                    excess = c_score - crit_max
                    c_score = crit_max
                    # redistribute excess to earlier criteria with headroom
                    for prev_idx in range(len(crit_scores)):
                        headroom = float(crit_list[prev_idx]["max_points"]) - crit_scores[prev_idx]
                        transfer = min(excess, headroom)
                        crit_scores[prev_idx] = round(crit_scores[prev_idx] + transfer, 2)
                        excess = round(excess - transfer, 2)
                        if excess <= 0:
                            break
            else:
                # Proportional score with small random variation
                prop = crit_max / float(rubric["total_points"])
                target_crit = raw_score * prop + float(rng.normal(0, 0.4))
                c_score = round(max(0.0, min(target_crit, crit_max)), 2)
                # Don't let remaining_raw become negative or leave impossible remainder
                remaining_max_other = sum(float(crit_list[k]["max_points"]) for k in range(idx + 1, num_crit))
                if remaining_raw - c_score > remaining_max_other:
                    c_score = round(remaining_raw - remaining_max_other, 2)
                elif remaining_raw - c_score < 0:
                    c_score = round(remaining_raw, 2)
                remaining_raw = round(remaining_raw - c_score, 2)
                
            crit_scores.append(c_score)
            
        # Reconcile raw_score exactly to sum of criteria scores
        raw_score = round(sum(crit_scores), 2)
        
        # 3. Apply Late Penalty
        late_penalty_pct = float(sub.get("late_penalty_percentage", 0.0))
        if sub.get("is_late", False) and late_penalty_pct > 0:
            late_penalty_applied = round(raw_score * (late_penalty_pct / 100.0), 2)
        else:
            late_penalty_applied = 0.00
            
        bonus_points = 0.00
        final_score = round(max(0.0, min(raw_score - late_penalty_applied + bonus_points, max_score)), 2)
        
        # Evaluator and timestamp
        inst_num = (abs(hash(cid)) % 25) + 1
        graded_by = f"USR-INST-{inst_num:04d}"
        days_after = int(rng.integers(1, 4))
        hours_after = int(rng.integers(1, 12))
        graded_at = sub_time + timedelta(days=days_after, hours=hours_after)
        
        # Update submission record
        sub["raw_score"] = raw_score
        sub["final_score"] = final_score
        sub["status"] = SubmissionStatus.GRADED.value
        sub["updated_at"] = graded_at.isoformat()
        
        grade_id = f"GRD-{sub_id}"
        grade_record = {
            "grade_id": grade_id,
            "submission_id": sub_id,
            "graded_by": graded_by,
            "raw_score": raw_score,
            "late_penalty_applied": late_penalty_applied,
            "bonus_points": bonus_points,
            "final_score": final_score,
            "is_final": True,
            "grade_status": GradeStatus.PUBLISHED.value,
            "graded_at": graded_at.isoformat(),
            "created_at": graded_at.isoformat(),
            "updated_at": graded_at.isoformat(),
        }
        grades.append(grade_record)
        
        # Itemized Criterion Scores
        for c_idx, (crit, score) in enumerate(zip(crit_list, crit_scores), start=1):
            crit_max = float(crit["max_points"])
            pct = (score / crit_max) if crit_max > 0 else 1.0
            if pct >= 0.90:
                comment = "Exemplary solution demonstrating comprehensive mastery."
            elif pct >= 0.75:
                comment = "Competent delivery meeting primary requirements with minor flaws."
            elif pct >= 0.60:
                comment = "Adequate effort; incomplete edge case handling observed."
            else:
                comment = "Significant gaps in required deliverables and specifications."
                
            score_id = f"GCS-{grade_id}-{c_idx:02d}"
            gcs_record = {
                "score_id": score_id,
                "grade_id": grade_id,
                "criterion_id": crit["criterion_id"],
                "score_awarded": score,
                "evaluator_comment": comment,
                "created_at": graded_at.isoformat(),
            }
            grade_criterion_scores.append(gcs_record)
            
        # Submission status history transition: SUBMITTED -> GRADED
        ssh_id = f"SSH-2026-{ssh_counter:06d}"
        status_histories.append({
            "history_id": ssh_id,
            "submission_id": sub_id,
            "old_status": SubmissionStatus.SUBMITTED.value,
            "new_status": SubmissionStatus.GRADED.value,
            "changed_by": graded_by,
            "change_reason": "Assessment evaluated against rubric and grade published.",
            "changed_at": graded_at.isoformat(),
        })
        ssh_counter += 1
        
    return grades, grade_criterion_scores, status_histories, ssh_counter
