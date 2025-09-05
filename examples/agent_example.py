#!/usr/bin/env python3
"""
Example script demonstrating how an AI agent might use the StateSet Data Studio MCP server
"""

import os
import json
import time
import requests
import argparse
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("agent-example")

class SyntheticDataAgent:
    """Example agent for interacting with the StateSet Data Studio MCP server"""
    
    def __init__(self, mcp_url="http://localhost:8000"):
        self.mcp_url = mcp_url
        self.tools = self._get_tools()
        
    def _get_tools(self):
        """Get tool descriptions from the MCP server"""
        response = requests.get(f"{self.mcp_url}/mcp/tools/description")
        if response.status_code == 200:
            return response.json()["tools"]
        else:
            logger.error(f"Failed to get tool descriptions: {response.status_code} {response.text}")
            return []
    
    def execute_tool(self, tool_name, params):
        """Execute a tool on the MCP server"""
        url = f"{self.mcp_url}/mcp/tools/execute/{tool_name}"
        response = requests.post(url, json=params)
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Tool execution failed: {response.status_code} {response.text}")
            return {"status": "error", "message": f"Status code: {response.status_code}"}
    
    def wait_for_job(self, job_id, max_wait_time=300, poll_interval=5):
        """Wait for a job to complete, polling at regular intervals"""
        start_time = time.time()
        
        while True:
            elapsed = time.time() - start_time
            if elapsed > max_wait_time:
                logger.warning(f"Exceeded maximum wait time of {max_wait_time}s for job {job_id}")
                return {"status": "timeout", "job_id": job_id}
            
            job_status = self.execute_tool("synthetic_data_job_status", {"job_id": job_id})
            
            if job_status["status"] == "completed":
                logger.info(f"Job {job_id} completed successfully")
                return job_status
            
            if job_status["status"] == "failed":
                logger.error(f"Job {job_id} failed: {job_status.get('details', {}).get('error', 'Unknown error')}")
                return job_status
            
            logger.info(f"Job {job_id} is {job_status['status']}. Waiting {poll_interval}s...")
            time.sleep(poll_interval)

def run_example_workflow():
    """Run a complete example workflow"""
    agent = SyntheticDataAgent()
    
    # Create a project
    logger.info("Creating a project...")
    project_response = agent.execute_tool("synthetic_data_create_project", {
        "name": "Example Agent Project",
        "description": "A demonstration of using the MCP server from an agent"
    })
    
    if project_response["status"] != "success":
        logger.error(f"Failed to create project: {project_response}")
        return
    
    project_id = project_response["project_id"]
    logger.info(f"Project created with ID: {project_id}")
    
    # Ingest data
    sample_text = """
    The StateSet Data Studio is a powerful tool for creating synthetic question-answer pairs.
    It supports various input formats like text, PDF, DOCX, and even YouTube videos.
    The system processes the input, generates high-quality QA pairs, and allows for curation
    and export in different formats. It's designed to help create training data for
    language models and other AI applications.
    """
    
    logger.info("Ingesting sample text...")
    ingest_response = agent.execute_tool("synthetic_data_ingest", {
        "project_id": project_id,
        "source_type": "text",
        "content": sample_text
    })
    
    if ingest_response["status"] != "pending":
        logger.error(f"Failed to start ingestion: {ingest_response}")
        return
    
    ingest_job_id = ingest_response["job_id"]
    logger.info(f"Ingestion job started with ID: {ingest_job_id}")
    
    # Wait for ingestion to complete
    ingest_status = agent.wait_for_job(ingest_job_id)
    if ingest_status["status"] != "completed":
        logger.error(f"Ingestion job failed: {ingest_status}")
        return
    
    # Generate QA pairs
    logger.info("Generating QA pairs...")
    create_response = agent.execute_tool("synthetic_data_create_qa", {
        "project_id": project_id,
        "ingest_job_id": ingest_job_id,
        "num_pairs": 5,
        "temperature": 0.7
    })
    
    if create_response["status"] != "pending":
        logger.error(f"Failed to start QA generation: {create_response}")
        return
    
    create_job_id = create_response["job_id"]
    logger.info(f"QA generation job started with ID: {create_job_id}")
    
    # Wait for QA generation to complete
    create_status = agent.wait_for_job(create_job_id)
    if create_status["status"] != "completed":
        logger.error(f"QA generation job failed: {create_status}")
        return
    
    # Curate QA pairs
    logger.info("Curating QA pairs...")
    curate_response = agent.execute_tool("synthetic_data_curate", {
        "project_id": project_id,
        "create_job_id": create_job_id,
        "quality_threshold": 0.6
    })
    
    if curate_response["status"] != "pending":
        logger.error(f"Failed to start curation: {curate_response}")
        return
    
    curate_job_id = curate_response["job_id"]
    logger.info(f"Curation job started with ID: {curate_job_id}")
    
    # Wait for curation to complete
    curate_status = agent.wait_for_job(curate_job_id)
    if curate_status["status"] != "completed":
        logger.error(f"Curation job failed: {curate_status}")
        return
    
    # Export data
    logger.info("Exporting data...")
    export_response = agent.execute_tool("synthetic_data_export", {
        "project_id": project_id,
        "curate_job_id": curate_job_id,
        "format": "jsonl",
        "include_metadata": True
    })
    
    if export_response["status"] != "pending":
        logger.error(f"Failed to start export: {export_response}")
        return
    
    export_job_id = export_response["job_id"]
    logger.info(f"Export job started with ID: {export_job_id}")
    
    # Wait for export to complete
    export_status = agent.wait_for_job(export_job_id)
    if export_status["status"] != "completed":
        logger.error(f"Export job failed: {export_status}")
        return
    
    # Get the result
    logger.info("Getting the result...")
    result_response = agent.execute_tool("synthetic_data_job_result", {
        "job_id": export_job_id
    })
    
    if result_response["status"] != "success":
        logger.error(f"Failed to get result: {result_response}")
        return
    
    # Display the result
    logger.info("Workflow completed successfully!")
    logger.info(f"Result path: {export_status.get('details', {}).get('result_path')}")
    
    if "result" in result_response:
        logger.info(f"Number of QA pairs: {len(result_response['result'])}")
        logger.info("Sample QA pair:")
        logger.info(json.dumps(result_response["result"][0] if result_response["result"] else {}, indent=2))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="StateSet Data Studio Agent Example")
    parser.add_argument("--mcp-url", default="http://localhost:8000", help="URL of the MCP server")
    args = parser.parse_args()
    
    logger.info(f"Using MCP server at {args.mcp_url}")
    
    # Create the agent with the specified MCP URL
    run_example_workflow()