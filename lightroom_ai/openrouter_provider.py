"""
OpenRouter API implementation for AI image analysis.
"""

import json
import requests
from typing import Dict, Any, Optional

from .config import AppConfig
from .ai_providers import AiProvider
from .logging_setup import get_logger

logger = get_logger(__name__)

class OpenRouterProvider(AiProvider):
    """OpenRouter API implementation of AI provider."""
    
    def __init__(self, config: AppConfig):
        """
        Initialize the OpenRouter provider.
        
        Args:
            config: Application configuration
        """
        super().__init__(config)
        
        self.provider_config = config.provider
        
        self.api_key = self.provider_config.api_key
        self.api_url = self.provider_config.api_url
        self.model = self.provider_config.model
        self.site_url = self.provider_config.site_url
        self.title = self.provider_config.title
        
        logger.info(f"Initialized OpenRouter provider with model: {self.model}")
    
    def analyze_image(self, image_b64: str, user_prompt: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Analyze an image using OpenRouter API and extract metadata.
        
        Args:
            image_b64: Base64-encoded image string
            user_prompt: Optional custom user prompt
            
        Returns:
            Dictionary with analysis results if successful, None otherwise
        """
        def make_request() -> Optional[Dict[str, Any]]:
            return self._call_openrouter_api(image_b64, user_prompt)
            
        return self.call_with_retries(make_request)
    
    def _call_openrouter_api(self, img_b64: str, user_prompt: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Call the OpenRouter API with the image.
        
        Args:
            img_b64: Base64-encoded image string
            user_prompt: Optional custom user prompt
            
        Returns:
            Dictionary with API response if successful, None otherwise
        """
        if not self.api_key:
            logger.error("OpenRouter API key not provided")
            return None
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": self.site_url,
            "X-Title": self.title
        }
        
        # Get the analysis prompt (either custom or default)
        prompt = user_prompt if user_prompt else self.get_analysis_prompt()
        
        # Prepare the messages
        messages = [
            {
                "role": "system",
                "content": "You are a photography assistant specializing in image analysis. Analyze images carefully and provide detailed, accurate categorization according to the specified categories."
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}
                ]
            }
        ]
        
        # Prepare the request payload
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": 4000,
            "temperature": 0.0
        }
        
        try:
            logger.debug(f"Calling OpenRouter API with model: {self.model}")
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=60
            )
            
            if response.status_code != 200:
                logger.error(f"OpenRouter API error: {response.status_code} - {response.text}")
                return None
            
            response_data = response.json()
            
            if self.config.debug_mode:
                logger.debug(f"OpenRouter API response: {json.dumps(response_data, indent=2)}")
            
            # Extract the response content
            if 'choices' in response_data and len(response_data['choices']) > 0:
                message = response_data['choices'][0].get('message', {})
                content = message.get('content', '')
                
                # Parse the response
                ai_result = self.parse_response(content)
                if not ai_result:
                    return None
                    
                # Format the result
                formatted_result = self.format_result(ai_result)
                return formatted_result
            
            logger.error("Invalid response format from OpenRouter API")
            return None
            
        except Exception as e:
            logger.error(f"Error calling OpenRouter API: {str(e)}")
            if self.config.debug_mode:
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
            return None
