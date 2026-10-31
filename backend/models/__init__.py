from sqlalchemy import event
from sqlalchemy.orm import Mapper
from backend.extensions import db

# Domain Enums
from backend.models.enums import (
    CourseStatus,
    EnrollmentStatus,
    AssignmentStatus,
    SubmissionStatus,
    ArtifactType,
    GradeStatus,
    FeedbackVisibility,
    ResubmissionStatus,
    AppealStatus,
    AppealReasonCategory,
    AuditActionType,
)

# Mandatory & Supporting Entities
from backend.models.course import Course
from backend.models.learner import Learner
from backend.models.enrollment import Enrollment
from backend.models.assignment import Assignment
from backend.models.rubric import Rubric
from backend.models.rubric_criterion import RubricCriterion
from backend.models.submission import Submission
from backend.models.submission_artifact import SubmissionArtifact
from backend.models.grade import Grade
from backend.models.grade_criterion_score import GradeCriterionScore
from backend.models.feedback import Feedback
from backend.models.resubmission import Resubmission
from backend.models.appeal import Appeal
from backend.models.submission_status_history import SubmissionStatusHistory
from backend.models.audit_log import AuditLog

# List of all managed models
ALL_MODELS = [
    Course,
    Learner,
    Enrollment,
    Assignment,
    Rubric,
    RubricCriterion,
    Submission,
    SubmissionArtifact,
    Grade,
    GradeCriterionScore,
    Feedback,
    Resubmission,
    Appeal,
    SubmissionStatusHistory,
    AuditLog,
]

def _prevent_pk_modification(mapper: Mapper, connection, target):
    """Enforce ID immutability across all entity instances."""
    state = db.inspect(target)
    for pk_col in mapper.primary_key:
        history = state.get_history(pk_col.key, True)
        if history.has_changes():
            raise ValueError(
                f"Immutable ID Violation: Primary key '{pk_col.key}' on {target.__class__.__name__} "
                f"cannot be modified from '{history.deleted[0]}' to '{history.added[0]}'."
            )

# Register immutability listeners across all models
for model_cls in ALL_MODELS:
    event.listen(model_cls, "before_update", _prevent_pk_modification)

__all__ = [
    "CourseStatus",
    "EnrollmentStatus",
    "AssignmentStatus",
    "SubmissionStatus",
    "ArtifactType",
    "GradeStatus",
    "FeedbackVisibility",
    "ResubmissionStatus",
    "AppealStatus",
    "AppealReasonCategory",
    "AuditActionType",
    "Course",
    "Learner",
    "Enrollment",
    "Assignment",
    "Rubric",
    "RubricCriterion",
    "Submission",
    "SubmissionArtifact",
    "Grade",
    "GradeCriterionScore",
    "Feedback",
    "Resubmission",
    "Appeal",
    "SubmissionStatusHistory",
    "AuditLog",
    "ALL_MODELS",
]
