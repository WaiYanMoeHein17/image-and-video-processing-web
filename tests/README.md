# Test Suite

Comprehensive pytest test suite for the image and video processing web application.

## Quick Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Add Test Images
```bash
# Add any images to tests/sample_images/
# Any format works: JPG, PNG, BMP, TIFF
# Any content works: photos, screenshots, graphics, etc.
```

## Running Tests

### Basic Usage
```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_unit_image_functions.py
```

### Test Categories
```bash
# Run only functional tests
pytest -m functional

# Skip slow tests
pytest -m "not slow"

# Skip video tests (if no DLL)
pytest -m "not requires_dll"
```

### Coverage
```bash
# Run with coverage report
pytest --cov=app --cov=image_functions --cov=video_wrapper
```

## Expected Results
```
==== 84 passed, 2 skipped in ~6s ====
```
- **84 passed**: All functionality working
- **2 skipped**: Video tests (if video_functions.dll unavailable)

## Test Structure
- `test_unit_image_functions.py` - Tests for 15+ image processing functions
- `test_unit_flask_app.py` - Tests for Flask app components  
- `test_integration_api.py` - Tests for API endpoints
- `test_functional_workflows.py` - Tests for complete user workflows
- `conftest.py` - Shared fixtures and test utilities
- `sample_images/` - Add your test images here (any images work!)

## Troubleshooting

**No images found**: Add images to `tests/sample_images/`
**Import errors**: Run from project root directory
**DLL tests skip**: Normal if video_functions.dll not compiled

## Key Features
- ✅ Works with **any image content**
- ✅ Automatic test discovery
- ✅ Comprehensive coverage (unit, integration, functional)
- ✅ Performance and error handling tests
- ✅ Synthetic test images for controlled scenarios