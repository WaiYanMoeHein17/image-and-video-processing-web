# WebAssembly Integration Instructions

This guide will help you set up WebAssembly (WASM) support for video processing in your application.

## Prerequisites

### 1. Install Emscripten

**Windows:**
```bash
# Download and install Emscripten
git clone https://github.com/emscripten-core/emsdk.git
cd emsdk
emsdk install latest
emsdk activate latest
emsdk_env.bat
```

**Linux/Mac:**
```bash
# Download and install Emscripten
git clone https://github.com/emscripten-core/emsdk.git
cd emsdk
./emsdk install latest
./emsdk activate latest
source ./emsdk_env.sh
```

### 2. Verify Installation

```bash
emcc --version
```

You should see output showing the Emscripten compiler version.

## Build Instructions

### Step 1: Build the WASM Module

**Windows:**
```bash
# Run the build script
build_wasm.bat
```

**Linux/Mac:**
```bash
# Make the script executable and run it
chmod +x build_wasm.sh
./build_wasm.sh
```

### Step 2: Verify Build Output

After successful compilation, you should see these files created:
- `static/video_processor.js` - The WASM module wrapper
- `static/video_processor.wasm` - The compiled WebAssembly binary

## How It Works

### Automatic Mode Selection

The application automatically chooses processing mode based on file size:

- **Files ≤ 50MB**: Server-side processing (existing Python/C++ pipeline)
- **Files > 50MB**: Client-side WASM processing (new WebAssembly pipeline)

### WASM Processing Features

1. **Memory Management**: Processes videos in chunks to handle large files efficiently
2. **No Upload Required**: Large videos stay in the browser, reducing server load
3. **Real-time Processing**: Operations applied with visual feedback
4. **Export Capability**: Processed videos can be downloaded directly

### Supported Operations (WASM Mode)

- **Reverse Video**: Reverses frame order
- **Swap Channels**: Swaps RGB color channels
- **Clip Channel**: Clamps channel values to specified range
- **Scale Channel**: Multiplies channel values by a factor

## Troubleshooting

### Build Issues

1. **"emcc not found"**:
   - Ensure Emscripten is installed and activated
   - Run `emsdk_env.bat` (Windows) or `source ./emsdk_env.sh` (Linux/Mac)

2. **"video_functions_wasm.c not found"**:
   - Ensure you're running the build script from the project root directory

3. **Memory allocation errors**:
   - The WASM module is configured with 64MB initial memory and can grow to 2GB
   - Very large videos (>1GB) may still need server-side processing

### Runtime Issues

1. **"WASM module not available"**:
   - Check browser console for errors
   - Ensure `video_processor.js` and `video_processor.wasm` are accessible
   - Some browsers require HTTPS for WASM modules

2. **"Failed to initialize WASM processor"**:
   - Check browser compatibility (Chrome 57+, Firefox 52+, Safari 11+)
   - Ensure files are served with correct MIME types

## Browser Compatibility

- ✅ Chrome 57+
- ✅ Firefox 52+
- ✅ Safari 11+
- ✅ Edge 16+
- ❌ Internet Explorer (not supported)

## Performance Notes

- WASM processing runs at ~80-90% of native C speed
- Client-side processing eliminates network transfer time for large files
- Memory usage is managed through chunked processing
- Processing progress is shown in real-time

## Development Notes

### Adding New Operations

To add new video operations:

1. Add the function to `video_functions_wasm.c`
2. Export it in `build_wasm.bat/sh`
3. Add wrapper method to `wasm_video_processor.js`
4. Update operation handling in `script.js`

### Custom Video Formats

The current implementation uses a simple custom format. To support standard video formats:

1. Integrate FFmpeg.js for decoding
2. Modify `createMockVideoData()` to handle real video data
3. Add encoding support for output formats

## Security Considerations

- WASM runs in a sandboxed environment
- No access to file system or network (beyond what JavaScript allows)
- Memory is isolated from main JavaScript heap
- All processing happens client-side (privacy-friendly)