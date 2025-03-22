"""
Database interaction with Lightroom catalog.
"""

import os
import sqlite3
import logging
import time
from typing import List, Tuple, Dict, Any, Optional, Set
from contextlib import contextmanager
import json
import uuid

from .config import AppConfig
from .logging_setup import get_logger

logger = get_logger(__name__)

class CatalogDatabase:
    """Class to handle interactions with the Lightroom catalog database."""
    
    def __init__(self, catalog_path: str, config: AppConfig):
        """
        Initialize the database connection.
    
        Args:
            catalog_path: Path to the Lightroom catalog file
            config: Application configuration
        
        Raises:
            FileNotFoundError: If the catalog file doesn't exist
            RuntimeError: If connection to the catalog fails
        """
        if not os.path.exists(catalog_path):
            raise FileNotFoundError(f"Lightroom catalog not found: {catalog_path}")
        
        self.catalog_path = catalog_path
        self.config = config
        # Connection is created on demand in each call to 'cursor()'
        
        # Get hierarchical preferences if available
        self.use_hierarchical_keywords = getattr(config, 'use_hierarchical_keywords', False)
        self.keyword_delimiter = getattr(config, 'keyword_delimiter', ':')
        
        # Get database timeout from config, default to 30 seconds if not specified
        self.db_busy_timeout = getattr(config, 'db_busy_timeout', 30000)
        self.max_retries = getattr(config, 'max_retries', 3)

    def _connect(self):
        """
        Establish a connection to the SQLite database.
        Creates a new connection for each thread to ensure thread safety.
        """
        try:
            conn = sqlite3.connect(self.catalog_path, isolation_level=None)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            # Set busy_timeout to reduce locking errors
            conn.execute(f"PRAGMA busy_timeout={self.db_busy_timeout}")
            return conn
        except sqlite3.Error as e:
            logger.error(f"Failed to connect to Lightroom catalog: {str(e)}")
            raise RuntimeError(f"Failed to connect to Lightroom catalog: {str(e)}")

    def close(self):
        """
        Close the database connection. (No-op here since we open/close per context manager call.)
        """
        pass

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with automatic close."""
        pass

    @contextmanager
    def cursor(self, retries=None):
        """
        Get a cursor as a context manager, ensuring proper cleanup.
        Each call opens a new connection; commits or rolls back, then closes.
        
        Args:
            retries: Number of retries if database is locked (defaults to self.max_retries)
        """
        if retries is None:
            retries = self.max_retries
            
        retry_count = 0
        last_error = None
        
        while retry_count <= retries:
            try:
                conn = self._connect()
                conn.execute("BEGIN DEFERRED")
                cursor = conn.cursor()
                try:
                    yield cursor
                    conn.commit()
                    return  # Success, exit the retry loop
                except sqlite3.OperationalError as e:
                    if "database is locked" in str(e) and retry_count < retries:
                        conn.rollback()
                        last_error = e
                        retry_count += 1
                        wait_time = 0.5 * (2 ** retry_count)  # Exponential backoff
                        logger.warning(f"Database locked, retrying in {wait_time:.2f}s (attempt {retry_count}/{retries})")
                        time.sleep(wait_time)
                    else:
                        conn.rollback()
                        raise
                except Exception as e:
                    conn.rollback()
                    raise
                finally:
                    cursor.close()
                    conn.close()
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e) and retry_count < retries:
                    last_error = e
                    retry_count += 1
                    wait_time = 0.5 * (2 ** retry_count)  # Exponential backoff
                    logger.warning(f"Database locked during connection, retrying in {wait_time:.2f}s (attempt {retry_count}/{retries})")
                    time.sleep(wait_time)
                else:
                    raise
        
        # If we get here, all retries failed
        if last_error:
            logger.error(f"All retries failed: {str(last_error)}")
            raise last_error
        else:
            raise RuntimeError("Failed to connect to database after multiple retries")

    def commit(self):
        """Commit is handled within the cursor() context manager."""
        pass

    def get_images(self, max_images: Optional[int] = None) -> List[Tuple]:
        """
        Query and return image list from Lightroom catalog with file IDs.
        
        Args:
            max_images: Maximum number of images to return.
        """
        try:
            with self.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        i.id_local AS image_id,
                        f.id_local AS file_id, 
                        f.baseName, 
                        fo.pathFromRoot, 
                        r.absolutePath,
                        i.id_global AS image_global_id,
                        f.id_global AS file_global_id,
                        i.captureTime AS image_time 
                    FROM AgLibraryFile f
                    JOIN AgLibraryFolder fo ON f.folder = fo.id_local
                    JOIN AgLibraryRootFolder r ON fo.rootFolder = r.id_local
                    JOIN Adobe_images i ON i.rootFile = f.id_local
                    WHERE f.importHash IS NOT NULL
                    ORDER BY i.id_local
                """)
                
                images = cursor.fetchall()
                logger.info(f"Retrieved {len(images)} images from catalog")
                
                if max_images and max_images > 0:
                    images = images[:max_images]
                    logger.info(f"Limiting to first {max_images} images as per configuration")
                    
                return images
        except sqlite3.Error as e:
            raise RuntimeError(f"Failed to retrieve images from catalog: {str(e)}")

    def get_processed_images(self) -> Set[int]:
        """
        Get a set of image IDs that have already been processed by our AI tool (keyword: 'AI_Processed').
        """
        try:
            with self.cursor() as cursor:
                cursor.execute("""
                    SELECT DISTINCT ki.image 
                    FROM AgLibraryKeywordImage ki
                    JOIN AgLibraryKeyword k ON ki.tag = k.id_local
                    WHERE k.name = 'AI_Processed'
                """)
                processed_ids = {row[0] for row in cursor.fetchall()}
                logger.info(f"Found {len(processed_ids)} already processed images")
                return processed_ids
        except sqlite3.Error as e:
            logger.error(f"Error getting processed images: {str(e)}")
            return set()

    def analyze_database_structure(self) -> Dict[str, Any]:
        """
        Analyze the Lightroom database structure to help with preview finding.
        
        Returns:
            Dictionary with database structure information.
        """
        try:
            with self.cursor() as cursor:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = [row[0] for row in cursor.fetchall()]
                
                logger.info(f"Found {len(tables)} tables in Lightroom catalog database")
                
                preview_tables = [t for t in tables if 'preview' in t.lower()]
                image_tables = [t for t in tables if 'image' in t.lower()]
                
                db_info = {
                    'has_adobe_images': 'Adobe_images' in tables,
                    'has_preview_images': 'AgPreviewImages' in tables,
                    'has_library_file': 'AgLibraryFile' in tables,
                    'preview_tables': preview_tables,
                    'image_tables': image_tables,
                    'column_map': {}
                }
                
                for table in ['Adobe_images', 'AgLibraryFile', 'AgPreviewImages']:
                    if table in tables:
                        cursor.execute(f"PRAGMA table_info({table})")
                        columns = [row[1] for row in cursor.fetchall()]
                        db_info['column_map'][table] = columns

                # Additional checks
                if 'Adobe_images' in db_info['column_map']:
                    columns = db_info['column_map']['Adobe_images']
                    db_info['has_capture_time'] = 'captureTime' in columns
                    db_info['has_import_time'] = 'importTime' in columns
                    db_info['has_id_global'] = 'id_global' in columns

                # Check for preview folder
                catalog_dir = os.path.dirname(self.catalog_path)
                catalog_name = os.path.splitext(os.path.basename(self.catalog_path))[0]
                previews_dir = os.path.join(catalog_dir, f"{catalog_name} Previews.lrdata")
                smart_previews_dir = os.path.join(catalog_dir, f"{catalog_name} Smart Previews.lrdata")
                
                db_info['has_previews_dir'] = os.path.exists(previews_dir)
                db_info['has_smart_previews_dir'] = os.path.exists(smart_previews_dir)
                db_info['previews_dir'] = previews_dir
                db_info['smart_previews_dir'] = smart_previews_dir
                
                logger.info(
                    f"Database analysis complete. "
                    f"Preview dirs: Standard={db_info['has_previews_dir']}, "
                    f"Smart={db_info['has_smart_previews_dir']}"
                )
                return db_info
        
        except Exception as e:
            logger.error(f"Error analyzing Lightroom database: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {}

    def _apply_keywords(self, cursor, image_id: int, ai_metadata: Dict[str, Any]):
        """
        Insert or link the 'AI_Processed' keyword, plus other keywords, tags, film format, etc.
        Only apply L2 or L3 keywords, not L1 (top-level) keywords.
        """
        keywords = ai_metadata.get('keywords', [])
        tags = ai_metadata.get('tags', [])
        taxonomy = ai_metadata.get('taxonomy', {})
        aesthetic_score = ai_metadata.get('aesthetic_score', 0)

        all_keywords = keywords + tags + ["AI_Processed"]

        # Also add the aesthetic score as a keyword (e.g. "AI_Score_7.5")
        score_keyword = f"AI_Score_{aesthetic_score:.1f}"
        all_keywords.append(score_keyword)

        # If hierarchical keywords are enabled, add them from taxonomy
        if self.use_hierarchical_keywords and taxonomy:
            delimiter = self.keyword_delimiter
            
            # Case-insensitive access to taxonomy keys
            vs_codes = []
            ic_codes = []
            ce_codes = []
            
            for key, value in taxonomy.items():
                if key.upper() == "VS":
                    vs_codes = value
                elif key.upper() == "IC":
                    ic_codes = value
                elif key.upper() == "CE":
                    ce_codes = value

            # Track which L2 categories have L3 subcategories
            vs_l2_with_l3 = set()
            ic_l2_with_l3 = set()
            ce_l2_with_l3 = set()

            # First pass to identify L3 codes
            for code in vs_codes:
                code_upper = code.upper()
                parts = code_upper.split('.')
                if len(parts) == 3:  # L3 code
                    l2_prefix = '.'.join(parts[:2])
                    vs_l2_with_l3.add(l2_prefix)
            
            for code in ic_codes:
                code_upper = code.upper()
                parts = code_upper.split('.')
                if len(parts) == 3:  # L3 code
                    l2_prefix = '.'.join(parts[:2])
                    ic_l2_with_l3.add(l2_prefix)
            
            for code in ce_codes:
                code_upper = code.upper()
                parts = code_upper.split('.')
                if len(parts) == 3:  # L3 code
                    l2_prefix = '.'.join(parts[:2])
                    ce_l2_with_l3.add(l2_prefix)

            # Visual Subject hierarchy - second pass to add keywords
            for code in vs_codes:
                code_upper = code.upper()
                parts = code_upper.split('.')
                
                # Skip L1 codes (e.g., VS1)
                if len(parts) == 1:
                    continue
                    
                if code_upper.startswith("VS1"):  # People
                    # Don't add the top-level "People" keyword
                    if code_upper.startswith("VS1.1"):  # Individual Portrait
                        # Only add L2 if no L3 is present
                        if code_upper == "VS1.1" and "VS1.1" not in vs_l2_with_l3:
                            all_keywords.append(f"People{delimiter}Portrait")
                        # Add L3 keywords
                        elif code_upper == "VS1.1.1":
                            all_keywords.append(f"People{delimiter}Portrait{delimiter}Close-up")
                        elif code_upper == "VS1.1.2":
                            all_keywords.append(f"People{delimiter}Portrait{delimiter}Half-body")
                        elif code_upper == "VS1.1.3":
                            all_keywords.append(f"People{delimiter}Portrait{delimiter}Full-body")
                    elif code_upper.startswith("VS1.2"):  # Group
                        # Only add L2 if no L3 is present
                        if code_upper == "VS1.2" and "VS1.2" not in vs_l2_with_l3:
                            all_keywords.append(f"People{delimiter}Group")
                        # Add L3 keywords for Group
                        elif code_upper == "VS1.2.1":
                            all_keywords.append(f"People{delimiter}Group{delimiter}Small")
                        elif code_upper == "VS1.2.2":
                            all_keywords.append(f"People{delimiter}Group{delimiter}Medium")
                        elif code_upper == "VS1.2.3":
                            all_keywords.append(f"People{delimiter}Group{delimiter}Large")
                    elif code_upper.startswith("VS1.3"):  # Human Activity
                        # Only add L2 if no L3 is present
                        if code_upper == "VS1.3" and "VS1.3" not in vs_l2_with_l3:
                            all_keywords.append(f"People{delimiter}Activity")
                        # Add L3 keywords for Activity
                        elif code_upper == "VS1.3.1":
                            all_keywords.append(f"People{delimiter}Activity{delimiter}Work")
                        elif code_upper == "VS1.3.2":
                            all_keywords.append(f"People{delimiter}Activity{delimiter}Leisure")
                        elif code_upper == "VS1.3.3":
                            all_keywords.append(f"People{delimiter}Activity{delimiter}Ceremony")
                        elif code_upper == "VS1.3.4":
                            all_keywords.append(f"People{delimiter}Activity{delimiter}Daily Life")
                
                elif code_upper.startswith("VS2"):  # Place
                    # Don't add the top-level "Place" keyword
                    if code_upper.startswith("VS2.1"):  # Natural Environment
                        # Only add L2 if no L3 is present
                        if code_upper == "VS2.1" and "VS2.1" not in vs_l2_with_l3:
                            all_keywords.append(f"Place{delimiter}Natural")
                        # Add L3 keywords for Natural Environment
                        elif code_upper == "VS2.1.1":
                            all_keywords.append(f"Place{delimiter}Natural{delimiter}Mountain")
                        elif code_upper == "VS2.1.2":
                            all_keywords.append(f"Place{delimiter}Natural{delimiter}Water")
                        elif code_upper == "VS2.1.3":
                            all_keywords.append(f"Place{delimiter}Natural{delimiter}Forest")
                        elif code_upper == "VS2.1.4":
                            all_keywords.append(f"Place{delimiter}Natural{delimiter}Desert")
                        elif code_upper == "VS2.1.5":
                            all_keywords.append(f"Place{delimiter}Natural{delimiter}Sky")
                    elif code_upper.startswith("VS2.2"):  # Built Environment
                        # Only add L2 if no L3 is present
                        if code_upper == "VS2.2" and "VS2.2" not in vs_l2_with_l3:
                            all_keywords.append(f"Place{delimiter}Built")
                        # Add L3 keywords for Built Environment
                        elif code_upper == "VS2.2.1":
                            all_keywords.append(f"Place{delimiter}Built{delimiter}Architecture")
                        elif code_upper == "VS2.2.2":
                            all_keywords.append(f"Place{delimiter}Built{delimiter}Interior")
                        elif code_upper == "VS2.2.3":
                            all_keywords.append(f"Place{delimiter}Built{delimiter}Urban")
                        elif code_upper == "VS2.2.4":
                            all_keywords.append(f"Place{delimiter}Built{delimiter}Rural")
                        elif code_upper == "VS2.2.5":
                            all_keywords.append(f"Place{delimiter}Built{delimiter}Transportation")
                
                elif code_upper.startswith("VS3"):  # Objects
                    # Don't add the top-level "Objects" keyword
                    if code_upper.startswith("VS3.1"):  # Natural Objects
                        # Only add L2 if no L3 is present
                        if code_upper == "VS3.1" and "VS3.1" not in vs_l2_with_l3:
                            all_keywords.append(f"Objects{delimiter}Natural")
                        # Add L3 keywords for Natural Objects
                        elif code_upper == "VS3.1.1":
                            all_keywords.append(f"Objects{delimiter}Natural{delimiter}Flora")
                        elif code_upper == "VS3.1.2":
                            all_keywords.append(f"Objects{delimiter}Natural{delimiter}Fauna")
                        elif code_upper == "VS3.1.3":
                            all_keywords.append(f"Objects{delimiter}Natural{delimiter}Rocks")
                    elif code_upper.startswith("VS3.2"):  # Manufactured Objects
                        # Only add L2 if no L3 is present
                        if code_upper == "VS3.2" and "VS3.2" not in vs_l2_with_l3:
                            all_keywords.append(f"Objects{delimiter}Manufactured")
                        # Add L3 keywords for Manufactured Objects
                        elif code_upper == "VS3.2.1":
                            all_keywords.append(f"Objects{delimiter}Manufactured{delimiter}Vehicles")
                        elif code_upper == "VS3.2.2":
                            all_keywords.append(f"Objects{delimiter}Manufactured{delimiter}Tools")
                        elif code_upper == "VS3.2.3":
                            all_keywords.append(f"Objects{delimiter}Manufactured{delimiter}Furnishings")
                        elif code_upper == "VS3.2.4":
                            all_keywords.append(f"Objects{delimiter}Manufactured{delimiter}Products")
                        elif code_upper == "VS3.2.5":
                            all_keywords.append(f"Objects{delimiter}Manufactured{delimiter}Art")

            # Image Characteristics hierarchy
            for code in ic_codes:
                code_upper = code.upper()
                parts = code_upper.split('.')
                
                # Skip L1 codes
                if len(parts) == 1:
                    continue
                    
                if code_upper.startswith("IC1"):  # Composition
                    # Don't add top-level "Composition" keyword
                    if code_upper.startswith("IC1.1"):  # Frame Arrangement
                        # Only add L2 if no L3 is present
                        if code_upper == "IC1.1" and "IC1.1" not in ic_l2_with_l3:
                            all_keywords.append(f"Composition{delimiter}Frame")
                        # Add L3 keywords
                        elif code_upper == "IC1.1.1":
                            all_keywords.append(f"Composition{delimiter}Frame{delimiter}Symmetrical")
                        elif code_upper == "IC1.1.2":
                            all_keywords.append(f"Composition{delimiter}Frame{delimiter}Rule of Thirds")
                        elif code_upper == "IC1.1.3":
                            all_keywords.append(f"Composition{delimiter}Frame{delimiter}Centered")
                        elif code_upper == "IC1.1.4":
                            all_keywords.append(f"Composition{delimiter}Frame{delimiter}Dynamic")
                    elif code_upper.startswith("IC1.2"):  # Perspective
                        # Only add L2 if no L3 is present
                        if code_upper == "IC1.2" and "IC1.2" not in ic_l2_with_l3:
                            all_keywords.append(f"Composition{delimiter}Perspective")
                        # Add L3 keywords
                        elif code_upper == "IC1.2.1":
                            all_keywords.append(f"Composition{delimiter}Perspective{delimiter}Eye Level")
                        elif code_upper == "IC1.2.2":
                            all_keywords.append(f"Composition{delimiter}Perspective{delimiter}High Angle")
                        elif code_upper == "IC1.2.3":
                            all_keywords.append(f"Composition{delimiter}Perspective{delimiter}Low Angle")
                        elif code_upper == "IC1.2.4":
                            all_keywords.append(f"Composition{delimiter}Perspective{delimiter}Bird's Eye")
                        elif code_upper == "IC1.2.5":
                            all_keywords.append(f"Composition{delimiter}Perspective{delimiter}Worm's Eye")
                    elif code_upper.startswith("IC1.3"):  # Distance/Scale
                        # Only add L2 if no L3 is present
                        if code_upper == "IC1.3" and "IC1.3" not in ic_l2_with_l3:
                            all_keywords.append(f"Composition{delimiter}Distance")
                        # Add L3 keywords
                        elif code_upper == "IC1.3.1":
                            all_keywords.append(f"Composition{delimiter}Distance{delimiter}Macro")
                        elif code_upper == "IC1.3.2":
                            all_keywords.append(f"Composition{delimiter}Distance{delimiter}Mid-range")
                        elif code_upper == "IC1.3.3":
                            all_keywords.append(f"Composition{delimiter}Distance{delimiter}Wide")
                        elif code_upper == "IC1.3.4":
                            all_keywords.append(f"Composition{delimiter}Distance{delimiter}Panoramic")
                
                elif code_upper.startswith("IC2"):  # Visual Style
                    # Don't add top-level "Style" keyword
                    if code_upper.startswith("IC2.1"):  # Tonality
                        # Only add L2 if no L3 is present
                        if code_upper == "IC2.1" and "IC2.1" not in ic_l2_with_l3:
                            all_keywords.append(f"Style{delimiter}Tonality")
                        # Add L3 keywords
                        elif code_upper == "IC2.1.1":
                            all_keywords.append(f"Style{delimiter}Black & White")
                        elif code_upper == "IC2.1.2":
                            all_keywords.append(f"Style{delimiter}Monochrome")
                        elif code_upper == "IC2.1.3":
                            all_keywords.append(f"Style{delimiter}Color")
                    elif code_upper.startswith("IC2.2"):  # Contrast
                        # Only add L2 if no L3 is present
                        if code_upper == "IC2.2" and "IC2.2" not in ic_l2_with_l3:
                            all_keywords.append(f"Style{delimiter}Contrast")
                        # Add L3 keywords
                        elif code_upper == "IC2.2.1":
                            all_keywords.append(f"Style{delimiter}Contrast{delimiter}High")
                        elif code_upper == "IC2.2.2":
                            all_keywords.append(f"Style{delimiter}Contrast{delimiter}Medium")
                        elif code_upper == "IC2.2.3":
                            all_keywords.append(f"Style{delimiter}Contrast{delimiter}Low")
                    elif code_upper.startswith("IC2.3"):  # Focus
                        # Only add L2 if no L3 is present
                        if code_upper == "IC2.3" and "IC2.3" not in ic_l2_with_l3:
                            all_keywords.append(f"Style{delimiter}Focus")
                        # Add L3 keywords
                        elif code_upper == "IC2.3.1":
                            all_keywords.append(f"Style{delimiter}Focus{delimiter}Deep Depth")
                        elif code_upper == "IC2.3.2":
                            all_keywords.append(f"Style{delimiter}Focus{delimiter}Shallow Depth")
                        elif code_upper == "IC2.3.3":
                            all_keywords.append(f"Style{delimiter}Focus{delimiter}Soft")
                        elif code_upper == "IC2.3.4":
                            all_keywords.append(f"Style{delimiter}Focus{delimiter}Motion Blur")
                
                elif code_upper.startswith("IC3"):  # Color Characteristics
                    # Don't add top-level "Color" keyword
                    if code_upper.startswith("IC3.1"):  # Color Temperature
                        # Only add L2 if no L3 is present
                        if code_upper == "IC3.1" and "IC3.1" not in ic_l2_with_l3:
                            all_keywords.append(f"Color{delimiter}Temperature")
                        # Add L3 keywords
                        elif code_upper == "IC3.1.1":
                            all_keywords.append(f"Color{delimiter}Warm")
                        elif code_upper == "IC3.1.2":
                            all_keywords.append(f"Color{delimiter}Cool")
                        elif code_upper == "IC3.1.3":
                            all_keywords.append(f"Color{delimiter}Neutral")
                        elif code_upper == "IC3.1.4":
                            all_keywords.append(f"Color{delimiter}Mixed")
                    elif code_upper.startswith("IC3.2"):  # Color Saturation
                        # Only add L2 if no L3 is present
                        if code_upper == "IC3.2" and "IC3.2" not in ic_l2_with_l3:
                            all_keywords.append(f"Color{delimiter}Saturation")
                        # Add L3 keywords
                        elif code_upper == "IC3.2.1":
                            all_keywords.append(f"Color{delimiter}Saturation{delimiter}High")
                        elif code_upper == "IC3.2.2":
                            all_keywords.append(f"Color{delimiter}Saturation{delimiter}Moderate")
                        elif code_upper == "IC3.2.3":
                            all_keywords.append(f"Color{delimiter}Saturation{delimiter}Muted")
                    elif code_upper.startswith("IC3.3"):  # Color Palette
                        # Only add L2 if no L3 is present
                        if code_upper == "IC3.3" and "IC3.3" not in ic_l2_with_l3:
                            all_keywords.append(f"Color{delimiter}Palette")
                        # Add L3 keywords
                        elif code_upper == "IC3.3.1":
                            all_keywords.append(f"Color{delimiter}Palette{delimiter}Monochromatic")
                        elif code_upper == "IC3.3.2":
                            all_keywords.append(f"Color{delimiter}Palette{delimiter}Complementary")
                        elif code_upper == "IC3.3.3":
                            all_keywords.append(f"Color{delimiter}Palette{delimiter}Analogous")
                        elif code_upper == "IC3.3.4":
                            all_keywords.append(f"Color{delimiter}Palette{delimiter}Variety")

            # Contextual Elements hierarchy
            for code in ce_codes:
                code_upper = code.upper()
                parts = code_upper.split('.')
                
                # Skip L1 codes
                if len(parts) == 1:
                    continue
                    
                if code_upper.startswith("CE1"):  # Temporal Indicators
                    # Don't add top-level "Time" keyword
                    if code_upper.startswith("CE1.1"):  # Era Identifiers
                        # Only add L2 if no L3 is present
                        if code_upper == "CE1.1" and "CE1.1" not in ce_l2_with_l3:
                            all_keywords.append(f"Time{delimiter}Era")
                        # Add L3 keywords
                        elif code_upper == "CE1.1.1":
                            all_keywords.append(f"Time{delimiter}Era{delimiter}1970s")
                        elif code_upper == "CE1.1.2":
                            all_keywords.append(f"Time{delimiter}Era{delimiter}1980s")
                        elif code_upper == "CE1.1.3":
                            all_keywords.append(f"Time{delimiter}Era{delimiter}1990s")
                        elif code_upper == "CE1.1.4":
                            all_keywords.append(f"Time{delimiter}Era{delimiter}2000s")
                        elif code_upper == "CE1.1.5":
                            all_keywords.append(f"Time{delimiter}Era{delimiter}2010-Present")
                    elif code_upper.startswith("CE1.2"):  # Time of Day
                        # Only add L2 if no L3 is present
                        if code_upper == "CE1.2" and "CE1.2" not in ce_l2_with_l3:
                            all_keywords.append(f"Time{delimiter}Day")
                        # Add L3 keywords
                        elif code_upper == "CE1.2.1":
                            all_keywords.append(f"Time{delimiter}Day{delimiter}Dawn")
                        elif code_upper == "CE1.2.2":
                            all_keywords.append(f"Time{delimiter}Day{delimiter}Daytime")
                        elif code_upper == "CE1.2.3":
                            all_keywords.append(f"Time{delimiter}Golden Hour")
                        elif code_upper == "CE1.2.4":
                            all_keywords.append(f"Time{delimiter}Blue Hour")
                        elif code_upper == "CE1.2.5":
                            all_keywords.append(f"Time{delimiter}Night")
                    elif code_upper.startswith("CE1.3"):  # Seasonal Indicators
                        # Only add L2 if no L3 is present
                        if code_upper == "CE1.3" and "CE1.3" not in ce_l2_with_l3:
                            all_keywords.append(f"Time{delimiter}Season")
                        # Add L3 keywords
                        elif code_upper == "CE1.3.1":
                            all_keywords.append(f"Time{delimiter}Season{delimiter}Spring")
                        elif code_upper == "CE1.3.2":
                            all_keywords.append(f"Time{delimiter}Season{delimiter}Summer")
                        elif code_upper == "CE1.3.3":
                            all_keywords.append(f"Time{delimiter}Season{delimiter}Autumn")
                        elif code_upper == "CE1.3.4":
                            all_keywords.append(f"Time{delimiter}Season{delimiter}Winter")
                
                elif code_upper.startswith("CE2"):  # Cultural Context
                    # Don't add top-level "Culture" keyword
                    if code_upper.startswith("CE2.1"):  # Geographic Indicators
                        # Only add L2 if no L3 is present
                        if code_upper == "CE2.1" and "CE2.1" not in ce_l2_with_l3:
                            all_keywords.append(f"Culture{delimiter}Geographic")
                        # Add L3 keywords
                        elif code_upper == "CE2.1.1":
                            all_keywords.append(f"Culture{delimiter}Geographic{delimiter}Landmark")
                        elif code_upper == "CE2.1.2":
                            all_keywords.append(f"Culture{delimiter}Geographic{delimiter}Architecture")
                        elif code_upper == "CE2.1.3":
                            all_keywords.append(f"Culture{delimiter}Geographic{delimiter}Biome")
                        elif code_upper == "CE2.1.4":
                            all_keywords.append(f"Culture{delimiter}Geographic{delimiter}Cultural")
                    elif code_upper.startswith("CE2.2"):  # Social Context
                        # Only add L2 if no L3 is present
                        if code_upper == "CE2.2" and "CE2.2" not in ce_l2_with_l3:
                            all_keywords.append(f"Culture{delimiter}Social")
                        # Add L3 keywords
                        elif code_upper == "CE2.2.1":
                            all_keywords.append(f"Culture{delimiter}Social{delimiter}Personal")
                        elif code_upper == "CE2.2.2":
                            all_keywords.append(f"Culture{delimiter}Social{delimiter}Public")
                        elif code_upper == "CE2.2.3":
                            all_keywords.append(f"Culture{delimiter}Social{delimiter}Tradition")
                        elif code_upper == "CE2.2.4":
                            all_keywords.append(f"Culture{delimiter}Social{delimiter}Professional")
                
                elif code_upper.startswith("CE3"):  # Photographic Condition
                    # Don't add top-level "Photo" keyword
                    if code_upper.startswith("CE3.1"):  # Print Quality
                        # Only add L2 if no L3 is present
                        if code_upper == "CE3.1" and "CE3.1" not in ce_l2_with_l3:
                            all_keywords.append(f"Photo{delimiter}Quality")
                        # Add L3 keywords
                        elif code_upper == "CE3.1.1":
                            all_keywords.append(f"Photo{delimiter}Quality{delimiter}Well-Preserved")
                        elif code_upper == "CE3.1.2":
                            all_keywords.append(f"Photo{delimiter}Quality{delimiter}Moderate Aging")
                        elif code_upper == "CE3.1.3":
                            all_keywords.append(f"Photo{delimiter}Quality{delimiter}Significant Aging")
                    elif code_upper.startswith("CE3.2"):  # Format Indicators
                        # Only add L2 if no L3 is present
                        if code_upper == "CE3.2" and "CE3.2" not in ce_l2_with_l3:
                            all_keywords.append(f"Photo{delimiter}Format")
                        # Add L3 keywords
                        elif code_upper == "CE3.2.1":
                            all_keywords.append(f"Photo{delimiter}Format{delimiter}Square")
                        elif code_upper == "CE3.2.2":
                            all_keywords.append(f"Photo{delimiter}Format{delimiter}3:2")
                        elif code_upper == "CE3.2.3":
                            all_keywords.append(f"Photo{delimiter}Format{delimiter}4:3")
                        elif code_upper == "CE3.2.4":
                            all_keywords.append(f"Photo{delimiter}Format{delimiter}Panoramic")
                    elif code_upper.startswith("CE3.3"):  # Photographic Genre
                        # Only add L2 if no L3 is present
                        if code_upper == "CE3.3" and "CE3.3" not in ce_l2_with_l3:
                            all_keywords.append(f"Genre")
                        # Add L3 keywords
                        elif code_upper == "CE3.3.1":
                            all_keywords.append(f"Genre{delimiter}Documentary")
                        elif code_upper == "CE3.3.2":
                            all_keywords.append(f"Genre{delimiter}Street")
                        elif code_upper == "CE3.3.3":
                            all_keywords.append(f"Genre{delimiter}Fine Art")
                        elif code_upper == "CE3.3.4":
                            all_keywords.append(f"Genre{delimiter}Snapshot")
                        elif code_upper == "CE3.3.5":
                            all_keywords.append(f"Genre{delimiter}Experimental")

        # Now insert or link keywords
        for kw in all_keywords:
            if not kw.strip():
                continue

            cursor.execute("SELECT id_local, id_global FROM AgLibraryKeyword WHERE name = ?", (kw,))
            row = cursor.fetchone()

            if row is None:
                # Insert new keyword
                keyword_global_id = str(uuid.uuid4()).replace('-', '').upper()
                cursor.execute(
                    "INSERT INTO AgLibraryKeyword (name, lc_name, includeOnExport, id_global) VALUES (?, ?, ?, ?)",
                    (kw, kw.lower(), 1, keyword_global_id)
                )
                keyword_id = cursor.lastrowid
                logger.debug(f"Inserted new keyword '{kw}' with id {keyword_id}")
            else:
                keyword_id = row[0]

            # Link the keyword to the image if not already linked
            cursor.execute(
                "SELECT 1 FROM AgLibraryKeywordImage WHERE image = ? AND tag = ?",
                (image_id, keyword_id)
            )
            if cursor.fetchone() is None:
                cursor.execute(
                    "INSERT INTO AgLibraryKeywordImage (image, tag) VALUES (?, ?)",
                    (image_id, keyword_id)
                )

    def _apply_aesthetic_score(self, cursor, image_id: int, aesthetic_score: float):
        """
        If there's a 'rating' column, set the rating based on aesthetic_score
        (only if rating is currently 0 or None).
        """
        cursor.execute("PRAGMA table_info(Adobe_images)")
        columns = [row[1] for row in cursor.fetchall()]
        if 'rating' not in columns:
            return

        cursor.execute("SELECT rating FROM Adobe_images WHERE id_local = ?", (image_id,))
        row = cursor.fetchone()
        if row is None:
            return

        current_rating = row[0]
        if current_rating in (0, None):
            lr_rating = min(5, max(0, int(round(aesthetic_score / 2))))
            cursor.execute("UPDATE Adobe_images SET rating = ? WHERE id_local = ?", 
                           (lr_rating, image_id))
            logger.debug(f"Updated rating to {lr_rating} for image ID {image_id}")
        else:
            logger.debug(f"Skipping rating update; user rating is {current_rating}")

    def _update_caption_for_film_analysis(self, cursor, image_id: int, ai_metadata: Dict[str, Any]):
        """
        Insert or update the caption field with film analysis details, taxonomy, etc.
        """
        # Check for 'caption' column
        cursor.execute("PRAGMA table_info(Adobe_images)")
        adobe_images_columns = [row[1] for row in cursor.fetchall()]
        if 'caption' not in adobe_images_columns:
            return

        # Build text sections
        aesthetic_score = ai_metadata.get('aesthetic_score', 0)
        score_text = f"AI Aesthetic Score: {aesthetic_score:.1f}/10"

        # Extract taxonomy information
        taxonomy = ai_metadata.get('taxonomy', {})
        
        # Case-insensitive access to taxonomy keys
        vs_codes = []
        ic_codes = []
        ce_codes = []
        
        for key, value in taxonomy.items():
            if key.upper() == "VS":
                vs_codes = value
            elif key.upper() == "IC":
                ic_codes = value
            elif key.upper() == "CE":
                ce_codes = value

        # Build film analysis text
        film_analysis_text = ""
        if taxonomy:
            film_analysis_text = "\n\nFILM ANALYSIS:\n"
            
            # Film format
            film_format = []
            for code in ce_codes:
                code_upper = code.upper()
                if code_upper == "CE3.2.1":  # Square Format
                    film_format.append("120-6x6")
                elif code_upper == "CE3.2.2":  # Rectangular (3:2)
                    film_format.append("35mm")
                elif code_upper == "CE3.2.4":  # Panoramic
                    film_format.append("120-6x9")
            
            if film_format:
                film_analysis_text += f"Film Format: {', '.join(film_format)}\n"
            
            # Film characteristics
            film_chars = []
            for code in ic_codes:
                code_upper = code.upper()
                if code_upper == "IC2.1.1":  # Black & White
                    film_chars.append("black & white")
                elif code_upper == "IC2.1.3":  # Color Image
                    film_chars.append("color")
                
                if code_upper == "IC2.2.1":  # High Contrast
                    film_chars.append("high contrast")
                elif code_upper == "IC2.2.3":  # Low/Soft Contrast
                    film_chars.append("low contrast")
            
            if film_chars:
                film_analysis_text += f"Film Characteristics: {', '.join(film_chars)}\n"
            
            # Lens characteristics
            lens_chars = []
            for code in ic_codes:
                code_upper = code.upper()
                if code_upper == "IC2.3.1":  # All-in-focus/Deep Depth
                    lens_chars.append("deep depth of field")
                elif code_upper == "IC2.3.2":  # Selective Focus/Shallow Depth
                    lens_chars.append("shallow depth of field")
            
            if lens_chars:
                film_analysis_text += f"Lens Characteristics: {', '.join(lens_chars)}\n"

        # Extract detailed evaluation if available
        detailed_eval_text = ""
        if "detailed_evaluation" in ai_metadata and "overall_rating" in ai_metadata["detailed_evaluation"]:
            overall = ai_metadata["detailed_evaluation"]["overall_rating"]
            strengths = overall.get("main_strengths", "")
            weaknesses = overall.get("main_weaknesses", "")
            
            if strengths or weaknesses:
                detailed_eval_text = "\n\nDETAILED EVALUATION:\n"
                if strengths:
                    detailed_eval_text += f"Strengths: {strengths}\n"
                if weaknesses:
                    detailed_eval_text += f"Weaknesses: {weaknesses}\n"

        # Fetch existing caption
        cursor.execute("SELECT caption FROM Adobe_images WHERE id_local = ?", (image_id,))
        row = cursor.fetchone()
        existing_caption = row[0] if row else ""

        import re
        if existing_caption:
            new_caption = existing_caption

            # Update or add aesthetic score
            if re.search(r'AI Aesthetic Score:', new_caption):
                new_caption = re.sub(r'AI Aesthetic Score:.*?/10', score_text, new_caption)
            else:
                new_caption += f"\n\n{score_text}"

            # Update or add film analysis
            if 'FILM ANALYSIS:' in new_caption:
                if film_analysis_text:
                    new_caption = re.sub(
                        r'FILM ANALYSIS:.*?(?=\n\n|$)',
                        film_analysis_text.replace("\n\nFILM ANALYSIS:", "FILM ANALYSIS:"),
                        new_caption,
                        flags=re.DOTALL
                    )
                else:
                    new_caption = re.sub(r'\n\nFILM ANALYSIS:.*?(?=\n\n|$)', '', new_caption, flags=re.DOTALL)
            elif film_analysis_text:
                new_caption += film_analysis_text

            # Update or add detailed evaluation
            if 'DETAILED EVALUATION:' in new_caption:
                if detailed_eval_text:
                    new_caption = re.sub(
                        r'DETAILED EVALUATION:.*?(?=\n\n|$)',
                        detailed_eval_text.replace("\n\nDETAILED EVALUATION:", "DETAILED EVALUATION:"),
                        new_caption,
                        flags=re.DOTALL
                    )
                else:
                    new_caption = re.sub(r'\n\nDETAILED EVALUATION:.*?(?=\n\n|$)', '', new_caption, flags=re.DOTALL)
            elif detailed_eval_text:
                new_caption += detailed_eval_text

        else:
            # No existing caption -> create from scratch
            new_caption = f"{score_text}{film_analysis_text}{detailed_eval_text}"

        cursor.execute("UPDATE Adobe_images SET caption = ? WHERE id_local = ?", (new_caption, image_id))

    def _store_structured_metadata(self, cursor, image_id: int, ai_metadata: Dict[str, Any]):
        """
        Store the entire AI metadata in Adobe_additionalMetadata.externalEditingData as JSON.
        """
        if not ai_metadata:
            return

        try:
            cursor.execute("PRAGMA table_info(Adobe_additionalMetadata)")
            if not cursor.fetchone():
                # Table doesn't exist or is empty
                return

            cursor.execute("SELECT id_local FROM Adobe_additionalMetadata WHERE image = ?", (image_id,))
            row = cursor.fetchone()
            
            # Store the complete AI metadata including taxonomy and evaluations
            metadata_to_store = {
                "taxonomy": ai_metadata.get("taxonomy", {}),
                "aesthetic_score": ai_metadata.get("aesthetic_score", 0),
                "keywords": ai_metadata.get("keywords", []),
                "tags": ai_metadata.get("tags", [])
            }
            
            # Include detailed evaluation if available
            if "detailed_evaluation" in ai_metadata:
                metadata_to_store["detailed_evaluation"] = ai_metadata["detailed_evaluation"]
            
            # Include aesthetic evaluation if available
            if "aesthetic_evaluation" in ai_metadata:
                metadata_to_store["aesthetic_evaluation"] = ai_metadata["aesthetic_evaluation"]
            
            metadata_json = json.dumps(metadata_to_store)

            if row:
                cursor.execute(
                    "UPDATE Adobe_additionalMetadata SET externalEditingData = ? WHERE id_local = ?",
                    (metadata_json, row[0])
                )
            else:
                cursor.execute(
                    "INSERT INTO Adobe_additionalMetadata (image, externalEditingData) VALUES (?, ?)",
                    (image_id, metadata_json)
                )
        except sqlite3.Error as meta_err:
            logger.debug(f"Could not store structured metadata for image {image_id}: {str(meta_err)}")

    def update_image_metadata(self, image_id: int, ai_metadata: Dict[str, Any]) -> bool:
        """
        Update Lightroom catalog with AI-generated metadata (keywords, tags, taxonomy, evaluations).
        """
        if not ai_metadata:
            return False

        aesthetic_score = ai_metadata.get('aesthetic_score', 0)

        try:
            # Use a higher retry count for metadata updates
            with self.cursor(retries=5) as cursor:
                # 1) Keywords
                self._apply_keywords(cursor, image_id, ai_metadata)

                # 2) Aesthetic score
                self._apply_aesthetic_score(cursor, image_id, aesthetic_score)

                # 3) Caption (film analysis, taxonomy, etc.)
                self._update_caption_for_film_analysis(cursor, image_id, ai_metadata)

                # 4) JSON metadata in Adobe_additionalMetadata
                self._store_structured_metadata(cursor, image_id, ai_metadata)

            return True

        except sqlite3.Error as e:
            logger.error(f"Failed to update metadata for image {image_id}: {str(e)}")
            return False
