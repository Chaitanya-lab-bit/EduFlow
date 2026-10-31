"""
Dashboard and Administrative Metrics REST API endpoints.
"""
from flask import Blueprint, jsonify
from sqlalchemy import func

from backend.extensions import db
from backend.models.course import Course
from backend.models.learner import Learner
from backend.models.assignment import Assignment
from backend.models.submission import Submission
from backend.models.grade import Grade
from backend.models.appeal import Appeal
from backend.models.enums import SubmissionStatus, AppealStatus, CourseStatus

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/api/dashboard")

@dashboard_bp.route("", methods=["GET"])
@dashboard_bp.route("/stats", methods=["GET"])
def get_dashboard_metrics():
    """
    Retrieve real-time platform metrics:
      1. Total learners
      2. Total courses
      3. Total assignments
      4. Total submissions
      5. Pending grading (status == SUBMITTED)
      6. Late submissions (is_late == True)
      7. Average grades
      8. Pending appeals (status in [SUBMITTED, UNDER_REVIEW])
    """
    total_learners = db.session.query(func.count(Learner.learner_id)).scalar() or 0
    total_courses = db.session.query(func.count(Course.course_id)).scalar() or 0
    total_assignments = db.session.query(func.count(Assignment.assignment_id)).scalar() or 0
    total_submissions = db.session.query(func.count(Submission.submission_id)).scalar() or 0
    
    pending_grading = db.session.query(func.count(Submission.submission_id)).filter(
        Submission.status == SubmissionStatus.SUBMITTED
    ).scalar() or 0
    
    late_submissions = db.session.query(func.count(Submission.submission_id)).filter(
        Submission.is_late == True
    ).scalar() or 0
    
    avg_grade_raw = db.session.query(func.avg(Grade.final_score)).scalar()
    average_grade = round(float(avg_grade_raw), 2) if avg_grade_raw is not None else 0.0
    
    pending_appeals = db.session.query(func.count(Appeal.appeal_id)).filter(
        Appeal.status.in_([AppealStatus.SUBMITTED, AppealStatus.UNDER_REVIEW])
    ).scalar() or 0
    
    active_courses = db.session.query(func.count(Course.course_id)).filter(
        Course.status == CourseStatus.ACTIVE
    ).scalar() or 0
    
    graded_submissions = db.session.query(func.count(Submission.submission_id)).filter(
        Submission.status == SubmissionStatus.GRADED
    ).scalar() or 0

    return jsonify({
        "metrics": {
            "total_learners": total_learners,
            "total_courses": total_courses,
            "active_courses": active_courses,
            "total_assignments": total_assignments,
            "total_submissions": total_submissions,
            "pending_grading": pending_grading,
            "graded_submissions": graded_submissions,
            "late_submissions": late_submissions,
            "average_grade": average_grade,
            "pending_appeals": pending_appeals,
        }
    }), 200

