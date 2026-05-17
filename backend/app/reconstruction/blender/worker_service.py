"""Blender worker service abstraction for headless refinement jobs.

This implementation runs the Blender headless command in a background thread
when `BLENDER_WORKER_ENABLED` is True. Output lines are streamed into the
in-memory `blender_jobs` registry for API consumption. The service gracefully
falls back to a simulated response when the worker flag is disabled.
"""

from __future__ import annotations

import shlex
import subprocess
import threading
import time
from pathlib import Path
from typing import Any

from backend.app.core.config import settings
from backend.app.reconstruction.blender.blender_runner import BlenderRunner
from backend.app.reconstruction.blender.job_registry import blender_jobs


class BlenderWorkerService:
    """Runs Blender refinement in worker context or simulated mode.

    In production this class should be used from a dedicated worker process
    (or Celery task) that has Blender available on PATH or via
    `settings.BLENDER_BINARY`.
    """

    def __init__(self) -> None:
        self.runner = BlenderRunner()

    def build_refinement_payload(self, job_id: str, scaffold_uri: str) -> dict[str, Any]:
        script_root = Path(settings.BLENDER_SCRIPT_ROOT)
        reconstruct_script = script_root / "reconstruct.py"
        command = self.runner.build_command(
            str(reconstruct_script), args=["--job-id", job_id, "--input", scaffold_uri]
        )

        return {
            "job_id": job_id,
            "blender_enabled": settings.BLENDER_WORKER_ENABLED,
            "command": command,
            "script_exists": reconstruct_script.exists(),
            "docker_image": settings.BLENDER_DOCKER_IMAGE,
        }

    def _run_subprocess(self, job_id: str, cmd: str, cwd: Path | None = None, timeout: int | None = None, max_retries: int = 1) -> None:
        """Execute `cmd` in a background thread, stream stdout/stderr to the registry.

        This function is intentionally synchronous (called inside a Thread) so
        it's easy to reason about retries and timeouts.
        """

        def _worker():
            attempt = 0
            while attempt < max_retries:
                attempt += 1
                blender_jobs.upsert(job_id, {"status": "running", "log": f"Starting attempt {attempt}"})
                try:
                    parts = shlex.split(cmd)
                    # Replace executable token with configured binary when present
                    if parts:
                        parts[0] = settings.BLENDER_BINARY or parts[0]

                    proc = subprocess.Popen(
                        parts,
                        cwd=str(cwd) if cwd else None,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        bufsize=1,
                    )

                    start = time.time()
                    assert proc.stdout is not None
                    for line in proc.stdout:
                        line = line.rstrip("\n")
                        blender_jobs.upsert(job_id, {"log": line})
                        # enforce soft timeout check
                        if timeout and (time.time() - start) > timeout:
                            proc.kill()
                            blender_jobs.upsert(job_id, {"log": "Timeout reached, killed process"})
                            break

                    ret = proc.wait()
                    if ret == 0:
                        blender_jobs.upsert(job_id, {"status": "completed", "log": "Blender finished successfully"})
                        return
                    else:
                        blender_jobs.upsert(job_id, {"status": "failed", "log": f"Blender exited with code {ret}"})
                except Exception as exc:  # pragma: no cover - safety net
                    blender_jobs.upsert(job_id, {"status": "failed", "log": f"Exception: {exc}"})

                if attempt < max_retries:
                    blender_jobs.upsert(job_id, {"log": f"Retrying (attempt {attempt+1}) in 1s"})
                    time.sleep(1)

            # If we reach here all attempts failed
            blender_jobs.upsert(job_id, {"status": "failed", "log": "All retry attempts exhausted"})

        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()

    def run_refinement(self, job_id: str, scaffold_uri: str) -> dict[str, Any]:
        payload = self.build_refinement_payload(job_id, scaffold_uri)

        if not settings.BLENDER_WORKER_ENABLED:
            return {
                **payload,
                "status": "simulated",
                "refined_mesh": f"reconstruction/{job_id}/blender/refined.glb",
                "uv_ready": True,
                "glass_shader": "enabled",
            }

        # Start background execution of Blender in this process. In real
        # deployments the worker process should be isolated (Docker, k8s job).
        cmd = payload["command"]
        cwd = Path(settings.BLENDER_SCRIPT_ROOT)
        blender_jobs.upsert(job_id, {"status": "queued", "log": "Job queued for execution"})

        # Kick off the subprocess runner with configured timeout and a couple retries
        self._run_subprocess(
            job_id,
            cmd,
            cwd=cwd,
            timeout=settings.BLENDER_TIMEOUT_SECONDS,
            max_retries=2,
        )

        return {
            **payload,
            "status": "queued",
            "refined_mesh": f"reconstruction/{job_id}/blender/refined.glb",
            "uv_ready": True,
            "glass_shader": "enabled",
            "worker_hint": "local-thread",
        }
