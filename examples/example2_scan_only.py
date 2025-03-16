#!/usr/bin/env python3
"""
Example 2: Scan-Only Mode for Testing Preview Extraction

This example demonstrates how to use the scan-only mode to test
if the tool can correctly locate preview files without making AI API calls.
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
from lightroom_ai.preview_extractor import PreviewExtractor
from lightroom_ai.logging_setup import setup_logging


def scan_only_example():
    """Scan-only mode example."""
    # Setup argument parser
    parser = argparse.ArgumentParser(description="Scan-only example for Lightroom AI Tool")
    parser.add_argument("catalog_path", help="Path to Lightroom catalog (.lrcat file)")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--max-images", type=int, default=None, 
                       help="Maximum number of images to scan")
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
    
    print(f"Scanning catalog: {args.catalog_path}")
    print("This will check if preview files can be found but won't process them with AI")
    
    # Connect to the catalog
    db = CatalogDatabase(args.catalog_path, config)
    
    # Get images from the catalog
    images = db.get_images(config.max_images)
    print(f"Found {len(images)} images in catalog")
    
    # Create a preview extractor
    extractor = PreviewExtractor(args.catalog_path, config)
    
    # Scan for previews
    total_images, found_previews = extractor.scan_previews(images)
    
    # Print summary
    print("\nScan complete!")
    print(f"Total images: {total_images}")
    print(f"Found previews: {found_previews}")
    print(f"Preview success rate: {found_previews/total_images*100:.1f}%")
    
    if found_previews < total_images:
        print("\nSome images don't have previews.")
        print("Suggestions:")
        print("- Generate standard previews in Lightroom (Library > Previews > Build Standard-Sized Previews)")
        print("- Enable smart previews in Lightroom")
        print("- Check if you have full access to the Lightroom catalog and preview files")
    
    return 0


if __name__ == "__main__":
    sys.exit(scan_only_example())
