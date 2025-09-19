#!/usr/bin/env python3
"""
Brzi test FFT popravke
"""

import requests
import json
import numpy as np

def test_fft_fix():
    base_url = "http://127.0.0.1:8001"
    
    print("🔬 TESTIRANJE FFT POPRAVKE")
    print("=" * 50)
    
    # Test različitih frekvencija
    test_frequencies = [1, 5, 10, 15, 25, 40]
    fs = 250
    duration = 4
    
    for freq in test_frequencies:
        print(f"\n📊 Test: {freq} Hz sinusoida")
        
        # Generiši čistu sinusoidu
        t = np.linspace(0, duration, fs * duration)
        test_signal = np.sin(2 * np.pi * freq * t).tolist()
        
        payload = {"signal": test_signal, "fs": fs}
        
        try:
            response = requests.post(f"{base_url}/api/analyze/fft", 
                                   json=payload, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                detected_freq = data.get('peak_frequency_hz', 0)
                error = abs(detected_freq - freq)
                analysis_range = data.get('physiological_range_analyzed', 'N/A')
                
                status = "✅ PASS" if error <= 1.0 else "❌ FAIL"
                
                print(f"   {status} Očekivano: {freq}Hz, Detektovano: {detected_freq}Hz, Greška: ±{error:.1f}Hz")
                print(f"   📈 Analiza opseg: {analysis_range}")
                
                if error <= 1.0:
                    print(f"   🎯 Tačnost: {100 - (error/freq)*100:.1f}%")
                else:
                    print(f"   ⚠️  Velika greška!")
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")
                print(f"   Response: {response.text[:100]}")
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
    
    print(f"\n🏁 FFT Test završen!")

if __name__ == "__main__":
    test_fft_fix()