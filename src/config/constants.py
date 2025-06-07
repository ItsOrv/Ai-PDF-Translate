"""
Application constants and default values.
"""


class Constants:
    """
    Application-wide constants and default values.
    """
    
    # File extensions
    PDF_EXTENSION = ".pdf"
    
    # Directory names
    SAMPLES_DIR = "samples"
    OUTPUT_DIR = "output"
    TEMP_DIR = "temp"
    
    # API settings
    DEFAULT_MODEL = "gemini-1.5-pro"
    FALLBACK_MODEL = "gemini-1.5-flash"
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_REQUESTS_PER_MINUTE = 20
    DEFAULT_BASE_DELAY = 1.0
    
    # Translation domains
    TRANSLATION_DOMAINS = [
        "general",
        "scientific",
        "medical",
        "legal",
        "technical",
        "genetic"
    ]
    
    # Font settings
    DEFAULT_FONT = "Vazirmatn"
    
    # Text processing
    MIN_FONT_SIZE = 6
    MAX_FONT_SIZE = 72
    DEFAULT_FONT_SIZE = 12
    LINE_HEIGHT_RATIO = 1.2  # Line height as a ratio of font size
    
    # Error messages
    ERROR_NO_API_KEY = "No API key provided. Please set the GEMINI_API_KEY environment variable."
    ERROR_FILE_NOT_FOUND = "File not found: {}"
    ERROR_INVALID_DOMAIN = "Invalid domain: {}. Valid domains are: {}"
    
    # Success messages
    SUCCESS_TRANSLATION = "Translation completed successfully: {}"
    
    # Regular expressions
    RETRY_DELAY_PATTERN = r"retry_after(?:=|\s+)(\d+)"
    PERSIAN_TEXT_PATTERN = r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]+"
    
    # Translation domains
    DOMAIN_GENERAL = "general"
    DOMAIN_SCIENTIFIC = "scientific"
    DOMAIN_GENETIC = "genetic"
    DOMAIN_MEDICAL = "medical"
    DOMAIN_LEGAL = "legal"
    DOMAIN_TECHNICAL = "technical"
    
    # Valid translation domains
    VALID_DOMAINS = [
        DOMAIN_GENERAL,
        DOMAIN_SCIENTIFIC,
        DOMAIN_GENETIC,
        DOMAIN_MEDICAL,
        DOMAIN_LEGAL,
        DOMAIN_TECHNICAL
    ]
    
    # Font-related constants
    DEFAULT_PERSIAN_FONTS = [
        'Vazirmatn',
        'Vazirmatn-Bold',
        'Vazirmatn-Light',
        'Sahel',
        'Samim'
    ]
    
    # Processing defaults
    DEFAULT_BATCH_SIZE = 3
    
    # Default directories
    FONTS_DIR = "fonts"
    
    # Persian language detection
    PERSIAN_UNICODE_RANGE_START = 0x0600
    PERSIAN_UNICODE_RANGE_END = 0x06FF
    PERSIAN_CHAR_THRESHOLD = 0.3  # Minimum ratio of Persian chars to consider text Persian 