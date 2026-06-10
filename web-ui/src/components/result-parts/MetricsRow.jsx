import React from 'react';

export default function MetricsRow({ affectedServicesCount, blastRadiusPct, incidentCount30d }) {
  
  const getColor = (type, val) => {
    if (type === 'services') {
      if (val <= 2) return 'var(--green)';
      if (val <= 4) return 'var(--amber)';
      return 'var(--red)';
    }
    if (type === 'blast') {
      if (val < 10) return 'var(--green)';
      if (val <= 40) return 'var(--amber)';
      return 'var(--red)';
    }
    if (type === 'incidents') {
      if (val === 0) return 'var(--green)';
      if (val <= 2) return 'var(--amber)';
      return 'var(--red)';
    }
    return 'var(--text-primary)';
  };

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px' }}>
      <div style={{ background: 'var(--bg-surface)', border: '0.5px solid var(--border)', borderRadius: 'var(--radius-md)', padding: '10px 12px' }}>
        <div style={{ fontSize: '20px', fontWeight: 500, color: getColor('services', affectedServicesCount) }}>
          {affectedServicesCount}
        </div>
        <div style={{ fontSize: '10px', textTransform: 'uppercase', color: 'var(--text-muted)' }}>
          Services affected
        </div>
      </div>

      <div style={{ background: 'var(--bg-surface)', border: '0.5px solid var(--border)', borderRadius: 'var(--radius-md)', padding: '10px 12px' }}>
        <div style={{ fontSize: '20px', fontWeight: 500, color: getColor('blast', blastRadiusPct) }}>
          {blastRadiusPct.toFixed(1)}%
        </div>
        <div style={{ fontSize: '10px', textTransform: 'uppercase', color: 'var(--text-muted)' }}>
          Blast radius
        </div>
      </div>

      <div style={{ background: 'var(--bg-surface)', border: '0.5px solid var(--border)', borderRadius: 'var(--radius-md)', padding: '10px 12px' }}>
        <div style={{ fontSize: '20px', fontWeight: 500, color: getColor('incidents', incidentCount30d) }}>
          {incidentCount30d}
        </div>
        <div style={{ fontSize: '10px', textTransform: 'uppercase', color: 'var(--text-muted)' }}>
          Incidents (30d)
        </div>
      </div>
    </div>
  );
}
