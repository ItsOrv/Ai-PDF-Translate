# Ai-PDF-Translate

[English](README.md) / [فارسی](README_FA.md)

A powerful tool that translates PDF documents from English to Persian while preserving the original layout. Built using Google's Gemini API to deliver high-quality translations, with special attention to the challenges of right-to-left Persian text rendering.

## Key Features

- **Layout Preservation** - Maintains the original document structure, including positioning and styling
- **Image Retention** - Keeps all images, charts, tables and graphics untouched
- **RTL Text Handling** - Properly renders right-to-left Persian text with correct alignment
- **Smart Text Wrapping** - Wraps Persian text intelligently for optimal readability
- **Adaptive Font Sizing** - Automatically adjusts text size to fit within original boundaries
- **Domain-Specific Translation** - Specialized modes for scientific, medical, technical, and legal documents
- **Genetics Support** - Special handling of genetic terminology for research papers
- **API Management** - Handles rate limits with intelligent retries and backoff strategies
- **Persian Font Support** - Includes popular Persian fonts like Vazirmatn, Sahel, and Samim
- **Error Recovery** - Continues processing even after encountering certain errors
- **Character-Level Processing** - Handles text accurately at the character level

## Installation

### Automatic Setup (Recommended)

The setup script handles everything for you:

```bash
./setup.sh
```

### Manual Setup

If you prefer setting things up manually:

1. Clone the repo:
```bash
git clone https://github.com/ItsOrv/Ai-PDF-Translate.git
cd Ai-PDF-Translate
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Download the Persian fonts:
```bash
python tools/download_fonts.py
```

5. Configure your API key:
   - Copy `.env.example` to `.env`
   - Add your Gemini API key to the `.env` file
   - Get a key from [Google AI Studio](https://aistudio.google.com/app/apikey)

## Usage Examples

### Basic Translation

For a quick translation with default settings:

```bash
python main.py --input document.pdf --output translated.pdf
```

### Domain-Specific Translation

For scientific papers:
```bash
python main.py --input scientific_paper.pdf --output translated_paper.pdf --domain scientific
```

For genetics research papers:
```bash
python main.py --input genetics_research.pdf --output translated_genetics.pdf --domain genetic
```

For legal documents:
```bash
python main.py --input contract.pdf --output translated_contract.pdf --domain legal
```

### Processing Large Documents

When working with large documents, you might need to adjust the batch size:
```bash
python main.py --input large_document.pdf --output translated_large.pdf --batch-size 2 --continue-on-error
```

## Command Line Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--input` | `-i` | Path to input PDF file | (Required) |
| `--output` | `-o` | Path to output PDF file | input_translated.pdf |
| `--batch-size` | `-b` | Number of text elements per translation batch | 3 |
| `--continue-on-error` | `-c` | Continue with untranslated text if errors occur | False |
| `--domain` | `-d` | Translation domain specialization | general |
| `--verbose` | `-v` | Enable detailed logging | False |

### Available Translation Domains

- `general` - Everyday content and general purpose translation
- `scientific` - Academic papers and scientific content
- `genetic` - Genetics and genomics research
- `medical` - Healthcare and medical documents
- `legal` - Contracts and legal documents
- `technical` - Engineering and technical documentation

## Technical Details

### How It Works

1. **Text Extraction**: The program extracts text elements and their exact positions from the PDF
2. **Translation**: Text is sent to Google's Gemini API with specialized prompts based on domain
3. **Layout Reconstruction**: Translated text is placed exactly in the original layout
4. **Font Management**: Persian fonts are automatically selected and sized to match the original style
5. **RTL Rendering**: Text is properly rendered with right-to-left alignment and character shaping

### Smart Text Positioning

This program uses several techniques to ensure proper placement of Persian text:

- **Dynamic Line Breaking**: Intelligently breaks text at appropriate boundaries
- **Adaptive Size Adjustment**: Reduces font size when necessary to fit longer translated text
- **Margin Protection**: Prevents text from extending beyond page boundaries
- **Character-Level Processing**: Manages Persian text at the character level for precise line breaks

### API Optimization

- **Rate Limiting**: Respects Google Gemini API limits (15 requests per minute for free tier)
- **Exponential Backoff**: Smart retries with increasing delays between attempts
- **Batch Processing**: Processes text in batches to optimize API usage
- **Random Jitter**: Adds random delays to prevent synchronized retry attempts

## Troubleshooting

### API Issues

- **Rate Limit Errors**: The program automatically manages rate limits, but you can further reduce batch size
- **API Key Issues**: Ensure your API key is properly set in the `.env` file
- **Connection Problems**: Check your internet connection and firewall settings

### Translation Quality

- **Poor Translation**: Try a different domain specialization (--domain option)
- **Terminology Issues**: For scientific/technical documents, use the appropriate domain
- **Text Problems**: For large documents with cross-references, process in smaller chunks

### PDF Rendering

- **Text Overflow**: The program manages this automatically, but complex layouts might need manual adjustment
- **Missing Fonts**: Run `python tools/download_fonts.py` to ensure all Persian fonts are installed
- **Image Quality**: Images are preserved at their original quality

## Testing Your API Key

Check if your Gemini API key is working correctly:

```bash
python tools/test_api_key.py
```

## Quick Start

Want to see it in action? Try:

```bash
python example.py
```

This will find a PDF in your `samples` directory (or current directory) and translate it.

## Contributing

Contributions are welcome! Feel free to submit pull requests or open issues.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 
