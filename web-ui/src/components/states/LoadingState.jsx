import React, { useState, useEffect } from 'react';
import { analyzeFeature } from '../../api';

export default function LoadingState({ feature, setAnalysisState, setResultData }) {
  const [activeStep, setActiveStep] = useState(0);

  const steps = [
    { title: "Input validated", sub: "Feature description confirmed as valid deployment request" },
    { title: "Service topology mapped", sub: "Identified N affected services in environment" },
    { title: "Querying incident history", sub: "Fetching 30-day problem logs from Dynatrace..." },
    { title: "Analyzing error rates and SLOs", sub: "Reading live metrics via Dynatrace MCP..." },
    { title: "Calculating fragility scores", sub: "Applying weighted scoring model..." },
    { title: "Synthesizing decision", sub: "Gemini 2.5 Flash generating recommendation..." }
  ];

  useEffect(() => {
    const startTime = Date.now();
    const timings = [0, 300, 700, 1400, 2100, 2800];
    
    let timers = timings.map((t, i) => setTimeout(() => setActiveStep(i), t));

    analyzeFeature(feature)
      .then(data => {
        const elapsed = Date.now() - startTime;
        const wait = Math.max(0, 3200 - elapsed);
        setTimeout(() => {
          setResultData(data);
          setAnalysisState('result');
        }, wait);
      })
      .catch(err => {
        console.error(err);
        setAnalysisState('idle'); // Or error state
      });

    return () => timers.forEach(clearTimeout);
  }, [feature, setAnalysisState, setResultData]);

  return (
    <div>
      <div style={{ fontSize: '15px', color: 'var(--text-primary)', fontWeight: 500 }}>Analyzing deployment risk...</div>
      <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '16px' }}>
        {feature.length > 60 ? feature.slice(0, 60) + '...' : feature}
      </div>

      <div style={{
        background: 'var(--bg-surface)',
        border: '0.5px solid var(--border)',
        borderRadius: 'var(--radius-lg)',
        padding: '16px 18px',
        display: 'flex',
        flexDirection: 'column'
      }}>
        {steps.map((step, idx) => {
          const isDone = idx < activeStep;
          const isActive = idx === activeStep;
          const isPending = idx > activeStep;

          return (
            <div key={idx} style={{ position: 'relative', display: 'flex', gap: '16px', minHeight: '60px' }}>
              {/* Connector line */}
              {idx < steps.length - 1 && (
                <div style={{
                  position: 'absolute',
                  left: '11px',
                  top: '32px',
                  height: 'calc(100% - 12px)',
                  width: '1px',
                  background: isDone ? 'var(--bg-overlay)' : 'var(--border-subtle)'
                }} />
              )}
              
              {/* Circle */}
              <div style={{
                width: '24px',
                height: '24px',
                borderRadius: '50%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0,
                marginTop: '4px',
                background: isDone ? 'var(--teal)' : isActive ? 'var(--blue)' : 'var(--bg-elevated)',
                animation: isActive ? 'pulse-ring 2s infinite' : 'none',
                color: isPending ? 'var(--text-muted)' : 'white',
                fontSize: '11px'
              }}>
                {isDone ? '✓' : isPending ? (idx + 1) : ''}
              </div>

              {/* Text */}
              <div style={{ display: 'flex', flexDirection: 'column', marginTop: '6px' }}>
                <span style={{ 
                  fontSize: '13px', 
                  fontWeight: isActive || isDone ? 500 : 400,
                  color: isActive ? 'white' : isDone ? 'var(--text-muted)' : 'var(--text-hint)'
                }}>
                  {step.title}
                </span>
                <span style={{
                  fontSize: '12px',
                  color: isPending ? 'var(--text-hint)' : 'var(--text-muted)',
                  marginTop: '2px'
                }}>
                  {step.sub}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
