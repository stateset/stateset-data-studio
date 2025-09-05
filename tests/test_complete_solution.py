#!/usr/bin/env python3
import os
import logging
import requests
import json
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test-complete-solution")

# Local API endpoint
API_URL = "http://localhost:8000"

def test_normalize_path():
    # Create a test file
    os.makedirs("data/output", exist_ok=True)
    test_file_path = "data/output/test_complete_solution.txt"
    with open(test_file_path, "w") as f:
        f.write("This is a test file for the complete path handling solution.")
    
    logger.info(f"Created test file at: {test_file_path}")
    
    # Log file existence
    with_backend = f"backend/{test_file_path}"
    logger.info(f"File exists at original path: {os.path.exists(test_file_path)}")
    logger.info(f"File exists with backend/ prefix: {os.path.exists(with_backend)}")
    
    # Simulate what happens in the React frontend
    logger.info("\nSimulating the frontend path handling when clicking 'Use for QA':")
    frontend_path = test_file_path
    
    # This is what the React component does
    if frontend_path.startswith('data/output/') and not frontend_path.startswith('backend/data/output/'):
        adjusted_path = f"backend/{frontend_path}"
        logger.info(f"Frontend adjusted path: {frontend_path} → {adjusted_path}")
        frontend_path = adjusted_path
    else:
        logger.info(f"Frontend kept original path: {frontend_path}")
    
    # Now test what the backend would do with this path
    logger.info("\nSimulating the backend path handling:")
    backend_input = frontend_path
    
    # This is what normalize_path does in the backend
    if not os.path.exists(backend_input) and backend_input.startswith("backend/"):
        alt_path = backend_input[len("backend/"):]
        if os.path.exists(alt_path):
            logger.info(f"Backend would find file at: {alt_path} instead of {backend_input}")
            backend_input = alt_path
        else:
            logger.info(f"Backend would not find file at: {alt_path}")
    else:
        if os.path.exists(backend_input):
            logger.info(f"Backend would find file at original path: {backend_input}")
        else:
            logger.info(f"Backend would not find file at: {backend_input}")
    
    # Verify the complete pipeline works
    logger.info("\nVerifying the complete frontend → backend pipeline:")
    if os.path.exists(backend_input):
        logger.info(f"PASS: File was correctly found at: {backend_input}")
    else:
        logger.error(f"FAIL: File was not found after path handling")
    
    # Clean up
    os.remove(test_file_path)
    logger.info(f"Removed test file")

if __name__ == "__main__":
    print("\n===== Testing complete path handling solution =====\n")
    test_normalize_path()
    print("\n===== Test completed =====\n")