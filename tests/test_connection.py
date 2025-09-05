import requests
import sys
import time

print("Testing connection to vLLM server...")
url = "http://192.222.55.167:8000/v1/models"

try:
    response = requests.get(url, timeout=120)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")

print("Done!")