"""
Integration tests for API endpoints.
Tests Flask API endpoints with real file uploads using sample images.
"""

import pytest
import json
import os
from io import BytesIO
from pathlib import Path
import uuid

import app
from video_wrapper import VIDEO_PROCESSING_AVAILABLE


@pytest.mark.integration
class TestUploadEndpoint:
    """Test file upload endpoint with real files."""
    
    def test_upload_valid_image(self, client, sample_image):
        """Test uploading a valid image file."""
        with open(sample_image, 'rb') as f:
            data = {
                'file': (f, sample_image.name)
            }
            response = client.post('/upload', data=data)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['success'] is True
        assert 'file_id' in data
        assert 'filename' in data
        assert 'file_type' in data
        assert 'file_extension' in data
        assert data['file_type'] == 'image'
        assert data['file_extension'] == 'jpg'
    

    

    
    def test_upload_invalid_file_type(self, client, temp_dir):
        """Test uploading an invalid file type."""
        # Create a temporary text file
        text_file = Path(temp_dir) / "test.txt"
        text_file.write_text("This is not an image")
        
        with open(text_file, 'rb') as f:
            data = {
                'file': (f, 'test.txt')
            }
            response = client.post('/upload', data=data)
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_upload_multiple_images(self, client, sample_image_paths):
        """Test uploading multiple different images."""
        # Test first 3 images to keep test time reasonable
        for image_path in sample_image_paths[:3]:
            with open(image_path, 'rb') as f:
                data = {
                    'file': (f, image_path.name)
                }
                response = client.post('/upload', data=data)
            
            assert response.status_code == 200
            response_data = json.loads(response.data)
            assert response_data['success'] is True


@pytest.mark.integration
class TestImageProcessingEndpoint:
    """Test image processing endpoint with real images."""
    
    def upload_test_image(self, client, image_path):
        """Helper method to upload an image and return file_id."""
        with open(image_path, 'rb') as f:
            data = {
                'file': (f, image_path.name)
            }
            response = client.post('/upload', data=data)
        
        assert response.status_code == 200
        return json.loads(response.data)['file_id']
    
    def test_process_image_adaptive_brightness(self, client, sample_image):
        """Test image processing with adaptive brightness."""
        file_id = self.upload_test_image(client, sample_image)
        
        processing_data = {
            'file_id': file_id,
            'operations': [
                {'name': 'adaptive_brightness', 'params': {}}
            ]
        }
        
        response = client.post('/process_image',
                             data=json.dumps(processing_data),
                             content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'processed_file' in data
        assert data['operations_applied'] == 1
    
    def test_process_image_logarithmic_transform(self, client, sample_image):
        """Test logarithmic transform (good for dark images)."""
        file_id = self.upload_test_image(client, sample_image)
        
        processing_data = {
            'file_id': file_id,
            'operations': [
                {'name': 'logarithmic_transform', 'params': {}}
            ]
        }
        
        response = client.post('/process_image',
                             data=json.dumps(processing_data),
                             content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
    
    def test_process_image_exponential_transform(self, client, sample_image):
        """Test exponential transform (good for bright images)."""
        file_id = self.upload_test_image(client, sample_image)
        
        processing_data = {
            'file_id': file_id,
            'operations': [
                {
                    'name': 'exponential_transform',
                    'params': {'c': 1.5, 'alpha': 1.3}
                }
            ]
        }
        
        response = client.post('/process_image',
                             data=json.dumps(processing_data),
                             content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
    
    def test_process_image_denoise(self, client, sample_image):
        """Test image denoising."""
        file_id = self.upload_test_image(client, sample_image)
        
        processing_data = {
            'file_id': file_id,
            'operations': [
                {
                    'name': 'denoise_image',
                    'params': {'h': 10, 'hColor': 10}
                }
            ]
        }
        
        response = client.post('/process_image',
                             data=json.dumps(processing_data),
                             content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
    
    def test_process_image_sharpen(self, client, sample_image):
        """Test image sharpening."""
        file_id = self.upload_test_image(client, sample_image)
        
        processing_data = {
            'file_id': file_id,
            'operations': [
                {'name': 'sharpen_img', 'params': {}}
            ]
        }
        
        response = client.post('/process_image',
                             data=json.dumps(processing_data),
                             content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
    
    def test_process_image_boost_saturation(self, client, sample_image):
        """Test saturation boosting."""
        file_id = self.upload_test_image(client, sample_image)
        
        processing_data = {
            'file_id': file_id,
            'operations': [
                {
                    'name': 'boost_saturation',
                    'params': {'saturation_scale': 1.8}
                }
            ]
        }
        
        response = client.post('/process_image',
                             data=json.dumps(processing_data),
                             content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
    
    def test_process_image_multiple_operations(self, client, sample_image):
        """Test applying multiple operations in sequence."""
        file_id = self.upload_test_image(client, sample_image)
        
        processing_data = {
            'file_id': file_id,
            'operations': [
                {'name': 'adaptive_brightness', 'params': {}},
                {'name': 'sharpen_img', 'params': {}},
                {
                    'name': 'boost_saturation',
                    'params': {'saturation_scale': 1.3}
                }
            ]
        }
        
        response = client.post('/process_image',
                             data=json.dumps(processing_data),
                             content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['operations_applied'] == 3
    
    def test_process_image_edge_preserving_filter(self, client, sample_image):
        """Test edge preserving filter."""
        file_id = self.upload_test_image(client, sample_image)
        
        processing_data = {
            'file_id': file_id,
            'operations': [
                {
                    'name': 'edge_preserving_filter',
                    'params': {'sigma_s': 80, 'sigma_r': 0.3}
                }
            ]
        }
        
        response = client.post('/process_image',
                             data=json.dumps(processing_data),
                             content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
    
    def test_process_image_bilateral_filter(self, client, sample_image):
        """Test bilateral filter."""
        file_id = self.upload_test_image(client, sample_image)
        
        processing_data = {
            'file_id': file_id,
            'operations': [
                {
                    'name': 'bilateral_filter',
                    'params': {'d': 20, 'sigmaColor': 60, 'sigmaSpace': 60}
                }
            ]
        }
        
        response = client.post('/process_image',
                             data=json.dumps(processing_data),
                             content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
    
    def test_process_image_invalid_file_id(self, client):
        """Test processing with invalid file_id."""
        processing_data = {
            'file_id': 'invalid-file-id',
            'operations': [
                {'name': 'adaptive_brightness', 'params': {}}
            ]
        }
        
        response = client.post('/process_image',
                             data=json.dumps(processing_data),
                             content_type='application/json')
        
        assert response.status_code == 404
    
    def test_process_image_multiple_operations(self, client, sample_image):
        """Test processing image with multiple operations to verify they work together."""
        file_id = self.upload_test_image(client, sample_image)
        
        # Apply multiple operations in sequence
        processing_data = {
            'file_id': file_id,
            'operations': [
                {'name': 'adaptive_brightness', 'params': {}},
                {'name': 'sharpen_img', 'params': {}},
                {'name': 'boost_saturation', 'params': {'saturation_scale': 1.2}}
            ]
        }
        
        response = client.post('/process_image',
                             data=json.dumps(processing_data),
                             content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['operations_applied'] == 3


@pytest.mark.integration
@pytest.mark.requires_dll
class TestVideoProcessingEndpoint:
    """Test video processing endpoint (requires DLL)."""
    
    def test_process_video_dll_unavailable(self, client):
        """Test video processing when DLL is not available."""
        if VIDEO_PROCESSING_AVAILABLE:
            pytest.skip("Video DLL is available, skipping unavailable test")
        
        processing_data = {
            'file_id': 'test-file-id',
            'operations': [
                {'name': 'reverse', 'params': {}}
            ]
        }
        
        response = client.post('/process_video',
                             data=json.dumps(processing_data),
                             content_type='application/json')
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert 'Video processing not available' in data['error']
    
    def test_video_operations_available(self, client, video_dll_available):
        """Test that video operations are available when DLL is present."""
        if not video_dll_available:
            pytest.skip("Video DLL not available")
        
        response = client.get('/get_video_operations')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert len(data) > 0
        
        # Check for expected video operations
        operation_names = [op['name'] for op in data]
        expected_operations = ['reverse', 'swap_channels', 'clip_channel', 'scale_channel']
        
        for expected_op in expected_operations:
            assert expected_op in operation_names


@pytest.mark.integration
class TestDownloadEndpoint:
    """Test file download endpoint."""
    
    def test_download_processed_file(self, client, sample_image):
        """Test downloading a processed file."""
        # First upload and process an image
        with open(sample_image, 'rb') as f:
            data = {
                'file': (f, sample_image.name)
            }
            upload_response = client.post('/upload', data=data)
        
        file_id = json.loads(upload_response.data)['file_id']
        
        # Process the image
        processing_data = {
            'file_id': file_id,
            'operations': [
                {'name': 'adaptive_brightness', 'params': {}}
            ]
        }
        
        process_response = client.post('/process_image',
                                     data=json.dumps(processing_data),
                                     content_type='application/json')
        
        processed_filename = json.loads(process_response.data)['processed_file']
        
        # Download the processed file
        download_response = client.get(f'/download/{processed_filename}')
        assert download_response.status_code == 200
        assert len(download_response.data) > 0
        
        # Check that we got image data
        assert download_response.headers['Content-Type'].startswith('image/')
    
    def test_download_nonexistent_file(self, client):
        """Test downloading a file that doesn't exist."""
        response = client.get('/download/nonexistent.png')
        assert response.status_code == 404


@pytest.mark.integration
class TestEndToEndImageWorkflow:
    """Test complete image processing workflows."""
    
    def test_basic_image_processing_workflow(self, client, sample_image):
        """Test complete basic image processing workflow."""
        # 1. Upload
        with open(sample_image, 'rb') as f:
            upload_data = {
                'file': (f, sample_image.name)
            }
            upload_response = client.post('/upload', data=upload_data)
        
        assert upload_response.status_code == 200
        file_id = json.loads(upload_response.data)['file_id']
        
        # 2. Process with basic enhancement operations
        processing_data = {
            'file_id': file_id,
            'operations': [
                {'name': 'adaptive_brightness', 'params': {}},    # Optimize brightness
                {'name': 'sharpen_img', 'params': {}},           # Add sharpness
                {'name': 'boost_saturation', 'params': {'saturation_scale': 1.3}}  # Enhance colors
            ]
        }
        
        process_response = client.post('/process_image',
                                     data=json.dumps(processing_data),
                                     content_type='application/json')
        
        assert process_response.status_code == 200
        process_data = json.loads(process_response.data)
        assert process_data['success'] is True
        assert process_data['operations_applied'] == 3
        
        # 3. Download
        download_response = client.get(f"/download/{process_data['processed_file']}")
        assert download_response.status_code == 200
        assert len(download_response.data) > 0
    
    def test_advanced_image_processing_workflow(self, client, sample_image):
        """Test complete advanced image processing workflow."""
        # 1. Upload
        with open(sample_image, 'rb') as f:
            upload_data = {
                'file': (f, sample_image.name)
            }
            upload_response = client.post('/upload', data=upload_data)
        
        assert upload_response.status_code == 200
        file_id = json.loads(upload_response.data)['file_id']
        
        # 2. Process with advanced operations
        processing_data = {
            'file_id': file_id,
            'operations': [
                {'name': 'denoise_image', 'params': {'h': 10, 'hColor': 10}},  # Remove noise
                {'name': 'edge_preserving_filter', 'params': {'sigma_s': 60, 'sigma_r': 0.4}},  # Smooth while preserving edges
                {'name': 'laplacian_sharpening', 'params': {'alpha': 0.5}},  # Advanced sharpening
                {'name': 'bilateral_filter', 'params': {'d': 15, 'sigmaColor': 50, 'sigmaSpace': 50}}  # Advanced filtering
            ]
        }
        
        process_response = client.post('/process_image',
                                     data=json.dumps(processing_data),
                                     content_type='application/json')
        
        assert process_response.status_code == 200
        process_data = json.loads(process_response.data)
        assert process_data['success'] is True
        assert process_data['operations_applied'] == 4
        
        # 3. Download
        download_response = client.get(f"/download/{process_data['processed_file']}")
        assert download_response.status_code == 200
        assert len(download_response.data) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])