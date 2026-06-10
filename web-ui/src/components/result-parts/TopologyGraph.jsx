import React from 'react';

export default function TopologyGraph({ topology, services }) {
  if (!topology || !topology.nodes || topology.nodes.length === 0) return null;

  // Build simple linear chain representation from edges
  // 1. Find root nodes (no incoming edges)
  const incomingCounts = {};
  topology.nodes.forEach(n => {
    incomingCounts[n.id || n] = 0;
  });
  
  if (topology.edges) {
    topology.edges.forEach(e => {
      const to = Array.isArray(e) ? e[1] : e.to;
      incomingCounts[to] = (incomingCounts[to] || 0) + 1;
    });
  }
  
  // Start from any root node, or first node if circular
  let roots = Object.keys(incomingCounts).filter(k => incomingCounts[k] === 0);
  if (roots.length === 0) roots = [(topology.nodes[0].id || topology.nodes[0])];
  
  // Just build a simple chain by following first outgoing edge
  const chain = [];
  const visited = new Set();
  
  let current = roots[0];
  while (current && !visited.has(current)) {
    chain.push(current);
    visited.add(current);
    
    // Find next
    let nextNode = null;
    if (topology.edges) {
      const outgoing = topology.edges.find(e => (Array.isArray(e) ? e[0] : e.from) === current);
      if (outgoing) {
        nextNode = Array.isArray(outgoing) ? outgoing[1] : outgoing.to;
      }
    }
    current = nextNode;
  }
  
  // Map back to full node objects if available, else strings
  const chainNodes = chain.map(nodeId => {
    const topoNode = topology.nodes.find(n => (n.id || n) === nodeId) || { id: nodeId, label: nodeId };
    const svcHealth = services.find(s => s.name === (topoNode.label || topoNode.id || topoNode));
    return {
      id: topoNode.id || topoNode,
      label: topoNode.label || topoNode.id || topoNode,
      health: svcHealth?.health_status || 'healthy'
    };
  });

  return (
    <div style={{
      background: 'var(--bg-surface)',
      border: '0.5px solid var(--border)',
      borderRadius: 'var(--radius-md)',
      padding: '12px 14px',
      overflowX: 'auto'
    }}>
      <div style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '10px', letterSpacing: '0.05em' }}>
        Dependency topology
      </div>
      
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', minWidth: 'min-content', paddingBottom: '4px' }}>
        {chainNodes.map((node, idx) => {
          let bg, border, color, animation;
          
          if (node.health === 'critical') {
            bg = 'var(--red-bg)'; border = 'var(--red)'; color = 'var(--red)';
            animation = 'pulse-border 1.5s infinite';
          } else if (node.health === 'degraded') {
            bg = 'var(--amber-bg)'; border = 'var(--amber-border)'; color = 'var(--amber)';
          } else {
            bg = 'var(--green-bg)'; border = 'var(--green-border)'; color = 'var(--green)';
          }
          
          return (
            <React.Fragment key={idx}>
              <div style={{
                borderRadius: 'var(--radius-sm)',
                padding: '6px 10px',
                fontSize: '10px',
                fontWeight: 500,
                border: `0.5px solid ${border}`,
                background: bg,
                color: color,
                whiteSpace: 'nowrap',
                animation: animation
              }}>
                {node.label}
              </div>
              
              {idx < chainNodes.length - 1 && (
                <div style={{ color: 'var(--text-hint)', fontSize: '16px', padding: '0 6px', flexShrink: 0 }}>
                  →
                </div>
              )}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
}
