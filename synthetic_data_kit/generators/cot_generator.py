"""
Chain-of-Thought generator module.
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
from synthetic_data_kit.utils.llm_processing import split_text, parse_cot_examples, extract_json

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("cot_generator")

# Enable verbose logging via environment variable
VERBOSE = os.environ.get('SDK_VERBOSE', 'false').lower() == 'true'

class COTGenerator:
    """
    Generator for chain-of-thought examples.
    """
    
    def __init__(
        self,
        client: LLMClient,
        config_path: Optional[Path] = None
    ):
        """
        Initialize the COT generator.
        
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
        self.num_examples = self.generation_config.get("num_pairs", 5)
        
        if VERBOSE:
            logger.info(f"Initialized COT generator with chunk size: {self.chunk_size}")
            logger.info(f"Temperature: {self.temperature}")
            logger.info(f"Default examples per document: {self.num_examples}")
    
    def generate_cot_examples(
        self,
        text: str,
        num_examples: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> List[Dict[str, str]]:
        """
        Generate chain-of-thought examples from text.
        
        Args:
            text: Source text content
            num_examples: Number of COT examples to generate
            temperature: LLM temperature parameter
            
        Returns:
            List of COT example dictionaries
        """
        # Use default parameters if not provided
        if num_examples is None:
            num_examples = self.num_examples
        
        if temperature is None:
            temperature = self.temperature
        
        # Get COT generation prompt
        prompt_template = get_prompt(self.client.config, "cot_generation")
        
        # Format prompt with text and number of examples
        prompt = prompt_template.format(
            context=text,  # Using context instead of text to match template
            num_pairs=num_examples,  # Using num_pairs to match template
            num_examples=num_examples  # Keeping for backwards compatibility
        )
        
        # Create message for the LLM
        messages = [
            {"role": "system", "content": prompt}
        ]
        
        if VERBOSE:
            logger.info(f"Generating {num_examples} COT examples for text of length {len(text)}")
        
        # Get completion from LLM
        response = self.client.chat_completion(
            messages=messages,
            temperature=temperature
        )
        
        # Parse COT examples from response
        cot_examples = parse_cot_examples(response)
        
        if VERBOSE:
            logger.info(f"Generated {len(cot_examples)} COT examples")
        
        return cot_examples
    
    def process_document(
        self,
        text: str,
        num_examples: Optional[int] = None,
        chunk_size: Optional[int] = None,
        overlap: Optional[int] = None,
        temperature: Optional[float] = None,
        include_simple_steps: bool = False
    ) -> Dict[str, Any]:
        """
        Process a document to generate chain-of-thought examples.
        
        Args:
            text: Document text content
            num_examples: Total number of COT examples to generate
            chunk_size: Size of text chunks to process
            overlap: Overlap between chunks
            temperature: LLM temperature parameter
            include_simple_steps: Include simple step-by-step breakdown
            
        Returns:
            Dictionary with COT examples
        """
        # Use default parameters if not provided
        if num_examples is None:
            num_examples = self.num_examples
        
        if chunk_size is None:
            chunk_size = self.chunk_size
        
        if overlap is None:
            overlap = self.overlap
        
        if temperature is None:
            temperature = self.temperature
        
        # Split text into chunks if needed
        if len(text) > chunk_size:
            chunks = split_text(text, chunk_size, overlap)
            
            # Calculate examples per chunk
            examples_per_chunk = max(1, num_examples // len(chunks))
            remaining_examples = num_examples % len(chunks)
            
            if VERBOSE:
                logger.info(f"Processing document with {len(chunks)} chunks")
                logger.info(f"Generating approximately {examples_per_chunk} examples per chunk")
                logger.info(f"Plus {remaining_examples} extra examples for the first chunks")
            
            # Generate examples for each chunk
            all_examples = []
            
            for i, chunk in enumerate(tqdm(chunks, desc="Generating COT examples")):
                # Calculate examples for this chunk
                chunk_examples = examples_per_chunk
                if i < remaining_examples:
                    chunk_examples += 1
                
                # Skip if no examples to generate
                if chunk_examples <= 0:
                    continue
                
                # Generate examples for this chunk
                try:
                    examples = self.generate_cot_examples(
                        text=chunk,
                        num_examples=chunk_examples,
                        temperature=temperature
                    )
                    
                    all_examples.extend(examples)
                    
                    # Short delay to avoid rate limiting
                    time.sleep(0.1)
                    
                except Exception as e:
                    logger.error(f"Error generating COT examples for chunk {i}: {str(e)}")
                    # Continue with next chunk
            
            examples = all_examples
        else:
            # Process the entire text at once
            examples = self.generate_cot_examples(
                text=text,
                num_examples=num_examples,
                temperature=temperature
            )
        
        if VERBOSE:
            logger.info(f"Generated a total of {len(examples)} COT examples")
        
        # Optionally add simple step-by-step breakdown
        if include_simple_steps and examples:
            examples_with_steps = []
            
            for example in examples:
                # Add simple steps if not already present
                if "steps" not in example:
                    # Extract steps from reasoning
                    reasoning = example.get("reasoning", "")
                    steps = self._extract_steps(reasoning)
                    
                    # Add steps to example
                    new_example = example.copy()
                    new_example["steps"] = steps
                    examples_with_steps.append(new_example)
                else:
                    examples_with_steps.append(example)
            
            examples = examples_with_steps
        
        # Prepare result
        result = {
            "cot_examples": examples
        }
        
        return result
    
    def enhance_with_cot(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        include_simple_steps: bool = False
    ) -> List[Dict[str, str]]:
        """
        Enhance conversation messages with chain-of-thought reasoning.
        
        Args:
            messages: List of conversation messages
            temperature: LLM temperature parameter
            include_simple_steps: Include simple step-by-step breakdown
            
        Returns:
            Enhanced messages with chain-of-thought reasoning
        """
        if not messages:
            return []
        
        # Use default temperature if not provided
        if temperature is None:
            temperature = self.temperature
        
        # Get COT enhancement prompt
        prompt_template = get_prompt(self.client.config, "cot_enhancement")
        
        # Format prompt with conversation
        conversation_json = json.dumps(messages, indent=2)
        prompt = prompt_template.format(conversation=conversation_json)
        
        # Create message for the LLM
        system_message = [
            {"role": "system", "content": prompt}
        ]
        
        if VERBOSE:
            logger.info(f"Enhancing {len(messages)} conversation messages with COT reasoning")
        
        # Get completion from LLM
        response = self.client.chat_completion(
            messages=system_message,
            temperature=temperature
        )
        
        # Try to parse enhanced messages as JSON
        enhanced_messages = extract_json(response)
        
        # Validate and use the enhanced messages
        if enhanced_messages and isinstance(enhanced_messages, list):
            # Check if the structure is valid
            if all(isinstance(msg, dict) and "role" in msg and "content" in msg for msg in enhanced_messages):
                if VERBOSE:
                    logger.info(f"Successfully enhanced {len(enhanced_messages)} messages")
                
                # Optionally add simple step-by-step breakdown
                if include_simple_steps:
                    for msg in enhanced_messages:
                        if msg.get("role") == "assistant":
                            content = msg.get("content", "")
                            
                            # If not already enhanced with Steps format
                            if "Step 1:" in content and "Step 2:" in content:
                                steps = self._extract_steps(content)
                                
                                # Append steps in a more structured format if needed
                                if steps and len(steps) > 1 and "STEPS:" not in content:
                                    steps_text = "\n\nSTEPS:\n" + "\n".join([f"{i+1}. {step}" for i, step in enumerate(steps)])
                                    msg["content"] = content + steps_text
                
                return enhanced_messages
        
        # If parsing fails, return original messages
        logger.warning("Failed to parse enhanced messages. Returning original messages.")
        return messages
    
    def _extract_steps(self, reasoning: str) -> List[str]:
        """
        Extract step-by-step reasoning from text.
        
        Args:
            reasoning: Chain-of-thought reasoning text
            
        Returns:
            List of reasoning steps
        """
        # Try to extract numbered steps
        import re
        
        # Try different step patterns
        patterns = [
            r'Step\s+(\d+)[\s:]+(.+?)(?=Step\s+\d+[\s:]|$)',  # "Step 1: ..."
            r'(\d+)[\.\)]\s+(.+?)(?=\d+[\.\)]|$)',            # "1. ..." or "1) ..."
            r'[\-\*]\s+(.+?)(?=[\-\*]|$)'                     # "- ..." or "* ..."
        ]
        
        for pattern in patterns:
            steps = []
            matches = re.finditer(pattern, reasoning, re.DOTALL)
            
            for match in matches:
                if len(match.groups()) == 2:  # Numbered steps
                    step_text = match.group(2).strip()
                    steps.append(step_text)
                elif len(match.groups()) == 1:  # Bullet points
                    step_text = match.group(1).strip()
                    steps.append(step_text)
            
            if steps:
                return steps
        
        # If no pattern matches, split by sentences as a fallback
        sentences = re.split(r'(?<=[.!?])\s+', reasoning)
        return [s.strip() for s in sentences if s.strip()]