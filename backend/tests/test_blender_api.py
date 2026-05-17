"""Tests for dedicated Blender worker API endpoints."""

from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_blender_job_start_and_status_and_logs() -> None:
    start = client.post(
        "/api/v1/blender/jobs/start",
        json={
            "job_id": "blend-job-1",
            "scaffold_uri": "reconstruction/blend-job-1/geometry/scaffold.glb",
        },
    )
    assert start.status_code == 200
    payload = start.json()
    assert payload["job_id"] == "blend-job-1"

    status = client.get("/api/v1/blender/jobs/blend-job-1/status")
    assert status.status_code == 200
    assert status.json()["status"] in {"queued", "simulated"}

    logs = client.get("/api/v1/blender/jobs/blend-job-1/logs")
    assert logs.status_code == 200
    assert isinstance(logs.json()["logs"], list)
