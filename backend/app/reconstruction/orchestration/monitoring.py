"""Reconstruction pipeline monitoring metrics."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from threading import Lock
from typing import Any


class ReconstructionMonitoring:
    """In-memory metrics tracker for pipeline observability."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._job_metrics: dict[str, dict[str, Any]] = {}
        self._stage_times: dict[str, list[float]] = defaultdict(list)
        self._failures: defaultdict[str, int] = defaultdict(int)

    def mark_stage(self, job_id: str, stage: str, duration_ms: float, gpu_memory_mb: float | None = None) -> None:
        with self._lock:
            self._job_metrics.setdefault(job_id, {})[stage] = {
                "duration_ms": duration_ms,
                "gpu_memory_mb": gpu_memory_mb,
                "timestamp": datetime.now(timezone.utc),
            }
            self._stage_times[stage].append(duration_ms)

    def mark_failure(self, stage: str) -> None:
        with self._lock:
            self._failures[stage] += 1

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            avg_times = {
                stage: (sum(times) / len(times) if times else 0.0)
                for stage, times in self._stage_times.items()
            }
            return {
                "jobs_tracked": len(self._job_metrics),
                "average_stage_duration_ms": avg_times,
                "failures": dict(self._failures),
            }


monitoring = ReconstructionMonitoring()
