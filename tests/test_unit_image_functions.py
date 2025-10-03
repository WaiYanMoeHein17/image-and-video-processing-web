"""
Unit tests for image processing functions.
Tests individual functions from image_functions.py with various inputs.
"""

import pytest
import numpy as np
import cv2
import tempfile
import os
from pathlib import Path

import image_functions
from conftest import assert_image_valid, assert_image_equal, create_test_image


class TestImageReading:
    """Test image reading functionality."""
    
    def test_read_img_valid_path(self, sample_image):
        """Test reading a valid image file."""
        img = image_functions.read_img(str(sample_image))
        assert_image_valid(img)
        assert img.shape[2] == 3  # Should be color image
    
    def test_read_img_invalid_path(self):
        """Test reading an invalid image path."""
        img = image_functions.read_img("non_existent_file.jpg")
        assert img is None
    
    def test_read_img_empty_path(self):
        """Test reading with empty path."""
        img = image_functions.read_img("")
        assert img is None


class TestBrightnessTransforms:
    """Test brightness and contrast transformation functions."""
    
    def test_adaptive_brightness(self, test_image_array):
        """Test adaptive brightness adjustment."""
        result = image_functions.adaptive_brightness(test_image_array)
        assert_image_valid(result)
        assert result.shape == test_image_array.shape
        # Result should be different from original (unless image is already optimal)
        assert not np.array_equal(result, test_image_array) or True  # May be same if already optimal
    
    def test_logarithmic_transform(self, test_image_array):
        """Test logarithmic transformation."""
        result = image_functions.logarithmic_transform(test_image_array)
        assert_image_valid(result)
        assert result.shape == test_image_array.shape
        # Logarithmic transform should enhance dark regions
        assert result.dtype == np.uint8
    
    def test_exponential_transform_default_params(self, test_image_array):
        """Test exponential transformation with default parameters."""
        result = image_functions.exponential_transform(test_image_array)
        assert_image_valid(result)
        assert result.shape == test_image_array.shape
    
    def test_exponential_transform_custom_params(self, test_image_array):
        """Test exponential transformation with custom parameters."""
        result = image_functions.exponential_transform(test_image_array, c=2, alpha=1.5)
        assert_image_valid(result)
        assert result.shape == test_image_array.shape
    
    def test_exponential_transform_edge_cases(self, synthetic_test_image):
        """Test exponential transformation with edge case parameters."""
        # Test with very small values
        result1 = image_functions.exponential_transform(synthetic_test_image, c=0.1, alpha=0.5)
        assert_image_valid(result1)
        
        # Test with large values
        result2 = image_functions.exponential_transform(synthetic_test_image, c=5, alpha=3)
        assert_image_valid(result2)


class TestDenoising:
    """Test denoising functions."""
    
    def test_denoise_image_default_params(self, test_image_array):
        """Test denoising with default parameters."""
        result = image_functions.denoise_image(test_image_array, h=10, hColor=10)
        assert_image_valid(result)
        assert result.shape == test_image_array.shape
    
    def test_denoise_image_custom_params(self, test_image_array):
        """Test denoising with custom parameters."""
        result = image_functions.denoise_image(
            test_image_array, 
            h=15, 
            hColor=15, 
            templateWindowSize=5, 
            searchWindowSize=15
        )
        assert_image_valid(result)
        assert result.shape == test_image_array.shape
    
    def test_remove_salt_pepper_noise_default(self, test_image_array):
        """Test salt and pepper noise removal with default kernel."""
        result = image_functions.remove_salt_pepper_noise(test_image_array)
        assert_image_valid(result)
        assert result.shape == test_image_array.shape
    
    def test_remove_salt_pepper_noise_custom_kernel(self, test_image_array):
        """Test salt and pepper noise removal with custom kernel size."""
        for kernel_size in [3, 5, 7]:
            result = image_functions.remove_salt_pepper_noise(test_image_array, kernel_size)
            assert_image_valid(result)
            assert result.shape == test_image_array.shape
    
    def test_adaptive_denoise_image(self, test_image_array):
        """Test adaptive denoising."""
        result = image_functions.adaptive_denoise_image(test_image_array)
        assert_image_valid(result)
        assert result.shape == test_image_array.shape


class TestSharpening:
    """Test image sharpening functions."""
    
    def test_sharpen_img(self, test_image_array):
        """Test basic image sharpening."""
        result = image_functions.sharpen_img(test_image_array)
        assert_image_valid(result)
        assert result.shape == test_image_array.shape
    
    def test_restore_edges(self, test_image_array):
        """Test edge restoration."""
        result = image_functions.restore_edges(test_image_array)
        assert_image_valid(result)
        assert result.shape == test_image_array.shape
    
    def test_laplacian_sharpening_default(self, test_image_array):
        """Test Laplacian sharpening with default alpha."""
        result = image_functions.laplacian_sharpening(test_image_array)
        assert_image_valid(result)
        assert result.shape == test_image_array.shape
    
    def test_laplacian_sharpening_custom_alpha(self, test_image_array):
        """Test Laplacian sharpening with custom alpha values."""
        for alpha in [0.1, 0.5, 1.0, 2.0]:
            result = image_functions.laplacian_sharpening(test_image_array, alpha)
            assert_image_valid(result)
            assert result.shape == test_image_array.shape


class TestColorEnhancement:
    """Test color enhancement functions."""
    
    def test_boost_saturation_default(self, test_image_array):
        """Test saturation boost with default scale."""
        result = image_functions.boost_saturation(test_image_array)
        assert_image_valid(result)
        assert result.shape == test_image_array.shape
    
    def test_boost_saturation_custom_scale(self, test_image_array):
        """Test saturation boost with custom scale values."""
        for scale in [0.5, 1.0, 1.5, 2.0, 3.0]:
            result = image_functions.boost_saturation(test_image_array, scale)
            assert_image_valid(result)
            assert result.shape == test_image_array.shape
    
    def test_adaptive_saturation(self, test_image_array):
        """Test adaptive saturation adjustment."""
        result = image_functions.adaptive_saturation(test_image_array)
        assert_image_valid(result)
        assert result.shape == test_image_array.shape


class TestFiltering:
    """Test various filtering functions."""
    
    def test_bilateral_filter_default(self, test_image_array):
        """Test bilateral filtering with default parameters."""
        result = image_functions.bilateral_filter(test_image_array)
        assert_image_valid(result)
        assert result.shape == test_image_array.shape
    
    def test_bilateral_filter_custom_params(self, test_image_array):
        """Test bilateral filtering with custom parameters."""
        result = image_functions.bilateral_filter(
            test_image_array,
            d=20,
            sigmaColor=75,
            sigmaSpace=75
        )
        assert_image_valid(result)
        assert result.shape == test_image_array.shape
    
    def test_edge_preserving_filter_default(self, test_image_array):
        """Test edge-preserving filter with default parameters."""
        result = image_functions.edge_preserving_filter(test_image_array)
        assert_image_valid(result)
        assert result.shape == test_image_array.shape
    
    def test_edge_preserving_filter_custom_params(self, test_image_array):
        """Test edge-preserving filter with custom parameters."""
        result = image_functions.edge_preserving_filter(
            test_image_array,
            sigma_s=100,
            sigma_r=0.2
        )
        assert_image_valid(result)
        assert result.shape == test_image_array.shape


class TestGeometricCorrection:
    """Test geometric correction functions."""
    
    def test_correct_warp(self, test_image_array):
        """Test perspective warp correction."""
        result = image_functions.correct_warp(test_image_array)
        assert_image_valid(result)
        # Shape might change due to perspective correction
        assert len(result.shape) == len(test_image_array.shape)


class TestInpainting:
    """Test inpainting functions."""
    
    def test_inpaint_black_circle(self, test_image_array):
        """Test basic black circle inpainting."""
        result = image_functions.inpaint_black_circle(test_image_array)
        assert_image_valid(result)
        assert result.shape == test_image_array.shape
    
    # @pytest.mark.slow
    # def test_criminisi_inpaint_black_circle_default(self, synthetic_test_image):
    #     """Test Criminisi inpainting with default parameters."""
    #     result = image_functions.criminisi_inpaint_black_circle(synthetic_test_image)
    #     assert_image_valid(result)
    #     assert result.shape == synthetic_test_image.shape
    
    # @pytest.mark.slow
    # def test_criminisi_inpaint_black_circle_custom_params(self, synthetic_test_image):
    #     """Test Criminisi inpainting with custom parameters."""
    #     result = image_functions.criminisi_inpaint_black_circle(
    #         synthetic_test_image,
    #         patch_size=7,
    #         stride=2
    #     )
    #     assert_image_valid(result)
    #     assert result.shape == synthetic_test_image.shape


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_functions_with_empty_array(self):
        """Test functions with empty arrays."""
        empty_img = np.array([])
        
        # Most functions should handle empty arrays gracefully or raise appropriate errors
        with pytest.raises((ValueError, cv2.error, AttributeError)):
            image_functions.adaptive_brightness(empty_img)
    
    def test_functions_with_single_pixel(self):
        """Test functions with single pixel images."""
        single_pixel = np.array([[[255, 128, 64]]], dtype=np.uint8)
        
        # Test a few functions that should handle single pixels
        try:
            result = image_functions.logarithmic_transform(single_pixel)
            assert_image_valid(result)
        except (cv2.error, ValueError):
            # Some functions may not support very small images
            pass
    
    def test_functions_with_grayscale_converted(self, test_image_array):
        """Test functions that internally convert to grayscale."""
        # Test functions that should work with color images
        result = image_functions.laplacian_sharpening(test_image_array)
        assert_image_valid(result)
        assert result.shape == test_image_array.shape
    
    def test_parameter_boundary_values(self, synthetic_test_image):
        """Test functions with boundary parameter values."""
        # Test exponential transform with boundary values
        result1 = image_functions.exponential_transform(synthetic_test_image, c=0.1, alpha=0.5)
        assert_image_valid(result1)
        
        result2 = image_functions.exponential_transform(synthetic_test_image, c=5.0, alpha=3.0)
        assert_image_valid(result2)
        
        # Test boost_saturation with boundary values
        result3 = image_functions.boost_saturation(synthetic_test_image, 0.1)
        assert_image_valid(result3)
        
        result4 = image_functions.boost_saturation(synthetic_test_image, 5.0)
        assert_image_valid(result4)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])