#!/usr/bin/env python
"""
Test script for YouTube URL ingestion.
"""
import os
import sys
import json
import time
import argparse
from urllib.parse import urlparse, parse_qs

# Add the parent directory to the module search path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the YouTube parser
from synthetic_data_kit.parsers.youtube_parser import YouTubeParser

def test_youtube_parser(url):
    """Test the YouTube parser with a given URL."""
    print(f"Testing YouTube parser with URL: {url}")
    
    # Extract video ID
    parser = YouTubeParser()
    video_id = parser._extract_video_id(url)
    
    if not video_id:
        print("❌ Failed to extract video ID")
        return False
    
    print(f"✅ Successfully extracted video ID: {video_id}")
    
    # Try to get transcript
    try:
        content = parser.parse(url)
        
        if not content:
            print("❌ Got empty content")
            return False
        
        # Print content summary
        content_length = len(content)
        word_count = len(content.split())
        line_count = len(content.splitlines())
        
        print(f"✅ Successfully parsed content:")
        print(f"  - Characters: {content_length}")
        print(f"  - Words: {word_count}")
        print(f"  - Lines: {line_count}")
        
        # Print first few lines
        preview_lines = content.splitlines()[:5]
        print("\nPreview:")
        for line in preview_lines:
            print(f"  {line[:100]}{'...' if len(line) > 100 else ''}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error parsing content: {str(e)}")
        return False

def test_url_variations():
    """Test the YouTube parser with various URL formats."""
    test_urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Standard YouTube URL
        "https://youtu.be/dQw4w9WgXcQ",  # Short YouTube URL
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=30s",  # URL with timestamp
        "https://www.youtube.com/watch?feature=share&v=dQw4w9WgXcQ",  # URL with parameters
        "https://www.youtube.com/embed/dQw4w9WgXcQ",  # Embed URL
        "https://www.youtube.com/shorts/dQw4w9WgXcQ"  # YouTube shorts
    ]
    
    results = []
    for url in test_urls:
        print(f"\n{'='*80}")
        print(f"Testing URL: {url}")
        success = test_youtube_parser(url)
        results.append((url, success))
    
    print(f"\n{'='*80}")
    print("Test Results Summary:")
    success_count = sum(1 for _, success in results if success)
    print(f"✅ Passed: {success_count}/{len(results)}")
    
    for url, success in results:
        status = "✅ Passed" if success else "❌ Failed"
        print(f"{status} - {url}")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Test YouTube URL ingestion.')
    parser.add_argument('--url', help='YouTube URL to test')
    args = parser.parse_args()
    
    if args.url:
        test_youtube_parser(args.url)
    else:
        test_url_variations()

if __name__ == "__main__":
    main()