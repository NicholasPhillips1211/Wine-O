"""Standardized response models for all API endpoints.

ARCHITECTURAL IMPROVEMENT #1 (May 12, 2026):
This module provides unified response wrappers, pagination, and error handling across all services.
Ensures consistent response format, metadata tracking, and error messaging throughout the API.

Before: Services returned inconsistent types (dict, list, custom models)
After: All endpoints return ServiceResponse[T] with standardized structure

Benefits:
- Unified error handling and error codes for client-side retry logic
- Built-in pagination metadata without schema changes
- Async job tracking via JobResponse
- Easy to add rate limiting, tracing, and performance metrics to all endpoints

Usage:
    from backend.app.core import ServiceResponse
    
    @router.get("/wines")
    async def list_wines(skip: int = 0, limit: int = 10):
        wines = await wine_service.list(skip, limit)
        return ServiceResponse.list(data=wines, total=100, skip=skip, limit=limit)
    
    @router.post("/wines/{wine_id}/reconstruct")
    async def reconstruct(wine_id: int):
        if not settings.FEATURE_RECONSTRUCTION_ENABLED:
            return ServiceResponse.error("Feature disabled", code="FEATURE_DISABLED")
        result = await service.reconstruct(wine_id)
        return ServiceResponse.created(data=result)
"""

from datetime import datetime
from enum import Enum
from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class ResponseStatus(str, Enum):
    """Status codes for API responses."""

    SUCCESS = "success"
    ERROR = "error"
    CREATED = "created"
    ACCEPTED = "accepted"


class PaginationMetadata(BaseModel):
    """Pagination information for list responses."""

    total: int
    skip: int
    limit: int
    has_more: bool


class ServiceMetadata(BaseModel):
    """Additional metadata for all responses."""

    timestamp: datetime = None
    request_id: Optional[str] = None
    version: str = "1.0"

    model_config = ConfigDict(populate_by_name=True)

    def __init__(self, **data):
        if "timestamp" not in data:
            data["timestamp"] = datetime.utcnow()
        super().__init__(**data)


class ServiceResponse(BaseModel, Generic[T]):
    """Standardized service response wrapper for all API endpoints.

    ARCHITECTURAL IMPROVEMENT #1: Unified Response Pattern
    
    All API endpoints return this structure to ensure consistency:
    - success: Boolean indicating whether the operation succeeded
    - data: Response payload (generic type T) - any model, list, or primitive
    - error: Error message if success is False
    - error_code: Machine-readable error identifier for client-side logic
    - metadata: Additional context (pagination, timestamps, tracing headers, etc.)

    This replaces inconsistent response types across the codebase.

    Example responses:
    
    Success with data:
        {
            "success": true,
            "data": {"wine_id": 1, "name": "Cabernet"},
            "error": null,
            "metadata": {"timestamp": "2026-05-12T10:30:00Z"}
        }
    
    Error response:
        {
            "success": false,
            "data": null,
            "error": "Wine not found",
            "error_code": "NOT_FOUND",
            "metadata": {"timestamp": "2026-05-12T10:30:00Z"}
        }
    
    Paginated list:
        {
            "success": true,
            "data": [{"id": 1, "name": "Wine 1"}, ...],
            "metadata": {
                "pagination": {
                    "total": 100,
                    "skip": 0,
                    "limit": 10,
                    "has_more": true
                }
            }
        }
    """

    success: bool
    data: Optional[T] = None
    error: Optional[str] = None
    error_code: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None

    model_config = ConfigDict(populate_by_name=True)

    @classmethod
    def ok(cls, data: T, metadata: Optional[dict[str, Any]] = None) -> "ServiceResponse[T]":
        """Create a successful response."""
        return cls(success=True, data=data, metadata=metadata or {})

    @classmethod
    def created(cls, data: T, metadata: Optional[dict[str, Any]] = None) -> "ServiceResponse[T]":
        """Create a response for a resource creation (HTTP 201 equivalent)."""
        meta = metadata or {}
        meta["status"] = "created"
        return cls(success=True, data=data, metadata=meta)

    @classmethod
    def error(
        cls,
        message: str,
        code: str = "INTERNAL_ERROR",
        metadata: Optional[dict[str, Any]] = None,
    ) -> "ServiceResponse[T]":
        """Create an error response with machine-readable error code."""
        return cls(success=False, error=message, error_code=code, metadata=metadata or {})

    @classmethod
    def list(
        cls,
        data: list[T],
        total: int,
        skip: int = 0,
        limit: int = 10,
    ) -> "ServiceResponse[T]":
        """Create a paginated list response with metadata."""
        pagination = PaginationMetadata(
            total=total,
            skip=skip,
            limit=limit,
            has_more=(skip + limit) < total,
        )
        return cls(success=True, data=data, metadata={"pagination": pagination.model_dump()})


class JobResponse(BaseModel):
    """Response for async job submissions."""

    job_id: str
    status: str
    created_at: datetime
    expires_at: datetime


class ErrorDetail(BaseModel):
    """Detailed error information."""

    code: str
    message: str
    field: Optional[str] = None  # For validation errors
    details: Optional[dict[str, Any]] = None
