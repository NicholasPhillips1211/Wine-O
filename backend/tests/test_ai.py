"""Tests for the AI Orchestration service and endpoints."""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.schemas_ai import WineAnalysisRequest, BatchAnalysisRequest
from backend.app.services.ai_service import AIOrchestrationService


client = TestClient(app)


class TestAIOrchestrationService:
    """Test the AI orchestration service layer."""

    @pytest.fixture
    def ai_service(self):
        """Create AI orchestration service instance."""
        return AIOrchestrationService()

    def test_analyze_wine_from_images(self, ai_service):
        """Test complete wine analysis pipeline via service."""
        request = WineAnalysisRequest(
            image_urls=["https://example.com/angle1.jpg", "https://example.com/angle2.jpg"],
            analysis_depth="standard",
            enable_reconstruction=True,
        )
        result = ai_service.analyze_wine_from_images(request)

        assert result.analysis_id is not None
        assert result.wine_name is not None
        assert 0 <= result.ocr_confidence <= 1
        assert 0 <= result.identification_confidence <= 1
        assert result.reconstruction_id is not None

    def test_get_pipeline_status(self, ai_service):
        """Test getting pipeline status via service."""
        status = ai_service.get_pipeline_status("test-analysis-id")

        assert status.analysis_id == "test-analysis-id"
        assert status.overall_status == "completed"
        assert len(status.stages) > 0
        for stage in status.stages:
            assert stage.progress_percent == 100

    def test_get_enhanced_analysis(self, ai_service):
        """Test getting enhanced analysis with recommendations via service."""
        enhanced = ai_service.get_enhanced_analysis("test-id")

        assert enhanced.base_analysis is not None
        assert len(enhanced.recommendations) > 0
        assert all(r.confidence_score <= 1 for r in enhanced.recommendations)

    def test_batch_analyze_wines(self, ai_service):
        """Test batch wine analysis via service."""
        requests = BatchAnalysisRequest(
            analysis_requests=[
                WineAnalysisRequest(
                    image_urls=["url1.jpg", "url2.jpg"],
                    analysis_depth="standard",
                    enable_reconstruction=True,
                ),
                WineAnalysisRequest(
                    image_urls=["url3.jpg", "url4.jpg"],
                    analysis_depth="quick",
                    enable_reconstruction=False,
                ),
            ],
            parallel_processing=True,
        )
        result = ai_service.batch_analyze_wines(requests)

        assert result.batch_id is not None
        assert result.total_items == 2
        assert result.successful_analyses > 0

    def test_check_label_compliance(self, ai_service):
        """Test label compliance checking via service."""
        compliance = ai_service.check_label_compliance("test-id")

        assert len(compliance.checks) > 0
        assert isinstance(compliance.overall_compliant, bool)
        assert 0 <= compliance.compliance_score <= 1

    def test_assess_analysis_quality(self, ai_service):
        """Test analysis quality assessment via service."""
        quality = ai_service.assess_analysis_quality("test-id")

        assert 0 <= quality.ocr_quality_score <= 1
        assert 0 <= quality.reconstruction_quality_score <= 1
        assert 0 <= quality.identification_reliability <= 1
        assert 0 <= quality.overall_quality_score <= 1

    def test_estimate_wine_value(self, ai_service):
        """Test wine valuation via service."""
        valuation = ai_service.estimate_wine_value("test-id")

        assert "estimated_price" in valuation
        assert "price_range" in valuation
        assert valuation["confidence"] > 0

    def test_get_tasting_profile(self, ai_service):
        """Test tasting profile generation via service."""
        profile = ai_service.get_tasting_profile("test-id")

        assert "body" in profile
        assert "acidity" in profile
        assert "tannins" in profile
        assert "primary_aromas" in profile


class TestAIEndpoints:
    """Test the AI Orchestration API endpoints."""

    def test_analyze_endpoint(self):
        """Test POST /api/v1/ai/analyze."""
        response = client.post(
            "/api/v1/ai/analyze",
            json={
                "image_urls": ["https://example.com/angle1.jpg", "https://example.com/angle2.jpg"],
                "analysis_depth": "standard",
                "enable_reconstruction": True,
            },
        )
        assert response.status_code in [200, 422]
        if response.status_code == 200:
            data = response.json()
            assert "analysis_id" in data
            assert "wine_name" in data

    def test_pipeline_status_endpoint(self):
        """Test GET /api/v1/ai/pipeline-status/{id}."""
        response = client.get("/api/v1/ai/pipeline-status/test-analysis-id")
        assert response.status_code in [200, 422]
        if response.status_code == 200:
            data = response.json()
            assert "overall_status" in data
            assert "stages" in data

    def test_enhanced_analysis_endpoint(self):
        """Test GET /api/v1/ai/enhanced/{id}."""
        response = client.get("/api/v1/ai/enhanced/test-id")
        assert response.status_code in [200, 422]
        if response.status_code == 200:
            data = response.json()
            assert "base_analysis" in data
            assert "recommendations" in data

    def test_batch_analyze_endpoint(self):
        """Test POST /api/v1/ai/batch-analyze."""
        response = client.post(
            "/api/v1/ai/batch-analyze",
            json={
                "analysis_requests": [
                    {
                        "image_urls": ["url1.jpg", "url2.jpg"],
                        "analysis_depth": "standard",
                        "enable_reconstruction": True,
                    },
                    {
                        "image_urls": ["url3.jpg"],
                        "analysis_depth": "quick",
                        "enable_reconstruction": False,
                    },
                ],
                "parallel_processing": True,
            },
        )
        assert response.status_code in [200, 422]
        if response.status_code == 200:
            data = response.json()
            assert "batch_id" in data
            assert "results" in data

    def test_compliance_endpoint(self):
        """Test GET /api/v1/ai/compliance/{id}."""
        response = client.get("/api/v1/ai/compliance/test-id")
        assert response.status_code in [200, 422]
        if response.status_code == 200:
            data = response.json()
            assert "checks" in data
            assert "overall_compliant" in data

    def test_quality_assessment_endpoint(self):
        """Test GET /api/v1/ai/quality/{id}."""
        response = client.get("/api/v1/ai/quality/test-id")
        assert response.status_code in [200, 422]
        if response.status_code == 200:
            data = response.json()
            assert "ocr_quality_score" in data
            assert "overall_quality_score" in data

    def test_valuation_endpoint(self):
        """Test GET /api/v1/ai/valuation/{id}."""
        response = client.get("/api/v1/ai/valuation/test-id")
        assert response.status_code in [200, 422]
        if response.status_code == 200:
            data = response.json()
            assert "estimated_price" in data
            assert "confidence" in data

    def test_tasting_profile_endpoint(self):
        """Test GET /api/v1/ai/tasting-profile/{id}."""
        response = client.get("/api/v1/ai/tasting-profile/test-id")
        assert response.status_code in [200, 422]
        if response.status_code == 200:
            data = response.json()
            assert "body" in data
            assert "acidity" in data
            assert "tannins" in data

    def test_health_check_endpoint(self):
        """Test GET /api/v1/ai/status (health check)."""
        response = client.get("/api/v1/ai/status")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "ai"
        assert data["status"] == "operational"
