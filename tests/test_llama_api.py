#!/usr/bin/env python
"""
Script to test the Llama API integration in the Synthetic Data Kit.
"""
import os
import json
import sys
import requests

# Test configuration
TEST_CONFIG = {
    "api_type": "llama",
    "llama": {
        "api_key": "llama-api-key",
        "model": "Llama-4-Maverick-17B-128E-Instruct-FP8"
    }
}

# Test message
TEST_MESSAGES = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Generate 3 question-answer pairs about synthetic data generation in JSON format."}
]

def test_direct_api_call():
    """Test direct API call to Llama API"""
    api_url = "https://api.llama.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": TEST_CONFIG["llama"]["api_key"]
    }
    
    data = {
        "model": TEST_CONFIG["llama"]["model"],
        "messages": TEST_MESSAGES,
        "temperature": 0.3
    }
    
    try:
        response = requests.post(api_url, headers=headers, json=data)
        response.raise_for_status()
        json_response = response.json()
        
        print("\nAPI Response:")
        print(json.dumps(json_response, indent=2))
        
        if "completion_message" in json_response:
            text_content = json_response["completion_message"]["content"]["text"]
            print("\nGenerated QA pairs:")
            print(text_content)
            return True
        else:
            print("Unexpected response format")
            return False
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def test_with_sdk_client():
    """Test using the SDK LLMClient"""
    try:
        from synthetic_data_kit.models.llm_client import LLMClient
        
        # Create LLM client with test config
        client = LLMClient()
        
        # Set API type and credentials
        client.api_type = TEST_CONFIG["api_type"]
        client.api_base = "https://api.llama.com/v1"
        client.model = TEST_CONFIG["llama"]["model"]
        client.api_key = TEST_CONFIG["llama"]["api_key"]
        
        print(f"Using API type: {client.api_type}")
        print(f"Using model: {client.model}")
        
        # Test chat completion
        print("\nTesting chat completion via SDK client...")
        response = client.chat_completion(
            messages=TEST_MESSAGES,
            temperature=0.3,
            max_tokens=1000
        )
        print("\nResponse from SDK client:")
        print(response)
        return True
    except Exception as e:
        print(f"Error with SDK client: {str(e)}")
        return False

def main():
    print("Testing Llama API integration...")
    
    print("\n1. Testing direct API call...")
    direct_success = test_direct_api_call()
    
    print("\n2. Testing with SDK client...")
    sdk_success = test_with_sdk_client()
    
    if direct_success and sdk_success:
        print("\nAll tests completed successfully!")
        return 0
    else:
        print("\nSome tests failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())