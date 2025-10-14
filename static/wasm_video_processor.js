// WebAssembly Video Processor Wrapper
// Handles client-side video processing using compiled C functions

class WASMVideoProcessor {
    constructor() {
        this.module = null;
        this.isInitialized = false;
        this.videoPtr = null;
        this.currentVideo = null;
    }

    async initialize() {
        if (this.isInitialized) return true;

        try {
            // Load the WASM module
            if (typeof VideoProcessorModule === 'undefined') {
                throw new Error('WASM module not loaded. Please ensure video_processor.js is included.');
            }

            this.module = await VideoProcessorModule();
            this.isInitialized = true;
            console.log('✅ WASM Video Processor initialized successfully');
            return true;
        } catch (error) {
            console.error('❌ Failed to initialize WASM module:', error);
            return false;
        }
    }

    async processVideoFile(file) {
        if (!this.isInitialized) {
            throw new Error('WASM module not initialized');
        }

        try {
            // For now, we'll create a simple video buffer
            // In a real implementation, you'd decode the actual video file
            const videoData = await this.createMockVideoData(file);
            
            // Allocate memory in WASM
            const dataSize = videoData.length;
            const dataPtr = this.module._malloc(dataSize);
            
            if (!dataPtr) {
                throw new Error('Failed to allocate memory for video data');
            }

            // Copy data to WASM memory
            this.module.HEAPU8.set(videoData, dataPtr);

            // Decode the video
            this.videoPtr = this.module._decode_S_wasm(dataPtr, dataSize);
            
            // Free the input data
            this.module._free(dataPtr);

            if (!this.videoPtr) {
                throw new Error('Failed to decode video data');
            }

            // Get video information
            const numFramesPtr = this.module._malloc(8); // long = 8 bytes
            const channelsPtr = this.module._malloc(1);
            const heightPtr = this.module._malloc(1);
            const widthPtr = this.module._malloc(1);

            const result = this.module._get_video_info(
                this.videoPtr, 
                numFramesPtr, 
                channelsPtr, 
                heightPtr, 
                widthPtr
            );

            if (result === 0) {
                this.currentVideo = {
                    numFrames: this.module.HEAP32[numFramesPtr >> 2],
                    channels: this.module.HEAPU8[channelsPtr],
                    height: this.module.HEAPU8[heightPtr],
                    width: this.module.HEAPU8[widthPtr]
                };
            }

            // Free info pointers
            this.module._free(numFramesPtr);
            this.module._free(channelsPtr);
            this.module._free(heightPtr);
            this.module._free(widthPtr);

            console.log('✅ Video processed successfully:', this.currentVideo);
            return this.currentVideo;

        } catch (error) {
            console.error('❌ Error processing video:', error);
            throw error;
        }
    }

    async createMockVideoData(file) {
        // Create a simple mock video structure for testing
        // In a real implementation, you would:
        // 1. Use FFmpeg.js or similar to decode the actual video
        // 2. Extract frames as raw pixel data
        // 3. Format according to your custom format

        const mockFrames = 30; // 30 frames
        const mockChannels = 3; // RGB
        const mockHeight = 240; // Height in pixels
        const mockWidth = 320; // Width in pixels
        
        const frameSize = mockChannels * mockHeight * mockWidth;
        const totalDataSize = frameSize * mockFrames;
        const headerSize = 8 + 3; // long + 3 bytes

        const buffer = new Uint8Array(headerSize + totalDataSize);
        
        // Write header
        let offset = 0;
        
        // Write num_frames as long (8 bytes, little endian)
        const numFramesBytes = new ArrayBuffer(8);
        const numFramesView = new DataView(numFramesBytes);
        numFramesView.setBigInt64(0, BigInt(mockFrames), true);
        buffer.set(new Uint8Array(numFramesBytes), offset);
        offset += 8;
        
        buffer[offset++] = mockChannels;
        buffer[offset++] = mockHeight;
        buffer[offset++] = mockWidth;

        // Generate mock frame data (simple gradient pattern)
        for (let frame = 0; frame < mockFrames; frame++) {
            for (let y = 0; y < mockHeight; y++) {
                for (let x = 0; x < mockWidth; x++) {
                    for (let c = 0; c < mockChannels; c++) {
                        // Create a simple pattern that varies by frame
                        const value = Math.floor(
                            128 + 
                            64 * Math.sin((x + frame * 5) * 0.02) * 
                            Math.cos((y + frame * 3) * 0.02) * 
                            (c + 1) / mockChannels
                        );
                        buffer[offset++] = Math.max(0, Math.min(255, value));
                    }
                }
            }
        }

        console.log(`📦 Created mock video data: ${mockFrames} frames, ${mockWidth}x${mockHeight}, ${mockChannels} channels`);
        return buffer;
    }

    async reverseVideo() {
        if (!this.videoPtr) {
            throw new Error('No video loaded');
        }

        const result = this.module._reverse_S_wasm(this.videoPtr);
        if (result !== 0) {
            throw new Error('Failed to reverse video');
        }

        console.log('✅ Video reversed successfully');
        return true;
    }

    async swapChannels(channel1, channel2) {
        if (!this.videoPtr) {
            throw new Error('No video loaded');
        }

        const result = this.module._swap_channels_S_wasm(this.videoPtr, channel1, channel2);
        if (result !== 0) {
            throw new Error('Failed to swap channels');
        }

        console.log(`✅ Channels ${channel1} and ${channel2} swapped successfully`);
        return true;
    }

    async clipChannel(channel, minVal, maxVal) {
        if (!this.videoPtr) {
            throw new Error('No video loaded');
        }

        const result = this.module._clip_channel_S_wasm(this.videoPtr, channel, minVal, maxVal);
        if (result !== 0) {
            throw new Error('Failed to clip channel');
        }

        console.log(`✅ Channel ${channel} clipped to range [${minVal}, ${maxVal}]`);
        return true;
    }

    async scaleChannel(channel, scaleFactor) {
        if (!this.videoPtr) {
            throw new Error('No video loaded');
        }

        const result = this.module._scale_channel_S_wasm(this.videoPtr, channel, scaleFactor);
        if (result !== 0) {
            throw new Error('Failed to scale channel');
        }

        console.log(`✅ Channel ${channel} scaled by factor ${scaleFactor}`);
        return true;
    }

    async exportVideo() {
        if (!this.videoPtr) {
            throw new Error('No video loaded');
        }

        // Get output size
        const sizePtr = this.module._malloc(8);
        const outputPtr = this.module._encode_S_wasm(this.videoPtr, sizePtr);
        
        if (!outputPtr) {
            this.module._free(sizePtr);
            throw new Error('Failed to encode video');
        }

        const outputSize = this.module.HEAP32[sizePtr >> 2];
        
        // Copy data from WASM memory to JavaScript
        const outputData = new Uint8Array(outputSize);
        outputData.set(this.module.HEAPU8.subarray(outputPtr, outputPtr + outputSize));

        // Free WASM memory
        this.module._free(outputPtr);
        this.module._free(sizePtr);

        console.log(`✅ Video exported successfully: ${outputSize} bytes`);
        return outputData;
    }

    cleanup() {
        if (this.videoPtr) {
            this.module._free_video_S_wasm(this.videoPtr);
            this.videoPtr = null;
            this.currentVideo = null;
            console.log('🧹 Video memory cleaned up');
        }
    }

    getVideoInfo() {
        return this.currentVideo;
    }

    isVideoLoaded() {
        return this.videoPtr !== null;
    }
}

// Global instance
window.wasmVideoProcessor = new WASMVideoProcessor();

// Auto-initialize when WASM module is available
document.addEventListener('DOMContentLoaded', async () => {
    // Wait a bit for the WASM module to load
    setTimeout(async () => {
        try {
            await window.wasmVideoProcessor.initialize();
        } catch (error) {
            console.warn('WASM initialization failed, falling back to server-side processing:', error);
        }
    }, 1000);
});