"""
File system operations for previews.
"""

import os
import hashlib
import logging
from typing import List, Dict, Any, Optional, Tuple
from functools import lru_cache

from .config import AppConfig
from .logging_setup import get_logger
from .utils import get_preview_resolution_rank  # Import the utility function

logger = get_logger(__name__)


class FilesystemHelper:
    """Helper class for file system operations."""
    
    def __init__(self, catalog_path: str, config: AppConfig):
        """
        Initialize the filesystem helper.
        
        Args:
            catalog_path: Path to the Lightroom catalog file
            config: Application configuration
        """
        self.catalog_path = catalog_path
        self.config = config
        
        # Determine the location of the Previews.lrdata and Smart Previews.lrdata folders
        catalog_dir = os.path.dirname(catalog_path)
        catalog_name = os.path.splitext(os.path.basename(catalog_path))[0]
        
        self.previews_dir = os.path.join(catalog_dir, f"{catalog_name} Previews.lrdata")
        self.smart_previews_dir = os.path.join(catalog_dir, f"{catalog_name} Smart Previews.lrdata")
        
        # Check if directories exist
        self.has_previews_dir = os.path.exists(self.previews_dir)
        self.has_smart_previews_dir = os.path.exists(self.smart_previews_dir)
        
        if self.has_previews_dir:
            self.build_preview_index()
            
        if not self.has_previews_dir and not self.has_smart_previews_dir:
            logger.warning("Neither standard previews nor smart previews directory found")

    def build_preview_index(self):
        """
        Build an in-memory map of preview filenames to file paths.
        """
        from collections import defaultdict
        self.preview_index = defaultdict(list)

        if not os.path.exists(self.previews_dir):
            logger.info("Previews directory does not exist; no index built.")
            return

        # Use a more efficient approach for large directories
        for root, dirs, files in os.walk(self.previews_dir):
            for f in files:
                if f.endswith('.db'):
                    continue
                name_lower = f.lower()
                full_path = os.path.join(root, f)
                self.preview_index[name_lower].append(full_path)

        logger.info(f"Built preview index with {len(self.preview_index)} unique filenames.")
            
    def get_catalog_info(self) -> Dict[str, Any]:
        """
        Get information about the catalog and preview directories.
        
        Returns:
            Dictionary with catalog information
        """
        return {
            'catalog_path': self.catalog_path,
            'catalog_dir': os.path.dirname(self.catalog_path),
            'catalog_name': os.path.splitext(os.path.basename(self.catalog_path))[0],
            'previews_dir': self.previews_dir,
            'smart_previews_dir': self.smart_previews_dir,
            'has_previews_dir': self.has_previews_dir,
            'has_smart_previews_dir': self.has_smart_previews_dir
        }
    
    @lru_cache(maxsize=1024)    
    def format_global_id_as_uuid(self, global_id: str) -> str:
        """
        Format a global ID as a UUID with dashes.
        
        Args:
            global_id: Global ID string
            
        Returns:
            Formatted UUID
        """
        if not global_id:
            return ""
            
        # Convert the id_global to UUID format with dashes if needed
        if "-" not in global_id and len(global_id) == 32:
            formatted_uuid = (
                f"{global_id[0:8]}-"
                f"{global_id[8:12]}-"
                f"{global_id[12:16]}-"
                f"{global_id[16:20]}-"
                f"{global_id[20:]}"
            )
            return formatted_uuid
        return global_id
        
    def find_preview_by_uuid(self, uuid: str, is_file_uuid: bool = True) -> Optional[str]:
        """
        Find a preview file by UUID.
        
        Args:
            uuid: UUID to search for
            is_file_uuid: Whether this is a file UUID (True) or image UUID (False)
            
        Returns:
            Path to the preview file if found, None otherwise
        """
        if not uuid or not self.has_previews_dir:
            return None
            
        formatted_uuid = self.format_global_id_as_uuid(uuid)
        logger.debug(f"Searching for preview with UUID: {formatted_uuid} (is_file_uuid={is_file_uuid})")
        
        preview_files = []
        
        # Search through the previews directory
        for root, _, files in os.walk(self.previews_dir):
            for file in files:
                if file.endswith('.db'):
                    continue
                    
                if formatted_uuid in file:
                    preview_path = os.path.join(root, file)
                    preview_files.append(preview_path)
                    
        # Sort by resolution using the shared utility function
        if preview_files:
            preview_files.sort(key=get_preview_resolution_rank, reverse=True)
            best_preview = preview_files[0]
            logger.info(f"Found UUID-based preview: {best_preview}")
            return best_preview
            
        return None
        
    def find_preview_by_basename(self, base_name: str) -> Optional[str]:
        """
        Find a preview file by base name.
        
        Args:
            base_name: Base name of the image
            
        Returns:
            Path to the preview file if found, None otherwise
        """
        if not base_name or not self.has_previews_dir:
            return None

        # Check if we built an index
        if hasattr(self, 'preview_index'):
            name_lower = os.path.splitext(base_name)[0].lower()
            
            # First try exact match
            if name_lower in self.preview_index:
                logger.debug(f"Using exact preview_index match for {base_name}: {self.preview_index[name_lower][0]}")
                return self.preview_index[name_lower][0]
                
            # Then try partial matches
            for k, v in self.preview_index.items():
                if name_lower in k:
                    logger.debug(f"Using partial preview_index match for {base_name}: {v[0]}")
                    return v[0]

            return None
            
        clean_basename = os.path.splitext(base_name)[0]
        logger.debug(f"Searching for preview with basename: {clean_basename}")
        
        # Direct search by basename
        for root, _, files in os.walk(self.previews_dir):
            for file in files:
                if file.endswith('.db'):
                    continue
                    
                if clean_basename in file:
                    preview_path = os.path.join(root, file)
                    logger.info(f"Found direct basename match: {preview_path}")
                    return preview_path
                    
        return None
        
    def find_preview_by_patterns(self, patterns: List[str], base_name: str, file_id: str) -> Optional[str]:
        """
        Find preview files by known patterns.
        
        Args:
            patterns: List of known patterns
            base_name: Base name of the image
            file_id: File ID
            
        Returns:
            Path to the preview file if found, None otherwise
        """
        if not patterns or not self.has_previews_dir:
            return None
            
        clean_basename = os.path.splitext(base_name)[0]
        
        for root, dirs, files in os.walk(self.previews_dir):
            # Skip database files
            filtered_files = [f for f in files if not f.endswith('.db')]
            
            # First check for patterns with basename or file_id match
            for pattern in patterns:
                for file in filtered_files:
                    if pattern in file and (clean_basename in file or str(file_id) in file):
                        preview_path = os.path.join(root, file)
                        logger.info(f"Found pattern-based match with basename/ID: {preview_path}")
                        return preview_path
                        
            # Then just check for patterns
            for pattern in patterns:
                pattern_matches = [f for f in filtered_files if pattern in f]
                if pattern_matches:
                    preview_path = os.path.join(root, pattern_matches[0])
                    logger.info(f"Found pattern-based match: {preview_path}")
                    return preview_path
                    
        return None
    
    @lru_cache(maxsize=256)    
    def find_preview_by_hash(self, base_name: str) -> Optional[str]:
        """
        Find preview files by filename hash.
        
        Args:
            base_name: Base name of the image
            
        Returns:
            Path to the preview file if found, None otherwise
        """
        if not base_name or not self.has_previews_dir or not self.config.deep_search:
            return None
            
        filename_hash = hashlib.md5(base_name.encode()).hexdigest().lower()
        logger.debug(f"Searching by hash for {base_name}, hash: {filename_hash}")
        
        for root, _, files in os.walk(self.previews_dir):
            for file in files:
                if file.endswith('.db'):
                    continue
                file_lower = file.lower()
                
                if filename_hash in file_lower:
                    preview_path = os.path.join(root, file)
                    logger.info(f"Found hash-based match: {preview_path}")
                    return preview_path
                    
        return None
        
    def find_smart_preview(self, base_name: str) -> Optional[str]:
        """
        Find a smart preview for an image.
        
        Args:
            base_name: Base name of the image
            
        Returns:
            Path to the smart preview if found, None otherwise
        """
        if not base_name or not self.has_smart_previews_dir or not self.config.use_smart_previews:
            return None
            
        clean_basename = os.path.splitext(base_name)[0]
        logger.debug(f"Checking smart previews for: {clean_basename}")
        
        for root, _, files in os.walk(self.smart_previews_dir):
            for file in files:
                if file.endswith('.db'):
                    continue
                    
                if file.lower().endswith('.dng') and clean_basename in file:
                    preview_path = os.path.join(root, file)
                    logger.info(f"Found smart preview .dng: {preview_path}")
                    return preview_path
                    
                # Or check partial matches
                filename_parts = clean_basename.split('-')
                for part in filename_parts:
                    if len(part) > 3 and part in file:
                        preview_path = os.path.join(root, file)
                        logger.info(f"Found smart preview match: {preview_path}")
                        return preview_path
                        
        return None
        
    def get_original_image_path(self, root_folder: str, path_from_root: str, base_name: str) -> Optional[str]:
        """
        Get the path to the original image file.
        
        Args:
            root_folder: Root folder path
            path_from_root: Path from root folder
            base_name: Base name of the image
            
        Returns:
            Path to the original image if found, None otherwise
        """
        if not self.config.use_original_if_no_preview:
            return None
            
        try:
            original_path = os.path.join(root_folder, path_from_root, base_name)
            if os.path.exists(original_path):
                logger.info(f"Using original image as fallback: {original_path}")
                return original_path
            else:
                logger.warning(f"Original image not found: {original_path}")
                return None
        except Exception as e:
            logger.warning(f"Failed to use original image: {str(e)}")
            return None
            
    def get_preview_resolution_rank(self, file_path: str) -> int:
        """
        Determine the resolution rank of a preview file based on its suffix.
        
        Args:
            file_path: Path to the preview file
            
        Returns:
            Rank value (higher means higher resolution)
        """
        file_name = os.path.basename(file_path)
        
        # High resolution
        if any(suffix in file_name for suffix in ('_3202', '_3200', '_3951', '_3199')):
            return 3
        # Medium resolution
        elif any(suffix in file_name for suffix in ('_1601', '_1600', '_1975', '_1599')):
            return 2
        # Low resolution
        elif any(suffix in file_name for suffix in ('_800', '_799', '_987')):
            return 1
        # Unknown
        return 0
        
    def debug_directory_structure(self, directory: str, depth: int = 2, current_depth: int = 0, max_items: int = 5) -> None:
        """
        Log directory structure for debugging.
        
        Args:
            directory: Directory to scan
            depth: Maximum depth to scan
            current_depth: Current recursion depth
            max_items: Maximum number of items to list per directory
        """
        if current_depth > depth or not os.path.exists(directory):
            return
            
        try:
            items = os.listdir(directory)
            
            # Limit the number of items to log
            if len(items) > max_items:
                sample_items = items[:max_items]
                logger.debug(f"{' ' * current_depth}Directory {directory}: {len(items)} items, showing first {max_items}: {sample_items}")
            else:
                logger.debug(f"{' ' * current_depth}Directory {directory}: {items}")
                
            # Recurse into subdirectories
            for item in items[:max_items]:
                item_path = os.path.join(directory, item)
                if os.path.isdir(item_path):
                    self.debug_directory_structure(item_path, depth, current_depth + 1, max_items)
                    
        except Exception as e:
            logger.debug(f"Error reading directory {directory}: {str(e)}")
