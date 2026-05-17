"""Failure recovery and retry bookkeeping for reconstruction jobs."""

from __future__ import annotations

from collections import defaultdict
from threading import Lock


class FailureRecoveryManager:
    """Tracks stage retries and determines whether retry budget is exhausted."""

    def __init__(self, max_retries: int = 3) -> None:
        self.max_retries = max_retries
        self._lock = Lock()
        self._attempts: dict[tuple[str, str], int] = defaultdict(int)

    def register_failure(self, job_id: str, stage: str) -> dict:
        with self._lock:
            key = (job_id, stage)
            self._attempts[key] += 1
            attempts = self._attempts[key]
        return {
            "attempts": attempts,
            "max_retries": self.max_retries,
            "retry_allowed": attempts <= self.max_retries,
        }


failure_recovery = FailureRecoveryManager(max_retries=3)
