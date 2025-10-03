"""
Unit tests for Flask application components.
Tests app initialization, helper functions, and route definitions.
"""

import pytest
import json
from unittest.mock import patch, MagicMock
import tempfile
import os

import app
from video_wrapper import VIDEO_PROCESSING_AVAILABLE


class TestAppConfiguration:
    """Test Flask app configuration and initialization."""
    
    def test_app_creation(self, flask_app):
        """Test that Flask app is created correctly."""
        assert flask_app is not None
        assert flask_app.config['TESTING'] is True
    
    def test_app_directories_created(self, flask_app):
        """Test that upload and processed directories are created."""
        upload_dir = flask_app.config['UPLOAD_FOLDER']
        processed_dir = flask_app.config['PROCESSED_FOLDER']
        
        assert os.path.exists(upload_dir)
        assert os.path.exists(processed_dir)
    
    def test_app_config_values(self, flask_app):
        """Test app configuration values."""
        assert flask_app.config['MAX_CONTENT_LENGTH'] == 100 * 1024 * 1024  # 100MB
        assert 'UPLOAD_FOLDER' in flask_app.config
        assert 'PROCESSED_FOLDER' in flask_app.config


class TestHelperFunctions:
    """Test helper functions in the app module."""
    
    def test_allowed_file_image_valid_extensions(self):
        """Test allowed_file function with valid image extensions."""
        valid_extensions = ['test.png', 'test.jpg', 'test.jpeg', 'test.gif', 'test.bmp', 'test.tiff']
        
        for filename in valid_extensions:
            assert app.allowed_file(filename, 'image') is True
    
    def test_allowed_file_image_invalid_extensions(self):
        """Test allowed_file function with invalid image extensions."""
        invalid_extensions = ['test.txt', 'test.doc', 'test.pdf', 'test.mp4', 'test.xyz']
        
        for filename in invalid_extensions:
            assert app.allowed_file(filename, 'image') is False
    
    def test_allowed_file_video_valid_extensions(self):
        """Test allowed_file function with valid video extensions."""
        valid_extensions = ['test.mp4', 'test.avi', 'test.mov', 'test.mkv', 'test.wmv']
        
        for filename in valid_extensions:
            assert app.allowed_file(filename, 'video') is True
    
    def test_allowed_file_video_invalid_extensions(self):
        """Test allowed_file function with invalid video extensions."""
        invalid_extensions = ['test.txt', 'test.jpg', 'test.png', 'test.pdf', 'test.xyz']
        
        for filename in invalid_extensions:
            assert app.allowed_file(filename, 'video') is False
    
    def test_allowed_file_case_insensitive(self):
        """Test that allowed_file is case insensitive."""
        assert app.allowed_file('test.PNG', 'image') is True
        assert app.allowed_file('test.JPG', 'image') is True
        assert app.allowed_file('test.MP4', 'video') is True
        assert app.allowed_file('test.AVI', 'video') is True
    
    def test_allowed_file_no_extension(self):
        """Test allowed_file with filenames without extensions."""
        assert app.allowed_file('test', 'image') is False
        assert app.allowed_file('test', 'video') is False
    
    def test_allowed_file_invalid_type(self):
        """Test allowed_file with invalid file type."""
        assert app.allowed_file('test.jpg', 'unknown') is False
        assert app.allowed_file('test.mp4', 'unknown') is False


class TestRouteDefinitions:
    """Test that routes are properly defined."""
    
    def test_index_route_exists(self, client):
        """Test that index route exists and returns 200."""
        response = client.get('/')
        assert response.status_code == 200
    
    def test_upload_route_exists(self, client):
        """Test that upload route exists."""
        # Test with GET method (should return 405 Method Not Allowed)
        response = client.get('/upload')
        assert response.status_code == 405
        
        # Test with POST method (should return 400 for missing file)
        response = client.post('/upload')
        assert response.status_code == 400
    
    def test_process_image_route_exists(self, client):
        """Test that process_image route exists."""
        response = client.get('/process_image')
        assert response.status_code == 405  # Should only accept POST
    
    def test_process_video_route_exists(self, client):
        """Test that process_video route exists."""
        response = client.get('/process_video')
        assert response.status_code == 405  # Should only accept POST
    
    def test_get_image_operations_route(self, client):
        """Test get_image_operations route."""
        response = client.get('/get_image_operations')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Check structure of operations
        operation = data[0]
        assert 'name' in operation
        assert 'display_name' in operation
        assert 'description' in operation
        assert 'params' in operation
    
    def test_get_video_operations_route(self, client):
        """Test get_video_operations route."""
        response = client.get('/get_video_operations')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert isinstance(data, list)
        
        # If video processing is available, should have operations
        if VIDEO_PROCESSING_AVAILABLE:
            assert len(data) > 0
            operation = data[0]
            assert 'name' in operation
            assert 'display_name' in operation
            assert 'description' in operation
            assert 'params' in operation
        else:
            # If not available, should return empty list
            assert len(data) == 0
    
    def test_download_route_exists(self, client):
        """Test that download route exists."""
        # Test with non-existent file
        response = client.get('/download/nonexistent.png')
        assert response.status_code == 404


class TestImageOperationsConfiguration:
    """Test image operations configuration."""
    
    def test_all_operations_have_required_fields(self, client):
        """Test that all image operations have required fields."""
        response = client.get('/get_image_operations')
        operations = json.loads(response.data)
        
        required_fields = ['name', 'display_name', 'description', 'params']
        
        for operation in operations:
            for field in required_fields:
                assert field in operation, f"Operation {operation.get('name', 'unknown')} missing field: {field}"
    
    def test_operation_parameters_structure(self, client):
        """Test that operation parameters have correct structure."""
        response = client.get('/get_image_operations')
        operations = json.loads(response.data)
        
        for operation in operations:
            for param in operation['params']:
                assert 'name' in param
                assert 'type' in param
                assert 'default' in param
                
                if param['type'] in ['int', 'float']:
                    assert 'min' in param
                    assert 'max' in param
    
    def test_specific_operations_exist(self, client):
        """Test that specific expected operations exist."""
        response = client.get('/get_image_operations')
        operations = json.loads(response.data)
        
        operation_names = [op['name'] for op in operations]
        
        expected_operations = [
            'adaptive_brightness',
            'logarithmic_transform',
            'exponential_transform',
            'denoise_image',
            'sharpen_img',
            'boost_saturation'
        ]
        
        for expected_op in expected_operations:
            assert expected_op in operation_names, f"Expected operation {expected_op} not found"


class TestVideoOperationsConfiguration:
    """Test video operations configuration."""
    
    @pytest.mark.requires_dll
    def test_video_operations_structure(self, client, video_dll_available):
        """Test video operations structure when DLL is available."""
        if not video_dll_available:
            pytest.skip("Video DLL not available")
        
        response = client.get('/get_video_operations')
        operations = json.loads(response.data)
        
        assert len(operations) > 0
        
        required_fields = ['name', 'display_name', 'description', 'params']
        
        for operation in operations:
            for field in required_fields:
                assert field in operation
    
    def test_video_operations_when_dll_unavailable(self, client):
        """Test video operations when DLL is not available."""
        if VIDEO_PROCESSING_AVAILABLE:
            pytest.skip("Video DLL is available, skipping unavailable test")
        
        response = client.get('/get_video_operations')
        operations = json.loads(response.data)
        
        assert operations == []


class TestErrorHandling:
    """Test error handling in various scenarios."""
    
    def test_upload_no_file_part(self, client):
        """Test upload endpoint with no file part."""
        response = client.post('/upload', data={})
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_upload_empty_filename(self, client):
        """Test upload endpoint with empty filename."""
        from io import BytesIO
        
        response = client.post('/upload', data={
            'file': (BytesIO(b'test data'), '')
        })
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_process_image_no_file_id(self, client):
        """Test process_image endpoint with no file_id."""
        response = client.post('/process_image',
                             data=json.dumps({}),
                             content_type='application/json')
        assert response.status_code == 400
    
    def test_process_video_no_file_id(self, client):
        """Test process_video endpoint with no file_id."""
        response = client.post('/process_video',
                             data=json.dumps({}),
                             content_type='application/json')
        assert response.status_code == 400


if __name__ == "__main__":
    pytest.main([__file__, "-v"])