# Backend Architecture - Modular Service Layer Pattern

The Wine-O backend follows a clean, modular architecture with clear separation of concerns:

## Layer Structure

### 1. **API Routes** (`backend/app/api/routers/`)
- Handle HTTP requests/responses
- Parse and validate input (via Pydantic schemas)
- Delegate business logic to services
- Return formatted responses

Example: `auth.py` routes receive requests, call `AuthService`, return results.

### 2. **Service Layer** (`backend/app/services/`)
- Contain all business logic
- Database operations (will use ORM)
- Business rules and validations
- Independent of HTTP - testable in isolation
- Can be reused by different interfaces (API, CLI, webhooks, etc.)

Example: `AuthService` handles registration, login, token generation, user lookup.

### 3. **Schemas** (`backend/app/schemas.py`)
- Pydantic models for request/response validation
- Data structure definitions
- Type hints and documentation

Example: `UserCreate`, `LoginRequest`, `TokenResponse`

### 4. **Utilities** (`backend/app/security.py`)
- Shared utilities like password hashing, JWT encoding/decoding
- No business logic
- Reusable across services

### 5. **Tests** (`backend/tests/`)
- Test services directly (unit tests)
- Test endpoints through HTTP (integration tests)
- Test security utilities

## Benefits

1. **Testability**: Services can be tested without HTTP layer
2. **Reusability**: Same service can be used by API, CLI, webhooks, etc.
3. **Maintainability**: Clear separation makes changes easier
4. **Scalability**: Easy to extract services to separate microservices later
5. **Dependency Injection**: FastAPI's `Depends()` makes services testable with mocks

## Future Modules

Apply this same pattern to other services:
- `wines_service.py` - Wine identification and data
- `ocr_service.py` - OCR operations
- `reconstruction_service.py` - 3D reconstruction orchestration
- `ai_service.py` - AI model interactions
