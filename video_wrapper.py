"""
Python wrapper for libFilmMaster2000.c using ctypes
This module provides a Python interface to the C video processing library
"""

import ctypes
from ctypes import Structure, c_long, c_ubyte, POINTER, c_char_p, c_float
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
        if lib_path is None:
            # Look for the DLL in the current project directory first
            current_dir = os.path.dirname(os.path.abspath(__file__))
            lib_path = os.path.join(current_dir, "video_functions.dll")
            
            # If not found locally, raise error
            if not os.path.exists(lib_path):
                raise FileNotFoundError(f"C library not found. Please ensure video_functions.dll is in the project directory or compile video_functions.c to a DLL first.")
        
        try:
            self.lib = ctypes.CDLL(lib_path)
        except OSError as e:
            raise RuntimeError(f"Could not load C library: {e}")
        
        self._setup_function_signatures()
    
    def _setup_function_signatures(self):
        """Set up function signatures for all C functions"""
        
        # decode functions
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
    
    def decode_video(self, filename, mode='standard'):
        """Decode a video file"""
        filename_bytes = filename.encode('utf-8')
        
        if mode == 'standard':
            return self.lib.decode(filename_bytes)
        elif mode == 'structured':
            return self.lib.decode_S(filename_bytes)
        elif mode == 'memory':
            return self.lib.decode_M(filename_bytes)
        else:
            raise ValueError("Mode must be 'standard', 'structured', or 'memory'")
    
    def encode_video(self, filename, video_ptr, mode='standard'):
        """Encode a video to file"""
        filename_bytes = filename.encode('utf-8')
        
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

# Create a global instance for easy access
try:
    video_processor = VideoProcessor()
    VIDEO_PROCESSING_AVAILABLE = True
except (FileNotFoundError, RuntimeError) as e:
    print(f"Warning: Video processing not available: {e}")
    video_processor = None
    VIDEO_PROCESSING_AVAILABLE = False