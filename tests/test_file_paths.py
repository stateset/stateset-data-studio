#!/usr/bin/env python3
import os
import json
import logging
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('file_paths_debug.log')
    ]
)
logger = logging.getLogger("file-paths-debug")

def diagnose_output_paths():
    """
    Diagnose issues with output paths for QA pair generation.
    """
    # Test file structure
    print("\n=== File Structure Diagnosis ===")
    
    # Key directories to check
    directories = [
        "",  # Current directory
        "data",
        "data/output",
        "data/generated",
        "backend",
        "backend/data",
        "backend/data/output",
        "backend/data/generated",
    ]
    
    cwd = os.getcwd()
    print(f"Current working directory: {cwd}")
    
    for dir_path in directories:
        abs_path = os.path.abspath(dir_path)
        exists = os.path.exists(abs_path)
        is_dir = os.path.isdir(abs_path) if exists else False
        is_writable = os.access(abs_path, os.W_OK) if exists else False
        
        print(f"Directory: {abs_path}")
        print(f"  - Exists: {exists}")
        print(f"  - Is directory: {is_dir}")
        print(f"  - Writable: {is_writable}")
        
        if exists and is_dir:
            try:
                # List files in directory
                files = os.listdir(abs_path)
                print(f"  - Contains {len(files)} files/directories")
                
                # Count specific file types
                qa_files = [f for f in files if f.endswith("_qa_pairs.json")]
                if qa_files:
                    print(f"  - Contains {len(qa_files)} QA pair files:")
                    for qa_file in qa_files:
                        file_path = os.path.join(abs_path, qa_file)
                        size = os.path.getsize(file_path)
                        print(f"    - {qa_file} ({size} bytes)")
            except Exception as e:
                print(f"  - Error listing directory: {str(e)}")
    
    # Test file creation
    print("\n=== File Creation Test ===")
    
    # Create test files in different locations to check write permissions
    test_locations = [
        "data/generated",
        "backend/data/generated"
    ]
    
    for location in test_locations:
        try:
            # Create directory if it doesn't exist
            os.makedirs(location, exist_ok=True)
            
            # Create timestamp for unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            test_file = os.path.join(location, f"test_file_{timestamp}.json")
            
            # Create test file
            test_data = {
                "test": True,
                "timestamp": timestamp,
                "location": location
            }
            
            with open(test_file, 'w') as f:
                json.dump(test_data, f, indent=2)
            
            # Verify file exists
            if os.path.exists(test_file):
                size = os.path.getsize(test_file)
                print(f"Successfully created test file at: {test_file} ({size} bytes)")
            else:
                print(f"Failed to create test file at: {test_file}")
        except Exception as e:
            print(f"Error creating test file in {location}: {str(e)}")
    
    # Test path resolution
    print("\n=== Path Resolution Test ===")
    
    test_paths = [
        "data/output/test.txt",
        "backend/data/output/test.txt",
        "data/generated/test_qa_pairs.json",
        "backend/data/generated/test_qa_pairs.json"
    ]
    
    for path in test_paths:
        abs_path = os.path.abspath(path)
        exists = os.path.exists(path)
        parent_dir = os.path.dirname(path)
        parent_exists = os.path.exists(parent_dir)
        
        print(f"Path: {path}")
        print(f"  - Absolute path: {abs_path}")
        print(f"  - Exists: {exists}")
        print(f"  - Parent directory: {parent_dir}")
        print(f"  - Parent exists: {parent_exists}")

if __name__ == "__main__":
    print("=== Diagnosing File Path Issues ===")
    diagnose_output_paths()
    print("\n=== Diagnosis Complete ===")