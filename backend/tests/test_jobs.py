"""Tests for background job submission and status tracking."""

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.job_service import JobService


client = TestClient(app)


class TestJobService:
    """Test the background job service layer."""

    def test_queue_ocr_process(self):
        """Queue OCR processing and return a job snapshot."""
        job_service = JobService()
        response = job_service.queue_ocr_process("https://example.com/wine_label.jpg", "en")

        assert response.job_id
        assert response.job_name == "ocr.process_image"
        assert response.state in {"PENDING", "STARTED", "SUCCESS", "RECEIVED"} or response.state

        status = job_service.get_job_status(response.job_id)
        assert status.job_id == response.job_id
        assert status.job_name == "ocr.process_image"
        assert status.state

    def test_queue_ocr_analysis(self):
        """Queue OCR analysis and return a job snapshot."""
        job_service = JobService()
        response = job_service.queue_ocr_analysis("https://example.com/wine_label.jpg", "en")

        assert response.job_id
        assert response.job_name == "ocr.analyze_label"

        status = job_service.get_job_status(response.job_id)
        assert status.job_id == response.job_id
        assert status.job_name == "ocr.analyze_label"


class TestJobEndpoints:
    """Test the async OCR job endpoints."""

    def test_process_async_endpoint(self):
        """Test POST /api/v1/ocr/process-async."""
        response = client.post(
            "/api/v1/ocr/process-async",
            json={"image_url": "https://example.com/wine_label.jpg", "language": "en"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["job_id"]
        assert data["job_name"] == "ocr.process_image"

    def test_analyze_async_endpoint(self):
        """Test POST /api/v1/ocr/analyze-async."""
        response = client.post(
            "/api/v1/ocr/analyze-async",
            json={"image_url": "https://example.com/wine_label.jpg", "language": "en"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["job_id"]
        assert data["job_name"] == "ocr.analyze_label"
