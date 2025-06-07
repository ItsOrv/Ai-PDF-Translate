"""
Module for translating text using the Gemini API.
"""
import os
import logging
import time
import re
import random
from typing import List, Dict, Any, Optional
import google.generativeai as genai
from dotenv import load_dotenv

from src.utils.text_utils import clean_text_for_translation

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GeminiTranslator:
    """Class for translating text using the Google Gemini API."""
    
    def __init__(self, domain: str = "general"):
        """
        Initialize the translator with API key from environment.
        
        Args:
            domain: Domain for translation (general, scientific, genetic, medical, legal, technical)
        """
        # Load environment variables
        load_dotenv()
        
        # Get API key from environment variables
        api_key = os.getenv("GEMINI_API_KEY")
        
        if not api_key:
            logger.error("No API key found. Please set GEMINI_API_KEY in .env file")
            raise ValueError("Missing API key")
        
        # Log key info for debugging (safely)
        logger.info(f"API Key found. Length: {len(api_key)}, First 4 chars: {api_key[:4]}...")
        
        # Configure the Gemini API
        genai.configure(api_key=api_key)
        
        # Rate limiting configuration
        self.requests_per_minute = 15  # Gemini API free tier limit
        self.request_timestamps = []  # Keep track of recent request timestamps
        self.max_retries = 5  # Maximum number of retries
        self.base_delay = 1  # Base delay for exponential backoff in seconds
        
        # Set the translation domain
        self.domain = domain
        logger.info(f"Using {domain} domain for translations")
        
        # Translation prompt templates for different domains
        self.prompt_templates = {
            "general": """Translate the following English text to Persian (Farsi). Only provide the translation, no explanations or additional text, just translate the text directly:

{text}""",
            
            "scientific": """متن زیر را از زبان انگلیسی به زبان فارسی به صورت حرفه‌ای و دقیق ترجمه کن. در ترجمه به موارد زیر توجه کن:

1. استفاده از اصطلاحات و واژگان تخصصی دقیق در حوزه علمی مربوطه و رعایت استانداردهای علمی پذیرفته‌شده.
2. حفظ سبک علمی، دانشگاهی و تخصصی متن اصلی بدون تغییر معنا یا ابهام در مفاهیم.
3. اطمینان از صحت ساختار جملات به گونه‌ای که هم از نظر دستوری و هم از نظر مفهومی به بهترین نحو به زبان فارسی منتقل شود.
4. در صورت وجود اصطلاح یا مفهوم دشوار، در صورت امکان ارائه معادل تخصصی مربوطه.
5. رعایت تناسب و انسجام متن به گونه‌ای که همخوانی مفهومی و ساختاری حفظ شود.

فقط متن ترجمه شده را بازگردان، بدون هیچ توضیح اضافی:

{text}""",
            
            "genetic": """متن زیر را از زبان انگلیسی به زبان فارسی به صورت حرفه‌ای و دقیق ترجمه کن. در ترجمه به موارد زیر توجه کن:

1. استفاده از اصطلاحات و واژگان تخصصی دقیق در حوزه ژنتیک (مانند DNA، RNA، ژن، اپی‌ژنتیک، موتاسیون و سایر مفاهیم مرتبط) و رعایت استانداردهای علمی پذیرفته‌شده.
2. حفظ سبک علمی، دانشگاهی و تخصصی متن اصلی بدون تغییر معنا یا ابهام در مفاهیم.
3. اطمینان از صحت ساختار جملات به گونه‌ای که هم از نظر دستوری و هم از نظر مفهومی به بهترین نحو به زبان فارسی منتقل شود.
4. در صورت وجود اصطلاح یا مفهوم دشوار، در صورت امکان ارائه معادل تخصصی مربوطه.
5. رعایت تناسب و انسجام متن به گونه‌ای که همخوانی مفهومی و ساختاری حفظ شود.

فقط متن ترجمه شده را بازگردان، بدون هیچ توضیح اضافی:

{text}""",
            
            "medical": """متن زیر را از زبان انگلیسی به زبان فارسی به صورت حرفه‌ای و دقیق ترجمه کن. در ترجمه به موارد زیر توجه کن:

1. استفاده از اصطلاحات و واژگان تخصصی دقیق در حوزه پزشکی و علوم زیستی و رعایت استانداردهای علمی پزشکی پذیرفته‌شده.
2. حفظ سبک علمی، دانشگاهی و تخصصی پزشکی متن اصلی بدون تغییر معنا یا ابهام در مفاهیم.
3. اطمینان از صحت ساختار جملات به گونه‌ای که هم از نظر دستوری و هم از نظر مفهومی به بهترین نحو به زبان فارسی منتقل شود.
4. در صورت وجود اصطلاح یا مفهوم دشوار پزشکی، در صورت امکان ارائه معادل تخصصی مربوطه.
5. رعایت تناسب و انسجام متن به گونه‌ای که همخوانی مفهومی و ساختاری حفظ شود.

فقط متن ترجمه شده را بازگردان، بدون هیچ توضیح اضافی:

{text}""",
            
            "legal": """متن زیر را از زبان انگلیسی به زبان فارسی به صورت حرفه‌ای و دقیق ترجمه کن. در ترجمه به موارد زیر توجه کن:

1. استفاده از اصطلاحات و واژگان تخصصی دقیق در حوزه حقوقی و قانونی و رعایت استانداردهای حقوقی پذیرفته‌شده.
2. حفظ سبک رسمی، حقوقی و تخصصی متن اصلی بدون تغییر معنا یا ابهام در مفاهیم قانونی.
3. اطمینان از صحت ساختار جملات به گونه‌ای که هم از نظر دستوری و هم از نظر مفهومی به بهترین نحو به زبان فارسی منتقل شود.
4. در صورت وجود اصطلاح یا مفهوم دشوار حقوقی، در صورت امکان ارائه معادل تخصصی مربوطه.
5. رعایت تناسب و انسجام متن به گونه‌ای که همخوانی مفهومی و ساختاری حفظ شود.

فقط متن ترجمه شده را بازگردان، بدون هیچ توضیح اضافی:

{text}""",
            
            "technical": """متن زیر را از زبان انگلیسی به زبان فارسی به صورت حرفه‌ای و دقیق ترجمه کن. در ترجمه به موارد زیر توجه کن:

1. استفاده از اصطلاحات و واژگان تخصصی دقیق در حوزه فنی و مهندسی و رعایت استانداردهای فنی پذیرفته‌شده.
2. حفظ سبک فنی و تخصصی متن اصلی بدون تغییر معنا یا ابهام در مفاهیم مهندسی.
3. اطمینان از صحت ساختار جملات به گونه‌ای که هم از نظر دستوری و هم از نظر مفهومی به بهترین نحو به زبان فارسی منتقل شود.
4. در صورت وجود اصطلاح یا مفهوم دشوار فنی، در صورت امکان ارائه معادل تخصصی مربوطه.
5. رعایت تناسب و انسجام متن به گونه‌ای که همخوانی مفهومی و ساختاری حفظ شود.

فقط متن ترجمه شده را بازگردان، بدون هیچ توضیح اضافی:

{text}"""
        }
        
        # Get the Gemini model - using the correct model
        try:
            self.model = genai.GenerativeModel('gemini-2.0-flash')
            logger.info("Using gemini-2.0-flash model")
        except Exception as e:
            logger.warning(f"Could not load gemini-2.0-flash model: {str(e)}")
            logger.info("Trying gemini-1.5-flash model")
            try:
                self.model = genai.GenerativeModel('gemini-1.5-flash')
                logger.info("Using gemini-1.5-flash model")
            except Exception as e:
                logger.warning(f"Could not load gemini-1.5-flash model: {str(e)}")
                logger.info("Falling back to gemini-pro model")
                self.model = genai.GenerativeModel('gemini-pro')
    
    def _extract_retry_delay(self, error_message: str) -> int:
        """
        Extract retry delay from error message.
        
        Args:
            error_message: Error message from Gemini API
            
        Returns:
            Retry delay in seconds, default 60 if not found
        """
        # Try to find retry_delay in the error message
        match = re.search(r'retry_delay\s*{\s*seconds:\s*(\d+)\s*}', error_message)
        if match:
            return int(match.group(1))
        return 60  # Default delay if not found
        
    def _wait_for_rate_limit(self):
        """
        Wait if we're approaching the rate limit.
        Implements a sliding window approach to track requests in the last minute.
        """
        # Remove timestamps older than 1 minute
        current_time = time.time()
        self.request_timestamps = [ts for ts in self.request_timestamps if current_time - ts < 60]
        
        # If we're at or near the rate limit, wait until we have capacity
        if len(self.request_timestamps) >= self.requests_per_minute - 1:
            # Calculate how long to wait
            oldest_timestamp = self.request_timestamps[0]
            wait_time = 60 - (current_time - oldest_timestamp) + 1  # Add 1 second buffer
            
            # Ensure wait time is reasonable
            wait_time = max(0, min(wait_time, 60))
            
            if wait_time > 0:
                logger.info(f"Rate limit approaching, waiting {wait_time:.2f} seconds")
                time.sleep(wait_time)
    
    def _get_prompt_template(self, text: str) -> str:
        """
        Get the appropriate prompt template based on the domain.
        
        Args:
            text: The text to translate (used for auto-detection in the future)
            
        Returns:
            Prompt template string
        """
        # Use the template for the specified domain, or fall back to general
        return self.prompt_templates.get(self.domain, self.prompt_templates["general"])
    
    def translate_text(self, text: str) -> str:
        """
        Translate text from English to Persian using Gemini API.
        
        Args:
            text: The text to translate
            
        Returns:
            Translated text in Persian
        """
        if not text or text.isspace():
            return ""
            
        # Clean text before translation
        cleaned_text = clean_text_for_translation(text)
        
        # Initialize variables for retry logic
        retries = 0
        max_retries = self.max_retries
        base_delay = self.base_delay
        
        while retries <= max_retries:
            try:
                # Wait if we're approaching rate limit
                self._wait_for_rate_limit()
                
                # Get the appropriate prompt template and format it with the text
                prompt_template = self._get_prompt_template(cleaned_text)
                prompt = prompt_template.format(text=cleaned_text)
                
                # Record the request timestamp
                self.request_timestamps.append(time.time())
                
                # Generate the translation
                response = self.model.generate_content(prompt)
                
                # Extract the translation from the response
                translated_text = response.text.strip()
                
                # If translation failed, log a warning and return the original text
                if not translated_text:
                    logger.warning(f"Translation returned empty result for: {text[:50]}...")
                    return text
                    
                return translated_text
                
            except Exception as e:
                error_message = str(e)
                logger.error(f"Translation error: {error_message}")
                
                # Check if this is a rate limit error (429)
                if "429" in error_message:
                    retries += 1
                    
                    # Extract retry delay from error message if available
                    retry_delay = self._extract_retry_delay(error_message)
                    
                    # Add some jitter to avoid all clients retrying at the same time
                    jitter = random.uniform(0.1, 0.3)
                    delay = retry_delay + jitter
                    
                    if retries <= max_retries:
                        logger.info(f"Rate limit hit. Retrying in {delay:.2f} seconds (attempt {retries}/{max_retries})")
                        time.sleep(delay)
                    else:
                        logger.warning(f"Maximum retries reached. Returning original text.")
                        return text
                else:
                    # For other errors, use exponential backoff
                    if retries < max_retries:
                        retries += 1
                        delay = base_delay * (2 ** (retries - 1)) + random.uniform(0, 1)
                        logger.info(f"Error occurred. Retrying in {delay:.2f} seconds (attempt {retries}/{max_retries})")
                        time.sleep(delay)
                    else:
                        logger.warning(f"Maximum retries reached. Returning original text.")
                        return text
        
        # If we've exhausted retries
        return text
            
    def batch_translate(self, texts: List[str], batch_size: int = 5) -> List[str]:
        """
        Translate a list of texts in batches to avoid API limits.
        
        Args:
            texts: List of texts to translate
            batch_size: Number of texts to translate in one batch
            
        Returns:
            List of translated texts
        """
        results = []
        
        # Process in batches
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            
            # Translate each text in the batch
            batch_results = []
            for text in batch:
                # Add a small delay between requests in the same batch
                if batch_results:  # Skip delay for the first request in batch
                    time.sleep(random.uniform(0.5, 1.5))  # Random delay between 0.5 and 1.5 seconds
                
                translated = self.translate_text(text)
                batch_results.append(translated)
            
            results.extend(batch_results)
            
            logger.info(f"Translated batch {i//batch_size + 1}/{(len(texts)-1)//batch_size + 1}")
            
            # Add a delay between batches to help with rate limiting
            if i + batch_size < len(texts):
                time.sleep(random.uniform(1, 3))  # Random delay between 1 and 3 seconds
            
        return results 