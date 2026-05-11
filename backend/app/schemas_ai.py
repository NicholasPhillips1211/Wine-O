"""Pydantic schemas for AI orchestration domain."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class WineAnalysisRequest(BaseModel):
    """Request to analyze wine label and reconstruct bottle."""
    image_urls: list[str] = Field(..., min_items=1, description="Images of wine bottle")
    analysis_depth: str = Field("standard", pattern="^(quick|standard|deep)$")
    enable_reconstruction: bool = Field(True, description="Build 3D model")
    enable_identification: bool = Field(True, description="Identify wine in database")


class WineAnalysisResult(BaseModel):
    """Complete wine analysis with OCR, identification, and 3D model."""
    analysis_id: str
    wine_name: Optional[str] = None
    producer: Optional[str] = None
    vintage: Optional[int] = None
    ocr_confidence: float = Field(..., ge=0, le=1)
    identification_confidence: float = Field(..., ge=0, le=1)
    reconstruction_id: Optional[str] = None
    reconstruction_confidence: Optional[float] = None
    estimated_price_range: Optional[dict] = None
    tasting_notes: Optional[str] = None
    processing_time_ms: float
    metadata: dict = Field(default_factory=dict)


class PipelineStage(BaseModel):
    """Status of a pipeline stage."""
    stage_name: str
    status: str = Field(..., pattern="^(pending|processing|completed|failed|skipped)$")
    progress_percent: int = Field(..., ge=0, le=100)
    error_message: Optional[str] = None
    duration_ms: Optional[float] = None


class WineAnalysisPipelineStatus(BaseModel):
    """Status of wine analysis pipeline execution."""
    analysis_id: str
    overall_status: str = Field(..., pattern="^(queued|processing|completed|failed)$")
    stages: list[PipelineStage]
    overall_progress_percent: int = Field(..., ge=0, le=100)
    started_at: datetime
    estimated_completion_time: Optional[datetime] = None
    error_summary: Optional[str] = None


class AIRecommendation(BaseModel):
    """AI recommendation based on wine analysis."""
    recommendation_type: str = Field(..., pattern="^(pairing|similar_wines|price_estimate|storage)$")
    title: str
    description: str
    confidence_score: float = Field(..., ge=0, le=1)
    related_items: Optional[list[str]] = None
    source: str = Field(default="ai", description="Source of recommendation")


class EnhancedWineAnalysis(BaseModel):
    """Enhanced analysis with AI recommendations."""
    base_analysis: WineAnalysisResult
    recommendations: list[AIRecommendation]
    similar_wines: Optional[list[dict]] = None
    compliance_issues: Optional[list[str]] = None


class BatchAnalysisRequest(BaseModel):
    """Request to analyze multiple wine images."""
    analysis_requests: list[WineAnalysisRequest] = Field(..., min_items=1)
    parallel_processing: bool = Field(True, description="Process in parallel")
    deduplicate_results: bool = Field(True, description="Remove duplicates")


class BatchAnalysisResult(BaseModel):
    """Results of batch wine analysis."""
    batch_id: str
    total_items: int
    successful_analyses: int
    failed_analyses: int
    results: list[WineAnalysisResult]
    total_processing_time_ms: float
    deduplication_matches: Optional[int] = None


class ComplianceCheck(BaseModel):
    """Compliance verification for wine label/data."""
    check_type: str
    is_compliant: bool
    details: str
    severity: str = Field(..., pattern="^(info|warning|error)$")


class LabelComplianceResult(BaseModel):
    """Full compliance check results."""
    analysis_id: str
    checks: list[ComplianceCheck]
    overall_compliant: bool
    compliance_score: float = Field(..., ge=0, le=1)
    recommendations: Optional[list[str]] = None


class QualityAssessment(BaseModel):
    """Quality assessment of wine analysis."""
    ocr_quality_score: float = Field(..., ge=0, le=1)
    reconstruction_quality_score: float = Field(..., ge=0, le=1)
    identification_reliability: float = Field(..., ge=0, le=1)
    overall_quality_score: float = Field(..., ge=0, le=1)
    quality_flags: Optional[list[str]] = None
