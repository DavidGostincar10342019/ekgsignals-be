import numpy as np
from scipy import signal
from scipy.signal import find_peaks

def detect_arrhythmias(ekg_signal, fs=250):
    """
    Osnovna detekcija aritmija u EKG signalu
    
    Args:
        ekg_signal: 1D numpy array EKG signala
        fs: Frekvencija uzorkovanja
    
    Returns:
        dict: Rezultati detekcije aritmija
    """
    try:
        signal_array = np.array(ekg_signal, dtype=float)
        
        if len(signal_array) == 0:
            return {"error": "Prazan signal"}
        
        # Predobrada signala
        filtered_signal = preprocess_ekg(signal_array, fs)
        
        # Detekcija R-pikova
        r_peaks = detect_r_peaks(filtered_signal, fs)
        
        # Analiza srčanog ritma
        heart_rate_analysis = analyze_heart_rate(r_peaks, fs)
        
        # Detekcija aritmija
        arrhythmia_results = classify_arrhythmias(r_peaks, filtered_signal, fs)
        
        return {
            "r_peaks": r_peaks.tolist(),
            "r_peaks_count": int(len(r_peaks)),  # DODATO: Eksplicitno brojanje
            "heart_rate": heart_rate_analysis,
            "arrhythmias": arrhythmia_results,
            "signal_quality": assess_signal_quality(filtered_signal),
            "total_duration_seconds": len(signal_array) / fs,
            "detection_method": "signal_analysis"  # DODATO: Označava da su R-pikovi detektovani iz signala
        }
        
    except Exception as e:
        return {"error": f"Greška u detekciji aritmija: {str(e)}"}

def preprocess_ekg(signal_data, fs):
    """
    Predobrada EKG signala - filtriranje šuma
    """
    # Bandpass filter 0.5-40 Hz (tipičan opseg za EKG)
    nyquist = fs / 2
    low = 0.5 / nyquist
    high = 40 / nyquist
    
    b, a = signal.butter(4, [low, high], btype='band')
    filtered = signal.filtfilt(b, a, signal_data)
    
    # Uklanjanje baseline drift
    # High-pass filter na 0.5 Hz
    b_hp, a_hp = signal.butter(2, 0.5/nyquist, btype='high')
    filtered = signal.filtfilt(b_hp, a_hp, filtered)
    
    return filtered

def detect_r_peaks(signal_data, fs):
    """
    Detekcija R-pikova u EKG signalu
    """
    # Normalizacija signala
    normalized = (signal_data - np.mean(signal_data)) / np.std(signal_data)
    
    # Parametri za detekciju pikova
    min_distance = int(0.3 * fs)  # Minimalno 300ms između R-pikova
    height_threshold = np.std(normalized) * 1.5  # Prag visine
    
    # Pronalaženje pikova
    peaks, properties = find_peaks(
        normalized, 
        height=height_threshold,
        distance=min_distance,
        prominence=0.5
    )
    
    return peaks

def analyze_heart_rate(r_peaks, fs):
    """
    Analiza srčanog ritma na osnovu R-pikova
    """
    if len(r_peaks) < 2:
        return {
            "average_bpm": 0,
            "rr_intervals": [],
            "heart_rate_variability": 0,
            "message": "Nedovoljno R-pikova za analizu"
        }
    
    # RR intervali u sekundama
    rr_intervals = np.diff(r_peaks) / fs
    
    # Srčana frekvencija u otkucajima po minuti
    heart_rates = 60.0 / rr_intervals
    average_bpm = np.mean(heart_rates)
    
    # Heart Rate Variability (HRV)
    hrv = np.std(rr_intervals) * 1000  # u milisekundama
    
    return {
        "average_bpm": float(average_bpm),
        "min_bpm": float(np.min(heart_rates)),
        "max_bpm": float(np.max(heart_rates)),
        "rr_intervals": rr_intervals.tolist(),
        "heart_rate_variability": float(hrv),
        "rr_count": int(len(rr_intervals))
    }

def classify_arrhythmias(r_peaks, signal_data, fs):
    """
    Klasifikacija osnovnih tipova aritmija
    """
    if len(r_peaks) < 3:
        return {"detected": [], "message": "Nedovoljno podataka za klasifikaciju"}
    
    # RR intervali
    rr_intervals = np.diff(r_peaks) / fs
    heart_rates = 60.0 / rr_intervals
    avg_hr = np.mean(heart_rates)
    
    detected_arrhythmias = []
    
    # 1. Bradikardija (< 60 bpm)
    if avg_hr < 60:
        detected_arrhythmias.append({
            "type": "Bradikardija",
            "description": "Spor srčani ritam",
            "severity": "low" if avg_hr > 50 else "medium",
            "value": f"{avg_hr:.1f} bpm"
        })
    
    # 2. Tahikardija (> 100 bpm)
    elif avg_hr > 100:
        detected_arrhythmias.append({
            "type": "Tahikardija", 
            "description": "Brz srčani ritam",
            "severity": "medium" if avg_hr < 150 else "high",
            "value": f"{avg_hr:.1f} bpm"
        })
    
    # 3. Aritmija (nepravilan ritam)
    rr_variability = np.std(rr_intervals)
    if rr_variability > 0.1:  # Visoka varijabilnost RR intervala
        detected_arrhythmias.append({
            "type": "Nepravilan ritam",
            "description": "Visoka varijabilnost RR intervala",
            "severity": "medium",
            "value": f"RR std: {rr_variability:.3f}s"
        })
    
    # 4. Detekcija propuštenih otkucaja
    median_rr = np.median(rr_intervals)
    long_intervals = rr_intervals > (median_rr * 1.8)
    if np.any(long_intervals):
        detected_arrhythmias.append({
            "type": "Propušteni otkucaji",
            "description": "Detektovani neobično dugi RR intervali",
            "severity": "medium",
            "value": f"{int(np.sum(long_intervals))} dugih intervala"
        })
    
    return {
        "detected": detected_arrhythmias,
        "total_count": int(len(detected_arrhythmias)),
        "overall_assessment": get_overall_assessment(detected_arrhythmias)
    }

def assess_signal_quality(signal_data):
    """
    Procena kvaliteta EKG signala
    """
    # Signal-to-noise ratio procena
    signal_power = np.var(signal_data)
    
    # Procena šuma kroz visokofrekventne komponente
    b, a = signal.butter(4, 0.8, btype='high')  # High-pass > 40Hz
    noise = signal.filtfilt(b, a, signal_data)
    noise_power = np.var(noise)
    
    if noise_power > 0:
        snr = 10 * np.log10(signal_power / noise_power)
    else:
        snr = float('inf')
    
    # Kvalitet na osnovu SNR
    if snr > 20:
        quality = "Odličan"
    elif snr > 10:
        quality = "Dobar"
    elif snr > 5:
        quality = "Umeren"
    else:
        quality = "Loš"
    
    return {
        "snr_db": float(snr) if snr != float('inf') else 100.0,
        "quality": quality,
        "signal_power": float(signal_power),
        "noise_power": float(noise_power)
    }

def get_overall_assessment(arrhythmias):
    """
    Ukupna procena na osnovu detektovanih aritmija
    """
    if not arrhythmias:
        return "Normalan ritam"
    
    severity_levels = [arr["severity"] for arr in arrhythmias]
    
    if "high" in severity_levels:
        return "Potrebna medicinska pažnja"
    elif "medium" in severity_levels:
        return "Preporučuje se konsultacija sa lekarom"
    else:
        return "Blage nepravilnosti detektovane"