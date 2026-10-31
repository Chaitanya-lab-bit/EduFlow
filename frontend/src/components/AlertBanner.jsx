import React, { useState } from 'react';

export default function AlertBanner({ alert, onClose }) {
  const [showDetails, setShowDetails] = useState(false);
  if (!alert || (!alert.message && !alert.error)) return null;

  const type = alert.type || (alert.error ? 'danger' : 'info');
  const message = alert.message || alert.error;
  const icon =
    type === 'success'
      ? 'check-circle-fill'
      : type === 'danger'
      ? 'exclamation-triangle-fill'
      : type === 'warning'
      ? 'exclamation-circle-fill'
      : 'info-circle-fill';

  const hasDetails = alert.details && (
    (Array.isArray(alert.details) && alert.details.length > 0) ||
    (typeof alert.details === 'object' && Object.keys(alert.details).length > 0) ||
    typeof alert.details === 'string'
  );

  return (
    <div
      className={`alert alert-${type} alert-dismissible fade show mb-4 shadow-sm`}
      role="alert"
    >
      <div className="d-flex align-items-start">
        <i className={`bi bi-${icon} me-2 fs-5 flex-shrink-0 mt-1`}></i>
        <div className="flex-grow-1 text-break">
          <div className="d-flex align-items-center flex-wrap gap-2 mb-1">
            <span className="fw-semibold">{message}</span>
            {alert.error_code && (
              <span className="badge bg-danger-subtle text-danger-emphasis border font-mono small">
                {alert.error_code}
              </span>
            )}
            {alert.status && (
              <span className="badge bg-secondary-subtle text-secondary small font-mono">
                HTTP {alert.status}
              </span>
            )}
          </div>

          {hasDetails && (
            <div className="mt-2">
              <button
                type="button"
                className="btn btn-sm btn-link text-decoration-none p-0 text-muted small"
                onClick={() => setShowDetails(!showDetails)}
              >
                <i className={`bi bi-chevron-${showDetails ? 'up' : 'down'} me-1`}></i>
                {showDetails ? 'Hide technical details' : 'Show technical details'}
              </button>

              {showDetails && (
                <div className="mt-2 p-2 bg-white bg-opacity-75 rounded border small font-mono">
                  {Array.isArray(alert.details) ? (
                    <ul className="mb-0 ps-3">
                      {alert.details.map((d, idx) => (
                        <li key={idx}>
                          {typeof d === 'object' ? (
                            <span>
                              <strong>{d.loc ? d.loc.join('.') : 'Field'}:</strong> {d.msg || JSON.stringify(d)}
                            </span>
                          ) : (
                            String(d)
                          )}
                        </li>
                      ))}
                    </ul>
                  ) : typeof alert.details === 'object' ? (
                    <pre className="mb-0 text-wrap">{JSON.stringify(alert.details, null, 2)}</pre>
                  ) : (
                    <div>{String(alert.details)}</div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>

        {onClose && (
          <button
            type="button"
            className="btn-close ms-2"
            aria-label="Close"
            onClick={onClose}
          ></button>
        )}
      </div>
    </div>
  );
}
