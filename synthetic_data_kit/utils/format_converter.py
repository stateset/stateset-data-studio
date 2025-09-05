"""
Format converter utilities for saving data in different formats.
"""
import os
import json
import csv
import logging
from typing import List, Dict, Any, Optional, Union
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("format_converter")

def to_jsonl(qa_pairs: List[Dict[str, Any]], output_path: str) -> str:
    """
    Convert QA pairs to JSONL format and save to file.
    
    Args:
        qa_pairs: List of QA pair dictionaries
        output_path: Path to save output file
        
    Returns:
        Path to the output file
    """
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # If output_path doesn't have the jsonl extension, add it
    if not output_path.endswith('.jsonl'):
        output_path = f"{output_path}.jsonl"
    
    # Write each pair as a JSON line
    with open(output_path, 'w', encoding='utf-8') as f:
        for pair in qa_pairs:
            f.write(json.dumps(pair) + '\n')
    
    logger.info(f"Saved {len(qa_pairs)} QA pairs to {output_path}")
    return output_path

def to_alpaca(qa_pairs: List[Dict[str, Any]], output_path: str) -> str:
    """
    Convert QA pairs to Alpaca instruction format and save as JSONL.
    
    Args:
        qa_pairs: List of QA pair dictionaries
        output_path: Path to save output file
        
    Returns:
        Path to the output file
    """
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # If output_path doesn't have the jsonl extension, add it
    if not output_path.endswith('.jsonl'):
        output_path = f"{output_path}.jsonl"
    
    # Convert to Alpaca format
    alpaca_data = []
    for pair in qa_pairs:
        alpaca_item = {
            "instruction": pair["question"],
            "input": "",
            "output": pair["answer"]
        }
        alpaca_data.append(alpaca_item)
    
    # Write each instruction as a JSON line
    with open(output_path, 'w', encoding='utf-8') as f:
        for item in alpaca_data:
            f.write(json.dumps(item) + '\n')
    
    logger.info(f"Saved {len(alpaca_data)} instructions to {output_path}")
    return output_path

def to_fine_tuning(qa_pairs: List[Dict[str, Any]], output_path: str) -> str:
    """
    Convert QA pairs to OpenAI fine-tuning format and save as JSONL.
    
    Args:
        qa_pairs: List of QA pair dictionaries
        output_path: Path to save output file
        
    Returns:
        Path to the output file
    """
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # If output_path doesn't have the jsonl extension, add it
    if not output_path.endswith('.jsonl'):
        output_path = f"{output_path}.jsonl"
    
    # Convert to OpenAI fine-tuning format
    ft_data = []
    for pair in qa_pairs:
        ft_item = {
            "messages": [
                {"role": "system", "content": "You are a helpful assistant that provides accurate and informative answers."},
                {"role": "user", "content": pair["question"]},
                {"role": "assistant", "content": pair["answer"]}
            ]
        }
        ft_data.append(ft_item)
    
    # Write each conversation as a JSON line
    with open(output_path, 'w', encoding='utf-8') as f:
        for item in ft_data:
            f.write(json.dumps(item) + '\n')
    
    logger.info(f"Saved {len(ft_data)} conversations to {output_path}")
    return output_path

def to_chatml(qa_pairs: List[Dict[str, Any]], output_path: str) -> str:
    """
    Convert QA pairs to ChatML format and save as JSONL.
    
    Args:
        qa_pairs: List of QA pair dictionaries
        output_path: Path to save output file
        
    Returns:
        Path to the output file
    """
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # If output_path doesn't have the jsonl extension, add it
    if not output_path.endswith('.jsonl'):
        output_path = f"{output_path}.jsonl"
    
    # Convert to ChatML format (similar to OpenAI fine-tuning, but with specific tags)
    chatml_data = []
    for pair in qa_pairs:
        chatml_item = {
            "messages": [
                {"role": "system", "content": "You are a helpful assistant that provides accurate and informative answers."},
                {"role": "user", "content": pair["question"]},
                {"role": "assistant", "content": pair["answer"]}
            ]
        }
        chatml_data.append(chatml_item)
    
    # Write each conversation as a JSON line
    with open(output_path, 'w', encoding='utf-8') as f:
        for item in chatml_data:
            f.write(json.dumps(item) + '\n')
    
    logger.info(f"Saved {len(chatml_data)} conversations to {output_path}")
    return output_path

def to_csv(qa_pairs: List[Dict[str, Any]], output_path: str) -> str:
    """
    Convert QA pairs to CSV format and save to file.
    
    Args:
        qa_pairs: List of QA pair dictionaries
        output_path: Path to save output file
        
    Returns:
        Path to the output file
    """
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # If output_path doesn't have the csv extension, add it
    if not output_path.endswith('.csv'):
        output_path = f"{output_path}.csv"
    
    # Write to CSV
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        fieldnames = ['question', 'answer']
        
        # Add extra fields if present in the first pair
        if qa_pairs:
            extra_fields = [key for key in qa_pairs[0].keys() if key not in fieldnames]
            fieldnames.extend(extra_fields)
        
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for pair in qa_pairs:
            # Only include known fields
            row = {key: pair.get(key, '') for key in fieldnames}
            writer.writerow(row)
    
    logger.info(f"Saved {len(qa_pairs)} QA pairs to {output_path}")
    return output_path

def to_hf_dataset(data: List[Dict[str, Any]], output_path: str) -> str:
    """
    Convert data to a Hugging Face dataset format.
    
    Args:
        data: List of data dictionaries
        output_path: Path to save output dataset
        
    Returns:
        Path to the output dataset
    """
    try:
        from datasets import Dataset
        
        # Create Hugging Face dataset
        dataset = Dataset.from_dict({
            key: [item.get(key, None) for item in data] 
            for key in data[0].keys()
        })
        
        # Save dataset
        dataset.save_to_disk(output_path)
        
        logger.info(f"Saved {len(data)} records to HF dataset at {output_path}")
        return output_path
    except ImportError:
        logger.error("datasets library not installed. Please install it with: pip install datasets")
        
        # Fallback to saving as JSON
        fallback_path = f"{output_path}.json"
        with open(fallback_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Saved {len(data)} records to {fallback_path} (fallback to JSON)")
        return fallback_path