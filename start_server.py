#!/usr/bin/env python3
"""
Simple script to start the FastAPI backend server for testing.
"""
import subprocess
import sys
import os
import time

def main():
    # Ensure we're in the project root
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    print(f"Working from directory: {os.getcwd()}")
    
    # Start the backend server
    print("Starting the backend server...")
    
    # Run the backend app from the backend module with verbose output
    backend_cmd = ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--log-level", "debug"]
    
    # Run in foreground to see output
    try:
        subprocess.run(backend_cmd)
    except KeyboardInterrupt:
        print("Server stopped by user")
    except Exception as e:
        print(f"Error starting server: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)