"""Validation and metadata packaging for exported reconstruction assets."""

from __future__ import annotations

from backend.app.core.config import settings


class ExportAssetValidator:
    """Enforce export constraints before delivery or CDN sync."""

    def validate(self, *, glb_size_mb: float, texture_count: int, has_uvs: bool, triangle_count: int) -> dict:
        issues: list[str] = []

        if glb_size_mb > settings.EXPORT_MAX_SIZE_MB:
            issues.append("asset_size_exceeded")
        if texture_count <= 0:
            issues.append("missing_textures")
        if not has_uvs:
            issues.append("broken_uvs")
        if triangle_count > settings.EXPORT_MAX_TRIANGLES:
            issues.append("triangle_budget_exceeded")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
        }

    def package_metadata(
        self,
        *,
        wine_name: str,
        winery: str,
        vintage: str,
        archetype: str,
        confidence: float,
        reconstruction_version: str,
    ) -> dict:
        return {
            "wine_name": wine_name,
            "winery": winery,
            "vintage": vintage,
            "archetype": archetype,
            "confidence": confidence,
            "reconstruction_version": reconstruction_version,
        }
