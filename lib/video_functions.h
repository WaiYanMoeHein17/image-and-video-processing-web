#ifndef VEDITOR_NAIVEVIDEO_LIBFILMMASTER2000_H
#define LIBFILMMASTER2000_H

#include <stddef.h>
#include <stdint.h>

typedef struct {
    long num_frames;          // Number of frames in the video
    unsigned char channels;   // Number of channels per frame (1-3)
    unsigned char height;     // Height of each frame in pixels (1-128)
    unsigned char width;      // Width of each frame in pixels (1-128)
    unsigned char *data;      // Pointer to the pixel data
} MVideo;

typedef struct {
    unsigned char *data;
} Channel;

typedef struct {
    Channel *channels;   // Pointer to the pixel data
} Frame;

// Structure to represent video metadata and frame data
typedef struct {
    long num_frames;          // Number of frames in the video
    unsigned char channels;   // Number of channels per frame (1-3)
    unsigned char height;     // Height of each frame in pixels (1-128)
    unsigned char width;      // Width of each frame in pixels (1-128)
    Frame *frames;
} SVideo;

typedef struct {
    long num_frames;          // Number of frames in the video
    unsigned char channels;   // Number of channels per frame (1-3)
    unsigned char height;     // Height of each frame in pixels (1-128)
    unsigned char width;      // Width of each frame in pixels (1-128)
    unsigned char *data;      // Pointer to the pixel data
} Video;

typedef struct {
    unsigned char *data;  // Pointer to the channel's data
    size_t start;         // Start index for this thread
    size_t end;           // End index for this thread
    float scale_factor;   // Scale factor
} ScaleThreadData;

typedef struct {
    unsigned char *data;       // Pointer to the channel's data
    size_t start;              // Start index for this thread
    size_t end;                // End index for this thread
    unsigned char min_value;   // Minimum clipping value
    unsigned char max_value;   // Maximum clipping value
} ClipThreadData;

Video *decode(const char *filename);

SVideo *decode_S(const char *filename);

MVideo *decode_M(const char *filename);

int encode(const char *filename, const Video *video);

int encode_S(const char *filename, const SVideo *video);

int encode_M(const char *filename, const MVideo *video);

void reverse(Video *video);

void reverse_S(SVideo *video);

void reverse_M(MVideo *video);

void swap_channels(Video *video, unsigned char channel1,
unsigned char channel2);

void swap_channels_S(SVideo *video, unsigned char channel1,
unsigned char channel2);

void swap_channels_M(MVideo *video, unsigned char channel1,
unsigned char channel2);

void clip_channel(Video *video, unsigned char channel,
unsigned char min_value, unsigned char max_value);

void clip_channel_S(SVideo *video, unsigned char channel,
unsigned char min_value, unsigned char max_value);

void clip_channel_M(MVideo *video, unsigned char channel,
unsigned char min_value, unsigned char max_value);

void scale_channel(Video *video, unsigned char channel,
float scale_factor);

void scale_channel_S(SVideo *video, unsigned char channel,
float scale_factor);

void scale_channel_M(MVideo *video, unsigned char channel,
float scale_factor);

void scale_channel_SIMD_S (SVideo *video, unsigned char channel);

void free_video(Video *video);

void free_video_S(SVideo *video);

void free_video_M(MVideo *video);

void print_memory_usage(const char *flag, void *video);

#endif   // VEDITOR_NAIVEVIDEO_LIBFILMMASTER2000_H
