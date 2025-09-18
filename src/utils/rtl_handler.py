"""
Utilities for handling Right-to-Left (RTL) text, particularly Persian.
"""

import re
import logging
from typing import Optional, List
import arabic_reshaper
from bidi.algorithm import get_display
from langdetect import detect, LangDetectException

logger = logging.getLogger(__name__)

# Regex pattern for Persian characters
PERSIAN_PATTERN = re.compile(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]+')


class RTLHandler:
    """
    Handles Right-to-Left (RTL) text processing, particularly for Persian language.
    """
    
    @staticmethod
    def is_persian(text: str) -> bool:
        """
        Check if text contains Persian characters.
        
        Args:
            text: Text to check
            
        Returns:
            True if text likely contains Persian, False otherwise
        """
        if not text or not isinstance(text, str):
            return False
            
        # First check using regex for Persian characters
        if PERSIAN_PATTERN.search(text):
            return True
            
        # If no Persian characters found but text is long enough,
        # try language detection
        if len(text) > 20:
            try:
                lang = detect(text)
                return lang == 'fa'
            except LangDetectException:
                # If language detection fails, rely on regex result
                pass
                
        return False
    
    @staticmethod
    def prepare_persian_text(text: str) -> str:
        """
        Prepare Persian text for rendering in PDFs.
        Applies Arabic reshaping and BiDi algorithm.
        
        Args:
            text: Persian text to prepare
            
        Returns:
            Prepared text ready for rendering
        """
        if not text:
            return ""
            
        try:
            # Apply Arabic reshaping (connects letters properly)
            reshaped_text = arabic_reshaper.reshape(text)
            
            # Apply BiDi algorithm to handle right-to-left text
            prepared_text = get_display(reshaped_text)
            
            return prepared_text
        except Exception as e:
            logger.error(f"Error preparing Persian text: {str(e)}")
            return text  # Return original text if processing fails
    
    @staticmethod
    def clean_text_for_translation(text: str) -> str:
        """
        Clean text before translation by removing excessive whitespace and control characters.
        
        Args:
            text: Text to clean
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
            
        # Remove control characters except newlines and tabs
        cleaned = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', text)
        
        # Replace multiple spaces with single space
        cleaned = re.sub(r' +', ' ', cleaned)
        
        # Replace multiple newlines with at most two
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
        
        # Trim whitespace
        cleaned = cleaned.strip()
        
        return cleaned
    
    @staticmethod
    def get_text_direction(text: str) -> str:
        """
        Determine the text direction (RTL or LTR).
        
        Args:
            text: Text to analyze
            
        Returns:
            'rtl' for right-to-left text, 'ltr' otherwise
        """
        return 'rtl' if RTLHandler.is_persian(text) else 'ltr'
    
    @staticmethod
    def get_alignment_for_text(text: str, default_alignment: Optional[str] = None) -> str:
        """
        Get the appropriate text alignment based on text direction.
        
        Args:
            text: Text to analyze
            default_alignment: Default alignment to use if not determined by text
            
        Returns:
            'right' for RTL text, 'left' for LTR text, or the default_alignment
        """
        if default_alignment:
            return default_alignment
            
        return 'right' if RTLHandler.is_persian(text) else 'left'

    @staticmethod
    def split_rtl_lines(text: str, max_width: float, font_name: str, font_size: float) -> List[str]:
        """
        Split RTL text into lines that fit within a specified width.
        
        Args:
            text: Text to split
            max_width: Maximum width in points
            font_name: Font name
            font_size: Font size
            
        Returns:
            List of text lines
        """
        from src.utils.font_utils import FontUtils
        
        # If text is empty, return empty list
        if not text or text.isspace():
            return []
            
        # Split text by newlines first
        lines = []
        paragraphs = text.split('\n')
        
        for paragraph in paragraphs:
            if not paragraph or paragraph.isspace():
                lines.append('')
                continue
                
            # For RTL text, we need character-by-character processing
            current_line = ''
            current_width = 0
            
            # Process each character
            chars = list(paragraph)
            for char in chars:
                # Calculate width of character
                char_width = FontUtils.get_text_width(char, font_name, font_size)
                
                # If adding this character would exceed max width, start new line
                if current_width + char_width > max_width and current_line:
                    lines.append(current_line)
                    current_line = char
                    current_width = char_width
                else:
                    current_line += char
                    current_width += char_width
                    
            # Add the last line
            if current_line:
                lines.append(current_line)
                
        return lines 