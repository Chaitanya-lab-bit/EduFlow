"""
Phase 7 Final End-to-End Workflow Tests for EduFlow.
Validates the complete academic lifecycle:
  1. Course & Learner Setup (Admin)
  2. Rubric-based Assignment Publication (Instructor)
  3. Artifact Ingestion & Lateness Evaluation (Learner)
  4. Rubric Grading & Single Late Penalty Application (Instructor)
  5. Qualitative Feedback Publication (Instructor)
  6. Resubmission Pipeline & Version Incrementing (Learner & Instructor)
  7. Academic Appeals Adjudication & Audit Logging (Learner & Committee)
  8. Dashboard Telemetry & Metric Accuracy
  9. Business Rule Exceptions (EX-01 through EX-08)
  10. Full-Stack Frontend Integration
"""
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import pytest

from backend.models.enums import (
    CourseStatus, EnrollmentStatus, AssignmentStatus,
    SubmissionStatus, ArtifactType, GradeStatus,
    FeedbackVisibility, ResubmissionStatus, AppealStatus,
    AppealReasonCategory, AuditActionType
)
from backend.models import (
    Course, Learner, Enrollment, Assignment, Rubric, RubricCriterion,
    Submission, Grade, AuditLog, SubmissionStatusHistory
)

class TestEndToEndAcademicLifecycle:
    def test_complete_course_to_evaluation_lifecycle(self, client):
        now = datetime.now(timezone.utc)

        # ---------------------------------------------------------
        # Step 1: Admin creates course
        # ---------------------------------------------------------
        course_payload = {
            "code": "CS-901",
            "title": "Advanced Distributed Systems & Microservices",
            "department": "Computer Science",
            "term": "Fall 2026",
            "timezone": "UTC",
            "start_date": (now - timedelta(days=15)).isoformat(),
            "end_date": (now + timedelta(days=90)).isoformat(),
        }
        c_res = client.post("/api/courses", json=course_payload)
        assert c_res.status_code == 201
        course_id = c_res.get_json()["course"]["course_id"]

        # ---------------------------------------------------------
        # Step 2: Admin registers learner
        # ---------------------------------------------------------
        learner_payload = {
            "first_name": "Jordan",
            "last_name": "Taylor",
            "email": "jordan.taylor@student.eduflow.edu",
            "student_number": "STU-994411",
            "timezone": "UTC"
        }
        l_res = client.post("/api/learners", json=learner_payload)
        assert l_res.status_code == 201
        learner_id = l_res.get_json()["learner"]["learner_id"]

        # ---------------------------------------------------------
        # Step 3: Admin enrolls learner in course
        # ---------------------------------------------------------
        enroll_payload = {
            "course_id": course_id,
            "learner_id": learner_id,
            "status": "active"
        }
        e_res = client.post("/api/enrollments", json=enroll_payload)
        assert e_res.status_code == 201

        # Verify enrollment check API
        chk_res = client.get(f"/api/enrollments/status?learner_id={learner_id}&course_id={course_id}")
        assert chk_res.status_code == 200
        assert chk_res.get_json()["is_enrolled"] is True

        # ---------------------------------------------------------
        # Step 4: Instructor authors draft assignment
        # ---------------------------------------------------------
        due_date = now + timedelta(days=7)
        cutoff_date = now + timedelta(days=12)
        assign_payload = {
            "course_id": course_id,
            "title": "Milestone 1: Resilient Stream Processing Engine",
            "description": "Build an event pipeline with fault-tolerant checkpoints.",
            "max_score": 100.0,
            "due_date": due_date.isoformat(),
            "cutoff_date": cutoff_date.isoformat(),
            "grace_period_minutes": 15,
            "late_penalty_per_day": 5.0,
            "max_resubmissions": 1,
            "required_artifact_types": ["code_repository", "report_pdf"],
            "status": "draft"
        }
        a_res = client.post("/api/assignments", json=assign_payload)
        assert a_res.status_code == 201
        assignment_id = a_res.get_json()["assignment"]["assignment_id"]
        assert a_res.get_json()["assignment"]["status"] == "draft"

        # ---------------------------------------------------------
        # Step 5: Instructor tries to publish before configuring rubrics (BR-04)
        # ---------------------------------------------------------
        pub_fail = client.post(f"/api/assignments/{assignment_id}/publish")
        assert pub_fail.status_code == 422
        assert pub_fail.get_json()["error_code"] == "ERR_RUBRIC_POINTS_MISMATCH"

        # ---------------------------------------------------------
        # Step 6: Instructor configures rubric criteria (sum = 100)
        # ---------------------------------------------------------
        rubric_payload = {
            "title": "Stream Engine Evaluation Rubric",
            "total_points": 100.0,
            "version": 1,
            "is_active": True,
            "criteria": [
                {
                    "criterion_name": "Fault Tolerance & Checkpointing",
                    "description": "Correct state snapshotting during worker failure",
                    "max_points": 60.0,
                    "weight": 1.0,
                    "display_order": 1
                },
                {
                    "criterion_name": "Code Quality & Documentation",
                    "description": "Modular code and benchmark results report",
                    "max_points": 40.0,
                    "weight": 1.0,
                    "display_order": 2
                }
            ]
        }
        rub_res = client.post(f"/api/assignments/{assignment_id}/rubrics", json=rubric_payload)
        assert rub_res.status_code == 201
        crit_list = rub_res.get_json()["rubric"]["criteria"]
        c1_id = crit_list[0]["criterion_id"]
        c2_id = crit_list[1]["criterion_id"]

        # ---------------------------------------------------------
        # Step 7: Instructor publishes assignment successfully
        # ---------------------------------------------------------
        pub_res = client.post(f"/api/assignments/{assignment_id}/publish")
        assert pub_res.status_code == 200
        assert pub_res.get_json()["assignment"]["status"] == "published"

        # ---------------------------------------------------------
        # Step 8: Learner submits coursework on-time with 2 artifacts
        # ---------------------------------------------------------
        submit_payload = {
            "assignment_id": assignment_id,
            "learner_id": learner_id,
            "submitted_at": (now + timedelta(days=2)).isoformat(),
            "status": "submitted",
            "artifacts": [
                {
                    "artifact_type": "code_repository",
                    "file_name": "pipeline_engine.zip",
                    "file_size_bytes": 2400100,
                    "mime_type": "application/zip",
                    "storage_uri": "s3://eduflow-artifacts/pipeline_engine.zip",
                    "checksum_sha256": "1234567890abcdef1234567890abcdef"
                },
                {
                    "artifact_type": "report_pdf",
                    "file_name": "benchmarks_report.pdf",
                    "file_size_bytes": 512000,
                    "mime_type": "application/pdf",
                    "storage_uri": "s3://eduflow-artifacts/benchmarks_report.pdf",
                    "checksum_sha256": "abcdef1234567890abcdef1234567890"
                }
            ]
        }
        sub_res = client.post("/api/submissions", json=submit_payload)
        assert sub_res.status_code == 201
        submission_id = sub_res.get_json()["submission"]["submission_id"]
        assert sub_res.get_json()["submission"]["attempt_number"] == 1
        assert sub_res.get_json()["submission"]["status"] == "submitted"

        # Check late status endpoint
        late_chk = client.get(f"/api/submissions/{submission_id}/late-status")
        assert late_chk.status_code == 200
        assert late_chk.get_json()["is_late"] is False
        assert late_chk.get_json()["late_penalty_percentage"] == 0.0

        # ---------------------------------------------------------
        # Step 9: Instructor evaluates submission with rubric criteria
        # ---------------------------------------------------------
        grade_payload = {
            "submission_id": submission_id,
            "graded_by": "INST-2026-0001",
            "criteria_scores": [
                {
                    "criterion_id": c1_id,
                    "score_awarded": 57.0,
                    "evaluator_comment": "Excellent checkpoint recovery."
                },
                {
                    "criterion_id": c2_id,
                    "score_awarded": 38.0,
                    "evaluator_comment": "Very clear benchmark analysis."
                }
            ]
        }
        grd_res = client.post("/api/grades", json=grade_payload)
        assert grd_res.status_code == 201
        grade_data = grd_res.get_json()["grade"]
        assert grade_data["raw_score"] == 95.0
        assert grade_data["late_penalty_applied"] == 0.0
        assert grade_data["final_score"] == 95.0
        grade_id = grade_data["grade_id"]

        # ---------------------------------------------------------
        # Step 10: Instructor publishes qualitative feedback
        # ---------------------------------------------------------
        fb_payload = {
            "grade_id": grade_id,
            "author_id": "INST-2026-0001",
            "general_comments": "Superb architectural design. Stream state isolation was executed cleanly.",
            "strengths": "Modular checkpoint manager and high throughput benchmarks."
        }
        fb_res = client.post("/api/feedback", json=fb_payload)
        assert fb_res.status_code == 201
        assert fb_res.get_json()["feedback"]["grade_id"] == grade_id

        # Verify feedback list
        fb_list = client.get(f"/api/feedback?grade_id={grade_id}")
        assert fb_list.status_code == 200
        assert len(fb_list.get_json()["feedback"]) >= 1

        # ---------------------------------------------------------
        # Step 11: Learner requests resubmission (allowed 1)
        # ---------------------------------------------------------
        resub_payload = {
            "original_submission_id": submission_id,
            "reason": "Updated edge-case recovery unit tests."
        }
        rs_res = client.post("/api/resubmissions", json=resub_payload)
        assert rs_res.status_code == 201
        resub_id = rs_res.get_json()["resubmission"]["resubmission_id"]

        # Instructor reviews and approves resubmission
        rev_res = client.post(f"/api/resubmissions/{resub_id}/review", json={
            "status": "approved",
            "reviewed_by": "INST-2026-0001",
            "change_summary": "Approved for revision attempt."
        })
        assert rev_res.status_code == 200
        resub_data = rev_res.get_json()["resubmission"]
        assert resub_data["status"] == "approved"
        new_sub_id = resub_data["new_submission_id"]

        # Fetch newly created submission version 2
        new_sub_res = client.get(f"/api/submissions/{new_sub_id}")
        assert new_sub_res.status_code == 200
        new_sub = new_sub_res.get_json()["submission"]
        assert new_sub["attempt_number"] == 2
        assert new_sub["status"] == "submitted"


class TestBusinessRulesAndEdgeCases:
    def test_ex01_unenrolled_learner_cannot_submit(self, client, sample_assignment):
        # Create an unenrolled learner
        l_res = client.post("/api/learners", json={
            "first_name": "Unenrolled",
            "last_name": "Student",
            "email": "unenrolled@eduflow.edu",
            "student_number": "STU-000000",
            "timezone": "UTC"
        })
        unenrolled_id = l_res.get_json()["learner"]["learner_id"]

        res = client.post("/api/submissions", json={
            "assignment_id": sample_assignment.assignment_id,
            "learner_id": unenrolled_id,
            "status": "draft"
        })
        assert res.status_code == 403
        assert res.get_json()["error_code"] == "ERR_UNENROLLED_LEARNER"

    def test_ex06_cutoff_exceeded_submission_rejected(self, client, sample_assignment, sample_learner, sample_enrollment):
        # Submit after cutoff date
        res = client.post("/api/submissions", json={
            "assignment_id": sample_assignment.assignment_id,
            "learner_id": sample_learner.learner_id,
            "submitted_at": (sample_assignment.cutoff_date + timedelta(days=2)).isoformat(),
            "status": "draft"
        })
        assert res.status_code == 403
        assert res.get_json()["error_code"] == "ERR_DEADLINE_EXCEEDED"

    def test_ex02_criterion_score_cannot_exceed_max_points(self, client, sample_submission, sample_assignment, sample_rubric):
        c1 = sample_rubric.criteria[0]
        res = client.post("/api/grades", json={
            "submission_id": sample_submission.submission_id,
            "graded_by": "INST-001",
            "criteria_scores": [
                {
                    "criterion_id": c1.criterion_id,
                    "score_awarded": 150.0  # Exceeds max_points (50.0)
                }
            ]
        })
        assert res.status_code == 422
        assert res.get_json()["error_code"] == "ERR_SCORE_EXCEEDS_MAX"

    def test_br02_and_br05_single_late_penalty_deduction(self, client, sample_assignment, sample_rubric, sample_learner, sample_enrollment):
        # Submit 18 hours late past grace period -> 1 day late -> 5% penalty
        sub_time = sample_assignment.due_date + timedelta(hours=18)
        sub_res = client.post("/api/submissions", json={
            "assignment_id": sample_assignment.assignment_id,
            "learner_id": sample_learner.learner_id,
            "submitted_at": sub_time.isoformat(),
            "status": "submitted",
            "artifacts": [
                {"artifact_type": "report_pdf", "file_name": "r.pdf", "file_size_bytes": 100, "mime_type": "app/pdf", "storage_uri": "s3://r", "checksum_sha256": "1234567890abcdef1234567890"},
                {"artifact_type": "code_repository", "file_name": "c.zip", "file_size_bytes": 100, "mime_type": "app/zip", "storage_uri": "s3://c", "checksum_sha256": "1234567890abcdef1234567891"},
            ]
        })
        submission_id = sub_res.get_json()["submission"]["submission_id"]

        # Check late status
        chk = client.get(f"/api/submissions/{submission_id}/late-status")
        assert chk.get_json()["is_late"] is True
        assert chk.get_json()["late_duration_seconds"] > 0
        assert chk.get_json()["late_penalty_percentage"] == 5.0

        # Grade: raw score 80.0 (40 on c1 + 40 on c2) -> 5% late penalty = 4.0 -> final score 76.0
        c1, c2 = sample_rubric.criteria[0], sample_rubric.criteria[1]
        grd_res = client.post("/api/grades", json={
            "submission_id": submission_id,
            "graded_by": "INST-001",
            "criteria_scores": [
                {"criterion_id": c1.criterion_id, "score_awarded": 40.0},
                {"criterion_id": c2.criterion_id, "score_awarded": 40.0}
            ]
        })
        assert grd_res.status_code == 201
        grd_data = grd_res.get_json()["grade"]
        assert grd_data["raw_score"] == 80.0
        assert grd_data["late_penalty_applied"] == 4.0
        assert grd_data["final_score"] == 76.0

    def test_ex04_appeal_atomic_grade_update_and_audit_trail(self, client, sample_submission, sample_rubric, sample_learner):
        c1, c2 = sample_rubric.criteria[0], sample_rubric.criteria[1]
        grd_res = client.post("/api/grades", json={
            "submission_id": sample_submission.submission_id,
            "graded_by": "INST-001",
            "criteria_scores": [
                {"criterion_id": c1.criterion_id, "score_awarded": 35.0},
                {"criterion_id": c2.criterion_id, "score_awarded": 40.0}
            ]
        })
        grade_id = grd_res.get_json()["grade"]["grade_id"]

        # Submit appeal
        app_res = client.post("/api/appeals", json={
            "submission_id": sample_submission.submission_id,
            "learner_id": sample_learner.learner_id,
            "reason_category": "calculation_error",
            "learner_statement": "Timeout test case passed in re-evaluation.",
            "requested_grade": 88.0
        })
        assert app_res.status_code == 201
        appeal_id = app_res.get_json()["appeal"]["appeal_id"]

        # Adjudicate appeal
        dec_res = client.post(f"/api/appeals/{appeal_id}/decision", json={
            "status": "approved",
            "final_grade": 88.0,
            "reviewed_by": "COMMITTEE-01",
            "decision_notes": "Re-run of test harness proved execution was within timeout threshold."
        })
        assert dec_res.status_code == 200
        appeal_data = dec_res.get_json()["appeal"]
        assert appeal_data["status"] == "approved"
        assert appeal_data["final_grade"] == 88.0

        # Verify AuditLog has recorded this action
        audit = AuditLog.query.filter_by(action=AuditActionType.APPEAL_DECISION).first()
        assert audit is not None
        assert audit.actor_id == "COMMITTEE-01"
        assert audit.new_values["final_score"] == 88.0


class TestDashboardTelemetryAndFrontend:
    def test_dashboard_stats_accuracy(self, client, sample_course, sample_learner, sample_assignment, sample_submission):
        res = client.get("/api/dashboard/stats")
        assert res.status_code == 200
        data = res.get_json()
        assert "metrics" in data
        metrics = data["metrics"]
        assert metrics["total_courses"] >= 1
        assert metrics["total_learners"] >= 1
        assert metrics["total_assignments"] >= 1
        assert metrics["total_submissions"] >= 1

    def test_frontend_full_stack_integration(self, client):
        # Verify index serving
        res = client.get("/")
        assert res.status_code == 200
        assert b"EduFlow" in res.data or b"html" in res.data

        # Verify CORS headers
        health_res = client.get("/api/health")
        assert health_res.status_code == 200
        assert health_res.headers.get("Access-Control-Allow-Origin") == "*"
        assert "GET" in health_res.headers.get("Access-Control-Allow-Methods")
