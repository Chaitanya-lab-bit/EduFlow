"""
Pydantic schemas and DTOs for EduFlow API validation and serialization.
"""
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional, List
from pydantic import BaseModel, Field, field_validator, model_validator

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

# ---------------------------------------------------------------------------
# Common / Pagination
# ---------------------------------------------------------------------------
class PaginationMeta(BaseModel):
    page: int
    per_page: int
    total: int
    pages: int

# ---------------------------------------------------------------------------
# Course Schemas
# ---------------------------------------------------------------------------
class CourseCreateSchema(BaseModel):
    course_id: Optional[str] = None
    code: str = Field(..., min_length=2, max_length=32)
    title: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = None
    department: str = Field(..., min_length=2, max_length=100)
    term: str = Field(..., min_length=2, max_length=32)
    timezone: str = Field(default="UTC", max_length=64)
    status: Optional[CourseStatus] = CourseStatus.DRAFT
    start_date: datetime
    end_date: datetime

    @model_validator(mode="after")
    def validate_dates(self):
        if self.end_date <= self.start_date:
            raise ValueError("end_date must be strictly after start_date")
        return self

class CourseUpdateSchema(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=255)
    description: Optional[str] = None
    department: Optional[str] = Field(None, min_length=2, max_length=100)
    term: Optional[str] = Field(None, min_length=2, max_length=32)
    timezone: Optional[str] = Field(None, max_length=64)
    status: Optional[CourseStatus] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    @model_validator(mode="after")
    def validate_dates(self):
        if self.start_date and self.end_date and self.end_date <= self.start_date:
            raise ValueError("end_date must be strictly after start_date")
        return self

# ---------------------------------------------------------------------------
# Learner Schemas
# ---------------------------------------------------------------------------
class LearnerCreateSchema(BaseModel):
    learner_id: Optional[str] = None
    student_number: str = Field(..., min_length=3, max_length=64)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    timezone: str = Field(default="UTC", max_length=64)
    status: Optional[EnrollmentStatus] = EnrollmentStatus.ACTIVE

class LearnerUpdateSchema(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[str] = Field(None, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    timezone: Optional[str] = Field(None, max_length=64)
    status: Optional[EnrollmentStatus] = None

# ---------------------------------------------------------------------------
# Enrollment Schemas
# ---------------------------------------------------------------------------
class EnrollmentCreateSchema(BaseModel):
    enrollment_id: Optional[str] = None
    course_id: str = Field(..., min_length=3, max_length=32)
    learner_id: str = Field(..., min_length=3, max_length=32)
    status: Optional[EnrollmentStatus] = EnrollmentStatus.ACTIVE

# ---------------------------------------------------------------------------
# Rubric Criterion & Rubric Schemas
# ---------------------------------------------------------------------------
class RubricCriterionInputSchema(BaseModel):
    criterion_id: Optional[str] = None
    criterion_name: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    max_points: Decimal = Field(..., gt=0, le=100)
    weight: Decimal = Field(default=Decimal("1.00"), gt=0)
    display_order: int = Field(default=1, ge=1)

class RubricCreateSchema(BaseModel):
    rubric_id: Optional[str] = None
    title: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    total_points: Decimal = Field(default=Decimal("100.00"), gt=0)
    version: int = Field(default=1, ge=1)
    is_active: bool = True
    criteria: List[RubricCriterionInputSchema] = Field(default_factory=list)

# ---------------------------------------------------------------------------
# Assignment Schemas
# ---------------------------------------------------------------------------
class AssignmentCreateSchema(BaseModel):
    assignment_id: Optional[str] = None
    course_id: str = Field(..., min_length=3, max_length=32)
    title: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = None
    max_score: Decimal = Field(default=Decimal("100.00"), gt=0, le=1000)
    due_date: datetime
    cutoff_date: datetime
    late_penalty_per_day: Decimal = Field(default=Decimal("5.00"), ge=0, le=100)
    max_late_days: int = Field(default=3, ge=0)
    grace_period_minutes: int = Field(default=15, ge=0)
    max_resubmissions: int = Field(default=1, ge=0)
    required_artifact_types: List[str] = Field(default_factory=lambda: ["report_pdf"])
    status: Optional[AssignmentStatus] = AssignmentStatus.DRAFT
    rubric: Optional[RubricCreateSchema] = None

    @model_validator(mode="after")
    def validate_dates(self):
        if self.cutoff_date < self.due_date:
            raise ValueError("cutoff_date must be greater than or equal to due_date")
        return self

class AssignmentUpdateSchema(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=255)
    description: Optional[str] = None
    max_score: Optional[Decimal] = Field(None, gt=0, le=1000)
    due_date: Optional[datetime] = None
    cutoff_date: Optional[datetime] = None
    late_penalty_per_day: Optional[Decimal] = Field(None, ge=0, le=100)
    max_late_days: Optional[int] = Field(None, ge=0)
    grace_period_minutes: Optional[int] = Field(None, ge=0)
    max_resubmissions: Optional[int] = Field(None, ge=0)
    required_artifact_types: Optional[List[str]] = None
    status: Optional[AssignmentStatus] = None

    @model_validator(mode="after")
    def validate_dates(self):
        if self.due_date and self.cutoff_date and self.cutoff_date < self.due_date:
            raise ValueError("cutoff_date must be greater than or equal to due_date")
        return self

# ---------------------------------------------------------------------------
# Submission & Artifact Schemas
# ---------------------------------------------------------------------------
class SubmissionArtifactInputSchema(BaseModel):
    artifact_id: Optional[str] = None
    artifact_type: ArtifactType
    file_name: str = Field(..., min_length=1, max_length=255)
    file_size_bytes: int = Field(..., gt=0)
    mime_type: str = Field(..., min_length=1, max_length=128)
    storage_uri: str = Field(..., min_length=1, max_length=512)
    checksum_sha256: str = Field(..., min_length=16, max_length=64)
    is_verified: bool = True

class SubmissionCreateSchema(BaseModel):
    submission_id: Optional[str] = None
    assignment_id: str = Field(..., min_length=3, max_length=32)
    learner_id: str = Field(..., min_length=3, max_length=32)
    attempt_number: Optional[int] = Field(default=1, ge=1)
    learner_notes: Optional[str] = None
    submitted_at: Optional[datetime] = None
    status: Optional[SubmissionStatus] = SubmissionStatus.SUBMITTED
    artifacts: Optional[List[SubmissionArtifactInputSchema]] = None

# ---------------------------------------------------------------------------
# Grading Schemas
# ---------------------------------------------------------------------------
class CriterionScoreInputSchema(BaseModel):
    criterion_id: str = Field(..., min_length=3, max_length=96)
    score_awarded: Decimal = Field(..., ge=0)
    evaluator_comment: Optional[str] = None

class GradeCreateSchema(BaseModel):
    grade_id: Optional[str] = None
    submission_id: str = Field(..., min_length=3, max_length=96)
    graded_by: str = Field(..., min_length=2, max_length=64)
    criteria_scores: List[CriterionScoreInputSchema] = Field(..., min_length=1)
    bonus_points: Decimal = Field(default=Decimal("0.00"), ge=0)
    is_final: bool = True
    grade_status: Optional[GradeStatus] = GradeStatus.PUBLISHED

# ---------------------------------------------------------------------------
# Feedback Schemas
# ---------------------------------------------------------------------------
class FeedbackCreateSchema(BaseModel):
    feedback_id: Optional[str] = None
    grade_id: str = Field(..., min_length=3, max_length=112)
    submission_id: Optional[str] = None
    author_id: str = Field(..., min_length=2, max_length=64)
    general_comments: str = Field(..., min_length=1)
    strengths: Optional[str] = None
    areas_for_improvement: Optional[str] = None
    visibility: Optional[FeedbackVisibility] = FeedbackVisibility.LEARNER_VISIBLE

# ---------------------------------------------------------------------------
# Resubmission Schemas
# ---------------------------------------------------------------------------
class ResubmissionRequestSchema(BaseModel):
    resubmission_id: Optional[str] = None
    original_submission_id: str = Field(..., min_length=3, max_length=96)
    reason: str = Field(..., min_length=3)
    change_summary: Optional[str] = None

class ResubmissionReviewSchema(BaseModel):
    status: ResubmissionStatus
    reviewed_by: str = Field(..., min_length=2, max_length=64)
    change_summary: Optional[str] = None

    @field_validator("status")
    @classmethod
    def validate_review_status(cls, v):
        if v not in (ResubmissionStatus.APPROVED, ResubmissionStatus.REJECTED):
            raise ValueError("Review status must be either APPROVED or REJECTED")
        return v

# ---------------------------------------------------------------------------
# Appeal Schemas
# ---------------------------------------------------------------------------
class AppealCreateSchema(BaseModel):
    appeal_id: Optional[str] = None
    submission_id: str = Field(..., min_length=3, max_length=96)
    learner_id: str = Field(..., min_length=3, max_length=32)
    reason_category: AppealReasonCategory
    learner_statement: str = Field(..., min_length=5)
    contested_criteria: Optional[List[str]] = None
    requested_grade: Optional[Decimal] = Field(None, ge=0, le=1000)

class AppealDecisionSchema(BaseModel):
    status: AppealStatus
    reviewed_by: str = Field(..., min_length=2, max_length=64)
    decision_notes: Optional[str] = Field(None, min_length=1)
    final_grade: Optional[Decimal] = Field(None, ge=0, le=1000)

    @field_validator("status")
    @classmethod
    def validate_decision_status(cls, v):
        if v not in (AppealStatus.APPROVED, AppealStatus.REJECTED, AppealStatus.UNDER_REVIEW):
            raise ValueError("Decision status must be APPROVED, REJECTED, or UNDER_REVIEW")
        return v

    @model_validator(mode="after")
    def validate_approved_final_grade(self):
        if self.status == AppealStatus.APPROVED and self.final_grade is None:
            raise ValueError("final_grade is required when appeal is APPROVED")
        return self
