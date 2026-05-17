"""Dedicated Blender worker orchestration endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.app.reconstruction.blender.job_registry import blender_jobs
from backend.app.reconstruction.blender.worker_service import BlenderWorkerService


router = APIRouter(prefix="/blender", tags=["blender"])
_worker = BlenderWorkerService()


class BlenderStartRequest(BaseModel):
    job_id: str
    scaffold_uri: str


@router.post("/jobs/start")
async def start_blender_job(request: BlenderStartRequest) -> dict:
    payload = _worker.run_refinement(request.job_id, request.scaffold_uri)
    blender_jobs.upsert(request.job_id, {**payload, "status": payload.get("status", "queued"), "log": "Blender job accepted"})
    return payload


@router.get("/jobs/{job_id}/status")
async def get_blender_job_status(job_id: str) -> dict:
    record = blender_jobs.get(job_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Blender job not found")
    return {
        "job_id": job_id,
        "status": record.get("status", "unknown"),
        "refined_mesh": record.get("refined_mesh"),
        "updated_at": record.get("updated_at"),
    }


@router.get("/jobs/{job_id}/logs")
async def get_blender_job_logs(job_id: str) -> dict:
    record = blender_jobs.get(job_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Blender job not found")
    return {"job_id": job_id, "logs": record.get("logs", [])}
