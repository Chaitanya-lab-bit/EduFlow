import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import StatusBadge from '../components/StatusBadge';
import AlertBanner from '../components/AlertBanner';

export default function LearnersView() {
  const [learners, setLearners] = useState([]);
  const [courses, setCourses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [alert, setAlert] = useState(null);
  const [showRegisterModal, setShowRegisterModal] = useState(false);
  const [showEnrollModal, setShowEnrollModal] = useState(false);

  // Forms
  const [registerForm, setRegisterForm] = useState({
    name: '',
    email: '',
    timezone: 'UTC',
    status: 'active'
  });

  const [enrollForm, setEnrollForm] = useState({
    learner_id: '',
    course_id: '',
    status: 'active'
  });

  const loadData = async () => {
    try {
      setLoading(true);
      const [lRes, cRes] = await Promise.all([
        api.getLearners({ per_page: 25 }),
        api.getCourses({ per_page: 50 })
      ]);
      setLearners(lRes.items || []);
      setCourses(cRes.items || []);
    } catch (err) {
      setAlert({ type: 'danger', message: err.message || 'Failed to load learners data' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleRegister = async (e) => {
    e.preventDefault();
    try {
      await api.registerLearner(registerForm);
      setAlert({ type: 'success', message: `Learner ${registerForm.name} registered successfully!` });
      setShowRegisterModal(false);
      setRegisterForm({ name: '', email: '', timezone: 'UTC', status: 'active' });
      loadData();
    } catch (err) {
      setAlert({ type: 'danger', message: err.message || 'Failed to register learner' });
    }
  };

  const handleEnroll = async (e) => {
    e.preventDefault();
    try {
      await api.enrollLearner(enrollForm);
      setAlert({ type: 'success', message: `Learner ${enrollForm.learner_id} enrolled in course ${enrollForm.course_id}!` });
      setShowEnrollModal(false);
      setEnrollForm({ learner_id: '', course_id: '', status: 'active' });
    } catch (err) {
      setAlert({ type: 'danger', message: err.message || 'Enrollment failed' });
    }
  };

  return (
    <div className="container-fluid px-0">
      <AlertBanner alert={alert} onClose={() => setAlert(null)} />

      <div className="d-flex flex-column flex-md-row justify-content-between align-items-md-center mb-4 gap-3">
        <div>
          <h3 className="fw-bold mb-1">Learner Directory</h3>
          <p className="text-muted mb-0">Manage student accounts, academic statuses, and institutional course enrollments.</p>
        </div>
        <div className="d-flex gap-2">
          <button className="btn btn-outline-primary" onClick={() => setShowEnrollModal(true)}>
            <i className="bi bi-box-arrow-in-right me-1"></i> Enroll in Course
          </button>
          <button className="btn btn-primary-gradient px-4" onClick={() => setShowRegisterModal(true)}>
            <i className="bi bi-person-plus me-1"></i> Register Learner
          </button>
        </div>
      </div>

      <div className="card card-eduflow">
        <div className="card-body p-0">
          {loading ? (
            <div className="p-5 text-center text-muted">
              <div className="spinner-border text-primary me-2" role="status"></div> Loading learners...
            </div>
          ) : learners.length === 0 ? (
            <div className="p-5 text-center text-muted">
              <i className="bi bi-people fs-1 d-block mb-2 text-secondary"></i>
              No learners registered yet.
            </div>
          ) : (
            <div className="table-responsive">
              <table className="table table-eduflow align-middle">
                <thead>
                  <tr>
                    <th>Learner</th>
                    <th>Email Address</th>
                    <th>Timezone</th>
                    <th>Status</th>
                    <th className="text-end">Quick Action</th>
                  </tr>
                </thead>
                <tbody>
                  {learners.map(l => (
                    <tr key={l.id}>
                      <td>
                        <div className="fw-bold text-dark">{l.name}</div>
                        <span className="text-muted font-mono small">{l.id}</span>
                      </td>
                      <td>
                        <span className="font-mono text-dark small">{l.email}</span>
                      </td>
                      <td>
                        <span className="badge bg-light text-secondary border font-mono">{l.timezone}</span>
                      </td>
                      <td>
                        <StatusBadge status={l.status} />
                      </td>
                      <td className="text-end">
                        <button
                          className="btn btn-sm btn-outline-secondary"
                          onClick={() => {
                            setEnrollForm(prev => ({ ...prev, learner_id: l.id }));
                            setShowEnrollModal(true);
                          }}
                        >
                          Enroll
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

      {/* Register Learner Modal */}
      {showRegisterModal && (
        <div className="modal show d-block" tabIndex="-1" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
          <div className="modal-dialog modal-dialog-centered">
            <div className="modal-content">
              <form onSubmit={handleRegister}>
                <div className="modal-header">
                  <h5 className="modal-title fw-bold">Register New Learner</h5>
                  <button type="button" className="btn-close" onClick={() => setShowRegisterModal(false)}></button>
                </div>
                <div className="modal-body">
                  <div className="mb-3">
                    <label className="form-label small fw-semibold">Full Name</label>
                    <input
                      type="text"
                      className="form-control"
                      placeholder="e.g. Alex Johnson"
                      required
                      value={registerForm.name}
                      onChange={e => setRegisterForm({ ...registerForm, name: e.target.value })}
                    />
                  </div>
                  <div className="mb-3">
                    <label className="form-label small fw-semibold">Email Address</label>
                    <input
                      type="email"
                      className="form-control"
                      placeholder="e.g. alex.johnson@eduflow.edu"
                      required
                      value={registerForm.email}
                      onChange={e => setRegisterForm({ ...registerForm, email: e.target.value })}
                    />
                  </div>
                  <div className="row g-2">
                    <div className="col-6">
                      <label className="form-label small fw-semibold">Timezone</label>
                      <select
                        className="form-select font-mono small"
                        value={registerForm.timezone}
                        onChange={e => setRegisterForm({ ...registerForm, timezone: e.target.value })}
                      >
                        <option value="UTC">UTC</option>
                        <option value="America/New_York">America/New_York (EST)</option>
                        <option value="America/Los_Angeles">America/Los_Angeles (PST)</option>
                        <option value="Asia/Kolkata">Asia/Kolkata (IST)</option>
                        <option value="Europe/London">Europe/London (GMT)</option>
                      </select>
                    </div>
                    <div className="col-6">
                      <label className="form-label small fw-semibold">Status</label>
                      <select
                        className="form-select small"
                        value={registerForm.status}
                        onChange={e => setRegisterForm({ ...registerForm, status: e.target.value })}
                      >
                        <option value="active">Active</option>
                        <option value="inactive">Inactive</option>
                        <option value="suspended">Suspended</option>
                      </select>
                    </div>
                  </div>
                </div>
                <div className="modal-footer">
                  <button type="button" className="btn btn-secondary" onClick={() => setShowRegisterModal(false)}>
                    Cancel
                  </button>
                  <button type="submit" className="btn btn-primary-gradient">
                    Register
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Enroll Learner Modal */}
      {showEnrollModal && (
        <div className="modal show d-block" tabIndex="-1" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
          <div className="modal-dialog modal-dialog-centered">
            <div className="modal-content">
              <form onSubmit={handleEnroll}>
                <div className="modal-header">
                  <h5 className="modal-title fw-bold">Enroll Learner into Course</h5>
                  <button type="button" className="btn-close" onClick={() => setShowEnrollModal(false)}></button>
                </div>
                <div className="modal-body">
                  <div className="mb-3">
                    <label className="form-label small fw-semibold">Learner</label>
                    <select
                      className="form-select font-mono small"
                      required
                      value={enrollForm.learner_id}
                      onChange={e => setEnrollForm({ ...enrollForm, learner_id: e.target.value })}
                    >
                      <option value="">Select a learner...</option>
                      {learners.map(l => (
                        <option key={l.id} value={l.id}>{l.name} ({l.id})</option>
                      ))}
                    </select>
                  </div>
                  <div className="mb-3">
                    <label className="form-label small fw-semibold">Course</label>
                    <select
                      className="form-select font-mono small"
                      required
                      value={enrollForm.course_id}
                      onChange={e => setEnrollForm({ ...enrollForm, course_id: e.target.value })}
                    >
                      <option value="">Select a course...</option>
                      {courses.map(c => (
                        <option key={c.id} value={c.id}>{c.code}: {c.title} ({c.id})</option>
                      ))}
                    </select>
                  </div>
                </div>
                <div className="modal-footer">
                  <button type="button" className="btn btn-secondary" onClick={() => setShowEnrollModal(false)}>
                    Cancel
                  </button>
                  <button type="submit" className="btn btn-primary-gradient">
                    Confirm Enrollment
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

