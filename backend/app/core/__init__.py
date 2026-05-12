"""Core infrastructure for Wine-O backend.

ARCHITECTURAL IMPROVEMENTS (May 12, 2026):

This module provides three key architectural improvements that enable cleaner
feature development and reduce technical debt:

1. IMPROVEMENT #1: Standardized Response Models (responses.py)
   - Unified ServiceResponse[T] wrapper for all endpoints
   - Consistent error handling with machine-readable error codes
   - Built-in pagination metadata
   - Async job tracking support
   
   Usage:
       from backend.app.core import ServiceResponse
       return ServiceResponse.ok(data=result)

2. IMPROVEMENT #4: Model-to-Schema Separation (../mappers.py)
   - Decouples SQLAlchemy ORM models from Pydantic schemas
   - Allows database evolution without breaking APIs
   - Explicit conversion logic for type safety
   - Located in backend/app/mappers.py (separate from core)
   
   Usage:
       from backend.app.mappers import WineMapper
       wine_response = WineMapper.model_to_schema(wine_orm)

3. IMPROVEMENT #5: Centralized Configuration (config.py)
   - All environment variables and feature flags in one place
   - 50+ configurable options with sensible defaults
   - Feature flags for roadmap items (AI sommelier, marketplace, social)
   - Environment-specific configurations
   
   Usage:
       from backend.app.core import settings
       if settings.FEATURE_AI_SOMMELIER_ENABLED:
           # ... implementation

Benefits:
- Production ready: No code changes for deployment
- Feature toggling: Enable/disable features via environment
- Scalable: Team onboarding with .env.example
- Maintainable: Clear separation of concerns
- Future-proof: Easy to add new entities and features

See docs/ARCHITECTURAL_IMPROVEMENTS.md for detailed guide.
"""

from backend.app.core.config import Settings, settings
from backend.app.core.responses import (
    ErrorDetail,
    JobResponse,
    PaginationMetadata,
    ResponseStatus,
    ServiceMetadata,
    ServiceResponse,
)

__all__ = [
    "Settings",
    "settings",
    "ServiceResponse",
    "ResponseStatus",
    "ServiceMetadata",
    "PaginationMetadata",
    "JobResponse",
    "ErrorDetail",
]
