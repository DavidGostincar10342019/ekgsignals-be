#!/usr/bin/env python3
"""
Primer korišćenja API-ja za analizu sirovih EKG signala
"""

import requests
import json
import numpy as np

# Kreiranje test signala (simulacija EKG-a sa R-pikovima)
def create_test_signal():
    """Kreira test EKG signal sa simuliranim R-pikovima"""
    fs = 250  # Hz
    duration = 10  # sekunde
    t = np.linspace(0, duration, int(fs * duration))
    
    # Bazni signal (P i T talasi)
    base_signal = 0.1 * np.sin(2 * np.pi * 1.2 * t) + 0.05 * np.sin(2 * np.pi * 0.3 * t)
    
    # Dodavanje R-pikova (simulacija srčanih otkucaja)
    heart_rate = 75  # BPM
    rr_interval = 60 / heart_rate  # sekunde između R-pikova
    
    signal = base_signal.copy()
    
    # Dodavanje R-pikova
    for beat_time in np.arange(1, duration, rr_interval):
        beat_idx = int(beat_time * fs)
        if beat_idx < len(signal) - 10:
            # QRS kompleks (pojednostavljen)
            signal[beat_idx-2:beat_idx+3] += [0.1, 0.3, 1.2, 0.4, 0.1]
    
    return signal.tolist(), fs

def test_raw_signal_api():
    """Testira API endpoint za sirove signale"""
    
    # 1. Kreiraj test signal
    signal, fs = create_test_signal()
    
    print(f"🧪 Test signala:")
    print(f"   Broj uzoraka: {len(signal)}")
    print(f"   Frekvencija uzorkovanja: {fs} Hz") 
    print(f"   Trajanje: {len(signal)/fs:.1f} sekundi")
    print()
    
    # 2. Šalji na analizu
    url = "http://localhost:8000/api/analyze/raw-signal"
    
    payload = {
        "signal": signal,
        "fs": fs,
        "filename": "test_simulirani_ekg.csv"
    }
    
    print("📤 Šalje signal na analizu...")
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            
            print("✅ Analiza uspešna!")
            print()
            
            # Prikaži osnovne rezultate
            if "signal_info" in result:
                info = result["signal_info"]
                print("📊 Informacije o signalu:")
                print(f"   Izvor: {info.get('source', 'N/A')}")
                print(f"   Fajl: {info.get('filename', 'N/A')}")
                print(f"   Trajanje: {info.get('duration_seconds', 0):.1f}s")
                print()
            
            # FFT rezultati
            if "fft_analysis" in result:
                fft = result["fft_analysis"]
                print("🌊 FFT Analiza:")
                print(f"   Peak frekvencija: {fft.get('peak_frequency_hz', 0):.2f} Hz")
                print(f"   Peak amplituda: {fft.get('peak_amplitude', 0):.4f}")
                print()
            
            # Srčana frekvencija
            if "arrhythmia_detection" in result and "heart_rate" in result["arrhythmia_detection"]:
                hr = result["arrhythmia_detection"]["heart_rate"]
                print("❤️ Srčana frekvencija:")
                print(f"   Prosečna: {hr.get('average_bpm', 0):.1f} BPM")
                print(f"   HRV: {hr.get('heart_rate_variability', 0):.1f} ms")
                print(f"   R-pikovi: {hr.get('rr_count', 0)}")
                print()
            
            # Aritmije
            if "arrhythmia_detection" in result and "arrhythmias" in result["arrhythmia_detection"]:
                arrhythmias = result["arrhythmia_detection"]["arrhythmias"]
                print("⚠️ Detekcija aritmija:")
                print(f"   Procena: {arrhythmias.get('overall_assessment', 'N/A')}")
                
                if "detected" in arrhythmias and arrhythmias["detected"]:
                    print("   Detektovane aritmije:")
                    for arr in arrhythmias["detected"]:
                        print(f"     - {arr.get('type', 'N/A')}: {arr.get('description', 'N/A')}")
                else:
                    print("   ✅ Nema detektovanih aritmija")
                print()
            
            # Napredna analiza
            if "advanced_analysis" in result:
                print("🔬 Napredna analiza dostupna!")
                print()
            
        else:
            error = response.json() if response.headers.get('content-type') == 'application/json' else {"error": response.text}
            print(f"❌ Greška: {error.get('error', 'Nepoznata greška')}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Greška pri komunikaciji sa serverom: {e}")
    except Exception as e:
        print(f"❌ Neočekivana greška: {e}")

def save_test_files():
    """Kreira test fajlove za demonstraciju"""
    signal, fs = create_test_signal()
    
    # CSV fajl
    with open("test_ekg_signal_generated.csv", "w") as f:
        for value in signal:
            f.write(f"{value:.6f}\\n")
    
    # JSON fajl
    data = {
        "signal": signal,
        "fs": fs,
        "metadata": {
            "description": "Programski generisan EKG signal",
            "duration_seconds": len(signal) / fs,
            "heart_rate_bpm": 75
        }
    }
    
    with open("test_ekg_signal_generated.json", "w") as f:
        json.dump(data, f, indent=2)
    
    print("✅ Kreirani test fajlovi:")
    print("   - test_ekg_signal_generated.csv")
    print("   - test_ekg_signal_generated.json")
    print()

if __name__ == "__main__":
    print("🩺 EKG Analiza - Test Sirovih Signala")
    print("=" * 50)
    print()
    
    # Kreiraj test fajlove
    save_test_files()
    
    # Testiraj API
    test_raw_signal_api()
    
    print("📋 Završeno!")
    print()
    print("💡 Možete koristiti kreirane fajlove za test uvoza u web aplikaciji:")
    print("   1. Otvorite http://localhost:8000")
    print("   2. Kliknite 'Uvezi Sirovi Signal'")
    print("   3. Odaberite test_ekg_signal_generated.csv ili .json")
    print("   4. Pokrenite analizu")