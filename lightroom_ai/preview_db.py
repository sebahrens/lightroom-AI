"""
Preview database analysis and interactions.
"""

import os
import sqlite3
import logging
from typing import Dict, Any, List, Optional, Tuple

from .config import AppConfig
from .logging_setup import get_logger
from .utils import get_preview_resolution_rank  # Import the utility function

logger = get_logger(__name__)


class PreviewDatabase:
    """Class to handle interactions with Lightroom preview database."""
    
    def __init__(self, previews_dir: str, config: AppConfig):
        """
        Initialize the preview database connection.
        
        Args:
            previews_dir: Path to the Lightroom previews directory
            config: Application configuration
        """
        self.previews_dir = previews_dir
        self.config = config
        self.preview_db_path = os.path.join(previews_dir, "previews.db")
        self.has_preview_db = os.path.exists(self.preview_db_path)
        
    def connect(self):
        """
        Connect to the preview database.
        
        Returns:
            SQLite connection if successful, None otherwise
        """
        if not self.has_preview_db:
            return None
            
        try:
            return sqlite3.connect(self.preview_db_path)
        except sqlite3.Error as e:
            logger.warning(f"Failed to connect to preview database: {str(e)}")
            return None
            
    def get_preview_uuid(self, image_id: int) -> Optional[str]:
        """
        Get the preview UUID for an image.
        
        Args:
            image_id: Image ID
            
        Returns:
            Preview UUID if found, None otherwise
        """
        if not self.has_preview_db:
            return None
            
        conn = self.connect()
        if not conn:
            return None
            
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT uuid FROM AgPreviewImages WHERE image = ?", (image_id,))
            result = cursor.fetchone()
            
            if result:
                preview_uuid = result[0]
                logger.debug(f"Found preview UUID: {preview_uuid} for image ID: {image_id}")
                return preview_uuid
            return None
        except sqlite3.Error as e:
            logger.debug(f"Error fetching preview UUID: {str(e)}")
            return None
        finally:
            conn.close()
            
    def get_image_preview_files(self, preview_uuid: str) -> List[str]:
        """
        Get all preview files for a given UUID.
        
        Args:
            preview_uuid: Preview UUID
            
        Returns:
            List of preview file paths
        """
        preview_files = []
        
        try:
            for root, _, files in os.walk(self.previews_dir):
                for file in files:
                    if file.endswith('.db'):
                        continue
                    if preview_uuid in file:
                        preview_files.append(os.path.join(root, file))
            
            # Sort by resolution using the shared utility function
            preview_files.sort(key=get_preview_resolution_rank, reverse=True)
            
            return preview_files
        except Exception as e:
            logger.error(f"Error finding preview files for UUID {preview_uuid}: {str(e)}")
            return []
            
            
    def analyze_preview_database(self) -> Dict[str, Any]:
        """
        Analyze the preview database structure.
        
        Returns:
            Dictionary with preview database information
        """
        if not self.has_preview_db:
            return {'has_preview_db': False}
            
        info = {'has_preview_db': True}
        
        conn = self.connect()
        if not conn:
            return info
            
        try:
            cursor = conn.cursor()
            
            # Get tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            info['tables'] = tables
            
            # Sample preview data
            if 'AgPreviewImages' in tables:
                cursor.execute("SELECT * FROM AgPreviewImages LIMIT 5")
                samples = cursor.fetchall()
                
                if samples:
                    column_names = [description[0] for description in cursor.description]
                    info['preview_columns'] = column_names
                    
                    if self.config.debug_mode:
                        sample_data = []
                        for sample in samples:
                            sample_dict = {column_names[i]: sample[i] for i in range(len(column_names))}
                            sample_data.append(sample_dict)
                        info['sample_data'] = sample_data
            
            # Detect special tables and features
            info['has_preview_uuid_table'] = any('uuid' in t.lower() for t in tables)
            
            return info
        except sqlite3.Error as e:
            logger.error(f"Error analyzing preview database: {str(e)}")
            return {'has_preview_db': True, 'error': str(e)}
        finally:
            conn.close()
            
    def collect_preview_file_patterns(self) -> List[str]:
        """
        Collect common patterns in preview filenames.
        
        Returns:
            List of detected patterns
        """
        patterns = set()
        
        try:
            # Get a sample of files from subdirectories
            for root, _, files in os.walk(self.previews_dir):
                if root == self.previews_dir:
                    continue
                    
                for filename in files[:10]:  # Limit to 10 files per directory
                    if '_' in filename:
                        parts = filename.split('_')
                        if len(parts) > 1:
                            last_part = parts[-1]
                            if last_part.isdigit():
                                patterns.add(f"_{last_part}")
            
            logger.info(f"Detected preview file patterns: {patterns}")
            return list(patterns)
        except Exception as e:
            logger.error(f"Error collecting preview file patterns: {str(e)}")
            return []
