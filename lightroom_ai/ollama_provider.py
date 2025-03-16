"""
Ollama-specific implementation of AI provider.
"""

import json
import re
import logging
import requests
from typing import Dict, Any, Optional, List, Callable

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
        
    def analyze_image(self, image_b64: str) -> Optional[Dict[str, Any]]:
        """
        Analyze an image using Ollama API and extract metadata.
        
        Args:
            image_b64: Base64-encoded image string
            
        Returns:
            Dictionary with analysis results if successful, None otherwise
        """
        def make_request() -> Optional[Dict[str, Any]]:
            return self._call_ollama_api(image_b64)
            
        return self.call_with_retries(make_request)
        
    def _call_ollama_api(self, img_b64: str) -> Optional[Dict[str, Any]]:
        """
        Call the Ollama API with an image to get metadata.
        
        Args:
            img_b64: Base64-encoded image string
            
        Returns:
            Dictionary with analysis results if successful, None otherwise
        """
        # Prompt for image analysis
        prompt = """
        You are a photography assistant specializing in image analysis.
        Please analyze this base64-encoded image and provide:
        1. Five keywords that best describe the content (objects, scenes, concepts).
        2. Five tags that would be useful for categorizing this photo (style, genre, mood).
        3. An aesthetic score from 0 to 10, where 10 represents exceptional artistic quality.
        
        Return ONLY a JSON object with this structure:
        {
            "keywords": [...],
            "tags": [...],
            "aesthetic_score": ...
        }
        """
        
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
            
            # Use the shared extraction utility from utils.py
from lightroom_ai.utils import extract_json

ai_result = extract_json(response_text, logger, self.config.debug_mode)
if not ai_result:
    return None
return ai_result

                
                return json.loads(json_str)
            else:
                logger.error("Failed to extract JSON from Ollama response")
                if self.config.debug_mode:
                    logger.debug(f"Ollama response: {response_text}")
                return None
                
        except requests.RequestException as e:
            logger.error(f"Ollama API network error: {str(e)}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Ollama API JSON parsing error: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error calling Ollama API: {str(e)}")
            return None
