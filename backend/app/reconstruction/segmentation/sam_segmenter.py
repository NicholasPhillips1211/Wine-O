"""SAM2 segmentation refinement interface."""

from __future__ import annotations

from typing import Any

from backend.app.core.config import settings

try:
    import httpx
except Exception:  # pragma: no cover - optional
    httpx = None


class SAMSegmenter:
    """Refine bottle masks and preserve transparent/glass boundaries."""

    def segment(self, image_uri: str, detection: dict[str, Any]) -> dict[str, Any]:
        """Return a high-resolution alpha mask descriptor for storage workers.

        If `settings.AI_MODEL_ENDPOINT` is set, attempt to call the remote
        segmenter service and return its JSON response. Otherwise return a
        conservative local placeholder mask URI.
        """
        endpoint = settings.AI_MODEL_ENDPOINT
        if endpoint and httpx is not None:
            try:
                resp = httpx.post(
                    f"{endpoint.rstrip('/')}/segment",
                    json={"image_uri": image_uri, "detection": detection},
                    timeout=settings.AI_TIMEOUT_SECONDS,
                )
                if resp.status_code == 200:
                    return resp.json()
            except Exception:
                pass

        return {
            "image_uri": image_uri,
            "mask_uri": f"{image_uri}.mask.png",
            "detection": detection,
        }
