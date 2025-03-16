import os
import unittest
from unittest.mock import patch, MagicMock, mock_open
import tempfile
import shutil
from pathlib import Path

from lightroom_ai.config import AppConfig
from lightroom_ai.filesystem import FilesystemHelper


class TestFilesystemHelper(unittest.TestCase):
    """Test cases for the FilesystemHelper class."""
    
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
        
        # Create the filesystem helper
        self.fs_helper = FilesystemHelper(self.catalog_path, self.config)
        
    def tearDown(self):
        """Clean up after tests."""
        # Remove the temporary directory and its contents
        shutil.rmtree(self.temp_dir)
        
    def test_init(self):
        """Test initialization of FilesystemHelper."""
        self.assertEqual(self.fs_helper.catalog_path, self.catalog_path)
        self.assertEqual(self.fs_helper.previews_dir, self.previews_dir)
        self.assertEqual(self.fs_helper.smart_previews_dir, self.smart_previews_dir)
        self.assertTrue(self.fs_helper.has_previews_dir)
        self.assertTrue(self.fs_helper.has_smart_previews_dir)
        
    def test_get_catalog_info(self):
        """Test getting catalog information."""
        info = self.fs_helper.get_catalog_info()
        
        self.assertEqual(info['catalog_path'], self.catalog_path)
        self.assertEqual(info['catalog_dir'], self.temp_dir)
        self.assertEqual(info['catalog_name'], "test_catalog")
        self.assertEqual(info['previews_dir'], self.previews_dir)
        self.assertEqual(info['smart_previews_dir'], self.smart_previews_dir)
        self.assertTrue(info['has_previews_dir'])
        self.assertTrue(info['has_smart_previews_dir'])
        
    def test_format_global_id_as_uuid(self):
        """Test formatting global ID as UUID."""
        # Test with a string that needs formatting
        global_id = "1234567890abcdef1234567890abcdef"
        expected = "12345678-90ab-cdef-1234-567890abcdef"
        self.assertEqual(self.fs_helper.format_global_id_as_uuid(global_id), expected)
        
        # Test with already formatted UUID
        formatted_id = "12345678-90ab-cdef-1234-567890abcdef"
        self.assertEqual(self.fs_helper.format_global_id_as_uuid(formatted_id), formatted_id)
        
        # Test with empty string
        self.assertEqual(self.fs_helper.format_global_id_as_uuid(""), "")
        
    @patch('os.walk')
    def test_find_preview_by_uuid(self, mock_walk):
        """Test finding preview by UUID."""
        uuid = "12345678-90ab-cdef-1234-567890abcdef"
        
        # Create a mock preview file
        preview_path = os.path.join(self.previews_dir, f"preview_{uuid}.jpg")
        
        # Mock os.walk to return our test file
        mock_walk.return_value = [
            (self.previews_dir, [], [f"preview_{uuid}.jpg"])
        ]
        
        # Mock get_preview_resolution_rank to return a high value
        with patch('lightroom_ai.utils.get_preview_resolution_rank', return_value=3):
            # Test finding the preview
            found_path = self.fs_helper.find_preview_by_uuid(uuid)
            self.assertEqual(found_path, preview_path)
        
        # Test with non-existent UUID
        mock_walk.return_value = [(self.previews_dir, [], [])]
        not_found = self.fs_helper.find_preview_by_uuid("nonexistent")
        self.assertIsNone(not_found)
        
    def test_find_preview_by_basename(self):
        """Test finding preview by basename."""
        base_name = "IMG_1234.jpg"
        clean_basename = "IMG_1234"
        
        # Create a mock preview file
        preview_path = os.path.join(self.previews_dir, f"preview_{clean_basename}.jpg")
        
        # Test finding the preview - this will use the index
        with patch.object(self.fs_helper, 'preview_index', {
            f'preview_{clean_basename}.jpg'.lower(): [preview_path]
        }):
            found_path = self.fs_helper.find_preview_by_basename(base_name)
            self.assertEqual(found_path, preview_path)
        
        # Test with non-existent basename
        with patch.object(self.fs_helper, 'preview_index', {}):
            not_found = self.fs_helper.find_preview_by_basename("nonexistent.jpg")
            self.assertIsNone(not_found)
        
    @patch('os.walk')
    def test_find_preview_by_patterns(self, mock_walk):
        """Test finding preview by patterns."""
        patterns = ["pattern1", "pattern2"]
        base_name = "IMG_1234.jpg"
        file_id = "5678"
        
        # Create a mock preview file with pattern
        preview_path = os.path.join(self.previews_dir, f"pattern1_IMG_1234.jpg")
        
        # Mock os.walk to return our test file
        mock_walk.return_value = [
            (self.previews_dir, [], [f"pattern1_IMG_1234.jpg"])
        ]
        
        # Test finding the preview
        found_path = self.fs_helper.find_preview_by_patterns(patterns, base_name, file_id)
        self.assertEqual(found_path, preview_path)
        
        # Test with non-existent pattern
        mock_walk.return_value = [(self.previews_dir, [], [])]
        not_found = self.fs_helper.find_preview_by_patterns(["nonexistent"], base_name, file_id)
        self.assertIsNone(not_found)
        
    @patch('os.walk')
    def test_find_preview_by_hash(self, mock_walk):
        """Test finding preview by hash."""
        base_name = "IMG_1234.jpg"
        
        # Calculate the expected hash
        import hashlib
        filename_hash = hashlib.md5(base_name.encode()).hexdigest().lower()
        
        # Create a mock preview file with hash
        preview_path = os.path.join(self.previews_dir, f"preview_{filename_hash}.jpg")
        
        # Mock os.walk to return our test file
        mock_walk.return_value = [
            (self.previews_dir, [], [f"preview_{filename_hash}.jpg"])
        ]
        
        # Test finding the preview
        found_path = self.fs_helper.find_preview_by_hash(base_name)
        self.assertEqual(found_path, preview_path)
        
        # Test with non-existent hash
        mock_walk.return_value = [(self.previews_dir, [], [])]
        not_found = self.fs_helper.find_preview_by_hash("nonexistent.jpg")
        self.assertIsNone(not_found)
        
    @patch('os.walk')
    def test_find_smart_preview(self, mock_walk):
        """Test finding smart preview."""
        base_name = "IMG_1234.jpg"
        
        # Create a mock smart preview file
        preview_path = os.path.join(self.smart_previews_dir, f"IMG_1234.dng")
        
        # Mock os.walk to return our test file
        mock_walk.return_value = [
            (self.smart_previews_dir, [], [f"IMG_1234.dng"])
        ]
        
        # Test finding the smart preview
        found_path = self.fs_helper.find_smart_preview(base_name)
        self.assertEqual(found_path, preview_path)
        
        # Test with non-existent smart preview
        mock_walk.return_value = [(self.smart_previews_dir, [], [])]
        not_found = self.fs_helper.find_smart_preview("nonexistent.jpg")
        self.assertIsNone(not_found)
        
    @patch('os.path.exists')
    def test_get_original_image_path(self, mock_exists):
        """Test getting original image path."""
        root_folder = self.temp_dir
        path_from_root = "photos"
        base_name = "IMG_1234.jpg"
        
        # Create a mock original image path
        original_path = os.path.join(root_folder, path_from_root, base_name)
        
        # Mock os.path.exists to return True for our test file
        mock_exists.return_value = True
        
        # Test finding the original image
        found_path = self.fs_helper.get_original_image_path(root_folder, path_from_root, base_name)
        self.assertEqual(found_path, original_path)
        
        # Test with non-existent original image
        mock_exists.return_value = False
        not_found = self.fs_helper.get_original_image_path(root_folder, path_from_root, "nonexistent.jpg")
        self.assertIsNone(not_found)
        
        # Test with use_original_if_no_preview set to False
        self.config.use_original_if_no_preview = False
        not_found = self.fs_helper.get_original_image_path(root_folder, path_from_root, base_name)
        self.assertIsNone(not_found)
        
    def test_get_preview_resolution_rank(self):
        """Test getting preview resolution rank."""
        # Test high resolution
        high_res = os.path.join(self.previews_dir, "preview_3200.jpg")
        self.assertEqual(self.fs_helper.get_preview_resolution_rank(high_res), 3)
        
        # Test medium resolution
        med_res = os.path.join(self.previews_dir, "preview_1600.jpg")
        self.assertEqual(self.fs_helper.get_preview_resolution_rank(med_res), 2)
        
        # Test low resolution
        low_res = os.path.join(self.previews_dir, "preview_800.jpg")
        self.assertEqual(self.fs_helper.get_preview_resolution_rank(low_res), 1)
        
        # Test unknown resolution
        unknown_res = os.path.join(self.previews_dir, "preview.jpg")
        self.assertEqual(self.fs_helper.get_preview_resolution_rank(unknown_res), 0)
        
    @patch('os.walk')
    @patch('os.listdir')
    def test_build_preview_index(self, mock_listdir, mock_walk):
        """Test building preview index."""
        # Mock files in the previews directory
        mock_walk.return_value = [
            (self.previews_dir, [], ["preview1.jpg", "preview2.jpg", "previews.db"])
        ]
        
        # Build the index
        self.fs_helper.build_preview_index()
        
        # Check that the index was built correctly
        self.assertTrue(hasattr(self.fs_helper, 'preview_index'))
        self.assertEqual(len(self.fs_helper.preview_index), 2)
        self.assertIn('preview1.jpg', self.fs_helper.preview_index)
        self.assertIn('preview2.jpg', self.fs_helper.preview_index)
        
    @patch('os.walk')
    @patch('os.listdir')
    def test_debug_directory_structure(self, mock_listdir, mock_walk):
        """Test debug directory structure."""
        # Mock os.walk to return a simple directory structure
        mock_walk.return_value = [
            (self.previews_dir, ['subdir1', 'subdir2'], ['file1.jpg', 'file2.jpg']),
            (os.path.join(self.previews_dir, 'subdir1'), [], ['file3.jpg']),
            (os.path.join(self.previews_dir, 'subdir2'), [], ['file4.jpg'])
        ]
        
        # Mock os.listdir to return files
        mock_listdir.return_value = ['file1.jpg', 'file2.jpg']
        
        # Test debug directory structure
        with self.assertLogs(level='DEBUG') as cm:
            self.fs_helper.debug_directory_structure(self.previews_dir)
            
        # Check that the debug logs were created
        self.assertTrue(any('Directory' in log for log in cm.output))
        
        # Test with error
        mock_listdir.side_effect = Exception("Test error")
        with self.assertLogs(level='DEBUG') as cm:
            self.fs_helper.debug_directory_structure(self.previews_dir)
            
        # Check that the error was logged
        self.assertTrue(any('Error reading directory' in log for log in cm.output))


if __name__ == '__main__':
    unittest.main()
