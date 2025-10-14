@echo off
REM Simple Emscripten build script for WebAssembly video processing (Windows)
REM Run this script after installing Emscripten

echo Building WebAssembly video processing module...

REM Set up Emscripten environment if emsdk directory exists
if exist "..\emsdk\emsdk_env.bat" (
    echo Setting up Emscripten environment...
    call ..\emsdk\emsdk_env.bat
) else (
    echo Warning: emsdk directory not found. Make sure Emscripten is installed in ../emsdk/
)

REM Check if Emscripten is available
where emcc >nul 2>nul
if %errorlevel% neq 0 (
    echo Error: Emscripten not found. Please install Emscripten first:
    echo 1. Download from: https://emscripten.org/docs/getting_started/downloads.html
    echo 2. Follow installation instructions
    echo 3. Or if already installed, run: emsdk\emsdk_env.bat
    exit /b 1
)

REM Build the WASM module
emcc ..\lib\video_functions_wasm.c ^
    -o ..\static\video_processor.js ^
    -s EXPORTED_FUNCTIONS="[\"_malloc\", \"_free\", \"_decode_S_wasm\", \"_free_video_S_wasm\", \"_reverse_S_wasm\", \"_swap_channels_S_wasm\", \"_clip_channel_S_wasm\", \"_scale_channel_S_wasm\", \"_encode_S_wasm\"]" ^
    -s EXPORTED_RUNTIME_METHODS="[\"ccall\", \"cwrap\", \"HEAPU8\", \"HEAP32\"]" ^
    -s ALLOW_MEMORY_GROWTH=1 ^
    -s INITIAL_MEMORY=67108864 ^
    -s MAXIMUM_MEMORY=2147483648 ^
    -s MODULARIZE=1 ^
    -s EXPORT_NAME="VideoProcessorModule" ^
    -O3 ^
    -DWASM_BUILD

if %errorlevel% equ 0 (
    echo ✅ WebAssembly module built successfully!
    echo Files created:
    echo   - static/video_processor.js
    echo   - static/video_processor.wasm
    echo.
    echo The module is ready to use in your web application.
) else (
    echo ❌ Build failed. Please check the error messages above.
    exit /b 1
)