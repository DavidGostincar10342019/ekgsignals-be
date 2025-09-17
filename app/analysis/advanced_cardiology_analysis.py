"""
Napredna kardiološka analiza EKG signala
Implementira sve zahteve za detaljni medicinski izveštaj
"""
import numpy as np
from scipy import signal
from scipy.signal import find_peaks
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import io
import base64

def advanced_ekg_analysis(ekg_signal, fs=250, annotations=None, wfdb_metadata=None):
    """
    Kompletna kardiološka analiza EKG signala
    
    Args:
        ekg_signal: 1D numpy array EKG signala
        fs: Frekvencija uzorkovanja
        annotations: MIT-BIH anotacije ako postoje
        wfdb_metadata: Metapodaci WFDB zapisa
    
    Returns:
        dict: Detaljan kardiološki izveštaj
    """
    signal_array = np.array(ekg_signal, dtype=float)
    
    if len(signal_array) == 0:
        return {"error": "Prazan signal"}
    
    # Predobrada signala
    filtered_signal = advanced_preprocess_ekg(signal_array, fs)
    
    # Detekcija R-pikova
    r_peaks = detect_r_peaks_advanced(filtered_signal, fs)
    
    # Opšte informacije
    general_info = get_general_info(signal_array, fs, wfdb_metadata)
    
    # Detaljne MIT-BIH anotacije
    annotation_analysis = analyze_annotations(annotations) if annotations else None
    
    # Analiza R-pikova sa poređenjem
    r_peak_analysis = analyze_r_peaks_detailed(r_peaks, annotations, fs)
    
    # Detaljan srčani ritam
    heart_rate_analysis = analyze_heart_rate_detailed(r_peaks, fs)
    
    # Napredni HRV parametri
    hrv_analysis = analyze_hrv_advanced(r_peaks, fs)
    
    # Detaljne aritmije
    arrhythmia_analysis = analyze_arrhythmias_detailed(r_peaks, signal_array, fs, annotations)
    
    # Kvalitet signala sa filtrima
    signal_quality = assess_signal_quality_detailed(signal_array, filtered_signal, fs)
    
    # Frekvencijska analiza
    freq_analysis = analyze_frequency_detailed(signal_array, fs)
    
    # Vizuelizacije
    visualizations = generate_visualizations(signal_array, filtered_signal, r_peaks, fs)
    
    # Convert numpy types to Python native types for JSON serialization
    def convert_numpy_types(obj):
        if isinstance(obj, dict):
            return {k: convert_numpy_types(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_numpy_types(item) for item in obj]
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return obj
    
    result = {
        "general_info": general_info,
        "annotation_analysis": annotation_analysis,
        "r_peak_analysis": r_peak_analysis,
        "heart_rate_analysis": heart_rate_analysis,
        "hrv_analysis": hrv_analysis,
        "arrhythmia_analysis": arrhythmia_analysis,
        "signal_quality": signal_quality,
        "frequency_analysis": freq_analysis,
        "visualizations": visualizations
    }
    
    return convert_numpy_types(result)

def get_general_info(signal_array, fs, wfdb_metadata=None):
    """📁 OPŠTE INFORMACIJE"""
    total_samples = len(signal_array)
    duration_seconds = total_samples / fs
    duration_minutes = duration_seconds / 60
    
    info = {
        "analyzed_samples": total_samples,
        "analyzed_duration_seconds": duration_seconds,
        "analyzed_duration_minutes": duration_minutes,
        "sampling_frequency": fs,
        "channels_used": "Kanal 0 (glavni EKG kanal)",
        "signal_source": "analizirani segment"
    }
    
    if wfdb_metadata:
        total_original_samples = wfdb_metadata.get('original_samples', total_samples)
        original_duration = total_original_samples / fs
        
        info.update({
            "total_original_samples": total_original_samples,
            "total_original_duration_minutes": original_duration / 60,
            "segment_percentage": (total_samples / total_original_samples) * 100,
            "n_channels_total": wfdb_metadata.get('n_signals', 1),
            "record_name": wfdb_metadata.get('record_name', 'Unknown')
        })
    
    return info

def analyze_annotations(annotations):
    """📍 ANOTACIJE (.atr fajl)"""
    if not annotations:
        return None
    
    # Tipovi MIT-BIH anotacija
    annotation_types = {}
    r_peak_annotations = 0
    arrhythmia_annotations = 0
    
    # Klasifikacija tipova anotacija
    arrhythmia_codes = ['V', 'A', 'L', 'R', 'P', 'S', 'E', 'j', 'F']
    
    for ann in annotations.get('symbols', []):
        ann_type = str(ann)
        annotation_types[ann_type] = annotation_types.get(ann_type, 0) + 1
        
        if ann_type in ['N', '.']:  # Normalni R-pikovi
            r_peak_annotations += 1
        elif ann_type in arrhythmia_codes:
            arrhythmia_annotations += 1
    
    return {
        "total_annotations": len(annotations.get('symbols', [])),
        "r_peak_annotations": r_peak_annotations,
        "arrhythmia_annotations": arrhythmia_annotations,
        "annotation_types": annotation_types,
        "detailed_list": list(annotation_types.keys()),
        "source_file": annotations.get('source_file', 'N/A')
    }

def analyze_r_peaks_detailed(r_peaks, annotations, fs):
    """📈 DETEKCIJA R-PIKOVA"""
    detected_count = len(r_peaks)
    
    analysis = {
        "detected_count": detected_count,
        "detection_method": "Scipy find_peaks sa prominence i distance kriterijumima",
        "detection_parameters": {
            "min_distance_ms": 300,
            "height_threshold": "1.5 × std",
            "prominence": 0.5
        }
    }
    
    if annotations and 'samples' in annotations:
        annotated_count = len(annotations['samples'])
        
        # Poklapanje - tolerancija od 50ms
        tolerance_samples = int(0.05 * fs)  # 50ms
        matched_peaks = 0
        
        for detected in r_peaks:
            for annotated in annotations['samples']:
                if abs(detected - annotated) <= tolerance_samples:
                    matched_peaks += 1
                    break
        
        accuracy = (matched_peaks / max(detected_count, annotated_count)) * 100 if max(detected_count, annotated_count) > 0 else 0
        
        analysis.update({
            "annotated_count": annotated_count,
            "matched_peaks": matched_peaks,
            "detection_accuracy_percent": accuracy,
            "false_positives": max(0, detected_count - matched_peaks),
            "false_negatives": max(0, annotated_count - matched_peaks),
            "tolerance_ms": 50,
            "comparison_note": f"Poređenje sa MIT-BIH 'zlatnim standardom' (.atr fajl)"
        })
    
    return analysis

def analyze_heart_rate_detailed(r_peaks, fs):
    """🫀 SRČANI RITAM"""
    if len(r_peaks) < 2:
        return {"error": "Nedovoljno R-pikova za analizu"}
    
    # RR intervali
    rr_intervals = np.diff(r_peaks) / fs
    rr_intervals_ms = rr_intervals * 1000
    
    # Srčana frekvencija
    heart_rates = 60.0 / rr_intervals
    
    # Statistike
    avg_hr = np.mean(heart_rates)
    min_hr = np.min(heart_rates)
    max_hr = np.max(heart_rates)
    
    # RR statistike
    avg_rr = np.mean(rr_intervals_ms)
    min_rr = np.min(rr_intervals_ms)
    max_rr = np.max(rr_intervals_ms)
    
    # Validacija da li se frekvencija poklapa sa brojem otkucaja
    total_duration_min = (r_peaks[-1] - r_peaks[0]) / fs / 60
    calculated_beats = len(r_peaks) - 1
    expected_beats_from_avg_hr = avg_hr * total_duration_min
    beat_validation = abs(calculated_beats - expected_beats_from_avg_hr) / expected_beats_from_avg_hr * 100
    
    return {
        "average_bpm": avg_hr,
        "min_bpm": min_hr,
        "max_bpm": max_hr,
        "total_beats": calculated_beats,
        "avg_rr_ms": avg_rr,
        "min_rr_ms": min_rr,
        "max_rr_ms": max_rr,
        "rr_intervals": rr_intervals.tolist(),
        "beat_validation_error_percent": beat_validation,
        "validation_note": "Poređenje broja otkucaja sa prosečnom frekvencijom" if beat_validation < 5 else "PAŽNJA: Neslaganje broja otkucaja i frekvencije",
        "analysis_duration_minutes": total_duration_min
    }

def analyze_hrv_advanced(r_peaks, fs):
    """📉 HRV (Heart Rate Variability)"""
    if len(r_peaks) < 3:
        return {"error": "Nedovoljno R-pikova za HRV analizu"}
    
    # RR intervali u milisekundama
    rr_intervals = np.diff(r_peaks) / fs * 1000
    
    # Time domain parametri
    sdrr = np.std(rr_intervals)  # Standard deviation RR
    rmssd = np.sqrt(np.mean(np.diff(rr_intervals) ** 2))  # Root mean square of successive differences
    
    # pNN50 - procenat uzastopnih RR intervala koji se razlikuju više od 50ms
    successive_diffs = np.abs(np.diff(rr_intervals))
    nn50 = np.sum(successive_diffs > 50)
    pnn50 = (nn50 / len(successive_diffs)) * 100 if len(successive_diffs) > 0 else 0
    
    # Interpretacije
    sdrr_interpretation = get_sdrr_interpretation(sdrr)
    rmssd_interpretation = get_rmssd_interpretation(rmssd)
    pnn50_interpretation = get_pnn50_interpretation(pnn50)
    
    return {
        "sdrr_ms": sdrr,
        "rmssd_ms": rmssd,
        "pnn50_percent": pnn50,
        "nn50_count": nn50,
        "total_rr_intervals": len(rr_intervals),
        "method": "Time-domain HRV analiza",
        "beats_used": len(r_peaks),
        "interpretations": {
            "sdrr": sdrr_interpretation,
            "rmssd": rmssd_interpretation,
            "pnn50": pnn50_interpretation
        },
        "overall_hrv_assessment": get_overall_hrv_assessment(sdrr, rmssd, pnn50)
    }

def analyze_arrhythmias_detailed(r_peaks, signal_array, fs, annotations=None):
    """⚠️ ARITMIJE"""
    if len(r_peaks) < 3:
        return {"error": "Nedovoljno podataka za analizu aritmija"}
    
    rr_intervals = np.diff(r_peaks) / fs
    heart_rates = 60.0 / rr_intervals
    avg_hr = np.mean(heart_rates)
    
    detected_arrhythmias = []
    
    # 1. Bradikardija/Tahikardija sa kriterijumima
    if avg_hr < 60:
        severity = "low" if avg_hr > 50 else ("medium" if avg_hr > 40 else "high")
        detected_arrhythmias.append({
            "type": "Bradikardija",
            "description": f"Spor srčani ritam (kriterijum: <60 bpm)",
            "severity": severity,
            "value": f"{avg_hr:.1f} bpm",
            "criteria": "WHO definicija bradikardije"
        })
    elif avg_hr > 100:
        severity = "medium" if avg_hr < 150 else "high"
        detected_arrhythmias.append({
            "type": "Tahikardija",
            "description": f"Brz srčani ritam (kriterijum: >100 bpm)",
            "severity": severity,
            "value": f"{avg_hr:.1f} bpm",
            "criteria": "WHO definicija tahikardije"
        })
    
    # 2. Analiza propuštenih otkucaja
    median_rr = np.median(rr_intervals)
    long_intervals = rr_intervals > (median_rr * 1.8)
    missed_beats = np.sum(long_intervals)
    
    if missed_beats > 0:
        detected_arrhythmias.append({
            "type": "Propušteni otkucaji",
            "description": f"RR intervali duži od {median_rr * 1.8:.3f}s",
            "severity": "medium" if missed_beats < 5 else "high",
            "value": f"{missed_beats} dugih intervala",
            "criteria": "RR > 1.8 × medijan RR"
        })
    
    # 3. Sekventni ventrikularni otkucaji (ako imamo anotacije)
    ventricular_sequences = 0
    if annotations and 'symbols' in annotations:
        v_beats = [i for i, sym in enumerate(annotations['symbols']) if str(sym) == 'V']
        sequences = []
        current_seq = []
        
        for i in range(len(v_beats) - 1):
            if v_beats[i+1] - v_beats[i] == 1:  # Uzastopni
                if not current_seq:
                    current_seq = [v_beats[i]]
                current_seq.append(v_beats[i+1])
            else:
                if len(current_seq) >= 2:
                    sequences.append(current_seq)
                current_seq = []
        
        if len(current_seq) >= 2:
            sequences.append(current_seq)
        
        ventricular_sequences = len(sequences)
        
        if ventricular_sequences > 0:
            detected_arrhythmias.append({
                "type": "Ventrikularni salvei",
                "description": f"Sekvence od ≥2 uzastopna V otkucaja",
                "severity": "high",
                "value": f"{ventricular_sequences} sekvenci",
                "criteria": "MIT-BIH anotacije (V type)"
            })
    
    return {
        "detected": detected_arrhythmias,
        "total_count": len(detected_arrhythmias),
        "missed_beats_analysis": {
            "threshold_seconds": median_rr * 1.8,
            "detected_long_intervals": int(missed_beats),
            "percentage_of_intervals": (missed_beats / len(rr_intervals)) * 100
        },
        "ventricular_sequences": ventricular_sequences,
        "analysis_basis": "RR intervali iz detektovanih R-pikova + MIT-BIH anotacije",
        "overall_assessment": get_overall_arrhythmia_assessment(detected_arrhythmias)
    }

def assess_signal_quality_detailed(original_signal, filtered_signal, fs):
    """📶 KVALITET SIGNALA"""
    # SNR analiza
    signal_power = np.var(filtered_signal)
    
    # Šum kroz high-pass filter
    nyquist = fs / 2
    b_noise, a_noise = signal.butter(4, 40/nyquist, btype='high')
    noise = signal.filtfilt(b_noise, a_noise, original_signal)
    noise_power = np.var(noise)
    
    snr = 10 * np.log10(signal_power / noise_power) if noise_power > 0 else 100
    
    # Baseline wander detekcija
    b_low, a_low = signal.butter(2, 0.5/nyquist, btype='low')
    baseline = signal.filtfilt(b_low, a_low, original_signal)
    baseline_drift = np.std(baseline)
    
    # Artefakt detekcija (nagle promene)
    gradient = np.gradient(original_signal)
    artifacts = np.sum(np.abs(gradient) > 5 * np.std(gradient))
    
    return {
        "snr_db": snr,
        "signal_power": signal_power,
        "noise_power": noise_power,
        "baseline_drift": baseline_drift,
        "artifacts_detected": artifacts,
        "filters_applied": [
            "Bandpass 0.5-40 Hz (main EKG band)",
            "High-pass 0.5 Hz (baseline removal)"
        ],
        "quality_assessment": get_quality_assessment(snr, baseline_drift, artifacts),
        "noise_level": "Nizak" if snr > 20 else ("Umeren" if snr > 10 else "Visok")
    }

def analyze_frequency_detailed(signal_array, fs):
    """🔬 FREKVENCIJSKA ANALIZA"""
    # Ukloni DC komponentu
    signal_no_dc = signal_array - np.mean(signal_array)
    
    # FFT
    n = len(signal_no_dc)
    freq = np.fft.rfftfreq(n, d=1.0/fs)
    spectrum = np.abs(np.fft.rfft(signal_no_dc)) / n
    
    # Pronađi peak u fiziološkom opsegu (0.5-5 Hz)
    physio_mask = (freq >= 0.5) & (freq <= 5.0)
    if np.any(physio_mask):
        physio_spectrum = spectrum.copy()
        physio_spectrum[~physio_mask] = 0
        peak_idx = np.argmax(physio_spectrum)
    else:
        peak_idx = np.argmax(spectrum[1:]) + 1  # Skip DC
    
    peak_freq = freq[peak_idx]
    peak_amp = spectrum[peak_idx]
    
    # Energija u različitim frekvencijskim bendovima
    energy_bands = {
        "very_low": (0.003, 0.04),
        "low": (0.04, 0.15),
        "normal": (0.15, 0.4),
        "high": (0.4, 2.0)
    }
    
    band_energies = {}
    for band_name, (low_f, high_f) in energy_bands.items():
        band_mask = (freq >= low_f) & (freq <= high_f)
        band_energies[band_name] = np.sum(spectrum[band_mask] ** 2)
    
    return {
        "peak_frequency_hz": peak_freq,
        "peak_amplitude": peak_amp,
        "dc_component_removed": True,
        "analyzed_range_hz": [freq[1], freq[-1]],
        "physiological_range": "0.5-5.0 Hz",
        "band_energies": band_energies,
        "dominant_band": max(band_energies, key=band_energies.get),
        "frequency_interpretation": get_frequency_interpretation(peak_freq)
    }

def generate_visualizations(signal_array, filtered_signal, r_peaks, fs):
    """📊 VIZUELIZACIJE"""
    visualizations = {}
    
    # 1. Signal sa R-pikovima
    fig1, ax1 = plt.subplots(figsize=(12, 4))
    time_axis = np.arange(len(signal_array)) / fs
    ax1.plot(time_axis, filtered_signal, 'b-', linewidth=1, label='Filtriran EKG')
    ax1.plot(time_axis[r_peaks], filtered_signal[r_peaks], 'ro', markersize=6, label=f'R-pikovi ({len(r_peaks)})')
    ax1.set_xlabel('Vreme (s)')
    ax1.set_ylabel('Amplituda')
    ax1.set_title('EKG Signal sa Detektovanim R-pikovima')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    visualizations['signal_with_peaks'] = fig_to_base64(fig1)
    plt.close(fig1)
    
    # 2. Histogram RR intervala
    if len(r_peaks) > 1:
        rr_intervals = np.diff(r_peaks) / fs * 1000  # ms
        fig2, ax2 = plt.subplots(figsize=(8, 5))
        ax2.hist(rr_intervals, bins=30, alpha=0.7, color='green', edgecolor='black')
        ax2.axvline(np.mean(rr_intervals), color='red', linestyle='--', label=f'Prosek: {np.mean(rr_intervals):.1f} ms')
        ax2.set_xlabel('RR Interval (ms)')
        ax2.set_ylabel('Frekvencija')
        ax2.set_title('Distribucija RR Intervala')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        visualizations['rr_histogram'] = fig_to_base64(fig2)
        plt.close(fig2)
        
        # 3. Srčana frekvencija kroz vreme
        heart_rates = 60.0 / (rr_intervals / 1000)
        fig3, ax3 = plt.subplots(figsize=(10, 4))
        time_hr = time_axis[r_peaks[1:]]  # Vreme za svaki RR interval
        ax3.plot(time_hr, heart_rates, 'g-', linewidth=2, marker='o', markersize=4)
        ax3.axhline(np.mean(heart_rates), color='red', linestyle='--', label=f'Prosek: {np.mean(heart_rates):.1f} bpm')
        ax3.set_xlabel('Vreme (s)')
        ax3.set_ylabel('Srčana frekvencija (bpm)')
        ax3.set_title('Srčana Frekvencija Kroz Vreme')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        visualizations['heart_rate_trend'] = fig_to_base64(fig3)
        plt.close(fig3)
        
        # 4. Poincaré dijagram HRV
        if len(rr_intervals) > 1:
            fig4, ax4 = plt.subplots(figsize=(6, 6))
            rr1 = rr_intervals[:-1]
            rr2 = rr_intervals[1:]
            ax4.scatter(rr1, rr2, alpha=0.6, s=20)
            ax4.plot([min(rr_intervals), max(rr_intervals)], [min(rr_intervals), max(rr_intervals)], 'r--', alpha=0.5)
            ax4.set_xlabel('RR(n) (ms)')
            ax4.set_ylabel('RR(n+1) (ms)')
            ax4.set_title('Poincaré Dijagram HRV')
            ax4.grid(True, alpha=0.3)
            ax4.set_aspect('equal')
            visualizations['poincare_plot'] = fig_to_base64(fig4)
            plt.close(fig4)
    
    return visualizations

def fig_to_base64(fig):
    """Konvertuje matplotlib figuru u base64 string"""
    buffer = io.BytesIO()
    fig.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.getvalue()).decode()
    buffer.close()
    return image_base64

# Helper funkcije za interpretacije
def get_sdrr_interpretation(sdrr):
    if sdrr < 20: return "Niska varijabilnost (mogući stres ili bolest)"
    elif sdrr < 50: return "Normalna varijabilnost"
    else: return "Visoka varijabilnost (dobra autonomna regulacija)"

def get_rmssd_interpretation(rmssd):
    if rmssd < 15: return "Smanjena parasimpatička aktivnost"
    elif rmssd < 40: return "Normalna parasimpatička aktivnost" 
    else: return "Povećana parasimpatička aktivnost"

def get_pnn50_interpretation(pnn50):
    if pnn50 < 3: return "Smanjena varijabilnost kratkoročnih promena"
    elif pnn50 < 15: return "Normalna varijabilnost"
    else: return "Povećana varijabilnost kratkoročnih promena"

def get_overall_hrv_assessment(sdrr, rmssd, pnn50):
    score = 0
    if sdrr >= 20: score += 1
    if rmssd >= 15: score += 1
    if pnn50 >= 3: score += 1
    
    if score == 3: return "Odlična HRV - zdravo srce"
    elif score == 2: return "Dobra HRV - normalna varijabilnost"
    elif score == 1: return "Umerena HRV - moguće poboljšanje"
    else: return "Niska HRV - preporučuje se konsultacija"

def get_frequency_interpretation(freq):
    if freq < 0.5: return "Vrlo niska frekvencija - mogući problem"
    elif 0.8 <= freq <= 2.0: return f"Normalna srčana frekvencija ({freq*60:.0f} bpm ekvivalent)"
    elif freq > 2.0: return f"Povišena frekvencija ({freq*60:.0f} bpm ekvivalent)"
    else: return f"Frekvencija van tipičnog EKG opsega ({freq*60:.0f} bpm)"

def get_quality_assessment(snr, baseline_drift, artifacts):
    score = 0
    if snr > 15: score += 2
    elif snr > 8: score += 1
    
    if baseline_drift < 0.1: score += 1
    if artifacts < 10: score += 1
    
    if score >= 4: return "Odličan kvalitet signala"
    elif score >= 3: return "Dobar kvalitet signala"
    elif score >= 2: return "Umeren kvalitet signala"
    else: return "Loš kvalitet signala"

def get_overall_arrhythmia_assessment(arrhythmias):
    if not arrhythmias: return "Normalan srčani ritam"
    
    severity_levels = [arr["severity"] for arr in arrhythmias]
    if "high" in severity_levels: return "Ozbiljne aritmije - hitna medicinska pažnja"
    elif "medium" in severity_levels: return "Umerene aritmije - konsultacija sa kardiologom"
    else: return "Blage nepravilnosti - redovna kontrola"

def advanced_preprocess_ekg(signal_data, fs):
    """Napredna predobrada EKG signala"""
    # Multi-stage filtriranje
    nyquist = fs / 2
    
    # 1. Bandpass filter 0.5-40 Hz
    b1, a1 = signal.butter(4, [0.5/nyquist, 40/nyquist], btype='band')
    filtered = signal.filtfilt(b1, a1, signal_data)
    
    # 2. Notch filter na 50Hz (mrežni šum)
    if fs > 100:
        b2, a2 = signal.iirnotch(50, 30, fs)
        filtered = signal.filtfilt(b2, a2, filtered)
    
    # 3. Dodatno baseline removal
    b3, a3 = signal.butter(2, 0.5/nyquist, btype='high')
    filtered = signal.filtfilt(b3, a3, filtered)
    
    return filtered

def detect_r_peaks_advanced(signal_data, fs):
    """Napredna detekcija R-pikova sa adaptivnim pragom"""
    # Normalizacija
    normalized = (signal_data - np.mean(signal_data)) / np.std(signal_data)
    
    # Adaptivni prag na osnovu lokalne statistike
    window_size = int(2 * fs)  # 2 sekunde
    adaptive_threshold = []
    
    for i in range(0, len(normalized), window_size//2):
        window = normalized[i:i+window_size]
        if len(window) > 0:
            threshold = np.std(window) * 1.2
            adaptive_threshold.extend([threshold] * min(window_size//2, len(normalized)-i))
    
    # Dopuni do kraja ako je potrebno
    while len(adaptive_threshold) < len(normalized):
        adaptive_threshold.append(adaptive_threshold[-1])
    
    adaptive_threshold = np.array(adaptive_threshold)
    
    # Detekcija sa adaptivnim pragom
    peaks, properties = find_peaks(
        normalized,
        height=adaptive_threshold,
        distance=int(0.3 * fs),  # Min 300ms
        prominence=0.3,
        width=int(0.02 * fs)  # Min 20ms širine
    )
    
    return peaks