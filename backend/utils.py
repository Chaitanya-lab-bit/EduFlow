"""
Utility functions, exception classes, serializers, and pagination helpers.
"""
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
import uuid
from werkzeug.exceptions import HTTPException
from pydantic import ValidationError

class APIException(HTTPException):
    def __init__(self, message: str, status_code: int = 400, error_code: str = "ERR_BAD_REQUEST", details: dict | None = None):
        super().__init__(description=message)
        self.code = status_code
        self.status_code = status_code
        self.message = message
        self.error_code = error_code
        self.details = details or {}

class UnenrolledLearnerException(APIException):
    def __init__(self, message: str = "Learner is not actively enrolled in the course for this assignment."):
        super().__init__(message, status_code=403, error_code="ERR_UNENROLLED_LEARNER")

class DeadlineExceededException(APIException):
    def __init__(self, message: str = "Submission timestamp exceeds the assignment cutoff date."):
        super().__init__(message, status_code=403, error_code="ERR_DEADLINE_EXCEEDED")

class ScoreExceedsMaxException(APIException):
    def __init__(self, message: str = "Grading score exceeds the allowed rubric or criterion maximum points.", details: dict | None = None):
        super().__init__(message, status_code=422, error_code="ERR_SCORE_EXCEEDS_MAX", details=details)

class MissingArtifactsException(APIException):
    def __init__(self, missing: list[str]):
        message = f"Missing required artifacts: {', '.join(missing)}"
        super().__init__(message, status_code=422, error_code="MISSING_REQUIRED_ARTIFACTS", details={"missing": missing})

class ResubmissionLimitReachedException(APIException):
    def __init__(self, message: str = "Maximum resubmission attempts limit reached for this assignment."):
        super().__init__(message, status_code=400, error_code="ERR_RESUBMISSION_LIMIT_REACHED")

class AppealWindowExpiredException(APIException):
    def __init__(self, message: str = "Appeal window has expired for this grade (must be submitted within 7 days of publication)."):
        super().__init__(message, status_code=400, error_code="ERR_APPEAL_WINDOW_EXPIRED")

class RubricPointsMismatchException(APIException):
    def __init__(self, message: str = "Sum of rubric criteria points does not equal the assignment max_score."):
        super().__init__(message, status_code=422, error_code="ERR_RUBRIC_POINTS_MISMATCH")

class DuplicateEntityException(APIException):
    def __init__(self, message: str = "A record with the specified unique attributes already exists."):
        super().__init__(message, status_code=409, error_code="ERR_DUPLICATE_ENTITY")

class EntityNotFoundException(APIException):
    def __init__(self, message: str = "The requested entity could not be found."):
        super().__init__(message, status_code=404, error_code="ERR_NOT_FOUND")

class UnauthorizedAccessException(APIException):
    def __init__(self, message: str = "Unauthorized action or insufficient permissions."):
        super().__init__(message, status_code=403, error_code="ERR_UNAUTHORIZED")


def validate_payload(schema_cls, data: dict):
    """Parse and validate payload against a Pydantic schema, raising APIException 422 on failure."""
    try:
        return schema_cls(**(data or {}))
    except ValidationError as err:
        cleaned_errors = []
        for e in err.errors():
            item = {
                "type": e.get("type"),
                "loc": e.get("loc"),
                "msg": e.get("msg"),
            }
            if "ctx" in e:
                item["ctx"] = {k: str(v) for k, v in e["ctx"].items()}
            cleaned_errors.append(item)
        raise APIException(
            "Request validation failed",
            status_code=422,
            error_code="ERR_VALIDATION",
            details={"errors": cleaned_errors}
        )


def format_iso(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


def serialize_model(model_instance, include_relationships: bool = False) -> dict:
    """Generic serializer for SQLAlchemy model instances."""
    if model_instance is None:
        return {}
    
    result = {}
    for col in model_instance.__table__.columns:
        val = getattr(model_instance, col.name)
        if isinstance(val, datetime):
            result[col.name] = format_iso(val)
        elif isinstance(val, Decimal):
            result[col.name] = float(val)
        elif isinstance(val, Enum):
            result[col.name] = val.value
        else:
            result[col.name] = val
    return result


def paginate_query(query, page: int = 1, per_page: int = 20, max_per_page: int = 100):
    """Paginates an SQLAlchemy query with boundary enforcement."""
    page = max(1, int(page))
    per_page = min(max_per_page, max(1, int(per_page)))
    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    pages = (total + per_page - 1) // per_page if total > 0 else 1
    return {
        "items": items,
        "meta": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "pages": pages,
        }
    }


def generate_id(prefix: str) -> str:
    """Generate structured ID like CRS-2026-XXXXXX."""
    current_year = datetime.now(timezone.utc).year
    short_uuid = uuid.uuid4().hex[:6].upper()
    return f"{prefix}-{current_year}-{short_uuid}"
