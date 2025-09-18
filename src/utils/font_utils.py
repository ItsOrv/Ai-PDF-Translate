"""
Utility functions for font handling and text rendering.
"""

import os
import logging
import tempfile
import shutil
from typing import List, Dict, Optional, Tuple
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.fonts import addMapping

logger = logging.getLogger(__name__)

# Default Persian font files
DEFAULT_PERSIAN_FONTS = {
    'Vazirmatn': 'Vazirmatn-Regular.ttf',
    'Vazirmatn-Bold': 'Vazirmatn-Bold.ttf',
    'Vazirmatn-Light': 'Vazirmatn-Light.ttf',
    'Sahel': 'Sahel.ttf',
    'Sahel-Bold': 'Sahel-Bold.ttf',
    'Tanha': 'Tanha.ttf'
}


def register_persian_fonts() -> str:
    """
    Register Persian fonts for use with ReportLab.
    
    Returns:
        Name of the default Persian font that was registered
    """
    # Default font to use if none of the preferred fonts are available
    default_font = 'Vazirmatn'
    registered_fonts = []
    
    try:
        # Look for fonts in common locations
        font_dirs = [
            os.path.join(os.path.dirname(__file__), '..', '..', 'fonts'),  # Project fonts directory
            os.path.join(os.path.expanduser('~'), '.fonts'),  # User fonts directory
            '/usr/share/fonts/truetype',  # Linux system fonts
            '/System/Library/Fonts',  # macOS system fonts
            'C:\\Windows\\Fonts'  # Windows system fonts
        ]
        
        # Try to find and register each font
        for font_name, font_file in DEFAULT_PERSIAN_FONTS.items():
            registered = False
            
            for font_dir in font_dirs:
                if not os.path.exists(font_dir):
                    continue
                    
                # Look for the font file
                font_path = os.path.join(font_dir, font_file)
                if os.path.exists(font_path):
                    try:
                        # Register the font with ReportLab
                        pdfmetrics.registerFont(TTFont(font_name, font_path))
                        registered_fonts.append(font_name)
                        registered = True
                        logger.info(f"Registered font: {font_name} from {font_path}")
                        break
                    except Exception as e:
                        logger.warning(f"Failed to register font {font_name}: {str(e)}")
            
            if not registered:
                logger.warning(f"Could not find font file for {font_name}")
        
        # If no fonts were registered, use a fallback approach
        if not registered_fonts:
            logger.warning("No Persian fonts found. Attempting to use fallback fonts.")
            
            # Try to use Arial or Helvetica as fallback
            for fallback in ['Arial', 'Helvetica']:
                try:
                    # These should be built-in to ReportLab
                    if fallback not in pdfmetrics.getRegisteredFontNames():
                        pdfmetrics.registerFont(TTFont(fallback, fallback))
                    default_font = fallback
                    logger.info(f"Using {fallback} as fallback font")
                    break
                except:
                    continue
        else:
            # Use the first registered font as default
            default_font = registered_fonts[0]
            
        return default_font
        
    except Exception as e:
        logger.error(f"Error registering fonts: {str(e)}")
        return 'Helvetica'  # Return a safe default


def get_available_persian_fonts() -> List[str]:
    """
    Get a list of available Persian fonts.
    
    Returns:
        List of registered Persian font names
    """
    registered_fonts = pdfmetrics.getRegisteredFontNames()
    
    # Filter for Persian fonts
    persian_fonts = [
        font for font in registered_fonts 
        if font in DEFAULT_PERSIAN_FONTS or 'vazir' in font.lower() or 'sahel' in font.lower()
    ]
    
    return persian_fonts


def download_persian_fonts(target_dir: Optional[str] = None) -> bool:
    """
    Download Persian fonts if they are not already available.
    
    Args:
        target_dir: Directory to save the downloaded fonts
        
    Returns:
        True if fonts were downloaded successfully, False otherwise
    """
    import requests
    
    # Font URLs
    font_urls = {
        'Vazirmatn-Regular.ttf': 'https://github.com/rastikerdar/vazirmatn/raw/master/fonts/ttf/Vazirmatn-Regular.ttf',
        'Vazirmatn-Bold.ttf': 'https://github.com/rastikerdar/vazirmatn/raw/master/fonts/ttf/Vazirmatn-Bold.ttf',
        'Vazirmatn-Light.ttf': 'https://github.com/rastikerdar/vazirmatn/raw/master/fonts/ttf/Vazirmatn-Light.ttf'
    }
    
    # Determine target directory
    if target_dir is None:
        target_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'fonts')
    
    # Create directory if it doesn't exist
    if not os.path.exists(target_dir):
        try:
            os.makedirs(target_dir)
        except Exception as e:
            logger.error(f"Failed to create fonts directory: {str(e)}")
            return False
    
    success = True
    
    # Download each font
    for font_file, url in font_urls.items():
        target_path = os.path.join(target_dir, font_file)
        
        # Skip if font already exists
        if os.path.exists(target_path):
            logger.info(f"Font already exists: {font_file}")
            continue
        
        try:
            logger.info(f"Downloading font: {font_file}")
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            with open(target_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
            logger.info(f"Downloaded font: {font_file}")
        except Exception as e:
            logger.error(f"Failed to download font {font_file}: {str(e)}")
            success = False
    
    return success


def get_text_width(text: str, font_name: str, font_size: float) -> float:
    """
    Calculate the width of text in the given font and size.
    
    Args:
        text: Text to measure
        font_name: Font name
        font_size: Font size in points
        
    Returns:
        Width of the text in points
    """
    try:
        # Get the font
        font = pdfmetrics.getFont(font_name)
        
        # Method 1: Try using stringWidth from pdfmetrics (most reliable)
        try:
            width = pdfmetrics.stringWidth(text, font_name, font_size)
            return width
        except Exception:
            pass
            
        # Method 2: Try using face.getCharWidth
        try:
            face = font.face
            width = 0
            for char in text:
                if hasattr(face, 'getCharWidth'):
                    width += face.getCharWidth(ord(char)) / 1000 * font_size
                else:
                    # Use a fallback if getCharWidth is not available
                    # This is a common issue with some font types
                    width += 0.6 * font_size  # Rough estimate for character width
            return width
        except Exception:
            pass
            
        # Method 3: Fallback to a rough estimate based on average character width
        # For Persian text, usually need more space
        if any(ord(c) > 127 for c in text):  # Non-ASCII characters
            return len(text) * font_size * 0.7  # Persian/Arabic characters
        else:
            return len(text) * font_size * 0.6  # ASCII characters
            
    except Exception as e:
        logger.warning(f"Error calculating text width: {str(e)}")
        # Final fallback
        return len(text) * font_size * 0.65 