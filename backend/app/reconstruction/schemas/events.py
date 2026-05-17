"""Event contracts for reconstruction pipeline telemetry."""

from enum import Enum


class ReconstructionEventType(str, Enum):
    """Canonical domain events emitted by the reconstruction pipeline."""

    JOB_CREATED = "JOB_CREATED"
    SEGMENTATION_STARTED = "SEGMENTATION_STARTED"
    SEGMENTATION_COMPLETED = "SEGMENTATION_COMPLETED"
    BLENDER_STARTED = "BLENDER_STARTED"
    BLENDER_COMPLETED = "BLENDER_COMPLETED"
    EXPORT_COMPLETED = "EXPORT_COMPLETED"
    JOB_FAILED = "JOB_FAILED"
