"""
Module for rendering text on PDF documents.
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from src.models.text_element import TextElement
from src.utils.rtl_handler import RTLHandler
from src.utils.font_utils import register_persian_fonts, get_text_width

logger = logging.getLogger(__name__)


class TextRenderer:
    """
    Renders text on PDF documents, handling right-to-left text and font selection.
    """
    
    def __init__(self, font_path: Optional[str] = None):
        """
        Initialize the text renderer.
        
        Args:
            font_path: Path to font file, or None to use default
        """
        # Register Persian fonts
        self.default_font = register_persian_fonts()
        logger.info(f"Using {self.default_font} as default font")
    
    def add_text_to_canvas(self, c: canvas.Canvas, text_elements: List[TextElement], page_height: float) -> None:
        """
        Add text elements to a canvas.
        
        Args:
            c: ReportLab canvas
            text_elements: List of TextElement objects to render
            page_height: Height of the page in points
        """
        for i, element in enumerate(text_elements):
            # Skip elements without translated text
            if not element.translated_text or element.translated_text.isspace():
                continue
            
            # Get element position and dimensions
            x = element.x0
            y = page_height - element.y1  # Convert from PDF coordinates (origin at bottom-left)
            width = element.width
            height = element.height
            
            # Debug log for text positioning
            logger.info(f"Rendering text element {i}: pos=({x}, {y}), size=({width}x{height}), text='{element.translated_text[:30]}...'")
            
            # Determine font and size
            font_name, font_size = self._determine_font(element)
            
            # Set font
            c.setFont(font_name, font_size)
            
            # Make sure we have at least a minimum width and height
            if width < 10:
                width = 10
            if height < 10:
                height = 10
                
            # Add some extra margin at the top to avoid text being cut off
            y = y - 2
                
            # Render the text
            self._render_text_block(c, element.translated_text, x, y, width, height, font_name, font_size, None)
    
    def _determine_font(self, element: TextElement) -> Tuple[str, float]:
        """
        Determine the appropriate font and size for a text element.
        
        Args:
            element: TextElement to determine font for
            
        Returns:
            Tuple of (font_name, font_size)
        """
        # Use element's font if available, otherwise use default
        font_name = element.font_name if element.font_name else self.default_font
        
        # Check if font is registered, otherwise use default
        if font_name not in pdfmetrics.getRegisteredFontNames():
            font_name = self.default_font
        
        # Use element's font size if available, otherwise use default
        font_size = element.font_size if element.font_size else 12.0
        
        # Ensure font size is reasonable
        font_size = max(6.0, min(font_size, 72.0))
        
        return font_name, font_size
    
    def _find_optimal_font_size(self, text: str, max_width: float, max_height: float, 
                              font_name: str, starting_font_size: float) -> float:
        """
        Find the optimal font size to fit text within given dimensions.
        
        Args:
            text: Text to render
            max_width: Maximum width
            max_height: Maximum height
            font_name: Font name
            starting_font_size: Initial font size
            
        Returns:
            Optimal font size
        """
        font_size = starting_font_size
        min_font_size = 6.0  # Minimum readable font size
        
        # Try decreasing font sizes until text fits
        while font_size >= min_font_size:
            # Check if text fits with current font size
            lines = self._wrap_text(text, max_width, font_name, font_size)
            line_height = font_size * 1.2
            total_height = len(lines) * line_height
            
            if total_height <= max_height:
                return font_size
            
            # Reduce font size and try again
            font_size *= 0.9  # Reduce by 10%
        
        # Return minimum font size if we couldn't find a better fit
        return min_font_size
    
    def _wrap_text(self, text: str, max_width: float, font_name: str, font_size: float) -> List[str]:
        """
        Wrap text to fit within a maximum width.
        
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
        
        # For Persian text, we need special handling
        is_persian = RTLHandler.is_persian(text)
        
        # Split text into lines based on newlines
        paragraphs = text.split('\n')
        result_lines = []
        
        for paragraph in paragraphs:
            if not paragraph:
                result_lines.append('')
                continue
            
            # For Persian text, we need to handle wrapping differently
            if is_persian:
                # Split into words
                words = paragraph.split()
                current_line = []
                current_width = 0
                
                for word in words:
                    word_width = get_text_width(word, font_name, font_size)
                    
                    # Check if adding this word would exceed max width
                    if current_width + word_width <= max_width or not current_line:
                        current_line.append(word)
                        current_width += word_width + get_text_width(' ', font_name, font_size)
                    else:
                        # Add current line to result and start a new line
                        result_lines.append(' '.join(current_line))
                        current_line = [word]
                        current_width = word_width
                
                # Add the last line
                if current_line:
                    result_lines.append(' '.join(current_line))
            else:
                # For non-Persian text, simpler approach
                words = paragraph.split()
                current_line = []
                current_width = 0
                
                for word in words:
                    word_width = get_text_width(word, font_name, font_size)
                    space_width = get_text_width(' ', font_name, font_size)
                    
                    if current_width + word_width + (space_width if current_line else 0) <= max_width or not current_line:
                        current_line.append(word)
                        current_width += word_width + (space_width if current_line else 0)
                    else:
                        result_lines.append(' '.join(current_line))
                        current_line = [word]
                        current_width = word_width
                
                if current_line:
                    result_lines.append(' '.join(current_line))
        
        return result_lines
    
    def _render_text_block(self, c: canvas.Canvas, text: str, x: float, y: float, 
                         width: float, height: float, font_name: str, font_size: float, 
                         alignment: Optional[str] = None) -> None:
        """
        Render a block of text on the canvas.
        
        Args:
            c: ReportLab canvas
            text: Text to render
            x: X coordinate (left)
            y: Y coordinate (top)
            width: Width of text block
            height: Height of text block
            font_name: Font name
            font_size: Font size
            alignment: Text alignment ('left', 'right', 'center', or 'justify')
        """
        # Determine if text is Persian
        is_persian = RTLHandler.is_persian(text)
        
        # Determine text alignment
        if alignment is None:
            alignment = 'right' if is_persian else 'left'
        
        # Add a small margin
        margin = 2
        max_width = width - (2 * margin)
        
        # Ensure positive width
        if max_width <= 0:
            max_width = 10
        
        # Wrap text to fit within width
        lines = self._wrap_text(text, max_width, font_name, font_size)
        
        # Calculate line height
        line_height = font_size * 1.2
        
        # Check if text fits in height
        total_height = len(lines) * line_height
        if total_height > height:
            # Try to find a smaller font size that fits
            adjusted_font_size = self._find_optimal_font_size(text, max_width, height, font_name, font_size)
            
            if adjusted_font_size != font_size:
                # Update font size and recalculate
                font_size = adjusted_font_size
                c.setFont(font_name, font_size)
                lines = self._wrap_text(text, max_width, font_name, font_size)
                line_height = font_size * 1.2
        
        # Render each line
        for i, line in enumerate(lines):
            if not line:
                continue
                
            # Calculate vertical position for this line
            line_y = y + (i * line_height)
            
            # Skip if line would be outside page
            if line_y < 0:
                continue
            
            # Prepare text for rendering if Persian
            if is_persian:
                line = RTLHandler.prepare_persian_text(line)
            
            # Render based on alignment
            if alignment == 'right':
                c.drawRightString(x + width - margin, line_y, line)
            elif alignment == 'center':
                c.drawCentredString(x + (width / 2), line_y, line)
            else:  # left or justify (we don't implement justify yet)
                c.drawString(x + margin, line_y, line) 