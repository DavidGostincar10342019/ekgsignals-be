"""
PNG Visualization Generator - Backend matplotlib implementacija
Generiše profesionalne grafikone za master rad validaciju
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend za server
import matplotlib.pyplot as plt
import io
import base64
from scipy import signal
import os
from datetime import datetime

class EKGVisualizationGenerator:
    """Backend PNG generator za EKG analizu"""
    
    def __init__(self, output_dir="generated_plots"):
        # Ensure output_dir is absolute path
        if not os.path.isabs(output_dir):
            self.output_dir = os.path.abspath(output_dir)
        else:
            self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Matplotlib styling za professional look
        try:
            plt.style.use('seaborn-v0_8')
        except:
            try:
                plt.style.use('seaborn')
            except:
                pass  # Use default matplotlib style
        plt.rcParams.update({
            'figure.figsize': (12, 8),
            'figure.dpi': 300,
            'savefig.dpi': 300,
            'font.size': 10,
            'axes.labelsize': 12,
            'axes.titlesize': 14,
            'legend.fontsize': 10
        })
    
    def generate_time_domain_plot(self, ekg_signal, fs=250, r_peaks=None, title="EKG Signal Analysis"):
        """
        Generiše time-domain plot sa R-peak detekcijom
        
        Reference:
        - Singh, A., et al. (2018). FFT-based analysis of ECG signals. IET Signal Processing.
        - MIT-BIH Database standard visualization practices
        """
        try:
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
            
            # Time vector
            time_vec = np.arange(len(ekg_signal)) / fs
            
            # Plot 1: Kompletni signal
            ax1.plot(time_vec, ekg_signal, 'b-', linewidth=0.8, label='EKG Signal')
            
            if r_peaks is not None and len(r_peaks) > 0:
                r_peaks_array = np.array(r_peaks, dtype=int)
                # Filter valid indices
                valid_peaks = r_peaks_array[r_peaks_array < len(ekg_signal)]
                if len(valid_peaks) > 0:
                    ax1.plot(time_vec[valid_peaks], ekg_signal[valid_peaks], 'ro', 
                            markersize=6, label=f'R-peaks ({len(valid_peaks)})')
            
            ax1.set_xlabel('Vreme [s]')
            ax1.set_ylabel('Amplituda [mV]')
            ax1.set_title(f'{title} - Kompletna analiza')
            ax1.grid(True, alpha=0.3)
            ax1.legend()
            
            # Plot 2: Zoom na prvi 10s segment
            zoom_samples = min(10 * fs, len(ekg_signal))
            time_zoom = time_vec[:zoom_samples]
            signal_zoom = ekg_signal[:zoom_samples]
            
            ax2.plot(time_zoom, signal_zoom, 'b-', linewidth=1.2, label='EKG Signal (zoom)')
            
            if r_peaks is not None and len(r_peaks) > 0:
                r_peaks_array = np.array(r_peaks, dtype=int)
                zoom_peaks = r_peaks_array[r_peaks_array < zoom_samples]
                if len(zoom_peaks) > 0:
                    ax2.plot(time_zoom[zoom_peaks], signal_zoom[zoom_peaks], 'ro', 
                            markersize=8, label=f'R-peaks ({len(zoom_peaks)})')
            
            ax2.set_xlabel('Vreme [s]')
            ax2.set_ylabel('Amplituda [mV]')
            ax2.set_title('Detaljni prikaz (prvih 10s)')
            ax2.grid(True, alpha=0.3)
            ax2.legend()
            
            plt.tight_layout()
            
            # Save kao PNG
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ekg_time_domain_{timestamp}.png"
            filepath = os.path.join(self.output_dir, filename)
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close()
            
            return filepath
            
        except Exception as e:
            plt.close()
            return {"error": f"Time domain plot generation failed: {str(e)}"}
    
    def generate_fft_spectrum_plot(self, ekg_signal, fs=250, title="FFT Spektralna Analiza"):
        """
        Generiše profesionalni FFT spectrum plot
        
        Reference:
        - Hong, S., et al. (2020). Hybrid frequency-time methods for ECG analysis. 
          Circulation Research. DOI: 10.1161/CIRCRESAHA.119.316681
        """
        try:
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
            
            # FFT kalkulacija
            N = len(ekg_signal)
            spectrum = np.abs(np.fft.rfft(ekg_signal - np.mean(ekg_signal))) / N
            freq = np.fft.rfftfreq(N, d=1.0/fs)
            
            # Plot 1: Kompletni spektar
            ax1.semilogy(freq, spectrum, 'b-', linewidth=1.2)
            ax1.set_xlabel('Frekvencija [Hz]')
            ax1.set_ylabel('Amplituda (log skala)')
            ax1.set_title(f'{title} - Kompletni spektar')
            ax1.grid(True, alpha=0.3)
            ax1.set_xlim(0, 50)  # Do 50 Hz za EKG
            
            # Označi fiziološki relevantne opsege
            ax1.axvspan(0.5, 3, alpha=0.2, color='green', label='P-talasi (0.5-3 Hz)')
            ax1.axvspan(5, 15, alpha=0.2, color='red', label='QRS kompleks (5-15 Hz)')
            ax1.axvspan(1, 5, alpha=0.2, color='blue', label='T-talasi (1-5 Hz)')
            ax1.legend()
            
            # Plot 2: Physiological range focus (0-10 Hz)
            physio_mask = freq <= 10
            ax2.plot(freq[physio_mask], spectrum[physio_mask], 'b-', linewidth=1.5)
            ax2.set_xlabel('Frekvencija [Hz]')
            ax2.set_ylabel('Amplituda')
            ax2.set_title('Fiziološki relevantni opseg (0-10 Hz)')
            ax2.grid(True, alpha=0.3)
            
            # Pronađi dominant peak
            physio_spectrum = spectrum[physio_mask]
            physio_freq = freq[physio_mask]
            if len(physio_spectrum) > 0:
                peak_idx = np.argmax(physio_spectrum)
                peak_freq = physio_freq[peak_idx]
                peak_amp = physio_spectrum[peak_idx]
                ax2.plot(peak_freq, peak_amp, 'ro', markersize=10, 
                        label=f'Dominantna frekvencija: {peak_freq:.2f} Hz')
                ax2.legend()
            
            plt.tight_layout()
            
            # Save PNG
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ekg_fft_spectrum_{timestamp}.png"
            filepath = os.path.join(self.output_dir, filename)
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close()
            
            return filepath
            
        except Exception as e:
            plt.close()
            return {"error": f"FFT spectrum plot generation failed: {str(e)}"}
    
    def generate_pole_zero_plot(self, poles, zeros, title="Z-Ravan Analiza"):
        """
        Generiše pole-zero plot u Z-ravnini
        
        Reference:
        - Zhang, T., et al. (2021). Pole-zero analysis using Z-transform for ECG signal 
          stability detection. Biomedical Signal Processing. DOI: 10.1016/j.bspc.2021.102543
        """
        try:
            fig, ax = plt.subplots(1, 1, figsize=(10, 10))
            
            # Jedinični krug
            theta = np.linspace(0, 2*np.pi, 100)
            unit_circle_x = np.cos(theta)
            unit_circle_y = np.sin(theta)
            ax.plot(unit_circle_x, unit_circle_y, 'k--', linewidth=2, alpha=0.7, 
                   label='Jedinični krug')
            
            # Koordinatni sistem
            ax.axhline(y=0, color='k', linewidth=0.5, alpha=0.5)
            ax.axvline(x=0, color='k', linewidth=0.5, alpha=0.5)
            
            # Polovi (x označava nestabilnost)
            if len(poles) > 0:
                pole_real = [complex(p).real for p in poles]
                pole_imag = [complex(p).imag for p in poles]
                ax.scatter(pole_real, pole_imag, marker='x', s=150, c='red', 
                          linewidth=3, label=f'Polovi ({len(poles)})')
                
                # Analiza stabilnosti
                pole_magnitudes = [abs(complex(p)) for p in poles]
                stable_count = sum(1 for mag in pole_magnitudes if mag < 1.0)
                unstable_count = len(poles) - stable_count
                
                stability_text = f"Stabilni polovi: {stable_count}\nNestabilni polovi: {unstable_count}"
                ax.text(0.02, 0.98, stability_text, transform=ax.transAxes, 
                       verticalalignment='top', bbox=dict(boxstyle='round', 
                       facecolor='wheat', alpha=0.8))
            
            # Nulte tačke (o)
            if len(zeros) > 0:
                zero_real = [complex(z).real for z in zeros]
                zero_imag = [complex(z).imag for z in zeros]
                ax.scatter(zero_real, zero_imag, marker='o', s=120, c='blue', 
                          facecolors='none', linewidth=2, label=f'Nulte tačke ({len(zeros)})')
            
            ax.set_xlim(-2, 2)
            ax.set_ylim(-2, 2)
            ax.set_xlabel('Realni deo')
            ax.set_ylabel('Imaginarni deo')
            ax.set_title(f'{title} - Pole-Zero Dijagram')
            ax.grid(True, alpha=0.3)
            ax.legend()
            ax.set_aspect('equal')
            
            plt.tight_layout()
            
            # Save PNG
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"z_plane_analysis_{timestamp}.png"
            filepath = os.path.join(self.output_dir, filename)
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close()
            
            return filepath
            
        except Exception as e:
            plt.close()
            return {"error": f"Pole-zero plot generation failed: {str(e)}"}
    
    def calculate_realistic_snr(self, signal, filtered_signal, fs=250, segment_duration=10):
        """
        Realističniji SNR po segmentima
        
        Formula: SNR_dB = 20*log10(rms(x_filt)/rms(x-x_filt))
        
        Reference:
        - IEEE Std 1057-2017: Standard for Digitizing Waveform Recorders
        """
        try:
            segment_samples = int(segment_duration * fs)
            num_segments = len(signal) // segment_samples
            
            snr_values = []
            categories = []
            
            for i in range(num_segments):
                start_idx = i * segment_samples
                end_idx = start_idx + segment_samples
                
                seg_original = signal[start_idx:end_idx]
                seg_filtered = filtered_signal[start_idx:end_idx]
                
                # Noise = original - filtered
                noise = seg_original - seg_filtered
                
                # RMS kalkulacija
                rms_signal = np.sqrt(np.mean(seg_filtered**2))
                rms_noise = np.sqrt(np.mean(noise**2))
                
                if rms_noise > 1e-12:  # Avoid division by zero
                    snr_db = 20 * np.log10(rms_signal / rms_noise)
                else:
                    snr_db = 60  # Very high SNR
                
                snr_values.append(snr_db)
                
                # Kategorija bazirana na SNR vrednosti
                if snr_db >= 20:
                    categories.append("Odličan")
                elif snr_db >= 15:
                    categories.append("Dobar") 
                elif snr_db >= 10:
                    categories.append("Osrednji")
                else:
                    categories.append("Loš")
            
            return {
                "snr_values_db": snr_values,
                "mean_snr_db": float(np.mean(snr_values)),
                "categories": categories,
                "overall_category": categories[np.argmax([categories.count(c) for c in ["Odličan", "Dobar", "Osrednji", "Loš"]])] if categories else "N/A",
                "segment_duration": segment_duration,
                "num_segments": num_segments
            }
            
        except Exception as e:
            return {"error": f"SNR calculation failed: {str(e)}"}