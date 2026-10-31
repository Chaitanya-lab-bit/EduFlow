from datetime import datetime, timedelta
import numpy as np
from backend.models.enums import FeedbackVisibility

COMMENT_TIERS = {
    "high": [
        "Outstanding submission. Architectural design exhibits high modularity and robust error handling.",
        "Superb work. The implementation is concise, highly performant, and adheres to all engineering best practices.",
        "Exemplary project delivery. Well-structured code base with exceptional test coverage and documentation."
    ],
    "medium": [
        "Solid implementation satisfying the project requirements. Code organization is clean and legible.",
        "Good submission overall. Core logic is sound with minor opportunities for computational optimization.",
        "Competent work. Met all required functional specifications; consider improving documentation clarity."
    ],
    "low": [
        "Basic requirements met, but several edge cases are unhandled and code modularity needs refinement.",
        "The submission shows partial implementation. Recommend reviewing rubric criteria and strengthening test coverage.",
        "Satisfactory baseline effort. Requires significant refactoring for production readiness and style guidelines."
    ]
}

STRENGTHS_LIST = [
    "Clean separation of concerns and well-defined API boundaries.",
    "Comprehensive unit test suite covering key boundary conditions.",
    "Excellent adherence to naming conventions and type annotations.",
    "Resilient exception handling and defensive programming patterns.",
    "Thorough analytical report detailing experimental results."
]

AREAS_IMPROVEMENT_LIST = [
    "Expand test suite to include asynchronous failure modes.",
    "Profile memory consumption under peak streaming workload.",
    "Enhance documentation with architectural sequence diagrams.",
    "Standardize logging output across all worker components.",
    "Refactor monolithic helper methods into dedicated utility modules."
]

def generate_feedback(
    grades: list[dict],
    seed: int
) -> list[dict]:
    """
    Generate deterministic qualitative feedback records for published grades.
    Returns:
        feedback_list: list of feedback dictionaries
    """
    rng = np.random.default_rng(seed)
    feedback_list = []
    
    for grade in grades:
        gid = grade["grade_id"]
        sub_id = grade["submission_id"]
        author = grade["graded_by"]
        final_score = float(grade["final_score"])
        graded_time = datetime.fromisoformat(grade["graded_at"])
        
        # Select appropriate qualitative feedback based on performance tier
        if final_score >= 88.0:
            comments = COMMENT_TIERS["high"]
        elif final_score >= 70.0:
            comments = COMMENT_TIERS["medium"]
        else:
            comments = COMMENT_TIERS["low"]
            
        gen_comment = comments[int(rng.integers(0, len(comments)))]
        strength = STRENGTHS_LIST[int(rng.integers(0, len(STRENGTHS_LIST)))]
        improvement = AREAS_IMPROVEMENT_LIST[int(rng.integers(0, len(AREAS_IMPROVEMENT_LIST)))]
        
        published_at = graded_time + timedelta(minutes=int(rng.integers(2, 10)))
        
        fbk_id = f"FBK-{gid}-01"
        feedback_record = {
            "feedback_id": fbk_id,
            "grade_id": gid,
            "submission_id": sub_id,
            "author_id": author,
            "visibility": FeedbackVisibility.LEARNER_VISIBLE.value,
            "general_comments": gen_comment,
            "strengths": strength,
            "areas_for_improvement": improvement,
            "published_at": published_at.isoformat(),
            "created_at": published_at.isoformat(),
            "updated_at": published_at.isoformat(),
        }
        feedback_list.append(feedback_record)
        
    return feedback_list
