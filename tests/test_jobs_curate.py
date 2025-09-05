#!/usr/bin/env python3
import requests
import json
import sys

API_URL = "http://localhost:8000"

# Get a project ID
try:
    print("Getting projects...")
    projects_response = requests.get(f"{API_URL}/projects")
    if projects_response.status_code != 200:
        print(f"Error getting projects: {projects_response.status_code}")
        print(projects_response.text)
        sys.exit(1)
    
    projects = projects_response.json()
    if not projects:
        print("No projects found. Please create a project first.")
        sys.exit(1)
    
    project_id = projects[0]["id"]
    print(f"Using project ID: {project_id}")
except Exception as e:
    print(f"Error getting projects: {str(e)}")
    sys.exit(1)

# Find jobs to get a valid input file
try:
    print("Getting existing jobs...")
    jobs_response = requests.get(f"{API_URL}/jobs?project_id={project_id}")
    
    if jobs_response.status_code != 200:
        print(f"Error getting jobs: {jobs_response.status_code}")
        print(jobs_response.text)
        sys.exit(1)
    
    jobs = jobs_response.json()
    
    # Find the most recent completed create job
    create_jobs = [job for job in jobs if job["job_type"] == "create" and job["status"] == "completed"]
    
    if not create_jobs:
        print("No completed create jobs found. Please generate QA pairs first.")
        sys.exit(1)
    
    # Sort by created_at (most recent first)
    create_jobs.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    input_file = create_jobs[0]["output_file"]
    print(f"Using input file: {input_file}")
except Exception as e:
    print(f"Error finding input file: {str(e)}")
    sys.exit(1)

# Test curate endpoint
try:
    print("\nTesting /jobs/curate endpoint...")
    form_data = {
        "project_id": project_id,
        "input_file": input_file,
        "threshold": 7.0
    }
    
    print(f"Sending request to {API_URL}/jobs/curate with data: {form_data}")
    
    # Make the request
    response = requests.post(f"{API_URL}/jobs/curate", data=form_data)
    
    print(f"Response status code: {response.status_code}")
    print(f"Response body: {response.text}")
    
    if response.status_code == 200:
        print("Curate endpoint is working!")
        sys.exit(0)
    else:
        print("Curate endpoint returned an error")
        sys.exit(1)
except Exception as e:
    print(f"Error testing curate endpoint: {str(e)}")
    sys.exit(1)