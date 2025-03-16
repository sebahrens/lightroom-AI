"""
AI provider interface and factory.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Type

from .config import AppConfig
from .logging_setup import get_logger

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
    
    @abstractmethod
    def analyze_image(self, image_b64: str) -> Optional[Dict[str, Any]]:
        """
        Analyze an image and extract metadata.
        
        Args:
            image_b64: Base64-encoded image string
            
        Returns:
            Dictionary with analysis results if successful, None otherwise
        """
        pass
