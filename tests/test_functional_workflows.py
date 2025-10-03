"""
Functional tests for complete workflows.
Tests end-to-end scenarios that users would perform on the web application.
"""

import pytest
import json
import time
from pathlib import Path
import random

from video_wrapper import VIDEO_PROCESSING_AVAILABLE


@pytest.mark.functional
class TestCompleteImageWorkflows:
    """Test complete user workflows for image processing."""
    
    def test_basic_image_enhancement_workflow(self, client, sample_image_paths):
        """Test basic image enhancement workflow with multiple images."""
        # Test with first 5 images or all available images (whichever is fewer)
        max_test_images = min(5, len(sample_image_paths))
        test_images = sample_image_paths[:max_test_images]
        
        for image_path in test_images:
            # 1. Upload image
            with open(image_path, 'rb') as f:
                data = {'file': (f, image_path.name)}
                upload_response = client.post('/upload', data=data)
            
            assert upload_response.status_code == 200
            file_id = json.loads(upload_response.data)['file_id']
            
            # 2. Apply basic enhancement operations
            processing_data = {
                'file_id': file_id,
                'operations': [
                    {'name': 'adaptive_brightness', 'params': {}},
                    {'name': 'sharpen_img', 'params': {}},
                    {'name': 'boost_saturation', 'params': {'saturation_scale': 1.3}}
                ]
            }
            
            process_response = client.post('/process_image',
                                         data=json.dumps(processing_data),
                                         content_type='application/json')
            
            assert process_response.status_code == 200
            process_data = json.loads(process_response.data)
            assert process_data['success'] is True
            assert process_data['operations_applied'] == 3
            
            # 3. Download processed image
            download_response = client.get(f"/download/{process_data['processed_file']}")
            assert download_response.status_code == 200
            assert len(download_response.data) > 0
    
    def test_different_processing_approaches(self, client, multiple_sample_images):
        """Test different processing approaches on the same or different images."""
        
        # Approach 1: Basic enhancement
        image1 = multiple_sample_images[0]
        with open(image1, 'rb') as f:
            data = {'file': (f, image1.name)}
            upload_response = client.post('/upload', data=data)
        
        file_id = json.loads(upload_response.data)['file_id']
        
        basic_processing = {
            'file_id': file_id,
            'operations': [
                {'name': 'adaptive_brightness', 'params': {}},
                {'name': 'sharpen_img', 'params': {}},
                {'name': 'boost_saturation', 'params': {'saturation_scale': 1.2}}
            ]
        }
        
        process_response = client.post('/process_image',
                                     data=json.dumps(basic_processing),
                                     content_type='application/json')
        
        assert process_response.status_code == 200
        process_data = json.loads(process_response.data)
        assert process_data['operations_applied'] == 3
        
        # Approach 2: Advanced filtering (if we have more images)
        if len(multiple_sample_images) > 1:
            image2 = multiple_sample_images[1]
            with open(image2, 'rb') as f:
                data = {'file': (f, image2.name)}
                upload_response = client.post('/upload', data=data)
            
            file_id = json.loads(upload_response.data)['file_id']
            
            advanced_processing = {
                'file_id': file_id,
                'operations': [
                    {'name': 'denoise_image', 'params': {'h': 10, 'hColor': 10}},
                    {'name': 'bilateral_filter', 'params': {'d': 15, 'sigmaColor': 50, 'sigmaSpace': 50}},
                    {'name': 'edge_preserving_filter', 'params': {'sigma_s': 60, 'sigma_r': 0.4}},
                    {'name': 'laplacian_sharpening', 'params': {'alpha': 0.5}}
                ]
            }
            
            process_response = client.post('/process_image',
                                         data=json.dumps(advanced_processing),
                                         content_type='application/json')
            
            assert process_response.status_code == 200
            process_data = json.loads(process_response.data)
            assert process_data['operations_applied'] == 4
    
    def test_progressive_enhancement_workflow(self, client, sample_image):
        """Test progressive enhancement - applying operations step by step."""
        # Upload image
        with open(sample_image, 'rb') as f:
            data = {'file': (f, sample_image.name)}
            upload_response = client.post('/upload', data=data)
        
        file_id = json.loads(upload_response.data)['file_id']
        
        # Step 1: Basic brightness adjustment
        step1_data = {
            'file_id': file_id,
            'operations': [{'name': 'adaptive_brightness', 'params': {}}]
        }
        
        step1_response = client.post('/process_image',
                                   data=json.dumps(step1_data),
                                   content_type='application/json')
        assert step1_response.status_code == 200
        
        # Step 2: Add sharpening
        step2_data = {
            'file_id': file_id,
            'operations': [
                {'name': 'adaptive_brightness', 'params': {}},
                {'name': 'sharpen_img', 'params': {}}
            ]
        }
        
        step2_response = client.post('/process_image',
                                   data=json.dumps(step2_data),
                                   content_type='application/json')
        assert step2_response.status_code == 200
        
        # Step 3: Final color enhancement
        step3_data = {
            'file_id': file_id,
            'operations': [
                {'name': 'adaptive_brightness', 'params': {}},
                {'name': 'sharpen_img', 'params': {}},
                {'name': 'boost_saturation', 'params': {'saturation_scale': 1.4}}
            ]
        }
        
        step3_response = client.post('/process_image',
                                   data=json.dumps(step3_data),
                                   content_type='application/json')
        assert step3_response.status_code == 200
        final_data = json.loads(step3_response.data)
        
        # Download final result
        download_response = client.get(f"/download/{final_data['processed_file']}")
        assert download_response.status_code == 200
    
    def test_intensive_processing_workflow(self, client, sample_image):
        """Test intensive processing with many operations."""
        with open(sample_image, 'rb') as f:
            data = {'file': (f, sample_image.name)}
            upload_response = client.post('/upload', data=data)
        
        file_id = json.loads(upload_response.data)['file_id']
        
        # Apply comprehensive processing pipeline
        intensive_processing = {
            'file_id': file_id,
            'operations': [
                {'name': 'denoise_image', 'params': {'h': 8, 'hColor': 8}},
                {'name': 'adaptive_brightness', 'params': {}},
                {'name': 'edge_preserving_filter', 'params': {'sigma_s': 70, 'sigma_r': 0.35}},
                {'name': 'laplacian_sharpening', 'params': {'alpha': 0.4}},
                {'name': 'boost_saturation', 'params': {'saturation_scale': 1.3}},
                {'name': 'bilateral_filter', 'params': {'d': 12, 'sigmaColor': 40, 'sigmaSpace': 40}},
                {'name': 'restore_edges', 'params': {}}
            ]
        }
        
        process_response = client.post('/process_image',
                                     data=json.dumps(intensive_processing),
                                     content_type='application/json')
        
        assert process_response.status_code == 200
        process_data = json.loads(process_response.data)
        assert process_data['success'] is True
        assert process_data['operations_applied'] == 7
        
        # Verify download works
        download_response = client.get(f"/download/{process_data['processed_file']}")
        assert download_response.status_code == 200


@pytest.mark.functional
class TestBatchProcessingWorkflows:
    """Test batch processing multiple images."""
    
    def test_batch_process_multiple_images(self, client, multiple_sample_images):
        """Test processing multiple images in batch with basic operations."""
        processed_files = []
        
        for image in multiple_sample_images:
            # Upload
            with open(image, 'rb') as f:
                data = {'file': (f, image.name)}
                upload_response = client.post('/upload', data=data)
            
            file_id = json.loads(upload_response.data)['file_id']
            
            # Process with basic operations
            processing_data = {
                'file_id': file_id,
                'operations': [
                    {'name': 'adaptive_brightness', 'params': {}},
                    {'name': 'sharpen_img', 'params': {}},
                    {'name': 'boost_saturation', 'params': {'saturation_scale': 1.3}}
                ]
            }
            
            process_response = client.post('/process_image',
                                         data=json.dumps(processing_data),
                                         content_type='application/json')
            
            assert process_response.status_code == 200
            process_data = json.loads(process_response.data)
            processed_files.append(process_data['processed_file'])
        
        # Verify all files can be downloaded
        for processed_file in processed_files:
            download_response = client.get(f'/download/{processed_file}')
            assert download_response.status_code == 200
    
    def test_batch_process_different_operations(self, client, multiple_sample_images):
        """Test processing multiple images with different operations."""
        operation_sets = [
            [{'name': 'logarithmic_transform', 'params': {}}],
            [{'name': 'denoise_image', 'params': {'h': 10, 'hColor': 10}}],
            [{'name': 'bilateral_filter', 'params': {'d': 15, 'sigmaColor': 50, 'sigmaSpace': 50}}]
        ]
        
        processed_files = []
        
        for i, image in enumerate(multiple_sample_images):
            # Upload
            with open(image, 'rb') as f:
                data = {'file': (f, image.name)}
                upload_response = client.post('/upload', data=data)
            
            file_id = json.loads(upload_response.data)['file_id']
            
            # Use different operations for each image
            operation_set = operation_sets[i % len(operation_sets)]
            processing_data = {
                'file_id': file_id,
                'operations': operation_set
            }
            
            process_response = client.post('/process_image',
                                         data=json.dumps(processing_data),
                                         content_type='application/json')
            
            assert process_response.status_code == 200
            process_data = json.loads(process_response.data)
            processed_files.append(process_data['processed_file'])
        
        # Verify all files can be downloaded
        for processed_file in processed_files:
            download_response = client.get(f'/download/{processed_file}')
            assert download_response.status_code == 200


@pytest.mark.functional
class TestErrorRecoveryWorkflows:
    """Test error handling and recovery in workflows."""
    
    def test_workflow_with_invalid_operations(self, client, sample_image):
        """Test workflow resilience with invalid operations."""
        with open(sample_image, 'rb') as f:
            data = {'file': (f, sample_image.name)}
            upload_response = client.post('/upload', data=data)
        
        file_id = json.loads(upload_response.data)['file_id']
        
        # Try processing with invalid operation - app should skip invalid ones
        invalid_processing = {
            'file_id': file_id,
            'operations': [
                {'name': 'adaptive_brightness', 'params': {}},  # Valid
                {'name': 'invalid_operation', 'params': {}},   # Invalid (silently skipped)
                {'name': 'sharpen_img', 'params': {}}          # Valid
            ]
        }
        
        process_response = client.post('/process_image',
                                     data=json.dumps(invalid_processing),
                                     content_type='application/json')
        
        # Should succeed (invalid operations are silently skipped)
        assert process_response.status_code == 200
        process_data = json.loads(process_response.data)
        # Counts all operations in the list, even invalid ones
        assert process_data['operations_applied'] == 3
    
    def test_workflow_with_extreme_parameters(self, client, sample_image):
        """Test workflow with extreme parameter values."""
        with open(sample_image, 'rb') as f:
            data = {'file': (f, sample_image.name)}
            upload_response = client.post('/upload', data=data)
        
        file_id = json.loads(upload_response.data)['file_id']
        
        # Process with extreme parameters
        extreme_processing = {
            'file_id': file_id,
            'operations': [
                {'name': 'exponential_transform', 'params': {'c': 5.0, 'alpha': 3.0}},
                {'name': 'boost_saturation', 'params': {'saturation_scale': 3.0}},
                {'name': 'bilateral_filter', 'params': {'d': 50, 'sigmaColor': 150, 'sigmaSpace': 150}}
            ]
        }
        
        process_response = client.post('/process_image',
                                     data=json.dumps(extreme_processing),
                                     content_type='application/json')
        
        assert process_response.status_code == 200
        process_data = json.loads(process_response.data)
        assert process_data['success'] is True


@pytest.mark.functional
@pytest.mark.requires_dll
class TestVideoWorkflows:
    """Test video processing workflows (requires DLL)."""
    
    def test_video_processing_availability_check(self, client, video_dll_available):
        """Test video processing availability workflow."""
        if not video_dll_available:
            # Test unavailable workflow
            processing_data = {
                'file_id': 'test-file-id',
                'operations': [{'name': 'reverse', 'params': {}}]
            }
            
            response = client.post('/process_video',
                                 data=json.dumps(processing_data),
                                 content_type='application/json')
            
            assert response.status_code == 500
            error_data = json.loads(response.data)
            assert 'not available' in error_data['error']
        else:
            # Test available workflow - just check operations are available
            response = client.get('/get_video_operations')
            assert response.status_code == 200
            operations = json.loads(response.data)
            assert len(operations) > 0


@pytest.mark.functional
@pytest.mark.slow
class TestPerformanceWorkflows:
    """Test performance-related workflows."""
    
    def test_concurrent_processing_simulation(self, client, sample_image_paths):
        """Simulate concurrent processing requests."""
        # Process multiple images "concurrently" (sequential but rapid)
        max_concurrent = min(5, len(sample_image_paths))
        test_images = sample_image_paths[:max_concurrent]
        results = []
        
        for image_path in test_images:
            # Upload
            with open(image_path, 'rb') as f:
                data = {'file': (f, image_path.name)}
                upload_response = client.post('/upload', data=data)
            
            file_id = json.loads(upload_response.data)['file_id']
            
            # Process with random operations
            operations = [
                {'name': 'adaptive_brightness', 'params': {}},
                {'name': 'sharpen_img', 'params': {}},
                {'name': 'boost_saturation', 'params': {'saturation_scale': random.uniform(1.1, 1.8)}}
            ]
            
            processing_data = {
                'file_id': file_id,
                'operations': operations
            }
            
            process_response = client.post('/process_image',
                                         data=json.dumps(processing_data),
                                         content_type='application/json')
            
            assert process_response.status_code == 200
            results.append(json.loads(process_response.data))
        
        # Verify all processed successfully
        for result in results:
            assert result['success'] is True
            assert result['operations_applied'] == 3
    
    def test_large_batch_workflow(self, client, sample_image_paths):
        """Test processing larger batch of images."""
        # Use more images for stress test (up to 10)
        max_batch_size = min(10, len(sample_image_paths))
        test_images = sample_image_paths[:max_batch_size]
        success_count = 0
        
        for image_path in test_images:
            try:
                # Upload
                with open(image_path, 'rb') as f:
                    data = {'file': (f, image_path.name)}
                    upload_response = client.post('/upload', data=data)
                
                if upload_response.status_code != 200:
                    continue
                
                file_id = json.loads(upload_response.data)['file_id']
                
                # Simple processing
                processing_data = {
                    'file_id': file_id,
                    'operations': [
                        {'name': 'adaptive_brightness', 'params': {}}
                    ]
                }
                
                process_response = client.post('/process_image',
                                             data=json.dumps(processing_data),
                                             content_type='application/json')
                
                if process_response.status_code == 200:
                    success_count += 1
                    
            except Exception as e:
                # Continue with next image if one fails
                continue
        
        # Should have at least 80% success rate
        success_rate = success_count / len(test_images)
        assert success_rate >= 0.8, f"Success rate too low: {success_rate}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "functional"])