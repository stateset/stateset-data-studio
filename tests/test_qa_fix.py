#!/usr/bin/env python3
import os
import json
import argparse
import tempfile
import logging
import uuid
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("qa-fix-test")

def test_safe_save():
    """Test the safe_save utility"""
    logger.info("Testing safe_save utility...")
    
    # Import the safe_save utility
    try:
        from synthetic_data_kit.utils.safe_save import safe_save_json
        
        # Create test data
        test_data = {
            "test": True,
            "timestamp": datetime.now().isoformat(),
            "qa_pairs": [
                {
                    "question": "What is this?",
                    "answer": "This is a test of the safe_save utility."
                }
            ]
        }
        
        # Test with various output paths
        test_paths = [
            os.path.join("data/generated", f"test_safe_save_{uuid.uuid4()}.json"),
            os.path.join("backend/data/generated", f"test_safe_save_{uuid.uuid4()}.json"),
            f"/tmp/test_safe_save_{uuid.uuid4()}.json"
        ]
        
        for path in test_paths:
            logger.info(f"Testing save to: {path}")
            saved_path = safe_save_json(test_data, path)
            
            if saved_path:
                logger.info(f"Successfully saved to: {saved_path}")
                
                # Verify the file exists and has content
                if os.path.exists(saved_path):
                    with open(saved_path, 'r') as f:
                        content = json.load(f)
                    
                    if "qa_pairs" in content:
                        logger.info(f"File has expected content with {len(content['qa_pairs'])} QA pairs")
                    else:
                        logger.error(f"File is missing expected content")
                else:
                    logger.error(f"File not found at: {saved_path}")
            else:
                logger.error(f"Failed to save to: {path}")
        
        return True
    except ImportError:
        logger.error("Failed to import safe_save_json")
        return False
    except Exception as e:
        logger.error(f"Error testing safe_save: {str(e)}")
        return False

def create_test_qa_job():
    """Create a test QA job to verify backend code"""
    logger.info("Creating test QA job...")
    
    # Create a test input file
    try:
        # Create a test input file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("This is a test input file for QA pair generation.")
            test_input = f.name
        
        logger.info(f"Created test input file: {test_input}")
        
        # Import backend SDK command
        sys.path.insert(0, os.getcwd())
        from backend.sdk_command import run_create_qa
        
        # Create args for run_create_qa
        job_id = str(uuid.uuid4())
        args = [test_input, "--type", "qa", "-n", "3"]
        
        # Run the function directly
        logger.info(f"Running run_create_qa with job_id={job_id}")
        success = run_create_qa(job_id, args)
        
        if success:
            logger.info("QA job completed successfully")
            return True
        else:
            logger.error("QA job failed")
            return False
    except Exception as e:
        logger.error(f"Error creating test QA job: {str(e)}")
        return False
    finally:
        # Clean up the test input file
        if 'test_input' in locals() and os.path.exists(test_input):
            os.unlink(test_input)

if __name__ == "__main__":
    # Parse arguments
    parser = argparse.ArgumentParser(description="Test QA pair generation fixes")
    parser.add_argument("--safe-save", action="store_true", help="Test safe_save utility")
    parser.add_argument("--create-job", action="store_true", help="Test creating a QA job")
    
    args = parser.parse_args()
    
    # Default behavior if no args specified: run both tests
    if not (args.safe_save or args.create_job):
        args.safe_save = True
        args.create_job = True
    
    # Run tests
    if args.safe_save:
        safe_save_success = test_safe_save()
        print(f"Safe save test: {'✅ SUCCESS' if safe_save_success else '❌ FAILED'}")
    
    if args.create_job:
        # Need to import sys for create_test_qa_job
        import sys
        job_success = create_test_qa_job()
        print(f"Create job test: {'✅ SUCCESS' if job_success else '❌ FAILED'}")