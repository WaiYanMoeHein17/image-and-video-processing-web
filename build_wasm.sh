#!/bin/bash

# Simple Emscripten build script for WebAssembly video processing
# Run this script after installing Emscripten

echo "Building WebAssembly video processing module..."

# Check if Emscripten is available
if ! command -v emcc &> /dev/null; then
    echo "Error: Emscripten not found. Please install Emscripten first:"
    echo "1. Download from: https://emscripten.org/docs/getting_started/downloads.html"
    echo "2. Follow installation instructions"
    echo "3. Run: source ./emsdk_env.sh"
    exit 1
fi

# Build the WASM module
emcc video_functions_wasm.c \
    -o static/video_processor.js \
    -s EXPORTED_FUNCTIONS='["_malloc", "_free", "_decode_S_wasm", "_free_video_S_wasm", "_reverse_S_wasm", "_swap_channels_S_wasm", "_clip_channel_S_wasm", "_scale_channel_S_wasm", "_encode_S_wasm"]' \
    -s EXPORTED_RUNTIME_METHODS='["ccall", "cwrap", "HEAPU8", "HEAP32"]' \
    -s ALLOW_MEMORY_GROWTH=1 \
    -s INITIAL_MEMORY=67108864 \
    -s MAXIMUM_MEMORY=2147483648 \
    -s MODULARIZE=1 \
    -s EXPORT_NAME='VideoProcessorModule' \
    -O3 \
    -DWASM_BUILD

if [ $? -eq 0 ]; then
    echo "✅ WebAssembly module built successfully!"
    echo "Files created:"
    echo "  - static/video_processor.js"
    echo "  - static/video_processor.wasm"
    echo ""
    echo "The module is ready to use in your web application."
else
    echo "❌ Build failed. Please check the error messages above."
    exit 1
fi