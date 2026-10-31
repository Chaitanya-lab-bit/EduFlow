import enum

class CourseStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class EnrollmentStatus(str, enum.Enum):
    ACTIVE = "active"
    DROPPED = "dropped"
    COMPLETED = "completed"
    SUSPENDED = "suspended"


class AssignmentStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    CLOSED = "closed"
    ARCHIVED = "archived"


class SubmissionStatus(str, enum.Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    GRADED = "graded"
    RESUBMITTED = "resubmitted"
    APPEALED = "appealed"


class ArtifactType(str, enum.Enum):
    CODE_REPOSITORY = "code_repository"
    REPORT_PDF = "report_pdf"
    DATASET_CSV = "dataset_csv"
    VIDEO_PRESENTATION = "video_presentation"
    SUPPLEMENTARY_ZIP = "supplementary_zip"


class GradeStatus(str, enum.Enum):
    PROVISIONAL = "provisional"
    PUBLISHED = "published"
    REVISED = "revised"
    DISPUTED = "disputed"


class FeedbackVisibility(str, enum.Enum):
    LEARNER_VISIBLE = "learner_visible"
    INTERNAL_STAFF_ONLY = "internal_staff_only"


class ResubmissionStatus(str, enum.Enum):
    REQUESTED = "requested"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUBMITTED = "submitted"


class AppealStatus(str, enum.Enum):
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class AppealReasonCategory(str, enum.Enum):
    CALCULATION_ERROR = "calculation_error"
    RUBRIC_MISINTERPRETATION = "rubric_misinterpretation"
    MISSING_ARTIFACT_RECONSIDERATION = "missing_artifact_reconsideration"
    EXTENUATING_CIRCUMSTANCES = "extenuating_circumstances"


class AuditActionType(str, enum.Enum):
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    STATUS_CHANGE = "STATUS_CHANGE"
    GRADE_OVERRIDE = "GRADE_OVERRIDE"
    APPEAL_DECISION = "APPEAL_DECISION"
    ARTIFACT_VERIFICATION = "ARTIFACT_VERIFICATION"
