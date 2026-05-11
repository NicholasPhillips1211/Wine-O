from fastapi import APIRouter, Depends

from backend.app.schemas import EmailVerificationRequest, LoginRequest, TokenResponse, UserCreate, UserResponse
from backend.app.services.auth_service import AuthService


router = APIRouter(prefix="/auth", tags=["auth"])


def get_auth_service() -> AuthService:
    """Dependency injection for auth service."""
    return AuthService()


@router.post("/register", response_model=UserResponse)
async def register(
    user: UserCreate,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Register a new user with email and password."""
    return auth_service.register_user(user)


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Authenticate user and return JWT token."""
    result = auth_service.login(credentials)
    if result is None:
        return {"error": "Invalid credentials"}, 401
    return result


@router.post("/verify-email")
async def verify_email(
    request: EmailVerificationRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Verify user email with token."""
    return auth_service.verify_email(request)


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    auth_service: AuthService = Depends(get_auth_service)
):
    """Get current authenticated user info."""
    # TODO: Extract user_id from JWT token in request header
    user_id = 1  # Placeholder
    return auth_service.get_current_user(user_id)