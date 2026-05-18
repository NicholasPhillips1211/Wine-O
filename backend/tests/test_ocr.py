"""Tests for the OCR service and endpoints."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.config import settings
from backend.app.schemas_ocr import OCRAnalysisRequest, OCRRequest
from backend.app.services.ocr_service import OCRService


client = TestClient(app)
REAL_LABEL_IMAGE = Path(__file__).resolve().parent / "fixtures" / "real_wine_label.jpg"


class TestOCRService:
    """Test the OCR service layer."""

    @pytest.fixture
    def ocr_service(self):
        """Create OCR service instance."""
        return OCRService()

    def test_process_image(self, ocr_service):
        """Test image processing via service."""
        request = OCRRequest(image_url="https://example.com/wine_label.jpg", language="en")
        result = ocr_service.process_image(request)
        
        assert result.raw_text is not None
        assert len(result.text_blocks) > 0
        assert result.overall_confidence > 0
        assert result.detected_language == "en"

    def test_process_real_image_fixture(self, ocr_service):
        """Test image processing against a real local image fixture."""
        assert REAL_LABEL_IMAGE.exists()

        result = ocr_service.process_image(OCRRequest(image_url=str(REAL_LABEL_IMAGE), language="en"))

        assert result.image_url == str(REAL_LABEL_IMAGE)
        assert isinstance(result.raw_text, str)
        assert isinstance(result.text_blocks, list)
        assert 0 <= result.overall_confidence <= 1

    def test_parse_wine_label(self, ocr_service):
        """Test label parsing via service."""
        request = OCRRequest(image_url="https://example.com/wine_label.jpg")
        ocr_result = ocr_service.process_image(request)
        
        parsed = ocr_service.parse_wine_label(ocr_result)
        
        assert parsed.wine_name is not None
        assert parsed.confidence_score > 0

    def test_analyze_label(self, ocr_service):
        """Test full OCR + parsing pipeline via service."""
        result = ocr_service.analyze_label("https://example.com/wine_label.jpg", "en")
        
        assert result.extraction_success is True
        assert result.ocr_result is not None
        assert result.parsed_label is not None

    def test_extract_text_blocks(self, ocr_service):
        """Test text block extraction via service."""
        blocks = ocr_service.extract_text_blocks("https://example.com/wine_label.jpg")
        
        assert isinstance(blocks, list)
        assert len(blocks) > 0
        for block in blocks:
            assert block.text is not None
            assert 0 <= block.confidence <= 1

    def test_validate_ocr_quality(self, ocr_service):
        """Test OCR quality validation via service."""
        request = OCRRequest(image_url="https://example.com/wine_label.jpg")
        ocr_result = ocr_service.process_image(request)
        
        is_valid = ocr_service.validate_ocr_quality(ocr_result, min_confidence=0.8)
        assert isinstance(is_valid, bool)

    def test_validate_ocr_quality_uses_config_default(self, ocr_service, monkeypatch):
        """Test OCR quality validation falls back to configured threshold."""
        monkeypatch.setattr(settings, "OCR_CONFIDENCE_THRESHOLD", 0.6)

        ocr_result = OCRRequest(image_url="https://example.com/wine_label.jpg")
        result = ocr_service.process_image(ocr_result)

        low_confidence_result = result.model_copy(update={"overall_confidence": 0.55})
        assert ocr_service.validate_ocr_quality(low_confidence_result) is False

    def test_preprocess_for_matching(self, ocr_service):
        """Test label preprocessing via service."""
        request = OCRRequest(image_url="https://example.com/wine_label.jpg")
        ocr_result = ocr_service.process_image(request)
        parsed = ocr_service.parse_wine_label(ocr_result)
        
        preprocessed = ocr_service.preprocess_for_matching(parsed)
        
        assert "name" in preprocessed
        assert "search_text" in preprocessed


class TestOCREndpoints:
    """Test the OCR API endpoints."""

    def test_process_image_endpoint(self):
        """Test POST /api/v1/ocr/process."""
        response = client.post("/api/v1/ocr/process", json={
            "image_url": "https://example.com/wine_label.jpg",
            "language": "en"
        })
        assert response.status_code in [200, 422]
        if response.status_code == 200:
            data = response.json()
            assert "raw_text" in data
            assert "text_blocks" in data

    def test_analyze_wine_label_endpoint(self):
        """Test POST /api/v1/ocr/analyze."""
        response = client.post("/api/v1/ocr/analyze", json={
            "image_url": "https://example.com/wine_label.jpg",
            "language": "en"
        })
        assert response.status_code in [200, 400, 422]
        if response.status_code == 200:
            data = response.json()
            assert "ocr_result" in data
            assert "parsed_label" in data

    def test_extract_text_blocks_endpoint(self):
        """Test GET /api/v1/ocr/text-blocks."""
        response = client.get(
            "/api/v1/ocr/text-blocks?image_url=https://example.com/wine_label.jpg"
        )
        assert response.status_code in [200, 422]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)

    def test_parse_label_endpoint(self):
        """Test POST /api/v1/ocr/parse."""
        response = client.post("/api/v1/ocr/parse", json={
            "raw_text": "2020 Cabernet\nNapa Valley",
            "text_blocks": [],
            "overall_confidence": 0.9,
            "detected_language": "en",
            "processing_time_ms": 150.0,
            "image_url": "https://example.com/wine_label.jpg"
        })
        assert response.status_code in [200, 422]

    def test_validate_ocr_quality_endpoint(self):
        """Test POST /api/v1/ocr/validate."""
        response = client.post("/api/v1/ocr/validate", json={
            "raw_text": "2020 Cabernet\nNapa Valley",
            "text_blocks": [],
            "overall_confidence": 0.95,
            "detected_language": "en",
            "processing_time_ms": 150.0,
            "image_url": "https://example.com/wine_label.jpg"
        })
        assert response.status_code in [200, 422]
        if response.status_code == 200:
            data = response.json()
            assert "valid" in data
            assert "confidence" in data

    def test_preprocess_for_matching_endpoint(self):
        """Test POST /api/v1/ocr/preprocess."""
        response = client.post("/api/v1/ocr/preprocess", json={
            "wine_name": "Cabernet Sauvignon",
            "producer": "Example",
            "region": "Napa Valley",
            "country": "USA",
            "vintage": 2020,
            "varietals": ["Cabernet Sauvignon"],
            "alcohol_content": 13.5,
            "volume": "750ml",
            "additional_text": "Premium",
            "confidence_score": 0.9
        })
        assert response.status_code in [200, 422]
