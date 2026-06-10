import React from 'react';

export default function ReasoningBox({ reasoning, decision, topRisks }) {
  return (
    <>
      {decision === 'NO_GO' && topRisks && topRisks.length > 0 && (
        <div style={{
          background: 'var(--red-bg)',
          border: '0.5px solid var(--red-border)',
          borderRadius: 'var(--radius-md)',
          padding: '12px 14px',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '8px' }}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--red)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10"></circle>
              <line x1="12" y1="8" x2="12" y2="12"></line>
              <line x1="12" y1="16" x2="12.01" y2="16"></line>
            </svg>
            <span style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--red)', fontWeight: 600 }}>
              Why this is a hard stop
            </span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {topRisks.map((risk, idx) => (
              <div key={idx} style={{ display: 'flex', alignItems: 'flex-start', gap: '8px' }}>
                <div style={{ flexShrink: 0, marginTop: '2px' }}>
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="var(--red)" strokeWidth="2"><circle cx="12" cy="12" r="4"></circle><circle cx="12" cy="12" r="10"></circle></svg>
                </div>
                <div style={{ fontSize: '12px', color: '#ffa3a3', lineHeight: '1.5' }}>
                  {risk.description}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div style={{
        background: 'var(--bg-surface)',
        border: '0.5px solid var(--border)',
        borderRadius: 'var(--radius-md)',
        padding: '12px 14px'
      }}>
        <div style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '8px', letterSpacing: '0.05em' }}>
          Agent reasoning
        </div>
        <div style={{ fontSize: '12px', color: 'var(--text-secondary)', lineHeight: '1.7' }}>
          {reasoning}
        </div>
      </div>
    </>
  );
}
