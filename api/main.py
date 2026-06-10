"""FastAPI application — REST API for The Canary Whisperer."""

from __future__ import annotations

import logging
import os
import sys
from contextlib import asynccontextmanager

from dotenv import load_dotenv

load_dotenv()  # Load .env before anything reads os.getenv()

from fastapi import FastAPI, HTTPException, Query  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402

from agent.validator import InputValidator  # noqa: E402
from api.models import AnalyzeRequest  # noqa: E402
from dtmcp.schema import (  # noqa: E402
    BlastRadius,
    Decision,
    DeployStrategy,
    RiskLevel,
    RiskItem,
    RiskReport,
    ServiceRisk,
)
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-25s | %(levelname)-7s | %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
USE_VERTEX_AI = os.getenv("USE_VERTEX_AI", "false").lower() == "true"
GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "")
DT_ENVIRONMENT = os.getenv("DT_ENVIRONMENT", "")

# ---------------------------------------------------------------------------
# Shared validator (lightweight, no MCP)
# ---------------------------------------------------------------------------
_validator = InputValidator()


# ---------------------------------------------------------------------------
# Error report helper
# ---------------------------------------------------------------------------
def _error_report(feature: str, rationale: str, conditions: list[str]) -> RiskReport:
    return RiskReport(
        feature=feature,
        decision=Decision.NO_GO,
        decision_rationale=rationale,
        risk_score=RiskLevel.CRITICAL,
        blast_radius=BlastRadius(),
        deploy_strategy=DeployStrategy(strategy="Halted", conditions=conditions),
        demo_mode=DEMO_MODE,
    )


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🐤 The Canary Whisperer is starting up...")
    if USE_VERTEX_AI and GOOGLE_CLOUD_PROJECT:
        logger.info(f"Using Vertex AI (project={GOOGLE_CLOUD_PROJECT}) — no API key needed.")
    elif not GOOGLE_API_KEY:
        logger.warning("No GOOGLE_API_KEY found and USE_VERTEX_AI is false — LLM validation will be limited.")
    if not DT_ENVIRONMENT and not DEMO_MODE:
        logger.warning("No DT_ENVIRONMENT set — only DEMO_MODE will work.")
    yield
    logger.info("🐤 The Canary Whisperer is shutting down...")


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="The Canary Whisperer",
    description=(
        "Pre-deployment risk simulation agent. Analyzes feature rollouts "
        "against production topology and generates GO/NO-GO decisions."
    ),
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "mode": "demo" if DEMO_MODE else "live",
        "version": "1.0.0"
    }


def build_risk_report_from_scenario(scenario: dict) -> RiskReport:
    services = []
    for s in scenario.get("affected_services", []):
        services.append(ServiceRisk(
            entity_id=s["service_id"],
            name=s["service_name"],
            fragility_score=s["fragility_score"],
            incident_count_30d=s["incident_count_30d"],
            current_error_rate=s["error_rate_pct"],
            slo_burn_rate=s["slo_burn_rate"],
            dependency_depth=s["dependency_depth"],
            risk_factors=[],
            health_status=s.get("health_status", "healthy"),
            last_incident=s.get("last_incident")
        ))
        
    top_risks = []
    for i, r in enumerate(scenario.get("top_risks", [])):
        title = r[:50] + "..." if len(r) > 50 else r
        top_risks.append(RiskItem(
            rank=i+1,
            title=title,
            description=r,
            severity=RiskLevel(scenario["risk_level"].capitalize()),
            affected_service="unknown",
            mitigation=""
        ))
        
    return RiskReport(
        feature=scenario["feature"],
        timestamp=datetime.now(timezone.utc),
        risk_score=RiskLevel(scenario["risk_level"].capitalize()),
        decision=Decision(scenario["decision"]),
        decision_rationale=scenario["reasoning"],
        blast_radius=BlastRadius(
            total_services_affected=len(services),
            user_impact_percentage=scenario["blast_radius_pct"],
            critical_path_services=[],
            affected_services=services
        ),
        top_risks=top_risks,
        deploy_strategy=DeployStrategy(
            strategy=scenario["deployment_strategy"],
            conditions=scenario["conditions"] or [],
            monitor_metrics=[]
        ),
        affected_services=services,
        reasoning_chain=[],
        raw_topology_data=scenario.get("topology_map", {}),
        demo_mode=True
    )


@app.post("/analyze", response_model=RiskReport)
async def analyze_feature(
    request: AnalyzeRequest,
    demo: bool = Query(default=False, description="Force demo mode for this request"),
):
    """Run the full risk analysis pipeline for a feature description.

    Flow:
      request → validator → [demo mock OR ADK agent via MCP] → RiskReport
    """
    feature = request.feature_description
    use_demo = DEMO_MODE or demo

    # ── STEP 0: Validate input ───────────────────────────────────────────
    try:
        is_valid, reason = await _validator.check(feature)
    except Exception as e:
        logger.warning(f"Validator error (allowing through): {e}")
        is_valid, reason = True, ""

    if not is_valid:
        return RiskReport(
            feature=feature,
            decision=Decision.NO_GO,
            decision_rationale=f"Input rejected: {reason}",
            risk_score=RiskLevel.LOW,
            blast_radius=BlastRadius(),
            deploy_strategy=DeployStrategy(strategy="Halted", conditions=[reason]),
            demo_mode=use_demo,
        )

    # ── STEP 1: Route to demo or live ───────────────────────────────────
    if use_demo:
        import asyncio
        from agent.mock_data import get_scenario
        logger.info(f"[DEMO] Routing '{feature[:60]}' to mock scenario")
        scenario = get_scenario(feature)
        await asyncio.sleep(3.5)  # Simulate analysis time for demo
        return build_risk_report_from_scenario(scenario)

    # ── STEP 2: Live — run ADK agent with Dynatrace MCP ─────────────────
    logger.info(f"[LIVE] Starting analysis for: {feature[:80]}")
    try:
        from canary_agent.mcp_runner import run_agent
        report = await run_agent(feature)
        return report

    except RuntimeError as e:
        err_str = str(e)
        logger.error(f"Agent error: {err_str}")

        if "OAuth" in err_str or "auth" in err_str.lower() or "scope" in err_str.lower():
            return _error_report(
                feature,
                rationale=f"Dynatrace authentication error: {err_str}",
                conditions=[
                    "Add all required OAuth scopes to your Dynatrace OAuth client.",
                    "Regenerate the client secret and update OAUTH_CLIENT_SECRET in .env.",
                    "See SETUP.md for the full list of required scopes.",
                ],
            )

        if "LLM" in err_str or "Gemini" in err_str or "503" in err_str:
            return _error_report(
                feature,
                rationale=f"Gemini API error: {err_str}",
                conditions=[
                    "Wait for the Google Gemini API to recover from rate limits.",
                    "Verify your GOOGLE_API_KEY is valid and has quota.",
                    "Use DEMO_MODE=true or the demo toggle as a fallback.",
                ],
            )

        return _error_report(
            feature,
            rationale=f"Analysis failed: {err_str}",
            conditions=["Check server logs for details.", "Try demo mode as a fallback."],
        )

    except Exception as e:
        logger.exception(f"Unexpected error during analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


# ---------------------------------------------------------------------------
# Run directly
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
