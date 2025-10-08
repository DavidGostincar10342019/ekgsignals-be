"""
Konvertovanje sirovih EKG signala u slike
Omogućava testiranje aplikacije kroz punu petlju: sirovi podaci -> slika -> analiza
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import io
import base64
from PIL import Image
import cv2

def create_ekg_image_from_signal(signal, fs=250, duration_seconds=None, style="clinical"):
    """
    Kreira sliku EKG-a iz sirovih podataka
    
    Args:
        signal: Lista ili numpy array sa EKG signalom
        fs: Frekvencija uzorkovanja (Hz)
        duration_seconds: Koliko sekundi signala da prikaže (None = ceo signal)
        style: "clinical" (medicinski papir) ili "monitor" (monitor stil)
    
    Returns:
        dict sa 'image_base64', 'image_pil', 'metadata'
    """
    signal = np.array(signal)
    
    # Ograniči trajanje ako je potrebno
    if duration_seconds:
        max_samples = int(duration_seconds * fs)
        if len(signal) > max_samples:
            signal = signal[:max_samples]
    
    # Kreiranje vremenske ose
    t = np.linspace(0, len(signal) / fs, len(signal))
    
    if style == "clinical":
        return _create_clinical_ekg_image(signal, t, fs)
    else:
        return _create_monitor_ekg_image(signal, t, fs)

def _create_clinical_ekg_image(signal, t, fs):
    """Kreira sliku u stilu medicinskog EKG papira - optimizovano za analizu"""
    
    # POBOLJŠANO: Veća figura za bolju čitljivost
    fig, ax = plt.subplots(figsize=(16, 10), dpi=200)  # Veća rezolucija
    
    # POBOLJŠANO: Preprocess signal za bolju vizibilnost
    signal_processed = _enhance_signal_for_analysis(signal, fs)
    
    # Medicinski EKG papir pozadina - tamniji grid za kontrast
    _add_enhanced_ekg_grid(ax, t[-1])
    
    # POBOLJŠANO: Amplifikacija signala za jasniju analizu
    signal_mv = signal_processed * 2.0  # Pojačaj signal 2x
    
    # Crtanje EKG signala sa većom linijom
    ax.plot(t, signal_mv, 'k-', linewidth=2.5, alpha=0.95)
    
    # Medicinski stil osa
    ax.set_xlim(0, t[-1])
    ax.set_ylim(-2, 2)
    ax.set_xlabel('Vreme (s)', fontsize=10)
    ax.set_ylabel('Amplituda (mV)', fontsize=10)
    
    # Uklanjanje margina
    plt.tight_layout()
    plt.subplots_adjust(left=0.08, right=0.95, top=0.95, bottom=0.08)
    
    # Dodavanje medicinskih anotacija
    _add_medical_annotations(ax, signal_mv, t, fs)
    
    return _fig_to_image_data(fig)

def _create_monitor_ekg_image(signal, t, fs):
    """Kreira sliku u stilu monitora/displeja"""
    
    fig, ax = plt.subplots(figsize=(12, 6), dpi=150, facecolor='black')
    ax.set_facecolor('black')
    
    # Monitor stil - zelena linija na crnoj pozadini
    ax.plot(t, signal, '#00FF00', linewidth=2.5, alpha=0.9)
    
    # Monitor grid
    _add_monitor_grid(ax, t[-1])
    
    # Monitor stil osa
    ax.set_xlim(0, t[-1])
    ax.set_ylim(np.min(signal) * 1.2, np.max(signal) * 1.2)
    ax.tick_params(colors='white', labelsize=8)
    ax.set_xlabel('Vreme (s)', color='white', fontsize=10)
    ax.set_ylabel('Amplituda', color='white', fontsize=10)
    
    plt.tight_layout()
    
    return _fig_to_image_data(fig)

def _enhance_signal_for_analysis(signal, fs):
    """Poboljšava signal za bolju analizu - amplifikuje R-pikove"""
    
    signal = np.array(signal)
    enhanced_signal = signal.copy()
    
    # Jednostavna detekcija R-pikova za amplifikaciju
    # Pronađi lokalne maksimume
    threshold = np.mean(signal) + 2 * np.std(signal)
    
    for i in range(2, len(signal) - 2):
        if (signal[i] > signal[i-1] and signal[i] > signal[i+1] and 
            signal[i] > threshold):
            # Amplifikuj R-pik i okolinu
            enhanced_signal[i-2:i+3] *= 1.5  # 50% amplifikacija za R-pikove
    
    return enhanced_signal

def _add_enhanced_ekg_grid(ax, duration):
    """Dodaje poboljšanu mrežu za bolju čitljivost"""
    
    # POBOLJŠANO: Tamniji grid za bolji kontrast
    major_time_spacing = 0.2  # 5 velikih kockica = 1 sekunda
    major_voltage_spacing = 1.0  # Veći razmak za jasniju sliku
    
    minor_time_spacing = 0.04
    minor_voltage_spacing = 0.2  # Veći minor spacing
    
    # Vertikalne linije (vreme) - tamniji
    for t in np.arange(0, duration + minor_time_spacing, minor_time_spacing):
        alpha = 0.9 if abs(t % major_time_spacing) < 0.01 else 0.4
        linewidth = 1.5 if abs(t % major_time_spacing) < 0.01 else 0.7
        color = '#CC6666' if abs(t % major_time_spacing) < 0.01 else '#DD9999'
        ax.axvline(t, color=color, alpha=alpha, linewidth=linewidth, zorder=0)
    
    # Horizontalne linije (napon) - tamniji
    for v in np.arange(-4, 4.1, minor_voltage_spacing):
        alpha = 0.9 if abs(v % major_voltage_spacing) < 0.01 else 0.4
        linewidth = 1.5 if abs(v % major_voltage_spacing) < 0.01 else 0.7
        color = '#CC6666' if abs(v % major_voltage_spacing) < 0.01 else '#DD9999'
        ax.axhline(v, color=color, alpha=alpha, linewidth=linewidth, zorder=0)

def _add_ekg_grid(ax, duration):
    """Zadržana originalna funkcija za kompatibilnost"""
    return _add_enhanced_ekg_grid(ax, duration)

def _add_monitor_grid(ax, duration):
    """Dodaje mrežu u stilu monitora"""
    
    # Monitor grid - tamniji
    time_spacing = 0.2
    voltage_range = ax.get_ylim()
    voltage_spacing = (voltage_range[1] - voltage_range[0]) / 10
    
    for t in np.arange(0, duration + time_spacing, time_spacing):
        ax.axvline(t, color='#004400', alpha=0.5, linewidth=0.8)
    
    for v in np.arange(voltage_range[0], voltage_range[1], voltage_spacing):
        ax.axhline(v, color='#004400', alpha=0.5, linewidth=0.8)

def _add_medical_annotations(ax, signal, t, fs):
    """Dodaje medicinske anotacije na EKG"""
    
    # Dodavanje skale referentne (1mV signal)
    scale_x = t[-1] * 0.02
    scale_y = 1.5
    
    # 1mV skala blok
    scale_signal = np.array([0, 0, 1, 1, 0])
    scale_time = np.linspace(scale_x, scale_x + 0.2, len(scale_signal))
    ax.plot(scale_time, scale_signal + scale_y, 'k-', linewidth=2)
    ax.text(scale_x + 0.1, scale_y + 1.2, '1mV', ha='center', va='bottom', fontsize=8)
    
    # Vremenska skala
    ax.text(t[-1] * 0.98, -1.8, f'{len(signal)/fs:.1f}s, {fs}Hz', 
            ha='right', va='bottom', fontsize=8, 
            bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8))

def _fig_to_image_data(fig):
    """Konvertuje matplotlib figuru u različite formate"""
    
    # Matplotlib -> PIL Image
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', 
                facecolor=fig.get_facecolor(), edgecolor='none')
    buf.seek(0)
    
    # PIL Image
    pil_image = Image.open(buf)
    
    # Base64 string za web
    buf.seek(0)
    image_base64 = base64.b64encode(buf.read()).decode('utf-8')
    
    # OpenCV format (za testiranje kroz postojeću logiku)
    opencv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
    
    # Metadata
    metadata = {
        'width': pil_image.width,
        'height': pil_image.height,
        'format': 'PNG',
        'mode': pil_image.mode
    }
    
    plt.close(fig)  # Oslobodi memoriju
    
    return {
        'image_base64': f"data:image/png;base64,{image_base64}",
        'image_pil': pil_image,
        'image_opencv': opencv_image,
        'metadata': metadata
    }

def test_signal_to_image_conversion(signal, fs=250):
    """
    Testira konverziju signala u sliku i nazad
    
    Returns:
        dict sa rezultatima testiranja
    """
    print("🔄 Testiranje Signal -> Slika -> Analiza...")
    
    try:
        # 1. Kreiraj sliku iz signala
        print(f"DEBUG: Creating image from signal, len={len(signal)}")
        image_data = create_ekg_image_from_signal(signal, fs, style="clinical")
        print("DEBUG: Image created successfully")
        
        # 2. Sačuvaj sliku za debug (opciono)
        # image_data['image_pil'].save('tmp_rovodev_generated_ekg.png')
        
        # 3. Testiraj kroz postojeću logiku obrade slike
        from .image_processing import process_ekg_image
        
        try:
            print("DEBUG: Processing EKG image...")
            # Konvertuj nazad kroz postojeću logiku (preskačemo validaciju za test slike)
            analysis_result = process_ekg_image(image_data['image_base64'], skip_validation=True)
            print("DEBUG: Image processing completed")
            
            if 'error' in analysis_result:
                return {
                    'success': False,
                    'error': analysis_result['error'],
                    'image_generated': True
                }
            
            extracted_signal = analysis_result['signal']
            print(f"DEBUG: Extracted signal, len={len(extracted_signal)}")
            
            # Poredi originalni i ekstraktovani signal
            print("DEBUG: Comparing signals...")
            comparison = compare_signals(signal, extracted_signal, fs)
            print("DEBUG: Signal comparison completed")
            
            return {
                'success': True,
                'image_generated': True,
                'signal_extracted': True,
                'original_length': len(signal),
                'extracted_length': len(extracted_signal),
                'comparison': comparison,
                'image_metadata': image_data['metadata']
            }
            
        except Exception as e:
            print(f"DEBUG: Error in image processing: {e}")
            return {
                'success': False,
                'error': str(e),
                'image_generated': True,
                'signal_extracted': False
            }
    except Exception as e:
        print(f"DEBUG: Error in image creation: {e}")
        return {
            'success': False,
            'error': str(e),
            'image_generated': False,
            'signal_extracted': False
        }

def compare_signals(original, extracted, fs):
    """Poredi originalni i ekstraktovani signal sa POBOLJŠANOM analizom"""
    
    original = np.array(original)
    extracted = np.array(extracted)
    
    # POBOLJŠANO: Resample na istu dužinu PRVO, pa onda normalizuj
    if len(original) != len(extracted):
        min_len = min(len(original), len(extracted))
        max_len = max(len(original), len(extracted))
        target_len = min_len  # Koristi kraći signal kao referentu
        
        if len(original) > len(extracted):
            from scipy import signal as scipy_signal
            original = scipy_signal.resample(original, target_len)
        elif len(extracted) > len(original):
            from scipy import signal as scipy_signal
            extracted = scipy_signal.resample(extracted, target_len)
    
    # POBOLJŠANO: Ukloni DC component prvo
    original = original - np.mean(original)
    extracted = extracted - np.mean(extracted)
    
    # POBOLJŠANO: Normalizuj sa robusnom metodom
    orig_std = np.std(original)
    extr_std = np.std(extracted)
    
    # Ako je std previše mali, ne normalizuj (verovatno konstantan signal)
    if orig_std > 1e-6:
        orig_norm = original / orig_std
    else:
        orig_norm = original
        
    if extr_std > 1e-6:
        extr_norm = extracted / extr_std
    else:
        extr_norm = extracted
    
    # POBOLJŠANO: Pokušaj različite metode korelacije
    correlation = 0.0
    
    try:
        if len(orig_norm) > 3 and len(extr_norm) > 3:  # Minimum 4 tačke
            # Metod 1: Pearson korelacija
            if np.var(orig_norm) > 1e-10 and np.var(extr_norm) > 1e-10:
                correlation = np.corrcoef(orig_norm, extr_norm)[0, 1]
                
                # Ako je korelacija NaN ili premala, pokušaj alternative
                if np.isnan(correlation) or abs(correlation) < 0.01:
                    # Metod 2: Cross-correlation peak
                    xcorr = np.correlate(orig_norm, extr_norm, mode='full')
                    max_xcorr = np.max(xcorr)
                    norm_factor = np.sqrt(np.sum(orig_norm**2) * np.sum(extr_norm**2))
                    if norm_factor > 1e-10:
                        correlation = max_xcorr / norm_factor
                    
                    # Metod 3: Cosine similarity kao fallback
                    if np.isnan(correlation) or abs(correlation) < 0.01:
                        dot_product = np.dot(orig_norm, extr_norm)
                        norm_orig = np.linalg.norm(orig_norm)
                        norm_extr = np.linalg.norm(extr_norm)
                        if norm_orig > 1e-10 and norm_extr > 1e-10:
                            correlation = dot_product / (norm_orig * norm_extr)
                        else:
                            correlation = 0.0
                            
            # Osiguraj da je korelacija u validnom opsegu
            if np.isnan(correlation) or np.isinf(correlation):
                correlation = 0.0
            else:
                correlation = np.clip(correlation, -1.0, 1.0)
                
    except Exception as e:
        print(f"DEBUG: Correlation calculation error: {e}")
        correlation = 0.0
    
    # POBOLJŠANO: RMSE sa normalizacijom
    try:
        rmse = np.sqrt(np.mean((orig_norm - extr_norm) ** 2))
        if np.isnan(rmse) or np.isinf(rmse):
            rmse = 1.0  # Worst case
    except:
        rmse = 1.0
    
    # POBOLJŠANO: Similarity score sa boljom formulom
    similarity_score = max(0, correlation * (1 - min(rmse / 2, 1.0)))  # RMSE može biti > 1
    
    return {
        'correlation': float(correlation),
        'rmse': float(rmse),
        'similarity_score': float(similarity_score),
        'length_match': len(original) == len(extracted)
    }

def generate_test_ekg_images(output_dir="test_images"):
    """Generiše različite test EKG slike za razvoj"""
    
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    test_cases = [
        ("normal_rhythm", create_normal_ekg_signal()),
        ("fast_heart_rate", create_tachycardia_signal()),
        ("slow_heart_rate", create_bradycardia_signal()),
        ("irregular_rhythm", create_irregular_signal())
    ]
    
    results = {}
    
    for name, (signal, fs) in test_cases:
        print(f"📝 Generišem {name}...")
        
        # Clinical stil
        clinical_img = create_ekg_image_from_signal(signal, fs, style="clinical")
        clinical_path = os.path.join(output_dir, f"{name}_clinical.png")
        clinical_img['image_pil'].save(clinical_path)
        
        # Monitor stil
        monitor_img = create_ekg_image_from_signal(signal, fs, style="monitor")
        monitor_path = os.path.join(output_dir, f"{name}_monitor.png")
        monitor_img['image_pil'].save(monitor_path)
        
        results[name] = {
            'clinical_image': clinical_path,
            'monitor_image': monitor_path,
            'signal_length': len(signal),
            'duration_seconds': len(signal) / fs,
            'fs': fs
        }
    
    print(f"✅ Generisano {len(test_cases)} test slika u {output_dir}/")
    return results

def create_normal_ekg_signal(duration=10, fs=250):
    """Kreira normalan EKG signal"""
    t = np.linspace(0, duration, int(fs * duration))
    
    # Bazni signal
    signal = 0.1 * np.sin(2 * np.pi * 1.2 * t)
    
    # R-pikovi (normalna frekvencija 70 BPM)
    rr_interval = 60 / 70
    for beat_time in np.arange(0.5, duration, rr_interval):
        beat_idx = int(beat_time * fs)
        if beat_idx < len(signal) - 5:
            # QRS kompleks
            signal[beat_idx-2:beat_idx+3] += [0.1, 0.3, 1.0, 0.4, 0.1]
    
    return signal, fs

def create_tachycardia_signal(duration=10, fs=250):
    """Kreira tahikardni EKG signal (brz ritam)"""
    t = np.linspace(0, duration, int(fs * duration))
    signal = 0.1 * np.sin(2 * np.pi * 1.5 * t)
    
    # Brži R-pikovi (120 BPM)
    rr_interval = 60 / 120
    for beat_time in np.arange(0.3, duration, rr_interval):
        beat_idx = int(beat_time * fs)
        if beat_idx < len(signal) - 5:
            signal[beat_idx-2:beat_idx+3] += [0.08, 0.25, 0.9, 0.35, 0.08]
    
    return signal, fs

def create_bradycardia_signal(duration=10, fs=250):
    """Kreira bradikardni EKG signal (spor ritam)"""
    t = np.linspace(0, duration, int(fs * duration))
    signal = 0.1 * np.sin(2 * np.pi * 0.8 * t)
    
    # Sporiji R-pikovi (45 BPM)
    rr_interval = 60 / 45
    for beat_time in np.arange(0.7, duration, rr_interval):
        beat_idx = int(beat_time * fs)
        if beat_idx < len(signal) - 5:
            signal[beat_idx-2:beat_idx+3] += [0.12, 0.35, 1.1, 0.45, 0.12]
    
    return signal, fs

def create_irregular_signal(duration=10, fs=250):
    """Kreira nepravilan EKG signal (aritmija)"""
    t = np.linspace(0, duration, int(fs * duration))
    signal = 0.1 * np.sin(2 * np.pi * 1.0 * t)
    
    # Nepravilni R-pikovi
    irregular_intervals = [0.8, 0.6, 1.2, 0.7, 0.9, 1.1, 0.5, 1.0]
    beat_time = 0.5
    
    for interval in irregular_intervals * 3:  # Ponovi pattern
        beat_time += interval
        if beat_time < duration:
            beat_idx = int(beat_time * fs)
            if beat_idx < len(signal) - 5:
                # Variranje amplitude također
                amp = 0.8 + 0.4 * np.random.random()
                signal[beat_idx-2:beat_idx+3] += amp * np.array([0.1, 0.3, 1.0, 0.4, 0.1])
    
    return signal, fs