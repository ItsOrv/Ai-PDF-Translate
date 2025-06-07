"""
Persian PDF Translator
---------------------
This script translates PDF documents from English to Persian while preserving
the original layout, font sizes, and positioning of text elements.
"""
import os
import sys
import argparse
import logging
import time
from typing import List, Dict, Any
from dotenv import load_dotenv

from src.extractor.pdf_extractor import PDFExtractor
from src.translator.translator import GeminiTranslator
from src.generator.pdf_generator import PDFGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('pdf_translator.log')
    ]
)
logger = logging.getLogger(__name__)

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Translate PDF from English to Persian')
    parser.add_argument('--input', '-i', type=str, required=True, help='Path to input PDF file')
    parser.add_argument('--output', '-o', type=str, help='Path to output PDF file (default: input_translated.pdf)')
    parser.add_argument('--batch-size', '-b', type=int, default=3, help='Batch size for translation (default: 3)')
    parser.add_argument('--continue-on-error', '-c', action='store_true', help='Continue processing with untranslated text if translation fails')
    parser.add_argument('--domain', '-d', type=str, default='general', 
                        choices=['general', 'scientific', 'genetic', 'medical', 'legal', 'technical'],
                        help='Domain for specialized translation (default: general)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Set output path if not provided
    if not args.output:
        file_name, file_ext = os.path.splitext(args.input)
        args.output = f"{file_name}_translated{file_ext}"
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    return args

def translate_pdf(input_path: str, output_path: str, batch_size: int = 3, continue_on_error: bool = False, domain: str = 'general') -> None:
    """
    Translate a PDF from English to Persian.
    
    Args:
        input_path: Path to the input PDF file
        output_path: Path to the output PDF file
        batch_size: Batch size for translation
        continue_on_error: Whether to continue with untranslated text if translation fails
        domain: Domain for specialized translation
    """
    try:
        start_time = time.time()
        logger.info(f"Starting translation of {input_path}")
        
        # Extract text and layout information from the PDF
        logger.info("Extracting text from PDF...")
        extractor = PDFExtractor(input_path)
        text_elements = extractor.extract_text_with_layout()
        
        # Get document metadata
        metadata = extractor.get_document_metadata()
        logger.info(f"Document has {metadata.get('page_count', 0)} pages")
        
        # Extract text for translation
        texts = [element['text'] for element in text_elements]
        logger.info(f"Extracted {len(texts)} text elements")
        
        # Translate text
        logger.info(f"Translating text to Persian using {domain} domain...")
        translator = GeminiTranslator(domain=domain)
        translated_texts = translator.batch_translate(texts, batch_size=batch_size)
        
        # Add translated text to elements
        for i, translated_text in enumerate(translated_texts):
            text_elements[i]['translated_text'] = translated_text
            
        # Generate the translated PDF
        logger.info("Generating translated PDF...")
        generator = PDFGenerator(output_path)
        generator.generate_translated_pdf(input_path, text_elements)
        
        # Log completion
        elapsed_time = time.time() - start_time
        logger.info(f"Translation completed in {elapsed_time:.2f} seconds")
        logger.info(f"Translated PDF saved to {output_path}")
        
    except Exception as e:
        logger.error(f"Error translating PDF: {str(e)}")
        if continue_on_error:
            logger.info("Continuing with partially translated document...")
            try:
                # Try to generate PDF with partial translations
                generator = PDFGenerator(output_path)
                generator.generate_translated_pdf(input_path, text_elements)
                logger.info(f"Partially translated PDF saved to {output_path}")
            except Exception as inner_e:
                logger.error(f"Failed to generate partial PDF: {str(inner_e)}")
                raise
        else:
            raise

def main():
    """Main entry point for the application."""
    # Load environment variables
    load_dotenv()
    
    # Parse command line arguments
    args = parse_arguments()
    
    # Translate the PDF
    translate_pdf(args.input, args.output, args.batch_size, args.continue_on_error, args.domain)

if __name__ == '__main__':
    main() 