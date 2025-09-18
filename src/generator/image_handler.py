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
                try:
                    image_list = page.get_images(full=True)
                    if not image_list:
                        logger.info(f"No images found on page {page_number} using get_images()")
                except Exception as e:
                    logger.warning(f"Error getting images from page {page_number}: {str(e)}")
                    image_list = []
                
                # Alternative approach using page.get_drawings() to find images
                try:
                    drawings = page.get_drawings()
                    drawing_images = []
                    for drawing in drawings:
                        if drawing["type"] == "image" and "xref" in drawing:
                            # Check if this xref is already in our image_list
                            xref_found = False
                            for img_info in image_list:
                                if img_info[0] == drawing["xref"]:
                                    xref_found = True
                                    break
                            
                            if not xref_found:
                                drawing_images.append((drawing["xref"], None, None, None, None))
                    
                    # Add any new images found in drawings to our image_list
                    if drawing_images:
                        logger.info(f"Found {len(drawing_images)} additional images in drawings on page {page_number}")
                        image_list.extend(drawing_images)
                except Exception as e:
                    logger.warning(f"Error getting drawings from page {page_number}: {str(e)}")
                
                # Process each image
                for img_index, img_info in enumerate(image_list):
                    try:
                        xref = img_info[0]  # xref number of the image
                        
                        # Try to extract image
                        try:
                            base_image = pdf_doc.extract_image(xref)
                            if not base_image:
                                logger.warning(f"Could not extract image {img_index} (xref: {xref}) on page {page_number}")
                                continue
                                
                            image_bytes = base_image.get("image")
                            image_ext = base_image.get("ext", "")
                            
                            if not image_bytes:
                                logger.warning(f"No image data found for image {img_index} (xref: {xref}) on page {page_number}")
                                continue
                        except Exception as e:
                            logger.warning(f"Error extracting image {img_index} (xref: {xref}) on page {page_number}: {str(e)}")
                            continue
                        
                        # Get image position and size info
                        try:
                            bbox = ImageHandler._get_image_bbox(page, xref)
                            
                            if not bbox:
                                # If we couldn't determine the bbox from the page, try to create one from image dimensions
                                img_width = base_image.get("width", 100)
                                img_height = base_image.get("height", 100)
                                
                                # Create a centered rectangle based on image dimensions
                                scale_factor = min(page.rect.width / img_width, page.rect.height / img_height) * 0.8
                                w = img_width * scale_factor
                                h = img_height * scale_factor
                                
                                # Center the image on the page
                                x0 = (page.rect.width - w) / 2
                                y0 = (page.rect.height - h) / 2
                                
                                bbox = fitz.Rect(x0, y0, x0 + w, y0 + h)
                                logger.info(f"Created estimated bbox for image {img_index} (xref: {xref}) on page {page_number}")
                            
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
                            logger.info(f"Successfully extracted image {img_index} (xref: {xref}) from page {page_number}")
                        except Exception as e:
                            logger.warning(f"Error processing bbox for image {img_index} (xref: {xref}) on page {page_number}: {str(e)}")
                    except Exception as e:
                        logger.warning(f"Error processing image {img_index} on page {page_number}: {str(e)}")
            
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
            # Get the image rectangle from the page directly using safer methods
            rect = None
            
            # Method 1: Try to use get_image_bbox if available
            try:
                rect = page.get_image_bbox(xref)
                if rect:
                    return rect
            except (AttributeError, Exception) as e:
                pass  # Silent fail, try next method
                
            # Method 2: Try to use page.get_drawings()
            try:
                drawings = page.get_drawings()
                for drawing in drawings:
                    if drawing["type"] == "image" and drawing.get("xref") == xref:
                        return fitz.Rect(drawing["rect"])
            except Exception:
                pass  # Silent fail, try next method
                
            # Method 3: Attempt to extract image dimensions
            try:
                img_info = page.parent.extract_image(xref)
                if img_info and "width" in img_info and "height" in img_info:
                    # Default to a centered image that takes up 80% of the page
                    # while maintaining aspect ratio
                    img_width = img_info["width"]
                    img_height = img_info["height"]
                    
                    scale = min(
                        page.rect.width / img_width,
                        page.rect.height / img_height
                    ) * 0.8
                    
                    w = img_width * scale
                    h = img_height * scale
                    
                    # Center on page
                    x0 = (page.rect.width - w) / 2
                    y0 = (page.rect.height - h) / 2
                    
                    return fitz.Rect(x0, y0, x0 + w, y0 + h)
            except Exception:
                pass  # Silent fail
            
            # If all methods failed, return None
            return None
            
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