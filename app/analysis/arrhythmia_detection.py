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
        
        # NOVO: QRS širina analiza
        qrs_analysis = calculate_qrs_width_analysis(filtered_signal, r_peaks, fs)
        
        # DODATO: Napredna QRS morphology analiza
        morphology_analysis = analyze_qrs_morphology_advanced(filtered_signal, r_peaks, fs)
        
        return {
            "r_peaks": r_peaks.tolist(),
            "r_peaks_count": int(len(r_peaks)),
            "heart_rate": heart_rate_analysis,
            "qrs_analysis": qrs_analysis,
            "qrs_morphology": morphology_analysis,  # NOVO: Napredna morphology analiza
            "arrhythmias": arrhythmia_results,
            "signal_quality": assess_signal_quality(filtered_signal),
            "total_duration_seconds": len(signal_array) / fs,
            "detection_method": "signal_analysis_with_morphology"
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

def calculate_qrs_width_analysis(signal, r_peaks, fs):
    """
    Analiza QRS širine korišćenjem Z-transformacije (gradijent analiza)
    
    Algoritam:
    1. Za svaki R-pik, uzmi segment ±100ms
    2. Izračunaj gradijent (Z-transform: y[n] = x[n] - x[n-1])
    3. Pronađi QRS početak i kraj na osnovu threshold-a
    4. Izračunaj QRS širinu u milisekundama
    
    Args:
        signal: Filtriran EKG signal
        r_peaks: Liste pozicija R-pikova
        fs: Frekvencija uzorkovanja
    
    Returns:
        dict: QRS analiza sa širinama i klasifikacijom
    """
    if len(r_peaks) == 0:
        return {"error": "Nema R-pikova za QRS analizu"}
    
    # Parametri
    window_ms = 100  # ±100ms oko R-pika
    window_samples = int(window_ms * fs / 1000)
    threshold_factor = 0.3  # 30% maksimalnog gradijenta
    
    qrs_widths = []
    
    for r_peak in r_peaks:
        try:
            # KORAK 1: Izvuci segment oko R-pika
            start_idx = max(0, r_peak - window_samples)
            end_idx = min(len(signal), r_peak + window_samples)
            segment = signal[start_idx:end_idx]
            
            if len(segment) < 20:  # Premali segment
                continue
            
            # KORAK 2: Z-transformacija - Gradijent (derivacija)
            gradient = np.diff(segment)
            gradient_abs = np.abs(gradient)
            
            # KORAK 3: Adaptivni threshold
            max_gradient = np.max(gradient_abs)
            threshold = max_gradient * threshold_factor
            
            # KORAK 4: Pronađi QRS granice
            r_peak_relative = r_peak - start_idx
            
            # QRS početak (traži unazad od R-pika)
            qrs_start = r_peak_relative
            for i in range(r_peak_relative - 1, max(0, r_peak_relative - window_samples//2), -1):
                if i < len(gradient_abs) and gradient_abs[i] > threshold:
                    qrs_start = i
                else:
                    break
            
            # QRS kraj (traži unapred od R-pika)
            qrs_end = r_peak_relative
            for i in range(r_peak_relative, min(len(gradient_abs), r_peak_relative + window_samples//2)):
                if gradient_abs[i] > threshold:
                    qrs_end = i + 1
                else:
                    break
            
            # KORAK 5: Izračunaj širinu u milisekundama
            qrs_width_samples = qrs_end - qrs_start
            qrs_width_ms = (qrs_width_samples / fs) * 1000
            
            # Validacija (fiziološki opseg: 40-200ms)
            if 40 <= qrs_width_ms <= 200:
                qrs_widths.append(qrs_width_ms)
                
        except Exception as e:
            print(f"QRS width calculation failed for R-peak {r_peak}: {e}")
            continue
    
    if not qrs_widths:
        return {"error": "Nisu pronađene validne QRS širine"}
    
    # KORAK 6: Statistička analiza
    qrs_widths = np.array(qrs_widths)
    mean_qrs = np.mean(qrs_widths)
    
    # KORAK 7: Klinička klasifikacija
    if mean_qrs < 80:
        classification = "Uzak QRS"
        clinical_significance = "Supraventrikularna provenijencija (normalno)"
        severity = "low"
    elif mean_qrs <= 120:
        classification = "Normalan QRS"
        clinical_significance = "Normalno sprovođenje kroz ventrikule"
        severity = "low"
    elif mean_qrs <= 140:
        classification = "Blago proširen QRS"
        clinical_significance = "Moguć blagi poremećaj intraventrikularnskog sprovođenja"
        severity = "medium"
    else:
        classification = "Širok QRS"
        clinical_significance = "Značajan blok intraventrikularnskog sprovođenja"
        severity = "high"
    
    return {
        "mean_width_ms": float(mean_qrs),
        "std_width_ms": float(np.std(qrs_widths)),
        "median_width_ms": float(np.median(qrs_widths)),
        "min_width_ms": float(np.min(qrs_widths)),
        "max_width_ms": float(np.max(qrs_widths)),
        "total_measurements": len(qrs_widths),
        "classification": classification,
        "clinical_significance": clinical_significance,
        "severity": severity,
        "mathematical_method": "Z-transform gradient analysis",
        "valid_qrs_percentage": (len(qrs_widths) / len(r_peaks)) * 100
    }

def analyze_qrs_morphology_advanced(signal_data, r_peaks, fs):
    """
    NAPREDNA QRS MORPHOLOGY ANALIZA
    
    Implementira:
    1. QT interval merenje
    2. ST segment analizu  
    3. P-wave detekciju
    4. QRS axis deviation
    5. T-wave analizu
    
    Args:
        signal_data: Filtrirani EKG signal
        r_peaks: Indeksi R-pikova
        fs: Frekvencija uzorkovanja
    
    Returns:
        dict: Detaljana morphology analiza
    """
    try:
        if len(r_peaks) < 2:
            return {
                "error": "Nedovoljno R-pikova za morphology analizu",
                "r_peaks_available": len(r_peaks)
            }
        
        morphology_results = []
        
        # Analiziraj svaki QRS kompleks
        for i, r_peak in enumerate(r_peaks):
            try:
                qrs_morphology = analyze_single_qrs_complex(signal_data, r_peak, fs, i)
                if "error" not in qrs_morphology:
                    morphology_results.append(qrs_morphology)
            except Exception:
                # Skip problematic complexes
                continue
        
        if not morphology_results:
            return {"error": "Nijedan QRS kompleks nije uspešno analiziran"}
        
        # Agregiraj rezultate
        summary_stats = calculate_morphology_summary(morphology_results)
        
        # Detektuj aritmije na osnovu morphology
        morphology_arrhythmias = detect_morphology_based_arrhythmias(morphology_results, summary_stats)
        
        return {
            "individual_complexes": morphology_results[:5],  # Ograniči na prvih 5 za čitljivost
            "summary_statistics": summary_stats,
            "morphology_arrhythmias": morphology_arrhythmias,
            "complexes_analyzed": len(morphology_results),
            "analysis_method": "advanced_qrs_morphology_analysis"
        }
        
    except Exception as e:
        return {"error": f"QRS morphology analiza neuspešna: {str(e)}"}

def analyze_single_qrs_complex(signal, r_peak, fs, complex_index):
    """
    Analizira jedan QRS kompleks u detalju
    """
    # Definiši prozor oko R-pika (tipično 600ms ukupno)
    window_before = int(0.3 * fs)  # 300ms pre R-pika
    window_after = int(0.3 * fs)   # 300ms posle R-pika
    
    start_idx = max(0, r_peak - window_before)
    end_idx = min(len(signal), r_peak + window_after)
    
    qrs_segment = signal[start_idx:end_idx]
    
    if len(qrs_segment) < 10:
        return {"error": "QRS segment prekratak", "complex_index": complex_index}
    
    # 1. QRS WIDTH MERENJE (poboljšano)
    qrs_width = measure_qrs_width_improved(qrs_segment, fs)
    
    # 2. QT INTERVAL (aproksimativno)
    qt_interval = estimate_qt_interval(qrs_segment, fs)
    
    # 3. ST SEGMENT ANALIZA
    st_analysis = analyze_st_segment(qrs_segment, r_peak - start_idx, fs)
    
    # 4. P-WAVE DETEKCIJA (ako je u prozoru)
    p_wave_analysis = detect_p_wave(qrs_segment, r_peak - start_idx, fs)
    
    # 5. T-WAVE ANALIZA
    t_wave_analysis = analyze_t_wave(qrs_segment, r_peak - start_idx, fs)
    
    # 6. QRS AMPLITUDE I AXIS
    qrs_amplitude_axis = analyze_qrs_amplitude_and_axis(qrs_segment, r_peak - start_idx)
    
    return {
        "complex_index": complex_index,
        "r_peak_position": r_peak,
        "qrs_width_ms": qrs_width,
        "qt_interval_ms": qt_interval,
        "st_segment": st_analysis,
        "p_wave": p_wave_analysis,
        "t_wave": t_wave_analysis,
        "qrs_amplitude_axis": qrs_amplitude_axis,
        "segment_start": start_idx,
        "segment_end": end_idx
    }

def measure_qrs_width_improved(qrs_segment, fs):
    """
    Poboljšano merenje QRS širine korišćenjem derivacije
    """
    try:
        if len(qrs_segment) < 5:
            return 0.0
        
        # Prva derivacija za detekciju onset/offset
        derivative = np.diff(qrs_segment)
        
        # Pronađi indeks R-pika (maksimalna amplituda)
        r_idx = np.argmax(np.abs(qrs_segment))
        
        # Threshold za detekciju onset/offset (10% od max derivacije)
        threshold = np.max(np.abs(derivative)) * 0.1
        
        # QRS onset - unazad od R-pika
        onset_idx = r_idx
        for i in range(r_idx, max(0, r_idx-int(0.1*fs)), -1):
            if i < len(derivative) and abs(derivative[i]) < threshold:
                onset_idx = i
                break
        
        # QRS offset - unapred od R-pika
        offset_idx = r_idx
        for i in range(r_idx, min(len(derivative), r_idx+int(0.1*fs))):
            if abs(derivative[i]) < threshold:
                offset_idx = i
                break
        
        # Konvertuj u milisekunde
        qrs_width_ms = ((offset_idx - onset_idx) / fs) * 1000
        
        return max(0, qrs_width_ms)
        
    except Exception:
        return 0.0

def estimate_qt_interval(qrs_segment, fs):
    """
    Procenjuje QT interval (Q do kraja T-wave)
    """
    try:
        if len(qrs_segment) < int(0.4 * fs):  # Premalo za QT merenje
            return 0.0
        
        # T-wave je obično 160-200ms posle R-pika
        r_idx = np.argmax(np.abs(qrs_segment))
        
        # Traži T-wave peak 100-250ms posle R-pika
        t_start = r_idx + int(0.1 * fs)
        t_end = min(len(qrs_segment), r_idx + int(0.25 * fs))
        
        if t_end <= t_start:
            return 0.0
        
        t_segment = qrs_segment[t_start:t_end]
        
        # T-wave može biti pozitivna ili negativna
        t_peak_idx = t_start + (np.argmax(np.abs(t_segment)))
        
        # QT = od početka QRS do kraja T-wave
        # Aproksimacija: T-wave se završava ~40ms posle T-peak
        qt_end = min(len(qrs_segment)-1, t_peak_idx + int(0.04 * fs))
        
        # QT interval u milisekundama
        qt_interval_ms = (qt_end / fs) * 1000
        
        return qt_interval_ms
        
    except Exception:
        return 0.0

def analyze_st_segment(qrs_segment, r_idx, fs):
    """
    Analizira ST segment za elevaciju/depresiju
    """
    try:
        # ST segment je 80ms posle R-pika
        st_start = r_idx + int(0.08 * fs)
        st_end = min(len(qrs_segment), r_idx + int(0.12 * fs))
        
        if st_end <= st_start or st_start >= len(qrs_segment):
            return {"error": "ST segment van opsega"}
        
        st_values = qrs_segment[st_start:st_end]
        baseline = np.mean(qrs_segment[:max(1, r_idx-int(0.1*fs))])
        
        st_elevation = np.mean(st_values) - baseline
        st_deviation = np.std(st_values)
        
        # Klasifikacija ST promene
        if st_elevation > 0.1:  # >0.1mV elevacija
            st_status = "ST elevacija"
            severity = "high" if st_elevation > 0.2 else "medium"
        elif st_elevation < -0.1:  # >0.1mV depresija
            st_status = "ST depresija"
            severity = "high" if st_elevation < -0.2 else "medium"
        else:
            st_status = "Normalan ST segment"
            severity = "low"
        
        return {
            "st_elevation_mv": float(st_elevation),
            "st_deviation": float(st_deviation),
            "status": st_status,
            "severity": severity,
            "baseline_mv": float(baseline)
        }
        
    except Exception:
        return {"error": "ST analiza neuspešna"}

def detect_p_wave(qrs_segment, r_idx, fs):
    """
    Pokušava da detektuje P-wave pre QRS kompleksa
    """
    try:
        # P-wave je obično 120-200ms pre R-pika
        p_end = max(0, r_idx - int(0.05 * fs))  # 50ms pre R-pika
        p_start = max(0, r_idx - int(0.2 * fs))  # 200ms pre R-pika
        
        if p_end <= p_start:
            return {"detected": False, "reason": "Nedovoljan prozor za P-wave"}
        
        p_segment = qrs_segment[p_start:p_end]
        
        # P-wave detekcija kroz lokalne maksimume
        if len(p_segment) < 5:
            return {"detected": False, "reason": "P segment prekratak"}
        
        # Traži karakteristični P-wave shape (mala pozitivna defleksija)
        p_amplitude = np.max(p_segment) - np.min(p_segment)
        r_amplitude = np.max(qrs_segment) - np.min(qrs_segment)
        
        # P-wave je obično 10-25% od R-wave amplitude
        p_to_r_ratio = p_amplitude / r_amplitude if r_amplitude > 0 else 0
        
        if 0.1 <= p_to_r_ratio <= 0.3:
            p_detected = True
            p_width_ms = (len(p_segment) / fs) * 1000
        else:
            p_detected = False
            p_width_ms = 0
        
        return {
            "detected": p_detected,
            "amplitude_ratio": float(p_to_r_ratio),
            "width_ms": float(p_width_ms),
            "confidence": min(100, p_to_r_ratio * 400) if p_detected else 0
        }
        
    except Exception:
        return {"detected": False, "error": "P-wave detekcija neuspešna"}

def analyze_t_wave(qrs_segment, r_idx, fs):
    """
    Analizira T-wave karakteristike
    """
    try:
        # T-wave region: 120-300ms posle R-pika
        t_start = r_idx + int(0.12 * fs)
        t_end = min(len(qrs_segment), r_idx + int(0.3 * fs))
        
        if t_end <= t_start:
            return {"error": "T-wave region van opsega"}
        
        t_segment = qrs_segment[t_start:t_end]
        
        # T-wave karakteristike
        t_amplitude = np.max(t_segment) - np.min(t_segment)
        t_peak_idx = np.argmax(np.abs(t_segment))
        t_polarity = "positive" if t_segment[t_peak_idx] > 0 else "negative"
        
        # T-wave inverzija (abnormalno)
        baseline = np.mean(qrs_segment[:max(1, r_idx-int(0.1*fs))])
        t_inversion = t_segment[t_peak_idx] < baseline - 0.05  # <-50μV od baseline
        
        return {
            "amplitude": float(t_amplitude),
            "polarity": t_polarity,
            "inverted": bool(t_inversion),
            "peak_position_ms": float((t_peak_idx / fs) * 1000),
            "width_ms": float((len(t_segment) / fs) * 1000)
        }
        
    except Exception:
        return {"error": "T-wave analiza neuspešna"}

def analyze_qrs_amplitude_and_axis(qrs_segment, r_idx):
    """
    Analizira QRS amplitudu i aproksimativni axis
    """
    try:
        # QRS amplitude (peak-to-peak)
        qrs_max = np.max(qrs_segment)
        qrs_min = np.min(qrs_segment)
        qrs_amplitude = qrs_max - qrs_min
        
        # R-wave amplitude (od baseline)
        baseline = np.mean(qrs_segment[:max(1, r_idx-20)])
        r_amplitude = qrs_segment[r_idx] - baseline
        
        # S-wave detekcija (negativna defleksija posle R-pika)
        s_region_start = r_idx + 1
        s_region_end = min(len(qrs_segment), r_idx + 20)
        
        if s_region_end > s_region_start:
            s_region = qrs_segment[s_region_start:s_region_end]
            s_amplitude = baseline - np.min(s_region)  # S-wave depth
        else:
            s_amplitude = 0
        
        # QRS axis aproksimacija (pozitivna ili negativna dominacija)
        if abs(r_amplitude) > abs(s_amplitude):
            axis_deviation = "normal" if r_amplitude > 0 else "left_axis_deviation"
        else:
            axis_deviation = "right_axis_deviation"
        
        return {
            "total_amplitude": float(qrs_amplitude),
            "r_amplitude": float(r_amplitude),
            "s_amplitude": float(s_amplitude),
            "rs_ratio": float(r_amplitude / s_amplitude) if s_amplitude > 0.01 else float('inf'),
            "axis_deviation": axis_deviation,
            "baseline": float(baseline)
        }
        
    except Exception:
        return {"error": "Amplitude analiza neuspešna"}

def calculate_morphology_summary(morphology_results):
    """
    Agregiraj morphology rezultate u summary statistike
    """
    try:
        if not morphology_results:
            return {"error": "Nema rezultata za agregaciju"}
        
        # Ekstraktuj numeričke vrednosti
        qrs_widths = [r.get("qrs_width_ms", 0) for r in morphology_results if r.get("qrs_width_ms", 0) > 0]
        qt_intervals = [r.get("qt_interval_ms", 0) for r in morphology_results if r.get("qt_interval_ms", 0) > 0]
        
        # ST segment analiza
        st_elevations = []
        st_abnormalities = 0
        
        for result in morphology_results:
            st_data = result.get("st_segment", {})
            if "st_elevation_mv" in st_data:
                st_elevations.append(st_data["st_elevation_mv"])
                if abs(st_data["st_elevation_mv"]) > 0.1:
                    st_abnormalities += 1
        
        # P-wave detekcija rate
        p_wave_detected = sum(1 for r in morphology_results 
                             if r.get("p_wave", {}).get("detected", False))
        
        # T-wave inverzije
        t_wave_inversions = sum(1 for r in morphology_results 
                               if r.get("t_wave", {}).get("inverted", False))
        
        return {
            "qrs_width_stats": {
                "mean_ms": float(np.mean(qrs_widths)) if qrs_widths else 0,
                "std_ms": float(np.std(qrs_widths)) if qrs_widths else 0,
                "min_ms": float(np.min(qrs_widths)) if qrs_widths else 0,
                "max_ms": float(np.max(qrs_widths)) if qrs_widths else 0,
                "count": len(qrs_widths)
            },
            "qt_interval_stats": {
                "mean_ms": float(np.mean(qt_intervals)) if qt_intervals else 0,
                "std_ms": float(np.std(qt_intervals)) if qt_intervals else 0,
                "prolonged_count": sum(1 for qt in qt_intervals if qt > 440)  # QT > 440ms
            },
            "st_segment_stats": {
                "mean_elevation_mv": float(np.mean(st_elevations)) if st_elevations else 0,
                "abnormal_count": st_abnormalities,
                "abnormal_percentage": (st_abnormalities / len(morphology_results)) * 100
            },
            "p_wave_stats": {
                "detection_rate": (p_wave_detected / len(morphology_results)) * 100,
                "detected_count": p_wave_detected
            },
            "t_wave_stats": {
                "inversion_count": t_wave_inversions,
                "inversion_rate": (t_wave_inversions / len(morphology_results)) * 100
            },
            "total_complexes": len(morphology_results)
        }
        
    except Exception:
        return {"error": "Summary kalkulacija neuspešna"}

def detect_morphology_based_arrhythmias(morphology_results, summary_stats):
    """
    Detektuj aritmije na osnovu QRS morphology analize
    """
    try:
        detected_arrhythmias = []
        
        # 1. WIDE QRS COMPLEX (Bundle branch block)
        mean_qrs_width = summary_stats.get("qrs_width_stats", {}).get("mean_ms", 0)
        if mean_qrs_width > 120:  # > 120ms = wide QRS
            severity = "high" if mean_qrs_width > 140 else "medium"
            detected_arrhythmias.append({
                "type": "Wide QRS Complex",
                "description": "Mogući bundle branch block ili ventrikularna aritmija",
                "severity": severity,
                "value": f"{mean_qrs_width:.1f} ms",
                "normal_range": "< 120 ms"
            })
        
        # 2. QT PROLONGATION
        qt_stats = summary_stats.get("qt_interval_stats", {})
        mean_qt = qt_stats.get("mean_ms", 0)
        prolonged_count = qt_stats.get("prolonged_count", 0)
        
        if mean_qt > 440 or prolonged_count > 0:
            severity = "high" if mean_qt > 500 else "medium"
            detected_arrhythmias.append({
                "type": "QT Prolongation",
                "description": "Produžen QT interval - rizik od Torsades de Pointes",
                "severity": severity,
                "value": f"{mean_qt:.1f} ms",
                "affected_complexes": prolonged_count,
                "normal_range": "< 440 ms"
            })
        
        # 3. ST SEGMENT ABNORMALITIES
        st_stats = summary_stats.get("st_segment_stats", {})
        st_abnormal_percentage = st_stats.get("abnormal_percentage", 0)
        mean_st_elevation = st_stats.get("mean_elevation_mv", 0)
        
        if st_abnormal_percentage > 30:  # >30% kompleksa ima ST abnormalnosti
            if mean_st_elevation > 0.1:
                arrhythmia_type = "ST Elevation"
                description = "ST elevacija - mogući akutni infarkt miokarda"
                severity = "high"
            elif mean_st_elevation < -0.1:
                arrhythmia_type = "ST Depression"
                description = "ST depresija - mogući ishemija ili strain"
                severity = "medium"
            else:
                arrhythmia_type = "ST Segment Variability"
                description = "Varijabilne ST promene"
                severity = "low"
            
            detected_arrhythmias.append({
                "type": arrhythmia_type,
                "description": description,
                "severity": severity,
                "value": f"{mean_st_elevation:.3f} mV",
                "affected_percentage": f"{st_abnormal_percentage:.1f}%"
            })
        
        # 4. P-WAVE ABNORMALITIES (Atrial arrhythmias)
        p_wave_stats = summary_stats.get("p_wave_stats", {})
        p_detection_rate = p_wave_stats.get("detection_rate", 0)
        
        if p_detection_rate < 70:  # <70% P-wave detekcije
            detected_arrhythmias.append({
                "type": "P-Wave Abnormalities",
                "description": "Nedostaju P-talasi - mogući atrial flutter/fibrillation",
                "severity": "medium",
                "value": f"{p_detection_rate:.1f}% detection rate",
                "normal_range": "> 90%"
            })
        
        # 5. T-WAVE INVERSIONS
        t_wave_stats = summary_stats.get("t_wave_stats", {})
        t_inversion_rate = t_wave_stats.get("inversion_rate", 0)
        
        if t_inversion_rate > 20:  # >20% T-wave inverzija
            detected_arrhythmias.append({
                "type": "T-Wave Inversions",
                "description": "T-wave inverzije - mogući ishemija ili strain",
                "severity": "medium" if t_inversion_rate < 50 else "high",
                "value": f"{t_inversion_rate:.1f}% inverted",
                "affected_count": t_wave_stats.get("inversion_count", 0)
            })
        
        return {
            "detected_morphology_arrhythmias": detected_arrhythmias,
            "total_morphology_issues": len(detected_arrhythmias),
            "analysis_summary": "Morphology-based arrhythmia detection completed",
            "clinical_significance": "high" if any(a["severity"] == "high" for a in detected_arrhythmias) else "medium"
        }
        
    except Exception:
        return {"error": "Morphology arrhythmia detection failed"}