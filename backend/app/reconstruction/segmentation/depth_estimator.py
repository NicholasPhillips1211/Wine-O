"""Depth estimation interface for silhouette and curvature fitting."""

from __future__ import annotations

from typing import Any

from backend.app.core.config import settings

try:
    import httpx
except Exception:  # pragma: no cover - optional
    httpx = None


class MiDaSDepthEstimator:
    """Generate approximate depth maps used to stabilize geometry reconstruction."""

    def estimate_depth(self, image_uri: str) -> dict[str, Any]:
        """Return a serializable depth map reference.

        Attempts to call an external depth estimation service when available.
        """
        endpoint = settings.AI_MODEL_ENDPOINT
        if endpoint and httpx is not None:
            try:
                resp = httpx.post(
                    f"{endpoint.rstrip('/')}/depth",
                    json={"image_uri": image_uri},
                    timeout=settings.AI_TIMEOUT_SECONDS,
                )
                if resp.status_code == 200:
                    return resp.json()
            except Exception:
                pass

        return {"image_uri": image_uri, "depth_map_uri": f"{image_uri}.depth.png"}
