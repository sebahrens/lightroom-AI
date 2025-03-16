"""
Utility functions for Lightroom AI processing.
"""

import os
import logging
import re
import json
from typing import Dict, Any, Optional
from .logging_setup import get_logger

logger = get_logger(__name__)

def setup_logging(config):
    """
    Set up logging configuration based on the provided app config.
    
    Args:
        config: Application configuration object with log_level and log_file attributes
    """
    log_level = getattr(logging, config.log_level, logging.INFO)
    
    # Configure basic logging
    logging_config = {
        'level': log_level,
        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        'datefmt': '%Y-%m-%d %H:%M:%S',
    }
    
    # Add file handler if log_file is specified
    if config.log_file:
        log_dir = os.path.dirname(config.log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        logging_config['filename'] = config.log_file
        logging_config['filemode'] = 'a'
    
    # Apply configuration
    logging.basicConfig(**logging_config)
    
    # Set level for third-party loggers to reduce noise
    logging.getLogger('PIL').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    
    logger.debug(f"Logging configured with level: {config.log_level}")

def get_preview_resolution_rank(file_path: str) -> int:
    """
    Determine the resolution rank of a preview file based on its suffix.
    
    Args:
        file_path: Path to the preview file
        
    Returns:
        Rank value (higher means higher resolution)
    """
    file_name = os.path.basename(file_path)
    
    # High resolution
    if any(suffix in file_name for suffix in ('_3202', '_3200', '_3951', '_3199')):
        return 3
    # Medium resolution
    elif any(suffix in file_name for suffix in ('_1601', '_1600', '_1975', '_1599')):
        return 2
    # Low resolution
    elif any(suffix in file_name for suffix in ('_800', '_799', '_987')):
        return 1
    # Unknown
    return 0

def extract_json(response_text, logger, debug_mode=False):
    """
    Extract a JSON object from response_text reliably.
    
    Args:
        response_text: Text containing JSON
        logger: Logger instance
        debug_mode: Whether to log debug information
        
    Returns:
        Extracted JSON as a dictionary or None if extraction failed
    """
    if not response_text:
        return None
    
    # Try direct JSON parsing first
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        if debug_mode:
            logger.debug("Direct JSON parsing failed, trying alternative methods")
    
    # Try to find JSON in code blocks
    json_pattern = r'```(?:json)?\s*([\s\S]*?)\s*```'
    matches = re.findall(json_pattern, response_text)
    
    for match in matches:
        try:
            return json.loads(match)
        except json.JSONDecodeError:
            continue
    
    # Try to find JSON with curly braces for objects
    try:
        start = response_text.find("{")
        end = response_text.rfind("}")
        if start != -1 and end != -1 and end > start:
            json_str = response_text[start:end+1]
            if debug_mode:
                logger.debug(f"Attempting to parse JSON object: {json_str[:100]}...")
            return json.loads(json_str)
    except json.JSONDecodeError:
        if debug_mode:
            logger.debug("Failed to parse JSON object with braces")
    
    # Try to find JSON with square brackets for arrays
    try:
        start = response_text.find("[")
        end = response_text.rfind("]")
        if start != -1 and end != -1 and end > start:
            json_str = response_text[start:end+1]
            if debug_mode:
                logger.debug(f"Attempting to parse JSON array: {json_str[:100]}...")
            return json.loads(json_str)
    except json.JSONDecodeError:
        if debug_mode:
            logger.debug("Failed to parse JSON array with brackets")
    
    # Try to repair truncated JSON arrays
    try:
        if '[' in response_text and ']' not in response_text:
            # Find the last complete array element
            last_comma = response_text.rfind(',')
            if last_comma != -1:
                # Try to close the array at the last complete element
                repaired_json = response_text[:last_comma] + "]"
                if debug_mode:
                    logger.debug(f"Attempting to repair truncated JSON array: {repaired_json[:100]}...")
                return json.loads(repaired_json)
    except json.JSONDecodeError:
        if debug_mode:
            logger.debug("Failed to repair truncated JSON array")
    
    # Try to extract array patterns like [["keyword1"], ["keyword2"]]
    try:
        array_pattern = r'\[\s*\[.*?\]\s*(?:,\s*\[.*?\]\s*)*\]'
        array_match = re.search(array_pattern, response_text, re.DOTALL)
        if array_match:
            json_str = array_match.group(0)
            if debug_mode:
                logger.debug(f"Attempting to parse array pattern: {json_str[:100]}...")
            return json.loads(json_str)
    except (json.JSONDecodeError, re.error):
        if debug_mode:
            logger.debug("Failed to parse array pattern")
    
    # Try to extract individual array elements and reconstruct
    try:
        elements = re.findall(r'\[\s*"[^"]*"(?:\s*,\s*"[^"]*")*\s*\]', response_text)
        if elements:
            reconstructed = "[" + ",".join(elements) + "]"
            if debug_mode:
                logger.debug(f"Attempting to parse reconstructed array: {reconstructed[:100]}...")
            return json.loads(reconstructed)
    except (json.JSONDecodeError, re.error):
        if debug_mode:
            logger.debug("Failed to reconstruct array from elements")
    
    # Last resort: try to manually fix common JSON syntax errors
    try:
        # Replace single quotes with double quotes
        fixed_text = response_text.replace("'", '"')
        # Add missing quotes around keys
        fixed_text = re.sub(r'([{,])\s*(\w+):', r'\1"\2":', fixed_text)
        return json.loads(fixed_text)
    except json.JSONDecodeError:
        if debug_mode:
            logger.debug("Failed to fix JSON syntax errors")
    
    logger.error("Failed to extract JSON block from AI response")
    if debug_mode:
        logger.debug(f"Response text: {response_text[:500]}...")
    
    return None
