"""Email API endpoints for sending transactional emails."""

from fastapi import APIRouter, Depends

from backend.app.schemas_email_oauth import (
    EmailRequest,
    EmailVerificationRequest,
    EmailVerificationResult,
    PasswordResetRequest,
    PasswordResetResult,
)
from backend.app.services.email_service import EmailService


router = APIRouter(prefix="/email", tags=["email"])


def get_email_service() -> EmailService:
    """Dependency: get email service instance."""
    return EmailService()


@router.post("/send", response_model=dict)
async def send_email(
    request: EmailRequest,
    email_service: EmailService = Depends(get_email_service),
) -> dict:
    """Send transactional email."""
    return email_service.send_email(request)


@router.post("/verify", response_model=EmailVerificationResult)
async def send_verification_email(
    request: EmailVerificationRequest,
    email_service: EmailService = Depends(get_email_service),
) -> EmailVerificationResult:
    """Send email verification link."""
    return email_service.send_verification_email(request)


@router.post("/password-reset", response_model=PasswordResetResult)
async def send_password_reset_email(
    request: PasswordResetRequest,
    email_service: EmailService = Depends(get_email_service),
) -> PasswordResetResult:
    """Send password reset link."""
    return email_service.send_password_reset_email(request)


@router.post("/welcome")
async def send_welcome_email(
    email: str,
    full_name: str = None,
    email_service: EmailService = Depends(get_email_service),
) -> dict:
    """Send welcome email to new user."""
    return email_service.send_welcome_email(email, full_name)


@router.post("/notify")
async def send_notification_email(
    email: str,
    subject: str,
    message: str,
    html_message: str = None,
    email_service: EmailService = Depends(get_email_service),
) -> dict:
    """Send notification email."""
    return email_service.send_notification_email(email, subject, message, html_message)


@router.get("/log/{email_id}")
async def get_email_log(
    email_id: str,
    email_service: EmailService = Depends(get_email_service),
) -> dict:
    """Get email sending log."""
    log = email_service.get_email_log(email_id)
    if not log:
        return {"error": "Email log not found"}
    return log


@router.post("/retry")
async def retry_failed_emails(
    max_retries: int = 3,
    email_service: EmailService = Depends(get_email_service),
) -> dict:
    """Retry sending failed emails."""
    return email_service.retry_failed_emails(max_retries)


@router.get("/status")
async def status():
    """Service health check."""
    return {"service": "email", "status": "operational"}
