import React from 'react';

export default function ServiceHealthList({ services }) {
  if (!services || services.length === 0) return null;

  return (
    <div>
      <div style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '8px', letterSpacing: '0.05em' }}>
        Service health
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
        {services.map((svc, idx) => {
          const isCritical = svc.health_status === 'critical';
          const isDegraded = svc.health_status === 'degraded';
          const isHealthy = svc.health_status === 'healthy';

          let bg = 'var(--bg-surface)';
          let border = 'var(--border)';
          let dotColor = 'var(--green)';
          let scoreColor = 'var(--green)';
          let fillColor = 'var(--green)';
          
          if (isDegraded) {
            bg = '#1a1500'; border = '#5a3d00'; dotColor = 'var(--amber)';
          }
          if (isCritical) {
            bg = '#1a0f0f'; border = 'var(--red-border)'; dotColor = 'var(--red)';
          }

          if (svc.fragility_score >= 0.35 && svc.fragility_score <= 0.65) {
            scoreColor = 'var(--amber)'; fillColor = 'var(--amber)';
          } else if (svc.fragility_score > 0.65) {
            scoreColor = 'var(--red)'; fillColor = 'var(--red)';
          }

          const hasActiveIncident = isCritical && svc.last_incident && svc.last_incident.startsWith('ACTIVE');
          const errorRate = (svc.current_error_rate || 0).toFixed(3);
          
          let metaText = `${svc.incident_count_30d || 0} incidents in 30d · error rate ${errorRate}%`;
          if (svc.incident_count_30d === 0) {
            metaText = `0 incidents · error rate ${errorRate}% · healthy`;
          } else if (svc.last_incident) {
            metaText += ` · last: ${svc.last_incident}`;
          }

          return (
            <div key={idx} style={{
              background: bg,
              border: `0.5px solid ${border}`,
              borderRadius: 'var(--radius-md)',
              padding: '10px 12px',
              display: 'flex',
              alignItems: 'center',
              gap: '10px'
            }}>
              <div style={{
                width: '8px', height: '8px', borderRadius: '50%', background: dotColor, flexShrink: 0,
                animation: isCritical ? 'pulse-dot 1.5s infinite' : 'none'
              }}></div>
              
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: '12px', fontWeight: 500, color: 'var(--text-primary)' }}>
                  {svc.name}
                </div>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                  {metaText}
                </div>
              </div>

              {hasActiveIncident && (
                <div style={{
                  background: 'rgba(248,81,73,0.2)',
                  border: '0.5px solid var(--red)',
                  borderRadius: '4px',
                  padding: '2px 6px',
                  fontSize: '10px',
                  color: 'var(--red)',
                  fontWeight: 500,
                  whiteSpace: 'nowrap',
                  animation: 'pulse-dot 1.5s infinite',
                  flexShrink: 0
                }}>
                  ACTIVE INCIDENT
                </div>
              )}

              <div style={{ width: '80px', height: '4px', background: 'var(--bg-elevated)', borderRadius: '2px', flexShrink: 0, overflow: 'hidden' }}>
                <div style={{ width: `${(svc.fragility_score || 0) * 100}%`, height: '100%', background: fillColor }}></div>
              </div>

              <div style={{ minWidth: '24px', textAlign: 'right', fontSize: '11px', fontWeight: 500, color: scoreColor, flexShrink: 0 }}>
                {(svc.fragility_score || 0).toFixed(2)}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
