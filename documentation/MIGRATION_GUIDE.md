# Migration Guide: video_wrapper_enhanced.py → video_wrapper.py

The two video wrapper files have been merged into a single unified `video_wrapper.py`. This document explains the changes and how to update your code.

## What Changed?

- ✅ `video_wrapper.py` now includes all functionality from `video_wrapper_enhanced.py`
- ✅ `video_wrapper_enhanced.py` is deprecated and can be deleted
- ✅ All existing code using the original `video_wrapper.py` continues to work
- ✅ New code gets automatic format detection for MP4/MOV files

## API Changes

### Before (video_wrapper_enhanced.py)

```python
from video_wrapper_enhanced import (
    StandardVideoProcessor,
    VideoProcessor,
    auto_detect_processor,
    STANDARD_FORMAT_SUPPORT
)

# Create instance
processor = StandardVideoProcessor()

# Or use auto-detect
processor = auto_detect_processor('file.mp4')

# Use it
video = processor.decode_video('input.mp4')
processor.reverse_video(video)
processor.encode_video('output.mp4', video, codec='libx264', fps=30)
processor.free_video(video)
```

### After (unified video_wrapper.py)

```python
from video_wrapper import (
    video_processor,  # Global instance (easiest)
    VideoProcessor,   # If you need your own instance
    STANDARD_FORMAT_SUPPORT,
    is_standard_format
)

# Use global instance (recommended)
video = video_processor.decode_video('input.mp4')  # Auto-detects MP4
video_processor.reverse_video(video, mode='structured')
video_processor.encode_video('output.mp4', video, codec='libx264', fps=30)
video_processor.free_video(video, mode='structured')

# Or create your own instance
processor = VideoProcessor()
video = processor.decode_video('input.mp4')
processor.reverse_video(video, mode='structured')
processor.encode_video('output.mp4', video, codec='libx264', fps=30)
processor.free_video(video, mode='structured')
```

## Key Differences

### 1. Import Statement
```python
# OLD
from video_wrapper_enhanced import StandardVideoProcessor
processor = StandardVideoProcessor()

# NEW
from video_wrapper import video_processor
# Or: processor = VideoProcessor()
```

### 2. Function Calls
```python
# OLD (video_wrapper_enhanced.py)
processor.reverse_video(video)
processor.swap_channels(video, 0, 1)

# NEW (unified video_wrapper.py)
video_processor.reverse_video(video, mode='structured')
video_processor.swap_channels(video, 0, 1, mode='structured')
```

**Note:** You need to specify `mode='structured'` for standard format videos since they decode to `SVideo` structure.

### 3. Auto-Detection
```python
# OLD
from video_wrapper_enhanced import auto_detect_processor
processor = auto_detect_processor('file.mp4')

# NEW - Not needed! Auto-detection is built-in
from video_wrapper import video_processor
# decode_video() automatically detects format based on extension
video = video_processor.decode_video('file.mp4')
```

### 4. Format Checking
```python
# OLD
from video_wrapper_enhanced import is_standard_format

# NEW - Same function, different module
from video_wrapper import is_standard_format
```

## Migration Steps

### Step 1: Update Imports

Find and replace in your Python files:

```python
# Replace this:
from video_wrapper_enhanced import

# With this:
from video_wrapper import
```

### Step 2: Update Class Names

```python
# Replace this:
StandardVideoProcessor()

# With this:
video_processor  # Use the global instance
# Or
VideoProcessor()  # Create your own instance
```

### Step 3: Add mode Parameters

For operations on standard format videos (MP4/MOV), add `mode='structured'`:

```python
# Add mode='structured' to processing functions:
video_processor.reverse_video(video, mode='structured')
video_processor.swap_channels(video, 0, 2, mode='structured')
video_processor.clip_channel(video, 0, 50, 200, mode='structured')
video_processor.scale_channel(video, 1, 1.2, mode='structured')
video_processor.free_video(video, mode='structured')
```

**Why?** The unified wrapper supports 3 video structure types (Video, SVideo, MVideo). Standard formats decode to SVideo, so we need to specify `mode='structured'`.

### Step 4: Remove Old File (After Testing)

Once everything works:
```bash
# Delete the old file
rm video_wrapper_enhanced.py
```

## Complete Example

### Before (using video_wrapper_enhanced.py)

```python
from video_wrapper_enhanced import (
    StandardVideoProcessor,
    STANDARD_FORMAT_SUPPORT
)

if not STANDARD_FORMAT_SUPPORT:
    raise RuntimeError("FFmpeg not available")

processor = StandardVideoProcessor()

# Get info
info = processor.get_video_info('video.mp4')
print(f"{info['width']}x{info['height']}")

# Process
video = processor.decode_video('video.mp4')
processor.reverse_video(video)
processor.swap_channels(video, 0, 2)
processor.encode_video('output.mp4', video, codec='libx264', fps=30)
processor.free_video(video)
```

### After (using unified video_wrapper.py)

```python
from video_wrapper import (
    video_processor,
    STANDARD_FORMAT_SUPPORT
)

if not STANDARD_FORMAT_SUPPORT:
    raise RuntimeError("FFmpeg not available")

# Get info
info = video_processor.get_video_info('video.mp4')
print(f"{info['width']}x{info['height']}")

# Process
video = video_processor.decode_video('video.mp4')
video_processor.reverse_video(video, mode='structured')
video_processor.swap_channels(video, 0, 2, mode='structured')
video_processor.encode_video('output.mp4', video, codec='libx264', fps=30)
video_processor.free_video(video, mode='structured')
```

## Compatibility Matrix

| Feature | video_wrapper_enhanced.py | video_wrapper.py (unified) |
|---------|---------------------------|----------------------------|
| Custom format support | ✅ | ✅ |
| Standard format support (MP4/MOV) | ✅ | ✅ |
| Auto format detection | ✅ | ✅ (built-in) |
| Video/SVideo/MVideo modes | ❌ (SVideo only) | ✅ (all 3 modes) |
| Backward compatible | ❌ | ✅ |
| Global instance | ❌ | ✅ |
| get_video_info() | ✅ | ✅ |

## Benefits of Unified Wrapper

1. **Single file to maintain** - No confusion about which wrapper to use
2. **Backward compatible** - Old code using `video_wrapper.py` still works
3. **Forward compatible** - New features available to all users
4. **Graceful degradation** - Works without FFmpeg, just with reduced functionality
5. **More flexible** - Supports all 3 video structure types
6. **Easier deployment** - One less file to worry about

## Troubleshooting

### "AttributeError: 'VideoProcessor' object has no attribute 'reverse_video'"

You forgot to add the mode parameter:
```python
# Wrong:
processor.reverse_video(video)

# Right:
processor.reverse_video(video, mode='structured')
```

### "RuntimeError: Standard format support not available"

You tried to process an MP4/MOV file without FFmpeg:
```python
# Check first:
if STANDARD_FORMAT_SUPPORT:
    video = video_processor.decode_video('file.mp4')
else:
    print("Install FFmpeg for MP4 support")
```

### Old imports not working

Update your imports:
```python
# Old:
from video_wrapper_enhanced import StandardVideoProcessor

# New:
from video_wrapper import video_processor
```

## Testing Your Migration

Run this test to verify everything works:

```python
from video_wrapper import (
    video_processor,
    VIDEO_PROCESSING_AVAILABLE,
    STANDARD_FORMAT_SUPPORT
)

print(f"Video Processing: {VIDEO_PROCESSING_AVAILABLE}")
print(f"Standard Formats: {STANDARD_FORMAT_SUPPORT}")

if VIDEO_PROCESSING_AVAILABLE:
    print("✅ Migration successful!")
else:
    print("❌ Something went wrong")
```

## Need Help?

See `video_wrapper_usage_examples.py` for complete examples of the new API.
