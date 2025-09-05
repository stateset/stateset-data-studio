"""
Configuration utilities for the synthetic data kit.
Provides functions to access and manage configuration settings.
"""
import os
import yaml
import json
import logging
from typing import Dict, Any, Optional, List, Union
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("config")

# Enable verbose logging via environment variable
VERBOSE = os.environ.get('SDK_VERBOSE', 'false').lower() == 'true'

# Default prompts
DEFAULT_PROMPTS = {
    # QA Generation prompt
    "qa_generation": """You are a helpful AI assistant who excels at creating realistic, high-quality question-answer pairs based on provided text content. 
Your task is to carefully read the following text and create {num_pairs} diverse question-answer pairs.

Guidelines:
1. Create questions that directly relate to the content of the text
2. Ensure questions are diverse in style (what, how, why, when, etc.)
3. Include a mix of factual, inferential, and analytical questions
4. Make sure answers are accurate, comprehensive, and directly supported by the text
5. Answers should be 2-5 sentences long in most cases
6. Each question-answer pair should be independent and not require knowledge of other pairs

Text to process:
{text}

Format your response as a valid JSON array of objects with "question" and "answer" fields:
[
  {{"question": "First question here?", "answer": "Answer to first question here."}},
  {{"question": "Second question here?", "answer": "Answer to second question here."}}
]

Generate {num_pairs} high-quality question-answer pairs.""",

    # QA Rating prompt
    "qa_rating": """You are a quality evaluator for question-answer pairs. Your task is to rate the quality of each given Q&A pair on a scale of 1-10.

Rate based on these criteria:
1. Relevance - Does the Q&A directly relate to the subject matter?
2. Accuracy - Is the answer factually correct given the question?
3. Completeness - Does the answer thoroughly address all aspects of the question?
4. Clarity - Is the question clear and unambiguous? Is the answer well-articulated?
5. Educational value - Does the Q&A provide valuable information?

For each pair, provide:
1. A numerical rating from 1-10, where 10 is excellent quality
2. A brief justification for your rating

Here are the Q&A pairs to evaluate:
{pairs}

Format your response as a valid JSON array with each object containing the original question, answer, your rating, and justification:
[
  {{
    "question": "Original question text",
    "answer": "Original answer text",
    "rating": 8,
    "justification": "Brief explanation of rating"
  }},
  ...
]""",

    # CoT generation prompt
    "cot_generation": """You are an AI expert at creating high-quality chain-of-thought reasoning examples. Your task is to carefully read the provided text and create {num_examples} diverse examples that demonstrate step-by-step reasoning processes.

Chain of thought (CoT) examples show how to break down complex problems into logical steps. Each example should include:
1. A challenging question that requires multi-step reasoning
2. A detailed step-by-step solution that shows the thought process
3. A clear final answer

Guidelines:
- Create diverse question types (mathematical, logical, analytical, etc.)
- Ensure questions are directly related to the content
- Make reasoning steps explicit and easy to follow
- Include ~3-6 reasoning steps for each example

Text to process:
{text}

Format your response as a valid JSON array of objects with "question", "reasoning", and "answer" fields:
[
  {{
    "question": "Complex question requiring reasoning?",
    "reasoning": "Step 1: First, I need to understand X.\nStep 2: Based on X, I can determine Y.\nStep 3: Y leads to Z because...\nStep 4: Therefore, the answer is...",
    "answer": "Final concise answer"
  }},
  ...
]

Generate {num_examples} high-quality chain-of-thought examples.""",

    # CoT enhancement prompt
    "cot_enhancement": """You are an AI expert at enhancing conversational data with explicit chain-of-thought reasoning. Your task is to take a conversation that contains questions and answers, and enhance it by adding detailed reasoning steps to show how the answers were derived.

For each message from the assistant that answers a question, you should:
1. Keep the original question from the user unchanged
2. Add a new detailed chain-of-thought reasoning process that logically leads to the answer
3. Keep the original answer, ensuring the reasoning supports it

Guidelines for effective chain-of-thought reasoning:
- Break down the problem into clear logical steps
- Explain each step of the reasoning process explicitly
- Make connections between steps clear
- Show how the final answer follows from the reasoning

Here's the conversation to enhance:
{conversation}

Format your response as a valid JSON array of message objects, following the same structure as input but with enhanced reasoning. Example structure:
[
  {{"role": "system", "content": "Original system message"}},
  {{"role": "user", "content": "Original user question"}},
  {{"role": "assistant", "content": "Step 1: First, I consider X.\nStep 2: Based on X, I can determine Y.\nStep 3: Y leads to Z because...\nStep 4: Therefore, the answer is...\n\nOriginal answer."}}
]

Ensure your enhanced messages maintain the original meaning while adding clear reasoning.""",

    # Document summarization prompt
    "summarization": """You are an expert at creating comprehensive, accurate summaries of complex documents. Your task is to read the following text carefully and create a concise but thorough summary.

Your summary should:
1. Capture the main topics, arguments, and conclusions of the text
2. Preserve the most important facts, figures, and examples
3. Maintain the original tone and perspective
4. Be well-structured and logically organized
5. Be approximately 10% of the original text length

Text to summarize:
{text}

Provide your summary in clear, concise language."""
}

def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load configuration from file or use default.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Configuration dictionary
    """
    # Default configuration
    default_config = {
        "vllm": {
            "api_base": "http://localhost:8000/v1",
            "model": "meta-llama/Llama-3.1-70B-Instruct"
        },
        "generation": {
            "temperature": 0.7,
            "chunk_size": 4000,
            "num_pairs": 25
        },
        "curate": {
            "threshold": 7.0,
            "batch_size": 8,
            "temperature": 0.1,
            "inference_batch": 32
        },
        "prompts": DEFAULT_PROMPTS
    }
    
    # If config path is provided, load from file
    if config_path:
        try:
            if VERBOSE:
                logger.info(f"Loading config from {config_path}")
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                
            # Ensure all required sections exist
            for section in default_config:
                if section not in config:
                    config[section] = default_config[section]
                elif section == "prompts" and isinstance(config[section], dict):
                    # Merge prompts, using defaults for any missing ones
                    for prompt_key in default_config["prompts"]:
                        if prompt_key not in config["prompts"]:
                            config["prompts"][prompt_key] = default_config["prompts"][prompt_key]
                else:
                    # Ensure all required keys exist in each section
                    for key in default_config[section]:
                        if key not in config[section]:
                            config[section][key] = default_config[section][key]
            
            return config
        except Exception as e:
            logger.error(f"Error loading config from {config_path}: {e}")
            logger.info("Using default configuration")
            return default_config
    
    # Look for config.yaml in configs directory
    config_dirs = [".", "configs"]
    for config_dir in config_dirs:
        config_file = os.path.join(config_dir, "config.yaml")
        if os.path.exists(config_file):
            try:
                if VERBOSE:
                    logger.info(f"Loading config from {config_file}")
                with open(config_file, 'r') as f:
                    config = yaml.safe_load(f)
                    
                # Ensure all required sections exist
                for section in default_config:
                    if section not in config:
                        config[section] = default_config[section]
                    elif section == "prompts" and isinstance(config[section], dict):
                        # Merge prompts, using defaults for any missing ones
                        for prompt_key in default_config["prompts"]:
                            if prompt_key not in config["prompts"]:
                                config["prompts"][prompt_key] = default_config["prompts"][prompt_key]
                    else:
                        # Ensure all required keys exist in each section
                        for key in default_config[section]:
                            if key not in config[section]:
                                config[section][key] = default_config[section][key]
                
                return config
            except Exception as e:
                logger.error(f"Error loading config from {config_file}: {e}")
    
    # Use default configuration
    logger.info("No config file found, using default configuration")
    return default_config

def get_generation_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get generation-specific configuration.
    
    Args:
        config: Full configuration dictionary
        
    Returns:
        Generation configuration dictionary
    """
    return config.get("generation", {})

def get_curate_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get curation-specific configuration.
    
    Args:
        config: Full configuration dictionary
        
    Returns:
        Curation configuration dictionary
    """
    return config.get("curate", {})

def get_path_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get path-specific configuration.
    
    Args:
        config: Full configuration dictionary
        
    Returns:
        Path configuration dictionary
    """
    return config.get("paths", {})

def get_prompt(config: Dict[str, Any], prompt_key: str) -> str:
    """
    Get a prompt template from configuration.
    
    Args:
        config: Full configuration dictionary
        prompt_key: Key for the prompt template
        
    Returns:
        Prompt template string
    """
    # Get prompts from config or use defaults
    prompts = config.get("prompts", {})
    
    # Return the requested prompt or the default
    if prompt_key in prompts:
        return prompts[prompt_key]
    elif prompt_key in DEFAULT_PROMPTS:
        return DEFAULT_PROMPTS[prompt_key]
    else:
        logger.warning(f"Prompt key '{prompt_key}' not found in config or defaults")
        return ""

def load_custom_prompts(file_path: str) -> Dict[str, str]:
    """
    Load custom prompts from a JSON file.
    
    Args:
        file_path: Path to JSON file with custom prompts
        
    Returns:
        Dictionary of custom prompts
    """
    try:
        with open(file_path, 'r') as f:
            custom_prompts = json.load(f)
        
        if not isinstance(custom_prompts, dict):
            logger.error(f"Custom prompts file {file_path} must contain a JSON object")
            return {}
            
        return custom_prompts
    except Exception as e:
        logger.error(f"Error loading custom prompts from {file_path}: {e}")
        return {}