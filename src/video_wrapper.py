"""
Python wrapper for video processing library using ctypes
Supports both custom binary format and standard video formats (MP4, MOV, AVI, etc.)
This module provides a Python interface to the C video processing library
"""

import ctypes
from ctypes import Structure, c_long, c_ubyte, c_int, c_double, POINTER, c_char_p, c_float
import os
import sys

# Define the C structures in Python
class Video(Structure):
    _fields_ = [
        ("num_frames", c_long),
        ("channels", c_ubyte),
        ("height", c_ubyte),
        ("width", c_ubyte),
        ("data", POINTER(c_ubyte))
    ]

class Channel(Structure):
    _fields_ = [
        ("data", POINTER(c_ubyte))
    ]

class Frame(Structure):
    _fields_ = [
        ("channels", POINTER(Channel))
    ]

class SVideo(Structure):
    _fields_ = [
        ("num_frames", c_long),
        ("channels", c_ubyte),
        ("height", c_ubyte),
        ("width", c_ubyte),
        ("frames", POINTER(Frame))
    ]

class MVideo(Structure):
    _fields_ = [
        ("num_frames", c_long),
        ("channels", c_ubyte),
        ("height", c_ubyte),
        ("width", c_ubyte),
        ("data", POINTER(c_ubyte))
    ]

class VideoProcessor:
    def __init__(self, lib_path=None):
        """Initialize the video processor with the C library"""
        self.has_standard_format_support = False
        
        if lib_path is None:
            # Look for the DLL in the lib folder
            current_dir = os.path.dirname(os.path.abspath(__file__))
            lib_dir = os.path.join(os.path.dirname(current_dir), "lib")
            
            # Try FFmpeg-enabled version first
            ffmpeg_lib_path = os.path.join(lib_dir, "video_functions_ffmpeg.dll")
            basic_lib_path = os.path.join(lib_dir, "video_functions.dll")
            
            if os.path.exists(ffmpeg_lib_path):
                lib_path = ffmpeg_lib_path
                self.has_standard_format_support = True
            elif os.path.exists(basic_lib_path):
                lib_path = basic_lib_path
                print("Note: Using basic video library. Standard format support (MP4, MOV) not available.")
            else:
                raise FileNotFoundError(
                    f"C library not found. Please ensure video_functions.dll or "
                    f"video_functions_ffmpeg.dll is in the project directory."
                )
        
        try:
            self.lib = ctypes.CDLL(lib_path)
        except OSError as e:
            raise RuntimeError(f"Could not load C library: {e}")
        
        self._setup_function_signatures()
    
    def _setup_function_signatures(self):
        """Set up function signatures for all C functions"""
        
        # Standard format functions (if FFmpeg support is available)
        if self.has_standard_format_support:
            # int get_video_info(const char *filename, int *width, int *height, 
            #                    long *num_frames, double *fps)
            self.lib.get_video_info.argtypes = [
                c_char_p, 
                POINTER(c_int), 
                POINTER(c_int),
                POINTER(c_long), 
                POINTER(c_double)
            ]
            self.lib.get_video_info.restype = c_int
            
            # SVideo *decode_standard_video(const char *filename)
            self.lib.decode_standard_video.argtypes = [c_char_p]
            self.lib.decode_standard_video.restype = POINTER(SVideo)
            
            # int encode_standard_video(const char *filename, const SVideo *video, 
            #                          const char *codec_name, int fps)
            self.lib.encode_standard_video.argtypes = [
                c_char_p, 
                POINTER(SVideo), 
                c_char_p, 
                c_int
            ]
            self.lib.encode_standard_video.restype = c_int
        
        # decode functions (custom format)
        self.lib.decode.argtypes = [c_char_p]
        self.lib.decode.restype = POINTER(Video)
        
        self.lib.decode_S.argtypes = [c_char_p]
        self.lib.decode_S.restype = POINTER(SVideo)
        
        self.lib.decode_M.argtypes = [c_char_p]
        self.lib.decode_M.restype = POINTER(MVideo)
        
        # encode functions
        self.lib.encode.argtypes = [c_char_p, POINTER(Video)]
        self.lib.encode.restype = ctypes.c_int
        
        self.lib.encode_S.argtypes = [c_char_p, POINTER(SVideo)]
        self.lib.encode_S.restype = ctypes.c_int
        
        self.lib.encode_M.argtypes = [c_char_p, POINTER(MVideo)]
        self.lib.encode_M.restype = ctypes.c_int
        
        # free functions
        self.lib.free_video.argtypes = [POINTER(Video)]
        self.lib.free_video.restype = None
        
        self.lib.free_video_S.argtypes = [POINTER(SVideo)]
        self.lib.free_video_S.restype = None
        
        self.lib.free_video_M.argtypes = [POINTER(MVideo)]
        self.lib.free_video_M.restype = None
        
        # processing functions
        self.lib.reverse.argtypes = [POINTER(Video)]
        self.lib.reverse.restype = None
        
        self.lib.reverse_S.argtypes = [POINTER(SVideo)]
        self.lib.reverse_S.restype = None
        
        self.lib.reverse_M.argtypes = [POINTER(MVideo)]
        self.lib.reverse_M.restype = None
        
        # swap channels
        self.lib.swap_channels.argtypes = [POINTER(Video), c_ubyte, c_ubyte]
        self.lib.swap_channels.restype = None
        
        self.lib.swap_channels_S.argtypes = [POINTER(SVideo), c_ubyte, c_ubyte]
        self.lib.swap_channels_S.restype = None
        
        self.lib.swap_channels_M.argtypes = [POINTER(MVideo), c_ubyte, c_ubyte]
        self.lib.swap_channels_M.restype = None
        
        # clip channel
        self.lib.clip_channel.argtypes = [POINTER(Video), c_ubyte, c_ubyte, c_ubyte]
        self.lib.clip_channel.restype = None
        
        self.lib.clip_channel_S.argtypes = [POINTER(SVideo), c_ubyte, c_ubyte, c_ubyte]
        self.lib.clip_channel_S.restype = None
        
        self.lib.clip_channel_M.argtypes = [POINTER(MVideo), c_ubyte, c_ubyte, c_ubyte]
        self.lib.clip_channel_M.restype = None
        
        # scale channel
        self.lib.scale_channel.argtypes = [POINTER(Video), c_ubyte, c_float]
        self.lib.scale_channel.restype = None
        
        self.lib.scale_channel_S.argtypes = [POINTER(SVideo), c_ubyte, c_float]
        self.lib.scale_channel_S.restype = None
        
        self.lib.scale_channel_M.argtypes = [POINTER(MVideo), c_ubyte, c_float]
        self.lib.scale_channel_M.restype = None
    
    def _is_standard_format(self, filename):
        """Check if file is a standard video format"""
        standard_formats = ['.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv', '.webm']
        ext = os.path.splitext(filename)[1].lower()
        return ext in standard_formats
    
    def get_video_info(self, filename):
        """
        Get video information without full decoding (standard formats only)
        
        Args:
            filename: Path to video file
            
        Returns:
            dict with keys: width, height, num_frames, fps
            
        Raises:
            RuntimeError: If standard format support is not available or file cannot be read
        """
        if not self.has_standard_format_support:
            raise RuntimeError("Standard format support not available. Compile with FFmpeg to use this feature.")
        
        width = c_int()
        height = c_int()
        num_frames = c_long()
        fps = c_double()
        
        result = self.lib.get_video_info(
            filename.encode('utf-8'),
            ctypes.byref(width),
            ctypes.byref(height),
            ctypes.byref(num_frames),
            ctypes.byref(fps)
        )
        
        if result != 0:
            raise RuntimeError(f"Failed to get video info from {filename}")
        
        return {
            'width': width.value,
            'height': height.value,
            'num_frames': num_frames.value,
            'fps': fps.value
        }
    
    def decode_video(self, filename, mode='standard', auto_detect=True):
        """
        Decode a video file
        
        Args:
            filename: Path to video file
            mode: 'standard' (Video), 'structured' (SVideo), or 'memory' (MVideo)
            auto_detect: If True, automatically use standard format decoder for MP4/MOV files
            
        Returns:
            Pointer to Video/SVideo/MVideo structure
        """
        filename_bytes = filename.encode('utf-8')
        
        # Auto-detect standard formats and use FFmpeg decoder
        if auto_detect and self.has_standard_format_support and self._is_standard_format(filename):
            # Standard formats always decode to SVideo
            return self.lib.decode_standard_video(filename_bytes)
        
        # Use custom format decoders
        if mode == 'standard':
            return self.lib.decode(filename_bytes)
        elif mode == 'structured':
            return self.lib.decode_S(filename_bytes)
        elif mode == 'memory':
            return self.lib.decode_M(filename_bytes)
        else:
            raise ValueError("Mode must be 'standard', 'structured', or 'memory'")
    
    def encode_video(self, filename, video_ptr, mode='standard', codec='libx264', fps=30, auto_detect=True):
        """
        Encode a video to file
        
        Args:
            filename: Output file path
            video_ptr: Pointer to Video/SVideo/MVideo structure
            mode: 'standard' (Video), 'structured' (SVideo), or 'memory' (MVideo)
            codec: Video codec for standard formats (libx264, libx265, etc.)
            fps: Frames per second for standard formats
            auto_detect: If True, automatically use standard format encoder for MP4/MOV files
            
        Returns:
            0 on success, -1 on error
        """
        filename_bytes = filename.encode('utf-8')
        
        # Auto-detect standard formats and use FFmpeg encoder
        if auto_detect and self.has_standard_format_support and self._is_standard_format(filename):
            # Standard formats require SVideo structure
            result = self.lib.encode_standard_video(
                filename_bytes,
                video_ptr,
                codec.encode('utf-8'),
                fps
            )
            if result != 0:
                raise RuntimeError(f"Failed to encode video: {filename}")
            return result
        
        # Use custom format encoders
        if mode == 'standard':
            return self.lib.encode(filename_bytes, video_ptr)
        elif mode == 'structured':
            return self.lib.encode_S(filename_bytes, video_ptr)
        elif mode == 'memory':
            return self.lib.encode_M(filename_bytes, video_ptr)
        else:
            raise ValueError("Mode must be 'standard', 'structured', or 'memory'")
    
    def free_video(self, video_ptr, mode='standard'):
        """Free video memory"""
        if mode == 'standard':
            self.lib.free_video(video_ptr)
        elif mode == 'structured':
            self.lib.free_video_S(video_ptr)
        elif mode == 'memory':
            self.lib.free_video_M(video_ptr)
    
    def reverse_video(self, video_ptr, mode='standard'):
        """Reverse video frames"""
        if mode == 'standard':
            self.lib.reverse(video_ptr)
        elif mode == 'structured':
            self.lib.reverse_S(video_ptr)
        elif mode == 'memory':
            self.lib.reverse_M(video_ptr)
    
    def swap_channels(self, video_ptr, channel1, channel2, mode='standard'):
        """Swap color channels"""
        if mode == 'standard':
            self.lib.swap_channels(video_ptr, channel1, channel2)
        elif mode == 'structured':
            self.lib.swap_channels_S(video_ptr, channel1, channel2)
        elif mode == 'memory':
            self.lib.swap_channels_M(video_ptr, channel1, channel2)
    
    def clip_channel(self, video_ptr, channel, min_val, max_val, mode='standard'):
        """Clip channel values to range"""
        if mode == 'standard':
            self.lib.clip_channel(video_ptr, channel, min_val, max_val)
        elif mode == 'structured':
            self.lib.clip_channel_S(video_ptr, channel, min_val, max_val)
        elif mode == 'memory':
            self.lib.clip_channel_M(video_ptr, channel, min_val, max_val)
    
    def scale_channel(self, video_ptr, channel, scale_factor, mode='standard'):
        """Scale channel values"""
        if mode == 'standard':
            self.lib.scale_channel(video_ptr, channel, scale_factor)
        elif mode == 'structured':
            self.lib.scale_channel_S(video_ptr, channel, scale_factor)
        elif mode == 'memory':
            self.lib.scale_channel_M(video_ptr, channel, scale_factor)

def is_standard_format(filename):
    """
    Check if file is a standard video format
    
    Args:
        filename: Path to video file
        
    Returns:
        bool: True if file is MP4, MOV, AVI, etc.
    """
    standard_formats = ['.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv', '.webm']
    ext = os.path.splitext(filename)[1].lower()
    return ext in standard_formats


# Create a global instance for easy access
try:
    video_processor = VideoProcessor()
    VIDEO_PROCESSING_AVAILABLE = True
    STANDARD_FORMAT_SUPPORT = video_processor.has_standard_format_support
except (FileNotFoundError, RuntimeError) as e:
    print(f"Warning: Video processing not available: {e}")
    video_processor = None
    VIDEO_PROCESSING_AVAILABLE = False
    STANDARD_FORMAT_SUPPORT = False