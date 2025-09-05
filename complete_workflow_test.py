#!/usr/bin/env python3
"""
Complete workflow test for StateSet Data Studio API
Tests ingest → create → curate → save with fully new files
"""
import os
import sys
import json
import time
import logging
import requests
import uuid
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('workflow_test.log')
    ]
)
logger = logging.getLogger("workflow-test")

# API settings
API_URL = "http://localhost:8000"

def create_test_file():
    """Create a unique test file for this run"""
    # Define test content
    test_content = """
    # Synthetic Data Generation Guide
    
    Synthetic data is artificially generated information that mimics real-world data without 
    containing any actual sensitive information. This type of data is increasingly important 
    for developing and testing machine learning models.
    
    ## Benefits of Synthetic Data
    
    - Privacy preservation: No real user data is exposed
    - Customization: Can be generated for specific edge cases
    - Availability: Can create large volumes of data when real data is scarce
    - Cost-effectiveness: Often cheaper than collecting real data
    
    ## Methods for Creating Synthetic Data
    
    1. **Statistical approaches**: Generate data that matches statistical properties of original data
    2. **Deep learning methods**: Use models like GANs or VAEs to create realistic synthetic samples
    3. **Rule-based systems**: Define explicit rules to generate structured data
    4. **Hybrid approaches**: Combine multiple methods for better results
    
    ## Quality Assessment
    
    When evaluating synthetic data, consider these metrics:
    - Fidelity: How closely it resembles real data
    - Utility: How useful it is for the intended purpose
    - Privacy: Ensuring it doesn't leak information from the original data
    
    ## Common Applications
    
    - Software testing
    - Model training when real data is limited
    - Augmenting existing datasets
    - Sharing "realistic" data without privacy concerns
    
    This is a unique test document (ID: {unique_id}) created at {timestamp}.
    """
    
    # Add unique identifiers to track the file through the workflow
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    test_content = test_content.format(unique_id=unique_id, timestamp=timestamp)
    
    # Ensure directory exists
    os.makedirs("data/txt", exist_ok=True)
    
    # Create timestamp for unique filename
    file_path = f"data/txt/workflow_test_{timestamp}.txt"
    
    # Write file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(test_content)
    
    logger.info(f"Created test file at: {file_path}")
    logger.info(f"Test file unique ID: {unique_id}")
    return file_path, unique_id

def get_projects():
    """Get list of projects or create one if none exist"""
    response = requests.get(f"{API_URL}/projects")
    if response.status_code == 200:
        projects = response.json()
        if projects:
            logger.info(f"Found {len(projects)} projects")
            return projects
        else:
            logger.info("No existing projects found. Creating one...")
            return create_project()
    else:
        logger.error(f"Failed to get projects: {response.status_code} {response.text}")
        return []

def create_project():
    """Create a test project"""
    project_data = {
        "name": f"Workflow Test Project {datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "description": "Created for complete workflow testing",
    }
    
    response = requests.post(f"{API_URL}/projects", json=project_data)
    if response.status_code == 200:
        logger.info(f"Created test project: {response.json()}")
        return [response.json()]
    else:
        logger.error(f"Failed to create project: {response.status_code} {response.text}")
        return []

def wait_for_job(job_id, timeout=180):
    """Wait for job to complete with a timeout in seconds"""
    start_time = time.time()
    interval = 3  # seconds between checks
    
    logger.info(f"Waiting for job {job_id} to complete (timeout: {timeout}s)...")
    
    while time.time() - start_time < timeout:
        # Get job status
        response = requests.get(f"{API_URL}/jobs/{job_id}")
        
        if response.status_code == 200:
            job = response.json()
            status = job.get('status')
            logger.info(f"Job status: {status}")
            
            if status in ['completed', 'warning']:
                # For our test, we'll accept warning as complete
                logger.info(f"Job completed with status '{status}': {job}")
                return job
            elif status == 'failed':
                logger.error(f"Job failed: {job}")
                return None
        else:
            logger.error(f"Failed to get job status: {response.text}")
        
        # Wait before retrying
        time.sleep(interval)
    
    logger.error(f"Job timed out after {timeout} seconds")
    return None

def test_ingest(project_id, file_path):
    """Test ingest API endpoint"""
    logger.info("\n=== STEP 1: TESTING INGEST API ===")
    
    # Prepare form data
    files = {'file': open(file_path, 'rb')}
    data = {'project_id': project_id}
    
    # Send request
    logger.info(f"Sending ingest request with file: {file_path}")
    response = requests.post(
        f"{API_URL}/jobs/ingest",
        files=files,
        data=data
    )
    
    if response.status_code in [200, 202]:
        job = response.json()
        logger.info(f"Ingest job created: ID={job['id']}")
        
        # Wait for job to complete
        completed_job = wait_for_job(job['id'])
        if completed_job:
            logger.info(f"✅ INGEST API test passed!")
            
            # Check for output file in the response
            output_file = completed_job.get('output_file')
            if not output_file:
                # If no output file in response, we need to look for it
                logger.info("No output file in response, looking for ingest output...")
                
                # Check data/output directory for the most recently created file
                output_dir = Path("data/output")
                if output_dir.exists():
                    # Get all txt files in output dir
                    txt_files = [(f, os.path.getmtime(f)) for f in output_dir.glob("*.txt")]
                    if txt_files:
                        # Sort by modification time (newest first)
                        txt_files.sort(key=lambda x: x[1], reverse=True)
                        output_file = str(txt_files[0][0])
                        logger.info(f"Found potential output file: {output_file}")
                    else:
                        logger.warning("No txt files found in output directory")
                else:
                    logger.warning("Output directory does not exist")
            
            return True, completed_job, output_file
        else:
            logger.error("❌ INGEST API test failed: Job did not complete")
            return False, None, None
    else:
        logger.error(f"❌ INGEST API test failed: {response.status_code} - {response.text}")
        return False, None, None

def test_create(project_id, input_file):
    """Test create API endpoint"""
    logger.info("\n=== STEP 2: TESTING CREATE API ===")
    
    # Prepare form data
    data = {
        'project_id': project_id,
        'input_file': input_file,
        'qa_type': 'qa',
        'num_pairs': 3  # Small number for faster testing
    }
    
    # Send request
    logger.info(f"Sending create request with input file: {input_file}")
    response = requests.post(
        f"{API_URL}/jobs/create",
        data=data
    )
    
    if response.status_code in [200, 202]:
        job = response.json()
        logger.info(f"Create job created: ID={job['id']}")
        
        # Wait for job to complete
        completed_job = wait_for_job(job['id'], timeout=300)  # Allow more time for generation
        if completed_job:
            logger.info(f"✅ CREATE API test passed!")
            
            # Get output file path
            output_file = completed_job.get('output_file')
            if output_file:
                # Verify file exists
                if os.path.exists(output_file):
                    logger.info(f"Output file exists: {output_file}")
                else:
                    logger.warning(f"Output file does not exist: {output_file}")
                    
                    # Look for the file in data/generated
                    if output_file.startswith('/'):
                        basename = os.path.basename(output_file)
                    else:
                        basename = os.path.basename(output_file)
                        
                    potential_paths = [
                        Path(f"data/generated/{basename}"),
                        Path(f"backend/data/generated/{basename}")
                    ]
                    
                    for path in potential_paths:
                        if path.exists():
                            output_file = str(path)
                            logger.info(f"Found file at: {output_file}")
                            break
            
            return True, completed_job, output_file
        else:
            logger.error("❌ CREATE API test failed: Job did not complete")
            return False, None, None
    else:
        logger.error(f"❌ CREATE API test failed: {response.status_code} - {response.text}")
        return False, None, None

def test_curate(project_id, input_file):
    """Test curate API endpoint"""
    logger.info("\n=== STEP 3: TESTING CURATE API ===")
    
    # Prepare form data
    data = {
        'project_id': project_id,
        'input_file': input_file,
        'threshold': 5.0  # Lower threshold for testing
    }
    
    # Send request
    logger.info(f"Sending curate request with input file: {input_file}")
    response = requests.post(
        f"{API_URL}/jobs/curate",
        data=data
    )
    
    if response.status_code in [200, 202]:
        job = response.json()
        logger.info(f"Curate job created: ID={job['id']}")
        
        # Wait for job to complete
        completed_job = wait_for_job(job['id'], timeout=300)  # Allow more time for curation
        if completed_job:
            logger.info(f"✅ CURATE API test passed!")
            
            # Get output file path
            output_file = completed_job.get('output_file')
            if output_file:
                # Verify file exists
                if os.path.exists(output_file):
                    logger.info(f"Output file exists: {output_file}")
                else:
                    logger.warning(f"Output file does not exist: {output_file}")
                    
                    # Look for the file in data/cleaned
                    basename = os.path.basename(output_file)
                    potential_paths = [
                        Path(f"data/cleaned/{basename}"),
                        Path(f"backend/data/cleaned/{basename}")
                    ]
                    
                    for path in potential_paths:
                        if path.exists():
                            output_file = str(path)
                            logger.info(f"Found file at: {output_file}")
                            break
            
            return True, completed_job, output_file
        else:
            logger.error("❌ CURATE API test failed: Job did not complete")
            return False, None, None
    else:
        logger.error(f"❌ CURATE API test failed: {response.status_code} - {response.text}")
        return False, None, None

def test_save(project_id, input_file):
    """Test save-as API endpoint"""
    logger.info("\n=== STEP 4: TESTING SAVE-AS API ===")
    
    # Prepare form data
    data = {
        'project_id': project_id,
        'input_file': input_file,
        'format': 'jsonl',
        'storage_type': 'local'
    }
    
    # Send request
    logger.info(f"Sending save-as request with input file: {input_file}")
    response = requests.post(
        f"{API_URL}/jobs/save-as",
        data=data
    )
    
    if response.status_code in [200, 202]:
        job = response.json()
        logger.info(f"Save job created: ID={job['id']}")
        
        # Wait for job to complete
        completed_job = wait_for_job(job['id'])
        if completed_job:
            logger.info(f"✅ SAVE-AS API test passed!")
            
            # Get output file path
            output_file = completed_job.get('output_file')
            if output_file:
                # Verify file exists
                if os.path.exists(output_file):
                    logger.info(f"Final output file exists: {output_file}")
                    # Verify file has content
                    try:
                        with open(output_file, 'r') as f:
                            content = f.read().strip()
                            if content:
                                logger.info(f"Final file has content ({len(content)} bytes)")
                                # Try to parse it if it's JSON
                                if output_file.endswith('.jsonl'):
                                    with open(output_file, 'r') as f:
                                        for idx, line in enumerate(f):
                                            if line.strip():
                                                record = json.loads(line)
                                                logger.info(f"Record {idx+1}: {list(record.keys())}")
                            else:
                                logger.warning("Final file is empty")
                    except Exception as e:
                        logger.error(f"Error reading final file: {str(e)}")
                else:
                    logger.warning(f"Final output file does not exist: {output_file}")
            
            return True, completed_job, output_file
        else:
            logger.error("❌ SAVE-AS API test failed: Job did not complete")
            return False, None, None
    else:
        logger.error(f"❌ SAVE-AS API test failed: {response.status_code} - {response.text}")
        return False, None, None

def test_full_workflow():
    """Test the complete workflow from ingest to save"""
    # Get start time
    start_time = time.time()
    logger.info(f"=== STARTING COMPLETE WORKFLOW TEST AT {datetime.now()} ===")
    
    # Create test file
    test_file, unique_id = create_test_file()
    
    # Get projects
    projects = get_projects()
    if not projects:
        logger.error("No projects found and couldn't create one")
        return False
    
    # Use the first project
    project = projects[0]
    project_id = project['id']
    logger.info(f"Using project: {project['name']} ({project_id})")
    
    # Step 1: Test ingest
    ingest_success, ingest_job, ingest_output = test_ingest(project_id, test_file)
    if not ingest_success or not ingest_output:
        logger.error("Ingest step failed, cannot continue workflow")
        return False
    
    # Step 2: Test create
    create_success, create_job, create_output = test_create(project_id, ingest_output)
    if not create_success or not create_output:
        logger.error("Create step failed, cannot continue workflow")
        return False
    
    # Step 3: Test curate
    curate_success, curate_job, curate_output = test_curate(project_id, create_output)
    if not curate_success or not curate_output:
        logger.error("Curate step failed, cannot continue workflow")
        return False
    
    # Step 4: Test save
    save_success, save_job, save_output = test_save(project_id, curate_output)
    
    # Calculate elapsed time
    elapsed_time = time.time() - start_time
    logger.info(f"=== WORKFLOW TEST COMPLETED IN {elapsed_time:.2f} SECONDS ===")
    
    # Results summary
    logger.info("\n=== WORKFLOW TEST RESULTS SUMMARY ===")
    logger.info(f"Ingest:  {'✅ Passed' if ingest_success else '❌ Failed'}")
    logger.info(f"Create:  {'✅ Passed' if create_success else '❌ Failed'}")
    logger.info(f"Curate:  {'✅ Passed' if curate_success else '❌ Failed'}")
    logger.info(f"Save:    {'✅ Passed' if save_success else '❌ Failed'}")
    
    # Final status
    workflow_success = ingest_success and create_success and curate_success and save_success
    logger.info(f"Overall: {'✅ COMPLETE WORKFLOW PASSED!' if workflow_success else '❌ WORKFLOW FAILED'}")
    
    return workflow_success

if __name__ == "__main__":
    print("Running complete workflow test...")
    success = test_full_workflow()
    sys.exit(0 if success else 1)