"""
Example script demonstrating how to use the Persian PDF Translator.
"""
import os
from dotenv import load_dotenv
from main import translate_pdf

def main():
    """Run an example PDF translation."""
    # Load environment variables (make sure .env file has GEMINI_API_KEY)
    load_dotenv()
    
    # Define input and output paths
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Check for PDFs in the samples directory
    samples_dir = os.path.join(current_dir, 'samples')
    if os.path.exists(samples_dir) and os.path.isdir(samples_dir):
        sample_pdfs = [f for f in os.listdir(samples_dir) if f.endswith('.pdf')]
        if sample_pdfs:
            input_path = os.path.join(samples_dir, sample_pdfs[0])
            output_path = os.path.join(current_dir, f"{os.path.splitext(sample_pdfs[0])[0]}_translated.pdf")
            print(f"Found sample PDF: {sample_pdfs[0]}")
        else:
            print("No PDF files found in the samples directory.")
            return
    else:
        # Look for PDFs in the current directory
        sample_pdfs = [f for f in os.listdir(current_dir) if f.endswith('.pdf')]
        if not sample_pdfs:
            print("No PDF files found in the current directory or samples directory.")
            return
        input_path = os.path.join(current_dir, sample_pdfs[0])
        output_path = os.path.join(current_dir, f"{os.path.splitext(sample_pdfs[0])[0]}_translated.pdf")
    
    print(f"Input PDF: {input_path}")
    print(f"Output PDF: {output_path}")
    
    # Translate the PDF
    translate_pdf(input_path, output_path, batch_size=3)
    
    print(f"Translation completed. Output saved to {output_path}")

if __name__ == "__main__":
    main() 