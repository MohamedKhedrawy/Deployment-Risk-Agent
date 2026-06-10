import React from 'react';
import DecisionBanner from '../result-parts/DecisionBanner';
import MetricsRow from '../result-parts/MetricsRow';
import ServiceHealthList from '../result-parts/ServiceHealthList';
import ConditionsBox from '../result-parts/ConditionsBox';
import ReasoningBox from '../result-parts/ReasoningBox';
import TopologyGraph from '../result-parts/TopologyGraph';

export default function ResultState({ data }) {
  if (!data) return null;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
      <DecisionBanner 
        decision={data.decision} 
        riskScore={data.risk_score} 
        riskLevel={data.risk_score} 
        feature={data.feature} 
      />
      
      <MetricsRow 
        affectedServicesCount={data.affected_services?.length || 0}
        blastRadiusPct={data.blast_radius?.user_impact_percentage || 0}
        incidentCount30d={data.affected_services?.reduce((acc, svc) => acc + (svc.incident_count_30d || 0), 0) || 0}
      />

      <ServiceHealthList services={data.affected_services || []} />

      {data.decision === 'GO_WITH_CONDITIONS' && data.deploy_strategy?.conditions?.length > 0 && (
        <ConditionsBox conditions={data.deploy_strategy.conditions} />
      )}

      <ReasoningBox 
        reasoning={data.decision_rationale} 
        decision={data.decision} 
        topRisks={data.top_risks} 
      />

      <TopologyGraph 
        topology={data.raw_topology_data} 
        services={data.affected_services || []} 
      />
    </div>
  );
}
