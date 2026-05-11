from fastapi import APIRouter, Depends, Query
from typing import List, Optional

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

@router.post("", response_model=WineResponse)
async def create_wine(
    wine_in: WineCreate,
    wine_service: WineService = Depends(get_wine_service)
):
    """Create a new wine record."""
    return wine_service.create_wine(wine_in)

@router.get("/{wine_id}", response_model=WineResponse)
async def get_wine(
    wine_id: int,
    wine_service: WineService = Depends(get_wine_service)
):
    """Get a wine by ID."""
    return wine_service.get_wine(wine_id)

@router.get("", response_model=List[WineResponse])
async def list_wines(
    skip: int = 0,
    limit: int = 100,
    wine_service: WineService = Depends(get_wine_service)
):
    """List wines with pagination."""
    return wine_service.list_wines(skip=skip, limit=limit)

@router.put("/{wine_id}", response_model=WineResponse)
async def update_wine(
    wine_id: int,
    wine_in: WineUpdate,
    wine_service: WineService = Depends(get_wine_service)
):
    """Update an existing wine record."""
    return wine_service.update_wine(wine_id, wine_in)

@router.get("/search/query", response_model=List[WineSearchResponse])
async def search_wines(
    q: str = Query(..., min_length=1),
    wine_service: WineService = Depends(get_wine_service)
):
    """Search for wines by query string."""
    return wine_service.search_wines(q)

@router.post("/identify", response_model=WineIdentificationResponse)
async def identify_wine(
    request: WineIdentificationRequest,
    wine_service: WineService = Depends(get_wine_service)
):
    """Identify a wine from an image/label."""
    return wine_service.identify_wine(request)

@router.post("/collection/{collection_id}", response_model=WineResponse)
async def add_to_collection(
    collection_id: int,
    wine_id: int,
    wine_service: WineService = Depends(get_wine_service)
):
    """Add a wine to a user's collection."""
    return wine_service.add_to_collection(collection_id, wine_id)

@router.get("/collection/user/{user_id}", response_model=List[WineResponse])
async def get_user_collection_wines(
    user_id: int,
    wine_service: WineService = Depends(get_wine_service)
):
    """Get all wines in a user's collection."""
    return wine_service.get_user_collection_wines(user_id)
