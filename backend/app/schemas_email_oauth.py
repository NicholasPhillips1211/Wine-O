"""Pydantic schemas for email and OAuth domain."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class EmailRequest(BaseModel):
    """Request to send email."""
    recipient_email: str
    subject: str
    body: str
    html_body: Optional[str] = None
    reply_to: Optional[str] = None


class EmailVerificationRequest(BaseModel):
    """Request to send verification email."""
    email: str
    verification_link: str


class EmailVerificationResult(BaseModel):
    """Result of email verification sending."""
    email: str
    sent_at: datetime
    delivery_status: str = "queued"  # queued, sent, failed
    message_id: Optional[str] = None


class PasswordResetRequest(BaseModel):
    """Request to send password reset email."""
    email: str
    reset_link: str


class PasswordResetResult(BaseModel):
    """Result of password reset email sending."""
    email: str
    sent_at: datetime
    delivery_status: str = "queued"


class OAuthProvider(BaseModel):
    """OAuth provider configuration."""
    provider_name: str = Field(..., pattern="^(google|apple|github|microsoft)$")
    client_id: str
    client_secret: str
    redirect_uri: str
    scopes: list[str] = Field(default_factory=list)


class OAuthAuthorizationRequest(BaseModel):
    """Request to start OAuth flow."""
    provider: str = Field(..., pattern="^(google|apple|github|microsoft)$")
    redirect_uri: str


class OAuthAuthorizationResponse(BaseModel):
    """Authorization URL for OAuth flow."""
    provider: str
    authorization_url: str
    state: str
    expires_in_seconds: int = 600


class OAuthCallbackRequest(BaseModel):
    """Callback from OAuth provider."""
    provider: str
    code: str
    state: str
    error: Optional[str] = None


class OAuthTokenResponse(BaseModel):
    """OAuth token response."""
    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    refresh_token: Optional[str] = None
    id_token: Optional[str] = None


class OAuthUserProfile(BaseModel):
    """User profile from OAuth provider."""
    provider: str
    provider_user_id: str
    email: str
    full_name: Optional[str] = None
    picture_url: Optional[str] = None
    verified_email: bool = False


class OAuthLinkRequest(BaseModel):
    """Request to link OAuth account to existing user."""
    user_id: int
    provider: str
    provider_user_id: str


class OAuthLinkResult(BaseModel):
    """Result of linking OAuth account."""
    user_id: int
    provider: str
    linked_at: datetime
    is_primary: bool


class EmailTemplate(BaseModel):
    """Email template configuration."""
    template_name: str
    subject_template: str
    html_template: str
    text_template: Optional[str] = None
    required_variables: list[str] = Field(default_factory=list)


class EmailLog(BaseModel):
    """Email sending log entry."""
    email_id: str
    recipient: str
    subject: str
    status: str = Field(..., pattern="^(queued|sent|failed|bounced)$")
    sent_at: Optional[datetime] = None
    failed_reason: Optional[str] = None
    retry_count: int = 0
    created_at: datetime


class OAuthSessionState(BaseModel):
    """OAuth session state tracking."""
    state: str
    provider: str
    created_at: datetime
    expires_at: datetime
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
