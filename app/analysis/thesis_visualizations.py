"""
Vizuelizacije specifično za master rad:
"Primena Furijeove i Z-transformacije u analizi biomedicinskih signala"
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import io
import base64
from scipy import signal

def create_thesis_visualizations(ekg_signal, fs, analysis_results, annotations=None):
    """
    Kreira vizuelizacije specifične za master rad
    
    Args:
        ekg_signal: EKG signal array
        fs: Sampling frequency  
        analysis_results: Rezultati analize (arrhythmia_detection, fft_analysis)
        annotations: MIT-BIH anotacije (opcional)
    
    Returns:
        dict: Base64 encoded slike za master rad
    """
    visualizations = {}
    
    # 1. EKG Signal sa R-pikovima i anotacijama
    visualizations['ekg_with_annotations'] = create_ekg_signal_plot(
        ekg_signal, fs, analysis_results, annotations
    )
    
    # 2. FFT Spektar sa dominantnom frekvencijom
    visualizations['fft_spectrum'] = create_fft_spectrum_plot(
        ekg_signal, fs, analysis_results.get('fft_analysis', {})
    )
    
    # 3. Poređenje sa MIT-BIH anotacijama
    if annotations:
        visualizations['mitbih_comparison'] = create_mitbih_comparison_plot(
            ekg_signal, fs, analysis_results, annotations
        )
    
    # 4. Signal processing pipeline
    visualizations['signal_processing_pipeline'] = create_processing_pipeline_plot(
        ekg_signal, fs
    )
    
    return visualizations

def create_ekg_signal_plot(ekg_signal, fs, analysis_results, annotations=None):
    """
    1. VIZUELIZACIJA EKG SIGNALA sa R-pikovima i anotacijama
    """
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10))
    
    # Vreme osa
    time_axis = np.arange(len(ekg_signal)) / fs
    
    # Gornji graf - Ceo signal
    ax1.plot(time_axis, ekg_signal, 'b-', linewidth=1, label='EKG Signal')
    
    # Detektovani R-pikovi
    r_peaks = analysis_results.get('arrhythmia_detection', {}).get('r_peaks', [])
    if r_peaks and len(r_peaks) > 0:
        # Konvertuj u numpy array i filtriraj validne indekse
        r_peaks_array = np.array(r_peaks, dtype=int)
        # Filtriraj indekse koji su u opsegu signala
        valid_r_peaks = r_peaks_array[r_peaks_array < len(ekg_signal)]
        if len(valid_r_peaks) > 0:
            ax1.plot(time_axis[valid_r_peaks], ekg_signal[valid_r_peaks], 
                    'ro', markersize=8, label=f'Detektovani R-pikovi ({len(valid_r_peaks)})')
    
    # MIT-BIH anotacije (ako postoje)
    if annotations and 'samples' in annotations:
        ann_samples = np.array(annotations['samples'], dtype=int)
        # Filtriraj anotacije koje su u opsegu signala
        valid_annotations = ann_samples[ann_samples < len(ekg_signal)]
        if len(valid_annotations) > 0:
            ax1.plot(time_axis[valid_annotations], ekg_signal[valid_annotations], 
                    'g^', markersize=6, label=f'MIT-BIH anotacije ({len(valid_annotations)})')
    
    ax1.set_xlabel('Vreme (s)')
    ax1.set_ylabel('Amplituda')
    ax1.set_title('EKG Signal sa Detektovanim R-pikovima i MIT-BIH Anotacijama')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Donji graf - Zoom na prvih 10 sekundi za detalj
    zoom_samples = min(int(10 * fs), len(ekg_signal))
    time_zoom = time_axis[:zoom_samples]
    signal_zoom = ekg_signal[:zoom_samples]
    
    ax2.plot(time_zoom, signal_zoom, 'b-', linewidth=2, label='EKG Signal (detalj)')
    
    # R-pikovi u zoom-u
    if r_peaks and len(r_peaks) > 0:
        r_peaks_zoom = [int(peak) for peak in r_peaks if int(peak) < zoom_samples]
        if r_peaks_zoom:
            r_peaks_zoom_array = np.array(r_peaks_zoom, dtype=int)
            ax2.plot(time_zoom[r_peaks_zoom_array], signal_zoom[r_peaks_zoom_array], 
                    'ro', markersize=10, label=f'R-pikovi ({len(r_peaks_zoom)})')
    
    # Anotacije u zoom-u
    if annotations and 'samples' in annotations:
        ann_zoom = [ann for ann in valid_annotations if ann < zoom_samples]
        if ann_zoom:
            ax2.plot(time_zoom[ann_zoom], signal_zoom[ann_zoom], 
                    'g^', markersize=8, label=f'MIT-BIH ({len(ann_zoom)})')
    
    ax2.set_xlabel('Vreme (s)')
    ax2.set_ylabel('Amplituda')
    ax2.set_title('Detaljan Prikaz - Prvih 10 Sekundi')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig_to_base64(fig)

def create_fft_spectrum_plot(ekg_signal, fs, fft_analysis):
    """
    2. FFT SPEKTAR sa dominantnom frekvencijom  
    """
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
    
    # Ukloni DC komponentu
    signal_no_dc = ekg_signal - np.mean(ekg_signal)
    
    # FFT
    n = len(signal_no_dc)
    freq = np.fft.rfftfreq(n, d=1.0/fs)
    spectrum = np.abs(np.fft.rfft(signal_no_dc)) / n
    
    # Gornji graf - Pun spektar
    ax1.plot(freq, spectrum, 'b-', linewidth=1)
    
    # Označi dominantnu frekvenciju
    peak_freq = fft_analysis.get('peak_frequency_hz', 0)
    peak_amp = fft_analysis.get('peak_amplitude', 0)
    if peak_freq > 0:
        ax1.axvline(peak_freq, color='red', linestyle='--', linewidth=2, 
                   label=f'Dominantna frekvencija: {peak_freq:.2f} Hz')
        ax1.plot(peak_freq, peak_amp, 'ro', markersize=10, 
                label=f'Peak amplituda: {peak_amp:.4f}')
    
    ax1.set_xlabel('Frekvencija (Hz)')
    ax1.set_ylabel('Amplituda')
    ax1.set_title('FFT Spektar EKG Signala (Furijeova Transformacija)')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(0, 10)  # Fokus na fiziološki opseg
    
    # Donji graf - Zoom na srčanu frekvenciju (0.5-3 Hz)
    heart_freq_mask = (freq >= 0.5) & (freq <= 3.0)
    freq_zoom = freq[heart_freq_mask]
    spectrum_zoom = spectrum[heart_freq_mask]
    
    ax2.plot(freq_zoom, spectrum_zoom, 'g-', linewidth=2)
    if peak_freq > 0 and 0.5 <= peak_freq <= 3.0:
        ax2.axvline(peak_freq, color='red', linestyle='--', linewidth=2)
        ax2.plot(peak_freq, peak_amp, 'ro', markersize=12)
        
        # Dodaj tekstualni opis
        ax2.text(peak_freq + 0.1, peak_amp, 
                f'{peak_freq:.2f} Hz\n({peak_freq*60:.0f} bpm)', 
                fontsize=12, bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.7))
    
    ax2.set_xlabel('Frekvencija (Hz)')
    ax2.set_ylabel('Amplituda')
    ax2.set_title('Srčana Frekvencija u FFT Spektru (0.5-3 Hz)')
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig_to_base64(fig)

def create_mitbih_comparison_plot(ekg_signal, fs, analysis_results, annotations):
    """
    3. POREĐENJE SA MIT-BIH ANOTACIJAMA
    """
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10))
    
    time_axis = np.arange(len(ekg_signal)) / fs
    
    # Detektovani R-pikovi
    detected_peaks = analysis_results.get('arrhythmia_detection', {}).get('r_peaks', [])
    annotated_peaks = annotations.get('samples', [])
    
    # Konvertuj u int i filtriraj anotacije koje su u opsegu
    detected_peaks = [int(peak) for peak in detected_peaks if int(peak) < len(ekg_signal)]
    annotated_peaks = [int(peak) for peak in annotated_peaks if int(peak) < len(ekg_signal)]
    
    # Gornji graf - Poređenje
    ax1.plot(time_axis, ekg_signal, 'b-', linewidth=1, alpha=0.7, label='EKG Signal')
    
    if detected_peaks:
        detected_array = np.array(detected_peaks, dtype=int)
        ax1.plot(time_axis[detected_array], ekg_signal[detected_array], 
                'ro', markersize=8, label=f'Moj algoritam ({len(detected_peaks)})')
    
    if annotated_peaks:
        annotated_array = np.array(annotated_peaks, dtype=int)
        ax1.plot(time_axis[annotated_array], ekg_signal[annotated_array], 
                'g^', markersize=6, label=f'MIT-BIH ekspert ({len(annotated_peaks)})')
    
    # Analiza poklapanja
    tolerance_samples = int(0.05 * fs)  # 50ms tolerancija
    true_positives = []
    false_positives = list(detected_peaks)
    false_negatives = list(annotated_peaks)
    
    for detected in detected_peaks:
        for annotated in annotated_peaks:
            if abs(detected - annotated) <= tolerance_samples:
                true_positives.append(detected)
                if detected in false_positives:
                    false_positives.remove(detected)
                if annotated in false_negatives:
                    false_negatives.remove(annotated)
                break
    
    # Označi greške
    if false_positives:
        fp_array = np.array(false_positives, dtype=int)
        ax1.plot(time_axis[fp_array], ekg_signal[fp_array], 
                'rx', markersize=12, markeredgewidth=3, label=f'False Positives ({len(false_positives)})')
    
    if false_negatives:
        fn_array = np.array(false_negatives, dtype=int)
        ax1.plot(time_axis[fn_array], ekg_signal[fn_array], 
                'ks', markersize=10, label=f'False Negatives ({len(false_negatives)})')
    
    ax1.set_xlabel('Vreme (s)')
    ax1.set_ylabel('Amplituda')
    ax1.set_title('Poređenje: Moj Algoritam vs MIT-BIH Anotacije')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Donji graf - Statistike
    ax2.axis('off')
    
    # Izračunaj statistike
    precision = len(true_positives) / len(detected_peaks) if detected_peaks else 0
    recall = len(true_positives) / len(annotated_peaks) if annotated_peaks else 0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    stats_text = f"""
    STATISTIKE POREĐENJA (Tolerancija: 50ms)
    
    True Positives:  {len(true_positives)}
    False Positives: {len(false_positives)}
    False Negatives: {len(false_negatives)}
    
    Precision (Preciznost): {precision:.3f} ({precision*100:.1f}%)
    Recall (Osetljivost):   {recall:.3f} ({recall*100:.1f}%)
    F1-Score:               {f1_score:.3f}
    
    Detektovano ukupno:     {len(detected_peaks)}
    MIT-BIH ukupno:         {len(annotated_peaks)}
    Poklapanje:             {len(true_positives)} / {len(annotated_peaks)}
    """
    
    ax2.text(0.1, 0.9, stats_text, transform=ax2.transAxes, fontsize=12, 
            verticalalignment='top', fontfamily='monospace',
            bbox=dict(boxstyle="round,pad=0.5", facecolor="lightblue", alpha=0.8))
    
    plt.tight_layout()
    return fig_to_base64(fig)

def create_processing_pipeline_plot(ekg_signal, fs):
    """
    4. SIGNAL PROCESSING PIPELINE (Z-transformacija)
    """
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    
    # Originalni signal
    time_axis = np.arange(len(ekg_signal)) / fs
    zoom_samples = min(int(5 * fs), len(ekg_signal))  # 5 sekundi
    time_zoom = time_axis[:zoom_samples]
    
    # 1. Originalni signal
    axes[0,0].plot(time_zoom, ekg_signal[:zoom_samples], 'b-', linewidth=1)
    axes[0,0].set_title('1. Originalni EKG Signal')
    axes[0,0].set_xlabel('Vreme (s)')
    axes[0,0].set_ylabel('Amplituda')
    axes[0,0].grid(True, alpha=0.3)
    
    # 2. Bandpass filter (Z-transformacija)
    nyquist = fs / 2
    low = 0.5 / nyquist
    high = 40 / nyquist
    b, a = signal.butter(4, [low, high], btype='band')
    filtered_signal = signal.filtfilt(b, a, ekg_signal)
    
    axes[0,1].plot(time_zoom, filtered_signal[:zoom_samples], 'g-', linewidth=1)
    axes[0,1].set_title('2. Bandpass Filter (0.5-40 Hz)\n(Z-transformacija)')
    axes[0,1].set_xlabel('Vreme (s)')
    axes[0,1].set_ylabel('Amplituda')
    axes[0,1].grid(True, alpha=0.3)
    
    # 3. High-pass za baseline removal
    b_hp, a_hp = signal.butter(2, 0.5/nyquist, btype='high')
    baseline_removed = signal.filtfilt(b_hp, a_hp, filtered_signal)
    
    axes[1,0].plot(time_zoom, baseline_removed[:zoom_samples], 'r-', linewidth=1)
    axes[1,0].set_title('3. Baseline Removal\n(High-pass 0.5 Hz)')
    axes[1,0].set_xlabel('Vreme (s)')
    axes[1,0].set_ylabel('Amplituda')
    axes[1,0].grid(True, alpha=0.3)
    
    # 4. Filter response (Z-domain)
    w, h = signal.freqz(b, a, worN=2000)
    freq_response = w * fs / (2 * np.pi)
    
    axes[1,1].plot(freq_response, np.abs(h), 'purple', linewidth=2)
    axes[1,1].set_title('4. Filter Response (Z-domen)\nBandpass 0.5-40 Hz')
    axes[1,1].set_xlabel('Frekvencija (Hz)')
    axes[1,1].set_ylabel('Magnitude')
    axes[1,1].grid(True, alpha=0.3)
    axes[1,1].set_xlim(0, 50)
    
    plt.tight_layout()
    return fig_to_base64(fig)

def fig_to_base64(fig):
    """Konvertuje matplotlib figuru u base64 string"""
    buffer = io.BytesIO()
    fig.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.getvalue()).decode()
    buffer.close()
    plt.close(fig)  # Oslobodi memoriju
    return image_base64