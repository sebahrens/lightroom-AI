"""
Database interaction with Lightroom catalog.
"""

import os
import sqlite3
import logging
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

    def _connect(self):
        """
        Establish a connection to the SQLite database.
        Creates a new connection for each thread to ensure thread safety.
        """
        try:
            conn = sqlite3.connect(self.catalog_path, isolation_level=None)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            # 30 second busy_timeout to reduce locking errors
            conn.execute("PRAGMA busy_timeout=30000")
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
    def cursor(self):
        """
        Get a cursor as a context manager, ensuring proper cleanup.
        Each call opens a new connection; commits or rolls back, then closes.
        """
        conn = self._connect()
        conn.execute("BEGIN DEFERRED")
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

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
        """
        keywords = ai_metadata.get('keywords', [])
        tags = ai_metadata.get('tags', [])
        categories = ai_metadata.get('categories', {})
        aesthetic_score = ai_metadata.get('aesthetic_score', 0)

        all_keywords = keywords + tags + ["AI_Processed"]

        # Also add the aesthetic score as a keyword (e.g. "AI_Score_7.5")
        score_keyword = f"AI_Score_{aesthetic_score:.1f}"
        all_keywords.append(score_keyword)

        # If hierarchical keywords are enabled, add them
        if self.use_hierarchical_keywords and categories:
            delimiter = self.keyword_delimiter

            # Film format
            if 'film_format' in categories and categories['film_format']:
                film_format = categories['film_format'][0]
                if film_format:
                    all_keywords.append(f"Film{delimiter}Format{delimiter}{film_format}")

            # Film characteristics
            if 'film_characteristics' in categories and categories['film_characteristics']:
                for value in categories['film_characteristics']:
                    all_keywords.append(f"Film{delimiter}Characteristics{delimiter}{value}")

            # Lens
            if 'lens_characteristics' in categories and categories['lens_characteristics']:
                all_keywords.append("Lens")
                for value in categories['lens_characteristics']:
                    all_keywords.append(f"Lens{delimiter}{value}")
            
            # Focal length
            if 'focal_length_estimate' in categories and categories['focal_length_estimate']:
                for value in categories['focal_length_estimate']:
                    all_keywords.append(f"Lens{delimiter}FocalLength{delimiter}{value}")

            # Aperture
            if 'aperture_evidence' in categories and categories['aperture_evidence']:
                for value in categories['aperture_evidence']:
                    all_keywords.append(f"Lens{delimiter}Aperture{delimiter}{value}")

            # Standard categories: content_type, main_subject, lighting, etc.
            for cat_type in ['content_type','main_subject','lighting','color','mood','style']:
                if cat_type in categories and categories[cat_type]:
                    cat_display = cat_type.replace('_',' ').title()
                    all_keywords.append(cat_display)
                    for val in categories[cat_type]:
                        all_keywords.append(f"{cat_display}{delimiter}{val}")

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

    def _update_caption_for_film_analysis(self, cursor, image_id: int, categories: Dict[str, Any], aesthetic_score: float):
        """
        Insert or update the caption field with film analysis details, standard categories, etc.
        """
        if not categories:
            return

        # Check for 'caption' column
        cursor.execute("PRAGMA table_info(Adobe_images)")
        adobe_images_columns = [row[1] for row in cursor.fetchall()]
        if 'caption' not in adobe_images_columns:
            return

        # Build text sections
        score_text = f"AI Aesthetic Score: {aesthetic_score:.1f}/10"

        film_analysis_text = ""
        film_categories = ['film_format','film_characteristics','lens_characteristics','focal_length_estimate','aperture_evidence']
        film_details = {}
        for cat in film_categories:
            if cat in categories and categories[cat]:
                film_details[cat] = categories[cat]

        if film_details:
            film_analysis_text = "\n\nFILM ANALYSIS:\n"
            if 'film_format' in film_details:
                film_analysis_text += f"Film Format: {', '.join(film_details['film_format'])}\n"
            if 'film_characteristics' in film_details:
                film_analysis_text += f"Film Characteristics: {', '.join(film_details['film_characteristics'])}\n"
            if 'lens_characteristics' in film_details:
                film_analysis_text += f"Lens Characteristics: {', '.join(film_details['lens_characteristics'])}\n"
            if 'focal_length_estimate' in film_details:
                film_analysis_text += f"Focal Length: {', '.join(film_details['focal_length_estimate'])}\n"
            if 'aperture_evidence' in film_details:
                film_analysis_text += f"Aperture/DOF: {', '.join(film_details['aperture_evidence'])}\n"

        # Standard categories
        standard_categories = ['content_type','main_subject','lighting','color','mood','style']
        cat_entries = []
        for cat_type in standard_categories:
            if cat_type in categories and categories[cat_type]:
                cat_name = cat_type.replace('_',' ').title()
                cat_entries.append(f"{cat_name}: {', '.join(categories[cat_type])}")
        categories_text = ""
        if cat_entries:
            categories_text = "\n\nCategories:\n" + "\n".join(cat_entries)

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

            # Update or add categories
            if 'Categories:' in new_caption:
                if categories_text:
                    new_caption = re.sub(
                        r'Categories:.*?(?=\n\n|$)',
                        categories_text.replace("\n\nCategories:", "Categories:"),
                        new_caption,
                        flags=re.DOTALL
                    )
                else:
                    new_caption = re.sub(r'\n\nCategories:.*?(?=\n\n|$)', '', new_caption, flags=re.DOTALL)
            elif categories_text:
                new_caption += categories_text

        else:
            # No existing caption -> create from scratch
            new_caption = f"{score_text}{film_analysis_text}{categories_text}"

        cursor.execute("UPDATE Adobe_images SET caption = ? WHERE id_local = ?", (new_caption, image_id))

    def _store_structured_metadata(self, cursor, image_id: int, categories: Dict[str, Any]):
        """
        Store the entire categories dict in Adobe_additionalMetadata.externalEditingData as JSON (if possible).
        """
        if not categories:
            return

        try:
            cursor.execute("PRAGMA table_info(Adobe_additionalMetadata)")
            if not cursor.fetchone():
                # Table doesn't exist or is empty
                return

            cursor.execute("SELECT id_local FROM Adobe_additionalMetadata WHERE image = ?", (image_id,))
            row = cursor.fetchone()
            metadata_json = json.dumps(categories)

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
        Update Lightroom catalog with AI-generated metadata (keywords, tags, film analysis).
        
        Splits the logic into sub-methods:
            _apply_keywords(...)
            _apply_aesthetic_score(...)
            _update_caption_for_film_analysis(...)
            _store_structured_metadata(...)
        """
        if not ai_metadata:
            return False

        categories = ai_metadata.get('categories', {})
        aesthetic_score = ai_metadata.get('aesthetic_score', 0)

        try:
            with self.cursor() as cursor:
                # 1) Keywords
                self._apply_keywords(cursor, image_id, ai_metadata)

                # 2) Aesthetic score
                self._apply_aesthetic_score(cursor, image_id, aesthetic_score)

                # 3) Caption (film analysis, categories, etc.)
                self._update_caption_for_film_analysis(cursor, image_id, categories, aesthetic_score)

                # 4) JSON metadata in Adobe_additionalMetadata
                self._store_structured_metadata(cursor, image_id, categories)

            return True

        except sqlite3.Error as e:
            logger.error(f"Failed to update metadata for image {image_id}: {str(e)}")
            return False
