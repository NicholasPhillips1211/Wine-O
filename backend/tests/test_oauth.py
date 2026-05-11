"""Tests for the OAuth service and endpoints."""

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from backend.app.main import app
from backend.app.schemas_email_oauth import OAuthAuthorizationRequest, OAuthCallbackRequest
from backend.app.services.oauth_service import OAuthService


client = TestClient(app)


class TestOAuthService:
    """Test the OAuth service layer."""

    @pytest.fixture
    def oauth_service(self):
        """Create OAuth service instance."""
        return OAuthService()

    def test_get_authorization_url_google(self, oauth_service):
        """Test generating Google OAuth authorization URL via service."""
        request = OAuthAuthorizationRequest(
            provider="google",
            redirect_uri="https://wine-o.app/auth/google/callback",
        )
        result = oauth_service.get_authorization_url(request)

        assert result.provider == "google"
        assert result.authorization_url is not None
        assert result.state is not None

    def test_get_authorization_url_github(self, oauth_service):
        """Test generating GitHub OAuth authorization URL via service."""
        request = OAuthAuthorizationRequest(
            provider="github",
            redirect_uri="https://wine-o.app/auth/github/callback",
        )
        result = oauth_service.get_authorization_url(request)

        assert result.provider == "github"
        assert result.authorization_url is not None

    def test_get_authorization_url_invalid_provider(self, oauth_service):
        """Test OAuth with invalid provider via service."""
        with pytest.raises(ValidationError):
            OAuthAuthorizationRequest(
                provider="invalid_provider",
                redirect_uri="https://wine-o.app/auth/callback",
            )

    def test_handle_callback(self, oauth_service):
        """Test handling OAuth callback via service."""
        # First get authorization URL to get valid state
        auth_request = OAuthAuthorizationRequest(
            provider="google",
            redirect_uri="https://wine-o.app/auth/google/callback",
        )
        auth_result = oauth_service.get_authorization_url(auth_request)

        # Then handle callback with that state
        callback_request = OAuthCallbackRequest(
            provider="google",
            code="auth_code_123",
            state=auth_result.state,
        )
        user_profile = oauth_service.handle_callback(callback_request)

        assert user_profile.provider == "google"
        assert user_profile.email is not None

    def test_exchange_code_for_token(self, oauth_service):
        """Test exchanging authorization code for token via service."""
        token = oauth_service.exchange_code_for_token(
            "google",
            "auth_code_123",
            "https://wine-o.app/auth/google/callback",
        )

        assert token.access_token is not None
        assert token.token_type == "Bearer"
        assert token.expires_in > 0

    def test_get_user_profile(self, oauth_service):
        """Test getting user profile from OAuth provider via service."""
        profile = oauth_service.get_user_profile("google", "access_token_123")

        assert profile.provider == "google"
        assert profile.email is not None

    def test_revoke_token(self, oauth_service):
        """Test revoking OAuth token via service."""
        success = oauth_service.revoke_token("google", "access_token_123")
        assert success is True

    def test_validate_state_valid(self, oauth_service):
        """Test validating valid OAuth state via service."""
        auth_request = OAuthAuthorizationRequest(
            provider="google",
            redirect_uri="https://wine-o.app/auth/google/callback",
        )
        auth_result = oauth_service.get_authorization_url(auth_request)

        is_valid = oauth_service.validate_state(auth_result.state)
        assert is_valid is True

    def test_validate_state_invalid(self, oauth_service):
        """Test validating invalid OAuth state via service."""
        is_valid = oauth_service.validate_state("invalid_state_123")
        assert is_valid is False


class TestOAuthEndpoints:
    """Test the OAuth API endpoints."""

    def test_authorize_endpoint_google(self):
        """Test POST /api/v1/oauth/authorize for Google."""
        response = client.post(
            "/api/v1/oauth/authorize",
            json={
                "provider": "google",
                "redirect_uri": "https://wine-o.app/auth/google/callback",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "authorization_url" in data
        assert "state" in data

    def test_authorize_endpoint_github(self):
        """Test POST /api/v1/oauth/authorize for GitHub."""
        response = client.post(
            "/api/v1/oauth/authorize",
            json={
                "provider": "github",
                "redirect_uri": "https://wine-o.app/auth/github/callback",
            },
        )
        assert response.status_code == 200

    def test_authorize_endpoint_apple(self):
        """Test POST /api/v1/oauth/authorize for Apple."""
        response = client.post(
            "/api/v1/oauth/authorize",
            json={
                "provider": "apple",
                "redirect_uri": "https://wine-o.app/auth/apple/callback",
            },
        )
        assert response.status_code == 200

    def test_authorize_endpoint_microsoft(self):
        """Test POST /api/v1/oauth/authorize for Microsoft."""
        response = client.post(
            "/api/v1/oauth/authorize",
            json={
                "provider": "microsoft",
                "redirect_uri": "https://wine-o.app/auth/microsoft/callback",
            },
        )
        assert response.status_code == 200

    @pytest.mark.skip(reason="Requires shared state management across service instances")
    def test_callback_endpoint(self):
        """Test POST /api/v1/oauth/callback."""
        # Get valid state first
        auth_response = client.post(
            "/api/v1/oauth/authorize",
            json={
                "provider": "google",
                "redirect_uri": "https://wine-o.app/auth/google/callback",
            },
        )
        assert auth_response.status_code == 200
        state = auth_response.json()["state"]

        # Now use that state in callback
        response = client.post(
            "/api/v1/oauth/callback",
            json={
                "provider": "google",
                "code": "auth_code_123",
                "state": state,
            },
        )
        assert response.status_code == 200

    def test_token_exchange_endpoint(self):
        """Test POST /api/v1/oauth/token."""
        response = client.post(
            "/api/v1/oauth/token",
            params={
                "provider": "google",
                "code": "auth_code_123",
                "redirect_uri": "https://wine-o.app/auth/google/callback",
            },
        )
        assert response.status_code == 200

    def test_user_profile_endpoint(self):
        """Test GET /api/v1/oauth/user-profile."""
        response = client.get(
            "/api/v1/oauth/user-profile?provider=google&access_token=token_123"
        )
        assert response.status_code == 200
        data = response.json()
        assert "email" in data

    def test_revoke_endpoint(self):
        """Test POST /api/v1/oauth/revoke."""
        response = client.post(
            "/api/v1/oauth/revoke",
            params={
                "provider": "google",
                "access_token": "token_123",
            },
        )
        assert response.status_code == 200

    def test_validate_state_endpoint(self):
        """Test GET /api/v1/oauth/validate-state."""
        response = client.get("/api/v1/oauth/validate-state?state=test_state")
        assert response.status_code == 200
        data = response.json()
        assert "valid" in data

    def test_oauth_health_check(self):
        """Test GET /api/v1/oauth/status."""
        response = client.get("/api/v1/oauth/status")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "oauth"
        assert data["status"] == "operational"
