#\!/usr/bin/env python3
"""
Test script for the /jobs/curate endpoint
"""
import requests
import json
import os
import sys
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='curate_test.log',
    filemode='w'
)
logger = logging.getLogger("curate-test")

def main():
    # API URL
    api_url = "http://localhost:8000"
    
    # Get a project ID to use
    try:
        projects_response = requests.get(f"{api_url}/projects")
        projects = projects_response.json()
        
        if not projects:
            logger.error("No projects found. Please create a project first.")
            print("No projects found. Please create a project first.")
            return False
        
        project_id = projects[0]["id"]
        logger.info(f"Using project ID: {project_id}")
        print(f"Using project ID: {project_id}")
    except Exception as e:
        logger.error(f"Error getting projects: {str(e)}")
        print(f"Error getting projects: {str(e)}")
        return False
    
    # Find a QA file to curate
    try:
        # Find the newest QA file in data/generated
        qa_file = None
        qa_dir = "data/generated"
        
        if os.path.exists(qa_dir):
            json_files = [(os.path.join(qa_dir, f), os.path.getmtime(os.path.join(qa_dir, f)))
                          for f in os.listdir(qa_dir)
                          if os.path.isfile(os.path.join(qa_dir, f)) and f.endswith('.json')]
            
            if json_files:
                json_files.sort(key=lambda x: x[1], reverse=True)
                qa_file = json_files[0][0]
                logger.info(f"Using QA file: {qa_file}")
                print(f"Using QA file: {qa_file}")
        
        if not qa_file:
            logger.error("No QA files found. Please generate QA pairs first.")
            print("No QA files found. Please generate QA pairs first.")
            return False
    except Exception as e:
        logger.error(f"Error finding QA file: {str(e)}")
        print(f"Error finding QA file: {str(e)}")
        return False
    
    # Create curate job
    try:
        # Create the form data
        form_data = {
            "project_id": project_id,
            "input_file": qa_file,
            "threshold": 7.0
        }
        
        # Log the request details
        logger.info(f"Sending request to {api_url}/jobs/curate with data: {form_data}")
        print(f"Sending request to {api_url}/jobs/curate with data: {form_data}")
        
        # Make the request
        response = requests.post(f"{api_url}/jobs/curate", data=form_data)
        
        # Log the response
        if response.status_code == 200:
            result = response.json()
            logger.info(f"Curate job created: {json.dumps(result, indent=2)}")
            print(f"Curate job created: {result['id']}")
            
            # Monitor job status
            job_id = result["id"]
            max_attempts = 60  # 5 minutes (5 sec * 60)
            attempt = 0
            
            print("Monitoring job status...")
            while attempt < max_attempts:
                attempt += 1
                time.sleep(5)  # Check every 5 seconds
                
                try:
                    job_response = requests.get(f"{api_url}/jobs/{job_id}")
                    job = job_response.json()
                    
                    status = job.get("status")
                    print(f"Job status: {status} (attempt {attempt}/{max_attempts})")
                    
                    if status == "completed":
                        logger.info(f"Job completed successfully: {json.dumps(job, indent=2)}")
                        print(f"Job completed successfully\!")
                        print(f"Output file: {job.get('output_file')}")
                        return True
                    elif status == "failed":
                        logger.error(f"Job failed: {job.get('error')}")
                        print(f"Job failed: {job.get('error')}")
                        return False
                    elif status not in ["pending", "running"]:
                        logger.error(f"Unexpected job status: {status}")
                        print(f"Unexpected job status: {status}")
                        return False
                except Exception as e:
                    logger.error(f"Error checking job status: {str(e)}")
                    print(f"Error checking job status: {str(e)}")
            
            logger.error("Job monitoring timed out")
            print("Job monitoring timed out")
        else:
            logger.error(f"Error creating curate job: {response.status_code} {response.text}")
            print(f"Error creating curate job: {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        logger.error(f"Error creating curate job: {str(e)}")
        print(f"Error creating curate job: {str(e)}")
        return False
    
    return False

if __name__ == "__main__":
    print("Testing /jobs/curate endpoint...")
    if main():
        print("Test completed successfully\!")
        sys.exit(0)
    else:
        print("Test failed\!")
        sys.exit(1)
EOF < /dev/null
