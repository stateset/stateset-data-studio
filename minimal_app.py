#!/usr/bin/env python3
"""
Minimal working server that only provides the basic endpoints
"""

import os
import sys
import logging
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Depends, Form, File, UploadFile, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Setup logger
logger = logging.getLogger("minimal-app")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
logger.addHandler(handler)

# Create FastAPI app
app = FastAPI(
    title="Minimal Synthetic Data API",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health endpoints
@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Synthetic Data API is running"}

@app.get("/healthz")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok"}

# File upload endpoint (the problematic one)
@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """Simple file upload endpoint that doesn't do much"""
    try:
        # Get file info
        filename = file.filename
        content_type = file.content_type
        
        # Only log file details - don't actually save it
        logger.info(f"Received file: {filename} ({content_type})")
        
        # Return success response
        return {
            "filename": filename,
            "content_type": content_type, 
            "status": "received"
        }
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"message": f"Error processing file: {str(e)}"}
        )

def main():
    """Run the server"""
    uvicorn.run(
        "minimal_app:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )

if __name__ == "__main__":
    main()