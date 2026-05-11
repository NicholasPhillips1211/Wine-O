from fastapi import APIRouter, Depends, HTTPException, Query

from backend.app.schemas_wine import WineCreate, WineIdentificationResult, WineResponse, WineUpdate
from backend.app.services.wine_service import WineService

from backend.app.schemas_wine import (
    WineCreate, 
    WineUpdate, 
    WineResponse, 
    WineSearchResponse, 
    WineIdentificationRequest, 
    WineIdentificationResponse
)
from backend.app.services.wine_service import WineService

router = APIRouter(prefix="/wines", tags=["wines"])

def get_wine_service() -> WineService:
    """Dependency injection for wine service."""
    return WineService()

def get_wine_service() -> WineService:
    """Dependency injection for wine service."""
    return WineService()


@router.post("", response_model=WineResponse, status_code=201)
async def create_wine(
    wine: WineCreate,
    wine_service: WineService = Depends(get_wine_service)
):
    """Create a new wine record."""
    return wine_service.create_wine(wine)


@router.get("/{wine_id}", response_model=WineResponse)
async def get_wine(
    wine_id: int,
    wine_service: WineService = Depends(get_wine_service)
):
    """Get wine details by ID."""
    wine = wine_service.get_wine(wine_id)
    if wine is None:
        raise HTTPException(status_code=404, detail="Wine not found")
    return wine


@router.get("", response_model=list[WineResponse])
async def list_wines(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    wine_service: WineService = Depends(get_wine_service)
):
    """List wines with pagination."""
    return wine_service.list_wines(skip=skip, limit=limit)


@router.put("/{wine_id}", response_model=WineResponse)
async def update_wine(
    wine_id: int,
    wine: WineUpdate,
    wine_service: WineService = Depends(get_wine_service)
):
    """Update wine information."""
    updated = wine_service.update_wine(wine_id, wine)
    if updated is None:
        raise HTTPException(status_code=404, detail="Wine not found")
    return updated


@router.get("/search/query", response_model=list[WineResponse])
async def search_wines(
    q: str = Query(..., min_length=1),
    wine_service: WineService = Depends(get_wine_service)
):
    """Search wines by name, region, or varietals."""
    return wine_service.search_wines(q)


@router.post("/identify", response_model=WineIdentificationResult)
async def identify_wine(
    extracted_text: str = Query(..., min_length=1),
    wine_service: WineService = Depends(get_wine_service)
):
    """Identify wine from OCR extracted label text."""
    return wine_service.identify_wine_from_ocr(extracted_text)


@router.post("/collection/{wine_id}")
async def add_to_collection(
    wine_id: int,
    user_id: int = Query(...),
    tasting_notes: str = Query(None),
    rating: float = Query(None, ge=1, le=5),
    wine_service: WineService = Depends(get_wine_service)
):
    """Add wine to user's collection."""
    return wine_service.add_to_collection(user_id, wine_id, tasting_notes, rating)


@router.get("/collection/user/{user_id}")
async def get_user_collection(
    user_id: int,
    wine_service: WineService = Depends(get_wine_service)
):
    """Get user's wine collection."""
    return wine_service.get_user_collection(user_id)
