import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import StatCard from '../components/StatCard';

export default function AdminDashboard({ setActiveTab }) {
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState(null);
  const [error, setError] = useState(null);

  const fetchStats = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getDashboardStats();
      setStats(data);
    } catch (err) {
      console.error('Failed to fetch admin dashboard stats', err);
      setError(err.message || 'Failed to connect to /api/dashboard/stats');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  return (
    <div className="container-fluid px-0">
      {/* Header Banner */}
      <div className="card-eduflow p-4 mb-4 bg-white border">
        <div className="d-flex flex-column flex-md-row justify-content-between align-items-md-center gap-3">
          <div>
            <span className="badge bg-dark text-white fw-semibold mb-2">
              <i className="bi bi-shield-lock-fill me-1"></i> System Administration
            </span>
            <h2 className="fw-bold mb-1">EduFlow Operations Dashboard</h2>
            <p className="text-muted mb-0">
              Platform-wide telemetry, academic compliance metrics, and database lifecycle management.
            </p>
          </div>
          <div className="d-flex gap-2">
            <button
              className="btn btn-outline-secondary d-flex align-items-center"
              onClick={fetchStats}
              disabled={loading}
            >
              <i className={`bi bi-arrow-clockwise me-2 ${loading ? 'spin' : ''}`}></i>
              Refresh Metrics
            </button>
            <button
              className="btn btn-primary-gradient"
              onClick={() => setActiveTab('courses')}
            >
              <i className="bi bi-plus-lg me-1"></i> Add Course
            </button>
          </div>
        </div>
      </div>

      {error && (
        <div className="alert alert-danger d-flex align-items-center mb-4">
          <i className="bi bi-exclamation-triangle-fill me-2 fs-5"></i>
          <div>{error}</div>
        </div>
      )}

      {/* 8 Required Dashboard Metrics Grid */}
      <div className="row g-3 mb-4">
        <div className="col-sm-6 col-lg-3">
          <StatCard
            title="Total Learners"
            value={stats ? stats.total_learners : (loading ? '...' : 0)}
            icon="people-fill"
            color="primary"
            subtext="Registered student accounts"
          />
        </div>
        <div className="col-sm-6 col-lg-3">
          <StatCard
            title="Total Courses"
            value={stats ? stats.total_courses : (loading ? '...' : 0)}
            icon="journal-bookmark-fill"
            color="indigo"
            subtext="Active & scheduled terms"
          />
        </div>
        <div className="col-sm-6 col-lg-3">
          <StatCard
            title="Total Assignments"
            value={stats ? stats.total_assignments : (loading ? '...' : 0)}
            icon="file-earmark-text-fill"
            color="cyan"
            subtext="Published & draft tasks"
          />
        </div>
        <div className="col-sm-6 col-lg-3">
          <StatCard
            title="Total Submissions"
            value={stats ? stats.total_submissions : (loading ? '...' : 0)}
            icon="send-check-fill"
            color="success"
            subtext="All learner attempts"
          />
        </div>
        <div className="col-sm-6 col-lg-3">
          <StatCard
            title="Pending Grading"
            value={stats ? stats.pending_grading : (loading ? '...' : 0)}
            icon="clock-history"
            color="warning"
            subtext="Awaiting evaluator review"
          />
        </div>
        <div className="col-sm-6 col-lg-3">
          <StatCard
            title="Late Submissions"
            value={stats ? stats.late_submissions : (loading ? '...' : 0)}
            icon="alarm-fill"
            color="danger"
            subtext="Past grace period cutoff"
          />
        </div>
        <div className="col-sm-6 col-lg-3">
          <StatCard
            title="Average Grade"
            value={stats && stats.average_grades !== null ? `${Number(stats.average_grades).toFixed(1)}%` : 'N/A'}
            icon="graph-up-arrow"
            color="success"
            subtext="Mean across evaluated submissions"
          />
        </div>
        <div className="col-sm-6 col-lg-3">
          <StatCard
            title="Pending Appeals"
            value={stats ? stats.pending_appeals : (loading ? '...' : 0)}
            icon="envelope-exclamation-fill"
            color="indigo"
            subtext="Awaiting formal adjudication"
          />
        </div>
      </div>

      {/* System Governance & Architectural Guardrails */}
      <div className="row g-4">
        <div className="col-lg-6">
          <div className="card card-eduflow h-100">
            <div className="card-header card-header-clean">
              <h5 className="mb-0 fw-bold">Platform Governance &amp; Invariants</h5>
            </div>
            <div className="card-body">
              <ul className="list-group list-group-flush">
                <li className="list-group-item d-flex justify-content-between align-items-center px-0">
                  <div>
                    <div className="fw-semibold text-dark">Universal UTC Timezone Normalization</div>
                    <small className="text-muted">Storage normalized to UTC; localized on client</small>
                  </div>
                  <span className="badge bg-success-subtle text-success">Compliant</span>
                </li>
                <li className="list-group-item d-flex justify-content-between align-items-center px-0">
                  <div>
                    <div className="fw-semibold text-dark">Zero Silent Mutation (Audit Logging)</div>
                    <small className="text-muted">All grade edits recorded with reason &amp; actor</small>
                  </div>
                  <span className="badge bg-success-subtle text-success">Active</span>
                </li>
                <li className="list-group-item d-flex justify-content-between align-items-center px-0">
                  <div>
                    <div className="fw-semibold text-dark">Pydantic v2 Contract Validation</div>
                    <small className="text-muted">Request DTO bounds &amp; email syntax verification</small>
                  </div>
                  <span className="badge bg-success-subtle text-success">Enforced</span>
                </li>
                <li className="list-group-item d-flex justify-content-between align-items-center px-0">
                  <div>
                    <div className="fw-semibold text-dark">Single Late Penalty Invariant (BR-05)</div>
                    <small className="text-muted">Late deduction applied strictly once upon scoring</small>
                  </div>
                  <span className="badge bg-success-subtle text-success">Idempotent</span>
                </li>
              </ul>
            </div>
          </div>
        </div>

        <div className="col-lg-6">
          <div className="card card-eduflow h-100">
            <div className="card-header card-header-clean">
              <h5 className="mb-0 fw-bold">Quick Administrative Workflows</h5>
            </div>
            <div className="card-body">
              <div className="row g-3">
                <div className="col-sm-6">
                  <div className="p-3 border rounded-3 bg-light h-100">
                    <div className="fw-bold text-dark mb-1">
                      <i className="bi bi-person-plus-fill text-primary me-2"></i>Learner Ingestion
                    </div>
                    <p className="text-muted small mb-3">Register new learners and assign them to active courses.</p>
                    <button
                      className="btn btn-sm btn-outline-primary w-100"
                      onClick={() => setActiveTab('learners')}
                    >
                      Manage Learners
                    </button>
                  </div>
                </div>
                <div className="col-sm-6">
                  <div className="p-3 border rounded-3 bg-light h-100">
                    <div className="fw-bold text-dark mb-1">
                      <i className="bi bi-journal-plus text-indigo me-2"></i>Course Deployment
                    </div>
                    <p className="text-muted small mb-3">Initialize term schedules, timezone contexts, and syllabi.</p>
                    <button
                      className="btn btn-sm btn-outline-secondary w-100"
                      onClick={() => setActiveTab('courses')}
                    >
                      Course Catalog
                    </button>
                  </div>
                </div>
                <div className="col-sm-6">
                  <div className="p-3 border rounded-3 bg-light h-100">
                    <div className="fw-bold text-dark mb-1">
                      <i className="bi bi-shield-shaded text-warning me-2"></i>Appeal Adjudication
                    </div>
                    <p className="text-muted small mb-3">Review grade dispute claims within 7-day policy window.</p>
                    <button
                      className="btn btn-sm btn-outline-warning w-100"
                      onClick={() => setActiveTab('appeals')}
                    >
                      Open Appeals
                    </button>
                  </div>
                </div>
                <div className="col-sm-6">
                  <div className="p-3 border rounded-3 bg-light h-100">
                    <div className="fw-bold text-dark mb-1">
                      <i className="bi bi-clipboard2-check text-success me-2"></i>Evaluation Workspace
                    </div>
                    <p className="text-muted small mb-3">Monitor grading queues and rubric alignment.</p>
                    <button
                      className="btn btn-sm btn-outline-success w-100"
                      onClick={() => setActiveTab('grading')}
                    >
                      Grading Workspace
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

