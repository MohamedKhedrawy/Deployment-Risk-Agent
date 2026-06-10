"""End-to-end tests — validates the full pipeline using mocked HTTP responses.

Tests use unittest.mock to patch the Dynatrace client's HTTP transport so the
pipeline runs without a live environment. The old DynatraceClient is gone;
these tests use a lightweight stub that conforms to the same interface.
"""

from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, patch

import pytest

from agent.orchestrator import AnalysisPipeline
from dtmcp.schema import (
    Decision,
    RiskReport,
    Service,
    ServiceMetrics,
    ServiceTopology,
)


# ---------------------------------------------------------------------------
# Lightweight stub client (replaces deleted DynatraceClient)
# ---------------------------------------------------------------------------

class _StubClient:
    """Minimal async client stub for pipeline tests."""

    def __init__(self, services=None, incidents=None, slos=None):
        self._services = services or []
        self._incidents = incidents or []
        self._slos = slos or []
        self._auth_error = None

    async def get_topology(self):
        if self._auth_error:
            raise RuntimeError(self._auth_error)
        return ServiceTopology(services=self._services)

    async def get_recent_incidents(self, entity_id=None, days=30):
        return self._incidents

    async def get_service_metrics(self, entity_id: str):
        return ServiceMetrics(entity_id=entity_id)

    async def get_slo_status(self, entity_id=None):
        return self._slos

    async def get_incident_details(self, problem_id):
        return None


SAMPLE_SERVICES = [
    Service(entity_id="SERVICE-CHECKOUT", name="checkout-service"),
    Service(entity_id="SERVICE-PAYMENT", name="payment-service", tags=["critical:true"]),
]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestEndToEnd:
    """Full pipeline integration tests using stub client."""

    def test_report_has_required_fields(self):
        """Pipeline output should contain all required top-level fields."""
        client = _StubClient(services=SAMPLE_SERVICES)
        pipeline = AnalysisPipeline(client=client)

        with patch("agent.orchestrator.InputValidator.check", new_callable=AsyncMock) as mock_val, \
             patch("agent.orchestrator.AnalysisPipeline._identify_affected_services",
                   new_callable=AsyncMock) as mock_ids:
            mock_val.return_value = (True, "")
            mock_ids.return_value = ["SERVICE-CHECKOUT"]

            report: RiskReport = asyncio.run(
                pipeline.run("Deploy new checkout loyalty points feature")
            )

        assert report.feature
        assert report.timestamp
        assert report.risk_score
        assert report.decision
        assert report.decision_rationale
        assert report.blast_radius is not None
        assert report.deploy_strategy is not None
        assert len(report.reasoning_chain) >= 3

    def test_invalid_input_returns_nogo(self):
        """Non-feature inputs must produce an immediate NO_GO."""
        client = _StubClient()
        pipeline = AnalysisPipeline(client=client)

        with patch("agent.orchestrator.InputValidator.check", new_callable=AsyncMock) as mock_val:
            mock_val.return_value = (False, "Not a valid software feature description")
            report: RiskReport = asyncio.run(pipeline.run("hello world"))

        assert report.decision == Decision.NO_GO
        assert "Not a valid software feature" in report.decision_rationale
        assert len(report.reasoning_chain) == 1

    def test_auth_error_propagates(self):
        """An auth error in the client should raise RuntimeError."""
        client = _StubClient()
        client._auth_error = "Dynatrace OAuth Configuration Error: missing scopes"
        pipeline = AnalysisPipeline(client=client)

        with patch("agent.orchestrator.InputValidator.check", new_callable=AsyncMock) as mock_val:
            mock_val.return_value = (True, "")
            with pytest.raises(RuntimeError, match="Dynatrace OAuth Configuration Error"):
                asyncio.run(pipeline.run("Add cache layer to product service"))

    def test_report_is_json_serializable(self):
        """The full report must be serialisable to JSON without errors."""
        client = _StubClient(services=SAMPLE_SERVICES)
        pipeline = AnalysisPipeline(client=client)

        with patch("agent.orchestrator.InputValidator.check", new_callable=AsyncMock) as mock_val, \
             patch("agent.orchestrator.AnalysisPipeline._identify_affected_services",
                   new_callable=AsyncMock) as mock_ids:
            mock_val.return_value = (True, "")
            mock_ids.return_value = ["SERVICE-CHECKOUT"]

            report: RiskReport = asyncio.run(
                pipeline.run("Deploy new checkout loyalty points feature")
            )

        data = report.model_dump(mode="json")
        assert isinstance(data, dict)
        assert "decision" in data
        assert "reasoning_chain" in data
        assert json.loads(json.dumps(data)) == data
