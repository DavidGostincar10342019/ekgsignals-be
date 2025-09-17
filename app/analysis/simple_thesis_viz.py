"""
Jednostavne, sigurne vizuelizacije za master rad
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64

def create_simple_thesis_visualizations(ekg_signal, fs, analysis_results):
    """
    Kreira jednostavne vizuelizacije koje sigurno rade
    """
    visualizations = {}
    
    try:
        # 1. EKG Signal sa R-pikovima
        visualizations['ekg_with_peaks'] = create_simple_ekg_plot(ekg_signal, fs, analysis_results)
        
        # 2. FFT Spektar
        visualizations['fft_spectrum'] = create_simple_fft_plot(ekg_signal, fs, analysis_results)
        
        # 3. Signal processing steps
        visualizations['processing_steps'] = create_simple_processing_plot(ekg_signal, fs)
        
        return visualizations
        
    except Exception as e:
        print(f"ERROR in simple visualizations: {str(e)}")
        return {"error": str(e)}

def create_simple_ekg_plot(ekg_signal, fs, analysis_results):
    """Jednostavan EKG plot sa R-pikovima"""
    try:
        fig, ax = plt.subplots(1, 1, figsize=(12, 6))
        
        # Ograniči na prvih 10 sekundi
        max_samples = min(int(10 * fs), len(ekg_signal))
        time_axis = np.arange(max_samples) / fs
        signal_segment = ekg_signal[:max_samples]
        
        # Plot signal
        ax.plot(time_axis, signal_segment, 'b-', linewidth=1, label='EKG Signal')
        
        # R-pikovi
        r_peaks = analysis_results.get('arrhythmia_detection', {}).get('r_peaks', [])
        if r_peaks:
            # Filtriraj R-pikove koji su u opsegu
            valid_peaks = [peak for peak in r_peaks if isinstance(peak, (int, float)) and 0 <= peak < max_samples]
            if valid_peaks:
                peak_indices = [int(peak) for peak in valid_peaks]
                ax.scatter(time_axis[peak_indices], signal_segment[peak_indices], 
                          color='red', s=50, marker='o', label=f'R-pikovi ({len(peak_indices)})', zorder=5)
        
        ax.set_xlabel('Vreme (s)')
        ax.set_ylabel('Amplituda')
        ax.set_title('EKG Signal sa Detektovanim R-pikovima (Master Rad Vizuelizacija)')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return fig_to_base64(fig)
        
    except Exception as e:
        print(f"ERROR in EKG plot: {str(e)}")
        return None

def create_simple_fft_plot(ekg_signal, fs, analysis_results):
    """Jednostavan FFT spektar"""
    try:
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
        
        # Ukloni DC i uradi FFT
        signal_no_dc = ekg_signal - np.mean(ekg_signal)
        n = len(signal_no_dc)
        freq = np.fft.rfftfreq(n, d=1.0/fs)
        spectrum = np.abs(np.fft.rfft(signal_no_dc)) / n
        
        # Gornji graf - pun spektar
        ax1.plot(freq, spectrum, 'b-', linewidth=1)
        ax1.set_xlabel('Frekvencija (Hz)')
        ax1.set_ylabel('Amplituda')
        ax1.set_title('FFT Spektar EKG Signala (Furijeova Transformacija)')
        ax1.grid(True, alpha=0.3)
        ax1.set_xlim(0, 10)
        
        # Označi dominantnu frekvenciju
        fft_data = analysis_results.get('fft_analysis', {})
        peak_freq = fft_data.get('peak_frequency_hz', 0)
        if peak_freq > 0:
            ax1.axvline(peak_freq, color='red', linestyle='--', linewidth=2, 
                       label=f'Dominantna: {peak_freq:.2f} Hz')
            ax1.legend()
        
        # Donji graf - zoom na srčanu frekvenciju
        heart_range = (freq >= 0.5) & (freq <= 3.0)
        if np.any(heart_range):
            ax2.plot(freq[heart_range], spectrum[heart_range], 'g-', linewidth=2)
            if peak_freq > 0 and 0.5 <= peak_freq <= 3.0:
                ax2.axvline(peak_freq, color='red', linestyle='--', linewidth=2)
                ax2.text(peak_freq + 0.1, max(spectrum[heart_range]) * 0.8, 
                        f'{peak_freq:.2f} Hz\n({peak_freq*60:.0f} bpm)', 
                        bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.7))
        
        ax2.set_xlabel('Frekvencija (Hz)')
        ax2.set_ylabel('Amplituda')
        ax2.set_title('Srčana Frekvencija (0.5-3 Hz)')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return fig_to_base64(fig)
        
    except Exception as e:
        print(f"ERROR in FFT plot: {str(e)}")
        return None

def create_simple_processing_plot(ekg_signal, fs):
    """Signal processing koraci"""
    try:
        from scipy import signal as scipy_signal
        
        fig, axes = plt.subplots(2, 2, figsize=(12, 8))
        
        # Ograniči na 5 sekundi
        max_samples = min(int(5 * fs), len(ekg_signal))
        time_axis = np.arange(max_samples) / fs
        original = ekg_signal[:max_samples]
        
        # 1. Originalni signal
        axes[0,0].plot(time_axis, original, 'b-', linewidth=1)
        axes[0,0].set_title('1. Originalni EKG Signal')
        axes[0,0].set_ylabel('Amplituda')
        axes[0,0].grid(True, alpha=0.3)
        
        # 2. Bandpass filtriran signal
        try:
            nyquist = fs / 2
            low = 0.5 / nyquist
            high = 40 / nyquist
            b, a = scipy_signal.butter(4, [low, high], btype='band')
            filtered = scipy_signal.filtfilt(b, a, ekg_signal)
            filtered_segment = filtered[:max_samples]
            
            axes[0,1].plot(time_axis, filtered_segment, 'g-', linewidth=1)
            axes[0,1].set_title('2. Bandpass Filter (0.5-40 Hz)')
            axes[0,1].set_ylabel('Amplituda')
            axes[0,1].grid(True, alpha=0.3)
            
            # 3. Baseline removal
            b_hp, a_hp = scipy_signal.butter(2, 0.5/nyquist, btype='high')
            baseline_removed = scipy_signal.filtfilt(b_hp, a_hp, filtered)
            baseline_segment = baseline_removed[:max_samples]
            
            axes[1,0].plot(time_axis, baseline_segment, 'r-', linewidth=1)
            axes[1,0].set_title('3. Baseline Removal (High-pass)')
            axes[1,0].set_xlabel('Vreme (s)')
            axes[1,0].set_ylabel('Amplituda')
            axes[1,0].grid(True, alpha=0.3)
            
            # 4. Filter response
            w, h = scipy_signal.freqz(b, a, worN=1000)
            freq_response = w * fs / (2 * np.pi)
            
            axes[1,1].plot(freq_response, np.abs(h), 'purple', linewidth=2)
            axes[1,1].set_title('4. Filter Response (Z-domen)')
            axes[1,1].set_xlabel('Frekvencija (Hz)')
            axes[1,1].set_ylabel('Magnitude')
            axes[1,1].grid(True, alpha=0.3)
            axes[1,1].set_xlim(0, 50)
            
        except Exception as filter_error:
            print(f"Filter error: {filter_error}")
            # Fallback - prikaži originalni signal
            for i, ax in enumerate([axes[0,1], axes[1,0], axes[1,1]]):
                ax.plot(time_axis, original, 'b-', linewidth=1)
                ax.set_title(f'Signal Processing Step {i+2}')
                ax.grid(True, alpha=0.3)
        
        plt.suptitle('Signal Processing Pipeline (Z-transformacija)', fontsize=14)
        plt.tight_layout()
        return fig_to_base64(fig)
        
    except Exception as e:
        print(f"ERROR in processing plot: {str(e)}")
        return None

def fig_to_base64(fig):
    """Konvertuje matplotlib figuru u base64 string"""
    try:
        buffer = io.BytesIO()
        fig.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        buffer.close()
        plt.close(fig)
        return image_base64
    except Exception as e:
        print(f"ERROR in fig_to_base64: {str(e)}")
        plt.close(fig)
        return None