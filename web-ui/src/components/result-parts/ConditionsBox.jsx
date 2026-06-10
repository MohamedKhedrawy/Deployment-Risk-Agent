import React from 'react';

export default function ConditionsBox({ conditions }) {
  if (!conditions || conditions.length === 0) return null;

  return (
    <div style={{
      background: 'var(--amber-bg)',
      border: '0.5px solid var(--amber-border)',
      borderRadius: 'var(--radius-md)',
      padding: '12px 14px'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '8px' }}>
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--amber)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
          <line x1="12" y1="9" x2="12" y2="13"></line>
          <line x1="12" y1="17" x2="12.01" y2="17"></line>
        </svg>
        <span style={{ fontSize: '11px', uppercase: 'uppercase', color: 'var(--amber)', letterSpacing: '0.07em', fontWeight: 600 }}>
          Deployment conditions
        </span>
      </div>
      
      <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
        {conditions.map((cond, idx) => {
          const text = cond.toLowerCase();
          let icon = (
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="var(--amber)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
              <line x1="12" y1="9" x2="12" y2="13"></line>
              <line x1="12" y1="17" x2="12.01" y2="17"></line>
            </svg>
          );
          
          if (text.includes('utc') || text.includes('hour') || text.includes('time')) {
            icon = <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="var(--amber)" strokeWidth="2"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>;
          } else if (text.includes('canary') || text.includes('rollout')) {
            icon = <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="var(--amber)" strokeWidth="2"><line x1="6" y1="3" x2="6" y2="15"></line><circle cx="18" cy="6" r="3"></circle><circle cx="6" cy="18" r="3"></circle><path d="M18 9a9 9 0 0 1-9 9"></path></svg>;
          } else if (text.includes('rollback') || text.includes('revert')) {
            icon = <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="var(--amber)" strokeWidth="2"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path><polyline points="9 22 9 12 15 12 15 22"></polyline></svg>; // home as fallback
          } else if (text.includes('slo') || text.includes('metric') || text.includes('drop')) {
            icon = <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="var(--amber)" strokeWidth="2"><polyline points="23 18 13.5 8.5 8.5 13.5 1 6"></polyline><polyline points="17 18 23 18 23 12"></polyline></svg>;
          }

          return (
            <div key={idx} style={{ display: 'flex', alignItems: 'flex-start', gap: '8px' }}>
              <div style={{ flexShrink: 0, marginTop: '1px' }}>{icon}</div>
              <div style={{ fontSize: '12px', color: '#c9a227', lineHeight: '1.5' }}>{cond}</div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
