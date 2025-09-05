#!/usr/bin/env python3
import os
import json
import logging
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test-qa-generation")

# Add the current directory to the path to import local modules
sys.path.insert(0, os.getcwd())

def test_qa_generation_paths():
    """Test QA generation path handling and file creation"""
    
    # Check directory structure
    directories = [
        "data/output",
        "data/generated",
        "backend/data/output",
        "backend/data/generated"
    ]
    
    logger.info("Checking directory structure:")
    for directory in directories:
        exists = os.path.exists(directory)
        is_dir = os.path.isdir(directory) if exists else False
        is_writable = os.access(directory, os.W_OK) if exists else False
        logger.info(f"Directory '{directory}': exists={exists}, is_dir={is_dir}, writable={is_writable}")
        
        # Create directory if it doesn't exist
        if not exists:
            try:
                os.makedirs(directory, exist_ok=True)
                logger.info(f"Created directory: {directory}")
            except Exception as e:
                logger.error(f"Failed to create directory {directory}: {str(e)}")
    
    # Create a test input file
    input_file = "data/output/test_qa_input.txt"
    with open(input_file, "w") as f:
        f.write("""
        This is a test document for QA generation.
        The synthetic data studio is a tool for generating question-answer pairs.
        It uses AI models to create realistic synthetic data.
        This data can be used for training, evaluation, and fine-tuning.
        The tool has several steps: ingest, create, curate, and export.
        """)
    logger.info(f"Created test input file: {input_file}")
    
    # Try to generate QA pairs directly
    try:
        from synthetic_data_kit.models.llm_client import LLMClient
        from synthetic_data_kit.generators.qa_generator import QAGenerator
        
        logger.info("Creating LLM client...")
        # Try to load config
        client_config = {}
        try:
            import yaml
            with open("configs/config.yaml", "r") as f:
                client_config = yaml.safe_load(f)
                logger.info("Loaded config from configs/config.yaml")
        except Exception as e:
            logger.warning(f"Could not load config: {str(e)}")
        
        # Set up API details
        api_type = client_config.get("api_type", "vllm")
        api_base = None
        model = None
        
        if api_type == "llama":
            api_base = client_config.get("llama", {}).get("api_base", "https://api.llama.com/v1")
            model = client_config.get("llama", {}).get("model", "llama-3-8b-instruct")
        else:  # vllm
            api_base = client_config.get("vllm", {}).get("api_base", "http://localhost:8000/v1")
            model = client_config.get("vllm", {}).get("model", "llama-3-8b-instruct")
            
        logger.info(f"Using API type: {api_type}, API base: {api_base}, Model: {model}")
        
        # Initialize LLM client
        client = LLMClient(api_base=api_base, model_name=model, api_type=api_type)
        
        # Initialize QA generator
        logger.info("Creating QA Generator...")
        generator = QAGenerator(client)
        
        # Read input file
        with open(input_file, 'r') as f:
            document_text = f.read()
        
        # Process document
        logger.info("Processing document to generate QA pairs...")
        result = generator.process_document(
            document_text,
            num_pairs=3,  # Just generate a few pairs for testing
            verbose=True
        )
        
        # Print result structure
        if result:
            logger.info(f"Result has keys: {list(result.keys())}")
            if "qa_pairs" in result:
                logger.info(f"Generated {len(result['qa_pairs'])} QA pairs")
            else:
                logger.error("No 'qa_pairs' key in result")
        else:
            logger.error("No result returned from process_document")
        
        # Try to save the result to different paths
        base_name = "test_qa_generation"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        output_paths = [
            f"data/generated/{base_name}_{timestamp}_qa_pairs.json",
            f"backend/data/generated/{base_name}_{timestamp}_qa_pairs.json"
        ]
        
        for output_path in output_paths:
            try:
                output_dir = os.path.dirname(output_path)
                os.makedirs(output_dir, exist_ok=True)
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2)
                    
                logger.info(f"Successfully saved QA pairs to: {output_path}")
                
                # Verify the file exists
                if os.path.exists(output_path):
                    file_size = os.path.getsize(output_path)
                    logger.info(f"Verified file exists at {output_path} with size {file_size} bytes")
                else:
                    logger.error(f"File does not exist at {output_path} after saving")
            except Exception as e:
                logger.error(f"Error saving to {output_path}: {str(e)}")
        
    except ImportError as e:
        logger.error(f"Failed to import required modules: {str(e)}")
    except Exception as e:
        logger.error(f"Error in QA generation: {str(e)}")
    
    # Test the SDK command execution
    try:
        logger.info("\nTesting SDK command execution...")
        from backend.sdk_command import run_create_qa
        
        # Create a simple job
        job_id = "test_job"
        args = [input_file, "--type", "qa", "-n", "3", "--output-dir", "data/generated"]
        
        logger.info(f"Running run_create_qa with args: {args}")
        result = run_create_qa(job_id, args)
        
        logger.info(f"SDK command execution result: {result}")
        
        # Check if files were created
        generated_dir = "data/generated"
        logger.info(f"Files in {generated_dir} after SDK command:")
        try:
            files = os.listdir(generated_dir)
            for file in files:
                if "test_qa_input" in file and file.endswith("_qa_pairs.json"):
                    file_path = os.path.join(generated_dir, file)
                    file_size = os.path.getsize(file_path)
                    logger.info(f"Found file: {file} (size: {file_size} bytes)")
                    
                    # Read the file to verify content
                    try:
                        with open(file_path, 'r') as f:
                            content = json.load(f)
                            if "qa_pairs" in content:
                                logger.info(f"File contains {len(content['qa_pairs'])} QA pairs")
                            else:
                                logger.error(f"File does not contain 'qa_pairs' key")
                    except Exception as e:
                        logger.error(f"Error reading file {file_path}: {str(e)}")
        except Exception as e:
            logger.error(f"Error listing files in {generated_dir}: {str(e)}")
        
    except ImportError as e:
        logger.error(f"Failed to import SDK command module: {str(e)}")
    except Exception as e:
        logger.error(f"Error in SDK command execution: {str(e)}")

if __name__ == "__main__":
    print("\n===== Testing QA Generation and Paths =====\n")
    test_qa_generation_paths()
    print("\n===== Test Completed =====\n")