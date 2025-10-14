"""
Flask Application for Image and Video Processing Web Interface
Combines Python image processing from main.py with C video processing from libFilmMaster2000
"""

from flask import Flask, request, render_template, jsonify, send_file, redirect, url_for
from flask_cors import CORS
import os
import tempfile
import uuid
from werkzeug.utils import secure_filename
import cv2
import numpy as np
import json
import ctypes
from ctypes import Structure, c_long, c_ubyte, POINTER
from src.video_wrapper import video_processor, VIDEO_PROCESSING_AVAILABLE
import src.image_functions as image_processor

app = Flask(__name__)
CORS(app)

# Configuration
# No file size limit - WASM will handle large files client-side
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['PROCESSED_FOLDER'] = 'processed'

# Create directories if they don't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PROCESSED_FOLDER'], exist_ok=True)

# Allowed file extensions
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'wmv'}

def allowed_file(filename, file_type):
    """Check if uploaded file is allowed"""
    if file_type == 'image':
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS
    elif file_type == 'video':
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_VIDEO_EXTENSIONS
    return False

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    # Determine file type
    file_type = 'image' if allowed_file(file.filename, 'image') else 'video' if allowed_file(file.filename, 'video') else None
    
    if file_type and allowed_file(file.filename, file_type):
        # Generate unique filename
        file_id = str(uuid.uuid4())
        filename = secure_filename(file.filename)
        file_extension = filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{file_id}.{file_extension}"
        
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(filepath)
        
        return jsonify({
            'success': True,
            'file_id': file_id,
            'filename': filename,
            'file_type': file_type,
            'file_extension': file_extension
        })
    
    return jsonify({'error': 'File type not allowed'}), 400

@app.route('/process_image', methods=['POST'])
def process_image():
    """Process image using Python functions from main.py"""
    data = request.json
    file_id = data.get('file_id')
    operations = data.get('operations', [])
    
    if not file_id:
        return jsonify({'error': 'No file ID provided'}), 400
    
    try:
        # Find the uploaded file
        upload_files = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) if f.startswith(file_id)]
        if not upload_files:
            return jsonify({'error': 'File not found'}), 404
        
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], upload_files[0])
        
        # Read image
        img = image_processor.read_img(input_path)
        if img is None:
            return jsonify({'error': 'Could not read image'}), 400
        
        # Process image based on operations
        processed_img = img.copy()
        
        for operation in operations:
            op_name = operation.get('name')
            params = operation.get('params', {})
            
            if op_name == 'adaptive_brightness':
                processed_img = image_processor.adaptive_brightness(processed_img)
            elif op_name == 'logarithmic_transform':
                processed_img = image_processor.logarithmic_transform(processed_img)
            elif op_name == 'exponential_transform':
                c = params.get('c', 1)
                alpha = params.get('alpha', 1.2)
                processed_img = image_processor.exponential_transform(processed_img, c, alpha)
            elif op_name == 'denoise_image':
                h = params.get('h', 10)
                hColor = params.get('hColor', 10)
                processed_img = image_processor.denoise_image(processed_img, h, hColor)
            elif op_name == 'sharpen_img':
                processed_img = image_processor.sharpen_img(processed_img)
            elif op_name == 'boost_saturation':
                scale = params.get('saturation_scale', 1.5)
                processed_img = image_processor.boost_saturation(processed_img, scale)
            elif op_name == 'correct_warp':
                processed_img = image_processor.correct_warp(processed_img)
            elif op_name == 'edge_preserving_filter':
                sigma_s = params.get('sigma_s', 60)
                sigma_r = params.get('sigma_r', 0.4)
                processed_img = image_processor.edge_preserving_filter(processed_img, sigma_s, sigma_r)
            elif op_name == 'remove_salt_pepper_noise':
                kernel_size = params.get('kernel_size', 3)
                processed_img = image_processor.remove_salt_pepper_noise(processed_img, kernel_size)
            elif op_name == 'restore_edges':
                processed_img = image_processor.restore_edges(processed_img)
            elif op_name == 'bilateral_filter':
                d = params.get('d', 15)
                sigmaColor = params.get('sigmaColor', 50)
                sigmaSpace = params.get('sigmaSpace', 50)
                processed_img = image_processor.bilateral_filter(processed_img, d, sigmaColor, sigmaSpace)
            elif op_name == 'laplacian_sharpening':
                alpha = params.get('alpha', 0.5)
                processed_img = image_processor.laplacian_sharpening(processed_img, alpha)
            elif op_name == 'inpaint_black_circle':
                processed_img = image_processor.inpaint_black_circle(processed_img)
            elif op_name == 'criminisi_inpaint_black_circle':
                patch_size = params.get('patch_size', 9)
                stride = params.get('stride', 3)
                processed_img = image_processor.criminisi_inpaint_black_circle(processed_img, patch_size, stride)
        
        # Clean up old processed files for this file_id to prevent accumulation
        for existing_file in os.listdir(app.config['PROCESSED_FOLDER']):
            if existing_file.startswith(f"{file_id}_") and existing_file.endswith("_processed.png"):
                try:
                    os.remove(os.path.join(app.config['PROCESSED_FOLDER'], existing_file))
                except:
                    pass  # Ignore errors if file is in use
        
        # Save processed image with unique filename to prevent caching
        unique_id = str(uuid.uuid4())
        output_filename = f"{file_id}_{unique_id}_processed.png"
        output_path = os.path.join(app.config['PROCESSED_FOLDER'], output_filename)
        cv2.imwrite(output_path, processed_img)
        
        return jsonify({
            'success': True,
            'processed_file': output_filename,
            'operations_applied': len(operations)
        })
        
    except Exception as e:
        return jsonify({'error': f'Processing failed: {str(e)}'}), 500

@app.route('/download/<filename>')
def download_file(filename):
    """Download processed file"""
    try:
        file_path = os.path.join(app.config['PROCESSED_FOLDER'], filename)
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True)
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get_image_operations')
def get_image_operations():
    """Return available image processing operations"""
    operations = [
        {
            'name': 'adaptive_brightness',
            'display_name': 'Adaptive Brightness',
            'description': 'Automatically adjust brightness based on image content',
            'params': []
        },
        {
            'name': 'logarithmic_transform',
            'display_name': 'Logarithmic Transform',
            'description': 'Enhance dark regions, compress bright regions',
            'params': []
        },
        {
            'name': 'exponential_transform',
            'display_name': 'Exponential Transform',
            'description': 'Enhance bright regions',
            'params': [
                {'name': 'c', 'type': 'float', 'default': 1, 'min': 0.1, 'max': 5},
                {'name': 'alpha', 'type': 'float', 'default': 1.2, 'min': 0.5, 'max': 3}
            ]
        },
        {
            'name': 'denoise_image',
            'display_name': 'Denoise Image',
            'description': 'Remove noise using Non-Local Means',
            'params': [
                {'name': 'h', 'type': 'int', 'default': 10, 'min': 1, 'max': 30},
                {'name': 'hColor', 'type': 'int', 'default': 10, 'min': 1, 'max': 30}
            ]
        },
        {
            'name': 'sharpen_img',
            'display_name': 'Sharpen Image',
            'description': 'Enhance image sharpness using Laplacian filter',
            'params': []
        },
        {
            'name': 'boost_saturation',
            'display_name': 'Boost Saturation',
            'description': 'Increase color saturation',
            'params': [
                {'name': 'saturation_scale', 'type': 'float', 'default': 1.5, 'min': 0.5, 'max': 3}
            ]
        },
        {
            'name': 'correct_warp',
            'display_name': 'Correct Perspective',
            'description': 'Fix perspective distortion',
            'params': []
        },
        {
            'name': 'edge_preserving_filter',
            'display_name': 'Edge Preserving Filter',
            'description': 'Smooth while preserving edges',
            'params': [
                {'name': 'sigma_s', 'type': 'float', 'default': 60, 'min': 10, 'max': 200},
                {'name': 'sigma_r', 'type': 'float', 'default': 0.4, 'min': 0.1, 'max': 1}
            ]
        },
        {
            'name': 'remove_salt_pepper_noise',
            'display_name': 'Remove Salt & Pepper Noise',
            'description': 'Remove impulse noise using median filter',
            'params': [
                {'name': 'kernel_size', 'type': 'int', 'default': 3, 'min': 3, 'max': 15, 'step': 2}
            ]
        },
        {
            'name': 'restore_edges',
            'display_name': 'Restore Edges',
            'description': 'Enhance edge definition',
            'params': []
        },
        {
            'name': 'bilateral_filter',
            'display_name': 'Bilateral Filter',
            'description': 'Denoise while preserving edges',
            'params': [
                {'name': 'd', 'type': 'int', 'default': 15, 'min': 5, 'max': 50},
                {'name': 'sigmaColor', 'type': 'int', 'default': 50, 'min': 10, 'max': 150},
                {'name': 'sigmaSpace', 'type': 'int', 'default': 50, 'min': 10, 'max': 150}
            ]
        },
        {
            'name': 'laplacian_sharpening',
            'display_name': 'Laplacian Sharpening',
            'description': 'Advanced sharpening using Laplacian operator',
            'params': [
                {'name': 'alpha', 'type': 'float', 'default': 0.5, 'min': 0.1, 'max': 2}
            ]
        },
        {
            'name': 'inpaint_black_circle',
            'display_name': 'Inpaint Black Regions',
            'description': 'Remove black spots/circles',
            'params': []
        },
        {
            'name': 'criminisi_inpaint_black_circle',
            'display_name': 'Advanced Inpainting',
            'description': 'Advanced patch-based inpainting',
            'params': [
                {'name': 'patch_size', 'type': 'int', 'default': 9, 'min': 5, 'max': 21, 'step': 2},
                {'name': 'stride', 'type': 'int', 'default': 3, 'min': 1, 'max': 10}
            ]
        }
    ]
    return jsonify(operations)

@app.route('/process_video', methods=['POST'])
def process_video():
    """Process video using C functions from libFilmMaster2000"""
    if not VIDEO_PROCESSING_AVAILABLE:
        return jsonify({'error': 'Video processing not available. Please compile libFilmMaster2000.c to a DLL.'}), 500
    
    data = request.json
    file_id = data.get('file_id')
    operations = data.get('operations', [])
    mode = data.get('mode', 'memory')  # Default to memory mode for better performance
    
    if not file_id:
        return jsonify({'error': 'No file ID provided'}), 400
    
    try:
        # Find the uploaded file
        upload_files = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) if f.startswith(file_id)]
        if not upload_files:
            return jsonify({'error': 'File not found'}), 404
        
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], upload_files[0])
        
        # Decode video
        video_ptr = video_processor.decode_video(input_path, mode)
        if not video_ptr:
            return jsonify({'error': 'Could not decode video'}), 400
        
        # Process video based on operations
        for operation in operations:
            op_name = operation.get('name')
            params = operation.get('params', {})
            
            if op_name == 'reverse':
                video_processor.reverse_video(video_ptr, mode)
            elif op_name == 'swap_channels':
                channel1 = params.get('channel1', 0)
                channel2 = params.get('channel2', 1)
                video_processor.swap_channels(video_ptr, channel1, channel2, mode)
            elif op_name == 'clip_channel':
                channel = params.get('channel', 0)
                min_val = params.get('min_val', 0)
                max_val = params.get('max_val', 255)
                video_processor.clip_channel(video_ptr, channel, min_val, max_val, mode)
            elif op_name == 'scale_channel':
                channel = params.get('channel', 0)
                scale_factor = params.get('scale_factor', 1.0)
                video_processor.scale_channel(video_ptr, channel, scale_factor, mode)
        
        # Clean up old processed files for this file_id to prevent accumulation
        for existing_file in os.listdir(app.config['PROCESSED_FOLDER']):
            if existing_file.startswith(f"{file_id}_") and existing_file.endswith("_processed.mp4"):
                try:
                    os.remove(os.path.join(app.config['PROCESSED_FOLDER'], existing_file))
                except:
                    pass  # Ignore errors if file is in use
        
        # Save processed video with unique filename to prevent caching
        unique_id = str(uuid.uuid4())
        output_filename = f"{file_id}_{unique_id}_processed.mp4"
        output_path = os.path.join(app.config['PROCESSED_FOLDER'], output_filename)
        
        result = video_processor.encode_video(output_path, video_ptr, mode)
        
        # Free memory
        video_processor.free_video(video_ptr, mode)
        
        if result == 0:  # Success
            return jsonify({
                'success': True,
                'processed_file': output_filename,
                'operations_applied': len(operations)
            })
        else:
            return jsonify({'error': 'Failed to encode processed video'}), 500
        
    except Exception as e:
        return jsonify({'error': f'Video processing failed: {str(e)}'}), 500

@app.route('/get_video_operations')
def get_video_operations():
    """Return available video processing operations"""
    if not VIDEO_PROCESSING_AVAILABLE:
        return jsonify([])
    
    operations = [
        {
            'name': 'reverse',
            'display_name': 'Reverse Video',
            'description': 'Reverse the order of video frames',
            'params': []
        },
        {
            'name': 'swap_channels',
            'display_name': 'Swap Color Channels',
            'description': 'Swap two color channels (RGB)',
            'params': [
                {'name': 'channel1', 'type': 'int', 'default': 0, 'min': 0, 'max': 2, 'options': [
                    {'value': 0, 'label': 'Red (0)'},
                    {'value': 1, 'label': 'Green (1)'},
                    {'value': 2, 'label': 'Blue (2)'}
                ]},
                {'name': 'channel2', 'type': 'int', 'default': 1, 'min': 0, 'max': 2, 'options': [
                    {'value': 0, 'label': 'Red (0)'},
                    {'value': 1, 'label': 'Green (1)'},
                    {'value': 2, 'label': 'Blue (2)'}
                ]}
            ]
        },
        {
            'name': 'clip_channel',
            'display_name': 'Clip Channel Values',
            'description': 'Clamp channel values to specified range',
            'params': [
                {'name': 'channel', 'type': 'int', 'default': 0, 'min': 0, 'max': 2, 'options': [
                    {'value': 0, 'label': 'Red (0)'},
                    {'value': 1, 'label': 'Green (1)'},
                    {'value': 2, 'label': 'Blue (2)'}
                ]},
                {'name': 'min_val', 'type': 'int', 'default': 0, 'min': 0, 'max': 255},
                {'name': 'max_val', 'type': 'int', 'default': 255, 'min': 0, 'max': 255}
            ]
        },
        {
            'name': 'scale_channel',
            'display_name': 'Scale Channel',
            'description': 'Scale channel values by a factor',
            'params': [
                {'name': 'channel', 'type': 'int', 'default': 0, 'min': 0, 'max': 2, 'options': [
                    {'value': 0, 'label': 'Red (0)'},
                    {'value': 1, 'label': 'Green (1)'},
                    {'value': 2, 'label': 'Blue (2)'}
                ]},
                {'name': 'scale_factor', 'type': 'float', 'default': 1.0, 'min': 0.1, 'max': 3.0}
            ]
        }
    ]
    return jsonify(operations)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)