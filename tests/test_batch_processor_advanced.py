import os
import unittest
from unittest.mock import patch, MagicMock, mock_open
import tempfile
import shutil
import json
import threading
import time  # Added import for time module
from concurrent.futures import ThreadPoolExecutor

from lightroom_ai.config import AppConfig
from lightroom_ai.batch_processor import BatchProcessor, ProcessingStats


class TestBatchProcessorAdvanced(unittest.TestCase):
    """Advanced test cases for the BatchProcessor class."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        
        # Create a mock catalog path
        self.catalog_path = os.path.join(self.temp_dir, "test_catalog.lrcat")
        with open(self.catalog_path, 'w') as f:
            f.write("mock catalog")
        
        # Create a basic config
        self.config = AppConfig()
        self.config.batch_size = 2
        self.config.max_workers = 2
        self.config.max_images = 10
        self.config.use_checkpoint = True
        self.config.checkpoint_interval = 1
        self.config.memory_limit_mb = 1000
        self.config.debug_mode = True
        
        # Create mocks for dependencies
        self.mock_db = MagicMock()
        self.mock_preview_extractor = MagicMock()
        self.mock_image_processor = MagicMock()
        self.mock_ai_provider = MagicMock()
        self.mock_checkpoint_manager = MagicMock()
        
        # Create test images
        self.test_images = [
            (1, 101, "image1.jpg", "path/to", "/root", "global1", "file_global1"),
            (2, 102, "image2.jpg", "path/to", "/root", "global2", "file_global2"),
            (3, 103, "image3.jpg", "path/to", "/root", "global3", "file_global3"),
            (4, 104, "image4.jpg", "path/to", "/root", "global4", "file_global4"),
            (5, 105, "image5.jpg", "path/to", "/root", "global5", "file_global5")
        ]
        
        # Set up the mock database to return test images
        self.mock_db.get_images.return_value = self.test_images
        self.mock_db.get_processed_images.return_value = set([3])  # Image 3 already processed
        self.mock_db.analyze_database_structure.return_value = {"has_id_global": True}
        
        # Set up the mock checkpoint manager
        self.mock_checkpoint_manager.load_checkpoint.return_value = set([4])  # Image 4 in checkpoint
        
        # Set up cache stats for preview extractor
        self.mock_preview_extractor.get_cache_stats.return_value = {
            'size': 3,
            'hits': 2,
            'misses': 1,
            'hit_rate': 0.67
        }
        
        # Create patches for the dependencies
        self.db_patcher = patch('lightroom_ai.batch_processor.CatalogDatabase', return_value=self.mock_db)
        self.preview_patcher = patch('lightroom_ai.batch_processor.PreviewExtractor', return_value=self.mock_preview_extractor)
        self.image_patcher = patch('lightroom_ai.batch_processor.ImageProcessor', return_value=self.mock_image_processor)
        self.ai_patcher = patch('lightroom_ai.batch_processor.AiProvider')
        self.checkpoint_patcher = patch('lightroom_ai.batch_processor.CheckpointManager', return_value=self.mock_checkpoint_manager)
        
        # Start the patches
        self.mock_db_class = self.db_patcher.start()
        self.mock_preview_class = self.preview_patcher.start()
        self.mock_image_class = self.image_patcher.start()
        self.mock_ai_class = self.ai_patcher.start()
        self.mock_checkpoint_class = self.checkpoint_patcher.start()
        
        # Configure AI provider
        self.mock_ai_class.get_provider.return_value = self.mock_ai_provider
        
        # Create the batch processor
        self.processor = BatchProcessor(self.catalog_path, self.config)
        
    def tearDown(self):
        """Clean up after tests."""
        # Stop the patches
        self.db_patcher.stop()
        self.preview_patcher.stop()
        self.image_patcher.stop()
        self.ai_patcher.stop()
        self.checkpoint_patcher.stop()
        
        # Remove the temporary directory and its contents
        shutil.rmtree(self.temp_dir)
        
    def test_init(self):
        """Test initialization of BatchProcessor."""
        self.assertEqual(self.processor.catalog_path, self.catalog_path)
        self.assertEqual(self.processor.config, self.config)
        self.assertEqual(self.processor.batch_size, self.config.batch_size)
        self.assertEqual(self.processor.max_workers, self.config.max_workers)
        
        # Check that dependencies were initialized
        self.mock_db_class.assert_called_once_with(self.catalog_path, self.config)
        self.mock_preview_class.assert_called_once_with(self.catalog_path, self.config)
        self.mock_image_class.assert_called_once_with(self.config)
        self.mock_ai_class.get_provider.assert_called_once_with(self.config)
        self.mock_checkpoint_class.assert_called_once_with(f"{self.catalog_path}.checkpoint.json", self.config)
        
        # Check that search strategies were optimized
        self.mock_db.analyze_database_structure.assert_called_once()
        self.mock_preview_extractor.optimize_search_strategies.assert_called_once_with({"has_id_global": True})
        
    def test_get_thread_db(self):
        """Test getting thread-local database connection."""
        # First call should create a new connection
        thread_db = self.processor._get_thread_db()
        self.assertEqual(thread_db, self.mock_db)
        
        # Second call should return the same connection
        thread_db2 = self.processor._get_thread_db()
        self.assertEqual(thread_db2, self.mock_db)
        
        # Call from another thread should create a new connection
        def thread_func():
            thread_db3 = self.processor._get_thread_db()
            self.assertEqual(thread_db3, self.mock_db)
            
        thread = threading.Thread(target=thread_func)
        thread.start()
        thread.join()
        
        # Check that a new database connection was created for the thread
        self.assertEqual(self.mock_db_class.call_count, 2)
        
    def test_process_image_success(self):
        """Test processing an image successfully."""
        # Set up mocks for successful processing
        self.mock_preview_extractor.locate_preview_file.return_value = "preview_path"
        mock_img = MagicMock()
        mock_img.width = 100
        mock_img.height = 100
        mock_img.close = MagicMock()
        self.mock_preview_extractor.extract_jpeg_from_preview.return_value = mock_img
        self.mock_image_processor.process_image.return_value = ("base64_image", (100, 100))
        self.mock_ai_provider.analyze_image.return_value = {"keywords": ["test"]}
        self.mock_db.update_image_metadata.return_value = True
        
        # Process an image
        image_data = self.test_images[0]
        result = self.processor.process_image(image_data)
        
        # Check the result
        self.assertTrue(result['success'])
        self.assertEqual(result['stage'], 'complete')
        self.assertEqual(result['image_id'], image_data[0])
        self.assertEqual(result['base_name'], image_data[2])
        self.assertEqual(result['preview_path'], "preview_path")
        self.assertEqual(result['preview_dimensions'], (100, 100))
        self.assertEqual(result['processed_dimensions'], (100, 100))
        self.assertEqual(result['ai_metadata'], {"keywords": ["test"]})
        
        # Check that the methods were called correctly
        self.mock_preview_extractor.locate_preview_file.assert_called_once_with(image_data)
        self.mock_preview_extractor.extract_jpeg_from_preview.assert_called_once_with("preview_path")
        self.mock_image_processor.process_image.assert_called_once_with(mock_img)
        self.mock_ai_provider.analyze_image.assert_called_once_with("base64_image")
        self.mock_db.update_image_metadata.assert_called_once_with(image_data[0], {"keywords": ["test"]})
        mock_img.close.assert_called_once()
        
    def test_process_image_no_preview(self):
        """Test processing an image with no preview."""
        # Set up mocks for no preview
        self.mock_preview_extractor.locate_preview_file.return_value = None
        
        # Process an image
        image_data = self.test_images[0]
        result = self.processor.process_image(image_data)
        
        # Check the result
        self.assertFalse(result['success'])
        self.assertEqual(result['stage'], 'locate_preview')
        self.assertEqual(result['error'], 'No preview found')
        
        # Check that only the locate_preview_file method was called
        self.mock_preview_extractor.locate_preview_file.assert_called_once_with(image_data)
        self.mock_preview_extractor.extract_jpeg_from_preview.assert_not_called()
        self.mock_image_processor.process_image.assert_not_called()
        self.mock_ai_provider.analyze_image.assert_not_called()
        self.mock_db.update_image_metadata.assert_not_called()
        
    def test_process_image_extract_failure(self):
        """Test processing an image with extract failure."""
        # Set up mocks for extract failure
        self.mock_preview_extractor.locate_preview_file.return_value = "preview_path"
        self.mock_preview_extractor.extract_jpeg_from_preview.return_value = None
        
        # Process an image
        image_data = self.test_images[0]
        result = self.processor.process_image(image_data)
        
        # Check the result
        self.assertFalse(result['success'])
        self.assertEqual(result['stage'], 'extract_preview')
        self.assertEqual(result['error'], 'Failed to extract preview')
        
        # Check that the methods were called correctly
        self.mock_preview_extractor.locate_preview_file.assert_called_once_with(image_data)
        self.mock_preview_extractor.extract_jpeg_from_preview.assert_called_once_with("preview_path")
        self.mock_image_processor.process_image.assert_not_called()
        self.mock_ai_provider.analyze_image.assert_not_called()
        self.mock_db.update_image_metadata.assert_not_called()
        
    def test_process_image_ai_failure(self):
        """Test processing an image with AI failure."""
        # Set up mocks for AI failure
        self.mock_preview_extractor.locate_preview_file.return_value = "preview_path"
        mock_img = MagicMock()
        mock_img.width = 100
        mock_img.height = 100
        mock_img.close = MagicMock()
        self.mock_preview_extractor.extract_jpeg_from_preview.return_value = mock_img
        self.mock_image_processor.process_image.return_value = ("base64_image", (100, 100))
        self.mock_ai_provider.analyze_image.return_value = None
        
        # Process an image
        image_data = self.test_images[0]
        result = self.processor.process_image(image_data)
        
        # Check the result
        self.assertFalse(result['success'])
        self.assertEqual(result['stage'], 'ai_analysis')
        self.assertEqual(result['error'], 'Failed to get AI metadata')
        
        # Check that the methods were called correctly
        self.mock_preview_extractor.locate_preview_file.assert_called_once_with(image_data)
        self.mock_preview_extractor.extract_jpeg_from_preview.assert_called_once_with("preview_path")
        self.mock_image_processor.process_image.assert_called_once_with(mock_img)
        self.mock_ai_provider.analyze_image.assert_called_once_with("base64_image")
        self.mock_db.update_image_metadata.assert_not_called()
        mock_img.close.assert_called_once()
        
    def test_process_image_db_failure(self):
        """Test processing an image with database update failure."""
        # Set up mocks for database update failure
        self.mock_preview_extractor.locate_preview_file.return_value = "preview_path"
        mock_img = MagicMock()
        mock_img.width = 100
        mock_img.height = 100
        mock_img.close = MagicMock()
        self.mock_preview_extractor.extract_jpeg_from_preview.return_value = mock_img
        self.mock_image_processor.process_image.return_value = ("base64_image", (100, 100))
        self.mock_ai_provider.analyze_image.return_value = {"keywords": ["test"]}
        self.mock_db.update_image_metadata.return_value = False
        
        # Process an image
        image_data = self.test_images[0]
        result = self.processor.process_image(image_data)
        
        # Check the result
        self.assertFalse(result['success'])
        self.assertEqual(result['stage'], 'db_update')
        self.assertEqual(result['error'], 'Failed to update database')
        
        # Check that the methods were called correctly
        self.mock_preview_extractor.locate_preview_file.assert_called_once_with(image_data)
        self.mock_preview_extractor.extract_jpeg_from_preview.assert_called_once_with("preview_path")
        self.mock_image_processor.process_image.assert_called_once_with(mock_img)
        self.mock_ai_provider.analyze_image.assert_called_once_with("base64_image")
        self.mock_db.update_image_metadata.assert_called_once_with(image_data[0], {"keywords": ["test"]})
        mock_img.close.assert_called_once()
        
    def test_process_image_exception(self):
        """Test processing an image with an exception."""
        # Set up mocks to raise an exception
        self.mock_preview_extractor.locate_preview_file.side_effect = Exception("Test exception")
        
        # Process an image
        image_data = self.test_images[0]
        result = self.processor.process_image(image_data)
        
        # Check the result
        self.assertFalse(result['success'])
        self.assertEqual(result['stage'], 'exception')
        self.assertEqual(result['error'], 'Test exception')
        
    def test_process_batch_sequential(self):
        """Test processing a batch sequentially."""
        # Set up mocks for successful processing
        self.mock_preview_extractor.locate_preview_file.return_value = "preview_path"
        mock_img = MagicMock()
        mock_img.width = 100
        mock_img.height = 100
        mock_img.close = MagicMock()
        self.mock_preview_extractor.extract_jpeg_from_preview.return_value = mock_img
        self.mock_image_processor.process_image.return_value = ("base64_image", (100, 100))
        self.mock_ai_provider.analyze_image.return_value = {"keywords": ["test"]}
        self.mock_db.update_image_metadata.return_value = True
        
        # Set max_workers to 1 for sequential processing
        self.processor.max_workers = 1
        
        # Process a batch
        batch = self.test_images[:2]
        results = self.processor.process_batch(batch)
        
        # Check the results
        self.assertEqual(len(results), 2)
        self.assertTrue(all(r['success'] for r in results))
        
        # Check that the methods were called correctly
        self.assertEqual(self.mock_preview_extractor.locate_preview_file.call_count, 2)
        self.assertEqual(self.mock_preview_extractor.extract_jpeg_from_preview.call_count, 2)
        self.assertEqual(self.mock_image_processor.process_image.call_count, 2)
        self.assertEqual(self.mock_ai_provider.analyze_image.call_count, 2)
        self.assertEqual(self.mock_db.update_image_metadata.call_count, 2)
        self.assertEqual(mock_img.close.call_count, 2)
        
    def test_process_batch_parallel(self):
        """Test processing a batch in parallel."""
        # Set up mocks for successful processing
        self.mock_preview_extractor.locate_preview_file.return_value = "preview_path"
        mock_img = MagicMock()
        mock_img.width = 100
        mock_img.height = 100
        mock_img.close = MagicMock()
        self.mock_preview_extractor.extract_jpeg_from_preview.return_value = mock_img
        self.mock_image_processor.process_image.return_value = ("base64_image", (100, 100))
        self.mock_ai_provider.analyze_image.return_value = {"keywords": ["test"]}
        self.mock_db.update_image_metadata.return_value = True
        
        # Set max_workers to 2 for parallel processing
        self.processor.max_workers = 2
        
        # Process a batch
        batch = self.test_images[:2]
        results = self.processor.process_batch(batch)
        
        # Check the results
        self.assertEqual(len(results), 2)
        self.assertTrue(all(r['success'] for r in results))
        
        # Check that the methods were called correctly
        self.assertEqual(self.mock_preview_extractor.locate_preview_file.call_count, 2)
        self.assertEqual(self.mock_preview_extractor.extract_jpeg_from_preview.call_count, 2)
        self.assertEqual(self.mock_image_processor.process_image.call_count, 2)
        self.assertEqual(self.mock_ai_provider.analyze_image.call_count, 2)
        self.assertEqual(self.mock_db.update_image_metadata.call_count, 2)
        self.assertEqual(mock_img.close.call_count, 2)
        
    @patch('lightroom_ai.batch_processor.ThreadPoolExecutor')
    def test_process_batch_executor_exception(self, mock_executor):
        """Test processing a batch with executor exception."""
        # Set up mock executor to raise an exception
        mock_future = MagicMock()
        mock_future.result.side_effect = Exception("Executor exception")
        
        mock_executor_instance = MagicMock()
        mock_executor_instance.__enter__.return_value.submit.return_value = mock_future
        mock_executor.return_value = mock_executor_instance
        
        # Set max_workers to 2 for parallel processing
        self.processor.max_workers = 2
        
        # Process a batch
        batch = self.test_images[:1]
        results = self.processor.process_batch(batch)
        
        # Check the results
        self.assertEqual(len(results), 1)
        self.assertFalse(results[0]['success'])
        self.assertEqual(results[0]['stage'], 'executor_exception')
        self.assertEqual(results[0]['error'], 'Executor exception')
        
    def test_run(self):
        """Test running the batch processor."""
        # Set up mocks for successful processing
        self.mock_preview_extractor.locate_preview_file.return_value = "preview_path"
        mock_img = MagicMock()
        mock_img.width = 100
        mock_img.height = 100
        mock_img.close = MagicMock()
        self.mock_preview_extractor.extract_jpeg_from_preview.return_value = mock_img
        self.mock_image_processor.process_image.return_value = ("base64_image", (100, 100))
        self.mock_ai_provider.analyze_image.return_value = {"keywords": ["test"]}
        self.mock_db.update_image_metadata.return_value = True
        
        # Run the processor
        stats = self.processor.run()
        
        # Check that the methods were called correctly
        self.mock_db.get_images.assert_called_once_with(self.config.max_images)
        self.mock_db.get_processed_images.assert_called_once()
        self.mock_checkpoint_manager.load_checkpoint.assert_called_once()
        
        # Check that images 3 and 4 were skipped (already processed)
        self.assertEqual(stats['skipped_images'], 2)
        
        # Check that the remaining images were processed
        self.assertEqual(stats['total_images'], 3)  # 5 total - 2 skipped
        
        # Check that the checkpoint was saved
        self.mock_checkpoint_manager.save_checkpoint.assert_called()
        
        # Check that progress stats were logged
        self.assertEqual(self.mock_preview_extractor.get_cache_stats.call_count, 1)
        
    def test_run_with_provided_images(self):
        """Test running the batch processor with provided images."""
        # Set up mocks for successful processing
        self.mock_preview_extractor.locate_preview_file.return_value = "preview_path"
        mock_img = MagicMock()
        mock_img.width = 100
        mock_img.height = 100
        mock_img.close = MagicMock()
        self.mock_preview_extractor.extract_jpeg_from_preview.return_value = mock_img
        self.mock_image_processor.process_image.return_value = ("base64_image", (100, 100))
        self.mock_ai_provider.analyze_image.return_value = {"keywords": ["test"]}
        self.mock_db.update_image_metadata.return_value = True
        
        # Run the processor with provided images
        provided_images = self.test_images[:2]
        stats = self.processor.run(provided_images)
        
        # Check that get_images was not called
        self.mock_db.get_images.assert_not_called()
        
        # Check that the provided images were processed
        self.assertEqual(stats['total_images'], 2)
        
    def test_log_progress_stats(self):
        """Test logging progress statistics."""
        # Set up stats
        self.processor.stats.start_time = time.time() - 10  # 10 seconds ago
        
        # Log progress stats
        with self.assertLogs(level='INFO') as cm:
            self.processor._log_progress_stats(5, 10)
            
        # Check that progress was logged
        self.assertTrue(any('Progress: 5/10' in log for log in cm.output))
        self.assertTrue(any('Time elapsed' in log for log in cm.output))
        
    def test_log_detailed_stats(self):
        """Test logging detailed statistics."""
        # Set up stats
        self.processor.stats.total_images = 10
        self.processor.stats.processed_images = 8
        self.processor.stats.successful_images = 6
        self.processor.stats.failed_images = 2
        self.processor.stats.skipped_images = 2
        self.processor.stats.preview_found_count = 7
        self.processor.stats.preview_extract_failures = 1
        self.processor.stats.ai_call_failures = 1
        self.processor.stats.db_update_failures = 0
        self.processor.stats.total_time = 20.5
        
        # Log detailed stats
        with self.assertLogs(level='INFO') as cm:
            self.processor._log_detailed_stats()
            
        # Check that stats were logged
        self.assertTrue(any('=== Processing Statistics ===' in log for log in cm.output))
        self.assertTrue(any('Total images: 10' in log for log in cm.output))
        self.assertTrue(any('Successful: 6' in log for log in cm.output))
        self.assertTrue(any('Preview cache:' in log for log in cm.output))
        
    @patch('psutil.Process')
    def test_check_memory_usage(self, mock_process):
        """Test checking memory usage."""
        # Set up mock process
        mock_process_instance = MagicMock()
        mock_process_instance.memory_info.return_value.rss = 900 * 1024 * 1024  # 900 MB
        mock_process.return_value = mock_process_instance
        
        # Check memory usage
        with self.assertLogs(level='WARNING') as cm:
            self.processor._check_memory_usage()
            
        # Check that cache was cleared due to high memory usage
        self.mock_preview_extractor.clear_cache.assert_called_once()
        self.assertTrue(any('Memory usage high' in log for log in cm.output))
        
        # Test with lower memory usage
        mock_process_instance.memory_info.return_value.rss = 500 * 1024 * 1024  # 500 MB
        self.mock_preview_extractor.clear_cache.reset_mock()
        
        # Check memory usage again
        self.processor._check_memory_usage()
        
        # Check that cache was not cleared
        self.mock_preview_extractor.clear_cache.assert_not_called()
        
    def test_processing_stats_to_dict(self):
        """Test converting ProcessingStats to dictionary."""
        # Create stats
        stats = ProcessingStats()
        stats.total_images = 10
        stats.processed_images = 8
        stats.successful_images = 6
        stats.failed_images = 2
        stats.skipped_images = 2
        stats.start_time = time.time() - 20
        stats.total_time = 20
        
        # Convert to dict
        stats_dict = stats.to_dict()
        
        # Check the dict
        self.assertEqual(stats_dict['total_images'], 10)
        self.assertEqual(stats_dict['processed_images'], 8)
        self.assertEqual(stats_dict['successful_images'], 6)
        self.assertEqual(stats_dict['failed_images'], 2)
        self.assertEqual(stats_dict['skipped_images'], 2)
        self.assertEqual(stats_dict['total_time'], 20)
        self.assertEqual(stats_dict['success_rate'], 0.6)  # 6/10
        self.assertEqual(stats_dict['avg_time_per_image'], 2.5)  # 20/8


if __name__ == '__main__':
    unittest.main()
