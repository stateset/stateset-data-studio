#!/usr/bin/env python3
import os
import logging

# Set up logging like in the app
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test-normalize-path")

def normalize_path(file_path):
    """
    Normalize file paths that might have 'backend/' prefix.
    If a path starts with 'backend/' but the file doesn't exist,
    try looking for the file without the prefix.
    """
    # Return the path as-is if it already exists
    if os.path.exists(file_path):
        logger.info(f"File exists at original path: {file_path}")
        return file_path
        
    # Check if the path has a backend/ prefix that needs to be removed
    if file_path.startswith("backend/"):
        alt_path = file_path[len("backend/"):]
        if os.path.exists(alt_path):
            logger.info(f"Found file at {alt_path} instead of {file_path}")
            return alt_path
            
    # If neither path exists, return original
    logger.warning(f"File not found at {file_path} or any alternative paths")
    return file_path

def test_with_existing_file():
    # Create a test file
    os.makedirs("data/output", exist_ok=True)
    test_file_path = "data/output/normalize_test.txt"
    with open(test_file_path, "w") as f:
        f.write("This is a test file for normalize_path")
    
    # Test cases
    test_cases = [
        "data/output/normalize_test.txt",  # Original path
        "backend/data/output/normalize_test.txt",  # With backend/ prefix
    ]
    
    print("\nTesting with existing files:")
    for path in test_cases:
        result = normalize_path(path)
        print(f"Input: {path} -> Output: {result}")
    
    # Clean up
    os.remove(test_file_path)

if __name__ == "__main__":
    print("Testing normalize_path function")
    test_with_existing_file()