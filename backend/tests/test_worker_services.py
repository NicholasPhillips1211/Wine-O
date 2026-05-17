import time

from backend.app.reconstruction.blender.worker_service import BlenderWorkerService
from backend.app.reconstruction.blender.job_registry import blender_jobs
from backend.app.reconstruction.segmentation.yolo_detector import YOLOBottleDetector
from backend.app.reconstruction.segmentation.sam_segmenter import SAMSegmenter
from backend.app.reconstruction.segmentation.depth_estimator import MiDaSDepthEstimator
from backend.app.core.config import settings


def test_yolo_sam_midas_stubs():
    # Ensure adapters return expected keys when no external endpoint configured
    settings.AI_MODEL_ENDPOINT = ""
    y = YOLOBottleDetector()
    r = y.detect("s3://bucket/image.jpg")
    assert "bottle_bbox" in r and "label_bbox" in r and "confidence" in r

    s = SAMSegmenter()
    sr = s.segment("s3://bucket/image.jpg", {"sample": True})
    assert "mask_uri" in sr and sr["image_uri"].endswith("image.jpg")

    d = MiDaSDepthEstimator()
    dr = d.estimate_depth("s3://bucket/image.jpg")
    assert "depth_map_uri" in dr


def test_blender_simulated_and_background(monkeypatch):
    # Simulated path when worker disabled
    settings.BLENDER_WORKER_ENABLED = False
    worker = BlenderWorkerService()
    resp = worker.run_refinement("job-sim", "reconstruction/job-sim/geometry/scaffold.glb")
    assert resp["status"] == "simulated"

    # Background path: monkeypatch _run_subprocess to simulate execution
    settings.BLENDER_WORKER_ENABLED = True

    def fake_run_subprocess(job_id, cmd, cwd=None, timeout=None, max_retries=1):
        blender_jobs.upsert(job_id, {"status": "running", "log": "fake: started"})
        blender_jobs.upsert(job_id, {"log": "fake: progress 50%"})
        blender_jobs.upsert(job_id, {"status": "completed", "log": "fake: completed"})

    monkeypatch.setattr(worker, "_run_subprocess", fake_run_subprocess)

    resp2 = worker.run_refinement("job-bg", "reconstruction/job-bg/geometry/scaffold.glb")
    assert resp2["status"] == "queued"

    # Registry should show completed status after the fake runner
    rec = blender_jobs.get("job-bg")
    assert rec is not None
    assert rec.get("status") == "completed"
    assert any("fake: completed" in l for l in rec.get("logs", []))
