#!/usr/bin/env python3
"""
Primer korišćenja EKG Analiza API-ja
"""

import requests
import numpy as np
import matplotlib.pyplot as plt
import base64
import json

# Konfiguracija
API_BASE_URL = "http://localhost:5000/api"

def test_api_health():
    """Test da li je API aktivan"""
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code == 200:
            print("✅ API je aktivan:", response.json())
            return True
        else:
            print("❌ API nije dostupan")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Nema konekcije sa API-jem. Pokrenite aplikaciju prvo!")
        return False

def create_test_ekg_signal():
    """Kreiranje test EKG signala"""
    fs = 250  # Hz
    duration = 10  # sekundi
    t = np.linspace(0, duration, fs * duration)
    
    # Simulacija EKG signala
    heart_rate = 75  # bpm
    rr_interval = 60 / heart_rate
    
    signal = []
    for time in t:
        # R-pikovi
        beat_phase = (time % rr_interval) / rr_interval
        
        if 0.1 <= beat_phase <= 0.2:  # R-pik
            amplitude = 1.0
        elif 0.05 <= beat_phase <= 0.1:  # Q-deo
            amplitude = -0.2
        elif 0.2 <= beat_phase <= 0.35:  # S-T segment
            amplitude = 0.1
        elif 0.35 <= beat_phase <= 0.5:  # T-talas
            amplitude = 0.3 * np.sin(np.pi * (beat_phase - 0.35) / 0.15)
        else:  # Baseline
            amplitude = 0.0
        
        # Dodavanje šuma
        noise = 0.05 * np.random.randn()
        signal.append(amplitude + noise)
    
    return signal, fs

def test_fft_analysis():
    """Test FFT analize"""
    print("\n🔍 Testiranje FFT analize...")
    
    signal, fs = create_test_ekg_signal()
    
    payload = {
        "signal": signal,
        "fs": fs
    }
    
    response = requests.post(f"{API_BASE_URL}/analyze/fft", json=payload)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ FFT Analiza uspešna:")
        print(f"   Peak frekvencija: {result['peak_frequency_hz']:.2f} Hz")
        print(f"   Peak amplituda: {result['peak_amplitude']:.4f}")
        print(f"   Broj uzoraka: {result['n']}")
        return result
    else:
        print(f"❌ FFT Analiza neuspešna: {response.text}")
        return None

def test_ztransform_analysis():
    """Test Z-transformacije"""
    print("\n🔍 Testiranje Z-transformacije...")
    
    signal, fs = create_test_ekg_signal()
    
    payload = {
        "signal": signal,
        "fs": fs
    }
    
    response = requests.post(f"{API_BASE_URL}/analyze/ztransform", json=payload)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Z-Transform analiza uspešna:")
        print(f"   Broj polova: {result['stability']['pole_count']}")
        print(f"   Stabilnost: {result['stability']['message']}")
        print(f"   Max magnitude pola: {result['stability']['max_pole_magnitude']:.4f}")
        return result
    else:
        print(f"❌ Z-Transform analiza neuspešna: {response.text}")
        return None

def test_arrhythmia_detection():
    """Test detekcije aritmija"""
    print("\n🔍 Testiranje detekcije aritmija...")
    
    signal, fs = create_test_ekg_signal()
    
    payload = {
        "signal": signal,
        "fs": fs
    }
    
    response = requests.post(f"{API_BASE_URL}/analyze/arrhythmia", json=payload)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Detekcija aritmija uspešna:")
        print(f"   Prosečna srčana frekvencija: {result['heart_rate']['average_bpm']:.1f} bpm")
        print(f"   Broj R-pikova: {len(result['r_peaks'])}")
        print(f"   HRV: {result['heart_rate']['heart_rate_variability']:.1f} ms")
        
        if result['arrhythmias']['detected']:
            print(f"   Detektovane aritmije:")
            for arr in result['arrhythmias']['detected']:
                print(f"     - {arr['type']}: {arr['description']}")
        else:
            print(f"   Nema detektovanih aritmija")
            
        print(f"   Ukupna procena: {result['arrhythmias']['overall_assessment']}")
        return result
    else:
        print(f"❌ Detekcija aritmija neuspešna: {response.text}")
        return None

def test_complete_analysis():
    """Test kompletne analize"""
    print("\n🔍 Testiranje kompletne analize...")
    
    signal, fs = create_test_ekg_signal()
    
    payload = {
        "signal": signal,
        "fs": fs
    }
    
    response = requests.post(f"{API_BASE_URL}/analyze/complete", json=payload)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Kompletna analiza uspešna:")
        print(f"   Trajanje signala: {result['signal_info']['duration_seconds']:.1f} s")
        print(f"   FFT peak: {result['fft_analysis']['peak_frequency_hz']:.2f} Hz")
        print(f"   Stabilnost sistema: {result['z_transform']['stability']['message']}")
        print(f"   Srčana frekvencija: {result['arrhythmia_detection']['heart_rate']['average_bpm']:.1f} bpm")
        return result
    else:
        print(f"❌ Kompletna analiza neuspešna: {response.text}")
        return None

def test_filter_design():
    """Test dizajna filtera"""
    print("\n🔍 Testiranje dizajna filtera...")
    
    payload = {
        "cutoff_frequency": 40,
        "fs": 250,
        "type": "bandpass"
    }
    
    response = requests.post(f"{API_BASE_URL}/filter/design", json=payload)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Dizajn filtera uspešan:")
        print(f"   Tip filtera: {result['filter_type']}")
        print(f"   Red filtera: {result['order']}")
        print(f"   Granična frekvencija: {result['cutoff_frequency']} Hz")
        return result
    else:
        print(f"❌ Dizajn filtera neuspešan: {response.text}")
        return None

def visualize_results(signal, fs, results):
    """Vizualizacija rezultata"""
    print("\n📊 Kreiranje vizualizacije...")
    
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle('EKG Analiza Rezultati', fontsize=16)
    
    # 1. Originalni signal
    t = np.linspace(0, len(signal)/fs, len(signal))
    axes[0,0].plot(t, signal)
    axes[0,0].set_title('EKG Signal')
    axes[0,0].set_xlabel('Vreme (s)')
    axes[0,0].set_ylabel('Amplituda')
    axes[0,0].grid(True)
    
    # 2. FFT spektar
    if 'fft_analysis' in results:
        fft_result = results['fft_analysis']
        # Kreiranje frekvencijskog spektra za vizualizaciju
        freqs = np.fft.rfftfreq(len(signal), d=1/fs)
        spectrum = np.abs(np.fft.rfft(signal)) / len(signal)
        
        axes[0,1].plot(freqs[:len(freqs)//4], spectrum[:len(spectrum)//4])  # Prikazuj do 1/4 Nyquist
        axes[0,1].axvline(fft_result['peak_frequency_hz'], color='red', linestyle='--', 
                         label=f'Peak: {fft_result["peak_frequency_hz"]:.2f} Hz')
        axes[0,1].set_title('FFT Spektar')
        axes[0,1].set_xlabel('Frekvencija (Hz)')
        axes[0,1].set_ylabel('Amplituda')
        axes[0,1].legend()
        axes[0,1].grid(True)
    
    # 3. R-pikovi
    if 'arrhythmia_detection' in results:
        arr_result = results['arrhythmia_detection']
        axes[1,0].plot(t, signal, alpha=0.7)
        
        if 'r_peaks' in arr_result and arr_result['r_peaks']:
            r_peak_times = np.array(arr_result['r_peaks']) / fs
            r_peak_values = [signal[int(peak)] for peak in arr_result['r_peaks'] if int(peak) < len(signal)]
            axes[1,0].scatter(r_peak_times, r_peak_values, color='red', s=50, label='R-pikovi')
        
        axes[1,0].set_title(f'Detekcija R-pikova (BPM: {arr_result["heart_rate"]["average_bpm"]:.1f})')
        axes[1,0].set_xlabel('Vreme (s)')
        axes[1,0].set_ylabel('Amplituda')
        axes[1,0].legend()
        axes[1,0].grid(True)
    
    # 4. Informacije o analizi
    axes[1,1].axis('off')
    info_text = "Rezultati Analize:\n\n"
    
    if 'signal_info' in results:
        info_text += f"Trajanje: {results['signal_info']['duration_seconds']:.1f} s\n"
        info_text += f"Fs: {results['signal_info']['sampling_frequency']} Hz\n\n"
    
    if 'arrhythmia_detection' in results:
        arr = results['arrhythmia_detection']
        info_text += f"Srčana frekvencija: {arr['heart_rate']['average_bpm']:.1f} bpm\n"
        info_text += f"HRV: {arr['heart_rate']['heart_rate_variability']:.1f} ms\n"
        info_text += f"Kvalitet signala: {arr['signal_quality']['quality']}\n\n"
        
        if arr['arrhythmias']['detected']:
            info_text += "Detektovane aritmije:\n"
            for arrhythmia in arr['arrhythmias']['detected']:
                info_text += f"• {arrhythmia['type']}\n"
        else:
            info_text += "Nema detektovanih aritmija\n"
    
    axes[1,1].text(0.1, 0.9, info_text, transform=axes[1,1].transAxes, 
                   fontsize=10, verticalalignment='top', fontfamily='monospace')
    
    plt.tight_layout()
    plt.savefig('ekg_analysis_results.png', dpi=150, bbox_inches='tight')
    print("📊 Grafik sačuvan kao 'ekg_analysis_results.png'")
    plt.show()

def main():
    """Glavna funkcija za testiranje"""
    print("🏥 EKG Analiza API - Test Suite")
    print("=" * 50)
    
    # Provera API-ja
    if not test_api_health():
        return
    
    # Kreiranje test signala
    print("\n📊 Kreiranje test EKG signala...")
    signal, fs = create_test_ekg_signal()
    print(f"✅ Kreiran signal: {len(signal)} uzoraka, {fs} Hz, {len(signal)/fs:.1f} s")
    
    # Testiranje svih funkcionalnosti
    results = {}
    
    # FFT
    fft_result = test_fft_analysis()
    if fft_result:
        results['fft_analysis'] = fft_result
    
    # Z-Transform
    zt_result = test_ztransform_analysis()
    if zt_result:
        results['z_transform'] = zt_result
    
    # Aritmije
    arr_result = test_arrhythmia_detection()
    if arr_result:
        results['arrhythmia_detection'] = arr_result
    
    # Filter
    filter_result = test_filter_design()
    
    # Kompletna analiza
    complete_result = test_complete_analysis()
    if complete_result:
        results.update(complete_result)
    
    # Vizualizacija
    if results:
        visualize_results(signal, fs, results)
    
    print("\n✅ Testiranje završeno!")

if __name__ == "__main__":
    main()