import cv2
import os 
import argparse
import sys
import math
import numpy as np
import skimage
import pywt

def read_img(img):
    """Reads the image.

    Args:
        img (str): Path to the image file.

    Returns:
        numpy.ndarray: Array representing the image pixels.
    """
    img = cv2.imread(img, cv2.IMREAD_COLOR)
    return img

def exponential_transform(img, c=1, alpha=1.2):
    """Decreases the dynamic range of dark regions
    whilst increasing the dynamic range in light 
    regions. Enhances detail in high value (bright) 
    regions. Use for BRIGHT IMAGES/REGIONS.

    Args:
        img (numpy.ndarray): The image.
        c (float): Scaling constant.
        alpha (float): Exponent base.
    """
    img = img.astype(np.float32)
    img = c * (np.power(1 + alpha / 255.0, img) - 1)
    img = np.clip(img, 0, 255).astype(np.uint8)
    return img

def logarithmic_transform(img):
    """Increases the dynamic range of dark parts
    of the image, Decreases the dynamic range of 
    bright parts of the images. 
    Spreads out the low values(dark) and compresses
    high values(bright)
    Use for DARK IMAGES. 

    Args:
        img (numpy.ndarray): the image

    Returns:
        numpy.ndarray: Transformed image.
    """
    img = img.astype(np.float32)
    c = 255 / np.log(1 + np.max(img))
    log_img = c * np.log(1 + img)
    log_img = np.clip(log_img, 0, 255).astype(np.uint8)
    return log_img

def restore_edges(img):
    """
    Restores edges in the image using a sharpening filter.

    Args:
        img (numpy.ndarray): Input image.

    Returns:
        numpy.ndarray: Image with restored edges.
    """
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    restored_img = cv2.filter2D(img, -1, kernel)
    
    return restored_img

def remove_salt_pepper_noise(img, kernel_size=3):
    """
    Removes salt and pepper noise using median filtering.

    Args:
        img (numpy.ndarray): Input image.
        kernel_size (int): Size of the kernel (default=3).

    Returns:
        numpy.ndarray: Image with reduced salt and pepper noise.
    """
    return cv2.medianBlur(img, kernel_size)

def extract_high_frequency(org_img, denoised_img):
    """
    Extracts high-frequency details from an image using a Laplacian filter.

    Args:
        org_img (numpy.ndarray): Original image.
        denoised_img (numpy.ndarray): Denoised image.

    Returns:
        numpy.ndarray: High-frequency details extracted from the image.
    """
    high_freq = cv2.subtract(org_img, denoised_img)  # Subtract blurred image from original
    return high_freq

def enhance_with_high_frequency(denoised_img, original_img, alpha=1.5):
    """
    Enhances a denoised image by adding high-frequency details from the original.

    Args:
        denoised_img (numpy.ndarray): The denoised image.
        original_img (numpy.ndarray): The original image.
        alpha (float): Weight of the high-frequency details to be added.

    Returns:
        numpy.ndarray: Enhanced image with high-frequency details.
    """
    # Extract high-frequency details by subtracting the denoised image from the original
    high_freq_details = cv2.subtract(original_img, denoised_img)
    
    # Add the high-frequency details to the denoised image with a specified weight
    enhanced_img = cv2.addWeighted(denoised_img, 1, high_freq_details, alpha, 0)
    
    return enhanced_img

def denoise_image(img, h, hColor, templateWindowSize=7, searchWindowSize=21):
    """
    Denoises an image using OpenCV's Non-Local Means Denoising algorithm.

    Parameters:
        img (numpy.ndarray): Input noisy image.
        h (int): Strength of noise removal for grayscale.
        hColor (int): Strength of noise removal for color images.
        templateWindowSize (int): Size of the template patch (default=7).
        searchWindowSize (int): Size of the window used to compute weighted average (default=21).

    Returns:
        numpy.ndarray: Denoised image.
    """
    # Apply Non-Local Means Denoising
    denoised = cv2.fastNlMeansDenoisingColored(img, None, h, hColor, templateWindowSize, searchWindowSize)
    return denoised

def inpaint_black_circle(img):
    """
    Inpaints black circles in the image.

    Args:
        img (numpy.ndarray): Input image.

    Returns:
        numpy.ndarray: Image with inpainted black circles.
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Create a binary mask for black regions in the top-right quadrant
    h, w = gray.shape
    top_right_quadrant = gray[0:h // 2, w // 2:w]
    mask = cv2.inRange(top_right_quadrant, 0, 10)  # Detect very dark regions

    # Apply morphological operations to refine the mask
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    # Create a full-size mask and place the refined mask in the top-right quadrant
    full_mask = np.zeros_like(gray)
    full_mask[0:h // 2, w // 2:w] = mask

    # Inpaint the image
    inpainted = cv2.inpaint(img, full_mask, inpaintRadius=10, flags=cv2.INPAINT_TELEA)

    return inpainted

def find_best_patch_quadrant_optimized(target_patch, target_mask, source_img, source_conf,
                                       patch_size=9, stride=3, region='bottom-left'):
    """
    Finds the best matching patch in a specified quadrant of the source image.

    Args:
        target_patch (np.ndarray): The patch to be filled.
        target_mask (np.ndarray): Mask indicating known regions in the target patch.
        source_img (np.ndarray): The source image from which patches are sampled.
        source_conf (np.ndarray): Confidence map of the source image.
        patch_size (int): Size of the square patch (default=9).
        stride (int): Step size for sampling candidate patches (default=3).
        region (str): Quadrant to search for patches ('bottom', 'bottom-left', 'left').

    Returns:
        np.ndarray: Best matching patch from the source image.
    """
    h, w = source_conf.shape[:2]
    half = patch_size // 2
    min_ssd = float('inf')
    best_patch = None

    # Define search bounds based on region
    y_range = range(half, h - half, stride)
    x_range = range(half, w - half, stride)

    if region == 'bottom':
        y_range = range(h // 2, h - half, stride)
    elif region == 'bottom-left':
        y_range = range(h // 2, h - half, stride)
        x_range = range(half, w // 2, stride)
    elif region == 'left':
        x_range = range(half, w // 2, stride)

    # Search for the best matching patch
    for y in y_range:
        for x in x_range:
            conf_patch = source_conf[y - half:y + half + 1, x - half:x + half + 1]
            if np.all(conf_patch == 1):
                candidate_patch = source_img[y - half:y + half + 1, x - half:x + half + 1]
                ssd = np.sum((target_patch[target_mask] - candidate_patch[target_mask]) ** 2)
                if ssd < min_ssd:
                    min_ssd = ssd
                    best_patch = candidate_patch.copy()

    return best_patch

def criminisi_inpaint_black_circle(img, patch_size=9, stride=3):
    """
    Inpaints a black circle region (top-right) using Criminisi exemplar-based patch filling.

    Args:
        img (np.ndarray): Input BGR image with black circle in top-right.
        patch_size (int): Size of the square patch (must be odd).
        stride (int): Step size for sampling candidate patches.

    Returns:
        np.ndarray: Inpainted BGR image.
    """
    img = img.copy()
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Detect black region
    mask = cv2.inRange(gray, 0, 10)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))

    h, w = gray.shape
    filled = (mask == 0).astype(np.uint8)
    confidence = filled.astype(np.float32)

    half = patch_size // 2
    padded_img = cv2.copyMakeBorder(img, half, half, half, half, cv2.BORDER_REFLECT)
    padded_conf = cv2.copyMakeBorder(confidence, half, half, half, half, cv2.BORDER_CONSTANT, value=0)

    while np.any(padded_conf[half:h + half, half:w + half] == 0):
        # Detect the front of the region to be filled
        front = cv2.Canny((1 - padded_conf).astype(np.uint8) * 255, 100, 200)
        ys, xs = np.where(front > 0)

        best_priority = -1
        best_patch_center = None

        # Find the patch with the highest priority
        for y, x in zip(ys, xs):
            patch_conf = padded_conf[y:y + patch_size, x:x + patch_size]
            patch_c = np.sum(patch_conf) / (patch_size ** 2)
            if patch_c > best_priority:
                best_priority = patch_c
                best_patch_center = (y, x)

        if best_patch_center is None:
            break

        y, x = best_patch_center
        target_patch = padded_img[y:y + patch_size, x:x + patch_size]
        target_mask = padded_conf[y:y + patch_size, x:x + patch_size] > 0

        # Find the best matching patch from the source image
        best_patch = find_best_patch_quadrant_optimized(
            target_patch, target_mask, padded_img, padded_conf,
            patch_size=patch_size, stride=stride, region='bottom-left'
        )

        if best_patch is not None:
            unknown_mask = ~target_mask
            padded_img[y:y + patch_size, x:x + patch_size][unknown_mask] = best_patch[unknown_mask]
            padded_conf[y:y + patch_size, x:x + patch_size][unknown_mask] = 1
        else:
            break  # No valid patch found

    return padded_img[half:-half, half:-half]

def laplacian_sharpening(img, alpha=0.5):
    """
    Enhances image sharpness using Laplacian edge detection.

    Args:
        img (numpy.ndarray): Input image (BGR format).
        alpha (float): Scaling factor for edge enhancement (default=0.5).

    Returns:
        numpy.ndarray: Sharpened image.
    """
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Apply Laplacian filter to detect edges
    laplacian = cv2.Laplacian(gray, cv2.CV_64F, ksize=3)

    # Convert back to uint8 format
    laplacian = np.uint8(np.abs(laplacian))

    # Convert grayscale Laplacian back to 3-channel image
    laplacian_color = cv2.cvtColor(laplacian, cv2.COLOR_GRAY2BGR)

    # Sharpen the image by adding the Laplacian (scaled by alpha)
    sharpened = cv2.addWeighted(img, 1.0, laplacian_color, -alpha, 0)

    return sharpened

def edge_preserving_filter(img, sigma_s=60, sigma_r=0.4):
    """
    Applies an edge-preserving filter to an image.

    Args:
        img (numpy.ndarray): Input image.
        sigma_s (float): Spatial smoothing parameter (default=60).
        sigma_r (float): Color smoothing parameter (default=0.4).

    Returns:
        numpy.ndarray: Filtered image.
    """
    # Apply edge-preserving filter using OpenCV
    filtered_img = cv2.edgePreservingFilter(img, sigma_s=sigma_s, sigma_r=sigma_r, flags=cv2.RECURS_FILTER)
    return filtered_img

def correct_warp(img):
    """
    Corrects perspective distortion in the image.

    Args:
        img (numpy.ndarray): Input image.

    Returns:
        numpy.ndarray: Image with corrected perspective.
    """
    h, w = img.shape[:2]

    # Rotation
    center = (w // 2, h // 2)
    rotation_matrix = cv2.getRotationMatrix2D(center, -5.5, 1.0)
    img = cv2.warpAffine(img, rotation_matrix, (w, h))

    # Perspective transformation
    src_pts = np.float32([[20, 30], [w - 20, 30], [20, h - 20], [w - 20, h - 20]])
    dst_pts = np.float32([[0, 0], [w, 0], [0, h], [w, h]])
    matrix = cv2.getPerspectiveTransform(src_pts, dst_pts)
    
    return cv2.warpPerspective(img, matrix, (w, h))

def adaptive_brightness(image):
    """
    Dynamically adjust brightness using gamma correction and CLAHE for better clarity.

    Args:
        image (numpy.ndarray): Input image in BGR format.

    Returns:
        numpy.ndarray: Image with adjusted brightness.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    mean_brightness = np.mean(gray)

    # Apply CLAHE only on dark images to boost local contrast
    if mean_brightness < 90:  # Dark image, likely rain
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)

        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l = clahe.apply(l)

        lab = cv2.merge((l, a, b))
        image = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

    # Gamma Correction
    if mean_brightness > 120:  # Too bright (snow)
        gamma = 1.4  # Reduce brightness slightly
    elif mean_brightness < 50:  # Too dark (rain)
        gamma = 0.75  # Increase brightness slightly
    else:
        gamma = 1.0  # Keep as is

    # Apply Gamma Correction
    look_up_table = np.array([((i / 255.0) ** (1.0 / gamma)) * 255 for i in range(256)]).astype("uint8")
    return cv2.LUT(image, look_up_table)

def boost_saturation(img, saturation_scale=1.5):
    """
    Boosts the color saturation of an image.

    Args:
        img (numpy.ndarray): Input image (BGR format).
        saturation_scale (float): Scale factor for boosting saturation (default=1.5).

    Returns:
        numpy.ndarray: Image with boosted saturation.
    """
    # Convert to HSV color space
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # Scale the saturation channel
    hsv[:, :, 1] = np.clip(hsv[:, :, 1] * saturation_scale, 0, 255)
    
    # Convert back to BGR color space
    boosted_img = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
    
    return boosted_img

def sharpen_img(img):
    """
    Sharpens the image using Laplacian filter.

    Args:
        img (numpy.ndarray): Input image.

    Returns:
        numpy.ndarray: Sharpened image.
    """
    # Apply Laplacian filter to detect edges
    laplacian = cv2.Laplacian(img, cv2.CV_64F)

    # Scale factor for sharpening
    # Determines the intensity of the sharpening effect
    # Higher value = more sharpening, lower value = less sharpening
    scale_factor = 0.7

    # Sharpen the image by subtracting the scaled Laplacian from the original
    sharpened = cv2.convertScaleAbs(img - scale_factor * laplacian)

    return sharpened

def bilateral_filter(img, d=15, sigmaColor=50, sigmaSpace=50):
    """
    Applies bilateral filtering to an image.

    Args:
        img (numpy.ndarray): Input image.
        d (int): Diameter of each pixel neighborhood (default=9).
        sigmaColor (float): Filter sigma in the color space (default=75).
        sigmaSpace (float): Filter sigma in the coordinate space (default=75).
        
        sigmaColor
        Effect of Increasing: When sigmaColor is increased, the filter will consider a larger color range,
        leading to more smoothing and less edge preservation.
        Effect of Decreasing: When sigmaColor is decreased, the filter will consider a smaller color range,
        resulting in less smoothing and more edge preservation
        
        sigmaSpace
        Effect of Increasing: When sigmaSpace is increased, the filter will consider a larger neighborhood 
        of pixels, leading to more extensive smoothing over a larger area.
        Effect of Decreasing: When sigmaSpace is decreased, the filter will consider a smaller neighborhood,
        resulting in less smoothing and more localized filtering.
        
        High sigmaColor and sigmaSpace: More smoothing, less edge preservation.
        Low sigmaColor and sigmaSpace: Less smoothing, better edge preservation.

    Returns:
        numpy.ndarray: Bilaterally filtered image.
    """
    filtered_img = cv2.bilateralFilter(img, d, sigmaColor, sigmaSpace)
    return filtered_img

def normalize_color_channel(img):
    """
    Normalizes the color channels of an image.

    Args:
        img (numpy.ndarray): Input image.

    Returns:
        numpy.ndarray: Image with normalized color channels.
    """
    img = img.astype(np.float32)
    for i in range(3):  # Iterate over each color channel
        channel = img[:, :, i]
        channel = (channel - np.min(channel)) / (np.max(channel) - np.min(channel)) * 255
        img[:, :, i] = channel
    return img.astype(np.uint8)

def box_filter(img, ksize=5):
    """
    Applies a box filter to an image.

    Args:
        img (numpy.ndarray): Input image.
        ksize (int): Size of the kernel (default=5).

    Returns:
        numpy.ndarray: Box filtered image.
    """
    filtered_img = cv2.boxFilter(img, -1, (ksize, ksize))
    return filtered_img

def butterworth_highpass_filter(shape, cutoff, order=2):
    """
    Create a Butterworth High-Pass Filter (HPF) mask.

    Args:
        shape (tuple): Shape of the image (height, width).
        cutoff (int): Cutoff frequency for the filter.
        order (int): Order of the filter (default=2).

    Returns:
        numpy.ndarray: Butterworth High-Pass Filter mask.
    """
    rows, cols = shape[:2]
    u = np.arange(rows) - rows // 2
    v = np.arange(cols) - cols // 2
    U, V = np.meshgrid(v, u)

    # Compute distance from center
    D = np.sqrt(U**2 + V**2)

    # Butterworth high-pass filter formula
    H = 1 / (1 + (cutoff / (D + 1e-5)) ** (2 * order))  # Avoid division by zero
    return np.fft.ifftshift(H)  # Shift filter to center

def adaptive_gamma_correction(image, gamma=0.8):
    """
    Apply gamma correction to reduce over-brightening.
    Gamma < 1 darkens the image, Gamma > 1 brightens.
    """
    look_up_table = np.array([((i / 255.0) ** gamma) * 255 for i in range(256)]).astype("uint8")
    return cv2.LUT(image, look_up_table)

def sharpen_with_butterworth_hpf(image, cutoff=30, order=2, alpha=1.2, gamma=0.5):
    """
    Apply Butterworth HPF for sharpening without excessive brightness.

    Parameters:
    - image: Input image (BGR).
    - cutoff: Cutoff frequency (higher = more details preserved).
    - order: Filter order (higher = sharper transition).
    - alpha: Sharpening intensity.
    - gamma: Gamma correction factor to avoid over-brightening.

    Returns:
    - Sharpened image with controlled brightness.
    """
    # Convert to YCrCb color space (Y = luminance, Cr & Cb = color)
    ycrcb = cv2.cvtColor(image, cv2.COLOR_BGR2YCrCb)
    Y, Cr, Cb = cv2.split(ycrcb)  # Extract luminance and color channels

    # Compute DFT for luminance channel
    dft = np.fft.fft2(Y)
    dft_shift = np.fft.fftshift(dft)  # Shift zero frequency to center

    # Create Butterworth HPF
    H = butterworth_highpass_filter(Y.shape, cutoff, order)

    # Apply filter in frequency domain
    filtered_dft = dft_shift * H

    # Inverse FFT to get back to spatial domain
    dft_inverse = np.fft.ifftshift(filtered_dft)
    filtered_Y = np.abs(np.fft.ifft2(dft_inverse))

    # Normalize filtered luminance to avoid brightness overflow
    filtered_Y = cv2.normalize(filtered_Y, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

    # Adjusted sharpening: Add HPF result with controlled weight
    #sharpened_Y = cv2.addWeighted(Y, 1 + alpha, filtered_Y, -alpha, 0)

    # Apply Adaptive Gamma Correction to control brightness
    #corrected_Y = adaptive_gamma_correction(sharpened_Y, gamma=gamma)

    # Merge back with original color channels
    sharpened_ycrcb = cv2.merge((filtered_Y, Cr, Cb))
    sharpened_bgr = cv2.cvtColor(sharpened_ycrcb, cv2.COLOR_YCrCb2BGR)  # Convert back to BGR

    return sharpened_bgr

def butterworth_lowpass_filter(shape, cutoff, order=2):
    """
    Create a Butterworth Low-Pass Filter (BLPF) mask.
    
    Parameters:
    - shape: Tuple, image shape (height, width).
    - cutoff: Int, cutoff frequency (higher preserves more details).
    - order: Int, filter order (higher = sharper transition).

    Returns:
    - Butterworth Low-Pass Filter mask.
    """
    rows, cols = shape[:2]
    u = np.arange(rows) - rows // 2
    v = np.arange(cols) - cols // 2
    U, V = np.meshgrid(v, u)

    # Compute distance from center
    D = np.sqrt(U**2 + V**2)

    # Butterworth low-pass filter formula
    H = 1 / (1 + (D / (cutoff + 1e-5)) ** (2 * order))  # Avoid division by zero
    return np.fft.ifftshift(H)  # Shift filter to center

def denoise_color_image_with_butterworth(image, cutoff=30, order=2):
    """
    Denoise a color image using Butterworth Low-Pass Filtering (BLPF) on the luminance channel.

    Parameters:
    - image: Input color image (BGR format).
    - cutoff: Cutoff frequency (higher = more details preserved).
    - order: Filter order (higher = sharper transition).

    Returns:
    - Denoised color image.
    """
    # Convert to YCrCb color space (Y = luminance, Cr & Cb = color)
    ycrcb = cv2.cvtColor(image, cv2.COLOR_BGR2YCrCb)
    Y, Cr, Cb = cv2.split(ycrcb)  # Extract luminance and color channels

    # Compute DFT for luminance channel
    dft = np.fft.fft2(Y)
    dft_shift = np.fft.fftshift(dft)  # Shift zero frequency to center

    # Create Butterworth LPF
    H = butterworth_lowpass_filter(Y.shape, cutoff, order)

    # Apply filter in frequency domain
    filtered_dft = dft_shift * H

    # Inverse FFT to get back to spatial domain
    dft_inverse = np.fft.ifftshift(filtered_dft)
    filtered_Y = np.abs(np.fft.ifft2(dft_inverse))

    # Normalize filtered luminance
    filtered_Y = cv2.normalize(filtered_Y, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

    # Merge denoised luminance back with original color channels
    denoised_ycrcb = cv2.merge((filtered_Y, Cr, Cb))
    denoised_bgr = cv2.cvtColor(denoised_ycrcb, cv2.COLOR_YCrCb2BGR)  # Convert back to BGR

    return denoised_bgr

def butterworth_bandpass_filter(shape, low_cutoff, high_cutoff, order=2):
    """
    Creates a Butterworth Bandpass Filter mask.

    Parameters:
        shape: Tuple, image shape (height, width).
        low_cutoff: Lower frequency cutoff.
        high_cutoff: Upper frequency cutoff.
        order: Butterworth filter order.

    Returns:
        Bandpass filter mask.
    """
    rows, cols = shape[:2]
    u = np.arange(rows) - rows // 2
    v = np.arange(cols) - cols // 2
    U, V = np.meshgrid(v, u)

    # Compute distance from center
    D = np.sqrt(U**2 + V**2)

    # Butterworth Low-Pass Filter
    H_low = 1 / (1 + (D / (high_cutoff + 1e-5)) ** (2 * order))

    # Butterworth High-Pass Filter
    H_high = 1 / (1 + (low_cutoff / (D + 1e-5)) ** (2 * order))

    # Bandpass filter = high-pass * low-pass
    H_bandpass = H_high * H_low
    
    return np.fft.ifftshift(H_bandpass)  # Shift back to original position

def analyze_image_frequency(img):
    """
    Analyzes the image frequency spectrum to determine optimal bandpass filter settings.
    
    Parameters:
        img: Input grayscale image.

    Returns:
        low_cutoff, high_cutoff, order: Optimized filter parameters.
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Compute DFT and shift to center
    dft = np.fft.fft2(gray)
    dft_shift = np.fft.fftshift(dft)
    
    # Compute magnitude spectrum
    magnitude_spectrum = np.log1p(np.abs(dft_shift))
    
    # Compute mean and standard deviation of frequency components
    mean_freq = np.mean(magnitude_spectrum)
    std_freq = np.std(magnitude_spectrum)

    # Determine optimal filter settings based on frequency spread
    low_cutoff = max(5, int(mean_freq - std_freq))  # Avoid negative or zero values
    high_cutoff = min(100, int(mean_freq + std_freq))  # Ensure it stays within range
    order = 2 if std_freq < 20 else 4  # Higher order if higher frequency variation

    return low_cutoff, high_cutoff, order

def apply_adaptive_bandpass_filter(img):
    """
    Applies an adaptive bandpass filter based on image frequency analysis.

    Parameters:
        img: Input color image (BGR format).

    Returns:
        Processed color image with adaptive bandpass filtering applied.
    """
    # Convert to YCrCb color space to apply filtering only on luminance
    ycrcb = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
    Y, Cr, Cb = cv2.split(ycrcb)

    # Determine optimized filter parameters
    low_cutoff, high_cutoff, order = analyze_image_frequency(img)

    # Convert Y channel to frequency domain
    dft = np.fft.fft2(Y)
    dft_shift = np.fft.fftshift(dft)

    # Apply optimized bandpass filter
    H_bandpass = butterworth_bandpass_filter(Y.shape, low_cutoff, high_cutoff, order)
    filtered_dft = dft_shift * H_bandpass

    # Convert back to spatial domain
    dft_inverse = np.fft.ifftshift(filtered_dft)
    filtered_Y = np.abs(np.fft.ifft2(dft_inverse))

    # Normalize filtered luminance
    filtered_Y = cv2.normalize(filtered_Y, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

    # Merge back with color channels
    filtered_ycrcb = cv2.merge((filtered_Y, Cr, Cb))
    filtered_bgr = cv2.cvtColor(filtered_ycrcb, cv2.COLOR_YCrCb2BGR)

    return filtered_bgr

def sadct_deblur_color(img, block_size, alpha):
    """
    Applies Spatially Adaptive Discrete Cosine Transform (SADCT) for deblurring
    on each color channel independently to preserve color.

    Args:
        img (numpy.ndarray): Input blurred color image (BGR format).
        block_size (int): Size of the DCT blocks (default=8).
        alpha (float): Strength of high-frequency amplification (default=0.1).

    Returns:
        numpy.ndarray: Deblurred color image.
    """
    h, w, c = img.shape
    output = np.zeros_like(img, dtype=np.float32)

    for ch in range(c):
        channel = img[:, :, ch].astype(np.float32)

        for i in range(0, h, block_size):
            for j in range(0, w, block_size):
                block = channel[i:i+block_size, j:j+block_size]

                if block.shape[0] != block_size or block.shape[1] != block_size:
                    continue  # skip incomplete blocks at edges

                dct_block = cv2.dct(block)
                dct_block[1:, 1:] *= (1 + alpha)
                idct_block = cv2.idct(dct_block)

                output[i:i+block_size, j:j+block_size, ch] = idct_block

    # Clip and convert back to uint8
    output = np.clip(output, 0, 255).astype(np.uint8)
    return output

def correct_color_imbalance_fixed(img):
    """
    Fixes color imbalance using LAB color space without excessive distortion.

    Args:
        img (numpy.ndarray): Input BGR image.

    Returns:
        numpy.ndarray: Corrected BGR image with balanced colors.
    """
    # Convert to LAB color space
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    L, A, B = cv2.split(lab)

    # Apply CLAHE to L-channel to correct brightness
    #clahe = cv2.createCLAHE(clipLimit=1.5, tileGridSize=(8, 8))
    #L = clahe.apply(L)

    # Normalize A and B channels to avoid overcorrection
    mean_A, mean_B = np.mean(A), np.mean(B)
    A = np.clip(A - (mean_A - 128), 0, 255).astype(np.uint8)
    B = np.clip(B - (mean_B - 128), 0, 255).astype(np.uint8)

    # Merge back and convert to BGR
    corrected_lab = cv2.merge([L, A, B])
    corrected = cv2.cvtColor(corrected_lab, cv2.COLOR_LAB2BGR)

    return corrected

def correct_color_imbalance_hsv(img):
    """
    Corrects color imbalance in an image using HSV color space.
    Boosts or normalizes saturation to reduce color cast.

    Args:
        img (np.ndarray): Input BGR image.

    Returns:
        np.ndarray: Color-balanced BGR image.
    """
    # Convert BGR to HSV
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    H, S, V = cv2.split(hsv)

    # Analyze saturation distribution
    mean_saturation = np.mean(S)
    
    # Heuristic: normalize saturation if it's too low or too high
    if mean_saturation < 60:
        # Low saturation → boost it to remove grayness (often snow)
        S = np.clip(S * 1.5, 0, 255).astype(np.uint8)
    elif mean_saturation > 180:
        # Oversaturated (e.g., due to color cast) → reduce it
        S = np.clip(S * 0.7, 0, 255).astype(np.uint8)
    # else: keep S as-is

    # Merge and convert back
    hsv_balanced = cv2.merge([H, S, V])
    balanced_bgr = cv2.cvtColor(hsv_balanced, cv2.COLOR_HSV2BGR)

    return balanced_bgr

def analyze_colorfulness(img):
    """
    Analyzes the colorfulness of an image based on mean saturation and vibrancy.

    Parameters:
        img: Input color image (BGR format).

    Returns:
        color_level: Estimated colorfulness level (low, normal, high).
    """
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    saturation_mean = np.mean(hsv[:, :, 1])  # Mean saturation

    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    a_mean = np.mean(lab[:, :, 1])
    b_mean = np.mean(lab[:, :, 2])
    vibrancy = np.sqrt(a_mean**2 + b_mean**2)  # Measure color intensity

    if saturation_mean < 50 and vibrancy < 50:
        return "low"
    elif saturation_mean > 150 and vibrancy > 150:
        return "high"
    else:
        return "normal"

def adaptive_color_enhancement(img):
    """
    Enhances colors adaptively by adjusting saturation and vibrancy based on image analysis.

    Parameters:
        img: Input color image (BGR format).

    Returns:
        Adjusted image with optimized color richness.
    """
    color_level = analyze_colorfulness(img)

    if color_level == "low":
        # Boost saturation and vibrancy significantly
        saturation_scale = 1.8
        vibrancy_factor = 1.3
    elif color_level == "high":
        # Reduce excessive saturation and vibrancy
        saturation_scale = 0.8
        vibrancy_factor = 0.9
    else:
        return img  # No change for normal colorfulness

    # Convert to HSV and scale saturation
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    hsv[:, :, 1] = np.clip(hsv[:, :, 1] * saturation_scale, 0, 255)
    img = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

    # Convert to LAB and scale color vibrancy
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    a = np.clip(a * vibrancy_factor, 0, 255).astype(np.uint8)
    b = np.clip(b * vibrancy_factor, 0, 255).astype(np.uint8)
    img = cv2.merge((l, a, b))
    img = cv2.cvtColor(img, cv2.COLOR_LAB2BGR)

    return img

def analyze_contrast(img):
    """
    Analyzes the contrast level of an image based on standard deviation of pixel intensities.

    Parameters:
        img: Input color image (BGR format).

    Returns:
        contrast_level: Estimated contrast level (low, normal, high).
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    contrast = np.std(gray)  # Standard deviation of pixel intensities

    if contrast < 40:
        return "low"
    elif contrast > 100:
        return "high"
    else:
        return "normal"

def adaptive_contrast(img):
    """
    Adjusts contrast adaptively based on contrast analysis.

    Parameters:
        img: Input color image (BGR format).

    Returns:
        Adjusted image.
    """
    contrast_level = analyze_contrast(img)

    if contrast_level == "low":
        # Increase contrast using CLAHE (Adaptive Histogram Equalization)
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)  # Convert to LAB color space
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=1.3, tileGridSize=(8,8))
        l = clahe.apply(l)
        img = cv2.merge((l, a, b))
        adjusted_img = cv2.cvtColor(img, cv2.COLOR_LAB2BGR)  # Convert back to BGR

    elif contrast_level == "high":
        
        # Increase contrast using CLAHE (Adaptive Histogram Equalization)
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)  # Convert to LAB color space
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=0.7, tileGridSize=(8,8))
        l = clahe.apply(l)
        img = cv2.merge((l, a, b))
        adjusted_img = cv2.cvtColor(img, cv2.COLOR_LAB2BGR)  # Convert back to BGR

    else:
        return img  # No change for normal contrast

    return adjusted_img

def adaptive_denoise_image(img): 
    """
    Apply adaptive denoising to an image based on its noise level.
    The function converts the input image to grayscale and calculates the noise level.
    Depending on the noise level, it selects appropriate parameters for the denoising
    algorithm and applies it to the image.
    Parameters:
    img (numpy.ndarray): Input image in BGR format.
    Returns:
    numpy.ndarray: Denoised image in BGR format.
    Notes:
    - The noise level is determined using the standard deviation of the grayscale image.
    - Different parameter sets are used for different noise levels to achieve optimal denoising.
    - The function uses OpenCV's fastNlMeansDenoisingColored for denoising.
    """
    # 6.5 = 96 percent
    # 8.5 = 96 percent
    # 8.5, 10 = 96 percent
    # 8.5, 12 = 96 percent
    # 8.5, 13 = 96 percent
    # 8.5, 15 = 95 percent
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    noise_level = cv2.meanStdDev(gray)[1][0]
    if noise_level > 70:
        params = {'h': 8.5, 'hColor': 12}
    elif noise_level > 50:
        params = {'h': 4, 'hColor': 4}
    elif noise_level > 30:
        params = {'h': 2, 'hColor': 2}
    else:
        params = {'h': 1, 'hColor': 1}
    return cv2.fastNlMeansDenoisingColored(img, None, params['h'], params['hColor'], 7, 21)

def adaptive_brightness(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    brightness = np.mean(gray)
    if brightness < 50:
        gamma = 2.0
    elif brightness < 100:
        gamma = 1.5
    elif brightness < 150:
        gamma = 1.2
    else:
        gamma = 1.0
    look_up_table = np.array([((i / 255.0) ** (1.0 / gamma)) * 255 for i in range(256)]).astype("uint8")
    return cv2.LUT(image, look_up_table)

def adaptive_contrast(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    contrast = np.std(gray)
    if contrast < 40:
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=1.3, tileGridSize=(8,8))
        l = clahe.apply(l)
        img = cv2.merge((l, a, b))
        adjusted_img = cv2.cvtColor(img, cv2.COLOR_LAB2BGR)
    elif contrast > 100:
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=0.7, tileGridSize=(8,8))
        l = clahe.apply(l)
        img = cv2.merge((l, a, b))
        adjusted_img = cv2.cvtColor(img, cv2.COLOR_LAB2BGR)
    else:
        return img
    return adjusted_img

def adaptive_saturation(img):
    """Adjusts the saturation of the image adaptively."""
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    avg_saturation = np.mean(hsv[:, :, 1])
    if avg_saturation < 50:
        saturation_scale = 1.5
    else:
        saturation_scale = 1.2
    hsv[:, :, 1] = np.clip(hsv[:, :, 1] * saturation_scale, 0, 255)
    return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

def process_image(img, dir): 
    """Processes a single image by applying various transformations and saves the result."""
    org_img = read_img(img)
    img = read_img(img)
    img = inpaint_black_circle(img)
    img = remove_salt_pepper_noise(img, kernel_size=3)
    img = adaptive_denoise_image(img)
    img = sadct_deblur_color(img, block_size=8, alpha=0.3)
    #img = adaptive_brightness(img)
    #img = adaptive_contrast(img)
    #img = adaptive_color_enhancement(img)
    img = sharpen_img(img)
    img = adaptive_saturation(img)
    img = correct_warp(img)
    cv2.imwrite(dir, img)

def process_directory(input_dir):
    """Processes all images in a directory."""
    if not os.path.exists("Results"):
        os.makedirs("Results")
    
    for filename in os.listdir(input_dir):
        if filename.endswith(".jpg"):
            input_path = os.path.join(input_dir, filename)
            output_path = os.path.join("Results", filename)
            process_image(input_path, output_path)

def main(): 
    """Main function to parse arguments and process the directory."""
    # example usage: python main.py ./driving_images ./outputdir
    parser = argparse.ArgumentParser()
    parser.add_argument("input_dir", help="Directory containing input images")
    #parser.add_argument("output_dir", help="Directory to save processed images")
    args = parser.parse_args()
    process_directory(args.input_dir)

if __name__=="__main__": 
    main()
    #print(cv2.__version__)