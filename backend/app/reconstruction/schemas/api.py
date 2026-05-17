"""API request/response schemas for reconstruction orchestration endpoints."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class StartReconstructionRequest(BaseModel):
    """Start a new asynchronous reconstruction job."""

    image_urls: list[str] = Field(..., min_length=2, description="Required capture angles")
    user_id: Optional[str] = None
    object_type: str = Field(default="wine_bottle")
    quality: str = Field(default="high", pattern="^(low|medium|high)$")


class StartReconstructionResponse(BaseModel):
    """Response payload when a new reconstruction is enqueued."""

    job_id: str
    status: str
    stage: str


class ReconstructionArtifactsResponse(BaseModel):
    """Artifact response for completed or in-progress jobs."""

    job_id: str
    artifacts: dict[str, Any] = Field(default_factory=dict)
    stage_results: dict[str, Any] = Field(default_factory=dict)
