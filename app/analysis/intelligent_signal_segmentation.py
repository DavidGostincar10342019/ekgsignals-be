"""
Inteligentna segmentacija EKG signala za optimalno generisanje slika
Fokusira se na najkritičnije delove signala umesto na celokupne podatke
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy import signal as sp_signal
from scipy.signal import find_peaks, butter, filtfilt

def find_critical_segments(ekg_signal, fs=250, segment_duration=1, num_segments=1):
    """
    Pronalazi najkritičnije segmente EKG signala za generisanje slike
    POBOLJŠANO: Fokusira se na kraće, kritičnije segmente sa najvećim pikovima
    
    Args:
        ekg_signal: EKG signal (numpy array ili lista)
        fs: Frekvencija uzorkovanja (Hz)
        segment_duration: Trajanje svakog segmenta u sekundama (default 1s - jedan otkucaj)
        num_segments: Broj segmenata da vrati (default 1)
    
    Returns:
        dict sa kritičnim segmentima i metapodacima
    """
    ekg_signal = np.array(ekg_signal)
    
    print(f"DEBUG: Tražim kritične segmente u signalu od {len(ekg_signal)} uzoraka")
    
    # POBOLJŠANO: Prvo pokušaj sa peak-centered pristupom
    peak_centered_segments = find_peak_centered_segments(ekg_signal, fs, segment_duration, num_segments)
    
    if peak_centered_segments:
        print(f"DEBUG: Pronašao {len(peak_centered_segments)} peak-centered segmenata")
        return {
            'critical_segments': peak_centered_segments,
            'total_r_peaks': sum(seg['r_peaks_count'] for seg in peak_centered_segments),
            'signal_length': len(ekg_signal),
            'segment_duration': segment_duration,
            'analysis_summary': {
                'highest_criticality': peak_centered_segments[0]['criticality_score'] if peak_centered_segments else 0,
                'r_peak_density': sum(seg['r_peaks_count'] for seg in peak_centered_segments) / (segment_duration * num_segments),
                'segments_analyzed': len(peak_centered_segments),
                'method': 'peak_centered'
            }
        }
    
    # Fallback na originalni pristup
    print(f"DEBUG: Peak-centered ne radi, koristim originalni pristup")
    segment_samples = int(segment_duration * fs)
    
    # 1. Predobrada signala
    processed_signal = preprocess_for_peak_detection(ekg_signal, fs)
    
    # 2. Detekcija R-pikova
    r_peaks = detect_r_peaks_advanced(processed_signal, fs)
    
    # 3. Analiza varijabilnosti i nepravilnosti
    segments_analysis = analyze_signal_segments(ekg_signal, r_peaks, fs, segment_samples)
    
    # 4. Rangiranje segmenata po kritičnosti
    ranked_segments = rank_segments_by_criticality(segments_analysis)
    
    # 5. Izbor najboljih segmenata
    selected_segments = select_optimal_segments(ranked_segments, num_segments, segment_samples)
    
    return {
        'critical_segments': selected_segments,
        'total_r_peaks': len(r_peaks),
        'signal_length': len(ekg_signal),
        'segment_duration': segment_duration,
        'analysis_summary': {
            'highest_criticality': ranked_segments[0]['criticality_score'] if ranked_segments else 0,
            'r_peak_density': len(r_peaks) / (len(ekg_signal) / fs) if len(ekg_signal) > 0 else 0,
            'segments_analyzed': len(segments_analysis),
            'method': 'sliding_window_fallback'
        }
    }

def find_peak_centered_segments(ekg_signal, fs, segment_duration=1, num_segments=1):
    """
    NOVA METODA: Pronalazi segmente centrirane oko najvećih R-pikova
    ULTRA POBOLJŠANO sa predobradom signala za čiste EKG oblike
    """
    try:
        ekg_signal = np.array(ekg_signal)
        segment_samples = int(segment_duration * fs)
        half_segment = segment_samples // 2
        
        print(f"DEBUG: Ultra-optimizovana peak-centered analiza za {segment_duration}s segment")
        
        # 0. PREDOBRADA SIGNALA za čišći EKG
        cleaned_signal = advanced_ekg_preprocessing(ekg_signal, fs)
        print(f"DEBUG: Signal očišćen od noise-a i baseline wander-a")
        
        # 1. Vrlo agresivna detekcija pikova na očišćenom signalu
        peak_candidates = find_strongest_peaks(cleaned_signal, fs)
        
        if len(peak_candidates) == 0:
            print(f"DEBUG: Nema pronađenih jakih pikova, pokušavam sa originalnim signalom")
            peak_candidates = find_strongest_peaks(ekg_signal, fs)
            if len(peak_candidates) == 0:
                return None
        
        print(f"DEBUG: Pronašao {len(peak_candidates)} ultra-kvalitetnih kandidata")
        
        # 2. Oceni svaki pik kao centar segmenta - koristi OČIŠĆEN signal
        scored_segments = []
        
        for peak_idx in peak_candidates:
            # Definiši segment oko pika
            start_idx = max(0, peak_idx - half_segment)
            end_idx = min(len(cleaned_signal), peak_idx + half_segment)
            
            # Proveri da li je segment dovoljno dugačak
            if end_idx - start_idx < segment_samples * 0.8:  # Minimum 80% željene dužine
                continue
            
            # Koristi OČIŠĆEN signal za segment
            segment = cleaned_signal[start_idx:end_idx]
            
            # Oceni ovaj segment
            score = score_peak_centered_segment(segment, peak_idx - start_idx, fs)
            
            scored_segments.append({
                'start_idx': start_idx,
                'end_idx': end_idx,
                'start_time': start_idx / fs,
                'end_time': end_idx / fs,
                'signal_segment': segment,
                'peak_position': peak_idx - start_idx,
                'criticality_score': score,
                'r_peaks_count': count_peaks_in_segment(segment, fs),
                'r_peaks_positions': find_peaks_in_segment(segment, fs),
                'central_peak_amplitude': cleaned_signal[peak_idx],
                'method': 'peak_centered'
            })
        
        if not scored_segments:
            print(f"DEBUG: Nema validnih peak-centered segmenata")
            return None
        
        # 3. Sortiraj po scoru i vrati najbolje
        scored_segments.sort(key=lambda x: x['criticality_score'], reverse=True)
        
        best_segments = scored_segments[:num_segments]
        
        for i, seg in enumerate(best_segments):
            print(f"DEBUG: Segment {i+1}: vreme={seg['start_time']:.1f}-{seg['end_time']:.1f}s, "
                  f"score={seg['criticality_score']:.1f}, amplitude={seg['central_peak_amplitude']:.3f}")
        
        return best_segments
        
    except Exception as e:
        print(f"DEBUG: Greška u peak-centered analizi: {str(e)}")
        return None

def advanced_ekg_preprocessing(signal, fs):
    """
    NAPREDNA PREDOBRADA EKG signala za najčistije moguće segmente
    Uklanja baseline wander, high-frequency noise, i artefakte
    """
    signal = np.array(signal, dtype=float)
    
    print(f"DEBUG: Napredna predobrada signala ({len(signal)} uzoraka)")
    
    # 1. UKLANJANJE BASELINE WANDER (0.5 Hz high-pass)
    try:
        nyquist = fs / 2
        
        # High-pass filter za baseline wander
        high_cutoff = 0.5 / nyquist
        if high_cutoff < 1.0:
            b_high, a_high = butter(3, high_cutoff, btype='high')
            signal = filtfilt(b_high, a_high, signal)
            print(f"DEBUG: Uklonjen baseline wander")
    except Exception as e:
        print(f"DEBUG: Baseline filter neuspešan: {e}")
        # Fallback - polynomial detrending
        x = np.arange(len(signal))
        coeffs = np.polyfit(x, signal, 3)  # Kubni polinom
        trend = np.polyval(coeffs, x)
        signal = signal - trend
        print(f"DEBUG: Korišćen polynomial detrending")
    
    # 2. LOW-PASS FILTER za uklanjanje high-frequency noise (40 Hz)
    try:
        low_cutoff = 40 / nyquist
        if low_cutoff < 1.0:
            b_low, a_low = butter(4, low_cutoff, btype='low')
            signal = filtfilt(b_low, a_low, signal)
            print(f"DEBUG: Uklonjen high-frequency noise")
    except Exception as e:
        print(f"DEBUG: Low-pass filter neuspešan: {e}")
    
    # 3. NOTCH FILTER za 50Hz/60Hz power line interference
    try:
        # 50Hz notch (Evropa)
        notch_freq = 50
        if notch_freq < nyquist:
            Q = 30  # Quality factor
            w0 = notch_freq / nyquist
            b_notch, a_notch = butter(2, [w0 - w0/Q, w0 + w0/Q], btype='bandstop')
            signal = filtfilt(b_notch, a_notch, signal)
            print(f"DEBUG: Uklonjen 50Hz power line interference")
    except Exception as e:
        print(f"DEBUG: Notch filter neuspešan: {e}")
    
    # 4. MEDIAN FILTER za spike removal
    try:
        from scipy import ndimage
        window_size = max(3, int(0.02 * fs))  # 20ms window
        if window_size % 2 == 0:
            window_size += 1
        signal = ndimage.median_filter(signal, size=window_size)
        print(f"DEBUG: Uklonjeni spike artefakti")
    except Exception as e:
        print(f"DEBUG: Median filter neuspešan: {e}")
    
    # 5. NORMALIZACIJA za optimalne amplitude
    signal_range = np.max(signal) - np.min(signal)
    if signal_range > 0:
        # Centri oko nule
        signal = signal - np.mean(signal)
        
        # Normalizuj da max amplitude bude oko 1.0
        max_abs = np.max(np.abs(signal))
        if max_abs > 0:
            signal = signal / max_abs
        
        print(f"DEBUG: Signal normalizovan")
    
    # 6. OUTLIER SUPPRESSION
    # Ograniči ekstremne vrednosti na 99.5 percentil
    percentile_99_5 = np.percentile(np.abs(signal), 99.5)
    signal = np.clip(signal, -percentile_99_5, percentile_99_5)
    
    print(f"DEBUG: Predobrada završena - signal optimizovan za QRS detekciju")
    
    return signal

def find_strongest_peaks(signal, fs):
    """Pronalazi najjače R-pikove u signalu - ULTRA AGRESIVNO za 1-sekundne segmente"""
    
    # 1. Posebna predobrada za pronalaženje najvećih pikova
    signal = np.array(signal)
    
    # Jednostavna ali efikasna detekcija najvećih pikova
    # Traži lokalne maksimume koji su značajno veći od okoline
    peak_candidates = []
    
    window_size = int(0.1 * fs)  # 100ms prozor
    min_distance = int(0.3 * fs)  # 300ms minimum između pikova
    
    print(f"DEBUG: Tražim najveće pikove u signalu od {len(signal)} uzoraka")
    
    # Pronaađi sve lokalne maksimume
    for i in range(window_size, len(signal) - window_size):
        current_val = signal[i]
        
        # Proveri da li je to lokalni maksimum
        left_window = signal[i-window_size:i]
        right_window = signal[i+1:i+window_size+1]
        
        if (current_val > np.max(left_window) and 
            current_val > np.max(right_window)):
            
            # Izračunaj "snagu" ovog pika
            local_mean = np.mean(np.concatenate([left_window, right_window]))
            local_std = np.std(np.concatenate([left_window, right_window]))
            
            # Pik mora biti značajno veći od okoline
            if current_val > local_mean + 2 * local_std:
                peak_strength = (current_val - local_mean) / (local_std + 1e-6)
                peak_candidates.append((i, abs(current_val), peak_strength))
    
    if not peak_candidates:
        print(f"DEBUG: Nema pronađenih pikova sa osnovnim kriterijumima")
        return []
    
    # Sortiraj po amplitudi (apsolutna vrednost)
    peak_candidates.sort(key=lambda x: x[1], reverse=True)
    
    # Ukloni pikove koji su preblizu jedan drugome (zadrži najjaći)
    filtered_peaks = []
    for peak_idx, amplitude, strength in peak_candidates:
        too_close = False
        for existing_peak in filtered_peaks:
            if abs(peak_idx - existing_peak) < min_distance:
                too_close = True
                break
        
        if not too_close:
            filtered_peaks.append(peak_idx)
        
        # Ograniči na top 5 pikova
        if len(filtered_peaks) >= 5:
            break
    
    print(f"DEBUG: Pronašao {len(filtered_peaks)} ultra-jakih pikova")
    
    # Prikaži informacije o top pikovima
    for i, peak_idx in enumerate(filtered_peaks[:3]):
        amplitude = signal[peak_idx]
        print(f"DEBUG: Pik {i+1}: pozicija={peak_idx} ({peak_idx/fs:.2f}s), amplituda={amplitude:.3f}")
    
    return filtered_peaks

def score_peak_centered_segment(segment, peak_pos, fs):
    """Ocenjuje segment centriran oko pika - ULTRA OPTIMIZOVANO za čiste EKG oblike"""
    
    score = 0
    segment = np.array(segment)
    
    # 1. AMPLITUDA CENTRALNOG PIKA (GLAVNI FAKTOR)
    if 0 <= peak_pos < len(segment):
        central_amplitude = abs(segment[peak_pos])
        score += central_amplitude * 200  # Udvostručen uticaj amplitudes
    
    # 2. MORFOLOŠKI KVALITET - da li liči na pravi QRS?
    morphology_score = evaluate_qrs_morphology(segment, peak_pos, fs)
    score += morphology_score * 100  # Veliki bonus za dobru morfologiju
    
    # 3. KONTRAST - da li se pik jasno izdvaja?
    contrast_score = calculate_peak_contrast(segment, peak_pos)
    score += contrast_score * 75
    
    # 4. ČISTOĆA SIGNALA (nema artifakte)
    cleanliness_score = evaluate_signal_cleanliness(segment, fs)
    score += cleanliness_score * 50
    
    # 5. BASELINE STABILNOST
    baseline_score = evaluate_baseline_stability(segment)
    score += baseline_score * 30
    
    # 6. CENTRIRANOST PIKA
    center_pos = len(segment) // 2
    center_distance = abs(peak_pos - center_pos) / len(segment)
    center_bonus = (1 - center_distance) * 25
    score += center_bonus
    
    return score

def evaluate_qrs_morphology(segment, peak_pos, fs):
    """Ocenjuje da li segment liči na pravi QRS kompleks"""
    
    if peak_pos < 10 or peak_pos >= len(segment) - 10:
        return 0
    
    score = 0
    
    # Tipični QRS kompleks traje 80-120ms
    qrs_width_samples = int(0.1 * fs)  # 100ms
    qrs_start = max(0, peak_pos - qrs_width_samples // 2)
    qrs_end = min(len(segment), peak_pos + qrs_width_samples // 2)
    
    qrs_region = segment[qrs_start:qrs_end]
    
    # 1. R-pik treba da bude najviši u QRS regionu
    if len(qrs_region) > 0 and peak_pos - qrs_start < len(qrs_region):
        local_peak_pos = peak_pos - qrs_start
        if np.argmax(np.abs(qrs_region)) == local_peak_pos:
            score += 20
    
    # 2. Brza promena oko R-pika (tipično za QRS)
    if peak_pos >= 5 and peak_pos < len(segment) - 5:
        before_peak = segment[peak_pos-5:peak_pos]
        after_peak = segment[peak_pos+1:peak_pos+6]
        
        # Nagib pre i posle pika
        slope_before = np.mean(np.diff(before_peak))
        slope_after = np.mean(np.diff(after_peak))
        
        # QRS ima brzu promenu - pozitivan nagib pre, negativan posle (ili obrnuto)
        if slope_before * slope_after < 0:  # Suprotni znaci
            score += 15
    
    # 3. Širina na pola visine (tipična za QRS)
    peak_amplitude = abs(segment[peak_pos])
    half_amplitude = peak_amplitude / 2
    
    # Traži tačke na pola visine levo i desno od pika
    left_half = None
    right_half = None
    
    for i in range(peak_pos, 0, -1):
        if abs(segment[i]) <= half_amplitude:
            left_half = i
            break
    
    for i in range(peak_pos, len(segment)):
        if abs(segment[i]) <= half_amplitude:
            right_half = i
            break
    
    if left_half is not None and right_half is not None:
        width_samples = right_half - left_half
        width_ms = width_samples * 1000 / fs
        
        # Tipična širina QRS: 80-120ms
        if 60 <= width_ms <= 150:
            score += 10
    
    return score

def calculate_peak_contrast(segment, peak_pos):
    """Računa kontrast pika u odnosu na okolinu"""
    
    if peak_pos < 20 or peak_pos >= len(segment) - 20:
        return 0
    
    peak_value = abs(segment[peak_pos])
    
    # Okolina pika (isključujemo sam pik i blisku okolinu)
    left_context = segment[peak_pos-20:peak_pos-5]
    right_context = segment[peak_pos+5:peak_pos+20]
    
    if len(left_context) == 0 or len(right_context) == 0:
        return 0
    
    context = np.concatenate([left_context, right_context])
    context_mean = np.mean(np.abs(context))
    context_std = np.std(context)
    
    if context_std == 0:
        return 0
    
    # Signal-to-noise ratio kao mera kontrasta
    contrast = (peak_value - context_mean) / context_std
    return max(0, contrast)

def evaluate_signal_cleanliness(segment, fs):
    """Ocenjuje čistoću signala (nema high-frequency noise)"""
    
    # 1. Proveri high-frequency komponente
    # Derivat signala - ako je previše varijabilan, signal je "prljav"
    derivative = np.diff(segment)
    derivative_std = np.std(derivative)
    
    # Normaliziraj po amplitudi signala
    signal_range = np.max(segment) - np.min(segment)
    if signal_range == 0:
        return 0
    
    relative_noise = derivative_std / signal_range
    
    # Manji noise = veći score
    cleanliness = max(0, 1 - relative_noise * 5)
    
    # 2. Proveri sudden jumps (artefakti)
    jump_penalty = 0
    for i in range(1, len(segment) - 1):
        # Velika promena koja nije graduelna
        prev_change = abs(segment[i] - segment[i-1])
        next_change = abs(segment[i+1] - segment[i])
        avg_change = (prev_change + next_change) / 2
        
        if avg_change > signal_range * 0.1:  # Više od 10% range-a
            jump_penalty += 0.1
    
    cleanliness = max(0, cleanliness - jump_penalty)
    
    return cleanliness * 100

def evaluate_baseline_stability(segment):
    """Ocenjuje stabilnost baseline-a"""
    
    # Ukloni trend i izmeri varijabilnost
    # Jednostavan detrend - ukloni linearni trend
    x = np.arange(len(segment))
    coeffs = np.polyfit(x, segment, 1)
    trend = np.polyval(coeffs, x)
    detrended = segment - trend
    
    # Baseline varjabilnost
    baseline_std = np.std(detrended)
    signal_range = np.max(segment) - np.min(segment)
    
    if signal_range == 0:
        return 0
    
    # Manja varijabilnost baseline-a = bolji score
    relative_baseline_var = baseline_std / signal_range
    stability = max(0, 1 - relative_baseline_var * 3)
    
    return stability * 100

def count_peaks_in_segment(segment, fs):
    """Broji R-pikove u segmentu"""
    try:
        processed = preprocess_for_peak_detection(segment, fs)
        threshold = np.mean(processed) + np.std(processed)
        peaks, _ = find_peaks(processed, height=threshold, distance=int(0.25 * fs))
        return len(peaks)
    except:
        return 0

def find_peaks_in_segment(segment, fs):
    """Pronalazi pozicije R-pikova u segmentu"""
    try:
        processed = preprocess_for_peak_detection(segment, fs)
        threshold = np.mean(processed) + np.std(processed)
        peaks, _ = find_peaks(processed, height=threshold, distance=int(0.25 * fs))
        return peaks.tolist()
    except:
        return []

def preprocess_for_peak_detection(signal, fs):
    """Predobrađuje signal za bolju detekciju R-pikova"""
    
    # Bandpass filter (0.5-40 Hz) za uklanjanje baseline wander i noise
    nyquist = fs / 2
    low_cutoff = 0.5 / nyquist
    high_cutoff = 40 / nyquist
    
    try:
        b, a = butter(4, [low_cutoff, high_cutoff], btype='band')
        filtered_signal = filtfilt(b, a, signal)
    except:
        # Fallback ako filter ne radi
        filtered_signal = signal - np.mean(signal)
    
    # Derivative filter za isticanje QRS kompleksa
    derivative = np.diff(filtered_signal)
    derivative = np.append(derivative, derivative[-1])
    
    # Squaring za amplifikaciju pikova
    squared = derivative ** 2
    
    # Moving average za smoothing
    window_size = int(0.08 * fs)  # 80ms prozor
    if window_size % 2 == 0:
        window_size += 1
    
    smoothed = np.convolve(squared, np.ones(window_size)/window_size, mode='same')
    
    return smoothed

def detect_r_peaks_advanced(processed_signal, fs):
    """Napredna detekcija R-pikova sa adaptivnim pragom"""
    
    # Početni prag na osnovu signal statistics
    mean_amplitude = np.mean(processed_signal)
    std_amplitude = np.std(processed_signal)
    initial_threshold = mean_amplitude + 2 * std_amplitude
    
    # Minimum distance između R-pikova (300ms = tipično minimum RR interval)
    min_distance = int(0.3 * fs)
    
    # Pronađi početne pikove
    peaks, properties = find_peaks(processed_signal, 
                                  height=initial_threshold,
                                  distance=min_distance)
    
    if len(peaks) == 0:
        # Smanji prag ako nema pikova
        initial_threshold = mean_amplitude + std_amplitude
        peaks, properties = find_peaks(processed_signal, 
                                      height=initial_threshold,
                                      distance=min_distance)
    
    # Adaptivni prag na osnovu detektovanih pikova
    if len(peaks) > 2:
        peak_amplitudes = processed_signal[peaks]
        adaptive_threshold = np.mean(peak_amplitudes) * 0.6
        
        # Ponovno pronalaženje sa adaptivnim pragom
        peaks, properties = find_peaks(processed_signal, 
                                      height=adaptive_threshold,
                                      distance=min_distance)
    
    return peaks

def analyze_signal_segments(signal, r_peaks, fs, segment_samples):
    """Analizira segmente signala i ocenjuje njihovu kritičnost"""
    
    segments_analysis = []
    step_size = segment_samples // 2  # 50% overlap
    
    for start_idx in range(0, len(signal) - segment_samples, step_size):
        end_idx = start_idx + segment_samples
        segment = signal[start_idx:end_idx]
        
        # R-pikovi u ovom segmentu
        segment_peaks = [p - start_idx for p in r_peaks 
                        if start_idx <= p < end_idx]
        
        # Analiza segmenta
        analysis = {
            'start_idx': start_idx,
            'end_idx': end_idx,
            'start_time': start_idx / fs,
            'end_time': end_idx / fs,
            'r_peaks_count': len(segment_peaks),
            'r_peaks_positions': segment_peaks,
            'signal_segment': segment
        }
        
        # Računanje kritičnosti
        analysis['criticality_score'] = calculate_segment_criticality(
            segment, segment_peaks, fs
        )
        
        segments_analysis.append(analysis)
    
    return segments_analysis

def calculate_segment_criticality(segment, peaks_in_segment, fs):
    """Računa kritičnost segmenta na osnovu različitih faktora"""
    
    criticality = 0
    
    # 1. Gustina R-pikova (više pikova = veći prioritet)
    peak_density = len(peaks_in_segment) / (len(segment) / fs)
    criticality += peak_density * 10
    
    # 2. Varijabilnost amplituda (veća varijabilnost = potencijalne aritmije)
    if len(peaks_in_segment) > 1:
        peak_amplitudes = [segment[p] for p in peaks_in_segment if p < len(segment)]
        if peak_amplitudes:
            amplitude_std = np.std(peak_amplitudes)
            amplitude_mean = np.mean(peak_amplitudes)
            cv = amplitude_std / amplitude_mean if amplitude_mean > 0 else 0
            criticality += cv * 15
    
    # 3. RR interval varijabilnost
    if len(peaks_in_segment) > 2:
        rr_intervals = np.diff(peaks_in_segment)
        rr_std = np.std(rr_intervals)
        rr_mean = np.mean(rr_intervals)
        rr_cv = rr_std / rr_mean if rr_mean > 0 else 0
        criticality += rr_cv * 20
    
    # 4. Prisutnost ekstremnih vrednosti
    segment_std = np.std(segment)
    segment_mean = np.mean(segment)
    extreme_threshold = segment_mean + 3 * segment_std
    extreme_count = np.sum(np.abs(segment - segment_mean) > extreme_threshold)
    criticality += extreme_count * 2
    
    # 5. Signal-to-noise ratio (viši SNR = bolja kvalitet)
    try:
        # Jednostavan SNR calc
        signal_power = np.mean(segment ** 2)
        noise_power = np.var(segment - np.mean(segment))
        snr = signal_power / noise_power if noise_power > 0 else 1
        criticality += np.log10(snr) * 5
    except:
        pass
    
    # 6. Bonus za segmente sa normalnim heart rate (60-100 BPM)
    if len(peaks_in_segment) >= 2:
        avg_rr_samples = np.mean(np.diff(peaks_in_segment))
        avg_rr_seconds = avg_rr_samples / fs
        bpm = 60 / avg_rr_seconds if avg_rr_seconds > 0 else 0
        
        if 60 <= bpm <= 100:
            criticality += 5  # Bonus za normalnu frekvenciju
        elif bpm > 120 or bpm < 50:
            criticality += 10  # Bonus za patološke frekvencije (zanimljive za analizu)
    
    return max(criticality, 0)  # Minimalno 0

def rank_segments_by_criticality(segments_analysis):
    """Rangira segmente po kritičnosti (opadajuće)"""
    
    return sorted(segments_analysis, 
                 key=lambda x: x['criticality_score'], 
                 reverse=True)

def select_optimal_segments(ranked_segments, num_segments, segment_samples):
    """Bira optimalne segmente izbegavajući preklapanje"""
    
    selected = []
    
    for segment in ranked_segments:
        if len(selected) >= num_segments:
            break
        
        # Proveri da li se preklapa sa već izabranim segmentima
        overlap = False
        for selected_seg in selected:
            if (segment['start_idx'] < selected_seg['end_idx'] and 
                segment['end_idx'] > selected_seg['start_idx']):
                overlap = True
                break
        
        if not overlap:
            selected.append(segment)
    
    # Ako nema dovoljno segmenata bez preklapanja, uzmi najbolje
    while len(selected) < num_segments and len(selected) < len(ranked_segments):
        for segment in ranked_segments:
            if segment not in selected:
                selected.append(segment)
                break
    
    return selected

def create_comparison_visualization(original_signal, selected_segments, fs):
    """
    Kreira vizualizaciju koja poredi originalni signal sa izabranim segmentima
    
    Returns:
        dict sa base64 slikom poređenja
    """
    import matplotlib.pyplot as plt
    import io
    import base64
    
    fig, axes = plt.subplots(len(selected_segments) + 1, 1, 
                            figsize=(14, 3 * (len(selected_segments) + 1)), dpi=150)
    
    if len(selected_segments) == 0:
        axes = [axes]
    
    # Originalni signal (overview)
    t_full = np.linspace(0, len(original_signal) / fs, len(original_signal))
    axes[0].plot(t_full, original_signal, 'b-', alpha=0.7, linewidth=1)
    axes[0].set_title('Ceo EKG Signal (Overview)', fontweight='bold')
    axes[0].set_xlabel('Vreme (s)')
    axes[0].set_ylabel('Amplituda')
    axes[0].grid(True, alpha=0.3)
    
    # Označi izabrane segmente na overview-u
    for i, segment in enumerate(selected_segments):
        start_time = segment['start_time']
        end_time = segment['end_time']
        axes[0].axvspan(start_time, end_time, alpha=0.3, 
                       color=f'C{i+1}', label=f'Segment {i+1}')
    
    if selected_segments:
        axes[0].legend()
    
    # Detaljni prikaz izabranih segmenata
    for i, segment in enumerate(selected_segments):
        if i + 1 < len(axes):
            ax = axes[i + 1]
            
            signal_segment = segment['signal_segment']
            t_segment = np.linspace(segment['start_time'], segment['end_time'], 
                                  len(signal_segment))
            
            # Plot segmenta
            ax.plot(t_segment, signal_segment, f'C{i+1}-', linewidth=2)
            
            # R-pikovi u segmentu
            r_peaks_pos = segment['r_peaks_positions']
            for peak_idx in r_peaks_pos:
                if peak_idx < len(signal_segment):
                    peak_time = segment['start_time'] + (peak_idx / fs)
                    ax.plot(peak_time, signal_segment[peak_idx], 'ro', 
                           markersize=8, markerfacecolor='red')
            
            # Naslov sa kritičnošću
            ax.set_title(f'Segment {i+1}: Kritičnost = {segment["criticality_score"]:.1f}, '
                        f'R-pikovi = {segment["r_peaks_count"]}', fontweight='bold')
            ax.set_xlabel('Vreme (s)')
            ax.set_ylabel('Amplituda')
            ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Konvertuj u base64
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', dpi=150)
    buf.seek(0)
    image_base64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    
    return {
        'comparison_image_base64': f"data:image/png;base64,{image_base64}",
        'segments_count': len(selected_segments),
        'total_r_peaks': sum(seg['r_peaks_count'] for seg in selected_segments)
    }

def generate_optimized_ekg_images(signal, fs, style="clinical"):
    """
    Generiše optimizovane EKG slike fokusirane na kritične delove
    
    Args:
        signal: EKG signal
        fs: Sampling frequency
        style: "clinical" ili "monitor"
    
    Returns:
        dict sa slikama i analizom
    """
    # Pronađi kritične segmente
    critical_analysis = find_critical_segments(signal, fs, segment_duration=6, num_segments=2)
    
    # Generiši slike za svaki kritični segment
    from .signal_to_image import create_ekg_image_from_signal
    
    segment_images = []
    
    for i, segment in enumerate(critical_analysis['critical_segments']):
        segment_signal = segment['signal_segment']
        
        # Generiši sliku za ovaj segment
        image_data = create_ekg_image_from_signal(
            segment_signal, fs, 
            duration_seconds=None, 
            style=style
        )
        
        segment_images.append({
            'segment_index': i + 1,
            'image_base64': image_data['image_base64'],
            'metadata': image_data['metadata'],
            'criticality_score': segment['criticality_score'],
            'r_peaks_count': segment['r_peaks_count'],
            'start_time': segment['start_time'],
            'end_time': segment['end_time'],
            'duration': segment['end_time'] - segment['start_time']
        })
    
    # Generiši poređenje
    comparison = create_comparison_visualization(
        signal, critical_analysis['critical_segments'], fs
    )
    
    return {
        'optimized_images': segment_images,
        'comparison_visualization': comparison,
        'analysis_summary': critical_analysis['analysis_summary'],
        'total_segments_analyzed': len(critical_analysis['critical_segments']),
        'original_signal_length': len(signal),
        'original_duration': len(signal) / fs
    }