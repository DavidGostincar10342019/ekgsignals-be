import numpy as np

def analyze_fft(signal, fs):
    """
    FFT analiza EKG signala sa uklanjanjem DC komponente
    """
    x = np.array(signal, dtype=float)
    n = len(x)
    if n == 0:
        return {"error": "empty signal"}
    
    # DODATO: Ukloni DC komponentu (srednju vrednost)
    x_no_dc = x - np.mean(x)
    
    freq = np.fft.rfftfreq(n, d=1.0/fs)
    spectrum = np.abs(np.fft.rfft(x_no_dc)) / n
    
    # POBOLJŠANO: Ignoriši DC komponentu (freq[0] = 0 Hz) i traži peak u fiziološkom opsegu
    # EKG srčana frekvencija je tipično 0.8-3 Hz (48-180 bpm)
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
        peak_idx = int(np.argmax(spectrum[min_freq_idx:])) + min_freq_idx
    
    # Dodatne informacije o spektru
    total_power = np.sum(spectrum[1:] ** 2)  # Ukupna snaga bez DC
    dc_component = spectrum[0]  # DC komponenta
    
    return {
        "n": n,
        "fs": fs,
        "peak_frequency_hz": float(freq[peak_idx]),
        "peak_amplitude": float(spectrum[peak_idx]),
        "dc_component": float(dc_component),
        "total_power": float(total_power),
        "frequency_range_hz": [float(freq[1]), float(freq[-1])],
        "physiological_range_analyzed": "0.5-5.0 Hz (fiziološki opseg za EKG)",
        "dc_removed": True
    }
