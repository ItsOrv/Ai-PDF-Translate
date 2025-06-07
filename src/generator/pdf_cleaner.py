"""
Module for removing text from PDF documents while preserving other elements.
"""

import logging
import fitz  # PyMuPDF
from typing import Optional

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
            image_list = page.get_images(full=True)
            
            for img_index, img_info in enumerate(image_list):
                xref = img_info[0]  # xref number of the image
                try:
                    # Extract image
                    base_image = page.parent.extract_image(xref)
                    image_bytes = base_image["image"]
                    
                    # Get image position and size info
                    bbox = PDFCleaner._get_image_bbox(page, xref)
                    if bbox:
                        # Insert image at the same position
                        new_page.insert_image(bbox, stream=image_bytes)
                except Exception as e:
                    logger.warning(f"Error extracting image {img_index} on page {page.number+1}: {str(e)}")
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
            # Try to find image bbox in the page's display list
            dl = page.get_displaylist()
            rect = None
            
            for item in dl:
                if item[0] == "i" and item[1] == xref:  # "i" for image
                    rect = item[2]  # item[2] is the rectangle
                    break
                    
            return rect
        except Exception as e:
            logger.warning(f"Error getting image bbox on page {page.number+1}: {str(e)}")
            return None 