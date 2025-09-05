from __future__ import annotations

"""Legacy‑compatibility endpoints that don't fit the clean CRUD routers.

These wrappers simply forward to the appropriate `JobService` helper so we
avoid duplicate business logic.  Keep them around while the frontend is still
calling the old paths.
"""

from pathlib import Path
from typing import Optional, Literal, List, Dict, Any, Union

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from fastapi.responses import JSONResponse
from fastapi import APIRouter, Depends

from sqlalchemy.orm import Session

from backend.api._base import BaseRouter, JobResponse, JobCreationResponse
from backend.services import files
from backend.services.jobs import JobService
from backend.db.session import get_db
from backend.db.models import Job
from pydantic import BaseModel, Field 

router: APIRouter = BaseRouter(prefix="/extensions", tags=["Extensions"])

# ---------------------------------------------------------------------------
# 1. Generic file / URL ingest  (superset of /jobs/ingest + /jobs/ingest/url)
# ---------------------------------------------------------------------------

@router.post("/process-file", status_code=status.HTTP_202_ACCEPTED, response_model=JobCreationResponse)
async def process_file(
    background: BackgroundTasks,
    project_id: str = Form(...),
    # supply **one** of the following
    file: Optional[UploadFile] = File(None),
    url: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    """Upload a file *or* pass a URL/Youtube link; queues an ingest job."""
    if not (file or url):
        raise HTTPException(400, "Provide either file or url")

    if file and url:
        raise HTTPException(400, "Specify only one of file OR url, not both")

    result = None
    
    if file:
        # Save the uploaded file
        dst_dir = files.ensure_output_dir(files.get_file_type(file.filename))
        dst_path = dst_dir / file.filename.replace(" ", "_")
        with dst_path.open("wb") as fh:
            fh.write(await file.read())
        
        # Use the queue_ingest method which now sets the output file
        result = JobService.queue_ingest(db, project_id, str(dst_path), background)
    else:
        # url branch
        assert url  # mypy
        if "youtube.com" in url or "youtu.be" in url:
            # Use the queue_ingest_youtube method which now sets the output file
            result = JobService.queue_ingest_youtube(db, project_id, url, background)
        else:
            # Use the queue_ingest_url method which now sets the output file
            result = JobService.queue_ingest_url(db, project_id, url, background)
    
    # Return a Pydantic model instance instead of raw dict
    return JobCreationResponse(
        id=result.id,
        status=result.status,
        job_type=result.job_type
    )

# ---------------------------------------------------------------------------
# 2. Curate QA (thin wrapper)
# ---------------------------------------------------------------------------

@router.post("/curate-qa", status_code=status.HTTP_202_ACCEPTED, response_model=JobResponse)
async def curate_qa(
    background: BackgroundTasks,
    project_id: str = Form(...),
    input_file: str = Form(...),
    threshold: Optional[float] = Form(None),
    batch_size: Optional[int] = Form(None),
    db: Session = Depends(get_db),
):
    path = files.normalise_or_404(input_file)
    return JobService.queue_curate(db, project_id, path, threshold, batch_size, background)

# ---------------------------------------------------------------------------
# 3. Convert / save‑as
# ---------------------------------------------------------------------------

@router.post("/convert-format", status_code=status.HTTP_202_ACCEPTED, response_model=JobResponse)
async def convert_format(
    background: BackgroundTasks,
    project_id: str = Form(...),
    input_file: str = Form(...),
    format: Literal["jsonl", "alpaca", "llama", "openai", "csv", "json"] = Form("jsonl"),
    storage: Optional[Literal["local", "s3", "azure", "gcp"]] = Form(None),
    output_name: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    path = files.normalise_or_404(input_file)
    return JobService.queue_save_as(
        db, project_id, path, format, storage, output_name, background
    )

# ---------------------------------------------------------------------------
# 4. List files (helper – no Job)
# ---------------------------------------------------------------------------

def _list_files(folder: Path, suffixes: tuple[str, ...]) -> List[dict]:
    items: list[dict] = []
    for p in folder.glob("*"):
        if p.is_file() and p.suffix in suffixes:
            stat = p.stat()
            items.append({
                "filename": p.name,
                "path": str(p),
                "size": stat.st_size,
                "modified": stat.st_mtime,
            })
    items.sort(key=lambda x: x["modified"], reverse=True)
    return items


class FileListResponse(BaseModel):
    """Response model for file listing endpoints"""
    files: List[dict]

@router.get("/list-files/{kind}", response_model=FileListResponse)
async def list_files(kind: Literal["output", "generated", "cleaned", "final"]):
    """List files of a specific type from the project data directories"""
    base = files.ensure_output_dir(kind)  # will return Path()
    if not base.exists():
        return FileListResponse(files=[])
    suffix_map = {
        "output": (".txt",),
        "generated": (".json",),
        "cleaned": (".json",),
        "final": (".json", ".jsonl", ".csv"),
    }
    return FileListResponse(files=_list_files(base, suffix_map[kind]))
