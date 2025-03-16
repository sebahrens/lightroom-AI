#!/usr/bin/env python3
"""
Example 6: Database Analysis and Debugging

This example demonstrates how to analyze the Lightroom catalog database structure
and debug issues with preview file extraction.
"""

import os
import sys
import logging
import argparse
from pathlib import Path
import pprint

# Add the parent directory to sys.path to import the package
sys.path.insert(0, str(Path(__file__).parent.parent))

from lightroom_ai.config import load_config
from lightroom_ai.catalog_db import CatalogDatabase
from lightroom_ai.preview_db import PreviewDatabase
from lightroom_ai.filesystem import FilesystemHelper
from lightroom_ai.preview_extractor import PreviewExtractor
from lightroom_ai.logging_setup import setup_logging


def database_analysis_example():
    """Database analysis example."""
    # Setup argument parser
    parser = argparse.ArgumentParser(description="Database analysis example for Lightroom AI Tool")
    parser.add_argument("catalog_path", help="Path to Lightroom catalog (.lrcat file)")
    parser.add_argument("--debug-image", help="Debug a specific image by filename")
    parser.add_argument("--dump-preview-db", action="store_true", 
                        help="Dump preview database information")
    parser.add_argument("--analyze-filesystem", action="store_true",
                       help="Analyze preview filesystem structure")
    args = parser.parse_args()

    # Check if catalog exists
    if not os.path.exists(args.catalog_path):
        print(f"Error: Catalog not found: {args.catalog_path}")
        return 1

    # Load configuration
    config_path = os.path.join(Path(__file__).parent.parent, "config.json")
    config = load_config(config_path)
    
    # Always enable debug mode for analysis
    config.debug_mode = True
    config.log_level = "DEBUG"
    config.deep_search = True

    # Setup logging
    setup_logging(config)
    
    print(f"Analyzing catalog: {args.catalog_path}")
    
    # Connect to the catalog
    db = CatalogDatabase(args.catalog_path, config)
    
    # Analyze database structure
    print("Analyzing Lightroom database structure...")
    db_info = db.analyze_database_structure()
    
    # Print database information
    print("\nDatabase Analysis Results:")
    print(f"- Has Adobe_images table: {db_info.get('has_adobe_images', False)}")
    print(f"- Has AgPreviewImages table: {db_info.get('has_preview_images', False)}")
    print(f"- Has AgLibraryFile table: {db_info.get('has_library_file', False)}")
    print(f"- Has previews directory: {db_info.get('has_previews_dir', False)}")
    print(f"- Has smart previews directory: {db_info.get('has_smart_previews_dir', False)}")
    
    # Print column information
    if 'column_map' in db_info:
        print("\nColumn Information:")
        for table, columns in db_info['column_map'].items():
            print(f"- {table}: {', '.join(columns)}")
    
    # Preview database analysis
    if args.dump_preview_db and db_info.get('has_previews_dir'):
        print("\nAnalyzing Preview Database...")
        preview_dir = db_info.get('previews_dir')
        preview_db = PreviewDatabase(preview_dir, config)
        preview_info = preview_db.analyze_preview_database()
        
        if preview_info.get('has_preview_db'):
            print("Preview database found!")
            print(f"- Tables: {', '.join(preview_info.get('tables', []))}")
            print(f"- Has UUID table: {preview_info.get('has_preview_uuid_table', False)}")
            
            # Print preview columns if available
            if 'preview_columns' in preview_info:
                print(f"- Preview columns: {', '.join(preview_info.get('preview_columns'))}")
            
            # Collect file patterns
            patterns = preview_db.collect_preview_file_patterns()
            if patterns:
                print(f"- Detected filename patterns: {patterns}")
        else:
            print("No preview database found.")
    
    # Filesystem analysis
    if args.analyze_filesystem:
        print("\nAnalyzing Filesystem Structure...")
        fs = FilesystemHelper(args.catalog_path, config)
        
        catalog_info = fs.get_catalog_info()
        print(f"Catalog name: {catalog_info['catalog_name']}")
        print(f"Previews directory: {catalog_info['previews_dir']}")
        print(f"Smart previews directory: {catalog_info['smart_previews_dir']}")
        
        # Debug directory structure
        if catalog_info['has_previews_dir']:
            print("\nPreviews Directory Structure:")
            fs.debug_directory_structure(catalog_info['previews_dir'], depth=2)
        
        if catalog_info['has_smart_previews_dir']:
            print("\nSmart Previews Directory Structure:")
            fs.debug_directory_structure(catalog_info['smart_previews_dir'], depth=1)
    
    # Debug specific image
    if args.debug_image:
        print(f"\nDebugging specific image: {args.debug_image}")
        
        # Get all images
        images = db.get_images()
        
        # Find matching images
        matches = [img for img in images if args.debug_image in img[2]]
        
        if not matches:
            print(f"No images found matching '{args.debug_image}'")
            return 0
        
        print(f"Found {len(matches)} matching images")
        
        # Create preview extractor
        extractor = PreviewExtractor(args.catalog_path, config)
        
        # Optimize search strategies
        extractor.optimize_search_strategies(db_info)
        
        # Process each match
        for i, img in enumerate(matches):
            print(f"\nImage {i+1}:")
            print(f"- ID: {img[0]}")
            print(f"- File ID: {img[1]}")
            print(f"- Filename: {img[2]}")
            print(f"- Path: {img[3]}")
            print(f"- Root: {img[4]}")
            print(f"- Image Global ID: {img[5]}")
            print(f"- File Global ID: {img[6]}")
            
            # Try to locate preview
            preview_path = extractor.locate_preview_file(img)
            
            if preview_path:
                print(f"- Found preview: {preview_path}")
                
                # Try to extract JPEG
                img_obj = extractor.extract_jpeg_from_preview(preview_path)
                if img_obj:
                    print(f"- Successfully extracted image: {img_obj.format}, {img_obj.width}x{img_obj.height}")
                    img_obj.close()
                else:
                    print("- Failed to extract image from preview")
            else:
                print("- No preview found")
    
    # Close database connection
    db.close()
    
    return 0


if __name__ == "__main__":
    sys.exit(database_analysis_example())
