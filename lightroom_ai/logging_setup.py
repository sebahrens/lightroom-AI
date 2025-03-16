"""
Logging configuration for the Lightroom AI script.
"""

import logging
import os
import sys
from typing import Optional
from .config import AppConfig


def setup_logging(config: AppConfig, log_prefix: Optional[str] = None) -> None:
    """
    Configure logging based on settings.
    
    Args:
        config: Application configuration
        log_prefix: Optional prefix for the log file name
    """
    log_level = getattr(logging, config.log_level)
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    
    # Set up log file if specified
    log_file = config.log_file
    
    # Create a timestamp-based log file if prefix provided but no specific file
    if not log_file and log_prefix:
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        log_file = f"{log_prefix}_{timestamp}.log"
    
    if log_file:
        # Create directory for log file if it doesn't exist
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
            
        logging.basicConfig(
            filename=log_file,
            level=log_level,
            format=log_format
        )
        
        # Also log to console if debug mode is enabled
        if config.debug_mode:
            console = logging.StreamHandler(sys.stdout)
            console.setLevel(log_level)
            console.setFormatter(logging.Formatter(log_format))
            logging.getLogger('').addHandler(console)
    else:
        logging.basicConfig(
            level=log_level,
            format=log_format
        )
    
    # Log some initial information
    provider_type = getattr(config.provider, 'provider_type', 'unknown')
    logging.info(f"Logging initialized. Using AI provider: {provider_type}")
    
    if config.debug_mode:
        logging.debug("Debug mode enabled")
        
        # Log additional system information
        logging.debug(f"Python version: {sys.version}")
        logging.debug(f"Platform: {sys.platform}")
        
        # Log configuration summary
        logging.debug(f"Configuration summary:")
        logging.debug(f"  Max retries: {config.max_retries}")
        logging.debug(f"  Batch size: {config.batch_size}")
        logging.debug(f"  Max workers: {config.max_workers}")
        logging.debug(f"  Max preview resolution: {config.preview_max_resolution}")
        logging.debug(f"  Use smart previews: {config.use_smart_previews}")
        logging.debug(f"  Memory limit: {config.memory_limit_mb} MB")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.
    
    Args:
        name: Name for the logger
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)
