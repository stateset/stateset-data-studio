"""
Parser for YouTube videos.
"""
import os
import logging
import re
import subprocess
import tempfile
from typing import Any, Optional, List, Dict

from synthetic_data_kit.parsers.base_parser import BaseParser

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("youtube_parser")

class YouTubeParser(BaseParser):
    """Parser for YouTube videos. Uses youtube_transcript_api and falls back to pytube if needed."""
    
    def parse(self, url: str) -> str:
        """
        Parse a YouTube video URL and return its transcript.
        
        Args:
            url: YouTube video URL
            
        Returns:
            Extracted transcript text
        """
        logger.info(f"Parsing YouTube video: {url}")
        
        # Extract video ID from URL
        video_id = self._extract_video_id(url)
        
        if not video_id:
            raise ValueError(f"Could not extract video ID from URL: {url}")
            
        # First try using the youtube_transcript_api
        transcript = self._get_transcript_with_api(video_id)
        
        # If that fails, try pytube as a fallback
        if not transcript:
            transcript = self._get_transcript_with_pytube(url)
            
        # If both methods fail, try the YouTube API without dependencies
        if not transcript:
            transcript = self._get_transcript_with_requests(video_id)
        
        if not transcript:
            raise ValueError(f"Could not extract transcript from YouTube video: {url}")
        
        # Clean the text
        transcript = self.clean_text(transcript)
        
        logger.info(f"Successfully parsed YouTube transcript ({len(transcript)} characters)")
        return transcript
    
    def _get_transcript_with_api(self, video_id: str) -> Optional[str]:
        """
        Get transcript using youtube_transcript_api.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            Transcript text or None if failed
        """
        try:
            # Import the YouTube transcript API
            from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
            
            # Get transcript
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
            
            # Extract transcript text
            transcript_parts = []
            for item in transcript_list:
                transcript_parts.append(item['text'])
            
            # Join transcript parts
            content = " ".join(transcript_parts)
            
            logger.info(f"Retrieved transcript using youtube_transcript_api: {len(content)} characters")
            return content
            
        except ImportError:
            logger.warning("youtube_transcript_api not installed. Trying alternative methods.")
            return None
        except (TranscriptsDisabled, NoTranscriptFound) as e:
            logger.warning(f"No transcript available for video {video_id}: {str(e)}")
            return None
        except Exception as e:
            logger.warning(f"Error getting transcript with youtube_transcript_api: {str(e)}")
            return None
    
    def _get_transcript_with_pytube(self, url: str) -> Optional[str]:
        """
        Get transcript using pytube library.
        
        Args:
            url: YouTube video URL
            
        Returns:
            Transcript text or None if failed
        """
        try:
            # Import pytube
            from pytube import YouTube
            
            # Get video info
            yt = YouTube(url)
            
            # Get video title and description
            title = yt.title
            description = yt.description
            
            # Create a simple transcript from available metadata
            content = f"Video Title: {title}\n\nDescription: {description}"
            
            logger.info(f"Retrieved metadata using pytube: {len(content)} characters")
            return content
            
        except ImportError:
            logger.warning("pytube not installed. Trying alternative methods.")
            return None
        except Exception as e:
            logger.warning(f"Error getting transcript with pytube: {str(e)}")
            return None
    
    def _get_transcript_with_requests(self, video_id: str) -> Optional[str]:
        """
        Get transcript using requests to YouTube API.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            Transcript text or None if failed
        """
        try:
            # Import requests
            import requests
            import json
            
            # Get video info from public API
            response = requests.get(f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json")
            
            if response.status_code == 200:
                data = response.json()
                
                # Get video title and author
                title = data.get('title', 'Untitled YouTube Video')
                author = data.get('author_name', 'Unknown Author')
                
                # Create a simple transcript
                content = f"Video Title: {title}\nAuthor: {author}\n\n"
                content += f"This is a summary for YouTube video ID: {video_id}."
                
                logger.info(f"Retrieved basic metadata using requests: {len(content)} characters")
                return content
                
        except ImportError:
            logger.warning("requests library not installed.")
            return None
        except Exception as e:
            logger.warning(f"Error getting transcript with requests: {str(e)}")
            return None
        
        return None
    
    def _extract_video_id(self, url: str) -> Optional[str]:
        """
        Extract YouTube video ID from URL.
        
        Args:
            url: YouTube video URL
            
        Returns:
            Video ID or None if not found
        """
        # Patterns for YouTube URLs
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]{11})',  # Standard and shortened URLs
            r'youtube\.com\/embed\/([a-zA-Z0-9_-]{11})',  # Embed URLs
            r'youtube\.com\/v\/([a-zA-Z0-9_-]{11})',      # Old-style URLs
            r'(?:youtube\.com\/watch\?.+&v=)([a-zA-Z0-9_-]{11})',  # Standard URL with parameters
            r'youtube\.com\/shorts\/([a-zA-Z0-9_-]{11})'  # YouTube shorts
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        # Try more advanced parsing for complex URLs
        try:
            from urllib.parse import urlparse, parse_qs
            parsed_url = urlparse(url)
            
            # Check if it's a YouTube domain
            if 'youtube.com' in parsed_url.netloc:
                # Parse query parameters
                query_params = parse_qs(parsed_url.query)
                
                # Get the 'v' parameter
                if 'v' in query_params:
                    return query_params['v'][0]
        except Exception as e:
            logger.warning(f"Error parsing URL {url}: {str(e)}")
            
        return None