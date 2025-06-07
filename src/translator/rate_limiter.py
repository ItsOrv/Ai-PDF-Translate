"""
Rate limiter for API requests to prevent exceeding rate limits.
"""

import time
import random
import logging
import re
from typing import List, Optional

from src.config.app_config import AppConfig

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Rate limiter for API requests.
    Implements sliding window approach to track requests.
    """
    
    def __init__(self, requests_per_minute: Optional[int] = None,
                 max_retries: Optional[int] = None,
                 base_delay: Optional[int] = None):
        """
        Initialize the rate limiter.
        
        Args:
            requests_per_minute: Maximum number of requests per minute
            max_retries: Maximum number of retry attempts
            base_delay: Base delay in seconds for exponential backoff
        """
        config = AppConfig()
        self.requests_per_minute = requests_per_minute or config.get('requests_per_minute')
        self.max_retries = max_retries or config.get('max_retries')
        self.base_delay = base_delay or config.get('base_delay')
        self.request_timestamps: List[float] = []
        
        logger.debug(f"Rate limiter initialized with {self.requests_per_minute} requests per minute")
    
    def wait_if_needed(self) -> None:
        """
        Wait if necessary to respect rate limits.
        Removes timestamps older than 1 minute and waits if approaching rate limit.
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
                
    def record_request(self) -> None:
        """Record that a request was made."""
        self.request_timestamps.append(time.time())
        
    def extract_retry_delay(self, error_message: str) -> int:
        """
        Extract retry delay from error message.
        
        Args:
            error_message: Error message from API
            
        Returns:
            Retry delay in seconds, default 60 if not found
        """
        # Try to find retry_delay in the error message
        match = re.search(r'retry_delay\s*{\s*seconds:\s*(\d+)\s*}', error_message)
        if match:
            return int(match.group(1))
        return 60  # Default delay if not found
        
    def get_retry_delay(self, attempt: int) -> float:
        """
        Calculate delay for retry with exponential backoff and jitter.
        
        Args:
            attempt: Current retry attempt number (1-based)
            
        Returns:
            Delay in seconds
        """
        # Exponential backoff with base delay
        delay = self.base_delay * (2 ** (attempt - 1))
        
        # Add random jitter (0-30% of delay)
        jitter = delay * random.uniform(0, 0.3)
        
        # Apply jitter and limit to reasonable max
        final_delay = min(delay + jitter, 60)
        
        return final_delay 