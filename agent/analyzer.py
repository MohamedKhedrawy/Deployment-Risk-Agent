"""Fragility scorer — calculates risk scores based on topology and incidents."""

from __future__ import annotations

import logging

from dtmcp.schema import (
    Incident,
    IncidentSeverity,
    Service,
    ServiceMetrics,
    ServiceRisk,
    SLOStatus,
)

logger = logging.getLogger(__name__)


class FragilityScorer:
    """Calculates risk/fragility scores for services based on multiple factors."""

    def __init__(self):
        # Weights for the scoring algorithm
        self.weights = {
            "incidents": 0.40,
            "error_rate": 0.25,
            "slo_burn": 0.25,
            "dependency_depth": 0.10,
        }

    def calculate_service_risk(
        self,
        service: Service,
        incidents: list[Incident],
        metrics: ServiceMetrics,
        slos: list[SLOStatus],
        depth: int,
    ) -> ServiceRisk:
        """Calculate the overall fragility score for a single service."""

        factors = []
        score = 0.0

        # 1. Incident History (0.40)
        incident_score = 0.0
        if incidents:
            # Weight incidents by severity and recency (simplified here to severity)
            severity_weights = {
                IncidentSeverity.AVAILABILITY: 1.0,
                IncidentSeverity.ERROR: 0.7,
                IncidentSeverity.SLOWDOWN: 0.4,
                IncidentSeverity.RESOURCE: 0.3,
                IncidentSeverity.CUSTOM: 0.2,
            }

            total_weight = sum(severity_weights.get(inc.severity, 0.5) for inc in incidents)
            # Normalize somewhat (e.g., 2 critical incidents = max score)
            incident_score = min(1.0, total_weight / 2.0)

            factors.append(f"{len(incidents)} recent incidents (score: {incident_score:.2f})")
        else:
            factors.append("No recent incidents")

        # 2. Current Error Rate (0.25)
        # Assuming an error rate > 0.05 (5%) is very bad
        error_score = min(1.0, metrics.error_rate / 0.05)
        if metrics.error_rate > 0.01:
            factors.append(f"Elevated error rate: {metrics.error_rate*100:.1f}%")

        # 3. SLO Burn Rate (0.20)
        slo_score = 0.0
        service_slos = [s for s in slos if service.name.lower() in s.name.lower()]
        if service_slos:
            worst_slo = min(service_slos, key=lambda s: s.error_budget_remaining)
            if worst_slo.status == "BREACHED":
                slo_score = 1.0
                factors.append(f"SLO breached: {worst_slo.name}")
            elif worst_slo.status == "WARNING" or worst_slo.error_budget_remaining < 20:
                slo_score = 0.6 + (0.4 * (20 - worst_slo.error_budget_remaining) / 20)
                factors.append(f"SLO at risk: {worst_slo.name} ({worst_slo.error_budget_remaining}% budget left)")

        # 4. Dependency Depth (0.15)
        # Closer to the root change = higher risk
        # depth 0 = the changed service itself
        depth_score = max(0.0, 1.0 - (depth * 0.2))

        # Calculate final weighted score
        score = (
            (incident_score * self.weights["incidents"]) +
            (error_score * self.weights["error_rate"]) +
            (slo_score * self.weights["slo_burn"]) +
            (depth_score * self.weights["dependency_depth"])
        )

        return ServiceRisk(
            entity_id=service.entity_id,
            name=service.name,
            fragility_score=round(score, 3),
            incident_count_30d=len(incidents),
            current_error_rate=metrics.error_rate,
            slo_burn_rate=slo_score, # Proxying burn rate with slo_score for now
            dependency_depth=depth,
            risk_factors=factors,
        )
