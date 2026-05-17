"""Persistence bridge for reconstruction job state snapshots."""

from __future__ import annotations

from datetime import datetime, timezone

from backend.app.db.models import Reconstruction
from backend.app.db.session import SessionLocal


class ReconstructionPersistence:
    """Stores job status snapshots in the reconstructions table."""

    def sync_job(self, *, job_id: str, status: str, quality: str = "high", confidence: float | None = None, error_message: str | None = None) -> None:
        db = SessionLocal()
        try:
            row = db.query(Reconstruction).filter(Reconstruction.reconstruction_id == job_id).first()
            if row is None:
                row = Reconstruction(
                    reconstruction_id=job_id,
                    status=status,
                    quality_setting=quality,
                    confidence_score=confidence,
                    created_at=datetime.now(timezone.utc),
                )
                db.add(row)
            else:
                row.status = status
                row.quality_setting = quality
                row.confidence_score = confidence
                row.error_message = error_message
                if status in {"completed", "failed"}:
                    row.completed_at = datetime.now(timezone.utc)
            db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()


persistence = ReconstructionPersistence()
