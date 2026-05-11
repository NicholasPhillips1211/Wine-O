"""Celery application for background jobs."""

from __future__ import annotations

import os

from celery import Celery


# Default to Redis when available, but keep the configuration overridable so
# local development can fall back to an in-process execution path.
BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")
TASK_ALWAYS_EAGER = os.getenv("CELERY_TASK_ALWAYS_EAGER", "false").lower() == "true"

celery_app = Celery(
    "wine_o",
    broker=BROKER_URL,
    backend=RESULT_BACKEND,
    include=["backend.app.tasks.ocr_tasks"],
)

celery_app.conf.update(
    task_track_started=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_always_eager=TASK_ALWAYS_EAGER,
)
