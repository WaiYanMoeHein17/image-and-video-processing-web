#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <immintrin.h>
#include "video_functions.h"


#define CLAMP(value, min, max) \
    ((value) < (min) ? (min) : ((value) > (max) ? (max) : (value)))

Video *decode(const char *filename) {
    /**
     * @brief Decodes a video file into a Video structure.
     * 
     * @param filename Path to the video file.
     * @return Pointer to a Video structure containing the video
     *         data, or NULL if an error occurred.
     */
    FILE *file = fopen(filename, "rb");
    if (!file) {
        perror("Error opening file");
        return NULL;
    }

    Video *video = (Video *)malloc(sizeof(Video));
    if (!video) {
        perror("Error allocating memory for Video");
        fclose(file);
        return NULL;
    }

    if (fread(&video->num_frames, sizeof(long), 1, file) != 1 ||
        fread(&video->channels, sizeof(unsigned char), 1, file) != 1 ||
        fread(&video->height, sizeof(unsigned char), 1, file) != 1 ||
        fread(&video->width, sizeof(unsigned char), 1, file) != 1) {
        perror("Error reading video header");
        free(video);
        fclose(file);
        return NULL;
    }

    size_t frame_size = video->channels * video->height * video->width;
    size_t total_size = frame_size * video->num_frames;

    video->data = (unsigned char *)malloc(total_size);
    if (!video->data) {
        perror("Error allocating memory for frame data");
        free(video);
        fclose(file);
        return NULL;
    }

    if (fread(video->data, 1, total_size, file) != total_size) {
        perror("Error reading frame data");
        free(video->data);
        free(video);
        fclose(file);
        return NULL;
    }

    fclose(file);
    return video;
}

SVideo *decode_S(const char *filename) {
    /**
     * @brief Decodes a video file into a contiguous memory block
     *        -S mode
     * 
     * @param filename Path to the video file.
     * @return Pointer to a SVideo structure containing the video
     *         data, or NULL if an error occurred.
     */
    FILE *file = fopen(filename, "rb");
    if (!file) {
        perror("Error opening file");
        return NULL;
    }

    SVideo *svideo = (SVideo *)malloc(sizeof(SVideo));
    if (!svideo) {
        perror("Error allocating memory for SVideo");
        fclose(file);
        return NULL;
    }

    if (fread(&svideo->num_frames, sizeof(long), 1, file) != 1 ||
        fread(&svideo->channels, sizeof(unsigned char), 1, file) != 1 ||
        fread(&svideo->height, sizeof(unsigned char), 1, file) != 1 ||
        fread(&svideo->width, sizeof(unsigned char), 1, file) != 1) {
        perror("Error reading video header");
        free(svideo);
        fclose(file);
        return NULL;
    }

    long num_frames = svideo->num_frames;
    unsigned char num_channels = svideo->channels;
    unsigned char height = svideo->height;
    unsigned char width = svideo->width;
    size_t frame_size = height * width;
    size_t total_channel_data_size = num_frames * num_channels * frame_size;

    size_t total_size =
        num_frames * sizeof(Frame) +
        num_frames * num_channels * sizeof(Channel) +
        total_channel_data_size;

    unsigned char *memory_block = (unsigned char *)malloc(total_size);
    if (!memory_block) {
        perror("Error allocating contiguous memory block");
        free(svideo);
        fclose(file);
        return NULL;
    }

    svideo->frames = (Frame *)memory_block;
    unsigned char *channels_block = memory_block +
num_frames * sizeof(Frame);
    unsigned char *data_block = channels_block +
num_frames * num_channels * sizeof(Channel);

    for (long frame_idx = 0; frame_idx <
    num_frames; frame_idx++) {
        Frame *frame = &svideo->frames[frame_idx];
        frame->channels = (Channel *)(channels_block + frame_idx *
        num_channels * sizeof(Channel));

        for (unsigned char channel_idx = 0; channel_idx <
        num_channels; channel_idx++) {
            frame->channels[channel_idx].data = data_block +
            frame_idx * num_channels * frame_size +
            channel_idx * frame_size;
        }
    }

    if (fread(data_block, 1, total_channel_data_size, file)
    != total_channel_data_size) {
        perror("Error reading channel data");
        free(memory_block);
        free(svideo);
        fclose(file);
        return NULL;
    }

    fclose(file);
    return svideo;
}

MVideo *decode_M(const char *filename) {
    /**
     * @brief Decodes a video file into a Video structure.
     * 
     * @param filename Path to the video file.
     * @return Pointer to a Video structure containing the video
     *         data, or NULL if an error occurred.
     */
    FILE *file = fopen(filename, "rb");
    if (!file) {
        perror("Error opening file");
        return NULL;
    }

    MVideo *video = (MVideo *)malloc(sizeof(MVideo));
    if (!video) {
        perror("Error allocating memory for Video");
        fclose(file);
        return NULL;
    }

    if (fread(&video->num_frames, sizeof(long), 1, file) != 1 ||
        fread(&video->channels, sizeof(unsigned char), 1, file) != 1 ||
        fread(&video->height, sizeof(unsigned char), 1, file) != 1 ||
        fread(&video->width, sizeof(unsigned char), 1, file) != 1) {
        perror("Error reading video header");
        free(video);
        fclose(file);
        return NULL;
    }

    size_t frame_size = video->channels * video->height * video->width;
    size_t total_size = frame_size * video->num_frames;

    video->data = (unsigned char *)malloc(total_size);
    if (!video->data) {
        perror("Error allocating memory for frame data");
        free(video);
        fclose(file);
        return NULL;
    }

    if (fread(video->data, 1, total_size, file) != total_size) {
        perror("Error reading frame data");
        free(video->data);
        free(video);
        fclose(file);
        return NULL;
    }

    fclose(file);
    return video;
}

void free_video(Video *video) {
    /**
     * @brief Frees memory allocated for a Video structure.
     * 
     * @param video Pointer to the Video structure.
     */
    if (video) {
        free(video->data);
        free(video);
    }
}

void free_video_S(SVideo *video) {
    /**
     * @brief Frees memory allocated for a SVideo structure.
     * 
     * @param video Pointer to the SVideo structure.
     */
    if (!video) return;

    free(video->frames);
    free(video);
}

void free_video_M(MVideo *video) {
    /**
     * @brief Frees memory allocated for a MVideo structure.
     * 
     * @param video Pointer to the MVideo structure.
     */
    if (!video) return;

    //  printf("Freeing video->data\n"); debug
    if (video->data) {
        free(video->data);
        video->data = NULL;
    }

    //  printf("Freeing MVideo struct\n"); debug
    free(video);
}

int encode(const char *filename, const Video *video) {
    /**
     * @brief Encodes a Video structure into a video file.
     *        -O mode, no optimisation
     * @param filename Path to the output video file.
     * @param video Pointer to the Video structure.
     * @return 0 if successful, -1 if an error occurred.
     */
    if (!filename || !video) {
        fprintf(stderr, "Invalid input to encode function.\n");
        return -1;
    }

    FILE *file = fopen(filename, "wb");
    if (!file) {
        perror("Error opening file for writing");
        return -1;
    }

    if (fwrite(&video->num_frames, sizeof(long), 1, file) != 1 ||
        fwrite(&video->channels, sizeof(unsigned char), 1, file) != 1 ||
        fwrite(&video->height, sizeof(unsigned char), 1, file) != 1 ||
        fwrite(&video->width, sizeof(unsigned char), 1, file) != 1) {
        perror("Error writing video header");
        fclose(file);
        return -1;
    }

    size_t frame_size = video->channels * video->height * video->width;
    size_t total_size = frame_size * video->num_frames;

    if (fwrite(video->data, 1, total_size, file) != total_size) {
        perror("Error writing frame data");
        fclose(file);
        return -1;
    }

    fclose(file);
    return 0;
}

int encode_S(const char *filename, const SVideo *video) {
    /**
     * @brief Encodes a SVideo structure into a video file.
     *        -S mode, optimised for runtime
     * @param filename Path to the output video file.
     * @param video Pointer to the SVideo structure.
     * @return 0 if successful, -1 if an error occurred.
     */
    if (!filename || !video) {
        fprintf(stderr, "Invalid input to encode function.\n");
        return -1;
    }

    FILE *file = fopen(filename, "wb");
    if (!file) {
        perror("Error opening file for writing");
        return -1;
    }

    if (fwrite(&video->num_frames, sizeof(long), 1, file) != 1 ||
        fwrite(&video->channels, sizeof(unsigned char), 1, file) != 1 ||
        fwrite(&video->height, sizeof(unsigned char), 1, file) != 1 ||
        fwrite(&video->width, sizeof(unsigned char), 1, file) != 1) {
        perror("Error writing video header");
        fclose(file);
        return -1;
    }

    for (long frame_idx = 0; frame_idx <
    video->num_frames; frame_idx++) {
        const Frame *frame = &video->frames[frame_idx];

        for (unsigned char channel_idx = 0; channel_idx <
        video->channels; channel_idx++) {
            const Channel *channel = &frame->channels[channel_idx];
            size_t channel_size = video->height * video->width;

            if (fwrite(channel->data, 1, channel_size, file) != channel_size) {
                perror("Error writing Channel data");
                fclose(file);
                return -1;
            }
        }
    }

    fclose(file);
    return 0;
}

int encode_M(const char *filename, const MVideo *video) {
    /**
     * @brief Encodes a Video structure into a video file.
     *        -M mode, optimised for memory usage
     * @param filename Path to the output video file.
     * @param video Pointer to the Video structure.
     * @return 0 if successful, -1 if an error occurred.
     */
    if (!filename || !video) {
        fprintf(stderr, "Invalid input to encode function.\n");
        return -1;
    }

    FILE *file = fopen(filename, "wb");
    if (!file) {
        perror("Error opening file for writing");
        return -1;
    }

    if (fwrite(&video->num_frames, sizeof(long), 1, file) != 1 ||
        fwrite(&video->channels, sizeof(unsigned char), 1, file) != 1 ||
        fwrite(&video->height, sizeof(unsigned char), 1, file) != 1 ||
        fwrite(&video->width, sizeof(unsigned char), 1, file) != 1) {
        perror("Error writing video header");
        fclose(file);
        return -1;
    }

    size_t frame_size = video->channels * video->height * video->width;
    size_t total_size = frame_size * video->num_frames;

    if (fwrite(video->data, 1, total_size, file) != total_size) {
        perror("Error writing frame data");
        fclose(file);
        return -1;
    }

    fclose(file);
    return 0;
}

void reverse(Video *video) {
    /**
     * @brief Reverses the order of frames in a Video structure.
     *        -O mode, no optimisation
     * @param video Pointer to the Video structure.
     */
    if (!video || !video->data) {
        fprintf(stderr, "Invalid input to reverse function.\n");
        return;
    }

    size_t frame_size = video->channels * video->height * video->width;

    unsigned char *temp = (unsigned char *)malloc(frame_size);
    if (!temp) {
        perror("Error allocating memory for reverse function");
        return;
    }

    for (long i = 0; i < video->num_frames / 2; i++) {
        unsigned char *frame1 = video->data + i * frame_size;
        unsigned char *frame2 = video->data +
        (video->num_frames - 1 - i) * frame_size;

        memcpy(temp, frame1, frame_size);
        memcpy(frame1, frame2, frame_size);
        memcpy(frame2, temp, frame_size);
    }

    free(temp);
}

void reverse_S(SVideo *video) {
    /**
     * @brief Reverses the order of frames in a SVideo structure.
     *        - S mode, optimised for runtime 
     *        in-place reversal
     * @param video Pointer to the SVideo structure.
     */
    if (!video || !video->frames) {
        fprintf(stderr, "Invalid input to reverse_S function.\n");
        return;
    }

    // One for loop to reverse all frames O(n/2)
    for (long i = 0; i < video->num_frames / 2; i++) {
        Frame temp;
        memcpy(&temp, &video->frames[i], sizeof(Frame));
        memcpy(&video->frames[i], &video->frames[video->num_frames - 1 - i],
        sizeof(Frame));
        memcpy(&video->frames[video->num_frames - 1 - i], &temp, sizeof(Frame));
    }
}

void reverse_M(MVideo *video) {
    /**
     * @brief Reverses the order of frames in a Video structure.
     *        -M mode, optimised for memory usage
     * @param video Pointer to the Video structure.
     */
    if (!video || !video->data) {
        fprintf(stderr, "Invalid input to reverse function.\n");
        return;
    }

    size_t frame_size = video->channels * video->height * video->width;

    unsigned char *temp = (unsigned char *)malloc(frame_size);
    if (!temp) {
        perror("Error allocating memory for reverse function");
        return;
    }

    for (long i = 0; i < video->num_frames / 2; i++) {
        unsigned char *frame1 = video->data + i * frame_size;
        unsigned char *frame2 = video->data +
        (video->num_frames - 1 - i) * frame_size;

        memcpy(temp, frame1, frame_size);
        memcpy(frame1, frame2, frame_size);
        memcpy(frame2, temp, frame_size);
    }

    free(temp);
}

void swap_channels(Video *video, unsigned char channel1,
unsigned char channel2) {
    /**
     * @brief Swaps two channels in a Video structure.
     *        -O mode, no optimisation, flat structure
     * @param video Pointer to the Video structure.
     * @param channel1 first channel to swap.
     * @param channel2 second channel to swap.
     */
    if (!video || !video->data) {
        fprintf(stderr, "Invalid input to swap_channels function.\n");
        return;
    }

    // Validate channel indices
    if (channel1 >= video->channels || channel2 >= video->channels) {
        fprintf(stderr, "Channel indices out of bounds.\n");
        return;
    }

    size_t frame_size = video->channels * video->height * video->width;
    size_t channel_size = video->height * video->width;

    for (long frame_idx = 0; frame_idx < video->num_frames; frame_idx++) {
        size_t offset1 = frame_idx * frame_size + channel1 * channel_size;
        size_t offset2 = frame_idx * frame_size + channel2 * channel_size;

        for (size_t i = 0; i < channel_size; i++) {
            unsigned char temp = video->data[offset1 + i];
            video->data[offset1 + i] = video->data[offset2 + i];
            video->data[offset2 + i] = temp;
        }
    }
}

void swap_channels_S(SVideo *video, unsigned char channel1,
unsigned char channel2) {
    /**
     * @brief Swaps two channels in a SVideo structure.
     *        -S mode, optimised for runtime, hierarchical
     * @param video Pointer to the SVideo structure.
     * @param channel1 first channel to swap.
     * @param channel2 second channel to swap.
     */
    if (channel1 >= video->channels || channel2 >= video->channels) {
        fprintf(stderr, "Channel indices out of bounds.\n");
        return;
    }

    if (!video || !video->frames) {
        fprintf(stderr, "Invalid input to swap_channel_S function.\n");
        return;
    }

    // One for loop to swap all channels in all frames O(n)
    for (long frame = 0; frame < video->num_frames; frame++) {
        Channel temp = video->frames[frame].channels[channel1];
        video->frames[frame].channels[channel1] =
        video->frames[frame].channels[channel2];
        video->frames[frame].channels[channel2] = temp;
    }
}

void swap_channels_M(MVideo *video, unsigned char channel1,
unsigned char channel2) {
    /**
     * @brief Swaps two channels in a Video structure.
     *        -M mode, optimised for memory usage
     * @param video Pointer to the Video structure.
     * @param channel1 first channel to swap.
     * @param channel2 second channel to swap.
     */
    if (!video || !video->data) {
        fprintf(stderr, "Invalid input to swap_channels function.\n");
        return;
    }

    // Validate channel indices
    if (channel1 >= video->channels || channel2 >= video->channels) {
        fprintf(stderr, "Channel indices out of bounds.\n");
        return;
    }

    size_t frame_size = video->channels * video->height * video->width;
    size_t channel_size = video->height * video->width;

    for (long frame_idx = 0; frame_idx < video->num_frames; frame_idx++) {
        size_t offset1 = frame_idx * frame_size + channel1 * channel_size;
        size_t offset2 = frame_idx * frame_size + channel2 * channel_size;

        for (size_t i = 0; i < channel_size; i++) {
            unsigned char temp = video->data[offset1 + i];
            video->data[offset1 + i] = video->data[offset2 + i];
            video->data[offset2 + i] = temp;
        }
    }
}

void clip_channel(Video *video, unsigned char channel,
unsigned char min_val, unsigned char max_val) {
    /**
     * @brief Clips the values of a channel in a Video structure to 
     *        specfic range. [min_val, max_val]
     *        -O mode, no optimisation
     * @param video Pointer to the Video structure.
     * @param channel Channel index to clip.
     * @param min_val Minimum value for clipping.
     * @param max_val Maximum value for clipping.
     */
    if (!video || !video->data) {
        fprintf(stderr, "Invalid input to clip_channel function.\n");
        return;
    }

    if (channel >= video->channels) {
        fprintf(stderr, "Channel index out of bounds.\n");
        return;
    }

    size_t frame_size = video->channels * video->height * video->width;
    size_t channel_size = video->height * video->width;

    for (long frame_idx = 0; frame_idx < video->num_frames; frame_idx++) {
        size_t channel_offset = frame_idx * frame_size + channel * channel_size;
        unsigned char *channel_data = &video->data[channel_offset];

        for (size_t i = 0; i < channel_size; i++) {
            channel_data[i] = CLAMP(channel_data[i], min_val, max_val);
        }
    }
}

void clip_channel_S(SVideo *video, unsigned char channel,
unsigned char min_value, unsigned char max_value) {
    /**
     * @brief Clips the values of a channel in a SVideo structure to
     *        a specific range. [min_value, max_value]
     *        -S mode, optimised for runtime
     *        SIMD utilization
     * @param video Pointer to the SVideo structure.
     * @param channel Channel index to clip.
     * @param min_value Minimum value for clipping.
     * @param max_value Maximum value for clipping.
     */
    if (!video || channel >= video->channels) {
        fprintf(stderr, "Invalid input to clip_channel_SIMD_SVideo.\n");
        return;
    }

        size_t channel_size = video->height * video->width;
    __m256i min_val_vec = _mm256_set1_epi8(min_value);
    __m256i max_val_vec = _mm256_set1_epi8(max_value);

    for (long frame_idx = 0; frame_idx < video->num_frames; frame_idx++) {
        unsigned char *data = video->frames[frame_idx].channels[channel].data;
        size_t i = 0;

        for (; i + 31 < channel_size; i += 32) {
            // Load 32 pixels into vector
            __m256i pixels = _mm256_loadu_si256((__m256i *)&data[i]);

            // Clip ALL pixel values simultaneously
            pixels = _mm256_min_epu8(_mm256_max_epu8(pixels, min_val_vec),
            max_val_vec);

            // store the clipped pixels back to memory
            _mm256_storeu_si256((__m256i *)&data[i], pixels);
        }

        for (; i < channel_size; i++) {
            data[i] = CLAMP(data[i], min_value, max_value);
        }
    }
}

void clip_channel_M(MVideo *video, unsigned char channel,
unsigned char min_val, unsigned char max_val) {
    /**
     * @brief Clips the values of a channel in a Video structure to 
     *        specfic range. [min_val, max_val]
     *        -M mode, optimised for memory usage
     * @param video Pointer to the Video structure.
     * @param channel Channel index to clip.
     * @param min_val Minimum value for clipping.
     * @param max_val Maximum value for clipping.
     */
    if (!video || !video->data) {
        fprintf(stderr, "Invalid input to clip_channel function.\n");
        return;
    }

    if (channel >= video->channels) {
        fprintf(stderr, "Channel index out of bounds.\n");
        return;
    }

    size_t frame_size = video->channels * video->height * video->width;
    size_t channel_size = video->height * video->width;

    for (long frame_idx = 0; frame_idx < video->num_frames; frame_idx++) {
        size_t channel_offset = frame_idx * frame_size + channel * channel_size;
        unsigned char *channel_data = &video->data[channel_offset];

        for (size_t i = 0; i < channel_size; i++) {
            channel_data[i] = CLAMP(channel_data[i], min_val, max_val);
        }
    }
}

void scale_channel(Video *video, unsigned char channel, float scale_factor) {
    /**
     * @brief Scales the values of a channel in a Video structure by a
     *        specific factor. [scale_factor]
     *        -O mode, no optimisation
     * @param video Pointer to the Video structure.
     * @param channel Channel to scale.
     * @param scale_factor Factor to scale the channel values.
     */
    if (!video || !video->data) {
        fprintf(stderr, "Invalid input to scale_channel function.\n");
        return;
    }

    if (channel >= video->channels) {
        fprintf(stderr, "Channel index out of bounds.\n");
        return;
    }

    size_t frame_size = video->channels * video->height * video->width;
    size_t channel_size = video->height * video->width;

    for (long frame_idx = 0; frame_idx < video->num_frames; frame_idx++) {
        size_t channel_offset = frame_idx * frame_size + channel * channel_size;
        unsigned char *channel_data = &video->data[channel_offset];

        for (size_t i = 0; i < channel_size; i++) {
            float scaled_value = channel_data[i] * scale_factor;
            channel_data[i] = (unsigned char)CLAMP(scaled_value, 0.0f, 255.0f);
        }
    }
}

void scale_channel_S(SVideo *video, unsigned char channel,
float scale_factor) {
    /**
     * @brief Scales the values of a channel in a SVideo structure by a
     *       specific factor. [scale_factor]
     *       -S mode, optimised for runtime
     *       Loop unrolling and prefetching
     * @param video Pointer to the SVideo structure.
     * @param channel Channel to scale.
     * @param scale_factor Factor to scale the channel values.
     */
    if (!video || channel >= video->channels) {
        fprintf(stderr, "Invalid input to scale_channel_S_S function.\n");
        return;
    }

    for (long frame_idx = 0; frame_idx < video->num_frames; frame_idx++) {
        Frame *frame = &video->frames[frame_idx];
        Channel *chan = &frame->channels[channel];
        size_t channel_size = video->height * video->width;
        unsigned char *data = chan->data;

        size_t i = 0;
        for (; i + 31 < channel_size; i += 32) {
            __builtin_prefetch(&data[i + 32], 0, 1);

            for (size_t j = 0; j < 32; j++) {
                float scaled_value = data[i + j] * scale_factor;
                data[i + j] = CLAMP(scaled_value, 0.0f, 255.0f);
            }
        }

        for (; i < channel_size; i++) {
            float scaled_value = data[i] * scale_factor;
            data[i] = CLAMP(scaled_value, 0.0f, 255.0f);
        }
    }
}

void scale_channel_M(MVideo *video, unsigned char channel, float scale_factor) {
    /**
     * @brief Scales the values of a channel in a Video structure by a
     *        specific factor. [scale_factor]
     *        -M mode, optimised for memory usage
     * @param video Pointer to the Video structure.
     * @param channel Channel to scale.
     * @param scale_factor Factor to scale the channel values.
     */
    if (!video || !video->data) {
        fprintf(stderr, "Invalid input to scale_channel function.\n");
        return;
    }

    if (channel >= video->channels) {
        fprintf(stderr, "Channel index out of bounds.\n");
        return;
    }

    size_t frame_size = video->channels * video->height * video->width;
    size_t channel_size = video->height * video->width;

    for (long frame_idx = 0; frame_idx < video->num_frames; frame_idx++) {
        size_t channel_offset = frame_idx * frame_size + channel * channel_size;
        unsigned char *channel_data = &video->data[channel_offset];

        for (size_t i = 0; i < channel_size; i++) {
            float scaled_value = channel_data[i] * scale_factor;
            channel_data[i] = (unsigned char)CLAMP(scaled_value, 0.0f, 255.0f);
        }
    }
}

// end
