"""
Unified and Improved EKG Image Processing Module (V3)
File: unified_image_processing.py

This version implements a signal enhancement pipeline, focusing on making the EKG trace
dominant before binarization, rather than aggressively removing the grid.

Core Pipeline (V3):
1.  Preprocessing: Grayscale conversion.
2.  Signal Enhancement: Apply Contrast Limited Adaptive Histogram Equalization (CLAHE)
    to make the dark EKG trace stand out.
3.  Edge-Preserving Denoising: Use a Bilateral Filter to reduce noise while keeping
    the sharp edges of the EKG signal intact.
4.  Optimized Binarization: Apply adaptive thresholding on the enhanced image.
5.  Morphological Operations: Final cleaning of the binary image.
6.  Signal Extraction & Post-processing: Use the proven full-width scan and final filtering.
"""
import cv2
import numpy as np
from scipy import signal as scipy_signal
from scipy.ndimage import gaussian_filter1d
import base64
import io
import matplotlib.pyplot as plt

def unified_process_ekg_image(image_data, return_steps=False):
    """
    The main unified function to process an EKG image (V3 Signal Enhancement Pipeline).
    """
    processing_steps = {}

    try:
        # 1. Decode Image
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        image_bytes = base64.b64decode(image_data)
        nparr = np.frombuffer(image_bytes, np.uint8)
        img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img_bgr is None: return {"error": "Failed to decode image."}
        
        img_gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        if return_steps: processing_steps['step_1_grayscale'] = _to_base64(img_gray, "1. Grayscale")

        # 2. Signal Enhancement (CLAHE)
        # This makes the EKG signal much more prominent.
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced_img = clahe.apply(img_gray)
        if return_steps: processing_steps['step_2_enhanced_contrast'] = _to_base64(enhanced_img, "2. Contrast Enhanced (CLAHE)")

        # 3. Edge-Preserving Denoising (Bilateral Filter)
        # This smooths the image but keeps the EKG's sharp edges.
        denoised_img = cv2.bilateralFilter(enhanced_img, d=9, sigmaColor=75, sigmaSpace=75)
        if return_steps: processing_steps['step_3_denoised'] = _to_base64(denoised_img, "3. Denoised (Bilateral)")

        # 4. Optimized Binarization
        # Thresholding on the enhanced image is much more effective.
        binary_img = cv2.adaptiveThreshold(
            denoised_img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV, 25, 10 # Adjusted parameters for high contrast image
        )
        if return_steps: processing_steps['step_4_binarized'] = _to_base64(binary_img, "4. Binarized")

        # 5. Morphological Cleaning
        # A small closing operation to fill minor gaps in the trace.
        kernel = np.ones((2, 2), np.uint8)
        cleaned_img = cv2.morphologyEx(binary_img, cv2.MORPH_CLOSE, kernel)
        if return_steps: processing_steps['step_5_cleaned'] = _to_base64(cleaned_img, "5. Morphologically Cleaned")

        # 6. Full-Width Signal Extraction
        extracted_signal = extract_signal_full_width_scan(cleaned_img)
        if extracted_signal is None or len(extracted_signal) < img_gray.shape[1] * 0.5:
             return {"error": "Signal extraction failed. Not enough signal points found."}
        if return_steps: processing_steps['step_6_raw_extraction'] = _plot_to_base64(extracted_signal, "6. Raw Extracted Signal")

        # 7. Signal Post-Processing
        processed_signal = post_process_signal(extracted_signal)
        if return_steps: processing_steps['step_7_processed_signal'] = _plot_to_base64(processed_signal, "7. Final Processed Signal")

        # Final result
        result = {
            "success": True,
            "signal": processed_signal.tolist(),
            "signal_length": len(processed_signal),
            "processing_method": "unified_clahe_bilateral_v3",
            "image_shape": img_gray.shape
        }
        if return_steps: result["processing_steps"] = processing_steps

        return result

    except Exception as e:
        import traceback
        return {"error": f"An unexpected error occurred: {str(e)}", "trace": traceback.format_exc()}

def extract_signal_full_width_scan(binary_img):
    """
    Scans the entire width of the binary image to extract the EKG signal.
    """
    height, width = binary_img.shape
    signal = []
    
    for x in range(width):
        column = binary_img[:, x]
        white_pixels = np.where(column == 255)[0]
        
        if len(white_pixels) > 0:
            # Use the median of the largest contour of white pixels to be robust against noise
            groups = np.split(white_pixels, np.where(np.diff(white_pixels) != 1)[0] + 1)
            largest_group = max(groups, key=len)
            avg_y = np.median(largest_group)
            signal_value = height - avg_y
            signal.append(signal_value)
        else:
            # Simple but effective interpolation for missing points
            if len(signal) >= 1:
                signal.append(signal[-1]) # Repeat last valid point
            else:
                signal.append(height / 2) # Default to center if no signal found yet
                
    return np.array(signal)

def post_process_signal(signal, fs=250):
    """
    Applies smoothing, filtering, and normalization to the raw extracted signal.
    """
    # Ensure signal is valid for processing
    if signal is None or len(signal) < 10 or not np.all(np.isfinite(signal)):
        return np.array([])

    # Only process if there is variation in the signal
    if np.std(signal) > 1e-6:
        # 1. Smoothing with a Savitzky-Golay filter, which is excellent for preserving peak shapes
        window_length = min(11, len(signal) // 2 * 2 - 1) # Must be odd and smaller than signal
        if window_length < 3:
             window_length = 3
        smoothed_signal = scipy_signal.savgol_filter(signal, window_length, 2) # polyorder 2

        # 2. Baseline Wander Removal using a bandpass filter
        nyquist = 0.5 * fs
        low = 0.5 / nyquist
        high = 45 / nyquist # Increased high freq to 45Hz
        b, a = scipy_signal.butter(2, [low, high], btype='band')
        filtered_signal = scipy_signal.filtfilt(b, a, smoothed_signal)
        
        # 3. Normalization (Z-score)
        final_signal = (filtered_signal - np.mean(filtered_signal)) / np.std(filtered_signal)
        return final_signal
    else:
        # If signal is constant, just return a zero-mean version
        return signal - np.mean(signal)

# Helper functions for visualization
def _to_base64(img, title=""):
    """Converts an OpenCV image to a base64 string with an optional title."""
    # Convert to BGR if it's grayscale for consistent color titles
    if len(img.shape) == 2:
        img_color = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    else:
        img_color = img

    if title:
        # Add a white border at the top for the title text
        img_with_title = cv2.copyMakeBorder(img_color, 30, 10, 10, 10, cv2.BORDER_CONSTANT, value=[255,255,255])
        # Put the title text
        cv2.putText(img_with_title, title, (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,0), 2)
    else:
        img_with_title = img_color

    _, buffer = cv2.imencode('.png', img_with_title)
    return f"data:image/png;base64,{base64.b64encode(buffer).decode('utf-8')}"

def _plot_to_base64(signal, title):
    """Plots a 1D signal and returns it as a base64 string."""
    fig, ax = plt.subplots(figsize=(10, 3))
    ax.plot(signal)
    ax.set_title(title)
    ax.grid(True)
    
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    
    return f"data:image/png;base64,{base64.b64encode(buf.read()).decode('utf-8')}"
