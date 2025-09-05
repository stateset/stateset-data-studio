import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

def extract_stats(path: Path) -> str:
    """Extract statistics from file based on file type and return as JSON string"""
    if not path.exists():
        return json.dumps({"error": "File not found"})
    
    stats = {
        "file_size": path.stat().st_size,
        "last_modified": datetime.fromtimestamp(path.stat().st_mtime).isoformat(),
        "path": str(path),
        "filename": path.name,
    }
    
    # Extract stats based on file type
    if path.suffix == ".json":
        try:
            data = json.loads(path.read_text())
            if isinstance(data, list):
                stats["item_count"] = len(data)
                
                # For QA pairs JSON
                if data and isinstance(data[0], dict) and "question" in data[0]:
                    stats["qa_count"] = len(data)
                    
                    # Calculate average question/answer length
                    if data and "question" in data[0] and "answer" in data[0]:
                        q_lengths = [len(item["question"]) for item in data if "question" in item]
                        a_lengths = [len(item["answer"]) for item in data if "answer" in item]
                        
                        if q_lengths:
                            stats["avg_question_length"] = sum(q_lengths) / len(q_lengths)
                        if a_lengths:
                            stats["avg_answer_length"] = sum(a_lengths) / len(a_lengths)
                
            elif isinstance(data, dict):
                stats["keys"] = list(data.keys())
        except json.JSONDecodeError:
            stats["error"] = "Invalid JSON"
    
    elif path.suffix == ".jsonl":
        try:
            with open(path, "r") as f:
                lines = [line.strip() for line in f if line.strip()]
            
            stats["line_count"] = len(lines)
            
            # Try to parse first line
            if lines:
                sample = json.loads(lines[0])
                stats["sample_keys"] = list(sample.keys())
        except Exception as e:
            stats["error"] = f"Error parsing JSONL: {str(e)}"
    
    elif path.suffix in (".txt", ".md"):
        try:
            content = path.read_text()
            lines = content.split("\n")
            words = re.findall(r'\w+', content)
            
            stats["line_count"] = len(lines)
            stats["word_count"] = len(words)
            stats["char_count"] = len(content)
        except Exception as e:
            stats["error"] = f"Error analyzing text: {str(e)}"
    
    return json.dumps(stats)