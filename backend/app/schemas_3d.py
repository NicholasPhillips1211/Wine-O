"""Pydantic schemas for 3D reconstruction domain."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class Point3D(BaseModel):
    """3D coordinate point."""
    x: float
    y: float
    z: float


class Mesh(BaseModel):
    """3D mesh representation."""
    vertices: list[Point3D]
    faces: list[tuple[int, int, int]]
    normals: Optional[list[Point3D]] = None


class ReconstructionRequest(BaseModel):
    """Request to reconstruct 3D model from images."""
    image_urls: list[str] = Field(..., min_items=2, description="Multiple angles of object")
    object_type: str = Field("wine_bottle", description="Type of object to reconstruct")
    quality: str = Field("medium", pattern="^(low|medium|high)$", description="Reconstruction quality")
    enable_texture: bool = Field(True, description="Include texture mapping")


class ReconstructionResult(BaseModel):
    """Result of 3D reconstruction."""
    reconstruction_id: str
    mesh: Mesh
    texture_url: Optional[str] = None
    confidence_score: float = Field(..., ge=0, le=1)
    processing_time_ms: float
    output_format: str = Field("gltf", description="3D file format")
    metadata: dict = Field(default_factory=dict)


class ReconstructionStatus(BaseModel):
    """Status of a reconstruction job."""
    reconstruction_id: str
    status: str = Field(..., pattern="^(queued|processing|completed|failed)$")
    progress_percent: int = Field(..., ge=0, le=100)
    estimated_time_remaining_ms: Optional[float] = None
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


class ReconstructionComparison(BaseModel):
    """Compare two 3D reconstructions."""
    reconstruction_id_1: str
    reconstruction_id_2: str
    similarity_score: float = Field(..., ge=0, le=1, description="0=completely different, 1=identical")
    dimensional_variance: dict = Field(default_factory=dict, description="Size/scale differences")
    structural_differences: Optional[str] = None


class BoundingBox(BaseModel):
    """3D bounding box."""
    min_point: Point3D
    max_point: Point3D
    volume: float


class MeshOptimizationRequest(BaseModel):
    """Request to optimize mesh complexity."""
    reconstruction_id: str
    target_vertex_count: int = Field(10000, ge=100, description="Target number of vertices")
    preserve_features: bool = Field(True, description="Preserve small features")


class MeshOptimizationResult(BaseModel):
    """Result of mesh optimization."""
    original_vertex_count: int
    optimized_vertex_count: int
    reduction_ratio: float
    quality_loss_percent: float
    optimization_time_ms: float
