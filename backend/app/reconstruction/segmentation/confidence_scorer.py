"""Quality validation for capture and segmentation confidence."""

from __future__ import annotations


class SegmentationConfidenceScorer:
    """Score image quality and segmentation suitability for reconstruction."""

    def score(self, *, is_blurry: bool, low_lighting: bool, glare: bool, poor_framing: bool) -> dict:
        """Return a quality score and rejection decision."""
        penalties = sum(int(flag) for flag in [is_blurry, low_lighting, glare, poor_framing])
        score = max(0.0, 1.0 - penalties * 0.25)
        return {
            "scan_quality_score": score,
            "reject": score < 0.5,
            "issues": {
                "is_blurry": is_blurry,
                "low_lighting": low_lighting,
                "glare": glare,
                "poor_framing": poor_framing,
            },
        }
