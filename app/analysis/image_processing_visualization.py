import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import cv2
import io
import base64
from scipy import signal
from PIL import Image

# Importujemo funkciju za kreiranje slike iz drugog modula
from .signal_to_image import create_ekg_image_from_signal

def visualize_complete_image_processing(image_data, show_intermediate_steps=True):
    try:
        if isinstance(image_data, str):
            if image_data.startswith('data:image'):
                image_data = image_data.split(',')[1]
            image_bytes = base64.b64decode(image_data)
        else:
            image_bytes = image_data
        
        image_array = np.frombuffer(image_bytes, dtype=np.uint8)
        original_image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        
        if original_image is None: return {"error": "Nije moguće dekodovati sliku"}
        
        # Glavna funkcija sada radi ceo round-trip i vraća sve korake
        processing_steps = process_image_step_by_step_with_roundtrip(original_image)
        
        if "error" in processing_steps: return {"error": processing_steps["error"]}

        visualization = create_step_by_step_visualization(processing_steps)
        
        return {
            "success": True,
            "processing_steps": processing_steps,
            "visualization": visualization,
            "extracted_signal": processing_steps.get("final_signal", []),
            "metadata": processing_steps.get("metadata", {})
        }
        
    except Exception as e:
        import traceback
        return {"error": f"Greška u obradi slike: {str(e)}", "trace": traceback.format_exc()}

def process_image_step_by_step_with_roundtrip(original_image):
    results = process_image_step_by_step(original_image)
    if "error" in results: return results

    signal_A = results.get("step_10_filtered")
    if signal_A is None or len(signal_A) == 0: return results

    try:
        fs = 250
        reconstructed_image_data = create_ekg_image_from_signal(signal_A, fs=fs, style="clinical")
        image_B = reconstructed_image_data['image_opencv']
        results["step_11_reconstructed_image"] = image_B

        results_B = process_image_step_by_step(image_B)
        if "error" in results_B: 
            results["step_12_signal_B"] = []
        else:
            signal_B = results_B.get("step_10_filtered", [])
            results["step_12_signal_B"] = signal_B

    except Exception as e:
        results["roundtrip_error"] = str(e)
        results["step_11_reconstructed_image"] = None
        results["step_12_signal_B"] = []

    return results

def process_image_step_by_step(original_image):
    results = {"metadata": {}}
    try:
        results["step_1_original"] = original_image.copy()
        gray_image = cv2.cvtColor(original_image, cv2.COLOR_BGR2GRAY)
        results["step_2_grayscale"] = gray_image
        blurred = cv2.GaussianBlur(gray_image, (7, 7), 0)
        results["step_3_blur"] = blurred
        binary = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)
        results["step_4_binary"] = binary
        h_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 1))
        h_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, h_kernel, iterations=1)
        v_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 25))
        v_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, v_kernel, iterations=1)
        grid_mask = h_lines + v_lines
        results["step_5_grid_detected"] = grid_mask
        no_grid = cv2.subtract(binary, grid_mask)
        results["step_6_grid_removed"] = no_grid
        cleanup_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        cleaned = cv2.morphologyEx(no_grid, cv2.MORPH_CLOSE, cleanup_kernel)
        results["step_7_cleaned"] = cleaned
        contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        final_mask = np.zeros_like(gray_image)
        if contours:
            min_area = 30
            valid_contours = [c for c in contours if cv2.contourArea(c) > min_area]
            if valid_contours:
                cv2.drawContours(final_mask, valid_contours, -1, 255, thickness=cv2.FILLED)
        dilate_kernel = np.ones((3,5), np.uint8)
        final_mask = cv2.dilate(final_mask, dilate_kernel, iterations=2)
        results["step_8_main_contour"] = final_mask
        raw_signal = extract_signal_row_wise(final_mask)
        results["step_9_signal_1d"] = raw_signal
        filtered_signal = filter_ekg_signal(raw_signal)
        results["step_10_filtered"] = filtered_signal
        results["final_signal"] = filtered_signal
    except Exception as e:
        results["error"] = str(e)
    return results

def extract_signal_row_wise(binary_image):
    height, width = binary_image.shape
    signal_points = []
    for x in range(width):
        white_pixels = np.where(binary_image[:, x] == 255)[0]
        if len(white_pixels) > 0:
            avg_y = np.median(white_pixels)
            inverted_y = height - avg_y
            signal_points.append(inverted_y)
        else:
            if len(signal_points) > 1:
                signal_points.append(2 * signal_points[-1] - signal_points[-2])
            elif signal_points:
                signal_points.append(signal_points[-1])
            else:
                signal_points.append(height / 2)
    return normalize_signal(signal_points)

def normalize_signal(signal_points):
    if len(signal_points) < 10: return []
    signal_array = np.array(signal_points, dtype=float)
    min_val, max_val = np.min(signal_array), np.max(signal_array)
    if (max_val - min_val) > 0:
        signal_array = 2 * (signal_array - min_val) / (max_val - min_val) - 1
    else:
        signal_array = np.zeros_like(signal_array)
    return signal_array.tolist()

def filter_ekg_signal(signal_1d, fs=250):
    if len(signal_1d) < 100: return signal_1d
    try:
        smoothed = signal.savgol_filter(signal_1d, 11, 3)
        nyquist = fs / 2
        low, high = 0.5 / nyquist, 40 / nyquist
        b, a = signal.butter(4, [low, high], btype='band')
        filtered = signal.filtfilt(b, a, smoothed)
        return filtered.tolist()
    except Exception: return signal_1d

def create_step_by_step_visualization(processing_steps):
    fig = plt.figure(figsize=(20, 16))
    gs = gridspec.GridSpec(4, 3, figure=fig, hspace=0.4, wspace=0.2)
    steps_to_show = [
        ("step_1_original", "1. Original", "bgr"),
        ("step_2_grayscale", "2. Grayscale", "gray"),
        ("step_3_blur", "3. Blurred (7x7)", "gray"),
        ("step_4_binary", "4. Binarizacija", "gray"),
        ("step_5_grid_detected", "5. Detektovan Grid", "gray"),
        ("step_6_grid_removed", "6. Signal bez Grida", "gray"),
        ("step_7_cleaned", "7. Očišćen Signal", "gray"),
        ("step_8_main_contour", "8. Finalna Kontura", "gray"),
        ("step_9_signal_1d", "9. Ekstraktovan Signal (A)", "signal"),
        ("step_10_filtered", "10. Filtriran Signal (A)", "signal"),
        ("step_11_reconstructed_image", "11. Rekonstruisana Slika (B)", "bgr"),
        ("step_12_signal_B", "12. Filtriran Signal (B)", "signal")
    ]
    for i, (step_key, title, plot_type) in enumerate(steps_to_show):
        ax = fig.add_subplot(gs[i // 3, i % 3])
        ax.set_title(title, fontsize=11, fontweight='bold')
        data = processing_steps.get(step_key)
        if data is not None and (isinstance(data, np.ndarray) or (isinstance(data, list) and len(data) > 0)):
            if plot_type == "bgr": ax.imshow(cv2.cvtColor(data, cv2.COLOR_BGR2RGB))
            elif plot_type == "gray": ax.imshow(data, cmap='gray')
            elif plot_type == "signal":
                ax.plot(data, 'b-', linewidth=1)
                ax.grid(True, alpha=0.3)
            ax.axis('off')
        else:
            ax.text(0.5, 0.5, 'Nije dostupno', ha='center', va='center')
            ax.axis('off')
    plt.suptitle('EKG - Full Round-Trip Visualization', fontsize=16, fontweight='bold', y=0.98)
    return _save_plot_as_base64(fig)

def _save_plot_as_base64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='white', edgecolor='none')
    buf.seek(0)
    image_base64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return {
        'image_base64': f"data:image/png;base64,{image_base64}",
        'width': fig.get_figwidth() * fig.dpi,
        'height': fig.get_figheight() * fig.dpi,
        'format': 'PNG'
    }

def create_summary_visualization(p): return create_step_by_step_visualization(p)
def create_comparison_visualization(o, e): return _save_plot_as_base64(plt.figure())
def extract_1d_signal_from_contour(c,s): return []
def extract_signal_adaptive_method(o,b): return [],"",0
def extract_signal_enhanced_rowwise(b): return extract_signal_row_wise(b)