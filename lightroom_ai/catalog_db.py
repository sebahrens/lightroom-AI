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

            # Visual Subject hierarchy
            for code in vs_codes:
                code_upper = code.upper()
                if code_upper.startswith("VS1"):  # People
                    all_keywords.append("People")
                    if code_upper.startswith("VS1.1"):  # Individual Portrait
                        all_keywords.append(f"People{delimiter}Portrait")
                        if code_upper == "VS1.1.1":
                            all_keywords.append(f"People{delimiter}Portrait{delimiter}Close-up")
                        elif code_upper == "VS1.1.2":
                            all_keywords.append(f"People{delimiter}Portrait{delimiter}Half-body")
                        elif code_upper == "VS1.1.3":
                            all_keywords.append(f"People{delimiter}Portrait{delimiter}Full-body")
                    elif code_upper.startswith("VS1.2"):  # Group
                        all_keywords.append(f"People{delimiter}Group")
                    elif code_upper.startswith("VS1.3"):  # Human Activity
                        all_keywords.append(f"People{delimiter}Activity")
                
                elif code_upper.startswith("VS2"):  # Place
                    all_keywords.append("Place")
                    if code_upper.startswith("VS2.1"):  # Natural Environment
                        all_keywords.append(f"Place{delimiter}Natural")
                    elif code_upper.startswith("VS2.2"):  # Built Environment
                        all_keywords.append(f"Place{delimiter}Built")
                
                elif code_upper.startswith("VS3"):  # Objects
                    all_keywords.append("Objects")
                    if code_upper.startswith("VS3.1"):  # Natural Objects
                        all_keywords.append(f"Objects{delimiter}Natural")
                    elif code_upper.startswith("VS3.2"):  # Manufactured Objects
                        all_keywords.append(f"Objects{delimiter}Manufactured")

            # Image Characteristics hierarchy
            for code in ic_codes:
                code_upper = code.upper()
                if code_upper.startswith("IC2.1"):  # Tonality
                    if code_upper == "IC2.1.1":  # Black & White
                        all_keywords.append(f"Style{delimiter}Black & White")
                    elif code_upper == "IC2.1.2":  # Monochrome
                        all_keywords.append(f"Style{delimiter}Monochrome")
                
                elif code_upper.startswith("IC3.1"):  # Color Temperature
                    all_keywords.append("Color")
                    if code_upper == "IC3.1.1":  # Warm Tones
                        all_keywords.append(f"Color{delimiter}Warm")
                    elif code_upper == "IC3.1.2":  # Cool Tones
                        all_keywords.append(f"Color{delimiter}Cool")

            # Contextual Elements hierarchy
            for code in ce_codes:
                code_upper = code.upper()
                if code_upper.startswith("CE1.2"):  # Time of Day
                    all_keywords.append("Time")
                    if code_upper == "CE1.2.3":  # Golden Hour
                        all_keywords.append(f"Time{delimiter}Golden Hour")
                    elif code_upper == "CE1.2.4":  # Blue Hour
                        all_keywords.append(f"Time{delimiter}Blue Hour")
                    elif code_upper == "CE1.2.5":  # Night
                        all_keywords.append(f"Time{delimiter}Night")
                
                elif code_upper.startswith("CE3.3"):  # Photographic Genre
                    all_keywords.append("Genre")
                    if code_upper == "CE3.3.1":  # Documentary
                        all_keywords.append(f"Genre{delimiter}Documentary")
                    elif code_upper == "CE3.3.2":  # Street Photography
                        all_keywords.append(f"Genre{delimiter}Street")
                    elif code_upper == "CE3.3.3":  # Fine Art
                        all_keywords.append(f"Genre{delimiter}Fine Art")

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
            with self.cursor() as cursor:
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
