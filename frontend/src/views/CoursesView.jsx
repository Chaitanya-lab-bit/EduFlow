import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import StatusBadge from '../components/StatusBadge';
import AlertBanner from '../components/AlertBanner';

export default function CoursesView() {
  const [courses, setCourses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [alert, setAlert] = useState(null);
  const [showModal, setShowModal] = useState(false);

  // Form State
  const [form, setForm] = useState({
    code: '',
    title: '',
    term: 'Fall 2026',
    start_date: '2026-09-01T00:00:00Z',
    end_date: '2026-12-15T23:59:59Z',
    timezone: 'UTC',
    status: 'active'
  });

  const loadCourses = async () => {
    try {
      setLoading(true);
      const res = await api.getCourses({ per_page: 20 });
      setCourses(res.items || []);
    } catch (err) {
      setAlert({ type: 'danger', message: err.message || 'Failed to load courses' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCourses();
  }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    try {
      await api.createCourse(form);
      setAlert({ type: 'success', message: `Course ${form.code} created successfully!` });
      setShowModal(false);
      setForm({
        code: '',
        title: '',
        term: 'Fall 2026',
        start_date: '2026-09-01T00:00:00Z',
        end_date: '2026-12-15T23:59:59Z',
        timezone: 'UTC',
        status: 'active'
      });
      loadCourses();
    } catch (err) {
      setAlert({ type: 'danger', message: err.message || 'Failed to create course' });
    }
  };

  return (
    <div className="container-fluid px-0">
      <AlertBanner alert={alert} onClose={() => setAlert(null)} />

      <div className="d-flex flex-column flex-md-row justify-content-between align-items-md-center mb-4 gap-3">
        <div>
          <h3 className="fw-bold mb-1">Course Catalog</h3>
          <p className="text-muted mb-0">Manage institutional course offerings, academic terms, and timezone alignments.</p>
        </div>
        <button className="btn btn-primary-gradient px-4" onClick={() => setShowModal(true)}>
          <i className="bi bi-plus-lg me-1"></i> Add Course
        </button>
      </div>

      <div className="card card-eduflow">
        <div className="card-body p-0">
          {loading ? (
            <div className="p-5 text-center text-muted">
              <div className="spinner-border text-primary me-2" role="status"></div> Loading courses...
            </div>
          ) : courses.length === 0 ? (
            <div className="p-5 text-center text-muted">
              <i className="bi bi-journal-x fs-1 d-block mb-2 text-secondary"></i>
              No courses found. Click "Add Course" above to create one.
            </div>
          ) : (
            <div className="table-responsive">
              <table className="table table-eduflow align-middle">
                <thead>
                  <tr>
                    <th>Course Code &amp; Title</th>
                    <th>Term</th>
                    <th>Timezone</th>
                    <th>Schedule (Start &ndash; End)</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {courses.map(c => (
                    <tr key={c.id}>
                      <td>
                        <div className="fw-bold text-dark">{c.title}</div>
                        <span className="badge bg-light text-primary border font-mono small">{c.code}</span>
                        <span className="text-muted font-mono small ms-2">{c.id}</span>
                      </td>
                      <td>
                        <span className="fw-semibold text-secondary">{c.term}</span>
                      </td>
                      <td>
                        <span className="badge bg-secondary-subtle text-secondary font-mono">{c.timezone}</span>
                      </td>
                      <td>
                        <div className="small text-muted">
                          {c.start_date ? new Date(c.start_date).toLocaleDateString() : '—'} &rarr;{' '}
                          {c.end_date ? new Date(c.end_date).toLocaleDateString() : '—'}
                        </div>
                      </td>
                      <td>
                        <StatusBadge status={c.status} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Create Course Modal */}
      {showModal && (
        <div className="modal show d-block" tabIndex="-1" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
          <div className="modal-dialog modal-dialog-centered">
            <div className="modal-content">
              <form onSubmit={handleCreate}>
                <div className="modal-header">
                  <h5 className="modal-title fw-bold">Create New Course</h5>
                  <button type="button" className="btn-close" onClick={() => setShowModal(false)}></button>
                </div>
                <div className="modal-body">
                  <div className="mb-3">
                    <label className="form-label small fw-semibold">Course Code</label>
                    <input
                      type="text"
                      className="form-control font-mono"
                      placeholder="e.g. CS101, DATA200"
                      required
                      value={form.code}
                      onChange={e => setForm({ ...form, code: e.target.value })}
                    />
                  </div>
                  <div className="mb-3">
                    <label className="form-label small fw-semibold">Course Title</label>
                    <input
                      type="text"
                      className="form-control"
                      placeholder="e.g. Introduction to Computer Science"
                      required
                      value={form.title}
                      onChange={e => setForm({ ...form, title: e.target.value })}
                    />
                  </div>
                  <div className="row g-2 mb-3">
                    <div className="col-6">
                      <label className="form-label small fw-semibold">Term</label>
                      <input
                        type="text"
                        className="form-control"
                        required
                        value={form.term}
                        onChange={e => setForm({ ...form, term: e.target.value })}
                      />
                    </div>
                    <div className="col-6">
                      <label className="form-label small fw-semibold">Timezone</label>
                      <select
                        className="form-select font-mono small"
                        value={form.timezone}
                        onChange={e => setForm({ ...form, timezone: e.target.value })}
                      >
                        <option value="UTC">UTC</option>
                        <option value="America/New_York">America/New_York (EST)</option>
                        <option value="America/Los_Angeles">America/Los_Angeles (PST)</option>
                        <option value="Asia/Kolkata">Asia/Kolkata (IST)</option>
                        <option value="Europe/London">Europe/London (GMT)</option>
                      </select>
                    </div>
                  </div>
                  <div className="row g-2 mb-3">
                    <div className="col-6">
                      <label className="form-label small fw-semibold">Start Date (ISO)</label>
                      <input
                        type="text"
                        className="form-control font-mono small"
                        value={form.start_date}
                        onChange={e => setForm({ ...form, start_date: e.target.value })}
                        required
                      />
                    </div>
                    <div className="col-6">
                      <label className="form-label small fw-semibold">End Date (ISO)</label>
                      <input
                        type="text"
                        className="form-control font-mono small"
                        value={form.end_date}
                        onChange={e => setForm({ ...form, end_date: e.target.value })}
                        required
                      />
                    </div>
                  </div>
                </div>
                <div className="modal-footer">
                  <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>
                    Cancel
                  </button>
                  <button type="submit" className="btn btn-primary-gradient">
                    Create Course
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

