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
        
        # Obrada slike za ekstrakciju EKG signala
        signal = extract_ekg_signal(img)
        
        return {
            "success": True,
            "signal": signal.tolist(),
            "signal_length": len(signal),
            "image_shape": img.shape,
            "processing_steps": "grayscale -> threshold -> contour_detection -> signal_extraction"
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