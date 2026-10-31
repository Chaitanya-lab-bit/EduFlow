import hashlib
from datetime import datetime, timedelta
from decimal import Decimal
import numpy as np
from backend.models.enums import (
    SubmissionStatus, ResubmissionStatus, GradeStatus,
    FeedbackVisibility
)
from data_generation.generators.artifact_generator import FILE_EXT_MAP, MIME_TYPE_MAP

RESUBMISSION_REASONS = [
    "Incorporated reviewer recommendations on code modularity and documentation.",
    "Refactored exception handling and added missing boundary test cases.",
    "Corrected dataset schema normalization and addressed evaluator comments.",
    "Resolved performance bottlenecks in consumer loop and revised architectural report."
]

def generate_resubmissions(
    submissions: list[dict],
    assignments: list[dict],
    rubrics: list[dict],
    criteria: list[dict],
    grades: list[dict],
    resubmission_rate: float,
    seed: int,
    ssh_counter_start: int = 1
) -> tuple[list[dict], list[dict], list[dict], list[dict], list[dict], list[dict], list[dict], int]:
    """
    Generate deterministic resubmissions (attempt 2), linking them to original attempts.
    Returns:
        resubmissions: list of resubmission dicts
        new_submissions: list of attempt 2 submission dicts
        new_artifacts: list of attempt 2 artifact dicts
        new_grades: list of attempt 2 grade dicts
        new_criteria_scores: list of attempt 2 criterion score dicts
        new_feedback: list of attempt 2 feedback dicts
        status_histories: list of status history records
        next_ssh_counter: updated counter
    """
    rng = np.random.default_rng(seed)
    
    assignment_lookup = {a["assignment_id"]: a for a in assignments}
    grade_by_submission = {g["submission_id"]: g for g in grades}
    
    # Active rubric lookup
    active_rubric_by_assignment = {}
    for r in rubrics:
        if r.get("is_active", True) and r["assignment_id"] not in active_rubric_by_assignment:
            active_rubric_by_assignment[r["assignment_id"]] = r
            
    criteria_by_rubric = {}
    for c in criteria:
        criteria_by_rubric.setdefault(c["rubric_id"], []).append(c)
    for r_id in criteria_by_rubric:
        criteria_by_rubric[r_id].sort(key=lambda x: x["display_order"])
        
    # Eligible candidates: attempt 1 submissions that were graded and have time before cutoff
    candidates = []
    for sub in submissions:
        if sub["attempt_number"] != 1 or sub["submission_id"] not in grade_by_submission:
            continue
        aid = sub["assignment_id"]
        assignment = assignment_lookup[aid]
        cutoff_date = datetime.fromisoformat(assignment["cutoff_date"])
        sub_time = datetime.fromisoformat(sub["submitted_at"])
        # Must have at least 6 hours remaining before cutoff to resubmit
        if cutoff_date - sub_time > timedelta(hours=6):
            candidates.append(sub)
            
    # Sort candidates by score ascending (lowest scores get first chance at resubmission)
    candidates.sort(key=lambda s: float(s["final_score"] if s["final_score"] is not None else 100.0))
    
    target_count = int(np.round(len(submissions) * resubmission_rate))
    chosen_submissions = candidates[:target_count]
    
    resubmissions = []
    new_submissions = []
    new_artifacts = []
    new_grades = []
    new_criteria_scores = []
    new_feedback = []
    status_histories = []
    ssh_counter = ssh_counter_start
    
    for r_idx, orig_sub in enumerate(chosen_submissions, start=1):
        orig_sub_id = orig_sub["submission_id"]
        orig_grade = grade_by_submission[orig_sub_id]
        aid = orig_sub["assignment_id"]
        lid = orig_sub["learner_id"]
        enr_id = orig_sub["enrollment_id"]
        assignment = assignment_lookup[aid]
        cid = assignment["course_id"]
        cutoff_date = datetime.fromisoformat(assignment["cutoff_date"])
        due_date = datetime.fromisoformat(assignment["due_date"])
        max_score = float(assignment["max_score"])
        late_penalty_per_day = float(assignment["late_penalty_per_day"])
        max_late_days = int(assignment["max_late_days"])
        grace_minutes = int(assignment["grace_period_minutes"])
        
        orig_graded_time = datetime.fromisoformat(orig_grade["graded_at"])
        
        # Timing for resubmission: between graded_at and cutoff_date
        resub_id = f"RSB-2026-{r_idx:06d}"
        new_sub_id = f"SUB-{aid}-{lid}-02"
        
        # Requested at: shortly after grade publication
        req_offset_mins = int(rng.integers(30, 360))
        requested_at = orig_graded_time + timedelta(minutes=req_offset_mins)
        if requested_at >= cutoff_date:
            requested_at = cutoff_date - timedelta(hours=4)
            
        reviewed_at = requested_at + timedelta(minutes=int(rng.integers(15, 60)))
        if reviewed_at >= cutoff_date:
            reviewed_at = requested_at + timedelta(minutes=5)
            
        # Submission time of attempt 2: between reviewed_at and cutoff_date
        remaining_secs = (cutoff_date - reviewed_at).total_seconds()
        if remaining_secs > 3600:
            resub_secs = int(rng.integers(1800, min(int(remaining_secs) - 60, 86400)))
            new_sub_time = reviewed_at + timedelta(seconds=resub_secs)
        else:
            new_sub_time = cutoff_date - timedelta(minutes=10)
            
        # Lateness calculation for attempt 2
        if new_sub_time <= due_date + timedelta(minutes=grace_minutes):
            is_late = False
            late_seconds = 0
            late_penalty_pct = 0.00
        else:
            is_late = True
            late_seconds = int((new_sub_time - due_date).total_seconds())
            grace_seconds = grace_minutes * 60
            days_late = int(np.ceil((late_seconds - grace_seconds) / 86400.0))
            days_late = max(1, min(days_late, max_late_days))
            late_penalty_pct = round(days_late * late_penalty_per_day, 2)
            
        # Update original submission status: GRADED -> RESUBMITTED
        orig_sub["status"] = SubmissionStatus.RESUBMITTED.value
        orig_sub["updated_at"] = new_sub_time.isoformat()
        
        ssh_id1 = f"SSH-2026-{ssh_counter:06d}"
        status_histories.append({
            "history_id": ssh_id1,
            "submission_id": orig_sub_id,
            "old_status": SubmissionStatus.GRADED.value,
            "new_status": SubmissionStatus.RESUBMITTED.value,
            "changed_by": lid,
            "change_reason": "Subsequent attempt submitted under academic resubmission policy.",
            "changed_at": new_sub_time.isoformat(),
        })
        ssh_counter += 1
        
        # Create Resubmission tracking record
        inst_num = (abs(hash(cid)) % 25) + 1
        evaluator_id = f"USR-INST-{inst_num:04d}"
        reason_txt = RESUBMISSION_REASONS[(r_idx - 1) % len(RESUBMISSION_REASONS)]
        
        resubmissions.append({
            "resubmission_id": resub_id,
            "original_submission_id": orig_sub_id,
            "new_submission_id": new_sub_id,
            "reason": reason_txt,
            "change_summary": "Revised implementation and enhanced documentation per grading notes.",
            "approved_by": evaluator_id,
            "status": ResubmissionStatus.SUBMITTED.value,
            "requested_at": requested_at.isoformat(),
            "reviewed_at": reviewed_at.isoformat(),
            "created_at": requested_at.isoformat(),
            "updated_at": reviewed_at.isoformat(),
        })
        
        # Create Attempt 2 Submission record
        new_sub = {
            "submission_id": new_sub_id,
            "assignment_id": aid,
            "learner_id": lid,
            "enrollment_id": enr_id,
            "attempt_number": 2,
            "submitted_at": new_sub_time.isoformat(),
            "status": SubmissionStatus.GRADED.value,
            "is_late": is_late,
            "late_duration_seconds": late_seconds,
            "late_penalty_percentage": late_penalty_pct,
            "raw_score": None,
            "final_score": None,
            "learner_notes": "Attempt 2: addressed feedback and updated implementation.",
            "created_at": (new_sub_time - timedelta(minutes=15)).isoformat(),
            "updated_at": new_sub_time.isoformat(),
        }
        
        # Artifacts for Attempt 2
        art_counter = 1
        for a_type in assignment["required_artifact_types"]:
            art_id = f"ART-{new_sub_id}-{art_counter:02d}"
            ext = FILE_EXT_MAP.get(a_type, "bin")
            mime = MIME_TYPE_MAP.get(a_type, "application/octet-stream")
            fname = f"{lid}_{aid.lower()}_v2_{a_type}.{ext}"
            fsize = int(rng.integers(102400, 10485760))
            h = hashlib.sha256(f"{art_id}-{fname}-{fsize}-{seed}".encode()).hexdigest()
            
            new_artifacts.append({
                "artifact_id": art_id,
                "submission_id": new_sub_id,
                "artifact_type": a_type,
                "file_name": fname,
                "file_size_bytes": fsize,
                "mime_type": mime,
                "storage_uri": f"s3://eduflow-artifacts/{cid.lower()}/{aid.lower()}/{fname}",
                "checksum_sha256": h,
                "is_verified": True,
                "uploaded_at": (new_sub_time - timedelta(minutes=5)).isoformat(),
            })
            art_counter += 1
            
        # Status history for Attempt 2: draft -> submitted
        ssh_id2 = f"SSH-2026-{ssh_counter:06d}"
        status_histories.append({
            "history_id": ssh_id2,
            "submission_id": new_sub_id,
            "old_status": SubmissionStatus.DRAFT.value,
            "new_status": SubmissionStatus.SUBMITTED.value,
            "changed_by": lid,
            "change_reason": "Resubmission attempt 2 submitted by learner.",
            "changed_at": new_sub_time.isoformat(),
        })
        ssh_counter += 1
        
        # Grade Attempt 2: Learner improves score!
        orig_raw = float(orig_grade["raw_score"])
        score_boost = float(rng.uniform(10.0, 22.0))
        new_raw = round(min(max_score, orig_raw + score_boost), 2)
        
        rubric = active_rubric_by_assignment[aid]
        crit_list = criteria_by_rubric[rubric["rubric_id"]]
        num_crit = len(crit_list)
        
        crit_scores = []
        rem_raw = new_raw
        for c_i, crit in enumerate(crit_list):
            c_max = float(crit["max_points"])
            if c_i == num_crit - 1:
                c_sc = round(rem_raw, 2)
                if c_sc < 0:
                    c_sc = 0.0
                elif c_sc > c_max:
                    diff = c_sc - c_max
                    c_sc = c_max
                    for prev_i in range(len(crit_scores)):
                        h_room = float(crit_list[prev_i]["max_points"]) - crit_scores[prev_i]
                        trans = min(diff, h_room)
                        crit_scores[prev_i] = round(crit_scores[prev_i] + trans, 2)
                        diff = round(diff - trans, 2)
                        if diff <= 0:
                            break
            else:
                target_sc = new_raw * (c_max / float(rubric["total_points"])) + float(rng.normal(0, 0.3))
                c_sc = round(max(0.0, min(target_sc, c_max)), 2)
                rem_max_other = sum(float(crit_list[k]["max_points"]) for k in range(c_i + 1, num_crit))
                if rem_raw - c_sc > rem_max_other:
                    c_sc = round(rem_raw - rem_max_other, 2)
                elif rem_raw - c_sc < 0:
                    c_sc = round(rem_raw, 2)
                rem_raw = round(rem_raw - c_sc, 2)
            crit_scores.append(c_sc)
            
        new_raw = round(sum(crit_scores), 2)
        
        if is_late and late_penalty_pct > 0:
            penalty_applied = round(new_raw * (late_penalty_pct / 100.0), 2)
        else:
            penalty_applied = 0.00
            
        new_final = round(max(0.0, min(new_raw - penalty_applied, max_score)), 2)
        
        new_graded_time = new_sub_time + timedelta(days=int(rng.integers(1, 3)), hours=int(rng.integers(1, 10)))
        
        new_sub["raw_score"] = new_raw
        new_sub["final_score"] = new_final
        new_sub["updated_at"] = new_graded_time.isoformat()
        new_submissions.append(new_sub)
        
        # Create Grade 2 record
        grade_2_id = f"GRD-{new_sub_id}"
        grade_record = {
            "grade_id": grade_2_id,
            "submission_id": new_sub_id,
            "graded_by": evaluator_id,
            "raw_score": new_raw,
            "late_penalty_applied": penalty_applied,
            "bonus_points": 0.00,
            "final_score": new_final,
            "is_final": True,
            "grade_status": GradeStatus.PUBLISHED.value,
            "graded_at": new_graded_time.isoformat(),
            "created_at": new_graded_time.isoformat(),
            "updated_at": new_graded_time.isoformat(),
        }
        new_grades.append(grade_record)
        
        # Criteria scores for Attempt 2
        for c_idx, (crit, score) in enumerate(zip(crit_list, crit_scores), start=1):
            score_id = f"GCS-{grade_2_id}-{c_idx:02d}"
            new_criteria_scores.append({
                "score_id": score_id,
                "grade_id": grade_2_id,
                "criterion_id": crit["criterion_id"],
                "score_awarded": score,
                "evaluator_comment": "Noticeable improvement in resubmitted revision.",
                "created_at": new_graded_time.isoformat(),
            })
            
        # Status history for Attempt 2: submitted -> graded
        ssh_id3 = f"SSH-2026-{ssh_counter:06d}"
        status_histories.append({
            "history_id": ssh_id3,
            "submission_id": new_sub_id,
            "old_status": SubmissionStatus.SUBMITTED.value,
            "new_status": SubmissionStatus.GRADED.value,
            "changed_by": evaluator_id,
            "change_reason": "Resubmission evaluated and revised grade published.",
            "changed_at": new_graded_time.isoformat(),
        })
        ssh_counter += 1
        
        # Feedback for Attempt 2
        fbk_id = f"FBK-{grade_2_id}-01"
        new_feedback.append({
            "feedback_id": fbk_id,
            "grade_id": grade_2_id,
            "submission_id": new_sub_id,
            "author_id": evaluator_id,
            "visibility": FeedbackVisibility.LEARNER_VISIBLE.value,
            "general_comments": "Commendable progress on Attempt 2. Feedback was effectively synthesized.",
            "strengths": "Demonstrated initiative in rectifying architectural concerns.",
            "areas_for_improvement": "Maintain this standard of defensive testing on upcoming projects.",
            "published_at": (new_graded_time + timedelta(minutes=5)).isoformat(),
            "created_at": (new_graded_time + timedelta(minutes=5)).isoformat(),
            "updated_at": (new_graded_time + timedelta(minutes=5)).isoformat(),
        })
        
    return (
        resubmissions,
        new_submissions,
        new_artifacts,
        new_grades,
        new_criteria_scores,
        new_feedback,
        status_histories,
        ssh_counter
    )
