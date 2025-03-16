#!/usr/bin/env python3
"""
Example 4: Parallel Processing for Speed

This example demonstrates how to use parallel processing to speed up
the AI analysis of images by utilizing multiple CPU cores.
"""

import os
import sys
import logging
import argparse
from pathlib import Path

# Add the parent directory to sys.path to import the package
sys.path.insert(0, str(Path(__file__).parent.parent))

from lightroom_ai.config import load_config
from lightroom_ai.batch_processor import BatchProcessor
from lightroom_ai.logging_setup import setup_logging


def parallel_processing_example():
    """Parallel processing example."""
    # Setup argument parser
    parser = argparse.ArgumentParser(description="Parallel processing example for Lightroom AI Tool")
    parser.add_argument("catalog_path", help="Path to Lightroom catalog (.lrcat file)")
    parser.add_argument("--max-workers", type=int, default=4, 
                        help="Number of worker threads to use")
    parser.add_argument("--batch-size", type=int, default=20,
                        help="Number of images to process in each batch")
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
    
    # Override configuration with command line arguments
    config.max_workers = args.max_workers
    config.batch_size = args.batch_size
    
    if args.max_images:
        config.max_images = args.max_images
        
    if args.debug:
        config.debug_mode = True
        config.log_level = "DEBUG"

    # Setup logging
    setup_logging(config)
    
    print(f"Processing catalog: {args.catalog_path}")
    print(f"Using {args.max_workers} worker threads")
    print(f"Batch size: {args.batch_size} images")
    
    # Create and run the batch processor
    processor = BatchProcessor(args.catalog_path, config)
    
    print("Starting parallel processing...")
    stats = processor.run()
    
    # Print summary
    print("\nProcessing complete!")
    print(f"Total images: {stats['total_images']}")
    print(f"Successfully processed: {stats['successful_images']}")
    print(f"Failed to process: {stats['failed_images']}")
    print(f"Skipped (already processed): {stats.get('skipped_images', 0)}")
    
    if 'total_time' in stats:
        print(f"Total time: {stats['total_time']:.1f} seconds")
        print(f"Average time per image: {stats['avg_time_per_image']:.2f} seconds")
        
        # Calculate theoretical speedup
        single_thread_time = stats['avg_time_per_image'] * stats['total_images']
        speedup = single_thread_time / stats['total_time']
        efficiency = speedup / args.max_workers * 100
        
        print(f"Parallelization efficiency: {efficiency:.1f}%")
        
        if efficiency < 50:
            print("\nNote: Low parallelization efficiency.")
            print("This could be due to:")
            print("- API rate limiting")
            print("- Network bottlenecks")
            print("- Disk I/O limitations")
            print("\nTry reducing the number of workers or increasing the batch size.")
    
    return 0


if __name__ == "__main__":
    sys.exit(parallel_processing_example())
