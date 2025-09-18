import numpy as np

def analyze_fft(signal, fs):
    """
    FFT analiza EKG signala sa uklanjanjem DC komponente - POBOLJŠANA VERZIJA
    """
    x = np.array(signal, dtype=float)
    n = len(x)
    
    # NUMERIČKA ZAŠTITA: Provjera dužine signala
    if n == 0:
        return {"error": "empty signal"}
    elif n == 1:
        return {
            "error": "signal too short for FFT analysis",
            "n": n,
            "fs": fs,
            "peak_frequency_hz": 0.0,
            "peak_amplitude": float(abs(x[0])),
            "dc_component": float(x[0]),
            "total_power": 0.0,
            "frequency_range_hz": [0.0, 0.0],
            "physiological_range_analyzed": "Signal prekratak za frekvencijsku analizu",
            "dc_removed": False,
            "sine_wave_analysis": {"error": "Signal prekratak za harmonijsku analizu"}
        }
    
    # DODATO: Ukloni DC komponentu (srednju vrednost)
    x_no_dc = x - np.mean(x)
    
    freq = np.fft.rfftfreq(n, d=1.0/fs)
    spectrum = np.abs(np.fft.rfft(x_no_dc)) / n
    
    # NUMERIČKA ZAŠTITA: Provjera da spectrum nije prazan
    if len(spectrum) <= 1:
        return {
            "error": "insufficient frequency resolution",
            "n": n,
            "fs": fs,
            "peak_frequency_hz": 0.0,
            "peak_amplitude": float(spectrum[0]) if len(spectrum) > 0 else 0.0,
            "dc_component": float(np.mean(x)),
            "total_power": 0.0,
            "frequency_range_hz": [0.0, 0.0],
            "physiological_range_analyzed": "Nedovoljna frekvencijska rezolucija",
            "dc_removed": True,
            "sine_wave_analysis": {"error": "Nedovoljna frekvencijska rezolucija"}
        }
    
    # POBOLJŠANO: Ignoriši DC komponentu (freq[0] = 0 Hz) i traži peak u fiziološkom opsegu
    min_freq_idx = 1  # Preskoči DC (0 Hz)
    max_freq_idx = len(freq) - 1
    
    # Ograniči na fiziološki opseg (0.5-5 Hz za EKG)
    physiological_mask = (freq >= 0.5) & (freq <= 5.0)
    
    if np.any(physiological_mask):
        # Traži peak u fiziološkom opsegu
        physiological_spectrum = spectrum.copy()
        physiological_spectrum[~physiological_mask] = 0
        peak_idx = int(np.argmax(physiological_spectrum))
    else:
        # Fallback: traži peak posle DC komponente
        if len(spectrum) > min_freq_idx:
            peak_idx = int(np.argmax(spectrum[min_freq_idx:])) + min_freq_idx
        else:
            peak_idx = 0
    
    # Dodatne informacije o spektru
    total_power = np.sum(spectrum[1:] ** 2) if len(spectrum) > 1 else 0.0
    dc_component = spectrum[0] if len(spectrum) > 0 else 0.0
    
    # NOVO: Sine Wave analiza
    sine_wave_analysis = analyze_sine_wave_components(x_no_dc, fs, freq, spectrum)
    
    return {
        "n": n,
        "fs": fs,
        "peak_frequency_hz": float(freq[peak_idx]) if peak_idx < len(freq) else 0.0,
        "peak_amplitude": float(spectrum[peak_idx]) if peak_idx < len(spectrum) else 0.0,
        "dc_component": float(dc_component),
        "total_power": float(total_power),
        "frequency_range_hz": [float(freq[1]), float(freq[-1])] if len(freq) > 1 else [0.0, 0.0],
        "physiological_range_analyzed": "0.5-5.0 Hz (fiziološki opseg za EKG)",
        "dc_removed": True,
        "sine_wave_analysis": sine_wave_analysis,
        "numerical_stability": "Enhanced with edge case protection"
    }

def analyze_sine_wave_components(signal, fs, freq, spectrum):
    """
    Analiza sinusoidalnih komponenti korišćenjem Furijeove transformacije
    
    Implementira:
    1. Harmonijsku analizu - detekcija čistih sinusoidalnih komponenti
    2. THD (Total Harmonic Distortion) računanje
    3. Klasifikaciju signala kao sine-wave ili complex
    4. Detekciju dominantnih harmonika
    
    Args:
        signal: Signal bez DC komponente
        fs: Frekvencija uzorkovanja  
        freq: Frekvencijski binovi iz FFT
        spectrum: Magnitude spektar iz FFT
    
    Returns:
        dict: Sine wave analiza sa harmonijskim komponentama
    """
    try:
        # KORAK 1: Pronađi dominantnu frekvenciju i njene harmonike
        fundamental_idx = np.argmax(spectrum[1:]) + 1  # Skip DC
        fundamental_freq = freq[fundamental_idx]
        fundamental_amp = spectrum[fundamental_idx]
        
        # KORAK 2: Detekcija harmonika (2f, 3f, 4f, 5f)
        harmonics = []
        harmonic_amplitudes = []
        
        for h in range(2, 6):  # 2nd do 5th harmonic
            harmonic_freq = fundamental_freq * h
            if harmonic_freq >= freq[-1]:  # Van Nyquist opsega
                break
                
            # Pronađi najbliži bin
            harmonic_idx = np.argmin(np.abs(freq - harmonic_freq))
            harmonic_amp = spectrum[harmonic_idx]
            
            # Threshold za validne harmonike
            if harmonic_amp > fundamental_amp * 0.05:  # 5% od fundamentalne
                harmonics.append({
                    "order": h,
                    "frequency_hz": float(freq[harmonic_idx]),
                    "amplitude": float(harmonic_amp),
                    "amplitude_ratio": float(harmonic_amp / fundamental_amp)
                })
                harmonic_amplitudes.append(harmonic_amp)
        
        # KORAK 3: THD (Total Harmonic Distortion) računanje
        if harmonic_amplitudes:
            harmonic_power = sum(amp**2 for amp in harmonic_amplitudes)
            fundamental_power = fundamental_amp**2
            thd_percent = (np.sqrt(harmonic_power) / fundamental_amp) * 100
        else:
            thd_percent = 0.0
        
        # KORAK 4: Spectral Purity Index (SPI)
        # Meri koliko je signal blizu čistom sinusu
        total_power_excluding_dc = np.sum(spectrum[1:]**2)
        fundamental_power_ratio = (fundamental_amp**2) / total_power_excluding_dc
        spectral_purity = fundamental_power_ratio * 100  # Procenat
        
        # KORAK 5: Klasifikacija signala
        if spectral_purity > 80 and thd_percent < 5:
            signal_type = "Čist sinusni signal"
            sine_wave_confidence = "visoka"
            clinical_interpretation = "Signal ima dominantnu sinusoidalnu komponentu - tipično za regularni ritam"
        elif spectral_purity > 60 and thd_percent < 15:
            signal_type = "Pretežno sinusni signal"
            sine_wave_confidence = "umerena"
            clinical_interpretation = "Signal ima jaku sinusoidalnu komponentu sa manjim harmonicima"
        elif spectral_purity > 40:
            signal_type = "Kompleksan signal sa sinusnim komponentama"
            sine_wave_confidence = "niska"
            clinical_interpretation = "Signal ima više frekvencijskih komponenti - složeniji EKG pattern"
        else:
            signal_type = "Kompleksan multi-spektralni signal"
            sine_wave_confidence = "vrlo niska"
            clinical_interpretation = "Signal ima širok frekvencijski sadržaj - mogući šum ili aritmija"
        
        # KORAK 6: Harmonic-to-Noise Ratio (HNR)
        if len(harmonics) > 0:
            harmonic_power_total = fundamental_power + sum(h["amplitude"]**2 for h in harmonics)
            noise_power = total_power_excluding_dc - harmonic_power_total
            if noise_power > 0:
                hnr_db = 10 * np.log10(harmonic_power_total / noise_power)
            else:
                hnr_db = float('inf')
        else:
            hnr_db = 10 * np.log10(fundamental_power / (total_power_excluding_dc - fundamental_power))
        
        return {
            "fundamental_frequency_hz": float(fundamental_freq),
            "fundamental_amplitude": float(fundamental_amp),
            "detected_harmonics": harmonics,
            "total_harmonics_count": len(harmonics),
            "thd_percent": float(thd_percent),
            "spectral_purity_percent": float(spectral_purity),
            "signal_classification": signal_type,
            "sine_wave_confidence": sine_wave_confidence,
            "clinical_interpretation": clinical_interpretation,
            "harmonic_to_noise_ratio_db": float(hnr_db) if hnr_db != float('inf') else 100.0,
            "mathematical_method": "Furijeova transformacija sa harmonijskom analizom",
            "frequency_resolution_hz": float(freq[1] - freq[0]),
            "analysis_bandwidth_hz": [float(freq[1]), float(freq[-1])],
            "pure_sine_criteria": {
                "spectral_purity_threshold": "80% (postignuto: {:.1f}%)".format(spectral_purity),
                "thd_threshold": "5% (postignuto: {:.1f}%)".format(thd_percent)
            }
        }
        
    except Exception as e:
        return {
            "error": f"Sine wave analiza neuspešna: {str(e)}",
            "fundamental_frequency_hz": 0,
            "signal_classification": "Nepoznato - greška u analizi"
        }
