import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import StatusBadge from '../components/StatusBadge';
import AlertBanner from '../components/AlertBanner';

export default function AssignmentsView() {
  const [assignments, setAssignments] = useState([]);
  const [courses, setCourses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [alert, setAlert] = useState(null);

  // Modals
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showRubricModal, setShowRubricModal] = useState(false);
  const [selectedAssignment, setSelectedAssignment] = useState(null);

  // Create Assignment Form
  const [createForm, setCreateForm] = useState({
    course_id: '',
    title: '',
    description: '',
    max_score: 100,
    due_date: '2026-11-15T23:59:59Z',
    cutoff_date: '2026-11-20T23:59:59Z',
    grace_period_minutes: 15,
    late_penalty_per_day: 0.05,
    max_resubmissions: 1,
    allowed_file_types: ['pdf', 'zip', 'py']
  });

  // Rubric Configuration Form
  const [criteria, setCriteria] = useState([
    { title: 'Functional Correctness', description: 'Implements all required specification tests', max_points: 60, weight: 0.6 },
    { title: 'Code Quality & Design', description: 'Modular architecture, comments, style adherence', max_points: 40, weight: 0.4 }
  ]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [aRes, cRes] = await Promise.all([
        api.getAssignments({ per_page: 50 }),
        api.getCourses({ per_page: 50 })
      ]);
      setAssignments(aRes.items || []);
      setCourses(cRes.items || []);
      if (cRes.items && cRes.items.length > 0 && !createForm.course_id) {
        setCreateForm(prev => ({ ...prev, course_id: cRes.items[0].id }));
      }
    } catch (err) {
      setAlert({ type: 'danger', message: err.message || 'Failed to load assignments' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        ...createForm,
        max_score: Number(createForm.max_score),
        grace_period_minutes: Number(createForm.grace_period_minutes),
        late_penalty_per_day: Number(createForm.late_penalty_per_day),
        max_resubmissions: Number(createForm.max_resubmissions),
      };
      const res = await api.createAssignment(payload);
      setAlert({ type: 'success', message: `Assignment "${payload.title}" created (${res.id}) as Draft!` });
      setShowCreateModal(false);
      loadData();
    } catch (err) {
      setAlert({ type: 'danger', message: err.message || 'Failed to create assignment' });
    }
  };

  const openRubricModal = (assignment) => {
    setSelectedAssignment(assignment);
    const half = Math.floor(assignment.max_score / 2);
    const remainder = assignment.max_score - half;
    setCriteria([
      { title: 'Technical Execution & Requirements', description: 'Meets functional deliverables and criteria', max_points: half, weight: half / assignment.max_score },
      { title: 'Documentation & Architecture', description: 'Clear design, report completeness, and code style', max_points: remainder, weight: remainder / assignment.max_score },
    ]);
    setShowRubricModal(true);
  };

  const handleCriterionChange = (index, field, value) => {
    const updated = [...criteria];
    updated[index][field] = field === 'max_points' || field === 'weight' ? Number(value) : value;
    setCriteria(updated);
  };

  const addCriterion = () => {
    setCriteria([...criteria, { title: 'New Criterion', description: '', max_points: 10, weight: 0.1 }]);
  };

  const removeCriterion = (index) => {
    if (criteria.length <= 1) return;
    setCriteria(criteria.filter((_, i) => i !== index));
  };

  const criteriaSum = criteria.reduce((sum, c) => sum + (Number(c.max_points) || 0), 0);

  const handleSaveRubrics = async () => {
    if (!selectedAssignment) return;
    try {
      const rubricsPayload = [
        {
          title: `${selectedAssignment.title} Rubric`,
          description: 'Standard grading rubric',
          criteria: criteria.map(c => ({
            title: c.title,
            description: c.description,
            max_points: Number(c.max_points),
            weight: Number(c.weight) || 0
          }))
        }
      ];

      await api.configureRubrics(selectedAssignment.id, rubricsPayload);
      setAlert({ type: 'success', message: `Rubrics successfully configured for ${selectedAssignment.id}!` });
      setShowRubricModal(false);
      loadData();
    } catch (err) {
      setAlert({ type: 'danger', message: err.message || 'Failed to save rubrics' });
    }
  };

  const handlePublish = async (assignmentId) => {
    try {
      await api.publishAssignment(assignmentId);
      setAlert({ type: 'success', message: `Assignment ${assignmentId} published successfully!` });
      loadData();
    } catch (err) {
      setAlert({ type: 'danger', message: err.message || 'Failed to publish assignment. Ensure rubric criteria points match assignment max score!' });
    }
  };

  return (
    <div className="container-fluid px-0">
      <AlertBanner alert={alert} onClose={() => setAlert(null)} />

      <div className="d-flex flex-column flex-md-row justify-content-between align-items-md-center mb-4 gap-3">
        <div>
          <h3 className="fw-bold mb-1">Course Assignments &amp; Rubrics</h3>
          <p className="text-muted mb-0">Define coursework, specify submission deadlines, configure grading criteria, and publish tasks.</p>
        </div>
        <button className="btn btn-primary-gradient px-4" onClick={() => setShowCreateModal(true)}>
          <i className="bi bi-plus-lg me-1"></i> New Assignment
        </button>
      </div>

      <div className="card card-eduflow">
        <div className="card-body p-0">
          {loading ? (
            <div className="p-5 text-center text-muted">
              <div className="spinner-border text-primary me-2" role="status"></div> Loading assignments...
            </div>
          ) : assignments.length === 0 ? (
            <div className="p-5 text-center text-muted">
              <i className="bi bi-file-earmark-x fs-1 d-block mb-2 text-secondary"></i>
              No assignments found. Click "New Assignment" to author one.
            </div>
          ) : (
            <div className="table-responsive">
              <table className="table table-eduflow align-middle">
                <thead>
                  <tr>
                    <th>Assignment Title &amp; ID</th>
                    <th>Course</th>
                    <th>Max Score</th>
                    <th>Due Date (UTC)</th>
                    <th>Cutoff Date</th>
                    <th>Status</th>
                    <th className="text-end">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {assignments.map(a => (
                    <tr key={a.id}>
                      <td>
                        <div className="fw-bold text-dark">{a.title}</div>
                        <span className="text-muted font-mono small">{a.id}</span>
                      </td>
                      <td>
                        <span className="badge bg-light text-dark border font-mono">{a.course_id}</span>
                      </td>
                      <td>
                        <span className="fw-bold text-success">{a.max_score} pts</span>
                      </td>
                      <td>
                        <div className="small text-dark">
                          {a.due_date ? new Date(a.due_date).toLocaleString() : '—'}
                        </div>
                        {a.grace_period_minutes > 0 && (
                          <span className="badge bg-warning-subtle text-warning-emphasis small">
                            +{a.grace_period_minutes}m grace
                          </span>
                        )}
                      </td>
                      <td>
                        <div className="small text-muted">
                          {a.cutoff_date ? new Date(a.cutoff_date).toLocaleString() : '—'}
                        </div>
                      </td>
                      <td>
                        <StatusBadge status={a.status} />
                      </td>
                      <td className="text-end">
                        <div className="btn-group btn-group-sm">
                          <button
                            className="btn btn-outline-secondary"
                            title="Configure Rubrics"
                            onClick={() => openRubricModal(a)}
                          >
                            <i className="bi bi-card-checklist me-1"></i> Rubric
                          </button>
                          {a.status === 'draft' && (
                            <button
                              className="btn btn-success"
                              title="Publish Assignment"
                              onClick={() => handlePublish(a.id)}
                            >
                              <i className="bi bi-send-check me-1"></i> Publish
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Create Assignment Modal */}
      {showCreateModal && (
        <div className="modal show d-block" tabIndex="-1" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
          <div className="modal-dialog modal-lg modal-dialog-centered">
            <div className="modal-content">
              <form onSubmit={handleCreate}>
                <div className="modal-header">
                  <h5 className="modal-title fw-bold">Author New Assignment</h5>
                  <button type="button" className="btn-close" onClick={() => setShowCreateModal(false)}></button>
                </div>
                <div className="modal-body">
                  <div className="row g-3 mb-3">
                    <div className="col-md-6">
                      <label className="form-label small fw-semibold">Target Course</label>
                      <select
                        className="form-select font-mono small"
                        required
                        value={createForm.course_id}
                        onChange={e => setCreateForm({ ...createForm, course_id: e.target.value })}
                      >
                        <option value="">Select course...</option>
                        {courses.map(c => (
                          <option key={c.id} value={c.id}>{c.code} - {c.title}</option>
                        ))}
                      </select>
                    </div>
                    <div className="col-md-6">
                      <label className="form-label small fw-semibold">Max Score (Total Points)</label>
                      <input
                        type="number"
                        className="form-control"
                        required
                        min="1"
                        max="1000"
                        value={createForm.max_score}
                        onChange={e => setCreateForm({ ...createForm, max_score: e.target.value })}
                      />
                    </div>
                  </div>

                  <div className="mb-3">
                    <label className="form-label small fw-semibold">Assignment Title</label>
                    <input
                      type="text"
                      className="form-control"
                      placeholder="e.g. Project 1: Vectorized Data Engineering Pipeline"
                      required
                      value={createForm.title}
                      onChange={e => setCreateForm({ ...createForm, title: e.target.value })}
                    />
                  </div>

                  <div className="mb-3">
                    <label className="form-label small fw-semibold">Instructions / Description</label>
                    <textarea
                      className="form-control"
                      rows="2"
                      placeholder="Describe learning goals, requirements and deliverables..."
                      value={createForm.description}
                      onChange={e => setCreateForm({ ...createForm, description: e.target.value })}
                    ></textarea>
                  </div>

                  <div className="row g-3 mb-3">
                    <div className="col-md-6">
                      <label className="form-label small fw-semibold">Due Date (ISO UTC)</label>
                      <input
                        type="text"
                        className="form-control font-mono small"
                        required
                        value={createForm.due_date}
                        onChange={e => setCreateForm({ ...createForm, due_date: e.target.value })}
                      />
                    </div>
                    <div className="col-md-6">
                      <label className="form-label small fw-semibold">Hard Cutoff Date (ISO UTC)</label>
                      <input
                        type="text"
                        className="form-control font-mono small"
                        required
                        value={createForm.cutoff_date}
                        onChange={e => setCreateForm({ ...createForm, cutoff_date: e.target.value })}
                      />
                    </div>
                  </div>

                  <div className="row g-3">
                    <div className="col-md-4">
                      <label className="form-label small fw-semibold">Grace Period (Minutes)</label>
                      <input
                        type="number"
                        className="form-control"
                        min="0"
                        value={createForm.grace_period_minutes}
                        onChange={e => setCreateForm({ ...createForm, grace_period_minutes: e.target.value })}
                      />
                    </div>
                    <div className="col-md-4">
                      <label className="form-label small fw-semibold">Late Penalty Rate / Day</label>
                      <input
                        type="number"
                        step="0.01"
                        min="0"
                        max="1"
                        className="form-control"
                        value={createForm.late_penalty_per_day}
                        onChange={e => setCreateForm({ ...createForm, late_penalty_per_day: e.target.value })}
                      />
                    </div>
                    <div className="col-md-4">
                      <label className="form-label small fw-semibold">Max Resubmissions</label>
                      <input
                        type="number"
                        min="0"
                        max="10"
                        className="form-control"
                        value={createForm.max_resubmissions}
                        onChange={e => setCreateForm({ ...createForm, max_resubmissions: e.target.value })}
                      />
                    </div>
                  </div>
                </div>
                <div className="modal-footer">
                  <button type="button" className="btn btn-secondary" onClick={() => setShowCreateModal(false)}>
                    Cancel
                  </button>
                  <button type="submit" className="btn btn-primary-gradient">
                    Create Assignment
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Configure Rubrics Modal */}
      {showRubricModal && selectedAssignment && (
        <div className="modal show d-block" tabIndex="-1" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
          <div className="modal-dialog modal-lg modal-dialog-centered">
            <div className="modal-content">
              <div className="modal-header">
                <div>
                  <h5 className="modal-title fw-bold">Configure Rubrics: {selectedAssignment.title}</h5>
                  <div className="text-muted small">Target Max Score: <strong className="text-primary">{selectedAssignment.max_score} pts</strong></div>
                </div>
                <button type="button" className="btn-close" onClick={() => setShowRubricModal(false)}></button>
              </div>
              <div className="modal-body">
                <div className={`alert d-flex justify-content-between align-items-center mb-3 ${
                  criteriaSum === selectedAssignment.max_score ? 'alert-success' : 'alert-warning'
                }`}>
                  <div>
                    <i className="bi bi-info-circle me-2"></i>
                    Criteria Points Sum: <strong>{criteriaSum} / {selectedAssignment.max_score} pts</strong>
                  </div>
                  {criteriaSum !== selectedAssignment.max_score && (
                    <span className="small text-danger fw-semibold">Must match assignment max score to publish (BR-04)!</span>
                  )}
                </div>

                {criteria.map((c, i) => (
                  <div key={i} className="card p-3 mb-2 bg-light border">
                    <div className="row g-2 align-items-center">
                      <div className="col-md-5">
                        <label className="form-label small fw-semibold mb-1">Criterion Title</label>
                        <input
                          type="text"
                          className="form-control form-control-sm"
                          value={c.title}
                          onChange={e => handleCriterionChange(i, 'title', e.target.value)}
                          placeholder="e.g. Code Architecture"
                        />
                      </div>
                      <div className="col-md-3">
                        <label className="form-label small fw-semibold mb-1">Max Points</label>
                        <input
                          type="number"
                          className="form-control form-control-sm"
                          value={c.max_points}
                          onChange={e => handleCriterionChange(i, 'max_points', e.target.value)}
                        />
                      </div>
                      <div className="col-md-3">
                        <label className="form-label small fw-semibold mb-1">Weight</label>
                        <input
                          type="number"
                          step="0.05"
                          className="form-control form-control-sm"
                          value={c.weight}
                          onChange={e => handleCriterionChange(i, 'weight', e.target.value)}
                        />
                      </div>
                      <div className="col-md-1 text-end mt-4">
                        <button
                          type="button"
                          className="btn btn-sm btn-outline-danger"
                          onClick={() => removeCriterion(i)}
                          disabled={criteria.length <= 1}
                        >
                          <i className="bi bi-trash"></i>
                        </button>
                      </div>
                      <div className="col-12 mt-2">
                        <input
                          type="text"
                          className="form-control form-control-sm"
                          placeholder="Evaluation guidelines for this criterion..."
                          value={c.description}
                          onChange={e => handleCriterionChange(i, 'description', e.target.value)}
                        />
                      </div>
                    </div>
                  </div>
                ))}

                <button
                  type="button"
                  className="btn btn-sm btn-outline-primary mt-2"
                  onClick={addCriterion}
                >
                  <i className="bi bi-plus-circle me-1"></i> Add Another Criterion
                </button>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setShowRubricModal(false)}>
                  Cancel
                </button>
                <button
                  type="button"
                  className="btn btn-primary-gradient"
                  onClick={handleSaveRubrics}
                >
                  Save Rubric Criteria
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

