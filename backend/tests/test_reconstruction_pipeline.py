"""Tests for asynchronous reconstruction orchestration endpoints."""

from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_start_reconstruction_job() -> None:
    """POST /api/v1/reconstruction/start should create a new job."""
    response = client.post(
        "/api/v1/reconstruction/start",
        json={
            "image_urls": ["https://example.com/front.jpg", "https://example.com/left.jpg"],
            "object_type": "wine_bottle",
            "quality": "high",
            "user_id": "user-123",
        },
    )
    assert response.status_code == 202
    payload = response.json()
    assert "job_id" in payload
    assert "status" in payload
    assert "stage" in payload


def test_reconstruction_job_lifecycle_endpoints() -> None:
    """Lifecycle endpoints should return status, progress, and artifacts for created jobs."""
    start = client.post(
        "/api/v1/reconstruction/start",
        json={
            "image_urls": [
                "https://example.com/front.jpg",
                "https://example.com/left.jpg",
                "https://example.com/right.jpg",
                "https://example.com/rear.jpg",
            ],
        },
    )
    assert start.status_code == 202
    job_id = start.json()["job_id"]

    details = client.get(f"/api/v1/reconstruction/{job_id}")
    assert details.status_code == 200
    assert details.json()["id"] == job_id

    status = client.get(f"/api/v1/reconstruction/{job_id}/status")
    assert status.status_code == 200
    assert status.json()["id"] == job_id

    progress = client.get(f"/api/v1/reconstruction/{job_id}/progress")
    assert progress.status_code == 200
    assert progress.json()["id"] == job_id
    assert "events" in progress.json()

    artifacts = client.get(f"/api/v1/reconstruction/{job_id}/artifacts")
    assert artifacts.status_code == 200
    assert artifacts.json()["job_id"] == job_id

    confidence = client.get(f"/api/v1/reconstruction/{job_id}/confidence")
    assert confidence.status_code == 200
    confidence_payload = confidence.json()
    assert "overall_confidence" in confidence_payload

    monitoring = client.get("/api/v1/reconstruction/monitoring/metrics")
    assert monitoring.status_code == 200
    assert "jobs_tracked" in monitoring.json()

    datasets = client.get("/api/v1/reconstruction/datasets/snapshot")
    assert datasets.status_code == 200
    assert "reconstructions" in datasets.json()


def test_reconstruction_rejects_insufficient_capture_angles() -> None:
    """Capture stage should fail jobs that do not meet required angle coverage."""
    start = client.post(
        "/api/v1/reconstruction/start",
        json={
            "image_urls": ["https://example.com/front.jpg", "https://example.com/right.jpg"],
        },
    )
    assert start.status_code == 202
    job_id = start.json()["job_id"]

    status = client.get(f"/api/v1/reconstruction/{job_id}/status")
    assert status.status_code == 200
    assert status.json()["status"] == "failed"
