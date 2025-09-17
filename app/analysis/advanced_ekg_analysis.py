"""
Napredna EKG analiza bazirana na naučnim radovima:
- Faust et al. (2004): Spatial Filling Index i time-frequency analiza
- Proakis & Manolakis (2007): Napredni DSP algoritmi
- Sörnmo & Laguna (2005): Specijalizovana EKG obrada
- Yıldırım (2018): Wavelet sekvence i deep learning pristup
"""

import numpy as np
from scipy import signal
from scipy.signal import find_peaks, butter, filtfilt
try:
    import pywt  # PyWavelets za wavelet transformacije
    PYWT_AVAILABLE = True
except ImportError:
    PYWT_AVAILABLE = False
    print("Warning: PyWavelets not available. Using simplified wavelet analysis.")
from scipy.stats import entropy
import matplotlib.pyplot as plt
import io
import base64

def spatial_filling_index(ekg_signal):
    """
    Spatial Filling Index (SFI) prema Faust et al. (2004)
    
    SFI = log(N) / log(L/a)
    gde je:
    N - broj tačaka signala
    L - ukupna dužina putanje
    a - prosečna amplituda
    
    Args:
        ekg_signal: 1D numpy array EKG signala
    
    Returns:
        dict: SFI vrednost i komponente
    """
    signal_array = np.array(ekg_signal, dtype=float)
    N = len(signal_array)
    
    # Kalkulacija ukupne dužine putanje (L)
    # L = suma euklidskih rastojanja između uzastopnih tačaka
    diff_signal = np.diff(signal_array)
    L = np.sum(np.sqrt(1 + diff_signal**2))  # sqrt(dx² + dy²) gde je dx=1
    
    # Prosečna amplituda
    a = np.mean(np.abs(signal_array))
    
    # Spatial Filling Index
    if L > 0 and a > 0:
        sfi = np.log(N) / np.log(L/a)
    else:
        sfi = 0
    
    return {
        "spatial_filling_index": float(sfi),
        "total_path_length": float(L),
        "average_amplitude": float(a),
        "signal_points": int(N),
        "formula": "SFI = log(N) / log(L/a)",
        "interpretation": get_sfi_interpretation(sfi)
    }

def get_sfi_interpretation(sfi):
    """Interpretacija SFI vrednosti"""
    if sfi > 1.5:
        return "Visoka kompleksnost - mogući patološki signal"
    elif sfi > 1.2:
        return "Umerena kompleksnost - potrebna dodatna analiza"
    elif sfi > 0.8:
        return "Normalna kompleksnost - zdrav signal"
    else:
        return "Niska kompleksnost - mogući artefakt"

def time_frequency_analysis(ekg_signal, fs=250):
    """
    Time-Frequency analiza prema Faust et al. (2004)
    Koristi Short-Time Fourier Transform (STFT)
    
    Args:
        ekg_signal: 1D numpy array
        fs: sampling frequency
    
    Returns:
        dict: Time-frequency reprezentacija
    """
    signal_array = np.array(ekg_signal, dtype=float)
    
    # STFT parametri
    nperseg = min(256, len(signal_array) // 4)  # Window length
    noverlap = nperseg // 2  # 50% overlap
    
    # Short-Time Fourier Transform
    f, t, Zxx = signal.stft(signal_array, fs=fs, nperseg=nperseg, noverlap=noverlap)
    
    # Power spectral density
    power_spectrum = np.abs(Zxx)**2
    
    # Dominantne frekvencije u vremenu
    dominant_freqs = []
    for i in range(len(t)):
        max_idx = np.argmax(power_spectrum[:, i])
        dominant_freqs.append(f[max_idx])
    
    # Spektralna entropija
    spectral_entropy = []
    for i in range(len(t)):
        psd = power_spectrum[:, i]
        psd_norm = psd / np.sum(psd)
        spectral_entropy.append(entropy(psd_norm))
    
    return {
        "frequencies": f.tolist(),
        "time_points": t.tolist(),
        "power_spectrum": power_spectrum.tolist(),
        "dominant_frequencies": dominant_freqs,
        "spectral_entropy": spectral_entropy,
        "mean_spectral_entropy": float(np.mean(spectral_entropy)),
        "formula": "STFT(x[n]) = Σ x[m]w[n-m]e^(-j2πfm)",
        "interpretation": "Time-frequency reprezentacija pokazuje kako se frekvencijski sadržaj menja kroz vreme"
    }

def wavelet_analysis(ekg_signal, wavelet='db4', levels=6):
    """
    Wavelet analiza prema Yıldırım (2018)
    Fallback verzija ako PyWavelets nije dostupan
    """
    if not PYWT_AVAILABLE:
        return simplified_wavelet_analysis(ekg_signal, levels)
    
    return full_wavelet_analysis(ekg_signal, wavelet, levels)

def simplified_wavelet_analysis(ekg_signal, levels=6, wavelet='db4'):
    """Pojednostavljena wavelet analiza bez PyWavelets"""
    signal_array = np.array(ekg_signal, dtype=float)
    
    # Simulacija wavelet dekompozicije kroz filtriranje
    details = []
    current_signal = signal_array.copy()
    
    for level in range(1, levels + 1):
        # High-pass filter za detail koeficijente
        nyquist = 0.5
        high_freq = 0.5 / (2 ** level)
        if high_freq < nyquist and len(current_signal) > 18:  # Minimum length check
            try:
                b, a = signal.butter(2, high_freq, btype='high')
                detail_coeffs = signal.filtfilt(b, a, current_signal)
            except:
                detail_coeffs = current_signal * 0.1  # Fallback
        else:
            detail_coeffs = current_signal * 0.1  # Minimal coefficients
        
        detail_info = {
            'level': level,
            'coefficients': detail_coeffs.tolist(),
            'energy': float(np.sum(detail_coeffs**2)),
            'mean': float(np.mean(detail_coeffs)),
            'std': float(np.std(detail_coeffs)),
            'max_coeff': float(np.max(np.abs(detail_coeffs)))
        }
        details.append(detail_info)
        
        # Low-pass filter za sledeći nivo
        if high_freq < nyquist and len(current_signal) > 18:  # Minimum length check
            try:
                b, a = signal.butter(2, high_freq, btype='low')
                current_signal = signal.filtfilt(b, a, current_signal)
            except:
                current_signal = current_signal * 0.9  # Fallback
    
    # Approximation koeficijenti
    approximation = {
        'coefficients': current_signal.tolist(),
        'energy': float(np.sum(current_signal**2)),
        'mean': float(np.mean(current_signal)),
        'std': float(np.std(current_signal))
    }
    
    # Wavelet entropija (aproksimacija)
    total_energy = sum([d['energy'] for d in details]) + approximation['energy']
    if total_energy > 0:
        relative_energies = [d['energy']/total_energy for d in details]
        relative_energies.append(approximation['energy']/total_energy)
        wavelet_entropy = -np.sum([e * np.log2(e) for e in relative_energies if e > 0])
    else:
        wavelet_entropy = 0.0
    
    return {
        "wavelet_type": f"simplified_{wavelet}",
        "decomposition_levels": levels,
        "approximation": approximation,
        "details": details,
        "reconstructed_signal": signal_array.tolist(),  # Original signal
        "wavelet_entropy": float(wavelet_entropy),
        "total_energy": float(total_energy),
        "formula": "Simplified WT approximation using cascaded filters",
        "interpretation": get_wavelet_interpretation(wavelet_entropy, details),
        "note": "Using simplified wavelet analysis (PyWavelets not available)"
    }

def full_wavelet_analysis(ekg_signal, wavelet='db4', levels=6):
    """
    Wavelet analiza prema Yıldırım (2018)
    
    Args:
        ekg_signal: 1D numpy array
        wavelet: tip wavelet-a (default: Daubechies 4)
        levels: broj nivoa dekompozicije
    
    Returns:
        dict: Wavelet koeficijenti i analiza
    """
    signal_array = np.array(ekg_signal, dtype=float)
    
    # Wavelet dekompozicija
    coeffs = pywt.wavedec(signal_array, wavelet, level=levels)
    
    # Analiza koeficijenata
    wavelet_features = {}
    
    # Approximation koeficijenti (niske frekvencije)
    cA = coeffs[0]
    wavelet_features['approximation'] = {
        'coefficients': cA.tolist(),
        'energy': float(np.sum(cA**2)),
        'mean': float(np.mean(cA)),
        'std': float(np.std(cA))
    }
    
    # Detail koeficijenti (visoke frekvencije)
    details = []
    for i, cD in enumerate(coeffs[1:], 1):
        detail_info = {
            'level': i,
            'coefficients': cD.tolist(),
            'energy': float(np.sum(cD**2)),
            'mean': float(np.mean(cD)),
            'std': float(np.std(cD)),
            'max_coeff': float(np.max(np.abs(cD)))
        }
        details.append(detail_info)
    
    # Rekonstrukcija signala
    reconstructed = pywt.waverec(coeffs, wavelet)
    
    # Wavelet entropija
    total_energy = sum([np.sum(c**2) for c in coeffs])
    relative_energies = [np.sum(c**2)/total_energy for c in coeffs]
    wavelet_entropy = -np.sum([e * np.log2(e) for e in relative_energies if e > 0])
    
    return {
        "wavelet_type": wavelet,
        "decomposition_levels": levels,
        "approximation": wavelet_features['approximation'],
        "details": details,
        "reconstructed_signal": reconstructed.tolist(),
        "wavelet_entropy": float(wavelet_entropy),
        "total_energy": float(total_energy),
        "formula": "WT(a,b) = (1/√a) ∫ x(t)ψ*((t-b)/a)dt",
        "interpretation": get_wavelet_interpretation(wavelet_entropy, details)
    }

def get_wavelet_interpretation(entropy, details):
    """Interpretacija wavelet analize"""
    high_freq_energy = sum([d['energy'] for d in details[:3]])  # Prva 3 nivoa
    low_freq_energy = sum([d['energy'] for d in details[3:]])   # Ostali nivoi
    
    if entropy > 3.0:
        complexity = "Visoka kompleksnost"
    elif entropy > 2.0:
        complexity = "Umerena kompleksnost"
    else:
        complexity = "Niska kompleksnost"
    
    if high_freq_energy > low_freq_energy:
        noise_level = "Visok nivo šuma ili artefakata"
    else:
        noise_level = "Nizak nivo šuma"
    
    return f"{complexity}. {noise_level}. Wavelet entropija: {entropy:.2f}"

def advanced_filtering(ekg_signal, fs=250):
    """
    Napredni filtri prema Sörnmo & Laguna (2005)
    
    Args:
        ekg_signal: 1D numpy array
        fs: sampling frequency
    
    Returns:
        dict: Filtrirani signali i analiza
    """
    signal_array = np.array(ekg_signal, dtype=float)
    
    # 1. Baseline wander removal (High-pass filter)
    # Cutoff: 0.5 Hz
    nyquist = fs / 2
    high_cutoff = 0.5 / nyquist
    b_hp, a_hp = butter(4, high_cutoff, btype='high')
    baseline_removed = filtfilt(b_hp, a_hp, signal_array)
    
    # 2. Power line interference removal (Notch filter)
    # 50 Hz notch filter
    notch_freq = 50.0 / nyquist
    Q = 30  # Quality factor
    b_notch, a_notch = signal.iirnotch(notch_freq, Q)
    powerline_removed = filtfilt(b_notch, a_notch, baseline_removed)
    
    # 3. EMG noise removal (Low-pass filter)
    # Cutoff: 40 Hz
    low_cutoff = 40 / nyquist
    b_lp, a_lp = butter(4, low_cutoff, btype='low')
    emg_removed = filtfilt(b_lp, a_lp, powerline_removed)
    
    # 4. Adaptive filter (Wiener filter approximation)
    # Estimate noise from high-frequency components
    b_noise, a_noise = butter(4, 0.8, btype='high')  # >100 Hz
    noise_estimate = filtfilt(b_noise, a_noise, signal_array)
    noise_power = np.var(noise_estimate)
    signal_power = np.var(emg_removed)
    
    # Wiener filter coefficient
    if noise_power > 0:
        wiener_coeff = signal_power / (signal_power + noise_power)
        adaptive_filtered = wiener_coeff * emg_removed
    else:
        adaptive_filtered = emg_removed
    
    return {
        "original_signal": signal_array.tolist(),
        "baseline_removed": baseline_removed.tolist(),
        "powerline_removed": powerline_removed.tolist(),
        "emg_removed": emg_removed.tolist(),
        "adaptive_filtered": adaptive_filtered.tolist(),
        "noise_power": float(noise_power),
        "signal_power": float(signal_power),
        "wiener_coefficient": float(wiener_coeff) if noise_power > 0 else 1.0,
        "filters_applied": [
            "High-pass (0.5 Hz) - baseline wander removal",
            "Notch (50 Hz) - power line interference",
            "Low-pass (40 Hz) - EMG noise removal",
            "Adaptive Wiener filter - residual noise"
        ],
        "formulas": {
            "highpass": "H(z) = (1-z^-1)/(1-az^-1)",
            "notch": "H(z) = (1-2cos(ω₀)z^-1+z^-2)/(1-2rcos(ω₀)z^-1+r²z^-2)",
            "lowpass": "H(z) = b₀(1+z^-1)²/(1+a₁z^-1+a₂z^-2)",
            "wiener": "W = S/(S+N) where S=signal power, N=noise power"
        }
    }

def comprehensive_ekg_analysis(ekg_signal, fs=250):
    """
    Komprehensivna analiza koja kombinuje sve napredne metode
    
    Args:
        ekg_signal: 1D numpy array
        fs: sampling frequency
    
    Returns:
        dict: Kompletni rezultati analize
    """
    results = {}
    
    # 1. Spatial Filling Index
    results['spatial_filling_index'] = spatial_filling_index(ekg_signal)
    
    # 2. Time-Frequency analiza
    results['time_frequency_analysis'] = time_frequency_analysis(ekg_signal, fs)
    
    # 3. Wavelet analiza
    results['wavelet_analysis'] = wavelet_analysis(ekg_signal)
    
    # 4. Napredni filtri
    results['advanced_filtering'] = advanced_filtering(ekg_signal, fs)
    
    # 5. Kombinovana interpretacija
    results['comprehensive_interpretation'] = generate_comprehensive_interpretation(results)
    
    return results

def generate_comprehensive_interpretation(results):
    """Generiše sveobuhvatnu interpretaciju svih analiza"""
    sfi = results['spatial_filling_index']['spatial_filling_index']
    entropy = results['time_frequency_analysis']['mean_spectral_entropy']
    wavelet_entropy = results['wavelet_analysis']['wavelet_entropy']
    
    interpretation = {
        "signal_complexity": "Visoka" if sfi > 1.3 else "Umerena" if sfi > 1.0 else "Niska",
        "frequency_stability": "Stabilna" if entropy < 2.0 else "Nestabilna",
        "wavelet_complexity": "Kompleksan" if wavelet_entropy > 2.5 else "Jednostavan",
        "overall_assessment": "",
        "recommendations": []
    }
    
    # Generisanje ukupne ocene
    if sfi > 1.3 and entropy > 2.0:
        interpretation["overall_assessment"] = "Signal pokazuje visoku kompleksnost i nestabilnost - potrebna medicinska evaluacija"
        interpretation["recommendations"].append("Konsultacija sa kardiologom")
        interpretation["recommendations"].append("Dodatne EKG analize")
    elif sfi < 1.0 and entropy < 1.5:
        interpretation["overall_assessment"] = "Signal je jednostavan i stabilan - verovatno normalan"
        interpretation["recommendations"].append("Rutinska kontrola")
    else:
        interpretation["overall_assessment"] = "Signal pokazuje umerene karakteristike - potrebno praćenje"
        interpretation["recommendations"].append("Redovno praćenje")
        interpretation["recommendations"].append("Ponoviti analizu")
    
    return interpretation