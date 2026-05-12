"""Service layer for background job submission and status lookup."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
import uuid

from celery.result import AsyncResult

from backend.app.core.celery_app import celery_app
from backend.app.schemas_jobs import JobStatusResponse, JobSubmissionResponse
from backend.app.tasks.ocr_tasks import analyze_label_task, process_image_task
from backend.app.services import BaseService


# Keep a local registry so status lookups still work when Redis is not available.
JOB_REGISTRY: dict[str, dict[str, Any]] = {}


class JobService(BaseService):
    """Service for queueing jobs and reading their status."""

    def _record_job(
        self,
        job_id: str,
        job_name: str,
        state: str,
        result: Any = None,
        error_message: str | None = None,
    ) -> None:
        """Persist the latest job snapshot for later status checks."""
        JOB_REGISTRY[job_id] = {
            "job_id": job_id,
            "job_name": job_name,
            "state": state,
            "ready": state in {"SUCCESS", "FAILURE"},
            "successful": state == "SUCCESS",
            "result": result,
            "error_message": error_message,
            "created_at": JOB_REGISTRY.get(job_id, {}).get("created_at", datetime.now(timezone.utc)),
            "updated_at": datetime.now(timezone.utc),
        }

    def _submit_task(self, task, job_name: str, *args, **kwargs) -> JobSubmissionResponse:
        """Submit a task to Celery, then fall back to eager execution if needed."""
        try:
            async_result = task.apply_async(args=args, kwargs=kwargs)
            self._record_job(async_result.id, job_name, async_result.state)
            return JobSubmissionResponse(job_id=async_result.id, job_name=job_name, state=async_result.state, detail="Queued on Celery broker")
        except Exception as exc:
            # If Redis or the worker is unavailable, execute inline so the API
            # still behaves predictably in development and test environments.
            eager_result = task.apply(args=args, kwargs=kwargs)
            job_id = eager_result.id or str(uuid.uuid4())
            self._record_job(
                job_id=job_id,
                job_name=job_name,
                state=eager_result.state,
                result=eager_result.result,
                error_message=str(exc) if eager_result.state == "FAILURE" else None,
            )
            return JobSubmissionResponse(job_id=job_id, job_name=job_name, state=eager_result.state, detail="Executed locally because the broker was unavailable")

    def queue_ocr_process(self, image_url: str, language: str = "en") -> JobSubmissionResponse:
        """Queue OCR extraction for an image URL."""
        return self._submit_task(process_image_task, "ocr.process_image", image_url, language)

    def queue_ocr_analysis(self, image_url: str, language: str = "en") -> JobSubmissionResponse:
        """Queue the combined OCR and label parsing pipeline."""
        return self._submit_task(analyze_label_task, "ocr.analyze_label", image_url, language)

    def get_job_status(self, job_id: str) -> JobStatusResponse:
        """Return the latest known state for a background job."""
        if job_id in JOB_REGISTRY:
            job = JOB_REGISTRY[job_id]
            return JobStatusResponse(**job)

        # Celery can still resolve task state when a real backend is configured.
        async_result = AsyncResult(job_id, app=celery_app)
        job_name = getattr(async_result, "name", None)
        result = async_result.result if async_result.ready() else None
        error_message = None
        if async_result.failed():
            error_message = str(async_result.result)

        return JobStatusResponse(
            job_id=job_id,
            job_name=job_name,
            state=async_result.state,
            ready=async_result.ready(),
            successful=async_result.successful() if async_result.ready() else None,
            result=result,
            error_message=error_message,
        )
