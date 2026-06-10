import React, { useState } from 'react';

export default function LeftPanel({ featureInput, setFeatureInput, triggerAnalysis, analysisState }) {
  const [hoveredBtn, setHoveredBtn] = useState(null);

  const handleScenarioClick = (scenarioText) => {
    setFeatureInput(scenarioText);
    triggerAnalysis(scenarioText);
  };

  const getBtnStyle = (type, isHovered) => {
    let bg, border, color;
    if (type === 'safe') { bg = 'var(--green-bg)'; border = 'var(--green-border)'; color = 'var(--green)'; }
    if (type === 'risky') { bg = 'var(--amber-bg)'; border = 'var(--amber-border)'; color = 'var(--amber)'; }
    if (type === 'fatal') { bg = 'var(--red-bg)'; border = 'var(--red-border)'; color = 'var(--red)'; }

    return {
      background: bg,
      border: `0.5px solid ${border}`,
      borderRadius: 'var(--radius-md)',
      padding: '8px 4px',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      gap: '4px',
      cursor: 'pointer',
      color: color,
      fontSize: '11px',
      filter: isHovered ? 'brightness(1.15)' : 'none',
      transition: 'filter 0.15s ease'
    };
  };

  return (
    <div style={{
      width: '320px',
      background: 'var(--bg-surface)',
      borderRight: '0.5px solid var(--border)',
      padding: '20px',
      display: 'flex',
      flexDirection: 'column',
      gap: '16px',
      height: '100%',
      flexShrink: 0
    }}>
      
      {/* Section 1 */}
      <div>
        <div style={{
          fontSize: '11px',
          fontWeight: 500,
          textTransform: 'uppercase',
          letterSpacing: '0.08em',
          color: 'var(--text-muted)',
          marginBottom: '8px'
        }}>
          Deployment scenario
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '6px' }}>
          <button
            style={getBtnStyle('safe', hoveredBtn === 'safe')}
            onMouseEnter={() => setHoveredBtn('safe')}
            onMouseLeave={() => setHoveredBtn(null)}
            onClick={() => handleScenarioClick("Add dark mode toggle to user preferences panel")}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>
            Safe
          </button>
          
          <button
            style={getBtnStyle('risky', hoveredBtn === 'risky')}
            onMouseEnter={() => setHoveredBtn('risky')}
            onMouseLeave={() => setHoveredBtn(null)}
            onClick={() => handleScenarioClick("Integrate loyalty points into the checkout flow")}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>
            Risky
          </button>
          
          <button
            style={getBtnStyle('fatal', hoveredBtn === 'fatal')}
            onMouseEnter={() => setHoveredBtn('fatal')}
            onMouseLeave={() => setHoveredBtn(null)}
            onClick={() => handleScenarioClick("Migrate authentication service to new OAuth2 provider")}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>
            Fatal
          </button>
        </div>
      </div>

      {/* Section 2 */}
      <textarea
        value={featureInput}
        onChange={e => setFeatureInput(e.target.value)}
        placeholder="Describe the feature you want to deploy...&#10;e.g. Integrate loyalty points into the checkout flow"
        rows={4}
        style={{
          width: '100%',
          background: 'var(--bg-base)',
          border: '0.5px solid var(--border)',
          borderRadius: 'var(--radius-md)',
          color: 'var(--text-primary)',
          fontSize: '13px',
          padding: '10px 12px',
          resize: 'none',
          fontFamily: 'inherit',
          lineHeight: '1.5',
          outline: 'none',
          transition: 'border-color 0.15s'
        }}
        onFocus={e => e.target.style.borderColor = 'var(--blue)'}
        onBlur={e => e.target.style.borderColor = 'var(--border)'}
      />

      {/* Section 3 */}
      <button
        disabled={analysisState === 'loading' || !featureInput.trim()}
        onClick={() => triggerAnalysis(featureInput)}
        style={{
          width: '100%',
          background: 'var(--teal)',
          color: 'white',
          fontSize: '13px',
          fontWeight: 500,
          borderRadius: 'var(--radius-md)',
          padding: '10px',
          border: 'none',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '8px',
          opacity: (analysisState === 'loading' || !featureInput.trim()) ? 0.6 : 1,
          cursor: (analysisState === 'loading' || !featureInput.trim()) ? 'not-allowed' : 'pointer',
          transition: 'background 0.2s ease'
        }}
        onMouseEnter={(e) => {
          if (analysisState !== 'loading' && featureInput.trim()) {
            e.currentTarget.style.background = '#19896a';
          }
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.background = 'var(--teal)';
        }}
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>
        Analyze deployment risk
      </button>

      {/* Section 4 */}
      <div style={{ marginTop: 'auto' }}>
        <div style={{ height: '1px', background: 'var(--border)', margin: '0 -20px 16px -20px' }}></div>
        <div style={{
          fontSize: '11px',
          fontWeight: 500,
          textTransform: 'uppercase',
          letterSpacing: '0.08em',
          color: 'var(--text-muted)',
          marginBottom: '12px'
        }}>
          How it works
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--teal)" strokeWidth="2"><circle cx="18" cy="5" r="3"></circle><circle cx="6" cy="12" r="3"></circle><circle cx="18" cy="19" r="3"></circle><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"></line><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"></line></svg>
            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Maps feature to Dynatrace service topology</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--teal)" strokeWidth="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg>
            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Checks 30-day incident history and SLO budgets</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--teal)" strokeWidth="2"><path d="M19 3H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V5a2 2 0 0 0-2-2z"></path><line x1="12" y1="7" x2="12" y2="17"></line><line x1="7" y1="12" x2="17" y2="12"></line></svg>
            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Calculates fragility scores and blast radius</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--teal)" strokeWidth="2"><path d="M14 13.5V22H6v-7.5M14 13.5 10 9M14 13.5l4-4.5M10 9l4-4.5M10 9l-4-4.5M18 9l-4-4.5M10 9l8-8M10 9l-8-8"></path></svg>
            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Returns structured GO / NO-GO decision</span>
          </div>
        </div>
      </div>

    </div>
  );
}
