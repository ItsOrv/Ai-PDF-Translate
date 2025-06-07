"""
Module for analyzing PDF layouts and grouping text elements into logical blocks.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple

from src.models.text_element import TextElement

logger = logging.getLogger(__name__)


class LayoutAnalyzer:
    """
    Analyzes PDF layouts and groups text elements into logical blocks based on position and style.
    """
    
    def __init__(self, line_margin: float = 0.3, block_margin: float = 2.0):
        """
        Initialize the layout analyzer.
        
        Args:
            line_margin: Maximum vertical spacing (relative to font size) to consider text as same line
            block_margin: Maximum horizontal spacing (relative to font size) to consider text as same block
        """
        self.line_margin = line_margin
        self.block_margin = block_margin
    
    def group_words_into_blocks(self, words: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Group words into logical text blocks based on their positions and attributes.
        
        Args:
            words: List of word dictionaries with position and text information
            
        Returns:
            List of text blocks with merged attributes
        """
        if not words:
            return []
        
        # Sort words by y-position (top to bottom) then x-position (left to right)
        sorted_words = sorted(words, key=lambda w: (w.get('y0', 0), w.get('x0', 0)))
        
        # Group words into lines
        lines = self._group_words_into_lines(sorted_words)
        
        # Group lines into blocks
        blocks = self._group_lines_into_blocks(lines)
        
        # Finalize text blocks
        return self._finalize_blocks(blocks)
    
    def _group_words_into_lines(self, words: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """
        Group words into lines based on vertical position.
        
        Args:
            words: List of word dictionaries sorted by y and x position
            
        Returns:
            List of lines, where each line is a list of word dictionaries
        """
        lines = []
        current_line = []
        last_y0 = None
        last_height = 0
        
        for word in words:
            y0 = word.get('y0', 0)
            height = word.get('height', 0) or (word.get('y1', y0 + 1) - y0)
            
            # Calculate vertical distance threshold based on font size/height
            # Use the maximum of the current and previous word heights
            threshold = max(height, last_height) * self.line_margin
            
            # Start a new line if vertical distance is significant
            if last_y0 is not None and abs(y0 - last_y0) > threshold:
                if current_line:
                    lines.append(current_line)
                    current_line = []
            
            # Add word to current line
            current_line.append(word)
            last_y0 = y0
            last_height = height
        
        # Add the last line if not empty
        if current_line:
            lines.append(current_line)
        
        return lines
    
    def _group_lines_into_blocks(self, lines: List[List[Dict[str, Any]]]) -> List[List[Dict[str, Any]]]:
        """
        Group lines into text blocks based on horizontal position and style.
        
        Args:
            lines: List of lines, where each line is a list of word dictionaries
            
        Returns:
            List of blocks, where each block is a list of merged line dictionaries
        """
        if not lines:
            return []
        
        blocks = []
        current_block = []
        
        for i, line in enumerate(lines):
            # Skip empty lines
            if not line:
                continue
                
            # Get line properties
            merged_line = self._merge_words_in_line(line)
            
            # Calculate line statistics
            line_x0 = merged_line.get('x0', 0)
            line_x1 = merged_line.get('x1', 0)
            line_width = line_x1 - line_x0
            font_size = merged_line.get('font_size', 12)
            
            # Determine if this line should start a new block
            start_new_block = False
            
            if not current_block:
                # First block
                start_new_block = False
            elif i > 0:
                # Get previous line properties
                prev_merged_line = current_block[-1]
                prev_x0 = prev_merged_line.get('x0', 0)
                prev_x1 = prev_merged_line.get('x1', 0)
                prev_width = prev_x1 - prev_x0
                prev_font = prev_merged_line.get('font_name', '')
                prev_font_size = prev_merged_line.get('font_size', 12)
                
                # Check horizontal overlap
                horizontal_overlap = min(line_x1, prev_x1) - max(line_x0, prev_x0)
                min_width = min(line_width, prev_width)
                
                # Start a new block if:
                # 1. Insufficient horizontal overlap
                # 2. Significant font size difference
                # 3. Different font family
                horizontal_threshold = min_width * 0.5
                if (horizontal_overlap < horizontal_threshold or
                    abs(font_size - prev_font_size) > 2 or
                    self._are_different_font_families(merged_line.get('font_name', ''), prev_font)):
                    start_new_block = True
            
            # Start a new block if needed
            if start_new_block:
                blocks.append(current_block)
                current_block = []
            
            # Add the merged line to the current block
            current_block.append(merged_line)
        
        # Add the last block if not empty
        if current_block:
            blocks.append(current_block)
        
        return blocks
    
    def _merge_words_in_line(self, line: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Merge words in a line into a single entry.
        
        Args:
            line: List of word dictionaries
            
        Returns:
            Dictionary with merged line properties
        """
        if not line:
            return {}
            
        # Sort words by x position
        sorted_line = sorted(line, key=lambda w: w.get('x0', 0))
        
        # Initialize with first word
        merged = dict(sorted_line[0])
        merged['text'] = sorted_line[0].get('text', '')
        
        # Merge with remaining words
        for word in sorted_line[1:]:
            # Update text
            merged['text'] += ' ' + word.get('text', '')
            
            # Update bounding box
            merged['x1'] = max(merged.get('x1', 0), word.get('x1', 0))
            merged['y0'] = min(merged.get('y0', 0), word.get('y0', 0))
            merged['y1'] = max(merged.get('y1', 0), word.get('y1', 0))
            
            # Update width and height
            merged['width'] = merged['x1'] - merged['x0']
            merged['height'] = merged['y1'] - merged['y0']
        
        return merged
    
    def _finalize_blocks(self, blocks: List[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """
        Finalize text blocks by merging lines in each block.
        
        Args:
            blocks: List of blocks, where each block is a list of line dictionaries
            
        Returns:
            List of merged block dictionaries
        """
        finalized_blocks = []
        
        for block in blocks:
            if not block:
                continue
                
            # Merge text from all lines in the block
            merged_block = dict(block[0])
            
            text_parts = []
            for line in block:
                text_parts.append(line.get('text', ''))
            
            merged_block['text'] = '\n'.join(text_parts)
            
            # Calculate bounding box for the entire block
            for line in block[1:]:
                merged_block['x0'] = min(merged_block.get('x0', float('inf')), line.get('x0', float('inf')))
                merged_block['y0'] = min(merged_block.get('y0', float('inf')), line.get('y0', float('inf')))
                merged_block['x1'] = max(merged_block.get('x1', 0), line.get('x1', 0))
                merged_block['y1'] = max(merged_block.get('y1', 0), line.get('y1', 0))
            
            # Update width and height
            merged_block['width'] = merged_block['x1'] - merged_block['x0']
            merged_block['height'] = merged_block['y1'] - merged_block['y0']
            
            # Add to finalized blocks
            finalized_blocks.append(merged_block)
        
        return finalized_blocks
    
    def _are_different_font_families(self, font1: str, font2: str) -> bool:
        """
        Check if two fonts belong to different families.
        
        Args:
            font1: First font name
            font2: Second font name
            
        Returns:
            True if fonts are from different families, False otherwise
        """
        # Extract base family name (before any dashes, which often denote weight/style)
        family1 = font1.split('-')[0].lower() if font1 else ''
        family2 = font2.split('-')[0].lower() if font2 else ''
        
        return family1 != family2
    
    def blocks_to_text_elements(self, blocks: List[Dict[str, Any]], page_number: int) -> List[TextElement]:
        """
        Convert text blocks to TextElement objects.
        
        Args:
            blocks: List of text block dictionaries
            page_number: Page number for the blocks
            
        Returns:
            List of TextElement objects
        """
        elements = []
        
        for block in blocks:
            # Create TextElement from block
            element = TextElement(
                text=block.get('text', ''),
                page_number=page_number,
                x0=block.get('x0', 0),
                y0=block.get('y0', 0),
                x1=block.get('x1', 0),
                y1=block.get('y1', 0),
                width=block.get('width'),
                height=block.get('height'),
                font_name=block.get('font_name'),
                font_size=block.get('font_size'),
                color=block.get('color'),
                alignment=block.get('alignment')
            )
            
            elements.append(element)
        
        return elements 