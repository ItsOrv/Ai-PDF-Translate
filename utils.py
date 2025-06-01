"""
Utility functions for handling RTL text and other common operations.
"""
import re
import os
import arabic_reshaper
from bidi.algorithm import get_display
from langdetect import detect
from typing import Dict, Any, List, Tuple
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from pathlib import Path
from reportlab.pdfbase.pdfmetrics import stringWidth

# Register Persian fonts
def register_persian_fonts():
    """Register Persian fonts for use with ReportLab."""
    fonts_dir = Path(os.path.dirname(os.path.abspath(__file__))) / 'fonts'
    
    # Font mappings for registration
    font_files = {
        'Vazirmatn': 'Vazirmatn-Regular.ttf',
        'Vazirmatn-Bold': 'Vazirmatn-Bold.ttf',
        'Vazirmatn-Light': 'Vazirmatn-Light.ttf',
        'Sahel': 'Sahel-Regular.ttf',
        'Samim': 'Samim-Regular.ttf'
    }
    
    # Register available fonts
    registered_fonts = []
    
    for font_name, font_file in font_files.items():
        font_path = fonts_dir / font_file
        if font_path.exists():
            try:
                pdfmetrics.registerFont(TTFont(font_name, str(font_path)))
                registered_fonts.append(font_name)
            except Exception as e:
                print(f"Error registering font {font_name}: {str(e)}")
    
    # If no fonts were registered, use a fallback
    if not registered_fonts:
        print("Warning: No Persian fonts were found. Using default font.")
        return 'Helvetica'
    
    # Return the first registered font as default
    return registered_fonts[0]

def prepare_persian_text(text: str) -> str:
    """
    Prepare Persian text for rendering in PDF.
    Applies Arabic reshaping and BiDi algorithm for proper RTL display.
    """
    # Handle None or empty text
    if not text or text.isspace():
        return ""
        
    # Reshape Arabic/Persian characters
    reshaped_text = arabic_reshaper.reshape(text)
    
    # Apply bidirectional algorithm
    bidi_text = get_display(reshaped_text)
    
    return bidi_text

def is_persian(text: str) -> bool:
    """Check if the text is likely Persian/Farsi."""
    try:
        if not text or text.isspace():
            return False
            
        # Check for Persian characters
        persian_pattern = re.compile(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]')
        if persian_pattern.search(text):
            return True
            
        # Use language detection as fallback
        lang = detect(text)
        return lang == 'fa'
    except:
        return False

def get_text_dimensions(text: str, font_name: str, font_size: int) -> Tuple[float, float]:
    """
    Estimate text dimensions for positioning.
    This is a simplified approximation and may need adjustment.
    """
    # Simplified estimate - this would need to be refined for production
    char_width = font_size * 0.6  # Rough estimate
    
    # For RTL languages, we need to account for different character widths
    if is_persian(text):
        char_width = font_size * 0.8  # Persian characters are often wider
    
    width = len(text) * char_width
    height = font_size * 1.2
    
    return width, height

def get_text_width(text: str, font_name: str, font_size: float) -> float:
    """
    Get accurate text width using ReportLab's stringWidth function.
    
    Args:
        text: Text to measure
        font_name: Font name
        font_size: Font size
        
    Returns:
        Width of the text in points
    """
    # Handle empty text
    if not text or text.isspace():
        return 0
        
    # For Persian text, we need to reshape and apply bidi first
    if is_persian(text):
        prepared_text = prepare_persian_text(text)
        return stringWidth(prepared_text, font_name, font_size)
    else:
        return stringWidth(text, font_name, font_size)

def wrap_text(text: str, max_width: float, font_name: str, font_size: float) -> List[str]:
    """
    Wrap text to fit within maximum width.
    
    Args:
        text: Text to wrap
        max_width: Maximum width in points
        font_name: Font name
        font_size: Font size
        
    Returns:
        List of wrapped text lines
    """
    # Handle empty text
    if not text or text.isspace():
        return []
        
    # For very short text or large width, no need to wrap
    if get_text_width(text, font_name, font_size) <= max_width:
        return [text]
    
    # For Persian text, we need to handle wrapping differently due to RTL
    if is_persian(text):
        # First try a character-by-character approach for Persian
        # This is more accurate for Persian text which doesn't have clear word boundaries in some cases
        result = []
        current_line = ""
        
        # Split into characters
        chars = list(text)
        
        for char in chars:
            test_line = current_line + char
            if get_text_width(test_line, font_name, font_size) <= max_width:
                current_line = test_line
            else:
                if current_line:
                    result.append(current_line)
                    current_line = char
                else:
                    # Character itself is too wide (rare case)
                    result.append(char)
                    current_line = ""
        
        # Add the last line
        if current_line:
            result.append(current_line)
        
        # If we ended up with just one line that's still too wide,
        # fall back to word-based wrapping
        if len(result) <= 1 and get_text_width(result[0], font_name, font_size) > max_width:
            # Try word-based wrapping as a fallback
            # Split text into words (considering Persian word boundaries)
            # Persian space character (ZWNJ) and standard space
            words = re.split(r'[\u200c\s]+', text)
            words = [w for w in words if w]  # Remove empty words
            
            result = []
            current_line = ""
            
            for word in words:
                test_line = current_line + (" " if current_line else "") + word
                if get_text_width(test_line, font_name, font_size) <= max_width:
                    current_line = test_line
                else:
                    if current_line:
                        result.append(current_line)
                        current_line = word
                    else:
                        # Word itself is too wide, need to split it
                        chars = list(word)
                        word_line = ""
                        for char in chars:
                            test_word_line = word_line + char
                            if get_text_width(test_word_line, font_name, font_size) <= max_width:
                                word_line = test_word_line
                            else:
                                if word_line:
                                    result.append(word_line)
                                    word_line = char
                                else:
                                    # Character is too wide (rare case)
                                    result.append(char)
                                    word_line = ""
                        
                        if word_line:
                            result.append(word_line)
                        current_line = ""
            
            # Add the last line
            if current_line:
                result.append(current_line)
    else:
        # For non-Persian text, use standard word-based wrapping
        words = text.split()
        result = []
        current_line = ""
        
        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            if get_text_width(test_line, font_name, font_size) <= max_width:
                current_line = test_line
            else:
                if current_line:
                    result.append(current_line)
                    current_line = word
                else:
                    # Word itself is too wide, need to split it
                    result.append(word)  # For non-Persian, just add the word even if too wide
                    current_line = ""
        
        # Add the last line
        if current_line:
            result.append(current_line)
        
    return result

def clean_text_for_translation(text: str) -> str:
    """Clean text before sending to translation API."""
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Remove control characters
    text = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', text)
    
    return text

def get_available_persian_fonts() -> List[str]:
    """Get a list of available registered Persian fonts."""
    fonts_dir = Path(os.path.dirname(os.path.abspath(__file__))) / 'fonts'
    
    # Font mappings
    font_files = {
        'Vazirmatn': 'Vazirmatn-Regular.ttf',
        'Vazirmatn-Bold': 'Vazirmatn-Bold.ttf',
        'Vazirmatn-Light': 'Vazirmatn-Light.ttf',
        'Sahel': 'Sahel-Regular.ttf',
        'Samim': 'Samim-Regular.ttf'
    }
    
    # Check available fonts
    available_fonts = []
    for font_name, font_file in font_files.items():
        font_path = fonts_dir / font_file
        if font_path.exists():
            available_fonts.append(font_name)
    
    return available_fonts 