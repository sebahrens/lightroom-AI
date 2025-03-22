"""
Ollama-specific implementation of AI provider.
"""

import json
import requests
from typing import Dict, Any, Optional

from .config import AppConfig, OllamaConfig
from .ai_providers import AiProvider
from .logging_setup import get_logger

logger = get_logger(__name__)

class OllamaProvider(AiProvider):
    """Ollama API implementation of AI provider."""
    
    def __init__(self, config: AppConfig):
        """
        Initialize the Ollama provider.
        
        Args:
            config: Application configuration
            
        Raises:
            ValueError: If config.provider is not an OllamaConfig object
        """
        super().__init__(config)
        
        if not hasattr(config.provider, 'provider_type') or config.provider.provider_type != 'ollama':
            raise ValueError("Invalid provider configuration for Ollama")
            
        self.ollama_config = config.provider
        
        if not isinstance(self.ollama_config, OllamaConfig):
            raise ValueError("Provider must be an OllamaConfig instance")
            
        self.api_url = self.ollama_config.api_url
        self.model = self.ollama_config.model
        
    def analyze_image(self, image_b64: str, user_prompt: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Analyze an image using Ollama API and extract metadata.
        
        Args:
            image_b64: Base64-encoded image string
            user_prompt: Optional custom user prompt
            
        Returns:
            Dictionary with analysis results if successful, None otherwise
        """
        def make_request() -> Optional[Dict[str, Any]]:
            return self._call_ollama_api(image_b64, user_prompt)
            
        return self.call_with_retries(make_request)
        
    def _call_ollama_api(self, img_b64: str, user_prompt: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Call the Ollama API with an image to get metadata.
        
        Args:
            img_b64: Base64-encoded image string
            user_prompt: Optional custom user prompt
            
        Returns:
            Dictionary with analysis results if successful, None otherwise
        """
        # Get the analysis prompt (either custom or default)
        prompt = user_prompt if user_prompt else self.get_analysis_prompt()
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "images": [img_b64],
            "stream": False
        }
        
        try:
            response = requests.post(self.api_url, json=payload, timeout=30)
            response.raise_for_status()
            result = response.json()
            response_text = result.get("response", "")
            
            # Parse the response
            ai_result = self.parse_response(response_text)
            if not ai_result:
                return None
                
            # Format the result
            formatted_result = self.format_result(ai_result)
            return formatted_result
                
        except requests.RequestException as e:
            logger.error(f"Ollama API network error: {str(e)}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Ollama API JSON parsing error: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error calling Ollama API: {str(e)}")
            return None
