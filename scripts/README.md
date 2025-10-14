# Scripts Directory

This folder contains all build and compilation scripts for the project.

## Available Scripts

### 🔨 build_wasm.bat / build_wasm.sh
**Purpose**: Compile C code to WebAssembly for client-side video processing

**Requirements**:
- Emscripten SDK (installed in `../emsdk/`)
- Node.js (comes with Emscripten)

**Usage**:
```bash
# Windows
cd scripts
.\build_wasm.bat

# Linux/Mac
cd scripts
chmod +x build_wasm.sh
./build_wasm.sh
```

**Output**:
- `../static/video_processor.js` - JavaScript wrapper
- `../static/video_processor.wasm` - WebAssembly binary

**When to use**: When you modify `lib/video_functions_wasm.c` or need to rebuild WASM

---

### 🔨 compile_video_lib.bat
**Purpose**: Compile basic video processing library (custom format only)

**Requirements**:
- Visual Studio with C++ tools OR
- MinGW-w64 with GCC

**Usage**:
```bash
cd scripts
.\compile_video_lib.bat
```

**Output**:
- `../lib/video_functions.dll` - Basic video library

**When to use**: 
- Initial setup
- After modifying `lib/video_functions.c` or `lib/video_functions.h`
- When you don't need MP4/MOV support

---

### 🔨 compile_with_ffmpeg.bat
**Purpose**: Compile video library WITH FFmpeg support (MP4, MOV, AVI, etc.)

**Requirements**:
- MinGW-w64 or MSYS2 with GCC
- FFmpeg development libraries (installed at `C:\ffmpeg`)

**FFmpeg Installation**:
1. Download from: https://www.gyan.dev/ffmpeg/builds/
2. Get: `ffmpeg-release-full-shared.7z`
3. Extract to: `C:\ffmpeg`
4. (Optional) Set `FFMPEG_PATH` environment variable if using different location

**Usage**:
```bash
cd scripts
.\compile_with_ffmpeg.bat
```

**Output**:
- `../lib/video_functions_ffmpeg.dll` - Video library with FFmpeg
- Copies FFmpeg DLLs to `../lib/` folder automatically

**When to use**:
- When you need MP4/MOV/AVI support
- After modifying `lib/video_codec.c` or `lib/video_codec.h`
- Production deployment with standard format support

---

## Quick Reference

| Script | Platform | Output | Purpose |
|--------|----------|--------|---------|
| `build_wasm.bat` | Windows | `*.js`, `*.wasm` | Client-side video processing |
| `build_wasm.sh` | Linux/Mac | `*.js`, `*.wasm` | Client-side video processing |
| `compile_video_lib.bat` | Windows | `video_functions.dll` | Basic video library |
| `compile_with_ffmpeg.bat` | Windows | `video_functions_ffmpeg.dll` | Full format support |

## Troubleshooting

### "Emscripten not found"
**Solution**: Install Emscripten in the `emsdk/` folder:
```bash
cd ..
git clone https://github.com/emscripten-core/emsdk.git
cd emsdk
.\emsdk install latest
.\emsdk activate latest
```

### "gcc not found" (compile_with_ffmpeg.bat)
**Solution**: Install MinGW-w64 or MSYS2:
- MinGW-w64: https://www.mingw-w64.org/
- MSYS2: https://www.msys2.org/

### "FFmpeg not found"
**Solution**: 
1. Download FFmpeg: https://www.gyan.dev/ffmpeg/builds/
2. Extract to `C:\ffmpeg`
3. Or set environment variable: `setx FFMPEG_PATH "C:\path\to\ffmpeg"`

### "cl.exe not found" (compile_video_lib.bat)
**Solution**: 
- Install Visual Studio with C++ tools, OR
- The script will automatically try GCC as fallback

### Build fails with path errors
**Solution**: Make sure you run scripts FROM the `scripts/` directory:
```bash
cd scripts
.\build_wasm.bat  # ✅ Correct
```

NOT from root:
```bash
.\scripts\build_wasm.bat  # ❌ Will fail - paths are relative
```

## Development Workflow

### First Time Setup
```bash
# 1. Navigate to scripts
cd scripts

# 2. Compile basic video library
.\compile_video_lib.bat

# 3. (Optional) Install FFmpeg and compile with support
.\compile_with_ffmpeg.bat

# 4. (Optional) Build WebAssembly for >50MB files
.\build_wasm.bat
```

### After Modifying C Code
```bash
cd scripts

# If you changed video_functions.c or video_functions.h
.\compile_video_lib.bat

# If you changed video_codec.c or video_codec.h (FFmpeg)
.\compile_with_ffmpeg.bat

# If you changed video_functions_wasm.c (WebAssembly)
.\build_wasm.bat
```

### Production Build
```bash
cd scripts

# Build everything with optimizations
.\compile_with_ffmpeg.bat  # Full format support
.\build_wasm.bat           # Client-side processing

# Output is ready for deployment!
```

## Notes

- All scripts automatically handle directory navigation
- Scripts update paths relative to their location
- Build artifacts go to appropriate folders (`lib/`, `static/`)
- FFmpeg DLLs are automatically copied when using `compile_with_ffmpeg.bat`
- WASM builds use `-O3` optimization for production performance

## See Also

- `../documentation/WASM_SETUP.md` - WebAssembly setup guide
- `../documentation/FFMPEG_INTEGRATION.md` - FFmpeg integration guide
- `../documentation/REORGANIZATION_SUMMARY.md` - Project structure overview
