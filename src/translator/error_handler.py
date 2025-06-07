"""
Error handler for translation processes.
"""

import logging
import time
from typing import Optional, Any, Dict, Callable, TypeVar

from src.translator.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)

# Define a generic type for function return
T = TypeVar('T')


class TranslationError(Exception):
    """Base exception for translation errors."""
    pass


class RateLimitError(TranslationError):
    """Exception raised when rate limit is hit."""
    pass


class AuthenticationError(TranslationError):
    """Exception raised for authentication issues."""
    pass


class ConnectionError(TranslationError):
    """Exception raised for network/connection issues."""
    pass


class ContentFilterError(TranslationError):
    """Exception raised when content is filtered by the API."""
    pass


class APIError(TranslationError):
    """Exception raised for generic API errors."""
    pass


class ErrorHandler:
    """
    Handles errors that occur during translation.
    """
    
    def __init__(self, rate_limiter: Optional[RateLimiter] = None):
        """
        Initialize the error handler.
        
        Args:
            rate_limiter: RateLimiter instance for handling rate limits
        """
        self.rate_limiter = rate_limiter or RateLimiter()
        
    def classify_error(self, error: Exception) -> Dict[str, Any]:
        """
        Classify the type of error and determine if it's retryable.
        
        Args:
            error: The exception that occurred
            
        Returns:
            Dictionary with error classification
        """
        error_str = str(error).lower()
        
        # Check for rate limit errors
        if "rate limit" in error_str or "quota" in error_str or "too many requests" in error_str:
            return {
                "type": "rate_limit",
                "retryable": True,
                "category": RateLimitError,
                "delay": self.rate_limiter.extract_retry_delay(error_str)
            }
            
        # Check for authentication errors
        elif "auth" in error_str or "key" in error_str or "permission" in error_str or "unauthorized" in error_str:
            return {
                "type": "authentication",
                "retryable": False,
                "category": AuthenticationError
            }
            
        # Check for connection errors
        elif "connection" in error_str or "timeout" in error_str or "network" in error_str:
            return {
                "type": "connection",
                "retryable": True,
                "category": ConnectionError,
                "delay": 5  # Short delay for connection issues
            }
            
        # Check for content filter errors
        elif "content" in error_str and ("filter" in error_str or "policy" in error_str or "block" in error_str):
            return {
                "type": "content_filter",
                "retryable": False,
                "category": ContentFilterError
            }
            
        # Generic API errors
        else:
            return {
                "type": "api_error",
                "retryable": True,  # Assume most errors can be retried
                "category": APIError,
                "delay": 2  # Short delay for generic errors
            }
    
    def handle_with_retry(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """
        Execute a function with retry logic for handling errors.
        
        Args:
            func: Function to execute
            *args: Arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function
            
        Returns:
            Result of the function
            
        Raises:
            TranslationError: If all retries fail or non-retryable error occurs
        """
        max_retries = self.rate_limiter.max_retries
        
        for attempt in range(1, max_retries + 2):  # +2 because first attempt is not a retry
            try:
                # Check rate limits before making the request
                self.rate_limiter.wait_if_needed()
                
                # Make the request
                result = func(*args, **kwargs)
                
                # Record the request
                self.rate_limiter.record_request()
                
                return result
                
            except Exception as e:
                # Record the error attempt
                self.rate_limiter.record_request()
                
                # Classify the error
                error_info = self.classify_error(e)
                
                # If this is the last attempt or error is not retryable, raise
                if attempt > max_retries or not error_info.get("retryable", False):
                    # Convert to appropriate exception type
                    error_category = error_info.get("category", TranslationError)
                    logger.error(f"Error during translation: {str(e)} (type: {error_info['type']})")
                    raise error_category(str(e))
                    
                # Get delay for this attempt
                delay = error_info.get("delay") or self.rate_limiter.get_retry_delay(attempt)
                
                # Log retry information
                logger.warning(f"Attempt {attempt}/{max_retries} failed: {str(e)}. "
                              f"Retrying in {delay:.1f} seconds...")
                
                # Wait before retrying
                time.sleep(delay) 