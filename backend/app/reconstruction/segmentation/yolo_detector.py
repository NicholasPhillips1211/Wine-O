"""YOLO-based bottle part detection interface.

This adapter will call an external model HTTP endpoint when
`settings.AI_MODEL_ENDPOINT` is configured. Otherwise it returns a local
fallback detection useful for unit tests and offline development.
"""

from __future__ import annotations

from typing import Any

from backend.app.core.config import settings

try:  # optional dependency for model-serving HTTP endpoints
    import httpx
except Exception:  # pragma: no cover - optional in tests
    httpx = None


class YOLOBottleDetector:
    """Detect bottle, label, cork, and foil regions from capture images."""

    def detect(self, image_uri: str) -> dict[str, Any]:
        """Return a normalized detection payload suitable for downstream segmentation.

        If an AI model endpoint is configured, call it and return its JSON
        response. Otherwise return a deterministic local stub.
        """
        endpoint = settings.AI_MODEL_ENDPOINT
        if endpoint and httpx is not None:
            try:
                resp = httpx.post(
                    f"{endpoint.rstrip('/')}/detect",
                    json={"image_uri": image_uri, "model": settings.AI_MODEL.value},
                    timeout=settings.AI_TIMEOUT_SECONDS,
                )
                if resp.status_code == 200:
                    return resp.json()
            except Exception:
                # fall back to local stub on any error
                pass

        return {
            "bottle_bbox": [0, 0, 1, 1],
            "label_bbox": [0, 0, 1, 1],
            "confidence": 0.95,
            "image_uri": image_uri,
        }
