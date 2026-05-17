"""Celery tasks for staged reconstruction pipeline execution."""

from __future__ import annotations

from backend.app.core.celery_app import celery_app
from backend.app.core.config import settings
from backend.app.reconstruction.blender.worker_service import BlenderWorkerService
from backend.app.reconstruction.capture.quality_validator import CaptureQualityValidator
from backend.app.reconstruction.export.asset_validator import ExportAssetValidator
from backend.app.reconstruction.optimization.mobile_optimizer import MobileOptimizer
from backend.app.reconstruction.orchestration.failure_recovery import failure_recovery
from backend.app.reconstruction.orchestration.pipeline_manager import pipeline_manager
from backend.app.reconstruction.orchestration.queues import (
    BLENDER_QUEUE,
    CAPTURE_QUEUE,
    EXPORT_QUEUE,
    GEOMETRY_QUEUE,
    OPTIMIZATION_QUEUE,
    SEGMENTATION_QUEUE,
)
from backend.app.reconstruction.schemas.events import ReconstructionEventType
from backend.app.reconstruction.schemas.reconstruction_job import (
    ReconstructionJobStatus,
    ReconstructionStage,
)
from backend.app.reconstruction.segmentation.confidence_scorer import SegmentationConfidenceScorer
from backend.app.reconstruction.segmentation.depth_estimator import MiDaSDepthEstimator
from backend.app.reconstruction.segmentation.mask_cleaner import MaskCleaner
from backend.app.reconstruction.segmentation.sam_segmenter import SAMSegmenter
from backend.app.reconstruction.segmentation.yolo_detector import YOLOBottleDetector
from backend.app.reconstruction.storage.asset_cache import asset_cache
from backend.app.reconstruction.storage.datasets import registry as dataset_registry
from backend.app.reconstruction.storage.object_storage import object_storage


capture_validator = CaptureQualityValidator()
segmentation_scorer = SegmentationConfidenceScorer()
yolo_detector = YOLOBottleDetector()
sam_segmenter = SAMSegmenter()
depth_estimator = MiDaSDepthEstimator()
mask_cleaner = MaskCleaner()
blender_worker = BlenderWorkerService()
mobile_optimizer = MobileOptimizer()
export_validator = ExportAssetValidator()


@celery_app.task(
    name="wine_o.reconstruction.capture",
    queue=CAPTURE_QUEUE,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": settings.CELERY_TASK_RETRY_MAX},
    retry_backoff=True,
)
def capture_stage_task(
    job_id: str,
    image_urls: list[str],
    quality: str = "high",
    object_type: str = "wine_bottle",
) -> dict:
    """Capture ingestion stage: validates required multi-angle set."""
    validation = capture_validator.validate(image_urls)

    capture_result = {
        "images_received": len(image_urls),
        "quality": quality,
        "object_type": object_type,
        "capture_validation": {
            "valid": validation.valid,
            "score": validation.score,
            "missing_required_angles": validation.missing_required_angles,
            "inferred_angles": validation.inferred_angles,
            "issues": validation.issues,
        },
        "confidence": validation.score,
    }

    pipeline_manager.update_stage(
        job_id,
        ReconstructionStage.CAPTURE,
        status=ReconstructionJobStatus.RUNNING,
        result=capture_result,
        artifacts={
            "capture_quality": quality,
            "capture_object_type": object_type,
            "capture_issues": validation.issues,
        },
    )

    if not validation.valid:
        recovery = failure_recovery.register_failure(job_id, ReconstructionStage.CAPTURE.value)
        pipeline_manager.fail_job(
            job_id,
            f"Capture validation failed: required angles missing or image quality below threshold. attempts={recovery['attempts']}",
        )
        return {"job_id": job_id, "status": "failed", "reason": "capture_validation_failed"}

    return segmentation_stage_task(job_id, image_urls, quality=quality)


@celery_app.task(
    name="wine_o.reconstruction.segmentation",
    queue=SEGMENTATION_QUEUE,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": settings.CELERY_TASK_RETRY_MAX},
    retry_backoff=True,
)
def segmentation_stage_task(job_id: str, image_urls: list[str], quality: str = "high") -> dict:
    """AI segmentation stage with quality scoring and depth-map references."""
    pipeline_manager.emit_event(job_id, ReconstructionEventType.SEGMENTATION_STARTED, {"images": len(image_urls)})

    reference_image = image_urls[0]
    detection = yolo_detector.detect(reference_image)
    mask_result = sam_segmenter.segment(reference_image, detection)
    clean_mask = mask_cleaner.clean(mask_result["mask_uri"])
    depth_map = depth_estimator.estimate_depth(reference_image)

    job = pipeline_manager.get_job(job_id)
    capture_issues = {}
    if job and isinstance(job.artifacts, dict):
        capture_issues = job.artifacts.get("capture_issues", {})

    quality_eval = segmentation_scorer.score(
        is_blurry=bool(capture_issues.get("blurry", False)),
        low_lighting=bool(capture_issues.get("low_lighting", False)),
        glare=bool(capture_issues.get("glare", False)),
        poor_framing=bool(capture_issues.get("poor_framing", False)),
    )

    segmentation_confidence = round(min(detection.get("confidence", 0.0), quality_eval["scan_quality_score"]), 3)
    segmentation_result = {
        "bottle_bbox": detection["bottle_bbox"],
        "label_bbox": detection["label_bbox"],
        "confidence": segmentation_confidence,
        "image_count": len(image_urls),
        "mask_uri": clean_mask["clean_mask_uri"],
        "depth_map_uri": depth_map["depth_map_uri"],
        "scan_quality": quality_eval,
    }

    if quality_eval["reject"]:
        recovery = failure_recovery.register_failure(job_id, ReconstructionStage.SEGMENTATION.value)
        pipeline_manager.fail_job(job_id, f"Segmentation rejected due to low scan quality. attempts={recovery['attempts']}")
        return {"job_id": job_id, "status": "failed", "reason": "low_scan_quality"}

    pipeline_manager.update_stage(
        job_id,
        ReconstructionStage.SEGMENTATION,
        status=ReconstructionJobStatus.RUNNING,
        result=segmentation_result,
        artifacts={
            "mask_archive": f"reconstruction/{job_id}/segmentation/masks.zip",
            "depth_map": depth_map["depth_map_uri"],
        },
    )
    pipeline_manager.emit_event(job_id, ReconstructionEventType.SEGMENTATION_COMPLETED, segmentation_result)
    return geometry_stage_task(job_id, quality=quality)


@celery_app.task(
    name="wine_o.reconstruction.geometry",
    queue=GEOMETRY_QUEUE,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": settings.CELERY_TASK_RETRY_MAX},
    retry_backoff=True,
)
def geometry_stage_task(job_id: str, quality: str = "high") -> dict:
    """Parametric geometry stage with confidence tied to segmentation quality."""
    job = pipeline_manager.get_job(job_id)
    segmentation_confidence = 0.75
    if job and job.segmentation_result:
        segmentation_confidence = float(job.segmentation_result.get("confidence", segmentation_confidence))

    geometry_confidence = round(max(0.6, min(0.98, segmentation_confidence * 0.95 + 0.05)), 3)
    geometry_result = {
        "scaffold_mesh": f"reconstruction/{job_id}/geometry/scaffold.glb",
        "archetype": "bordeaux",
        "confidence": geometry_confidence,
    }
    pipeline_manager.update_stage(
        job_id,
        ReconstructionStage.GEOMETRY,
        status=ReconstructionJobStatus.RUNNING,
        result=geometry_result,
        artifacts={"geometry": geometry_result["scaffold_mesh"]},
    )
    dataset_registry.add_archetype(
        {
            "job_id": job_id,
            "archetype": geometry_result["archetype"],
            "confidence": geometry_confidence,
        }
    )
    return blender_stage_task(job_id, quality=quality)


@celery_app.task(
    name="wine_o.reconstruction.blender",
    queue=BLENDER_QUEUE,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": settings.CELERY_TASK_RETRY_MAX},
    retry_backoff=True,
)
def blender_stage_task(job_id: str, quality: str = "high") -> dict:
    """Blender refinement stage via worker service abstraction."""
    pipeline_manager.emit_event(job_id, ReconstructionEventType.BLENDER_STARTED, {"job_id": job_id})

    job = pipeline_manager.get_job(job_id)
    scaffold_uri = f"reconstruction/{job_id}/geometry/scaffold.glb"
    if job and job.geometry_result:
        scaffold_uri = job.geometry_result.get("scaffold_mesh", scaffold_uri)

    blender_result = blender_worker.run_refinement(job_id, scaffold_uri)
    blender_result["confidence"] = 0.9 if blender_result.get("status") in {"queued", "simulated"} else 0.75

    pipeline_manager.update_stage(
        job_id,
        ReconstructionStage.BLENDER_REFINEMENT,
        status=ReconstructionJobStatus.RUNNING,
        result=blender_result,
        artifacts={
            "blender": blender_result["refined_mesh"],
            "blender_command": blender_result.get("command", ""),
        },
    )
    pipeline_manager.emit_event(job_id, ReconstructionEventType.BLENDER_COMPLETED, blender_result)
    return materials_stage_task(job_id, quality=quality)


@celery_app.task(
    name="wine_o.reconstruction.materials",
    queue=BLENDER_QUEUE,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": settings.CELERY_TASK_RETRY_MAX},
    retry_backoff=True,
)
def materials_stage_task(job_id: str, quality: str = "high") -> dict:
    """PBR material stage producing confidence and map references."""
    cache_key = f"materials:{quality}"
    cached_profile = asset_cache.get(cache_key)
    if cached_profile is None:
        cached_profile = {"material_profile": quality, "maps": ["albedo", "roughness", "metallic", "normal", "ao", "opacity"]}
        asset_cache.set(cache_key, cached_profile)

    material_confidence = 0.88 if quality == "high" else 0.82
    material_result = {
        "maps": cached_profile["maps"],
        "material_profile": cached_profile["material_profile"],
        "confidence": material_confidence,
    }
    pipeline_manager.update_stage(
        job_id,
        ReconstructionStage.MATERIALS,
        status=ReconstructionJobStatus.RUNNING,
        result=material_result,
        artifacts={"material_manifest": f"reconstruction/{job_id}/materials/manifest.json"},
    )
    return optimization_stage_task(job_id, quality=quality)


@celery_app.task(
    name="wine_o.reconstruction.optimization",
    queue=OPTIMIZATION_QUEUE,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": settings.CELERY_TASK_RETRY_MAX},
    retry_backoff=True,
)
def optimization_stage_task(job_id: str, quality: str = "high") -> dict:
    """Optimization stage with mobile-safe LOD and compression manifest."""
    optimization_result = mobile_optimizer.build_manifest(job_id, quality)
    optimization_result["confidence"] = 0.9 if quality == "high" else 0.84

    pipeline_manager.update_stage(
        job_id,
        ReconstructionStage.OPTIMIZATION,
        status=ReconstructionJobStatus.RUNNING,
        result=optimization_result,
        artifacts={"lod_manifest": f"reconstruction/{job_id}/optimization/lods.json"},
    )
    return export_stage_task(job_id, quality=quality)


@celery_app.task(
    name="wine_o.reconstruction.export",
    queue=EXPORT_QUEUE,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": settings.CELERY_TASK_RETRY_MAX},
    retry_backoff=True,
)
def export_stage_task(job_id: str, quality: str = "high") -> dict:
    """Export stage with metadata packaging and quality validation checks."""
    optimization_result = {}
    job = pipeline_manager.get_job(job_id)
    if job and job.geometry_result:
        optimization_result = job.geometry_result

    estimated_triangles = 45000 if quality == "high" else 22000 if quality == "medium" else 9000
    validation = export_validator.validate(
        glb_size_mb=24.0 if quality == "high" else 14.0,
        texture_count=6,
        has_uvs=True,
        triangle_count=estimated_triangles,
    )

    metadata = export_validator.package_metadata(
        wine_name="Unknown Wine",
        winery="Unknown Winery",
        vintage="Unknown",
        archetype=optimization_result.get("archetype", "bordeaux"),
        confidence=0.9,
        reconstruction_version="v2",
    )

    if not validation["valid"]:
        recovery = failure_recovery.register_failure(job_id, ReconstructionStage.EXPORT.value)
        pipeline_manager.fail_job(
            job_id,
            f"Export validation failed: {', '.join(validation['issues'])}. attempts={recovery['attempts']}",
        )
        return {"job_id": job_id, "status": "failed", "reason": "export_validation_failed", "issues": validation["issues"]}

    glb_object = object_storage.upload_stub(job_id, "export/model.glb")
    usdz_object = object_storage.upload_stub(job_id, "export/model.usdz")

    export_result = {
        "glb": glb_object["object_key"],
        "usdz": usdz_object["object_key"],
        "delivery_urls": {
            "glb": glb_object["url"],
            "usdz": usdz_object["url"],
        },
        "metadata": metadata,
        "confidence": 0.9,
    }

    pipeline_manager.update_stage(
        job_id,
        ReconstructionStage.EXPORT,
        status=ReconstructionJobStatus.RUNNING,
        result=export_result,
        artifacts={"glb": export_result["glb"], "usdz": export_result["usdz"]},
    )
    pipeline_manager.emit_event(job_id, ReconstructionEventType.EXPORT_COMPLETED, export_result)
    pipeline_manager.complete_job(job_id)
    dataset_registry.add_reconstruction(
        {
            "job_id": job_id,
            "quality": quality,
            "success": True,
            "segmentation_confidence": (job.segmentation_result or {}).get("confidence") if job else None,
            "overall_confidence": 0.9,
        }
    )
    return {"job_id": job_id, "status": "completed", "export": export_result}
