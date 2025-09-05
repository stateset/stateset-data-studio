#!/usr/bin/env python3
"""
Special runner for the FastAPI server with debug mode enabled
and direct integration with the app.
"""

import os
import sys
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn

def main():
    # Set environment variables needed for the server
    os.environ["PYTHONPATH"] = os.path.dirname(os.path.abspath(__file__))
    
    # Create a minimal FastAPI app
    app = FastAPI()
    
    @app.get("/")
    async def root():
        return {"message": "Hello World"}
    
    # Run the server
    uvicorn.run(
        "backend.app:app", 
        host="0.0.0.0", 
        port=8000, 
        log_level="debug",
        reload=True
    )

if __name__ == "__main__":
    main()