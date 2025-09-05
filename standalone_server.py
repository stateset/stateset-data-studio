#!/usr/bin/env python3
"""
Standalone server script to work around FastAPI UploadFile import issues
"""

import os
import sys
import uvicorn

# Make sure our package is in the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Run the server with custom settings"""
    
    # These settings are important to avoid import loops and allow slower startup
    uvicorn.run(
        "backend.app:app",
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=False,  # Don't use reload to avoid import issues
        workers=1,     # Single worker
        timeout_keep_alive=120,  # Keep connections alive longer
        limit_concurrency=100,  # Limit concurrent connections
    )

if __name__ == "__main__":
    main()