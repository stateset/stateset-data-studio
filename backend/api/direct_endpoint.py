"""Direct API endpoint that doesn't require request/background dependencies"""
from __future__ import annotations

import logging
import os
import json
from pathlib import Path
from typing import Optional, Literal, Dict, Any
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    Form,
    HTTPException,
    status,
)
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy.orm import Session

from backend.api._base import BaseRouter, JobResponse
from backend.services import files
from backend.services.jobs import JobService
from backend.db.session import get_db

# Set up logger for this module
logger = logging.getLogger(__name__)

router: APIRouter = BaseRouter(prefix="/direct", tags=["Direct Endpoints"])

# Direct endpoint that doesn't require Request parameter
@router.post("/create-qa", status_code=status.HTTP_202_ACCEPTED, response_model=JobResponse)
async def create_qa_direct(
    background_tasks: BackgroundTasks,  # This is injected by FastAPI
    project_id: str = Form(...),
    input_file: str = Form(...),
    qa_type: Literal["qa", "cot", "summary", "extraction"] = Form("qa"),
    num_pairs: Optional[int] = Form(None),
    verbose: bool = Form(False),
    db: Session = Depends(get_db),
):
    """Direct implementation of create-qa without dependency issues"""
    try:
        logger.info(f"Creating QA job: project_id={project_id}, input_file={input_file}, qa_type={qa_type}, num_pairs={num_pairs}")
        path = files.normalise_or_404(input_file)
        logger.info(f"Normalized path: {path}")
        return JobService.queue_create(db, project_id, path, qa_type, num_pairs, background_tasks)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating QA job: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create QA job: {str(e)}"
        )

# Direct endpoint for downloading job results without request dependency
@router.get("/{job_id}/download", response_model=None)
async def download_job_direct(
    job_id: str,
    db: Session = Depends(get_db)
):
    """Direct implementation of job download without dependency issues"""
    try:
        logger.info(f"Downloading job result directly: job_id={job_id}")
        job = JobService.get_job(db, job_id)
        
        if not job:
            logger.error(f"Job not found: {job_id}")
            raise HTTPException(status_code=404, detail="Job not found")
        
        if not job.output_file or not Path(job.output_file).exists():
            logger.error(f"Output file not found for job: {job_id}")
            
            # Try to find the file with alternative paths
            possible_paths = [
                job.output_file,
                f"data/generated/{job_id}_qa_pairs.json" if job.job_type == "create" else None,
                f"data/cleaned/{job_id}_curated.json" if job.job_type == "curate" else None,
                f"data/final/{job_id}.jsonl" if job.job_type == "save-as" else None
            ]
            
            alternative_file = None
            for path in possible_paths:
                if path and Path(path).exists():
                    alternative_file = path
                    logger.info(f"Found alternative file path: {alternative_file}")
                    break
            
            if alternative_file:
                job.output_file = alternative_file
                db.commit()
            else:
                raise HTTPException(status_code=404, detail="Output file not found")
        
        # Directly read the file content
        content = Path(job.output_file).read_text()
        
        # Return the content as a JSON response with filename
        return JSONResponse(content={
            "filename": Path(job.output_file).name,
            "content": content
        })
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error downloading job result: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to download job result: {str(e)}"
        )
