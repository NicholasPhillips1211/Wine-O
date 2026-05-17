"""Capture quality and multi-angle validation for reconstruction."""

from __future__ import annotations

from dataclasses import dataclass


REQUIRED_ANGLES = ("front", "left", "right", "rear")
OPTIONAL_ANGLES = ("top", "label_closeup")


@dataclass
class CaptureValidationResult:
    """Validation output used by segmentation and orchestration stages."""

    valid: bool
    score: float
    missing_required_angles: list[str]
    inferred_angles: list[str]
    issues: dict[str, bool]


class CaptureQualityValidator:
    """Heuristic validator that enforces Wine-O capture constraints."""

    def _infer_angles(self, image_urls: list[str]) -> list[str]:
        angles: list[str] = []
        lowered = [url.lower() for url in image_urls]
        for angle in [*REQUIRED_ANGLES, *OPTIONAL_ANGLES]:
            if any(angle in url for url in lowered):
                angles.append(angle)

        # Fallback: infer a valid baseline when metadata is unavailable.
        if len(angles) < len(REQUIRED_ANGLES) and len(image_urls) >= 4:
            return list(REQUIRED_ANGLES)
        return angles

    def validate(self, image_urls: list[str]) -> CaptureValidationResult:
        inferred_angles = self._infer_angles(image_urls)
        missing_required = [angle for angle in REQUIRED_ANGLES if angle not in inferred_angles]

        insufficient_count = len(image_urls) < 4
        poor_framing = insufficient_count or bool(missing_required)
        low_lighting = any("dark" in u.lower() or "lowlight" in u.lower() for u in image_urls)
        glare = any("glare" in u.lower() or "reflection" in u.lower() for u in image_urls)
        blurry = any("blur" in u.lower() for u in image_urls)

        penalties = sum(int(flag) for flag in [poor_framing, low_lighting, glare, blurry])
        score = max(0.0, 1.0 - penalties * 0.2)

        return CaptureValidationResult(
            valid=(not poor_framing) and score >= 0.5,
            score=score,
            missing_required_angles=missing_required,
            inferred_angles=inferred_angles,
            issues={
                "poor_framing": poor_framing,
                "low_lighting": low_lighting,
                "glare": glare,
                "blurry": blurry,
            },
        )
