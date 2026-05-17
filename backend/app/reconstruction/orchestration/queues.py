"""Queue names used by the staged asynchronous reconstruction pipeline."""

CAPTURE_QUEUE = "capture_queue"
SEGMENTATION_QUEUE = "segmentation_queue"
GEOMETRY_QUEUE = "geometry_queue"
BLENDER_QUEUE = "blender_queue"
OPTIMIZATION_QUEUE = "optimization_queue"
EXPORT_QUEUE = "export_queue"

STAGE_QUEUE_MAP = {
    "capture": CAPTURE_QUEUE,
    "segmentation": SEGMENTATION_QUEUE,
    "geometry": GEOMETRY_QUEUE,
    "blender_refinement": BLENDER_QUEUE,
    "materials": BLENDER_QUEUE,
    "optimization": OPTIMIZATION_QUEUE,
    "export": EXPORT_QUEUE,
    "delivery": EXPORT_QUEUE,
}
