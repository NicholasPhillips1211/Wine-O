from fastapi import APIRouter

from .routers import ai, auth, health, ocr, reconstruction, wines


api_router = APIRouter(prefix="/api/v1")

api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(wines.router)
api_router.include_router(ocr.router)
api_router.include_router(reconstruction.router)
api_router.include_router(ai.router)