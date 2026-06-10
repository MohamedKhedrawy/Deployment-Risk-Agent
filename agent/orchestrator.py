"""Orchestrator — now delegates all data fetching to the ADK agent via MCP.

The AnalysisPipeline class is kept for backward compatibility with tests,
but the live execution path runs through canary_agent/mcp_runner.py.
"""

from __future__ import annotations

import logging

from agent.validator import InputValidator
from dtmcp.schema import (
    BlastRadius,
    Decision,
    DeployStrategy,
    ReasoningStep,
    RiskLevel,
    RiskReport,
)

logger = logging.getLogger(__name__)


class AnalysisPipeline:
    """Thin wrapper retained for test compatibility.

    In production, api/main.py calls canary_agent.mcp_runner.run_agent()
    directly, which invokes the ADK agent with the Dynatrace MCP toolset.
    """

    def __init__(self, client=None):
        self.client = client  # Kept for test injection
        self.validator = InputValidator()

    async def run(self, feature_description: str) -> RiskReport:
        """Run the analysis pipeline.

        If a client is injected (tests), uses it directly.
        Otherwise delegates to the MCP runner.
        """
        # Step 0: Validate
        is_valid, reason = await self.validator.check(feature_description)
        if not is_valid:
            return RiskReport(
                feature=feature_description,
                decision=Decision.NO_GO,
                decision_rationale=f"Input rejected: {reason}",
                risk_score=RiskLevel.LOW,
                blast_radius=BlastRadius(),
                deploy_strategy=DeployStrategy(strategy="Halted", conditions=[reason]),
                reasoning_chain=[
                    ReasoningStep(
                        step_number=0,
                        title="Input Validation Failed",
                        action="Evaluated the feature description for validity",
                        findings=f"Rejected: {reason}",
                        data={"input": feature_description},
                    )
                ],
                raw_topology_data={},
            )

        # If a test client was injected, use it directly (simplified path)
        if self.client is not None:
            return await self._run_with_client(feature_description)

        # Production path: delegate to ADK MCP runner
        from canary_agent.mcp_runner import run_agent
        return await run_agent(feature_description)

    async def _run_with_client(self, feature_description: str) -> RiskReport:
        """Simplified pipeline path used in tests with mock client."""
        topology = await self.client.get_topology()
        affected_ids = await self._identify_affected_services(feature_description, topology)
        all_incidents = await self.client.get_recent_incidents()
        slos = await self.client.get_slo_status()

        from agent.analyzer import FragilityScorer
        from agent.simulator import BlastRadiusSimulator
        from agent.report import ReportBuilder
        from dtmcp.schema import ServiceMetrics, ReasoningStep

        scorer = FragilityScorer()
        simulator = BlastRadiusSimulator()
        report_builder = ReportBuilder()

        metrics_map = {}
        for eid in affected_ids:
            metrics_map[eid] = await self.client.get_service_metrics(eid)

        service_risks = []
        for idx, eid in enumerate(affected_ids):
            svc = topology.get_service(eid)
            if not svc:
                continue
            svc_incidents = [i for i in all_incidents if eid in i.affected_entities]
            svc_metrics = metrics_map.get(eid, ServiceMetrics(entity_id=eid))
            risk = scorer.calculate_service_risk(
                service=svc, incidents=svc_incidents,
                metrics=svc_metrics, slos=slos, depth=idx,
            )
            service_risks.append(risk)

        primary = affected_ids[0] if affected_ids else None
        if primary:
            blast_radius = simulator.simulate(
                target_service_id=primary, topology=topology,
                all_incidents=all_incidents, metrics_map=metrics_map, slos=slos,
            )
        else:
            blast_radius = BlastRadius()

        service_risks.sort(key=lambda r: r.fragility_score, reverse=True)

        reasoning = [
            ReasoningStep(
                step_number=1, title="Map the Topology",
                action="Queried topology via test client",
                findings=f"Found {len(topology.services)} services. Affected: {len(affected_ids)}.",
                data={"total_services": len(topology.services), "affected_service_ids": affected_ids},
            ),
            ReasoningStep(
                step_number=2, title="Check Historical Health",
                action="Pulled incidents, metrics, and SLOs",
                findings=f"{len(all_incidents)} incidents. {len(slos)} SLOs.",
                data={"total_incidents": len(all_incidents)},
            ),
            ReasoningStep(
                step_number=3, title="Assess the Risk",
                action="Scored fragility and simulated blast radius",
                findings=f"Blast radius: {blast_radius.total_services_affected} services.",
                data={"blast_radius_services": blast_radius.total_services_affected},
            ),
        ]

        return report_builder.build(
            feature=feature_description, topology=topology,
            affected_services=service_risks, blast_radius=blast_radius,
            incidents=all_incidents, slos=slos, reasoning_steps=reasoning,
        )

    async def _identify_affected_services(self, feature_description, topology):
        """Identify affected services via LLM or fall back to all services."""
        if not topology.services:
            return []
        try:
            from agent.llm_client import llm_client
            service_list = [
                f"ID: {s.entity_id} | Name: {s.name} | Tags: {s.tags}"
                for s in topology.services[:50]
            ]
            prompt = (
                "You are an SRE. Given the feature description, return ONLY a "
                "comma-separated list of Service IDs (e.g., SERVICE-ABC123) that "
                f"are most likely impacted.\n\nFeature: {feature_description}\n\n"
                "Services:\n" + "\n".join(service_list) +
                "\n\nOutput ONLY the Service IDs, nothing else."
            )
            response = llm_client.generate_content(model="gemini-2.5-flash", contents=prompt)
            text = response.text if response.text else ""
            raw_ids = [s.strip() for s in text.split(",") if s.strip()]
            matched = [sid for sid in raw_ids if topology.get_service(sid)]
            if matched:
                return matched
        except Exception as e:
            logger.warning(f"LLM service mapping failed (using all): {e}")
        return [s.entity_id for s in topology.services[:3]]
