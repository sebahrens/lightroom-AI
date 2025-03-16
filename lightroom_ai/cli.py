"""
Command-line interface for the Lightroom AI script.
"""

import os
import sys
import argparse
import logging
from typing import Dict, Any, Optional, List

from .config import AppConfig, load_config, ClaudeConfig, OllamaConfig
from .logging_setup import setup_logging, get_logger
from .catalog_db import CatalogDatabase
from .preview_extractor import PreviewExtractor
from .batch_processor import BatchProcessor
from .checkpoint_manager import CheckpointManager

logger = get_logger(__name__)


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments.
    
    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description="Extract Lightroom previews and enhance metadata with AI"
    )
    
    parser.add_argument(
        "catalog_path",
        help="Path to Lightroom catalog (.lrcat file)"
    )
    
    parser.add_argument(
        "--config",
        default="config.json",
        help="Path to configuration JSON file (default: config.json)"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode regardless of config setting"
    )
    
    parser.add_argument(
        "--scan-only",
        action="store_true",
        help="Scan for previews but don't process with AI (for testing)"
    )
    
    parser.add_argument(
        "--filter",
        help="Filter images by filename pattern"
    )
    
    parser.add_argument(
        "--no-checkpoint",
        action="store_true",
        help="Ignore checkpoint file and process all images"
    )
    
    parser.add_argument(
        "--clear-checkpoint",
        action="store_true", 
        help="Clear checkpoint file before processing"
    )
    
    parser.add_argument(
        "--clear-cache",
        action="store_true", 
        help="Clear any cached preview locations"
    )
    
    parser.add_argument(
        "--batch-size",
        type=int,
        help="Override batch size from config file"
    )
    
    parser.add_argument(
        "--max-workers",
        type=int,
        help="Override max workers from config file"
    )
    
    parser.add_argument(
        "--max-images",
        type=int,
        help="Override max images from config file"
    )
    
    parser.add_argument(
        "--analyze-db",
        action="store_true",
        help="Perform detailed database analysis"
    )
    
    return parser.parse_args()


def process_arguments(args: argparse.Namespace, config: AppConfig) -> AppConfig:
    """
    Process command-line arguments and override config values.
    
    Args:
        args: Parsed arguments
        config: Loaded configuration
        
    Returns:
        Updated configuration
    """
    # Override from CLI
    if args.debug:
        config.debug_mode = True
    if args.no_checkpoint:
        config.use_checkpoint = False
    if args.batch_size:
        config.batch_size = args.batch_size
    if args.max_workers:
        config.max_workers = args.max_workers
    if args.max_images:
        config.max_images = args.max_images
        
    return config


def run_cli() -> int:
    """
    Run the command-line interface.
    
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        # Parse arguments
        args = parse_arguments()
        
        # Load configuration
        config = load_config(args.config)
        
        # Process arguments and override config
        config = process_arguments(args, config)
        
        # Setup logging
        setup_logging(config, log_prefix="lightroom_ai")
        
        # Log system information
        logger.info(f"Python version: {sys.version}")
        logger.info(f"Platform: {sys.platform}")
        logger.info(f"Using AI provider: {getattr(config.provider, 'provider_type', 'unknown')}")
        logger.info(f"Debug mode: {'enabled' if config.debug_mode else 'disabled'}")
        logger.info(f"Smart previews: {'enabled' if config.use_smart_previews else 'disabled'}")
        logger.info(f"Parallelization: {config.max_workers} workers")
        logger.info(f"Batch size: {config.batch_size} images")
        logger.info(f"Max images: {config.max_images or 'unlimited'}")
        
        # Check if catalog exists
        if not os.path.exists(args.catalog_path):
            logger.error(f"Catalog not found: {args.catalog_path}")
            return 1
        
        # Clear checkpoint if requested
        if args.clear_checkpoint:
            checkpoint_manager = CheckpointManager(f"{args.catalog_path}.checkpoint.json", config)
            checkpoint_manager.clear_checkpoint()
        
        # Connect to catalog database
        db = CatalogDatabase(args.catalog_path, config)
        
        # Get images from catalog
        images = db.get_images(config.max_images)
        
        # Filter images if requested
        if args.filter:
            filtered_images = [
                img for img in images if args.filter in img[2]
            ]
            logger.info(f"Filtered to {len(filtered_images)} images matching '{args.filter}'")
            images = filtered_images
        
        # Create preview extractor
        preview_extractor = PreviewExtractor(args.catalog_path, config)
        
        # Clear preview cache if requested
        if args.clear_cache:
            preview_extractor.clear_cache()
        
        # Database analysis if requested
        if args.analyze_db:
            logger.info("Performing detailed database analysis...")
            db_info = db.analyze_database_structure()
            if db_info:
                logger.info(f"Analysis complete: {len(db_info)} properties found")
                for key, value in db_info.items():
                    if isinstance(value, dict) or isinstance(value, list):
                        logger.info(f"  {key}: {type(value).__name__} with {len(value)} items")
                    else:
                        logger.info(f"  {key}: {value}")
        
        # Scan-only mode
        if args.scan_only:
            preview_extractor.scan_previews(images)
            return 0
        
        # Process all images
        processor = BatchProcessor(args.catalog_path, config)
        stats = processor.run(images)
        
        # Log final stats
        logger.info("Processing complete")
        logger.info(f"Total images: {stats['total_images']}")
        logger.info(f"Successfully processed: {stats['successful_images']}")
        logger.info(f"Failed to process: {stats['failed_images']}")
        logger.info(f"Skipped (already processed): {stats['skipped_images']}")
        
        if 'total_time' in stats:
            logger.info(f"Total time: {stats['total_time']:.1f} seconds")
            logger.info(f"Average time per image: {stats['avg_time_per_image']:.2f} seconds")
        
        return 0
        
    except Exception as e:
        logger.error(f"Script execution failed: {str(e)}")
        if 'config' in locals() and config.debug_mode:
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
        return 1
