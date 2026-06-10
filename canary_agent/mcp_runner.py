"""ADK Runner — invokes the canary_whisperer agent and parses its JSON output.

This module bridges the FastAPI endpoint and the ADK agent. It:
1. Creates a fresh ADK Runner + session per request
2. Streams events until the agent produces its final response
3. Extracts the JSON block from the response text
4. Maps the JSON to internal RiskReport Pydantic models via the scorer/report builder

Design choice: We invoke the ADK agent directly via `Runner.run_async` rather than
using `get_fast_api_app` because we need to parse structured JSON output and feed
it through the existing scorer and report builder — a pattern that doesn't fit
the ADK FastAPI passthrough model.
"""

from __future__ import annotations

import json
import logging
import re
import uuid
from datetime import datetime, timezone

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from dtmcp.schema import (
    BlastRadius,
    Decision,
    DeployStrategy,
    ReasoningStep,
    RiskItem,
    RiskLevel,
    RiskReport,
    ServiceRisk,
)

logger = logging.getLogger(__name__)

# Lazy-import the agent to avoid MCP subprocess at module load time
_runner: Runner | None = None


def _get_runner() -> Runner:
    global _runner
    if _runner is None:
        from canary_agent.agent import root_agent
        _runner = Runner(
            agent=root_agent,
            session_service=InMemorySessionService(),
            app_name="canary_whisperer",
        )
    return _runner


def _extract_json(text: str) -> dict:
    """Extract the first JSON object from the agent's response text."""
    # Try the whole text first (agent should output only JSON)
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Fallback: extract from a ```json ... ``` fence
    fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fence_match:
        try:
            return json.loads(fence_match.group(1))
        except json.JSONDecodeError:
            pass

    # Fallback: find the first {...} block
    brace_match = re.search(r"\{.*\}", text, re.DOTALL)
    if brace_match:
        try:
            return json.loads(brace_match.group(0))
        except json.JSONDecodeError:
            pass

    raise ValueError(f"No valid JSON found in agent response. Response was:\n{text[:500]}")


def _level_from_str(level: str) -> RiskLevel:
    mapping = {
        "low": RiskLevel.LOW,
        "medium": RiskLevel.MEDIUM,
        "high": RiskLevel.HIGH,
        "critical": RiskLevel.CRITICAL,
    }
    return mapping.get(level.lower(), RiskLevel.MEDIUM)


def _decision_from_str(decision: str) -> Decision:
    mapping = {
        "go": Decision.GO,
        "go_with_conditions": Decision.GO_WITH_CONDITIONS,
        "no_go": Decision.NO_GO,
        "no-go": Decision.NO_GO,
    }
    return mapping.get(decision.lower().replace(" ", "_"), Decision.GO_WITH_CONDITIONS)


def _build_report_from_agent_json(feature: str, data: dict) -> RiskReport:
    """Convert the agent's JSON output into a full RiskReport."""
    raw_services = data.get("affected_services", [])

    # Build ServiceRisk list
    service_risks = []
    for i, svc in enumerate(raw_services):
        service_risks.append(ServiceRisk(
            entity_id=svc.get("service_id", f"UNKNOWN-{i}"),
            name=svc.get("service_name", "Unknown Service"),
            fragility_score=float(svc.get("fragility_score", 0.0)),
            incident_count_30d=int(svc.get("incident_count_30d", 0)),
            current_error_rate=float(svc.get("error_rate_pct", 0.0)) / 100.0,
            slo_burn_rate=float(svc.get("slo_burn_rate", 0.0)),
            dependency_depth=int(svc.get("dependency_depth", 0)),
            risk_factors=[svc.get("health_status", "unknown")],
        ))

    # Build blast radius
    blast = BlastRadius(
        total_services_affected=len(service_risks),
        user_impact_percentage=float(data.get("blast_radius_pct", 0.0)),
        critical_path_services=[
            s.name for s in service_risks
            if s.fragility_score > 0.6
        ],
        affected_services=service_risks,
    )

    # Build top risks from agent's top_risks list
    top_risks = []
    for i, risk_text in enumerate(data.get("top_risks", [])[:3]):
        # Find the most fragile service to associate
        assoc_svc = service_risks[0].entity_id if service_risks else "UNKNOWN"
        top_risks.append(RiskItem(
            rank=i + 1,
            title=risk_text[:80],
            description=risk_text,
            severity=_level_from_str(data.get("risk_level", "medium")),
            affected_service=assoc_svc,
            mitigation="See deployment conditions for mitigations.",
        ))

    # Build deploy strategy
    conditions = data.get("conditions") or []
    risk_level = _level_from_str(data.get("risk_level", "medium"))
    strategy_str = data.get("deployment_strategy", "Canary rollout")
    canary_pct = None
    if "5%" in strategy_str:
        canary_pct = 5.0
    elif "10%" in strategy_str:
        canary_pct = 10.0

    deploy_strategy = DeployStrategy(
        strategy=strategy_str,
        canary_percentage=canary_pct,
        recommended_window=None,
        monitor_metrics=[f"{s.name} error rate" for s in service_risks[:3]],
        conditions=conditions,
    )

    # Build reasoning chain from agent reasoning text
    reasoning_text = data.get("reasoning", "Agent analysis complete.")
    reasoning_chain = [
        ReasoningStep(
            step_number=1,
            title="Map the Topology",
            action="Queried Dynatrace via MCP tools",
            findings=f"Identified {len(service_risks)} affected services.",
            data={"affected_services": [s.name for s in service_risks]},
        ),
        ReasoningStep(
            step_number=2,
            title="Check Historical Health",
            action="Pulled incidents, error rates, and SLO status via MCP",
            findings=reasoning_text,
            data={"risk_score": data.get("risk_score", 0.0)},
        ),
        ReasoningStep(
            step_number=3,
            title="Assess the Risk",
            action="Applied fragility formula and calculated blast radius",
            findings=(
                f"Blast radius: {blast.user_impact_percentage:.1f}% of users. "
                f"Risk: {data.get('risk_level', 'MEDIUM')}."
            ),
            data={"blast_radius_pct": blast.user_impact_percentage},
        ),
        ReasoningStep(
            step_number=4,
            title="GO/NO-GO Decision",
            action="Synthesized all findings into a deployment recommendation",
            findings=f"Decision: {data.get('decision', 'GO_WITH_CONDITIONS')}. {reasoning_text[:200]}",
            data={"decision": data.get("decision"), "strategy": strategy_str},
        ),
    ]

    # Build topology graph for UI
    raw_topology = {
        "nodes": [
            {
                "id": s.entity_id,
                "label": s.name,
                "type": "SERVICE",
                "affected": True,
                "fragility": s.fragility_score,
            }
            for s in service_risks
        ],
        "edges": [],
    }

    return RiskReport(
        feature=feature,
        timestamp=datetime.now(timezone.utc),
        risk_score=risk_level,
        decision=_decision_from_str(data.get("decision", "GO_WITH_CONDITIONS")),
        decision_rationale=reasoning_text,
        blast_radius=blast,
        top_risks=top_risks,
        deploy_strategy=deploy_strategy,
        affected_services=service_risks,
        reasoning_chain=reasoning_chain,
        raw_topology_data=raw_topology,
        notebook_url=data.get("notebook_url"),
        slack_notified=bool(data.get("slack_notified", False)),
        demo_mode=False,
    )


async def run_agent(feature_description: str) -> RiskReport:
    """Invoke the ADK agent and return a structured RiskReport.

    Raises:
        RuntimeError: if the agent fails, times out, or returns unparseable output.
    """
    runner = _get_runner()
    session_id = f"canary-{uuid.uuid4().hex[:8]}"
    user_id = "api-backend"

    # Create a fresh session for this request
    await runner.session_service.create_session(
        app_name="canary_whisperer",
        user_id=user_id,
        session_id=session_id,
    )

    user_message = types.Content(
        role="user",
        parts=[types.Part(text=feature_description)],
    )

    final_text = ""
    try:
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=user_message,
        ):
            # Collect the final model text response
            if (
                event.content
                and event.content.role == "model"
                and event.content.parts
            ):
                for part in event.content.parts:
                    if hasattr(part, "text") and part.text:
                        final_text += part.text
    except Exception as e:
        raise RuntimeError(f"ADK agent execution failed: {e}") from e

    if not final_text.strip():
        raise RuntimeError("Agent returned an empty response. Check MCP server connectivity.")

    try:
        agent_data = _extract_json(final_text)
    except ValueError as e:
        raise RuntimeError(str(e)) from e

    return _build_report_from_agent_json(feature_description, agent_data)
