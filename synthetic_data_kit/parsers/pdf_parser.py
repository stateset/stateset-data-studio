"""
Parser for PDF files.
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
logger = logging.getLogger("pdf_parser")

class PDFParser(BaseParser):
    """Parser for PDF files. Requires PyPDF2 or pdfplumber."""
    
    def parse(self, file_path: str) -> str:
        """
        Parse a PDF file and return its text content.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Extracted text content
        """
        logger.info(f"Parsing PDF file: {file_path}")
        
        try:
            # Try using pdfplumber first
            import pdfplumber
            
            with pdfplumber.open(file_path) as pdf:
                pages = []
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        pages.append(text)
                
                content = "\n\n".join(pages)
                
                # Clean the text
                content = self.clean_text(content)
                
                logger.info(f"Successfully parsed PDF with pdfplumber ({len(content)} characters)")
                return content
        
        except ImportError:
            logger.info("pdfplumber not installed, trying PyPDF2...")
            
            try:
                # Fall back to PyPDF2
                from PyPDF2 import PdfReader
                
                reader = PdfReader(file_path)
                pages = []
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        pages.append(text)
                
                content = "\n\n".join(pages)
                
                # Clean the text
                content = self.clean_text(content)
                
                logger.info(f"Successfully parsed PDF with PyPDF2 ({len(content)} characters)")
                return content
            
            except ImportError:
                logger.error("Neither pdfplumber nor PyPDF2 is installed. Please install one of them.")
                raise ImportError("PDF parsing requires either pdfplumber or PyPDF2 to be installed.")
        
        except Exception as e:
            logger.error(f"Error parsing PDF file {file_path}: {str(e)}")
            raise