#!/usr/bin/env python3
"""
A simple API server to create QA jobs without dependency issues.
"""
import logging
import os
import sys
import json
import uuid
from datetime import datetime
from typing import Optional

import uvicorn
from fastapi import FastAPI, Form, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("fixed-api")

@app.get("/")
async def root():
    return {"message": "Fixed API server is running"}

@app.post("/create-qa")
async def create_qa(
    project_id: str = Form(...),
    input_file: str = Form(...),
    qa_type: str = Form("qa"),
    num_pairs: Optional[int] = Form(None),
    verbose: Optional[bool] = Form(False)
):
    """Simple endpoint to create QA jobs without the dependency issues"""
    logger.info(f"Create QA request: project_id={project_id}, input_file={input_file}, qa_type={qa_type}, num_pairs={num_pairs}")
    
    # Create a mock job
    job_id = str(uuid.uuid4())
    
    # Log all form data to help debug
    logger.info(f"Parameters received - project_id: {project_id}")
    logger.info(f"Parameters received - input_file: {input_file}")
    logger.info(f"Parameters received - qa_type: {qa_type}")
    logger.info(f"Parameters received - num_pairs: {num_pairs}")
    logger.info(f"Parameters received - verbose: {verbose}")
    
    # Return a mock job response
    return {
        "id": job_id,
        "status": "pending",
        "job_type": "create",
        "message": "This is a mock job response from the fixed API server. In a real implementation, this would queue a job."
    }

@app.post("/upload-file")
async def upload_file(
    project_id: str = Form(...),
    file: UploadFile = File(...)
):
    """Simple endpoint to handle file uploads without the dependency issues"""
    logger.info(f"Upload file request: project_id={project_id}, filename={file.filename}")
    
    # Create a mock job
    job_id = str(uuid.uuid4())
    
    # Return a mock job response
    return {
        "id": job_id,
        "status": "pending",
        "job_type": "ingest",
        "message": "This is a mock file upload response from the fixed API server."
    }

if __name__ == "__main__":
    port = 8006  # Use a different port
    logger.info(f"Starting fixed API server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)