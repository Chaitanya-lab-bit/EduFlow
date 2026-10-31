import React from 'react';

export default function Footer() {
  return (
    <footer className="bg-white border-top py-4 mt-auto">
      <div className="container-fluid px-4 d-flex flex-column flex-md-row justify-content-between align-items-center gap-2 text-muted small">
        <div className="d-flex align-items-center gap-2">
          <span className="fw-bold text-dark">EduFlow</span>
          <span>&copy; {new Date().getFullYear()} Assignment & Evaluation Management System</span>
        </div>
        <div className="d-flex align-items-center gap-3">
          <span><i className="bi bi-shield-check text-success me-1"></i>ACID Invariants Verified</span>
          <span><i className="bi bi-database me-1"></i>PostgreSQL &amp; SQLAlchemy 2.0</span>
          <span><i className="bi bi-globe me-1"></i>ISO UTC Timezone Compliant</span>
        </div>
      </div>
    </footer>
  );
}

