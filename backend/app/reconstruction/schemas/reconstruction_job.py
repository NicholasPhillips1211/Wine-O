"""Core schemas for asynchronous reconstruction jobs."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class ReconstructionStage(str, Enum):
    """Pipeline stages for wine-bottle constrained reconstruction."""

    CAPTURE = "capture"
    SEGMENTATION = "segmentation"
    GEOMETRY = "geometry"
    BLENDER_REFINEMENT = "blender_refinement"
    MATERIALS = "materials"
    OPTIMIZATION = "optimization"
    EXPORT = "export"
    DELIVERY = "delivery"


class ReconstructionJobStatus(str, Enum):
    """High-level lifecycle state for a reconstruction job."""

    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class StageResult(BaseModel):
    """A single pipeline stage output payload."""

    stage: ReconstructionStage
    status: ReconstructionJobStatus = ReconstructionJobStatus.QUEUED
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    artifacts: dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None


class ReconstructionJob(BaseModel):
    """Aggregate job state used by orchestration and API endpoints."""

    id: str
    status: ReconstructionJobStatus = ReconstructionJobStatus.QUEUED
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    user_id: Optional[str] = None

    segmentation_result: Optional[dict[str, Any]] = None
    geometry_result: Optional[dict[str, Any]] = None
    blender_result: Optional[dict[str, Any]] = None
    material_result: Optional[dict[str, Any]] = None
    export_result: Optional[dict[str, Any]] = None

    confidence_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    confidence_breakdown: dict[str, float] = Field(default_factory=dict)
    processing_time: Optional[float] = None
    reconstruction_version: str = "v2"

    stage: ReconstructionStage = ReconstructionStage.CAPTURE
    progress_percent: int = Field(default=0, ge=0, le=100)
    error_message: Optional[str] = None
    artifacts: dict[str, Any] = Field(default_factory=dict)
    stage_results: list[StageResult] = Field(default_factory=list)
