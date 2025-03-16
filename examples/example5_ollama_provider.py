#!/usr/bin/env python3
"""
Example 5: Using a Different AI Provider (Ollama)

This example demonstrates how to use the Ollama local AI provider
instead of the default Claude API provider.
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path

# Add the parent directory to sys.path to import the package
sys.path.insert(0, str(Path(__file__).parent.parent))

from lightroom_ai.config import load_config, AppConfig, OllamaConfig
from lightroom_ai.batch_processor import BatchProcessor
from lightroom_ai.logging_setup import setup_logging


def create_ollama_config(output_path):
    """Create a sample Ollama configuration file."""
    config = {
        "provider": "ollama",
        "ollama_model": "llava",
        "ollama_api_url": "http://localhost:11434/api/generate",
        "max_workers": 1,
        "batch_size": 5,
        "preview_max_resolution": 1024,
        "debug_mode": True,
        "log_level": "DEBUG",
        "use_smart_previews": True,
        "use_checkpoint": True
    }
    
    with open(output_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"Created Ollama configuration file at: {output_path}")


def ollama_provider_example():
    """Ollama provider example."""
    # Setup argument parser
    parser = argparse.ArgumentParser(description="Ollama provider example for Lightroom AI Tool")
    parser.add_argument("--catalog-path", help="Path to Lightroom catalog (.lrcat file)")
    parser.add_argument("--create-config", action="store_true", 
                        help="Create a sample Ollama configuration file")
    parser.add_argument("--config", default="ollama_config.json",
                       help="Path to Ollama configuration file")
    parser.add_argument("--max-images", type=int, default=5, 
                       help="Maximum number of images to process")
    args = parser.parse_args()

    # Create sample config if requested
    if args.create_config:
        config_path = os.path.join(os.getcwd(), "ollama_config.json")
        create_ollama_config(config_path)
        if not args.catalog_path:
            return 0
    
    # Check for required arguments
    if not args.catalog_path:
        print("Error: --catalog-path is required unless using --create-config")
        return 1
    
    # Check if catalog exists
    if not os.path.exists(args.catalog_path):
        print(f"Error: Catalog not found: {args.catalog_path}")
        return 1

    # Check if config exists
    if not os.path.exists(args.config):
        print(f"Error: Configuration file not found: {args.config}")
        if not args.create_config:
            print("Use --create-config to generate a sample configuration")
        return 1

    # Load configuration
    config = load_config(args.config)
    
    # Ensure we're using Ollama provider
    if not hasattr(config.provider, 'provider_type') or config.provider.provider_type != 'ollama':
        print("Warning: Configuration file does not specify Ollama provider")
        print("Creating a new Ollama configuration")
        
        # Create a new config with Ollama provider
        config.provider = OllamaConfig(
            provider_type="ollama",
            api_url="http://localhost:11434/api/generate",
            model="llava"
        )
    
    # Override max images if specified
    if args.max_images:
        config.max_images = args.max_images

    # Setup logging
    setup_logging(config)
    
    print(f"Processing catalog: {args.catalog_path}")
    print(f"Using Ollama model: {config.provider.model}")
    print(f"Ollama API URL: {config.provider.api_url}")
    
    print("\nNote: This example requires a running Ollama server with an image model like llava.")
    print("If not running, start Ollama with: 'ollama run llava'")
    
    # Ask for confirmation
    confirm = input("\nContinue with processing (y/n)? ")
    if confirm.lower() != 'y':
        print("Exiting without processing")
        return 0
    
    # Process the catalog
    processor = BatchProcessor(args.catalog_path, config)
    stats = processor.run()
    
    # Print summary
    print("\nProcessing complete!")
    print(f"Total images: {stats['total_images']}")
    print(f"Successfully processed: {stats['successful_images']}")
    print(f"Failed to process: {stats['failed_images']}")
    
    if 'total_time' in stats:
        print(f"Total time: {stats['total_time']:.1f} seconds")
        print(f"Average time per image: {stats['avg_time_per_image']:.2f} seconds")
    
    return 0


if __name__ == "__main__":
    sys.exit(ollama_provider_example())
