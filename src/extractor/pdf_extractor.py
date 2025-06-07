"""
Module for extracting text and layout information from PDF documents.
"""

import os
import logging
import fitz  # PyMuPDF
from typing import List, Dict, Any, Optional, Tuple

from src.extractor.text_element import TextElement
from src.extractor.layout_analyzer import LayoutAnalyzer

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
        if not os.path.exists(pdf_path):
            error_msg = f"PDF file not found: {pdf_path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
            
        self.pdf_path = pdf_path
        logger.info(f"Initialized PDF extractor for {pdf_path}")
        
    def extract_text_with_layout(self) -> List[TextElement]:
        """
        Extract text along with layout information from the PDF.
        
        Returns:
            List of TextElement objects with text content and layout information
        """
        try:
            # Open the PDF document
            doc = fitz.open(self.pdf_path)
            logger.info(f"Opened PDF document: {self.pdf_path} with {len(doc)} pages")
            
            all_words = []
            
            # Process each page
            for page_num, page in enumerate(doc):
                logger.debug(f"Processing page {page_num + 1}/{len(doc)}")
                
                # Extract words with their positions
                words = page.get_text("words")
                
                # Process each word to extract position and text
                for word in words:
                    x0, y0, x1, y1, text, block_no, line_no, word_no = word
                    
                    # Skip empty words
                    if not text or text.isspace():
                        continue
                        
                    # Create a word dictionary with position information
                    word_dict = {
                        "text": text,
                        "page_num": page_num,
                        "x": x0,
                        "y": y0,  # Note: PDF coordinates are from bottom
                        "width": x1 - x0,
                        "height": y1 - y0
                    }
                    
                    all_words.append(word_dict)
            
            # Group words into logical text blocks
            text_blocks = LayoutAnalyzer.group_words_into_blocks(all_words)
            
            # Extract font information for each block
            text_blocks_with_fonts = self._extract_font_info(text_blocks, doc)
            
            # Convert to TextElement objects
            text_elements = LayoutAnalyzer.convert_blocks_to_text_elements(text_blocks_with_fonts)
            
            # Close the document
            doc.close()
            
            logger.info(f"Extracted {len(text_elements)} text elements from PDF")
            return text_elements
            
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
            x = block["x"]
            y = block["y"]
            
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