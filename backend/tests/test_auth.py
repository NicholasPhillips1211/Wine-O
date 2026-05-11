"""Tests for the auth service."""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.schemas import EmailVerificationRequest, LoginRequest, UserCreate
from backend.app.services.auth_service import AuthService


client = TestClient(app)


class TestAuthService:
    """Test the auth service layer."""

    @pytest.fixture
    def auth_service(self):
        """Create auth service instance."""
        return AuthService()

    def test_register_user(self, auth_service):
        """Test user registration via service."""
        user_data = UserCreate(
            email="test@example.com",
            password="password123",
            first_name="Test",
            last_name="User"
        )
        result = auth_service.register_user(user_data)
        
        assert result["email"] == "test@example.com"
        assert result["first_name"] == "Test"
        assert result["is_active"] is False  # Not active until email verified

    def test_login(self, auth_service):
        """Test login via service."""
        credentials = LoginRequest(
            email="test@example.com",
            password="password123"
        )
        result = auth_service.login(credentials)
        
        assert result is not None
        assert "access_token" in result
        assert result["token_type"] == "bearer"
        assert result["expires_in"] > 0

    def test_verify_email(self, auth_service):
        """Test email verification via service."""
        request = EmailVerificationRequest(token="dummy_token")
        result = auth_service.verify_email(request)
        
        assert result["verified"] is True
        assert "message" in result

    def test_get_current_user(self, auth_service):
        """Test getting current user via service."""
        result = auth_service.get_current_user(user_id=1)
        
        assert result is not None
        assert result["id"] == 1
        assert "email" in result


class TestAuthEndpoints:
    """Test the auth API endpoints."""

    def test_register_endpoint_exists(self):
        """Test that register endpoint is available."""
        response = client.post("/api/v1/auth/register", json={
            "email": "test@example.com",
            "password": "password123",
            "first_name": "Test",
            "last_name": "User"
        })
        assert response.status_code in [200, 201, 422]

    def test_login_endpoint_exists(self):
        """Test that login endpoint is available."""
        response = client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "password123"
        })
        assert response.status_code in [200, 401, 422]

    def test_verify_email_endpoint_exists(self):
        """Test that email verification endpoint is available."""
        response = client.post("/api/v1/auth/verify-email", json={
            "token": "dummy_token"
        })
        assert response.status_code in [200, 400, 422]

    def test_get_current_user_endpoint_exists(self):
        """Test that get current user endpoint is available."""
        response = client.get("/api/v1/auth/me")
        assert response.status_code in [200, 401, 422]
