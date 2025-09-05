# StateSet Data Studio - One-Click Workflow

This tool provides a simple web interface to process text content through the complete synthetic data generation pipeline with a single click.

## Features

- **Simple Web Interface**: Upload a file and configure settings through a user-friendly form
- **End-to-End Processing**: Automatically runs all four pipeline steps:
  1. **Ingest**: Process and store the input content
  2. **Create**: Generate QA pairs from the content
  3. **Curate**: Evaluate and filter QA pairs based on quality
  4. **Save-As**: Export the final data in your chosen format
- **Customizable Settings**: Adjust the number of QA pairs, quality threshold, and output format
- **Live Progress Updates**: Monitor the workflow as it progresses
- **Database Integration**: All jobs are tracked in the system database

## Usage

1. Start the server:
   ```
   ./test_run.sh
   ```
   or
   ```
   python one_click_workflow.py
   ```

2. Open your browser and navigate to: http://localhost:5000

3. Fill in the form:
   - Project Name: Name for your synthetic data project
   - Project Description: Brief description of the project
   - Upload Content File: Text file containing the source content
   - Number of QA Pairs: How many question-answer pairs to generate
   - Quality Threshold: Minimum quality score (1-10) for keeping QA pairs
   - Output Format: Choose between JSONL, JSON, or CSV

4. Click "Generate Synthetic Data" to start the workflow

5. Monitor the progress in real-time

6. Once complete, you'll see a success message with links to your generated files

## Output

The workflow creates several files during processing:

- **Uploaded File**: `data/uploads/{timestamp}_{filename}`
- **Processed Content**: `data/output/processed_{timestamp}.txt`
- **Generated QA Pairs**: `data/generated/{project_id}_{timestamp}_qa_pairs.json`
- **Curated QA Pairs**: `data/cleaned/{project_id}_{timestamp}_curated.json`
- **Final Output**: `data/final/{project_id}_{timestamp}.{format}`

## Customization

You can modify the default settings in the `one_click_workflow.py` file:

- Change LLM model or API settings
- Adjust default number of QA pairs
- Modify quality threshold
- Add additional processing steps

## Requirements

- fastapi
- uvicorn
- python-multipart
- Synthetic Data Kit dependencies