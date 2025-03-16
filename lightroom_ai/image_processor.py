"""
Prepare images for AI analysis.
"""

import io
import base64
import logging
from typing import Optional, Dict, Any, Tuple
from PIL import Image

from .config import AppConfig
from .logging_setup import get_logger

logger = get_logger(__name__)


class ImageProcessor:
    """Class to handle image processing for AI analysis."""
    
    def __init__(self, config: AppConfig):
        """
        Initialize the image processor.
        
        Args:
            config: Application configuration
        """
        self.config = config
        self.max_resolution = config.preview_max_resolution
        
    def prepare_image_for_ai(self, img: Image.Image) -> Optional[str]:
        """
        Prepare an image for AI processing by resizing if needed and converting to base64.
        
        Args:
            img: PIL Image object
            
        Returns:
            Base64-encoded image string if successful, None otherwise
        """
        if not img:
            return None
        
        try:
            img_copy = img.copy()
            
            # If extremely large, apply more aggressive scaling
            if img_copy.width * img_copy.height > 20000000:  # ~20MP threshold
                logger.debug(f"Image very large ({img_copy.width}x{img_copy.height}), applying aggressive downscaling")
                max_resolution = min(self.max_resolution, 800)
            else:
                max_resolution = self.max_resolution
            
            if max_resolution and (img_copy.width > max_resolution or img_copy.height > max_resolution):
                img_copy.thumbnail((max_resolution, max_resolution))
                logger.debug(f"Resized image to {img_copy.width}x{img_copy.height}")
            
            buffer = io.BytesIO()
            # Ensure we're saving as JPEG regardless of input format
            if img_copy.mode != 'RGB':
                img_copy = img_copy.convert('RGB')
            img_copy.save(buffer, format="JPEG", quality=85)
            img_bytes = buffer.getvalue()
            
            img_b64 = base64.b64encode(img_bytes).decode('utf-8')
            
            img_copy.close()
            buffer.close()
            
            logger.debug(f"Prepared image for AI analysis (base64 size: {len(img_b64)} chars)")
            return img_b64
        except Exception as e:
            logger.error(f"Error preparing image for AI: {str(e)}")
            return None
            
    def get_image_dimensions(self, img: Image.Image) -> Dict[str, Any]:
        """
        Get the dimensions of an image.
        
        Args:
            img: PIL Image object
            
        Returns:
            Dictionary with image dimensions and format
        """
        if not img:
            return {}
            
        try:
            return {
                'width': img.width,
                'height': img.height,
                'format': img.format,
                'mode': img.mode,
                'aspect_ratio': round(img.width / img.height, 2) if img.height > 0 else 0
            }
        except Exception as e:
            logger.error(f"Error getting image dimensions: {str(e)}")
            return {}
            
    def process_image(self, img: Image.Image) -> Tuple[Optional[str], Dict[str, Any]]:
        """
        Process an image for AI analysis and get its metadata.
        
        Args:
            img: PIL Image object
            
        Returns:
            Tuple of (base64-encoded image string, image metadata)
        """
        if not img:
            return None, {}
            
        image_b64 = self.prepare_image_for_ai(img)
        image_dimensions = self.get_image_dimensions(img)
        
        return image_b64, image_dimensions