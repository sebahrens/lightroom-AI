"""
Locate and extract preview images from Lightroom catalog.
"""

import os
import re
import io
import logging
import threading
import time
from typing import Dict, Any, Optional, Tuple, List
from functools import lru_cache

from PIL import Image

from .config import AppConfig
from .catalog_db import CatalogDatabase
from .preview_db import PreviewDatabase
from .filesystem import FilesystemHelper
from .logging_setup import get_logger

logger = get_logger(__name__)


class PreviewExtractor:
    """Class to handle locating and extracting preview images."""
    
    def __init__(self, catalog_path: str, config: AppConfig):
        """
        Initialize the preview extractor.
        
        Args:
            catalog_path: Path to the Lightroom catalog file
            config: Application configuration
        """
        self.catalog_path = catalog_path
        self.config = config
        self.filesystem = FilesystemHelper(catalog_path, config)
        
        # Replace module-level cache with instance-level cache with lock
        self._preview_cache: Dict[str, str] = {}
        self._cache_lock = threading.RLock()  # Use RLock to allow nested calls
        
        # Add a cache hit counter for statistics
        self._cache_hits = 0
        self._cache_misses = 0
        self._cache_last_report = time.time()
        
        # Initialize preview database if available
        if self.filesystem.has_previews_dir:
            self.preview_db = PreviewDatabase(self.filesystem.previews_dir, config)
        else:
            self.preview_db = None
            
    def clear_cache(self) -> None:
        """Clear the preview location cache."""
        with self._cache_lock:
            cache_size = len(self._preview_cache)
            self._preview_cache.clear()
            self._cache_hits = 0
            self._cache_misses = 0
        logger.debug(f"Preview location cache cleared ({cache_size} entries removed)")
        
    def get_cache_size(self) -> int:
        """Get the size of the preview location cache."""
        with self._cache_lock:
            return len(self._preview_cache)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._cache_lock:
            total = self._cache_hits + self._cache_misses
            hit_rate = self._cache_hits / total if total > 0 else 0
            return {
                'size': len(self._preview_cache),
                'hits': self._cache_hits,
                'misses': self._cache_misses,
                'hit_rate': hit_rate
            }
        
    def optimize_search_strategies(self, db_info: Dict[str, Any]) -> None:
        """
        Optimize search strategies based on database analysis.
        
        Args:
            db_info: Database information from analyze_database_structure
        """
        if not db_info:
            return
            
        # Check if smart previews are present
        if db_info.get('has_smart_previews_dir'):
            self.config.use_smart_previews = True
            logger.info("Smart Previews directory found - enabling smart preview search")
        
        # Set additional search flags based on database structure
        has_preview_db = db_info.get('has_previews_dir') and os.path.exists(os.path.join(db_info.get('previews_dir', ''), 'previews.db'))
        if has_preview_db:
            self.config.use_preview_db = True
            logger.info("Preview database found - enabling preview database search")
        
        # Add any catalog-specific preview search strategies
        if db_info.get('has_id_global'):
            self.config.use_id_global = True
            logger.info("Global ID column found - enabling search by global ID")
            
        # Extract patterns if preview directory exists
        if self.preview_db and self.filesystem.has_previews_dir:
            patterns = self.preview_db.collect_preview_file_patterns()
            if patterns:
                self.config.known_preview_patterns = patterns
                logger.info(f"Preview search strategies optimized based on DB analysis")
    
    @lru_cache(maxsize=32)
    def _get_preview_resolution_rank(self, file_path: str) -> int:
        """
        Cached wrapper for resolution rank calculation.
        """
        return self.filesystem.get_preview_resolution_rank(file_path)
        
    def locate_preview_file(self, image_data: Tuple) -> Optional[str]:
        """
        Locate the preview file for an image in the Lightroom preview or smart preview cache.
        
        Args:
            image_data: Tuple containing image information
                (image_id, file_id, baseName, pathFromRoot, absolutePath, 
                 image_global_id, file_global_id, image_time)
            
        Returns:
            Path to the preview file if found, None otherwise
        """
        # Unpack needed values from image_data tuple
        image_id = image_data[0]
        file_id = image_data[1]
        base_name = image_data[2]
        path_from_root = image_data[3]
        root_folder = image_data[4]
        image_global_id = image_data[5] if len(image_data) > 5 else None
        file_global_id = image_data[6] if len(image_data) > 6 else None
        
        # Check cache first (thread-safe)
        cache_key = f"{image_id}_{base_name}"
        with self._cache_lock:
            if cache_key in self._preview_cache:
                self._cache_hits += 1
                
                # Report cache stats periodically
                now = time.time()
                if now - self._cache_last_report > 60:  # Report every minute
                    total = self._cache_hits + self._cache_misses
                    hit_rate = self._cache_hits / total if total > 0 else 0
                    logger.debug(f"Preview cache stats: {len(self._preview_cache)} entries, {hit_rate:.1%} hit rate")
                    self._cache_last_report = now
                    
                return self._preview_cache[cache_key]
            else:
                self._cache_misses += 1
            
        if self.config.debug_mode:
            logger.debug(f"Searching for previews for image: {base_name} (ID: {image_id}, File Global ID: {file_global_id})")
            
        preview_path = None
        
        # Strategy 1: Try to find by file's global ID (most accurate)
        if file_global_id and self.config.use_id_global:
            preview_path = self.filesystem.find_preview_by_uuid(file_global_id, is_file_uuid=True)
            
        # Strategy 2: Try to find via preview database
        if not preview_path and self.preview_db and self.config.use_preview_db:
            preview_uuid = self.preview_db.get_preview_uuid(image_id)
            if preview_uuid:
                preview_files = self.preview_db.get_image_preview_files(preview_uuid)
                if preview_files:
                    preview_path = preview_files[0]  # Get the highest resolution
                    
        # Strategy 3: Try to find by image's global ID (less accurate but sometimes works)
        if not preview_path and image_global_id and self.config.use_id_global:
            preview_path = self.filesystem.find_preview_by_uuid(image_global_id, is_file_uuid=False)
            
        # Strategy 4: Try to find by base name (fallback)
        if not preview_path:
            preview_path = self.filesystem.find_preview_by_basename(base_name)
            
        # Strategy 5: Try to find by known patterns
        if not preview_path and self.config.known_preview_patterns:
            preview_path = self.filesystem.find_preview_by_patterns(
                self.config.known_preview_patterns, base_name, str(file_id))
                
        # Strategy 6: Deep search by filename hash (slower)
        if not preview_path and self.config.deep_search:
            preview_path = self.filesystem.find_preview_by_hash(base_name)
            
        # Strategy 7: Try smart previews
        if not preview_path and self.config.use_smart_previews:
            preview_path = self.filesystem.find_smart_preview(base_name)
            
        # Strategy 8: Use original file as fallback
        if not preview_path and self.config.use_original_if_no_preview:
            preview_path = self.filesystem.get_original_image_path(root_folder, path_from_root, base_name)
            
        # No preview found
        if not preview_path:
            logger.warning(f"No preview found for image: {base_name} (ID: {image_id})")
        else:
            # Cache the result for future queries (thread-safe)
            with self._cache_lock:
                self._preview_cache[cache_key] = preview_path
            
        return preview_path
    
    def _is_jpeg_header(self, header: bytes) -> bool:
        """
        Check if the given bytes represent a JPEG header.
        
        Args:
            header: Bytes to check
            
        Returns:
            True if it's a JPEG header, False otherwise
        """
        return header[0:3] == b'\xFF\xD8\xFF'
        
    def extract_jpeg_from_preview(self, preview_path: str) -> Optional[Image.Image]:
        """
        Extract JPEG data from a Lightroom preview file.
        Handles .lrprev containers, direct JPEG files, and DNG smart previews.
        
        Args:
            preview_path: Path to the preview file
            
        Returns:
            PIL Image object if successful, None otherwise
        """
        if not preview_path:
            return None
            
        img = None  # Initialize img to None to avoid UnboundLocalError in finally block
        
        try:
            file_size = os.path.getsize(preview_path)
            if file_size == 0:
                logger.error(f"Preview file is empty: {preview_path}")
                return None
                
            if self.config.debug_mode:
                logger.debug(f"Processing preview file: {preview_path} (size: {file_size} bytes)")
                
            with open(preview_path, "rb") as f:
                header = f.read(16)
            
            # Strategy 1: Check if it's already a JPEG
            if self._is_jpeg_header(header):
                if self.config.debug_mode:
                    logger.debug(f"File is a JPEG: {preview_path}")
                with Image.open(preview_path) as img:
                    return img.copy()
            
            # Strategy 2: Try opening directly as an image
            # (Newer LR previews often have no standard extension but are valid JPEG)
            try:
                img = Image.open(preview_path)
                if self.config.debug_mode:
                    logger.debug(f"Successfully opened preview as direct image: {preview_path} ({img.format}, {img.width}x{img.height})")
                return img
            except Exception:
                pass  # We'll keep trying below
            
            # Strategy 3: For .lrprev files (older LR versions), extract JPEG data
            if preview_path.lower().endswith('.lrprev'):
                if self.config.debug_mode:
                    logger.debug(f"Extracting JPEG from .lrprev container: {preview_path}")
                with open(preview_path, "rb") as f:
                    data = f.read()
                start = data.find(b"\xFF\xD8")
                end = data.rfind(b"\xFF\xD9")
                
                if start != -1 and end != -1:
                    jpeg_data = data[start:end+2]
                    return Image.open(io.BytesIO(jpeg_data))
                else:
                    logger.error(f"No JPEG data found in {preview_path}")
                    if self.config.debug_mode:
                        logger.debug(f"First 32 bytes of file: {data[:32].hex()}")
                    return None
            
            # Strategy 4: For DNG files (smart previews)
            if preview_path.lower().endswith('.dng'):
                if self.config.debug_mode:
                    logger.debug(f"Attempting to extract preview from DNG: {preview_path}")
                try:
                    import rawpy
                    with rawpy.imread(preview_path) as raw:
                        try:
                            thumb = raw.extract_thumb()
                            if thumb.format == rawpy.ThumbFormat.JPEG:
                                return Image.open(io.BytesIO(thumb.data))
                        except:
                            pass
                        rgb = raw.postprocess()
                        return Image.fromarray(rgb)
                except ImportError:
                    logger.warning("rawpy not available for DNG processing. Install with: pip install rawpy")
                except Exception as e:
                    logger.error(f"Failed to extract preview from DNG via rawpy: {str(e)}")
                
                # If all else fails, try PIL
                try:
                    with Image.open(preview_path) as img:
                        return img.copy()
                except:
                    logger.error(f"Failed to extract preview from DNG: {preview_path}")
                    return None
            
            # Strategy 5: Scan file for a JPEG header
            with open(preview_path, "rb") as f:
                data = f.read()
            
            start = data.find(b"\xFF\xD8\xFF")
            if start != -1:
                end = data.rfind(b"\xFF\xD9")
                if end != -1 and end > start:
                    jpeg_data = data[start:end+2]
                    if self.config.debug_mode:
                        logger.debug(f"Found embedded JPEG at offset {start}, length {len(jpeg_data)}")
                    return Image.open(io.BytesIO(jpeg_data))
            
            # Strategy 6: Final fallback—try opening directly again
            try:
                with Image.open(preview_path) as img:
                    return img.copy()
                    
            except Exception as e:
                logger.error(f"All extraction methods failed for {preview_path}: {str(e)}")
                return None
        
        except Exception as e:
            logger.error(f"Failed to extract preview from {preview_path}: {str(e)}")
            if self.config.debug_mode:
                import traceback
                logger.debug(f"Traceback: {traceback.format_exc()}")
            return None
        finally:
            # Ensure resources are closed even if an exception occurs
            if img is not None:
                try:
                    img.close()
                except Exception:
                    pass
            
    def scan_previews(self, images: List[Tuple]) -> Tuple[int, int]:
        """
        Scan for preview files without extracting them.
        
        Args:
            images: List of image data tuples
            
        Returns:
            Tuple of (total_images, found_previews)
        """
        logger.info(f"SCAN-ONLY MODE: Checking previews for {len(images)} images (no extraction)")
        
        found_count = 0
        start_time = time.time()
        last_report_time = start_time
        
        for i, image_data in enumerate(images, 1):
            image_id = image_data[0]
            base_name = image_data[2]
            
            preview_path = self.locate_preview_file(image_data)
            
            if preview_path:
                found_count += 1
                logger.info(f"[{i}/{len(images)}] Found preview for {base_name} (ID: {image_id}): {preview_path}")
            else:
                logger.warning(f"[{i}/{len(images)}] No preview for {base_name} (ID: {image_id})")
                
            # Report progress at regular intervals
            current_time = time.time()
            if i % 10 == 0 or i == len(images) or (current_time - last_report_time) > 5:
                elapsed = current_time - start_time
                images_per_second = i / elapsed if elapsed > 0 else 0
                logger.info(f"Scan progress: {i}/{len(images)} images checked, {found_count} previews found ({images_per_second:.1f} img/sec)")
                last_report_time = current_time
                
        total_time = time.time() - start_time
        images_per_second = len(images) / total_time if total_time > 0 else 0
        logger.info(f"Scan complete: {found_count}/{len(images)} previews found ({found_count/len(images)*100:.1f}%) in {total_time:.1f}s ({images_per_second:.1f} img/sec)")
        
        # Report cache statistics
        cache_stats = self.get_cache_stats()
        logger.info(f"Cache statistics: {cache_stats['size']} entries, {cache_stats['hit_rate']:.1%} hit rate")
        
        return len(images), found_count
