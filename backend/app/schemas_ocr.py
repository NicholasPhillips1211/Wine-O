"""Pydantic models for OCR domain."""

from typing import Optional

from pydantic import BaseModel, Field


class TextBlock(BaseModel):
    """Extracted text block with position and confidence."""
    text: str
    confidence: float
    x: Optional[int] = None  # Bounding box x coordinate
    y: Optional[int] = None  # Bounding box y coordinate
    width: Optional[int] = None
    height: Optional[int] = None


class OCRRequest(BaseModel):
    """Request for OCR processing."""
    image_url: str
    language: str = "en"
    extract_structure: bool = True  # Extract label structure


class OCRResult(BaseModel):
    """Result from OCR processing."""
    raw_text: str
    text_blocks: list[TextBlock]
    overall_confidence: float
    detected_language: str
    processing_time_ms: float
    image_url: str


class ParsedWineLabel(BaseModel):
    """Parsed wine label information."""
    wine_name: Optional[str] = None
    producer: Optional[str] = None
    region: Optional[str] = None
    country: Optional[str] = None
    vintage: Optional[int] = None
    varietals: list[str] = Field(default_factory=list)
    alcohol_content: Optional[float] = None
    volume: Optional[str] = None
    tasting_notes: Optional[str] = None
    additional_text: str = ""  # Any text that wasn't categorized
    confidence_score: float


class OCRAnalysisRequest(BaseModel):
    """Request for OCR followed by label parsing."""
    image_url: str
    language: str = "en"


class OCRAnalysisResult(BaseModel):
    """Result from OCR + parsing."""
    ocr_result: OCRResult
    parsed_label: ParsedWineLabel
    extraction_success: bool
    error_message: Optional[str] = None
