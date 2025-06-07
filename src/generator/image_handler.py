"""
Module for handling images in PDF documents.
"""

import logging
import io
import fitz  # PyMuPDF
from typing import Dict, List, Any, Optional, Tuple
from PIL import Image

logger = logging.getLogger(__name__)


class ImageHandler:
    """
    Handles extraction and insertion of images in PDF documents.
    """
    
    @staticmethod
    def extract_images(pdf_path: str, page_number: int = None) -> List[Dict[str, Any]]:
        """
        Extract images from a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            page_number: Specific page to extract images from, or None for all pages
            
        Returns:
            List of dictionaries with image data and metadata
        """
        images = []
        
        try:
            # Open the PDF document
            pdf_doc = fitz.open(pdf_path)
            
            # Determine which pages to process
            if page_number is not None:
                if 0 <= page_number < len(pdf_doc):
                    pages_to_process = [pdf_doc[page_number]]
                else:
                    logger.warning(f"Page {page_number} out of range")
                    return []
            else:
                pages_to_process = pdf_doc
                
            # Process each page
            for i, page in enumerate(pages_to_process):
                page_number = page.number
                
                # Get images from the page
                image_list = page.get_images(full=True)
                
                # Process each image
                for img_index, img_info in enumerate(image_list):
                    xref = img_info[0]  # xref number of the image
                    
                    try:
                        # Extract image
                        base_image = pdf_doc.extract_image(xref)
                        image_bytes = base_image["image"]
                        image_ext = base_image["ext"]
                        
                        # Get image position and size info
                        bbox = ImageHandler._get_image_bbox(page, xref)
                        
                        if bbox:
                            # Store image data and metadata
                            image_data = {
                                "page_number": page_number,
                                "image_index": img_index,
                                "xref": xref,
                                "bbox": bbox,
                                "image_bytes": image_bytes,
                                "extension": image_ext,
                                "width": bbox.width,
                                "height": bbox.height
                            }
                            
                            images.append(image_data)
                        else:
                            logger.warning(f"Could not determine position for image {img_index} on page {page_number}")
                            
                    except Exception as e:
                        logger.warning(f"Error extracting image {img_index} on page {page_number}: {str(e)}")
            
            # Close the document
            pdf_doc.close()
            
        except Exception as e:
            logger.error(f"Error extracting images: {str(e)}")
            
        return images
        
    @staticmethod
    def _get_image_bbox(page: fitz.Page, xref: int) -> Optional[fitz.Rect]:
        """
        Get the bounding box of an image on a page.
        
        Args:
            page: PDF page
            xref: Image reference
            
        Returns:
            Rectangle bounding box or None if not found
        """
        try:
            # Try to find image bbox in the page's display list
            dl = page.get_displaylist()
            rect = None
            
            for item in dl:
                if item[0] == "i" and item[1] == xref:  # "i" for image
                    rect = item[2]  # item[2] is the rectangle
                    break
                    
            return rect
        except Exception as e:
            logger.warning(f"Error getting image bbox: {str(e)}")
            return None
            
    @staticmethod
    def insert_image_on_canvas(canvas, image_data: Dict[str, Any], page_height: float) -> None:
        """
        Insert an image onto a ReportLab canvas.
        
        Args:
            canvas: ReportLab canvas
            image_data: Image data and metadata
            page_height: Height of the page in points
        """
        try:
            # Extract image data
            image_bytes = image_data["image_bytes"]
            bbox = image_data["bbox"]
            
            # Convert bbox coordinates to ReportLab coordinates (origin at bottom-left)
            x = bbox.x0
            y = page_height - bbox.y1  # Adjust y-coordinate for ReportLab
            width = bbox.width
            height = bbox.height
            
            # Create PIL Image from bytes
            img = Image.open(io.BytesIO(image_bytes))
            
            # Draw image on canvas
            canvas.drawInlineImage(img, x, y, width, height)
            
        except Exception as e:
            logger.warning(f"Error inserting image: {str(e)}")
            
    @staticmethod
    def get_image_count(pdf_path: str) -> int:
        """
        Get the number of images in a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Number of images
        """
        count = 0
        
        try:
            # Open the PDF document
            pdf_doc = fitz.open(pdf_path)
            
            # Process each page
            for page in pdf_doc:
                # Get images from the page
                image_list = page.get_images(full=True)
                count += len(image_list)
                
            # Close the document
            pdf_doc.close()
            
        except Exception as e:
            logger.error(f"Error counting images: {str(e)}")
            
        return count 