"""Celery application for background jobs."""

from __future__ import annotations

import os

from celery import Celery

from backend.app.core.config import settings


# Default to Redis when available, but keep the configuration overridable so
# local development can fall back to an in-process execution path.
BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")
TASK_ALWAYS_EAGER = os.getenv("CELERY_TASK_ALWAYS_EAGER", "false").lower() == "true"

celery_app = Celery(
    "wine_o",
    broker=BROKER_URL,
    backend=RESULT_BACKEND,
    include=[
        "backend.app.tasks.ocr_tasks",
        "backend.app.tasks.reconstruction_tasks",
    ],
)

celery_app.conf.update(
    task_track_started=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_always_eager=TASK_ALWAYS_EAGER,
    task_default_queue="capture_queue",
    task_routes={
        "wine_o.reconstruction.capture": {"queue": "capture_queue"},
        "wine_o.reconstruction.segmentation": {"queue": "segmentation_queue"},
        "wine_o.reconstruction.geometry": {"queue": "geometry_queue"},
        "wine_o.reconstruction.blender": {"queue": "blender_queue"},
        "wine_o.reconstruction.materials": {"queue": "blender_queue"},
        "wine_o.reconstruction.optimization": {"queue": "optimization_queue"},
        "wine_o.reconstruction.export": {"queue": "export_queue"},
    },
)

# Global task annotations derived from settings to centralize retry/timeouts
celery_app.conf.task_annotations = {
    "*": {
        "rate_limit": "10/s",
        "time_limit": settings.CELERY_TASK_TIMEOUT,
        "soft_time_limit": max(1, settings.CELERY_TASK_TIMEOUT - 10),
        "max_retries": settings.CELERY_TASK_RETRY_MAX,
        "default_retry_delay": 5,
    }
}

# Worker tuning defaults
celery_app.conf.worker_prefetch_multiplier = 1
celery_app.conf.task_acks_late = True
