"""
Batch processing and parallelization for Lightroom images.
"""

import gc
import threading
import time
import logging
import os
import psutil
from typing import List, Tuple, Dict, Any, Optional, Set
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field

from .config import AppConfig
from .catalog_db import CatalogDatabase
from .preview_extractor import PreviewExtractor
from .image_processor import ImageProcessor
from .ai_providers import AiProvider
from .checkpoint_manager import CheckpointManager
from .logging_setup import get_logger

logger = get_logger(__name__)


@dataclass
class ProcessingStats:
    """Class to track processing statistics."""
    total_images: int = 0
    processed_images: int = 0
    successful_images: int = 0
    failed_images: int = 0
    skipped_images: int = 0
    start_time: float = 0
    total_time: float = 0
    preview_found_count: int = 0
    preview_extract_failures: int = 0
    ai_call_failures: int = 0
    db_update_failures: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert stats to dictionary."""
        result = {k: v for k, v in self.__dict__.items()}
        if self.total_images > 0:
            result['success_rate'] = self.successful_images / self.total_images
        # Always include avg_time_per_image, defaulting to 0 if no processing has occurred
        if self.processed_images > 0:
            result['avg_time_per_image'] = self.total_time / self.processed_images
        else:
            result['avg_time_per_image'] = 0
        return result


class BatchProcessor:
    """Class to handle batch processing of images."""
    
    def __init__(self, catalog_path: str, config: AppConfig):
        """
        Initialize the batch processor.
        
        Args:
            catalog_path: Path to the Lightroom catalog file
            config: Application configuration
        """
        self.catalog_path = catalog_path
        self.config = config
        self.batch_size = config.batch_size
        self.max_workers = config.max_workers
        
        # Initialize components
        self.db = CatalogDatabase(catalog_path, config)
        self.preview_extractor = PreviewExtractor(catalog_path, config)
        self.image_processor = ImageProcessor(config)
        self.ai_provider = AiProvider.get_provider(config)
        
        # Get database info and optimize search strategies
        db_info = self.db.analyze_database_structure()
        self.preview_extractor.optimize_search_strategies(db_info)
        
        # Initialize checkpoint manager if enabled
        if config.use_checkpoint:
            self.checkpoint_manager = CheckpointManager(f"{catalog_path}.checkpoint.json", config)
        else:
            self.checkpoint_manager = None
            
        # Store stats
        self.stats = ProcessingStats()
        self.stats_lock = threading.RLock()
        
        # Add a thread-local storage for database connections
        self.thread_local = threading.local()
        
    def _get_thread_db(self):
        """Get a thread-local database connection."""
        if not hasattr(self.thread_local, 'db'):
            # Create a new database connection for this thread
            self.thread_local.db = CatalogDatabase(self.catalog_path, self.config)
        return self.thread_local.db
        
    def process_image(self, image_data: Tuple) -> Dict[str, Any]:
        """
        Process a single image: extract preview, call AI, update metadata.

        Args:
            image_data: Tuple containing image information
    
        Returns:
            Dictionary with processing results
        """
        image_id = image_data[0]
        base_name = image_data[2]
        
        result = {
            'image_id': image_id,
            'base_name': base_name,
            'success': False,
            'stage': 'init',
            'error': None
        }

        img = None  # Initialize img to None to avoid UnboundLocalError in finally block

        try:
            logger.debug(f"Processing image: {base_name} (ID: {image_id})")
    
            # 1) Locate preview
            preview_path = self.preview_extractor.locate_preview_file(image_data)
            if not preview_path:
                result['stage'] = 'locate_preview'
                result['error'] = 'No preview found'
                logger.warning(f"No preview found for {base_name} (ID: {image_id})")
                return result
                
            result['preview_path'] = preview_path
            
            with self.stats_lock:
                self.stats.preview_found_count += 1
    
            # 2) Extract JPEG
            img = self.preview_extractor.extract_jpeg_from_preview(preview_path)
            if not img:
                result['stage'] = 'extract_preview'
                result['error'] = 'Failed to extract preview'
                logger.warning(f"Failed to extract preview for {base_name} (ID: {image_id})")
                with self.stats_lock:
                    self.stats.preview_extract_failures += 1
                return result
                
            result['preview_dimensions'] = (img.width, img.height)
    
            # 3) Prepare image for AI
            img_b64, img_dimensions = self.image_processor.process_image(img)
            img.close()  # free memory
            img = None  # Set to None after closing to avoid double-close in finally block
            
            if not img_b64:
                result['stage'] = 'process_image'
                result['error'] = 'Failed to prepare image for AI'
                logger.warning(f"Failed to prepare image for AI: {base_name} (ID: {image_id})")
                return result
                
            result['processed_dimensions'] = img_dimensions
    
            # 4) Call AI service
            ai_metadata = self.ai_provider.analyze_image(img_b64)
            if not ai_metadata:
                result['stage'] = 'ai_analysis'
                result['error'] = 'Failed to get AI metadata'
                logger.warning(f"Failed to get AI metadata for {base_name} (ID: {image_id})")
                with self.stats_lock:
                    self.stats.ai_call_failures += 1
                return result
                
            result['ai_metadata'] = ai_metadata
    
            # 5) Create a thread-local database connection for metadata update
            thread_db = self._get_thread_db()
            try:
                success = thread_db.update_image_metadata(image_id, ai_metadata)
                if not success:
                    result['stage'] = 'db_update'
                    result['error'] = 'Failed to update database'
                    logger.warning(f"Failed to update metadata for {base_name} (ID: {image_id})")
                    with self.stats_lock:
                        self.stats.db_update_failures += 1
                    return result
            except Exception as e:
                result['stage'] = 'db_update'
                result['error'] = f'Database error: {str(e)}'
                logger.error(f"Database error updating metadata for {base_name}: {str(e)}")
                with self.stats_lock:
                    self.stats.db_update_failures += 1
                return result
    
            result['success'] = True
            result['stage'] = 'complete'
            logger.info(f"Successfully processed {base_name} (ID: {image_id})")
            return result
        
        except Exception as e:
            result['stage'] = 'exception'
            result['error'] = str(e)
            logger.error(f"Error processing {base_name} (ID: {image_id}): {str(e)}")
            if self.config.debug_mode:
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
            return result
        finally:
            # Ensure resources are properly cleaned up
            if img is not None:
                try:
                    img.close()
                except:
                    pass
            
    def process_batch(self, images_batch: List[Tuple]) -> List[Dict[str, Any]]:
        """
        Process a batch of images with optional parallelization.
    
        Args:
            images_batch: List of image data tuples
        
        Returns:
            List of processing result dictionaries
        """
        if self.max_workers > 1:
            # Parallel processing with proper thread initialization
            with ThreadPoolExecutor(max_workers=self.max_workers, 
                                   thread_name_prefix="ImgProc") as executor:
                # Submit all tasks
                future_to_image = {
                    executor.submit(self.process_image, img): img 
                    for img in images_batch
                }
                
                # Process results as they complete
                results = []
                for future in as_completed(future_to_image):
                    img = future_to_image[future]
                    try:
                        result = future.result()
                        results.append(result)
                    except Exception as e:
                        # Handle any unexpected exceptions from the executor
                        image_id = img[0] if img else "unknown"
                        base_name = img[2] if img and len(img) > 2 else "unknown"
                        logger.error(f"Executor exception for {base_name} (ID: {image_id}): {str(e)}")
                        results.append({
                            'image_id': image_id,
                            'base_name': base_name,
                            'success': False,
                            'stage': 'executor_exception',
                            'error': str(e)
                        })
                
                return results
        else:
            # Sequential processing
            results = []
            for img in images_batch:
                result = self.process_image(img)
                results.append(result)
        
            return results
        
    def run(self, images: Optional[List[Tuple]] = None) -> Dict[str, Any]:
        """
        Process all images, handling batching, checkpointing, and statistics.
    
        Args:
            images: Optional list of images to process (if None, fetches from catalog)
        
        Returns:
            Dictionary with processing statistics
        """
        self.stats = ProcessingStats()
        self.stats.start_time = time.time()
    
        # Get images from catalog if not provided
        if images is None:
            images = self.db.get_images(self.config.max_images)
    
        # Get already processed images from the database
        already_processed_ids = self.db.get_processed_images()
    
        # Get processed IDs from checkpoint if enabled
        checkpoint_processed_ids = set()
        if self.checkpoint_manager:
            checkpoint_processed_ids = self.checkpoint_manager.load_checkpoint()
            logger.info(f"Loaded checkpoint with {len(checkpoint_processed_ids)} images")
    
        # Combine both sources of processed IDs
        processed_ids = already_processed_ids.union(checkpoint_processed_ids)
        logger.info(f"Total {len(processed_ids)} already processed images identified")
    
        if processed_ids:
            original_count = len(images)
            images = [img for img in images if img[0] not in processed_ids]
            skipped_count = original_count - len(images)
            with self.stats_lock:
                self.stats.skipped_images = skipped_count
            logger.info(f"Skipping {skipped_count} already-processed images")
    
        total_images = len(images)
        with self.stats_lock:
            self.stats.total_images = total_images
    
        if total_images == 0:
            logger.info("No images to process")
            return self.stats.to_dict()
    
        # Process in batches
        successful = 0
        processed_count = 0
        batch_start_time = time.time()
        
        for i in range(0, total_images, self.batch_size):
            batch = images[i:i + self.batch_size]
            batch_num = i // self.batch_size + 1
            total_batches = (total_images + self.batch_size - 1) // self.batch_size
            
            logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} images)")
            results = self.process_batch(batch)
            
            # Process results
            batch_success = sum(1 for r in results if r['success'])
            successful += batch_success
            
            with self.stats_lock:
                self.stats.processed_images += len(batch)
                self.stats.successful_images += batch_success
                self.stats.failed_images += len(batch) - batch_success
            
            # Update checkpoint
            if self.checkpoint_manager:
                for result in results:
                    if result['success']:
                        processed_ids.add(result['image_id'])
                
                if batch_num % self.config.checkpoint_interval == 0:
                    self.checkpoint_manager.save_checkpoint(processed_ids)
                    logger.info(f"Checkpoint saved ({len(processed_ids)} total processed)")
            
            # Calculate batch timing
            batch_end_time = time.time()
            batch_duration = batch_end_time - batch_start_time
            images_per_second = len(batch) / batch_duration if batch_duration > 0 else 0
            
            logger.info(
                f"Batch {batch_num} done: {batch_success}/{len(batch)} succeeded "
                f"({batch_duration:.1f}s, {images_per_second:.2f} img/sec)"
            )
            
            # Update processed count
            processed_count += len(batch)
            
            # Log progress and statistics
            self._log_progress_stats(processed_count, total_images)
            
            # Memory management
            gc.collect()
            self._check_memory_usage()
            
            # Reset for next batch
            batch_start_time = time.time()
        
        # Final checkpoint
        if self.checkpoint_manager:
            self.checkpoint_manager.save_checkpoint(processed_ids)
            logger.info(f"Final checkpoint saved ({len(processed_ids)} total processed)")
        
        # Update final statistics
        total_time = time.time() - self.stats.start_time
        with self.stats_lock:
            self.stats.total_time = total_time
        
        logger.info(
            f"Completed: {successful}/{total_images} images processed successfully "
            f"in {total_time:.1f}s ({total_time / total_images:.2f}s per image)"
        )
        
        # Log detailed statistics
        self._log_detailed_stats()
        
        return self.stats.to_dict()
        
    def _log_progress_stats(self, images_processed: int, total_images: int) -> None:
        """
        Log progress statistics.
        
        Args:
            images_processed: Number of images processed so far
            total_images: Total number of images to process
        """
        elapsed = time.time() - self.stats.start_time
        avg_time_per_image = elapsed / images_processed if images_processed else 0
        estimated_remaining = avg_time_per_image * (total_images - images_processed)
        
        # Calculate ETA
        eta_seconds = int(estimated_remaining)
        eta_str = time.strftime('%H:%M:%S', time.gmtime(eta_seconds))
        
        logger.info(
            f"Progress: {images_processed}/{total_images} "
            f"({images_processed / total_images * 100:.1f}%)"
        )
        logger.info(
            f"Time elapsed: {elapsed:.1f}s, est. remaining: {estimated_remaining:.1f}s (ETA: {eta_str}), "
            f"avg: {avg_time_per_image:.2f}s/image"
        )
    
    def _log_detailed_stats(self) -> None:
        """Log detailed statistics about the processing run."""
        with self.stats_lock:
            stats = self.stats
            
            # Calculate derived statistics
            success_rate = stats.successful_images / stats.total_images if stats.total_images > 0 else 0
            preview_found_rate = stats.preview_found_count / stats.processed_images if stats.processed_images > 0 else 0
            
            logger.info("=== Processing Statistics ===")
            logger.info(f"Total images: {stats.total_images}")
            logger.info(f"Processed: {stats.processed_images}")
            logger.info(f"Successful: {stats.successful_images} ({success_rate:.1%})")
            logger.info(f"Failed: {stats.failed_images}")
            logger.info(f"Skipped: {stats.skipped_images}")
            logger.info(f"Preview found: {stats.preview_found_count} ({preview_found_rate:.1%})")
            logger.info(f"Preview extraction failures: {stats.preview_extract_failures}")
            logger.info(f"AI call failures: {stats.ai_call_failures}")
            logger.info(f"Database update failures: {stats.db_update_failures}")
            logger.info(f"Total time: {stats.total_time:.1f}s")
            
            # Log cache statistics from preview extractor
            cache_stats = self.preview_extractor.get_cache_stats()
            logger.info(f"Preview cache: {cache_stats['size']} entries, {cache_stats['hit_rate']:.1%} hit rate")
        
    def _check_memory_usage(self) -> None:
        """Check memory usage and clear caches if needed."""
        if self.config.memory_limit_mb:
            try:
                process = psutil.Process(os.getpid())
                mem_mb = process.memory_info().rss / 1024 / 1024
                logger.debug(f"Current memory usage: {mem_mb:.1f} MB")
                
                if mem_mb > self.config.memory_limit_mb * 0.8:
                    logger.warning(f"Memory usage high ({mem_mb:.1f} MB), clearing caches")
                    self.preview_extractor.clear_cache()
                    gc.collect()
                    
                    # Log new memory usage after cleanup
                    new_mem_mb = process.memory_info().rss / 1024 / 1024
                    logger.info(f"Memory usage after cleanup: {new_mem_mb:.1f} MB (freed {mem_mb - new_mem_mb:.1f} MB)")
            except Exception as e:
                logger.debug(f"Error checking memory usage: {str(e)}")
