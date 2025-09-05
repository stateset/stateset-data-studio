# StateSet Data Studio MCP Server

This document describes how to use the StateSet Data Studio MCP (Model Control Protocol) Server for AI Agent integration.

## Overview

The MCP Server provides an interface for AI Agents to interact with StateSet Data Studio capabilities. It allows agents to create projects, ingest data, generate QA pairs, curate them, and export results in various formats.

## Running the Server

To start the MCP server:

```bash
python run_mcp_server.py
```

Optional arguments:
- `--host`: Host address to bind to (default: 0.0.0.0)
- `--port`: Port to bind to (default: 8000)
- `--reload`: Enable auto-reload during development
- `--log-level`: Set logging level (debug, info, warning, error, critical)

Example:
```bash
python run_mcp_server.py --port 8080 --log-level debug
```

## API Endpoints for AI Agents

The MCP server exposes tool descriptions and execution endpoints:

- **Tool Descriptions**: `/mcp/tools/description`
- **Tool Execution**: `/mcp/tools/execute/{tool_name}`

## StateSet Data Studio Tools

### 1. Create Project

Create a new project for synthetic data generation.

- **Tool Name**: `synthetic_data_create_project`
- **Parameters**:
  - `name`: Name of the project (required)
  - `description`: Description of the project (optional)

Example:
```json
{
  "name": "Medical QA Dataset",
  "description": "Dataset containing medical question-answer pairs for fine-tuning"
}
```

### 2. Ingest Data

Ingest data from text, URL, or YouTube for processing.

- **Tool Name**: `synthetic_data_ingest`
- **Parameters**:
  - `project_id`: ID of the project (optional)
  - `source_type`: Type of source (`text`, `url`, `youtube`)
  - `content`: Text content to ingest (for `source_type='text'`)
  - `url`: URL to ingest from (for `source_type='url'` or `'youtube'`)

Example:
```json
{
  "project_id": "f8a5c4d3-b9e7-42a1-8f6d-9e0c3b1a2d5e",
  "source_type": "text",
  "content": "This is some text that will be used to generate synthetic QA pairs..."
}
```

### 3. Create QA Pairs

Generate question-answer pairs from ingested data.

- **Tool Name**: `synthetic_data_create_qa`
- **Parameters**:
  - `project_id`: ID of the project (required)
  - `ingest_job_id`: ID of the ingestion job (required)
  - `num_pairs`: Number of QA pairs to generate (optional, default: 10)
  - `temperature`: Temperature for LLM generation (optional, default: 0.7)

Example:
```json
{
  "project_id": "f8a5c4d3-b9e7-42a1-8f6d-9e0c3b1a2d5e",
  "ingest_job_id": "a1b2c3d4-e5f6-7890-a1b2-c3d4e5f67890",
  "num_pairs": 20,
  "temperature": 0.8
}
```

### 4. Curate QA Pairs

Curate and filter generated QA pairs based on quality.

- **Tool Name**: `synthetic_data_curate`
- **Parameters**:
  - `project_id`: ID of the project (required)
  - `create_job_id`: ID of the creation job (required)
  - `quality_threshold`: Threshold for quality (0.0 to 1.0) (optional, default: 0.7)

Example:
```json
{
  "project_id": "f8a5c4d3-b9e7-42a1-8f6d-9e0c3b1a2d5e",
  "create_job_id": "b2c3d4e5-f6g7-8901-b2c3-d4e5f6g78901",
  "quality_threshold": 0.8
}
```

### 5. Export Data

Export curated data to the specified format.

- **Tool Name**: `synthetic_data_export`
- **Parameters**:
  - `project_id`: ID of the project (required)
  - `curate_job_id`: ID of the curation job (required)
  - `format`: Format to export to (`jsonl`, `csv`, `alpaca`, `llama`) (required)
  - `include_metadata`: Whether to include metadata in export (optional, default: true)

Example:
```json
{
  "project_id": "f8a5c4d3-b9e7-42a1-8f6d-9e0c3b1a2d5e",
  "curate_job_id": "c3d4e5f6-g7h8-9012-c3d4-e5f6g7h89012",
  "format": "jsonl",
  "include_metadata": true
}
```

### 6. Get Job Status

Get the status of a job.

- **Tool Name**: `synthetic_data_job_status`
- **Parameters**:
  - `job_id`: ID of the job to check status for (required)

Example:
```json
{
  "job_id": "d4e5f6g7-h8i9-0123-d4e5-f6g7h8i90123"
}
```

### 7. Get Job Result

Get the result of a completed job.

- **Tool Name**: `synthetic_data_job_result`
- **Parameters**:
  - `job_id`: ID of the job to get result for (required)

Example:
```json
{
  "job_id": "d4e5f6g7-h8i9-0123-d4e5-f6g7h8i90123"
}
```

## Complete Workflow Example

Here's an example of a complete workflow from an agent perspective:

1. Create a project:
   ```json
   {
     "name": "Medical QA Dataset"
   }
   ```
   Response: `{"status": "success", "project_id": "f8a5c4d3-b9e7-42a1-8f6d-9e0c3b1a2d5e", "name": "Medical QA Dataset"}`

2. Ingest text data:
   ```json
   {
     "project_id": "f8a5c4d3-b9e7-42a1-8f6d-9e0c3b1a2d5e",
     "source_type": "text",
     "content": "Diabetes is a chronic health condition that affects how your body turns food into energy..."
   }
   ```
   Response: `{"status": "pending", "job_id": "a1b2c3d4-e5f6-7890-a1b2-c3d4e5f67890", "message": "Data ingestion started"}`

3. Check ingestion job status:
   ```json
   {
     "job_id": "a1b2c3d4-e5f6-7890-a1b2-c3d4e5f67890"
   }
   ```
   Response: `{"status": "completed", "updated_at": 1715698461.123, "details": {"project_id": "f8a5c4d3-b9e7-42a1-8f6d-9e0c3b1a2d5e", "result_path": "data/output/processed_20250504_063658.txt", "input_file": "data/uploads/mcp_a1b2c3d4-e5f6-7890-a1b2-c3d4e5f67890_20250504_063658.txt"}}`

4. Generate QA pairs:
   ```json
   {
     "project_id": "f8a5c4d3-b9e7-42a1-8f6d-9e0c3b1a2d5e",
     "ingest_job_id": "a1b2c3d4-e5f6-7890-a1b2-c3d4e5f67890",
     "num_pairs": 15
   }
   ```
   Response: `{"status": "pending", "job_id": "b2c3d4e5-f6g7-8901-b2c3-d4e5f6g78901", "message": "QA pair generation started"}`

5. Check QA generation job status:
   ```json
   {
     "job_id": "b2c3d4e5-f6g7-8901-b2c3-d4e5f6g78901"
   }
   ```
   Response: `{"status": "completed", "updated_at": 1715698481.456, "details": {"project_id": "f8a5c4d3-b9e7-42a1-8f6d-9e0c3b1a2d5e", "result_path": "data/generated/81d25571-bae6-4293-b561-4f44c1b1548f_20250504_063706_qa_pairs.json", "input_file": "data/output/processed_20250504_063658.txt", "count": 15}}`

6. Curate QA pairs:
   ```json
   {
     "project_id": "f8a5c4d3-b9e7-42a1-8f6d-9e0c3b1a2d5e",
     "create_job_id": "b2c3d4e5-f6g7-8901-b2c3-d4e5f6g78901",
     "quality_threshold": 0.8
   }
   ```
   Response: `{"status": "pending", "job_id": "c3d4e5f6-g7h8-9012-c3d4-e5f6g7h89012", "message": "Curation job started"}`

7. Check curation job status:
   ```json
   {
     "job_id": "c3d4e5f6-g7h8-9012-c3d4-e5f6g7h89012"
   }
   ```
   Response: `{"status": "completed", "updated_at": 1715698491.789, "details": {"project_id": "f8a5c4d3-b9e7-42a1-8f6d-9e0c3b1a2d5e", "result_path": "data/cleaned/81d25571-bae6-4293-b561-4f44c1b1548f_20250504_063706_curated.json", "input_file": "data/generated/81d25571-bae6-4293-b561-4f44c1b1548f_20250504_063706_qa_pairs.json", "original_count": 15, "curated_count": 11}}`

8. Export curated data:
   ```json
   {
     "project_id": "f8a5c4d3-b9e7-42a1-8f6d-9e0c3b1a2d5e",
     "curate_job_id": "c3d4e5f6-g7h8-9012-c3d4-e5f6g7h89012",
     "format": "jsonl"
   }
   ```
   Response: `{"status": "pending", "job_id": "d4e5f6g7-h8i9-0123-d4e5-f6g7h8i90123", "message": "Export to jsonl started"}`

9. Check export job status:
   ```json
   {
     "job_id": "d4e5f6g7-h8i9-0123-d4e5-f6g7h8i90123"
   }
   ```
   Response: `{"status": "completed", "updated_at": 1715698501.012, "details": {"project_id": "f8a5c4d3-b9e7-42a1-8f6d-9e0c3b1a2d5e", "result_path": "data/final/81d25571-bae6-4293-b561-4f44c1b1548f_20250504_063706.jsonl", "input_file": "data/cleaned/81d25571-bae6-4293-b561-4f44c1b1548f_20250504_063706_curated.json", "format": "jsonl", "count": 11}}`

10. Get job result:
    ```json
    {
      "job_id": "d4e5f6g7-h8i9-0123-d4e5-f6g7h8i90123"
    }
    ```
    Response: `{"status": "success", "job_id": "d4e5f6g7-h8i9-0123-d4e5-f6g7h8i90123", "result": [...exported data...]}`

## Error Handling

If a job fails, the status endpoint will return:

```json
{
  "status": "failed",
  "updated_at": 1715698520.345,
  "details": {
    "project_id": "f8a5c4d3-b9e7-42a1-8f6d-9e0c3b1a2d5e",
    "error": "Error message describing what went wrong"
  }
}
```

## Security Considerations

- The MCP server is designed for internal use by trusted AI agents
- Implement appropriate authentication and authorization if exposing to external networks
- Consider rate limiting for production environments
- Monitor server logs for unusual activity or error patterns