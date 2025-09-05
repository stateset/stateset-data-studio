#!/usr/bin/env python3
"""
MCP Server for StateSet Data Studio - AI Agent Integration
This server exposes the StateSet Data Studio functionality for AI Agents.
"""

import os
import json
import uuid
import time
import base64
import logging
from typing import Dict, List, Optional, Union, Any
from fastapi import FastAPI, Request, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Import local modules
from backend.app import app as backend_app
from synthetic_data_kit.utils.config import load_config
from synthetic_data_kit.models.llm_client import LLMClient
from synthetic_data_kit.parsers.base_parser import get_parser_for_file
from synthetic_data_kit.generators.qa_generator import QAGenerator
from synthetic_data_kit.utils.format_converter import convert_format

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load configuration
config = load_config()

# Initialize FastAPI app
app = FastAPI(
    title="StateSet Data Studio MCP API",
    description="MCP API for StateSet Data Studio, allowing AI agents to work with synthetic data generation",
    version="1.0.0"
)

# CORS for the React dev-server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Merge routers instead of mounting
app.include_router(backend_app.router)

# MCP specific models
class MCPProjectRequest(BaseModel):
    name: str
    description: Optional[str] = None

class MCPIngestRequest(BaseModel):
    project_id: Optional[str] = None
    source_type: str = "text"  # text, url, youtube
    content: Optional[str] = None
    url: Optional[str] = None

class MCPCreateRequest(BaseModel):
    project_id: str
    ingest_job_id: Optional[str] = None
    num_pairs: Optional[int] = 10
    temperature: Optional[float] = 0.7
    advanced_options: Optional[Dict[str, Any]] = None

class MCPCurateRequest(BaseModel):
    project_id: str
    create_job_id: Optional[str] = None
    quality_threshold: Optional[float] = 0.7
    advanced_options: Optional[Dict[str, Any]] = None

class MCPExportRequest(BaseModel):
    project_id: str
    curate_job_id: Optional[str] = None
    format: str = "jsonl"  # jsonl, csv, alpaca, llama
    include_metadata: bool = True

# Running jobs and their status
job_status = {}

# Helper functions
def get_unique_id():
    return str(uuid.uuid4())

def update_job_status(job_id, status, details=None):
    job_status[job_id] = {
        "status": status,
        "updated_at": time.time(),
        "details": details or {}
    }

def save_text_to_file(text, file_path):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(text)
    return file_path

def get_output_path(job_id, suffix, ext="txt"):
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    return f"data/uploads/mcp_{job_id}_{timestamp}.{ext}"

# MCP endpoints for AI agents
@app.post("/mcp/projects/create")
async def mcp_create_project(request: MCPProjectRequest):
    """Create a new project for synthetic data generation"""
    project_id = get_unique_id()
    
    # Here we would normally create the project in the database
    # For now, we'll just return a success response with the project ID
    
    return {"status": "success", "project_id": project_id, "name": request.name}

@app.post("/mcp/data/ingest")
async def mcp_ingest_data(request: MCPIngestRequest, background_tasks: BackgroundTasks):
    """Ingest data from text, URL, or YouTube for processing"""
    job_id = get_unique_id()
    update_job_status(job_id, "pending")
    
    try:
        if request.source_type == "text" and request.content:
            # Save content to file
            file_path = get_output_path(job_id, "ingest")
            save_text_to_file(request.content, file_path)
            
            # Process the text file
            parser = get_parser_for_file(file_path)
            output_path = f"data/output/processed_{time.strftime('%Y%m%d_%H%M%S')}.txt"
            
            background_tasks.add_task(
                process_ingest_job, 
                job_id=job_id,
                file_path=file_path,
                output_path=output_path,
                project_id=request.project_id or "default"
            )
            
        elif request.source_type == "url" and request.url:
            # We would handle URL ingestion here
            # This would use the appropriate parser based on the URL
            update_job_status(job_id, "failed", {"error": "URL ingestion not implemented in MCP server"})
            raise HTTPException(status_code=501, detail="URL ingestion not implemented in MCP server")
            
        elif request.source_type == "youtube" and request.url:
            # We would handle YouTube ingestion here
            update_job_status(job_id, "failed", {"error": "YouTube ingestion not implemented in MCP server"})
            raise HTTPException(status_code=501, detail="YouTube ingestion not implemented in MCP server")
        
        else:
            update_job_status(job_id, "failed", {"error": "Invalid request parameters"})
            raise HTTPException(status_code=400, detail="Invalid request parameters")
        
        return {
            "status": "pending", 
            "job_id": job_id,
            "message": "Data ingestion started"
        }
        
    except Exception as e:
        update_job_status(job_id, "failed", {"error": str(e)})
        logger.exception(f"Error in data ingestion: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in data ingestion: {str(e)}")

@app.post("/mcp/data/create")
async def mcp_create_qa_pairs(request: MCPCreateRequest, background_tasks: BackgroundTasks):
    """Generate QA pairs from ingested data"""
    job_id = get_unique_id()
    update_job_status(job_id, "pending")
    
    try:
        # Determine the source data - either from the specified ingest job or the most recent one
        ingest_job_id = request.ingest_job_id
        
        if not ingest_job_id:
            # In a real implementation, we would query the database for the most recent ingest job
            # For now, we'll require the ingest_job_id
            update_job_status(job_id, "failed", {"error": "ingest_job_id is required"})
            raise HTTPException(status_code=400, detail="ingest_job_id is required")
        
        # Generate file paths
        # In a real implementation, we'd get the actual path from the database
        input_path = f"data/output/processed_{ingest_job_id}.txt"
        if not os.path.exists(input_path):
            # Fallback to a default path pattern
            potential_files = [f for f in os.listdir("data/output") if f.startswith("processed_")]
            if potential_files:
                input_path = os.path.join("data/output", sorted(potential_files)[-1])
            else:
                update_job_status(job_id, "failed", {"error": "No processed data found"})
                raise HTTPException(status_code=404, detail="No processed data found")
        
        output_path = f"data/generated/{get_unique_id()}_{time.strftime('%Y%m%d_%H%M%S')}_qa_pairs.json"
        
        # Start the creation job in the background
        background_tasks.add_task(
            process_create_job,
            job_id=job_id,
            input_path=input_path,
            output_path=output_path,
            project_id=request.project_id,
            num_pairs=request.num_pairs,
            temperature=request.temperature,
            advanced_options=request.advanced_options
        )
        
        return {
            "status": "pending",
            "job_id": job_id,
            "message": "QA pair generation started"
        }
        
    except Exception as e:
        update_job_status(job_id, "failed", {"error": str(e)})
        logger.exception(f"Error in QA pair generation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in QA pair generation: {str(e)}")

@app.post("/mcp/data/curate")
async def mcp_curate_qa_pairs(request: MCPCurateRequest, background_tasks: BackgroundTasks):
    """Curate and filter generated QA pairs based on quality"""
    job_id = get_unique_id()
    update_job_status(job_id, "pending")
    
    try:
        # Determine the source data
        create_job_id = request.create_job_id
        
        if not create_job_id:
            # In a real implementation, we would query the database for the most recent create job
            # For now, we'll require the create_job_id
            update_job_status(job_id, "failed", {"error": "create_job_id is required"})
            raise HTTPException(status_code=400, detail="create_job_id is required")
        
        # Generate file paths
        input_path = f"data/generated/{create_job_id}_qa_pairs.json"
        if not os.path.exists(input_path):
            # Fallback to a default path pattern
            potential_files = [f for f in os.listdir("data/generated") if f.endswith("_qa_pairs.json")]
            if potential_files:
                input_path = os.path.join("data/generated", sorted(potential_files)[-1])
            else:
                update_job_status(job_id, "failed", {"error": "No generated QA pairs found"})
                raise HTTPException(status_code=404, detail="No generated QA pairs found")
        
        output_path = f"data/cleaned/{get_unique_id()}_{time.strftime('%Y%m%d_%H%M%S')}_curated.json"
        
        # Start the curation job in the background
        background_tasks.add_task(
            process_curate_job,
            job_id=job_id,
            input_path=input_path,
            output_path=output_path,
            project_id=request.project_id,
            quality_threshold=request.quality_threshold,
            advanced_options=request.advanced_options
        )
        
        return {
            "status": "pending",
            "job_id": job_id,
            "message": "Curation job started"
        }
        
    except Exception as e:
        update_job_status(job_id, "failed", {"error": str(e)})
        logger.exception(f"Error in curation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in curation: {str(e)}")

@app.post("/mcp/data/export")
async def mcp_export_data(request: MCPExportRequest, background_tasks: BackgroundTasks):
    """Export curated data to the specified format"""
    job_id = get_unique_id()
    update_job_status(job_id, "pending")
    
    try:
        # Determine the source data
        curate_job_id = request.curate_job_id
        
        if not curate_job_id:
            # In a real implementation, we would query the database for the most recent curate job
            # For now, we'll require the curate_job_id
            update_job_status(job_id, "failed", {"error": "curate_job_id is required"})
            raise HTTPException(status_code=400, detail="curate_job_id is required")
        
        # Generate file paths
        input_path = f"data/cleaned/{curate_job_id}_curated.json"
        if not os.path.exists(input_path):
            # Fallback to a default path pattern
            potential_files = [f for f in os.listdir("data/cleaned") if f.endswith("_curated.json")]
            if potential_files:
                input_path = os.path.join("data/cleaned", sorted(potential_files)[-1])
            else:
                update_job_status(job_id, "failed", {"error": "No curated data found"})
                raise HTTPException(status_code=404, detail="No curated data found")
        
        output_path = f"data/final/{get_unique_id()}_{time.strftime('%Y%m%d_%H%M%S')}.{request.format}"
        
        # Start the export job in the background
        background_tasks.add_task(
            process_export_job,
            job_id=job_id,
            input_path=input_path,
            output_path=output_path,
            project_id=request.project_id,
            format=request.format,
            include_metadata=request.include_metadata
        )
        
        return {
            "status": "pending",
            "job_id": job_id,
            "message": f"Export to {request.format} started"
        }
        
    except Exception as e:
        update_job_status(job_id, "failed", {"error": str(e)})
        logger.exception(f"Error in export: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in export: {str(e)}")

@app.get("/mcp/jobs/{job_id}")
async def mcp_get_job_status(job_id: str):
    """Get the status of a job"""
    if job_id not in job_status:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return job_status[job_id]

@app.get("/mcp/jobs/{job_id}/result")
async def mcp_get_job_result(job_id: str):
    """Get the result of a completed job"""
    if job_id not in job_status:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = job_status[job_id]
    
    if job["status"] != "completed":
        return {"status": job["status"], "message": "Job not completed yet"}
    
    if "result_path" not in job["details"]:
        raise HTTPException(status_code=404, detail="Job result not found")
    
    try:
        with open(job["details"]["result_path"], "r", encoding="utf-8") as f:
            result = json.load(f)
        
        return {
            "status": "success",
            "job_id": job_id,
            "result": result
        }
    except Exception as e:
        logger.exception(f"Error retrieving job result: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving job result: {str(e)}")

@app.get("/mcp/projects/{project_id}/jobs")
async def mcp_get_project_jobs(project_id: str):
    """Get all jobs for a project"""
    # In a real implementation, we would query the database for all jobs for this project
    # For now, we'll just return a filtered list of jobs from our in-memory storage
    
    project_jobs = {
        job_id: job for job_id, job in job_status.items() 
        if "project_id" in job.get("details", {}) and job["details"]["project_id"] == project_id
    }
    
    return {"status": "success", "jobs": project_jobs}

# Background task processing functions
async def process_ingest_job(job_id, file_path, output_path, project_id):
    """Process an ingestion job in the background"""
    try:
        update_job_status(job_id, "running", {"project_id": project_id})
        
        # Get the appropriate parser
        parser = get_parser_for_file(file_path)
        if not parser:
            update_job_status(job_id, "failed", {
                "project_id": project_id,
                "error": f"No parser found for file: {file_path}"
            })
            return
        
        # Extract the text
        text = parser.parse()
        
        # Save the processed text
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(text)
        
        # Update job status to completed
        update_job_status(job_id, "completed", {
            "project_id": project_id,
            "result_path": output_path,
            "input_file": file_path
        })
        
    except Exception as e:
        logger.exception(f"Error in ingestion job {job_id}: {str(e)}")
        update_job_status(job_id, "failed", {
            "project_id": project_id,
            "error": str(e)
        })

async def process_create_job(job_id, input_path, output_path, project_id, num_pairs, temperature, advanced_options):
    """Process a QA pair creation job in the background"""
    try:
        update_job_status(job_id, "running", {"project_id": project_id})
        
        # Initialize LLM client
        llm_client = LLMClient(config.get("llm", {}))
        
        # Initialize QA generator
        generator = QAGenerator(llm_client)
        
        # Read the input text
        with open(input_path, "r", encoding="utf-8") as f:
            text = f.read()
        
        # Generate QA pairs
        qa_pairs = generator.generate(
            text=text, 
            num_pairs=num_pairs,
            temperature=temperature,
            **(advanced_options or {})
        )
        
        # Save the generated QA pairs
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(qa_pairs, f, indent=2)
        
        # Update job status to completed
        update_job_status(job_id, "completed", {
            "project_id": project_id,
            "result_path": output_path,
            "input_file": input_path,
            "count": len(qa_pairs)
        })
        
    except Exception as e:
        logger.exception(f"Error in create job {job_id}: {str(e)}")
        update_job_status(job_id, "failed", {
            "project_id": project_id,
            "error": str(e)
        })

async def process_curate_job(job_id, input_path, output_path, project_id, quality_threshold, advanced_options):
    """Process a curation job in the background"""
    try:
        update_job_status(job_id, "running", {"project_id": project_id})
        
        # Initialize LLM client
        llm_client = LLMClient(config.get("llm", {}))
        
        # Load the QA pairs
        with open(input_path, "r", encoding="utf-8") as f:
            qa_pairs = json.load(f)
        
        # In a real implementation, we would:
        # 1. Rate each QA pair for quality
        # 2. Filter out low-quality pairs
        # 3. Save the curated pairs
        # For simplicity in this example, we'll just filter based on token length
        
        curated_pairs = []
        for pair in qa_pairs:
            # Simple mock curation logic - usually this would use the LLM
            question_tokens = len(pair["question"].split())
            answer_tokens = len(pair["answer"].split())
            
            # Simulated quality score
            quality_score = min(1.0, (question_tokens / 50) * (answer_tokens / 200))
            
            pair["metadata"] = pair.get("metadata", {})
            pair["metadata"]["quality_score"] = quality_score
            
            if quality_score >= quality_threshold:
                curated_pairs.append(pair)
        
        # Save the curated QA pairs
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(curated_pairs, f, indent=2)
        
        # Update job status to completed
        update_job_status(job_id, "completed", {
            "project_id": project_id,
            "result_path": output_path,
            "input_file": input_path,
            "original_count": len(qa_pairs),
            "curated_count": len(curated_pairs)
        })
        
    except Exception as e:
        logger.exception(f"Error in curate job {job_id}: {str(e)}")
        update_job_status(job_id, "failed", {
            "project_id": project_id,
            "error": str(e)
        })

async def process_export_job(job_id, input_path, output_path, project_id, format, include_metadata):
    """Process an export job in the background"""
    try:
        update_job_status(job_id, "running", {"project_id": project_id})
        
        # Load the curated QA pairs
        with open(input_path, "r", encoding="utf-8") as f:
            qa_pairs = json.load(f)
        
        # Convert to the requested format
        converted_data = convert_format(
            qa_pairs, 
            target_format=format,
            include_metadata=include_metadata
        )
        
        # Save the converted data
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        if format == "jsonl":
            with open(output_path, "w", encoding="utf-8") as f:
                for item in converted_data:
                    f.write(json.dumps(item) + "\n")
        else:
            # For other formats, we'll just save as JSON for now
            with open(output_path, "w", encoding="utf-8") as f:
                if isinstance(converted_data, list):
                    json.dump(converted_data, f, indent=2)
                else:
                    f.write(converted_data)
        
        # Update job status to completed
        update_job_status(job_id, "completed", {
            "project_id": project_id,
            "result_path": output_path,
            "input_file": input_path,
            "format": format,
            "count": len(qa_pairs) if isinstance(qa_pairs, list) else 0
        })
        
    except Exception as e:
        logger.exception(f"Error in export job {job_id}: {str(e)}")
        update_job_status(job_id, "failed", {
            "project_id": project_id,
            "error": str(e)
        })

# MCP AI tool descriptions for agents
@app.get("/mcp/tools/description")
async def get_mcp_tool_descriptions():
    """Returns the tool descriptions for AI agents to use"""
    return {
        "tools": [
            {
                "name": "synthetic_data_create_project",
                "description": "Create a new synthetic data project",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Name of the project"
                        },
                        "description": {
                            "type": "string",
                            "description": "Description of the project"
                        }
                    },
                    "required": ["name"]
                }
            },
            {
                "name": "synthetic_data_ingest",
                "description": "Ingest data from text, URL, or YouTube for processing",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "project_id": {
                            "type": "string",
                            "description": "ID of the project"
                        },
                        "source_type": {
                            "type": "string",
                            "description": "Type of source (text, url, youtube)",
                            "enum": ["text", "url", "youtube"]
                        },
                        "content": {
                            "type": "string",
                            "description": "Text content to ingest (for source_type='text')"
                        },
                        "url": {
                            "type": "string",
                            "description": "URL to ingest from (for source_type='url' or 'youtube')"
                        }
                    },
                    "required": ["source_type"]
                }
            },
            {
                "name": "synthetic_data_create_qa",
                "description": "Generate question-answer pairs from ingested data",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "project_id": {
                            "type": "string",
                            "description": "ID of the project"
                        },
                        "ingest_job_id": {
                            "type": "string",
                            "description": "ID of the ingestion job"
                        },
                        "num_pairs": {
                            "type": "integer",
                            "description": "Number of QA pairs to generate",
                            "minimum": 1
                        },
                        "temperature": {
                            "type": "number",
                            "description": "Temperature for LLM generation",
                            "minimum": 0,
                            "maximum": 1
                        }
                    },
                    "required": ["project_id", "ingest_job_id"]
                }
            },
            {
                "name": "synthetic_data_curate",
                "description": "Curate and filter generated QA pairs based on quality",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "project_id": {
                            "type": "string",
                            "description": "ID of the project"
                        },
                        "create_job_id": {
                            "type": "string",
                            "description": "ID of the creation job"
                        },
                        "quality_threshold": {
                            "type": "number",
                            "description": "Threshold for quality (0.0 to 1.0)",
                            "minimum": 0,
                            "maximum": 1
                        }
                    },
                    "required": ["project_id", "create_job_id"]
                }
            },
            {
                "name": "synthetic_data_export",
                "description": "Export curated data to the specified format",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "project_id": {
                            "type": "string",
                            "description": "ID of the project"
                        },
                        "curate_job_id": {
                            "type": "string",
                            "description": "ID of the curation job"
                        },
                        "format": {
                            "type": "string",
                            "description": "Format to export to",
                            "enum": ["jsonl", "csv", "alpaca", "llama"]
                        },
                        "include_metadata": {
                            "type": "boolean",
                            "description": "Whether to include metadata in export"
                        }
                    },
                    "required": ["project_id", "curate_job_id", "format"]
                }
            },
            {
                "name": "synthetic_data_job_status",
                "description": "Get the status of a job",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "job_id": {
                            "type": "string",
                            "description": "ID of the job to check status for"
                        }
                    },
                    "required": ["job_id"]
                }
            },
            {
                "name": "synthetic_data_job_result",
                "description": "Get the result of a completed job",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "job_id": {
                            "type": "string",
                            "description": "ID of the job to get result for"
                        }
                    },
                    "required": ["job_id"]
                }
            }
        ]
    }

# API tool handler routes for AI agents
@app.post("/mcp/tools/execute/synthetic_data_create_project")
async def execute_create_project(request: Request):
    """Handle synthetic_data_create_project tool execution"""
    data = await request.json()
    response = await mcp_create_project(MCPProjectRequest(**data))
    return response

@app.post("/mcp/tools/execute/synthetic_data_ingest")
async def execute_ingest(request: Request, background_tasks: BackgroundTasks):
    """Handle synthetic_data_ingest tool execution"""
    data = await request.json()
    response = await mcp_ingest_data(MCPIngestRequest(**data), background_tasks)
    return response

@app.post("/mcp/tools/execute/synthetic_data_create_qa")
async def execute_create_qa(request: Request, background_tasks: BackgroundTasks):
    """Handle synthetic_data_create_qa tool execution"""
    data = await request.json()
    response = await mcp_create_qa_pairs(MCPCreateRequest(**data), background_tasks)
    return response

@app.post("/mcp/tools/execute/synthetic_data_curate")
async def execute_curate(request: Request, background_tasks: BackgroundTasks):
    """Handle synthetic_data_curate tool execution"""
    data = await request.json()
    response = await mcp_curate_qa_pairs(MCPCurateRequest(**data), background_tasks)
    return response

@app.post("/mcp/tools/execute/synthetic_data_export")
async def execute_export(request: Request, background_tasks: BackgroundTasks):
    """Handle synthetic_data_export tool execution"""
    data = await request.json()
    response = await mcp_export_data(MCPExportRequest(**data), background_tasks)
    return response

@app.post("/mcp/tools/execute/synthetic_data_job_status")
async def execute_job_status(request: Request):
    """Handle synthetic_data_job_status tool execution"""
    data = await request.json()
    response = await mcp_get_job_status(data["job_id"])
    return response

@app.post("/mcp/tools/execute/synthetic_data_job_result")
async def execute_job_result(request: Request):
    """Handle synthetic_data_job_result tool execution"""
    data = await request.json()
    response = await mcp_get_job_result(data["job_id"])
    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)