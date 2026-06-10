"""Report builder — generates structured risk reports with reasoning chains."""

from __future__ import annotations

import logging
from datetime import datetime

from dtmcp.schema import (
    BlastRadius,
    Decision,
    DeployStrategy,
    RiskItem,
    RiskLevel,
    RiskReport,
    ReasoningStep,
    ServiceRisk,
    ServiceTopology,
    Incident,
    SLOStatus,
)

logger = logging.getLogger(__name__)


class ReportBuilder:
    """Builds the final RiskReport from analysis results."""

    def build(
        self,
        feature: str,
        topology: ServiceTopology,
        affected_services: list[ServiceRisk],
        blast_radius: BlastRadius,
        incidents: list[Incident],
        slos: list[SLOStatus],
        reasoning_steps: list[ReasoningStep],
    ) -> RiskReport:
        """Assemble the final risk report."""

        risk_score = self._determine_risk_level(affected_services, blast_radius, slos)
        top_risks = self._identify_top_risks(affected_services, incidents, slos)
        deploy_strategy = self._recommend_strategy(risk_score, blast_radius, affected_services)
        decision, rationale = self._make_decision(risk_score, blast_radius, top_risks, slos)

        # Build topology data for UI rendering
        raw_topology = self._build_topology_for_ui(topology, affected_services)

        return RiskReport(
            feature=feature,
            timestamp=datetime.now(tz=None),
            risk_score=risk_score,
            decision=decision,
            decision_rationale=rationale,
            blast_radius=blast_radius,
            top_risks=top_risks[:3],
            deploy_strategy=deploy_strategy,
            affected_services=affected_services,
            reasoning_chain=reasoning_steps,
            raw_topology_data=raw_topology,
        )

    def _determine_risk_level(
        self,
        services: list[ServiceRisk],
        blast: BlastRadius,
        slos: list[SLOStatus],
    ) -> RiskLevel:
        """Determine the overall risk level from all signals."""
        if not services:
            return RiskLevel.LOW

        max_fragility = max(s.fragility_score for s in services)
        avg_fragility = sum(s.fragility_score for s in services) / len(services)

        # Check for SLO breaches
        has_breach = any(s.status == "BREACHED" for s in slos)

        # Critical: any SLO breached + high fragility + wide blast radius
        if has_breach and max_fragility > 0.6 and blast.user_impact_percentage > 50:
            return RiskLevel.CRITICAL

        # High: significant fragility or broad impact
        if max_fragility > 0.5 or blast.user_impact_percentage > 20:
            return RiskLevel.HIGH

        # Medium: significant incident history or moderate fragility
        total_incidents = sum(s.incident_count_30d for s in services)
        if total_incidents > 1 or avg_fragility > 0.2:
            return RiskLevel.MEDIUM

        return RiskLevel.LOW

    def _identify_top_risks(
        self,
        services: list[ServiceRisk],
        incidents: list[Incident],
        slos: list[SLOStatus],
    ) -> list[RiskItem]:
        """Identify and rank the top risks."""
        risks: list[RiskItem] = []
        rank = 1

        # Sort services by fragility (most fragile first)
        sorted_services = sorted(services, key=lambda s: s.fragility_score, reverse=True)

        for svc in sorted_services[:5]:
            if svc.fragility_score < 0.1:
                continue

            # Determine severity from fragility
            if svc.fragility_score > 0.7:
                severity = RiskLevel.CRITICAL
            elif svc.fragility_score > 0.5:
                severity = RiskLevel.HIGH
            elif svc.fragility_score > 0.3:
                severity = RiskLevel.MEDIUM
            else:
                severity = RiskLevel.LOW

            # Build a descriptive risk
            description_parts = []
            mitigation_parts = []

            if svc.incident_count_30d > 0:
                description_parts.append(
                    f"{svc.incident_count_30d} incidents in the last 30 days"
                )
                mitigation_parts.append("Review and fix root causes before deploying")

            if svc.current_error_rate > 0.01:
                description_parts.append(
                    f"current error rate {svc.current_error_rate*100:.1f}%"
                )
                mitigation_parts.append("Investigate elevated errors first")

            # Check SLO for this service
            svc_slos = [s for s in slos if svc.name.lower() in s.name.lower()]
            for slo in svc_slos:
                if slo.status in ("BREACHED", "WARNING"):
                    description_parts.append(
                        f"SLO '{slo.name}' at {slo.current}% (target: {slo.target}%)"
                    )
                    mitigation_parts.append(
                        f"Restore {slo.name} before adding load"
                    )

            if svc.risk_factors:
                for factor in svc.risk_factors:
                    if factor not in description_parts:
                        description_parts.append(factor)

            description = "; ".join(description_parts) if description_parts else (
                f"Fragility score {svc.fragility_score:.2f} indicates elevated risk"
            )
            mitigation = ". ".join(mitigation_parts) if mitigation_parts else (
                "Monitor closely during rollout"
            )

            risks.append(RiskItem(
                rank=rank,
                title=f"{svc.name} instability",
                description=description,
                severity=severity,
                affected_service=svc.entity_id,
                mitigation=mitigation,
            ))
            rank += 1

        return risks

    def _recommend_strategy(
        self,
        risk_level: RiskLevel,
        blast: BlastRadius,
        services: list[ServiceRisk],
    ) -> DeployStrategy:
        """Recommend a deployment strategy based on risk assessment."""

        if risk_level == RiskLevel.CRITICAL:
            return DeployStrategy(
                strategy="Hold — do not deploy",
                canary_percentage=None,
                recommended_window=None,
                monitor_metrics=[
                    f"{s.name} error rate" for s in services[:3]
                ],
                conditions=[
                    "Resolve all active incidents",
                    "Restore breached SLOs to healthy state",
                    "Re-assess after fixes are deployed",
                ],
            )

        if risk_level == RiskLevel.HIGH:
            return DeployStrategy(
                strategy="Canary rollout — off-peak hours",
                canary_percentage=5.0,
                recommended_window="After 8pm local time (low traffic)",
                monitor_metrics=[
                    f"{s.name} error rate" for s in services[:2]
                ] + [
                    f"{s.name} p99 latency" for s in services[:2]
                ],
                conditions=[
                    "Deploy after peak hours",
                    f"Start with {5}% canary traffic",
                    "Automated rollback if error rate exceeds 2%",
                    "Watch for 30 minutes before scaling up",
                ],
            )

        if risk_level == RiskLevel.MEDIUM:
            return DeployStrategy(
                strategy="Canary rollout — standard",
                canary_percentage=10.0,
                recommended_window=None,
                monitor_metrics=[
                    f"{s.name} error rate" for s in services[:2]
                ],
                conditions=[
                    "Start with 10% canary traffic",
                    "Monitor for 15 minutes before full rollout",
                ],
            )

        # LOW risk
        return DeployStrategy(
            strategy="Full rollout",
            canary_percentage=None,
            recommended_window=None,
            monitor_metrics=[
                f"{s.name} error rate" for s in services[:1]
            ] if services else [],
            conditions=[],
        )

    def _make_decision(
        self,
        risk_level: RiskLevel,
        blast: BlastRadius,
        top_risks: list[RiskItem],
        slos: list[SLOStatus],
    ) -> tuple[Decision, str]:
        """Make the final GO/NO-GO decision with rationale."""

        has_breach = any(s.status == "BREACHED" for s in slos)

        if risk_level == RiskLevel.CRITICAL:
            reasons = []
            if has_breach:
                breached = [s for s in slos if s.status == "BREACHED"]
                reasons.append(
                    f"{len(breached)} SLO(s) already breached"
                )
            if blast.user_impact_percentage > 50:
                reasons.append(
                    f"blast radius covers {blast.user_impact_percentage:.0f}% of users"
                )
            if top_risks:
                reasons.append(f"critical risk: {top_risks[0].title}")
            return (
                Decision.NO_GO,
                f"NO-GO — {'; '.join(reasons)}. Deploying now would likely cause a user-facing outage.",
            )

        if risk_level == RiskLevel.HIGH:
            conditions = []
            if blast.user_impact_percentage > 10:
                conditions.append(
                    f"cap at 5% canary (blast radius: {blast.user_impact_percentage:.0f}% of users)"
                )
            conditions.append("deploy after peak hours")
            if top_risks:
                conditions.append(
                    f"monitor {top_risks[0].affected_service.split('-')[-1]} closely"
                )
            return (
                Decision.GO_WITH_CONDITIONS,
                f"GO WITH CONDITIONS — {'; '.join(conditions)}.",
            )

        if risk_level == RiskLevel.MEDIUM:
            return (
                Decision.GO_WITH_CONDITIONS,
                "GO WITH CONDITIONS — use canary rollout at 10% and monitor for 15 minutes.",
            )

        return (
            Decision.GO,
            "GO — all services are healthy, no recent incidents, SLOs within budget.",
        )

    def _build_topology_for_ui(
        self,
        topology: ServiceTopology,
        affected_services: list[ServiceRisk],
    ) -> dict:
        """Build a topology dict suitable for UI rendering."""
        affected_ids = {s.entity_id for s in affected_services}

        nodes = []
        edges = []

        for svc in topology.services:
            risk = next(
                (s for s in affected_services if s.entity_id == svc.entity_id),
                None,
            )
            nodes.append({
                "id": svc.entity_id,
                "label": svc.name,
                "type": svc.service_type.value,
                "affected": svc.entity_id in affected_ids,
                "fragility": risk.fragility_score if risk else 0.0,
            })

            for dep in svc.dependencies:
                edges.append({
                    "from": svc.entity_id,
                    "to": dep,
                })

        return {"nodes": nodes, "edges": edges}
