"""Pydantic models for wine domain."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class WineBase(BaseModel):
    name: str
    region: str
    vintage: int
    varietals: Optional[list[str]] = None
    alcohol_content: Optional[float] = None
    description: Optional[str] = None


class WineCreate(WineBase):
    pass


class WineUpdate(BaseModel):
    name: Optional[str] = None
    region: Optional[str] = None
    vintage: Optional[int] = None
    varietals: Optional[list[str]] = None
    alcohol_content: Optional[float] = None
    description: Optional[str] = None


class WineResponse(WineBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WineIdentificationResult(BaseModel):
    """Result from OCR/AI wine identification."""
    confidence: float
    wine: Optional[WineResponse] = None
    candidates: list[WineResponse] = []
    extracted_text: Optional[str] = None


class UserWineCollection(BaseModel):
    """User's collection of wines."""
    id: int
    user_id: int
    wine_id: int
    wine: WineResponse
    tasting_notes: Optional[str] = None
    rating: Optional[float] = None
    purchase_date: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class WineSearchResponse(BaseModel):
    """Search result for a wine."""
    id: int
    name: str
    region: str
    vintage: int
    score: Optional[float] = None


class WineIdentificationRequest(BaseModel):
    """Request to identify a wine from an image."""
    image_base64: str


class WineIdentificationResponse(BaseModel):
    """Response from identifying a wine."""
    identification_id: str
    result: WineIdentificationResult
