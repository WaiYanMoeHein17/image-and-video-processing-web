# FilmMaster & ImagePro - Professional Media Processing Suite

A web application that combines advanced image processing capabilities from Python with high-performance video processing from C, providing a professional interface for media manipulation. 

Also, this is a versatile repo where I just want to experiment with new technologies like WASM, C/C++ SIMD vectorisation, OpenMP, OpenCV and more. There isn't really a speific goal or coherency in the project, its just me trying out new things and layering them on top of each other hoping it works. Nothing was planned. 

## Features

### Image Processing (Python-based OpenCV)
- **Brightness & Contrast**: Adaptive brightness adjustment, logarithmic/exponential transforms
- **Noise Reduction**: Advanced denoising using Non-Local Means, salt & pepper noise removal
- **Sharpening**: Multiple sharpening algorithms including Laplacian-based methods
- **Color Enhancement**: Saturation boosting, color balance correction
- **Edge Processing**: Edge preservation filters, edge restoration
- **Geometric Correction**: Perspective correction, warping fixes
- **Inpainting**: Advanced patch-based inpainting for object removal
- **Filtering**: Bilateral filtering, edge-preserving smoothing

### Video Processing (C-based SIMD(AVX256) & OpenMP) 
- **Frame Operations**: Reverse video playback
- **Channel Manipulation**: Swap RGB channels, individual channel scaling
- **Value Adjustment**: Channel clipping, brightness/contrast per channel
- **Memory Optimization**: Multiple processing modes for different performance needs

### Currently Trying to Migrate to C++ and implement OOP for structure

### Web Interface (Designed using Figma)
- **Modern UI**: Professional dark theme with gradient accents
- **Drag & Drop**: Intuitive file upload with progress indication
- **Real-time Preview**: Side-by-side original and processed media comparison
- **Parameter Control**: Interactive sliders and controls for all operations
- **Batch Processing**: Apply multiple operations in sequence
- **Download Results**: Direct download of processed media

## Setup Instructions

### Prerequisites

1. **Python 3.8+** with pip installed
2. **Visual Studio** or **MinGW-w64** for C compilation
3. **Git** (for cloning repositories if needed)

### Step 1: Install Python Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Compile the C Library

**Option A: Using Visual Studio (Recommended)**
```bash
# Compile to DLL using Visual Studio
cl /LD video_functions.c /Fe:video_functions.dll
```

**Option B: Using MinGW-w64**
```bash
# Compile to DLL using GCC
gcc -shared -fPIC -o video_functions.dll video_functions.c
```

**Option C: Using the provided batch file**
```bash
# Run the automated compilation script
.\compile_video_lib.bat
```

### Step 3: Run the Application

```bash
# Navigate to the project directory
cd image-and-video-processing-web

# Start the Flask server
python app.py
```

The application will be available at: http://localhost:5000

## File Structure

```
image-and-video-processing-web/
├── app.py                    # Main Flask application
├── image_functions.py        # Image processing functions
├── video_functions.c         # C video processing library
├── video_functions.h         # C library header file
├── video_functions.dll       # Compiled C library (after compilation)
├── video_wrapper.py          # Python wrapper for C library
├── compile_video_lib.bat     # Automated compilation script
├── requirements.txt          # Python dependencies
├── templates/
│   └── index.html           # Main HTML template
├── static/
│   ├── styles.css           # CSS styling
│   └── script.js            # JavaScript functionality
├── uploads/                 # Temporary uploaded files
└── processed/               # Processed output files
```

## What I used and plan to use in the future

### Backend (Flask)

### Frontend (HTML/CSS/JS)

### AVX-256 and OpenMP 
There are different functions in the video_functions.c file that use AVX-256 and OpenMP to compare performance between the two, but also with normal C implementations. 

Each function has 3 variants, one normal C, one for speed and one for memory efficiency.

