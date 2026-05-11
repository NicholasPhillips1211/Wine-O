"""OAuth API endpoints for external authentication."""

from fastapi import APIRouter, Depends

from backend.app.schemas_email_oauth import (
    OAuthAuthorizationRequest,
    OAuthAuthorizationResponse,
    OAuthCallbackRequest,
    OAuthUserProfile,
    OAuthTokenResponse,
)
from backend.app.services.oauth_service import OAuthService


router = APIRouter(prefix="/oauth", tags=["oauth"])


def get_oauth_service() -> OAuthService:
    """Dependency: get OAuth service instance."""
    return OAuthService()


@router.post("/authorize", response_model=OAuthAuthorizationResponse)
async def authorize(
    request: OAuthAuthorizationRequest,
    oauth_service: OAuthService = Depends(get_oauth_service),
) -> OAuthAuthorizationResponse:
    """Get OAuth authorization URL."""
    return oauth_service.get_authorization_url(request)


@router.post("/callback", response_model=OAuthUserProfile)
async def callback(
    request: OAuthCallbackRequest,
    oauth_service: OAuthService = Depends(get_oauth_service),
) -> OAuthUserProfile:
    """Handle OAuth provider callback."""
    return oauth_service.handle_callback(request)


@router.post("/token", response_model=OAuthTokenResponse)
async def exchange_code_for_token(
    provider: str,
    code: str,
    redirect_uri: str,
    oauth_service: OAuthService = Depends(get_oauth_service),
) -> OAuthTokenResponse:
    """Exchange authorization code for access token."""
    return oauth_service.exchange_code_for_token(provider, code, redirect_uri)


@router.get("/user-profile", response_model=OAuthUserProfile)
async def get_user_profile(
    provider: str,
    access_token: str,
    oauth_service: OAuthService = Depends(get_oauth_service),
) -> OAuthUserProfile:
    """Get user profile from OAuth provider."""
    return oauth_service.get_user_profile(provider, access_token)


@router.post("/revoke")
async def revoke_token(
    provider: str,
    access_token: str,
    oauth_service: OAuthService = Depends(get_oauth_service),
) -> dict:
    """Revoke OAuth token (logout)."""
    success = oauth_service.revoke_token(provider, access_token)
    return {"revoked": success}


@router.get("/validate-state")
async def validate_state(
    state: str,
    oauth_service: OAuthService = Depends(get_oauth_service),
) -> dict:
    """Validate OAuth state token."""
    is_valid = oauth_service.validate_state(state)
    return {"valid": is_valid}


@router.get("/status")
async def status():
    """Service health check."""
    return {"service": "oauth", "status": "operational"}
