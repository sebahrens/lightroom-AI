"""
Claude-specific implementation of AI provider with film photography analysis.
"""

import json
import requests
from typing import Dict, Any, Optional

from .config import AppConfig, ClaudeConfig
from .ai_providers import AiProvider
from .logging_setup import get_logger

logger = get_logger(__name__)

class ClaudeProvider(AiProvider):
    """Claude API implementation of AI provider."""
    
    def __init__(self, config: AppConfig):
        """
        Initialize the Claude provider.
        
        Args:
            config: Application configuration
            
        Raises:
            ValueError: If config.provider is not a ClaudeConfig object
        """
        super().__init__(config)
        
        if not hasattr(config.provider, 'provider_type') or config.provider.provider_type != 'claude':
            raise ValueError("Invalid provider configuration for Claude")
            
        self.claude_config = config.provider
        
        if not isinstance(self.claude_config, ClaudeConfig):
            raise ValueError("Provider must be a ClaudeConfig instance")
            
        self.api_url = self.claude_config.api_url
        self.api_key = self.claude_config.api_key
        self.model = self.claude_config.model
        self.use_batch_api = self.claude_config.use_batch_api
        
    def analyze_image(self, image_b64: str, user_prompt: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Analyze an image using Claude API and extract metadata.
        
        Args:
            image_b64: Base64-encoded image string
            user_prompt: Optional custom user prompt
            
        Returns:
            Dictionary with analysis results if successful, None otherwise
        """
        def make_request() -> Optional[Dict[str, Any]]:
            return self._call_claude_api(image_b64, user_prompt)
            
        return self.call_with_retries(make_request)
        
    def _call_claude_api(self, img_b64: str, user_prompt: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Call the Claude API with an image to get metadata.
    
        Args:
            img_b64: Base64-encoded image string
            user_prompt: Optional custom user prompt
        
        Returns:
            Dictionary with analysis results if successful, None otherwise
        """
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
    
        # Make sure the base64 doesn't have the prefix if it's included
        if img_b64.startswith("data:image"):
            # Extract just the base64 part after the comma
            img_b64 = img_b64.split(",", 1)[1]
    
        # Generate the system prompt with film photography expertise
        system_prompt = """You are a photography assistant specializing in film photography analysis. 
You have expert knowledge of analog photography, including:
- Film formats (35mm, 120 medium format in various aspect ratios)
- Film characteristics (grain structure, contrast, color rendition)
- Lens characteristics for analog cameras
- Depth of field and aperture indicators
- Visual signatures of various film stocks

When analyzing images, pay special attention to:
1. Evidence of film format based on aspect ratio, frame edges, and grain structure
2. Optical characteristics that reveal the type of lens used
3. Film stock characteristics visible in tone, grain, contrast, and color rendition"""

        # Get the analysis prompt (either custom or default)
        analysis_prompt = user_prompt if user_prompt else self.get_analysis_prompt()

        # Structure for the messages API
        payload = {
            "model": self.model,
            "system": system_prompt,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": analysis_prompt
                        },
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": img_b64
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 1024,
            "stream": False
        }
        
        try:
            response = requests.post(self.api_url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            result = response.json()
        
            # In the messages API, the response is in content field
            response_text = result.get("content", [{}])[0].get("text", "")

            # Extract JSON from the response
            ai_result = self.parse_response(response_text)
            if not ai_result:
                return None
                
            # Format the result
            formatted_result = self.format_result(ai_result)
            return formatted_result
            
        except requests.RequestException as e:
            logger.error(f"Claude API network error: {str(e)}")
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                logger.error(f"Response details: {e.response.text}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Claude API JSON parsing error: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error calling Claude API: {str(e)}")
            return None
