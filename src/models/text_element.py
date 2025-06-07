"""
Module for the TextElement class that represents text elements extracted from PDFs.
"""

from typing import Dict, Any, Optional, List, Tuple


class TextElement:
    """
    Represents a text element extracted from a PDF document.
    Contains the original text, position, font information, and translated text.
    """
    
    def __init__(
        self,
        text: str,
        page_number: int,
        x0: float,
        y0: float,
        x1: float,
        y1: float,
        width: Optional[float] = None,
        height: Optional[float] = None,
        font_name: Optional[str] = None,
        font_size: Optional[float] = None,
        color: Optional[Tuple[float, float, float]] = None,
        alignment: Optional[str] = None
    ):
        """
        Initialize a TextElement.
        
        Args:
            text: Original text content
            page_number: Page number where the text appears (0-indexed)
            x0: Left x-coordinate 
            y0: Top y-coordinate
            x1: Right x-coordinate
            y1: Bottom y-coordinate
            width: Width of text element
            height: Height of text element
            font_name: Name of the font used
            font_size: Size of the font used
            color: RGB color tuple (0-1 range)
            alignment: Text alignment ('left', 'right', 'center', or 'justify')
        """
        self.text = text
        self.page_number = page_number
        self.x0 = x0
        self.y0 = y0
        self.x1 = x1
        self.y1 = y1
        self.width = width if width is not None else (x1 - x0)
        self.height = height if height is not None else (y1 - y0)
        self.font_name = font_name
        self.font_size = font_size
        self.color = color or (0, 0, 0)  # Default to black
        self.alignment = alignment
        self.translated_text = None
        self.is_complete = False  # Flag to track if translation is complete
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TextElement':
        """
        Create a TextElement from a dictionary.
        
        Args:
            data: Dictionary containing text element data
            
        Returns:
            TextElement instance
        """
        return cls(
            text=data.get('text', ''),
            page_number=data.get('page', 0),
            x0=float(data.get('x0', 0)),
            y0=float(data.get('y0', 0)),
            x1=float(data.get('x1', 0)),
            y1=float(data.get('y1', 0)),
            width=float(data.get('width', 0)) if 'width' in data else None,
            height=float(data.get('height', 0)) if 'height' in data else None,
            font_name=data.get('font_name'),
            font_size=float(data.get('font_size', 12)) if 'font_size' in data else None,
            color=data.get('color'),
            alignment=data.get('alignment')
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the TextElement to a dictionary.
        
        Returns:
            Dictionary representation of the TextElement
        """
        return {
            'text': self.text,
            'page': self.page_number,
            'x0': self.x0,
            'y0': self.y0,
            'x1': self.x1,
            'y1': self.y1,
            'width': self.width,
            'height': self.height,
            'font_name': self.font_name,
            'font_size': self.font_size,
            'color': self.color,
            'alignment': self.alignment,
            'translated_text': self.translated_text,
            'is_complete': self.is_complete
        }
    
    def set_translated_text(self, translated_text: str) -> None:
        """
        Set the translated text for this element.
        
        Args:
            translated_text: Translated text content
        """
        self.translated_text = translated_text
        self.is_complete = True
    
    def get_position(self) -> Tuple[float, float]:
        """
        Get the position of the text element.
        
        Returns:
            Tuple of (x, y) coordinates representing the top-left position
        """
        return (self.x0, self.y0)
    
    def get_dimensions(self) -> Tuple[float, float]:
        """
        Get the dimensions of the text element.
        
        Returns:
            Tuple of (width, height)
        """
        return (self.width, self.height)
    
    def __repr__(self) -> str:
        """
        String representation of the TextElement.
        
        Returns:
            String representing the TextElement
        """
        return f"TextElement(text='{self.text[:20]}{'...' if len(self.text) > 20 else ''}', page={self.page_number}, pos=({self.x0:.1f}, {self.y0:.1f}))" 