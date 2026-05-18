"""Centralized application configuration.

ARCHITECTURAL IMPROVEMENT #5 (May 12, 2026):
Manages all environment variables, feature flags, and service settings in one place.
This makes it easy to toggle features, change providers, and configure quality settings
without modifying code across multiple services.

Before: Settings scattered across files, hardcoded values, env vars inconsistent
After: Single Settings class with 50+ configurable options, feature flags, grouped accessors

Why this matters:
- Deployment: Change config via .env, not code changes
- Feature toggling: Enable/disable roadmap items (AI sommelier, marketplace) without deployment
- Team onboarding: Copy .env.example with sensible defaults
- A/B testing: Different configs for different user groups
- Multi-tenancy: Tenant-specific configurations
- Production ready: Separate development, staging, production configs

Configuration categories:
1. Core: DEBUG, ENVIRONMENT, SECRET_KEY
2. Database: URL, connection pools, echo mode
3. Auth: JWT algorithm, token expiry, secret key
4. 3D Reconstruction: Quality levels, SFM provider, PBR settings
5. OCR: Provider (Tesseract/EasyOCR/GPT-Vision), confidence threshold
6. AI: Model selection, device (CPU/CUDA/MPS), timeouts
7. Feature flags: Enable/disable AI Sommelier, Marketplace, Social features
8. Storage: S3 bucket, CDN URL, local S3-compatible endpoints
9. Queue: Celery broker URL, task timeouts, retry counts

Setup (.env file):
    ENVIRONMENT=development
    DEBUG=True
    RECONSTRUCTION_QUALITY=high
    FEATURE_AI_SOMMELIER_ENABLED=False

Usage in code:
    from backend.app.core import settings
    if settings.is_production():
        db_url = settings.get_database_url()
    recon_config = settings.get_reconstruction_settings()
"""

from enum import Enum
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class OCRProvider(str, Enum):
    """Available OCR providers."""

    TESSERACT = "tesseract"
    EASYOCR = "easyocr"
    GPT_VISION = "gpt-vision"


class AIModel(str, Enum):
    """Available AI model providers."""

    YOLOV8 = "yolov8"
    SEGMENT_ANYTHING = "segment-anything"


class ReconstructionQuality(str, Enum):
    """Quality levels for 3D reconstruction."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class SfMProvider(str, Enum):
    """SfM (Structure from Motion) providers."""

    COLMAP = "colmap"
    FEATURE_MATCH = "feature-match"


class Settings(BaseSettings):
    """Application settings loaded from environment.
    
    ARCHITECTURAL IMPROVEMENT #5: Centralized Configuration
    
    This class manages all application configuration in one place. Settings can be:
    1. Loaded from environment variables
    2. Loaded from .env file
    3. Overridden at runtime for testing
    
    Benefits:
    - No hardcoded values in code
    - Easy feature toggling via env vars
    - Production/staging/dev configs via ENVIRONMENT variable
    - Type-safe configuration access
    - Self-documenting settings with defaults
    
    Loading order (from highest to lowest priority):
    1. Environment variables (ENVIRONMENT, DEBUG, DATABASE_URL, etc.)
    2. .env file in project root
    3. Class defaults (development-friendly defaults)
    
    For production deployment:
    - Create .env file with production values
    - Or set environment variables directly in deployment platform
    - Never commit .env to version control (use .env.example)
    
    For team members:
    - Copy .env.example to .env
    - Use development defaults
    - No special setup needed for local development
    """

    # --- Core Application Settings ---
    APP_NAME: str = "Wine-O API"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"  # development, staging, production
    API_VERSION: str = "1.0"
    SECRET_KEY: str = "your-secret-key-change-in-production"

    # --- Server Settings ---
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 4

    # --- Database Settings ---
    DATABASE_URL: str = "sqlite:///./test.db"
    DATABASE_ECHO: bool = False
    DATABASE_POOL_SIZE: int = 20
    DATABASE_POOL_RECYCLE: int = 3600

    # --- Redis Settings ---
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_TTL: int = 3600  # 1 hour

    # --- JWT & Security ---
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    JWT_ALGORITHM: str = "HS256"

    # --- Email Settings ---
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = "noreply@wine-o.com"
    SMTP_PASSWORD: str = ""
    FROM_EMAIL: str = "noreply@wine-o.com"
    VERIFICATION_TOKEN_EXPIRE_HOURS: int = 24

    # --- OAuth Settings ---
    GOOGLE_OAUTH_CLIENT_ID: str = ""
    GOOGLE_OAUTH_CLIENT_SECRET: str = ""
    GITHUB_OAUTH_CLIENT_ID: str = ""
    GITHUB_OAUTH_CLIENT_SECRET: str = ""
    APPLE_OAUTH_CLIENT_ID: str = ""
    APPLE_OAUTH_CLIENT_SECRET: str = ""
    MICROSOFT_OAUTH_CLIENT_ID: str = ""
    MICROSOFT_OAUTH_CLIENT_SECRET: str = ""

    # --- OCR Settings ---
    OCR_PROVIDER: OCRProvider = OCRProvider.TESSERACT
    OCR_CONFIDENCE_THRESHOLD: float = 0.6
    OCR_LANGUAGE: str = "eng"
    OCR_TIMEOUT_SECONDS: int = 30
    OCR_TESSERACT_CMD: str = ""

    # --- 3D Reconstruction Settings ---
    RECONSTRUCTION_QUALITY: ReconstructionQuality = ReconstructionQuality.MEDIUM
    SFM_PROVIDER: SfMProvider = SfMProvider.COLMAP
    SFM_ENABLE: bool = True
    SFM_TIMEOUT_SECONDS: int = 300  # 5 minutes
    PBR_QUALITY: str = "high"  # low, medium, high
    PERSPECTIVE_CORRECTION_ENABLE: bool = True
    LIGHTING_ESTIMATION_ENABLE: bool = True
    MESH_OPTIMIZATION_ENABLE: bool = True
    MESH_VERTEX_LIMIT: int = 100000
    TEXTURE_RESOLUTION: int = 2048  # pixels
    RECONSTRUCTION_ASYNC_ENABLED: bool = False

    # --- Blender Worker Settings ---
    BLENDER_WORKER_ENABLED: bool = False
    BLENDER_BINARY: str = "blender"
    BLENDER_SCRIPT_ROOT: str = "backend/app/reconstruction/blender/scripts"
    BLENDER_TIMEOUT_SECONDS: int = 900
    BLENDER_DOCKER_IMAGE: str = "wine-o/blender-worker:4.2"

    # --- Mobile Optimization Settings ---
    MOBILE_TRIANGLES_PREMIUM: int = 50000
    MOBILE_TRIANGLES_MOBILE: int = 25000
    MOBILE_TRIANGLES_LOW_LOD: int = 10000
    MOBILE_ENABLE_DRACO: bool = True
    MOBILE_ENABLE_KTX2: bool = True
    MOBILE_ENABLE_BASISU: bool = True

    # --- Export Validation Settings ---
    EXPORT_MAX_SIZE_MB: float = 30.0
    EXPORT_MAX_TRIANGLES: int = 50000

    # --- AI Services Settings ---
    AI_MODEL: AIModel = AIModel.YOLOV8
    AI_MODEL_ENDPOINT: str = ""  # URL for external AI service
    AI_TIMEOUT_SECONDS: int = 60
    BATCH_SIZE: int = 4
    DEVICE: str = "cpu"  # cpu, cuda, mps

    # --- Feature Flags ---
    FEATURE_OCR_ENABLED: bool = True
    FEATURE_RECONSTRUCTION_ENABLED: bool = True
    FEATURE_AI_SOMMELIER_ENABLED: bool = False
    FEATURE_MARKETPLACE_ENABLED: bool = False
    FEATURE_SOCIAL_ENABLED: bool = False
    FEATURE_ADVANCED_ANALYTICS_ENABLED: bool = False

    # --- Celery/Queue Settings ---
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    CELERY_TASK_TIMEOUT: int = 300  # 5 minutes
    CELERY_TASK_RETRY_MAX: int = 3

    # --- Storage Settings ---
    S3_BUCKET_NAME: str = "wine-o-images"
    S3_REGION: str = "us-east-1"
    S3_ACCESS_KEY: str = ""
    S3_SECRET_KEY: str = ""
    S3_ENDPOINT_URL: Optional[str] = None  # For MinIO or local S3 compatible
    CDN_URL: str = "https://cdn.wine-o.com"

    # --- Logging Settings ---
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # json, text
    SENTRY_DSN: str = ""

    # --- Pagination Defaults ---
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    # --- Rate Limiting ---
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 60

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    def get_database_url(self) -> str:
        """Get the database URL, potentially modified for testing."""
        if self.ENVIRONMENT == "testing":
            return "sqlite:///:memory:"
        return self.DATABASE_URL

    def is_production(self) -> bool:
        """Check if running in production."""
        return self.ENVIRONMENT == "production"

    def is_development(self) -> bool:
        """Check if running in development."""
        return self.ENVIRONMENT == "development"

    def get_reconstruction_settings(self) -> dict:
        """Get all reconstruction-related settings as a dictionary."""
        return {
            "quality": self.RECONSTRUCTION_QUALITY.value,
            "sfm_provider": self.SFM_PROVIDER.value,
            "sfm_enabled": self.SFM_ENABLE,
            "pbr_quality": self.PBR_QUALITY,
            "perspective_correction": self.PERSPECTIVE_CORRECTION_ENABLE,
            "lighting_estimation": self.LIGHTING_ESTIMATION_ENABLE,
            "mesh_optimization": self.MESH_OPTIMIZATION_ENABLE,
            "mesh_vertex_limit": self.MESH_VERTEX_LIMIT,
            "texture_resolution": self.TEXTURE_RESOLUTION,
            "async_enabled": self.RECONSTRUCTION_ASYNC_ENABLED,
            "blender_worker_enabled": self.BLENDER_WORKER_ENABLED,
            "blender_timeout_seconds": self.BLENDER_TIMEOUT_SECONDS,
            "blender_docker_image": self.BLENDER_DOCKER_IMAGE,
            "mobile_triangles_premium": self.MOBILE_TRIANGLES_PREMIUM,
            "mobile_triangles_mobile": self.MOBILE_TRIANGLES_MOBILE,
            "mobile_triangles_low_lod": self.MOBILE_TRIANGLES_LOW_LOD,
            "mobile_enable_draco": self.MOBILE_ENABLE_DRACO,
            "mobile_enable_ktx2": self.MOBILE_ENABLE_KTX2,
            "mobile_enable_basisu": self.MOBILE_ENABLE_BASISU,
            "export_max_size_mb": self.EXPORT_MAX_SIZE_MB,
            "export_max_triangles": self.EXPORT_MAX_TRIANGLES,
        }

    def get_ocr_settings(self) -> dict:
        """Get all OCR-related settings as a dictionary."""
        return {
            "provider": self.OCR_PROVIDER.value,
            "confidence_threshold": self.OCR_CONFIDENCE_THRESHOLD,
            "language": self.OCR_LANGUAGE,
            "timeout_seconds": self.OCR_TIMEOUT_SECONDS,
            "tesseract_cmd": self.OCR_TESSERACT_CMD,
        }

    def get_feature_flags(self) -> dict:
        """Get all feature flags as a dictionary."""
        return {
            "ocr": self.FEATURE_OCR_ENABLED,
            "reconstruction": self.FEATURE_RECONSTRUCTION_ENABLED,
            "ai_sommelier": self.FEATURE_AI_SOMMELIER_ENABLED,
            "marketplace": self.FEATURE_MARKETPLACE_ENABLED,
            "social": self.FEATURE_SOCIAL_ENABLED,
            "advanced_analytics": self.FEATURE_ADVANCED_ANALYTICS_ENABLED,
        }


# Global settings instance
settings = Settings()
