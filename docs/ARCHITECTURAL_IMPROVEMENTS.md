# Architectural Improvements (May 12, 2026)

This document outlines three key architectural improvements made to enable cleaner feature development and reduce technical debt as the roadmap progresses.

## 1. Standardized Response Models (`backend/app/core/responses.py`)

**Problem Solved:** Services returned inconsistent response types, making pagination, error handling, and async job tracking fragmented and error-prone.

**Solution:** Unified `ServiceResponse` wrapper that all endpoints use.

### Usage

```python
from backend.app.core.responses import ServiceResponse, PaginationMetadata

# Successful response with data
response = ServiceResponse.ok(data={"wine_id": 1, "name": "Cabernet"})

# Error response
response = ServiceResponse.error(
    message="Wine not found",
    code="NOT_FOUND"
)

# Paginated list response
response = ServiceResponse.list(
    data=wines,
    total=100,
    skip=0,
    limit=10
)

# Job submission response
response = ServiceResponse.created(
    data={"job_id": "abc123"},
    metadata={"status": "queued"}
)
```

### Benefits

- **Consistent API contract:** All endpoints return the same structure.
- **Built-in pagination:** Easy to add pagination metadata without schema changes.
- **Error tracking:** Standardized error codes enable client-side retry logic and analytics.
- **Async job tracking:** `JobResponse` model makes job status polling straightforward.

### Future Improvements

- Add rate limit metadata to responses
- Track response timing and performance metrics
- Implement distributed tracing headers

---

## 2. Model-to-Schema Separation (`backend/app/mappers.py`)

**Problem Solved:** ORM models and API schemas were tightly coupled, making database schema evolution dangerous and forcing API-level changes when business logic shifted.

**Solution:** Explicit mappers that decouple `SQLAlchemy` models from `Pydantic` schemas.

### Structure

```
Database Layer              API Layer
├── SQLAlchemy ORM    ←→    Pydantic Schemas
│   models.py         via    schemas.py
│   (User, Wine)      mappers (UserResponse, WineResponse)
└── No longer         (mappers.py)
    exposed to API
```

### Usage

```python
from backend.app.mappers import WineMapper
from backend.app.db.models import Wine

# Get wine from database (ORM model)
wine_orm = db.query(Wine).first()

# Convert to API schema for response
wine_response = WineMapper.model_to_schema(wine_orm)

# Convert incoming schema to ORM for creation
wine_create = WineCreate(name="Cabernet", region="Napa", ...)
wine_orm = WineMapper.schema_to_model(wine_create)
db.add(wine_orm)

# Batch conversion
wines = [WineMapper.model_to_schema(w) for w in wines_orm]
# or use the helper
wines = WineMapper.list_models_to_schema(wines_orm)
```

### Benefits

- **Database isolation:** Change ORM field names without breaking API contracts.
- **Schema evolution:** Add/remove DB columns without coordinating API versioning.
- **Type safety:** Explicit conversion logic catches mismatches early.
- **Testing:** Mock mappers independently from database.

### Adding New Mappers

When adding a new entity:

1. Create ORM model in `backend/app/db/models.py`
2. Create Pydantic schema in `backend/app/schemas.py`
3. Add mapper class in `backend/app/mappers.py`
4. Use mapper in service layer

---

## 3. Centralized Configuration (`backend/app/core/config.py`)

**Problem Solved:** Settings scattered across files and hardcoded values made feature toggling, environment-specific tuning, and team onboarding difficult.

**Solution:** Single `Settings` class with environment-based configuration, feature flags, and helper methods.

### Setup

1. Create `.env` file in project root:

```bash
# .env
ENVIRONMENT=development
DEBUG=True
DATABASE_URL=postgresql://user:password@localhost/wine_o
REDIS_URL=redis://localhost:6379/0

# 3D Reconstruction
RECONSTRUCTION_QUALITY=high
SFM_ENABLE=True
PBR_QUALITY=high

# Feature Flags
FEATURE_AI_SOMMELIER_ENABLED=False
FEATURE_MARKETPLACE_ENABLED=False
```

2. Use in application:

```python
from backend.app.core.config import settings

# Access individual settings
if settings.is_production():
    db_url = settings.get_database_url()

# Get grouped settings
recon_config = settings.get_reconstruction_settings()
ocr_config = settings.get_ocr_settings()
feature_flags = settings.get_feature_flags()
```

3. Toggle features without code changes:

```python
# In router
from backend.app.core.config import settings

@router.post("/ai/sommelier")
async def get_sommelier_notes(wine_id: int):
    if not settings.FEATURE_AI_SOMMELIER_ENABLED:
        raise HTTPException(status_code=404, detail="Feature not available")
    # ... implementation
```

### Configuration Categories

| Category | Examples |
|----------|----------|
| **Core** | DEBUG, ENVIRONMENT, SECRET_KEY |
| **Database** | DATABASE_URL, POOL_SIZE, ECHO |
| **Auth** | JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES |
| **3D** | RECONSTRUCTION_QUALITY, SFM_ENABLE, PBR_QUALITY |
| **OCR** | OCR_PROVIDER, CONFIDENCE_THRESHOLD |
| **AI** | AI_MODEL, DEVICE (cpu/cuda/mps) |
| **Features** | FEATURE_AI_SOMMELIER_ENABLED, FEATURE_MARKETPLACE_ENABLED |
| **Storage** | S3_BUCKET_NAME, CDN_URL |
| **Queue** | CELERY_BROKER_URL, TASK_TIMEOUT |

### Benefits

- **No code changes for deployment:** Environment differences managed via `.env`.
- **Feature toggling:** Enable/disable roadmap features without deployment.
- **Team onboarding:** New developers copy `.env.example` with sensible defaults.
- **A/B testing:** Toggle features for specific users/environments.
- **Multi-tenancy ready:** Different configs per tenant.

### Adding New Settings

1. Add field to `Settings` class with type and default
2. Add to `.env.example`
3. Access via `settings.<FIELD_NAME>`

Example:

```python
# In Settings class
FEATURE_VECTOR_SEARCH_ENABLED: bool = False
PINECONE_API_KEY: str = ""
EMBEDDING_MODEL: str = "openai/text-embedding-3-small"
```

---

## Integration Example: Adding AI Sommelier Feature

Here's how these three improvements work together for future development:

### 1. Create schema & model
```python
# backend/app/schemas.py
class SommelierNotes(BaseModel):
    wine_id: int
    food_pairings: list[str]
    similar_wines: list[str]
    storage_advice: str
    
# backend/app/db/models.py
class SommelierAnalysis(Base):
    __tablename__ = "sommelier_analyses"
    wine_id = Column(Integer, ForeignKey("wines.id"))
    food_pairings = Column(JSON)
    # ...
```

### 2. Create mapper
```python
# backend/app/mappers.py
class SommelierMapper:
    @staticmethod
    def model_to_schema(analysis: SommelierAnalysis) -> SommelierNotes:
        return SommelierNotes(...)
```

### 3. Use unified response
```python
# backend/app/api/routers/sommelier.py
from backend.app.core.responses import ServiceResponse

@router.get("/wines/{wine_id}/sommelier")
async def get_sommelier_notes(wine_id: int):
    if not settings.FEATURE_AI_SOMMELIER_ENABLED:
        return ServiceResponse.error("Feature not available", code="FEATURE_DISABLED")
    
    analysis = await sommelier_service.analyze(wine_id)
    return ServiceResponse.ok(data=SommelierMapper.model_to_schema(analysis))
```

### 4. Configure via settings
```bash
# .env
FEATURE_AI_SOMMELIER_ENABLED=True
AI_MODEL_ENDPOINT=https://sommelier-ai.wine-o.com
AI_TIMEOUT_SECONDS=30
```

Done! No structural changes to existing code. The three improvements provide a clean foundation for this and future features.

---

## Testing Architecture

With these improvements, testing becomes more focused:

```python
# Test mapper isolation
def test_wine_mapper():
    wine_orm = Wine(name="Cab", region="Napa")
    schema = WineMapper.model_to_schema(wine_orm)
    assert schema.name == "Cab"

# Test service with mocked mapper
def test_wine_service():
    mock_mapper = Mock()
    service = WineService(mapper=mock_mapper)
    
# Test configuration
def test_feature_flags():
    settings = Settings(FEATURE_AI_SOMMELIER_ENABLED=True)
    assert settings.get_feature_flags()["ai_sommelier"] is True
```

---

## Checklist for Future Features

When implementing features from the roadmap:

- [ ] Define ORM models in `backend/app/db/models.py`
- [ ] Define Pydantic schemas in `backend/app/schemas.py`
- [ ] Create mapper class in `backend/app/mappers.py`
- [ ] Add feature flag in `backend/app/core/config.py`
- [ ] Use `ServiceResponse` for all API responses
- [ ] Add to `.env.example` with defaults
- [ ] Document in this file or in module docstrings

---

## References

- **Responses:** `backend/app/core/responses.py` - Full implementation
- **Mappers:** `backend/app/mappers.py` - All available mappers
- **Config:** `backend/app/core/config.py` - Full settings reference
- **Models:** `backend/app/db/models.py` - ORM definitions
- **Schemas:** `backend/app/schemas.py` - API contracts
