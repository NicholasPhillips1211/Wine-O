from fastapi import APIRouter


router = APIRouter(prefix="/ai", tags=["ai"])


@router.get("/status")
async def status():
    return {"service": "ai", "status": "scaffolded"}