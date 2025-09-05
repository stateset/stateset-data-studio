"""
LLM Client module for interacting with language models via vLLM API or Llama API.
"""
import os
import yaml
import json
import logging
import time
import requests
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
import asyncio
import aiohttp
from tqdm import tqdm

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("llm_client")

# Enable verbose logging via environment variable
VERBOSE = os.environ.get('SDK_VERBOSE', 'false').lower() == 'true'

class LLMClient:
    """
    Client for interacting with LLMs via vLLM API or Llama API.
    """
    
    def __init__(
        self,
        config_path: Optional[Path] = None,
        api_base: Optional[str] = None,
        model_name: Optional[str] = None,
        api_type: Optional[str] = None
    ):
        """
        Initialize LLM client with configuration.
        
        Args:
            config_path: Path to configuration file
            api_base: API base URL (overrides config)
            model_name: Model name to use (overrides config)
            api_type: API type to use ('vllm' or 'llama', overrides config)
        """
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Override config with parameters if provided
        if api_type:
            self.config["api_type"] = api_type
        if api_base and self.config.get("api_type", "vllm") == "vllm":
            self.config["vllm"]["api_base"] = api_base
        if model_name:
            if self.config.get("api_type", "vllm") == "vllm":
                self.config["vllm"]["model"] = model_name
            else:
                self.config["llama"]["model"] = model_name
        
        # Set API type
        self.api_type = self.config.get("api_type", "vllm")
            
        if self.api_type == "vllm":
            self.api_base = self.config["vllm"]["api_base"]
            self.model = self.config["vllm"]["model"]
            if VERBOSE:
                logger.info(f"Initialized LLM client with vLLM API base: {self.api_base}")
                logger.info(f"Using vLLM model: {self.model}")
        else:  # llama
            self.api_base = "https://api.llama.com/v1"
            self.model = self.config["llama"]["model"]
            self.api_key = self.config["llama"]["api_key"]
            if VERBOSE:
                logger.info(f"Initialized LLM client with Llama API")
                logger.info(f"Using Llama model: {self.model}")
    
    def _load_config(self, config_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        Load configuration from file or use default.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Configuration dictionary
        """
        # Default configuration
        default_config = {
            "api_type": "vllm",
            "vllm": {
                "api_base": "http://localhost:8000/v1",
                "model": "meta-llama/Llama-3.1-70B-Instruct"
            },
            "llama": {
                "api_key": "",
                "model": "Llama-4-Maverick-17B-128E-Instruct-FP8"
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
            }
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
                    else:
                        # Ensure all required keys exist in each section
                        if isinstance(default_config[section], dict) and isinstance(config[section], dict):
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
                        else:
                            # Ensure all required keys exist in each section
                            if isinstance(default_config[section], dict) and isinstance(config[section], dict):
                                for key in default_config[section]:
                                    if key not in config[section]:
                                        config[section][key] = default_config[section][key]
                    
                    return config
                except Exception as e:
                    logger.error(f"Error loading config from {config_file}: {e}")
        
        # Use default configuration
        logger.info("No config file found, using default configuration")
        return default_config
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        stop: Optional[List[str]] = None,
        stream: bool = False,
        functions: Optional[List[Dict[str, Any]]] = None,
        function_call: Optional[str] = None
    ) -> str:
        """
        Get a chat completion from the LLM.
        
        Args:
            messages: List of message dictionaries with role and content
            temperature: Sampling temperature (default: 0.7)
            max_tokens: Maximum number of tokens to generate
            top_p: Top-p probability mass to consider
            stop: List of strings that stop generation when encountered
            stream: Whether to stream responses
            functions: List of function definitions for function calling
            function_call: Function call mode ("auto" or specific function)
            
        Returns:
            Model response text
        """
        # Use parameters from config if not provided
        if temperature is None:
            temperature = self.config["generation"].get("temperature", 0.7)
        
        if max_tokens is None:
            max_tokens = self.config["generation"].get("max_tokens", 2048)
        
        # Prepare request payload and headers based on API type
        if self.api_type == "vllm":
            url = f"{self.api_base}/chat/completions"
            headers = {"Content-Type": "application/json"}
            
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            if top_p is not None:
                payload["top_p"] = top_p
            
            if stop is not None:
                payload["stop"] = stop
            
            if stream:
                payload["stream"] = True
                
            if functions is not None:
                payload["functions"] = functions
                
            if function_call is not None:
                payload["function_call"] = function_call
        else:  # llama
            url = f"{self.api_base}/chat/completions"
            headers = {
                "Content-Type": "application/json",
                "Authorization": self.api_key
            }
            
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature
            }
            
            if max_tokens is not None:
                payload["max_tokens"] = max_tokens
            
            if top_p is not None:
                payload["top_p"] = top_p
            
            if stop is not None:
                payload["stop"] = stop
            
            if stream:
                payload["stream"] = True
                
            if functions is not None:
                payload["functions"] = functions
                
            if function_call is not None:
                payload["function_call"] = function_call
        
        if VERBOSE:
            logger.info(f"Sending request to {url}")
            logger.info(f"API type: {self.api_type}")
            logger.info(f"Messages: {json.dumps(messages)[:200]}...")
        
        # Send request with exponential backoff for retries
        max_retries = 5
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=120)
                
                if response.status_code == 200:
                    data = response.json()
                    if VERBOSE:
                        logger.info(f"Response: {json.dumps(data)[:200]}...")
                    
                    # Extract response text
                    if self.api_type == "llama":
                        # Handle Llama API response format
                        if "completion_message" in data and "content" in data["completion_message"]:
                            content = data["completion_message"]["content"]
                            if content.get("type") == "text":
                                return content.get("text", "")
                            else:
                                logger.error(f"Unexpected Llama API response format: {data}")
                                return ""
                        else:
                            logger.error(f"Unexpected Llama API response format: {data}")
                            return ""
                    else:
                        # Handle vLLM response format
                        if "choices" in data and len(data["choices"]) > 0:
                            if "message" in data["choices"][0]:
                                # Handle function call response
                                if "function_call" in data["choices"][0]["message"]:
                                    return json.dumps(data["choices"][0]["message"]["function_call"])
                                return data["choices"][0]["message"]["content"]
                            else:
                                logger.error(f"Unexpected vLLM response format: {data}")
                                return ""
                        else:
                            logger.error(f"Unexpected response format: {data}")
                            return ""
                else:
                    logger.error(f"API request failed with status {response.status_code}: {response.text}")
                    
                    if attempt < max_retries - 1:
                        wait_time = retry_delay * (2 ** attempt)
                        logger.info(f"Retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
                    else:
                        logger.error("Max retries exceeded")
                        return f"API request failed after {max_retries} attempts"
            
            except Exception as e:
                logger.error(f"Error sending API request: {str(e)}")
                
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error("Max retries exceeded")
                    return f"Error sending API request: {str(e)}"
        
        return "Failed to get response from API"
    
    async def _async_chat_completion(
        self,
        messages: List[Dict[str, str]],
        session: aiohttp.ClientSession,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        stop: Optional[List[str]] = None,
        functions: Optional[List[Dict[str, Any]]] = None,
        function_call: Optional[str] = None
    ) -> str:
        """
        Async implementation of chat completion for batch requests.
        """
        # Use parameters from config if not provided
        if temperature is None:
            temperature = self.config["generation"].get("temperature", 0.7)
        
        if max_tokens is None:
            max_tokens = self.config["generation"].get("max_tokens", 2048)
        
        # Prepare request payload and headers based on API type
        if self.api_type == "vllm":
            url = f"{self.api_base}/chat/completions"
            headers = {"Content-Type": "application/json"}
            
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            if top_p is not None:
                payload["top_p"] = top_p
            
            if stop is not None:
                payload["stop"] = stop
                
            if functions is not None:
                payload["functions"] = functions
                
            if function_call is not None:
                payload["function_call"] = function_call
        else:  # llama
            url = f"{self.api_base}/chat/completions"
            headers = {
                "Content-Type": "application/json",
                "Authorization": self.api_key
            }
            
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature
            }
            
            if max_tokens is not None:
                payload["max_tokens"] = max_tokens
            
            if top_p is not None:
                payload["top_p"] = top_p
            
            if stop is not None:
                payload["stop"] = stop
                
            if functions is not None:
                payload["functions"] = functions
                
            if function_call is not None:
                payload["function_call"] = function_call
        
        # Send request with exponential backoff for retries
        max_retries = 5
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                async with session.post(url, headers=headers, json=payload, timeout=120) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Extract response text
                        if self.api_type == "llama":
                            # Handle Llama API response format
                            if "completion_message" in data and "content" in data["completion_message"]:
                                content = data["completion_message"]["content"]
                                if content.get("type") == "text":
                                    return content.get("text", "")
                                else:
                                    logger.error(f"Unexpected Llama API async response format: {data}")
                                    return ""
                            else:
                                logger.error(f"Unexpected Llama API async response format: {data}")
                                return ""
                        else:
                            # Handle vLLM response format
                            if "choices" in data and len(data["choices"]) > 0:
                                if "message" in data["choices"][0]:
                                    # Handle function call response
                                    if "function_call" in data["choices"][0]["message"]:
                                        return json.dumps(data["choices"][0]["message"]["function_call"])
                                    return data["choices"][0]["message"]["content"]
                                else:
                                    logger.error(f"Unexpected vLLM async response format: {data}")
                                    return ""
                            else:
                                logger.error(f"Unexpected async response format: {data}")
                                return ""
                    else:
                        error_text = await response.text()
                        logger.error(f"API request failed with status {response.status}: {error_text}")
                        
                        if attempt < max_retries - 1:
                            wait_time = retry_delay * (2 ** attempt)
                            await asyncio.sleep(wait_time)
                        else:
                            logger.error("Max retries exceeded")
                            return f"API request failed after {max_retries} attempts"
            
            except Exception as e:
                logger.error(f"Error sending API request: {str(e)}")
                
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)
                    await asyncio.sleep(wait_time)
                else:
                    logger.error("Max retries exceeded")
                    return f"Error sending API request: {str(e)}"
        
        return "Failed to get response from API"
    
    async def _process_batch(
        self,
        all_messages: List[List[Dict[str, str]]],
        batch_size: int,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        stop: Optional[List[str]] = None,
        functions: Optional[List[Dict[str, Any]]] = None,
        function_call: Optional[str] = None
    ) -> List[str]:
        """
        Process a batch of message lists asynchronously.
        """
        responses = []
        
        # Create client session with appropriate headers based on API type
        if self.api_type == "vllm":
            headers = {"Content-Type": "application/json"}
        else:  # llama
            headers = {
                "Content-Type": "application/json",
                "Authorization": self.api_key
            }
        
        async with aiohttp.ClientSession(headers=headers) as session:
            tasks = []
            for i in range(0, len(all_messages), batch_size):
                batch = all_messages[i:i+batch_size]
                for messages in batch:
                    task = asyncio.ensure_future(
                        self._async_chat_completion(
                            messages, session, temperature, max_tokens, top_p, stop, functions, function_call
                        )
                    )
                    tasks.append(task)
                
                # Wait for the batch to complete
                batch_responses = await asyncio.gather(*tasks)
                responses.extend(batch_responses)
                tasks = []
        
        return responses
    
    def batch_completion(
        self,
        all_messages: List[List[Dict[str, str]]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        stop: Optional[List[str]] = None,
        batch_size: Optional[int] = None,
        functions: Optional[List[Dict[str, Any]]] = None,
        function_call: Optional[str] = None
    ) -> List[str]:
        """
        Get completions for multiple message sets in parallel.
        
        Args:
            all_messages: List of message lists to process
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            top_p: Top-p probability mass
            stop: List of strings that stop generation
            batch_size: Number of requests to process in parallel
            functions: List of function definitions for function calling
            function_call: Function call mode ("auto" or specific function)
            
        Returns:
            List of model response texts
        """
        if not all_messages:
            return []
        
        # Use batch size from config if not provided
        if batch_size is None:
            batch_size = self.config["curate"].get("inference_batch", 32)
        
        try:
            # Use asyncio to process requests in parallel
            loop = asyncio.get_event_loop()
        except RuntimeError:
            # Create a new event loop if one doesn't exist
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        try:
            responses = loop.run_until_complete(
                self._process_batch(
                    all_messages, batch_size, temperature, max_tokens, top_p, stop, functions, function_call
                )
            )
            return responses
        except Exception as e:
            logger.error(f"Error in batch processing: {str(e)}")
            # Fallback to sequential processing
            logger.info("Falling back to sequential processing")
            return [
                self.chat_completion(
                    messages, temperature, max_tokens, top_p, stop, False, functions, function_call
                )
                for messages in tqdm(all_messages, desc="Processing")
            ]