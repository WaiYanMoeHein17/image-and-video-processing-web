#ifndef VIDEO_CODEC_H
#define VIDEO_CODEC_H

#include "video_functions.h"

/**
 * @brief Video codec wrapper for standard formats (MP4, MOV, AVI, etc.)
 * Uses FFmpeg for encoding/decoding
 */

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief Decode a standard video file (MP4, MOV, AVI, etc.) to SVideo format
 * 
 * @param filename Path to the input video file
 * @return SVideo* Pointer to decoded video, or NULL on error
 */
SVideo *decode_standard_video(const char *filename);

/**
 * @brief Encode an SVideo structure to a standard video file
 * 
 * @param filename Path to the output video file
 * @param video Pointer to the SVideo structure
 * @param codec_name Codec name (e.g., "libx264" for H.264, "libx265" for H.265)
 * @param fps Frames per second (e.g., 30, 60)
 * @return int 0 on success, -1 on error
 */
int encode_standard_video(const char *filename, const SVideo *video, 
                         const char *codec_name, int fps);

/**
 * @brief Get video information without full decoding
 * 
 * @param filename Path to the video file
 * @param width Output parameter for video width
 * @param height Output parameter for video height
 * @param num_frames Output parameter for number of frames
 * @param fps Output parameter for frames per second
 * @return int 0 on success, -1 on error
 */
int get_video_info(const char *filename, int *width, int *height, 
                   long *num_frames, double *fps);

#ifdef __cplusplus
}
#endif

#endif // VIDEO_CODEC_H