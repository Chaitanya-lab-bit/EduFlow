from datetime import datetime, timezone, timedelta
import numpy as np
from backend.models.enums import EnrollmentStatus

def generate_enrollments(
    courses: list[dict],
    learners: list[dict],
    min_per_learner: int,
    max_per_learner: int,
    seed: int
) -> tuple[list[dict], dict[tuple[str, str], str]]:
    """
    Generate deterministic enrollments ensuring every learner has valid course associations.
    Returns:
        enrollments: list of enrollment dictionaries
        enrollment_map: lookup dict mapping (course_id, learner_id) -> enrollment_id
    """
    rng = np.random.default_rng(seed)
    enrollments = []
    enrollment_map = {}
    
    course_ids = [c["course_id"] for c in courses]
    num_courses = len(course_ids)
    
    enr_counter = 1
    base_time = datetime(2026, 8, 20, 9, 0, 0, tzinfo=timezone.utc)
    
    for learner in learners:
        lid = learner["learner_id"]
        # Determine number of course enrollments for this learner
        k = int(rng.integers(min_per_learner, max_per_learner + 1))
        k = min(k, num_courses)
        
        # Pick k distinct courses deterministically
        chosen_indices = rng.choice(num_courses, size=k, replace=False)
        for idx in chosen_indices:
            cid = course_ids[idx]
            enr_id = f"ENR-2026-{enr_counter:06d}"
            
            enrolled_at = base_time + timedelta(minutes=int(rng.integers(0, 7200)))
            
            enrollment_record = {
                "enrollment_id": enr_id,
                "course_id": cid,
                "learner_id": lid,
                "status": EnrollmentStatus.ACTIVE.value,
                "enrolled_at": enrolled_at.isoformat(),
                "dropped_at": None,
                "created_at": enrolled_at.isoformat(),
                "updated_at": enrolled_at.isoformat(),
            }
            enrollments.append(enrollment_record)
            enrollment_map[(cid, lid)] = enr_id
            enr_counter += 1
            
    return enrollments, enrollment_map
