import React from 'react';

export default function DecisionBanner({ decision, riskScore, riskLevel, feature }) {
  let bg, border, iconColor, titleColor, titleText, icon;
  let pulseClass = '';
  let numericalScore = 0.08;

  if (decision === 'GO') {
    bg = 'var(--green-bg)'; border = 'var(--green-border)';
    iconColor = 'var(--green)'; titleColor = 'var(--green)';
    titleText = 'GO';
    numericalScore = 0.08;
    icon = (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="currentColor">
        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
      </svg>
    );
  } else if (decision === 'GO_WITH_CONDITIONS') {
    bg = 'var(--amber-bg)'; border = 'var(--amber-border)';
    iconColor = 'var(--amber)'; titleColor = 'var(--amber)';
    titleText = 'GO WITH CONDITIONS';
    numericalScore = 0.61;
    icon = (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
        <line x1="12" y1="9" x2="12" y2="13"/>
        <line x1="12" y1="17" x2="12.01" y2="17"/>
      </svg>
    );
  } else {
    bg = 'var(--red-bg)'; border = 'var(--red-border)';
    iconColor = 'var(--red)'; titleColor = 'var(--red)';
    titleText = 'NO-GO';
    numericalScore = 0.94;
    pulseClass = 'banner-no-go';
    icon = (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="10"/>
        <line x1="4.93" y1="4.93" x2="19.07" y2="19.07"/>
      </svg>
    );
  }

  // Override numeric score based on level if available in riskLevel
  if (riskLevel === 'Critical') numericalScore = 0.94;
  else if (riskLevel === 'High') numericalScore = 0.61;
  else if (riskLevel === 'Low') numericalScore = 0.08;

  return (
    <div 
      style={{
        background: bg,
        border: `0.5px solid ${border}`,
        borderRadius: 'var(--radius-lg)',
        padding: '16px 20px',
        display: 'flex',
        alignItems: 'center',
        gap: '16px',
        animation: decision === 'NO_GO' ? 'pulse-danger 2s ease-in-out infinite' : 'none'
      }}
    >
      <div style={{ color: iconColor, flexShrink: 0 }}>
        {icon}
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontSize: '18px', fontWeight: 500, color: titleColor, marginBottom: '2px' }}>
          {titleText}
        </div>
        <div style={{ fontSize: '12px', color: 'var(--text-muted)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
          {feature}
        </div>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', flexShrink: 0 }}>
        <div style={{ fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Risk score</div>
        <div style={{ fontSize: '22px', fontWeight: 500, color: titleColor, lineHeight: '1.2' }}>
          {numericalScore.toFixed(2)}
        </div>
        <div style={{ 
          fontSize: '9px', 
          background: titleColor, 
          color: bg, 
          padding: '2px 6px', 
          borderRadius: '4px', 
          fontWeight: 600,
          marginTop: '2px',
          textTransform: 'uppercase'
        }}>
          {riskLevel}
        </div>
      </div>
    </div>
  );
}
