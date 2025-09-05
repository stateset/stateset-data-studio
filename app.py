# app.py - Root level application wrapper for synthetic-data-studio
# This file serves as a wrapper around the backend app.py

import logging
from fastapi import FastAPI, Request
from fastapi.responses import ORJSONResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import importlib
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Create the FastAPI app
app = FastAPI(
    title="StateSet Data Studio API",
    default_response_class=ORJSONResponse,
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, you'd want to limit this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add a simple root endpoint as health check
@app.get("/")
async def root():
    return {"status": "ok", "message": "StateSet Data Studio API"}

# Health check for monitoring
@app.get("/healthz")
async def healthz():
    return {"status": "ok"}

# CORS test
@app.get("/cors-test")
async def cors_test():
    return {"status": "success", "message": "CORS is working correctly"}

# Import the backend app dynamically
sys.path.insert(0, '.')
try:
    # Get the backend FastAPI app instance 
    backend_app = importlib.import_module("backend.app").app
    
    # Mount the backend app at the /api path
    app.mount("/api", backend_app)
    
    logger.info("Backend API mounted successfully")
except Exception as e:
    logger.error(f"Failed to mount backend API: {str(e)}")
    
    @app.get("/error")
    async def error():
        return {"status": "error", "message": f"Failed to load backend API: {str(e)}"}

# Import key API routes directly to ensure they're in the main app
try:
    from backend.db.session import get_db
    from backend.db.models import Job, Project
    from sqlalchemy.orm import Session
    from fastapi import Depends, File, UploadFile, Form, BackgroundTasks
    from backend.services.jobs import JobService
    from backend.services import files
    
    # File upload endpoint that was causing issues
    @app.post("/api/v1/upload-file")
    async def upload_file(
        background_tasks: BackgroundTasks,
        project_id: str = Form(...),
        file: UploadFile = File(...),
        db: Session = Depends(get_db)
    ):
        """Alternative file upload endpoint that avoids type inference issues"""
        try:
            dst_dir = files.ensure_output_dir(files.get_file_type(file.filename))
            dst_path = dst_dir / file.filename.replace(" ", "_")
            with dst_path.open("wb") as fh:
                fh.write(await file.read())
            result = JobService.queue_ingest(db, project_id, str(dst_path), background_tasks)
            return {
                "id": result.id, 
                "status": result.status, 
                "job_type": result.job_type
            }
        except Exception as e:
            logger.error(f"Error uploading file: {str(e)}")
            return {"status": "error", "message": f"Failed to upload file: {str(e)}"}
    
    # Add the fixed create-qa endpoint
    @app.post("/synthdata/create-qa")
    async def create_qa_pairs(
        background_tasks: BackgroundTasks,
        project_id: str = Form(...),
        input_file: str = Form(...),
        qa_type: str = Form("qa"),
        num_pairs: int = Form(None),
        verbose: bool = Form(False),
        db: Session = Depends(get_db)
    ):
        """Fixed implementation of the create-qa endpoint that had dependency issues"""
        try:
            path = files.normalise_or_404(input_file)
            # Use JobService directly
            result = JobService.queue_create(db, project_id, path, qa_type, num_pairs, background_tasks)
            return {
                "id": result.id, 
                "status": result.status, 
                "job_type": result.job_type
            }
        except Exception as e:
            logger.error(f"Error creating QA pairs: {str(e)}")
            return {"status": "error", "message": f"Failed to create QA pairs: {str(e)}"}
            
    # Add a completely new implementation of jobs/create
    @app.post("/jobs/create-qa")
    async def create_qa_job(
        background_tasks: BackgroundTasks,
        project_id: str = Form(...),
        input_file: str = Form(...),
        qa_type: str = Form("qa"),
        num_pairs: int = Form(None),
        db: Session = Depends(get_db)
    ):
        """Direct implementation of create-qa without dependency issues"""
        try:
            logger.info(f"Creating QA job with project_id={project_id}, input_file={input_file}, qa_type={qa_type}, num_pairs={num_pairs}")
            path = files.normalise_or_404(input_file)
            # Use JobService directly
            result = JobService.queue_create(db, project_id, path, qa_type, num_pairs, background_tasks)
            return {
                "id": result.id, 
                "status": result.status, 
                "job_type": result.job_type
            }
        except Exception as e:
            logger.error(f"Error creating QA job: {str(e)}")
            return {"status": "error", "message": f"Failed to create QA job: {str(e)}"}
            
    logger.info("Additional API routes mounted successfully")
except Exception as e:
    logger.error(f"Failed to set up additional API routes: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)