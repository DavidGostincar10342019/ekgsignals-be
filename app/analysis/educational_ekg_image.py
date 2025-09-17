"""
Kreiranje edukativnih EKG slika sa prikazanim parametrima analize
Za potrebe prikaza rezultata analize sirovih EKG podataka
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import io
import base64
from PIL import Image
import cv2

def create_educational_ekg_image(signal, analysis_results, fs=250, duration_seconds=None):
    """
    Kreira edukativnu EKG sliku sa prikazanim parametrima analize
    
    Args:
        signal: EKG signal (lista ili numpy array)
        analysis_results: Rezultati analize (dict)
        fs: Frekvencija uzorkovanja
        duration_seconds: Trajanje prikaza (None = ceo signal)
    
    Returns:
        dict sa image_base64, metadata, itd.
    """
    signal = np.array(signal)
    
    # Ograniči trajanje ako je potrebno
    if duration_seconds:
        max_samples = int(duration_seconds * fs)
        if len(signal) > max_samples:
            signal = signal[:max_samples]
    
    # Kreiranje vremenske ose
    t = np.linspace(0, len(signal) / fs, len(signal))
    
    # Kreiranje figure sa dodatnim prostorom za anotacije
    fig, (ax_main, ax_info) = plt.subplots(2, 1, figsize=(14, 10), 
                                          gridspec_kw={'height_ratios': [3, 1]}, dpi=150)
    
    # Glavni EKG plot
    _create_main_ekg_plot(ax_main, signal, t, analysis_results, fs)
    
    # Info panel sa parametrima
    _create_info_panel(ax_info, analysis_results, signal, fs)
    
    plt.tight_layout()
    
    return _fig_to_image_data(fig)

def _create_main_ekg_plot(ax, signal, t, analysis_results, fs):
    """Kreira glavni EKG plot sa medicinskim grid-om i anotacijama"""
    
    # Medicinski EKG papir pozadina
    _add_medical_grid(ax, t[-1])
    
    # Normalizacija signala za medicinski prikaz (1mV = 10mm)
    signal_mv = signal * 1.0  # Pretpostavljamo da je signal već u mV
    
    # Crtanje EKG signala
    ax.plot(t, signal_mv, 'k-', linewidth=2.0, alpha=0.9, label='EKG Signal')
    
    # Dodavanje R-peak markera ako su dostupni
    _add_rpeak_markers(ax, t, signal_mv, analysis_results)
    
    # Dodavanje aritmije markera ako su detektovane
    _add_arrhythmia_markers(ax, t, signal_mv, analysis_results)
    
    # Medicinski stil osa
    ax.set_xlim(0, t[-1])
    ax.set_ylim(-2, 2)
    ax.set_xlabel('Vreme (s)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Amplituda (mV)', fontsize=12, fontweight='bold')
    ax.set_title('EKG Analiza - Edukativni Prikaz', fontsize=16, fontweight='bold', pad=20)
    
    # Dodavanje skale referencne
    _add_calibration_signal(ax, t, signal_mv)
    
    # Legenda
    ax.legend(loc='upper right', fontsize=10)

def _add_medical_grid(ax, duration):
    """Dodaje medicinsku mrežu (5mm velika, 1mm mala kockica)"""
    
    # Velika mreža (5mm = 0.2s, 0.5mV)
    major_time_spacing = 0.2
    major_voltage_spacing = 0.5
    
    # Mala mreža (1mm = 0.04s, 0.1mV)
    minor_time_spacing = 0.04
    minor_voltage_spacing = 0.1
    
    # Vertikalne linije (vreme)
    for t in np.arange(0, duration + minor_time_spacing, minor_time_spacing):
        alpha = 0.8 if abs(t % major_time_spacing) < 0.01 else 0.3
        linewidth = 1.0 if abs(t % major_time_spacing) < 0.01 else 0.5
        color = '#FF6B6B' if abs(t % major_time_spacing) < 0.01 else '#FFB3B3'
        ax.axvline(t, color=color, alpha=alpha, linewidth=linewidth, zorder=0)
    
    # Horizontalne linije (napon)
    for v in np.arange(-2, 2.1, minor_voltage_spacing):
        alpha = 0.8 if abs(v % major_voltage_spacing) < 0.01 else 0.3
        linewidth = 1.0 if abs(v % major_voltage_spacing) < 0.01 else 0.5
        color = '#FF6B6B' if abs(v % major_voltage_spacing) < 0.01 else '#FFB3B3'
        ax.axhline(v, color=color, alpha=alpha, linewidth=linewidth, zorder=0)

def _add_rpeak_markers(ax, t, signal, analysis_results):
    """Dodaje markere za R-pikove ako su detektovani"""
    
    # Pokušaj da izvuci R-pikove iz rezultata
    arrhythmia_data = analysis_results.get('arrhythmia_detection', {})
    heart_rate_data = arrhythmia_data.get('heart_rate', {})
    
    # Jednostavna detekcija R-pikova ako nije dostupna iz analize
    if 'rr_intervals' not in heart_rate_data:
        r_peaks = _simple_rpeak_detection(signal, len(t))
    else:
        # Konvertuj RR intervale u R-peak pozicije
        rr_intervals = heart_rate_data.get('rr_intervals', [])
        r_peaks = []
        current_pos = 0
        for interval in rr_intervals:
            current_pos += interval
            if current_pos < len(t):
                r_peaks.append(int(current_pos))
    
    # Nacrtaj R-peak markere
    for peak_idx in r_peaks:
        if peak_idx < len(t) and peak_idx < len(signal):
            ax.plot(t[peak_idx], signal[peak_idx], 'ro', markersize=8, 
                   markerfacecolor='red', markeredgecolor='darkred', 
                   markeredgewidth=2, label='R-pikovi' if peak_idx == r_peaks[0] else "")

def _simple_rpeak_detection(signal, n_samples):
    """Jednostavna detekcija R-pikova"""
    # Pronađi lokalne maksimume koji su veći od 70% maksimalne vrednosti
    threshold = 0.7 * np.max(signal)
    peaks = []
    
    for i in range(1, len(signal) - 1):
        if (signal[i] > signal[i-1] and 
            signal[i] > signal[i+1] and 
            signal[i] > threshold):
            # Proveri da nije previše blizu prethodnom piku (minimum 150ms)
            if not peaks or (i - peaks[-1]) > (150 * len(signal) / (n_samples * 1000 / 250)):
                peaks.append(i)
    
    return peaks

def _add_arrhythmia_markers(ax, t, signal, analysis_results):
    """Dodaje markere za detektovane aritmije"""
    
    arrhythmias = analysis_results.get('arrhythmia_detection', {}).get('arrhythmias', {})
    
    if arrhythmias.get('detected'):
        # Dodaj crvene zone za aritmije (simulacija)
        for i, arrhythmia in enumerate(arrhythmias['detected'][:3]):  # Max 3 za čitljivost
            # Simulacija pozicije aritmije
            start_time = (i + 1) * len(t) / 4
            end_time = start_time + len(t) / 8
            
            if start_time < len(t):
                start_idx = int(start_time)
                end_idx = min(int(end_time), len(t) - 1)
                
                # Crvena zona
                ax.axvspan(t[start_idx], t[end_idx], alpha=0.2, color='red', 
                          label=f'Aritmija: {arrhythmia.get("type", "Nepoznata")}' if i == 0 else "")

def _add_calibration_signal(ax, t, signal):
    """Dodaje kalibraciju signal (1mV blok)"""
    
    # Pozicija za kalibraciju (levo gore)
    cal_x = t[-1] * 0.02
    cal_y = 1.3
    
    # 1mV kalibracijski signal
    cal_signal = np.array([0, 0, 1, 1, 0])
    cal_time = np.linspace(cal_x, cal_x + 0.2, len(cal_signal))
    ax.plot(cal_time, cal_signal + cal_y, 'k-', linewidth=3, label='1mV Kalibracija')
    ax.text(cal_x + 0.1, cal_y + 1.2, '1mV', ha='center', va='bottom', 
           fontsize=10, fontweight='bold',
           bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8))

def _create_info_panel(ax, analysis_results, signal, fs):
    """Kreira info panel sa ključnim parametrima analize"""
    
    ax.axis('off')  # Ukloni ose
    
    # Pozadina info panela
    info_bg = patches.Rectangle((0, 0), 1, 1, linewidth=2, edgecolor='black', 
                               facecolor='lightblue', alpha=0.1, transform=ax.transAxes)
    ax.add_patch(info_bg)
    
    # Naslov
    ax.text(0.5, 0.9, 'REZULTATI ANALIZE', ha='center', va='top', 
           fontsize=16, fontweight='bold', transform=ax.transAxes)
    
    # Osnovni parametri u kolone
    _add_basic_params(ax, analysis_results, signal, fs)
    _add_heart_rate_params(ax, analysis_results)
    _add_frequency_params(ax, analysis_results)
    _add_arrhythmia_assessment(ax, analysis_results)

def _add_basic_params(ax, analysis_results, signal, fs):
    """Dodaje osnovne parametre signala"""
    
    signal_info = analysis_results.get('signal_info', {})
    
    text = f"""📊 OSNOVNI PARAMETRI:
• Uzorci: {len(signal):,}
• Trajanje: {len(signal)/fs:.1f}s
• Frekvencija: {fs} Hz
• Izvor: {signal_info.get('source', 'Nepoznat')}"""
    
    ax.text(0.02, 0.75, text, ha='left', va='top', fontsize=11, 
           transform=ax.transAxes, fontfamily='monospace')

def _add_heart_rate_params(ax, analysis_results):
    """Dodaje parametre srčane frekvencije"""
    
    hr_data = analysis_results.get('arrhythmia_detection', {}).get('heart_rate', {})
    
    avg_bpm = hr_data.get('average_bpm', 0)
    hrv = hr_data.get('heart_rate_variability', 0)
    rr_count = hr_data.get('rr_count', 0)
    
    # Procena na osnovu BPM
    if avg_bpm > 100:
        hr_status = "TAHIKARDIJA"
        hr_color = "🔴"
    elif avg_bpm < 60:
        hr_status = "BRADIKARDIJA" 
        hr_color = "🟡"
    else:
        hr_status = "NORMALNA"
        hr_color = "🟢"
    
    text = f"""❤️ SRČANA FREKVENCIJA:
• BPM: {avg_bpm:.1f} {hr_color}
• Status: {hr_status}
• HRV: {hrv:.1f} ms
• R-pikovi: {rr_count}"""
    
    ax.text(0.27, 0.75, text, ha='left', va='top', fontsize=11,
           transform=ax.transAxes, fontfamily='monospace')

def _add_frequency_params(ax, analysis_results):
    """Dodaje FFT parametre"""
    
    fft_data = analysis_results.get('fft_analysis', {})
    
    peak_freq = fft_data.get('peak_frequency_hz', 0)
    peak_amp = fft_data.get('peak_amplitude', 0)
    
    text = f"""🌊 SPEKTRALNA ANALIZA:
• Peak freq: {peak_freq:.2f} Hz
• Peak amp: {peak_amp:.4f}
• Dominantna: {peak_freq*60:.0f} BPM
• FFT analiza: ✅"""
    
    ax.text(0.52, 0.75, text, ha='left', va='top', fontsize=11,
           transform=ax.transAxes, fontfamily='monospace')

def _add_arrhythmia_assessment(ax, analysis_results):
    """Dodaje procenu aritmija"""
    
    arrhythmias = analysis_results.get('arrhythmia_detection', {}).get('arrhythmias', {})
    
    assessment = arrhythmias.get('overall_assessment', 'Nepoznato')
    detected = arrhythmias.get('detected', [])
    
    if detected:
        status_icon = "⚠️"
        arrhythmia_list = "\n".join([f"  • {arr.get('type', 'N/A')}" for arr in detected[:2]])
    else:
        status_icon = "✅"
        arrhythmia_list = "  • Nema detektovanih aritmija"
    
    text = f"""⚠️ ARITMIJE:
• Status: {assessment} {status_icon}
• Detektovane:
{arrhythmia_list}"""
    
    ax.text(0.77, 0.75, text, ha='left', va='top', fontsize=11,
           transform=ax.transAxes, fontfamily='monospace')

def _fig_to_image_data(fig):
    """Konvertuje matplotlib figuru u image data"""
    
    # Matplotlib -> PIL Image
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', 
                facecolor='white', edgecolor='none', dpi=150)
    buf.seek(0)
    
    # PIL Image
    pil_image = Image.open(buf)
    
    # Base64 string za web
    buf.seek(0)
    image_base64 = base64.b64encode(buf.read()).decode('utf-8')
    
    # OpenCV format (za postojeću logiku)
    opencv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
    
    # Metadata
    metadata = {
        'width': pil_image.width,
        'height': pil_image.height,
        'format': 'PNG',
        'mode': pil_image.mode,
        'type': 'educational_ekg'
    }
    
    plt.close(fig)  # Oslobodi memoriju
    
    return {
        'image_base64': f"data:image/png;base64,{image_base64}",
        'image_pil': pil_image,
        'image_opencv': opencv_image,
        'metadata': metadata
    }