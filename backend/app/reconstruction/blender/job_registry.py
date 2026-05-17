"""Tracks Blender worker jobs for API status and logs."""

from __future__ import annotations

from datetime import datetime, timezone
from threading import Lock
from typing import Any


class BlenderJobRegistry:
    """In-memory registry for Blender execution lifecycle."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._jobs: dict[str, dict[str, Any]] = {}

    def upsert(self, job_id: str, payload: dict[str, Any]) -> None:
        with self._lock:
            existing = self._jobs.get(job_id, {"logs": []})
            logs = existing.get("logs", [])
            if "log" in payload:
                logs.append(payload["log"])
            self._jobs[job_id] = {
                **existing,
                **payload,
                "logs": logs,
                "updated_at": datetime.now(timezone.utc),
            }

    def get(self, job_id: str) -> dict[str, Any] | None:
        with self._lock:
            return self._jobs.get(job_id)


blender_jobs = BlenderJobRegistry()
