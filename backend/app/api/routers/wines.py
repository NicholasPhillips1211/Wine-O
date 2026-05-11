from fastapi import APIRouter


router = APIRouter(prefix="/wines", tags=["wines"])


@router.get("/status")
async def status():
    return {"service": "wines", "status": "scaffolded"}