from __future__ import annotations

"""REST endpoints for Job operations.

Each endpoint is a *very thin* HTTP wrapper.  All business logic lives in
services.jobs.JobService so we can unit‑test it without FastAPI.
"""

import logging
from typing import Optional, Literal, List, Dict, Any, Union, Annotated

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy.orm import Session

from backend.api._base import BaseRouter, JobResponse, JobCreationResponse  # auto‑injects DB dependency
from backend.api.logging_utils import log_call
from backend.services import files
from backend.services.jobs import JobService
from backend.db.session import get_db
from backend.db.models import Job

logger = logging.getLogger(__name__)

router: APIRouter = BaseRouter(prefix="/jobs", tags=["Jobs"])

# Type aliases to simplify function signatures
FileUpload = Annotated[UploadFile, File()]
DB = Annotated[Session, Depends(get_db)]

# ---------------------------------------------------------------------------
# Ingest‑type endpoints
# ---------------------------------------------------------------------------

@router.post("/ingest", status_code=status.HTTP_202_ACCEPTED,
             response_model=JobCreationResponse)
@log_call
async def ingest_file(
    request: Request,
    background_tasks: BackgroundTasks,
    file: Annotated[UploadFile, File()],
    project_id: Annotated[str, Form()],
    db: DB,
):
    """Upload a file (pdf, txt, docx, …) and queue an ingest job."""
    dst_dir = files.ensure_output_dir(files.get_file_type(file.filename))
    dst_path = dst_dir / file.filename.replace(" ", "_")
    with dst_path.open("wb") as fh:
        fh.write(await file.read())

    result = JobService.queue_ingest(db, project_id, str(dst_path), background_tasks)
    return JobCreationResponse(id=result.id,
                               status=result.status,
                               job_type=result.job_type)


@router.post("/ingest/url", status_code=status.HTTP_202_ACCEPTED, response_model=JobResponse)
@log_call
async def ingest_url(
    request: Request,
    background_tasks: BackgroundTasks,
    project_id: Annotated[str, Form()],
    url: Annotated[str, Form()],
    db: DB,
):
    return JobService.queue_ingest_url(db, project_id, url, background_tasks)


@router.post("/ingest/youtube", status_code=status.HTTP_202_ACCEPTED, response_model=JobResponse)
@log_call
async def ingest_youtube(
    request: Request,
    background_tasks: BackgroundTasks,
    project_id: Annotated[str, Form()],
    youtube_url: Annotated[str, Form()],
    db: DB,
):
    return JobService.queue_ingest_youtube(db, project_id, youtube_url, background_tasks)

# ---------------------------------------------------------------------------
# Create‑type endpoints
# ---------------------------------------------------------------------------

@router.post("/create", status_code=status.HTTP_202_ACCEPTED, response_model=JobResponse)
@log_call
async def create_pairs(
    background_tasks: BackgroundTasks,
    project_id: Annotated[str, Form()],
    input_file: Annotated[str, Form()],
    qa_type: Annotated[Literal["qa", "cot", "summary", "extraction"], Form("qa")],
    num_pairs: Annotated[Optional[int], Form(None)],
    db: DB,
):
    input_path = files.normalise_or_404(input_file)
    return JobService.queue_create(
        db, project_id, input_path, qa_type, num_pairs, background_tasks
    )


@router.post("/create/advanced", status_code=status.HTTP_202_ACCEPTED, response_model=JobResponse)
@log_call
async def create_pairs_advanced(
    request: Request,
    background_tasks: BackgroundTasks,
    project_id: Annotated[str, Form()],
    input_file: Annotated[str, Form()],
    qa_type: Annotated[Literal["qa", "cot", "summary", "extraction"], Form("qa")],
    num_pairs: Annotated[Optional[int], Form(None)],
    temperature: Annotated[Optional[float], Form(None)],
    chunk_size: Annotated[Optional[int], Form(None)],
    max_tokens: Annotated[Optional[int], Form(None)],
    overlap: Annotated[Optional[int], Form(None)],
    prompts_json: Annotated[Optional[str], Form(None)],
    db: DB,
):
    input_path = files.normalise_or_404(input_file)
    return JobService.queue_create_advanced(
        db,
        project_id,
        input_path,
        qa_type,
        num_pairs,
        temperature,
        chunk_size,
        max_tokens,
        overlap,
        prompts_json,
        background_tasks,
    )

# ---------------------------------------------------------------------------
# Curate‑type endpoints
# ---------------------------------------------------------------------------

@router.post("/curate", status_code=status.HTTP_202_ACCEPTED, response_model=JobResponse)
@log_call
async def curate_pairs(
    request: Request,
    background_tasks: BackgroundTasks,
    project_id: Annotated[str, Form()],
    input_file: Annotated[str, Form()],
    threshold: Annotated[Optional[float], Form(None)],
    batch_size: Annotated[Optional[int], Form(None)],
    db: DB,
):
    input_path = files.normalise_or_404(input_file)
    return JobService.queue_curate(
        db, project_id, input_path, threshold, batch_size, background_tasks
    )


@router.post("/curate/auto", status_code=status.HTTP_202_ACCEPTED, response_model=JobResponse)
@log_call
async def curate_auto(
    request: Request,
    background_tasks: BackgroundTasks,
    project_id: Annotated[str, Form()],
    threshold: Annotated[Optional[float], Form(None)],
    batch_size: Annotated[Optional[int], Form(None)],
    db: DB,
):
    return JobService.queue_curate_auto(
        db, project_id, threshold, batch_size, background_tasks
    )

# ---------------------------------------------------------------------------
# Save‑as
# ---------------------------------------------------------------------------

@router.post("/save-as", status_code=status.HTTP_202_ACCEPTED, response_model=JobResponse)
@log_call
async def save_as(
    request: Request,
    background_tasks: BackgroundTasks,
    project_id: Annotated[str, Form()],
    input_file: Annotated[str, Form()],
    format: Annotated[Literal["jsonl", "alpaca", "llama", "openai", "csv", "json"], Form("jsonl")],
    storage: Annotated[Optional[Literal["local", "s3", "azure", "gcp"]], Form(None)],
    output_name: Annotated[Optional[str], Form(None)],
    db: DB,
):
    input_path = files.normalise_or_404(input_file)
    return JobService.queue_save_as(
        db,
        project_id,
        input_path,
        format,
        storage,
        output_name,
        background_tasks,
    )


@router.post("/save-as/auto", status_code=status.HTTP_202_ACCEPTED, response_model=JobResponse)
@log_call
async def save_as_auto(
    request: Request,
    background_tasks: BackgroundTasks,
    project_id: Annotated[str, Form()],
    format: Annotated[Literal["jsonl", "alpaca", "llama", "openai", "csv", "json"], Form("jsonl")],
    storage: Annotated[Optional[Literal["local", "s3", "azure", "gcp"]], Form(None)],
    output_name: Annotated[Optional[str], Form(None)],
    source_type: Annotated[Literal["curate", "create"], Form("curate")],
    db: DB,
):
    return JobService.queue_save_as_auto(
        db,
        project_id,
        format,
        storage,
        output_name,
        source_type,
        background_tasks,
    )

# ---------------------------------------------------------------------------
# Retrieval endpoints (thin wrappers)
# ---------------------------------------------------------------------------

@router.get("/{job_id}", response_model=JobResponse)
@log_call
async def get_job(request: Request, job_id: str, db: DB):
    job = JobService.get_job(db, job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return job


@router.get("/{job_id}/preview", response_model=None)
@log_call
async def preview(request: Request, job_id: str, db: DB) -> JSONResponse:
    """Get a preview of job output"""
    return JobService.preview_job(db, job_id)


@router.get("/{job_id}/download", response_model=None)
@log_call
async def download_json(request: Request, job_id: str, db: DB) -> JSONResponse:
    """Download job output as JSON"""
    return JobService.download_job_json(db, job_id)


@router.get("/{job_id}/file", response_model=None)
@log_call
async def download_file(request: Request, job_id: str, db: DB) -> JSONResponse:
    """Download the file associated with a job"""
    return JobService.download_job_file(db, job_id)


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
@log_call
async def delete(request: Request, job_id: str, db: DB):
    if not JobService.delete_job(db, job_id):
        raise HTTPException(404, "Job not found")

# ---------------------------------------------------------------------------
# Listing
# ---------------------------------------------------------------------------

@router.get("", response_model=List[JobResponse])
async def list_jobs(
    db: Annotated[Session, Depends(get_db)],
    project_id: Optional[str] = None,
    status_param: Optional[str] = None,
    job_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
):
    # Get the status parameter and use it correctly
    status = status_param
    return JobService.list_jobs(db, project_id, status, job_type, skip, limit)