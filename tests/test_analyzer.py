"""Unit tests for the fragility scorer and report builder."""

from __future__ import annotations

import pytest

from agent.analyzer import FragilityScorer
from agent.report import ReportBuilder
from agent.simulator import BlastRadiusSimulator

from dtmcp.schema import (
    BlastRadius,
    Incident,
    IncidentSeverity,
    IncidentStatus,
    RiskLevel,
    Service,
    ServiceMetrics,
    ServiceRisk,
    ServiceType,
    SLOStatus,
)
from datetime import datetime, timedelta


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def scorer():
    return FragilityScorer()


@pytest.fixture
def report_builder():
    return ReportBuilder()


@pytest.fixture
def simulator():
    return BlastRadiusSimulator()


@pytest.fixture
def healthy_service():
    return Service(
        entity_id="SERVICE-HEALTHY",
        name="healthy-service",
        service_type=ServiceType.SERVICE,
        technology="Go",
        dependencies=[],
        dependents=[],
    )


@pytest.fixture
def healthy_metrics():
    return ServiceMetrics(
        entity_id="SERVICE-HEALTHY",
        error_rate=0.001,
        response_time_p50_ms=25,
        response_time_p95_ms=80,
        response_time_p99_ms=150,
        throughput_rpm=5000,
    )


@pytest.fixture
def fragile_service():
    return Service(
        entity_id="SERVICE-FRAGILE",
        name="fragile-service",
        service_type=ServiceType.SERVICE,
        technology="Java",
        dependencies=["SERVICE-DB"],
        dependents=["SERVICE-GATEWAY"],
        tags=["critical:true"],
    )


@pytest.fixture
def fragile_metrics():
    return ServiceMetrics(
        entity_id="SERVICE-FRAGILE",
        error_rate=0.035,
        response_time_p50_ms=300,
        response_time_p95_ms=1200,
        response_time_p99_ms=3500,
        throughput_rpm=2000,
    )


@pytest.fixture
def recent_incidents():
    now = datetime.now(tz=None)
    return [
        Incident(
            problem_id="P-001",
            title="Service outage",
            severity=IncidentSeverity.AVAILABILITY,
            status=IncidentStatus.RESOLVED,
            affected_entities=["SERVICE-FRAGILE"],
            start_time=now - timedelta(days=5),
            end_time=now - timedelta(days=5, hours=-2),
        ),
        Incident(
            problem_id="P-002",
            title="High error rate",
            severity=IncidentSeverity.ERROR,
            status=IncidentStatus.RESOLVED,
            affected_entities=["SERVICE-FRAGILE"],
            start_time=now - timedelta(days=12),
            end_time=now - timedelta(days=12, hours=-1),
        ),
    ]


# ---------------------------------------------------------------------------
# FragilityScorer Tests
# ---------------------------------------------------------------------------

class TestFragilityScorer:
    """Tests for FragilityScorer."""

    def test_healthy_service_low_score(self, scorer, healthy_service, healthy_metrics):
        """Healthy service with no incidents should score low."""
        risk = scorer.calculate_service_risk(
            service=healthy_service,
            incidents=[],
            metrics=healthy_metrics,
            slos=[],
            depth=0,
        )
        assert risk.fragility_score < 0.2
        assert risk.incident_count_30d == 0

    def test_fragile_service_high_score(
        self, scorer, fragile_service, fragile_metrics, recent_incidents
    ):
        """Service with incidents and high error rate should score high."""
        risk = scorer.calculate_service_risk(
            service=fragile_service,
            incidents=recent_incidents,
            metrics=fragile_metrics,
            slos=[],
            depth=0,
        )
        assert risk.fragility_score > 0.4
        assert risk.incident_count_30d == 2
        assert len(risk.risk_factors) > 0

    def test_breached_slo_increases_score(self, scorer, fragile_service, fragile_metrics):
        """Breached SLO should significantly increase fragility score."""
        slos = [
            SLOStatus(
                slo_id="SLO-1",
                name="fragile-service Availability",
                target=99.9,
                current=98.5,
                error_budget_remaining=0.0,
                status="BREACHED",
            )
        ]

        risk_with_slo = scorer.calculate_service_risk(
            service=fragile_service,
            incidents=[],
            metrics=fragile_metrics,
            slos=slos,
            depth=0,
        )
        risk_without_slo = scorer.calculate_service_risk(
            service=fragile_service,
            incidents=[],
            metrics=fragile_metrics,
            slos=[],
            depth=0,
        )
        assert risk_with_slo.fragility_score > risk_without_slo.fragility_score

    def test_depth_reduces_score(self, scorer, healthy_service, healthy_metrics):
        """Services deeper in the chain should score lower."""
        risk_depth_0 = scorer.calculate_service_risk(
            service=healthy_service, incidents=[], metrics=healthy_metrics,
            slos=[], depth=0,
        )
        risk_depth_3 = scorer.calculate_service_risk(
            service=healthy_service, incidents=[], metrics=healthy_metrics,
            slos=[], depth=3,
        )
        assert risk_depth_0.fragility_score >= risk_depth_3.fragility_score


# ---------------------------------------------------------------------------
# ReportBuilder Tests
# ---------------------------------------------------------------------------

class TestReportBuilder:
    """Tests for ReportBuilder risk level determination."""

    def test_low_risk_determination(self, report_builder):
        """Services with very low fragility should be Low risk."""
        services = [
            ServiceRisk(
                entity_id="S1", name="svc-1", fragility_score=0.05,
                incident_count_30d=0, current_error_rate=0.001,
            )
        ]
        blast = BlastRadius(total_services_affected=1, user_impact_percentage=0.5)
        level = report_builder._determine_risk_level(services, blast, [])
        assert level == RiskLevel.LOW

    def test_critical_risk_with_breach(self, report_builder):
        """SLO breach + high fragility + wide blast = Critical."""
        services = [
            ServiceRisk(
                entity_id="S1", name="svc-1", fragility_score=0.8,
                incident_count_30d=5, current_error_rate=0.05,
            )
        ]
        blast = BlastRadius(total_services_affected=10, user_impact_percentage=80.0)
        slos = [
            SLOStatus(
                slo_id="SLO-1", name="Avail", target=99.9,
                current=97.0, error_budget_remaining=0.0, status="BREACHED",
            )
        ]
        level = report_builder._determine_risk_level(services, blast, slos)
        assert level == RiskLevel.CRITICAL

    def test_high_risk_from_blast_radius(self, report_builder):
        """Wide blast radius alone should trigger High."""
        services = [
            ServiceRisk(
                entity_id="S1", name="svc-1", fragility_score=0.3,
                incident_count_30d=1, current_error_rate=0.01,
            )
        ]
        blast = BlastRadius(total_services_affected=5, user_impact_percentage=35.0)
        level = report_builder._determine_risk_level(services, blast, [])
        assert level == RiskLevel.HIGH



