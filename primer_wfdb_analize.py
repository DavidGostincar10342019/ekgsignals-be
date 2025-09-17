#!/usr/bin/env python3
"""
Primer korišćenja WFDB API-ja za analizu MIT-BIH signala
"""

import requests

def test_wfdb_analysis():
    """Testira WFDB API endpoint"""
    
    print("🏥 Test WFDB Analize")
    print("=" * 40)
    
    # Test sa lokalnim fajlovima
    dat_file = "test_record.dat"
    hea_file = "test_record.hea"
    
    try:
        # Pripremi fajlove za upload
        files = [
            ('file', (dat_file, open(dat_file, 'rb'), 'application/octet-stream')),
            ('file', (hea_file, open(hea_file, 'r'), 'text/plain'))
        ]
        
        print(f"📂 Upload fajlova: {dat_file}, {hea_file}")
        
        try:
            # Pošalji na analizu
            response = requests.post(
                'http://localhost:8000/api/analyze/wfdb',
                files=files
            )
        finally:
            # Zatvori fajlove
            for _, (_, f, _) in files:
                f.close()
        
        if response.status_code == 200:
            result = response.json()
            
            print("✅ WFDB analiza uspešna!")
            print()
            
            # Signal info
            signal_info = result.get("signal_info", {})
            print("📊 Informacije o signalu:")
            print(f"   Record: {signal_info.get('record_name', 'N/A')}")
            print(f"   Fajl: {signal_info.get('filename', 'N/A')}")
            print(f"   Uzorci: {signal_info.get('length', 0):,}")
            print(f"   Trajanje: {signal_info.get('duration_seconds', 0):.1f}s")
            print(f"   Fs: {signal_info.get('sampling_frequency', 0)} Hz")
            print()
            
            # WFDB metadata
            wfdb_meta = result.get("wfdb_metadata", {})
            print("🏥 WFDB Metapodaci:")
            print(f"   Kanali: {wfdb_meta.get('n_signals', 0)}")
            print(f"   Originalni uzorci: {wfdb_meta.get('original_samples', 0):,}")
            print()
            
            # Analiza rezultati
            print("🔬 Rezultati analize:")
            
            # Srčana frekvencija
            hr = result.get("arrhythmia_detection", {}).get("heart_rate", {})
            print(f"   ❤️  Prosečna frekvencija: {hr.get('average_bpm', 0):.1f} BPM")
            print(f"   📈 HRV: {hr.get('heart_rate_variability', 0):.1f} ms")
            print(f"   📊 R-pikovi: {hr.get('rr_count', 0)}")
            
            # FFT
            fft = result.get("fft_analysis", {})
            print(f"   🌊 Peak frekvencija: {fft.get('peak_frequency_hz', 0):.2f} Hz")
            
            # Aritmije
            arrhythmias = result.get("arrhythmia_detection", {}).get("arrhythmias", {})
            print(f"   ⚠️  Procena: {arrhythmias.get('overall_assessment', 'N/A')}")
            
            if arrhythmias.get('detected'):
                print("   Detektovane aritmije:")
                for arr in arrhythmias['detected']:
                    print(f"     - {arr.get('type', 'N/A')}: {arr.get('description', 'N/A')}")
            else:
                print("   ✅ Nema detektovanih aritmija")
                
        else:
            error = response.json() if response.headers.get('content-type') == 'application/json' else {"error": response.text}
            print(f"❌ Greška: {error.get('error', 'Nepoznata greška')}")
            
    except FileNotFoundError as e:
        print(f"❌ Fajl nije pronađen: {e}")
        print("💡 Pokrenite 'python primer_uvoza_signala.py' da kreirate test fajlove")
    except requests.exceptions.RequestException as e:
        print(f"❌ Greška pri komunikaciji sa serverom: {e}")
    except Exception as e:
        print(f"❌ Neočekivana greška: {e}")

def download_mit_bih_example():
    """Preuzima MIT-BIH primer sa interneta"""
    
    print("🌐 Preuzimanje MIT-BIH primera...")
    
    # MIT-BIH record 100 (normalan ritam)
    base_url = "https://physionet.org/files/mitdb/1.0.0/"
    
    records = ["100"]  # Možeš dodati više: ["100", "101", "111"]
    
    for record in records:
        for ext in [".dat", ".hea"]:
            filename = f"{record}{ext}"
            url = base_url + filename
            
            try:
                print(f"📥 Preuzimam {filename}...")
                response = requests.get(url)
                response.raise_for_status()
                
                with open(filename, 'wb' if ext == '.dat' else 'w') as f:
                    if ext == '.dat':
                        f.write(response.content)
                    else:
                        f.write(response.text)
                        
                print(f"✅ {filename} preuzet")
                
            except Exception as e:
                print(f"❌ Greška pri preuzimanju {filename}: {e}")
    
    print()
    print("💡 Sada možete koristiti preuzete fajlove:")
    print("   1. Otvorite http://localhost:8000")
    print("   2. Kliknite 'Uvezi Sirovi Signal'")
    print("   3. Odaberite i 100.dat i 100.hea fajlove")
    print("   4. Pokrenite analizu")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--download":
        download_mit_bih_example()
    else:
        test_wfdb_analysis()
    
    print()
    print("📋 Dodatne opcije:")
    print("   python primer_wfdb_analize.py --download  # Preuzmi MIT-BIH primere")
    print("   python primer_wfdb_analize.py             # Testiraj lokalne fajlove")