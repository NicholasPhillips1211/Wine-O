from fastapi import APIRouter


router = APIRouter(prefix="/ocr", tags=["ocr"])


@router.get("/status")
async def status():
    return {"service": "ocr", "status": "scaffolded"}