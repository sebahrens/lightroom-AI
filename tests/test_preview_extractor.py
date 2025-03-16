import os
import unittest
from unittest.mock import patch, MagicMock, mock_open
import tempfile
import shutil
import io
from PIL import Image
import numpy as np

from lightroom_ai.config import AppConfig
from lightroom_ai.preview_extractor import PreviewExtractor


class TestPreviewExtractor(unittest.TestCase):
    """Test cases for the PreviewExtractor class."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        
        # Create a mock catalog path
        self.catalog_path = os.path.join(self.temp_dir, "test_catalog.lrcat")
        
        # Create mock preview directories
        self.previews_dir = os.path.join(self.temp_dir, "test_catalog Previews.lrdata")
        self.smart_previews_dir = os.path.join(self.temp_dir, "test_catalog Smart Previews.lrdata")
        
        os.makedirs(self.previews_dir, exist_ok=True)
        os.makedirs(self.smart_previews_dir, exist_ok=True)
        
        # Create a basic config
        self.config = AppConfig()
        self.config.deep_search = True
        self.config.use_smart_previews = True
        self.config.use_original_if_no_preview = True
        self.config.use_id_global = True
        self.config.use_preview_db = True
        self.config.known_preview_patterns = ["pattern1", "pattern2"]
        self.config.debug_mode = True
        
        # Create the preview extractor with mocked preview_db
        with patch('lightroom_ai.preview_extractor.PreviewDatabase') as mock_preview_db_class:
            self.mock_preview_db = mock_preview_db_class.return_value
            self.extractor = PreviewExtractor(self.catalog_path, self.config)
            self.extractor.preview_db = self.mock_preview_db
        
        # Create a test image
        self.create_test_image()
        
    def tearDown(self):
        """Clean up after tests."""
        # Remove the temporary directory and its contents
        shutil.rmtree(self.temp_dir)
        
    def create_test_image(self):
        """Create a test JPEG image."""
        # Create a small test image
        img = Image.new('RGB', (100, 100), color='red')
        self.test_image_path = os.path.join(self.temp_dir, "test_image.jpg")
        img.save(self.test_image_path)
        
        # Create a test preview file
        self.test_preview_path = os.path.join(self.previews_dir, "test_preview.jpg")
        img.save(self.test_preview_path)
        
        # Create a test .lrprev file with JPEG data embedded
        with open(self.test_image_path, 'rb') as f:
            jpeg_data = f.read()
        
        self.test_lrprev_path = os.path.join(self.previews_dir, "test_preview.lrprev")
        with open(self.test_lrprev_path, 'wb') as f:
            # Add a JPEG header and footer to the data
            f.write(b"HEADER\xFF\xD8\xFF" + jpeg_data + b"\xFF\xD9")
        
    def test_init(self):
        """Test initialization of PreviewExtractor."""
        self.assertEqual(self.extractor.catalog_path, self.catalog_path)
        self.assertEqual(self.extractor.config, self.config)
        self.assertTrue(hasattr(self.extractor, 'filesystem'))
        self.assertTrue(hasattr(self.extractor, '_preview_cache'))
        self.assertTrue(hasattr(self.extractor, '_cache_lock'))
        
    def test_clear_cache(self):
        """Test clearing the cache."""
        # Add some items to the cache
        with self.extractor._cache_lock:
            self.extractor._preview_cache = {"key1": "value1", "key2": "value2"}
            self.extractor._cache_hits = 10
            self.extractor._cache_misses = 5
            
        # Clear the cache
        self.extractor.clear_cache()
        
        # Check that the cache was cleared
        with self.extractor._cache_lock:
            self.assertEqual(len(self.extractor._preview_cache), 0)
            self.assertEqual(self.extractor._cache_hits, 0)
            self.assertEqual(self.extractor._cache_misses, 0)
            
    def test_get_cache_size(self):
        """Test getting the cache size."""
        # Add some items to the cache
        with self.extractor._cache_lock:
            self.extractor._preview_cache = {"key1": "value1", "key2": "value2"}
            
        # Get the cache size
        size = self.extractor.get_cache_size()
        
        # Check that the size is correct
        self.assertEqual(size, 2)
        
    def test_get_cache_stats(self):
        """Test getting cache statistics."""
        # Add some items to the cache and set hit/miss counts
        with self.extractor._cache_lock:
            self.extractor._preview_cache = {"key1": "value1", "key2": "value2"}
            self.extractor._cache_hits = 15
            self.extractor._cache_misses = 5
            
        # Get the cache stats
        stats = self.extractor.get_cache_stats()
        
        # Check that the stats are correct
        self.assertEqual(stats['size'], 2)
        self.assertEqual(stats['hits'], 15)
        self.assertEqual(stats['misses'], 5)
        self.assertEqual(stats['hit_rate'], 0.75)  # 15 / (15 + 5)
        
    def test_optimize_search_strategies(self):
        """Test optimizing search strategies."""
        # Create a mock database info
        db_info = {
            'has_smart_previews_dir': True,
            'has_previews_dir': True,
            'previews_dir': self.previews_dir,
            'has_id_global': True
        }
        
        # Mock the preview_db
        self.mock_preview_db.collect_preview_file_patterns.return_value = ["pattern3", "pattern4"]
        
        # Optimize search strategies
        self.extractor.optimize_search_strategies(db_info)
        
        # Check that the config was updated
        self.assertTrue(self.config.use_smart_previews)
        self.assertTrue(self.config.use_preview_db)
        self.assertTrue(self.config.use_id_global)
        self.assertEqual(self.config.known_preview_patterns, ["pattern3", "pattern4"])
        
    @patch('lightroom_ai.preview_extractor.PreviewExtractor.locate_preview_file')
    def test_scan_previews(self, mock_locate):
        """Test scanning previews."""
        # Mock locate_preview_file to return a path for some images and None for others
        mock_locate.side_effect = [self.test_preview_path, None, self.test_preview_path]
        
        # Create some test image data
        images = [
            (1, 101, "image1.jpg", "path/to", "/root", "global1", "file_global1"),
            (2, 102, "image2.jpg", "path/to", "/root", "global2", "file_global2"),
            (3, 103, "image3.jpg", "path/to", "/root", "global3", "file_global3")
        ]
        
        # Scan previews
        total, found = self.extractor.scan_previews(images)
        
        # Check the results
        self.assertEqual(total, 3)
        self.assertEqual(found, 2)  # Two images had previews, one didn't
        self.assertEqual(mock_locate.call_count, 3)
        
    def test_is_jpeg_header(self):
        """Test checking for JPEG header."""
        # Valid JPEG header
        valid_header = b'\xFF\xD8\xFF\xE0\x00\x10\x4A\x46\x49\x46'
        self.assertTrue(self.extractor._is_jpeg_header(valid_header))
        
        # Invalid header
        invalid_header = b'\x89\x50\x4E\x47\x0D\x0A\x1A\x0A'  # PNG header
        self.assertFalse(self.extractor._is_jpeg_header(invalid_header))
        
    @patch('lightroom_ai.filesystem.FilesystemHelper.find_preview_by_uuid')
    @patch('lightroom_ai.filesystem.FilesystemHelper.find_preview_by_basename')
    def test_locate_preview_file(self, mock_find_basename, mock_find_uuid):
        """Test locating preview file."""
        # Mock the find methods to return paths
        mock_find_uuid.return_value = self.test_preview_path
        mock_find_basename.return_value = None
        
        # Create test image data
        image_data = (1, 101, "image1.jpg", "path/to", "/root", "global1", "file_global1")
        
        # Locate preview file
        preview_path = self.extractor.locate_preview_file(image_data)
        
        # Check that the correct path was returned
        self.assertEqual(preview_path, self.test_preview_path)
        
        # Check that the path was cached
        cache_key = f"{image_data[0]}_{image_data[2]}"
        with self.extractor._cache_lock:
            self.assertIn(cache_key, self.extractor._preview_cache)
            self.assertEqual(self.extractor._preview_cache[cache_key], self.test_preview_path)
        
        # Test cache hit
        mock_find_uuid.reset_mock()
        preview_path = self.extractor.locate_preview_file(image_data)
        self.assertEqual(preview_path, self.test_preview_path)
        mock_find_uuid.assert_not_called()  # Should not be called again due to cache hit
        
    def test_extract_jpeg_from_preview_direct_jpeg(self):
        """Test extracting JPEG from a direct JPEG file."""
        # Extract JPEG from the test preview file
        img = self.extractor.extract_jpeg_from_preview(self.test_preview_path)
        
        # Check that an image was returned
        self.assertIsNotNone(img)
        self.assertEqual(img.width, 100)
        self.assertEqual(img.height, 100)
        
    @patch('PIL.Image.open')
    def test_extract_jpeg_from_preview_lrprev(self, mock_image_open):
        """Test extracting JPEG from an .lrprev file."""
        # Mock the Image.open method to return a test image
        mock_img = MagicMock()
        mock_img.width = 100
        mock_img.height = 100
        mock_image_open.return_value = mock_img
        
        # Extract JPEG from the test .lrprev file
        img = self.extractor.extract_jpeg_from_preview(self.test_lrprev_path)
        
        # Check that an image was returned
        self.assertIsNotNone(img)
        
        # Verify that Image.open was called with BytesIO
        mock_image_open.assert_called()
        args, _ = mock_image_open.call_args
        self.assertTrue(isinstance(args[0], io.BytesIO))
                
    def test_extract_jpeg_from_preview_empty_file(self):
        """Test extracting JPEG from an empty file."""
        # Create an empty file
        empty_path = os.path.join(self.temp_dir, "empty.jpg")
        with open(empty_path, 'w') as f:
            pass
            
        # Extract JPEG from the empty file
        img = self.extractor.extract_jpeg_from_preview(empty_path)
        
        # Check that no image was returned
        self.assertIsNone(img)
        
    def test_extract_jpeg_from_preview_nonexistent_file(self):
        """Test extracting JPEG from a nonexistent file."""
        # Extract JPEG from a nonexistent file
        img = self.extractor.extract_jpeg_from_preview(os.path.join(self.temp_dir, "nonexistent.jpg"))
        
        # Check that no image was returned
        self.assertIsNone(img)


if __name__ == '__main__':
    unittest.main()
