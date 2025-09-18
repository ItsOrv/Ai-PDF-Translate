"""
Module for generating PDFs with translated text.
"""

import os
import logging
import shutil
from typing import List, Dict, Any, Optional
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import fitz  # PyMuPDF

from src.models.text_element import TextElement
from src.generator.text_renderer import TextRenderer
from src.generator.pdf_cleaner import PDFCleaner
from src.utils.file_utils import FileUtils

logger = logging.getLogger(__name__)


class PDFGenerator:
    """
    Generates a PDF document with translated text elements.
    """
    
    def __init__(self, font_path: Optional[str] = None):
        """
        Initialize the PDF Generator.
        
        Args:
            font_path: Path to font file for text rendering, or None to use default
        """
        self.text_renderer = TextRenderer(font_path)
        self.temp_dir = "temp"
        FileUtils.ensure_directory_exists(self.temp_dir)
        
    def generate_translated_pdf(
        self, 
        original_pdf_path: str, 
        output_pdf_path: str, 
        translated_elements: List[TextElement]
    ) -> bool:
        """
        Generate a PDF with translated text.
        
        Args:
            original_pdf_path: Path to the original PDF
            output_pdf_path: Path where the translated PDF will be saved
            translated_elements: List of TextElement objects with translated text
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Generating translated PDF from {original_pdf_path} to {output_pdf_path}")
            
            # Create a clean PDF without text
            clean_pdf_path = os.path.join(self.temp_dir, "clean_pdf.pdf")
            PDFCleaner.remove_text(original_pdf_path, clean_pdf_path)
            
            # Get document dimensions from original PDF
            doc_info = self._get_document_info(original_pdf_path)
            
            # Generate PDF pages with translated text only
            text_pdf_path = os.path.join(self.temp_dir, "text_pdf.pdf")
            self._generate_text_pdf(text_pdf_path, translated_elements, doc_info)
            
            # Merge the clean PDF and text PDF
            self._merge_pdfs(clean_pdf_path, text_pdf_path, output_pdf_path)
            
            # Clean up temporary files
            self._cleanup_temp_files([clean_pdf_path, text_pdf_path])
            
            logger.info(f"Successfully generated translated PDF at {output_pdf_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error generating translated PDF: {str(e)}")
            return False
    
    def _get_document_info(self, pdf_path: str) -> Dict[str, Any]:
        """
        Get document information including page dimensions.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary with document information
        """
        doc_info = {"pages": []}
        
        try:
            # Open the PDF document
            pdf_doc = fitz.open(pdf_path)
            
            # Get general document information
            doc_info["page_count"] = len(pdf_doc)
            
            # Get page-specific information
            for page_num in range(len(pdf_doc)):
                page = pdf_doc[page_num]
                page_info = {
                    "width": page.rect.width,
                    "height": page.rect.height,
                    "rotation": page.rotation
                }
                doc_info["pages"].append(page_info)
            
            # Close the document
            pdf_doc.close()
            
        except Exception as e:
            logger.error(f"Error getting document info: {str(e)}")
            
        return doc_info
    
    def _generate_text_pdf(self, output_path: str, text_elements: List[TextElement], doc_info: Dict[str, Any]) -> None:
        """
        Generate a PDF with only translated text.
        
        Args:
            output_path: Path where the text-only PDF will be saved
            text_elements: List of TextElement objects with translated text
            doc_info: Dictionary with document information
        """
        try:
            # Log the number of text elements
            logger.info(f"Generating text PDF with {len(text_elements)} text elements")
            
            # Debug: Check which elements have translated text
            for i, element in enumerate(text_elements):
                logger.info(f"Element {i}: text='{element.text[:20]}...', translated_text={element.translated_text is not None}, translated={element.is_complete}")
            
            # Group text elements by page
            elements_by_page = {}
            for element in text_elements:
                page_num = element.page_number
                if page_num not in elements_by_page:
                    elements_by_page[page_num] = []
                elements_by_page[page_num].append(element)
            
            # Log elements by page
            for page_num, elements in elements_by_page.items():
                logger.info(f"Page {page_num}: {len(elements)} elements")
            
            # Create a new PDF with ReportLab
            c = canvas.Canvas(output_path)
            
            # Process each page
            for page_num in range(doc_info["page_count"]):
                if page_num in elements_by_page:
                    page_info = doc_info["pages"][page_num]
                    width = page_info["width"]
                    height = page_info["height"]
                    
                    # Set page size to match original
                    c.setPageSize((width, height))
                    
                    logger.info(f"Rendering page {page_num} with dimensions {width}x{height}")
                    
                    # Render text elements for this page
                    self.text_renderer.add_text_to_canvas(
                        c, 
                        elements_by_page[page_num], 
                        height
                    )
                    
                else:
                    logger.warning(f"No text elements found for page {page_num}")
                    
                # Finalize the page
                c.showPage()
            
            # Save the PDF
            c.save()
            logger.info(f"Text PDF saved to {output_path}")
            
        except Exception as e:
            logger.error(f"Error generating text PDF: {str(e)}")
            raise
    
    def _merge_pdfs(self, clean_pdf_path: str, text_pdf_path: str, output_path: str) -> None:
        """
        Merge a clean PDF (without text) and a text-only PDF.
        
        Args:
            clean_pdf_path: Path to PDF with images and other non-text elements
            text_pdf_path: Path to PDF with only text elements
            output_path: Path where the merged PDF will be saved
        """
        try:
            # Open the source PDFs
            pdf_clean = fitz.open(clean_pdf_path)
            pdf_text = fitz.open(text_pdf_path)
            
            # Debug info about PDFs
            logger.info(f"Clean PDF has {len(pdf_clean)} pages")
            logger.info(f"Text PDF has {len(pdf_text)} pages")
            
            # Check if text PDF pages are empty
            for page_num in range(len(pdf_text)):
                text_content = pdf_text[page_num].get_text("text")
                logger.info(f"Text PDF page {page_num} text length: {len(text_content)}")
            
            # Create a new PDF document
            pdf_result = fitz.open()
            
            # Process each page - use the maximum number of pages from either document
            max_pages = max(len(pdf_clean), len(pdf_text))
            
            for page_num in range(max_pages):
                # Determine page dimensions - use the clean PDF if available, otherwise the text PDF
                if page_num < len(pdf_clean):
                    width = pdf_clean[page_num].rect.width
                    height = pdf_clean[page_num].rect.height
                elif page_num < len(pdf_text):
                    width = pdf_text[page_num].rect.width
                    height = pdf_text[page_num].rect.height
                else:
                    # This shouldn't happen due to max_pages, but just in case
                    continue
                
                # Create a new page in the result PDF
                result_page = pdf_result.new_page(width=width, height=height)
                logger.info(f"Created result page {page_num} with dimensions {width}x{height}")
                
                # The key issue is in these next sections. Instead of just using show_pdf_page,
                # we'll use a more direct approach to copying content
                
                # Add content from the clean page (images, etc.) if it exists
                if page_num < len(pdf_clean):
                    try:
                        # Check if clean page has content
                        clean_has_content = False
                        try:
                            # Try to get some content - images or xobjects
                            if pdf_clean[page_num].get_images() or pdf_clean[page_num].get_xobjects():
                                clean_has_content = True
                        except Exception:
                            # If we can't check content, assume there might be some
                            clean_has_content = True
                        
                        if clean_has_content:
                            # Create a temporary file for this clean page
                            temp_clean_page_path = os.path.join(self.temp_dir, f"temp_clean_page_{page_num}.pdf")
                            temp_clean_doc = fitz.open()
                            temp_page = temp_clean_doc.new_page(width=width, height=height)
                            
                            # Copy content from clean PDF to temp page using PyMuPDF's more direct approach
                            clean_page = pdf_clean[page_num]
                            temp_page.show_pdf_page(
                                temp_page.rect,
                                pdf_clean,
                                page_num,
                                clip=None,  # No clipping
                                keep_proportion=True,
                                overlay=True  # Important: overlay content
                            )
                            
                            # Save temp doc
                            temp_clean_doc.save(temp_clean_page_path)
                            temp_clean_doc.close()
                            
                            # Now add this to our result page
                            result_page.show_pdf_page(
                                result_page.rect,
                                fitz.open(temp_clean_page_path),
                                0,  # First page of temp doc
                                clip=None,
                                keep_proportion=True,
                                overlay=False  # Base layer
                            )
                            
                            logger.info(f"Added content from clean PDF page {page_num}")
                            
                            # Clean up temp file
                            if os.path.exists(temp_clean_page_path):
                                os.remove(temp_clean_page_path)
                        else:
                            logger.warning(f"Clean PDF page {page_num} appears to be empty, skipping")
                    except Exception as e:
                        logger.error(f"Error showing clean page {page_num}: {str(e)}")
                
                # Add content from the text page if it exists
                if page_num < len(pdf_text):
                    try:
                        # Check if the text page is empty
                        if pdf_text[page_num].get_text("text").strip():
                            # Create a temporary file for this text page
                            temp_text_page_path = os.path.join(self.temp_dir, f"temp_text_page_{page_num}.pdf")
                            temp_text_doc = fitz.open()
                            temp_page = temp_text_doc.new_page(width=width, height=height)
                            
                            # Copy content from text PDF to temp page
                            temp_page.show_pdf_page(
                                temp_page.rect,
                                pdf_text,
                                page_num,
                                clip=None,  # No clipping
                                keep_proportion=True,
                                overlay=True  # Important: overlay content
                            )
                            
                            # Save temp doc
                            temp_text_doc.save(temp_text_page_path)
                            temp_text_doc.close()
                            
                            # Now add this to our result page
                            result_page.show_pdf_page(
                                result_page.rect,
                                fitz.open(temp_text_page_path),
                                0,  # First page of temp doc
                                clip=None,
                                keep_proportion=True,
                                overlay=True  # Overlay on top of images
                            )
                            
                            logger.info(f"Added content from text PDF page {page_num}")
                            
                            # Clean up temp file
                            if os.path.exists(temp_text_page_path):
                                os.remove(temp_text_page_path)
                        else:
                            logger.warning(f"Text PDF page {page_num} appears to be empty, skipping")
                    except Exception as e:
                        logger.error(f"Error showing text page {page_num}: {str(e)}")
            
            # Save the result
            pdf_result.save(output_path)
            logger.info(f"Saved merged PDF to {output_path}")
            
            # Close all documents
            pdf_clean.close()
            pdf_text.close()
            pdf_result.close()
            
        except Exception as e:
            logger.error(f"Error merging PDFs: {str(e)}")
            raise
    
    def _cleanup_temp_files(self, file_paths: List[str]) -> None:
        """
        Delete temporary files.
        
        Args:
            file_paths: List of file paths to delete
        """
        for file_path in file_paths:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as e:
                    logger.warning(f"Error cleaning up temp file {file_path}: {str(e)}")
                    
    def add_metadata(self, pdf_path: str, metadata: Dict[str, str]) -> bool:
        """
        Add metadata to a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            metadata: Dictionary with metadata fields like title, author, subject
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create a temporary copy of the PDF
            temp_path = os.path.join(self.temp_dir, "temp_metadata.pdf")
            shutil.copy(pdf_path, temp_path)
            
            # Open the PDF document
            pdf_doc = fitz.open(temp_path)
            
            # Set metadata
            meta_dict = {}
            for key, value in metadata.items():
                if key.lower() in ["title", "author", "subject", "keywords", "creator", "producer"]:
                    meta_dict[key] = value
            
            # Update the metadata
            pdf_doc.set_metadata(meta_dict)
            
            # Save with updated metadata - with garbage=4 to compact the PDF
            pdf_doc.save(pdf_path, garbage=4)
            pdf_doc.close()
            
            # Remove temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
            
            logger.info(f"Successfully updated metadata for {pdf_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding metadata to PDF: {str(e)}")
            return False 