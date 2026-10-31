import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { api } from '../api/client';
import StatusBadge from '../components/StatusBadge';
import AlertBanner from '../components/AlertBanner';

export default function SubmissionsView({ selectedAssignmentId }) {
  const { role, currentUser } = useAuth();
  const [submissions, setSubmissions] = useState([]);
  const [assignments, setAssignments] = useState([]);
  const [learners, setLearners] = useState([]);
  const [loading, setLoading] = useState(true);
  const [alert, setAlert] = useState(null);
  const [activeTab, setActiveTab] = useState('submit'); // 'submit' | 'history'
  const [enrollmentStatus, setEnrollmentStatus] = useState(null); // 'active' | 'unenrolled' | 'checking' | null

  // Submit Form
  const [submitForm, setSubmitForm] = useState({
    assignment_id: selectedAssignmentId || '',
    learner_id: currentUser ? currentUser.id : '',
    artifacts: [
      {
        filename: 'report.pdf',
        file_type: 'pdf',
        byte_size: 1048576,
        checksum_sha256: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
        storage_path: 's3://eduflow-artifacts/report.pdf'
      }
    ]
  });

  // Late Status Modal
  const [lateStatusData, setLateStatusData] = useState(null);

  const loadData = async () => {
    try {
      setLoading(true);
      const [sRes, aRes, lRes] = await Promise.all([
        api.getSubmissionHistory({ per_page: 50 }),
        api.getAssignments({ status: 'published', per_page: 50 }),
        api.getLearners({ per_page: 50 })
      ]);
      setSubmissions(sRes.items || []);
      setAssignments(aRes.items || []);
      setLearners(lRes.items || []);

      const defaultAsn = selectedAssignmentId || (aRes.items && aRes.items.length > 0 ? aRes.items[0].id : '');
      const defaultLnr = currentUser && currentUser.id ? currentUser.id : (lRes.items && lRes.items.length > 0 ? lRes.items[0].id : '');

      setSubmitForm(prev => ({
        ...prev,
        assignment_id: prev.assignment_id || defaultAsn,
        learner_id: prev.learner_id || defaultLnr
      }));
    } catch (err) {
      setAlert({
        type: 'danger',
        message: err.message || 'Failed to load submissions context',
        error_code: err.error_code,
        details: err.details,
        status: err.status
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [currentUser]);

  useEffect(() => {
    if (selectedAssignmentId) {
      setSubmitForm(prev => ({ ...prev, assignment_id: selectedAssignmentId }));
    }
  }, [selectedAssignmentId]);

  // Check enrollment status when assignment or learner changes
  useEffect(() => {
    const currentAsn = assignments.find(a => a.id === submitForm.assignment_id);
    if (!currentAsn || !submitForm.learner_id) {
      setEnrollmentStatus(null);
      return;
    }

    setEnrollmentStatus('checking');
    api.checkEnrollmentStatus(submitForm.learner_id, currentAsn.course_id)
      .then(res => {
        setEnrollmentStatus(res && res.enrolled ? res.status || 'active' : 'unenrolled');
      })
      .catch(() => {
        setEnrollmentStatus('unenrolled');
      });
  }, [submitForm.assignment_id, submitForm.learner_id, assignments]);

  const generateDummyChecksum = () => {
    const chars = '0123456789abcdef';
    let hash = '';
    for (let i = 0; i < 64; i++) {
      hash += chars[Math.floor(Math.random() * chars.length)];
    }
    return hash;
  };

  const handleArtifactChange = (index, field, value) => {
    const updated = [...submitForm.artifacts];
    updated[index][field] = field === 'byte_size' ? Number(value) : value;
    setSubmitForm({ ...submitForm, artifacts: updated });
  };

  const addArtifact = () => {
    setSubmitForm({
      ...submitForm,
      artifacts: [
        ...submitForm.artifacts,
        {
          filename: 'code_deliverable.zip',
          file_type: 'zip',
          byte_size: 2097152,
          checksum_sha256: generateDummyChecksum(),
          storage_path: 's3://eduflow-artifacts/code_deliverable.zip'
        }
      ]
    });
  };

  const removeArtifact = (index) => {
    if (submitForm.artifacts.length <= 1) return;
    setSubmitForm({
      ...submitForm,
      artifacts: submitForm.artifacts.filter((_, i) => i !== index)
    });
  };

  const handleSubmitWork = async (e) => {
    e.preventDefault();
    try {
      setAlert(null);
      const payload = {
        assignment_id: submitForm.assignment_id,
        learner_id: submitForm.learner_id,
        submitted_at: new Date().toISOString(),
        artifacts: submitForm.artifacts
      };
      const res = await api.submitAssignment(payload);
      setAlert({
        type: 'success',
        message: `Submission successful! Recorded attempt ${res.id} (Version: ${res.version}, Status: ${res.status}).`
      });
      loadData();
      setActiveTab('history');
    } catch (err) {
      setAlert({
        type: 'danger',
        message: err.message || 'Submission failed.',
        error_code: err.error_code,
        details: err.details,
        status: err.status
      });
    }
  };

  const handleCheckLateStatus = async (submissionId) => {
    try {
      const statusRes = await api.checkLateStatus(submissionId);
      setLateStatusData({ id: submissionId, ...statusRes });
    } catch (err) {
      setAlert({
        type: 'danger',
        message: err.message || 'Failed to check late status',
        error_code: err.error_code,
        details: err.details,
        status: err.status
      });
    }
  };

  const currentAssignment = assignments.find(a => a.id === submitForm.assignment_id);

  // Filter submissions if learner
  const displayedSubmissions = role === 'learner' && currentUser
    ? submissions.filter(s => s.learner_id === currentUser.id)
    : submissions;

  return (
    <div className="container-fluid px-0">
      <AlertBanner alert={alert} onClose={() => setAlert(null)} />

      <div className="d-flex flex-column flex-md-row justify-content-between align-items-md-center mb-4 gap-3">
        <div>
          <h3 className="fw-bold mb-1">Student Submissions &amp; Artifact Ingestion</h3>
          <p className="text-muted mb-0">Upload coursework deliverables with verified checksums, audit lateness, and inspect versions.</p>
        </div>
        <div className="btn-group">
          <button
            className={`btn ${activeTab === 'submit' ? 'btn-primary' : 'btn-outline-primary'}`}
            onClick={() => setActiveTab('submit')}
          >
            <i className="bi bi-cloud-arrow-up me-1"></i> Submit Work
          </button>
          <button
            className={`btn ${activeTab === 'history' ? 'btn-primary' : 'btn-outline-primary'}`}
            onClick={() => setActiveTab('history')}
          >
            <i className="bi bi-clock-history me-1"></i> Submission History ({displayedSubmissions.length})
          </button>
        </div>
      </div>

      {activeTab === 'submit' ? (
        <div className="row g-4 justify-content-center">
          <div className="col-lg-8">
            <div className="card card-eduflow">
              <div className="card-header card-header-clean bg-light d-flex justify-content-between align-items-center">
                <div>
                  <h5 className="mb-0 fw-bold">Assignment Ingestion Form</h5>
                  <span className="text-muted small">Validated with enrollment &amp; deadline policies</span>
                </div>
                {enrollmentStatus && (
                  <span
                    className={`badge ${
                      enrollmentStatus === 'active'
                        ? 'bg-success-subtle text-success'
                        : enrollmentStatus === 'checking'
                        ? 'bg-secondary-subtle text-secondary'
                        : 'bg-danger-subtle text-danger'
                    }`}
                  >
                    <i
                      className={`bi bi-${
                        enrollmentStatus === 'active'
                          ? 'check-circle'
                          : enrollmentStatus === 'checking'
                          ? 'hourglass-split'
                          : 'exclamation-circle'
                      } me-1`}
                    ></i>
                    {enrollmentStatus === 'active'
                      ? 'Enrollment Verified'
                      : enrollmentStatus === 'checking'
                      ? 'Checking Enrollment...'
                      : 'Unenrolled in Course'}
                  </span>
                )}
              </div>
              <div className="card-body p-4">
                <form onSubmit={handleSubmitWork}>
                  <div className="row g-3 mb-3">
                    <div className="col-md-6">
                      <label className="form-label small fw-semibold">Target Assignment</label>
                      <select
                        className="form-select font-mono small"
                        required
                        value={submitForm.assignment_id}
                        onChange={e => setSubmitForm({ ...submitForm, assignment_id: e.target.value })}
                      >
                        <option value="">Select assignment...</option>
                        {assignments.map(a => (
                          <option key={a.id} value={a.id}>
                            {a.title} ({a.id}) - {a.course_id}
                          </option>
                        ))}
                      </select>
                    </div>

                    <div className="col-md-6">
                      <label className="form-label small fw-semibold">Learner</label>
                      {learners.length > 0 ? (
                        <select
                          className="form-select font-mono small"
                          required
                          value={submitForm.learner_id}
                          onChange={e => setSubmitForm({ ...submitForm, learner_id: e.target.value })}
                        >
                          <option value="">Select learner...</option>
                          {learners.map(l => (
                            <option key={l.id} value={l.id}>
                              {l.name} ({l.id})
                            </option>
                          ))}
                        </select>
                      ) : (
                        <input
                          type="text"
                          className="form-control font-mono small"
                          placeholder="e.g. LNR-2026-000001"
                          required
                          value={submitForm.learner_id}
                          onChange={e => setSubmitForm({ ...submitForm, learner_id: e.target.value })}
                        />
                      )}
                    </div>
                  </div>

                  {/* Assignment Deadline Context Card */}
                  {currentAssignment && (
                    <div className="p-3 mb-4 rounded-3 border bg-light">
                      <div className="row g-2 small">
                        <div className="col-sm-4">
                          <span className="text-muted d-block">Due Date (UTC):</span>
                          <span className="fw-semibold text-dark">
                            {currentAssignment.due_date ? new Date(currentAssignment.due_date).toLocaleString() : '—'}
                          </span>
                        </div>
                        <div className="col-sm-4">
                          <span className="text-muted d-block">Grace Period:</span>
                          <span className="fw-semibold text-primary">{currentAssignment.grace_period_minutes} minutes</span>
                        </div>
                        <div className="col-sm-4">
                          <span className="text-muted d-block">Late Penalty Rate:</span>
                          <span className="fw-semibold text-danger">{(currentAssignment.late_penalty_per_day * 100).toFixed(0)}% / day</span>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Artifacts Metadata Section */}
                  <div className="mb-4">
                    <div className="d-flex justify-content-between align-items-center mb-2">
                      <label className="form-label small fw-bold text-uppercase mb-0 text-muted" style={{ letterSpacing: '0.04em' }}>
                        Required Deliverable Artifacts (SHA-256 Verified)
                      </label>
                      <button
                        type="button"
                        className="btn btn-sm btn-outline-secondary"
                        onClick={addArtifact}
                      >
                        <i className="bi bi-plus-lg me-1"></i> Add Artifact
                      </button>
                    </div>

                    {submitForm.artifacts.map((art, idx) => (
                      <div key={idx} className="card p-3 mb-2 border bg-white">
                        <div className="row g-2 align-items-center">
                          <div className="col-md-4">
                            <label className="form-label small text-muted mb-1">File Name</label>
                            <input
                              type="text"
                              className="form-control form-control-sm"
                              required
                              value={art.filename}
                              onChange={e => handleArtifactChange(idx, 'filename', e.target.value)}
                            />
                          </div>
                          <div className="col-md-2">
                            <label className="form-label small text-muted mb-1">Type</label>
                            <select
                              className="form-select form-select-sm"
                              value={art.file_type}
                              onChange={e => handleArtifactChange(idx, 'file_type', e.target.value)}
                            >
                              <option value="pdf">pdf</option>
                              <option value="zip">zip</option>
                              <option value="py">py</option>
                              <option value="tar.gz">tar.gz</option>
                            </select>
                          </div>
                          <div className="col-md-2">
                            <label className="form-label small text-muted mb-1">Size (bytes)</label>
                            <input
                              type="number"
                              className="form-control form-control-sm"
                              value={art.byte_size}
                              onChange={e => handleArtifactChange(idx, 'byte_size', e.target.value)}
                            />
                          </div>
                          <div className="col-md-3">
                            <label className="form-label small text-muted mb-1">Storage Path</label>
                            <input
                              type="text"
                              className="form-control form-control-sm font-mono small"
                              value={art.storage_path}
                              onChange={e => handleArtifactChange(idx, 'storage_path', e.target.value)}
                            />
                          </div>
                          <div className="col-md-1 text-end mt-4">
                            <button
                              type="button"
                              className="btn btn-sm btn-outline-danger"
                              onClick={() => removeArtifact(idx)}
                              disabled={submitForm.artifacts.length <= 1}
                            >
                              <i className="bi bi-trash"></i>
                            </button>
                          </div>
                          <div className="col-12 mt-2">
                            <div className="input-group input-group-sm">
                              <span className="input-group-text font-mono small">SHA-256</span>
                              <input
                                type="text"
                                className="form-control font-mono small"
                                required
                                value={art.checksum_sha256}
                                onChange={e => handleArtifactChange(idx, 'checksum_sha256', e.target.value)}
                              />
                              <button
                                type="button"
                                className="btn btn-outline-secondary btn-sm"
                                onClick={() => handleArtifactChange(idx, 'checksum_sha256', generateDummyChecksum())}
                              >
                                Regenerate Hash
                              </button>
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>

                  <div className="d-flex justify-content-end gap-2">
                    <button type="submit" className="btn btn-primary-gradient px-4 py-2">
                      <i className="bi bi-send-check me-2"></i> Submit Assignment
                    </button>
                  </div>
                </form>
              </div>
            </div>
          </div>
        </div>
      ) : (
        /* Submission History Tab */
        <div className="card card-eduflow">
          <div className="card-body p-0">
            {loading ? (
              <div className="p-5 text-center text-muted">
                <div className="spinner-border text-primary me-2" role="status"></div> Loading history...
              </div>
            ) : displayedSubmissions.length === 0 ? (
              <div className="p-5 text-center text-muted">
                <i className="bi bi-inbox fs-1 d-block mb-2 text-secondary"></i>
                No submissions found.
              </div>
            ) : (
              <div className="table-responsive">
                <table className="table table-eduflow align-middle">
                  <thead>
                    <tr>
                      <th>Submission ID</th>
                      <th>Assignment</th>
                      <th>Learner</th>
                      <th>Attempt</th>
                      <th>Submitted At (UTC)</th>
                      <th>Status</th>
                      <th className="text-end">Lateness Audit</th>
                    </tr>
                  </thead>
                  <tbody>
                    {displayedSubmissions.map(s => (
                      <tr key={s.id}>
                        <td>
                          <span className="fw-bold font-mono text-dark small">{s.id}</span>
                        </td>
                        <td>
                          <span className="badge bg-light text-dark border font-mono small">{s.assignment_id}</span>
                        </td>
                        <td>
                          <span className="badge bg-light text-secondary border font-mono small">{s.learner_id}</span>
                        </td>
                        <td>
                          <span className="badge bg-secondary-subtle text-secondary small">Ver. {s.version}</span>
                        </td>
                        <td>
                          <span className="small text-dark">
                            {s.submitted_at ? new Date(s.submitted_at).toLocaleString() : '—'}
                          </span>
                        </td>
                        <td>
                          <StatusBadge status={s.status} />
                        </td>
                        <td className="text-end">
                          <button
                            className="btn btn-sm btn-outline-secondary"
                            onClick={() => handleCheckLateStatus(s.id)}
                          >
                            <i className="bi bi-alarm me-1"></i> Check Lateness
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
      )}

      {/* Lateness Modal */}
      {lateStatusData && (
        <div className="modal show d-block" tabIndex="-1" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
          <div className="modal-dialog modal-dialog-centered">
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title fw-bold">Submission Lateness Audit</h5>
                <button type="button" className="btn-close" onClick={() => setLateStatusData(null)}></button>
              </div>
              <div className="modal-body">
                <div className="font-mono small text-muted mb-3">{lateStatusData.id}</div>
                <ul className="list-group list-group-flush mb-3">
                  <li className="list-group-item d-flex justify-content-between px-0">
                    <span className="text-muted">Is Late Submission?</span>
                    <span className={`fw-bold ${lateStatusData.is_late ? 'text-danger' : 'text-success'}`}>
                      {lateStatusData.is_late ? 'YES (Late)' : 'NO (On-Time)'}
                    </span>
                  </li>
                  <li className="list-group-item d-flex justify-content-between px-0">
                    <span className="text-muted">Days Late Count:</span>
                    <span className="fw-semibold text-dark">{lateStatusData.days_late || 0} day(s)</span>
                  </li>
                  <li className="list-group-item d-flex justify-content-between px-0">
                    <span className="text-muted">Late Penalty Percentage:</span>
                    <span className="fw-bold text-danger">
                      {lateStatusData.late_penalty_percentage !== undefined ? `${(lateStatusData.late_penalty_percentage * 100).toFixed(1)}%` : '0%'}
                    </span>
                  </li>
                </ul>
                <div className="alert alert-info small mb-0">
                  <i className="bi bi-info-circle me-1"></i> Late penalty is calculated via BR-02 and deducted strictly once upon grading (BR-05).
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-primary" onClick={() => setLateStatusData(null)}>
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
