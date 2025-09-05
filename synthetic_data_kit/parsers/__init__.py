"""
File parser initialization module.
"""
import os
import logging
from typing import Dict, Any, Optional

from synthetic_data_kit.parsers.base_parser import BaseParser
from synthetic_data_kit.parsers.txt_parser import TXTParser
from synthetic_data_kit.parsers.pdf_parser import PDFParser
from synthetic_data_kit.parsers.html_parser import HTMLParser
from synthetic_data_kit.parsers.docx_parser import DOCXParser
from synthetic_data_kit.parsers.ppt_parser import PPTParser
from synthetic_data_kit.parsers.youtube_parser import YouTubeParser

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("parsers")

def determine_parser(file_path: str, config: Optional[Dict[str, Any]] = None) -> BaseParser:
    """
    Determine which parser to use based on the file path or URL.
    
    Args:
        file_path: Path to the file or URL to parse
        config: Optional configuration dictionary
        
    Returns:
        Appropriate parser instance for the file type
    """
    # For URLs
    if file_path.startswith(('http://', 'https://')):
        # YouTube URLs
        if 'youtube.com' in file_path or 'youtu.be' in file_path:
            logger.info(f"Using YouTubeParser for {file_path}")
            return YouTubeParser()
        
        # HTML URLs
        logger.info(f"Using HTMLParser for {file_path}")
        return HTMLParser()
    
    # For files, check extension
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    
    if ext in ['.pdf']:
        logger.info(f"Using PDFParser for {file_path}")
        return PDFParser()
    elif ext in ['.docx', '.doc']:
        logger.info(f"Using DOCXParser for {file_path}")
        return DOCXParser()
    elif ext in ['.html', '.htm']:
        logger.info(f"Using HTMLParser for {file_path}")
        return HTMLParser()
    elif ext in ['.pptx', '.ppt']:
        logger.info(f"Using PPTParser for {file_path}")
        return PPTParser()
    elif ext in ['.txt', '.md', '.rst', '.log']:
        logger.info(f"Using TXTParser for {file_path}")
        return TXTParser()
    else:
        # Default to TXT parser
        logger.warning(f"Unknown file extension: {ext} for {file_path}, defaulting to TXTParser")
        return TXTParser()