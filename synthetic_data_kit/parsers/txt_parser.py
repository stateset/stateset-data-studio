"""
Parser for plain text files.
"""
import os
import logging
from typing import Any, Optional

from synthetic_data_kit.parsers.base_parser import BaseParser

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("txt_parser")

class TXTParser(BaseParser):
    """Parser for plain text files."""
    
    def parse(self, file_path: str) -> str:
        """
        Parse a text file and return its content.
        
        Args:
            file_path: Path to the text file
            
        Returns:
            Text content of the file
        """
        logger.info(f"Parsing text file: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Clean the text
            content = self.clean_text(content)
            
            logger.info(f"Successfully parsed text file ({len(content)} characters)")
            return content
        
        except UnicodeDecodeError:
            # Try different encodings
            for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    
                    # Clean the text
                    content = self.clean_text(content)
                    
                    logger.info(f"Successfully parsed text file using {encoding} ({len(content)} characters)")
                    return content
                except Exception:
                    continue
            
            # If all encodings fail, raise the error
            logger.error(f"Failed to parse text file {file_path} with any encoding")
            raise
        
        except Exception as e:
            logger.error(f"Error parsing text file {file_path}: {str(e)}")
            raise