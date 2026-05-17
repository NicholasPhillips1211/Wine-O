"""Asynchronous pipeline orchestrator for staged wine-bottle reconstruction."""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone
from threading import Lock
from typing import Any

from backend.app.reconstruction.orchestration.monitoring import monitoring
from backend.app.reconstruction.orchestration.persistence import persistence
from backend.app.reconstruction.schemas.events import ReconstructionEventType
from backend.app.reconstruction.schemas.reconstruction_job import (
    ReconstructionJob,
    ReconstructionJobStatus,
    ReconstructionStage,
)


class PipelineManager:
    """Coordinates stage scheduling, retries, and job state aggregation."""

    _stage_progress: dict[ReconstructionStage, int] = {
        ReconstructionStage.CAPTURE: 5,
        ReconstructionStage.SEGMENTATION: 20,
        ReconstructionStage.GEOMETRY: 40,
        ReconstructionStage.BLENDER_REFINEMENT: 60,
        ReconstructionStage.MATERIALS: 72,
        ReconstructionStage.OPTIMIZATION: 84,
        ReconstructionStage.EXPORT: 95,
        ReconstructionStage.DELIVERY: 100,
    }

    def __init__(self) -> None:
        self._jobs: dict[str, ReconstructionJob] = {}
        self._events: dict[str, list[dict[str, Any]]] = {}
        self._artifacts: dict[str, dict[str, Any]] = {}
        self._started_at: dict[str, float] = {}
        self._stage_started_at: dict[tuple[str, str], float] = {}
        self._lock = Lock()

    def create_job(self, user_id: str | None = None, reconstruction_version: str = "v2") -> ReconstructionJob:
        """Create and register a new job in queued state."""
        with self._lock:
            job_id = str(uuid.uuid4())
            now = datetime.now(timezone.utc)
            job = ReconstructionJob(
                id=job_id,
                user_id=user_id,
                reconstruction_version=reconstruction_version,
                created_at=now,
                updated_at=now,
            )
            self._jobs[job_id] = job
            self._events[job_id] = []
            self._artifacts[job_id] = {}
            self._started_at[job_id] = time.perf_counter()

        self.emit_event(job_id, ReconstructionEventType.JOB_CREATED, {"job_id": job_id})
        persistence.sync_job(job_id=job_id, status=ReconstructionJobStatus.QUEUED.value)
        return job

    def get_job(self, job_id: str) -> ReconstructionJob | None:
        """Return job if present."""
        return self._jobs.get(job_id)

    def get_job_status(self, job_id: str) -> dict[str, Any] | None:
        """Return a status payload optimized for polling clients."""
        job = self.get_job(job_id)
        if not job:
            return None
        return {
            "id": job.id,
            "status": job.status,
            "stage": job.stage,
            "progress_percent": job.progress_percent,
            "updated_at": job.updated_at,
            "error_message": job.error_message,
        }

    def get_job_progress(self, job_id: str) -> dict[str, Any] | None:
        """Return progress plus recent event log."""
        status = self.get_job_status(job_id)
        if not status:
            return None
        status["events"] = self._events.get(job_id, [])
        return status

    def get_artifacts(self, job_id: str) -> dict[str, Any] | None:
        """Return collected artifact references and stage outputs."""
        job = self.get_job(job_id)
        if not job:
            return None
        return {
            "job_id": job_id,
            "artifacts": self._artifacts.get(job_id, {}),
            "stage_results": {
                "segmentation": job.segmentation_result,
                "geometry": job.geometry_result,
                "blender": job.blender_result,
                "materials": job.material_result,
                "export": job.export_result,
            },
        }

    def emit_event(self, job_id: str, event_type: ReconstructionEventType, payload: dict[str, Any] | None = None) -> None:
        """Append a timeline event for observability and progress tracking."""
        event = {
            "event": event_type.value,
            "timestamp": datetime.now(timezone.utc),
            "payload": payload or {},
        }
        with self._lock:
            self._events.setdefault(job_id, []).append(event)

    def update_stage(
        self,
        job_id: str,
        stage: ReconstructionStage,
        *,
        status: ReconstructionJobStatus = ReconstructionJobStatus.RUNNING,
        result: dict[str, Any] | None = None,
        artifacts: dict[str, Any] | None = None,
    ) -> ReconstructionJob | None:
        """Update stage state, aggregate outputs, and bump progress."""
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return None

            now = datetime.now(timezone.utc)
            job.stage = stage
            job.status = status
            job.updated_at = now
            job.progress_percent = max(job.progress_percent, self._stage_progress.get(stage, job.progress_percent))

            stage_key = (job_id, stage.value)
            if stage_key not in self._stage_started_at:
                self._stage_started_at[stage_key] = time.perf_counter()

            if result:
                if "confidence" in result and isinstance(result["confidence"], (int, float)):
                    job.confidence_breakdown[stage.value] = float(result["confidence"])
                if stage == ReconstructionStage.SEGMENTATION:
                    job.segmentation_result = result
                elif stage == ReconstructionStage.GEOMETRY:
                    job.geometry_result = result
                elif stage == ReconstructionStage.BLENDER_REFINEMENT:
                    job.blender_result = result
                elif stage == ReconstructionStage.MATERIALS:
                    job.material_result = result
                elif stage in (ReconstructionStage.EXPORT, ReconstructionStage.DELIVERY):
                    job.export_result = result

            if artifacts:
                self._artifacts.setdefault(job_id, {}).update(artifacts)
                job.artifacts.update(artifacts)

            stage_elapsed_ms = (time.perf_counter() - self._stage_started_at.get(stage_key, time.perf_counter())) * 1000.0
            monitoring.mark_stage(job_id, stage.value, duration_ms=round(stage_elapsed_ms, 2))
            persistence.sync_job(
                job_id=job.id,
                status=job.status.value,
                quality=str(job.artifacts.get("capture_quality", "high")),
                confidence=job.confidence_score,
                error_message=job.error_message,
            )

            return job

    def complete_job(self, job_id: str, confidence_score: float | None = None) -> ReconstructionJob | None:
        """Mark a job completed and compute processing time."""
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return None

            elapsed = time.perf_counter() - self._started_at.get(job_id, time.perf_counter())
            job.status = ReconstructionJobStatus.COMPLETED
            job.stage = ReconstructionStage.DELIVERY
            job.progress_percent = 100
            job.processing_time = round(elapsed, 3)
            job.updated_at = datetime.now(timezone.utc)
            if confidence_score is not None:
                job.confidence_score = confidence_score
            elif job.confidence_breakdown:
                values = list(job.confidence_breakdown.values())
                job.confidence_score = round(sum(values) / len(values), 3)

            persistence.sync_job(
                job_id=job.id,
                status=job.status.value,
                quality=str(job.artifacts.get("capture_quality", "high")),
                confidence=job.confidence_score,
                error_message=job.error_message,
            )
            return job

    def fail_job(self, job_id: str, error_message: str) -> ReconstructionJob | None:
        """Mark a job failed and emit a failure event."""
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return None
            job.status = ReconstructionJobStatus.FAILED
            job.error_message = error_message
            job.updated_at = datetime.now(timezone.utc)

        monitoring.mark_failure(self._jobs[job_id].stage.value if job_id in self._jobs else "unknown")
        persistence.sync_job(
            job_id=job_id,
            status=ReconstructionJobStatus.FAILED.value,
            quality=str(self._jobs[job_id].artifacts.get("capture_quality", "high")) if job_id in self._jobs else "high",
            confidence=self._jobs[job_id].confidence_score if job_id in self._jobs else None,
            error_message=error_message,
        )
        self.emit_event(job_id, ReconstructionEventType.JOB_FAILED, {"error": error_message})
        return self._jobs.get(job_id)


pipeline_manager = PipelineManager()
