# FilmMaster & ImagePro - Professional Media Processing Suite

A powerful web application that combines advanced image processing capabilities from Python with high-performance video processing from C, providing a professional interface for media manipulation.

## Features

### Image Processing (Python-based)
- **Brightness & Contrast**: Adaptive brightness adjustment, logarithmic/exponential transforms
- **Noise Reduction**: Advanced denoising using Non-Local Means, salt & pepper noise removal
- **Sharpening**: Multiple sharpening algorithms including Laplacian-based methods
- **Color Enhancement**: Saturation boosting, color balance correction
- **Edge Processing**: Edge preservation filters, edge restoration
- **Geometric Correction**: Perspective correction, warping fixes
- **Inpainting**: Advanced patch-based inpainting for object removal
- **Filtering**: Bilateral filtering, edge-preserving smoothing

### Video Processing (C-based)
- **Frame Operations**: Reverse video playback
- **Channel Manipulation**: Swap RGB channels, individual channel scaling
- **Value Adjustment**: Channel clipping, brightness/contrast per channel
- **Memory Optimization**: Multiple processing modes for different performance needs

### Web Interface
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

## Usage Guide

### For Images

1. **Upload**: Drag and drop an image or click to browse
2. **Select Operations**: Choose from 15+ image processing operations
3. **Adjust Parameters**: Use sliders and controls to fine-tune settings
4. **Process**: Apply operations in sequence
5. **Download**: Save the processed result

**Available Image Operations:**
- Adaptive Brightness, Logarithmic/Exponential Transform
- Advanced Denoising, Salt & Pepper Noise Removal
- Laplacian Sharpening, Edge Restoration
- Saturation Boost, Color Balance Correction
- Bilateral Filtering, Edge-Preserving Filters
- Perspective Correction, Advanced Inpainting

### For Videos

1. **Upload**: Support for MP4, AVI, MOV formats (max 1 minute)
2. **Apply Operations**: Video-specific processing options
3. **Process**: High-performance C-based processing
4. **Download**: Processed video output

**Available Video Operations:**
- Reverse playbook order
- Swap RGB channels
- Individual channel scaling and clipping
- Memory-optimized processing modes

## Technical Architecture

### Backend (Flask)
- **Image Processing**: Direct integration with existing Python functions
- **Video Processing**: ctypes wrapper for C library integration
- **File Management**: Secure upload/download with temporary storage
- **API Endpoints**: RESTful API for frontend communication

### Frontend (HTML/CSS/JS)
- **Modern Design**: Professional interface with responsive layout
- **Interactive Controls**: Dynamic parameter adjustment
- **Real-time Feedback**: Progress indication and error handling
- **Media Preview**: Side-by-side comparison view

### Performance Optimizations
- **Memory Management**: Automatic cleanup of temporary files
- **Progress Tracking**: Real-time processing status
- **Error Handling**: Comprehensive error reporting
- **File Validation**: Size and type restrictions

## Troubleshooting

### Common Issues

**"Video processing not available"**
- Ensure video_functions.dll is compiled and in the project directory
- Run `compile_video_lib.bat` or compile manually using the commands above
- Check that Visual Studio or MinGW-w64 is properly installed

**"Import cv2 could not be resolved"**
- Install OpenCV: `pip install opencv-python`
- Ensure Python environment is properly activated

**"File not found" errors**
- Ensure all files are in the correct locations as shown in the file structure
- Check that image_functions.py is in the project root directory

**Upload fails**
- Check file size limits (100MB max)
- Ensure file formats are supported
- Verify upload/processed directories exist

### Performance Tips

1. **For large files**: Use video memory mode for better performance
2. **For batch processing**: Apply operations in logical order
3. **For development**: Enable Flask debug mode for detailed error messages

## Development

### Adding New Operations

**For Images (Python):**
1. Add function to image_functions.py
2. Update `/get_image_operations` endpoint in app.py
3. Add operation handling in `/process_image` endpoint

**For Videos (C):**
1. Add function to video_functions.c
2. Update video_wrapper.py with new function binding
3. Add operation to `/get_video_operations` endpoint
4. Recompile the DLL using `compile_video_lib.bat`

### Customization

- **Styling**: Modify `static/styles.css`
- **Behavior**: Update `static/script.js`
- **Backend Logic**: Extend `app.py`

## License

This project combines multiple components. Please refer to individual component licenses.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## Support

For issues related to:
- **Image Processing**: Check image_functions.py and OpenCV documentation
- **Video Processing**: Verify C compilation and library loading (video_functions.dll)
- **Web Interface**: Check browser console for JavaScript errors
- **Server Issues**: Check Flask logs and Python environment