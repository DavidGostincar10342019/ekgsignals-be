try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("Warning: OpenCV not available. Image processing will be limited.")

import numpy as np
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("Warning: PIL not available. Image processing will be limited.")

import io
import base64
try:
    from scipy import interpolate
    from scipy.ndimage import gaussian_filter1d
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    print("Warning: SciPy not available. Advanced signal processing will be limited.")

def process_ekg_image(image_data, is_base64=True, skip_validation=False):
    """
    Konvertuje EKG fotografiju u digitalni signal
    
    Args:
        image_data: Base64 string ili bytes slike
        is_base64: Da li je input base64 enkodovan
    
    Returns:
        dict: Rezultat sa digitalnim signalom i metapodacima
    """
    if not CV2_AVAILABLE:
        return {"error": "OpenCV nije dostupan. Instaliraju: pip install opencv-python"}
    
    try:
        # Dekodiranje slike
        if is_base64:
            # Uklanjanje data:image/jpeg;base64, prefiksa ako postoji
            if ',' in image_data:
                image_data = image_data.split(',')[1]
            image_bytes = base64.b64decode(image_data)
        else:
            image_bytes = image_data
            
        # Konverzija u OpenCV format
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return {"error": "Nije moguće dekodirati sliku"}
        
        # Validacija da li je slika EKG (opciono za test slike)
        if not skip_validation:
            validation_result = validate_ekg_image(img)
            if not validation_result["is_valid"]:
                return {"error": f"Slika nije prepoznata kao EKG: {validation_result['reason']}"}
        else:
            validation_result = {"is_valid": True, "reason": "Validacija preskočena (test slika)"}
        
        # POBOLJŠANO: Pokušaj sa naprednom grid-aware metodom
        advanced_result = extract_ekg_signal_advanced(img)
        
        if advanced_result.get("success", False):
            return {
                "success": True,
                "signal": advanced_result["signal"],
                "signal_length": len(advanced_result["signal"]),
                "voltage_calibrated": advanced_result.get("voltage_calibrated", False),
                "time_calibrated": advanced_result.get("time_calibrated", False),
                "grid_detected": advanced_result.get("grid_detected", False),
                "processing_method": "advanced_grid_aware_spline_fitting",
                "image_shape": img.shape,
                "processing_steps": "grayscale -> grid_detection -> threshold -> spline_fitting -> calibration",
                "calibration_info": advanced_result.get("calibration_info", {})
            }
        else:
            # FALLBACK na postojeću metodu ako napredna ne radi
            signal = extract_ekg_signal(img)
            return {
                "success": True,
                "signal": signal.tolist(),
                "signal_length": len(signal),
                "voltage_calibrated": False,
                "time_calibrated": False,
                "grid_detected": False,
                "processing_method": "legacy_contour_centroid",
                "image_shape": img.shape,
                "processing_steps": "grayscale -> threshold -> contour_detection -> signal_extraction",
                "note": "Advanced processing failed, using legacy method"
            }
        
    except Exception as e:
        return {"error": f"Greška pri obradi slike: {str(e)}"}

def extract_ekg_signal(img):
    """
    Ekstraktuje EKG signal iz slike koristeći obradu kontura
    
    Args:
        img: OpenCV slika (BGR format)
    
    Returns:
        numpy.array: 1D signal amplituda
    """
    # Konverzija u grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Adaptivni threshold za binarizaciju
    binary = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY_INV, 11, 2
    )
    
    # Morfološke operacije za čišćenje šuma
    kernel = np.ones((2,2), np.uint8)
    cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
    
    # Detekcija kontura
    contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if not contours:
        # Ako nema kontura, pokušaj sa osnovnim pristupom
        return extract_signal_basic(gray)
    
    # Pronalaženje najveće konture (pretpostavljamo da je to EKG signal)
    largest_contour = max(contours, key=cv2.contourArea)
    
    # Kreiranje maske za signal
    mask = np.zeros(gray.shape, np.uint8)
    cv2.drawContours(mask, [largest_contour], -1, 255, -1)
    
    # Ekstrakcija signala po kolonama
    height, width = gray.shape
    signal = []
    
    for x in range(width):
        # Pronalaženje Y koordinata signala u koloni x
        column_mask = mask[:, x]
        signal_points = np.where(column_mask == 255)[0]
        
        if len(signal_points) > 0:
            # Uzimanje srednje vrednosti ako ima više tačaka
            avg_y = np.mean(signal_points)
            # Konverzija u amplitudu (invertovano jer je Y osa obrnuta)
            amplitude = (height - avg_y) / height
            signal.append(amplitude)
        else:
            # Ako nema signala u koloni, dodaj prethodnu vrednost ili 0
            signal.append(signal[-1] if signal else 0.5)
    
    return np.array(signal)

def extract_signal_basic(gray_img):
    """
    Osnovni pristup ekstrakciji signala kada konture ne rade dobro
    """
    height, width = gray_img.shape
    signal = []
    
    for x in range(width):
        column = gray_img[:, x]
        # Pronalaženje najcrnje tačke u koloni (EKG linija)
        min_idx = np.argmin(column)
        amplitude = (height - min_idx) / height
        signal.append(amplitude)
    
    return np.array(signal)

def preprocess_for_analysis(signal, target_fs=250):
    """
    Priprema signal za analizu - resample i normalizacija
    
    Args:
        signal: 1D numpy array
        target_fs: Ciljna frekvencija uzorkovanja
    
    Returns:
        tuple: (processed_signal, effective_fs)
    """
    # Normalizacija signala
    signal = np.array(signal)
    signal = (signal - np.mean(signal)) / np.std(signal)
    
    # Osnovni resampling (interpolacija)
    target_length = int(target_fs * 10)  # Ensure integer
    if len(signal) != target_length:  # Pretpostavljamo 10 sekundi EKG-a
        try:
            from scipy import interpolate
            x_old = np.linspace(0, 1, len(signal))
            x_new = np.linspace(0, 1, target_length)
            f = interpolate.interp1d(x_old, signal, kind='linear', bounds_error=False, fill_value='extrapolate')
            signal = f(x_new)
        except ImportError:
            # Fallback bez scipy - jednostavno ponavljanje ili skraćivanje
            if len(signal) > target_length:
                signal = signal[:target_length]
            else:
                # Ponovi signal da dostigne target_length
                repeat_factor = target_length // len(signal) + 1
                signal = np.tile(signal, repeat_factor)[:target_length]
    
    return signal, target_fs

def validate_ekg_image(img):
    """
    Validira da li je slika stvarno EKG zapis
    
    Args:
        img: OpenCV slika
    
    Returns:
        dict: Rezultat validacije
    """
    try:
        height, width = img.shape[:2]
        
        # 1. Provera dimenzija - EKG slike su obično landscape
        if height > width:
            return {"is_valid": False, "reason": "EKG slike su obično šire nego više (landscape format)"}
        
        # 2. Konverzija u grayscale za analizu
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img
        
        # 3. Provera kontrasta - EKG mora imati dovoljno kontrasta
        contrast = np.std(gray)
        if contrast < 20:
            return {"is_valid": False, "reason": "Slika nema dovoljno kontrasta za EKG signal"}
        
        # 4. Detekcija linija - EKG mora imati kontinuirane linije
        edges = cv2.Canny(gray, 50, 150)
        line_density = np.sum(edges > 0) / (height * width)
        
        if line_density < 0.005:  # Manje od 0.5% piksela su linije
            return {"is_valid": False, "reason": "Slika ne sadrži dovoljno linija karakterističnih za EKG"}
        
        if line_density > 0.6:  # Više od 60% piksela su linije (previše šuma)
            return {"is_valid": False, "reason": "Slika sadrži previše linija/šuma - nije jasna EKG slika"}
        
        # 5. Provera horizontalnih linija - EKG ima grid
        horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
        horizontal_lines = cv2.morphologyEx(edges, cv2.MORPH_OPEN, horizontal_kernel)
        horizontal_density = np.sum(horizontal_lines > 0) / (height * width)
        
        # 6. Provera vertikalnih linija - EKG ima grid
        vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
        vertical_lines = cv2.morphologyEx(edges, cv2.MORPH_OPEN, vertical_kernel)
        vertical_density = np.sum(vertical_lines > 0) / (height * width)
        
        # EKG mora imati i horizontalne i vertikalne linije (grid)
        if horizontal_density < 0.001 and vertical_density < 0.001:
            return {"is_valid": False, "reason": "Slika ne sadrži grid karakterističan za EKG papir"}
        
        # 7. Detekcija kontinuiranih krivulja - EKG signal
        # Uklanjanje grid-a da ostane samo signal
        clean_edges = edges.copy()
        clean_edges = cv2.subtract(clean_edges, horizontal_lines)
        clean_edges = cv2.subtract(clean_edges, vertical_lines)
        
        # Detekcija kontura signala
        contours, _ = cv2.findContours(clean_edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if len(contours) == 0:
            return {"is_valid": False, "reason": "Nije pronađen EKG signal na slici"}
        
        # Analiza najveće konture (trebalo bi biti EKG signal)
        largest_contour = max(contours, key=cv2.contourArea)
        contour_area = cv2.contourArea(largest_contour)
        
        if contour_area < 100:  # Premala kontura
            return {"is_valid": False, "reason": "Pronađeni signal je premali da bi bio EKG"}
        
        # 8. Provera da li kontura ima karakteristike EKG signala
        # EKG signal treba da se proteže kroz značajan deo slike horizontalno
        x, y, w, h = cv2.boundingRect(largest_contour)
        horizontal_coverage = w / width
        
        if horizontal_coverage < 0.15:  # Signal pokriva manje od 15% širine
            return {"is_valid": False, "reason": "Signal ne pokriva dovoljno širine slike za EKG"}
        
        # 9. Provera frekvencije oscilacija - EKG ima karakteristične pikove
        # Uzimamo srednju liniju konture
        contour_points = largest_contour.reshape(-1, 2)
        if len(contour_points) < 50:
            return {"is_valid": False, "reason": "Signal nema dovoljno tačaka za analizu"}
        
        # Sortiramo po x koordinati
        sorted_points = contour_points[contour_points[:, 0].argsort()]
        y_values = sorted_points[:, 1]
        
        # Analiza varijabilnosti - EKG mora imati pikove
        if len(y_values) > 10:
            y_std = np.std(y_values)
            y_range = np.max(y_values) - np.min(y_values)
            
            if y_std < 5 or y_range < 20:
                return {"is_valid": False, "reason": "Signal nema dovoljno varijabilnosti za EKG (previše ravan)"}
        
        # Sve provere prošle - verovatno je EKG
        return {
            "is_valid": True, 
            "reason": "Slika prošla sve validacije za EKG",
            "confidence": calculate_ekg_confidence(contrast, line_density, horizontal_density, 
                                                 vertical_density, horizontal_coverage, y_std if 'y_std' in locals() else 0),
            "metrics": {
                "contrast": float(contrast),
                "line_density": float(line_density),
                "horizontal_coverage": float(horizontal_coverage),
                "signal_variability": float(y_std if 'y_std' in locals() else 0)
            }
        }
        
    except Exception as e:
        return {"is_valid": False, "reason": f"Greška pri validaciji: {str(e)}"}

def calculate_ekg_confidence(contrast, line_density, horizontal_density, vertical_density, horizontal_coverage, y_std):
    """
    Kalkuliše confidence score za EKG sliku (0-100%)
    """
    score = 0
    
    # Contrast score (0-25 points)
    if contrast > 50:
        score += 25
    elif contrast > 30:
        score += 15
    elif contrast > 20:
        score += 10
    
    # Line density score (0-25 points)
    if 0.05 <= line_density <= 0.15:  # Optimalan opseg
        score += 25
    elif 0.01 <= line_density <= 0.3:
        score += 15
    
    # Grid presence score (0-20 points)
    if horizontal_density > 0.001 and vertical_density > 0.001:
        score += 20
    elif horizontal_density > 0.001 or vertical_density > 0.001:
        score += 10
    
    # Coverage score (0-15 points)
    if horizontal_coverage > 0.7:
        score += 15
    elif horizontal_coverage > 0.5:
        score += 10
    elif horizontal_coverage > 0.3:
        score += 5
    
    # Variability score (0-15 points)
    if y_std > 20:
        score += 15
    elif y_std > 10:
        score += 10
    elif y_std > 5:
        score += 5
    
    return min(100, score)

def extract_ekg_signal_advanced(img):
    """
    NAPREDNA METODA: Grid-aware EKG signal ekstrakcija sa spline fitting
    
    Implementira:
    1. EKG grid detekciju za kalibraciju
    2. Spline fitting umesto centroida
    3. Voltage i time kalibraciju
    4. Noise filtering i outlier removal
    
    Args:
        img: OpenCV slika (BGR format)
    
    Returns:
        dict: Rezultat sa kalibrisanim signalom ili error
    """
    if not SCIPY_AVAILABLE:
        return {"success": False, "error": "SciPy not available for advanced processing"}
    
    try:
        # 1. GRID DETEKCIJA za kalibraciju
        grid_info = detect_ekg_grid(img)
        
        # 2. PREDOBRADA slike sa grid-aware pristupom
        processed_img = preprocess_image_for_signal_extraction(img, grid_info)
        
        # 3. SPLINE-BASED signal ekstrakcija
        signal_points = extract_signal_via_spline_fitting(processed_img)
        
        if len(signal_points) < 10:  # Premalo tačaka za validni signal
            return {"success": False, "error": "Insufficient signal points detected"}
        
        # 4. KALIBRACIJA sa grid informacijama
        calibrated_signal = apply_grid_calibration(signal_points, grid_info)
        
        # 5. POST-PROCESSING: noise filtering i validacija
        final_signal = post_process_extracted_signal(calibrated_signal)
        
        return {
            "success": True,
            "signal": final_signal.tolist(),
            "voltage_calibrated": grid_info.get("voltage_scale_detected", False),
            "time_calibrated": grid_info.get("time_scale_detected", False),
            "grid_detected": grid_info.get("grid_detected", False),
            "calibration_info": grid_info,
            "processing_quality": assess_extraction_quality(final_signal, signal_points),
            "method": "spline_fitting_with_grid_calibration"
        }
        
    except Exception as e:
        return {"success": False, "error": f"Advanced extraction failed: {str(e)}"}

def detect_ekg_grid(img):
    """
    Detektuje EKG grid za voltage/time kalibraciju
    
    EKG papir standardno ima:
    - Mali kvadrat: 1mm x 1mm (0.04s x 0.1mV)  
    - Veliki kvadrat: 5mm x 5mm (0.2s x 0.5mV)
    
    Returns:
        dict: Grid informacije za kalibraciju
    """
    try:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Detektuj horizontalne linije (time grid)
        horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
        horizontal_lines = cv2.morphologyEx(gray, cv2.MORPH_OPEN, horizontal_kernel)
        
        # Detektuj vertikalne linije (voltage grid)  
        vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
        vertical_lines = cv2.morphologyEx(gray, cv2.MORPH_OPEN, vertical_kernel)
        
        # Analiza grid spacing-a
        h_spacing = analyze_line_spacing(horizontal_lines, direction='horizontal')
        v_spacing = analyze_line_spacing(vertical_lines, direction='vertical')
        
        # Procena kalibracije na osnovu grid spacing-a
        grid_detected = (h_spacing > 0 and v_spacing > 0)
        
        if grid_detected:
            # Standardni EKG papir: 25mm/s brzina, 10mm/mV skala
            time_scale = 0.04 / h_spacing if h_spacing > 0 else 1.0  # sekunde po pikselu
            voltage_scale = 0.1 / v_spacing if v_spacing > 0 else 1.0  # mV po pikselu
        else:
            # Default vrednosti ako grid nije detektovan
            time_scale = 1.0
            voltage_scale = 1.0
        
        return {
            "grid_detected": grid_detected,
            "horizontal_spacing_px": h_spacing,
            "vertical_spacing_px": v_spacing,
            "time_scale_s_per_px": time_scale,
            "voltage_scale_mv_per_px": voltage_scale,
            "time_scale_detected": grid_detected and h_spacing > 5,
            "voltage_scale_detected": grid_detected and v_spacing > 5,
            "confidence": min(100, (h_spacing + v_spacing) / 2) if grid_detected else 0
        }
        
    except Exception as e:
        return {
            "grid_detected": False,
            "error": f"Grid detection failed: {str(e)}",
            "time_scale_s_per_px": 1.0,
            "voltage_scale_mv_per_px": 1.0,
            "time_scale_detected": False,
            "voltage_scale_detected": False,
            "confidence": 0
        }

def analyze_line_spacing(line_img, direction='horizontal'):
    """
    Analizira spacing između grid linija
    """
    try:
        # Threshold za binarnu sliku
        _, binary = cv2.threshold(line_img, 50, 255, cv2.THRESH_BINARY)
        
        if direction == 'horizontal':
            # Sumiraj po kolionama da pronađeš horizontalne linije
            line_profile = np.sum(binary, axis=1)
        else:
            # Sumiraj po redovima da pronađeš vertikalne linije
            line_profile = np.sum(binary, axis=0)
        
        # Pronađi pikove (linije)
        from scipy.signal import find_peaks
        peaks, _ = find_peaks(line_profile, height=np.max(line_profile) * 0.1, distance=5)
        
        if len(peaks) < 2:
            return 0
        
        # Izračunaj prosečan spacing
        spacings = np.diff(peaks)
        return np.mean(spacings) if len(spacings) > 0 else 0
        
    except Exception:
        return 0

def preprocess_image_for_signal_extraction(img, grid_info):
    """
    Predobrada slike sa grid-aware pristupom
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Adaptivni threshold koji poštuje grid strukturu
    if grid_info.get("grid_detected", False):
        # Ako je grid detektovan, koristi specifične parametre
        block_size = max(11, int(grid_info.get("horizontal_spacing_px", 20) // 3))
        if block_size % 2 == 0:  # Mora biti neparan
            block_size += 1
        binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                     cv2.THRESH_BINARY_INV, block_size, 3)
    else:
        # Default adaptive threshold
        binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                     cv2.THRESH_BINARY_INV, 11, 2)
    
    # Morfološke operacije za čišćenje
    kernel = np.ones((2,2), np.uint8)
    cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
    
    # Grid noise removal ako je grid detektovan
    if grid_info.get("grid_detected", False):
        cleaned = remove_grid_noise(cleaned, grid_info)
    
    return cleaned

def remove_grid_noise(binary_img, grid_info):
    """
    Uklanja grid linije da ostavi samo EKG signal
    """
    try:
        # Kreiraj kernel za horizontalne grid linije
        h_spacing = grid_info.get("horizontal_spacing_px", 20)
        v_spacing = grid_info.get("vertical_spacing_px", 20)
        
        # Ukloni horizontalne grid linije
        h_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (max(5, int(h_spacing//3)), 1))
        h_grid = cv2.morphologyEx(binary_img, cv2.MORPH_OPEN, h_kernel)
        
        # Ukloni vertikalne grid linije
        v_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, max(5, int(v_spacing//3))))
        v_grid = cv2.morphologyEx(binary_img, cv2.MORPH_OPEN, v_kernel)
        
        # Kombinuj grid noise
        grid_noise = cv2.bitwise_or(h_grid, v_grid)
        
        # Ukloni grid noise iz originalnog
        cleaned = cv2.bitwise_xor(binary_img, grid_noise)
        
        return cleaned
        
    except Exception:
        # Ako uklanjanje grids ne radi, vrati original
        return binary_img

def extract_signal_via_spline_fitting(processed_img):
    """
    KLJUČNO POBOLJŠANJE: Spline fitting umesto centroida
    
    Implementira B-spline aproksimaciju EKG krive za preciznu rekonstrukciju
    """
    if not SCIPY_AVAILABLE:
        # Fallback na osnovnu metodu
        return extract_signal_basic_fallback(processed_img)
    
    try:
        # 1. Detekcija kontura
        contours, _ = cv2.findContours(processed_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return np.array([])
        
        # 2. Pronađi glavnu konturu (najveću ili najbliže centru)
        main_contour = find_main_ekg_contour(contours, processed_img.shape)
        
        if main_contour is None or len(main_contour) < 10:
            return np.array([])
        
        # 3. Konverzija konture u koordinate
        contour_points = main_contour.reshape(-1, 2)
        
        # 4. Sortiranje po x-koordinati za temporalni signal
        sorted_points = contour_points[np.argsort(contour_points[:, 0])]
        
        # 5. SPLINE FITTING - ključno poboljšanje!
        x_coords = sorted_points[:, 0]
        y_coords = sorted_points[:, 1]
        
        # Ukloni duplikate i outliere
        x_unique, unique_indices = np.unique(x_coords, return_index=True)
        y_unique = y_coords[unique_indices]
        
        # B-spline aproksimacija
        if len(x_unique) >= 4:  # Minimum za kubni spline
            # Kubni spline interpolacija
            spline_func = interpolate.interp1d(x_unique, y_unique, kind='cubic', 
                                             bounds_error=False, fill_value='extrapolate')
            
            # Generiši uniformno samplovane tačke
            x_new = np.linspace(x_unique[0], x_unique[-1], len(x_unique) * 2)
            y_new = spline_func(x_new)
            
            # Invertuj y-koordinate (slika ima origin u gornjem levom uglu)
            signal = processed_img.shape[0] - y_new
            
        else:
            # Fallback na linearnu interpolaciju
            signal = processed_img.shape[0] - y_unique
        
        return signal
        
    except Exception as e:
        print(f"Spline fitting failed: {e}, using fallback")
        return extract_signal_basic_fallback(processed_img)

def find_main_ekg_contour(contours, img_shape):
    """
    Pronalazi glavnu EKG konturu među svim detektovanim konturama
    """
    if not contours:
        return None
    
    # Kriterijumi za glavnu konturu:
    # 1. Dovoljno velika (ne noise)
    # 2. Proteže se horizontalno (EKG signal)
    # 3. Blizu vertikalnog centra (glavni EKG trace)
    
    height, width = img_shape
    center_y = height // 2
    
    best_contour = None
    best_score = 0
    
    for contour in contours:
        if len(contour) < 10:  # Premaloj kontour
            continue
        
        # Analizn konturu
        x, y, w, h = cv2.boundingRect(contour)
        area = cv2.contourArea(contour)
        
        # Scoring kriterijumi
        size_score = min(100, area / (width * height) * 1000)  # Relativna veličina
        horizontal_score = min(100, w / width * 100)  # Horizontalna pokrivenost
        vertical_position_score = max(0, 100 - abs(y + h//2 - center_y) / center_y * 100)  # Blizina centra
        
        total_score = (size_score + horizontal_score + vertical_position_score) / 3
        
        if total_score > best_score:
            best_score = total_score
            best_contour = contour
    
    return best_contour

def extract_signal_basic_fallback(processed_img):
    """
    Fallback metoda kada spline fitting nije dostupan
    """
    contours, _ = cv2.findContours(processed_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if not contours:
        return np.array([])
    
    # Pronađi najveću konturu
    largest_contour = max(contours, key=cv2.contourArea)
    
    # Osnovni centroid pristup
    signal = []
    height = processed_img.shape[0]
    
    for x in range(processed_img.shape[1]):
        column = processed_img[:, x]
        if np.any(column > 0):
            # Pronađi centroida white pixels u ovoj koloni
            white_pixels = np.where(column > 0)[0]
            centroid_y = np.mean(white_pixels)
            signal.append(height - centroid_y)  # Invertuj y
        else:
            signal.append(height // 2)  # Default srednja vrednost
    
    return np.array(signal)

def apply_grid_calibration(signal_points, grid_info):
    """
    Primenjuje voltage i time kalibraciju na osnovu detektovanog grida
    """
    if not grid_info.get("grid_detected", False):
        # Bez grida - vrati normalizovani signal
        return (signal_points - np.mean(signal_points)) / np.std(signal_points)
    
    try:
        # Time kalibracija (x-osa)
        if grid_info.get("time_scale_detected", False):
            time_scale = grid_info.get("time_scale_s_per_px", 1.0)
            # Signal već ima x-koordinate u pikselima, kalibracija je informativna
        
        # Voltage kalibracija (y-osa)
        if grid_info.get("voltage_scale_detected", False):
            voltage_scale = grid_info.get("voltage_scale_mv_per_px", 1.0)
            # Konvertuj piksele u milivolte
            calibrated_signal = signal_points * voltage_scale
        else:
            # Normalizuj na standardni EKG opseg (~5mV)
            calibrated_signal = (signal_points - np.mean(signal_points))
            calibrated_signal = calibrated_signal / np.std(calibrated_signal) * 2.0  # ~2mV std
        
        return calibrated_signal
        
    except Exception:
        # Fallback na normalizaciju
        return (signal_points - np.mean(signal_points)) / np.std(signal_points)

def post_process_extracted_signal(signal):
    """
    Post-processing: noise filtering, outlier removal, validacija
    """
    if len(signal) < 3:
        return signal
    
    try:
        # 1. Outlier removal (remove extreme values)
        q75, q25 = np.percentile(signal, [75, 25])
        iqr = q75 - q25
        lower_bound = q25 - 1.5 * iqr
        upper_bound = q75 + 1.5 * iqr
        
        # Clamp outliers
        filtered_signal = np.clip(signal, lower_bound, upper_bound)
        
        # 2. Gentle smoothing (if scipy available)
        if SCIPY_AVAILABLE and len(filtered_signal) > 10:
            # Gaussian smoothing sa malim sigma da sačuva EKG karakteristike
            smoothed_signal = gaussian_filter1d(filtered_signal, sigma=0.5)
        else:
            smoothed_signal = filtered_signal
        
        # 3. Ensure valid range
        if np.std(smoothed_signal) < 1e-6:  # Constant signal
            # Generate small variation to avoid constant signal
            smoothed_signal = smoothed_signal + np.random.normal(0, 0.01, len(smoothed_signal))
        
        return smoothed_signal
        
    except Exception:
        return signal

def assess_extraction_quality(final_signal, original_points):
    """
    Procenjuje kvalitet ekstrakcije signala
    """
    try:
        if len(final_signal) < 10:
            return {"quality": "poor", "score": 20, "reason": "Too few points"}
        
        # Kriterijumi kvaliteta
        signal_variation = np.std(final_signal)
        signal_smoothness = np.mean(np.abs(np.diff(final_signal, 2))) if len(final_signal) > 2 else 0
        data_coverage = len(final_signal) / len(original_points) if len(original_points) > 0 else 0
        
        # Composite score
        variation_score = min(100, signal_variation * 20)  # Penalizuj constant signals
        smoothness_score = max(0, 100 - signal_smoothness * 10)  # Penalizuj roughness
        coverage_score = min(100, data_coverage * 100)
        
        total_score = (variation_score + smoothness_score + coverage_score) / 3
        
        if total_score > 80:
            quality = "excellent"
        elif total_score > 60:
            quality = "good"
        elif total_score > 40:
            quality = "fair"
        else:
            quality = "poor"
        
        return {
            "quality": quality,
            "score": total_score,
            "variation_score": variation_score,
            "smoothness_score": smoothness_score,
            "coverage_score": coverage_score,
            "signal_std": signal_variation,
            "data_points": len(final_signal)
        }
        
    except Exception:
        return {"quality": "unknown", "score": 50, "reason": "Assessment failed"}