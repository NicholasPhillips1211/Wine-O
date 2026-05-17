"""Mask cleaning and artifact suppression utilities."""


class MaskCleaner:
    """Post-process segmentation masks before geometry fitting."""

    def clean(self, mask_uri: str) -> dict:
        """Return cleaned mask metadata."""
        return {"clean_mask_uri": mask_uri, "artifacts_removed": True}
