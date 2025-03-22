"""
AI provider interface and factory.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Type, List, Callable
import time

from .config import AppConfig
from .logging_setup import get_logger
from .prompt_templates import get_image_analysis_prompt, format_analysis_result
from .utils import extract_json

logger = get_logger(__name__)

class AiProvider(ABC):
    """Abstract base class for AI providers."""
    
    @staticmethod
    def get_provider(config: AppConfig) -> 'AiProvider':
        """
        Factory method to get the appropriate AI provider based on configuration.
        
        Args:
            config: Application configuration
            
        Returns:
            An instance of the appropriate AiProvider subclass
        """
        provider_type = config.provider.provider_type.lower()
        
        if provider_type == 'claude':
            from .claude_provider import ClaudeProvider
            return ClaudeProvider(config)
        elif provider_type == 'ollama':
            from .ollama_provider import OllamaProvider
            return OllamaProvider(config)
        elif provider_type == 'openrouter':
            from .openrouter_provider import OpenRouterProvider
            return OpenRouterProvider(config)
        else:
            logger.warning(f"Unknown provider type: {provider_type}, using Claude")
            from .claude_provider import ClaudeProvider
            return ClaudeProvider(config)
    
    def __init__(self, config: AppConfig):
        """
        Initialize the AI provider.
        
        Args:
            config: Application configuration
        """
        self.config = config
        self.max_retries = config.max_retries
        
        # Whether to include film analysis in prompts
        self.include_film_analysis = getattr(config, 'include_film_analysis', True)
    
    def call_with_retries(self, request_func: Callable[[], Optional[Dict[str, Any]]]) -> Optional[Dict[str, Any]]:
        """
        Call an API function with retries.
        
        Args:
            request_func: Function to call that returns a response or None
            
        Returns:
            API response if successful, None otherwise
        """
        for attempt in range(self.max_retries):
            try:
                result = request_func()
                if result:
                    return result
                
                if attempt < self.max_retries - 1:
                    logger.info(f"Retrying API call in {2 ** attempt} seconds (attempt {attempt + 1}/{self.max_retries})")
                    time.sleep(2 ** attempt)  # Exponential backoff
            except Exception as e:
                logger.error(f"Error in API call (attempt {attempt + 1}): {str(e)}")
                if attempt < self.max_retries - 1:
                    logger.info(f"Retrying in {2 ** attempt} seconds")
                    time.sleep(2 ** attempt)
        
        logger.error(f"Failed to get valid response after {self.max_retries} attempts")
        return None
    
    def get_analysis_prompt(self) -> str:
        """
        Get the prompt for image analysis.
        
        Returns:
            Formatted prompt string
        """
        return get_image_analysis_prompt(self.include_film_analysis)
    
    def format_result(self, raw_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format the AI result into a standardized structure.
        
        Args:
            raw_result: Raw AI result
            
        Returns:
            Formatted result dictionary
        """
        return format_analysis_result(raw_result)
    
    def parse_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """
        Parse the text response from the AI into a structured format.
        
        Args:
            response_text: Text response from the AI
            
        Returns:
            Parsed JSON data or None if parsing fails
        """
        # Use the shared extraction utility
        return extract_json(response_text, logger, self.config.debug_mode)
    
    @abstractmethod
    def analyze_image(self, image_b64: str, user_prompt: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Analyze an image and extract metadata.
        
        Args:
            image_b64: Base64-encoded image string
            user_prompt: Optional custom user prompt
            
        Returns:
            Dictionary with analysis results if successful, None otherwise
        """
        pass
