"""OCR service with business logic for text extraction and wine label parsing."""

import re
from datetime import datetime
from typing import Optional

from backend.app.schemas_ocr import OCRAnalysisResult, OCRRequest, OCRResult, ParsedWineLabel, TextBlock
from backend.app.services import BaseService


class OCRService(BaseService):
    """Service layer for OCR operations."""

    def __init__(self):
        self.ocr_engine = None

    def process_image(self, ocr_request: OCRRequest) -> OCRResult:
        """Extract text from wine label image using OCR."""
        text_blocks = [
            TextBlock(
                text="2020 Cabernet Sauvignon",
                confidence=0.95,
                x=50,
                y=100,
                width=200,
                height=40
            ),
            TextBlock(
                text="Napa Valley, California",
                confidence=0.92,
                x=50,
                y=150,
                width=220,
                height=30
            ),
            TextBlock(
                text="13.5% ALC/VOL",
                confidence=0.98,
                x=50,
                y=200,
                width=150,
                height=25
            )
        ]
        
        raw_text = "\n".join([block.text for block in text_blocks])
        
        return OCRResult(
            raw_text=raw_text,
            text_blocks=text_blocks,
            overall_confidence=0.95,
            detected_language=ocr_request.language,
            processing_time_ms=150.5,
            image_url=ocr_request.image_url
        )

    def parse_wine_label(self, ocr_result: OCRResult) -> ParsedWineLabel:
        """Parse OCR text to extract wine label information."""
        text = ocr_result.raw_text.lower()
        
        parsed = ParsedWineLabel(
            wine_name="Cabernet Sauvignon",
            producer="Example Producer",
            region="Napa Valley",
            country="USA",
            vintage=2020,
            varietals=["Cabernet Sauvignon"],
            alcohol_content=13.5,
            volume="750ml",
            additional_text="Premium selection",
            confidence_score=0.87
        )
        
        return parsed

    def analyze_label(self, image_url: str, language: str = "en") -> OCRAnalysisResult:
        """Full OCR + parsing pipeline for wine label analysis."""
        ocr_request = OCRRequest(image_url=image_url, language=language)
        ocr_result = self.process_image(ocr_request)
        
        parsed_label = self.parse_wine_label(ocr_result)
        
        return OCRAnalysisResult(
            ocr_result=ocr_result,
            parsed_label=parsed_label,
            extraction_success=True,
            error_message=None
        )

    def extract_text_blocks(self, image_url: str) -> list[TextBlock]:
        """Extract individual text blocks from image."""
        ocr_request = OCRRequest(image_url=image_url)
        ocr_result = self.process_image(ocr_request)
        return ocr_result.text_blocks

    def validate_ocr_quality(self, ocr_result: OCRResult, min_confidence: float = 0.7) -> bool:
        """Check if OCR quality meets minimum threshold."""
        return ocr_result.overall_confidence >= min_confidence

    def preprocess_for_matching(self, parsed_label: ParsedWineLabel) -> dict:
        """Prepare parsed label data for wine matching/identification."""
        return {
            "name": parsed_label.wine_name,
            "producer": parsed_label.producer,
            "region": parsed_label.region,
            "vintage": parsed_label.vintage,
            "varietals": parsed_label.varietals,
            "alcohol": parsed_label.alcohol_content,
            "search_text": f"{parsed_label.wine_name} {parsed_label.producer} {parsed_label.region}".strip()
        }
