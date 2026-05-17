from fastapi import APIRouter

from .routers import (
	ai,
	auth,
	blender,
	email,
	health,
	oauth,
	ocr,
	reconstruction,
	reconstruction_pipeline,
	wines,
	viewer,
)


api_router = APIRouter(prefix="/api/v1")

api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(email.router)
api_router.include_router(oauth.router)
api_router.include_router(wines.router)
api_router.include_router(ocr.router)
api_router.include_router(reconstruction.router)
api_router.include_router(reconstruction_pipeline.router)
api_router.include_router(blender.router)
api_router.include_router(viewer.router)
api_router.include_router(ai.router)