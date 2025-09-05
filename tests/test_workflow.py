#!/usr/bin/env python
"""
Script to test the full StateSet Data Studio workflow using the Llama API.
"""
import os
import json
import sys
import time
from synthetic_data_kit.models.llm_client import LLMClient

# Test file content
TEST_CONTENT = """
This is a test document for synthetic data generation.
It contains some test content that can be used to generate question-answer pairs.
The synthetic-data-kit tool is designed to process documents and create training data for language models.
This process involves several steps:
1. Ingesting and preprocessing documents
2. Generating synthetic data with LLMs
3. Curating the generated data for quality
4. Saving the curated data in appropriate formats for model training.
"""

# Workflow configuration
CONFIG = {
    "api_type": "llama",
    "llama": {
        "api_key": "llama-api-key",
        "model": "Llama-4-Maverick-17B-128E-Instruct-FP8"
    }
}

def setup_client():
    """Set up LLMClient with Llama API configuration"""
    client = LLMClient()
    client.api_type = CONFIG["api_type"]
    client.api_base = "https://api.llama.com/v1"
    client.model = CONFIG["llama"]["model"]
    client.api_key = CONFIG["llama"]["api_key"]
    return client

def step1_create_qa_pairs(client, input_text, num_pairs=3):
    """Generate QA pairs using the Llama API"""
    print(f"\n====== STEP 1: CREATING {num_pairs} QA PAIRS ======")
    
    prompt = [
        {"role": "system", "content": "You are an AI trained to generate high-quality question-answer pairs."},
        {"role": "user", "content": f"""
Generate {num_pairs} high-quality question-answer pairs from the following content.
Each pair should test understanding of different aspects of the content.
Format your response as a JSON array where each object has a 'question' and 'answer' field.

CONTENT:
{input_text}
"""}
    ]
    
    print(f"Sending request to generate {num_pairs} QA pairs...")
    response = client.chat_completion(
        messages=prompt,
        temperature=0.3,
        max_tokens=1500
    )
    
    print("\nGenerated QA pairs:")
    print(response)
    
    # Extract JSON from response
    try:
        # Look for JSON content between triple backticks
        json_content = response
        if "```json" in response:
            json_content = response.split("```json")[1].split("```")[0].strip()
        elif "```" in response:
            json_content = response.split("```")[1].split("```")[0].strip()
            
        qa_pairs = json.loads(json_content)
        
        # Save to file
        output_file = "generated_qa_pairs.json"
        with open(output_file, "w") as f:
            json.dump(qa_pairs, f, indent=2)
            
        print(f"\nSaved {len(qa_pairs)} QA pairs to {output_file}")
        return output_file, qa_pairs
    except Exception as e:
        print(f"Error extracting JSON from response: {str(e)}")
        # Fallback: save raw response
        with open("raw_response.txt", "w") as f:
            f.write(response)
        print("Saved raw response to raw_response.txt")
        return None, None

def step2_curate_qa_pairs(client, qa_pairs, threshold=7.0):
    """Curate QA pairs for quality using the Llama API"""
    print(f"\n====== STEP 2: CURATING QA PAIRS (Threshold: {threshold}) ======")
    
    if not qa_pairs:
        print("No QA pairs to curate")
        return None
    
    # For each QA pair, evaluate its quality
    curated_pairs = []
    
    for i, pair in enumerate(qa_pairs):
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
        
        print(f"\nEvaluating pair {i+1}/{len(qa_pairs)}...")
        response = client.chat_completion(
            messages=prompt,
            temperature=0.1,
            max_tokens=300
        )
        
        print(f"Evaluation: {response}")
        
        # Extract score from response (first number found)
        import re
        score_match = re.search(r'(\d+(\.\d+)?)', response)
        if score_match:
            score = float(score_match.group(1))
            if score >= threshold:
                pair['score'] = score
                curated_pairs.append(pair)
                print(f"✅ Pair meets threshold with score {score}")
            else:
                print(f"❌ Pair below threshold with score {score}")
        else:
            print("Could not extract score, skipping pair")
    
    # Save curated pairs
    if curated_pairs:
        output_file = "curated_qa_pairs.json"
        with open(output_file, "w") as f:
            json.dump(curated_pairs, f, indent=2)
            
        print(f"\nSaved {len(curated_pairs)} curated QA pairs to {output_file}")
        return output_file, curated_pairs
    else:
        print("No pairs met the quality threshold")
        return None, None

def step3_save_as_format(curated_pairs, format='jsonl'):
    """Save curated pairs in the specified format"""
    print(f"\n====== STEP 3: SAVING IN {format.upper()} FORMAT ======")
    
    if not curated_pairs:
        print("No curated pairs to save")
        return None
    
    output_file = f"final_qa_pairs.{format}"
    
    if format == 'jsonl':
        with open(output_file, "w") as f:
            for pair in curated_pairs:
                f.write(json.dumps(pair) + "\n")
    elif format == 'json':
        with open(output_file, "w") as f:
            json.dump(curated_pairs, f, indent=2)
    elif format == 'csv':
        import csv
        with open(output_file, "w", newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["question", "answer", "score"])
            for pair in curated_pairs:
                writer.writerow([pair["question"], pair["answer"], pair.get("score", "")])
    else:
        print(f"Unsupported format: {format}")
        return None
        
    print(f"Successfully saved curated QA pairs to {output_file}")
    return output_file

def main():
    """Run the full workflow"""
    print("Testing synthetic data workflow with Llama API integration...")
    
    # Set up LLM client
    client = setup_client()
    
    # Step 1: Create QA pairs
    qa_file, qa_pairs = step1_create_qa_pairs(client, TEST_CONTENT, num_pairs=3)
    if not qa_pairs:
        print("Failed to create QA pairs. Exiting workflow.")
        return 1
    
    # Step 2: Curate QA pairs
    curated_file, curated_pairs = step2_curate_qa_pairs(client, qa_pairs, threshold=5.0)
    if not curated_pairs:
        print("Failed to curate QA pairs. Exiting workflow.")
        return 1
    
    # Step 3: Save in desired format
    final_file = step3_save_as_format(curated_pairs, format='jsonl')
    if not final_file:
        print("Failed to save in the desired format.")
        return 1
    
    print("\n✨ Workflow completed successfully!")
    print(f"Input: {len(TEST_CONTENT)} characters of text")
    print(f"Generated: {len(qa_pairs)} QA pairs")
    print(f"Curated: {len(curated_pairs)} high-quality QA pairs")
    print(f"Final output: {final_file}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())