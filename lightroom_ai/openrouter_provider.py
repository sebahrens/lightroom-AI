"""
OpenRouter API implementation for AI image analysis.
"""

import json
import time
import requests
from typing import Dict, Any, Optional, List
import base64
import logging
import re

from .config import AppConfig
from .logging_setup import get_logger
from .utils import extract_json

logger = get_logger(__name__)

class OpenRouterProvider:
    """OpenRouter API implementation of AI provider with film photography expertise."""
    
    def __init__(self, config: AppConfig):
        """
        Initialize the OpenRouter provider.
        
        Args:
            config: Application configuration
        """
        self.config = config
        self.provider_config = config.provider
        
        self.api_key = self.provider_config.api_key
        self.api_url = self.provider_config.api_url
        self.model = self.provider_config.model
        self.site_url = self.provider_config.site_url
        self.title = self.provider_config.title
        self.max_retries = config.max_retries
        self.debug_mode = config.debug_mode
        
        logger.info(f"Initialized OpenRouter provider with model: {self.model}")
    
    def analyze_image(self, image_b64: str, user_prompt: Optional[str] = None, system_prompt: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Analyze an image using OpenRouter API and extract metadata.
        
        Args:
            image_b64: Base64-encoded image string
            user_prompt: Optional custom user prompt
            system_prompt: Optional system prompt
            
        Returns:
            Dictionary with analysis results if successful, None otherwise
        """
        def make_request() -> Optional[Dict[str, Any]]:
            try:
                result = self._call_openrouter_api(image_b64, user_prompt, system_prompt)
                if not result:
                    logger.warning("Empty response from OpenRouter API")
                    return None
                
                # Format the result
                formatted_result = self._format_film_analysis_result(result)
                return formatted_result
                
            except Exception as e:
                logger.error(f"Error analyzing image with OpenRouter: {str(e)}")
                if self.debug_mode:
                    import traceback
                    logger.error(f"Traceback: {traceback.format_exc()}")
                return None
        
        # Try with retries
        for attempt in range(self.max_retries):
            result = make_request()
            if result:
                return result
            
            if attempt < self.max_retries - 1:
                logger.info(f"Retrying OpenRouter API call in 5 seconds (attempt {attempt + 1}/{self.max_retries})")
                time.sleep(5)
        
        logger.error(f"Failed to analyze image after {self.max_retries} attempts")
        return None
    
    def _call_openrouter_api(self, img_b64: str, user_prompt: Optional[str] = None, system_prompt: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Call the OpenRouter API with the image.
        
        Args:
            img_b64: Base64-encoded image string
            user_prompt: Optional custom user prompt
            system_prompt: Optional system prompt
            
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
        
        # Prepare the prompt
        prompt = user_prompt if user_prompt else self._get_film_analysis_prompt()
        
        # Prepare the messages
        messages = []
        
        # Add system message if provided
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        
        # Add user message with text and image
        messages.append({
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}
            ]
        })
        
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
            
            if self.debug_mode:
                logger.debug(f"OpenRouter API response: {json.dumps(response_data, indent=2)}")
            
            # Extract the response content
            if 'choices' in response_data and len(response_data['choices']) > 0:
                message = response_data['choices'][0].get('message', {})
                content = message.get('content', '')
                
                return {"response": content}
            
            logger.error("Invalid response format from OpenRouter API")
            return None
            
        except Exception as e:
            logger.error(f"Error calling OpenRouter API: {str(e)}")
            if self.debug_mode:
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
            return None
    
    def _get_film_analysis_prompt(self) -> str:
        """
        Get the prompt for film analysis.
        
        Returns:
            Prompt string
        """
        return """You are an expert in film photography analysis. Analyze this photograph and provide detailed information about it.

Focus on identifying:
1. Film format (35mm, medium format, large format)
2. Film characteristics (color, black & white, grain, contrast)
3. Lens characteristics (sharpness, bokeh, distortion)
4. Focal length estimate (wide, normal, telephoto)
5. Aperture evidence (shallow/deep depth of field)

Also categorize the image by:
- Content type (portrait, landscape, street, etc.)
- Main subject
- Lighting conditions
- Color palette
- Mood/atmosphere
- Photographic style

Provide an aesthetic score from 1-10.

Format your response as a JSON object with these fields:
{
  "keywords": ["keyword1", "keyword2", ...],
  "tags": ["tag1", "tag2", ...],
  "aesthetic_score": 7.5,
  "categories": {
    "film_format": ["35mm"],
    "film_characteristics": ["color", "fine grain"],
    "lens_characteristics": ["sharp", "smooth bokeh"],
    "focal_length_estimate": ["50mm", "normal"],
    "aperture_evidence": ["shallow depth of field", "f/2.8"],
    "content_type": ["portrait", "environmental"],
    "main_subject": ["person", "urban"],
    "lighting": ["golden hour", "side lit"],
    "color": ["warm", "muted"],
    "mood": ["contemplative", "nostalgic"],
    "style": ["documentary", "candid"]
  }
}

Respond ONLY with the JSON object, no other text."""
    
    def _format_film_analysis_result(self, ai_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format the AI result into a standardized structure.
        
        Args:
            ai_result: Raw AI result
            
        Returns:
            Formatted result dictionary
        """
        if 'response' not in ai_result:
            logger.error("Invalid AI result format")
            return {"analysis": "Error: Invalid response format"}
        
        response_text = ai_result['response']
        
        # Try to extract JSON from the response
        try:
            # Look for JSON in the response
            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response_text, re.DOTALL)
            
            if json_match:
                json_str = json_match.group(1)
                analysis_data = json.loads(json_str)
            else:
                # Try to find JSON with curly braces
                start = response_text.find("{")
                end = response_text.rfind("}")
                if start != -1 and end != -1 and end > start:
                    json_str = response_text[start:end+1]
                    analysis_data = json.loads(json_str)
                else:
                    # If no JSON found, use the raw text
                    analysis_data = {"raw_analysis": response_text}
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse JSON from AI response: {e}")
            analysis_data = {"raw_analysis": response_text}
        
        return {"analysis": response_text, "structured_data": analysis_data}
