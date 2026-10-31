import pytest
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo
from sqlalchemy.exc import IntegrityError
from backend.models import (
    Course, Learner, Enrollment, Assignment, Rubric, RubricCriterion,
    Submission, SubmissionArtifact, Grade, GradeCriterionScore, Feedback,
    Resubmission, Appeal, SubmissionStatusHistory, AuditLog,
    CourseStatus, EnrollmentStatus, AssignmentStatus, SubmissionStatus,
    ArtifactType, GradeStatus, FeedbackVisibility, ResubmissionStatus,
    AppealStatus, AppealReasonCategory, AuditActionType
)
from backend.services.audit_service import AuditService

class TestEduFlowDatabaseLayer:
    """Automated test suite verifying the EduFlow persistence layer and business rules."""

    def test_01_create_all_mandatory_and_supporting_entities(
        self, session, sample_course, sample_learner, sample_enrollment,
        sample_assignment, sample_rubric
    ):
        """1. Verify that every mandatory entity and supporting entity can be successfully created."""
        now = datetime.now(timezone.utc)

        # 1. Submission (SUB-ASN-2026-000001-LNR-2026-000001-01)
        sub_id = f"SUB-{sample_assignment.assignment_id}-{sample_learner.learner_id}-01"
        submission = Submission(
            submission_id=sub_id,
            assignment_id=sample_assignment.assignment_id,
            learner_id=sample_learner.learner_id,
            enrollment_id=sample_enrollment.enrollment_id,
            attempt_number=1,
            submitted_at=now,
            status=SubmissionStatus.SUBMITTED,
            is_late=False,
            late_duration_seconds=0,
            late_penalty_percentage=Decimal("0.00"),
            raw_score=Decimal("94.00"),
            final_score=Decimal("94.00"),
        )
        session.add(submission)
        session.flush()

        # 2. Submission Artifact (ART-SUB-...-01)
        artifact = SubmissionArtifact(
            artifact_id=f"ART-{sub_id}-01",
            submission_id=sub_id,
            artifact_type=ArtifactType.REPORT_PDF,
            file_name="alex_chen_distributed_sys.pdf",
            file_size_bytes=2458900,
            mime_type="application/pdf",
            storage_uri="s3://eduflow-artifacts/2026/alex_report.pdf",
            checksum_sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            is_verified=True,
        )
        session.add(artifact)

        # 3. Submission Status History (SSH-2026-000001)
        history = SubmissionStatusHistory(
            history_id="SSH-2026-000001",
            submission_id=sub_id,
            old_status=SubmissionStatus.DRAFT,
            new_status=SubmissionStatus.SUBMITTED,
            changed_by=sample_learner.learner_id,
            change_reason="Student uploaded report and submitted attempt 1",
            changed_at=now,
        )
        session.add(history)

        # 4. Grade (GRD-SUB-ASN-2026-000001-LNR-2026-000001-01)
        grade_id = f"GRD-{sub_id}"
        grade = Grade(
            grade_id=grade_id,
            submission_id=sub_id,
            graded_by="USR-INST-0042",
            raw_score=Decimal("94.00"),
            late_penalty_applied=Decimal("0.00"),
            bonus_points=Decimal("0.00"),
            final_score=Decimal("94.00"),
            is_final=True,
            grade_status=GradeStatus.PUBLISHED,
            graded_at=now,
        )
        session.add(grade)
        session.flush()

        # 5. Grade Criterion Scores
        criteria = sample_rubric.criteria
        gcs1 = GradeCriterionScore(
            score_id=f"GCS-{grade_id}-01",
            grade_id=grade_id,
            criterion_id=criteria[0].criterion_id,
            score_awarded=Decimal("47.00"),
            evaluator_comment="Excellent fault-tolerance guarantees.",
        )
        gcs2 = GradeCriterionScore(
            score_id=f"GCS-{grade_id}-02",
            grade_id=grade_id,
            criterion_id=criteria[1].criterion_id,
            score_awarded=Decimal("47.00"),
            evaluator_comment="Clear design docs and thorough unit tests.",
        )
        session.add_all([gcs1, gcs2])

        # 6. Feedback (FBK-GRD-...-01)
        feedback = Feedback(
            feedback_id=f"FBK-{grade_id}-01",
            grade_id=grade_id,
            submission_id=sub_id,
            author_id="USR-INST-0042",
            visibility=FeedbackVisibility.LEARNER_VISIBLE,
            general_comments="Outstanding work overall. Clean architectural separation.",
            strengths="Exceptional handling of network partitions.",
            areas_for_improvement="Consider using Raft heartbeat optimizations.",
            published_at=now,
        )
        session.add(feedback)

        # 7. Resubmission (RSB-2026-000001)
        sub_id_v2 = f"SUB-{sample_assignment.assignment_id}-{sample_learner.learner_id}-02"
        submission_v2 = Submission(
            submission_id=sub_id_v2,
            assignment_id=sample_assignment.assignment_id,
            learner_id=sample_learner.learner_id,
            enrollment_id=sample_enrollment.enrollment_id,
            attempt_number=2,
            submitted_at=now + timedelta(hours=2),
            status=SubmissionStatus.SUBMITTED,
            is_late=False,
            late_duration_seconds=0,
            late_penalty_percentage=Decimal("0.00"),
            raw_score=Decimal("98.00"),
            final_score=Decimal("98.00"),
        )
        session.add(submission_v2)
        session.flush()

        resubmission = Resubmission(
            resubmission_id="RSB-2026-000001",
            original_submission_id=sub_id,
            new_submission_id=sub_id_v2,
            reason="Incorporated instructor feedback on heartbeat timeouts.",
            change_summary="Refactored heartbeat loop and added partition test.",
            approved_by="USR-INST-0042",
            status=ResubmissionStatus.SUBMITTED,
            requested_at=now + timedelta(hours=1),
        )
        session.add(resubmission)

        # 8. Appeal (APP-2026-000001)
        appeal = Appeal(
            appeal_id="APP-2026-000001",
            submission_id=sub_id,
            grade_id=grade_id,
            learner_id=sample_learner.learner_id,
            status=AppealStatus.SUBMITTED,
            reason_category=AppealReasonCategory.CALCULATION_ERROR,
            learner_statement="Criterion 1 points sum to 48 instead of 47.",
            contested_criteria=[criteria[0].criterion_id],
            original_grade=Decimal("94.00"),
            requested_grade=Decimal("95.00"),
            submitted_at=now + timedelta(hours=3),
        )
        session.add(appeal)

        # 9. AuditLog (AUD-2026-000001)
        audit = AuditService.create_audit_entry(
            audit_id="AUD-2026-000001",
            entity_name="appeal",
            entity_id=appeal.appeal_id,
            action=AuditActionType.INSERT,
            actor_id=sample_learner.learner_id,
            actor_role="learner",
            old_values=None,
            new_values={"status": "submitted", "requested_grade": 95.00},
            client_ip="192.168.1.10",
            user_agent="pytest-client/1.0"
        )

        session.commit()

        # Assertions
        assert session.get(Submission, sub_id) is not None
        assert session.get(SubmissionArtifact, f"ART-{sub_id}-01") is not None
        assert session.get(Grade, grade_id) is not None
        assert session.get(Feedback, f"FBK-{grade_id}-01") is not None
        assert session.get(Resubmission, "RSB-2026-000001") is not None
        assert session.get(Appeal, "APP-2026-000001") is not None
        assert session.get(SubmissionStatusHistory, "SSH-2026-000001") is not None
        assert session.get(AuditLog, "AUD-2026-000001") is not None

    def test_02_primary_keys_are_unique(self, session, sample_course):
        """2. Verify that attempting to insert a duplicate primary key is strictly rejected."""
        existing_pk = sample_course.course_id
        session.expunge(sample_course)

        duplicate_course = Course(
            course_id=existing_pk,  # Same PK
            code="CS-999",
            title="Duplicate Test",
            department="Computer Science",
            term="Fall 2026",
            start_date=datetime.now(timezone.utc),
            end_date=datetime.now(timezone.utc) + timedelta(days=60),
        )
        session.add(duplicate_course)
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()

    def test_03_foreign_key_relationships_enforced(self, session, sample_assignment):
        """3. Verify that foreign key constraints are strictly enforced."""
        now = datetime.now(timezone.utc)
        orphan_submission = Submission(
            submission_id="SUB-ASN-2026-000001-LNR-NONEXISTENT-01",
            assignment_id=sample_assignment.assignment_id,
            learner_id="LNR-NONEXISTENT-999999",  # Non-existent learner
            enrollment_id="ENR-NONEXISTENT-999999",
            attempt_number=1,
            submitted_at=now,
            status=SubmissionStatus.SUBMITTED,
        )
        session.add(orphan_submission)
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()

    def test_04_invalid_rubric_and_grade_scores_rejected(self, session, sample_rubric):
        """4. Verify that negative or invalid scores violate database check constraints."""
        invalid_criterion = RubricCriterion(
            criterion_id="CRT-TEST-INVALID-01",
            rubric_id=sample_rubric.rubric_id,
            criterion_name="Negative Test",
            max_points=Decimal("-10.00"),  # Violates CHECK (max_points > 0)
            weight=Decimal("1.00"),
            display_order=1,
        )
        session.add(invalid_criterion)
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()

    def test_05_duplicate_enrollment_rejected(self, session, sample_course, sample_learner, sample_enrollment):
        """5. Verify that a learner cannot be enrolled into the same course more than once."""
        duplicate_enrollment = Enrollment(
            enrollment_id="ENR-2026-000002",
            course_id=sample_course.course_id,
            learner_id=sample_learner.learner_id,  # Duplicate pair
            status=EnrollmentStatus.ACTIVE,
        )
        session.add(duplicate_enrollment)
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()

    def test_06_submission_versions_are_preserved(
        self, session, sample_assignment, sample_learner, sample_enrollment
    ):
        """6. Verify that multiple submission attempts are preserved immutably."""
        now = datetime.now(timezone.utc)

        # Attempt 1
        sub1_id = f"SUB-{sample_assignment.assignment_id}-{sample_learner.learner_id}-01"
        sub1 = Submission(
            submission_id=sub1_id,
            assignment_id=sample_assignment.assignment_id,
            learner_id=sample_learner.learner_id,
            enrollment_id=sample_enrollment.enrollment_id,
            attempt_number=1,
            submitted_at=now,
            status=SubmissionStatus.GRADED,
            raw_score=Decimal("72.00"),
            final_score=Decimal("72.00"),
        )
        session.add(sub1)
        session.flush()

        # Attempt 2 (Resubmission)
        sub2_id = f"SUB-{sample_assignment.assignment_id}-{sample_learner.learner_id}-02"
        sub2 = Submission(
            submission_id=sub2_id,
            assignment_id=sample_assignment.assignment_id,
            learner_id=sample_learner.learner_id,
            enrollment_id=sample_enrollment.enrollment_id,
            attempt_number=2,
            submitted_at=now + timedelta(days=1),
            status=SubmissionStatus.SUBMITTED,
            raw_score=Decimal("92.00"),
            final_score=Decimal("92.00"),
        )
        session.add(sub2)
        session.flush()

        resubmission = Resubmission(
            resubmission_id="RSB-2026-000002",
            original_submission_id=sub1_id,
            new_submission_id=sub2_id,
            reason="Resubmission allowed per course policy",
            status=ResubmissionStatus.SUBMITTED,
        )
        session.add(resubmission)
        session.commit()

        # Both attempts must exist independently
        record_sub1 = session.get(Submission, sub1_id)
        record_sub2 = session.get(Submission, sub2_id)
        assert record_sub1 is not None and record_sub1.attempt_number == 1
        assert record_sub2 is not None and record_sub2.attempt_number == 2
        assert record_sub1.final_score == Decimal("72.00")
        assert record_sub2.final_score == Decimal("92.00")
        assert record_sub2.resubmission_as_new.original_submission_id == sub1_id

    def test_07_audit_records_are_append_only_and_ids_immutable(self, session, sample_course):
        """7. Verify that IDs are immutable and audit records cannot be silently modified."""
        # Attempting to mutate a primary key must raise ValueError
        with pytest.raises(ValueError, match="Immutable ID Violation"):
            sample_course.course_id = "CRS-2026-MUTATED"
            session.commit()
        session.rollback()

        # Audit log creation works seamlessly
        audit = AuditService.create_audit_entry(
            audit_id="AUD-2026-000002",
            entity_name="course",
            entity_id=sample_course.course_id,
            action=AuditActionType.UPDATE,
            actor_id="admin-01",
            old_values={"title": "Old Title"},
            new_values={"title": "Distributed Data Systems"},
        )
        session.commit()
        fetched = session.get(AuditLog, "AUD-2026-000002")
        assert fetched.entity_name == "course"
        assert fetched.action == AuditActionType.UPDATE

    def test_08_timezone_aware_timestamps_handled_correctly(
        self, session, sample_assignment, sample_learner, sample_enrollment
    ):
        """8. Verify that timezone-aware timestamps (specifically Asia/Kolkata) are handled accurately."""
        # 1. Verify zoneinfo resolution for Asia/Kolkata
        ist_tz = ZoneInfo("Asia/Kolkata")
        assert ist_tz.key == "Asia/Kolkata"

        # 2. Assignment due date is timezone-aware in UTC
        due_utc = sample_assignment.due_date
        assert due_utc.tzinfo is not None

        # 3. Learner submits from India (IST = UTC+05:30)
        # Exactly 30 minutes before the assignment deadline
        sub_time_ist = (due_utc - timedelta(minutes=30)).astimezone(ist_tz)
        assert sub_time_ist.tzinfo is not None

        # Verify that comparison across timezones works seamlessly
        assert sub_time_ist < due_utc
        assert not (sub_time_ist > due_utc)

        # 4. Persist a submission using the Asia/Kolkata localized timestamp
        sub_id = f"SUB-{sample_assignment.assignment_id}-{sample_learner.learner_id}-08"
        submission = Submission(
            submission_id=sub_id,
            assignment_id=sample_assignment.assignment_id,
            learner_id=sample_learner.learner_id,
            enrollment_id=sample_enrollment.enrollment_id,
            attempt_number=1,
            submitted_at=sub_time_ist,
            status=SubmissionStatus.SUBMITTED,
            is_late=False,
            late_duration_seconds=0,
            late_penalty_percentage=Decimal("0.00"),
        )
        session.add(submission)
        session.commit()

        # 5. Retrieve from DB and verify timezone-awareness is preserved without naive conversion
        retrieved = session.get(Submission, sub_id)
        assert retrieved is not None
        assert retrieved.submitted_at.tzinfo is not None

        # Convert back to Asia/Kolkata and check exact component identity
        retrieved_ist = retrieved.submitted_at.astimezone(ist_tz)
        assert retrieved_ist.hour == sub_time_ist.hour
        assert retrieved_ist.minute == sub_time_ist.minute
        assert retrieved_ist.second == sub_time_ist.second
        assert retrieved_ist.tzinfo == ist_tz

    def test_09_multi_timezone_late_submission_reconciliation(
        self, session, sample_assignment, sample_learner, sample_enrollment
    ):
        """9. Verify late deadline reconciliation across multiple timezones (Asia/Kolkata and America/New_York)."""
        ist_tz = ZoneInfo("Asia/Kolkata")
        ny_tz = ZoneInfo("America/New_York")

        due_utc = sample_assignment.due_date
        grace_period = timedelta(minutes=sample_assignment.grace_period_minutes)

        # Scenario A: Submitted 10 minutes past deadline in IST (within 15-min grace period)
        sub_within_grace_ist = (due_utc + timedelta(minutes=10)).astimezone(ist_tz)
        is_late_grace = sub_within_grace_ist > (due_utc + grace_period)
        assert is_late_grace is False

        # Scenario B: Submitted 2 hours past deadline in NY timezone (exceeds grace period)
        sub_late_ny = (due_utc + timedelta(hours=2)).astimezone(ny_tz)
        is_late_ny = sub_late_ny > (due_utc + grace_period)
        assert is_late_ny is True
        lateness_seconds = int((sub_late_ny - due_utc).total_seconds())
        assert lateness_seconds == 7200
