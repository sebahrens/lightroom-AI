"""
Claude-specific implementation of AI provider with film photography analysis.
"""

import json
import re
import logging
import requests
from typing import Dict, Any, Optional, List, Callable

from .config import AppConfig, ClaudeConfig
from .ai_providers import AiProvider
from .logging_setup import get_logger
from .utils import extract_json

logger = get_logger(__name__)


class ClaudeProvider(AiProvider):
    """Claude API implementation of AI provider with film photography expertise."""
    
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
        
        # Get categories from config
        self.categories = getattr(config, 'categories', {})
        
        # Check if we should use the categorical approach
        self.use_categories = getattr(config, 'use_categorical_keywords', True)
        
    def analyze_image(self, image_b64: str) -> Optional[Dict[str, Any]]:
        """
        Analyze an image using Claude API and extract metadata.
        
        Args:
            image_b64: Base64-encoded image string
            
        Returns:
            Dictionary with analysis results if successful, None otherwise
        """
        def make_request() -> Optional[Dict[str, Any]]:
            return self._call_claude_api(image_b64)
            
        return self.call_with_retries(make_request)
        
    def _call_claude_api(self, img_b64: str) -> Optional[Dict[str, Any]]:
        """
        Call the Claude API with an image to get metadata with film photography analysis.
    
        Args:
        img_b64: Base64-encoded image string
        
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
                            "text": self._get_film_analysis_prompt()
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
            ai_result = extract_json(response_text, logger, self.config.debug_mode)
            if not ai_result:
                return None
            return self._format_film_analysis_result(ai_result)
            
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
            
    def _get_film_analysis_prompt(self) -> str:
        """Get the specialized film photography analysis prompt."""
        prompt = """Please analyze this film photograph and categorize it according to these predefined categories.

I need specific analysis for film photography. This is a camera-scanned analog film image that needs to be analyzed for its film format, film characteristics, and lens characteristics.

"""
        # Add the standard categories
        for category, values in self.categories.items():
            if values:
                # Format category name for display (e.g., 'film_format' → 'FILM FORMAT')
                category_display = category.replace('_', ' ').upper()
                
                # Only ask to select one value for film_format
                if category == 'film_format':
                    prompt += f"{category_display} (select the 1 most likely match):\n"
                # For lens and film categories, specifically request detailed analysis
                elif category in ['film_characteristics', 'lens_characteristics', 'focal_length_estimate', 'aperture_evidence']:
                    prompt += f"{category_display} (select up to 3 that apply):\n"
                else:
                    prompt += f"{category_display} (select up to 2 best matches):\n"
                
                prompt += f"{', '.join(values)}\n\n"
        
        # Add specific analysis instructions
        prompt += """
          For FILM FORMAT analysis, consider:
          - If the image has a 3:2 aspect ratio with distinctive 35mm grain pattern, select "35mm"
          - If it has a square or near-square format (6x6), select "120-6x6"
          - If it's rectangular but wider than 35mm (6x4.5, 6x7, 6x9), select the appropriate 120 format
          - Look for film border edges, sprocket holes, or frame numbers that might be visible

          For LENS CHARACTERISTICS, consider:
          - Perspective distortion (wide-angle vs. telephoto compression)
          - Depth of field and bokeh qualities (lens speed indicators)
          - Sharpness, contrast, and rendering characteristics
          - Any distinctive lens signatures (swirly bokeh, particular flare patterns)

          Also provide an aesthetic score from 0 to 10, where 10 represents exceptional artistic quality.

          Return ONLY a JSON object with this structure:
          {
          """
        
        # Add each category to the requested JSON structure
        for category in self.categories.keys():
            prompt += f'    "{category}": [...],\n'
            
        prompt += """    "aesthetic_score": ...
          }

          Choose only from the provided category values. If a category doesn't apply, include an empty array for that category."""
        
        return prompt
        
    def _format_film_analysis_result(self, ai_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format film analysis results for the application.
        
        Args:
            ai_result: Raw AI result with categories
            
        Returns:
            Formatted result compatible with the application
        """
        # Extract standard keywords and tags for backward compatibility
        content_keywords = ai_result.get("content_type", []) + ai_result.get("main_subject", [])
        
        # Add film-specific keywords
        film_keywords = []
        if "film_format" in ai_result and ai_result["film_format"]:
            film_keywords.extend(ai_result["film_format"])
        
        # Add lens-related keywords
        lens_keywords = []
        for cat in ["lens_characteristics", "focal_length_estimate", "aperture_evidence"]:
            if cat in ai_result and ai_result[cat]:
                lens_keywords.extend(ai_result[cat])
        
        # Add film characteristics
        film_char_keywords = ai_result.get("film_characteristics", [])
        
        # Combine standard tags
        standard_tags = (
            ai_result.get("lighting", []) + 
            ai_result.get("color", []) + 
            ai_result.get("mood", []) + 
            ai_result.get("style", [])
        )
        
        # Create the full metadata object
        metadata = {
            "keywords": content_keywords + film_keywords,
            "tags": standard_tags + lens_keywords + film_char_keywords,
            "aesthetic_score": ai_result.get("aesthetic_score", 0),
            
            # Store all the detailed categorization
            "categories": {
                category: ai_result.get(category, [])
                for category in self.categories.keys()
            }
        }
        
        return metadata
