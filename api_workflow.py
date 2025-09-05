#!/usr/bin/env python
"""
API-based workflow for StateSet Data Studio using direct SDK calls.
This script simulates the complete project workflow:
1. Creating a project
2. Ingesting content
3. Creating QA pairs
4. Curating for quality
5. Saving in desired format
"""
import os
import json
import sys
import time
import uuid
import datetime
import sqlite3
from synthetic_data_kit.models.llm_client import LLMClient

# Database path
DB_PATH = "synthetic_data_api.db"

# Configure verbose output
VERBOSE = True

# ----------------- Configuration -----------------
CONFIG = {
    "api_type": "llama",
    "llama": {
        "api_key": "llama-api-key",
        "model": "Llama-4-Maverick-17B-128E-Instruct-FP8"
    },
    "workflow": {
        "creation": {
            "temperature": 0.3,
            "num_pairs": 5,
            "max_tokens": 2000
        },
        "curation": {
            "threshold": 6.0,
            "temperature": 0.1
        },
        "output_format": "jsonl"  # Options: jsonl, json, csv
    }
}

# Test content for ingestion
TEST_CONTENT = """
# Machine Learning Applications

Machine learning is transforming industries across the global economy. By enabling computers to learn from data and improve their performance over time without explicit programming, ML has opened up new possibilities for automation, prediction, and decision-making.

## Key Applications

### Healthcare
- **Disease Diagnosis**: ML algorithms can analyze medical images to detect diseases like cancer, often with accuracy rivaling or exceeding human doctors.
- **Drug Discovery**: ML accelerates the identification of potential drug candidates by predicting how different compounds will interact with biological targets.
- **Patient Monitoring**: Wearable devices combined with ML can continuously monitor patients and predict health events before they occur.

### Finance
- **Fraud Detection**: ML systems can identify unusual patterns in transaction data to flag potential fraud in real-time.
- **Algorithmic Trading**: ML models analyze market data to make trading decisions at speeds impossible for humans.
- **Credit Scoring**: More sophisticated ML-based credit models can assess creditworthiness using diverse data sources.

### Transportation
- **Autonomous Vehicles**: Self-driving cars use ML to understand their environment, predict movements of other road users, and navigate safely.
- **Traffic Prediction**: ML algorithms analyze historical and real-time traffic data to predict congestion and optimize routing.
- **Public Transit Optimization**: Cities use ML to optimize bus and train schedules based on demand patterns.

## Challenges

Despite its potential, ML faces several important challenges:

1. **Data Quality**: ML models are only as good as the data they're trained on. Biased or incomplete data leads to flawed models.

2. **Interpretability**: Many powerful ML models (like deep neural networks) function as "black boxes," making it difficult to understand how they arrive at specific decisions.

3. **Computational Resources**: Training sophisticated ML models requires significant computing power and energy, raising both cost and environmental concerns.

4. **Privacy Concerns**: ML systems often require large amounts of data, which can include sensitive personal information.

As these challenges are addressed, ML applications will continue to expand, bringing both tremendous opportunities and important ethical considerations that society must navigate carefully.
"""

# ----------------- Utility Functions -----------------
def print_header(text):
    """Print a formatted header"""
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"\n\n{'='*80}")
    print(f"[{timestamp}] {text}")
    print(f"{'='*80}")

def print_step(text):
    """Print a step description"""
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"\n[{timestamp}] 📋 {text}")

def print_result(text, data=None):
    """Print a result with optional data"""
    if data and VERBOSE:
        print(f"✅ {text}:")
        print(f"   {data}")
    else:
        print(f"✅ {text}")

def print_error(text):
    """Print an error message"""
    print(f"❌ {text}")

def setup_client():
    """Set up the LLM client with the configuration"""
    client = LLMClient()
    client.api_type = CONFIG["api_type"]
    
    if CONFIG["api_type"] == "llama":
        client.api_base = "https://api.llama.com/v1"
        client.model = CONFIG["llama"]["model"]
        client.api_key = CONFIG["llama"]["api_key"]
    else:
        # Default to vLLM if not using Llama API
        client.api_base = "http://localhost:8000/v1"
        client.model = "meta-llama/Llama-3.3-70B-Instruct"
    
    return client

def ensure_dir(directory):
    """Ensure a directory exists"""
    if not os.path.exists(directory):
        os.makedirs(directory)

# ----------------- Database Functions -----------------
def init_db():
    """Initialize the database if it doesn't exist"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create projects table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS projects (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create jobs table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS jobs (
        id TEXT PRIMARY KEY,
        project_id TEXT NOT NULL,
        job_type TEXT NOT NULL,
        status TEXT NOT NULL,
        input_file TEXT,
        output_file TEXT,
        config TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        error TEXT,
        stats TEXT,
        FOREIGN KEY (project_id) REFERENCES projects (id)
    )
    ''')
    
    conn.commit()
    conn.close()

def create_project(name, description=None):
    """Create a new project in the database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    project_id = str(uuid.uuid4())
    cursor.execute(
        "INSERT INTO projects (id, name, description) VALUES (?, ?, ?)",
        (project_id, name, description)
    )
    
    conn.commit()
    conn.close()
    
    return project_id

def create_job(project_id, job_type, status="pending", input_file=None, config=None):
    """Create a new job in the database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    job_id = str(uuid.uuid4())
    cursor.execute(
        "INSERT INTO jobs (id, project_id, job_type, status, input_file, config) VALUES (?, ?, ?, ?, ?, ?)",
        (job_id, project_id, job_type, status, input_file, config)
    )
    
    conn.commit()
    conn.close()
    
    return job_id

def update_job(job_id, status=None, output_file=None, error=None, stats=None):
    """Update a job in the database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if stats column exists in jobs table
    cursor.execute("PRAGMA table_info(jobs)")
    columns = [item[1] for item in cursor.fetchall()]
    
    # Add stats column if it doesn't exist
    if "stats" not in columns:
        cursor.execute("ALTER TABLE jobs ADD COLUMN stats TEXT")
        conn.commit()
    
    updates = []
    params = []
    
    if status:
        updates.append("status = ?")
        params.append(status)
    
    if output_file:
        updates.append("output_file = ?")
        params.append(output_file)
    
    if error:
        updates.append("error = ?")
        params.append(error)
    
    if stats:
        updates.append("stats = ?")
        params.append(json.dumps(stats) if isinstance(stats, dict) else stats)
    
    if updates:
        updates.append("updated_at = CURRENT_TIMESTAMP")
        query = f"UPDATE jobs SET {', '.join(updates)} WHERE id = ?"
        params.append(job_id)
        
        cursor.execute(query, params)
        conn.commit()
    
    conn.close()

# ----------------- Workflow Steps -----------------
def step1_create_project():
    """Create a new project"""
    print_header("STEP 1: CREATE PROJECT")
    
    project_name = "Llama API Demo"
    project_description = "Testing full workflow with Llama API"
    
    print_step(f"Creating project '{project_name}'...")
    
    project_id = create_project(project_name, project_description)
    
    print_result(f"Project created with ID: {project_id}")
    return project_id

def step2_ingest(project_id, content):
    """Ingest content into the project"""
    print_header("STEP 2: INGESTION")
    
    # Create job record
    job_id = create_job(project_id, "ingest")
    print_step(f"Created ingest job with ID: {job_id}")
    
    print_step("Processing input content...")
    
    # Analyze content
    char_count = len(content)
    word_count = len(content.split())
    line_count = len(content.splitlines())
    
    # Update job as running
    update_job(job_id, status="completed")
    
    # Save content to a file
    ensure_dir("data/uploads")
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"data/uploads/ingest_{timestamp}.txt"
    
    with open(filename, 'w') as f:
        f.write(content)
    
    # Process content for further steps - in this case just save it as processed
    ensure_dir("data/output")
    output_file = f"data/output/processed_{timestamp}.txt"
    with open(output_file, 'w') as f:
        f.write(content)
    
    # Update job stats
    stats = {
        "chars": char_count,
        "words": word_count,
        "lines": line_count
    }
    
    # Update job as completed
    update_job(job_id, 
               status="completed", 
               output_file=output_file, 
               stats=stats)
    
    print_result(f"Ingestion job completed. Content saved to {output_file}")
    print_result("Content statistics", 
                f"Characters: {char_count}, Words: {word_count}, Lines: {line_count}")
    
    return job_id, output_file

def step3_create_qa_pairs(project_id, input_file, client, config):
    """Generate QA pairs from input content"""
    print_header("STEP 3: QA PAIR GENERATION")
    
    # Create job record
    job_id = create_job(project_id, "create", input_file=input_file)
    print_step(f"Created QA generation job with ID: {job_id}")
    
    # Read the input file
    print_step(f"Reading content from {input_file}...")
    with open(input_file, 'r') as f:
        content = f.read()
    
    # Update job as running
    update_job(job_id, status="completed")
    
    # Set up generation parameters
    num_pairs = config["workflow"]["creation"]["num_pairs"]
    temperature = config["workflow"]["creation"]["temperature"]
    max_tokens = config["workflow"]["creation"]["max_tokens"]
    
    print_step(f"Generating {num_pairs} QA pairs with temperature {temperature}...")
    
    # Prepare prompt
    prompt = [
        {"role": "system", "content": "You are an expert instructor tasked with creating high-quality question-answer pairs."},
        {"role": "user", "content": f"""
Create {num_pairs} high-quality question-answer pairs from the following content.
Each pair should test understanding of different aspects of the content.
Make questions challenging and diverse, covering different topics and difficulty levels.
Format your response as a JSON array where each object has a 'question' and 'answer' field.

CONTENT:
{content}
"""}
    ]
    
    try:
        # Send request to LLM
        response = client.chat_completion(
            messages=prompt,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        # Extract JSON from response
        json_content = response
        if "```json" in response:
            json_content = response.split("```json")[1].split("```")[0].strip()
        elif "```" in response:
            json_content = response.split("```")[1].split("```")[0].strip()
            
        qa_pairs = json.loads(json_content)
        
        # Save to file
        ensure_dir("data/generated")
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"data/generated/{project_id}_{timestamp}_qa_pairs.json"
        with open(output_file, "w") as f:
            json.dump(qa_pairs, f, indent=2)
            
        # Update stats
        stats = {
            "qa_count": len(qa_pairs),
            "temperature": temperature,
            "sample": qa_pairs[0] if qa_pairs else None
        }
        
        # Update job as completed
        update_job(job_id, 
                  status="completed", 
                  output_file=output_file, 
                  stats=stats)
        
        print_result(f"Generated {len(qa_pairs)} QA pairs")
        
        # Show sample
        if qa_pairs and VERBOSE:
            print("\nSample QA pair:")
            print(f"  Q: {qa_pairs[0]['question']}")
            print(f"  A: {qa_pairs[0]['answer'][:100]}...")
        
        return job_id, output_file, qa_pairs
    
    except Exception as e:
        # Update job as failed
        update_job(job_id, 
                  status="failed", 
                  error=str(e))
        
        print_error(f"Error generating QA pairs: {str(e)}")
        return job_id, None, None

def step4_curate_qa_pairs(project_id, input_file, client, config):
    """Curate QA pairs for quality"""
    print_header("STEP 4: CURATION")
    
    # Create job record
    job_id = create_job(project_id, "curate", input_file=input_file)
    print_step(f"Created curation job with ID: {job_id}")
    
    # Read the input file
    print_step(f"Reading QA pairs from {input_file}...")
    try:
        with open(input_file, 'r') as f:
            qa_pairs = json.load(f)
    except Exception as e:
        update_job(job_id, 
                  status="failed", 
                  error=f"Error reading input file: {str(e)}")
        print_error(f"Error reading input file: {str(e)}")
        return job_id, None, None
    
    if not qa_pairs:
        update_job(job_id, 
                  status="failed", 
                  error="No QA pairs to curate")
        print_error("No QA pairs to curate")
        return job_id, None, None
    
    # Update job as running
    update_job(job_id, status="running")
    
    threshold = config["workflow"]["curation"]["threshold"]
    temperature = config["workflow"]["curation"]["temperature"]
    
    print_step(f"Curating {len(qa_pairs)} QA pairs with quality threshold {threshold}...")
    
    # Evaluate each QA pair
    curated_pairs = []
    scores = []
    
    for i, pair in enumerate(qa_pairs):
        print_step(f"Evaluating pair {i+1}/{len(qa_pairs)}...")
        
        prompt = [
            {"role": "system", "content": "You are an expert at evaluating the quality of question-answer pairs."},
            {"role": "user", "content": f"""
On a scale from 1 to 10, rate the quality of this question-answer pair.
A high-quality pair should:
- Have a clear, specific question directly related to the content
- Provide a comprehensive, accurate answer
- Test understanding rather than just recall
- Be free of errors or ambiguity

Question: {pair['question']}
Answer: {pair['answer']}

Provide your rating as a number between 1 and 10, followed by a brief explanation.
"""}
        ]
        
        try:
            response = client.chat_completion(
                messages=prompt,
                temperature=temperature,
                max_tokens=300
            )
            
            # Extract score from response (first number found)
            import re
            score_match = re.search(r'(\d+(\.\d+)?)', response)
            if score_match:
                score = float(score_match.group(1))
                scores.append(score)
                
                if score >= threshold:
                    pair['score'] = score
                    curated_pairs.append(pair)
                    print_result(f"Pair {i+1} meets threshold with score {score}")
                else:
                    print_step(f"Pair {i+1} below threshold with score {score}")
            else:
                print_error(f"Could not extract score for pair {i+1}")
        
        except Exception as e:
            print_error(f"Error evaluating pair {i+1}: {str(e)}")
    
    # Summarize curation results
    if scores:
        avg_score = sum(scores) / len(scores)
        print_result(f"Average quality score: {avg_score:.2f}")
    
    if curated_pairs:
        # Save curated pairs
        ensure_dir("data/cleaned")
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"data/cleaned/{project_id}_{timestamp}_curated.json"
        with open(output_file, "w") as f:
            json.dump(curated_pairs, f, indent=2)
            
        # Update stats
        stats = {
            "original_count": len(qa_pairs),
            "curated_count": len(curated_pairs),
            "kept_percentage": round(len(curated_pairs) / len(qa_pairs) * 100, 2),
            "avg_score": round(avg_score, 2) if scores else None,
            "threshold": threshold
        }
        
        # Update job as completed
        update_job(job_id, 
                  status="completed", 
                  output_file=output_file, 
                  stats=stats)
        
        print_result(f"Saved {len(curated_pairs)} curated QA pairs to {output_file}")
        print_result(f"Removed {len(qa_pairs) - len(curated_pairs)} low-quality pairs")
        return job_id, output_file, curated_pairs
    else:
        # Update job as failed
        update_job(job_id, 
                  status="failed", 
                  error="No pairs met the quality threshold")
        
        print_error("No pairs met the quality threshold")
        return job_id, None, None

def step5_export_data(project_id, input_file, config):
    """Save curated pairs in the desired format"""
    print_header("STEP 5: EXPORT")
    
    # Create job record
    job_id = create_job(project_id, "save-as", input_file=input_file)
    print_step(f"Created export job with ID: {job_id}")
    
    # Read the input file
    print_step(f"Reading curated pairs from {input_file}...")
    try:
        with open(input_file, 'r') as f:
            curated_pairs = json.load(f)
    except Exception as e:
        update_job(job_id, 
                  status="failed", 
                  error=f"Error reading input file: {str(e)}")
        print_error(f"Error reading input file: {str(e)}")
        return job_id, None
    
    if not curated_pairs:
        update_job(job_id, 
                  status="failed", 
                  error="No curated pairs to export")
        print_error("No curated pairs to export")
        return job_id, None
    
    # Update job as running
    update_job(job_id, status="running")
    
    format_type = config["workflow"]["output_format"]
    print_step(f"Exporting {len(curated_pairs)} QA pairs in {format_type.upper()} format...")
    
    ensure_dir("data/final")
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"data/final/{project_id}_{timestamp}.{format_type}"
    
    try:
        if format_type == 'jsonl':
            with open(output_file, "w") as f:
                for pair in curated_pairs:
                    f.write(json.dumps(pair) + "\n")
        elif format_type == 'json':
            with open(output_file, "w") as f:
                json.dump(curated_pairs, f, indent=2)
        elif format_type == 'csv':
            import csv
            with open(output_file, "w", newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["question", "answer", "score"])
                for pair in curated_pairs:
                    writer.writerow([pair["question"], pair["answer"], pair.get("score", "")])
        else:
            update_job(job_id, 
                      status="failed", 
                      error=f"Unsupported format: {format_type}")
            print_error(f"Unsupported format: {format_type}")
            return job_id, None
        
        # Update stats
        stats = {
            "format": format_type,
            "record_count": len(curated_pairs),
            "file_size_bytes": os.path.getsize(output_file),
            "file_size_mb": round(os.path.getsize(output_file) / (1024 * 1024), 4)
        }
        
        # Update job as completed
        update_job(job_id, 
                  status="completed", 
                  output_file=output_file, 
                  stats=stats)
            
        print_result(f"Successfully exported data to {output_file}")
        return job_id, output_file
    except Exception as e:
        # Update job as failed
        update_job(job_id, 
                  status="failed", 
                  error=str(e))
        
        print_error(f"Error exporting data: {str(e)}")
        return job_id, None

def run_workflow():
    """Run the complete workflow"""
    print_header("SYNTHETIC DATA STUDIO WORKFLOW DEMONSTRATION")
    
    # Initialize database
    print_step("Initializing database...")
    init_db()
    
    # Setup LLM client
    print_step("Setting up LLM client...")
    client = setup_client()
    
    # Step 1: Create project
    project_id = step1_create_project()
    
    # Step 2: Ingest content
    ingest_job_id, processed_file = step2_ingest(project_id, TEST_CONTENT)
    
    if not processed_file:
        print_error("Ingestion failed. Exiting workflow.")
        return 1
    
    # Step 3: Generate QA pairs
    create_job_id, qa_file, qa_pairs = step3_create_qa_pairs(project_id, processed_file, client, CONFIG)
    
    if not qa_pairs:
        print_error("QA pair generation failed. Exiting workflow.")
        return 1
    
    # Step 4: Curate QA pairs
    curate_job_id, curated_file, curated_pairs = step4_curate_qa_pairs(project_id, qa_file, client, CONFIG)
    
    if not curated_pairs:
        print_error("Curation failed. Exiting workflow.")
        return 1
    
    # Step 5: Export data
    export_job_id, final_file = step5_export_data(project_id, curated_file, CONFIG)
    
    if not final_file:
        print_error("Export failed. Exiting workflow.")
        return 1
    
    # Summary
    print_header("WORKFLOW SUMMARY")
    print_result(f"Project ID: {project_id}")
    print_result(f"Ingest Job ID: {ingest_job_id}")
    print_result(f"Create Job ID: {create_job_id}")
    print_result(f"Curate Job ID: {curate_job_id}")
    print_result(f"Export Job ID: {export_job_id}")
    print_result(f"Starting with {len(TEST_CONTENT)} characters of text")
    print_result(f"Generated {len(qa_pairs)} initial QA pairs")
    print_result(f"Curated to {len(curated_pairs)} high-quality QA pairs")
    print_result(f"Exported to {final_file} in {CONFIG['workflow']['output_format']} format")
    
    print("\nYou can view the files in the data directory and query the database for job details.")
    
    return 0

if __name__ == "__main__":
    sys.exit(run_workflow())