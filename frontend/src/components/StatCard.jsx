import React from 'react';

export default function StatCard({ title, value, icon, color = 'primary', subtext }) {
  const colorMap = {
    primary: { bg: '#eff6ff', text: '#2563eb' },
    success: { bg: '#ecfdf5', text: '#059669' },
    warning: { bg: '#fffbeb', text: '#d97706' },
    danger: { bg: '#fef2f2', text: '#dc2626' },
    indigo: { bg: '#e0e7ff', text: '#4f46e5' },
    cyan: { bg: '#ecfeff', text: '#0891b2' },
  };

  const scheme = colorMap[color] || colorMap.primary;

  return (
    <div className="card card-eduflow h-100 p-3">
      <div className="d-flex align-items-center">
        <div
          className="stat-icon-wrapper me-3 flex-shrink-0"
          style={{ backgroundColor: scheme.bg, color: scheme.text }}
        >
          <i className={`bi bi-${icon}`}></i>
        </div>
        <div className="overflow-hidden">
          <div className="text-muted small text-uppercase fw-semibold" style={{ letterSpacing: '0.04em' }}>
            {title}
          </div>
          <div className="fs-3 fw-bold text-dark my-1">
            {value !== undefined && value !== null ? value : '—'}
          </div>
          {subtext && <div className="text-muted small text-truncate">{subtext}</div>}
        </div>
      </div>
    </div>
  );
}

