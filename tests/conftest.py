"""
Pytest configuration and shared fixtures for testing the image and video processing web application.
"""

import pytest
import os
import tempfile
import shutil
import numpy as np
import cv2
from pathlib import Path
import sys

# Add the project root to Python path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import app
import image_functions
from video_wrapper import VIDEO_PROCESSING_AVAILABLE


@pytest.fixture(scope="session")
def project_root():
    """Return the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def sample_images_dir(project_root):
    """Return the path to sample images directory."""
    sample_dir = project_root / "tests" / "sample_images"
    if not sample_dir.exists():
        # Create the directory and a helpful README
        sample_dir.mkdir(parents=True, exist_ok=True)
        readme_path = sample_dir / "README.md"
        if not readme_path.exists():
            with open(readme_path, 'w') as f:
                f.write("# Sample Images Directory\n\n")
                f.write("Add your test images here for pytest testing.\n\n")
                f.write("## Supported formats:\n")
                f.write("- JPG, JPEG, PNG, BMP, TIFF\n\n")
                f.write("## What to add:\n")
                f.write("- Any images you have: photos, screenshots, graphics, etc.\n")
                f.write("- All tests focus on function correctness, not image content\n\n")
                f.write("## Examples:\n")
                f.write("- my_vacation_photo.jpg\n")
                f.write("- desktop_screenshot.png\n")
                f.write("- any_random_image.jpg\n")
        pytest.skip(f"Sample images directory created at {sample_dir}. Please add test images and run again.")
    return sample_dir


@pytest.fixture(scope="session")
def sample_image_paths(sample_images_dir):
    """Return a list of sample image file paths."""
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
    image_paths = []
    
    for ext in image_extensions:
        image_paths.extend(sample_images_dir.glob(f"*{ext}"))
        image_paths.extend(sample_images_dir.glob(f"*{ext.upper()}"))
    
    if not image_paths:
        pytest.skip("No sample images found in sample_images directory")
    
    return sorted(image_paths)








@pytest.fixture
def multiple_sample_images(sample_image_paths):
    """Return multiple sample images for batch testing (up to 3)."""
    max_images = min(3, len(sample_image_paths))
    return sample_image_paths[:max_images]


@pytest.fixture
def sample_image(sample_image_paths):
    """Return the path to a single sample image."""
    return sample_image_paths[0]


@pytest.fixture
def test_image_array(sample_image):
    """Return a sample image as a numpy array."""
    img = cv2.imread(str(sample_image), cv2.IMREAD_COLOR)
    if img is None:
        pytest.skip(f"Could not load image: {sample_image}")
    return img


@pytest.fixture
def synthetic_test_image():
    """Create a synthetic test image for testing."""
    # Create a 100x100x3 test image with gradient
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    
    # Add some patterns for testing
    for i in range(100):
        for j in range(100):
            img[i, j] = [i * 2.55, j * 2.55, (i + j) * 1.275]
    
    return img.astype(np.uint8)


@pytest.fixture
def dark_test_image():
    """Create a dark test image for brightness testing."""
    # Create a very dark image (values 0-50)
    img = np.random.randint(0, 50, (100, 100, 3), dtype=np.uint8)
    return img


@pytest.fixture
def bright_test_image():
    """Create a bright test image for testing."""
    # Create a very bright image (values 200-255)
    img = np.random.randint(200, 255, (100, 100, 3), dtype=np.uint8)
    return img


@pytest.fixture
def noisy_test_image():
    """Create a noisy test image for denoising testing."""
    # Create base image
    img = np.full((100, 100, 3), 128, dtype=np.uint8)
    # Add salt and pepper noise
    noise = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    mask = np.random.random((100, 100, 3)) < 0.1  # 10% noise
    img[mask] = noise[mask]
    return img


def assert_image_changed(original, processed, function_name):
    """Assert that image processing function actually changed the image."""
    assert not np.array_equal(original, processed), f"{function_name} did not change the image"
    assert original.shape == processed.shape, f"{function_name} changed image dimensions"
    assert processed.dtype == original.dtype, f"{function_name} changed image data type"


def assert_brightness_increased(original, processed):
    """Assert that processed image is brighter than original."""
    original_mean = np.mean(original)
    processed_mean = np.mean(processed)
    assert processed_mean > original_mean, f"Brightness not increased: {original_mean} -> {processed_mean}"


def assert_brightness_decreased(original, processed):
    """Assert that processed image is darker than original."""
    original_mean = np.mean(original)
    processed_mean = np.mean(processed)
    assert processed_mean < original_mean, f"Brightness not decreased: {original_mean} -> {processed_mean}"


@pytest.fixture
def flask_app():
    """Create and configure a Flask app instance for testing."""
    # Create temporary directories for testing
    test_upload_dir = tempfile.mkdtemp(prefix="test_uploads_")
    test_processed_dir = tempfile.mkdtemp(prefix="test_processed_")
    
    # Configure the app for testing
    app.app.config.update({
        "TESTING": True,
        "UPLOAD_FOLDER": test_upload_dir,
        "PROCESSED_FOLDER": test_processed_dir,
        "WTF_CSRF_ENABLED": False,
        "SECRET_KEY": "test-secret-key"
    })
    
    yield app.app
    
    # Cleanup temporary directories
    shutil.rmtree(test_upload_dir, ignore_errors=True)
    shutil.rmtree(test_processed_dir, ignore_errors=True)


@pytest.fixture
def client(flask_app):
    """Create a test client for the Flask app."""
    return flask_app.test_client()


@pytest.fixture
def runner(flask_app):
    """Create a test runner for the Flask app."""
    return flask_app.test_cli_runner()


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def mock_file_upload(sample_image):
    """Create a mock file upload for testing."""
    def _create_mock_upload(filename=None):
        if filename is None:
            filename = sample_image.name
        
        with open(sample_image, 'rb') as f:
            content = f.read()
        
        from io import BytesIO
        return BytesIO(content), filename
    
    return _create_mock_upload


@pytest.fixture(scope="session")
def video_dll_available():
    """Check if video processing DLL is available."""
    return VIDEO_PROCESSING_AVAILABLE


def pytest_configure(config):
    """Pytest configuration hook."""
    # Ensure test directories exist
    test_dir = Path(__file__).parent
    sample_images_dir = test_dir / "sample_images"
    
    if not sample_images_dir.exists():
        print(f"Warning: Sample images directory not found: {sample_images_dir}")
        print("Please create the directory and add sample images for testing.")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test names and requirements."""
    for item in items:
        # Add markers based on test file names
        if "unit" in item.fspath.basename:
            item.add_marker(pytest.mark.unit)
        elif "integration" in item.fspath.basename:
            item.add_marker(pytest.mark.integration)
        elif "functional" in item.fspath.basename:
            item.add_marker(pytest.mark.functional)
        
        # Add marker for tests that require DLL
        if "video" in item.name.lower() or "dll" in item.name.lower():
            item.add_marker(pytest.mark.requires_dll)
        
        # Add slow marker for functional tests
        if "functional" in item.fspath.basename or "e2e" in item.name.lower():
            item.add_marker(pytest.mark.slow)


# Utility functions for tests
def create_test_image(width=100, height=100, channels=3):
    """Create a test image with specified dimensions."""
    if channels == 1:
        return np.random.randint(0, 256, (height, width), dtype=np.uint8)
    else:
        return np.random.randint(0, 256, (height, width, channels), dtype=np.uint8)


def assert_image_equal(img1, img2, tolerance=0):
    """Assert that two images are equal within tolerance."""
    assert img1.shape == img2.shape, f"Image shapes don't match: {img1.shape} vs {img2.shape}"
    
    if tolerance == 0:
        assert np.array_equal(img1, img2), "Images are not exactly equal"
    else:
        diff = np.abs(img1.astype(np.float32) - img2.astype(np.float32))
        max_diff = np.max(diff)
        assert max_diff <= tolerance, f"Images differ by more than tolerance: {max_diff} > {tolerance}"


def assert_image_valid(img):
    """Assert that an image is valid."""
    assert img is not None, "Image is None"
    assert isinstance(img, np.ndarray), f"Image is not numpy array, got {type(img)}"
    assert img.dtype == np.uint8, f"Image dtype is not uint8, got {img.dtype}"
    assert len(img.shape) in [2, 3], f"Invalid image shape: {img.shape}"
    if len(img.shape) == 3:
        assert img.shape[2] in [1, 3, 4], f"Invalid number of channels: {img.shape[2]}"