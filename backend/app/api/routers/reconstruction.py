"""3D Reconstruction API endpoints."""

from fastapi import APIRouter, Depends

from backend.app.schemas_3d import (
    MeshOptimizationRequest,
    MeshOptimizationResult,
    ReconstructionComparison,
    ReconstructionRequest,
    ReconstructionResult,
    ReconstructionStatus,
    BoundingBox,
)
from backend.app.services.reconstruction_service import ReconstructionService


router = APIRouter(prefix="/3d", tags=["3d"])
_reconstruction_service = ReconstructionService()


def get_reconstruction_service() -> ReconstructionService:
    """Dependency: get reconstruction service instance."""
    return _reconstruction_service


@router.post("/reconstruct", response_model=ReconstructionResult)
async def reconstruct_from_images(
    request: ReconstructionRequest,
    reconstruction_service: ReconstructionService = Depends(get_reconstruction_service),
) -> ReconstructionResult:
    """Reconstruct 3D model from multiple images."""
    return reconstruction_service.reconstruct_from_images(request)


@router.post("/reconstruct-enhanced")
async def reconstruct_from_images_enhanced(
    request: ReconstructionRequest,
    enable_photogrammetry: bool = False,
    reconstruction_service: ReconstructionService = Depends(get_reconstruction_service),
) -> dict:
    """Reconstruct with perspective correction, camera pose, PBR maps, and lighting."""
    return await reconstruction_service.reconstruct_from_images_enhanced(
        image_urls=request.image_urls,
        bottle_type=request.object_type,
        enable_perspective_correction=True,
        enable_pbr_materials=True,
        enable_photogrammetry=enable_photogrammetry,
    )


@router.get("/status/{reconstruction_id}", response_model=ReconstructionStatus)
async def get_status(
    reconstruction_id: str,
    reconstruction_service: ReconstructionService = Depends(get_reconstruction_service),
) -> ReconstructionStatus:
    """Get status of a reconstruction job."""
    return reconstruction_service.get_reconstruction_status(reconstruction_id)


@router.get("/compare/{id1}/{id2}", response_model=ReconstructionComparison)
async def compare_reconstructions(
    id1: str,
    id2: str,
    reconstruction_service: ReconstructionService = Depends(get_reconstruction_service),
) -> ReconstructionComparison:
    """Compare two 3D reconstructions."""
    return reconstruction_service.compare_reconstructions(id1, id2)


@router.get("/bounding-box/{reconstruction_id}", response_model=BoundingBox)
async def get_bounding_box(
    reconstruction_id: str,
    reconstruction_service: ReconstructionService = Depends(get_reconstruction_service),
) -> BoundingBox:
    """Get 3D bounding box of reconstruction."""
    return reconstruction_service.get_bounding_box(reconstruction_id)


@router.post("/optimize", response_model=MeshOptimizationResult)
async def optimize_mesh(
    request: MeshOptimizationRequest,
    reconstruction_service: ReconstructionService = Depends(get_reconstruction_service),
) -> MeshOptimizationResult:
    """Optimize mesh complexity by reducing vertex count."""
    return reconstruction_service.optimize_mesh(request)


@router.get("/export/{reconstruction_id}")
async def export_reconstruction(
    reconstruction_id: str,
    format: str = "gltf",
    reconstruction_service: ReconstructionService = Depends(get_reconstruction_service),
) -> dict:
    """Export reconstruction in specified format."""
    return reconstruction_service.export_reconstruction(reconstruction_id, format)


@router.post("/batch-reconstruct")
async def batch_reconstruct(
    requests: list[ReconstructionRequest],
    reconstruction_service: ReconstructionService = Depends(get_reconstruction_service),
) -> list[ReconstructionResult]:
    """Reconstruct multiple objects in batch."""
    return reconstruction_service.batch_reconstruct(requests)


@router.get("/status")
async def status():
    """Service health check."""
    return {"service": "3d", "status": "operational"}