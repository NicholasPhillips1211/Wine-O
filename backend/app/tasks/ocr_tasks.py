"""Celery tasks for OCR processing and wine label parsing."""

from __future__ import annotations

from backend.app.core.celery_app import celery_app
from backend.app.schemas_ocr import OCRAnalysisResult, OCRRequest, OCRResult
from backend.app.services.ocr_service import OCRService


@celery_app.task(name="wine_o.ocr.process_image")
def process_image_task(image_url: str, language: str = "en") -> dict:
    """Run OCR in the background and return a serializable payload."""
    service = OCRService()
    result: OCRResult = service.process_image(OCRRequest(image_url=image_url, language=language))
    return result.model_dump()


@celery_app.task(name="wine_o.ocr.analyze_label")
def analyze_label_task(image_url: str, language: str = "en") -> dict:
    """Run the full OCR + parsing pipeline in the background."""
    service = OCRService()
    result: OCRAnalysisResult = service.analyze_label(image_url=image_url, language=language)
    return result.model_dump()
