import React from 'react';

export default function Header() {
  return (
    <header style={{
      height: '52px',
      background: 'var(--bg-surface)',
      borderBottom: '0.5px solid var(--border)',
      padding: '0 24px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      flexShrink: 0
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <div style={{
          background: 'var(--teal)',
          borderRadius: 'var(--radius-sm)',
          width: '28px',
          height: '28px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        }}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M20.24 12.24a6 6 0 0 0-8.49-8.49L5 10.5V19h8.5z"></path>
            <line x1="16" y1="8" x2="2" y2="22"></line>
            <line x1="17.5" y1="15" x2="9" y2="15"></line>
          </svg>
        </div>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px' }}>
          <span style={{ fontSize: '15px', fontWeight: 500 }}>Canary Whisperer</span>
          <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Pre-deployment risk simulation</span>
        </div>
      </div>
      
      <div style={{ display: 'flex', flexDirection: 'row', alignItems: 'center', gap: '16px' }}>
        <div style={{
          background: 'var(--bg-elevated)',
          border: '0.5px solid var(--border-subtle)',
          borderRadius: '20px',
          padding: '4px 10px',
          fontSize: '11px',
          color: 'var(--amber)',
          display: 'flex',
          alignItems: 'center',
          gap: '6px'
        }}>
          <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: 'var(--teal)' }}></div>
          Demo mode
        </div>
        
        <div style={{ fontSize: '11px', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '4px' }}>
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="var(--amber)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon>
          </svg>
          Gemini 2.5 Flash · Dynatrace MCP
        </div>
      </div>
    </header>
  );
}
