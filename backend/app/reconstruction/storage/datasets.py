"""Dataset registries for archetypes, labels, and reconstruction telemetry."""

from __future__ import annotations

from datetime import datetime, timezone
from threading import Lock
from typing import Any


class DatasetRegistry:
    """Stores lightweight in-memory dataset telemetry for model improvement."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._archetypes: list[dict[str, Any]] = []
        self._labels: list[dict[str, Any]] = []
        self._reconstructions: list[dict[str, Any]] = []

    def add_archetype(self, payload: dict[str, Any]) -> None:
        with self._lock:
            self._archetypes.append({**payload, "timestamp": datetime.now(timezone.utc)})

    def add_label(self, payload: dict[str, Any]) -> None:
        with self._lock:
            self._labels.append({**payload, "timestamp": datetime.now(timezone.utc)})

    def add_reconstruction(self, payload: dict[str, Any]) -> None:
        with self._lock:
            self._reconstructions.append({**payload, "timestamp": datetime.now(timezone.utc)})

    def snapshot(self) -> dict[str, int]:
        with self._lock:
            return {
                "archetypes": len(self._archetypes),
                "labels": len(self._labels),
                "reconstructions": len(self._reconstructions),
            }


registry = DatasetRegistry()
