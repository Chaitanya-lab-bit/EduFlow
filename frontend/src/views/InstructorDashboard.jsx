import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import StatCard from '../components/StatCard';
import StatusBadge from '../components/StatusBadge';

export default function InstructorDashboard({ setActiveTab, setSelectedSubmissionId }) {
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState(null);
  const [pendingSubmissions, setPendingSubmissions] = useState([]);
  const [recentAssignments, setRecentAssignments] = useState([]);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const [dashRes, subRes, asnRes] = await Promise.allSettled([
          api.getDashboardStats(),
          api.getSubmissionHistory({ status: 'submitted', per_page: 8 }),
          api.getAssignments({ per_page: 8 }),
        ]);

        if (dashRes.status === 'fulfilled' && dashRes.value) {
          setStats(dashRes.value);
        }
        if (subRes.status === 'fulfilled' && subRes.value) {
          setPendingSubmissions(subRes.value.items || []);
        }
        if (asnRes.status === 'fulfilled' && asnRes.value) {
          setRecentAssignments(asnRes.value.items || []);
        }
      } catch (err) {
        console.error('Failed to load instructor dashboard', err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  return (
    <div className="container-fluid px-0">
      {/* Header Banner */}
      <div className="card-eduflow p-4 mb-4 bg-white border">
        <div className="row align-items-center">
          <div className="col-md-8">
            <span className="badge bg-indigo-subtle text-indigo fw-semibold mb-2" style={{ backgroundColor: '#e0e7ff', color: '#4338ca' }}>
              Instructor Control Center
            </span>
            <h2 className="fw-bold mb-1">Course &amp; Evaluation Workspace</h2>
            <p className="text-muted mb-0">
              Manage course syllabi, calibrate weighted rubric criteria, evaluate student artifacts, and resolve appeals.
            </p>
          </div>
          <div className="col-md-4 text-md-end mt-3 mt-md-0 d-flex flex-wrap justify-content-md-end gap-2">
            <button
              className="btn btn-primary-gradient px-3 py-2 rounded-3"
              onClick={() => setActiveTab('assignments')}
            >
              <i className="bi bi-plus-circle me-1"></i> New Assignment
            </button>
            <button
              className="btn btn-outline-primary px-3 py-2 rounded-3"
              onClick={() => setActiveTab('grading')}
            >
              <i className="bi bi-pencil-square me-1"></i> Grade Queue
            </button>
          </div>
        </div>
      </div>

      {/* Metric Cards */}
      <div className="row g-3 mb-4">
        <div className="col-sm-6 col-xl-3">
          <StatCard
            title="Managed Courses"
            value={stats ? stats.total_courses : '—'}
            icon="journal-bookmark-fill"
            color="primary"
            subtext="Active academic terms"
          />
        </div>
        <div className="col-sm-6 col-xl-3">
          <StatCard
            title="Pending Evaluations"
            value={stats ? stats.pending_grading : pendingSubmissions.length}
            icon="hourglass-split"
            color="warning"
            subtext="Submissions awaiting grading"
          />
        </div>
        <div className="col-sm-6 col-xl-3">
          <StatCard
            title="Total Submissions"
            value={stats ? stats.total_submissions : '—'}
            icon="folder-check"
            color="indigo"
            subtext={`${stats ? stats.late_submissions : 0} late submissions`}
          />
        </div>
        <div className="col-sm-6 col-xl-3">
          <StatCard
            title="Pending Appeals"
            value={stats ? stats.pending_appeals : '—'}
            icon="exclamation-octagon-fill"
            color="danger"
            subtext="Awaiting faculty adjudication"
          />
        </div>
      </div>

      <div className="row g-4">
        {/* Pending Grading Queue */}
        <div className="col-lg-7">
          <div className="card card-eduflow h-100">
            <div className="card-header card-header-clean d-flex justify-content-between align-items-center">
              <div>
                <h5 className="mb-0 fw-bold">Submissions Needing Grading</h5>
                <span className="text-muted small">Evaluate student work with rubric criteria &amp; feedback</span>
              </div>
              <button
                className="btn btn-sm btn-outline-primary"
                onClick={() => setActiveTab('grading')}
              >
                Open Workspace
              </button>
            </div>
            <div className="card-body p-0">
              {loading ? (
                <div className="p-4 text-center text-muted">
                  <div className="spinner-border spinner-border-sm me-2" role="status"></div> Loading queue...
                </div>
              ) : pendingSubmissions.length === 0 ? (
                <div className="p-4 text-center text-muted">
                  <i className="bi bi-check2-circle fs-2 d-block mb-2 text-success"></i>
                  All caught up! No submissions currently pending grading.
                </div>
              ) : (
                <div className="table-responsive">
                  <table className="table table-eduflow align-middle">
                    <thead>
                      <tr>
                        <th>Submission ID</th>
                        <th>Learner</th>
                        <th>Submitted At (UTC)</th>
                        <th>Status</th>
                        <th className="text-end">Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {pendingSubmissions.map(s => (
                        <tr key={s.id}>
                          <td>
                            <span className="fw-semibold font-mono text-dark small">{s.id}</span>
                            <div className="text-muted small font-mono">{s.assignment_id}</div>
                          </td>
                          <td>
                            <span className="badge bg-light text-dark border font-mono">{s.learner_id}</span>
                          </td>
                          <td>
                            <div className="small text-muted">
                              {s.submitted_at ? new Date(s.submitted_at).toLocaleString() : '—'}
                            </div>
                            <span className="badge bg-secondary-subtle text-secondary small">Ver. {s.version}</span>
                          </td>
                          <td>
                            <StatusBadge status={s.status} />
                          </td>
                          <td className="text-end">
                            <button
                              className="btn btn-sm btn-primary-gradient px-3"
                              onClick={() => {
                                if (setSelectedSubmissionId) setSelectedSubmissionId(s.id);
                                setActiveTab('grading');
                              }}
                            >
                              Grade
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Assignment Lifecycle */}
        <div className="col-lg-5">
          <div className="card card-eduflow h-100">
            <div className="card-header card-header-clean d-flex justify-content-between align-items-center">
              <div>
                <h5 className="mb-0 fw-bold">Assignment Overview</h5>
                <span className="text-muted small">Publication and rubric readiness</span>
              </div>
              <button
                className="btn btn-sm btn-outline-secondary"
                onClick={() => setActiveTab('assignments')}
              >
                Manage
              </button>
            </div>
            <div className="card-body p-0">
              {loading ? (
                <div className="p-4 text-center text-muted">
                  <div className="spinner-border spinner-border-sm me-2" role="status"></div> Loading assignments...
                </div>
              ) : recentAssignments.length === 0 ? (
                <div className="p-4 text-center text-muted">
                  <i className="bi bi-file-earmark-plus fs-2 d-block mb-2 text-secondary"></i>
                  No assignments created yet.
                </div>
              ) : (
                <div className="list-group list-group-flush">
                  {recentAssignments.slice(0, 6).map(a => (
                    <div key={a.id} className="list-group-item p-3">
                      <div className="d-flex justify-content-between align-items-start mb-1">
                        <div>
                          <span className="fw-semibold text-dark d-block">{a.title}</span>
                          <span className="font-mono text-muted small">{a.course_id} &bull; {a.max_score} pts</span>
                        </div>
                        <StatusBadge status={a.status} />
                      </div>
                      <div className="d-flex justify-content-between align-items-center mt-2 small">
                        <span className="text-muted">
                          Due: {a.due_date ? new Date(a.due_date).toLocaleDateString() : '—'}
                        </span>
                        {a.status === 'draft' ? (
                          <button
                            className="btn btn-sm btn-outline-primary py-0 px-2"
                            onClick={() => setActiveTab('assignments')}
                          >
                            Configure Rubric
                          </button>
                        ) : (
                          <span className="text-success small fw-semibold">
                            <i className="bi bi-check-all"></i> Published
                          </span>
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

