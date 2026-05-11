"""Shared schemas for asynchronous job submission and status tracking."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class JobSubmissionResponse(BaseModel):
    """Response returned when a background job is queued."""

    job_id: str
    job_name: str
    state: str = Field(default="queued")
    detail: Optional[str] = None


class JobStatusResponse(BaseModel):
    """Current state and result payload for a background job."""

    job_id: str
    job_name: Optional[str] = None
    state: str
    ready: bool = False
    successful: Optional[bool] = None
    result: Optional[Any] = None
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
