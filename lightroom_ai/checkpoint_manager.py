"""
Checkpoint handling for resumable processing.
"""

import os
import json
import logging
from typing import Set, List, Optional

from .config import AppConfig
from .logging_setup import get_logger

logger = get_logger(__name__)


class CheckpointManager:
    """Class to handle checkpoint saving and loading."""
    
    def __init__(self, checkpoint_file: str, config: AppConfig):
        """
        Initialize the checkpoint manager.
        
        Args:
            checkpoint_file: Path to the checkpoint file
            config: Application configuration
        """
        self.checkpoint_file = checkpoint_file
        self.config = config
        
    def load_checkpoint(self) -> Set[int]:
        """
        Load checkpoint file to avoid reprocessing images.
        
        Returns:
            Set of processed image IDs
        """
        if not self.config.use_checkpoint:
            return set()
            
        if os.path.exists(self.checkpoint_file):
            try:
                with open(self.checkpoint_file, 'r') as f:
                    image_ids = json.load(f)
                    return set(image_ids)
            except Exception as e:
                logger.error(f"Error loading checkpoint file: {str(e)}")
                
        return set()
        
    def save_checkpoint(self, processed_ids: Set[int]) -> bool:
        """
        Save checkpoint file.
        
        Args:
            processed_ids: Set of processed image IDs
            
        Returns:
            True if successful, False otherwise
        """
        if not self.config.use_checkpoint:
            return False
            
        try:
            with open(self.checkpoint_file, 'w') as f:
                json.dump(list(processed_ids), f)
            return True
        except Exception as e:
            logger.error(f"Error saving checkpoint file: {str(e)}")
            return False
            
    def clear_checkpoint(self) -> bool:
        """
        Clear checkpoint file.
        
        Returns:
            True if successful, False otherwise
        """
        if os.path.exists(self.checkpoint_file):
            try:
                os.remove(self.checkpoint_file)
                logger.info(f"Checkpoint file cleared: {self.checkpoint_file}")
                return True
            except Exception as e:
                logger.error(f"Error clearing checkpoint file: {str(e)}")
                return False
        return True