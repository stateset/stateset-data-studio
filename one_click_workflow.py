#!/usr/bin/env python
"""
One-click synthetic data generation workflow.
Provides a simple web interface to upload a file and process it through
all workflow steps (ingest, create, curate, save-as).
"""
import os
import uuid
import shutil
import datetime
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Import workflow functions
from api_workflow import (
    init_db, 
    setup_client, 
    step1_create_project, 
    step2_ingest, 
    step3_create_qa_pairs,
    step4_curate_qa_pairs,
    step5_export_data,
    print_header,
    print_step,
    print_result,
    print_error,
    CONFIG
)

app = FastAPI(title="StateSet Data Studio - One-Click Workflow")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure directories exist
os.makedirs("data/uploads", exist_ok=True)
os.makedirs("data/output", exist_ok=True)
os.makedirs("data/generated", exist_ok=True)
os.makedirs("data/cleaned", exist_ok=True)
os.makedirs("data/final", exist_ok=True)

# Initialize database
init_db()

# Global LLM client
llm_client = setup_client()

@app.get("/", response_class=HTMLResponse)
async def get_upload_page():
    """Return simple HTML page with file upload form"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>StateSet Data Studio - One-Click Workflow</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                line-height: 1.6;
            }
            h1 {
                color: #333;
                border-bottom: 1px solid #ddd;
                padding-bottom: 10px;
            }
            .container {
                background-color: #f9f9f9;
                border-radius: 5px;
                padding: 20px;
                margin-top: 20px;
            }
            .form-group {
                margin-bottom: 15px;
            }
            label {
                display: block;
                margin-bottom: 5px;
                font-weight: bold;
            }
            input[type="text"], input[type="number"] {
                width: 100%;
                padding: 8px;
                box-sizing: border-box;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
            input[type="file"] {
                padding: 10px 0;
            }
            button {
                background-color: #4CAF50;
                color: white;
                padding: 10px 15px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 16px;
            }
            button:hover {
                background-color: #45a049;
            }
            .loading {
                display: none;
                margin-top: 20px;
            }
            .progress {
                margin-top: 20px;
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: #fff;
                min-height: 200px;
                overflow-y: auto;
            }
            .status {
                margin-top: 10px;
                padding: 10px;
                border-radius: 4px;
            }
            .success {
                background-color: #dff0d8;
                border: 1px solid #d6e9c6;
                color: #3c763d;
            }
            .error {
                background-color: #f2dede;
                border: 1px solid #ebccd1;
                color: #a94442;
            }
        </style>
    </head>
    <body>
        <h1>StateSet Data Studio - One-Click Workflow</h1>
        <div class="container">
            <form id="uploadForm" enctype="multipart/form-data">
                <div class="form-group">
                    <label for="name">Project Name:</label>
                    <input type="text" id="name" name="name" required value="My Synthetic Data Project">
                </div>
                
                <div class="form-group">
                    <label for="description">Project Description:</label>
                    <input type="text" id="description" name="description" value="Generated with one-click workflow">
                </div>
                
                <div class="form-group">
                    <label for="file">Upload Content File:</label>
                    <input type="file" id="file" name="file" required>
                </div>
                
                <div class="form-group">
                    <label for="num_pairs">Number of QA Pairs to Generate:</label>
                    <input type="number" id="num_pairs" name="num_pairs" min="1" max="20" value="5">
                </div>
                
                <div class="form-group">
                    <label for="quality_threshold">Quality Threshold (1-10):</label>
                    <input type="number" id="quality_threshold" name="quality_threshold" min="1" max="10" step="0.1" value="6.0">
                </div>
                
                <div class="form-group">
                    <label for="format">Output Format:</label>
                    <select id="format" name="format">
                        <option value="jsonl">JSONL</option>
                        <option value="json">JSON</option>
                        <option value="csv">CSV</option>
                    </select>
                </div>
                
                <button type="submit" id="submitBtn">Generate Synthetic Data</button>
            </form>
            
            <div id="loading" class="loading">
                <p>Processing... This may take a few minutes.</p>
            </div>
            
            <div id="progress" class="progress" style="display: none;">
                <h3>Progress:</h3>
                <div id="progressContent"></div>
            </div>
            
            <div id="status" class="status" style="display: none;"></div>
        </div>
        
        <script>
            document.getElementById('uploadForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                
                const submitBtn = document.getElementById('submitBtn');
                const loadingDiv = document.getElementById('loading');
                const progressDiv = document.getElementById('progress');
                const progressContent = document.getElementById('progressContent');
                const statusDiv = document.getElementById('status');
                
                // Show loading indicator
                submitBtn.disabled = true;
                loadingDiv.style.display = 'block';
                progressDiv.style.display = 'block';
                statusDiv.style.display = 'none';
                progressContent.innerHTML = '<p>Starting workflow...</p>';
                
                // Prepare form data
                const formData = new FormData();
                formData.append('file', document.getElementById('file').files[0]);
                formData.append('name', document.getElementById('name').value);
                formData.append('description', document.getElementById('description').value);
                formData.append('num_pairs', document.getElementById('num_pairs').value);
                formData.append('quality_threshold', document.getElementById('quality_threshold').value);
                formData.append('format', document.getElementById('format').value);
                
                try {
                    // Call API endpoint
                    const response = await fetch('/api/workflow/run', {
                        method: 'POST',
                        body: formData
                    });
                    
                    // Parse JSON response
                    const result = await response.json();
                    
                    // Update progress with logs
                    if (result.logs) {
                        progressContent.innerHTML += result.logs.map(log => `<p>${log}</p>`).join('');
                    }
                    
                    // Show success or error status
                    if (response.ok) {
                        statusDiv.className = 'status success';
                        statusDiv.innerHTML = `
                            <h3>Workflow Completed Successfully!</h3>
                            <p>Project ID: ${result.project_id}</p>
                            <p>Final Output File: ${result.final_output_file}</p>
                            <p>Generated ${result.qa_count} QA pairs, kept ${result.curated_count} high-quality pairs.</p>
                        `;
                    } else {
                        statusDiv.className = 'status error';
                        statusDiv.innerHTML = `<h3>Error:</h3><p>${result.detail || 'Unknown error occurred'}</p>`;
                    }
                } catch (error) {
                    statusDiv.className = 'status error';
                    statusDiv.innerHTML = `<h3>Error:</h3><p>${error.message}</p>`;
                } finally {
                    // Hide loading indicator, show status
                    submitBtn.disabled = false;
                    loadingDiv.style.display = 'none';
                    statusDiv.style.display = 'block';
                    
                    // Scroll to status
                    statusDiv.scrollIntoView({ behavior: 'smooth' });
                }
            });
        </script>
    </body>
    </html>
    """

@app.post("/api/workflow/run")
async def run_workflow(
    file: UploadFile = File(...),
    name: str = Form(...),
    description: str = Form(...),
    num_pairs: int = Form(5),
    quality_threshold: float = Form(6.0),
    format: str = Form("jsonl")
):
    """Run the complete synthetic data workflow from a single upload"""
    
    logs = []
    
    try:
        # Read file content
        file_content = await file.read()
        
        # Save original file
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        original_filename = f"data/uploads/{timestamp}_{file.filename}"
        with open(original_filename, "wb") as f:
            f.write(file_content)
        
        logs.append(f"Uploaded file saved as {original_filename}")
        
        # Update configuration
        custom_config = CONFIG.copy()
        custom_config["workflow"]["creation"]["num_pairs"] = num_pairs
        custom_config["workflow"]["curation"]["threshold"] = quality_threshold
        custom_config["workflow"]["output_format"] = format
        
        # Step 1: Create project
        logs.append("Creating project...")
        project_id = step1_create_project()
        logs.append(f"Project created with ID: {project_id}")
        
        # Step 2: Ingest content
        logs.append("Ingesting content...")
        
        # Check file extension
        file_ext = file.filename.lower().split('.')[-1] if '.' in file.filename else ''
        
        # Handle based on file type
        if file_ext in ['pdf', 'docx', 'pptx', 'xlsx']:
            # For binary files that need special processing
            logs.append(f"Detected binary file of type {file_ext}")
            logs.append("Binary files are not directly supported in this demo")
            logs.append("Using extracted text from file")
            
            # For this demo, we'll just create some placeholder text
            # In a real implementation, you would use appropriate parsers
            content = f"""
            # Content extracted from {file.filename}
            
            This is placeholder text for demonstration purposes.
            In a production environment, the appropriate parser would be used
            to extract text content from this {file_ext.upper()} file.
            
            The file has been saved at {original_filename} for further processing.
            """
        else:
            # Try to read as text
            try:
                content = file_content.decode("utf-8")
            except UnicodeDecodeError:
                # If it's not UTF-8, try other encodings
                try:
                    content = file_content.decode("latin-1")  # More permissive encoding
                except:
                    # Last resort - read with replacement characters
                    with open(original_filename, "r", errors="replace") as f:
                        content = f.read()
        ingest_job_id, processed_file = step2_ingest(project_id, content)
        logs.append(f"Ingestion complete: {processed_file}")
        
        if not processed_file:
            raise HTTPException(status_code=500, detail="Ingestion failed")
        
        # Step 3: Generate QA pairs
        logs.append("Generating QA pairs...")
        create_job_id, qa_file, qa_pairs = step3_create_qa_pairs(
            project_id, processed_file, llm_client, custom_config
        )
        
        if not qa_pairs:
            raise HTTPException(status_code=500, detail="QA pair generation failed")
        
        logs.append(f"Generated {len(qa_pairs)} QA pairs: {qa_file}")
        
        # Step 4: Curate QA pairs
        logs.append("Curating QA pairs...")
        curate_job_id, curated_file, curated_pairs = step4_curate_qa_pairs(
            project_id, qa_file, llm_client, custom_config
        )
        
        if not curated_pairs:
            raise HTTPException(status_code=500, detail="Curation failed")
        
        logs.append(f"Curated to {len(curated_pairs)} high-quality QA pairs: {curated_file}")
        
        # Step 5: Export data
        logs.append("Exporting final data...")
        export_job_id, final_file = step5_export_data(
            project_id, curated_file, custom_config
        )
        
        if not final_file:
            raise HTTPException(status_code=500, detail="Export failed")
        
        logs.append(f"Data exported to {final_file}")
        
        # Return successful response
        return {
            "project_id": project_id,
            "original_file": original_filename,
            "final_output_file": final_file,
            "qa_count": len(qa_pairs) if qa_pairs else 0,
            "curated_count": len(curated_pairs) if curated_pairs else 0,
            "format": format,
            "logs": logs
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    print("Starting StateSet Data Studio One-Click Workflow Server...")
    print("Open http://localhost:5000 in your browser")
    uvicorn.run(app, host="0.0.0.0", port=5000)