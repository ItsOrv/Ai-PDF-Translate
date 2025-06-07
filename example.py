"""
Example script demonstrating how to use the Persian PDF Translator.
"""
import os
import logging
from dotenv import load_dotenv

from src.config.app_config import AppConfig
from src.extractor.pdf_extractor import PDFExtractor
from src.translator.translator import GeminiTranslator
from src.generator.pdf_generator import PDFGenerator
from src.utils.file_utils import find_pdf_files, get_output_path

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def translate_pdf(input_path, output_path=None, domain="general", batch_size=5):
    """
    Translate a PDF from English to Persian.
    
    Args:
        input_path: Path to the input PDF file
        output_path: Path where the translated PDF will be saved (optional)
        domain: Translation domain (general, scientific, medical, etc.)
        batch_size: Number of text elements to translate in each batch
    
    Returns:
        Path to the translated PDF file
    """
    # Initialize configuration
    config = AppConfig()
    
    # Generate output path if not provided
    if output_path is None:
        output_path = get_output_path(input_path)
    
    logger.info(f"Translating PDF: {input_path} -> {output_path}")
    logger.info(f"Using domain: {domain}")
    
    # Extract text from PDF
    logger.info("Extracting text from PDF...")
    extractor = PDFExtractor(input_path)
    text_elements = extractor.extract_text_with_layout()
    logger.info(f"Extracted {len(text_elements)} text elements")
    
    # Initialize translator
    logger.info("Initializing translator...")
    translator = GeminiTranslator(domain=domain)
    
    # Translate text elements
    logger.info(f"Translating text elements in batches of {batch_size}...")
    translator.translate_elements(text_elements, batch_size=batch_size)
    
    # Generate translated PDF
    logger.info("Generating translated PDF...")
    generator = PDFGenerator()
    success = generator.generate_translated_pdf(input_path, output_path, text_elements)
    
    if success:
        logger.info(f"Translation completed successfully: {output_path}")
        
        # Add metadata
        metadata = extractor.get_document_metadata()
        metadata["producer"] = "Persian PDF Translator"
        metadata["creator"] = "Persian PDF Translator"
        metadata["title"] = f"{metadata.get('title', 'Translated Document')} (Persian)"
        generator.add_metadata(output_path, metadata)
        
        return output_path
    else:
        logger.error("Failed to generate translated PDF")
        return None


def main():
    """Run an example PDF translation."""
    # Load environment variables (make sure .env file has GEMINI_API_KEY)
    load_dotenv()
    
    # Find PDF files
    pdf_files = find_pdf_files()
    
    if not pdf_files:
        logger.error("No PDF files found in the current directory or samples directory.")
        return
    
    # Use the first PDF file found
    input_path = pdf_files[0]
    output_path = get_output_path(input_path)
    
    logger.info(f"Input PDF: {input_path}")
    logger.info(f"Output PDF: {output_path}")
    
    # Translate the PDF
    translate_pdf(input_path, output_path, batch_size=3)
    
    logger.info(f"Translation completed. Output saved to {output_path}")


if __name__ == "__main__":
    main() 