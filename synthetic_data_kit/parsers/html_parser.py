"""
Parser for HTML files and web pages.
"""
import os
import logging
import re
from typing import Any, Optional
from urllib.parse import urlparse

from synthetic_data_kit.parsers.base_parser import BaseParser

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("html_parser")

class HTMLParser(BaseParser):
    """Parser for HTML files and web pages. Requires requests and beautifulsoup4."""
    
    def parse(self, file_path: str) -> str:
        """
        Parse an HTML file or URL and return its content.
        
        Args:
            file_path: Path to the HTML file or URL
            
        Returns:
            Extracted text content
        """
        # Check if file_path is a URL
        is_url = file_path.startswith(('http://', 'https://'))
        
        if is_url:
            logger.info(f"Parsing HTML from URL: {file_path}")
            return self._parse_url(file_path)
        else:
            logger.info(f"Parsing HTML file: {file_path}")
            return self._parse_file(file_path)
    
    def _parse_url(self, url: str) -> str:
        """Parse HTML from a URL."""
        try:
            import requests
            from bs4 import BeautifulSoup
            
            # Make HTTP request
            response = requests.get(url, timeout=30)
            response.raise_for_status()  # Raise an exception for HTTP errors
            
            # Parse HTML with BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer"]):
                script.extract()
            
            # Get text content
            content = soup.get_text()
            
            # Clean the text
            content = self._clean_html_content(content)
            
            logger.info(f"Successfully parsed HTML from URL ({len(content)} characters)")
            return content
        
        except ImportError:
            logger.error("HTML parsing requires requests and beautifulsoup4. Please install them.")
            raise ImportError("HTML parsing requires requests and beautifulsoup4 to be installed.")
        
        except Exception as e:
            logger.error(f"Error parsing HTML from URL {url}: {str(e)}")
            raise
    
    def _parse_file(self, file_path: str) -> str:
        """Parse HTML from a local file."""
        try:
            from bs4 import BeautifulSoup
            
            # Read HTML file
            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Parse HTML with BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer"]):
                script.extract()
            
            # Get text content
            content = soup.get_text()
            
            # Clean the text
            content = self._clean_html_content(content)
            
            logger.info(f"Successfully parsed HTML file ({len(content)} characters)")
            return content
        
        except ImportError:
            logger.error("HTML parsing requires beautifulsoup4. Please install it.")
            raise ImportError("HTML parsing requires beautifulsoup4 to be installed.")
        
        except UnicodeDecodeError:
            # Try different encodings
            for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        html_content = f.read()
                    
                    # Parse HTML with BeautifulSoup
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(html_content, 'html.parser')
                    
                    # Remove script and style elements
                    for script in soup(["script", "style", "nav", "footer"]):
                        script.extract()
                    
                    # Get text content
                    content = soup.get_text()
                    
                    # Clean the text
                    content = self._clean_html_content(content)
                    
                    logger.info(f"Successfully parsed HTML file using {encoding} ({len(content)} characters)")
                    return content
                except Exception:
                    continue
            
            # If all encodings fail, raise the error
            logger.error(f"Failed to parse HTML file {file_path} with any encoding")
            raise
        
        except Exception as e:
            logger.error(f"Error parsing HTML file {file_path}: {str(e)}")
            raise
    
    def _clean_html_content(self, text: str) -> str:
        """
        Clean extracted HTML content.
        
        Args:
            text: HTML text content to clean
            
        Returns:
            Cleaned text
        """
        # Replace multiple whitespace characters with a single space
        text = re.sub(r'\s+', ' ', text)
        
        # Replace multiple newlines with two newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Split into paragraphs and clean each paragraph
        paragraphs = text.split('\n\n')
        cleaned_paragraphs = []
        
        for para in paragraphs:
            # Skip empty paragraphs
            if not para.strip():
                continue
                
            # Clean paragraph
            para = re.sub(r'\s+', ' ', para).strip()
            if para:
                cleaned_paragraphs.append(para)
        
        # Rejoin paragraphs with double newlines
        return '\n\n'.join(cleaned_paragraphs)