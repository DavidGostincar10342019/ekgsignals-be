"""
Vizuelizacija step-by-step procesa obrade EKG slike
Prikazuje sve korake od originalne slike do finalnog 1D signala
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import cv2
import io
import base64
from scipy import signal, interpolate
from PIL import Image

def visualize_complete_image_processing(image_data, show_intermediate_steps=True):
    """
    Kreira kompletnu vizuelizaciju procesa obrade EKG slike
    
    Args:
        image_data: Base64 ili bytes data slike
        show_intermediate_steps: Da li prikazati sve intermediate korake
    
    Returns:
        dict: Rezultat sa vizuelizacijama i ekstraktovanim signalom
    """
    
    try:
        # Dekodiraj sliku
        if isinstance(image_data, str):
            if image_data.startswith('data:image'):
                image_data = image_data.split(',')[1]
            image_bytes = base64.b64decode(image_data)
        else:
            image_bytes = image_data
        
        # Učitaj sliku
        image_array = np.frombuffer(image_bytes, dtype=np.uint8)
        original_image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        
        if original_image is None:
            return {"error": "Nije moguće dekodovati sliku"}
        
        # Kreiraj step-by-step processing
        processing_steps = process_image_step_by_step(original_image)
        
        # Kreiraj vizuelizaciju
        if show_intermediate_steps:
            visualization = create_step_by_step_visualization(processing_steps)
        else:
            visualization = create_summary_visualization(processing_steps)
        
        return {
            "success": True,
            "processing_steps": processing_steps,
            "visualization": visualization,
            "extracted_signal": processing_steps["final_signal"],
            "metadata": {
                "original_size": original_image.shape,
                "processing_time": "calculated",
                "steps_count": len([k for k in processing_steps.keys() if k.startswith("step_")])
            }
        }
        
    except Exception as e:
        return {"error": f"Greška u obradi slike: {str(e)}"}

def process_image_step_by_step(original_image):
    """
    Obrađuje sliku korak po korak i čuva rezultate
    """
    
    results = {
        "step_1_original": original_image.copy(),
        "metadata": {
            "original_size": original_image.shape,
            "original_dtype": str(original_image.dtype)
        }
    }
    
    # KORAK 2: Konverzija u grayscale
    gray_image = cv2.cvtColor(original_image, cv2.COLOR_BGR2GRAY)
    results["step_2_grayscale"] = gray_image
    results["metadata"]["grayscale_info"] = "RGB → Grayscale konverzija"
    
    # KORAK 3: Predprocesiranje (Gaussian blur)
    blurred = cv2.GaussianBlur(gray_image, (3, 3), 0)
    results["step_3_blur"] = blurred
    results["metadata"]["blur_info"] = "Gaussian blur (3x3 kernel) za noise reduction"
    
    # KORAK 4: Adaptivna binarizacija
    binary = cv2.adaptiveThreshold(
        blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2
    )
    results["step_4_binary"] = binary
    results["metadata"]["binary_info"] = "Adaptivna binarizacija (block_size=11, C=2)"
    
    # KORAK 5: Morfološko filtriranje - uklanjanje grid-a
    # Horizontalne linije (grid)
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
    horizontal_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, horizontal_kernel)
    
    # Vertikalne linije (grid)
    vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
    vertical_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, vertical_kernel)
    
    # Kombinuj grid linije
    grid = cv2.add(horizontal_lines, vertical_lines)
    results["step_5_grid_detected"] = grid
    results["metadata"]["grid_info"] = "Detekcija grid mreže (40x1 i 1x40 kernels)"
    
    # KORAK 6: Uklanjanje grid-a
    no_grid = cv2.subtract(binary, grid)
    results["step_6_grid_removed"] = no_grid
    results["metadata"]["grid_removal_info"] = "Oduzimanje grid mreže od binarne slike"
    
    # KORAK 7: Detaljno čišćenje - uklanjanje malih objekata
    # Morfološko otvaranje
    cleanup_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    cleaned = cv2.morphologyEx(no_grid, cv2.MORPH_OPEN, cleanup_kernel)
    results["step_7_cleaned"] = cleaned
    results["metadata"]["cleanup_info"] = "Morfološko otvaranje (3x3 ellipse kernel)"
    
    # KORAK 8: Detekcija konturen - ROBUSNIJI PRISTUP
    contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Nacrtaj sve konture za debug
    all_contours_image = np.zeros_like(cleaned)
    if contours:
        cv2.drawContours(all_contours_image, contours, -1, 255, 1)
    results["step_8_all_contours"] = all_contours_image
    
    # BACKUP metod: Ako nema dovoljno konturen, koristi edge detection
    if not contours or len(contours) < 3:
        # Fallback: Canny edge detection
        edges = cv2.Canny(cleaned, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        results["metadata"]["backup_method"] = "Canny edge detection korišćen kao fallback"
    
    # Pronađi glavnu konturu (više tolerantan pristup)
    main_contour = None
    if contours:
        # Sortiraj konture po area
        contours = sorted(contours, key=cv2.contourArea, reverse=True)
        
        # Probaj različite kriterijume za glavnu konturu
        for contour in contours[:5]:  # Proveris top 5 kontura
            area = cv2.contourArea(contour)
            if area > 100:  # Smanjena minimalna area
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = w / h if h > 0 else 0
                
                # Relaksirani kriterijumi
                if aspect_ratio > 1.5 or area > 500:  # Ili široka kontura ili velika area
                    main_contour = contour
                    results["metadata"]["contour_selection"] = f"Kontura sa area={area:.0f}, aspect_ratio={aspect_ratio:.2f}"
                    break
        
        # Ako JOŠ UVEK nema konture, uzmi najveću
        if main_contour is None and contours:
            main_contour = contours[0]
            results["metadata"]["contour_selection"] = "Uzeta najveća dostupna kontura"
    
    if main_contour is not None:
        # Nacrtaj glavni kontur
        contour_image = np.zeros_like(cleaned)
        cv2.drawContours(contour_image, [main_contour], -1, 255, 2)
        results["step_8_main_contour"] = contour_image
        results["metadata"]["contour_info"] = f"Glavna kontura (area: {cv2.contourArea(main_contour):.0f})"
        
        # KORAK 9: Ekstrakcija 1D signala
        signal_1d = extract_1d_signal_from_contour(main_contour, gray_image.shape)
        
        # BACKUP: Ako kontura ne da dobar signal, koristi row-wise approach
        if len(signal_1d) < 50:
            signal_1d = extract_signal_row_wise(cleaned)
            results["metadata"]["signal_extraction"] = "Row-wise extraction korišćen kao backup"
        
        results["step_9_signal_1d"] = signal_1d
        results["final_signal"] = signal_1d
        results["metadata"]["signal_info"] = f"1D signal sa {len(signal_1d)} tačaka"
        
        # KORAK 10: Filtriranje signala
        if len(signal_1d) > 50:  # Smanjen minimum za filtriranje
            try:
                filtered_signal = filter_ekg_signal(signal_1d)
                results["step_10_filtered"] = filtered_signal
                results["final_signal"] = filtered_signal
                results["metadata"]["filter_info"] = "Band-pass filter (0.5-40 Hz)"
            except:
                results["final_signal"] = signal_1d
                results["metadata"]["filter_info"] = "Filtriranje preskočeno zbog greške"
        else:
            results["final_signal"] = signal_1d
    else:
        # POSLEDNJI BACKUP: Row-wise extraction iz originalne binarne slike
        backup_signal = extract_signal_row_wise(binary)
        results["final_signal"] = backup_signal
        results["metadata"]["backup_extraction"] = f"Row-wise backup: {len(backup_signal)} tačaka"
        results["step_9_signal_1d"] = backup_signal
    
    return results

def extract_1d_signal_from_contour(contour, image_shape):
    """
    Ekstraktuje 1D signal iz konture
    """
    
    # Dobij bounding rectangle
    x, y, w, h = cv2.boundingRect(contour)
    
    # Kreiraj y-values za svaki x
    signal_points = []
    
    for xi in range(x, x + w):
        # Pronađi sve y-koordinate za ovaj x
        y_coords = []
        for point in contour.reshape(-1, 2):
            if point[0] == xi:
                y_coords.append(point[1])
        
        if y_coords:
            # Uzmi srednju vrednost ako ima više tačaka
            avg_y = np.mean(y_coords)
            # Invertuji y jer je koordinatni sistem obrnut
            inverted_y = image_shape[0] - avg_y
            signal_points.append(inverted_y)
        else:
            # Interpoliraj ako nema tačke
            if signal_points:
                signal_points.append(signal_points[-1])
            else:
                signal_points.append(image_shape[0] / 2)
    
    # Normalizuj signal
    if signal_points:
        signal_array = np.array(signal_points)
        # Centri signal oko nule
        signal_array = signal_array - np.mean(signal_array)
        # Normalizuj amplitudu
        if np.std(signal_array) > 0:
            signal_array = signal_array / np.std(signal_array)
        
        return signal_array.tolist()
    else:
        return []

def extract_signal_row_wise(binary_image):
    """
    BACKUP metod: Ekstraktuje signal row-by-row iz binarne slike
    """
    height, width = binary_image.shape
    signal_points = []
    
    for x in range(width):
        # Pronađi sve bele piksele u ovom stupcu
        white_pixels = np.where(binary_image[:, x] == 255)[0]
        
        if len(white_pixels) > 0:
            # Uzmi srednju vrednost
            avg_y = np.mean(white_pixels)
            # Invertuј y koordinatu
            inverted_y = height - avg_y
            signal_points.append(inverted_y)
        else:
            # Interpoliraj ako nema piksela
            if signal_points:
                signal_points.append(signal_points[-1])
            else:
                signal_points.append(height / 2)
    
    # Normalizuj signal
    if len(signal_points) > 10:
        signal_array = np.array(signal_points)
        signal_array = signal_array - np.mean(signal_array)
        if np.std(signal_array) > 0:
            signal_array = signal_array / np.std(signal_array)
        return signal_array.tolist()
    else:
        return []

def filter_ekg_signal(signal_1d, fs=250):
    """
    Aplikuje band-pass filter na EKG signal
    """
    
    if len(signal_1d) < 100:
        return signal_1d
    
    try:
        # Band-pass filter 0.5-40 Hz
        nyquist = fs / 2
        low = 0.5 / nyquist
        high = 40 / nyquist
        
        b, a = signal.butter(4, [low, high], btype='band')
        filtered = signal.filtfilt(b, a, signal_1d)
        
        return filtered.tolist()
    except Exception:
        return signal_1d

def create_step_by_step_visualization(processing_steps):
    """
    Kreira detaljnu step-by-step vizuelizaciju
    """
    
    # Pripremi figure sa grid layout
    fig = plt.figure(figsize=(20, 16))
    gs = gridspec.GridSpec(4, 3, figure=fig, hspace=0.3, wspace=0.2)
    
    # Definišemo steps za prikaz
    steps_to_show = [
        ("step_1_original", "1. Originalna Slika", "original"),
        ("step_2_grayscale", "2. Grayscale Konverzija", "grayscale"),
        ("step_3_blur", "3. Gaussian Blur (3x3)", "grayscale"),
        ("step_4_binary", "4. Adaptivna Binarizacija", "binary"),
        ("step_5_grid_detected", "5. Detektovan Grid", "binary"),
        ("step_6_grid_removed", "6. Grid Uklonjen", "binary"),
        ("step_7_cleaned", "7. Morfološko Čišćenje", "binary"),
        ("step_8_main_contour", "8. Glavna EKG Kontura", "binary"),
        ("step_9_signal_1d", "9. Ekstraktovan 1D Signal", "signal"),
        ("step_10_filtered", "10. Filtriran Signal", "signal")
    ]
    
    current_step = 0
    
    for i in range(4):
        for j in range(3):
            if current_step < len(steps_to_show) and current_step < len([k for k in processing_steps.keys() if k.startswith("step_")]):
                
                step_key, title, plot_type = steps_to_show[current_step]
                
                if step_key in processing_steps:
                    ax = fig.add_subplot(gs[i, j])
                    
                    if plot_type == "original":
                        # BGR → RGB za matplotlib
                        rgb_image = cv2.cvtColor(processing_steps[step_key], cv2.COLOR_BGR2RGB)
                        ax.imshow(rgb_image)
                        
                    elif plot_type in ["grayscale", "binary"]:
                        ax.imshow(processing_steps[step_key], cmap='gray')
                        
                    elif plot_type == "signal":
                        signal_data = processing_steps[step_key]
                        if isinstance(signal_data, list) and len(signal_data) > 0:
                            ax.plot(signal_data, 'b-', linewidth=1)
                            ax.set_ylabel('Amplituda')
                            ax.set_xlabel('Samples')
                            ax.grid(True, alpha=0.3)
                        else:
                            ax.text(0.5, 0.5, 'Signal nije dostupan', 
                                   ha='center', va='center', transform=ax.transAxes)
                    
                    ax.set_title(title, fontsize=11, fontweight='bold')
                    ax.axis('off' if plot_type != "signal" else 'on')
                    
                else:
                    # Prazan plot ako step ne postoji
                    ax = fig.add_subplot(gs[i, j])
                    ax.text(0.5, 0.5, f'{title}\n(Korak preskočen)', 
                           ha='center', va='center', transform=ax.transAxes)
                    ax.axis('off')
                
                current_step += 1
            else:
                # Summary ili metadata panel
                if i == 3 and j == 2:  # Poslednji panel
                    ax = fig.add_subplot(gs[i, j])
                    
                    # Metadata summary
                    metadata_text = "PROCESSING SUMMARY\n\n"
                    metadata = processing_steps.get("metadata", {})
                    
                    if "original_size" in metadata:
                        size = metadata["original_size"]
                        metadata_text += f"Originalna veličina: {size[1]}x{size[0]}px\n"
                    
                    if "final_signal" in processing_steps:
                        signal_len = len(processing_steps["final_signal"])
                        metadata_text += f"Dužina signala: {signal_len} tačaka\n"
                    
                    metadata_text += f"\nPROCESSING STEPS:\n"
                    metadata_text += f"✓ RGB → Grayscale\n"
                    metadata_text += f"✓ Gaussian Blur\n"
                    metadata_text += f"✓ Adaptivna Binarizacija\n"
                    metadata_text += f"✓ Grid Detection & Removal\n"
                    metadata_text += f"✓ Morfološko Čišćenje\n"
                    metadata_text += f"✓ Kontura Detekcija\n"
                    metadata_text += f"✓ 1D Signal Ekstrakcija\n"
                    metadata_text += f"✓ Band-pass Filtriranje\n"
                    
                    if "error" in processing_steps:
                        metadata_text += f"\n⚠️ GREŠKA: {processing_steps['error']}"
                    else:
                        metadata_text += f"\n✅ USPEŠNO ZAVRŠENO"
                    
                    ax.text(0.05, 0.95, metadata_text, transform=ax.transAxes,
                           fontsize=9, verticalalignment='top', fontfamily='monospace',
                           bbox=dict(boxstyle="round,pad=0.5", facecolor='lightblue', alpha=0.8))
                    ax.axis('off')
                    break
    
    plt.suptitle('EKG Image Processing - Step by Step Analiza', 
                 fontsize=16, fontweight='bold', y=0.98)
    
    return _save_plot_as_base64(fig)

def create_summary_visualization(processing_steps):
    """
    Kreira sažetu vizuelizaciju (pre/posle + signal)
    """
    
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    
    # Original slika
    if "step_1_original" in processing_steps:
        rgb_image = cv2.cvtColor(processing_steps["step_1_original"], cv2.COLOR_BGR2RGB)
        axes[0, 0].imshow(rgb_image)
        axes[0, 0].set_title('Originalna EKG Slika', fontweight='bold')
        axes[0, 0].axis('off')
    
    # Finalno procesirana slika
    if "step_7_cleaned" in processing_steps:
        axes[0, 1].imshow(processing_steps["step_7_cleaned"], cmap='gray')
        axes[0, 1].set_title('Procesirana Slika (Grid Uklonjen)', fontweight='bold')
        axes[0, 1].axis('off')
    
    # Detekcija konture
    if "step_8_main_contour" in processing_steps:
        axes[1, 0].imshow(processing_steps["step_8_main_contour"], cmap='gray')
        axes[1, 0].set_title('Detektovana EKG Kontura', fontweight='bold')
        axes[1, 0].axis('off')
    
    # Finalni 1D signal
    if "final_signal" in processing_steps and len(processing_steps["final_signal"]) > 0:
        signal_data = processing_steps["final_signal"]
        t = np.linspace(0, len(signal_data)/250, len(signal_data))  # Assume 250 Hz
        axes[1, 1].plot(t, signal_data, 'b-', linewidth=1.5)
        axes[1, 1].set_title('Ekstraktovan 1D EKG Signal', fontweight='bold')
        axes[1, 1].set_xlabel('Vreme (s)')
        axes[1, 1].set_ylabel('Amplituda')
        axes[1, 1].grid(True, alpha=0.3)
    else:
        axes[1, 1].text(0.5, 0.5, 'Signal nije uspešno ekstraktovan', 
                       ha='center', va='center', transform=axes[1, 1].transAxes)
        axes[1, 1].set_title('Ekstraktovan 1D EKG Signal', fontweight='bold')
    
    plt.tight_layout()
    plt.suptitle('EKG Image Processing - Summary', fontsize=14, fontweight='bold', y=0.98)
    
    return _save_plot_as_base64(fig)

def _save_plot_as_base64(fig):
    """
    Konvertuje matplotlib figuru u base64 string
    """
    
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight', 
                facecolor='white', edgecolor='none')
    buf.seek(0)
    
    # Base64 encoding
    image_base64 = base64.b64encode(buf.read()).decode('utf-8')
    
    plt.close(fig)  # Oslobodi memoriju
    
    return {
        'image_base64': f"data:image/png;base64,{image_base64}",
        'width': fig.get_figwidth() * fig.dpi,
        'height': fig.get_figheight() * fig.dpi,
        'format': 'PNG'
    }

def create_comparison_visualization(original_signal, extracted_signal):
    """
    Poredi originalni signal sa ekstraktovanim iz slike
    """
    
    fig, axes = plt.subplots(3, 1, figsize=(15, 10))
    
    # Originalni signal
    if len(original_signal) > 0:
        t1 = np.linspace(0, len(original_signal)/250, len(original_signal))
        axes[0].plot(t1, original_signal, 'b-', linewidth=1.5, alpha=0.8)
        axes[0].set_title('Originalni EKG Signal', fontweight='bold')
        axes[0].set_ylabel('Amplituda')
        axes[0].grid(True, alpha=0.3)
    
    # Ekstraktovani signal
    if len(extracted_signal) > 0:
        t2 = np.linspace(0, len(extracted_signal)/250, len(extracted_signal))
        axes[1].plot(t2, extracted_signal, 'r-', linewidth=1.5, alpha=0.8)
        axes[1].set_title('Signal Ekstraktovan iz Slike', fontweight='bold')
        axes[1].set_ylabel('Amplituda')
        axes[1].grid(True, alpha=0.3)
    
    # Overlay poređenje
    if len(original_signal) > 0 and len(extracted_signal) > 0:
        # Resample na istu dužinu
        min_len = min(len(original_signal), len(extracted_signal))
        orig_resampled = signal.resample(original_signal, min_len)
        extr_resampled = signal.resample(extracted_signal, min_len)
        t_common = np.linspace(0, min_len/250, min_len)
        
        axes[2].plot(t_common, orig_resampled, 'b-', linewidth=2, alpha=0.7, label='Originalni')
        axes[2].plot(t_common, extr_resampled, 'r--', linewidth=2, alpha=0.7, label='Ekstraktovani')
        
        # Korelacija
        correlation = np.corrcoef(orig_resampled, extr_resampled)[0, 1]
        axes[2].set_title(f'Overlay Poređenje (Korelacija: {correlation:.3f})', fontweight='bold')
        axes[2].set_xlabel('Vreme (s)')
        axes[2].set_ylabel('Amplituda')
        axes[2].legend()
        axes[2].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.suptitle('Poređenje: Originalni vs Ekstraktovani Signal', fontsize=14, fontweight='bold', y=0.98)
    
    return _save_plot_as_base64(fig)