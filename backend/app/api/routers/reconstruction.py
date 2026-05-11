from fastapi import APIRouter


router = APIRouter(prefix="/3d", tags=["3d"])


@router.get("/status")
async def status():
    return {"service": "3d", "status": "scaffolded"}