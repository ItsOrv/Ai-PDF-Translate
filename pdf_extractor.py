"""
Module for extracting text and layout information from PDF files.
"""
import os
import logging
import pdfplumber
from PyPDF2 import PdfReader
from typing import List, Dict, Any, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PDFExtractor:
    """Class for extracting text and layout information from PDF files."""
    
    def __init__(self, pdf_path: str):
        """
        Initialize the PDF extractor.
        
        Args:
            pdf_path: Path to the PDF file
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
            
        self.pdf_path = pdf_path
        
    def extract_text_with_layout(self) -> List[Dict[str, Any]]:
        """
        Extract text with layout information from the PDF.
        
        Returns:
            List of dictionaries with text and layout information for each text element
        """
        text_elements = []
        
        try:
            # Open the PDF with pdfplumber
            with pdfplumber.open(self.pdf_path) as pdf:
                # Get total number of pages
                total_pages = len(pdf.pages)
                logger.info(f"Extracting text from {total_pages} pages")
                
                # Process each page
                for page_num, page in enumerate(pdf.pages):
                    logger.info(f"Processing page {page_num + 1}/{total_pages}")
                    
                    # Extract text and layout information
                    words = page.extract_words(
                        x_tolerance=3,
                        y_tolerance=3,
                        keep_blank_chars=False,
                        use_text_flow=True
                    )
                    
                    # Group words into text blocks
                    blocks = self._group_words_into_blocks(words)
                    
                    # Store text elements with layout information
                    for block in blocks:
                        # Calculate block boundaries
                        x0 = min(w['x0'] for w in block)
                        y0 = min(w['top'] for w in block)
                        x1 = max(w['x1'] for w in block)
                        y1 = max(w['bottom'] for w in block)
                        
                        # Get font information (approximate)
                        font_info = self._extract_font_info(block)
                        
                        # Join words to form text
                        text = ' '.join(w['text'] for w in block)
                        
                        # Store text element with layout information
                        text_elements.append({
                            'text': text,
                            'page': page_num,
                            'x0': x0,
                            'y0': y0,
                            'x1': x1,
                            'y1': y1,
                            'width': x1 - x0,
                            'height': y1 - y0,
                            'font_size': font_info['size'],
                            'font_name': font_info['name'],
                            'page_width': page.width,
                            'page_height': page.height,
                        })
                        
            return text_elements
            
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {str(e)}")
            raise
            
    def _group_words_into_blocks(self, words: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """
        Group words into logical text blocks based on their positions.
        
        Args:
            words: List of words extracted from a page
            
        Returns:
            List of word groups representing text blocks
        """
        if not words:
            return []
            
        # Sort words by y-position (top to bottom)
        sorted_words = sorted(words, key=lambda w: (w['top'], w['x0']))
        
        blocks = []
        current_block = [sorted_words[0]]
        
        # Set initial line position
        current_line_y = sorted_words[0]['top']
        line_height = sorted_words[0]['bottom'] - sorted_words[0]['top']
        
        # Threshold for considering words to be on the same line (1.5 times line height)
        line_threshold = line_height * 1.5
        
        for word in sorted_words[1:]:
            # Check if word is on the same line
            if abs(word['top'] - current_line_y) <= line_threshold:
                # Add to current block if on same line
                current_block.append(word)
            else:
                # Start a new block
                if current_block:
                    blocks.append(current_block)
                current_block = [word]
                current_line_y = word['top']
                line_height = word['bottom'] - word['top']
                
        # Add the last block
        if current_block:
            blocks.append(current_block)
            
        return blocks
        
    def _extract_font_info(self, words: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract approximate font information from words.
        
        Args:
            words: List of words
            
        Returns:
            Dictionary with font information
        """
        # Calculate average font size
        sizes = [w['bottom'] - w['top'] for w in words]
        avg_size = sum(sizes) / len(sizes) if sizes else 12  # Default to 12pt
        
        # Get font name (if available)
        font_name = 'Helvetica'  # Default font
        
        # Return font information
        return {
            'size': avg_size,
            'name': font_name,
        }
        
    def get_document_metadata(self) -> Dict[str, Any]:
        """
        Get metadata from the PDF document.
        
        Returns:
            Dictionary with document metadata
        """
        try:
            with open(self.pdf_path, 'rb') as file:
                reader = PdfReader(file)
                info = reader.metadata
                
                # Extract basic metadata
                metadata = {
                    'title': info.title if info and hasattr(info, 'title') else None,
                    'author': info.author if info and hasattr(info, 'author') else None,
                    'subject': info.subject if info and hasattr(info, 'subject') else None,
                    'creator': info.creator if info and hasattr(info, 'creator') else None,
                    'producer': info.producer if info and hasattr(info, 'producer') else None,
                    'page_count': len(reader.pages),
                }
                
                return metadata
                
        except Exception as e:
            logger.error(f"Error getting document metadata: {str(e)}")
            return {
                'page_count': 0,
                'error': str(e)
            } 