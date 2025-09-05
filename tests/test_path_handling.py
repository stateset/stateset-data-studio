#\!/usr/bin/env python3
import os
import sys

def check_paths():
    # Input file from the error
    file_path = "data/generated/test_create_20250504_101901_qa_pairs.json"
    
    # Check different variants of the path
    variants = [
        file_path,  # Original path
        f"backend/{file_path}",  # With backend/ prefix
        f"/home/dom/synthetic-data-studio/{file_path}",  # Absolute path
        f"/home/dom/synthetic-data-studio/backend/{file_path}",  # Absolute path with backend/
    ]
    
    print(f"Current working directory: {os.getcwd()}")
    print()
    
    for path in variants:
        if os.path.exists(path):
            print(f"✅ EXISTS: {path}")
        else:
            print(f"❌ NOT FOUND: {path}")
    
    # List files in the data/generated directory
    print("\nListing files in data/generated:")
    for variant in ["data/generated", "backend/data/generated"]:
        if os.path.exists(variant):
            print(f"\nFiles in {variant}:")
            files = os.listdir(variant)
            for file in files:
                if file.endswith(".json"):
                    full_path = os.path.join(variant, file)
                    print(f"  {file} - {os.path.getsize(full_path)} bytes")
        else:
            print(f"\n{variant} directory not found")

if __name__ == "__main__":
    print("Checking path handling...")
    check_paths()
EOF < /dev/null
