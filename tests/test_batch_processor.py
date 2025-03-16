"""
Tests for the batch processor module.
"""
import unittest
from unittest.mock import MagicMock, patch
from typing import List, Tuple

from lightroom_ai.batch_processor import BatchProcessor
from lightroom_ai.config import AppConfig


class TestBatchProcessor(unittest.TestCase):
    """Test cases for the BatchProcessor class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a mock config
        self.config = MagicMock(spec=AppConfig)
        self.config.batch_size = 10
        self.config.max_workers = 2
        self.config.use_checkpoint = False
        self.config.debug_mode = True
        self.config.memory_limit_mb = 1000
        
        # Mock dependencies
        self.mock_db = MagicMock()
        self.mock_preview_extractor = MagicMock()
        self.mock_image_processor = MagicMock()
        self.mock_ai_provider = MagicMock()
        
        # Create patches
        self.db_patch = patch('lightroom_ai.batch_processor.CatalogDatabase', return_value=self.mock_db)
        self.preview_patch = patch('lightroom_ai.batch_processor.PreviewExtractor', return_value=self.mock_preview_extractor)
        self.image_patch = patch('lightroom_ai.batch_processor.ImageProcessor', return_value=self.mock_image_processor)
        self.ai_patch = patch('lightroom_ai.batch_processor.AiProvider')
        
        # Start patches
        self.mock_db_class = self.db_patch.start()
        self.mock_preview_class = self.preview_patch.start()
        self.mock_image_class = self.image_patch.start()
        self.mock_ai_class = self.ai_patch.start()
        
        # Configure AI provider
        self.mock_ai_class.get_provider.return_value = self.mock_ai_provider
        
        # Configure database
        self.mock_db.analyze_database_structure.return_value = {}
        
    def tearDown(self):
        """Tear down test fixtures."""
        # Stop patches
        self.db_patch.stop()
        self.preview_patch.stop()
        self.image_patch.stop()
        self.ai_patch.stop()
    
    def test_init(self):
        """Test initialization of BatchProcessor."""
        processor = BatchProcessor("test.lrcat", self.config)
        
        # Verify components were initialized
        self.mock_db_class.assert_called_once_with("test.lrcat", self.config)
        self.mock_preview_class.assert_called_once_with("test.lrcat", self.config)
        self.mock_image_class.assert_called_once_with(self.config)
        self.mock_ai_class.get_provider.assert_called_once_with(self.config)
        
        # Verify stats were initialized
        self.assertEqual(processor.stats['total_images'], 0)
        self.assertEqual(processor.stats['processed_images'], 0)
        self.assertEqual(processor.stats['successful_images'], 0)
        self.assertEqual(processor.stats['failed_images'], 0)
        self.assertEqual(processor.stats['skipped_images'], 0)
    
    def test_process_image_success(self):
        """Test successful image processing."""
        # Setup
        processor = BatchProcessor("test.lrcat", self.config)
        image_data = (1, "path/to/image", "test_image.jpg")
        
        # Configure mocks for success
        self.mock_preview_extractor.locate_preview_file.return_value = "preview.jpg"
        self.mock_preview_extractor.extract_jpeg_from_preview.return_value = MagicMock()
        self.mock_image_processor.process_image.return_value = ("base64", (100, 100))
        self.mock_ai_provider.analyze_image.return_value = {"description": "test"}
        self.mock_db.update_image_metadata.return_value = True
        
        # Execute
        result = processor.process_image(image_data)
        
        # Verify
        self.assertEqual(result, (1, True))
        self.mock_preview_extractor.locate_preview_file.assert_called_once_with(image_data)
        self.mock_preview_extractor.extract_jpeg_from_preview.assert_called_once()
        self.mock_image_processor.process_image.assert_called_once()
        self.mock_ai_provider.analyze_image.assert_called_once()
        self.mock_db.update_image_metadata.assert_called_once_with(1, {"description": "test"})
    
    def test_process_image_no_preview(self):
        """Test image processing with no preview found."""
        # Setup
        processor = BatchProcessor("test.lrcat", self.config)
        image_data = (1, "path/to/image", "test_image.jpg")
        
        # Configure mocks for failure
        self.mock_preview_extractor.locate_preview_file.return_value = None
        
        # Execute
        result = processor.process_image(image_data)
        
        # Verify
        self.assertEqual(result, (1, False))
        self.mock_preview_extractor.locate_preview_file.assert_called_once_with(image_data)
        self.mock_preview_extractor.extract_jpeg_from_preview.assert_not_called()
        
    def test_process_batch_sequential(self):
        """Test batch processing in sequential mode."""
        # Setup
        self.config.max_workers = 1
        processor = BatchProcessor("test.lrcat", self.config)
        
        # Mock process_image to return success
        processor.process_image = MagicMock(return_value=(1, True))
        
        # Create batch
        batch = [(1, "path", "img1.jpg"), (2, "path", "img2.jpg")]
        
        # Execute
        results = processor.process_batch(batch)
        
        # Verify
        self.assertEqual(len(results), 2)
        self.assertEqual(results, [(1, True), (1, True)])
        self.assertEqual(processor.process_image.call_count, 2)


if __name__ == '__main__':
    unittest.main()
