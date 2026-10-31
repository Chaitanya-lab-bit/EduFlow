import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { api } from '../api/client';

export default function Navbar({ activeTab, setActiveTab }) {
  const { role, currentUser, availableLearners, switchRole, loginAsUser, apiBaseUrl, updateApiBaseUrl } = useAuth();
  const [apiOnline, setApiOnline] = useState(null);
  const [showConfigModal, setShowConfigModal] = useState(false);
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [tempApiUrl, setTempApiUrl] = useState(apiBaseUrl);

  const checkConnectivity = () => {
    api.checkHealth()
      .then(data => {
        setApiOnline(data && data.status === 'healthy');
      })
      .catch(() => setApiOnline(false));
  };

  useEffect(() => {
    checkConnectivity();
    const interval = setInterval(checkConnectivity, 15000);
    return () => clearInterval(interval);
  }, [apiBaseUrl]);

  const roles = [
    { id: 'learner', label: 'Learner', icon: 'person-workspace' },
    { id: 'instructor', label: 'Instructor', icon: 'person-video3' },
    { id: 'admin', label: 'Administrator', icon: 'shield-lock' }
  ];

  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: 'speedometer2' },
    { id: 'courses', label: 'Courses', icon: 'journal-bookmark-fill' },
    { id: 'learners', label: 'Learners', icon: 'people-fill', roles: ['instructor', 'admin'] },
    { id: 'assignments', label: 'Assignments', icon: 'file-earmark-ruled' },
    { id: 'submissions', label: 'Submissions', icon: 'upload' },
    { id: 'grading', label: 'Grading', icon: 'check2-square', roles: ['instructor', 'admin'] },
    { id: 'appeals', label: 'Appeals & Resubmissions', icon: 'arrow-repeat' },
  ];

  const visibleNav = navItems.filter(item => !item.roles || item.roles.includes(role));

  const handleSaveApiUrl = (e) => {
    e.preventDefault();
    updateApiBaseUrl(tempApiUrl);
    setShowConfigModal(false);
    setTimeout(checkConnectivity, 300);
  };

  return (
    <header className="sticky-top bg-white border-bottom shadow-sm">
      {/* Top Banner: Role Selection, User Badge & API Status */}
      <div className="bg-light border-bottom py-1 px-3 px-md-4">
        <div className="container-fluid d-flex flex-wrap justify-content-between align-items-center gap-2">
          {/* Role selector */}
          <div className="d-flex align-items-center gap-2">
            <span className="small text-muted fw-semibold me-1">ACTIVE ROLE:</span>
            {roles.map(r => (
              <button
                key={r.id}
                type="button"
                className={`role-badge ${role === r.id ? 'active' : ''}`}
                onClick={() => {
                  switchRole(r.id);
                  if (r.id === 'learner' && (activeTab === 'grading' || activeTab === 'learners')) {
                    setActiveTab('dashboard');
                  }
                }}
              >
                <i className={`bi bi-${r.icon} me-1`}></i>
                {r.label}
              </button>
            ))}
          </div>

          {/* User Profile & API Settings */}
          <div className="d-flex align-items-center gap-3 small">
            {/* User identification badge */}
            <button
              type="button"
              className="btn btn-sm btn-outline-secondary py-0 px-2 rounded-pill d-flex align-items-center"
              onClick={() => setShowLoginModal(true)}
              title="Click to switch user account"
            >
              <i className="bi bi-person-fill text-primary me-1"></i>
              <span className="fw-semibold text-dark">{currentUser ? currentUser.name : 'Guest'}</span>
              <span className="text-muted font-mono ms-1 small">({currentUser ? currentUser.id : ''})</span>
              <i className="bi bi-caret-down-fill text-muted ms-1" style={{ fontSize: '0.65rem' }}></i>
            </button>

            {/* API Connection indicator with config button */}
            <div className="d-flex align-items-center gap-1">
              <span
                className="d-inline-block rounded-circle me-1"
                style={{
                  width: '8px',
                  height: '8px',
                  backgroundColor: apiOnline === true ? '#10b981' : apiOnline === false ? '#ef4444' : '#f59e0b',
                }}
              ></span>
              <span className="text-muted small d-none d-sm-inline">
                {apiOnline === true ? 'API Connected' : apiOnline === false ? 'API Offline' : 'Connecting...'}
              </span>
              <button
                type="button"
                className="btn btn-link text-muted p-0 ms-1"
                onClick={() => {
                  setTempApiUrl(apiBaseUrl);
                  setShowConfigModal(true);
                }}
                title="Configure API Base URL"
              >
                <i className="bi bi-gear-fill"></i>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Navbar */}
      <nav className="navbar navbar-expand-lg navbar-light bg-white py-2 px-3 px-md-4">
        <div className="container-fluid">
          <a
            className="navbar-brand d-flex align-items-center cursor-pointer me-4"
            href="#dashboard"
            onClick={(e) => { e.preventDefault(); setActiveTab('dashboard'); }}
          >
            <div
              className="bg-primary text-white rounded-3 d-flex align-items-center justify-content-center me-2 shadow-sm"
              style={{ width: '34px', height: '34px' }}
            >
              <i className="bi bi-mortarboard-fill fs-5"></i>
            </div>
            <span>EduFlow</span>
          </a>

          <button
            className="navbar-toggler"
            type="button"
            data-bs-toggle="collapse"
            data-bs-target="#eduflowNavbar"
            aria-controls="eduflowNavbar"
            aria-expanded="false"
            aria-label="Toggle navigation"
          >
            <span className="navbar-toggler-icon"></span>
          </button>

          <div className="collapse navbar-collapse" id="eduflowNavbar">
            <ul className="navbar-nav me-auto mb-2 mb-lg-0 gap-1">
              {visibleNav.map((item) => (
                <li className="nav-item" key={item.id}>
                  <button
                    className={`nav-link btn btn-link text-decoration-none border-0 ${
                      activeTab === item.id ? 'active' : ''
                    }`}
                    onClick={() => setActiveTab(item.id)}
                  >
                    <i className={`bi bi-${item.icon} me-1`}></i>
                    {item.label}
                  </button>
                </li>
              ))}
            </ul>

            <div className="d-flex align-items-center gap-2">
              <span className="badge bg-light text-dark border px-3 py-2 rounded-pill small">
                <i className="bi bi-shield-check text-primary me-1"></i>
                <span className="fw-semibold text-capitalize">{role} Portal</span>
              </span>
            </div>
          </div>
        </div>
      </nav>

      {/* Switch User / Login Modal */}
      {showLoginModal && (
        <div className="modal show d-block" tabIndex="-1" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
          <div className="modal-dialog modal-dialog-centered">
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title fw-bold">Switch User Identity</h5>
                <button type="button" className="btn-close" onClick={() => setShowLoginModal(false)}></button>
              </div>
              <div className="modal-body">
                <p className="text-muted small mb-3">
                  Select an identity to test role-based permissions, course enrollments, and submission histories.
                </p>

                <h6 className="fw-bold small text-uppercase text-muted">Role Quick Switch</h6>
                <div className="list-group mb-3">
                  <button
                    type="button"
                    className="list-group-item list-group-item-action d-flex justify-content-between align-items-center"
                    onClick={() => {
                      switchRole('learner');
                      setShowLoginModal(false);
                    }}
                  >
                    <div>
                      <div className="fw-bold text-dark">Learner Persona</div>
                      <small className="text-muted">Alex Johnson (Default Student)</small>
                    </div>
                    <span className="badge bg-primary">Learner</span>
                  </button>
                  <button
                    type="button"
                    className="list-group-item list-group-item-action d-flex justify-content-between align-items-center"
                    onClick={() => {
                      switchRole('instructor');
                      setShowLoginModal(false);
                    }}
                  >
                    <div>
                      <div className="fw-bold text-dark">Instructor Persona</div>
                      <small className="text-muted">Dr. Evelyn Vance (Faculty Grader)</small>
                    </div>
                    <span className="badge bg-indigo text-white" style={{ backgroundColor: '#4f46e5' }}>Instructor</span>
                  </button>
                  <button
                    type="button"
                    className="list-group-item list-group-item-action d-flex justify-content-between align-items-center"
                    onClick={() => {
                      switchRole('admin');
                      setShowLoginModal(false);
                    }}
                  >
                    <div>
                      <div className="fw-bold text-dark">Administrator Persona</div>
                      <small className="text-muted">System Administrator (Full Privileges)</small>
                    </div>
                    <span className="badge bg-dark">Admin</span>
                  </button>
                </div>

                {availableLearners.length > 0 && (
                  <>
                    <h6 className="fw-bold small text-uppercase text-muted">Registered Learners from Database</h6>
                    <div className="list-group" style={{ maxHeight: '180px', overflowY: 'auto' }}>
                      {availableLearners.slice(0, 10).map(l => (
                        <button
                          key={l.id}
                          type="button"
                          className="list-group-item list-group-item-action py-2 d-flex justify-content-between align-items-center"
                          onClick={() => {
                            loginAsUser({
                              id: l.id,
                              name: l.name,
                              email: l.email,
                              role: 'learner',
                              timezone: l.timezone || 'UTC'
                            });
                            setShowLoginModal(false);
                          }}
                        >
                          <div>
                            <span className="fw-semibold text-dark small d-block">{l.name}</span>
                            <span className="font-mono text-muted small" style={{ fontSize: '0.75rem' }}>{l.id}</span>
                          </div>
                          <span className="badge bg-light text-secondary border font-mono small">{l.email}</span>
                        </button>
                      ))}
                    </div>
                  </>
                )}
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setShowLoginModal(false)}>
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Configure API Base URL Modal */}
      {showConfigModal && (
        <div className="modal show d-block" tabIndex="-1" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
          <div className="modal-dialog modal-dialog-centered">
            <div className="modal-content">
              <form onSubmit={handleSaveApiUrl}>
                <div className="modal-header">
                  <h5 className="modal-title fw-bold">Configure Flask API Base URL</h5>
                  <button type="button" className="btn-close" onClick={() => setShowConfigModal(false)}></button>
                </div>
                <div className="modal-body">
                  <p className="text-muted small">
                    Default is <code className="fw-bold">/api</code> which is forwarded by the Vite dev server proxy to <code className="fw-bold">http://127.0.0.1:5000</code>.
                  </p>
                  <div className="mb-3">
                    <label className="form-label small fw-semibold">API Base URL</label>
                    <input
                      type="text"
                      className="form-control font-mono"
                      placeholder="e.g. /api or http://localhost:5000/api"
                      value={tempApiUrl}
                      onChange={e => setTempApiUrl(e.target.value)}
                      required
                    />
                  </div>
                  <div className="d-flex gap-2">
                    <button
                      type="button"
                      className="btn btn-sm btn-outline-secondary"
                      onClick={() => setTempApiUrl('/api')}
                    >
                      Reset to Default (/api)
                    </button>
                    <button
                      type="button"
                      className="btn btn-sm btn-outline-secondary"
                      onClick={() => setTempApiUrl('http://127.0.0.1:5000/api')}
                    >
                      Use Direct (http://127.0.0.1:5000/api)
                    </button>
                  </div>
                </div>
                <div className="modal-footer">
                  <button type="button" className="btn btn-secondary" onClick={() => setShowConfigModal(false)}>
                    Cancel
                  </button>
                  <button type="submit" className="btn btn-primary-gradient">
                    Save &amp; Reconnect
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </header>
  );
}
