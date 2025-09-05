"""
Question-Answer generator module.
"""
import os
import logging
import time
import json
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
from tqdm import tqdm

from synthetic_data_kit.models.llm_client import LLMClient
from synthetic_data_kit.utils.config import get_generation_config, get_prompt
from synthetic_data_kit.utils.llm_processing import split_text, parse_qa_pairs, clean_text_chunks

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("qa_generator")

# Enable verbose logging via environment variable
VERBOSE = os.environ.get('SDK_VERBOSE', 'false').lower() == 'true'

class QAGenerator:
    """
    Generator for question-answer pairs from text content.
    """
    
    def __init__(
        self,
        client: LLMClient,
        config_path: Optional[Path] = None
    ):
        """
        Initialize the QA generator.
        
        Args:
            client: LLM client instance
            config_path: Path to configuration file
        """
        self.client = client
        self.config_path = config_path
        
        # Get generation configuration
        self.generation_config = get_generation_config(client.config)
        
        # Set default parameters
        self.chunk_size = self.generation_config.get("chunk_size", 4000)
        self.overlap = self.generation_config.get("overlap", 0)
        self.temperature = self.generation_config.get("temperature", 0.7)
        self.num_pairs = self.generation_config.get("num_pairs", 25)
        
        if VERBOSE:
            logger.info(f"Initialized QA generator with chunk size: {self.chunk_size}")
            logger.info(f"Temperature: {self.temperature}")
            logger.info(f"Default pairs per document: {self.num_pairs}")
    
    def generate_qa_pairs(
        self,
        text: str,
        num_pairs: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> List[Dict[str, str]]:
        """
        Generate question-answer pairs from text.
        
        Args:
            text: Source text content
            num_pairs: Number of QA pairs to generate
            temperature: LLM temperature parameter
            
        Returns:
            List of QA pair dictionaries
        """
        # Use default parameters if not provided
        if num_pairs is None:
            num_pairs = self.num_pairs
        
        if temperature is None:
            temperature = self.temperature
        
        # Get QA generation prompt
        prompt_template = get_prompt(self.client.config, "qa_generation")
        
        # Format prompt with text and number of pairs
        prompt = prompt_template.format(
            context=text,  # Using context instead of text to match the prompt template
            num_pairs=num_pairs
        )
        
        # Create message for the LLM
        messages = [
            {"role": "system", "content": prompt}
        ]
        
        if VERBOSE:
            logger.info(f"Generating {num_pairs} QA pairs for text of length {len(text)}")
        
        # Get completion from LLM
        response = self.client.chat_completion(
            messages=messages,
            temperature=temperature
        )
        
        # Parse QA pairs from response
        qa_pairs = parse_qa_pairs(response)
        
        if VERBOSE:
            logger.info(f"Generated {len(qa_pairs)} QA pairs")
        
        return qa_pairs
    
    def process_document(
        self,
        text: str,
        num_pairs: Optional[int] = None,
        chunk_size: Optional[int] = None,
        overlap: Optional[int] = None,
        temperature: Optional[float] = None,
        verbose: bool = False
    ) -> Dict[str, Any]:
        """
        Process a document to generate QA pairs.
        
        Args:
            text: Document text content
            num_pairs: Total number of QA pairs to generate
            chunk_size: Size of text chunks to process
            overlap: Overlap between chunks
            temperature: LLM temperature parameter
            verbose: Show detailed progress
            
        Returns:
            Dictionary with QA pairs and summary
        """
        # Use default parameters if not provided
        if num_pairs is None:
            num_pairs = self.num_pairs
        
        if chunk_size is None:
            chunk_size = self.chunk_size
        
        if overlap is None:
            overlap = self.overlap
        
        if temperature is None:
            temperature = self.temperature
        
        # First, generate a summary for context
        summary = self.generate_summary(text, temperature)
        
        # Split text into chunks
        chunks = split_text(text, chunk_size, overlap)
        
        # Calculate pairs per chunk to achieve target number of pairs
        pairs_per_chunk = max(1, num_pairs // len(chunks))
        remaining_pairs = num_pairs % len(chunks)
        
        if VERBOSE or verbose:
            logger.info(f"Processing document with {len(chunks)} chunks")
            logger.info(f"Generating approximately {pairs_per_chunk} pairs per chunk")
            logger.info(f"Plus {remaining_pairs} extra pairs for the first chunks")
        
        # Generate QA pairs for each chunk
        all_pairs = []
        
        for i, chunk in enumerate(tqdm(chunks, desc="Generating QA pairs", disable=not (VERBOSE or verbose))):
            # Calculate pairs for this chunk
            chunk_pairs = pairs_per_chunk
            if i < remaining_pairs:
                chunk_pairs += 1
            
            # Skip if no pairs to generate
            if chunk_pairs <= 0:
                continue
            
            # Generate pairs for this chunk
            try:
                pairs = self.generate_qa_pairs(
                    text=chunk,
                    num_pairs=chunk_pairs,
                    temperature=temperature
                )
                
                all_pairs.extend(pairs)
                
                # Short delay to avoid rate limiting
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error generating QA pairs for chunk {i}: {str(e)}")
                # Continue with next chunk
        
        if VERBOSE or verbose:
            logger.info(f"Generated a total of {len(all_pairs)} QA pairs")
        
        # Prepare result
        result = {
            "summary": summary,
            "qa_pairs": all_pairs
        }
        
        return result
    
    def generate_summary(
        self,
        text: str,
        temperature: Optional[float] = None
    ) -> str:
        """
        Generate a summary of the text.
        
        Args:
            text: Text to summarize
            temperature: LLM temperature parameter
            
        Returns:
            Summary text
        """
        if temperature is None:
            temperature = self.temperature
        
        # Trim text if too long
        if len(text) > self.chunk_size * 1.5:
            # Use first and last chunks for summarization
            first_chunk = text[:self.chunk_size]
            last_chunk = text[-self.chunk_size:]
            text_for_summary = f"{first_chunk}\n\n[...content truncated...]\n\n{last_chunk}"
        else:
            text_for_summary = text
        
        # Get summarization prompt
        prompt_template = get_prompt(self.client.config, "summarization")
        
        # Format prompt with text
        prompt = prompt_template.format(
            context=text_for_summary,  # Using context instead of text to match template
            text=text_for_summary      # Include both for backwards compatibility
        )
        
        # Create message for the LLM
        messages = [
            {"role": "system", "content": prompt}
        ]
        
        if VERBOSE:
            logger.info(f"Generating summary for text of length {len(text)}")
        
        # Get completion from LLM
        response = self.client.chat_completion(
            messages=messages,
            temperature=temperature
        )
        
        if VERBOSE:
            logger.info(f"Generated summary of length {len(response)}")
        
        return response