#!/usr/bin/env python3
"""
Example 7: Resuming an Interrupted Process

This example demonstrates how to use checkpointing features to manage
long-running processes and resume from where you left off if interrupted.
"""

import os
import sys
import time
import logging
import argparse
from pathlib import Path

# Add the parent directory to sys.path to import the package
sys.path.insert(0, str(Path(__file__).parent.parent))

from lightroom_ai.config import load_config
from lightroom_ai.batch_processor import BatchProcessor
from lightroom_ai.checkpoint_manager import CheckpointManager
from lightroom_ai.logging_setup import setup_logging


def resuming_example():
    """Resuming from checkpoint example."""
    # Setup argument parser
    parser = argparse.ArgumentParser(description="Checkpoint resuming example for Lightroom AI Tool")
    parser.add_argument("catalog_path", help="Path to Lightroom catalog (.lrcat file)")
    parser.add_argument("--clear-checkpoint", action="store_true", 
                        help="Clear checkpoint and start fresh")
    parser.add_argument("--no-checkpoint", action="store_true",
                       help="Disable checkpointing entirely")
    parser.add_argument("--simulate-interruption", action="store_true",
                       help="Simulate process interruption after a few images")
    parser.add_argument("--max-images", type=int, default=20, 
                       help="Maximum number of images to process")
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
    
    # Override settings from arguments
    if args.no_checkpoint:
        config.use_checkpoint = False
        print("Checkpointing disabled")
    
    if args.max_images:
        config.max_images = args.max_images
    
    # Setup logging
    setup_logging(config)
    
    # Clear checkpoint if requested
    if args.clear_checkpoint:
        checkpoint_manager = CheckpointManager(f"{args.catalog_path}.checkpoint.json", config)
        checkpoint_manager.clear_checkpoint()
        print("Checkpoint cleared")
    
    # Process the catalog
    print(f"Processing catalog: {args.catalog_path}")
    processor = BatchProcessor(args.catalog_path, config)
    
    # Simulate interruption if requested
    if args.simulate_interruption:
        print("\nSimulating process interruption")
        print("Will stop after processing a few images\n")
        
        # Override the process_batch method to interrupt after a few images
        original_process_batch = processor.process_batch
        
        def interrupted_process_batch(images_batch):
            result = original_process_batch(images_batch)
            print("\nProcess interrupted! (simulated)")
            print("You can restart the script to resume from checkpoint\n")
            sys.exit(0)
            return result
        
        # Replace with our modified version
        processor.process_batch = interrupted_process_batch
    
    # Run the processor
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
    
    return 0


if __name__ == "__main__":
    sys.exit(resuming_example())
