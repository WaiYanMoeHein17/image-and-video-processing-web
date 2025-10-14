#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>

#ifdef WASM_BUILD
#include <emscripten.h>
#define EMSCRIPTEN_KEEPALIVE __attribute__((used))
#else
#define EMSCRIPTEN_KEEPALIVE
#endif

#define CLAMP(value, min, max) \
    ((value) < (min) ? (min) : ((value) > (max) ? (max) : (value)))

// Simplified structures for WASM
typedef struct {
    unsigned char *data;
} Channel;

typedef struct {
    Channel *channels;
} Frame;

typedef struct {
    long num_frames;
    unsigned char channels;
    unsigned char height;
    unsigned char width;
    Frame *frames;
} SVideo;

// WASM-compatible video processing functions
EMSCRIPTEN_KEEPALIVE
SVideo* decode_S_wasm(unsigned char* data, size_t data_size) {
    /**
     * @brief Decode video data from memory buffer for WASM
     * This function expects raw video frame data in a simple format:
     * - Header: num_frames (8 bytes), channels (1 byte), height (1 byte), width (1 byte)
     * - Data: frame data in sequence
     */
    if (!data || data_size < 11) {
        return NULL;
    }

    SVideo *svideo = (SVideo *)malloc(sizeof(SVideo));
    if (!svideo) {
        return NULL;
    }

    // Read header from buffer
    size_t offset = 0;
    memcpy(&svideo->num_frames, data + offset, sizeof(long));
    offset += sizeof(long);
    
    svideo->channels = data[offset++];
    svideo->height = data[offset++];
    svideo->width = data[offset++];

    long num_frames = svideo->num_frames;
    unsigned char num_channels = svideo->channels;
    unsigned char height = svideo->height;
    unsigned char width = svideo->width;
    size_t frame_size = height * width;
    size_t total_channel_data_size = num_frames * num_channels * frame_size;

    // Check if we have enough data
    if (data_size < offset + total_channel_data_size) {
        free(svideo);
        return NULL;
    }

    size_t total_size =
        num_frames * sizeof(Frame) +
        num_frames * num_channels * sizeof(Channel) +
        total_channel_data_size;

    unsigned char *memory_block = (unsigned char *)malloc(total_size);
    if (!memory_block) {
        free(svideo);
        return NULL;
    }

    svideo->frames = (Frame *)memory_block;
    unsigned char *channels_block = memory_block + num_frames * sizeof(Frame);
    unsigned char *data_block = channels_block + num_frames * num_channels * sizeof(Channel);

    for (long frame_idx = 0; frame_idx < num_frames; frame_idx++) {
        Frame *frame = &svideo->frames[frame_idx];
        frame->channels = (Channel *)(channels_block + frame_idx * num_channels * sizeof(Channel));

        for (unsigned char channel_idx = 0; channel_idx < num_channels; channel_idx++) {
            Channel *channel = &frame->channels[channel_idx];
            channel->data = data_block + (frame_idx * num_channels + channel_idx) * frame_size;
        }
    }

    // Copy frame data from input buffer
    memcpy(data_block, data + offset, total_channel_data_size);

    return svideo;
}

EMSCRIPTEN_KEEPALIVE
void free_video_S_wasm(SVideo *video) {
    /**
     * @brief Free memory allocated for a SVideo structure in WASM
     */
    if (!video) return;

    if (video->frames) {
        free(video->frames);
    }
    free(video);
}

EMSCRIPTEN_KEEPALIVE
int reverse_S_wasm(SVideo *video) {
    /**
     * @brief Reverse the order of frames in a SVideo structure (WASM version)
     */
    if (!video || !video->frames) {
        return -1;
    }

    // Process in chunks to manage memory efficiently
    const long CHUNK_SIZE = 100; // Process 100 frames at a time
    long total_frames = video->num_frames;
    
    for (long chunk_start = 0; chunk_start < total_frames / 2; chunk_start += CHUNK_SIZE) {
        long chunk_end = chunk_start + CHUNK_SIZE;
        if (chunk_end > total_frames / 2) {
            chunk_end = total_frames / 2;
        }
        
        for (long i = chunk_start; i < chunk_end; i++) {
            Frame temp;
            memcpy(&temp, &video->frames[i], sizeof(Frame));
            memcpy(&video->frames[i], &video->frames[total_frames - 1 - i], sizeof(Frame));
            memcpy(&video->frames[total_frames - 1 - i], &temp, sizeof(Frame));
        }
    }

    return 0;
}

EMSCRIPTEN_KEEPALIVE
int swap_channels_S_wasm(SVideo *video, unsigned char channel1, unsigned char channel2) {
    /**
     * @brief Swap two channels in a SVideo structure (WASM version)
     */
    if (!video || !video->frames) {
        return -1;
    }

    if (channel1 >= video->channels || channel2 >= video->channels) {
        return -1;
    }

    // Process in chunks to manage memory efficiently
    const long CHUNK_SIZE = 50; // Process 50 frames at a time
    long total_frames = video->num_frames;
    
    for (long chunk_start = 0; chunk_start < total_frames; chunk_start += CHUNK_SIZE) {
        long chunk_end = chunk_start + CHUNK_SIZE;
        if (chunk_end > total_frames) {
            chunk_end = total_frames;
        }
        
        for (long frame = chunk_start; frame < chunk_end; frame++) {
            Channel temp = video->frames[frame].channels[channel1];
            video->frames[frame].channels[channel1] = video->frames[frame].channels[channel2];
            video->frames[frame].channels[channel2] = temp;
        }
    }

    return 0;
}

EMSCRIPTEN_KEEPALIVE
int clip_channel_S_wasm(SVideo *video, unsigned char channel, unsigned char min_value, unsigned char max_value) {
    /**
     * @brief Clip channel values to specified range (WASM version)
     */
    if (!video || channel >= video->channels) {
        return -1;
    }

    size_t channel_size = video->height * video->width;
    
    // Process in chunks to manage memory efficiently
    const long CHUNK_SIZE = 25; // Process 25 frames at a time
    long total_frames = video->num_frames;
    
    for (long chunk_start = 0; chunk_start < total_frames; chunk_start += CHUNK_SIZE) {
        long chunk_end = chunk_start + CHUNK_SIZE;
        if (chunk_end > total_frames) {
            chunk_end = total_frames;
        }
        
        for (long frame_idx = chunk_start; frame_idx < chunk_end; frame_idx++) {
            unsigned char *channel_data = video->frames[frame_idx].channels[channel].data;
            
            for (size_t i = 0; i < channel_size; i++) {
                channel_data[i] = CLAMP(channel_data[i], min_value, max_value);
            }
        }
    }

    return 0;
}

EMSCRIPTEN_KEEPALIVE
int scale_channel_S_wasm(SVideo *video, unsigned char channel, float scale_factor) {
    /**
     * @brief Scale channel values by a factor (WASM version)
     */
    if (!video || channel >= video->channels) {
        return -1;
    }

    size_t channel_size = video->height * video->width;
    
    // Process in chunks to manage memory efficiently
    const long CHUNK_SIZE = 25; // Process 25 frames at a time
    long total_frames = video->num_frames;
    
    for (long chunk_start = 0; chunk_start < total_frames; chunk_start += CHUNK_SIZE) {
        long chunk_end = chunk_start + CHUNK_SIZE;
        if (chunk_end > total_frames) {
            chunk_end = total_frames;
        }
        
        for (long frame_idx = chunk_start; frame_idx < chunk_end; frame_idx++) {
            unsigned char *channel_data = video->frames[frame_idx].channels[channel].data;
            
            for (size_t i = 0; i < channel_size; i++) {
                float scaled_value = channel_data[i] * scale_factor;
                channel_data[i] = CLAMP((unsigned char)scaled_value, 0, 255);
            }
        }
    }

    return 0;
}

EMSCRIPTEN_KEEPALIVE
unsigned char* encode_S_wasm(SVideo *video, size_t *output_size) {
    /**
     * @brief Encode SVideo structure to memory buffer for WASM
     */
    if (!video || !output_size) {
        return NULL;
    }

    size_t frame_size = video->height * video->width;
    size_t total_channel_data_size = video->num_frames * video->channels * frame_size;
    size_t header_size = sizeof(long) + 3; // num_frames + channels + height + width
    
    *output_size = header_size + total_channel_data_size;
    unsigned char *output = (unsigned char *)malloc(*output_size);
    if (!output) {
        *output_size = 0;
        return NULL;
    }

    // Write header
    size_t offset = 0;
    memcpy(output + offset, &video->num_frames, sizeof(long));
    offset += sizeof(long);
    
    output[offset++] = video->channels;
    output[offset++] = video->height;
    output[offset++] = video->width;

    // Write frame data
    for (long frame_idx = 0; frame_idx < video->num_frames; frame_idx++) {
        const Frame *frame = &video->frames[frame_idx];

        for (unsigned char channel_idx = 0; channel_idx < video->channels; channel_idx++) {
            memcpy(output + offset, frame->channels[channel_idx].data, frame_size);
            offset += frame_size;
        }
    }

    return output;
}

// Helper function for JavaScript to get video info
EMSCRIPTEN_KEEPALIVE
int get_video_info(SVideo *video, long *num_frames, unsigned char *channels, unsigned char *height, unsigned char *width) {
    if (!video) return -1;
    
    *num_frames = video->num_frames;
    *channels = video->channels;
    *height = video->height;
    *width = video->width;
    
    return 0;
}