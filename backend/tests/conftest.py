import sys
from pathlib import Path

# Ensure project root is in sys.path regardless of working directory
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from backend.app import create_app
from backend.extensions import db
from backend.models import (
    Course, Learner, Enrollment, Assignment, Rubric, RubricCriterion,
    Submission, SubmissionArtifact, Grade, GradeCriterionScore, Feedback,
    Resubmission, Appeal, SubmissionStatusHistory, AuditLog,
    CourseStatus, EnrollmentStatus, AssignmentStatus, SubmissionStatus,
    ArtifactType, GradeStatus, FeedbackVisibility, ResubmissionStatus,
    AppealStatus, AppealReasonCategory, AuditActionType
)

@pytest.fixture(scope="session")
def app():
    """Create testing application with in-memory database."""
    app = create_app("testing")
    with app.app_context():
        yield app

@pytest.fixture(scope="function")
def session(app):
    """Provide a clean database session for each test."""
    with app.app_context():
        db.create_all()
        yield db.session
        db.session.rollback()
        db.drop_all()

@pytest.fixture(scope="function")
def client(app, session):
    """Provide a test client with clean database for API endpoint tests."""
    return app.test_client()

@pytest.fixture
def sample_course(session):
    now = datetime.now(timezone.utc)
    course = Course(
        course_id="CRS-2026-000001",
        code="CS-504",
        title="Distributed Data Systems",
        description="Core architectures in distributed databases and stream processing.",
        department="Computer Science",
        term="Fall 2026",
        timezone="America/New_York",
        status=CourseStatus.ACTIVE,
        start_date=now - timedelta(days=30),
        end_date=now + timedelta(days=90),
    )
    session.add(course)
    session.commit()
    return course

@pytest.fixture
def sample_learner(session):
    learner = Learner(
        learner_id="LNR-2026-000001",
        student_number="STU-984321",
        first_name="Alex",
        last_name="Chen",
        email="alex.chen@university.edu",
        timezone="America/Los_Angeles",
        status=EnrollmentStatus.ACTIVE,
    )
    session.add(learner)
    session.commit()
    return learner

@pytest.fixture
def sample_enrollment(session, sample_course, sample_learner):
    enrollment = Enrollment(
        enrollment_id="ENR-2026-000001",
        course_id=sample_course.course_id,
        learner_id=sample_learner.learner_id,
        status=EnrollmentStatus.ACTIVE,
    )
    session.add(enrollment)
    session.commit()
    return enrollment

@pytest.fixture
def sample_assignment(session, sample_course):
    now = datetime.now(timezone.utc)
    assignment = Assignment(
        assignment_id="ASN-2026-000001",
        course_id=sample_course.course_id,
        title="Streaming Pipeline Architecture",
        description="Implement an event-driven data streaming engine.",
        max_score=Decimal("100.00"),
        due_date=now + timedelta(days=7),
        cutoff_date=now + timedelta(days=10),
        late_penalty_per_day=Decimal("5.00"),
        max_late_days=3,
        grace_period_minutes=15,
        max_resubmissions=1,
        required_artifact_types=["code_repository", "report_pdf"],
        status=AssignmentStatus.PUBLISHED,
    )
    session.add(assignment)
    session.commit()
    return assignment

@pytest.fixture
def sample_rubric(session, sample_assignment):
    rubric = Rubric(
        rubric_id=f"RUB-{sample_assignment.assignment_id}-01",
        assignment_id=sample_assignment.assignment_id,
        title="Pipeline Architecture Rubric v1",
        description="Comprehensive technical evaluation criteria.",
        total_points=Decimal("100.00"),
        version=1,
        is_active=True,
    )
    session.add(rubric)
    session.flush()

    c1 = RubricCriterion(
        criterion_id=f"CRT-{rubric.rubric_id}-01",
        rubric_id=rubric.rubric_id,
        criterion_name="Streaming Fault-Tolerance",
        description="Handling worker and broker failover.",
        max_points=Decimal("50.00"),
        weight=Decimal("1.00"),
        display_order=1,
    )
    c2 = RubricCriterion(
        criterion_id=f"CRT-{rubric.rubric_id}-02",
        rubric_id=rubric.rubric_id,
        criterion_name="Code Quality & Documentation",
        description="Modularization, type annotations, and unit tests.",
        max_points=Decimal("50.00"),
        weight=Decimal("1.00"),
        display_order=2,
    )
    session.add_all([c1, c2])
    session.commit()
    return rubric

@pytest.fixture
def sample_submission(session, sample_assignment, sample_learner, sample_enrollment):
    now = datetime.now(timezone.utc)
    submission = Submission(
        submission_id=f"SUB-{sample_assignment.assignment_id}-{sample_learner.learner_id}-01",
        assignment_id=sample_assignment.assignment_id,
        learner_id=sample_learner.learner_id,
        enrollment_id=sample_enrollment.enrollment_id,
        attempt_number=1,
        submitted_at=now - timedelta(hours=12),
        is_late=False,
        late_duration_seconds=0,
        late_penalty_percentage=Decimal("0.00"),
        status=SubmissionStatus.SUBMITTED,
    )
    session.add(submission)
    session.flush()

    art1 = SubmissionArtifact(
        artifact_id=f"ART-{submission.submission_id}-01",
        submission_id=submission.submission_id,
        artifact_type=ArtifactType.CODE_REPOSITORY,
        file_name="code.zip",
        file_size_bytes=1024,
        mime_type="application/zip",
        storage_uri="s3://eduflow/code.zip",
        checksum_sha256="1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
        is_verified=True,
    )
    art2 = SubmissionArtifact(
        artifact_id=f"ART-{submission.submission_id}-02",
        submission_id=submission.submission_id,
        artifact_type=ArtifactType.REPORT_PDF,
        file_name="report.pdf",
        file_size_bytes=2048,
        mime_type="application/pdf",
        storage_uri="s3://eduflow/report.pdf",
        checksum_sha256="abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
        is_verified=True,
    )
    session.add_all([art1, art2])
    session.commit()
    return submission
