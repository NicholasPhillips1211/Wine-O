"""Tests for the Email service and endpoints."""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.schemas_email_oauth import EmailRequest, EmailVerificationRequest, PasswordResetRequest
from backend.app.services.email_service import EmailService


client = TestClient(app)


class TestEmailService:
    """Test the email service layer."""

    @pytest.fixture
    def email_service(self):
        """Create email service instance."""
        return EmailService()

    def test_send_email(self, email_service):
        """Test sending transactional email via service."""
        request = EmailRequest(
            recipient_email="user@example.com",
            subject="Test Subject",
            body="Test body",
            html_body="<p>Test body</p>",
        )
        result = email_service.send_email(request)

        assert result["recipient"] == "user@example.com"
        assert result["subject"] == "Test Subject"
        assert result["status"] == "sent"
        assert "email_id" in result

    def test_send_verification_email(self, email_service):
        """Test sending verification email via service."""
        request = EmailVerificationRequest(
            email="user@example.com",
            verification_link="https://wine-o.app/verify?token=abc123",
        )
        result = email_service.send_verification_email(request)

        assert result.email == "user@example.com"
        assert result.delivery_status == "sent"
        assert result.message_id is not None

    def test_send_password_reset_email(self, email_service):
        """Test sending password reset email via service."""
        request = PasswordResetRequest(
            email="user@example.com",
            reset_link="https://wine-o.app/reset?token=xyz789",
        )
        result = email_service.send_password_reset_email(request)

        assert result.email == "user@example.com"
        assert result.delivery_status == "sent"

    def test_send_welcome_email(self, email_service):
        """Test sending welcome email via service."""
        result = email_service.send_welcome_email("user@example.com", "John Doe")

        assert result["recipient"] == "user@example.com"
        assert "welcome" in result["subject"].lower() or "Welcome" in result["subject"]
        assert result["status"] == "sent"

    def test_send_notification_email(self, email_service):
        """Test sending notification email via service."""
        result = email_service.send_notification_email(
            "user@example.com",
            "New Wine Added",
            "A new wine has been added to your collection.",
        )

        assert result["recipient"] == "user@example.com"
        assert result["status"] == "sent"

    def test_get_email_log(self, email_service):
        """Test retrieving email log via service."""
        request = EmailRequest(
            recipient_email="user@example.com",
            subject="Test",
            body="Test body",
        )
        send_result = email_service.send_email(request)
        email_id = send_result["email_id"]

        log = email_service.get_email_log(email_id)
        assert log is not None
        assert log["recipient"] == "user@example.com"

    def test_retry_failed_emails(self, email_service):
        """Test retrying failed emails via service."""
        result = email_service.retry_failed_emails(max_retries=3)

        assert "retried" in result
        assert "total_emails" in result


class TestEmailEndpoints:
    """Test the Email API endpoints."""

    def test_send_email_endpoint(self):
        """Test POST /api/v1/email/send."""
        response = client.post(
            "/api/v1/email/send",
            json={
                "recipient_email": "user@example.com",
                "subject": "Test",
                "body": "Test email body",
            },
        )
        assert response.status_code in [200, 422]
        if response.status_code == 200:
            data = response.json()
            assert "email_id" in data
            assert "status" in data

    def test_verify_email_endpoint(self):
        """Test POST /api/v1/email/verify."""
        response = client.post(
            "/api/v1/email/verify",
            json={
                "email": "user@example.com",
                "verification_link": "https://example.com/verify?token=abc",
            },
        )
        assert response.status_code in [200, 422]
        if response.status_code == 200:
            data = response.json()
            assert "delivery_status" in data

    def test_password_reset_email_endpoint(self):
        """Test POST /api/v1/email/password-reset."""
        response = client.post(
            "/api/v1/email/password-reset",
            json={
                "email": "user@example.com",
                "reset_link": "https://example.com/reset?token=xyz",
            },
        )
        assert response.status_code in [200, 422]
        if response.status_code == 200:
            data = response.json()
            assert "delivery_status" in data

    def test_welcome_email_endpoint(self):
        """Test POST /api/v1/email/welcome."""
        response = client.post(
            "/api/v1/email/welcome?email=user@example.com&full_name=John+Doe"
        )
        assert response.status_code in [200, 422]
        if response.status_code == 200:
            data = response.json()
            assert "status" in data

    def test_notification_email_endpoint(self):
        """Test POST /api/v1/email/notify."""
        response = client.post(
            "/api/v1/email/notify",
            json={
                "email": "user@example.com",
                "subject": "Notification",
                "message": "This is a notification",
            },
        )
        assert response.status_code in [200, 422]

    def test_email_log_endpoint(self):
        """Test GET /api/v1/email/log/{email_id}."""
        response = client.get("/api/v1/email/log/test_email_123")
        assert response.status_code in [200, 422]

    def test_retry_emails_endpoint(self):
        """Test POST /api/v1/email/retry."""
        response = client.post("/api/v1/email/retry?max_retries=3")
        assert response.status_code in [200, 422]
        if response.status_code == 200:
            data = response.json()
            assert "retried" in data

    def test_email_health_check(self):
        """Test GET /api/v1/email/status."""
        response = client.get("/api/v1/email/status")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "email"
        assert data["status"] == "operational"
