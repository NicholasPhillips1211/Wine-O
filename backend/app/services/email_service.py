"""Email service for sending transactional emails."""

import os
from datetime import datetime
from typing import Optional

from backend.app.schemas_email_oauth import (
    EmailRequest,
    EmailVerificationRequest,
    EmailVerificationResult,
    PasswordResetRequest,
    PasswordResetResult,
)
from backend.app.services import BaseService


class EmailService(BaseService):
    """Service layer for email operations.
    
    Handles transactional email delivery for user authentication and notifications.
    Supports email verification, password reset, welcome emails, and general notifications.
    Uses SMTP for email delivery (configurable to use SendGrid, AWS SES, etc.).
    
    Key capabilities:
    - Email verification links for account registration
    - Password reset workflows
    - Welcome emails for new users
    - Notification emails for system events
    - Email delivery tracking and logging
    - Retry mechanism for failed emails
    """

    def __init__(self):
        """Initialize email service with provider configuration.
        
        Reads SMTP configuration from environment variables and initializes
        connection parameters for email delivery.
        """
        # SMTP server configuration from environment or defaults
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER", "noreply@wine-o.com")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.from_email = os.getenv("FROM_EMAIL", "noreply@wine-o.com")
        # Log of sent emails for tracking and debugging
        self.email_logs = {}

    def send_email(self, request: EmailRequest) -> dict:
        """Send transactional email."""
        email_id = f"email_{int(datetime.utcnow().timestamp() * 1000)}"

        # Simulate email sending (real implementation would use smtplib or SendGrid)
        self.email_logs[email_id] = {
            "recipient": request.recipient_email,
            "subject": request.subject,
            "status": "sent",
            "sent_at": datetime.utcnow().isoformat(),
        }

        return {
            "email_id": email_id,
            "recipient": request.recipient_email,
            "subject": request.subject,
            "status": "sent",
            "sent_at": datetime.utcnow().isoformat(),
        }

    def send_verification_email(self, request: EmailVerificationRequest) -> EmailVerificationResult:
        """Send email verification link."""
        verification_request = EmailRequest(
            recipient_email=request.email,
            subject="Verify your Wine-O Account",
            html_body=f"""
            <h1>Welcome to Wine-O</h1>
            <p>Please verify your email address by clicking the link below:</p>
            <a href="{request.verification_link}">Verify Email</a>
            <p>This link expires in 24 hours.</p>
            """,
            body=f"Click here to verify: {request.verification_link}",
        )

        email_result = self.send_email(verification_request)

        return EmailVerificationResult(
            email=request.email,
            sent_at=datetime.utcnow(),
            delivery_status="sent",
            message_id=email_result["email_id"],
        )

    def send_password_reset_email(self, request: PasswordResetRequest) -> PasswordResetResult:
        """Send password reset link."""
        reset_request = EmailRequest(
            recipient_email=request.email,
            subject="Reset your Wine-O Password",
            html_body=f"""
            <h1>Password Reset Request</h1>
            <p>Click the link below to reset your password:</p>
            <a href="{request.reset_link}">Reset Password</a>
            <p>This link expires in 1 hour.</p>
            <p>If you didn't request this, please ignore this email.</p>
            """,
            body=f"Click here to reset your password: {request.reset_link}",
        )

        email_result = self.send_email(reset_request)

        return PasswordResetResult(
            email=request.email,
            sent_at=datetime.utcnow(),
            delivery_status="sent",
            message_id=email_result["email_id"],
        )

    def send_welcome_email(self, email: str, full_name: Optional[str] = None) -> dict:
        """Send welcome email to new user."""
        name = full_name if full_name else email.split("@")[0]
        welcome_request = EmailRequest(
            recipient_email=email,
            subject="Welcome to Wine-O!",
            html_body=f"""
            <h1>Welcome, {name}!</h1>
            <p>Your account has been successfully created.</p>
            <p>Start exploring wines, building collections, and leveraging AI for wine analysis.</p>
            <a href="https://wine-o.app/dashboard">Go to Dashboard</a>
            """,
            body=f"Welcome {name}! Your account is ready.",
        )

        return self.send_email(welcome_request)

    def send_notification_email(
        self, email: str, subject: str, message: str, html_message: Optional[str] = None
    ) -> dict:
        """Send notification email.
        
        Sends a general-purpose notification email (system alerts, activity updates,
        recommendations, etc.). Supports both plain text and HTML formatting.
        
        Args:
            email: Recipient email address
            subject: Email subject line
            message: Plain text message body
            html_message: Optional HTML formatted message
            
        Returns:
            Dictionary with email delivery status
        """
        notification_request = EmailRequest(
            recipient_email=email,
            subject=subject,
            body=message,
            html_body=html_message,
        )

        return self.send_email(notification_request)

    def get_email_log(self, email_id: str) -> Optional[dict]:
        """Get email sending log."""
        return self.email_logs.get(email_id)

    def retry_failed_emails(self, max_retries: int = 3) -> dict:
        """Retry sending failed emails."""
        retried = 0
        for email_id, log in self.email_logs.items():
            if log["status"] == "failed" and log.get("retry_count", 0) < max_retries:
                # Simulate retry
                log["retry_count"] = log.get("retry_count", 0) + 1
                log["status"] = "sent"
                retried += 1

        return {"retried": retried, "total_emails": len(self.email_logs)}
