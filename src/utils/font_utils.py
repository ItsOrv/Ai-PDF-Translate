"""
Utility functions for font handling, registration, and text measurement.
"""
import os
import logging
from typing import List, Tuple
from pathlib import Path
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import stringWidth

from src.utils.text_utils import prepare_persian_text, is_persian

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def register_persian_fonts() -> str:
    """
    Register Persian fonts for use with ReportLab.
    
    Returns:
        Name of the default registered font
    """
    fonts_dir = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))) / 'fonts'
    
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
                logger.error(f"Error registering font {font_name}: {str(e)}")
    
    # If no fonts were registered, use a fallback
    if not registered_fonts:
        logger.warning("No Persian fonts were found. Using default font.")
        return 'Helvetica'
    
    # Return the first registered font as default
    return registered_fonts[0]

def get_available_persian_fonts() -> List[str]:
    """
    Get a list of available registered Persian fonts.
    
    Returns:
        List of available font names
    """
    fonts_dir = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))) / 'fonts'
    
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

def get_text_dimensions(text: str, font_name: str, font_size: int) -> Tuple[float, float]:
    """
    Estimate text dimensions for positioning.
    
    Args:
        text: Text to measure
        font_name: Font name
        font_size: Font size
    
    Returns:
        Tuple of (width, height) in points
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