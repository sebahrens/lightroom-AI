#!/usr/bin/env python3
"""
Command-line script to consolidate keywords in a Lightroom catalog.
"""

import os
import sys
import argparse
import json
import logging
from typing import Dict, Any

from .config import load_config
from .keyword_consolidator import KeywordConsolidator
from .utils import get_logger, setup_logging

logger = get_logger(__name__)

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Consolidate keywords in a Lightroom catalog")
    
    parser.add_argument("catalog_path", help="Path to the Lightroom catalog file (.lrcat)")
    parser.add_argument("-c", "--config", default="config.json", help="Path to configuration file")
    parser.add_argument("-m", "--model", help="Override AI model specified in config")
    parser.add_argument("-w", "--workers", type=int, help="Override number of worker threads")
    parser.add_argument("--dry-run", action="store_true", help="Analyze keywords but don't update catalog")
    parser.add_argument("--output", help="Path to save analysis results as JSON")
    parser.add_argument("--log-file", help="Path to log file")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], default="INFO", 
                        help="Logging level")
    parser.add_argument("--drop-all", action="store_true", help="Drop all existing keywords before adding new ones")
    parser.add_argument("--similarity", type=float, help="Set similarity threshold for keyword grouping (0.0-1.0)")
    
    return parser.parse_args()

def main():
    """Main entry point for the keyword consolidation script."""
    args = parse_args()
    
    # Validate catalog path
    if not os.path.exists(args.catalog_path):
        print(f"Error: Catalog file not found: {args.catalog_path}")
        return 1
    
    if not args.catalog_path.endswith('.lrcat'):
        print(f"Warning: Catalog file does not have .lrcat extension: {args.catalog_path}")
    
    # Load configuration
    try:
        config = load_config(args.config)
        
        # Override config with command-line arguments
        if args.log_file:
            config.log_file = args.log_file
        
        config.log_level = args.log_level
        config.keyword_consolidation = True
        
        # Override model if specified
        if args.model:
            logger.info(f"Overriding model with: {args.model}")
            if hasattr(config, 'claude_config') and config.provider == "claude":
                config.claude_config.model = args.model
            elif hasattr(config, 'openrouter_config') and config.provider == "openrouter":
                config.openrouter_config.model = args.model
            elif hasattr(config, 'ollama_config') and config.provider == "ollama":
                config.ollama_config.model = args.model
        
        # Override number of workers if specified
        if args.workers is not None:
            logger.info(f"Overriding max_workers with: {args.workers}")
            config.max_workers = args.workers
            
        # Override similarity threshold if specified
        if args.similarity is not None:
            logger.info(f"Setting keyword similarity threshold to: {args.similarity}")
            config.keyword_similarity_threshold = args.similarity
        
    except Exception as e:
        print(f"Error loading configuration: {e}")
        return 1
    
    # Setup logging
    setup_logging(config)
    
    logger.info(f"Starting keyword consolidation for catalog: {args.catalog_path}")
    if args.model:
        logger.info(f"Using model override: {args.model}")
    if args.workers is not None:
        logger.info(f"Using worker override: {args.workers}")
    
    try:
        # Create keyword consolidator
        consolidator = KeywordConsolidator(args.catalog_path, config, model_override=args.model)
        
        # Set drop-all flag if specified
        if args.drop_all:
            consolidator.drop_all_keywords = True
            logger.info("Will drop all existing keywords before adding new ones")
        
        if args.dry_run:
            # Just extract and analyze keywords without updating catalog
            keywords = consolidator.extract_keywords()
            clusters = consolidator.cluster_keywords()
            hierarchy = consolidator.create_hierarchical_keywords()
            
            results = {
                "original_keyword_count": len(keywords),
                "cluster_count": len(clusters),
                "hierarchical_keyword_count": len(hierarchy),
                "keywords": list(keywords),
                "clusters": clusters,
                "hierarchy": hierarchy,
                "dry_run": True
            }
            
            logger.info(f"Dry run completed. Found {len(keywords)} keywords, created {len(clusters)} clusters.")
        else:
            # Run full consolidation
            results = consolidator.run()
            
            if results["success"]:
                logger.info(f"Keyword consolidation completed successfully.")
                logger.info(f"Original keywords: {results['original_keyword_count']}")
                logger.info(f"Clusters created: {results['cluster_count']}")
                logger.info(f"Hierarchical keywords: {results['hierarchical_keyword_count']}")
                logger.info(f"Relationships updated: {results['updated_relationships']}")
            else:
                logger.error(f"Keyword consolidation failed: {results.get('error', 'Unknown error')}")
                return 1
        
        # Save results to file if requested
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)
            logger.info(f"Results saved to {args.output}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error during keyword consolidation: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
