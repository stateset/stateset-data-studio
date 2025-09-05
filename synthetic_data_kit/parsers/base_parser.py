"""
Base parser class for handling different file formats.
"""
import os
import logging
from typing import Any, Optional
from abc import ABC, abstractmethod

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("parsers")

class BaseParser(ABC):
    """Base class for file parsers."""
    
    def __init__(self):
        """Initialize parser."""
        pass
    
    @abstractmethod
    def parse(self, file_path: str) -> str:
        """
        Parse a file and return its content as text.
        
        Args:
            file_path: Path to the file to parse
            
        Returns:
            Extracted text content
        """
        pass
    
    def save(self, content: str, output_path: str) -> str:
        """
        Save parsed content to a text file.
        
        Args:
            content: Text content to save
            output_path: Path to save text content
            
        Returns:
            Path to the saved file
        """
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Save content to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"Saved parsed content to {output_path} ({len(content)} characters)")
        return output_path
    
    def clean_text(self, text: str) -> str:
        """
        Clean text content by removing excessive whitespace and normalizing linebreaks.
        
        Args:
            text: Text to clean
            
        Returns:
            Cleaned text
        """
        # Replace multiple newlines with two newlines
        import re
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Replace tabs with spaces
        text = text.replace('\t', '    ')
        
        # Remove excessive spaces
        text = re.sub(r' {3,}', '  ', text)
        
        return text.strip()