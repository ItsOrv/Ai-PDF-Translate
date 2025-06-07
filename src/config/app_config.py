"""
Application configuration management.
"""

import os
import logging
from typing import Dict, Any, Optional

from src.config.constants import Constants

logger = logging.getLogger(__name__)


class AppConfig:
    """
    Manages application configuration and settings.
    """
    
    def __init__(self):
        """
        Initialize the application configuration.
        Loads settings from environment variables.
        """
        self.config = {}
        self._load_from_env()
    
    def _load_from_env(self) -> None:
        """
        Load configuration from environment variables.
        """
        # API keys
        self.config['api_key'] = os.environ.get('GEMINI_API_KEY', '')
        
        # Translation settings
        self.config['model_name'] = os.environ.get('MODEL_NAME', Constants.DEFAULT_MODEL)
        self.config['fallback_model'] = os.environ.get('FALLBACK_MODEL', Constants.FALLBACK_MODEL)
        self.config['max_retries'] = int(os.environ.get('MAX_RETRIES', Constants.DEFAULT_MAX_RETRIES))
        self.config['requests_per_minute'] = int(os.environ.get('REQUESTS_PER_MINUTE', Constants.DEFAULT_REQUESTS_PER_MINUTE))
        self.config['base_delay'] = float(os.environ.get('BASE_DELAY', Constants.DEFAULT_BASE_DELAY))
        
        # Logging settings
        log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
        self.config['log_level'] = getattr(logging, log_level, logging.INFO)
        
        # Font settings
        self.config['default_font'] = os.environ.get('DEFAULT_FONT', Constants.DEFAULT_FONT)
        
        # Validate API key
        if not self.config['api_key']:
            logger.warning("No Gemini API key found in environment variables. Translation will not work.")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key is not found
            
        Returns:
            Configuration value or default
        """
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value.
        
        Args:
            key: Configuration key
            value: Configuration value
        """
        self.config[key] = value
        logger.debug(f"Set config {key} = {value}")
    
    def get_api_key(self) -> str:
        """
        Get the API key for Gemini.
        
        Returns:
            API key string
        """
        return self.get('api_key', '')
    
    def get_model_name(self) -> str:
        """
        Get the model name to use for translation.
        
        Returns:
            Model name string
        """
        return self.get('model_name', Constants.DEFAULT_MODEL)
    
    def get_fallback_model(self) -> str:
        """
        Get the fallback model name to use if the primary model fails.
        
        Returns:
            Fallback model name string
        """
        return self.get('fallback_model', Constants.FALLBACK_MODEL)
    
    def get_max_retries(self) -> int:
        """
        Get the maximum number of retries for API calls.
        
        Returns:
            Maximum number of retries
        """
        return self.get('max_retries', Constants.DEFAULT_MAX_RETRIES)
    
    def get_requests_per_minute(self) -> int:
        """
        Get the maximum number of requests allowed per minute.
        
        Returns:
            Requests per minute limit
        """
        return self.get('requests_per_minute', Constants.DEFAULT_REQUESTS_PER_MINUTE)
    
    def get_base_delay(self) -> float:
        """
        Get the base delay for retry backoff.
        
        Returns:
            Base delay in seconds
        """
        return self.get('base_delay', Constants.DEFAULT_BASE_DELAY)
    
    def get_log_level(self) -> int:
        """
        Get the logging level.
        
        Returns:
            Logging level
        """
        return self.get('log_level', logging.INFO)
    
    def get_default_font(self) -> str:
        """
        Get the default font for text rendering.
        
        Returns:
            Default font name
        """
        return self.get('default_font', Constants.DEFAULT_FONT)
    
    def as_dict(self) -> Dict[str, Any]:
        """
        Get the entire configuration as a dictionary.
        
        Returns:
            Dictionary of configuration values
        """
        # Create a copy to avoid modifying the original
        config_copy = dict(self.config)
        
        # Mask sensitive values
        if 'api_key' in config_copy and config_copy['api_key']:
            config_copy['api_key'] = f"{config_copy['api_key'][:4]}...{config_copy['api_key'][-4:]}"
            
        return config_copy 