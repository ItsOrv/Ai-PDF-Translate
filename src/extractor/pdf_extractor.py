"""
Module for extracting text and layout information from PDF documents.
"""

import os
import logging
import fitz  # PyMuPDF
from typing import List, Dict, Any, Optional, Tuple
import json

from src.models.text_element import TextElement
from src.extractor.layout_analyzer import LayoutAnalyzer
from src.utils.file_utils import FileUtils

# Configure logging
logger = logging.getLogger(__name__)


class PDFExtractor:
    """
    Extracts text and layout information from PDF files.
    """
    
    def __init__(self, pdf_path: str):
        """
        Initialize the PDFExtractor with a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
        """
        self.pdf_path = pdf_path
        
        if not os.path.exists(pdf_path):
            logger.error(f"PDF file not found: {pdf_path}")
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
            
        logger.info(f"Initialized PDF extractor for {pdf_path}")
    
    def extract_text_with_layout(self) -> List[TextElement]:
        """
        Extract text with layout information from the PDF.
        
        Returns:
            List of TextElement objects with position and text information
        """
        try:
            # Open the PDF document
            doc = fitz.open(self.pdf_path)
            logger.info(f"Opened PDF document: {self.pdf_path} with {len(doc)} pages")
            
            # Initialize layout analyzer
            layout_analyzer = LayoutAnalyzer()
            
            # Initialize list for all text elements
            all_text_elements = []
            
            # Process each page
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                # Extract words with their positions
                words = []
                for word_info in page.get_text("words"):
                    # word_info format: (x0, y0, x1, y1, word, block_no, line_no, word_no)
                    if len(word_info) >= 5:  # Ensure we have at least the word text
                        x0, y0, x1, y1 = word_info[:4]
                        text = word_info[4]
                        
                        word_dict = {
                            "text": text,
                            "page_num": page_num,
                            "x0": x0,
                            "y0": y0,
                            "x1": x1,
                            "y1": y1,
                            "width": x1 - x0,
                            "height": y1 - y0
                        }
                        
                        words.append(word_dict)
                
                # Group words into logical text blocks for this page
                text_blocks = layout_analyzer.group_words_into_blocks(words)
                
                # Extract font information for each block
                text_blocks_with_fonts = self._extract_font_info(text_blocks, doc)
                
                # Convert to TextElement objects for this page
                page_text_elements = layout_analyzer.blocks_to_text_elements(text_blocks_with_fonts, page_num)
                
                # Add to the overall list
                all_text_elements.extend(page_text_elements)
            
            # Close the document
            doc.close()
            
            logger.info(f"Extracted {len(all_text_elements)} text elements from PDF")
            return all_text_elements
            
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {str(e)}")
            raise
    
    def _extract_font_info(self, text_blocks: List[Dict[str, Any]], doc: fitz.Document) -> List[Dict[str, Any]]:
        """
        Extract approximate font information from the text blocks.
        
        Args:
            text_blocks: List of text blocks
            doc: PDF document
            
        Returns:
            List of text blocks with font information
        """
        # Process each text block
        for block in text_blocks:
            page_num = block["page_num"]
            x = block["x0"]
            y = block["y0"]
            
            # Get the page
            if page_num < len(doc):
                page = doc[page_num]
                
                # Get spans that intersect with this block's position
                spans = self._get_text_spans_at_position(page, x, y)
                
                if spans:
                    # Use the first span's font info
                    span = spans[0]
                    block["font_name"] = span.get("font", "Helvetica")
                    block["font_size"] = span.get("size", 12.0)
                else:
                    # Use default values if no spans are found
                    block["font_name"] = "Helvetica"
                    block["font_size"] = 12.0
                    logger.debug(f"No font info found for block at ({x}, {y}) on page {page_num+1}")
            
        return text_blocks
    
    def _get_text_spans_at_position(self, page: fitz.Page, x: float, y: float) -> List[Dict[str, Any]]:
        """
        Get text spans at the given position.
        
        Args:
            page: PDF page
            x: X-coordinate
            y: Y-coordinate
            
        Returns:
            List of text spans
        """
        try:
            # Get text information as a dictionary
            text_dict = page.get_text("dict")
            
            # Find blocks that contain the position
            matching_spans = []
            
            # Process each block in the page
            for block in text_dict.get("blocks", []):
                # Skip non-text blocks
                if block.get("type") != 0:  # 0 means text block
                    continue
                    
                # Process each line in the block
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        # Get span's bounding box
                        span_x0, span_y0, span_x1, span_y1 = span.get("bbox", (0, 0, 0, 0))
                        
                        # Check if the position is inside the span
                        if span_x0 <= x <= span_x1 and span_y0 <= y <= span_y1:
                            matching_spans.append(span)
            
            return matching_spans
                        
        except Exception as e:
            logger.warning(f"Error getting text spans at position ({x}, {y}): {str(e)}")
            return []
    
    def get_document_metadata(self) -> Dict[str, Any]:
        """
        Get metadata from the PDF document.
        
        Returns:
            Dictionary with metadata information
        """
        try:
            # Open the PDF document
            doc = fitz.open(self.pdf_path)
            
            # Extract metadata
            metadata = {
                "title": doc.metadata.get("title", ""),
                "author": doc.metadata.get("author", ""),
                "subject": doc.metadata.get("subject", ""),
                "creator": doc.metadata.get("creator", ""),
                "producer": doc.metadata.get("producer", ""),
                "page_count": len(doc)
            }
            
            # Close the document
            doc.close()
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error extracting metadata from PDF: {str(e)}")
            return {
                "title": "",
                "author": "",
                "subject": "",
                "creator": "",
                "producer": "",
                "page_count": 0
            } 