from datetime import datetime, timezone, timedelta
import numpy as np
from backend.models.enums import SubmissionStatus

def generate_submissions(
    assignments: list[dict],
    enrollments: list[dict],
    target_count: int,
    seed: int
) -> tuple[list[dict], list[dict]]:
    """
    Generate initial submission attempts (attempt 1) and status history records.
    Returns:
        submissions: list of initial submission dicts
        status_histories: list of status history event dicts
    """
    rng = np.random.default_rng(seed)
    
    submissions = []
    status_histories = []
    
    # Index enrollments by course_id for fast valid candidate selection
    enrollments_by_course = {}
    for enr in enrollments:
        cid = enr["course_id"]
        enrollments_by_course.setdefault(cid, []).append(enr)
        
    assignment_lookup = {a["assignment_id"]: a for a in assignments}
    assignment_ids = list(assignment_lookup.keys())
    
    created_pairs = set()
    ssh_counter = 1
    
    # Pre-generate distributions for speed and determinism
    timing_rolls = rng.random(target_count)
    hours_early_samples = np.abs(rng.normal(14.0, 8.0, target_count))
    exp_days_samples = rng.exponential(1.2, target_count)
    grace_minute_samples = rng.integers(1, 15, target_count)
    
    i = 0
    generated = 0
    num_assignments = len(assignment_ids)
    
    while generated < target_count:
        aid = assignment_ids[i % num_assignments]
        assignment = assignment_lookup[aid]
        cid = assignment["course_id"]
        
        candidates = enrollments_by_course.get(cid, [])
        if not candidates:
            i += 1
            continue
            
        cand_idx = (i // num_assignments + i) % len(candidates)
        enr = candidates[cand_idx]
        lid = enr["learner_id"]
        enr_id = enr["enrollment_id"]
        
        pair_key = (aid, lid)
        if pair_key in created_pairs:
            # Deterministically find next available enrolled learner for this assignment
            found = False
            for offset in range(1, len(candidates)):
                alt_enr = candidates[(cand_idx + offset) % len(candidates)]
                alt_lid = alt_enr["learner_id"]
                if (aid, alt_lid) not in created_pairs:
                    enr = alt_enr
                    lid = alt_lid
                    enr_id = alt_enr["enrollment_id"]
                    found = True
                    break
            if not found:
                i += 1
                continue
                
        created_pairs.add((aid, lid))
        
        sub_id = f"SUB-{aid}-{lid}-01"
        due_date = datetime.fromisoformat(assignment["due_date"])
        cutoff_date = datetime.fromisoformat(assignment["cutoff_date"])
        grace_minutes = assignment["grace_period_minutes"]
        max_late_days = assignment["max_late_days"]
        late_penalty_per_day = assignment["late_penalty_per_day"]
        
        idx = generated
        timing_roll = timing_rolls[idx]
        
        if timing_roll < 0.80:
            # On-time: Normal(14h early, 8h stddev) bounded
            hours_early = max(0.1, min(float(hours_early_samples[idx]), 168.0))
            sub_time = due_date - timedelta(hours=hours_early)
            is_late = False
            late_seconds = 0
            late_penalty_pct = 0.00
        elif timing_roll < 0.85:
            # Grace period: within grace_period_minutes
            grace_secs = int(grace_minute_samples[idx] * 60)
            sub_time = due_date + timedelta(seconds=grace_secs)
            is_late = False
            late_seconds = grace_secs
            late_penalty_pct = 0.00
        else:
            # Late: Exponential(1.2 days) up to cutoff
            exp_days = min(float(exp_days_samples[idx]), float(max_late_days))
            late_seconds = int(exp_days * 86400)
            sub_time = due_date + timedelta(seconds=late_seconds)
            if sub_time > cutoff_date:
                sub_time = cutoff_date - timedelta(minutes=5)
                late_seconds = int((sub_time - due_date).total_seconds())
                
            is_late = True
            grace_seconds = grace_minutes * 60
            # BR-02: Recheck — exponential draw may produce a late_seconds < grace window
            if late_seconds <= grace_seconds:
                is_late = False
                late_penalty_pct = 0.00
            else:
                days_late = int(np.ceil((late_seconds - grace_seconds) / 86400.0))
                days_late = max(1, min(days_late, max_late_days))
                late_penalty_pct = round(days_late * late_penalty_per_day, 2)
            
        submission_record = {
            "submission_id": sub_id,
            "assignment_id": aid,
            "learner_id": lid,
            "enrollment_id": enr_id,
            "attempt_number": 1,
            "submitted_at": sub_time.isoformat(),
            "status": SubmissionStatus.SUBMITTED.value,
            "is_late": is_late,
            "late_duration_seconds": late_seconds,
            "late_penalty_percentage": late_penalty_pct,
            "raw_score": None,
            "final_score": None,
            "learner_notes": "Deliverable attached for grading.",
            "created_at": (sub_time - timedelta(minutes=10)).isoformat(),
            "updated_at": sub_time.isoformat(),
        }
        submissions.append(submission_record)
        
        # Status History entry for submission
        ssh_id = f"SSH-2026-{ssh_counter:06d}"
        status_histories.append({
            "history_id": ssh_id,
            "submission_id": sub_id,
            "old_status": SubmissionStatus.DRAFT.value,
            "new_status": SubmissionStatus.SUBMITTED.value,
            "changed_by": lid,
            "change_reason": "Submission artifacts uploaded and submitted by learner.",
            "changed_at": sub_time.isoformat(),
        })
        ssh_counter += 1
        
        generated += 1
        i += 1
        
    return submissions, status_histories
