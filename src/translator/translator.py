"""
Module for translating text using the Gemini API.
"""

import logging
import re
from typing import List, Optional, Dict, Any
import google.generativeai as genai

from src.config.app_config import AppConfig
from src.config.constants import Constants
from src.translator.prompt_templates import PromptTemplates
from src.translator.rate_limiter import RateLimiter
from src.translator.error_handler import ErrorHandler, TranslationError
from src.utils.text_utils import clean_text_for_translation

# Configure logging
logger = logging.getLogger(__name__)


class GeminiTranslator:
    """
    Translates text from English to Persian using the Google Gemini API.
    """
    
    def __init__(self, domain: str = None):
        """
        Initialize the translator with API key from configuration.
        
        Args:
            domain: Domain for translation (general, scientific, genetic, etc.)
        """
        # Get configuration
        self.config = AppConfig()
        
        # Set domain
        self.domain = domain or self.config.get('default_domain', Constants.DOMAIN_GENERAL)
        if self.domain not in Constants.VALID_DOMAINS:
            logger.warning(f"Invalid domain: {self.domain}, using {Constants.DOMAIN_GENERAL}")
            self.domain = Constants.DOMAIN_GENERAL
            
        logger.info(f"Using {self.domain} domain for translations")
        
        # Create rate limiter
        self.rate_limiter = RateLimiter()
        
        # Create error handler
        self.error_handler = ErrorHandler(self.rate_limiter)
        
        # Initialize the API
        self._initialize_api()
        
    def _initialize_api(self) -> None:
        """Initialize the Google Generative AI API with available models."""
        # Get API key from configuration
        api_key = self.config.api_key
        
        if not api_key:
            logger.error("No API key found. Please set GEMINI_API_KEY in .env file")
            raise ValueError("Missing API key")
        
        # Log key info for debugging (safely)
        logger.info(f"API Key found. Length: {len(api_key)}, First 4 chars: {api_key[:4]}...")
        
        # Configure the Gemini API
        genai.configure(api_key=api_key)
        
        # Get model name from configuration
        model_name = self.config.model
        fallback_models = self.config.get('fallback_models', [])
        
        # Try to load the primary model
        try:
            self.model = genai.GenerativeModel(model_name)
            logger.info(f"Using {model_name} model")
        except Exception as e:
            logger.warning(f"Could not load {model_name} model: {str(e)}")
            
            # Try fallback models
            for fallback_model in fallback_models:
                try:
                    logger.info(f"Trying {fallback_model} model")
                    self.model = genai.GenerativeModel(fallback_model)
                    logger.info(f"Using {fallback_model} model")
                    break
                except Exception as e:
                    logger.warning(f"Could not load {fallback_model} model: {str(e)}")
            else:
                # If all models fail, raise exception
                logger.error("Could not load any model")
                raise ValueError("Could not load any model")
                
    def _get_prompt_template(self) -> str:
        """
        Get the appropriate prompt template based on the domain.
        
        Returns:
            Prompt template string
        """
        return PromptTemplates.get_template(self.domain)
        
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
            
        # Clean the text
        cleaned_text = clean_text_for_translation(text)
        if not cleaned_text:
            return ""
            
        # Get prompt template and format with text
        prompt = self._get_prompt_template().format(text=cleaned_text)
        
        # Define the translation function
        def perform_translation():
            response = self.model.generate_content(prompt)
            return response.text
            
        try:
            # Use error handler to manage retries and rate limits
            translated_text = self.error_handler.handle_with_retry(perform_translation)
            
            # Clean up the response
            cleaned_response = self._clean_response(translated_text)
            
            logger.debug(f"Translated: '{text[:30]}...' -> '{cleaned_response[:30]}...'")
            return cleaned_response
            
        except TranslationError as e:
            logger.error(f"Translation error: {str(e)}")
            return f"[Translation error: {str(e)}]"
    
    def _clean_response(self, response: str) -> str:
        """
        Clean the response from the API.
        
        Args:
            response: Response from the API
            
        Returns:
            Cleaned response
        """
        if not response:
            return ""
            
        # Remove any explanatory text that might have been added
        # First, try to extract just the Persian text
        persian_pattern = re.compile(r'[\u0600-\u06FF\s،؛؟]+')
        persian_matches = persian_pattern.findall(response)
        
        if persian_matches:
            # Join all Persian text segments
            return ' '.join(persian_matches).strip()
            
        # If no Persian text found, return the cleaned response
        return response.strip()
        
    def batch_translate(self, texts: List[str], batch_size: int = None) -> List[str]:
        """
        Translate multiple texts in batches.
        
        Args:
            texts: List of texts to translate
            batch_size: Number of texts per batch
            
        Returns:
            List of translated texts
        """
        if not texts:
            return []
            
        # Get batch size from config if not provided
        if batch_size is None:
            batch_size = self.config.get('batch_size', Constants.DEFAULT_BATCH_SIZE)
            
        logger.info(f"Translating {len(texts)} texts in batches of {batch_size}")
        
        results = []
        for i in range(0, len(texts), batch_size):
            # Get batch
            batch = texts[i:i+batch_size]
            
            # Translate each text in batch
            batch_results = []
            for text in batch:
                translated = self.translate_text(text)
                batch_results.append(translated)
                
            # Extend results
            results.extend(batch_results)
            
            # Log progress
            logger.info(f"Translated batch {i//batch_size + 1}/{(len(texts) + batch_size - 1)//batch_size}")
            
        return results
        
    def translate_elements(self, elements: List[Dict[str, Any]], 
                          batch_size: int = None,
                          continue_on_error: bool = False) -> List[Dict[str, Any]]:
        """
        Translate text elements and update with translations.
        
        Args:
            elements: List of text element dictionaries
            batch_size: Number of elements per batch
            continue_on_error: Whether to continue if errors occur
            
        Returns:
            List of updated text elements with translations
        """
        # Extract text from elements
        texts = [element.get('text', '') for element in elements]
        
        try:
            # Translate texts
            translated_texts = self.batch_translate(texts, batch_size)
            
            # Update elements with translations
            for element, translated_text in zip(elements, translated_texts):
                element['translated_text'] = translated_text
                element['original_text'] = element.get('text', '')
                element['is_translated'] = bool(translated_text and not translated_text.startswith('[Translation error:'))
                
        except Exception as e:
            logger.error(f"Error in batch translation: {str(e)}")
            
            if not continue_on_error:
                raise
                
            # If continuing on error, mark all untranslated elements
            for element in elements:
                if not element.get('translated_text'):
                    element['translated_text'] = f"[Translation error: {str(e)}]"
                    element['is_translated'] = False
                    
        return elements 