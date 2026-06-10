"""Pydantic models for Dynatrace topology, incidents, SLOs, and risk reports."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class RiskLevel(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class Decision(str, Enum):
    GO = "GO"
    GO_WITH_CONDITIONS = "GO_WITH_CONDITIONS"
    NO_GO = "NO_GO"


class ServiceType(str, Enum):
    SERVICE = "SERVICE"
    PROCESS_GROUP = "PROCESS_GROUP"
    HOST = "HOST"
    DATABASE = "DATABASE"
    QUEUE = "QUEUE"


class IncidentSeverity(str, Enum):
    AVAILABILITY = "AVAILABILITY"
    ERROR = "ERROR"
    SLOWDOWN = "SLOWDOWN"
    RESOURCE = "RESOURCE"
    CUSTOM = "CUSTOM"


class IncidentStatus(str, Enum):
    OPEN = "OPEN"
    RESOLVED = "RESOLVED"


# ---------------------------------------------------------------------------
# Dynatrace Entity Models
# ---------------------------------------------------------------------------

class Service(BaseModel):
    """A monitored service/entity in the Dynatrace topology."""
    entity_id: str = Field(..., description="Dynatrace entity ID (e.g., SERVICE-ABC123)")
    name: str = Field(..., description="Human-readable service name")
    service_type: ServiceType = Field(default=ServiceType.SERVICE)
    technology: str = Field(default="", description="e.g., Java, Node.js, .NET")
    dependencies: list[str] = Field(
        default_factory=list,
        description="Entity IDs this service calls (outgoing)",
    )
    dependents: list[str] = Field(
        default_factory=list,
        description="Entity IDs that call this service (incoming)",
    )
    tags: list[str] = Field(default_factory=list)
    properties: dict[str, Any] = Field(default_factory=dict)


class ServiceTopology(BaseModel):
    """Full service topology map from Dynatrace."""
    services: list[Service] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=_now)

    def get_service(self, entity_id: str) -> Service | None:
        """Look up a service by entity ID."""
        return next((s for s in self.services if s.entity_id == entity_id), None)

    def get_service_by_name(self, name: str) -> Service | None:
        """Look up a service by name (case-insensitive)."""
        name_lower = name.lower()
        return next((s for s in self.services if s.name.lower() == name_lower), None)

    def get_downstream(self, entity_id: str, depth: int = 3) -> list[Service]:
        """Get all services downstream of a given service (BFS)."""
        visited: set[str] = set()
        queue = [entity_id]
        result: list[Service] = []
        current_depth = 0

        while queue and current_depth < depth:
            next_queue: list[str] = []
            for eid in queue:
                if eid in visited:
                    continue
                visited.add(eid)
                svc = self.get_service(eid)
                if svc and eid != entity_id:
                    result.append(svc)
                if svc:
                    next_queue.extend(
                        dep for dep in svc.dependents if dep not in visited
                    )
            queue = next_queue
            current_depth += 1
        return result


class Incident(BaseModel):
    """A historical problem/incident from Dynatrace."""
    problem_id: str
    title: str
    severity: IncidentSeverity = Field(default=IncidentSeverity.ERROR)
    status: IncidentStatus = Field(default=IncidentStatus.RESOLVED)
    affected_entities: list[str] = Field(default_factory=list)
    root_cause_entity: str | None = None
    start_time: datetime
    end_time: datetime | None = None
    impact_level: str = Field(default="SERVICE", description="SERVICE, APPLICATION, ENVIRONMENT")
    details: str = Field(default="")


class ServiceMetrics(BaseModel):
    """Current performance metrics for a service."""
    entity_id: str
    error_rate: float = Field(default=0.0, description="Current error rate (0.0-1.0)")
    response_time_p50_ms: float = Field(default=0.0, description="Median response time in ms")
    response_time_p95_ms: float = Field(default=0.0, description="95th percentile response time")
    response_time_p99_ms: float = Field(default=0.0, description="99th percentile response time")
    throughput_rpm: float = Field(default=0.0, description="Requests per minute")
    cpu_usage: float = Field(default=0.0, description="CPU usage (0.0-1.0)")
    memory_usage: float = Field(default=0.0, description="Memory usage (0.0-1.0)")


class SLOStatus(BaseModel):
    """SLO compliance status for a service."""
    slo_id: str
    name: str
    target: float = Field(..., description="Target SLO (e.g., 99.9)")
    current: float = Field(..., description="Current SLO performance (e.g., 99.7)")
    error_budget_remaining: float = Field(
        ..., description="Remaining error budget as percentage (0.0-100.0)"
    )
    evaluation_window: str = Field(default="30d", description="e.g., 7d, 30d")
    status: str = Field(default="OK", description="OK, WARNING, BREACHED")


# ---------------------------------------------------------------------------
# Risk Analysis Models
# ---------------------------------------------------------------------------

class ServiceRisk(BaseModel):
    """Risk assessment for a single service."""
    entity_id: str
    name: str
    fragility_score: float = Field(
        ..., ge=0.0, le=1.0, description="Fragility score (0=rock solid, 1=extremely fragile)"
    )
    incident_count_30d: int = Field(default=0, description="Incidents in last 30 days")
    current_error_rate: float = Field(default=0.0)
    slo_burn_rate: float = Field(default=0.0, description="Rate of SLO budget consumption")
    dependency_depth: int = Field(
        default=0, description="How deep in the dependency chain from changed service"
    )
    risk_factors: list[str] = Field(
        default_factory=list, description="Human-readable risk factors"
    )
    health_status: str = Field(default="healthy")
    last_incident: str | None = Field(default=None)


class BlastRadius(BaseModel):
    """Estimated blast radius of a deployment failure."""
    total_services_affected: int = 0
    user_impact_percentage: float = Field(
        default=0.0, description="Estimated % of users affected (0.0-100.0)"
    )
    critical_path_services: list[str] = Field(
        default_factory=list, description="Services on the critical user-facing path"
    )
    affected_services: list[ServiceRisk] = Field(default_factory=list)


class RiskItem(BaseModel):
    """A specific identified risk."""
    rank: int = Field(..., ge=1, le=10)
    title: str
    description: str
    severity: RiskLevel
    affected_service: str
    mitigation: str = Field(default="", description="Suggested mitigation")


class DeployStrategy(BaseModel):
    """Recommended deployment strategy."""
    strategy: str = Field(
        ..., description="e.g., 'Full rollout', 'Canary 5%', 'Off-peak only', 'Hold'"
    )
    canary_percentage: float | None = Field(
        default=None, description="Suggested canary traffic %"
    )
    recommended_window: str | None = Field(
        default=None, description="e.g., 'After 8pm EST'"
    )
    monitor_metrics: list[str] = Field(
        default_factory=list, description="Metrics to watch during rollout"
    )
    conditions: list[str] = Field(
        default_factory=list, description="Conditions that must be met before deploy"
    )


class ReasoningStep(BaseModel):
    """A single step in the agent's reasoning chain."""
    step_number: int
    title: str
    action: str = Field(..., description="What the agent did")
    findings: str = Field(..., description="What the agent found")
    data: dict[str, Any] = Field(default_factory=dict, description="Raw data supporting findings")


class RiskReport(BaseModel):
    """The final structured risk report — the main output of the agent."""
    feature: str = Field(..., description="Description of the feature being assessed")
    timestamp: datetime = Field(default_factory=_now)
    risk_score: RiskLevel
    decision: Decision
    decision_rationale: str
    blast_radius: BlastRadius
    top_risks: list[RiskItem] = Field(default_factory=list, description="Top 3 risks")
    deploy_strategy: DeployStrategy
    affected_services: list[ServiceRisk] = Field(default_factory=list)
    reasoning_chain: list[ReasoningStep] = Field(
        default_factory=list, description="Full reasoning chain for transparency"
    )
    raw_topology_data: dict[str, Any] = Field(
        default_factory=dict, description="Raw topology snapshot for UI rendering"
    )
    # Extended fields for new capabilities
    notebook_url: str | None = Field(
        default=None, description="URL of the Dynatrace Notebook created for this report"
    )
    slack_notified: bool = Field(
        default=False, description="Whether a Slack notification was sent"
    )
    demo_mode: bool = Field(
        default=False, description="True if this report was generated from mock data"
    )

