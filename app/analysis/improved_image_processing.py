"""
Poboljšana obrada EKG slika za bolju detekciju R-pikova
Specijalno optimizovano za SVT i tahikardije
"""
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

import numpy as np
from scipy import signal
import io
import base64

def process_ekg_image_improved(image_data, is_base64=True, skip_validation=False):
    """
    Poboljšana obrada EKG slike sa boljom detekcijom R-pikova
    """
    if not CV2_AVAILABLE:
        return {"error": "OpenCV nije dostupan"}
    
    try:
        # Dekodiranje slike
        if is_base64:
            if ',' in image_data:
                image_data = image_data.split(',')[1]
            image_bytes = base64.b64decode(image_data)
        else:
            image_bytes = image_data
            
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return {"error": "Nije moguće dekodirati sliku"}
        
        # Napredna ekstrakcija signala
        signal_data = extract_ekg_signal_advanced(img)
        
        return {
            "success": True,
            "signal": signal_data["signal"],
            "signal_length": len(signal_data["signal"]),
            "image_shape": img.shape,
            "processing_steps": signal_data["processing_steps"],
            "detected_leads": signal_data["detected_leads"],
            "estimated_heart_rate": signal_data["estimated_heart_rate"]
        }
        
    except Exception as e:
        return {"error": f"Greška pri obradi slike: {str(e)}"}

def extract_ekg_signal_advanced(img):
    """
    Napredna ekstrakcija EKG signala sa Multi-Lead detekcijom
    """
    height, width = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 1. PREDOBRADA SLIKE
    # Gaussian blur da uklonimo šum
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)
    
    # Adaptivni threshold sa većom prethodnicom
    binary = cv2.adaptiveThreshold(
        blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY_INV, 15, 4
    )
    
    # 2. UKLANJANJE GRID-a
    # Detekcija horizontalnih linija (grid)
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (width//30, 1))
    horizontal_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, horizontal_kernel)
    
    # Detekcija vertikalnih linija (grid) 
    vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, height//30))
    vertical_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, vertical_kernel)
    
    # Uklanjanje grid-a
    signal_only = binary.copy()
    signal_only = cv2.subtract(signal_only, horizontal_lines)
    signal_only = cv2.subtract(signal_only, vertical_lines)
    
    # 3. MORFOLOŠKE OPERACIJE ZA ČIŠĆENJE
    # Uklanjanje malih objekata
    kernel = np.ones((2,2), np.uint8)
    cleaned = cv2.morphologyEx(signal_only, cv2.MORPH_CLOSE, kernel)
    cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel)
    
    # 4. DETEKCIJA EKG LEAD-OVA
    leads = detect_ekg_leads(cleaned, height, width)
    
    if not leads:
        # Fallback - koristi celu sliku kao jedan lead
        leads = [{"y_start": 0, "y_end": height, "center_y": height//2}]
    
    # 5. EKSTRAKCIJA SIGNALA IZ GLAVNOG LEAD-a
    main_lead = leads[0]  # Uzmi prvi (najjasniji) lead
    lead_signal = extract_signal_from_lead(cleaned, main_lead, width)
    
    # 6. POST-PROCESSING
    # Normalizacija
    lead_signal = np.array(lead_signal)
    lead_signal = (lead_signal - np.mean(lead_signal)) / (np.std(lead_signal) + 1e-8)
    
    # Uklanjanje baseline wander
    lead_signal = remove_baseline_wander(lead_signal)
    
    # Filtriranje
    lead_signal = filter_ekg_signal(lead_signal)
    
    # 7. PROCENA SRČANE FREKVENCIJE
    estimated_hr = estimate_heart_rate_from_image(lead_signal, target_duration=10.0)
    
    # 8. RESAMPLE NA STANDARDNU FREKVENCIJU
    target_fs = 250
    target_length = int(target_fs * 10)  # 10 sekundi
    
    if len(lead_signal) != target_length:
        x_old = np.linspace(0, 1, len(lead_signal))
        x_new = np.linspace(0, 1, target_length)
        lead_signal = np.interp(x_new, x_old, lead_signal)
    
    return {
        "signal": lead_signal.tolist(),
        "processing_steps": [
            "1. Gaussian blur",
            "2. Adaptivni threshold", 
            "3. Grid removal (horizontal/vertical)",
            "4. Morfološko čišćenje",
            "5. Multi-lead detekcija",
            "6. Signal ekstrakcija",
            "7. Baseline removal",
            "8. Filtriranje",
            "9. Resample na 250 Hz"
        ],
        "detected_leads": len(leads),
        "estimated_heart_rate": estimated_hr
    }

def detect_ekg_leads(binary_img, height, width):
    """
    Detektuje različite EKG lead-ove na slici
    """
    leads = []
    
    # Podeli sliku na horizontalne trake da pronađeš lead-ove
    num_sections = 6  # Maksimalno 6 lead-ova
    section_height = height // num_sections
    
    for i in range(num_sections):
        y_start = i * section_height
        y_end = min((i + 1) * section_height, height)
        section = binary_img[y_start:y_end, :]
        
        # Proveri da li sekcija ima dovoljno signala
        signal_density = np.sum(section > 0) / (section.shape[0] * section.shape[1])
        
        if signal_density > 0.01:  # Ako ima barem 1% belih piksela
            # Pronađi centar signala u ovoj sekciji
            y_coords, x_coords = np.where(section > 0)
            if len(y_coords) > 0:
                center_y_relative = np.mean(y_coords)
                center_y_absolute = y_start + center_y_relative
                
                leads.append({
                    "y_start": y_start,
                    "y_end": y_end, 
                    "center_y": center_y_absolute,
                    "signal_density": signal_density
                })
    
    # Sortiraj lead-ove po signal density (najjasniji prvo)
    leads.sort(key=lambda x: x["signal_density"], reverse=True)
    
    return leads

def extract_signal_from_lead(binary_img, lead_info, width):
    """
    POBOLJŠANO: Ekstraktuje signal iz određenog lead-a sa boljom obradom
    """
    y_start = int(lead_info["y_start"])
    y_end = int(lead_info["y_end"])
    lead_section = binary_img[y_start:y_end, :]
    
    signal = []
    
    for x in range(width):
        column = lead_section[:, x]
        white_pixels = np.where(column > 0)[0]
        
        if len(white_pixels) > 0:
            # POBOLJŠANO: Weighted center of mass umesto simple average
            groups = []
            current_group = [white_pixels[0]]
            
            for i in range(1, len(white_pixels)):
                if white_pixels[i] - white_pixels[i-1] <= 3:  # Gap threshold
                    current_group.append(white_pixels[i])
                else:
                    groups.append(current_group)
                    current_group = [white_pixels[i]]
            groups.append(current_group)
            
            if groups and len(groups) > 0:
                # Weighted average po veličini grupe
                positions = []
                weights = []
                for group in groups:
                    center_y = np.mean(group)
                    weight = len(group)  # Veća grupa = veći weight
                    positions.append(center_y)
                    weights.append(weight)
                
                weighted_avg = np.average(positions, weights=weights)
                amplitude = (lead_section.shape[0] - weighted_avg) / lead_section.shape[0]
                signal.append(amplitude)
            else:
                # Fallback na osnovni average
                avg_y = np.mean(white_pixels)
                amplitude = (lead_section.shape[0] - avg_y) / lead_section.shape[0]
                signal.append(amplitude)
        else:
            # POBOLJŠANA interpolacija za prazne kolone
            if len(signal) >= 2:
                # Linearna ekstrapolacija
                signal.append(2 * signal[-1] - signal[-2])
            elif signal:
                signal.append(signal[-1])
            else:
                # Traži signal u okolini
                nearest_value = find_nearest_signal_in_lead(lead_section, x)
                signal.append(nearest_value)
    
    return signal

def find_nearest_signal_in_lead(lead_section, x):
    """
    NOVO: Pronalazi najbliži signal u lead sekciji
    """
    height, width = lead_section.shape
    
    # Traži u okolini ±5 piksela
    for offset in range(1, 6):
        # Levo
        if x - offset >= 0:
            left_column = lead_section[:, x - offset]
            left_pixels = np.where(left_column > 0)[0]
            if len(left_pixels) > 0:
                avg_y = np.mean(left_pixels)
                return (height - avg_y) / height
        
        # Desno
        if x + offset < width:
            right_column = lead_section[:, x + offset]
            right_pixels = np.where(right_column > 0)[0]
            if len(right_pixels) > 0:
                avg_y = np.mean(right_pixels)
                return (height - avg_y) / height
    
    # Ako nema ništa u okolini, vrati centru
    return 0.5

def remove_baseline_wander(signal):
    """
    Uklanja baseline wander iz EKG signala
    """
    if len(signal) < 10:
        return signal
        
    # Moving average za baseline
    window_size = max(10, len(signal) // 20)
    baseline = np.convolve(signal, np.ones(window_size)/window_size, mode='same')
    
    # Uklanjanje baseline-a
    corrected = signal - baseline
    
    return corrected

def filter_ekg_signal(signal):
    """
    Filtrira EKG signal (bandpass 0.5-40 Hz)
    """
    if len(signal) < 10:
        return signal
        
    try:
        # Simulate sampling rate 250 Hz for filtering
        fs = 250
        nyquist = fs / 2
        
        # Bandpass filter 0.5-40 Hz
        low = 0.5 / nyquist
        high = 40 / nyquist
        
        # Ensure frequency values are in valid range
        low = max(0.001, min(low, 0.99))
        high = max(low + 0.001, min(high, 0.99))
        
        b, a = signal.butter(4, [low, high], btype='band')
        filtered = signal.filtfilt(b, a, signal)
        
        return filtered
        
    except Exception as e:
        print(f"Filter error: {e}")
        return signal

def estimate_heart_rate_from_image(signal, target_duration=10.0):
    """
    Procenjuje srčanu frekvenciju iz signala ekstraktovanog iz slike
    """
    if len(signal) < 50:
        return {"bpm": 60, "confidence": "low", "reason": "Signal prekratak"}
    
    try:
        # Normalizuj signal
        signal = np.array(signal)
        signal = (signal - np.mean(signal)) / (np.std(signal) + 1e-8)
        
        # Pronađi pikove (R-wave kandidati)
        # Visok threshold za jasne pikove
        height_threshold = np.std(signal) * 1.5
        
        peaks, properties = signal.find_peaks(
            signal,
            height=height_threshold,
            distance=len(signal) // 50,  # Minimum razmak između pikova
            prominence=0.3
        )
        
        if len(peaks) < 2:
            # Probaj sa nižim threshold-om
            height_threshold = np.std(signal) * 0.8
            peaks, properties = signal.find_peaks(
                signal,
                height=height_threshold,
                distance=len(signal) // 80,
                prominence=0.1
            )
        
        if len(peaks) < 2:
            return {"bpm": 60, "confidence": "low", "reason": f"Malo pikova detektovano: {len(peaks)}"}
        
        # Računanje frekvencije
        num_beats = len(peaks)
        duration_seconds = target_duration
        bpm = (num_beats / duration_seconds) * 60
        
        # Confidence based na broj pikova
        if num_beats >= 8:
            confidence = "high"
        elif num_beats >= 4:
            confidence = "medium"
        else:
            confidence = "low"
        
        return {
            "bpm": round(bpm, 1),
            "confidence": confidence,
            "detected_peaks": num_beats,
            "duration": duration_seconds,
            "reason": f"{num_beats} R-pikova u {duration_seconds}s"
        }
        
    except Exception as e:
        return {"bpm": 60, "confidence": "low", "reason": f"Greška: {str(e)}"}

def analyze_ekg_rhythm_from_image(signal):
    """
    Analizira ritam EKG-a iz signala dobijenog iz slike
    """
    estimated_hr = estimate_heart_rate_from_image(signal)
    
    # Klasifikacija ritma
    bpm = estimated_hr["bpm"]
    
    if bpm < 60:
        rhythm_type = "Bradikardija"
        severity = "medium" if bpm > 50 else "high"
    elif bpm > 100:
        if bpm > 150:
            rhythm_type = "SVT (Supraventrikularna tahikardija)"
            severity = "high"
        else:
            rhythm_type = "Tahikardija"
            severity = "medium"
    else:
        rhythm_type = "Normalan sinusni ritam"
        severity = "low"
    
    return {
        "rhythm_type": rhythm_type,
        "heart_rate_bpm": bpm,
        "severity": severity,
        "confidence": estimated_hr["confidence"],
        "detected_peaks": estimated_hr.get("detected_peaks", 0),
        "clinical_interpretation": get_clinical_interpretation(bpm, rhythm_type)
    }

def get_clinical_interpretation(bpm, rhythm_type):
    """
    Daje kliničku interpretaciju na osnovu frekvencije
    """
    if "SVT" in rhythm_type:
        return f"Supraventrikularna tahikardija ({bpm} bpm) - tipična frekvencija 150-220 bpm. Potrebna hitna evaluacija."
    elif "Tahikardija" in rhythm_type:
        return f"Sinusna tahikardija ({bpm} bpm) - može biti posledica stresa, anksioznosti, vežbanja ili patoloških stanja."
    elif "Bradikardija" in rhythm_type:
        return f"Bradikardija ({bpm} bpm) - sporiji ritam, praćenje preporučeno."
    else:
        return f"Normalan sinusni ritam ({bpm} bpm) - u fiziološkim granicama."

def preprocess_for_analysis(signal, target_fs=250):
    """
    Priprema signal za analizu - resample i normalizacija
    (Kopija iz image_processing.py da se izbegnu import greške)
    """
    # Normalizacija signala
    signal = np.array(signal)
    signal = (signal - np.mean(signal)) / np.std(signal)
    
    # Osnovni resampling (interpolacija)
    target_length = int(target_fs * 10)  # 10 sekundi EKG-a
    if len(signal) != target_length:
        try:
            # Jednostavna interpolacija bez scipy
            x_old = np.linspace(0, 1, len(signal))
            x_new = np.linspace(0, 1, target_length)
            signal = np.interp(x_new, x_old, signal)
        except Exception:
            # Fallback - ponavljanje ili skraćivanje
            if len(signal) > target_length:
                signal = signal[:target_length]
            else:
                repeat_factor = target_length // len(signal) + 1
                signal = np.tile(signal, repeat_factor)[:target_length]
    
    return signal, target_fs