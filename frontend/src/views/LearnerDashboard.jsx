import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { api } from '../api/client';
import StatCard from '../components/StatCard';
import StatusBadge from '../components/StatusBadge';
import AlertBanner from '../components/AlertBanner';

export default function LearnerDashboard({ setActiveTab, setSelectedAssignmentId }) {
  const { currentUser } = useAuth();
  const [loading, setLoading] = useState(true);
  const [courses, setCourses] = useState([]);
  const [assignments, setAssignments] = useState([]);
  const [submissions, setSubmissions] = useState([]);
  const [enrollments, setEnrollments] = useState([]);
  const [alert, setAlert] = useState(null);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        setAlert(null);

        const learnerId = currentUser ? currentUser.id : null;

        const [cRes, aRes, sRes, eRes] = await Promise.allSettled([
          api.getCourses({ per_page: 10 }),
          api.getAssignments({ status: 'published', per_page: 20 }),
          learnerId ? api.getSubmissionHistory({ learner_id: learnerId, per_page: 10 }) : api.getSubmissionHistory({ per_page: 10 }),
          learnerId ? api.getEnrollments({ learner_id: learnerId }) : Promise.resolve({ items: [] })
        ]);

        if (cRes.status === 'fulfilled' && cRes.value) {
          setCourses(cRes.value.items || []);
        } else if (cRes.status === 'rejected') {
          console.warn('Courses fetch notice:', cRes.reason);
        }

        if (aRes.status === 'fulfilled' && aRes.value) {
          setAssignments(aRes.value.items || []);
        }

        if (sRes.status === 'fulfilled' && sRes.value) {
          setSubmissions(sRes.value.items || []);
        }

        if (eRes.status === 'fulfilled' && eRes.value) {
          setEnrollments(eRes.value.items || []);
        }
      } catch (err) {
        setAlert({
          type: 'danger',
          message: err.message || 'Failed to load learner dashboard telemetry',
          error_code: err.error_code,
          details: err.details,
          status: err.status
        });
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [currentUser]);

  const totalSubmitted = submissions.length;
  const gradedList = submissions.filter(s => s.status === 'graded');
  const totalGraded = gradedList.length;

  // Set of enrolled course IDs
  const enrolledCourseIds = new Set(enrollments.map(e => e.course_id));

  return (
    <div className="container-fluid px-0">
      <AlertBanner alert={alert} onClose={() => setAlert(null)} />

      {/* Welcome Banner */}
      <div className="card-eduflow p-4 mb-4 bg-white border">
        <div className="row align-items-center">
          <div className="col-md-8">
            <div className="d-flex align-items-center gap-2 mb-2">
              <span className="badge bg-primary-subtle text-primary fw-semibold">Student Portal</span>
              <span className="badge bg-light text-dark border font-mono small">
                ID: {currentUser ? currentUser.id : 'LNR-2026-000001'}
              </span>
              <span className="badge bg-light text-secondary border small">
                Timezone: {currentUser ? currentUser.timezone : 'UTC'}
              </span>
            </div>
            <h2 className="fw-bold mb-1">
              Welcome back, {currentUser ? currentUser.name : 'Learner'}!
            </h2>
            <p className="text-muted mb-0">
              Track course deliverables, review deadline grace periods, inspect rubric criteria, and verify evaluation feedback.
            </p>
          </div>
          <div className="col-md-4 text-md-end mt-3 mt-md-0">
            <button
              className="btn btn-primary-gradient px-4 py-2 rounded-3"
              onClick={() => setActiveTab('submissions')}
            >
              <i className="bi bi-cloud-arrow-up-fill me-2"></i> Submit New Work
            </button>
          </div>
        </div>
      </div>

      {/* Metric Cards */}
      <div className="row g-3 mb-4">
        <div className="col-sm-6 col-xl-3">
          <StatCard
            title="My Enrollments"
            value={enrollments.length > 0 ? enrollments.length : courses.length}
            icon="journal-bookmark-fill"
            color="primary"
            subtext="Institutional courses"
          />
        </div>
        <div className="col-sm-6 col-xl-3">
          <StatCard
            title="Published Tasks"
            value={assignments.length}
            icon="file-earmark-text"
            color="indigo"
            subtext="Available assignments"
          />
        </div>
        <div className="col-sm-6 col-xl-3">
          <StatCard
            title="My Submissions"
            value={totalSubmitted}
            icon="send-check"
            color="cyan"
            subtext={`${totalGraded} graded so far`}
          />
        </div>
        <div className="col-sm-6 col-xl-3">
          <StatCard
            title="Completed Evaluations"
            value={totalGraded}
            icon="award-fill"
            color="success"
            subtext="With rubric scores"
          />
        </div>
      </div>

      {/* Main Content */}
      <div className="row g-4">
        {/* Active & Upcoming Assignments */}
        <div className="col-lg-7">
          <div className="card card-eduflow h-100">
            <div className="card-header card-header-clean d-flex justify-content-between align-items-center">
              <div>
                <h5 className="mb-0 fw-bold">Active &amp; Upcoming Assignments</h5>
                <span className="text-muted small">Deadlines, grace periods, and maximum scores</span>
              </div>
              <button
                className="btn btn-sm btn-outline-secondary"
                onClick={() => setActiveTab('assignments')}
              >
                View Catalog
              </button>
            </div>
            <div className="card-body p-0">
              {loading ? (
                <div className="p-4 text-center text-muted">
                  <div className="spinner-border spinner-border-sm me-2" role="status"></div> Loading assignments...
                </div>
              ) : assignments.length === 0 ? (
                <div className="p-4 text-center text-muted">
                  <i className="bi bi-inbox fs-2 d-block mb-2 text-secondary"></i>
                  No published assignments currently available.
                </div>
              ) : (
                <div className="table-responsive">
                  <table className="table table-eduflow align-middle">
                    <thead>
                      <tr>
                        <th>Assignment</th>
                        <th>Course</th>
                        <th>Due Date (UTC)</th>
                        <th>Points</th>
                        <th className="text-end">Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {assignments.map(a => {
                        const isEnrolled = enrolledCourseIds.size === 0 || enrolledCourseIds.has(a.course_id);
                        return (
                          <tr key={a.id}>
                            <td>
                              <div className="fw-semibold text-dark">{a.title}</div>
                              <span className="text-muted font-mono small">{a.id}</span>
                            </td>
                            <td>
                              <span className="badge bg-light text-dark border font-mono">{a.course_id}</span>
                              {isEnrolled && (
                                <span className="badge bg-success-subtle text-success ms-1 small">Enrolled</span>
                              )}
                            </td>
                            <td>
                              <div className="small text-dark">
                                <i className="bi bi-calendar-event me-1 text-primary"></i>
                                {a.due_date ? new Date(a.due_date).toLocaleString() : '—'}
                              </div>
                              {a.grace_period_minutes > 0 && (
                                <span className="badge bg-warning-subtle text-warning-emphasis small mt-1">
                                  +{a.grace_period_minutes}m grace
                                </span>
                              )}
                            </td>
                            <td>
                              <span className="fw-bold text-success">{a.max_score} pts</span>
                            </td>
                            <td className="text-end">
                              <button
                                className="btn btn-sm btn-primary"
                                onClick={() => {
                                  if (setSelectedAssignmentId) setSelectedAssignmentId(a.id);
                                  setActiveTab('submissions');
                                }}
                              >
                                Submit
                              </button>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Recent Submissions */}
        <div className="col-lg-5">
          <div className="card card-eduflow h-100">
            <div className="card-header card-header-clean d-flex justify-content-between align-items-center">
              <div>
                <h5 className="mb-0 fw-bold">My Recent Submissions</h5>
                <span className="text-muted small">Attempts and evaluation progress</span>
              </div>
              <button
                className="btn btn-sm btn-outline-secondary"
                onClick={() => setActiveTab('submissions')}
              >
                All History
              </button>
            </div>
            <div className="card-body p-0">
              {loading ? (
                <div className="p-4 text-center text-muted">
                  <div className="spinner-border spinner-border-sm me-2" role="status"></div> Loading history...
                </div>
              ) : submissions.length === 0 ? (
                <div className="p-4 text-center text-muted">
                  <i className="bi bi-clock-history fs-2 d-block mb-2 text-secondary"></i>
                  No submissions recorded for {currentUser ? currentUser.name : 'this learner'}.
                </div>
              ) : (
                <div className="list-group list-group-flush">
                  {submissions.slice(0, 5).map(s => (
                    <div key={s.id} className="list-group-item p-3">
                      <div className="d-flex justify-content-between align-items-start mb-1">
                        <div>
                          <span className="fw-semibold font-mono small text-dark d-block">{s.id}</span>
                          <span className="text-muted small font-mono">{s.assignment_id} &bull; Attempt #{s.version}</span>
                        </div>
                        <StatusBadge status={s.status} />
                      </div>
                      <div className="d-flex justify-content-between align-items-center mt-2 small">
                        <span className="text-muted">
                          <i className="bi bi-clock me-1"></i>
                          {s.submitted_at ? new Date(s.submitted_at).toLocaleDateString() : '—'}
                        </span>
                        {s.status === 'graded' ? (
                          <span className="text-success fw-bold">
                            <i className="bi bi-check-circle-fill me-1"></i> Evaluation Ready
                          </span>
                        ) : (
                          <span className="text-muted">Under Review</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
