import React from 'react';

export default function IdleState() {
  return (
    <div style={{
      height: '100%',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center'
    }}>
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#30363d" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="10"></circle>
        <circle cx="12" cy="12" r="6"></circle>
        <circle cx="12" cy="12" r="2"></circle>
      </svg>
      <div style={{ fontSize: '15px', color: 'var(--text-muted)', marginTop: '12px' }}>
        Ready to analyze
      </div>
      <div style={{ fontSize: '12px', color: '#444c56', textAlign: 'center', maxWidth: '240px', marginTop: '8px' }}>
        Pick a scenario or describe your feature, then click analyze to run a pre-deployment risk simulation
      </div>
    </div>
  );
}
