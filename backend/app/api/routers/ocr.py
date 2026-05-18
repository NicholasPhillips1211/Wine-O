from fastapi import APIRouter, Depends, HTTPException, Query

from backend.app.core.config import settings
from backend.app.schemas_jobs import JobStatusResponse, JobSubmissionResponse
from backend.app.schemas_ocr import OCRAnalysisRequest, OCRAnalysisResult, OCRRequest, OCRResult, ParsedWineLabel, TextBlock
from backend.app.services.job_service import JobService
from backend.app.services.ocr_service import OCRService


router = APIRouter(prefix="/ocr", tags=["ocr"])


def get_ocr_service() -> OCRService:
    """Dependency injection for OCR service."""
    return OCRService()


def get_job_service() -> JobService:
    """Dependency injection for background job service."""
    return JobService()


@router.post("/process", response_model=OCRResult)
async def process_image(
    request: OCRRequest,
    ocr_service: OCRService = Depends(get_ocr_service)
):
    """Extract text from image using OCR."""
    return ocr_service.process_image(request)


@router.post("/process-async", response_model=JobSubmissionResponse)
async def process_image_async(
    request: OCRRequest,
    job_service: JobService = Depends(get_job_service),
) -> JobSubmissionResponse:
    """Queue OCR extraction so the caller does not wait for processing."""
    return job_service.queue_ocr_process(request.image_url, request.language)


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


@router.post("/analyze-async", response_model=JobSubmissionResponse)
async def analyze_wine_label_async(
    request: OCRAnalysisRequest,
    job_service: JobService = Depends(get_job_service),
) -> JobSubmissionResponse:
    """Queue OCR plus label parsing for asynchronous execution."""
    return job_service.queue_ocr_analysis(request.image_url, request.language)


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
    min_confidence: float = Query(settings.OCR_CONFIDENCE_THRESHOLD, ge=0.0, le=1.0),
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


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(
    job_id: str,
    job_service: JobService = Depends(get_job_service),
) -> JobStatusResponse:
    """Return the latest known state for an OCR background job."""
    return job_service.get_job_status(job_id)
    return ocr_service.preprocess_for_matching(parsed_label)
