# FFmpeg Integration Guide

This guide explains how to add support for standard video formats (MP4, MOV, AVI, etc.) to your video processing application using FFmpeg.

## Overview

Your current implementation uses a custom binary format. We've added new functions that can:
- **Decode** standard formats (MP4, MOV, AVI, etc.) → Your SVideo format
- **Process** using your existing optimized functions
- **Encode** back to standard formats

## Prerequisites

### Install FFmpeg Development Libraries

**Windows:**
```bash
# Download FFmpeg development build
# Visit: https://www.gyan.dev/ffmpeg/builds/
# Download: ffmpeg-release-full-shared.7z

# Extract to C:\ffmpeg
# Add to PATH: C:\ffmpeg\bin
```

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install libavcodec-dev libavformat-dev libavutil-dev libswscale-dev
```

**macOS:**
```bash
brew install ffmpeg
```

## Compilation

### Windows (Visual Studio)

Create `compile_with_ffmpeg.bat`:

```batch
@echo off
REM Compile video processing library with FFmpeg support

set FFMPEG_PATH=C:\ffmpeg

cl /LD /O2 ^
    video_functions.c video_codec.c ^
    /I"%FFMPEG_PATH%\include" ^
    /link ^
    /LIBPATH:"%FFMPEG_PATH%\lib" ^
    avcodec.lib avformat.lib avutil.lib swscale.lib ^
    /OUT:video_functions_ffmpeg.dll

if %errorlevel% equ 0 (
    echo ✅ Successfully compiled video_functions_ffmpeg.dll
) else (
    echo ❌ Compilation failed
)
```

### Windows (MinGW/GCC)

```batch
gcc -shared -O3 ^
    video_functions.c video_codec.c ^
    -I"C:/ffmpeg/include" ^
    -L"C:/ffmpeg/lib" ^
    -lavcodec -lavformat -lavutil -lswscale ^
    -o video_functions_ffmpeg.dll
```

### Linux/macOS

```bash
gcc -shared -O3 -fPIC \
    video_functions.c video_codec.c \
    -lavcodec -lavformat -lavutil -lswscale \
    -o video_functions_ffmpeg.so
```

## Usage

### Python Usage

```python
from video_wrapper import (
    video_processor,
    STANDARD_FORMAT_SUPPORT,
    is_standard_format
)

# Check if standard format support is available
if STANDARD_FORMAT_SUPPORT:
    print("✅ FFmpeg support available")
else:
    print("❌ FFmpeg support not available")

# Method 1: Automatic format detection (Recommended)
# The processor auto-detects MP4/MOV and uses FFmpeg

# Get video information
info = video_processor.get_video_info('input.mp4')
print(f"Video: {info['width']}x{info['height']}, "
      f"{info['num_frames']} frames, {info['fps']} fps")

# Decode video (auto-detects format)
video_ptr = video_processor.decode_video('input.mp4')

# Process video (same functions work for all formats!)
video_processor.reverse_video(video_ptr, mode='structured')
video_processor.swap_channels(video_ptr, 0, 2, mode='structured')  # Swap Red and Blue

# Encode back to MP4 (auto-detects format)
video_processor.encode_video('output.mp4', video_ptr, codec='libx264', fps=30)

# Cleanup
video_processor.free_video(video_ptr, mode='structured')

# Method 2: Manual format checking
if is_standard_format('video.mov'):
    print("This is a standard format, will use FFmpeg")
    
video_ptr = video_processor.decode_video('video.mov')
video_processor.clip_channel(video_ptr, 0, 50, 200, mode='structured')
video_processor.encode_video('output.mov', video_ptr, codec='libx264', fps=24)
video_processor.free_video(video_ptr, mode='structured')
```

### C Usage

```c
#include "video_codec.h"

// Get video info
int width, height;
long num_frames;
double fps;
get_video_info("input.mp4", &width, &height, &num_frames, &fps);

// Decode standard format
SVideo *video = decode_standard_video("input.mp4");

// Process using your existing functions
reverse_S(video);
swap_channels_S(video, 0, 2);
clip_channel_S(video, 0, 50, 200);

// Encode to standard format
encode_standard_video("output.mp4", video, "libx264", 30);

// Cleanup
free_video_S(video);
```

## Supported Formats

### Input Formats
- MP4 (.mp4)
- MOV (.mov)
- AVI (.avi)
- MKV (.mkv)
- WMV (.wmv)
- FLV (.flv)
- WebM (.webm)
- And many more...

### Output Codecs
- **H.264** (libx264) - Most compatible, good quality
- **H.265** (libx265) - Better compression, newer
- **VP8** (libvpx) - WebM format
- **VP9** (libvpx-vp9) - Better WebM
- **MPEG-4** (mpeg4) - Older, widely supported

## Integration with Flask App

Update your `app.py`:

```python
from video_wrapper import (
    video_processor,
    STANDARD_FORMAT_SUPPORT,
    is_standard_format
)

@app.route('/process_video', methods=['POST'])
def process_video():
    # ... existing code ...
    
    input_path = os.path.join(app.config['UPLOAD_FOLDER'], upload_files[0])
    
    try:
        # Decode video (auto-detects format)
        video_ptr = video_processor.decode_video(input_path)
        mode = 'structured'  # Standard formats use SVideo structure
        
        # Process operations
        for operation in operations:
            op_name = operation.get('name')
            params = operation.get('params', {})
            
            if op_name == 'reverse':
                video_processor.reverse_video(video_ptr, mode=mode)
            elif op_name == 'swap_channels':
                video_processor.swap_channels(video_ptr, 
                                             params.get('channel1', 0),
                                             params.get('channel2', 1),
                                             mode=mode)
            # ... more operations ...
        
        # Encode output
        output_filename = f"{file_id}_{unique_id}_processed.mp4"
        output_path = os.path.join(app.config['PROCESSED_FOLDER'], output_filename)
        
        # encode_video auto-detects output format
        if is_standard_format(output_path):
            video_processor.encode_video(output_path, video_ptr, codec='libx264', fps=30)
        else:
            video_processor.encode_video(output_path, video_ptr, mode=mode)
        
        video_processor.free_video(video_ptr, mode=mode)
        
        return jsonify({
            'success': True,
            'processed_file': output_filename
        })
    
    except Exception as e:
        return jsonify({'error': f'Processing failed: {str(e)}'}), 500
```

## Performance Notes

### Encoding Options

**Fast encoding (lower quality):**
```python
processor.encode_video('output.mp4', video_ptr, codec='libx264', fps=30)
# FFmpeg will use default preset (medium)
```

**High quality (slower):**
```c
// In video_codec.c, modify codec_ctx settings:
codec_ctx->bit_rate = 8000000;  // 8 Mbps instead of 4 Mbps
```

### Memory Usage

- **Decoding**: Allocates memory for all frames
- **Large videos**: May require significant RAM
- **Chunked processing**: Consider processing in batches for very large files

## Troubleshooting

### Error: "Could not find codec"
**Solution**: Install FFmpeg with the required codec:
```bash
# Windows: Download full build (not essentials)
# Linux: sudo apt-get install libx264-dev libx265-dev
```

### Error: "DLL not found" (Windows)
**Solution**: Copy FFmpeg DLLs to your project directory:
```batch
copy C:\ffmpeg\bin\*.dll .
```

### Error: "Unsupported pixel format"
**Solution**: The code converts to RGB24 automatically. If issues persist, check FFmpeg build.

### Performance is slow
**Solutions**:
- Use hardware acceleration if available
- Reduce bit rate
- Use faster codec preset
- Process in chunks

## Advanced: Hardware Acceleration

To enable GPU encoding (much faster):

```c
// In video_codec.c, modify codec selection:
codec = avcodec_find_encoder_by_name("h264_nvenc");  // NVIDIA
// or
codec = avcodec_find_encoder_by_name("h264_qsv");    // Intel Quick Sync
// or  
codec = avcodec_find_encoder_by_name("h264_videotoolbox");  // macOS
```

## Testing

Test script:

```python
from video_wrapper import video_processor, STANDARD_FORMAT_SUPPORT

if not STANDARD_FORMAT_SUPPORT:
    print("❌ FFmpeg support not available")
    exit(1)

# Test MP4
print("Testing MP4...")
video = video_processor.decode_video("test.mp4")
video_processor.reverse_video(video, mode='structured')
video_processor.encode_video("output.mp4", video, codec='libx264', fps=30)
video_processor.free_video(video, mode='structured')
print("✅ MP4 test passed")

# Test MOV
print("Testing MOV...")
video = video_processor.decode_video("test.mov")
video_processor.swap_channels(video, 0, 2, mode='structured')
video_processor.encode_video("output.mov", video, codec='libx264', fps=24)
video_processor.free_video(video, mode='structured')
print("✅ MOV test passed")
```

## Summary

**Files Created:**
- `video_codec.h` - Header for standard format support
- `video_codec.c` - Implementation using FFmpeg
- `video_wrapper.py` - Unified Python wrapper (supports both custom and standard formats)
- `FFMPEG_INTEGRATION.md` - This guide

**Compilation:**
- Compile with FFmpeg libraries to get `video_functions_ffmpeg.dll/.so`
- Falls back to custom format if FFmpeg not available

**Usage:**
- Auto-detects format and uses appropriate decoder/encoder
- Same processing functions work for both formats
- Transparent to the user