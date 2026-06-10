"""Request/response Pydantic models for the FastAPI layer."""

from __future__ import annotations

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    """Request body for the /analyze endpoint."""
    feature_description: str = Field(
        ...,
        description="Description of the feature to be deployed",
        examples=[
            "Add loyalty points calculation during checkout",
            "Migrate user-auth-service to a new database schema",
        ],
    )



class AnalyzeResponse(BaseModel):
    """Simplified response wrapper."""
    success: bool = True
    message: str = ""
    # The full RiskReport is returned directly from the endpoint;
    # this model is used for error responses.


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "ok"
    version: str = "0.1.0"
    agent: str = "canary-whisperer"



