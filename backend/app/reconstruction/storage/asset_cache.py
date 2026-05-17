"""Simple in-memory artifact cache for repeated archetype assets."""

from __future__ import annotations

from threading import Lock
from typing import Any


class AssetCache:
    """Caches generated artifacts to reduce duplicate processing."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._store: dict[str, Any] = {}

    def get(self, key: str) -> Any | None:
        with self._lock:
            return self._store.get(key)

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            self._store[key] = value


asset_cache = AssetCache()
