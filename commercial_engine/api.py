"""HTTP API. Rendering never happens inside a request: POST returns 202 with job
ids, a separate worker process renders, GET polls status."""
from __future__ import annotations

from functools import lru_cache

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field

from .auth import require_api_key
from .config import settings
from .jobs import enqueue
from .manifest import ManifestError
from .state import IllegalTransition, JobNotFound, Store

app = FastAPI(title="JobCommand Commercial Engine")


@lru_cache
def get_store() -> Store:
    return Store(settings.database_path)


class EnqueueRequest(BaseModel):
    manifest: str = Field(description="Plain file name inside MANIFESTS_DIR, e.g. jobcommand_v2.csv")
    video_ids: list[str] | None = Field(default=None, description="Subset of commercials; default all")


class ApproveRequest(BaseModel):
    approved_by: str = Field(min_length=1)
    note: str | None = None


@app.get("/health")
def health() -> dict:
    return {"ok": True}


@app.post("/commercials", status_code=202, dependencies=[Depends(require_api_key)])
def create_commercials(req: EnqueueRequest, store: Store = Depends(get_store)) -> dict:
    try:
        jobs = enqueue(store, req.manifest, req.video_ids)
    except ManifestError as exc:
        raise HTTPException(status_code=422, detail={"problems": exc.problems})
    return {"jobs": jobs}


@app.get("/commercials", dependencies=[Depends(require_api_key)])
def list_commercials(store: Store = Depends(get_store)) -> dict:
    return {"jobs": store.list_jobs()}


@app.get("/commercials/{job_id}", dependencies=[Depends(require_api_key)])
def get_commercial(job_id: str, store: Store = Depends(get_store)) -> dict:
    try:
        job = store.get_job(job_id)
    except JobNotFound:
        raise HTTPException(status_code=404, detail="job not found")
    return {"job": job, "scenes": store.scenes(job_id), "events": store.events(job_id)}


@app.post("/commercials/{job_id}/retry", dependencies=[Depends(require_api_key)])
def retry_commercial(job_id: str, store: Store = Depends(get_store)) -> dict:
    try:
        job = store.get_job(job_id)
        if job["status"] not in ("failed", "staged"):
            raise IllegalTransition(f"only failed or staged jobs can be retried (job is {job['status']})")
        return {"job": store.transition(job_id, "queued", note="retry requested", expect=job["status"])}
    except JobNotFound:
        raise HTTPException(status_code=404, detail="job not found")
    except IllegalTransition as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@app.post("/commercials/{job_id}/approve", dependencies=[Depends(require_api_key)])
def approve_commercial(job_id: str, req: ApproveRequest, store: Store = Depends(get_store)) -> dict:
    try:
        return {"job": store.approve(job_id, approved_by=req.approved_by, note=req.note)}
    except JobNotFound:
        raise HTTPException(status_code=404, detail="job not found")
    except IllegalTransition as exc:
        raise HTTPException(status_code=409, detail=str(exc))
