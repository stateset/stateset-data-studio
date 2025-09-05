"""
Test script for the synthetic_data_kit package.
"""
import os
import json
from synthetic_data_kit.models.llm_client import LLMClient
from synthetic_data_kit.generators.qa_generator import QAGenerator
from synthetic_data_kit.parsers.txt_parser import TXTParser

def main():
    print("Testing synthetic_data_kit package...")
    
    # Set up file paths
    input_file = "data/uploads/test.txt"
    output_dir = "data/output"
    
    # Create parser and parse the file
    print(f"Parsing file: {input_file}")
    parser = TXTParser()
    content = parser.parse(input_file)
    print(f"Parsed {len(content)} characters")
    
    # Save the parsed content
    output_file = os.path.join(output_dir, "test_parsed.txt")
    parser.save(content, output_file)
    print(f"Saved parsed content to {output_file}")
    
    # Create test config
    test_config = {
        "vllm": {
            "api_base": "http://localhost:8000/v1",
            "model": "meta-llama/Llama-3.1-70B-Instruct"
        },
        "generation": {
            "temperature": 0.7,
            "chunk_size": 4000,
            "num_pairs": 5
        }
    }
    
    # Save test config
    with open("configs/test_config.yaml", "w") as f:
        import yaml
        yaml.dump(test_config, f)
    
    try:
        # Initialize LLM client (mock mode)
        print("Initializing LLM client (mock mode)")
        # Mock the LLM client to avoid real API calls
        class MockLLMClient:
            def __init__(self):
                self.config = test_config
            
            def chat_completion(self, messages, **kwargs):
                print(f"Mock chat completion with {len(messages)} messages")
                # Generate mock QA pairs in expected format
                return json.dumps([
                    {"question": "What is synthetic-data-kit?", 
                     "answer": "The synthetic-data-kit is a tool designed to process documents and create training data for language models."},
                    {"question": "What are the steps involved in the synthetic data generation process?", 
                     "answer": "The process involves several steps: 1. Ingesting and preprocessing documents, 2. Generating synthetic data with LLMs, 3. Curating the generated data for quality, 4. Saving the curated data in appropriate formats for model training."}
                ])
            
            def batch_completion(self, all_messages, **kwargs):
                return [self.chat_completion(messages) for messages in all_messages]
        
        client = MockLLMClient()
        
        # Generate QA pairs
        print("Generating QA pairs...")
        generator = QAGenerator(client)
        result = generator.process_document(
            content,
            num_pairs=3,
            verbose=True
        )
        
        # Save results
        output_qa_file = os.path.join("data/generated", "test_qa_pairs.json")
        with open(output_qa_file, "w") as f:
            json.dump(result, f, indent=2)
        
        print(f"Saved QA pairs to {output_qa_file}")
        print(f"Generated {len(result.get('qa_pairs', []))} QA pairs")
        
        # Print sample QA pair
        if result.get("qa_pairs"):
            print("\nSample QA pair:")
            pair = result["qa_pairs"][0]
            print(f"Q: {pair['question']}")
            print(f"A: {pair['answer']}")
        
        print("\nTest completed successfully!")
        
    except Exception as e:
        print(f"Error during test: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()