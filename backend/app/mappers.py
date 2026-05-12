"""Model-to-schema mappers for data transformation.

ARCHITECTURAL IMPROVEMENT #4 (May 12, 2026):
Provides clean separation between database ORM models (SQLAlchemy) and API schemas (Pydantic).
This allows the database schema to evolve independently from API contracts.

Before: ORM models directly exposed to API, schema changes cascade through code
After: Explicit mappers decouple database schema from API response schemas

Why this matters:
- Database evolution: Add/remove columns without breaking API contracts
- Schema versioning: Support multiple API versions with same database
- Type safety: Explicit conversion logic catches mismatches early
- Testing: Mock mappers independently from database
- Flexibility: Different API representations for same data
- Code organization: Clear layer separation (DB → Mapper → API)

The mapper pattern:
    Database Layer (SQLAlchemy ORM)
            ↓
        Mapper (explicit conversion)
            ↓
        API Layer (Pydantic schemas)

Example - User Entity:
    
    ORM Model (db/models.py):
        class User(Base):
            id: int
            username: str
            email: str
            is_verified: bool
            created_at: datetime
    
    API Schema (schemas.py):
        class UserResponse(BaseModel):
            id: int
            email: EmailStr
            created_at: datetime
    
    Mapper (mappers.py):
        class UserMapper:
            @staticmethod
            def model_to_schema(user: User) -> UserResponse:
                return UserResponse(
                    id=user.id,
                    email=user.email,
                    created_at=user.created_at
                )
    
    Usage in router:
        @router.get("/users/{user_id}")
        async def get_user(user_id: int):
            user_orm = db.query(User).get(user_id)
            user_response = UserMapper.model_to_schema(user_orm)
            return ServiceResponse.ok(data=user_response)

When adding a new entity:
    1. Create ORM model in backend/app/db/models.py
    2. Create Pydantic schema in backend/app/schemas_*.py
    3. Create mapper class in backend/app/mappers.py
    4. Use mapper in service and router layers
    5. Add feature flag in backend/app/core/config.py if needed

Patterns implemented:
- model_to_schema: Convert ORM model instance to Pydantic schema
- schema_to_model: Convert Pydantic schema to ORM model instance (for creation/update)
- update_model: Update ORM model from Pydantic update schema
- list_models_to_schema: Batch conversion of multiple models
"""

from typing import Optional

from backend.app.db.models import (
    Analysis,
    OCRSession,
    Reconstruction,
    User,
    Wine,
    WineCollection,
)
from backend.app.schemas import UserCreate, UserResponse
from backend.app.schemas_wine import WineCreate, WineResponse, WineUpdate
from backend.app.schemas_ocr import OCRResult
from backend.app.schemas_3d import ReconstructionResult


class UserMapper:
    """Convert between User ORM model and UserResponse schema.
    
    MAPPER PATTERN: User
    - ORM Model: backend/app/db/models.User
    - API Schema: backend/app/schemas.UserResponse
    - Use case: User registration, authentication, profile endpoints
    
    This mapper handles all conversions between database representation
    and API response format, allowing schema evolution independently.
    """

    @staticmethod
    def model_to_schema(user: User) -> UserResponse:
        """Convert User ORM model to UserResponse schema.
        
        Used when returning user data in API responses.
        Example: GET /api/v1/users/{user_id}, GET /api/v1/auth/me
        
        Note: Password hashes are never included in response schema.
        """
        return UserResponse(
            id=user.id,
            email=user.email,
            first_name=getattr(user, "first_name", None),
            last_name=getattr(user, "last_name", None),
            created_at=user.created_at,
            is_active=user.is_active,
        )

    @staticmethod
    def schema_to_model(user_create: UserCreate) -> User:
        """Convert UserCreate schema to User ORM model (without saving).
        
        Used when creating new users from API requests.
        The model is not persisted until db.add() and db.commit() are called.
        
        Example: POST /api/v1/auth/register
        """
        return User(
            email=user_create.email,
            first_name=getattr(user_create, "first_name", None),
            last_name=getattr(user_create, "last_name", None),
        )

    @staticmethod
    def list_models_to_schema(users: list[User]) -> list[UserResponse]:
        """Convert multiple User models to schemas (batch operation).
        
        Used for list endpoints and pagination operations.
        Example: GET /api/v1/users?skip=0&limit=10
        """
        return [UserMapper.model_to_schema(user) for user in users]


class WineMapper:
    """Convert between Wine ORM model and WineResponse schema.
    
    MAPPER PATTERN: Wine
    - ORM Model: backend/app/db/models.Wine
    - API Schema: backend/app/schemas_wine.WineResponse
    - Use case: Wine CRUD, search, collections, OCR identification results
    """

    @staticmethod
    def model_to_schema(wine: Wine) -> WineResponse:
        """Convert Wine ORM model to WineResponse schema.
        
        Used when returning wine data in API responses.
        Example: GET /api/v1/wines/{wine_id}, GET /api/v1/wines?search=cabernet
        """
        return WineResponse(
            id=wine.id,
            name=wine.wine_name,
            region=getattr(wine, "region", None),
            vintage=getattr(wine, "vintage", None),
            varietals=getattr(wine, "varietals", []),
            alcohol_content=getattr(wine, "alcohol_content", None),
            description=getattr(wine, "tasting_notes", None),
            created_at=wine.created_at,
            updated_at=wine.updated_at,
        )

    @staticmethod
    def schema_to_model(wine_create: WineCreate) -> Wine:
        """Convert WineCreate schema to Wine ORM model."""
        return Wine(
            wine_name=wine_create.name,
            region=wine_create.region,
            vintage=wine_create.vintage,
            varietals=wine_create.varietals or [],
            alcohol_content=wine_create.alcohol_content,
            tasting_notes=wine_create.description,
        )

    @staticmethod
    def update_model(wine: Wine, wine_update: WineUpdate) -> Wine:
        """Update Wine ORM model from WineUpdate schema."""
        if wine_update.name:
            wine.wine_name = wine_update.name
        if wine_update.region:
            wine.region = wine_update.region
        if wine_update.vintage:
            wine.vintage = wine_update.vintage
        if wine_update.varietals:
            wine.varietals = wine_update.varietals
        if wine_update.alcohol_content:
            wine.alcohol_content = wine_update.alcohol_content
        if wine_update.description:
            wine.tasting_notes = wine_update.description
        return wine

    @staticmethod
    def list_models_to_schema(wines: list[Wine]) -> list[WineResponse]:
        """Convert multiple Wine models to schemas."""
        return [WineMapper.model_to_schema(wine) for wine in wines]


class OCRMapper:
    """Convert between OCRSession ORM model and OCRResult schema.
    
    MAPPER PATTERN: OCR Session
    - ORM Model: backend/app/db/models.OCRSession
    - API Schema: backend/app/schemas_ocr.OCRResult
    - Use case: OCR processing results, text extraction, label parsing
    """

    @staticmethod
    def model_to_schema(session: OCRSession) -> OCRResult:
        """Convert OCRSession model to OCRResult schema.
        
        Used when returning OCR results in API responses.
        Example: POST /api/v1/ocr/analyze, GET /api/v1/ocr/text-blocks
        """
        return OCRResult(
            session_id=session.id,
            raw_text=session.raw_text or "",
            extracted_data=session.extracted_data or {},
            confidence=session.ocr_confidence or 0.0,
            processing_time_ms=session.processing_time_ms or 0.0,
            status=session.status,
            created_at=session.created_at,
        )

    @staticmethod
    def list_models_to_schema(sessions: list[OCRSession]) -> list[OCRResult]:
        """Convert multiple OCRSession models to schemas."""
        return [OCRMapper.model_to_schema(session) for session in sessions]


class ReconstructionMapper:
    """Convert between Reconstruction ORM model and ReconstructionResult schema.
    
    MAPPER PATTERN: Reconstruction
    - ORM Model: backend/app/db/models.Reconstruction
    - API Schema: backend/app/schemas_3d.ReconstructionResult
    - Use case: 3D reconstruction requests, results, viewer data
    """

    @staticmethod
    def model_to_schema(reconstruction: Reconstruction) -> ReconstructionResult:
        """Convert Reconstruction model to ReconstructionResult schema.
        
        Used when returning 3D reconstruction results in API responses.
        Example: POST /api/v1/3d/reconstruct-enhanced, GET /api/v1/viewer/{id}
        """
        return ReconstructionResult(
            reconstruction_id=reconstruction.reconstruction_id,
            status=reconstruction.status,
            object_type=getattr(reconstruction, "object_type", "wine_bottle"),
            confidence_score=reconstruction.confidence_score or 0.0,
            texture_url=reconstruction.texture_url or "",
            export_format=reconstruction.export_format or "gltf",
            created_at=reconstruction.created_at,
            completed_at=reconstruction.completed_at,
        )

    @staticmethod
    def list_models_to_schema(reconstructions: list[Reconstruction]) -> list[ReconstructionResult]:
        """Convert multiple Reconstruction models to schemas."""
        return [ReconstructionMapper.model_to_schema(r) for r in reconstructions]


class WineCollectionMapper:
    """Convert between WineCollection ORM model and schema.
    
    MAPPER PATTERN: Wine Collection
    - ORM Model: backend/app/db/models.WineCollection
    - API Schema: dict (flexible schema for collection metadata)
    - Use case: User wine collections, public collections, collection sharing
    """

    @staticmethod
    def model_to_schema(collection: WineCollection) -> dict:
        """Convert WineCollection model to dictionary/schema.
        
        Used when returning collection metadata in API responses.
        Example: GET /api/v1/users/{user_id}/collections
        """
        return {
            "id": collection.id,
            "name": collection.collection_name,
            "description": collection.description or "",
            "is_public": collection.is_public,
            "wine_count": len(collection.wines) if collection.wines else 0,
            "created_at": collection.created_at,
            "updated_at": collection.updated_at,
        }

    @staticmethod
    def list_models_to_schema(collections: list[WineCollection]) -> list[dict]:
        """Convert multiple WineCollection models to dictionaries."""
        return [WineCollectionMapper.model_to_schema(c) for c in collections]
