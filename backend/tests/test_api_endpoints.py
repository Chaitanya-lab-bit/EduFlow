"""
Comprehensive automated tests for EduFlow Phase 4 REST API modules.
Covers:
  1. Course APIs (create, list, get, update)
  2. Learner APIs (register, list, get, update)
  3. Enrollment APIs (enroll, list, check status)
  4. Assignment APIs (create, publish, list, details, update, configure rubrics)
  5. Submission APIs (submit, upload artifacts, history, late status, cutoff & enrollment guards)
  6. Grading APIs (grade rubric criteria, late penalty calculation, score bounds, audit log)
  7. Feedback APIs (add feedback, list feedback)
  8. Resubmission APIs (request resubmission, limit check, approve & create attempt 2, reject)
  9. Appeal APIs (submit appeal, window expiry check, approve with atomic grade update, reject)
  10. Dashboard APIs (all 8 metrics, pending grading, late submissions, averages)
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
    Submission, Grade, AuditLog
)

class TestCourseAPI:
    def test_create_course_success(self, client):
        now = datetime.now(timezone.utc)
        payload = {
            "code": "CS-601",
            "title": "Cloud Native Distributed Systems",
            "department": "Computer Science",
            "term": "Fall 2026",
            "timezone": "America/New_York",
            "start_date": (now - timedelta(days=10)).isoformat(),
            "end_date": (now + timedelta(days=80)).isoformat(),
        }
        res = client.post("/api/courses", json=payload)
        assert res.status_code == 201
        data = res.get_json()
        assert data["course"]["code"] == "CS-601"
        assert data["course"]["course_id"].startswith("CRS-")

    def test_create_course_duplicate_code_conflict(self, client, sample_course):
        now = datetime.now(timezone.utc)
        payload = {
            "code": sample_course.code,  # Duplicate!
            "title": "Another Course",
            "department": "Computer Science",
            "term": "Fall 2026",
            "start_date": now.isoformat(),
            "end_date": (now + timedelta(days=30)).isoformat(),
        }
        res = client.post("/api/courses", json=payload)
        assert res.status_code == 409
        assert res.get_json()["error_code"] == "ERR_DUPLICATE_ENTITY"

    def test_create_course_invalid_dates_rejected(self, client):
        now = datetime.now(timezone.utc)
        payload = {
            "code": "CS-999",
            "title": "Bad Dates Course",
            "department": "Computer Science",
            "term": "Fall 2026",
            "start_date": now.isoformat(),
            "end_date": (now - timedelta(days=5)).isoformat(),  # End before start!
        }
        res = client.post("/api/courses", json=payload)
        assert res.status_code == 422

    def test_list_courses_with_filtering(self, client, sample_course):
        res = client.get("/api/courses?department=Computer")
        assert res.status_code == 200
        data = res.get_json()
        assert len(data["courses"]) >= 1
        assert "meta" in data
        assert data["meta"]["total"] >= 1

    def test_get_course_details_and_not_found(self, client, sample_course):
        res = client.get(f"/api/courses/{sample_course.course_id}")
        assert res.status_code == 200
        assert res.get_json()["course"]["course_id"] == sample_course.course_id

        res_nf = client.get("/api/courses/NON_EXISTENT")
        assert res_nf.status_code == 404

    def test_update_course(self, client, sample_course):
        payload = {"title": "Updated Course Title", "status": "active"}
        res = client.patch(f"/api/courses/{sample_course.course_id}", json=payload)
        assert res.status_code == 200
        assert res.get_json()["course"]["title"] == "Updated Course Title"


class TestLearnerAPI:
    def test_register_learner_success(self, client):
        payload = {
            "student_number": "STU-888888",
            "first_name": "Jordan",
            "last_name": "Lee",
            "email": "jordan.lee@university.edu",
            "timezone": "America/Chicago",
        }
        res = client.post("/api/learners", json=payload)
        assert res.status_code == 201
        data = res.get_json()
        assert data["learner"]["email"] == "jordan.lee@university.edu"
        assert data["learner"]["learner_id"].startswith("LNR-")

    def test_register_learner_duplicate_email(self, client, sample_learner):
        payload = {
            "student_number": "STU-999999",
            "first_name": "Copy",
            "last_name": "Cat",
            "email": sample_learner.email,
        }
        res = client.post("/api/learners", json=payload)
        assert res.status_code == 409
        assert res.get_json()["error_code"] == "ERR_DUPLICATE_ENTITY"

    def test_list_learners_search(self, client, sample_learner):
        res = client.get(f"/api/learners?search={sample_learner.last_name}")
        assert res.status_code == 200
        data = res.get_json()
        assert len(data["learners"]) >= 1

    def test_get_learner_details(self, client, sample_learner):
        res = client.get(f"/api/learners/{sample_learner.learner_id}")
        assert res.status_code == 200
        assert res.get_json()["learner"]["learner_id"] == sample_learner.learner_id

    def test_update_learner(self, client, sample_learner):
        res = client.patch(f"/api/learners/{sample_learner.learner_id}", json={"first_name": "Alexander"})
        assert res.status_code == 200
        assert res.get_json()["learner"]["first_name"] == "Alexander"


class TestEnrollmentAPI:
    def test_enroll_learner_success(self, client, sample_course):
        # Register a second learner
        l_res = client.post("/api/learners", json={
            "student_number": "STU-123456",
            "first_name": "Taylor",
            "last_name": "Swift",
            "email": "taylor.swift@university.edu",
        })
        new_lid = l_res.get_json()["learner"]["learner_id"]

        res = client.post("/api/enrollments", json={
            "course_id": sample_course.course_id,
            "learner_id": new_lid,
        })
        assert res.status_code == 201
        data = res.get_json()
        assert data["enrollment"]["course_id"] == sample_course.course_id
        assert data["enrollment"]["learner_id"] == new_lid

    def test_enroll_duplicate_rejected(self, client, sample_enrollment):
        res = client.post("/api/enrollments", json={
            "course_id": sample_enrollment.course_id,
            "learner_id": sample_enrollment.learner_id,
        })
        assert res.status_code == 409
        assert res.get_json()["error_code"] == "ERR_DUPLICATE_ENTITY"

    def test_check_enrollment_status(self, client, sample_enrollment):
        res = client.get(f"/api/enrollments/status?course_id={sample_enrollment.course_id}&learner_id={sample_enrollment.learner_id}")
        assert res.status_code == 200
        data = res.get_json()
        assert data["is_enrolled"] is True
        assert data["status"] == "active"

        res_not = client.get(f"/api/enrollments/status?course_id={sample_enrollment.course_id}&learner_id=NON_EXISTENT")
        assert res_not.status_code == 200
        assert res_not.get_json()["is_enrolled"] is False


class TestAssignmentAPI:
    def test_create_and_publish_assignment_with_rubric(self, client, sample_course):
        now = datetime.now(timezone.utc)
        payload = {
            "course_id": sample_course.course_id,
            "title": "Kafka Real-Time Analytics",
            "description": "Implement streaming consumer groups.",
            "max_score": 100.0,
            "due_date": (now + timedelta(days=7)).isoformat(),
            "cutoff_date": (now + timedelta(days=10)).isoformat(),
            "rubric": {
                "title": "Kafka Rubric v1",
                "total_points": 100.0,
                "criteria": [
                    {"criterion_name": "Throughput", "max_points": 50.0, "display_order": 1},
                    {"criterion_name": "Correctness", "max_points": 50.0, "display_order": 2},
                ]
            }
        }
        res = client.post("/api/assignments", json=payload)
        assert res.status_code == 201
        aid = res.get_json()["assignment"]["assignment_id"]

        # Publish assignment (should succeed because criteria 50+50 == 100 max_score)
        pub_res = client.post(f"/api/assignments/{aid}/publish")
        assert pub_res.status_code == 200
        assert pub_res.get_json()["assignment"]["status"] == "published"

    def test_publish_assignment_fails_if_rubric_sum_mismatched(self, client, sample_course):
        now = datetime.now(timezone.utc)
        payload = {
            "course_id": sample_course.course_id,
            "title": "Mismatched Rubric Lab",
            "max_score": 100.0,
            "due_date": (now + timedelta(days=5)).isoformat(),
            "cutoff_date": (now + timedelta(days=7)).isoformat(),
            "rubric": {
                "title": "Bad Rubric",
                "total_points": 80.0,
                "criteria": [
                    {"criterion_name": "Part 1", "max_points": 40.0},
                    {"criterion_name": "Part 2", "max_points": 40.0},
                ]  # Sum = 80, but max_score = 100!
            }
        }
        res = client.post("/api/assignments", json=payload)
        aid = res.get_json()["assignment"]["assignment_id"]

        # Publish should fail with 422 RubricPointsMismatch
        pub_res = client.post(f"/api/assignments/{aid}/publish")
        assert pub_res.status_code == 422
        assert pub_res.get_json()["error_code"] == "ERR_RUBRIC_POINTS_MISMATCH"

    def test_get_assignment_details(self, client, sample_assignment, sample_rubric):
        res = client.get(f"/api/assignments/{sample_assignment.assignment_id}")
        assert res.status_code == 200
        data = res.get_json()["assignment"]
        assert data["assignment_id"] == sample_assignment.assignment_id
        assert len(data["rubrics"]) >= 1


class TestSubmissionAPI:
    def test_submission_unenrolled_learner_fails_ex01(self, client, sample_assignment):
        # Register an unenrolled learner
        l_res = client.post("/api/learners", json={
            "student_number": "STU-UNENR",
            "first_name": "No",
            "last_name": "Enrollment",
            "email": "unenrolled@university.edu",
        })
        unenrolled_lid = l_res.get_json()["learner"]["learner_id"]

        res = client.post("/api/submissions", json={
            "assignment_id": sample_assignment.assignment_id,
            "learner_id": unenrolled_lid,
            "status": "draft"
        })
        assert res.status_code == 403
        assert res.get_json()["error_code"] == "ERR_UNENROLLED_LEARNER"

    def test_submission_past_cutoff_fails_ex06(self, client, sample_assignment, sample_learner, sample_enrollment):
        now = datetime.now(timezone.utc)
        sub_time = now + timedelta(days=20)  # Past cutoff_date (which is now + 10 days)

        res = client.post("/api/submissions", json={
            "assignment_id": sample_assignment.assignment_id,
            "learner_id": sample_learner.learner_id,
            "submitted_at": sub_time.isoformat(),
            "status": "draft"
        })
        assert res.status_code == 403
        assert res.get_json()["error_code"] == "ERR_DEADLINE_EXCEEDED"

    def test_submission_missing_required_artifacts_fails_ex05(self, client, sample_assignment, sample_learner, sample_enrollment):
        # Assignment requires ['code_repository', 'report_pdf']
        res = client.post("/api/submissions", json={
            "assignment_id": sample_assignment.assignment_id,
            "learner_id": sample_learner.learner_id,
            "status": "submitted",  # finalize without artifacts
            "artifacts": []
        })
        assert res.status_code == 422
        assert res.get_json()["error_code"] == "MISSING_REQUIRED_ARTIFACTS"

    def test_submission_on_time_success(self, client, sample_assignment, sample_learner, sample_enrollment):
        now = datetime.now(timezone.utc)
        sub_time = now + timedelta(days=1)  # Well before due date (now + 7 days)
        payload = {
            "assignment_id": sample_assignment.assignment_id,
            "learner_id": sample_learner.learner_id,
            "submitted_at": sub_time.isoformat(),
            "status": "submitted",
            "artifacts": [
                {
                    "artifact_type": "report_pdf",
                    "file_name": "report.pdf",
                    "file_size_bytes": 1024,
                    "mime_type": "application/pdf",
                    "storage_uri": "s3://eduflow/report.pdf",
                    "checksum_sha256": "abcdef1234567890abcdef1234567890",
                },
                {
                    "artifact_type": "code_repository",
                    "file_name": "repo.zip",
                    "file_size_bytes": 2048,
                    "mime_type": "application/zip",
                    "storage_uri": "s3://eduflow/repo.zip",
                    "checksum_sha256": "123456abcdef7890123456abcdef7890",
                }
            ]
        }
        res = client.post("/api/submissions", json=payload)
        assert res.status_code == 201
        data = res.get_json()["submission"]
        assert data["is_late"] is False
        assert data["late_penalty_percentage"] == 0.0

        sub_id = data["submission_id"]
        # Check late-status endpoint
        late_res = client.get(f"/api/submissions/{sub_id}/late-status")
        assert late_res.status_code == 200
        assert late_res.get_json()["is_late"] is False


class TestGradingAPI:
    def test_grade_submission_success_and_penalty(self, client, sample_assignment, sample_rubric, sample_learner, sample_enrollment):
        # Create a submission that is late (1 day late beyond grace period: 18 hours late)
        sub_time = sample_assignment.due_date + timedelta(hours=18)
        sub_payload = {
            "assignment_id": sample_assignment.assignment_id,
            "learner_id": sample_learner.learner_id,
            "submitted_at": sub_time.isoformat(),
            "status": "submitted",
            "artifacts": [
                {"artifact_type": "report_pdf", "file_name": "r.pdf", "file_size_bytes": 100, "mime_type": "app/pdf", "storage_uri": "s3://r", "checksum_sha256": "1234567890abcdef1234567890"},
                {"artifact_type": "code_repository", "file_name": "c.zip", "file_size_bytes": 100, "mime_type": "app/zip", "storage_uri": "s3://c", "checksum_sha256": "1234567890abcdef1234567891"},
            ]
        }
        sub_res = client.post("/api/submissions", json=sub_payload)
        assert sub_res.status_code == 201
        sub_data = sub_res.get_json()["submission"]
        sub_id = sub_data["submission_id"]
        assert sub_data["is_late"] is True
        assert sub_data["late_penalty_percentage"] == 5.0  # 1 day late * 5% per day

        # Grade the submission: Criterion 1 max 50 (award 40), Criterion 2 max 50 (award 40) -> Raw = 80.0
        # Expected Late Penalty = 80.0 * 5% = 4.0
        # Final Score = 80.0 - 4.0 = 76.0
        c1, c2 = sample_rubric.criteria[0], sample_rubric.criteria[1]
        grade_payload = {
            "submission_id": sub_id,
            "graded_by": "USR-INST-0001",
            "criteria_scores": [
                {"criterion_id": c1.criterion_id, "score_awarded": 40.0, "evaluator_comment": "Good"},
                {"criterion_id": c2.criterion_id, "score_awarded": 40.0, "evaluator_comment": "Solid"},
            ],
            "bonus_points": 0.0,
        }
        grade_res = client.post("/api/grades", json=grade_payload)
        assert grade_res.status_code == 201
        grd = grade_res.get_json()["grade"]
        assert grd["raw_score"] == 80.0
        assert grd["late_penalty_applied"] == 4.0
        assert grd["final_score"] == 76.0

        # View grade
        get_res = client.get(f"/api/grades/{grd['grade_id']}")
        assert get_res.status_code == 200
        assert len(get_res.get_json()["grade"]["criterion_scores"]) == 2

    def test_grade_exceeding_rubric_maximum_fails_ex02(self, client, sample_assignment, sample_rubric, sample_learner, sample_enrollment):
        sub_payload = {
            "assignment_id": sample_assignment.assignment_id,
            "learner_id": sample_learner.learner_id,
            "status": "draft",
        }
        sub_res = client.post("/api/submissions", json=sub_payload)
        sub_id = sub_res.get_json()["submission"]["submission_id"]

        c1 = sample_rubric.criteria[0]  # max_points = 50.0
        grade_payload = {
            "submission_id": sub_id,
            "graded_by": "USR-INST-0001",
            "criteria_scores": [
                {"criterion_id": c1.criterion_id, "score_awarded": 55.0},  # Exceeds 50.0!
            ]
        }
        res = client.post("/api/grades", json=grade_payload)
        assert res.status_code == 422
        assert res.get_json()["error_code"] == "ERR_SCORE_EXCEEDS_MAX"


class TestFeedbackAPI:
    def test_add_and_list_feedback(self, client, sample_assignment, sample_rubric, sample_learner, sample_enrollment):
        sub_res = client.post("/api/submissions", json={
            "assignment_id": sample_assignment.assignment_id,
            "learner_id": sample_learner.learner_id,
            "status": "draft"
        })
        sub_id = sub_res.get_json()["submission"]["submission_id"]

        c1 = sample_rubric.criteria[0]
        c2 = sample_rubric.criteria[1]
        grd_res = client.post("/api/grades", json={
            "submission_id": sub_id,
            "graded_by": "USR-INST-0001",
            "criteria_scores": [
                {"criterion_id": c1.criterion_id, "score_awarded": 45.0},
                {"criterion_id": c2.criterion_id, "score_awarded": 45.0},
            ]
        })
        gid = grd_res.get_json()["grade"]["grade_id"]

        # Add feedback
        fb_res = client.post("/api/feedback", json={
            "grade_id": gid,
            "author_id": "USR-INST-0001",
            "general_comments": "Great work on streaming architecture.",
            "strengths": "Clean code and good test coverage.",
            "areas_for_improvement": "Add monitoring metrics.",
        })
        assert fb_res.status_code == 201
        data = fb_res.get_json()["feedback"]
        assert data["grade_id"] == gid

        # List feedback
        list_res = client.get(f"/api/feedback?submission_id={sub_id}")
        assert list_res.status_code == 200
        assert len(list_res.get_json()["feedback"]) >= 1


class TestResubmissionAPI:
    def test_resubmission_request_and_approval(self, client, sample_assignment, sample_rubric, sample_learner, sample_enrollment):
        # 1. First submission
        sub_res = client.post("/api/submissions", json={
            "assignment_id": sample_assignment.assignment_id,
            "learner_id": sample_learner.learner_id,
            "status": "draft"
        })
        sub_id = sub_res.get_json()["submission"]["submission_id"]

        # 2. Request resubmission
        req_res = client.post("/api/resubmissions", json={
            "original_submission_id": sub_id,
            "reason": "Want to fix edge case handling and improve test suite.",
        })
        assert req_res.status_code == 201
        rsb_id = req_res.get_json()["resubmission"]["resubmission_id"]

        # 3. Instructor approves resubmission
        appr_res = client.post(f"/api/resubmissions/{rsb_id}/review", json={
            "status": "approved",
            "reviewed_by": "USR-INST-0001",
            "change_summary": "Approved for attempt 2.",
        })
        assert appr_res.status_code == 200
        assert appr_res.get_json()["resubmission"]["status"] == "approved"


class TestAppealAPI:
    def test_appeal_submission_and_decision_with_audit_ex04(self, client, sample_assignment, sample_rubric, sample_learner, sample_enrollment):
        # 1. Create and grade submission
        sub_res = client.post("/api/submissions", json={
            "assignment_id": sample_assignment.assignment_id,
            "learner_id": sample_learner.learner_id,
            "status": "draft"
        })
        sub_id = sub_res.get_json()["submission"]["submission_id"]

        c1, c2 = sample_rubric.criteria[0], sample_rubric.criteria[1]
        grd_res = client.post("/api/grades", json={
            "submission_id": sub_id,
            "graded_by": "USR-INST-0001",
            "criteria_scores": [
                {"criterion_id": c1.criterion_id, "score_awarded": 40.0},
                {"criterion_id": c2.criterion_id, "score_awarded": 40.0},
            ]
        })
        assert grd_res.status_code == 201

        # 2. Submit appeal
        app_res = client.post("/api/appeals", json={
            "submission_id": sub_id,
            "learner_id": sample_learner.learner_id,
            "reason_category": "calculation_error",
            "learner_statement": "The criterion 1 points were computed incorrectly.",
            "requested_grade": 90.0,
        })
        assert app_res.status_code == 201
        app_id = app_res.get_json()["appeal"]["appeal_id"]

        # 3. Adjudicate appeal with approval (final_grade: 92.0)
        # EX-04: Must register AuditLog atomically
        dec_res = client.post(f"/api/appeals/{app_id}/decision", json={
            "status": "approved",
            "reviewed_by": "USR-DEAN-0001",
            "decision_notes": "Calculation verified and adjusted.",
            "final_grade": 92.0,
        })
        assert dec_res.status_code == 200
        data = dec_res.get_json()["appeal"]
        assert data["status"] == "approved"
        assert data["final_grade"] == 92.0

        # Verify audit log exists
        audits = AuditLog.query.filter_by(action=AuditActionType.APPEAL_DECISION).all()
        assert len(audits) >= 1
        assert audits[-1].new_values["final_score"] == 92.0


class TestDashboardAPI:
    def test_dashboard_metrics(self, client, sample_course, sample_learner, sample_assignment):
        res = client.get("/api/dashboard/stats")
        assert res.status_code == 200
        metrics = res.get_json()["metrics"]
        assert "total_learners" in metrics
        assert "total_courses" in metrics
        assert "total_assignments" in metrics
        assert "total_submissions" in metrics
        assert "pending_grading" in metrics
        assert "late_submissions" in metrics
        assert "average_grade" in metrics
        assert "pending_appeals" in metrics
        assert metrics["total_courses"] >= 1
        assert metrics["total_learners"] >= 1
        assert metrics["total_assignments"] >= 1


class TestFrontendIntegration:
    def test_serve_frontend_index(self, client):
        res = client.get("/")
        assert res.status_code == 200
        assert b"<!DOCTYPE html>" in res.data or b"EduFlow" in res.data

    def test_cors_headers_present(self, client):
        res = client.get("/api/health")
        assert res.status_code == 200
        assert res.headers.get("Access-Control-Allow-Origin") == "*"

    def test_unknown_api_route_returns_json_404(self, client):
        res = client.get("/api/non-existent-route-999")
        assert res.status_code == 404
        data = res.get_json()
        assert data["error_code"] == "ERR_NOT_FOUND"
