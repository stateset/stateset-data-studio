#!/usr/bin/env python
"""
Workflow demonstration script for StateSet Data Studio using the Llama API.
This script shows the complete end-to-end workflow of:
1. Ingesting content
2. Creating QA pairs
3. Curating for quality
4. Saving in desired format
"""
import os
import json
import sys
import time
import datetime
from synthetic_data_kit.models.llm_client import LLMClient

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
# Synthetic Data Generation

Synthetic data refers to artificially created data rather than data obtained through direct measurement or observation. It is generated using algorithms and models to mimic the characteristics of real data. This type of data is increasingly important in machine learning, testing, and privacy-preserving applications.

## Benefits of Synthetic Data

1. **Privacy Protection**: Synthetic data doesn't contain sensitive personal information, making it useful for sharing and collaboration without privacy concerns.

2. **Cost Reduction**: Collecting real-world data can be expensive and time-consuming. Synthetic data offers a cost-effective alternative.

3. **Data Augmentation**: Synthetic data can supplement limited datasets, helping to improve model performance and reduce bias.

4. **Edge Case Testing**: Synthetic data can generate rare but critical scenarios that might be difficult to capture in real-world data collection.

## Techniques for Generating Synthetic Data

Several approaches are used to create synthetic data:

- **Statistical Methods**: Using statistical distributions to generate data that matches the statistical properties of real data.

- **Generative Adversarial Networks (GANs)**: Neural networks that learn to generate data that is indistinguishable from real data.

- **Variational Autoencoders (VAEs)**: Neural networks that learn the underlying distribution of data and generate new samples.

- **Agent-Based Modeling**: Simulating the behavior of individual agents to generate data based on defined rules and interactions.

## Challenges

Despite its benefits, synthetic data faces several challenges:

- Ensuring the generated data accurately represents real-world patterns
- Maintaining statistical fidelity while preserving privacy
- Avoiding the introduction of biases or artifacts in the generation process
- Validating the quality and usefulness of synthetic data

Researchers continue to develop more sophisticated methods to address these challenges, making synthetic data an increasingly valuable resource in data science and machine learning.
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

def save_to_file(data, filename):
    """Save data to a file"""
    with open(filename, 'w') as f:
        f.write(data)
    print_result(f"Saved to {filename}")

# ----------------- Workflow Steps -----------------
def step1_ingest(content):
    """Simulate document ingestion"""
    print_header("STEP 1: INGESTION")
    print_step("Processing input content...")
    
    # Analyze content
    char_count = len(content)
    word_count = len(content.split())
    line_count = len(content.splitlines())
    
    print_result("Content statistics", 
                f"Characters: {char_count}, Words: {word_count}, Lines: {line_count}")
    
    # Save content to a file
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"workflow_input_{timestamp}.txt"
    
    with open(filename, 'w') as f:
        f.write(content)
    
    print_result(f"Ingestion complete. Content saved to {filename}")
    return filename

def step2_create_qa_pairs(client, input_file, config):
    """Generate QA pairs from input content"""
    print_header("STEP 2: QA PAIR GENERATION")
    
    # Read the input file
    print_step(f"Reading content from {input_file}...")
    with open(input_file, 'r') as f:
        content = f.read()
    
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
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"generated_qa_pairs_{timestamp}.json"
        with open(output_file, "w") as f:
            json.dump(qa_pairs, f, indent=2)
            
        print_result(f"Generated {len(qa_pairs)} QA pairs")
        
        # Show sample
        if qa_pairs and VERBOSE:
            print("\nSample QA pair:")
            print(f"  Q: {qa_pairs[0]['question']}")
            print(f"  A: {qa_pairs[0]['answer'][:100]}...")
        
        return output_file, qa_pairs
    
    except Exception as e:
        print_error(f"Error generating QA pairs: {str(e)}")
        return None, None

def step3_curate_qa_pairs(client, qa_pairs, config):
    """Curate QA pairs for quality"""
    print_header("STEP 3: CURATION")
    
    if not qa_pairs:
        print_error("No QA pairs to curate")
        return None, None
    
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
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"curated_qa_pairs_{timestamp}.json"
        with open(output_file, "w") as f:
            json.dump(curated_pairs, f, indent=2)
            
        print_result(f"Saved {len(curated_pairs)} curated QA pairs to {output_file}")
        print_result(f"Removed {len(qa_pairs) - len(curated_pairs)} low-quality pairs")
        return output_file, curated_pairs
    else:
        print_error("No pairs met the quality threshold")
        return None, None

def step4_export_data(curated_pairs, config):
    """Save curated pairs in the desired format"""
    print_header("STEP 4: EXPORT")
    
    if not curated_pairs:
        print_error("No curated pairs to export")
        return None
    
    format_type = config["workflow"]["output_format"]
    print_step(f"Exporting {len(curated_pairs)} QA pairs in {format_type.upper()} format...")
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"final_qa_data_{timestamp}.{format_type}"
    
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
        print_error(f"Unsupported format: {format_type}")
        return None
        
    print_result(f"Successfully exported data to {output_file}")
    return output_file

def run_workflow():
    """Run the complete workflow"""
    print_header("SYNTHETIC DATA WORKFLOW DEMONSTRATION")
    
    print_step("Setting up LLM client...")
    client = setup_client()
    
    # Step 1: Ingest content
    input_file = step1_ingest(TEST_CONTENT)
    
    # Step 2: Generate QA pairs
    qa_file, qa_pairs = step2_create_qa_pairs(client, input_file, CONFIG)
    if not qa_pairs:
        print_error("Failed to create QA pairs. Exiting workflow.")
        return 1
    
    # Step 3: Curate QA pairs
    curated_file, curated_pairs = step3_curate_qa_pairs(client, qa_pairs, CONFIG)
    if not curated_pairs:
        print_error("Failed to curate QA pairs. Exiting workflow.")
        return 1
    
    # Step 4: Export in desired format
    final_file = step4_export_data(curated_pairs, CONFIG)
    if not final_file:
        print_error("Failed to export data. Exiting workflow.")
        return 1
    
    # Summary
    print_header("WORKFLOW SUMMARY")
    print_result(f"Starting with {len(TEST_CONTENT)} characters of text")
    print_result(f"Generated {len(qa_pairs)} initial QA pairs")
    print_result(f"Curated to {len(curated_pairs)} high-quality QA pairs")
    print_result(f"Exported to {final_file} in {CONFIG['workflow']['output_format']} format")
    
    return 0

if __name__ == "__main__":
    sys.exit(run_workflow())