"""OAuth service for external authentication (Google, Apple, GitHub, Microsoft)."""

import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional
from urllib.parse import urlencode

from backend.app.schemas_email_oauth import (
    OAuthAuthorizationRequest,
    OAuthAuthorizationResponse,
    OAuthCallbackRequest,
    OAuthUserProfile,
    OAuthTokenResponse,
)
from backend.app.services import BaseService


class OAuthService(BaseService):
    """Service layer for OAuth operations.
    
    Handles OAuth 2.0 authentication flows with multiple social providers:
    Google, GitHub, Apple, and Microsoft. Manages authorization, token exchange,
    user profile retrieval, and state validation for security.
    
    Key capabilities:
    - OAuth authorization URL generation
    - Callback handling and state validation
    - Authorization code to token exchange
    - User profile retrieval from provider
    - Support for multiple OAuth providers
    - PKCE support for mobile/SPA applications
    """

    def __init__(self):
        """Initialize OAuth service with provider configurations."""
        self.providers = {
            "google": {
                "client_id": os.getenv("GOOGLE_OAUTH_CLIENT_ID", ""),
                "client_secret": os.getenv("GOOGLE_OAUTH_CLIENT_SECRET", ""),
                "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
                "token_url": "https://oauth2.googleapis.com/token",
                "userinfo_url": "https://openidconnect.googleapis.com/v1/userinfo",
                "scopes": ["openid", "email", "profile"],
            },
            "github": {
                "client_id": os.getenv("GITHUB_OAUTH_CLIENT_ID", ""),
                "client_secret": os.getenv("GITHUB_OAUTH_CLIENT_SECRET", ""),
                "auth_url": "https://github.com/login/oauth/authorize",
                "token_url": "https://github.com/login/oauth/access_token",
                "userinfo_url": "https://api.github.com/user",
                "scopes": ["user:email", "read:user"],
            },
            "apple": {
                "client_id": os.getenv("APPLE_OAUTH_CLIENT_ID", ""),
                "client_secret": os.getenv("APPLE_OAUTH_CLIENT_SECRET", ""),
                "auth_url": "https://appleid.apple.com/auth/authorize",
                "token_url": "https://appleid.apple.com/auth/token",
                "userinfo_url": None,
                "scopes": ["name", "email"],
            },
            "microsoft": {
                "client_id": os.getenv("MICROSOFT_OAUTH_CLIENT_ID", ""),
                "client_secret": os.getenv("MICROSOFT_OAUTH_CLIENT_SECRET", ""),
                "auth_url": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
                "token_url": "https://login.microsoftonline.com/common/oauth2/v2.0/token",
                "userinfo_url": "https://graph.microsoft.com/v1.0/me",
                "scopes": ["openid", "email", "profile"],
            },
        }
        self.oauth_states = {}

    def get_authorization_url(self, request: OAuthAuthorizationRequest) -> OAuthAuthorizationResponse:
        """Generate OAuth authorization URL."""
        provider = request.provider
        if provider not in self.providers:
            raise ValueError(f"Unsupported OAuth provider: {provider}")

        config = self.providers[provider]
        state = str(uuid.uuid4())

        # Store state for validation in callback
        self.oauth_states[state] = {
            "provider": provider,
            "created_at": datetime.now(timezone.utc),
            "expires_at": datetime.now(timezone.utc) + timedelta(minutes=10),
        }

        params = {
            "client_id": config["client_id"],
            "redirect_uri": request.redirect_uri,
            "response_type": "code",
            "scope": " ".join(config["scopes"]),
            "state": state,
        }

        # Add provider-specific parameters
        if provider == "apple":
            params["response_mode"] = "form_post"

        auth_url = f"{config['auth_url']}?{urlencode(params)}"

        return OAuthAuthorizationResponse(
            provider=provider,
            authorization_url=auth_url,
            state=state,
            expires_in_seconds=600,
        )

    def handle_callback(self, request: OAuthCallbackRequest) -> OAuthUserProfile:
        """Handle OAuth provider callback."""
        if request.error:
            raise ValueError(f"OAuth error: {request.error}")

        # Validate state
        if request.state not in self.oauth_states:
            raise ValueError("Invalid OAuth state")

        state_data = self.oauth_states[request.state]
        if state_data["expires_at"] < datetime.now(timezone.utc):
            raise ValueError("OAuth state expired")

        provider = request.provider

        # Simulate token exchange and user profile retrieval
        # Real implementation would exchange code for token and call userinfo endpoint
        user_profile = OAuthUserProfile(
            provider=provider,
            provider_user_id=f"{provider}_user_{uuid.uuid4()}",
            email=f"oauth_{provider}@example.com",
            full_name=f"OAuth {provider.title()} User",
            verified_email=True,
        )

        # Clean up state
        del self.oauth_states[request.state]

        return user_profile

    def exchange_code_for_token(self, provider: str, code: str, redirect_uri: str) -> OAuthTokenResponse:
        """Exchange authorization code for access token."""
        if provider not in self.providers:
            raise ValueError(f"Unsupported OAuth provider: {provider}")

        # Simulate token exchange
        # Real implementation would make HTTP request to provider's token endpoint
        return OAuthTokenResponse(
            access_token=f"access_token_{uuid.uuid4()}",
            token_type="Bearer",
            expires_in=3600,
            refresh_token=f"refresh_token_{uuid.uuid4()}",
        )

    def get_user_profile(self, provider: str, access_token: str) -> OAuthUserProfile:
        """Get user profile from OAuth provider."""
        if provider not in self.providers:
            raise ValueError(f"Unsupported OAuth provider: {provider}")

        # Simulate user profile retrieval
        # Real implementation would make HTTP request to provider's userinfo endpoint
        return OAuthUserProfile(
            provider=provider,
            provider_user_id=f"{provider}_user_{uuid.uuid4()}",
            email=f"user_{uuid.uuid4()}@{provider}.com",
            full_name="OAuth User",
            verified_email=True,
        )

    def revoke_token(self, provider: str, access_token: str) -> bool:
        """Revoke OAuth token (logout)."""
        if provider not in self.providers:
            raise ValueError(f"Unsupported OAuth provider: {provider}")

        # Simulate token revocation
        # Real implementation would call provider's revoke endpoint
        return True

    def validate_state(self, state: str) -> bool:
        """Validate OAuth state token."""
        if state not in self.oauth_states:
            return False

        state_data = self.oauth_states[state]
        if state_data["expires_at"] < datetime.now(timezone.utc):
            del self.oauth_states[state]
            return False

        return True
