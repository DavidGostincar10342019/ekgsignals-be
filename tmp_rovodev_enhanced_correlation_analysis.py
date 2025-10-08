"""
POBOLJŠANE METRIKE ZA EKG KORELACIJSKU ANALIZU
Dodatne metrike specifične za EKG signale
"""

import numpy as np
from scipy import signal
from scipy.stats import pearsonr
from scipy.spatial.distance import euclidean
from fastdtw import fastdtw

def enhanced_ekg_correlation_analysis(original, extracted, fs=250):
    """
    Komprehensivna analiza korelacije između originalnog i ekstraktovanog EKG signala
    """
    
    # 1. OSNOVNE METRIKE (postojeće)
    basic_metrics = compare_signals_basic(original, extracted, fs)
    
    # 2. FREKVENCIJSKI DOMEN
    freq_metrics = frequency_domain_analysis(original, extracted, fs)
    
    # 3. EKG-SPECIFIČNE METRIKE
    ekg_metrics = ekg_specific_analysis(original, extracted, fs)
    
    # 4. ADVANCED SIMILARITY MEASURES
    advanced_metrics = advanced_similarity_analysis(original, extracted)
    
    # 5. CLINICAL RELEVANCE SCORE
    clinical_score = calculate_clinical_relevance(basic_metrics, freq_metrics, ekg_metrics)
    
    return {
        "basic": basic_metrics,
        "frequency": freq_metrics, 
        "ekg_specific": ekg_metrics,
        "advanced": advanced_metrics,
        "clinical_relevance": clinical_score,
        "overall_assessment": assess_overall_quality(clinical_score)
    }

def frequency_domain_analysis(original, extracted, fs):
    """Analiza u frekvencijskom domenu"""
    
    # FFT spektri
    f1, psd1 = signal.welch(original, fs, nperseg=min(1024, len(original)//4))
    f2, psd2 = signal.welch(extracted, fs, nperseg=min(1024, len(extracted)//4))
    
    # Fokus na EKG frekvencijski opseg (0.5-40 Hz)
    ekg_band = (f1 >= 0.5) & (f1 <= 40)
    
    # Korelacija u EKG opsegu
    ekg_freq_corr = np.corrcoef(psd1[ekg_band], psd2[ekg_band])[0, 1] if np.sum(ekg_band) > 1 else 0
    
    # Power preservation
    power_orig = np.sum(psd1[ekg_band])
    power_extr = np.sum(psd2[ekg_band])
    power_ratio = min(power_orig, power_extr) / max(power_orig, power_extr) if max(power_orig, power_extr) > 0 else 0
    
    return {
        "full_spectrum_correlation": np.corrcoef(psd1, psd2)[0, 1] if len(psd1) > 1 else 0,
        "ekg_band_correlation": ekg_freq_corr,
        "power_preservation_ratio": power_ratio,
        "dominant_frequency_shift": abs(f1[np.argmax(psd1)] - f2[np.argmax(psd2)])
    }

def ekg_specific_analysis(original, extracted, fs):
    """EKG-specifične metrike"""
    
    # R-pik detekcija (jednostavna)
    r_peaks_orig = detect_r_peaks_simple(original, fs)
    r_peaks_extr = detect_r_peaks_simple(extracted, fs)
    
    # Heart rate calculation
    hr_orig = len(r_peaks_orig) * 60 / (len(original) / fs) if len(r_peaks_orig) > 0 else 0
    hr_extr = len(r_peaks_extr) * 60 / (len(extracted) / fs) if len(r_peaks_extr) > 0 else 0
    
    # R-R interval variability preservation
    if len(r_peaks_orig) > 1 and len(r_peaks_extr) > 1:
        rr_orig = np.diff(r_peaks_orig) / fs
        rr_extr = np.diff(r_peaks_extr) / fs
        
        rr_variability_corr = np.corrcoef(rr_orig[:min(len(rr_orig), len(rr_extr))], 
                                        rr_extr[:min(len(rr_orig), len(rr_extr))])[0, 1]
    else:
        rr_variability_corr = 0
    
    return {
        "heart_rate_original": hr_orig,
        "heart_rate_extracted": hr_extr, 
        "heart_rate_error": abs(hr_orig - hr_extr),
        "r_peaks_detected_orig": len(r_peaks_orig),
        "r_peaks_detected_extr": len(r_peaks_extr),
        "rr_variability_correlation": rr_variability_corr,
        "qrs_amplitude_preservation": calculate_qrs_amplitude_preservation(original, extracted, r_peaks_orig, r_peaks_extr)
    }

def advanced_similarity_analysis(original, extracted):
    """Napredne mere sličnosti"""
    
    # Dynamic Time Warping
    try:
        distance, path = fastdtw(original, extracted, dist=euclidean)
        dtw_similarity = 1 / (1 + distance / len(original))  # Normalize
    except:
        dtw_similarity = 0
    
    # Cross-correlation peak
    cross_corr = np.correlate(original, extracted, mode='full')
    peak_lag = np.argmax(cross_corr) - len(extracted) + 1
    peak_value = np.max(cross_corr) / (np.linalg.norm(original) * np.linalg.norm(extracted))
    
    return {
        "dtw_similarity": dtw_similarity,
        "cross_correlation_peak": peak_value,
        "optimal_lag_samples": peak_lag,
        "structural_similarity": calculate_structural_similarity(original, extracted)
    }

def calculate_clinical_relevance(basic, freq, ekg):
    """Izračunava klinički relevantni skor"""
    
    # Weighted scoring system
    weights = {
        "correlation": 0.3,
        "ekg_freq_preservation": 0.25, 
        "heart_rate_accuracy": 0.2,
        "qrs_preservation": 0.15,
        "rr_variability": 0.1
    }
    
    scores = {
        "correlation": basic.get("correlation", 0),
        "ekg_freq_preservation": freq.get("ekg_band_correlation", 0),
        "heart_rate_accuracy": 1 - min(1, ekg.get("heart_rate_error", 100) / 50),  # Normalize to [0,1]
        "qrs_preservation": ekg.get("qrs_amplitude_preservation", 0),
        "rr_variability": ekg.get("rr_variability_correlation", 0)
    }
    
    clinical_score = sum(weights[k] * max(0, scores[k]) for k in weights.keys())
    
    return {
        "clinical_score": clinical_score,
        "component_scores": scores,
        "weights_used": weights
    }

# Helper functions
def detect_r_peaks_simple(signal, fs):
    """Jednostavna R-pik detekcija"""
    threshold = np.mean(signal) + 2 * np.std(signal)
    peaks = []
    for i in range(1, len(signal)-1):
        if signal[i] > signal[i-1] and signal[i] > signal[i+1] and signal[i] > threshold:
            peaks.append(i)
    return np.array(peaks)

def calculate_qrs_amplitude_preservation(orig, extr, r_orig, r_extr):
    """Izračunava očuvanje amplitude QRS kompleksa"""
    if len(r_orig) == 0 or len(r_extr) == 0:
        return 0
    
    # Amplitude QRS kompleksa
    qrs_amp_orig = np.mean([orig[r] for r in r_orig if 0 <= r < len(orig)])
    qrs_amp_extr = np.mean([extr[r] for r in r_extr if 0 <= r < len(extr)])
    
    return min(qrs_amp_orig, qrs_amp_extr) / max(qrs_amp_orig, qrs_amp_extr) if max(qrs_amp_orig, qrs_amp_extr) > 0 else 0

def calculate_structural_similarity(orig, extr):
    """Strukturalna sličnost signala"""
    # Simplified SSIM-like measure for 1D signals
    min_len = min(len(orig), len(extr))
    orig_segment = orig[:min_len]
    extr_segment = extr[:min_len]
    
    mu1, mu2 = np.mean(orig_segment), np.mean(extr_segment)
    sigma1, sigma2 = np.std(orig_segment), np.std(extr_segment)
    sigma12 = np.mean((orig_segment - mu1) * (extr_segment - mu2))
    
    c1, c2 = 0.01**2, 0.03**2  # Constants
    
    ssim = ((2*mu1*mu2 + c1) * (2*sigma12 + c2)) / ((mu1**2 + mu2**2 + c1) * (sigma1**2 + sigma2**2 + c2))
    return max(0, ssim)

def assess_overall_quality(clinical_score):
    """Procena ukupnog kvaliteta na osnovu kliničkog skora"""
    if clinical_score >= 0.9:
        return "KLINIČKI ODLIČAN - Dijagnostička preciznost"
    elif clinical_score >= 0.8:
        return "KLINIČKI DOBAR - Prihvatljiv za analizu" 
    elif clinical_score >= 0.7:
        return "KLINIČKI ZADOVOLJAVAJUĆI - Ograničena preciznost"
    elif clinical_score >= 0.6:
        return "KLINIČKI PROBLEMATIČAN - Značajna distorsija"
    else:
        return "KLINIČKI NEPRIHVATLJIV - Dijagnostička vrednost upitna"