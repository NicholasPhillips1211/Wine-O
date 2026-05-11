"""AI Orchestration API endpoints for wine analysis."""

from fastapi import APIRouter, Depends

from backend.app.schemas_ai import (
    BatchAnalysisRequest,
    BatchAnalysisResult,
    EnhancedWineAnalysis,
    LabelComplianceResult,
    QualityAssessment,
    WineAnalysisPipelineStatus,
    WineAnalysisRequest,
    WineAnalysisResult,
)
from backend.app.services.ai_service import AIOrchestrationService


router = APIRouter(prefix="/ai", tags=["ai"])


def get_ai_service() -> AIOrchestrationService:
    """Dependency: get AI orchestration service instance."""
    return AIOrchestrationService()


@router.post("/analyze", response_model=WineAnalysisResult)
async def analyze_wine_from_images(
    request: WineAnalysisRequest,
    ai_service: AIOrchestrationService = Depends(get_ai_service),
) -> WineAnalysisResult:
    """Orchestrate complete wine analysis pipeline (OCR + ID + 3D)."""
    return ai_service.analyze_wine_from_images(request)


@router.get("/pipeline-status/{analysis_id}", response_model=WineAnalysisPipelineStatus)
async def get_pipeline_status(
    analysis_id: str,
    ai_service: AIOrchestrationService = Depends(get_ai_service),
) -> WineAnalysisPipelineStatus:
    """Get status of wine analysis pipeline execution."""
    return ai_service.get_pipeline_status(analysis_id)


@router.get("/enhanced/{analysis_id}", response_model=EnhancedWineAnalysis)
async def get_enhanced_analysis(
    analysis_id: str,
    ai_service: AIOrchestrationService = Depends(get_ai_service),
) -> EnhancedWineAnalysis:
    """Get enhanced analysis with AI recommendations."""
    return ai_service.get_enhanced_analysis(analysis_id)


@router.post("/batch-analyze", response_model=BatchAnalysisResult)
async def batch_analyze_wines(
    request: BatchAnalysisRequest,
    ai_service: AIOrchestrationService = Depends(get_ai_service),
) -> BatchAnalysisResult:
    """Analyze multiple wines in batch."""
    return ai_service.batch_analyze_wines(request)


@router.get("/compliance/{analysis_id}", response_model=LabelComplianceResult)
async def check_label_compliance(
    analysis_id: str,
    ai_service: AIOrchestrationService = Depends(get_ai_service),
) -> LabelComplianceResult:
    """Check compliance of wine label information."""
    return ai_service.check_label_compliance(analysis_id)


@router.get("/quality/{analysis_id}", response_model=QualityAssessment)
async def assess_analysis_quality(
    analysis_id: str,
    ai_service: AIOrchestrationService = Depends(get_ai_service),
) -> QualityAssessment:
    """Assess quality of wine analysis results."""
    return ai_service.assess_analysis_quality(analysis_id)


@router.get("/valuation/{analysis_id}")
async def estimate_wine_value(
    analysis_id: str,
    ai_service: AIOrchestrationService = Depends(get_ai_service),
) -> dict:
    """Estimate market value of wine based on analysis."""
    return ai_service.estimate_wine_value(analysis_id)


@router.get("/tasting-profile/{analysis_id}")
async def get_tasting_profile(
    analysis_id: str,
    ai_service: AIOrchestrationService = Depends(get_ai_service),
) -> dict:
    """Generate tasting profile from analysis."""
    return ai_service.get_tasting_profile(analysis_id)


@router.get("/status")
async def status():
    """Service health check."""
    return {"service": "ai", "status": "operational"}