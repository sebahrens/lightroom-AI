#!/usr/bin/env python3
"""
Example demonstrating the use of the KeywordConsolidator to organize
and structure keywords in a Lightroom catalog.
"""

import os
import sys
import logging
from pathlib import Path

# Add the parent directory to the path so we can import the lightroom_ai package
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lightroom_ai.keyword_consolidator import KeywordConsolidator
from lightroom_ai.config import load_config, AppConfig
from lightroom_ai.logging_setup import setup_logging, get_logger

logger = get_logger(__name__)

def keyword_consolidator_example(catalog_path, config_path=None):
    """
    Run the keyword consolidator on a Lightroom catalog.
    
    Args:
        catalog_path: Path to the Lightroom catalog (.lrcat file)
        config_path: Optional path to a configuration file
    """
    # Load configuration
    if config_path and os.path.exists(config_path):
        config = load_config(config_path)
    else:
        # Create a default configuration
        config = AppConfig()
    
    # Set up logging
    setup_logging(config, log_prefix="keyword_example")
    
    logger.info(f"Starting keyword consolidation for catalog: {catalog_path}")
    
    try:
        # Initialize the keyword consolidator
        consolidator = KeywordConsolidator(
            catalog_path=catalog_path,
            config=config
        )
        
        # Connect to the database
        consolidator.connect_to_db()
        logger.info("Connected to Lightroom catalog database")
        
        # Extract all keywords from the catalog
        keywords = consolidator.extract_keywords()
        logger.info(f"Extracted {len(keywords)} keywords from catalog")
        
        # Clean and normalize keywords
        normalized = consolidator.clean_and_normalize_keywords()
        logger.info(f"Normalized keywords: {len(normalized)} unique terms")
        
        # Cluster keywords into related groups
        clusters = consolidator.cluster_keywords()
        logger.info(f"Created {len(clusters)} keyword clusters")
        
        # Create hierarchical keyword structure
        hierarchies = consolidator.create_hierarchical_keywords()
        logger.info(f"Created hierarchical structure with {len(hierarchies)} relationships")
        
        # Update the catalog with the new keyword structure
        updated = consolidator.update_catalog_keywords()
        logger.info(f"Updated {updated} keywords in catalog")
        
        # Run the complete process
        results = consolidator.run()
        logger.info(f"Consolidation complete. Results: {results}")
        
        return results
        
    except Exception as e:
        logger.error(f"Error during keyword consolidation: {str(e)}", exc_info=True)
        return {"error": str(e)}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python example_keyword_consolidator.py <path_to_catalog.lrcat> [path_to_config.json]")
        sys.exit(1)
    
    catalog_path = sys.argv[1]
    config_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    result = keyword_consolidator_example(catalog_path, config_path)
    
    if "error" in result:
        print(f"Error: {result['error']}")
        sys.exit(1)
    else:
        print("\nKeyword Consolidation Summary:")
        print(f"- Total keywords processed: {result.get('total_keywords', 0)}")
        print(f"- Keyword clusters created: {result.get('clusters_created', 0)}")
        print(f"- Hierarchical relationships: {result.get('hierarchies_created', 0)}")
        print(f"- Keywords updated in catalog: {result.get('keywords_updated', 0)}")
