@echo off
REM Compile video processing library with FFmpeg support for Windows

echo Compiling video processing library with FFmpeg support...
echo.

REM Check if FFmpeg path is set
if not defined FFMPEG_PATH (
    set FFMPEG_PATH=C:\ffmpeg
    echo Using default FFmpeg path: %FFMPEG_PATH%
) else (
    echo Using FFmpeg path: %FFMPEG_PATH%
)

REM Check if FFmpeg exists
if not exist "%FFMPEG_PATH%\include\libavcodec\avcodec.h" (
    echo.
    echo Error: FFmpeg not found at %FFMPEG_PATH%
    echo.
    echo Please install FFmpeg:
    echo 1. Download from: https://www.gyan.dev/ffmpeg/builds/
    echo 2. Download: ffmpeg-release-full-shared.7z
    echo 3. Extract to C:\ffmpeg
    echo 4. Or set FFMPEG_PATH environment variable
    echo.
    exit /b 1
)

echo.
echo Compiling with gcc...
echo.

cd ..\lib

gcc -shared -O3 ^
    video_functions.c video_codec.c ^
    -I"%FFMPEG_PATH%\include" ^
    -L"%FFMPEG_PATH%\lib" ^
    -lavcodec -lavformat -lavutil -lswscale ^
    -o video_functions_ffmpeg.dll

if %errorlevel% equ 0 (
    echo.
    echo ✅ Successfully compiled video_functions_ffmpeg.dll
    echo.
    
    REM Copy required FFmpeg DLLs
    echo Copying FFmpeg DLLs...
    copy "%FFMPEG_PATH%\bin\avcodec-*.dll" . >nul 2>&1
    copy "%FFMPEG_PATH%\bin\avformat-*.dll" . >nul 2>&1
    copy "%FFMPEG_PATH%\bin\avutil-*.dll" . >nul 2>&1
    copy "%FFMPEG_PATH%\bin\swscale-*.dll" . >nul 2>&1
    copy "%FFMPEG_PATH%\bin\swresample-*.dll" . >nul 2>&1
    echo ✅ FFmpeg DLLs copied
    
    cd ..\scripts
    echo.
    echo Ready to use! Your application now supports:
    echo   - MP4, MOV, AVI, MKV, WMV, and more
    echo   - All your existing optimized processing functions
    echo.
) else (
    cd ..\scripts
    echo.
    echo ❌ Compilation failed
    echo.
    echo Troubleshooting:
    echo - Ensure gcc is installed (MinGW or MSYS2)
    echo - Check FFmpeg path: %FFMPEG_PATH%
    echo - Try running as administrator
    echo.
    exit /b 1
)
