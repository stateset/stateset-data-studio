#!/usr/bin/env python3
"""
Comprehensive test script for StateSet Data Studio API endpoints
"""
import os
import sys
import json
import time
import logging
import requests
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('api_tests.log')
    ]
)
logger = logging.getLogger("api-tests")

# API settings
API_URL = "http://localhost:8000"

def get_projects():
    """Get list of projects"""
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
        "name": f"Test Project {datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "description": "Automatically created for API testing",
    }
    
    response = requests.post(f"{API_URL}/projects", json=project_data)
    if response.status_code == 200:
        logger.info(f"Created test project: {response.json()}")
        return [response.json()]
    else:
        logger.error(f"Failed to create project: {response.status_code} {response.text}")
        return []

def create_test_file():
    """Create a test file for QA generation"""
    # Define test content
    test_content = """
    # Synthetic Data Generation Guide
    
    Synthetic data is artificially generated information that mimics real-world data without containing any actual sensitive information. This type of data is increasingly important for developing and testing machine learning models.
    
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
    """
    
    # Ensure directory exists
    os.makedirs("data/txt", exist_ok=True)
    
    # Create timestamp for unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = f"data/txt/test_ingest_{timestamp}.txt"
    
    # Write file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(test_content)
    
    logger.info(f"Created test file at: {file_path}")
    return file_path

def wait_for_job(job_id, timeout=180):
    """Wait for job to complete with a timeout in seconds"""
    start_time = time.time()
    interval = 2  # seconds between checks

    logger.info(f"Waiting for job {job_id} to complete...")
    
    while time.time() - start_time < timeout:
        # Get job status
        response = requests.get(f"{API_URL}/jobs/{job_id}")
        
        if response.status_code == 200:
            job = response.json()
            status = job.get('status')
            logger.info(f"Job status: {status}")
            
            if status in ['completed', 'warning']:  # Treat warning as success for tests
                logger.info(f"Job completed: {job}")
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

def test_ingest():
    """Test the ingest endpoint"""
    logger.info("=== TESTING INGEST ENDPOINT ===")
    
    # Get projects
    projects = get_projects()
    if not projects:
        logger.error("No projects found, cannot continue")
        return False
    
    # Use the first project
    project = projects[0]
    project_id = project['id']
    logger.info(f"Using project: {project['name']} ({project_id})")
    
    # Create test file
    test_file = create_test_file()
    
    # Prepare form data
    files = {'file': open(test_file, 'rb')}
    data = {'project_id': project_id}
    
    # Send request
    logger.info(f"Sending ingest request with file: {test_file}")
    response = requests.post(
        f"{API_URL}/jobs/ingest",
        files=files,
        data=data
    )
    
    if response.status_code in [200, 202]:  # Handle both OK and Accepted status codes
        job = response.json()
        logger.info(f"Ingest job created: {job}")
        
        # Wait for job to complete
        completed_job = wait_for_job(job['id'])
        if completed_job:
            logger.info(f"Ingest job completed successfully. Output file: {completed_job.get('output_file')}")
            return True, completed_job
        else:
            logger.error("Ingest job failed or timed out")
            return False, None
    else:
        logger.error(f"Failed to create ingest job: {response.status_code} {response.text}")
        return False, None

def test_create(project_id, input_file):
    """Test the create endpoint"""
    logger.info("=== TESTING CREATE ENDPOINT ===")
    
    # Prepare form data
    data = {
        'project_id': project_id,
        'input_file': input_file,
        'qa_type': 'qa',
        'num_pairs': 3  # Small number for testing
    }
    
    # Send request
    logger.info(f"Sending create request with input file: {input_file}")
    response = requests.post(
        f"{API_URL}/jobs/create",
        data=data
    )
    
    if response.status_code in [200, 202]:  # Handle both OK and Accepted status codes
        job = response.json()
        logger.info(f"QA job created: {job}")
        
        # Wait for job to complete
        completed_job = wait_for_job(job['id'], timeout=120)  # Allow more time for generation
        if completed_job:
            logger.info(f"QA job completed successfully. Output file: {completed_job.get('output_file')}")
            return True, completed_job
        else:
            logger.error("QA job failed or timed out")
            return False, None
    else:
        logger.error(f"Failed to create QA job: {response.status_code} {response.text}")
        return False, None

def test_curate(project_id, input_file):
    """Test the curate endpoint"""
    logger.info("=== TESTING CURATE ENDPOINT ===")
    
    # Prepare form data
    data = {
        'project_id': project_id,
        'input_file': input_file,
        'threshold': 5.0  # Use lower threshold for testing
    }
    
    # Send request
    logger.info(f"Sending curate request with input file: {input_file}")
    response = requests.post(
        f"{API_URL}/jobs/curate",
        data=data
    )
    
    if response.status_code in [200, 202]:  # Handle both OK and Accepted status codes
        job = response.json()
        logger.info(f"Curate job created: {job}")
        
        # Wait for job to complete
        completed_job = wait_for_job(job['id'], timeout=120)  # Allow more time for curation
        if completed_job:
            logger.info(f"Curate job completed successfully. Output file: {completed_job.get('output_file')}")
            return True, completed_job
        else:
            logger.error("Curate job failed or timed out")
            return False, None
    else:
        logger.error(f"Failed to create curate job: {response.status_code} {response.text}")
        return False, None

def test_save(project_id, input_file):
    """Test the save-as endpoint"""
    logger.info("=== TESTING SAVE-AS ENDPOINT ===")
    
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
    
    if response.status_code in [200, 202]:  # Handle both OK and Accepted status codes
        job = response.json()
        logger.info(f"Save job created: {job}")
        
        # Wait for job to complete
        completed_job = wait_for_job(job['id'])
        if completed_job:
            logger.info(f"Save job completed successfully. Output file: {completed_job.get('output_file')}")
            return True, completed_job
        else:
            logger.error("Save job failed or timed out")
            return False, None
    else:
        logger.error(f"Failed to create save job: {response.status_code} {response.text}")
        return False, None

def test_save_auto(project_id):
    """Test the save-as/auto endpoint"""
    logger.info("=== TESTING SAVE-AS/AUTO ENDPOINT ===")
    
    # Prepare form data
    data = {
        'project_id': project_id,
        'job_type': 'curate',  # Look for the latest curate job
        'format': 'jsonl',
        'storage_type': 'local'
    }
    
    # Send request
    logger.info(f"Sending save-as/auto request")
    response = requests.post(
        f"{API_URL}/jobs/save-as/auto",
        data=data
    )
    
    if response.status_code in [200, 202]:  # Handle both OK and Accepted status codes
        job = response.json()
        logger.info(f"Auto-save job created: {job}")
        
        # Wait for job to complete
        completed_job = wait_for_job(job['id'])
        if completed_job:
            logger.info(f"Auto-save job completed successfully. Output file: {completed_job.get('output_file')}")
            return True, completed_job
        else:
            logger.error("Auto-save job failed or timed out")
            return False, None
    else:
        logger.error(f"Failed to create auto-save job: {response.status_code} {response.text}")
        return False, None

def main():
    """Run the complete API test suite"""
    logger.info("Starting StateSet Data Studio API tests")
    
    # Get argument for which test to run
    import argparse
    parser = argparse.ArgumentParser(description='Run API tests for StateSet Data Studio')
    parser.add_argument('test', nargs='?', default='all', 
                        choices=['all', 'ingest', 'create', 'curate', 'save'],
                        help='Test to run (default: all)')
    args = parser.parse_args()
    
    # Initialize variables
    ingest_success = create_success = curate_success = save_success = auto_save_success = False
    ingest_job = create_job = curate_job = save_job = auto_save_job = None
    
    # Get a project ID to use for all tests
    projects = get_projects()
    if not projects:
        logger.error("No projects found, cannot continue")
        return False
    
    project_id = projects[0]['id']
    logger.info(f"Using project: {projects[0]['name']} ({project_id})")
    
    # Create a test file that can be used for all tests
    test_file = create_test_file()
    
    # Run the specified test(s)
    if args.test in ['all', 'ingest']:
        # Step 1: Ingest
        ingest_success, ingest_job = test_ingest()
        if not ingest_success:
            logger.error("Ingest test failed.")
            if args.test == 'ingest':
                return False
        elif args.test != 'all':
            return ingest_success
    
    input_file = ingest_job['output_file'] if ingest_job else None
    
    if args.test in ['all', 'create'] and input_file:
        # Step 2: Create
        create_success, create_job = test_create(project_id, input_file)
        if not create_success:
            logger.error("Create test failed.")
            if args.test == 'create':
                return False
        elif args.test != 'all':
            return create_success
    
    input_file = create_job['output_file'] if create_job else input_file
    
    if args.test in ['all', 'curate'] and input_file:
        # Step 3: Curate
        curate_success, curate_job = test_curate(project_id, input_file)
        if not curate_success:
            logger.error("Curate test failed.")
            if args.test == 'curate':
                return False
        elif args.test != 'all':
            return curate_success
    
    input_file = curate_job['output_file'] if curate_job else input_file
    
    if args.test in ['all', 'save'] and input_file:
        # Step 4: Save
        save_success, save_job = test_save(project_id, input_file)
        if not save_success:
            logger.error("Save test failed.")
            if args.test == 'save':
                return False
        elif args.test != 'all':
            return save_success
        
        # Step 5: Auto-save (only if running all tests or save specifically)
        auto_save_success, auto_save_job = test_save_auto(project_id)
    
    # Calculate overall results based on which tests were run
    all_passed = True
    if args.test == 'all':
        all_passed = ingest_success and create_success and curate_success and save_success and auto_save_success
    
    if all_passed:
        logger.info("✅ All API tests passed successfully!")
    else:
        logger.info("❌ Some API tests failed. Check logs for details.")
    
    logger.info("Test Results:")
    logger.info(f"  Ingest: {'✅ Passed' if ingest_success else '❌ Failed'}")
    logger.info(f"  Create: {'✅ Passed' if create_success else '❌ Failed'}")
    logger.info(f"  Curate: {'✅ Passed' if curate_success else '❌ Failed'}")
    logger.info(f"  Save:   {'✅ Passed' if save_success else '❌ Failed'}")
    logger.info(f"  Auto-Save: {'✅ Passed' if auto_save_success else '❌ Failed'}")
    
    return all_passed

if __name__ == "__main__":
    print("Running StateSet Data Studio API tests...")
    success = main()
    sys.exit(0 if success else 1)