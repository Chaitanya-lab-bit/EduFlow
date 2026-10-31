from datetime import datetime, timezone, timedelta
from decimal import Decimal
import numpy as np
from backend.models.enums import AssignmentStatus

CRITERIA_NAMES = [
    ("Problem Decomposition & Architecture", "Evaluation of high-level modularity and abstractions."),
    ("Algorithmic Efficiency & Data Structures", "Analysis of computational complexity and memory usage."),
    ("Implementation Correctness & Edge Cases", "Verification against comprehensive test vectors."),
    ("Code Quality, Styling & Documentation", "Adherence to PEP 8, docstrings, and type annotations."),
    ("Unit Testing & Fault Tolerance", "Thoroughness of pytest test suites and exception coverage.")
]

ARTIFACT_TYPE_COMBINATIONS = [
    ["report_pdf"],
    ["code_repository", "report_pdf"],
    ["code_repository", "report_pdf", "dataset_csv"],
    ["report_pdf", "video_presentation"],
]

def generate_assignments_and_rubrics(
    courses: list[dict],
    num_assignments: int,
    criteria_per_rubric: int,
    additional_rubric_versions: int,
    seed: int
) -> tuple[list[dict], list[dict], list[dict]]:
    """
    Generate deterministic assignments, active rubrics, criteria, and versioned rubrics.
    Returns:
        assignments: list of assignment dictionaries
        rubrics: list of rubric dictionaries
        criteria: list of rubric criterion dictionaries
    """
    rng = np.random.default_rng(seed)
    
    assignments = []
    rubrics = []
    criteria = []
    
    num_courses = len(courses)
    
    for i in range(1, num_assignments + 1):
        assignment_id = f"ASN-2026-{i:06d}"
        course = courses[(i - 1) % num_courses]
        cid = course["course_id"]
        
        # Assignment sequencing within course
        course_start = datetime.fromisoformat(course["start_date"])
        # Schedule assignment due dates between week 2 and week 14 of semester
        week_num = 2 + ((i - 1) // num_courses) % 13
        due_date = course_start + timedelta(weeks=week_num, days=int(rng.integers(1, 6)), hours=23, minutes=59)
        max_late_days = 3
        cutoff_date = due_date + timedelta(days=max_late_days)
        
        art_idx = int(rng.integers(0, len(ARTIFACT_TYPE_COMBINATIONS)))
        req_artifacts = ARTIFACT_TYPE_COMBINATIONS[art_idx]
        
        assignment_record = {
            "assignment_id": assignment_id,
            "course_id": cid,
            "title": f"Project Deliverable #{((i - 1) // num_courses) + 1}: {course['department']} Practical Lab",
            "description": f"Hands-on technical implementation deliverable for {course['code']}.",
            "max_score": 100.00,
            "due_date": due_date.isoformat(),
            "cutoff_date": cutoff_date.isoformat(),
            "late_penalty_per_day": 5.00,
            "max_late_days": max_late_days,
            "grace_period_minutes": 15,
            "max_resubmissions": 1,
            "required_artifact_types": req_artifacts,
            "status": AssignmentStatus.PUBLISHED.value,
            "created_at": (due_date - timedelta(days=21)).isoformat(),
            "updated_at": (due_date - timedelta(days=21)).isoformat(),
        }
        assignments.append(assignment_record)
        
        # Primary Active Rubric (version 1)
        rubric_id = f"RUB-{assignment_id}-01"
        rubric_record = {
            "rubric_id": rubric_id,
            "assignment_id": assignment_id,
            "title": f"Rubric for {assignment_id}",
            "description": f"Standardized {criteria_per_rubric}-criteria assessment rubric.",
            "total_points": 100.00,
            "version": 1,
            "is_active": True,
            "created_at": (due_date - timedelta(days=21)).isoformat(),
            "updated_at": (due_date - timedelta(days=21)).isoformat(),
        }
        rubrics.append(rubric_record)
        
        # Rubric Criteria (points divide to sum strictly to 100.00)
        pts = [round(100.0 / criteria_per_rubric, 2) for _ in range(criteria_per_rubric)]
        pts[-1] = round(100.0 - sum(pts[:-1]), 2)
        
        for c_idx in range(1, criteria_per_rubric + 1):
            crit_name, crit_desc = CRITERIA_NAMES[(c_idx - 1) % len(CRITERIA_NAMES)]
            crit_id = f"CRT-{rubric_id}-{c_idx:02d}"
            criterion_record = {
                "criterion_id": crit_id,
                "rubric_id": rubric_id,
                "criterion_name": f"{crit_name} (Part {c_idx})",
                "description": crit_desc,
                "max_points": pts[c_idx - 1],
                "weight": 1.00,
                "display_order": c_idx,
                "created_at": (due_date - timedelta(days=21)).isoformat(),
                "updated_at": (due_date - timedelta(days=21)).isoformat(),
            }
            criteria.append(criterion_record)

    # Additional versioned rubrics for selected assignments (e.g. revised rubric version 2)
    # to demonstrate lifecycle rubric versioning and exceed 1,000 rubrics & 5,000 criteria
    for v_idx in range(1, min(additional_rubric_versions + 1, num_assignments + 1)):
        target_asn = assignments[v_idx - 1]
        target_aid = target_asn["assignment_id"]
        due_date = datetime.fromisoformat(target_asn["due_date"])
        
        v2_rubric_id = f"RUB-{target_aid}-02"
        v2_rubric = {
            "rubric_id": v2_rubric_id,
            "assignment_id": target_aid,
            "title": f"Revised Rubric for {target_aid} (v2)",
            "description": f"Updated assessment criteria for {target_aid}.",
            "total_points": 100.00,
            "version": 2,
            "is_active": False,
            "created_at": (due_date - timedelta(days=14)).isoformat(),
            "updated_at": (due_date - timedelta(days=14)).isoformat(),
        }
        rubrics.append(v2_rubric)
        
        pts = [round(100.0 / criteria_per_rubric, 2) for _ in range(criteria_per_rubric)]
        pts[-1] = round(100.0 - sum(pts[:-1]), 2)
        
        for c_idx in range(1, criteria_per_rubric + 1):
            crit_name, crit_desc = CRITERIA_NAMES[(c_idx - 1) % len(CRITERIA_NAMES)]
            crit_id = f"CRT-{v2_rubric_id}-{c_idx:02d}"
            criterion_record = {
                "criterion_id": crit_id,
                "rubric_id": v2_rubric_id,
                "criterion_name": f"{crit_name} (Revised Part {c_idx})",
                "description": crit_desc,
                "max_points": pts[c_idx - 1],
                "weight": 1.00,
                "display_order": c_idx,
                "created_at": (due_date - timedelta(days=14)).isoformat(),
                "updated_at": (due_date - timedelta(days=14)).isoformat(),
            }
            criteria.append(criterion_record)
            
    return assignments, rubrics, criteria
