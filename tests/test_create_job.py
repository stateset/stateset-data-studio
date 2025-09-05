#!/usr/bin/env python3
import requests
import json
import os
import logging
import time
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('create_job_test.log')
    ]
)
logger = logging.getLogger("create-job-test")

# API settings
API_URL = "http://localhost:8000"

def get_projects():
    """Get list of projects"""
    response = requests.get(f"{API_URL}/projects")
    return response.json() if response.status_code == 200 else []

def create_test_file():
    """Create a test file for QA generation"""
    # Define test content
    test_content = """
    StateSet Data Studio is a powerful tool for generating synthetic data.
    
    Key features:
    - Import data from various sources
    - Generate Q&A pairs using AI
    - Curate data with quality controls
    - Export in different formats
    
    The system has a frontend built with React and a backend using FastAPI.
    The synthetic data generation uses LLMs to create high-quality training data.
    """
    
    # Ensure directory exists
    os.makedirs("data/txt", exist_ok=True)
    
    # Create timestamp for unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = f"data/txt/test_create_{timestamp}.txt"
    
    # Write file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(test_content)
    
    logger.info(f"Created test file at: {file_path}")
    return file_path

def create_ingest_job(project_id, file_path):
    """Create an ingest job"""
    # Prepare form data
    files = {'file': open(file_path, 'rb')}
    data = {'project_id': project_id}
    
    # Send request
    response = requests.post(
        f"{API_URL}/jobs/ingest",
        files=files,
        data=data
    )
    
    if response.status_code == 200:
        logger.info(f"Ingest job created: {response.json()}")
        return response.json()
    else:
        logger.error(f"Failed to create ingest job: {response.text}")
        return None

def wait_for_job(job_id):
    """Wait for job to complete"""
    max_retries = 10
    retry_count = 0
    
    while retry_count < max_retries:
        # Get job status
        response = requests.get(f"{API_URL}/jobs/{job_id}")
        
        if response.status_code == 200:
            job = response.json()
            logger.info(f"Job status: {job['status']}")
            
            if job['status'] == 'completed':
                logger.info(f"Job completed: {job}")
                return job
            elif job['status'] == 'failed':
                logger.error(f"Job failed: {job}")
                return None
        else:
            logger.error(f"Failed to get job status: {response.text}")
        
        # Wait before retrying
        retry_count += 1
        logger.info(f"Waiting for job completion (attempt {retry_count}/{max_retries})...")
        time.sleep(2)
    
    logger.error("Job did not complete in the expected time")
    return None

def create_qa_job(project_id, input_file):
    """Create a QA generation job"""
    # Prepare form data
    data = {
        'project_id': project_id,
        'input_file': input_file,
        'qa_type': 'qa',
        'num_pairs': 3  # Small number for testing
    }
    
    # Send request
    response = requests.post(
        f"{API_URL}/jobs/create",
        data=data
    )
    
    if response.status_code == 200:
        logger.info(f"QA job created: {response.json()}")
        return response.json()
    else:
        logger.error(f"Failed to create QA job: {response.text}")
        return None

def check_qa_file(output_file):
    """Check if the QA file exists and has content"""
    # Check multiple potential locations
    potential_paths = [
        output_file,
        f"backend/{output_file}",
        os.path.join("data/generated", os.path.basename(output_file)),
        os.path.join("backend/data/generated", os.path.basename(output_file))
    ]
    
    for path in potential_paths:
        if os.path.exists(path):
            logger.info(f"Found QA file at: {path}")
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if "qa_pairs" in data:
                    logger.info(f"QA file contains {len(data['qa_pairs'])} pairs")
                    return True, path
                else:
                    logger.warning(f"QA file does not contain qa_pairs key")
            except Exception as e:
                logger.error(f"Error reading QA file: {str(e)}")
    
    logger.error(f"QA file not found at any of these paths: {', '.join(potential_paths)}")
    return False, None

def run_test():
    """Run the complete test"""
    logger.info("Starting QA generation test")
    
    # Get projects
    projects = get_projects()
    if not projects:
        logger.error("No projects found")
        return False
    
    # Use the first project
    project = projects[0]
    project_id = project['id']
    logger.info(f"Using project: {project['name']} ({project_id})")
    
    # Create test file
    test_file = create_test_file()
    
    # Create ingest job
    ingest_job = create_ingest_job(project_id, test_file)
    if not ingest_job:
        return False
    
    # Wait for ingest job to complete
    completed_ingest_job = wait_for_job(ingest_job['id'])
    if not completed_ingest_job:
        return False
    
    # Get the output file from the ingest job
    output_file = completed_ingest_job['output_file']
    logger.info(f"Ingest produced: {output_file}")
    
    # Create QA job
    qa_job = create_qa_job(project_id, output_file)
    if not qa_job:
        return False
    
    # Wait for QA job to complete
    completed_qa_job = wait_for_job(qa_job['id'])
    if not completed_qa_job:
        return False
    
    # Check if output file exists
    qa_output_file = completed_qa_job['output_file']
    logger.info(f"QA job produced: {qa_output_file}")
    
    # Check if file exists and has content
    success, file_path = check_qa_file(qa_output_file)
    
    if success:
        logger.info("QA generation test completed successfully!")
        logger.info(f"QA file created at: {file_path}")
        return True
    else:
        logger.error("QA generation test failed: QA file not created properly")
        return False

if __name__ == "__main__":
    success = run_test()
    if success:
        print("✅ Test completed successfully!")
    else:
        print("❌ Test failed!")