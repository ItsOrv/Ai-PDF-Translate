"""
Module for removing text from PDF documents while preserving other elements.
"""

import logging
import fitz  # PyMuPDF
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


class PDFCleaner:
    """
    Removes text from PDF documents while preserving images, forms, and other elements.
    """
    
    @staticmethod
    def remove_text(input_path: str, output_path: str) -> bool:
        """
        Remove text from a PDF while preserving images and other elements.
        
        Args:
            input_path: Path to the input PDF
            output_path: Path to save the PDF with text removed
            
        Returns:
            True if successful, False otherwise
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
                PDFCleaner._copy_images(page, new_page)
                
                # Copy form XObjects (complex elements like logos, charts, etc.)
                PDFCleaner._copy_xobjects(page, new_page)
                    
                # Copy annotations (except text annotations)
                PDFCleaner._copy_annotations(page, new_page)
                
                # Copy links
                PDFCleaner._copy_links(page, new_page)
            
            # Save the new PDF with text removed
            new_pdf.save(output_path)
            new_pdf.close()
            pdf_doc.close()
            
            logger.info(f"Text removed from PDF and saved to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error removing text from PDF: {str(e)}")
            return False
    
    @staticmethod
    def _copy_images(page: fitz.Page, new_page: fitz.Page) -> None:
        """
        Copy images from one page to another.
        
        Args:
            page: Source page
            new_page: Destination page
        """
        try:
            # Try using page.get_images() to get all images
            try:
                image_list = page.get_images(full=True)
                if not image_list:
                    logger.info(f"No images found on page {page.number+1} using get_images()")
            except Exception as e:
                logger.warning(f"Error getting images from page {page.number+1}: {str(e)}")
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
                    logger.info(f"Found {len(drawing_images)} additional images in drawings on page {page.number+1}")
                    image_list.extend(drawing_images)
            except Exception as e:
                logger.warning(f"Error getting drawings from page {page.number+1}: {str(e)}")
            
            # Process each image
            for img_index, img_info in enumerate(image_list):
                try:
                    xref = img_info[0]  # xref number of the image
                    
                    # Try to extract image
                    try:
                        base_image = page.parent.extract_image(xref)
                        if not base_image:
                            logger.warning(f"Could not extract image {img_index} (xref: {xref}) on page {page.number+1}")
                            continue
                            
                        image_bytes = base_image.get("image")
                        if not image_bytes:
                            logger.warning(f"No image data found for image {img_index} (xref: {xref}) on page {page.number+1}")
                            continue
                    except Exception as e:
                        logger.warning(f"Error extracting image {img_index} (xref: {xref}) on page {page.number+1}: {str(e)}")
                        continue
                    
                    # Get image position and size info
                    try:
                        bbox = PDFCleaner._get_image_bbox(page, xref)
                        if not bbox:
                            # If we couldn't determine the bbox from the page, try to create one from the image size
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
                            logger.info(f"Created estimated bbox for image {img_index} (xref: {xref}) on page {page.number+1}")
                        
                        # Insert image at the position
                        new_page.insert_image(bbox, stream=image_bytes)
                        logger.info(f"Successfully copied image {img_index} (xref: {xref}) to page {page.number+1}")
                    except Exception as e:
                        logger.warning(f"Error inserting image {img_index} (xref: {xref}) on page {page.number+1}: {str(e)}")
                except Exception as e:
                    logger.warning(f"Error processing image {img_index} on page {page.number+1}: {str(e)}")
        except Exception as e:
            logger.warning(f"Error copying images on page {page.number+1}: {str(e)}")
    
    @staticmethod
    def _copy_xobjects(page: fitz.Page, new_page: fitz.Page) -> None:
        """
        Copy form XObjects from one page to another.
        
        Args:
            page: Source page
            new_page: Destination page
        """
        try:
            for xref in page.get_xobjects():
                try:
                    new_page._copy_xobj_contents(page, xref)
                except Exception as e:
                    logger.warning(f"Error copying XObject {xref} on page {page.number+1}: {str(e)}")
        except Exception as e:
            logger.warning(f"Error copying XObjects on page {page.number+1}: {str(e)}")
    
    @staticmethod
    def _copy_annotations(page: fitz.Page, new_page: fitz.Page) -> None:
        """
        Copy non-text annotations from one page to another.
        
        Args:
            page: Source page
            new_page: Destination page
        """
        try:
            for annot in page.annots():
                # Skip text-related annotations
                # Types 3, 4, 8, 9, 10, 11, 12, 13, 22 are text-related
                text_annotation_types = (3, 4, 8, 9, 10, 11, 12, 13, 22)
                if annot.type[0] not in text_annotation_types:
                    try:
                        new_page.add_annot(annot.rect, annot.type[0], annot.info)
                    except Exception as e:
                        logger.warning(f"Error copying annotation on page {page.number+1}: {str(e)}")
        except Exception as e:
            logger.warning(f"Error copying annotations on page {page.number+1}: {str(e)}")
    
    @staticmethod
    def _copy_links(page: fitz.Page, new_page: fitz.Page) -> None:
        """
        Copy links from one page to another.
        
        Args:
            page: Source page
            new_page: Destination page
        """
        try:
            for link in page.links():
                try:
                    new_page.insert_link(link)
                except Exception as e:
                    logger.warning(f"Error copying link on page {page.number+1}: {str(e)}")
        except Exception as e:
            logger.warning(f"Error copying links on page {page.number+1}: {str(e)}")
    
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
            logger.warning(f"Error getting image bbox on page {page.number+1}: {str(e)}")
            return None 