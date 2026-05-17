"""Object storage abstraction for reconstruction artifacts."""

from __future__ import annotations

from backend.app.core.config import settings


class ObjectStorageService:
    """Build object keys and public URLs for generated assets."""

    def build_key(self, job_id: str, artifact_name: str) -> str:
        return f"reconstruction/{job_id}/{artifact_name}"

    def public_url(self, object_key: str) -> str:
        base = settings.CDN_URL.rstrip("/")
        return f"{base}/{object_key}"

    def upload_stub(self, job_id: str, artifact_name: str) -> dict:
        key = self.build_key(job_id, artifact_name)
        return {
            "object_key": key,
            "url": self.public_url(key),
            "provider": "s3_or_r2",
            "bucket": settings.S3_BUCKET_NAME,
        }


object_storage = ObjectStorageService()
