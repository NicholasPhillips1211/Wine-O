from fastapi import APIRouter, Depends, HTTPException, Query

from backend.app.schemas_ocr import OCRAnalysisRequest, OCRAnalysisResult, OCRRequest, OCRResult, ParsedWineLabel, TextBlock
from backend.app.services.ocr_service import OCRService


router = APIRouter(prefix="/ocr", tags=["ocr"])


def get_ocr_service() -> OCRService:
    """Dependency injection for OCR service."""
    return OCRService()


@router.post("/process", response_model=OCRResult)
async def process_image(
    request: OCRRequest,
    ocr_service: OCRService = Depends(get_ocr_service)
):
    """Extract text from image using OCR."""
    return ocr_service.process_image(request)


@router.post("/analyze", response_model=OCRAnalysisResult)
async def analyze_wine_label(
    request: OCRAnalysisRequest,
    ocr_service: OCRService = Depends(get_ocr_service)
):
    """Full OCR + parsing pipeline for wine label."""
    result = ocr_service.analyze_label(request.image_url, request.language)
    if not result.extraction_success:
        raise HTTPException(status_code=400, detail=result.error_message)
    return result


@router.get("/text-blocks", response_model=list[TextBlock])
async def extract_text_blocks(
    image_url: str = Query(..., min_length=1),
    ocr_service: OCRService = Depends(get_ocr_service)
):
    """Extract individual text blocks from image."""
    return ocr_service.extract_text_blocks(image_url)


@router.post("/parse", response_model=ParsedWineLabel)
async def parse_label(
    ocr_result: OCRResult,
    ocr_service: OCRService = Depends(get_ocr_service)
):
    """Parse OCR text to extract structured wine data."""
    return ocr_service.parse_wine_label(ocr_result)


@router.post("/validate")
async def validate_ocr_quality(
    ocr_result: OCRResult,
    min_confidence: float = Query(0.7, ge=0.0, le=1.0),
    ocr_service: OCRService = Depends(get_ocr_service)
):
    """Check if OCR quality meets minimum threshold."""
    is_valid = ocr_service.validate_ocr_quality(ocr_result, min_confidence)
    return {
        "valid": is_valid,
        "confidence": ocr_result.overall_confidence,
        "min_required": min_confidence
    }


@router.post("/preprocess")
async def preprocess_for_matching(
    parsed_label: ParsedWineLabel,
    ocr_service: OCRService = Depends(get_ocr_service)
):
    """Prepare parsed label data for wine matching."""
    return ocr_service.preprocess_for_matching(parsed_label)