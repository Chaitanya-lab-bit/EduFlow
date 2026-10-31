import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { api } from '../api/client';
import StatusBadge from '../components/StatusBadge';
import AlertBanner from '../components/AlertBanner';

export default function GradingView({ selectedSubmissionId }) {
  const { currentUser } = useAuth();
  const [submissions, setSubmissions] = useState([]);
  const [activeSubmissionId, setActiveSubmissionId] = useState(selectedSubmissionId || '');
  const [submissionDetail, setSubmissionDetail] = useState(null);
  const [assignmentDetail, setAssignmentDetail] = useState(null);
  const [rubricCriteria, setRubricCriteria] = useState([]);
  const [criterionScores, setCriterionScores] = useState({});
  const [lateStatus, setLateStatus] = useState(null);
  const [feedbackText, setFeedbackText] = useState('');
  const [sentiment, setSentiment] = useState('positive');
  const [existingGrade, setExistingGrade] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [alert, setAlert] = useState(null);

  // Load submissions needing evaluation
  const loadSubmissions = async () => {
    try {
      setLoading(true);
      const res = await api.getSubmissionHistory({ per_page: 50 });
      const items = res.items || [];
      setSubmissions(items);

      if (!activeSubmissionId && items.length > 0) {
        // Pick first pending or first submission
        const pending = items.find(s => s.status === 'submitted' || s.status === 'under_review') || items[0];
        setActiveSubmissionId(pending.id);
      }
    } catch (err) {
      setAlert({
        type: 'danger',
        message: err.message || 'Failed to load submissions for grading',
        error_code: err.error_code,
        details: err.details,
        status: err.status
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSubmissions();
  }, []);

  useEffect(() => {
    if (selectedSubmissionId) {
      setActiveSubmissionId(selectedSubmissionId);
    }
  }, [selectedSubmissionId]);

  // When activeSubmissionId changes, load details, assignment rubrics, existing grade, and late status
  useEffect(() => {
    if (!activeSubmissionId) return;

    async function loadGradingContext() {
      try {
        const sub = submissions.find(s => s.id === activeSubmissionId);
        if (!sub) return;
        setSubmissionDetail(sub);
        setExistingGrade(null);

        // Fetch assignment & late status
        const [asn, late] = await Promise.all([
          api.getAssignment(sub.assignment_id),
          api.checkLateStatus(sub.id)
        ]);

        setAssignmentDetail(asn);
        setLateStatus(late);

        // Extract rubric criteria from assignment or build defaults
        let criteria = [];
        if (asn.rubrics && asn.rubrics.length > 0 && asn.rubrics[0].criteria) {
          criteria = asn.rubrics[0].criteria;
        } else {
          criteria = [
            { id: 1, title: 'Functional Implementation', max_points: Math.floor(asn.max_score * 0.7) },
            { id: 2, title: 'Code Quality & Style', max_points: Math.ceil(asn.max_score * 0.3) }
          ];
        }
        setRubricCriteria(criteria);

        // Check if already graded
        try {
          const gradeData = await api.getGradeBySubmission(sub.id);
          if (gradeData) {
            setExistingGrade(gradeData);
            if (gradeData.criterion_scores) {
              const scores = {};
              gradeData.criterion_scores.forEach(cs => {
                scores[cs.criterion_id || cs.criterion_title] = cs.score;
              });
              setCriterionScores(scores);
            }
          } else {
            // Default initial scores
            const initialScores = {};
            criteria.forEach(c => {
              initialScores[c.id || c.title] = Math.round(c.max_points * 0.85);
            });
            setCriterionScores(initialScores);
          }
        } catch {
          // Not graded yet, set default scores
          const initialScores = {};
          criteria.forEach(c => {
            initialScores[c.id || c.title] = Math.round(c.max_points * 0.85);
          });
          setCriterionScores(initialScores);
        }
      } catch (err) {
        console.error('Failed to load grading context', err);
      }
    }

    loadGradingContext();
  }, [activeSubmissionId, submissions]);

  const handleScoreChange = (critId, val, maxPoints) => {
    const num = Math.min(Math.max(0, Number(val) || 0), maxPoints);
    setCriterionScores(prev => ({ ...prev, [critId]: num }));
  };

  // Calculations
  const rawScore = rubricCriteria.reduce((sum, c) => sum + (Number(criterionScores[c.id || c.title]) || 0), 0);
  const latePenaltyRate = lateStatus && lateStatus.is_late ? (lateStatus.late_penalty_percentage || 0) : 0;
  const latePenaltyDeduction = rawScore * latePenaltyRate;
  const finalScore = Math.max(0, Math.round((rawScore - latePenaltyDeduction) * 10) / 10);

  const handleSubmitGrade = async (e) => {
    e.preventDefault();
    if (!submissionDetail) return;

    try {
      setSaving(true);
      setAlert(null);
      const graderId = currentUser && currentUser.id ? currentUser.id : 'INST-2026-0001';

      const gradePayload = {
        submission_id: submissionDetail.id,
        criterion_scores: rubricCriteria.map(c => ({
          criterion_id: typeof c.id === 'number' ? c.id : undefined,
          criterion_title: c.title,
          score: Number(criterionScores[c.id || c.title]) || 0,
          max_points: c.max_points,
          comments: 'Evaluated according to coursework rubric'
        })),
        grader_id: graderId
      };

      const gradeRes = await api.gradeSubmission(gradePayload);

      // Submit qualitative feedback if provided
      if (feedbackText.trim()) {
        try {
          await api.addFeedback({
            submission_id: submissionDetail.id,
            grade_id: gradeRes.id,
            feedback_text: feedbackText,
            sentiment: sentiment,
            instructor_id: graderId
          });
        } catch (fErr) {
          console.warn('Feedback notice:', fErr);
        }
      }

      setAlert({
        type: 'success',
        message: `Evaluation committed! Grade ID: ${gradeRes.id} (Final Score: ${gradeRes.final_score} pts). Late penalty deduction applied: ${gradeRes.late_penalty_deduction} pts.`
      });

      loadSubmissions();
    } catch (err) {
      setAlert({
        type: 'danger',
        message: err.message || 'Failed to submit grade evaluation',
        error_code: err.error_code,
        details: err.details,
        status: err.status
      });
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="container-fluid px-0">
      <AlertBanner alert={alert} onClose={() => setAlert(null)} />

      <div className="d-flex flex-column flex-md-row justify-content-between align-items-md-center mb-4 gap-3">
        <div>
          <h3 className="fw-bold mb-1">Grading &amp; Evaluation Workspace</h3>
          <p className="text-muted mb-0">Evaluate student coursework against rubric criteria, compute automated late deductions, and provide qualitative feedback.</p>
        </div>
      </div>

      <div className="row g-4">
        {/* Left Column: Submissions Queue */}
        <div className="col-lg-4">
          <div className="card card-eduflow h-100">
            <div className="card-header card-header-clean d-flex justify-content-between align-items-center">
              <h6 className="mb-0 fw-bold">Evaluation Queue</h6>
              <span className="badge bg-secondary-subtle text-secondary small">{submissions.length} Submissions</span>
            </div>
            <div className="card-body p-0" style={{ maxHeight: '650px', overflowY: 'auto' }}>
              {loading ? (
                <div className="p-4 text-center text-muted">
                  <div className="spinner-border spinner-border-sm me-2" role="status"></div> Loading queue...
                </div>
              ) : submissions.length === 0 ? (
                <div className="p-4 text-center text-muted">No submissions found.</div>
              ) : (
                <div className="list-group list-group-flush">
                  {submissions.map(s => {
                    const isSelected = s.id === activeSubmissionId;
                    return (
                      <button
                        key={s.id}
                        type="button"
                        className={`list-group-item list-group-item-action p-3 border-bottom ${
                          isSelected ? 'bg-light border-start border-4 border-primary' : ''
                        }`}
                        onClick={() => setActiveSubmissionId(s.id)}
                      >
                        <div className="d-flex justify-content-between align-items-start mb-1">
                          <span className="fw-bold font-mono small text-dark">{s.id}</span>
                          <StatusBadge status={s.status} />
                        </div>
                        <div className="text-muted small font-mono">{s.assignment_id}</div>
                        <div className="d-flex justify-content-between align-items-center mt-2 small">
                          <span className="text-secondary font-mono">{s.learner_id}</span>
                          <span className="text-muted">Ver. {s.version}</span>
                        </div>
                      </button>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Right Column: Grading Interface */}
        <div className="col-lg-8">
          {submissionDetail && assignmentDetail ? (
            <div className="card card-eduflow">
              <div className="card-header card-header-clean bg-white d-flex justify-content-between align-items-center">
                <div>
                  <h5 className="mb-0 fw-bold">{assignmentDetail.title}</h5>
                  <div className="text-muted small">
                    Submission: <span className="font-mono text-dark">{submissionDetail.id}</span> &bull; Learner:{' '}
                    <span className="font-mono text-dark">{submissionDetail.learner_id}</span>
                  </div>
                </div>
                <StatusBadge status={submissionDetail.status} />
              </div>

              <div className="card-body p-4">
                {/* Existing Grade Notification */}
                {existingGrade && (
                  <div className="alert alert-info d-flex align-items-center mb-3">
                    <i className="bi bi-info-circle-fill me-2 fs-5"></i>
                    <div>
                      This submission has already been graded with Final Score: <strong>{existingGrade.final_score} / {assignmentDetail.max_score} pts</strong> (Raw: {existingGrade.raw_score} pts, Deduction: -{existingGrade.late_penalty_deduction} pts). Re-submitting updates the grade idempotently with an audit log entry.
                    </div>
                  </div>
                )}

                {/* Lateness Policy Banner */}
                {lateStatus && (
                  <div className={`alert d-flex align-items-center mb-4 ${lateStatus.is_late ? 'alert-warning' : 'alert-success'}`}>
                    <i className={`bi bi-${lateStatus.is_late ? 'alarm-fill' : 'check-circle-fill'} me-2 fs-5`}></i>
                    <div>
                      {lateStatus.is_late ? (
                        <span>
                          <strong>Late Submission:</strong> {lateStatus.days_late} day(s) late past grace period. A{' '}
                          <strong>{(lateStatus.late_penalty_percentage * 100).toFixed(0)}%</strong> penalty is calculated automatically.
                        </span>
                      ) : (
                        <span>
                          <strong>On-Time Submission:</strong> Submitted within official deadline and grace window.
                        </span>
                      )}
                    </div>
                  </div>
                )}

                <form onSubmit={handleSubmitGrade}>
                  {/* Rubric Criteria Table */}
                  <h6 className="fw-bold text-uppercase small text-muted mb-3" style={{ letterSpacing: '0.04em' }}>
                    Rubric Criteria Evaluation
                  </h6>

                  <div className="table-responsive mb-4">
                    <table className="table table-bordered align-middle">
                      <thead className="table-light">
                        <tr>
                          <th>Criterion &amp; Guidelines</th>
                          <th style={{ width: '120px' }}>Max Points</th>
                          <th style={{ width: '160px' }}>Assigned Score</th>
                        </tr>
                      </thead>
                      <tbody>
                        {rubricCriteria.map(c => {
                          const critId = c.id || c.title;
                          const currentVal = criterionScores[critId] !== undefined ? criterionScores[critId] : 0;
                          return (
                            <tr key={critId}>
                              <td>
                                <div className="fw-semibold text-dark">{c.title}</div>
                                {c.description && <div className="text-muted small">{c.description}</div>}
                              </td>
                              <td className="text-center font-mono fw-bold text-secondary">
                                {c.max_points} pts
                              </td>
                              <td>
                                <div className="input-group input-group-sm">
                                  <input
                                    type="number"
                                    className="form-control text-end font-mono fw-bold"
                                    min="0"
                                    max={c.max_points}
                                    step="0.5"
                                    required
                                    value={currentVal}
                                    onChange={e => handleScoreChange(critId, e.target.value, c.max_points)}
                                  />
                                  <span className="input-group-text font-mono small">/ {c.max_points}</span>
                                </div>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>

                  {/* Score Computation Summary */}
                  <div className="p-3 mb-4 rounded-3 border bg-light">
                    <div className="row text-center g-3">
                      <div className="col-4">
                        <div className="text-muted small text-uppercase">Raw Score Sum</div>
                        <div className="fs-4 fw-bold text-dark">{rawScore} pts</div>
                      </div>
                      <div className="col-4 border-start border-end">
                        <div className="text-muted small text-uppercase">Late Deduction</div>
                        <div className="fs-4 fw-bold text-danger">
                          -{latePenaltyDeduction.toFixed(1)} pts
                          <span className="small text-muted d-block" style={{ fontSize: '0.75rem' }}>
                            ({(latePenaltyRate * 100).toFixed(0)}%)
                          </span>
                        </div>
                      </div>
                      <div className="col-4">
                        <div className="text-muted small text-uppercase">Final Score</div>
                        <div className="fs-4 fw-bold text-success">
                          {finalScore} <span className="fs-6 text-muted">/ {assignmentDetail.max_score}</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Qualitative Feedback */}
                  <div className="mb-4">
                    <label className="form-label small fw-bold text-uppercase text-muted">
                      Instructor Qualitative Feedback
                    </label>
                    <textarea
                      className="form-control mb-2"
                      rows="3"
                      placeholder="Provide constructive feedback, highlight strengths, or point out areas for improvement..."
                      value={feedbackText}
                      onChange={e => setFeedbackText(e.target.value)}
                    ></textarea>
                    <div className="d-flex align-items-center gap-2">
                      <span className="small text-muted fw-semibold">Sentiment:</span>
                      <select
                        className="form-select form-select-sm"
                        style={{ width: '180px' }}
                        value={sentiment}
                        onChange={e => setSentiment(e.target.value)}
                      >
                        <option value="positive">&bull; Positive</option>
                        <option value="neutral">&bull; Neutral</option>
                        <option value="needs_improvement">&bull; Needs Improvement</option>
                      </select>
                    </div>
                  </div>

                  <div className="d-flex justify-content-end gap-2">
                    <button
                      type="submit"
                      className="btn btn-primary-gradient px-4 py-2"
                      disabled={saving}
                    >
                      {saving ? (
                        <>
                          <span className="spinner-border spinner-border-sm me-2" role="status"></span>
                          Recording Evaluation...
                        </>
                      ) : (
                        <>
                          <i className="bi bi-check2-circle me-2"></i> Commit Grade &amp; Feedback
                        </>
                      )}
                    </button>
                  </div>
                </form>
              </div>
            </div>
          ) : (
            <div className="card card-eduflow p-5 text-center text-muted">
              <i className="bi bi-file-earmark-person fs-1 d-block mb-2 text-secondary"></i>
              Select a submission from the left queue to begin grading.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
