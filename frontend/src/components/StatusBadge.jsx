import React from 'react';

export default function StatusBadge({ status }) {
  if (!status) return null;
  const s = String(status).toLowerCase();

  let badgeClass = 'bg-secondary';
  if (['published', 'active', 'approved'].includes(s)) {
    badgeClass = 'bg-success';
  } else if (['submitted', 'completed'].includes(s)) {
    badgeClass = 'bg-primary';
  } else if (['under_review', 'appealed', 'pending'].includes(s)) {
    badgeClass = 'bg-warning text-dark';
  } else if (['graded'].includes(s)) {
    badgeClass = 'bg-info text-dark';
  } else if (['rejected', 'dropped', 'failed'].includes(s)) {
    badgeClass = 'bg-danger';
  } else if (['draft', 'archived'].includes(s)) {
    badgeClass = 'bg-light text-muted border';
  }

  return (
    <span className={`badge ${badgeClass} text-uppercase px-2 py-1`} style={{ fontSize: '0.72rem', letterSpacing: '0.04em' }}>
      {s.replace('_', ' ')}
    </span>
  );
}

