"""Mobile optimization profiles for LOD and geometry budgets."""

from __future__ import annotations

from dataclasses import dataclass

from backend.app.core.config import settings


@dataclass
class MobileBudget:
    tier: str
    max_triangles: int


class MobileOptimizer:
    """Build optimization manifests for runtime-safe mobile delivery."""

    def get_budget(self, quality: str) -> MobileBudget:
        if quality == "high":
            return MobileBudget(tier="premium", max_triangles=settings.MOBILE_TRIANGLES_PREMIUM)
        if quality == "medium":
            return MobileBudget(tier="mobile_preferred", max_triangles=settings.MOBILE_TRIANGLES_MOBILE)
        return MobileBudget(tier="low_lod", max_triangles=settings.MOBILE_TRIANGLES_LOW_LOD)

    def build_manifest(self, job_id: str, quality: str) -> dict:
        budget = self.get_budget(quality)
        return {
            "job_id": job_id,
            "tier": budget.tier,
            "triangle_budget": budget.max_triangles,
            "lods": [
                {"name": "thumbnail", "max_triangles": min(2000, budget.max_triangles // 5)},
                {"name": "LOD2", "max_triangles": min(10000, budget.max_triangles // 2)},
                {"name": "LOD1", "max_triangles": min(25000, budget.max_triangles)},
                {"name": "LOD0", "max_triangles": budget.max_triangles},
            ],
            "compression": {
                "draco": settings.MOBILE_ENABLE_DRACO,
                "ktx2": settings.MOBILE_ENABLE_KTX2,
                "basisu": settings.MOBILE_ENABLE_BASISU,
            },
            "progressive_streaming": ["thumbnail", "LOD2", "LOD1", "LOD0"],
        }
