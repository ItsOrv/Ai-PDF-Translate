"""
Module for generating a PDF with translated text.
"""
import os
import logging
from typing import List, Dict, Any, Optional
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PyPDF2 import PdfReader, PdfWriter
import io
from decimal import Decimal
import fitz  # PyMuPDF
import tempfile
import shutil

from src.utils.text_utils import prepare_persian_text, is_persian, wrap_text
from src.utils.font_utils import register_persian_fonts, get_available_persian_fonts, get_text_width

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PDFGenerator:
    """Class for generating a PDF with translated text."""
    
    def __init__(self, output_path: str):
        """
        Initialize the PDF generator.
        
        Args:
            output_path: Path where the output PDF will be saved
        """
        self.output_path = output_path
        self.default_persian_font = register_persian_fonts()
        self.available_fonts = get_available_persian_fonts()
        logger.info(f"Using {self.default_persian_font} as default Persian font")
        logger.info(f"Available Persian fonts: {', '.join(self.available_fonts)}")
        
    def generate_translated_pdf(self, original_pdf_path: str, text_elements: List[Dict[str, Any]]) -> None:
        """
        Generate a PDF with translated text.
        
        Args:
            original_pdf_path: Path to the original PDF
            text_elements: List of dictionaries with text and layout information
        """
        try:
            # Create temporary directory for processing files
            with tempfile.TemporaryDirectory() as temp_dir:
                # Path for PDF with text removed
                text_removed_path = os.path.join(temp_dir, "text_removed.pdf")
                
                # Remove text from original PDF using PyMuPDF (fitz)
                self._remove_text_from_pdf(original_pdf_path, text_removed_path)
                
                # Create a PDF writer
                pdf_writer = PdfWriter()
                
                # Open the PDF with text removed
                with open(text_removed_path, 'rb') as file:
                    pdf_reader = PdfReader(file)
                    
                    # Get the number of pages
                    num_pages = len(pdf_reader.pages)
                    
                    # Group text elements by page
                    elements_by_page = self._group_elements_by_page(text_elements, num_pages)
                    
                    # Process each page
                    for page_num in range(num_pages):
                        logger.info(f"Processing page {page_num + 1}/{num_pages}")
                        
                        # Get the page with text removed
                        page_without_text = pdf_reader.pages[page_num]
                        
                        # Create a canvas for the translated text
                        buffer = io.BytesIO()
                        page_width = float(page_without_text.mediabox.width)
                        page_height = float(page_without_text.mediabox.height)
                        c = canvas.Canvas(buffer, pagesize=(page_width, page_height))
                        
                        # Add translated text to the canvas
                        elements = elements_by_page.get(page_num, [])
                        self._add_translated_text_to_canvas(c, elements, page_height)
                        
                        # Save the canvas
                        c.save()
                        
                        # Create a PDF from the canvas
                        buffer.seek(0)
                        text_pdf = PdfReader(buffer)
                        
                        # Merge the page without text and the translated text
                        page_without_text.merge_page(text_pdf.pages[0])
                        
                        # Add the page to the writer
                        pdf_writer.add_page(page_without_text)
                    
                    # Write the output PDF
                    with open(self.output_path, 'wb') as output_file:
                        pdf_writer.write(output_file)
                        
                logger.info(f"Generated translated PDF: {self.output_path}")
                
        except Exception as e:
            logger.error(f"Error generating PDF: {str(e)}")
            raise
    
    def _remove_text_from_pdf(self, input_path: str, output_path: str) -> None:
        """
        Remove text from PDF while preserving images and other elements.
        
        Args:
            input_path: Path to the input PDF
            output_path: Path to save the PDF with text removed
        """
        try:
            # Open the PDF
            pdf_doc = fitz.open(input_path)
            
            # Create a new PDF document
            new_pdf = fitz.open()
            
            # Process each page
            for page_num in range(len(pdf_doc)):
                page = pdf_doc[page_num]
                
                # Create a new page in the output document with the same dimensions
                new_page = new_pdf.new_page(width=page.rect.width, height=page.rect.height)
                
                # Extract and insert images from the original page to the new page
                image_list = page.get_images(full=True)
                
                for img_index, img_info in enumerate(image_list):
                    xref = img_info[0]  # xref number of the image
                    try:
                        # Extract image
                        base_image = pdf_doc.extract_image(xref)
                        image_bytes = base_image["image"]
                        
                        # Get image position and size info
                        bbox = self._get_image_bbox(page, xref)
                        if bbox:
                            # Insert image at the same position
                            new_page.insert_image(bbox, stream=image_bytes)
                    except Exception as e:
                        logger.warning(f"Error extracting image {img_index} on page {page_num+1}: {str(e)}")
                
                # Extract and copy form XObjects (complex elements like logos, charts, etc.)
                for xref in page.get_xobjects():
                    try:
                        new_page._copy_xobj_contents(page, xref)
                    except Exception as e:
                        logger.warning(f"Error copying XObject {xref} on page {page_num+1}: {str(e)}")
                        
                # Copy annotations (except text annotations)
                for annot in page.annots():
                    if annot.type[0] not in (3, 4, 8, 9, 10, 11, 12, 13, 22):  # Skip text-related annotations
                        try:
                            new_page.add_annot(annot.rect, annot.type[0], annot.info)
                        except Exception as e:
                            logger.warning(f"Error copying annotation on page {page_num+1}: {str(e)}")
                
                # Copy links
                for link in page.links():
                    try:
                        new_page.insert_link(link)
                    except Exception as e:
                        logger.warning(f"Error copying link on page {page_num+1}: {str(e)}")
            
            # Save the new PDF with text removed
            new_pdf.save(output_path)
            new_pdf.close()
            pdf_doc.close()
            
            logger.info(f"Text removed from PDF and saved to {output_path}")
            
        except Exception as e:
            logger.error(f"Error removing text from PDF: {str(e)}")
            raise
    
    def _get_image_bbox(self, page, xref):
        """
        Get the bounding box of an image on a page.
        
        Args:
            page: PDF page
            xref: Image reference
            
        Returns:
            Rectangle bounding box or None if not found
        """
        # Try to find image bbox in the page's display list
        try:
            dl = page.get_displaylist()
            rect = None
            
            for item in dl:
                if item[0] == "i" and item[1] == xref:  # This is our image
                    # Return the rectangle
                    return fitz.Rect(item[2])
            
            # If we couldn't find the exact reference, estimate based on image size
            base_image = page.parent.extract_image(xref)
            width, height = base_image.get("width", 0), base_image.get("height", 0)
            
            # Create a rectangle with the image dimensions
            # This is approximate and may not be correctly positioned
            return fitz.Rect(0, 0, width, height)
        except:
            # Fallback: return the whole page rect
            return None
            
    def _group_elements_by_page(self, elements: List[Dict[str, Any]], num_pages: int) -> Dict[int, List[Dict[str, Any]]]:
        """
        Group text elements by page.
        
        Args:
            elements: List of text elements
            num_pages: Number of pages in the document
            
        Returns:
            Dictionary mapping page numbers to lists of elements
        """
        result = {i: [] for i in range(num_pages)}
        
        for element in elements:
            page = element.get('page', 0)
            if 0 <= page < num_pages:
                result[page].append(element)
                
        return result
        
    def _add_translated_text_to_canvas(self, c: canvas.Canvas, elements: List[Dict[str, Any]], page_height: float) -> None:
        """
        Add translated text to a canvas.
        
        Args:
            c: ReportLab canvas
            elements: List of text elements for the page
            page_height: Height of the page
        """
        # Define page margins to prevent text from going outside printable area
        page_width = float(c._pagesize[0])
        left_margin = 20
        right_margin = 20
        
        for element in elements:
            text = element.get('text', '')
            translated_text = element.get('translated_text', text)
            
            # Skip empty text
            if not translated_text or translated_text.isspace():
                continue
                
            # Get text position and dimensions
            # Convert all values to float to avoid decimal.Decimal compatibility issues
            x = float(element.get('x0', 0))
            # Ensure y1 is properly converted to float
            y1 = element.get('y1', 0)
            if isinstance(y1, Decimal):
                y1 = float(y1)
                
            y = page_height - y1  # Convert from PDF coordinates
            width = float(element.get('width', 0))
            height = float(element.get('height', 0))
            font_size = float(element.get('font_size', 12))
            
            # Make sure we have a minimum width to work with
            width = max(width, 100)  # Ensure at least 100 points width
            
            # Add a small margin to ensure text doesn't touch the edge
            margin = 5
            max_width = width - (2 * margin)
            
            # Ensure the text box doesn't extend beyond page boundaries
            if x < left_margin:
                width = width - (left_margin - x)
                x = left_margin
                max_width = width - (2 * margin)
            
            if x + width > page_width - right_margin:
                width = page_width - right_margin - x
                max_width = width - (2 * margin)
            
            # Determine font style based on original text
            font_name = self._determine_font_style(element.get('font_name', ''), font_size)
            
            # Set font
            c.setFont(font_name, font_size)
            
            # Set text color based on original color if available
            if 'color' in element:
                c.setFillColorRGB(*element['color'])
            
            # Check if text width exceeds available width
            text_width = get_text_width(translated_text, font_name, font_size)
            
            # Adaptive text sizing - ensure the text fits within bounds
            if max_width <= 0:
                max_width = 100  # Fallback to a minimum width
            
            # Determine text alignment - default right alignment for Persian
            text_align = element.get('alignment', 'right' if is_persian(translated_text) else 'left')
            
            # If the text is too wide, we have two options:
            # 1. Wrap the text into multiple lines
            # 2. Reduce the font size to fit
            
            if text_width > max_width:
                # First try: wrap text into multiple lines
                lines = wrap_text(translated_text, max_width, font_name, font_size)
                
                # If we have too many lines for the available height, reduce font size
                line_height = font_size * 1.2
                total_height = len(lines) * line_height
                
                if total_height > height and len(lines) > 1:
                    # Try to find an optimal font size that fits both width and height constraints
                    adjusted_font_size = self._find_optimal_font_size(
                        translated_text, max_width, height, font_name, font_size
                    )
                    
                    # Set the new font size
                    if adjusted_font_size != font_size:
                        font_size = adjusted_font_size
                        c.setFont(font_name, font_size)
                        lines = wrap_text(translated_text, max_width, font_name, font_size)
                        line_height = font_size * 1.2
                
                # Draw multiple lines
                for i, line in enumerate(lines):
                    # Calculate vertical position for each line
                    line_y = y - (i * line_height)
                    
                    # Skip if line is outside vertical page bounds
                    if line_y < 0 or line_y > page_height:
                        continue
                    
                    # Prepare Persian text for rendering (reshape and apply bidi)
                    formatted_line = prepare_persian_text(line)
                    
                    # Handle different alignments
                    if text_align == 'right':
                        # Right align the text (default for Persian)
                        text_x = x + width - margin
                        c.drawRightString(text_x, line_y, formatted_line)
                    elif text_align == 'center':
                        # Center align
                        text_x = x + (width / 2)
                        c.drawCentredString(text_x, line_y, formatted_line)
                    else:
                        # Left align (rare for Persian)
                        text_x = x + margin
                        c.drawString(text_x, line_y, formatted_line)
            else:
                # Prepare Persian text for rendering
                formatted_text = prepare_persian_text(translated_text)
                
                # Handle different alignments for single-line text
                if text_align == 'right':
                    # Right align (default for Persian)
                    text_x = x + width - margin
                    c.drawRightString(text_x, y, formatted_text)
                elif text_align == 'center':
                    # Center align
                    text_x = x + (width / 2)
                    c.drawCentredString(text_x, y, formatted_text)
                else:
                    # Left align (rare for Persian)
                    text_x = x + margin
                    c.drawString(text_x, y, formatted_text)
    
    def _find_optimal_font_size(self, text: str, max_width: float, max_height: float, 
                               font_name: str, starting_font_size: float) -> float:
        """
        Find the optimal font size to fit text within given width and height constraints.
        
        Args:
            text: Text to render
            max_width: Maximum width
            max_height: Maximum height
            font_name: Font name
            starting_font_size: Initial font size to try
            
        Returns:
            Optimal font size
        """
        font_size = starting_font_size
        min_font_size = 6  # Don't go below 6pt for readability
        
        while font_size >= min_font_size:
            # Check if text fits with current font size
            lines = wrap_text(text, max_width, font_name, font_size)
            line_height = font_size * 1.2
            total_height = len(lines) * line_height
            
            # If it fits, we're done
            if total_height <= max_height:
                return font_size
                
            # Reduce font size and try again
            font_size *= 0.9  # Reduce by 10%
            
        # Return the minimum font size if we couldn't find a better fit
        return min_font_size
            
    def _determine_font_style(self, original_font: str, font_size: float) -> str:
        """
        Determine the appropriate Persian font style based on the original font.
        
        Args:
            original_font: Original font name
            font_size: Font size
            
        Returns:
            Appropriate Persian font name
        """
        # Default font
        persian_font = self.default_persian_font
        
        # Check if we should use a bold variant based on the original font
        original_lower = original_font.lower()
        
        if 'bold' in original_lower or 'black' in original_lower:
            if 'Vazirmatn-Bold' in self.available_fonts:
                persian_font = 'Vazirmatn-Bold'
        elif 'light' in original_lower or 'thin' in original_lower:
            if 'Vazirmatn-Light' in self.available_fonts:
                persian_font = 'Vazirmatn-Light'
        elif font_size > 14:  # Headings are often larger
            if 'Vazirmatn-Bold' in self.available_fonts:
                persian_font = 'Vazirmatn-Bold'
                
        return persian_font 