#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "video_codec.h"

// FFmpeg headers
#include <libavcodec/avcodec.h>
#include <libavformat/avformat.h>
#include <libavutil/imgutils.h>
#include <libswscale/swscale.h>

int get_video_info(const char *filename, int *width, int *height, 
                   long *num_frames, double *fps) {
    AVFormatContext *fmt_ctx = NULL;
    AVCodecParameters *codecpar = NULL;
    int video_stream_idx = -1;

    // Open input file
    if (avformat_open_input(&fmt_ctx, filename, NULL, NULL) < 0) {
        fprintf(stderr, "Error: Could not open video file: %s\n", filename);
        return -1;
    }

    // Retrieve stream information
    if (avformat_find_stream_info(fmt_ctx, NULL) < 0) {
        fprintf(stderr, "Error: Could not find stream information\n");
        avformat_close_input(&fmt_ctx);
        return -1;
    }

    // Find video stream
    for (unsigned int i = 0; i < fmt_ctx->nb_streams; i++) {
        if (fmt_ctx->streams[i]->codecpar->codec_type == AVMEDIA_TYPE_VIDEO) {
            video_stream_idx = i;
            codecpar = fmt_ctx->streams[i]->codecpar;
            break;
        }
    }

    if (video_stream_idx == -1) {
        fprintf(stderr, "Error: Could not find video stream\n");
        avformat_close_input(&fmt_ctx);
        return -1;
    }

    // Get video information
    *width = codecpar->width;
    *height = codecpar->height;
    *num_frames = fmt_ctx->streams[video_stream_idx]->nb_frames;
    
    // Calculate FPS
    AVRational frame_rate = fmt_ctx->streams[video_stream_idx]->avg_frame_rate;
    *fps = (double)frame_rate.num / frame_rate.den;

    // If nb_frames is not available, estimate from duration
    if (*num_frames == 0 && fmt_ctx->duration != AV_NOPTS_VALUE) {
        double duration = (double)fmt_ctx->duration / AV_TIME_BASE;
        *num_frames = (long)(duration * (*fps));
    }

    avformat_close_input(&fmt_ctx);
    return 0;
}

SVideo *decode_standard_video(const char *filename) {
    AVFormatContext *fmt_ctx = NULL;
    AVCodecContext *codec_ctx = NULL;
    AVCodec *codec = NULL;
    AVFrame *frame = NULL;
    AVFrame *frame_rgb = NULL;
    AVPacket *packet = NULL;
    struct SwsContext *sws_ctx = NULL;
    int video_stream_idx = -1;
    SVideo *svideo = NULL;

    // Open input file
    if (avformat_open_input(&fmt_ctx, filename, NULL, NULL) < 0) {
        fprintf(stderr, "Error: Could not open video file: %s\n", filename);
        return NULL;
    }

    // Retrieve stream information
    if (avformat_find_stream_info(fmt_ctx, NULL) < 0) {
        fprintf(stderr, "Error: Could not find stream information\n");
        goto cleanup;
    }

    // Find video stream
    for (unsigned int i = 0; i < fmt_ctx->nb_streams; i++) {
        if (fmt_ctx->streams[i]->codecpar->codec_type == AVMEDIA_TYPE_VIDEO) {
            video_stream_idx = i;
            break;
        }
    }

    if (video_stream_idx == -1) {
        fprintf(stderr, "Error: Could not find video stream\n");
        goto cleanup;
    }

    // Get codec parameters
    AVCodecParameters *codecpar = fmt_ctx->streams[video_stream_idx]->codecpar;
    
    // Find decoder
    codec = avcodec_find_decoder(codecpar->codec_id);
    if (!codec) {
        fprintf(stderr, "Error: Unsupported codec\n");
        goto cleanup;
    }

    // Allocate codec context
    codec_ctx = avcodec_alloc_context3(codec);
    if (!codec_ctx) {
        fprintf(stderr, "Error: Could not allocate codec context\n");
        goto cleanup;
    }

    // Copy codec parameters to context
    if (avcodec_parameters_to_context(codec_ctx, codecpar) < 0) {
        fprintf(stderr, "Error: Could not copy codec parameters\n");
        goto cleanup;
    }

    // Open codec
    if (avcodec_open2(codec_ctx, codec, NULL) < 0) {
        fprintf(stderr, "Error: Could not open codec\n");
        goto cleanup;
    }

    // Allocate frames
    frame = av_frame_alloc();
    frame_rgb = av_frame_alloc();
    if (!frame || !frame_rgb) {
        fprintf(stderr, "Error: Could not allocate frames\n");
        goto cleanup;
    }

    // Determine required buffer size and allocate buffer
    int num_bytes = av_image_get_buffer_size(AV_PIX_FMT_RGB24, 
                                              codec_ctx->width, 
                                              codec_ctx->height, 1);
    uint8_t *buffer = (uint8_t *)av_malloc(num_bytes * sizeof(uint8_t));

    av_image_fill_arrays(frame_rgb->data, frame_rgb->linesize, buffer,
                        AV_PIX_FMT_RGB24, codec_ctx->width, codec_ctx->height, 1);

    // Initialize SWScale context for color conversion
    sws_ctx = sws_getContext(codec_ctx->width, codec_ctx->height, codec_ctx->pix_fmt,
                             codec_ctx->width, codec_ctx->height, AV_PIX_FMT_RGB24,
                             SWS_BILINEAR, NULL, NULL, NULL);
    if (!sws_ctx) {
        fprintf(stderr, "Error: Could not initialize color conversion context\n");
        goto cleanup;
    }

    // Get frame count
    long num_frames = fmt_ctx->streams[video_stream_idx]->nb_frames;
    if (num_frames == 0) {
        // Estimate from duration if not available
        if (fmt_ctx->duration != AV_NOPTS_VALUE) {
            AVRational frame_rate = fmt_ctx->streams[video_stream_idx]->avg_frame_rate;
            double fps = (double)frame_rate.num / frame_rate.den;
            double duration = (double)fmt_ctx->duration / AV_TIME_BASE;
            num_frames = (long)(duration * fps);
        } else {
            num_frames = 1000; // Default estimate
        }
    }

    // Allocate SVideo structure
    svideo = (SVideo *)malloc(sizeof(SVideo));
    if (!svideo) {
        fprintf(stderr, "Error: Could not allocate SVideo\n");
        goto cleanup;
    }

    svideo->num_frames = 0; // Will update as we decode
    svideo->channels = 3; // RGB
    svideo->height = codec_ctx->height;
    svideo->width = codec_ctx->width;

    // Allocate memory for frames (we'll use a temporary buffer and reallocate)
    size_t frame_size = svideo->height * svideo->width;
    size_t initial_capacity = num_frames > 0 ? num_frames : 1000;
    
    size_t total_size = initial_capacity * sizeof(Frame) +
                       initial_capacity * svideo->channels * sizeof(Channel) +
                       initial_capacity * svideo->channels * frame_size;

    unsigned char *memory_block = (unsigned char *)malloc(total_size);
    if (!memory_block) {
        fprintf(stderr, "Error: Could not allocate memory for frames\n");
        free(svideo);
        svideo = NULL;
        goto cleanup;
    }

    svideo->frames = (Frame *)memory_block;
    unsigned char *channels_block = memory_block + initial_capacity * sizeof(Frame);
    unsigned char *data_block = channels_block + 
                                initial_capacity * svideo->channels * sizeof(Channel);

    // Allocate packet
    packet = av_packet_alloc();
    if (!packet) {
        fprintf(stderr, "Error: Could not allocate packet\n");
        goto cleanup;
    }

    // Decode frames
    long frame_count = 0;
    while (av_read_frame(fmt_ctx, packet) >= 0) {
        if (packet->stream_index == video_stream_idx) {
            // Send packet to decoder
            int ret = avcodec_send_packet(codec_ctx, packet);
            if (ret < 0) {
                fprintf(stderr, "Error sending packet to decoder\n");
                break;
            }

            // Receive decoded frames
            while (ret >= 0) {
                ret = avcodec_receive_frame(codec_ctx, frame);
                if (ret == AVERROR(EAGAIN) || ret == AVERROR_EOF) {
                    break;
                } else if (ret < 0) {
                    fprintf(stderr, "Error during decoding\n");
                    goto cleanup;
                }

                // Check if we need to reallocate
                if (frame_count >= (long)initial_capacity) {
                    initial_capacity *= 2;
                    size_t new_total_size = initial_capacity * sizeof(Frame) +
                                           initial_capacity * svideo->channels * sizeof(Channel) +
                                           initial_capacity * svideo->channels * frame_size;
                    
                    unsigned char *new_memory_block = (unsigned char *)realloc(memory_block, new_total_size);
                    if (!new_memory_block) {
                        fprintf(stderr, "Error: Could not reallocate memory\n");
                        goto cleanup;
                    }
                    
                    memory_block = new_memory_block;
                    svideo->frames = (Frame *)memory_block;
                    channels_block = memory_block + initial_capacity * sizeof(Frame);
                    data_block = channels_block + 
                                initial_capacity * svideo->channels * sizeof(Channel);
                }

                // Convert frame to RGB
                sws_scale(sws_ctx, (const uint8_t * const *)frame->data,
                         frame->linesize, 0, codec_ctx->height,
                         frame_rgb->data, frame_rgb->linesize);

                // Set up frame structure
                Frame *current_frame = &svideo->frames[frame_count];
                current_frame->channels = (Channel *)(channels_block + 
                                         frame_count * svideo->channels * sizeof(Channel));

                // Copy RGB data to separate channels
                for (unsigned char c = 0; c < svideo->channels; c++) {
                    current_frame->channels[c].data = data_block + 
                                                     (frame_count * svideo->channels + c) * frame_size;
                    
                    // Extract channel data from interleaved RGB
                    for (size_t y = 0; y < (size_t)svideo->height; y++) {
                        for (size_t x = 0; x < (size_t)svideo->width; x++) {
                            size_t pixel_idx = y * svideo->width + x;
                            size_t rgb_idx = (y * frame_rgb->linesize[0]) + (x * 3) + c;
                            current_frame->channels[c].data[pixel_idx] = frame_rgb->data[0][rgb_idx];
                        }
                    }
                }

                frame_count++;
            }
        }
        av_packet_unref(packet);
    }

    svideo->num_frames = frame_count;
    printf("Decoded %ld frames from %s\n", frame_count, filename);

cleanup:
    if (packet) av_packet_free(&packet);
    if (buffer) av_free(buffer);
    if (frame_rgb) av_frame_free(&frame_rgb);
    if (frame) av_frame_free(&frame);
    if (sws_ctx) sws_freeContext(sws_ctx);
    if (codec_ctx) avcodec_free_context(&codec_ctx);
    if (fmt_ctx) avformat_close_input(&fmt_ctx);

    return svideo;
}

int encode_standard_video(const char *filename, const SVideo *video, 
                         const char *codec_name, int fps) {
    AVFormatContext *fmt_ctx = NULL;
    AVCodecContext *codec_ctx = NULL;
    AVCodec *codec = NULL;
    AVStream *stream = NULL;
    AVFrame *frame = NULL;
    AVFrame *frame_yuv = NULL;
    AVPacket *packet = NULL;
    struct SwsContext *sws_ctx = NULL;
    int ret = -1;

    if (!filename || !video || !codec_name) {
        fprintf(stderr, "Invalid input to encode_standard_video\n");
        return -1;
    }

    // Allocate output format context
    avformat_alloc_output_context2(&fmt_ctx, NULL, NULL, filename);
    if (!fmt_ctx) {
        fprintf(stderr, "Could not create output context\n");
        return -1;
    }

    // Find encoder
    codec = avcodec_find_encoder_by_name(codec_name);
    if (!codec) {
        fprintf(stderr, "Codec '%s' not found\n", codec_name);
        goto cleanup;
    }

    // Create stream
    stream = avformat_new_stream(fmt_ctx, NULL);
    if (!stream) {
        fprintf(stderr, "Could not create stream\n");
        goto cleanup;
    }

    // Allocate codec context
    codec_ctx = avcodec_alloc_context3(codec);
    if (!codec_ctx) {
        fprintf(stderr, "Could not allocate codec context\n");
        goto cleanup;
    }

    // Set codec parameters
    codec_ctx->width = video->width;
    codec_ctx->height = video->height;
    codec_ctx->time_base = (AVRational){1, fps};
    codec_ctx->framerate = (AVRational){fps, 1};
    codec_ctx->pix_fmt = AV_PIX_FMT_YUV420P;
    codec_ctx->bit_rate = 4000000; // 4 Mbps

    // Some formats require global headers
    if (fmt_ctx->oformat->flags & AVFMT_GLOBALHEADER) {
        codec_ctx->flags |= AV_CODEC_FLAG_GLOBAL_HEADER;
    }

    // Open codec
    if (avcodec_open2(codec_ctx, codec, NULL) < 0) {
        fprintf(stderr, "Could not open codec\n");
        goto cleanup;
    }

    // Copy codec parameters to stream
    if (avcodec_parameters_from_context(stream->codecpar, codec_ctx) < 0) {
        fprintf(stderr, "Could not copy codec parameters\n");
        goto cleanup;
    }

    stream->time_base = codec_ctx->time_base;

    // Open output file
    if (!(fmt_ctx->oformat->flags & AVFMT_NOFILE)) {
        if (avio_open(&fmt_ctx->pb, filename, AVIO_FLAG_WRITE) < 0) {
            fprintf(stderr, "Could not open output file '%s'\n", filename);
            goto cleanup;
        }
    }

    // Write header
    if (avformat_write_header(fmt_ctx, NULL) < 0) {
        fprintf(stderr, "Error writing header\n");
        goto cleanup;
    }

    // Allocate frames
    frame = av_frame_alloc();
    frame_yuv = av_frame_alloc();
    if (!frame || !frame_yuv) {
        fprintf(stderr, "Could not allocate frames\n");
        goto cleanup;
    }

    frame->format = AV_PIX_FMT_RGB24;
    frame->width = video->width;
    frame->height = video->height;

    frame_yuv->format = codec_ctx->pix_fmt;
    frame_yuv->width = video->width;
    frame_yuv->height = video->height;

    // Allocate buffers
    if (av_frame_get_buffer(frame, 0) < 0 || 
        av_frame_get_buffer(frame_yuv, 0) < 0) {
        fprintf(stderr, "Could not allocate frame data\n");
        goto cleanup;
    }

    // Initialize SWScale context
    sws_ctx = sws_getContext(video->width, video->height, AV_PIX_FMT_RGB24,
                             video->width, video->height, codec_ctx->pix_fmt,
                             SWS_BILINEAR, NULL, NULL, NULL);
    if (!sws_ctx) {
        fprintf(stderr, "Could not initialize conversion context\n");
        goto cleanup;
    }

    // Allocate packet
    packet = av_packet_alloc();
    if (!packet) {
        fprintf(stderr, "Could not allocate packet\n");
        goto cleanup;
    }

    // Encode frames
    for (long frame_idx = 0; frame_idx < video->num_frames; frame_idx++) {
        av_frame_make_writable(frame);

        // Convert from planar RGB to interleaved RGB
        for (int y = 0; y < video->height; y++) {
            for (int x = 0; x < video->width; x++) {
                size_t pixel_idx = y * video->width + x;
                size_t rgb_idx = (y * frame->linesize[0]) + (x * 3);
                
                for (unsigned char c = 0; c < 3; c++) {
                    frame->data[0][rgb_idx + c] = 
                        video->frames[frame_idx].channels[c].data[pixel_idx];
                }
            }
        }

        // Convert RGB to YUV
        sws_scale(sws_ctx, (const uint8_t * const *)frame->data,
                 frame->linesize, 0, video->height,
                 frame_yuv->data, frame_yuv->linesize);

        frame_yuv->pts = frame_idx;

        // Encode frame
        ret = avcodec_send_frame(codec_ctx, frame_yuv);
        if (ret < 0) {
            fprintf(stderr, "Error sending frame to encoder\n");
            goto cleanup;
        }

        while (ret >= 0) {
            ret = avcodec_receive_packet(codec_ctx, packet);
            if (ret == AVERROR(EAGAIN) || ret == AVERROR_EOF) {
                break;
            } else if (ret < 0) {
                fprintf(stderr, "Error encoding frame\n");
                goto cleanup;
            }

            // Write packet
            av_packet_rescale_ts(packet, codec_ctx->time_base, stream->time_base);
            packet->stream_index = stream->index;

            ret = av_interleaved_write_frame(fmt_ctx, packet);
            av_packet_unref(packet);

            if (ret < 0) {
                fprintf(stderr, "Error writing frame\n");
                goto cleanup;
            }
        }
    }

    // Flush encoder
    avcodec_send_frame(codec_ctx, NULL);
    while (avcodec_receive_packet(codec_ctx, packet) == 0) {
        av_packet_rescale_ts(packet, codec_ctx->time_base, stream->time_base);
        packet->stream_index = stream->index;
        av_interleaved_write_frame(fmt_ctx, packet);
        av_packet_unref(packet);
    }

    // Write trailer
    av_write_trailer(fmt_ctx);
    ret = 0;
    printf("Encoded %ld frames to %s\n", video->num_frames, filename);

cleanup:
    if (packet) av_packet_free(&packet);
    if (frame) av_frame_free(&frame);
    if (frame_yuv) av_frame_free(&frame_yuv);
    if (sws_ctx) sws_freeContext(sws_ctx);
    if (codec_ctx) avcodec_free_context(&codec_ctx);
    if (fmt_ctx) {
        if (!(fmt_ctx->oformat->flags & AVFMT_NOFILE)) {
            avio_closep(&fmt_ctx->pb);
        }
        avformat_free_context(fmt_ctx);
    }

    return ret;
}