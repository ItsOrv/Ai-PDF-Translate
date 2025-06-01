[English](README.md) / [فارسی](README_FA.md)


# Persian PDF Translator

A powerful tool that translates PDF documents from English to Persian while preserving the original layout. This project uses Google's Gemini API for high-quality translation and implements advanced techniques for handling right-to-left Persian text rendering.

## Key Features

- **Layout Preservation**: Maintains the original document structure, positioning, and styling
- **Image & Graphics Retention**: Preserves all images, charts, tables, and non-text elements
- **RTL Text Handling**: Properly renders right-to-left Persian text with correct alignment
- **Smart Text Wrapping**: Intelligently wraps Persian text to maintain readability
- **Adaptive Font Sizing**: Automatically adjusts font sizes to fit text within boundaries
- **Domain-Specific Translation**: Specialized translation modes for scientific, medical, technical, and legal content
- **Genetic Domain Support**: Specialized handling of genetics terminology and academic content
- **API Rate Management**: Smart handling of API limits with automatic retries and exponential backoff
- **Persian Font Integration**: Built-in support for popular Persian fonts (Vazirmatn, Sahel, Samim)
- **Error Recovery**: Ability to continue processing after encountering errors
- **Character-Level Accuracy**: Character-by-character processing for highest accuracy

## Installation

### Automatic Setup (Recommended)

Use our setup script which handles everything for you:

```bash
./setup.sh
```

### Manual Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/persian-pdf-translator.git
cd persian-pdf-translator
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

4. Download and set up Persian fonts:
```bash
python download_fonts.py
```

5. Configure your API key:
   - Copy `.env.example` to `.env`
   - Add your Gemini API key to the `.env` file
   - Get an API key from [Google AI Studio](https://aistudio.google.com/app/apikey)

## Usage Examples

### Basic Translation

Translate a PDF with default settings:

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

For large documents, you may need to adjust batch size to handle API limits:
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

- `general`: General purpose translation
- `scientific`: Scientific and academic content
- `genetic`: Genetics and genomics terminology
- `medical`: Medical and healthcare content
- `legal`: Legal and contractual documents
- `technical`: Engineering and technical content

## Technical Details

### How It Works

1. **Text Extraction**: The application extracts text elements and their precise positioning from the PDF
2. **Translation**: Text is sent to Google's Gemini API with specialized prompts based on the domain
3. **Layout Reconstruction**: Translated text is precisely positioned in the same layout as the original
4. **Font Handling**: Persian fonts are automatically selected and sized to match the original style
5. **RTL Rendering**: Text is properly rendered with right-to-left alignment and proper character shaping

### Smart Text Positioning

The application employs several techniques to ensure Persian text fits properly:

- **Dynamic Wrapping**: Intelligently wraps text at appropriate boundaries
- **Adaptive Sizing**: Reduces font size when necessary to fit longer translated text
- **Margin Protection**: Prevents text from extending beyond page boundaries
- **Character-Level Processing**: Handles Persian text at the character level for accurate wrapping

### API Optimization

- **Rate Limiting**: Respects Google Gemini API limits (15 requests per minute for free tier)
- **Exponential Backoff**: Smart retries with increasing delays between attempts
- **Batch Processing**: Processes text in batches to optimize API usage
- **Jitter**: Adds randomized delays to prevent synchronized retries

## Troubleshooting

### API Issues

- **Rate Limit Errors**: The application automatically handles rate limits, but you can reduce batch size further
- **API Key Problems**: Ensure your API key is correctly set in the `.env` file
- **Connectivity Issues**: Check your internet connection and firewall settings

### Translation Quality

- **Poor Translation**: Try a different domain specialization (--domain option)
- **Terminology Issues**: For scientific/technical documents, use the appropriate domain
- **Context Problems**: For large documents with cross-references, process in smaller chunks

### PDF Rendering

- **Text Overflow**: The application handles this automatically, but complex layouts may need manual adjustment
- **Missing Fonts**: Run `python download_fonts.py` to ensure all Persian fonts are installed
- **Image Quality**: Images are preserved at their original quality

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 
