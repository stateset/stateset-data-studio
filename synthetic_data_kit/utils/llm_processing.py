"""
Utilities for processing LLM outputs and handling text formats.
"""
import json
import re
import logging
from typing import List, Dict, Any, Optional, Union

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("llm_processing")

def extract_json(text: str) -> Any:
    """
    Extract JSON from text that might contain additional content.
    
    Args:
        text: Text that may contain JSON
        
    Returns:
        Parsed JSON object or None if parsing fails
    """
    # Try to find JSON in the text
    json_match = re.search(r'```json\s*([\s\S]*?)\s*```', text)
    if json_match:
        json_str = json_match.group(1)
    else:
        # Try to find array/object without code blocks
        json_match = re.search(r'(\[[\s\S]*\]|\{[\s\S]*\})', text)
        if json_match:
            json_str = json_match.group(1)
        else:
            json_str = text
    
    # Try to parse JSON
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        # Try to clean up the string and parse again
        try:
            # Remove any trailing commas
            json_str = re.sub(r',\s*([}\]])', r'\1', json_str)
            return json.loads(json_str)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON from text: {text[:100]}...")
            return None

def clean_text_chunks(chunks: List[str]) -> List[str]:
    """
    Clean and normalize text chunks.
    
    Args:
        chunks: List of text chunks
        
    Returns:
        Cleaned text chunks
    """
    cleaned_chunks = []
    for chunk in chunks:
        # Remove excessive whitespace
        cleaned = re.sub(r'\s+', ' ', chunk).strip()
        
        if cleaned:
            cleaned_chunks.append(cleaned)
    
    return cleaned_chunks

def split_text(text: str, chunk_size: int, overlap: int = 0) -> List[str]:
    """
    Split text into chunks of specified size with optional overlap.
    
    Args:
        text: Text to split
        chunk_size: Maximum chunk size in characters
        overlap: Number of characters to overlap between chunks
        
    Returns:
        List of text chunks
    """
    # If text is shorter than chunk size, return as is
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        # Determine end of chunk
        end = start + chunk_size
        
        # If this is not the last chunk, try to break at a sentence boundary
        if end < len(text):
            # Look for sentence boundaries
            sentence_end = max(
                text.rfind('. ', start, end),
                text.rfind('? ', start, end),
                text.rfind('! ', start, end),
                text.rfind('\n', start, end)
            )
            
            # If found, use it; otherwise use the exact chunk size
            if sentence_end > start:
                end = sentence_end + 1  # Include the period
        
        # Add chunk to list
        chunks.append(text[start:end].strip())
        
        # Update start position for next chunk
        start = end - overlap if overlap > 0 else end
    
    return chunks

def parse_qa_pairs(response: str) -> List[Dict[str, str]]:
    """
    Parse question-answer pairs from LLM response.
    
    Args:
        response: LLM response text
        
    Returns:
        List of dictionaries with question and answer fields
    """
    # Try to parse as JSON first
    qa_pairs = extract_json(response)
    
    if qa_pairs and isinstance(qa_pairs, list):
        # Validate format
        valid_pairs = []
        for pair in qa_pairs:
            if isinstance(pair, dict) and "question" in pair and "answer" in pair:
                valid_pairs.append({
                    "question": pair["question"],
                    "answer": pair["answer"]
                })
        
        if valid_pairs:
            return valid_pairs
    
    # If JSON parsing fails, try to extract using patterns
    logger.info("JSON parsing failed, trying pattern matching")
    
    # Pattern for "Q: ... A: ..." format
    pattern = r'(?:Q|Question)(?:uestion)?[:\s]+([^\n]+)(?:\n|.)+?(?:A|Answer)(?:nswer)?[:\s]+([^\n]+(?:\n[^\n]+)*)'
    matches = re.finditer(pattern, response, re.IGNORECASE | re.MULTILINE)
    
    pairs = []
    for match in matches:
        pairs.append({
            "question": match.group(1).strip(),
            "answer": match.group(2).strip()
        })
    
    if pairs:
        return pairs
    
    # Also try to match when the question-answer pairs are preceded by numbers
    pattern = r'(?:\d+[\.\)]\s+)?(?:Q|Question)(?:uestion)?[:\s]+([^\n]+)(?:\n|.)+?(?:A|Answer)(?:nswer)?[:\s]+([^\n]+(?:\n[^\n]+)*)'
    matches = re.finditer(pattern, response, re.IGNORECASE | re.MULTILINE)
    
    for match in matches:
        pairs.append({
            "question": match.group(1).strip(),
            "answer": match.group(2).strip()
        })
    
    if pairs:
        return pairs
    
    # Check for numbered list format
    pattern = r'(?:\d+\.\s+|\-\s+|\*\s+)([^\n]+\?)\s*\n+([^\n]+(?:\n[^\n\d\-\*]+)*)'
    matches = re.finditer(pattern, response, re.MULTILINE)
    
    for match in matches:
        # Check if this looks like a Q&A pair
        text = match.group(1).strip()
        if text.endswith('?'):  # It's likely a question
            pairs.append({
                "question": text,
                "answer": match.group(2).strip()
            })
    
    # If we still have no pairs, try an even more lenient pattern for numbered paragraphs
    if not pairs:
        pattern = r'(?:\d+\.\s+)([^\n]+)(?:\n|.)+?(?:\d+\.\s+|$)'
        sections = re.split(pattern, response)[1:]
        
        for i in range(0, len(sections) - 1, 2):
            if i + 1 < len(sections):
                question = sections[i].strip()
                answer = sections[i + 1].strip()
                
                # Only include it if it looks like a question
                if '?' in question:
                    pairs.append({
                        "question": question,
                        "answer": answer
                    })
    
    return pairs

def parse_ratings(response: str, original_pairs: List[Dict[str, str]]) -> List[Dict[str, Union[str, float]]]:
    """
    Parse quality ratings from LLM response.
    
    Args:
        response: LLM response text
        original_pairs: Original QA pairs for fallback
        
    Returns:
        List of dictionaries with question, answer, rating, and justification fields
    """
    # Try to parse as JSON first
    rated_pairs = extract_json(response)
    
    if rated_pairs and isinstance(rated_pairs, list):
        # Validate format
        valid_pairs = []
        for pair in rated_pairs:
            if isinstance(pair, dict) and "question" in pair and "answer" in pair and "rating" in pair:
                # Ensure rating is a float
                try:
                    rating = float(pair["rating"])
                    pair["rating"] = rating
                    valid_pairs.append(pair)
                except (ValueError, TypeError):
                    # If rating can't be converted to float, skip this pair
                    logger.warning(f"Invalid rating in pair: {pair}")
        
        if valid_pairs:
            return valid_pairs
    
    # If JSON parsing fails, try to extract using patterns
    logger.info("JSON parsing failed, trying pattern matching")
    
    # Use original QA pairs as fallback
    result = []
    for i, pair in enumerate(original_pairs):
        # Try to find rating pattern for this pair
        question_text = re.escape(pair["question"][:30])  # Use start of question for matching
        pattern = fr'{question_text}.*?(?:rating|score).*?(\d+(?:\.\d+)?)'
        match = re.search(pattern, response, re.IGNORECASE | re.DOTALL)
        
        if match:
            rating = float(match.group(1))
            result.append({
                "question": pair["question"],
                "answer": pair["answer"],
                "rating": rating
            })
        else:
            # If no match, look for rating patterns and assign sequentially
            pattern = r'(?:rating|score)[:\s]+(\d+(?:\.\d+)?)'
            ratings = re.findall(pattern, response, re.IGNORECASE)
            
            if i < len(ratings):
                result.append({
                    "question": pair["question"],
                    "answer": pair["answer"],
                    "rating": float(ratings[i])
                })
            else:
                # No rating found, assign default
                logger.warning(f"Could not find rating for pair {i+1}, assigning default")
                result.append({
                    "question": pair["question"],
                    "answer": pair["answer"],
                    "rating": 5.0
                })
    
    return result

def parse_cot_examples(response: str) -> List[Dict[str, str]]:
    """
    Parse chain-of-thought examples from LLM response.
    
    Args:
        response: LLM response text
        
    Returns:
        List of dictionaries with question, reasoning, and answer fields
    """
    # Try to parse as JSON first
    cot_examples = extract_json(response)
    
    if cot_examples and isinstance(cot_examples, list):
        # Validate format
        valid_examples = []
        for example in cot_examples:
            if isinstance(example, dict) and "question" in example and "reasoning" in example and "answer" in example:
                valid_examples.append({
                    "question": example["question"],
                    "reasoning": example["reasoning"],
                    "answer": example["answer"]
                })
        
        if valid_examples:
            return valid_examples
    
    # If JSON parsing fails, try to extract using patterns
    logger.info("JSON parsing failed, trying pattern matching")
    
    # Pattern for "Question: ... Reasoning: ... Answer: ..." format
    pattern = r'(?:Q|Question)(?:uestion)?[:\s]+([^\n]+)(?:\n|.)+?(?:Reasoning|Thoughts|Steps)[:\s]+([^\n]+(?:\n[^\n]+)*)(?:\n|.)+?(?:A|Answer)[:\s]+([^\n]+(?:\n[^\n]+)*)'
    matches = re.finditer(pattern, response, re.IGNORECASE | re.MULTILINE)
    
    examples = []
    for match in matches:
        examples.append({
            "question": match.group(1).strip(),
            "reasoning": match.group(2).strip(),
            "answer": match.group(3).strip()
        })
    
    return examples

def convert_to_conversation_format(qa_pairs: List[Dict[str, str]]) -> List[List[Dict[str, str]]]:
    """
    Convert QA pairs to conversation format for fine-tuning.
    
    Args:
        qa_pairs: List of QA pair dictionaries
        
    Returns:
        List of conversations (each a list of messages)
    """
    conversations = []
    
    for pair in qa_pairs:
        conversation = [
            {"role": "system", "content": "You are a helpful assistant that provides accurate and informative answers."},
            {"role": "user", "content": pair["question"]},
            {"role": "assistant", "content": pair["answer"]}
        ]
        conversations.append(conversation)
    
    return conversations