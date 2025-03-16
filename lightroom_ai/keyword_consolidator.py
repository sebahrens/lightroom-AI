"""
Keyword consolidation functionality for Lightroom catalogs.
This module extracts keywords from a Lightroom catalog, clusters them using AI,
and converts them into hierarchical keywords.
"""

import sqlite3
import json
import base64
import re
import uuid
import difflib
from typing import List, Dict, Set, Tuple, Optional, Any
from collections import defaultdict
import logging
import time
from tqdm import tqdm
import concurrent.futures
from threading import Lock

from .config import AppConfig
from .ai_providers import AiProvider
from .utils import get_logger, extract_json

logger = get_logger(__name__)

class KeywordConsolidator:
    """Class to handle keyword consolidation in Lightroom catalogs."""
    
    def __init__(self, catalog_path: str, config: AppConfig, model_override: Optional[str] = None):
        """
        Initialize the KeywordConsolidator.
        
        Args:
            catalog_path: Path to the Lightroom catalog
            config: Application configuration
            model_override: Optional model to override the one in config
        """
        self.catalog_path = catalog_path
        self.config = config
        self.model_override = model_override
        self.ai_provider = AiProvider.get_provider(config)
        
        # Override model if specified
        if model_override and hasattr(self.ai_provider, 'config') and hasattr(self.ai_provider.config, 'model'):
            logger.info(f"Overriding model from {self.ai_provider.config.model} to {model_override}")
            self.ai_provider.config.model = model_override
            
        self.db_conn = None
        self.keywords = set()
        self.cleaned_keywords = {}  # Maps original keywords to cleaned versions
        self.keyword_clusters = {}
        self.keyword_hierarchy = {}
        self.used_keywords = set()  # Track keywords that are actually used in images
        self.drop_all_keywords = False
        
        # For thread safety
        self.lock = Lock()
        
        # Get max_workers from config or default to 1
        self.max_workers = getattr(config, 'max_workers', 1)
        logger.info(f"Initializing KeywordConsolidator with {self.max_workers} workers")
        
    def connect_to_db(self) -> None:
        """Connect to the Lightroom catalog database."""
        try:
            self.db_conn = sqlite3.connect(self.catalog_path)
            self.db_conn.row_factory = sqlite3.Row
            logger.info(f"Connected to catalog database: {self.catalog_path}")
        except sqlite3.Error as e:
            logger.error(f"Failed to connect to catalog database: {e}")
            raise RuntimeError(f"Failed to connect to catalog database: {e}")
    
    def extract_keywords(self) -> Set[str]:
        """
        Extract all keywords from the Lightroom catalog.
        
        Returns:
            Set of unique keywords
        """
        if not self.db_conn:
            self.connect_to_db()
            
        try:
            cursor = self.db_conn.cursor()
            
            # Query to get all keywords from the AgLibraryKeyword table
            cursor.execute("SELECT name FROM AgLibraryKeyword")
            rows = cursor.fetchall()
            
            # Extract keywords and add to set
            for row in rows:
                keyword = row['name']
                if keyword and keyword.strip():
                    self.keywords.add(keyword.strip())
            
            # Also get keywords that are actually used in images
            cursor.execute("""
                SELECT DISTINCT k.name 
                FROM AgLibraryKeyword k
                JOIN AgLibraryKeywordImage ki ON k.id_local = ki.tag
            """)
            
            used_keywords_rows = cursor.fetchall()
            for row in used_keywords_rows:
                keyword = row['name']
                if keyword and keyword.strip():
                    self.used_keywords.add(keyword.strip())
            
            logger.info(f"Extracted {len(self.keywords)} unique keywords from catalog ({len(self.used_keywords)} used in images)")
            return self.keywords
            
        except sqlite3.Error as e:
            logger.error(f"Error extracting keywords: {e}")
            raise RuntimeError(f"Error extracting keywords: {e}")
    
    def clean_and_normalize_keywords(self) -> Dict[str, str]:
        """
        Clean and normalize keywords, collapsing similar terms.
        
        Returns:
            Dictionary mapping original keywords to cleaned versions
        """
        if not self.keywords:
            self.extract_keywords()
            
        logger.info("Cleaning and normalizing keywords...")
        
        # First pass: basic cleaning
        cleaned_keywords = {}
        for keyword in self.keywords:
            cleaned = self._basic_keyword_cleaning(keyword)
            if cleaned:  # Skip empty strings
                cleaned_keywords[keyword] = cleaned
        
        # Get the similarity threshold from config or use default
        similarity_threshold = getattr(self.config, 'keyword_similarity_threshold', 0.92)
        
        # Use LLM for grouping similar keywords
        if hasattr(self.config, 'use_llm_grouping') and self.config.use_llm_grouping:
            logger.info("Using LLM for keyword grouping")
            unique_cleaned = list(set(cleaned_keywords.values()))
            
            # Group similar keywords using LLM
            similarity_groups = self._group_keywords_with_llm(unique_cleaned)
            
            # Create mapping from original to canonical form
            canonical_mapping = {}
            for group in similarity_groups:
                if len(group) > 1:  # Only process groups with multiple keywords
                    canonical = self._select_canonical_keyword(group)
                    for keyword in group:
                        canonical_mapping[keyword] = canonical
            
            # Final mapping from original keywords to canonical forms
            final_mapping = {}
            for original, cleaned in cleaned_keywords.items():
                if cleaned in canonical_mapping:
                    final_mapping[original] = canonical_mapping[cleaned]
                else:
                    final_mapping[original] = cleaned
        else:
            # Use traditional similarity-based grouping
            similarity_groups = self._group_similar_keywords(list(cleaned_keywords.values()), similarity_threshold)
            
            # Create mapping from original to canonical form
            canonical_mapping = {}
            for group in similarity_groups:
                # Use the most common or shortest as canonical
                canonical = self._select_canonical_keyword(group)
                for keyword in group:
                    canonical_mapping[keyword] = canonical
            
            # Final mapping from original keywords to canonical forms
            final_mapping = {}
            for original, cleaned in cleaned_keywords.items():
                if cleaned in canonical_mapping:
                    final_mapping[original] = canonical_mapping[cleaned]
                else:
                    final_mapping[original] = cleaned
        
        # Count how many keywords were collapsed
        unique_cleaned = len(set(final_mapping.values()))
        reduction = len(self.keywords) - unique_cleaned
        
        # Verify we haven't over-consolidated
        if unique_cleaned < 10 and len(self.keywords) > 100:
            logger.warning("Excessive keyword consolidation detected, reverting to basic cleaning only")
            # Revert to just basic cleaning without consolidation
            final_mapping = cleaned_keywords
            unique_cleaned = len(set(final_mapping.values()))
            reduction = len(self.keywords) - unique_cleaned
        
        logger.info(f"Reduced {len(self.keywords)} keywords to {unique_cleaned} normalized terms ({reduction} collapsed)")
        
        self.cleaned_keywords = final_mapping
        return final_mapping
    
    def _basic_keyword_cleaning(self, keyword: str) -> str:
        """
        Perform basic cleaning on a keyword.
        
        Args:
            keyword: Original keyword
            
        Returns:
            Cleaned keyword
        """
        # Convert to lowercase
        cleaned = keyword.lower()
        
        # Remove leading/trailing whitespace and punctuation
        cleaned = cleaned.strip().strip('.,;:!?-_"\'')
        
        # Replace multiple spaces with a single space
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        # Remove special characters except spaces and hyphens
        cleaned = re.sub(r'[^\w\s-]', '', cleaned, flags=re.UNICODE)
        
        # Skip very short words (except common words like "a" and "i")
        if len(cleaned) <= 1 and cleaned not in ['a', 'i']:
            return ""
            
        return cleaned
    
    def _group_similar_keywords(self, keywords: List[str], similarity_threshold: float = 0.92) -> List[List[str]]:
        """
        Group similar keywords together.
        
        Args:
            keywords: List of cleaned keywords
            similarity_threshold: Threshold for considering keywords similar
            
        Returns:
            List of groups of similar keywords
        """
        # Sort keywords by length (shortest first)
        sorted_keywords = sorted(keywords, key=len)
        
        # Initialize groups
        groups = []
        processed = set()
        
        # Process each keyword
        for keyword in sorted_keywords:
            if keyword in processed or not keyword:
                continue
                
            # Skip very short keywords (less than 3 chars) for grouping
            if len(keyword) < 3:
                processed.add(keyword)
                continue
                
            # Start a new group with this keyword
            group = [keyword]
            processed.add(keyword)
            
            # Find similar keywords
            for other in sorted_keywords:
                if other in processed or other == keyword or not other:
                    continue
                    
                # Skip very short keywords for comparison
                if len(other) < 3:
                    continue
                    
                # Check if they're similar
                if self._are_keywords_similar(keyword, other, similarity_threshold):
                    group.append(other)
                    processed.add(other)
            
            # Only add groups with multiple keywords
            if len(group) > 1:
                groups.append(group)
            else:
                # Add single keywords as their own groups
                groups.append([keyword])
        
        # Add any remaining unprocessed keywords as single-item groups
        for keyword in sorted_keywords:
            if keyword not in processed and keyword:
                groups.append([keyword])
                
        return groups
    
    def _group_keywords_with_llm(self, keywords: List[str]) -> List[List[str]]:
        """
        Use LLM to identify groups of semantically similar keywords.
        
        Args:
            keywords: List of keywords to group
            
        Returns:
            List of groups of semantically similar keywords
        """
        # If we have too many keywords, process in batches
        max_batch_size = 200  # Limit to avoid token limits
        
        if len(keywords) > max_batch_size:
            logger.info(f"Processing {len(keywords)} keywords in batches for LLM grouping")
            all_groups = []
            
            # Process keywords in batches using multiple workers
            if self.max_workers > 1:
                batches = [keywords[i:i+max_batch_size] for i in range(0, len(keywords), max_batch_size)]
                logger.info(f"Processing {len(batches)} batches with up to {self.max_workers} workers")
                
                with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                    future_to_batch = {executor.submit(self._process_llm_keyword_batch, batch): batch for batch in batches}
                    
                    for future in concurrent.futures.as_completed(future_to_batch):
                        batch = future_to_batch[future]
                        try:
                            batch_groups = future.result()
                            all_groups.extend(batch_groups)
                        except Exception as e:
                            logger.error(f"Error processing batch: {e}")
                
                return all_groups
            else:
                # Process sequentially if max_workers is 1
                for i in range(0, len(keywords), max_batch_size):
                    batch = keywords[i:i+max_batch_size]
                    batch_groups = self._process_llm_keyword_batch(batch)
                    all_groups.extend(batch_groups)
                    
                return all_groups
        else:
            return self._process_llm_keyword_batch(keywords)
    
    def _process_llm_keyword_batch(self, keywords: List[str]) -> List[List[str]]:
        """
        Process a batch of keywords with the LLM for semantic grouping.
        
        Args:
            keywords: Batch of keywords to process
            
        Returns:
            List of keyword groups identified by the LLM
        """
        # Format the prompt for the LLM
        prompt = f"""
        I have a list of photography keywords that need to be grouped by semantic similarity.
        Group keywords that represent the same concept or are very similar.
        
        For example:
        - "sunset", "sunsets", "setting sun" should be in one group
        - "portrait", "portraiture", "portraits" should be in one group
        - "landscape", "landscapes", "scenic" should be in one group
        
        Here are the keywords:
        {', '.join(keywords)}
        
        Return the groups as a JSON array of arrays. Each inner array should contain similar keywords.
        Format: [["keyword1", "keyword2"], ["keyword3", "keyword4", "keyword5"], ...]
        
        IMPORTANT:
        - Group keywords that mean essentially the same thing
        - Prefer generic terms over specific ones (e.g., "airplane" over "airplane tail")
        - Return ONLY the JSON array with no additional text
        - Make sure to properly close all brackets and format as valid JSON
        - Do not include any explanations or markdown formatting
        """
        
        # Try up to 3 times to get a valid response
        for attempt in range(3):
            try:
                # Create a dummy image since our AI providers expect an image
                dummy_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
                
                # Call the AI provider with the prompt and dummy image
                response = self.ai_provider.analyze_image(dummy_image, user_prompt=prompt)
                
                if response and 'analysis' in response:
                    # Try to extract JSON from the response
                    analysis_text = response['analysis']
                    logger.debug(f"LLM grouping response: {analysis_text[:500]}...")
                    
                    # Use the extract_json utility function
                    json_data = extract_json(analysis_text, logger, self.config.debug_mode if hasattr(self.config, 'debug_mode') else False)
                    
                    if json_data and isinstance(json_data, list):
                        # Filter out empty groups and ensure all groups are lists
                        valid_groups = []
                        for group in json_data:
                            if isinstance(group, list) and len(group) > 0:
                                valid_groups.append(group)
                        
                        if valid_groups:
                            logger.info(f"LLM identified {len(valid_groups)} keyword groups")
                            return valid_groups
                
                # If we get here, either no response or invalid format
                logger.warning(f"LLM grouping attempt {attempt+1} failed, retrying...")
                time.sleep(2)  # Wait before retrying
                
            except Exception as e:
                logger.error(f"Error in LLM keyword grouping (attempt {attempt+1}): {e}")
                time.sleep(2)  # Wait before retrying
        
        # If we get here, LLM grouping failed after all attempts
        logger.warning("LLM keyword grouping failed, falling back to similarity-based grouping")
        return self._group_similar_keywords(keywords)
    
    def _are_keywords_similar(self, keyword1: str, keyword2: str, similarity_threshold: float = 0.92) -> bool:
        """
        Determine if two keywords are semantically similar.
        
        Args:
            keyword1: First keyword
            keyword2: Second keyword
            similarity_threshold: Threshold for considering keywords similar
            
        Returns:
            True if the keywords are similar, False otherwise
        """
        # If the keywords are identical
        if keyword1 == keyword2:
            return True
            
        # If one is a substring of the other, they must be at least 4 chars long
        if len(keyword1) >= 4 and len(keyword2) >= 4:
            if keyword1 in keyword2 or keyword2 in keyword1:
                return True
        
        # Check for plural/singular forms
        if keyword1 + 's' == keyword2 or keyword2 + 's' == keyword1:
            return True
        if keyword1 + 'es' == keyword2 or keyword2 + 'es' == keyword1:
            return True
        if keyword1.endswith('y') and keyword1[:-1] + 'ies' == keyword2:
            return True
        if keyword2.endswith('y') and keyword2[:-1] + 'ies' == keyword1:
            return True
            
        # Check similarity ratio
        similarity = difflib.SequenceMatcher(None, keyword1, keyword2).ratio()
        return similarity >= similarity_threshold
    
    def _select_canonical_keyword(self, group: List[str]) -> str:
        """
        Select the canonical form from a group of similar keywords.
        
        Args:
            group: List of similar keywords
            
        Returns:
            The canonical form
        """
        if not group:
            return ""
            
        # If there's only one keyword, use it
        if len(group) == 1:
            return group[0]
            
        # Count occurrences in the original keywords
        counts = defaultdict(int)
        for original in self.keywords:
            cleaned = self._basic_keyword_cleaning(original)
            if cleaned in group:
                counts[cleaned] += 1
        
        # If we have counts, use the most common
        if counts:
            most_common = max(counts.items(), key=lambda x: x[1])[0]
            return most_common
            
        # Otherwise, prefer shorter keywords (they're usually more generic)
        # but not too short (to avoid unusual terms)
        reasonable_length_keywords = [k for k in group if 3 <= len(k) <= 15]
        if reasonable_length_keywords:
            return min(reasonable_length_keywords, key=len)
            
        # If all else fails, use the shortest one
        return min(group, key=len)
    
    def cluster_keywords(self) -> Dict[str, List[str]]:
        """
        Cluster keywords into categories using AI.
        
        Returns:
            Dictionary mapping category names to lists of keywords
        """
        # First clean and normalize keywords
        if not self.cleaned_keywords:
            self.clean_and_normalize_keywords()
            
        # Use the cleaned keywords for clustering
        unique_cleaned_keywords = list(set(self.cleaned_keywords.values()))
        
        # Check if we have a reasonable number of keywords to cluster
        if len(unique_cleaned_keywords) < 3:
            logger.warning(f"Only {len(unique_cleaned_keywords)} unique keywords after normalization, using fallback clustering")
            return self._fallback_clustering(unique_cleaned_keywords)
            
        logger.info(f"Clustering {len(unique_cleaned_keywords)} normalized keywords using AI...")
        
        # Check if we should use LLM for clustering
        if hasattr(self.config, 'use_llm_clustering') and self.config.use_llm_clustering:
            logger.info("Using LLM for keyword clustering")
            self.keyword_clusters = self._cluster_keywords_with_llm(unique_cleaned_keywords)
            
            # Validate the clusters
            if self._validate_clustering_results(self.keyword_clusters):
                return self.keyword_clusters
            else:
                logger.warning("LLM clustering produced poor results, falling back to traditional clustering")
        
        # If we get here, either LLM clustering is disabled or it failed
        # If we have too many keywords, split them into batches
        max_batch_size = 250  # Reduced from 300 to ensure we stay within token limits
        
        if len(unique_cleaned_keywords) > max_batch_size:
            logger.info(f"Processing {len(unique_cleaned_keywords)} keywords in batches of {max_batch_size}")
            self.keyword_clusters = self._process_keywords_in_batches(unique_cleaned_keywords, max_batch_size)
            return self.keyword_clusters
        else:
            # Process all keywords at once
            prompt = self._get_clustering_prompt(unique_cleaned_keywords)
            self.keyword_clusters = self._process_clustering_prompt(prompt)
            return self.keyword_clusters
    
    def _cluster_keywords_with_llm(self, keywords: List[str]) -> Dict[str, List[str]]:
        """
        Use LLM to cluster keywords into categories.
        
        Args:
            keywords: List of keywords to cluster
            
        Returns:
            Dictionary mapping category names to lists of keywords
        """
        # If we have too many keywords, process in batches
        max_batch_size = 200  # Limit to avoid token limits
        
        if len(keywords) > max_batch_size:
            logger.info(f"Processing {len(keywords)} keywords in batches for LLM clustering")
            combined_clusters = {}
            
            # Process keywords in batches using multiple workers if configured
            if self.max_workers > 1:
                batches = [keywords[i:i+max_batch_size] for i in range(0, len(keywords), max_batch_size)]
                logger.info(f"Processing {len(batches)} batches with up to {self.max_workers} workers")
                
                with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                    future_to_batch = {executor.submit(self._process_llm_clustering_batch, batch): batch for batch in batches}
                    
                    for future in concurrent.futures.as_completed(future_to_batch):
                        batch = future_to_batch[future]
                        try:
                            batch_clusters = future.result()
                            
                            # Merge with combined results
                            with self.lock:
                                for category, words in batch_clusters.items():
                                    if category in combined_clusters:
                                        combined_clusters[category].extend(words)
                                    else:
                                        combined_clusters[category] = words
                        except Exception as e:
                            logger.error(f"Error processing batch: {e}")
            else:
                # Process sequentially if max_workers is 1
                for i in range(0, len(keywords), max_batch_size):
                    batch = keywords[i:i+max_batch_size]
                    logger.info(f"Processing batch {i//max_batch_size + 1} with {len(batch)} keywords")
                    batch_clusters = self._process_llm_clustering_batch(batch)
                    
                    # Merge with combined results
                    for category, words in batch_clusters.items():
                        if category in combined_clusters:
                            combined_clusters[category].extend(words)
                        else:
                            combined_clusters[category] = words
            
            # Remove duplicates in each category
            for category in combined_clusters:
                combined_clusters[category] = list(set(combined_clusters[category]))
            
            logger.info(f"LLM clustering created {len(combined_clusters)} categories")
            return combined_clusters
        else:
            return self._process_llm_clustering_batch(keywords)
    
    def _process_llm_clustering_batch(self, keywords: List[str]) -> Dict[str, List[str]]:
        """
        Process a batch of keywords with the LLM for clustering.
        
        Args:
            keywords: Batch of keywords to process
            
        Returns:
            Dictionary mapping category names to lists of keywords
        """
        # Get categories from config or use default
        categories = self.config.categories if hasattr(self.config, 'categories') and self.config.categories else [
            "Composition", "Lighting", "Subject", "Technique", "Mood", "Color", 
            "Location", "Time", "Event", "People", "Objects", "Style", "Technical"
        ]
        
        # Format the prompt for the LLM
        prompt = f"""
        You are a photography expert tasked with organizing keywords into logical categories.
        
        TASK:
        Analyze these photography keywords and organize them into the provided categories.
        
        KEYWORDS:
        {', '.join(keywords)}
        
        CATEGORIES:
        {', '.join(categories)}
        
        INSTRUCTIONS:
        1. Assign each keyword to the most appropriate category
        2. You may create subcategories within the main categories if needed
        3. Every keyword MUST be assigned to a category - none should be left out
        4. If a keyword doesn't fit any category well, create an "Other" category
        5. Be consistent with your categorization logic
        6. Consolidate similar terms (e.g., "airplane", "aircraft", "plane" should all be represented by one term)
        
        REQUIRED OUTPUT FORMAT:
        Return ONLY a JSON object where:
        - Keys are category names (use only the provided categories plus "Other" if needed)
        - Values are arrays of keywords that belong to that category
        - For subcategories, use the format "MainCategory|Subcategory" as the key
        
        Example:
        {{
          "Composition": ["rule of thirds", "symmetry", "balance"],
          "Composition|Framing": ["frame within frame", "natural frame"],
          "Lighting": ["backlight", "golden hour", "shadow"]
        }}
        
        IMPORTANT:
        - Include EVERY keyword from the provided list
        - Your response must be valid JSON that can be parsed directly
        - Do not include any explanations or text outside the JSON structure
        - Make sure to properly close all brackets and format as valid JSON
        - Do not use markdown formatting or code blocks
        """
        
        # Try up to 3 times to get a valid response
        for attempt in range(3):
            try:
                # Create a dummy image since our AI providers expect an image
                dummy_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
                
                # Call the AI provider with the prompt and dummy image
                response = self.ai_provider.analyze_image(dummy_image, user_prompt=prompt)
                
                if response and 'analysis' in response:
                    # Try to extract JSON from the response
                    analysis_text = response['analysis']
                    logger.debug(f"LLM clustering response: {analysis_text[:500]}...")
                    
                    # Use the extract_json utility function
                    json_data = extract_json(analysis_text, logger, self.config.debug_mode if hasattr(self.config, 'debug_mode') else False)
                    
                    if json_data and isinstance(json_data, dict):
                        # Validate that all values are lists
                        valid_clusters = {}
                        for category, words in json_data.items():
                            if isinstance(words, list) and words:
                                valid_clusters[category] = words
                            elif isinstance(words, str):
                                # Handle case where words might be a comma-separated string
                                valid_clusters[category] = [w.strip() for w in words.split(',') if w.strip()]
                        
                        if valid_clusters:
                            logger.info(f"LLM created {len(valid_clusters)} keyword clusters")
                            return valid_clusters
                
                # If we get here, either no response or invalid format
                logger.warning(f"LLM clustering attempt {attempt+1} failed, retrying...")
                time.sleep(2)  # Wait before retrying
                
            except Exception as e:
                logger.error(f"Error in LLM keyword clustering (attempt {attempt+1}): {e}")
                time.sleep(2)  # Wait before retrying
        
        # If we get here, LLM clustering failed after all attempts
        logger.warning("LLM keyword clustering failed, falling back to traditional clustering")
        return self._fallback_clustering(keywords)
    
    def _process_keywords_in_batches(self, keywords: List[str], batch_size: int) -> Dict[str, List[str]]:
        """
        Process keywords in batches to avoid token limits.
        
        Args:
            keywords: List of all keywords
            batch_size: Maximum number of keywords per batch
            
        Returns:
            Combined clustering results
        """
        combined_clusters = {}
        
        # Split keywords into batches
        batches = [keywords[i:i + batch_size] for i in range(0, len(keywords), batch_size)]
        
        # Process batches in parallel if multiple workers are configured
        if self.max_workers > 1:
            logger.info(f"Processing {len(batches)} batches with up to {self.max_workers} workers")
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Create a function to process a batch and return the results
                def process_batch(batch_idx, batch):
                    logger.info(f"Processing batch {batch_idx+1}/{len(batches)} with {len(batch)} keywords")
                    prompt = self._get_clustering_prompt(batch)
                    return self._process_clustering_prompt(prompt)
                
                # Submit all batches to the executor
                future_to_batch = {executor.submit(process_batch, i, batch): (i, batch) for i, batch in enumerate(batches)}
                
                # Process results as they complete
                for future in concurrent.futures.as_completed(future_to_batch):
                    batch_idx, batch = future_to_batch[future]
                    try:
                        batch_clusters = future.result()
                        
                        # Merge with combined results
                        with self.lock:
                            for category, words in batch_clusters.items():
                                if category in combined_clusters:
                                    combined_clusters[category].extend(words)
                                else:
                                    combined_clusters[category] = words
                    except Exception as e:
                        logger.error(f"Error processing batch {batch_idx+1}: {e}")
        else:
            # Process sequentially if max_workers is 1
            for i, batch in enumerate(batches):
                logger.info(f"Processing batch {i+1}/{len(batches)} with {len(batch)} keywords")
                
                # Process this batch
                prompt = self._get_clustering_prompt(batch)
                batch_clusters = self._process_clustering_prompt(prompt)
                
                # Merge with combined results
                for category, words in batch_clusters.items():
                    if category in combined_clusters:
                        combined_clusters[category].extend(words)
                    else:
                        combined_clusters[category] = words
        
        # Remove duplicates in each category
        for category in combined_clusters:
            combined_clusters[category] = list(set(combined_clusters[category]))
        
        logger.info(f"Combined results: {len(combined_clusters)} categories")
        return combined_clusters
    
    def _process_clustering_prompt(self, prompt: str) -> Dict[str, List[str]]:
        """
        Process a clustering prompt and return the results.
        
        Args:
            prompt: The prompt to send to the AI
            
        Returns:
            Dictionary mapping category names to lists of keywords
        """
        # Try up to 3 times to get a valid response
        for attempt in range(3):
            try:
                # Call the AI provider
                response = self._call_ai_for_clustering(prompt)
                
                if response:
                    clusters = self._parse_clustering_response(response)
                    if self._validate_clustering_results(clusters):
                        logger.info(f"Created {len(clusters)} keyword clusters")
                        return clusters
                
                # If we get here, either no response or invalid format
                logger.warning(f"Clustering attempt {attempt+1} failed, retrying...")
                time.sleep(2)  # Wait before retrying
                
            except Exception as e:
                logger.error(f"Error during keyword clustering (attempt {attempt+1}): {e}")
                time.sleep(2)  # Wait before retrying
        
        # If we get here, AI clustering failed after all attempts
        logger.warning("AI clustering failed, falling back to simple clustering")
        return self._fallback_clustering(list(set(self.cleaned_keywords.values())))
    
    def _validate_clustering_results(self, clusters: Dict[str, List[str]]) -> bool:
        """
        Validate the clustering results to ensure they're usable.
        
        Args:
            clusters: Dictionary mapping category names to lists of keywords
            
        Returns:
            True if the clusters are valid, False otherwise
        """
        if not clusters or len(clusters) <= 1:
            logger.warning("Clustering produced too few categories")
            return False
            
        # Count total keywords in clusters
        all_clustered_keywords = set()
        for keywords in clusters.values():
            all_clustered_keywords.update(keywords)
            
        # Check if we have a reasonable number of keywords
        unique_cleaned_keywords = set(self.cleaned_keywords.values())
        coverage_ratio = len(all_clustered_keywords) / len(unique_cleaned_keywords) if unique_cleaned_keywords else 0
        if coverage_ratio < 0.7:  # Increased from 0.5 to 0.7 for better coverage
            logger.warning(f"Clustering only covered {coverage_ratio:.2f} of keywords")
            return False
            
        # Check if any category has too many keywords (potential dumping ground)
        max_category_size = max(len(keywords) for keywords in clusters.values())
        if max_category_size > len(unique_cleaned_keywords) * 0.5:
            logger.warning("One category contains too many keywords")
            return False
            
        return True
    
    def _fallback_clustering(self, keywords: List[str]) -> Dict[str, List[str]]:
        """
        Fallback method for clustering when AI fails.
        Uses simple heuristics to categorize keywords.
        
        Args:
            keywords: List of keywords to categorize
            
        Returns:
            Dictionary mapping category names to lists of keywords
        """
        # Define common categories and patterns with expanded keyword lists
        categories = {
            "People": [
                "person", "people", "man", "woman", "child", "family", "portrait", "face", 
                "boy", "girl", "baby", "adult", "teen", "senior", "crowd", "group", "couple",
                "wedding", "bride", "groom", "model", "self-portrait", "selfie"
            ],
            "Location": [
                "city", "town", "country", "mountain", "beach", "landscape", "urban", "rural", "street",
                "park", "forest", "ocean", "sea", "lake", "river", "desert", "jungle", "waterfall",
                "building", "architecture", "home", "house", "apartment", "indoor", "outdoor", "garden",
                "field", "farm", "village", "downtown", "suburb", "highway", "road", "path", "trail"
            ],
            "Time": [
                "morning", "evening", "night", "sunset", "sunrise", "dusk", "dawn", "day",
                "afternoon", "noon", "midnight", "twilight", "hour", "minute", "second",
                "winter", "summer", "spring", "fall", "autumn", "season", "holiday", "vacation",
                "weekend", "weekday", "year", "month", "week", "date", "birthday", "anniversary"
            ],
            "Color": [
                "red", "blue", "green", "yellow", "black", "white", "orange", "purple", "pink", "color",
                "brown", "gray", "grey", "silver", "gold", "bronze", "copper", "turquoise", "teal",
                "magenta", "cyan", "indigo", "violet", "maroon", "navy", "olive", "lime", "aqua",
                "pastel", "neon", "bright", "dark", "light", "saturated", "desaturated", "monochrome",
                "colorful", "vibrant", "muted", "tone", "hue", "shade", "tint"
            ],
            "Composition": [
                "composition", "frame", "rule of thirds", "symmetry", "pattern", "texture", "depth",
                "foreground", "background", "middle ground", "leading lines", "diagonal", "horizontal",
                "vertical", "perspective", "angle", "viewpoint", "wide", "narrow", "panorama", "square",
                "rectangle", "crop", "aspect ratio", "golden ratio", "balance", "negative space",
                "minimalist", "busy", "simple", "complex", "layered", "flat", "geometric"
            ],
            "Lighting": [
                "light", "shadow", "contrast", "bright", "dark", "silhouette", "backlight",
                "highlight", "lowlight", "rim light", "key light", "fill light", "natural light",
                "artificial light", "flash", "strobe", "soft light", "hard light", "diffused",
                "reflection", "refraction", "specular", "ambient", "mood lighting", "dramatic",
                "high key", "low key", "exposure", "overexposed", "underexposed", "glow", "beam"
            ],
            "Technique": [
                "long exposure", "macro", "bokeh", "hdr", "panorama", "focus", "depth of field",
                "shallow depth of field", "deep depth of field", "selective focus", "tilt-shift",
                "zoom", "telephoto", "wide angle", "fisheye", "prime lens", "zoom lens", "filter",
                "black and white", "monochrome", "sepia", "vintage", "retro", "film", "digital",
                "raw", "jpeg", "composite", "double exposure", "multiple exposure", "time-lapse",
                "slow motion", "high speed", "panning", "handheld", "tripod", "stabilized"
            ],
            "Subject": [
                "animal", "nature", "architecture", "food", "plant", "flower", "tree", "building",
                "wildlife", "pet", "dog", "cat", "bird", "fish", "insect", "reptile", "mammal",
                "landscape", "seascape", "cityscape", "still life", "product", "vehicle", "car",
                "boat", "plane", "train", "bicycle", "motorcycle", "sports", "action", "event",
                "concert", "performance", "art", "sculpture", "painting", "graffiti", "street art"
            ],
            "Mood": [
                "happy", "sad", "dramatic", "peaceful", "moody", "calm", "energetic", "emotional",
                "joyful", "melancholic", "nostalgic", "romantic", "mysterious", "eerie", "scary",
                "tense", "relaxed", "serene", "chaotic", "orderly", "playful", "serious", "formal",
                "casual", "intimate", "distant", "warm", "cool", "harsh", "soft", "dreamy", "surreal",
                "realistic", "fantasy", "whimsical", "somber", "uplifting", "inspiring", "depressing"
            ],
            "Style": [
                "vintage", "modern", "minimalist", "abstract", "documentary", "fine art", "commercial",
                "photojournalism", "fashion", "portrait", "landscape", "street", "architectural",
                "product", "food", "travel", "sports", "wildlife", "macro", "night", "long exposure",
                "black and white", "color", "HDR", "panoramic", "aerial", "underwater", "infrared",
                "tilt-shift", "lomography", "polaroid", "instant", "film", "digital", "smartphone"
            ],
            "Technical": [
                "aperture", "shutter speed", "iso", "exposure", "white balance", "focus", "blur",
                "sharp", "soft", "noise", "grain", "resolution", "megapixel", "raw", "jpeg", "tiff",
                "compression", "bit depth", "dynamic range", "histogram", "clipping", "bracketing",
                "metering", "spot metering", "matrix metering", "center-weighted", "manual", "auto",
                "program", "priority", "bulb", "continuous", "single shot", "burst", "timer", "remote"
            ]
        }
        
        # Initialize result dictionary
        result = {category: [] for category in categories}
        result["Uncategorized"] = []
        
        # Categorize each keyword
        for keyword in keywords:
            keyword_lower = keyword.lower()
            assigned = False
            
            # Check each category
            for category, patterns in categories.items():
                # First check for exact matches or contains
                for pattern in patterns:
                    if pattern == keyword_lower or pattern in keyword_lower or keyword_lower in pattern:
                        result[category].append(keyword)
                        assigned = True
                        break
                        
                # If not assigned, try word stemming/partial matching
                if not assigned:
                    for pattern in patterns:
                        # Check if the first 4+ characters match (simple stemming)
                        if len(pattern) >= 4 and len(keyword_lower) >= 4:
                            if pattern[:4] == keyword_lower[:4]:
                                result[category].append(keyword)
                                assigned = True
                                break
                
                if assigned:
                    break
            
            # If not assigned to any category, put in Uncategorized
            if not assigned:
                result["Uncategorized"].append(keyword)
        
        # Remove empty categories
        result = {k: v for k, v in result.items() if v}
        
        # If we have no categories at all, create some basic ones
        if not result:
            # Create alphabetical categories
            for keyword in keywords:
                first_char = keyword[0].upper() if keyword else "?"
                category = f"Keywords {first_char}"
                if category not in result:
                    result[category] = []
                result[category].append(keyword)
        
        # If Uncategorized has too many keywords, try to distribute them further
        if "Uncategorized" in result and len(result["Uncategorized"]) > len(keywords) * 0.3:
            logger.info("Too many uncategorized keywords, attempting further distribution")
            uncategorized = result["Uncategorized"]
            result["Uncategorized"] = []
            
            # Create subcategories based on first letter
            alpha_categories = {}
            for keyword in uncategorized:
                first_char = keyword[0].upper() if keyword else "?"
                if first_char not in alpha_categories:
                    alpha_categories[first_char] = []
                alpha_categories[first_char].append(keyword)
            
            # Add alpha categories to result
            for char, words in alpha_categories.items():
                if len(words) > 0:
                    result[f"Other {char}"] = words
        
        logger.info(f"Created {len(result)} keyword clusters using fallback method")
        return result
    
    def _get_clustering_prompt(self, keywords: List[str]) -> str:
        """
        Generate a prompt for the AI to cluster keywords.
        
        Args:
            keywords: List of keywords to cluster
            
        Returns:
            Prompt string for the AI
        """
        categories = self.config.categories if hasattr(self.config, 'categories') and self.config.categories else [
            "Composition", "Lighting", "Subject", "Technique", "Mood", "Color", 
            "Location", "Time", "Event", "People", "Objects", "Style", "Technical"
        ]
        
        # Sort keywords alphabetically for better processing
        sorted_keywords = sorted(keywords)
        
        prompt = f"""
        You are a photography expert tasked with organizing keywords into a logical hierarchy.
        
        TASK:
        Analyze these photography keywords and organize them into categories and subcategories.
        
        KEYWORDS:
        {', '.join(sorted_keywords)}
        
        INSTRUCTIONS:
        1. Assign EVERY keyword to one of these main categories: {', '.join(categories)}
        2. Create appropriate subcategories as needed
        3. Every keyword MUST be assigned to a category - none should be left out
        4. If a keyword doesn't fit any category well, use your best judgment
        5. Distribute keywords evenly - don't put too many in one category
        6. Be consistent with your categorization logic
        7. Consolidate similar terms (e.g., "airplane", "aircraft", "plane" should all be represented by one term)
        
        REQUIRED OUTPUT FORMAT:
        Return ONLY a JSON object with this structure:
        {{
            "Category1": {{
                "keywords": ["keyword1", "keyword2"],
                "subcategories": {{
                    "Subcategory1": {{
                        "keywords": ["keyword3", "keyword4"]
                    }}
                }}
            }},
            "Category2": {{
                "keywords": ["keyword5", "keyword6"]
            }}
        }}
        
        IMPORTANT:
        - Include EVERY keyword from the provided list
        - Use ONLY the main categories listed above
        - Your response must be valid JSON that can be parsed directly
        - Do not include any explanations or text outside the JSON structure
        - Ensure no keyword appears in multiple categories
        - Make sure all JSON keys and values are properly quoted
        - Make sure to properly close all brackets and format as valid JSON
        - Do not use markdown formatting or code blocks
        """
        
        return prompt
    
    def _call_ai_for_clustering(self, prompt: str) -> Optional[Dict[str, Any]]:
        """
        Call the AI provider to cluster keywords.
        
        Args:
            prompt: Prompt for the AI
            
        Returns:
            AI response as a dictionary
        """
        try:
            # Create a dummy image since our AI providers expect an image
            # This is a 1x1 transparent pixel encoded as base64
            dummy_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
            
            # Call the AI provider with the prompt and dummy image
            response = self.ai_provider.analyze_image(dummy_image, user_prompt=prompt)
            
            # Extract the JSON response from the AI
            if response and 'analysis' in response:
                # Try to find JSON in the response
                analysis_text = response['analysis']
                logger.debug(f"AI response: {analysis_text[:500]}...")
                
                # Use the extract_json utility function
                json_data = extract_json(analysis_text, logger, self.config.debug_mode if hasattr(self.config, 'debug_mode') else False)
                if json_data:
                    return json_data
                
                # If extract_json fails, try manual extraction
                try:
                    # Try to parse directly if it's already JSON
                    return json.loads(analysis_text)
                except json.JSONDecodeError:
                    # Try to extract JSON from text
                    json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', analysis_text, re.DOTALL)
                    if json_match:
                        try:
                            return json.loads(json_match.group(1))
                        except json.JSONDecodeError:
                            logger.error("Failed to parse JSON from AI response")
                    else:
                        # Try to find JSON with curly braces
                        start = analysis_text.find("{")
                        end = analysis_text.rfind("}")
                        if start != -1 and end != -1 and end > start:
                            try:
                                return json.loads(analysis_text[start:end+1])
                            except json.JSONDecodeError:
                                logger.error("Failed to parse JSON from AI response")
                        else:
                            logger.error("No JSON found in AI response")
            
            # If we have structured_data in the response, try to use that
            if response and 'structured_data' in response:
                return response['structured_data']
                
            return None
        except Exception as e:
            logger.error(f"Error calling AI for clustering: {e}")
            return None
    
    def _parse_clustering_response(self, response: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Parse the AI response to extract keyword clusters.
        
        Args:
            response: AI response as a dictionary
            
        Returns:
            Dictionary mapping category names to lists of keywords
        """
        clusters = {}
        
        # Try up to 3 times to parse the response
        for attempt in range(3):
            try:
                # Handle different possible response formats
                if not response:
                    return {}
                    
                # Check if response is already in the simple format we want
                if all(isinstance(v, list) for v in response.values()):
                    return response
                    
                # Extract analysis text if present
                analysis_text = response.get('analysis', '')
                if analysis_text:
                    # Try to extract JSON from the text
                    json_data = extract_json(analysis_text, logger, self.config.debug_mode if hasattr(self.config, 'debug_mode') else False)
                    if json_data and isinstance(json_data, dict):
                        response = json_data
                
                # Process each top-level category
                for category, data in response.items():
                    # Skip non-dictionary values
                    if not isinstance(data, dict):
                        if isinstance(data, list):
                            clusters[category] = data
                        continue
                        
                    # Initialize category
                    if category not in clusters:
                        clusters[category] = []
                        
                    # Add direct keywords
                    if 'keywords' in data and isinstance(data['keywords'], list):
                        clusters[category].extend(data['keywords'])
                        
                    # Process subcategories
                    if 'subcategories' in data and isinstance(data['subcategories'], dict):
                        for subcategory, subdata in data['subcategories'].items():
                            full_category = f"{category}{self.config.keyword_delimiter if hasattr(self.config, 'keyword_delimiter') else '|'}{subcategory}"
                            clusters[full_category] = []
                            
                            if isinstance(subdata, dict) and 'keywords' in subdata and isinstance(subdata['keywords'], list):
                                clusters[full_category].extend(subdata['keywords'])
                            elif isinstance(subdata, list):
                                clusters[full_category].extend(subdata)
                
                # If we still have no clusters, try to interpret the response differently
                if not clusters:
                    # Try to handle a flat list of categories with keywords
                    for category, value in response.items():
                        if isinstance(value, list):
                            clusters[category] = value
                        elif isinstance(value, str):
                            # Handle case where keywords are comma-separated strings
                            clusters[category] = [k.strip() for k in value.split(',') if k.strip()]
                
                # If we have clusters, return them
                if clusters:
                    return clusters
                
                # If we get here, parsing failed
                logger.warning(f"Failed to parse clustering response (attempt {attempt+1})")
                time.sleep(1)  # Wait before retrying
                
            except Exception as e:
                logger.error(f"Error parsing clustering response (attempt {attempt+1}): {e}")
                time.sleep(1)  # Wait before retrying
        
        # If we get here, all parsing attempts failed
        logger.error("Failed to parse clustering response after multiple attempts")
        return {}
    
    def create_hierarchical_keywords(self) -> Dict[str, str]:
        """
        Create hierarchical keywords mapping.
        
        Returns:
            Dictionary mapping original keywords to hierarchical keywords
        """
        # First clean and normalize keywords if not already done
        if not self.cleaned_keywords:
            self.clean_and_normalize_keywords()
            
        # Then cluster if not already done
        if not self.keyword_clusters:
            self.cluster_keywords()
            
        # Create mapping from normalized keyword to hierarchical path
        normalized_to_hierarchy = {}
        
        # Default delimiter if not specified in config
        delimiter = self.config.keyword_delimiter if hasattr(self.config, 'keyword_delimiter') else '|'
        
        for category, keywords in self.keyword_clusters.items():
            for keyword in keywords:
                normalized_to_hierarchy[keyword] = f"{category}{delimiter}{keyword}"
        
        # Check if any normalized keywords were not assigned to categories
        unassigned_keywords = set(self.cleaned_keywords.values()) - set(normalized_to_hierarchy.keys())
        if unassigned_keywords:
            logger.warning(f"{len(unassigned_keywords)} normalized keywords were not assigned to categories")
            # Assign unassigned keywords to an "Uncategorized" category
            for keyword in unassigned_keywords:
                normalized_to_hierarchy[keyword] = f"Uncategorized{delimiter}{keyword}"
        
        # Map original keywords to hierarchical paths through normalized keywords
        keyword_to_hierarchy = {}
        for original, normalized in self.cleaned_keywords.items():
            if normalized in normalized_to_hierarchy:
                keyword_to_hierarchy[original] = normalized_to_hierarchy[normalized]
            else:
                # This should not happen, but just in case
                keyword_to_hierarchy[original] = f"Uncategorized{delimiter}{original}"
        
        self.keyword_hierarchy = keyword_to_hierarchy
        logger.info(f"Created hierarchical mapping for {len(keyword_to_hierarchy)} keywords")
        return keyword_to_hierarchy
    
    def _generate_global_id(self) -> str:
        """
        Generate a unique global ID for Lightroom database.
        
        Returns:
            A string representation of a UUID
        """
        return str(uuid.uuid4()).upper()
    
    def update_catalog_keywords(self) -> int:
        """
        Update the Lightroom catalog with hierarchical keywords.
        
        Returns:
            Number of keywords updated
        """
        if not self.keyword_hierarchy:
            self.create_hierarchical_keywords()
            
        if not self.db_conn:
            self.connect_to_db()
            
        try:
            cursor = self.db_conn.cursor()
            updated_count = 0
            
            # Start a transaction
            self.db_conn.execute("BEGIN TRANSACTION")
            
            # If drop_all_keywords is set, delete all existing keywords
            if self.drop_all_keywords:
                logger.warning("Dropping all existing keywords from catalog")
                cursor.execute("DELETE FROM AgLibraryKeywordImage")
                cursor.execute("DELETE FROM AgLibraryKeyword")
                
            # First, check if the AgLibraryKeywordTree table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='AgLibraryKeywordTree'")
            keyword_tree_exists = cursor.fetchone() is not None
            
            # Get existing keywords
            cursor.execute("SELECT id_local, id_global, name FROM AgLibraryKeyword")
            existing_keywords = {row['name']: {'id': row['id_local'], 'global_id': row['id_global']} for row in cursor.fetchall()}
            
            # Create new hierarchical keywords if they don't exist
            new_keywords = set()
            delimiter = self.config.keyword_delimiter if hasattr(self.config, 'keyword_delimiter') else '|'
            
            for hierarchical_path in self.keyword_hierarchy.values():
                parts = hierarchical_path.split(delimiter)
                for i in range(len(parts)):
                    partial_path = delimiter.join(parts[:i+1])
                    if partial_path not in existing_keywords:
                        new_keywords.add(partial_path)
            
            # Add new keywords to the catalog
            for keyword in new_keywords:
                # Generate a unique global ID for the new keyword
                global_id = self._generate_global_id()
                
                cursor.execute(
                    "INSERT INTO AgLibraryKeyword (id_global, name, dateCreated) VALUES (?, ?, datetime('now'))",
                    (global_id, keyword)
                )
                keyword_id = cursor.lastrowid
                existing_keywords[keyword] = {'id': keyword_id, 'global_id': global_id}
                
                # Also add to keyword tree if the table exists
                if keyword_tree_exists:
                    cursor.execute(
                        "INSERT INTO AgLibraryKeywordTree (keywordID, lc_name) VALUES (?, ?)",
                        (keyword_id, keyword.lower())
                    )
            
            # Check if the relationship table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='AgLibraryKeywordTreeRelation'")
            relation_table_exists = cursor.fetchone() is not None
            
            # Update keyword relationships if the table exists
            if relation_table_exists:
                for hierarchical_path in self.keyword_hierarchy.values():
                    parts = hierarchical_path.split(delimiter)
                    for i in range(1, len(parts)):
                        parent = delimiter.join(parts[:i])
                        child = delimiter.join(parts[:i+1])
                        
                        if parent in existing_keywords and child in existing_keywords:
                            parent_id = existing_keywords[parent]['id']
                            child_id = existing_keywords[child]['id']
                            
                            # Check if relationship already exists
                            cursor.execute(
                                "SELECT COUNT(*) FROM AgLibraryKeywordTreeRelation WHERE keywordID = ? AND parentID = ?",
                                (child_id, parent_id)
                            )
                            if cursor.fetchone()[0] == 0:
                                cursor.execute(
                                    "INSERT INTO AgLibraryKeywordTreeRelation (keywordID, parentID) VALUES (?, ?)",
                                    (child_id, parent_id)
                                )
                                updated_count += 1
            else:
                # If the relationship table doesn't exist, update the parent field in AgLibraryKeyword
                for hierarchical_path in self.keyword_hierarchy.values():
                    parts = hierarchical_path.split(delimiter)
                    for i in range(1, len(parts)):
                        parent = delimiter.join(parts[:i])
                        child = delimiter.join(parts[:i+1])
                        
                        if parent in existing_keywords and child in existing_keywords:
                            parent_id = existing_keywords[parent]['id']
                            child_id = existing_keywords[child]['id']
                            
                            # Update the parent field
                            cursor.execute(
                                "UPDATE AgLibraryKeyword SET parent = ? WHERE id_local = ?",
                                (parent_id, child_id)
                            )
                            updated_count += 1
            
            # Purge unused keywords if configured to do so
            if hasattr(self.config, 'purge_unused_keywords') and self.config.purge_unused_keywords:
                purged_count = self._purge_unused_keywords(cursor, existing_keywords)
                logger.info(f"Purged {purged_count} unused keywords from catalog")
            
            # Commit the transaction
            self.db_conn.commit()
            logger.info(f"Updated {updated_count} keyword relationships in catalog")
            return updated_count
            
        except sqlite3.Error as e:
            # Rollback in case of error
            self.db_conn.rollback()
            logger.error(f"Error updating catalog keywords: {e}")
            raise RuntimeError(f"Error updating catalog keywords: {e}")
    
    def _purge_unused_keywords(self, cursor: sqlite3.Cursor, existing_keywords: Dict[str, Dict[str, Any]]) -> int:
        """
        Purge unused keywords from the catalog.
        
        Args:
            cursor: Database cursor
            existing_keywords: Dictionary of existing keywords
            
        Returns:
            Number of keywords purged
        """
        try:
            # Get all keywords that are actually used in images
            cursor.execute("""
                SELECT DISTINCT k.id_local 
                FROM AgLibraryKeyword k
                JOIN AgLibraryKeywordImage ki ON k.id_local = ki.tag
            """)
            
            used_keyword_ids = {row[0] for row in cursor.fetchall()}
            
            # Get all keywords that are part of our hierarchy
            hierarchy_keywords = set()
            delimiter = self.config.keyword_delimiter if hasattr(self.config, 'keyword_delimiter') else '|'
            
            for hierarchical_path in self.keyword_hierarchy.values():
                parts = hierarchical_path.split(delimiter)
                for i in range(len(parts)):
                    partial_path = delimiter.join(parts[:i+1])
                    if partial_path in existing_keywords:
                        hierarchy_keywords.add(existing_keywords[partial_path]['id'])
            
            # Get all keywords
            cursor.execute("SELECT id_local FROM AgLibraryKeyword")
            all_keyword_ids = {row[0] for row in cursor.fetchall()}
            
            # Find keywords to purge: not used in images and not part of our hierarchy
            keywords_to_purge = all_keyword_ids - used_keyword_ids - hierarchy_keywords
            
            # Check if the relationship table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='AgLibraryKeywordTreeRelation'")
            relation_table_exists = cursor.fetchone() is not None
            
            # Delete from relationship table first if it exists
            if relation_table_exists:
                for keyword_id in keywords_to_purge:
                    cursor.execute(
                        "DELETE FROM AgLibraryKeywordTreeRelation WHERE keywordID = ? OR parentID = ?",
                        (keyword_id, keyword_id)
                    )
            
            # Delete from keyword tree if it exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='AgLibraryKeywordTree'")
            keyword_tree_exists = cursor.fetchone() is not None
            
            if keyword_tree_exists:
                for keyword_id in keywords_to_purge:
                    cursor.execute(
                        "DELETE FROM AgLibraryKeywordTree WHERE keywordID = ?",
                        (keyword_id,)
                    )
            
            # Finally delete the keywords themselves
            for keyword_id in keywords_to_purge:
                cursor.execute(
                    "DELETE FROM AgLibraryKeyword WHERE id_local = ?",
                    (keyword_id,)
                )
            
            return len(keywords_to_purge)
            
        except sqlite3.Error as e:
            logger.error(f"Error purging unused keywords: {e}")
            return 0
    
    def run(self) -> Dict[str, Any]:
        """
        Run the full keyword consolidation process.
        
        Returns:
            Dictionary with results
        """
        try:
            logger.info(f"Starting keyword consolidation process with {self.max_workers} workers")
            
            # Extract keywords
            start_keyword_count = len(self.extract_keywords())
            
            # Clean and normalize keywords
            cleaned_count = len(set(self.clean_and_normalize_keywords().values()))
            
            # Try LLM-based grouping first
            if hasattr(self.config, 'use_llm_grouping') and self.config.use_llm_grouping:
                logger.info("Using LLM-based keyword grouping")
                unique_keywords = list(set(self.cleaned_keywords.values()))
                similarity_groups = self._group_keywords_with_llm(unique_keywords)
                
                # If LLM grouping succeeded, use these groups for canonical mapping
                if similarity_groups:
                    canonical_mapping = {}
                    for group in similarity_groups:
                        if len(group) > 1:  # Only process groups with multiple keywords
                            canonical = self._select_canonical_keyword(group)
                            for keyword in group:
                                canonical_mapping[keyword] = canonical
                    
                    # Update cleaned_keywords with the new canonical forms
                    for original, cleaned in self.cleaned_keywords.items():
                        if cleaned in canonical_mapping:
                            self.cleaned_keywords[original] = canonical_mapping[cleaned]
                    
                    # Update cleaned_count
                    cleaned_count = len(set(self.cleaned_keywords.values()))
                    logger.info(f"LLM grouping reduced keywords to {cleaned_count} normalized terms")
            
            # Cluster keywords
            cluster_count = len(self.cluster_keywords())
            
            # Create hierarchical keywords
            hierarchy_count = len(self.create_hierarchical_keywords())
            
            # Update catalog
            update_count = self.update_catalog_keywords()
            
            # Close database connection
            if self.db_conn:
                self.db_conn.close()
                
            results = {
                "original_keyword_count": start_keyword_count,
                "normalized_keyword_count": cleaned_count,
                "cluster_count": cluster_count,
                "hierarchical_keyword_count": hierarchy_count,
                "updated_relationships": update_count,
                "success": True
            }
            
            logger.info("Keyword consolidation completed successfully")
            return results
            
        except Exception as e:
            logger.error(f"Keyword consolidation failed: {e}")
            if self.db_conn:
                self.db_conn.close()
            return {
                "success": False,
                "error": str(e)
            }
