#!/usr/bin/env python3
"""
Example 3: Processing Specific Images

This example demonstrates how to process only specific images from the catalog
by filtering them based on filename patterns.
"""

import os
import sys
import logging
import argparse
from pathlib import Path

# Add the parent directory to sys.path to import the package
sys.path.insert(0, str(Path(__file__).parent.parent))

from lightroom_ai.config import load_config
from lightroom_ai.catalog_db import CatalogDatabase
from lightroom_ai.batch_processor import BatchProcessor
from lightroom_ai.logging_setup import setup_logging


def filtering_example():
    """Image filtering example."""
    # Setup argument parser
    parser = argparse.ArgumentParser(description="Image filtering example for Lightroom AI Tool")
    parser.add_argument("catalog_path", help="Path to Lightroom catalog (.lrcat file)")
    parser.add_argument("--filter", required=True, help="Filter images by this text in filename")
    parser.add_argument("--max-images", type=int, default=None, 
                       help="Maximum number of images to process")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    # Check if catalog exists
    if not os.path.exists(args.catalog_path):
        print(f"Error: Catalog not found: {args.catalog_path}")
        return 1

    # Load configuration
    config_path = os.path.join(Path(__file__).parent.parent, "config.json")
    if not os.path.exists(config_path):
        print(f"Error: Configuration file not found: {config_path}")
        return 1

    config = load_config(config_path)
    
    # Override debug mode if specified
    if args.debug:
        config.debug_mode = True
        config.log_level = "DEBUG"
    
    # Override max images if specified
    if args.max_images:
        config.max_images = args.max_images

    # Setup logging
    setup_logging(config)
    
    print(f"Processing catalog: {args.catalog_path}")
    print(f"Filtering images by text: '{args.filter}'")
    
    # Connect to the catalog
    db = CatalogDatabase(args.catalog_path, config)
    
    # Get images from the catalog
    all_images = db.get_images(config.max_images)
    
    # Filter images by filename
    filtered_images = [img for img in all_images if args.filter in img[2]]
    print(f"Found {len(filtered_images)} images matching filter out of {len(all_images)} total")
    
    if not filtered_images:
        print("No images match the filter criteria.")
        return 0
    
    # Process the filtered images
    processor = BatchProcessor(args.catalog_path, config)
    stats = processor.run(filtered_images)
    
    # Print summary
    print("\nProcessing complete!")
    print(f"Total images processed: {stats['total_images']}")
    print(f"Successfully processed: {stats['successful_images']}")
    print(f"Failed to process: {stats['failed_images']}")
    
    if 'total_time' in stats:
        print(f"Total time: {stats['total_time']:.1f} seconds")
        print(f"Average time per image: {stats['avg_time_per_image']:.2f} seconds")
    
    return 0


if __name__ == "__main__":
    sys.exit(filtering_example())
