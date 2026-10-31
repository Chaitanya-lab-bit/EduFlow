import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { api } from '../api/client';
import StatusBadge from '../components/StatusBadge';
import AlertBanner from '../components/AlertBanner';

export default function AppealsResubmissionsView() {
  const { currentUser } = useAuth();
  const [activeTab, setActiveTab] = useState('appeals'); // 'appeals' | 'resubmissions'
  const [appeals, setAppeals] = useState([]);
  const [resubmissions, setResubmissions] = useState([]);
  const [submissions, setSubmissions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [alert, setAlert] = useState(null);

  // Modals
  const [showAppealModal, setShowAppealModal] = useState(false);
  const [showAdjudicateModal, setShowAdjudicateModal] = useState(false);
  const [selectedAppeal, setSelectedAppeal] = useState(null);

  const [showResubModal, setShowResubModal] = useState(false);
  const [showReviewResubModal, setShowReviewResubModal] = useState(false);
  const [selectedResub, setSelectedResub] = useState(null);

  // Appeal Form
  const [appealForm, setAppealForm] = useState({
    submission_id: '',
    learner_id: currentUser ? currentUser.id : '',
    reason_category: 'calculation_error',
    learner_statement: 'Detailed justification for criterion evaluation reconsideration.',
    requested_grade: 95.0,
    contested_criteria: ['Code Quality & Architecture']
  });

  // Adjudicate Form
  const [adjudicateForm, setAdjudicateForm] = useState({
    decision: 'approved',
    adjusted_score: 95.0,
    rationale: 'Review by academic committee confirmed rubric compliance and criterion satisfaction.',
    reviewer_id: currentUser ? currentUser.id : 'REV-2026-0001'
  });

  // Resubmission Form
  const [resubForm, setResubForm] = useState({
    original_submission_id: '',
    learner_id: currentUser ? currentUser.id : '',
    reason: 'Policy-compliant resubmission attempt addressing instructor feedback.'
  });

  // Review Resubmission Form
  const [reviewResubForm, setReviewResubForm] = useState({
    status: 'approved',
    change_summary: 'Approved for version N+1 attempt.',
    reviewed_by: currentUser ? currentUser.id : 'INST-2026-0001'
  });

  const loadData = async () => {
    try {
      setLoading(true);
      const [appRes, resubRes, subRes] = await Promise.all([
        api.getAppeals({ per_page: 50 }),
        api.getResubmissions({ per_page: 50 }),
        api.getSubmissionHistory({ per_page: 50 })
      ]);
      setAppeals(appRes.items || []);
      setResubmissions(resubRes.items || []);
      setSubmissions(subRes.items || []);

      if (currentUser && currentUser.id) {
        setAppealForm(prev => ({ ...prev, learner_id: currentUser.id }));
        setResubForm(prev => ({ ...prev, learner_id: currentUser.id }));
      }
    } catch (err) {
      setAlert({
        type: 'danger',
        message: err.message || 'Failed to load records',
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

  // Submit Appeal
  const handleCreateAppeal = async (e) => {
    e.preventDefault();
    try {
      setAlert(null);
      const res = await api.submitAppeal(appealForm);
      setAlert({
        type: 'success',
        message: `Appeal ${res.id} submitted! Status: ${res.status}. Submitted within 7-day post-publication window.`
      });
      setShowAppealModal(false);
      loadData();
    } catch (err) {
      setAlert({
        type: 'danger',
        message: err.message || 'Appeal submission failed. Verify that grade ID exists and submission was within the 7-day appeal window (EX-08).',
        error_code: err.error_code,
        details: err.details,
        status: err.status
      });
    }
  };

  // Adjudicate Appeal
  const handleAdjudicate = async (e) => {
    e.preventDefault();
    if (!selectedAppeal) return;
    try {
      setAlert(null);
      const payload = {
        status: adjudicateForm.decision,
        reviewed_by: adjudicateForm.reviewer_id || (currentUser ? currentUser.id : 'REV-2026-0001'),
        decision_notes: adjudicateForm.rationale,
      };
      if (adjudicateForm.decision === 'approved') {
        payload.final_grade = Number(adjudicateForm.adjusted_score);
      }
      const res = await api.decideAppeal(selectedAppeal.id, payload);
      setAlert({
        type: 'success',
        message: `Appeal ${res.id} adjudicated as ${res.status}! Grade was updated with mandatory AuditLog trail (EX-04).`
      });
      setShowAdjudicateModal(false);
      loadData();
    } catch (err) {
      setAlert({
        type: 'danger',
        message: err.message || 'Adjudication failed',
        error_code: err.error_code,
        details: err.details,
        status: err.status
      });
    }
  };

  // Request Resubmission
  const handleCreateResub = async (e) => {
    e.preventDefault();
    try {
      setAlert(null);
      const res = await api.requestResubmission(resubForm);
      setAlert({
        type: 'success',
        message: `Resubmission request ${res.id} submitted for evaluation!`
      });
      setShowResubModal(false);
      loadData();
    } catch (err) {
      setAlert({
        type: 'danger',
        message: err.message || 'Resubmission request failed. Verify that max attempt limits (EX-07) and deadline cutoff have not been exceeded.',
        error_code: err.error_code,
        details: err.details,
        status: err.status
      });
    }
  };

  // Review Resubmission
  const handleReviewResub = async (e) => {
    e.preventDefault();
    if (!selectedResub) return;
    try {
      setAlert(null);
      const res = await api.reviewResubmission(selectedResub.id, {
        ...reviewResubForm,
        reviewed_by: reviewResubForm.reviewed_by || (currentUser ? currentUser.id : 'INST-2026-0001')
      });
      setAlert({
        type: 'success',
        message: `Resubmission request ${res.id} reviewed (${res.status})! New submission version was created upon approval.`
      });
      setShowReviewResubModal(false);
      loadData();
    } catch (err) {
      setAlert({
        type: 'danger',
        message: err.message || 'Review failed',
        error_code: err.error_code,
        details: err.details,
        status: err.status
      });
    }
  };

  return (
    <div className="container-fluid px-0">
      <AlertBanner alert={alert} onClose={() => setAlert(null)} />

      <div className="d-flex flex-column flex-md-row justify-content-between align-items-md-center mb-4 gap-3">
        <div>
          <h3 className="fw-bold mb-1">Academic Appeals &amp; Resubmission Governance</h3>
          <p className="text-muted mb-0">Adjudicate formal student appeals, track grade adjustments with audit history, and authorize attempts.</p>
        </div>
        <div className="btn-group">
          <button
            className={`btn ${activeTab === 'appeals' ? 'btn-primary' : 'btn-outline-primary'}`}
            onClick={() => setActiveTab('appeals')}
          >
            <i className="bi bi-shield-check me-1"></i> Grade Appeals ({appeals.length})
          </button>
          <button
            className={`btn ${activeTab === 'resubmissions' ? 'btn-primary' : 'btn-outline-primary'}`}
            onClick={() => setActiveTab('resubmissions')}
          >
            <i className="bi bi-arrow-repeat me-1"></i> Resubmissions ({resubmissions.length})
          </button>
        </div>
      </div>

      {activeTab === 'appeals' ? (
        /* Appeals Tab */
        <div className="card card-eduflow">
          <div className="card-header card-header-clean d-flex justify-content-between align-items-center">
            <div>
              <h5 className="mb-0 fw-bold">Formal Grade Appeals</h5>
              <span className="text-muted small">Governed by the 7-day post-publication window (EX-08)</span>
            </div>
            <button className="btn btn-sm btn-primary" onClick={() => setShowAppealModal(true)}>
              <i className="bi bi-plus-lg me-1"></i> Submit Appeal
            </button>
          </div>
          <div className="card-body p-0">
            {loading ? (
              <div className="p-5 text-center text-muted">
                <div className="spinner-border text-primary me-2" role="status"></div> Loading appeals...
              </div>
            ) : appeals.length === 0 ? (
              <div className="p-5 text-center text-muted">
                <i className="bi bi-shield-slash fs-1 d-block mb-2 text-secondary"></i>
                No appeals filed yet.
              </div>
            ) : (
              <div className="table-responsive">
                <table className="table table-eduflow align-middle">
                  <thead>
                    <tr>
                      <th>Appeal ID</th>
                      <th>Grade ID</th>
                      <th>Learner</th>
                      <th>Reason / Justification</th>
                      <th>Desired Score</th>
                      <th>Status</th>
                      <th className="text-end">Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {appeals.map(a => (
                      <tr key={a.id}>
                        <td>
                          <span className="fw-bold font-mono text-dark small">{a.id}</span>
                        </td>
                        <td>
                          <span className="badge bg-light text-dark border font-mono small">{a.grade_id}</span>
                        </td>
                        <td>
                          <span className="font-mono text-secondary small">{a.learner_id}</span>
                        </td>
                        <td>
                          <div className="text-dark small text-truncate" style={{ maxWidth: '300px' }}>
                            {a.reason}
                          </div>
                        </td>
                        <td>
                          <span className="fw-bold text-primary">{a.desired_score || '—'} pts</span>
                        </td>
                        <td>
                          <StatusBadge status={a.status} />
                        </td>
                        <td className="text-end">
                          {a.status === 'pending' || a.status === 'under_review' ? (
                            <button
                              className="btn btn-sm btn-outline-primary"
                              onClick={() => {
                                setSelectedAppeal(a);
                                setAdjudicateForm(prev => ({
                                  ...prev,
                                  adjusted_score: a.desired_score || 90.0
                                }));
                                setShowAdjudicateModal(true);
                              }}
                            >
                              Adjudicate
                            </button>
                          ) : (
                            <span className="text-muted small">Resolved</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      ) : (
        /* Resubmissions Tab */
        <div className="card card-eduflow">
          <div className="card-header card-header-clean d-flex justify-content-between align-items-center">
            <div>
              <h5 className="mb-0 fw-bold">Resubmission Policy Requests</h5>
              <span className="text-muted small">Governed by maximum attempt limits &amp; deadline policies</span>
            </div>
            <button className="btn btn-sm btn-primary" onClick={() => setShowResubModal(true)}>
              <i className="bi bi-plus-lg me-1"></i> Request Resubmission
            </button>
          </div>
          <div className="card-body p-0">
            {loading ? (
              <div className="p-5 text-center text-muted">
                <div className="spinner-border text-primary me-2" role="status"></div> Loading resubmissions...
              </div>
            ) : resubmissions.length === 0 ? (
              <div className="p-5 text-center text-muted">
                <i className="bi bi-arrow-clockwise fs-1 d-block mb-2 text-secondary"></i>
                No resubmission requests recorded yet.
              </div>
            ) : (
              <div className="table-responsive">
                <table className="table table-eduflow align-middle">
                  <thead>
                    <tr>
                      <th>Request ID</th>
                      <th>Submission ID</th>
                      <th>Learner</th>
                      <th>Reason</th>
                      <th>Status</th>
                      <th className="text-end">Review</th>
                    </tr>
                  </thead>
                  <tbody>
                    {resubmissions.map(r => (
                      <tr key={r.id}>
                        <td>
                          <span className="fw-bold font-mono text-dark small">{r.id}</span>
                        </td>
                        <td>
                          <span className="badge bg-light text-dark border font-mono small">{r.submission_id}</span>
                        </td>
                        <td>
                          <span className="font-mono text-secondary small">{r.learner_id}</span>
                        </td>
                        <td>
                          <div className="text-dark small text-truncate" style={{ maxWidth: '320px' }}>
                            {r.reason}
                          </div>
                        </td>
                        <td>
                          <StatusBadge status={r.status} />
                        </td>
                        <td className="text-end">
                          {r.status === 'pending' ? (
                            <button
                              className="btn btn-sm btn-outline-primary"
                              onClick={() => {
                                setSelectedResub(r);
                                setShowReviewResubModal(true);
                              }}
                            >
                              Review
                            </button>
                          ) : (
                            <span className="text-muted small">Reviewed</span>
                          )}
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

      {/* File Appeal Modal */}
      {showAppealModal && (
        <div className="modal show d-block" tabIndex="-1" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
          <div className="modal-dialog modal-dialog-centered">
            <div className="modal-content">
              <form onSubmit={handleCreateAppeal}>
                <div className="modal-header">
                  <h5 className="modal-title fw-bold">Submit Academic Appeal</h5>
                  <button type="button" className="btn-close" onClick={() => setShowAppealModal(false)}></button>
                </div>
                <div className="modal-body">
                  <div className="mb-3">
                    <label className="form-label small fw-semibold">Grade ID</label>
                    <input
                      type="text"
                      className="form-control font-mono small"
                      placeholder="e.g. GRD-SUB-ASN-2026-000001-LNR-2026-000001-01"
                      required
                      value={appealForm.grade_id}
                      onChange={e => setAppealForm({ ...appealForm, grade_id: e.target.value })}
                    />
                    <div className="form-text small">Must be an issued grade within the 7-day post-publication window (EX-08).</div>
                  </div>
                  <div className="mb-3">
                    <label className="form-label small fw-semibold">Learner ID</label>
                    <input
                      type="text"
                      className="form-control font-mono small"
                      placeholder="e.g. LNR-2026-000001"
                      required
                      value={appealForm.learner_id}
                      onChange={e => setAppealForm({ ...appealForm, learner_id: e.target.value })}
                    />
                  </div>
                  <div className="mb-3">
                    <label className="form-label small fw-semibold">Desired Score</label>
                    <input
                      type="number"
                      step="0.5"
                      className="form-control"
                      value={appealForm.desired_score}
                      onChange={e => setAppealForm({ ...appealForm, desired_score: Number(e.target.value) })}
                    />
                  </div>
                  <div className="mb-3">
                    <label className="form-label small fw-semibold">Formal Rationale</label>
                    <textarea
                      className="form-control"
                      rows="3"
                      required
                      value={appealForm.reason}
                      onChange={e => setAppealForm({ ...appealForm, reason: e.target.value })}
                    ></textarea>
                  </div>
                </div>
                <div className="modal-footer">
                  <button type="button" className="btn btn-secondary" onClick={() => setShowAppealModal(false)}>
                    Cancel
                  </button>
                  <button type="submit" className="btn btn-primary-gradient">
                    Lodge Appeal
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Adjudicate Appeal Modal */}
      {showAdjudicateModal && selectedAppeal && (
        <div className="modal show d-block" tabIndex="-1" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
          <div className="modal-dialog modal-dialog-centered">
            <div className="modal-content">
              <form onSubmit={handleAdjudicate}>
                <div className="modal-header">
                  <h5 className="modal-title fw-bold">Adjudicate Appeal: {selectedAppeal.id}</h5>
                  <button type="button" className="btn-close" onClick={() => setShowAdjudicateModal(false)}></button>
                </div>
                <div className="modal-body">
                  <div className="mb-3">
                    <label className="form-label small fw-semibold">Decision</label>
                    <select
                      className="form-select"
                      value={adjudicateForm.decision}
                      onChange={e => setAdjudicateForm({ ...adjudicateForm, decision: e.target.value })}
                    >
                      <option value="approved">Approve &amp; Adjust Grade</option>
                      <option value="rejected">Reject Appeal</option>
                    </select>
                  </div>
                  {adjudicateForm.decision === 'approved' && (
                    <div className="mb-3">
                      <label className="form-label small fw-semibold">Adjusted Final Score</label>
                      <input
                        type="number"
                        step="0.5"
                        className="form-control font-mono fw-bold"
                        required
                        value={adjudicateForm.adjusted_score}
                        onChange={e => setAdjudicateForm({ ...adjudicateForm, adjusted_score: Number(e.target.value) })}
                      />
                    </div>
                  )}
                  <div className="mb-3">
                    <label className="form-label small fw-semibold">Committee Rationale (Audit Trail)</label>
                    <textarea
                      className="form-control"
                      rows="3"
                      required
                      value={adjudicateForm.rationale}
                      onChange={e => setAdjudicateForm({ ...adjudicateForm, rationale: e.target.value })}
                    ></textarea>
                    <div className="form-text small">Mandatory rationale recorded into immutable AuditLog (EX-04).</div>
                  </div>
                </div>
                <div className="modal-footer">
                  <button type="button" className="btn btn-secondary" onClick={() => setShowAdjudicateModal(false)}>
                    Cancel
                  </button>
                  <button type="submit" className="btn btn-primary-gradient">
                    Confirm Adjudication
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Request Resubmission Modal */}
      {showResubModal && (
        <div className="modal show d-block" tabIndex="-1" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
          <div className="modal-dialog modal-dialog-centered">
            <div className="modal-content">
              <form onSubmit={handleCreateResub}>
                <div className="modal-header">
                  <h5 className="modal-title fw-bold">Request Resubmission</h5>
                  <button type="button" className="btn-close" onClick={() => setShowResubModal(false)}></button>
                </div>
                <div className="modal-body">
                  <div className="mb-3">
                    <label className="form-label small fw-semibold">Existing Submission ID</label>
                    {submissions.length > 0 ? (
                      <select
                        className="form-select font-mono small"
                        required
                        value={resubForm.submission_id}
                        onChange={e => setResubForm({ ...resubForm, submission_id: e.target.value })}
                      >
                        <option value="">Select submission...</option>
                        {submissions.map(s => (
                          <option key={s.id} value={s.id}>
                            {s.id} ({s.assignment_id} - Ver {s.version})
                          </option>
                        ))}
                      </select>
                    ) : (
                      <input
                        type="text"
                        className="form-control font-mono small"
                        placeholder="e.g. SUB-ASN-2026-000001-LNR-2026-000001-01"
                        required
                        value={resubForm.submission_id}
                        onChange={e => setResubForm({ ...resubForm, submission_id: e.target.value })}
                      />
                    )}
                  </div>
                  <div className="mb-3">
                    <label className="form-label small fw-semibold">Learner ID</label>
                    <input
                      type="text"
                      className="form-control font-mono small"
                      placeholder="e.g. LNR-2026-000001"
                      required
                      value={resubForm.learner_id}
                      onChange={e => setResubForm({ ...resubForm, learner_id: e.target.value })}
                    />
                  </div>
                  <div className="mb-3">
                    <label className="form-label small fw-semibold">Reason for Request</label>
                    <textarea
                      className="form-control"
                      rows="3"
                      required
                      value={resubForm.reason}
                      onChange={e => setResubForm({ ...resubForm, reason: e.target.value })}
                    ></textarea>
                  </div>
                </div>
                <div className="modal-footer">
                  <button type="button" className="btn btn-secondary" onClick={() => setShowResubModal(false)}>
                    Cancel
                  </button>
                  <button type="submit" className="btn btn-primary-gradient">
                    Submit Request
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Review Resubmission Modal */}
      {showReviewResubModal && selectedResub && (
        <div className="modal show d-block" tabIndex="-1" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
          <div className="modal-dialog modal-dialog-centered">
            <div className="modal-content">
              <form onSubmit={handleReviewResub}>
                <div className="modal-header">
                  <h5 className="modal-title fw-bold">Review Resubmission: {selectedResub.id}</h5>
                  <button type="button" className="btn-close" onClick={() => setShowReviewResubModal(false)}></button>
                </div>
                <div className="modal-body">
                  <div className="mb-3">
                    <label className="form-label small fw-semibold">Review Decision</label>
                    <select
                      className="form-select"
                      value={reviewResubForm.status}
                      onChange={e => setReviewResubForm({ ...reviewResubForm, status: e.target.value })}
                    >
                      <option value="approved">Approve (Increment Version to Attempt N+1)</option>
                      <option value="rejected">Reject</option>
                    </select>
                  </div>
                  <div className="mb-3">
                    <label className="form-label small fw-semibold">Instructor Review Notes</label>
                    <textarea
                      className="form-control"
                      rows="3"
                      value={reviewResubForm.notes}
                      onChange={e => setReviewResubForm({ ...reviewResubForm, notes: e.target.value })}
                    ></textarea>
                  </div>
                </div>
                <div className="modal-footer">
                  <button type="button" className="btn btn-secondary" onClick={() => setShowReviewResubModal(false)}>
                    Cancel
                  </button>
                  <button type="submit" className="btn btn-primary-gradient">
                    Confirm Review
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
