"""Mock scenarios for DEMO_MODE=true.

Three pre-configured scenarios that return full RiskReport objects identical
in structure to the live pipeline output. The frontend renders these
identically to real Dynatrace data.
"""

from __future__ import annotations

from datetime import datetime, timezone

from dtmcp.schema import (
    BlastRadius,
    Decision,
    DeployStrategy,
    RiskItem,
    RiskLevel,
    RiskReport,
    ReasoningStep,
    ServiceRisk,
)

_NOW = lambda: datetime.now(timezone.utc)  # noqa: E731


# ---------------------------------------------------------------------------
# Scenario 1 — SAFE (GO)
# ---------------------------------------------------------------------------

def _safe_scenario(feature: str) -> RiskReport:
    services = [
        ServiceRisk(
            entity_id="SERVICE-FRONTEND001",
            name="frontend-service",
            fragility_score=0.06,
            incident_count_30d=0,
            current_error_rate=0.0008,
            slo_burn_rate=0.0,
            dependency_depth=0,
            risk_factors=["No recent incidents", "Error rate 0.08% — nominal"],
        ),
        ServiceRisk(
            entity_id="SERVICE-PREFS001",
            name="user-preferences-service",
            fragility_score=0.09,
            incident_count_30d=0,
            current_error_rate=0.0010,
            slo_burn_rate=0.0,
            dependency_depth=1,
            risk_factors=["No recent incidents", "SLO healthy at 99.97%"],
        ),
    ]
    return RiskReport(
        feature=feature,
        timestamp=_NOW(),
        risk_score=RiskLevel.LOW,
        decision=Decision.GO,
        decision_rationale=(
            "GO — Both affected services are healthy with zero incidents in the last "
            "30 days. Error rates are nominal (<0.1%). SLOs are well within budget. "
            "A dark mode toggle carries no stateful risk and touches no payment or "
            "auth critical paths."
        ),
        blast_radius=BlastRadius(
            total_services_affected=2,
            user_impact_percentage=4.0,
            critical_path_services=[],
            affected_services=services,
        ),
        top_risks=[],
        deploy_strategy=DeployStrategy(
            strategy="Full rollout",
            canary_percentage=None,
            recommended_window=None,
            monitor_metrics=["frontend-service error rate", "user-preferences-service latency p95"],
            conditions=[],
        ),
        affected_services=services,
        reasoning_chain=[
            ReasoningStep(
                step_number=1,
                title="Map the Topology",
                action="Queried Dynatrace service topology via MCP",
                findings="Feature touches frontend-service (UI layer) and user-preferences-service (persistence). No auth or payment path involvement.",
                data={"total_services": 2, "affected_service_ids": ["SERVICE-FRONTEND001", "SERVICE-PREFS001"]},
            ),
            ReasoningStep(
                step_number=2,
                title="Check Historical Health",
                action="Pulled incident history and metrics for all affected services",
                findings="0 incidents in 30 days across both services. Error rates <0.1%. SLOs at 99.97% and 99.94%.",
                data={"total_incidents": 0, "active_incidents": 0},
            ),
            ReasoningStep(
                step_number=3,
                title="Assess the Risk",
                action="Calculated fragility scores",
                findings="Max fragility score: 0.09 (LOW). Blast radius: 4% of users.",
                data={"max_fragility": 0.09, "blast_radius_pct": 4.0},
            ),
            ReasoningStep(
                step_number=4,
                title="GO/NO-GO Decision",
                action="Synthesized findings into deployment recommendation",
                findings="Decision: GO. Risk: Low. Full rollout approved.",
                data={"decision": "GO", "risk_level": "Low", "strategy": "Full rollout"},
            ),
        ],
        raw_topology_data={
            "nodes": [
                {"id": "SERVICE-FRONTEND001", "label": "frontend-service", "type": "SERVICE", "affected": True, "fragility": 0.06},
                {"id": "SERVICE-PREFS001", "label": "user-preferences-service", "type": "SERVICE", "affected": True, "fragility": 0.09},
            ],
            "edges": [{"from": "SERVICE-FRONTEND001", "to": "SERVICE-PREFS001"}],
        },
        notebook_url=None,
        slack_notified=False,
        demo_mode=True,
    )


# ---------------------------------------------------------------------------
# Scenario 2 — RISKY (GO WITH CONDITIONS)
# ---------------------------------------------------------------------------

def _risky_scenario(feature: str) -> RiskReport:
    services = [
        ServiceRisk(
            entity_id="SERVICE-CHECKOUT001",
            name="checkout-service",
            fragility_score=0.34,
            incident_count_30d=1,
            current_error_rate=0.0080,
            slo_burn_rate=0.1,
            dependency_depth=0,
            risk_factors=["1 incident in last 30 days", "Error rate 0.8%"],
        ),
        ServiceRisk(
            entity_id="SERVICE-PAYMENT001",
            name="payment-service",
            fragility_score=0.61,
            incident_count_30d=3,
            current_error_rate=0.0230,
            slo_burn_rate=0.75,
            dependency_depth=1,
            risk_factors=[
                "3 incidents in last 30 days",
                "Error rate 2.3% — elevated",
                "SLO at 94.2% — burning fast",
            ],
        ),
        ServiceRisk(
            entity_id="SERVICE-LOYALTY001",
            name="loyalty-service",
            fragility_score=0.22,
            incident_count_30d=0,
            current_error_rate=0.0015,
            slo_burn_rate=0.0,
            dependency_depth=1,
            risk_factors=["No recent incidents", "New service — low baseline data"],
        ),
        ServiceRisk(
            entity_id="SERVICE-ORDER001",
            name="order-management-service",
            fragility_score=0.18,
            incident_count_30d=0,
            current_error_rate=0.0010,
            slo_burn_rate=0.0,
            dependency_depth=2,
            risk_factors=["No recent incidents"],
        ),
    ]
    return RiskReport(
        feature=feature,
        timestamp=_NOW(),
        risk_score=RiskLevel.HIGH,
        decision=Decision.GO_WITH_CONDITIONS,
        decision_rationale=(
            "GO WITH CONDITIONS — payment-service has 3 incidents in the last 30 days, "
            "a 2.3% error rate, and its SLO is burning at 94.2% (critical threshold: 95%). "
            "Adding loyalty point logic directly into the checkout flow creates a new "
            "synchronous dependency that could amplify existing payment instability to "
            "23% of user traffic. Deploy with a 5% canary after 10pm UTC only."
        ),
        blast_radius=BlastRadius(
            total_services_affected=4,
            user_impact_percentage=23.0,
            critical_path_services=["payment-service", "checkout-service"],
            affected_services=services,
        ),
        top_risks=[
            RiskItem(
                rank=1,
                title="payment-service SLO near breach",
                description="SLO at 94.2% with 3 incidents in 30 days. Adding checkout coupling amplifies existing instability.",
                severity=RiskLevel.HIGH,
                affected_service="SERVICE-PAYMENT001",
                mitigation="Deploy after payment-service error rate drops below 1% and SLO recovers above 98%.",
            ),
            RiskItem(
                rank=2,
                title="Loyalty service coupling risk",
                description="New synchronous dependency on loyalty-service. If loyalty-service degrades, checkout will cascade.",
                severity=RiskLevel.MEDIUM,
                affected_service="SERVICE-LOYALTY001",
                mitigation="Implement circuit breaker between checkout-service and loyalty-service before deploying.",
            ),
            RiskItem(
                rank=3,
                title="Blast radius covers checkout critical path",
                description="23% of user traffic flows through checkout-service. Any regression affects 1 in 4 users.",
                severity=RiskLevel.MEDIUM,
                affected_service="SERVICE-CHECKOUT001",
                mitigation="Start with 5% canary traffic. Auto-rollback if checkout error rate exceeds 1.5%.",
            ),
        ],
        deploy_strategy=DeployStrategy(
            strategy="Canary rollout — off-peak hours only",
            canary_percentage=5.0,
            recommended_window="After 10pm UTC (low traffic window)",
            monitor_metrics=[
                "payment-service error rate",
                "payment-service p99 latency",
                "checkout-service error rate",
                "loyalty-service response time",
            ],
            conditions=[
                "Deploy after 10pm UTC",
                "Canary to 5% of traffic first",
                "Monitor payment-service error rate for 30 min before full rollout",
                "Have rollback plan ready — target < 5 min rollback time",
            ],
        ),
        affected_services=services,
        reasoning_chain=[
            ReasoningStep(
                step_number=1,
                title="Map the Topology",
                action="Queried Dynatrace service topology via MCP",
                findings="Feature touches checkout-service, payment-service (dependency), loyalty-service (new integration), and order-management-service (downstream). Blast radius covers 23% of user traffic.",
                data={"total_services": 4, "affected_service_ids": ["SERVICE-CHECKOUT001", "SERVICE-PAYMENT001", "SERVICE-LOYALTY001", "SERVICE-ORDER001"]},
            ),
            ReasoningStep(
                step_number=2,
                title="Check Historical Health",
                action="Pulled incident history, error rates, and SLO status for all services",
                findings="payment-service: 3 incidents, 2.3% error rate, SLO at 94.2%. checkout-service: 1 incident, 0.8% error rate. loyalty-service: 0 incidents but new service. order-management: healthy.",
                data={"total_incidents": 4, "active_incidents": 0, "services_at_risk": ["payment-service"]},
            ),
            ReasoningStep(
                step_number=3,
                title="Assess the Risk",
                action="Calculated fragility scores and blast radius",
                findings="Max fragility: 0.61 (payment-service). Blast radius: 23% of users. Critical path: checkout → payment.",
                data={"max_fragility": 0.61, "blast_radius_pct": 23.0},
            ),
            ReasoningStep(
                step_number=4,
                title="GO/NO-GO Decision",
                action="Synthesized findings into deployment recommendation",
                findings="Decision: GO WITH CONDITIONS. Deploy with 5% canary after 10pm UTC. Rollback trigger: payment error rate >1.5%.",
                data={"decision": "GO_WITH_CONDITIONS", "risk_level": "High", "strategy": "Canary 5%"},
            ),
        ],
        raw_topology_data={
            "nodes": [
                {"id": "SERVICE-CHECKOUT001", "label": "checkout-service", "type": "SERVICE", "affected": True, "fragility": 0.34},
                {"id": "SERVICE-PAYMENT001", "label": "payment-service", "type": "SERVICE", "affected": True, "fragility": 0.61},
                {"id": "SERVICE-LOYALTY001", "label": "loyalty-service", "type": "SERVICE", "affected": True, "fragility": 0.22},
                {"id": "SERVICE-ORDER001", "label": "order-management-service", "type": "SERVICE", "affected": True, "fragility": 0.18},
            ],
            "edges": [
                {"from": "SERVICE-CHECKOUT001", "to": "SERVICE-PAYMENT001"},
                {"from": "SERVICE-CHECKOUT001", "to": "SERVICE-LOYALTY001"},
                {"from": "SERVICE-CHECKOUT001", "to": "SERVICE-ORDER001"},
            ],
        },
        notebook_url=None,
        slack_notified=False,
        demo_mode=True,
    )


# ---------------------------------------------------------------------------
# Scenario 3 — FATAL (NO-GO)
# ---------------------------------------------------------------------------

def _fatal_scenario(feature: str) -> RiskReport:
    services = [
        ServiceRisk(
            entity_id="SERVICE-AUTH001",
            name="auth-service",
            fragility_score=0.95,
            incident_count_30d=7,
            current_error_rate=0.0870,
            slo_burn_rate=1.0,
            dependency_depth=0,
            risk_factors=[
                "7 incidents in last 30 days",
                "Error rate 8.7% — critical",
                "SLO at 87% — BREACHED",
                "ACTIVE problem open right now",
            ],
        ),
        ServiceRisk(
            entity_id="SERVICE-GATEWAY001",
            name="api-gateway",
            fragility_score=0.58,
            incident_count_30d=4,
            current_error_rate=0.0310,
            slo_burn_rate=0.5,
            dependency_depth=1,
            risk_factors=["4 incidents in last 30 days", "Error rate 3.1% — elevated"],
        ),
        ServiceRisk(
            entity_id="SERVICE-USER001",
            name="user-service",
            fragility_score=0.22,
            incident_count_30d=1,
            current_error_rate=0.0050,
            slo_burn_rate=0.0,
            dependency_depth=1,
            risk_factors=["1 incident in last 30 days"],
        ),
        ServiceRisk(
            entity_id="SERVICE-SESSION001",
            name="session-manager",
            fragility_score=0.41,
            incident_count_30d=2,
            current_error_rate=0.0120,
            slo_burn_rate=0.3,
            dependency_depth=2,
            risk_factors=["2 incidents", "Degraded status", "Error rate 1.2%"],
        ),
        ServiceRisk(
            entity_id="SERVICE-FRONTEND001",
            name="frontend-service",
            fragility_score=0.30,
            incident_count_30d=1,
            current_error_rate=0.0040,
            slo_burn_rate=0.1,
            dependency_depth=2,
            risk_factors=["Downstream of auth — will inherit auth failures"],
        ),
    ]
    return RiskReport(
        feature=feature,
        timestamp=_NOW(),
        risk_score=RiskLevel.CRITICAL,
        decision=Decision.NO_GO,
        decision_rationale=(
            "NO-GO — auth-service has an ACTIVE incident right now. It has had 7 incidents "
            "in the last 30 days, an 8.7% error rate, and its SLO is breached at 87% "
            "(target: 99.9%). Migrating the OAuth provider during an active incident would "
            "cascade through api-gateway and session-manager to 89% of users, causing a "
            "full authentication outage. This deployment must be halted until the active "
            "incident is resolved and auth-service returns to baseline for 48 hours."
        ),
        blast_radius=BlastRadius(
            total_services_affected=5,
            user_impact_percentage=89.0,
            critical_path_services=["auth-service", "api-gateway", "session-manager"],
            affected_services=services,
        ),
        top_risks=[
            RiskItem(
                rank=1,
                title="auth-service ACTIVE incident",
                description="auth-service has an open incident RIGHT NOW with 8.7% error rate and SLO breached at 87%. Any deployment amplifies this.",
                severity=RiskLevel.CRITICAL,
                affected_service="SERVICE-AUTH001",
                mitigation="Resolve active incident first. Wait 48 hours of stability before re-assessing.",
            ),
            RiskItem(
                rank=2,
                title="89% blast radius — near-total user impact",
                description="auth-service sits on the critical path for 89% of user traffic. A failed OAuth migration would lock out virtually all users.",
                severity=RiskLevel.CRITICAL,
                affected_service="SERVICE-AUTH001",
                mitigation="Migration must be done with a shadow deployment and gradual traffic shift, never a direct cutover.",
            ),
            RiskItem(
                rank=3,
                title="api-gateway cascading failure risk",
                description="api-gateway has 4 incidents and 3.1% error rate. auth-service failure will immediately cascade here.",
                severity=RiskLevel.HIGH,
                affected_service="SERVICE-GATEWAY001",
                mitigation="Implement fallback auth tokens in api-gateway before attempting migration.",
            ),
        ],
        deploy_strategy=DeployStrategy(
            strategy="Hold — do not deploy",
            canary_percentage=None,
            recommended_window=None,
            monitor_metrics=[
                "auth-service error rate (target: <0.5%)",
                "auth-service SLO (target: >99.5%)",
                "auth-service active problems (target: 0)",
            ],
            conditions=[
                "Resolve the currently active incident on auth-service",
                "Wait 48 hours of clean baseline before re-assessing",
                "Restore auth-service SLO above 99.5%",
                "Implement shadow deployment strategy before any OAuth migration",
                "Ensure rollback plan can restore previous OAuth provider within 60 seconds",
            ],
        ),
        affected_services=services,
        reasoning_chain=[
            ReasoningStep(
                step_number=1,
                title="Map the Topology",
                action="Queried Dynatrace service topology via MCP",
                findings="OAuth migration touches auth-service (primary), api-gateway, user-service, session-manager, and frontend-service. auth-service sits on the critical path for 89% of user traffic.",
                data={"total_services": 5, "affected_service_ids": ["SERVICE-AUTH001", "SERVICE-GATEWAY001", "SERVICE-USER001", "SERVICE-SESSION001", "SERVICE-FRONTEND001"]},
            ),
            ReasoningStep(
                step_number=2,
                title="Check Historical Health",
                action="Pulled incident history and current status for all services",
                findings="CRITICAL: auth-service has an ACTIVE open problem. 7 incidents in 30 days, 8.7% error rate, SLO BREACHED at 87%. api-gateway: 4 incidents, 3.1% error rate. session-manager: degraded.",
                data={"total_incidents": 15, "active_incidents": 1, "services_with_active_problems": ["auth-service"]},
            ),
            ReasoningStep(
                step_number=3,
                title="Assess the Risk",
                action="Calculated fragility scores and blast radius",
                findings="auth-service fragility: 0.95 (CRITICAL). Blast radius: 89% of users — near-total outage scenario.",
                data={"max_fragility": 0.95, "blast_radius_pct": 89.0, "active_problems": 1},
            ),
            ReasoningStep(
                step_number=4,
                title="GO/NO-GO Decision",
                action="Synthesized findings — HALT required",
                findings="Decision: NO-GO. Active incident + SLO breach + 89% blast radius = certain production outage. Deployment halted.",
                data={"decision": "NO_GO", "risk_level": "Critical", "strategy": "Hold"},
            ),
        ],
        raw_topology_data={
            "nodes": [
                {"id": "SERVICE-AUTH001", "label": "auth-service", "type": "SERVICE", "affected": True, "fragility": 0.95},
                {"id": "SERVICE-GATEWAY001", "label": "api-gateway", "type": "SERVICE", "affected": True, "fragility": 0.58},
                {"id": "SERVICE-USER001", "label": "user-service", "type": "SERVICE", "affected": True, "fragility": 0.22},
                {"id": "SERVICE-SESSION001", "label": "session-manager", "type": "SERVICE", "affected": True, "fragility": 0.41},
                {"id": "SERVICE-FRONTEND001", "label": "frontend-service", "type": "SERVICE", "affected": True, "fragility": 0.30},
            ],
            "edges": [
                {"from": "SERVICE-FRONTEND001", "to": "SERVICE-AUTH001"},
                {"from": "SERVICE-GATEWAY001", "to": "SERVICE-AUTH001"},
                {"from": "SERVICE-GATEWAY001", "to": "SERVICE-SESSION001"},
                {"from": "SERVICE-GATEWAY001", "to": "SERVICE-USER001"},
            ],
        },
        notebook_url=None,
        slack_notified=False,
        demo_mode=True,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

_SAFE_KEYWORDS = {"dark mode", "theme", "toggle", "preferences", "ui", "color", "font"}
_FATAL_KEYWORDS = {"auth", "oauth", "authentication", "login", "session", "sso", "identity", "migrate"}


def get_demo_report(feature_description: str) -> RiskReport:
    """Return the most appropriate mock scenario based on keyword matching."""
    text = feature_description.lower()

    # Check fatal first — auth migrations are always NO-GO in demo
    if any(kw in text for kw in _FATAL_KEYWORDS):
        return _fatal_scenario(feature_description)

    # Check safe scenarios
    if any(kw in text for kw in _SAFE_KEYWORDS):
        return _safe_scenario(feature_description)

    # Default: RISKY scenario (the most educational for demo)
    return _risky_scenario(feature_description)
