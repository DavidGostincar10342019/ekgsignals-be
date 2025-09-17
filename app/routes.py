from flask import Blueprint, jsonify, request, render_template
from .analysis.fft import analyze_fft
from .analysis.ztransform import z_transform_analysis, digital_filter_design
from .analysis.image_processing import process_ekg_image, preprocess_for_analysis
from .analysis.arrhythmia_detection import detect_arrhythmias
from .analysis.advanced_ekg_analysis import comprehensive_ekg_analysis
from .analysis.educational_visualization import create_step_by_step_analysis
from .analysis.wfdb_reader import parse_wfdb_files, validate_wfdb_files, extract_signal_for_analysis, parse_wfdb_files_with_annotations
from .analysis.signal_to_image import create_ekg_image_from_signal, test_signal_to_image_conversion
from .analysis.educational_ekg_image import create_educational_ekg_image
from .analysis.intelligent_signal_segmentation import find_critical_segments

api = Blueprint("api", __name__)

@api.get("/")
def index():
    """Glavna stranica mobilne web aplikacije"""
    return render_template('index.html')

@api.get("/health")
def health():
    return jsonify(status="ok")

@api.post("/analyze/fft")
def analyze_fft_endpoint():
    """FFT analiza digitalnog signala"""
    payload = request.get_json(force=True)
    signal = payload.get("signal", [])
    fs = payload.get("fs", 250)
    result = analyze_fft(signal, fs)
    return jsonify(result)

@api.post("/analyze/image")
def analyze_ekg_image():
    """Analiza EKG slike - konverzija u digitalni signal"""
    try:
        payload = request.get_json(force=True)
        image_data = payload.get("image", "")
        
        if not image_data:
            return jsonify({"error": "Nedostaje slika"}), 400
        
        # Obrada slike
        result = process_ekg_image(image_data)
        
        if "error" in result:
            return jsonify(result), 400
            
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": f"Greška pri obradi: {str(e)}"}), 500

@api.post("/analyze/complete")
def complete_ekg_analysis():
    """Kompletna analiza EKG-a - od slike do detekcije aritmija"""
    try:
        payload = request.get_json(force=True)
        print(f"DEBUG: Received payload keys: {list(payload.keys()) if payload else 'None'}")
        
        if payload and 'image' in payload:
            image_size = len(payload['image']) if payload['image'] else 0
            print(f"DEBUG: Image data size: {image_size} characters")
        
        # Opcija 1: Direktno prosleđen signal
        if "signal" in payload:
            signal = payload["signal"]
            fs = payload.get("fs", 250)
        
        # Opcija 2: Analiza slike
        elif "image" in payload:
            print(f"DEBUG: Processing image...")
            # Proverava da li je slika generisana iz signala (preskače validaciju)
            skip_validation = payload.get("skip_validation", False)
            try:
                image_result = process_ekg_image(payload["image"], skip_validation=skip_validation)
                print(f"DEBUG: Image processing result keys: {list(image_result.keys())}")
                
                if "error" in image_result:
                    print(f"DEBUG: Image processing error: {image_result["error"]}")
                    return jsonify(image_result), 400
                
                signal = image_result["signal"]
                fs = payload.get("fs", 250)
                print(f"DEBUG: Extracted signal length: {len(signal)}")
                
                # Predobrada signala
                signal, fs = preprocess_for_analysis(signal, fs)
                print(f"DEBUG: Preprocessed signal length: {len(signal)}")
                
            except Exception as e:
                print(f"DEBUG: Exception in image processing: {str(e)}")
                import traceback
                traceback.print_exc()
                return jsonify({"error": f"Greška pri obradi slike: {str(e)}"}), 400
        else:
            return jsonify({"error": "Potreban je 'signal' ili 'image' parametar"}), 400
        
        # Kompletna analiza
        results = {}
        
        # 1. FFT analiza
        results["fft_analysis"] = analyze_fft(signal, fs)
        
        # 2. Z-transformacija
        results["z_transform"] = z_transform_analysis(signal, fs)
        
        # 3. Detekcija aritmija
        results["arrhythmia_detection"] = detect_arrhythmias(signal, fs)
        
        # 4. Napredna analiza (naučni algoritmi) - ZAKOMENTARISANO
        # results["advanced_analysis"] = comprehensive_ekg_analysis(signal, fs)
        
        # 5. Osnovne informacije
        results["signal_info"] = {
            "length": len(signal),
            "duration_seconds": len(signal) / fs,
            "sampling_frequency": fs
        }
        
        return jsonify(results)
        
    except Exception as e:
        return jsonify({"error": f"Greška pri kompletnoj analizi: {str(e)}"}), 500

@api.post("/analyze/ztransform")
def analyze_ztransform():
    """Z-transformacija digitalnog signala"""
    try:
        payload = request.get_json(force=True)
        signal = payload.get("signal", [])
        fs = payload.get("fs", 250)
        
        if not signal:
            return jsonify({"error": "Nedostaje signal"}), 400
            
        result = z_transform_analysis(signal, fs)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": f"Greška u Z-transformaciji: {str(e)}"}), 500

@api.post("/analyze/arrhythmia")
def analyze_arrhythmia():
    """Detekcija aritmija u EKG signalu"""
    try:
        payload = request.get_json(force=True)
        signal = payload.get("signal", [])
        fs = payload.get("fs", 250)
        
        if not signal:
            return jsonify({"error": "Nedostaje signal"}), 400
            
        result = detect_arrhythmias(signal, fs)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": f"Greška u detekciji aritmija: {str(e)}"}), 500

@api.post("/analyze/raw-signal")
def analyze_raw_signal():
    """Kompletna analiza sirovih EKG podataka (direktni uvoz signala)"""
    try:
        payload = request.get_json(force=True)
        signal = payload.get("signal", [])
        fs = payload.get("fs", 250)
        filename = payload.get("filename", "nepoznat_signal")
        
        if not signal:
            return jsonify({"error": "Nedostaje signal"}), 400
        
        if len(signal) < 100:
            return jsonify({"error": "Signal je prekratak (minimum 100 uzoraka)"}), 400
        
        if len(signal) > 100000:
            return jsonify({"error": "Signal je predugačak (maksimum 100,000 uzoraka)"}), 400
        
        print(f"DEBUG: Analyzing raw signal '{filename}', length: {len(signal)}, fs: {fs}")
        
        # Kompletna analiza sirovih podataka
        results = {}
        
        # 1. FFT analiza
        results["fft_analysis"] = analyze_fft(signal, fs)
        
        # 2. Z-transformacija
        results["z_transform"] = z_transform_analysis(signal, fs)
        
        # 3. Detekcija aritmija
        results["arrhythmia_detection"] = detect_arrhythmias(signal, fs)
        
        # 4. Napredna analiza (naučni algoritmi) - ZAKOMENTARISANO  
        # results["advanced_analysis"] = comprehensive_ekg_analysis(signal, fs)
        
        # 5. Osnovne informacije sa dodatnim metapodacima
        results["signal_info"] = {
            "length": len(signal),
            "duration_seconds": len(signal) / fs,
            "sampling_frequency": fs,
            "source": "raw_import",
            "filename": filename,
            "import_method": "direct_file_upload"
        }
        
        return jsonify(results)
        
    except Exception as e:
        print(f"DEBUG: Error in raw signal analysis: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Greška pri analizi sirovih podataka: {str(e)}"}), 500

@api.post("/analyze/wfdb")
def analyze_wfdb_files():
    """Analiza WFDB formata (.dat + .hea + .atr fajlovi) - POBOLJŠANO sa .atr podrškom"""
    try:
        # Čitanje fajlova iz form-data
        files = request.files
        
        if not files:
            return jsonify({"error": "Nedostaju fajlovi"}), 400
        
        # Konvertovanje u dict {filename: content}
        files_dict = {}
        for key in files.keys():
            file_list = files.getlist(key)  # Može biti više fajlova sa istim key-em
            for file in file_list:
                if file.filename:
                    files_dict[file.filename] = file.read()
        
        if not validate_wfdb_files(files_dict):
            return jsonify({"error": "Potrebni su .dat i .hea fajlovi"}), 400
        
        # Pronađi sve WFDB fajlove
        dat_content = None
        hea_content = None
        atr_content = None  # NOVO: .atr podrška
        dat_filename = ""
        atr_filename = ""
        
        for filename, content in files_dict.items():
            if filename.endswith('.dat'):
                dat_content = content
                dat_filename = filename
            elif filename.endswith('.hea'):
                hea_content = content.decode('utf-8')
            elif filename.endswith('.atr'):  # NOVO: čitaj .atr fajl
                atr_content = content
                atr_filename = filename
                print(f"DEBUG: Found .atr file: {filename}")
        
        if not dat_content or not hea_content:
            return jsonify({"error": "Potrebni su i .dat i .hea fajlovi"}), 400
        
        print(f"DEBUG: Processing WFDB files: {dat_filename}")
        if atr_content:
            print(f"DEBUG: Including annotations from: {atr_filename}")
        
        # NOVO: Parsiranje WFDB fajlova sa annotations
        if atr_content:
            signals, fs, metadata, annotations = parse_wfdb_files_with_annotations(dat_content, hea_content, atr_content)
        else:
            signals, fs, metadata = parse_wfdb_files(dat_content, hea_content)
            annotations = {}  # Prazan ako nema .atr
        
        # Izvuci prvi kanal za analizu
        signal = extract_signal_for_analysis(signals, channel=0)
        
        if len(signal) < 100:
            return jsonify({"error": "Signal je prekratak (minimum 100 uzoraka)"}), 400
        
        if len(signal) > 100000:
            # Skrati signal na prvih 100k uzoraka
            signal = signal[:100000]
            print(f"DEBUG: Signal skraćen na {len(signal)} uzoraka")
        
        print(f"DEBUG: Analyzing WFDB signal, length: {len(signal)}, fs: {fs}")
        
        # Kompletna analiza
        results = {}
        
        # 1. FFT analiza
        results["fft_analysis"] = analyze_fft(signal, fs)
        
        # 2. Z-transformacija
        results["z_transform"] = z_transform_analysis(signal, fs)
        
        # 3. Detekcija aritmija
        results["arrhythmia_detection"] = detect_arrhythmias(signal, fs)
        
        # 4. Napredna analiza - ZAKOMENTARISANO
        # results["advanced_analysis"] = comprehensive_ekg_analysis(signal, fs)
        
        # 5. Informacije o signalu sa WFDB metapodacima
        results["signal_info"] = {
            "length": len(signal),
            "duration_seconds": len(signal) / fs,
            "sampling_frequency": fs,
            "source": "wfdb_import",
            "filename": dat_filename,
            "import_method": "wfdb_format",
            "original_shape": list(signals.shape),
            "n_channels": metadata.get('n_signals', 1),
            "record_name": metadata.get('record_name', 'unknown'),
            "has_annotations": bool(atr_content)  # NOVO: da li su učitani annotations
        }
        
        # 6. WFDB specifični metapodaci
        results["wfdb_metadata"] = {
            "record_name": metadata.get('record_name'),
            "n_signals": metadata.get('n_signals'),
            "original_samples": metadata.get('n_samples'),
            "signals_info": metadata.get('signals', [])
        }
        
        # 7. NOVO: Annotation podaci iz .atr fajla
        if annotations:
            results["annotations"] = {
                "total_annotations": annotations.get('total_annotations', 0),
                "r_peaks_count": len(annotations.get('r_peaks', [])),
                "arrhythmias_count": len(annotations.get('arrhythmias', [])),
                "annotation_types": annotations.get('annotation_types', {}),
                "r_peaks": annotations.get('r_peaks', [])[:20],  # Prvih 20 R-pikova
                "arrhythmias": annotations.get('arrhythmias', []),
                "source_file": atr_filename
            }
            
            # POBOLJŠANO: Koristi annotation R-pikove za bolju analizu aritmija
            if annotations.get('r_peaks'):
                print(f"DEBUG: Using {len(annotations['r_peaks'])} annotated R-peaks for enhanced arrhythmia detection")
                # Možete dodati logiku koja koristi tačne R-peak pozicije iz annotations
        
        return jsonify(results)
        
    except Exception as e:
        print(f"DEBUG: Error in WFDB analysis: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Greška pri analizi WFDB fajlova: {str(e)}"}), 500

@api.get("/download/wfdb/<record_name>/<file_type>")
def download_wfdb_file(record_name, file_type):
    """Proxy za preuzimanje WFDB fajlova sa PhysioNet-a"""
    try:
        if file_type not in ['dat', 'hea', 'atr', 'xws']:
            return jsonify({"error": "Podržani tipovi: dat, hea, atr, xws"}), 400
        
        # PhysioNet URL
        url = f"https://physionet.org/files/mitdb/1.0.0/{record_name}.{file_type}"
        
        import requests
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Odrediti Content-Type
        content_type = 'application/octet-stream' if file_type == 'dat' else 'text/plain'
        
        return response.content, 200, {
            'Content-Type': content_type,
            'Content-Disposition': f'attachment; filename="{record_name}.{file_type}"'
        }
        
    except Exception as e:
        return jsonify({"error": f"Greška pri preuzimanju: {str(e)}"}), 500

@api.post("/filter/design")
def design_filter():
    """Dizajn digitalnog filtera"""
    try:
        payload = request.get_json(force=True)
        cutoff_freq = payload.get("cutoff_frequency", 40)
        fs = payload.get("fs", 250)
        filter_type = payload.get("type", "lowpass")
        
        result = digital_filter_design(cutoff_freq, fs, filter_type)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": f"Greška u dizajnu filtera: {str(e)}"}), 500

@api.post("/analyze/educational")
def educational_analysis():
    """Detaljana edukativna analiza sa vizualizacijama i objašnjenjima"""
    try:
        payload = request.get_json(force=True)
        
        # Opcija 1: Direktno prosleđen signal
        if "signal" in payload:
            signal = payload["signal"]
            fs = payload.get("fs", 250)
        
        # Opcija 2: Analiza slike
        elif "image" in payload:
            print("DEBUG: Starting image processing...")
            # Proverava da li je slika generisana iz signala (preskače validaciju)
            skip_validation = payload.get("skip_validation", False)
            try:
                image_result = process_ekg_image(payload["image"], skip_validation=skip_validation)
                print(f"DEBUG: Image result keys: {list(image_result.keys())}")
                
                if "error" in image_result:
                    print(f"DEBUG: Validation error: {image_result['error']}")
                    return jsonify(image_result), 400
                
                signal = image_result["signal"]
                fs = payload.get("fs", 250)
                print(f"DEBUG: Signal extracted, length: {len(signal)}")
                
                # Predobrada signala
                signal, fs = preprocess_for_analysis(signal, fs)
                print(f"DEBUG: Signal preprocessed, final length: {len(signal)}")
                
            except Exception as e:
                print(f"DEBUG: EXCEPTION in image processing: {str(e)}")
                import traceback
                traceback.print_exc()
                return jsonify({"error": f"Greška pri obradi slike: {str(e)}"}), 400
        else:
            return jsonify({"error": "Potreban je 'signal' ili 'image' parametar"}), 400
        
        # Kreiranje step-by-step edukativne analize
        educational_result = create_step_by_step_analysis(signal, fs)
        
        return jsonify(educational_result)
        
    except Exception as e:
        return jsonify({"error": f"Greška u edukativnoj analizi: {str(e)}"}), 500

@api.post("/convert/signal-to-image")
def convert_signal_to_image():
    """Konvertuje sirove EKG podatke u sliku za testiranje - POBOLJŠANO sa inteligentnom segmentacijom"""
    try:
        payload = request.get_json(force=True)
        signal = payload.get("signal", [])
        fs = payload.get("fs", 250)
        style = payload.get("style", "clinical")  # "clinical" ili "monitor"
        duration_seconds = payload.get("duration_seconds", None)
        
        if not signal:
            return jsonify({"error": "Nedostaje signal"}), 400
        
        if len(signal) < 100:
            return jsonify({"error": "Signal je prekratak (minimum 100 uzoraka)"}), 400
        
        print(f"DEBUG: Converting signal to image, length: {len(signal)}, fs: {fs}, style: {style}")
        
        # POBOLJŠANO: Ultra-fokusirana segmentacija za EKG otkucaje
        optimal_duration = 1  # SAMO 1 SEKUNDA - jedan čist otkucaj kao na referentnoj slici
        optimal_samples = int(optimal_duration * fs)
        
        if len(signal) > optimal_samples and not duration_seconds:
            print(f"DEBUG: Signal je veliki ({len(signal)} uzoraka), tražim jedan savršen otkucaj")
            
            # Pronađi najjači R-pik i napravi 1-sekundni segment oko njega
            critical_analysis = find_critical_segments(signal, fs, segment_duration=1, num_segments=1)
            
            if critical_analysis['critical_segments']:
                best_segment = critical_analysis['critical_segments'][0]
                signal_to_use = best_segment['signal_segment']
                
                print(f"DEBUG: Izabran kritičan segment: {best_segment['start_time']:.1f}-{best_segment['end_time']:.1f}s, "
                      f"kritičnost={best_segment['criticality_score']:.1f}, R-pikovi={best_segment['r_peaks_count']}")
                
                # Generiši sliku od kritičnog segmenta
                image_result = create_ekg_image_from_signal(signal_to_use, fs, None, style)
                
                # Dodatne informacije o segmentaciji
                response_data = {
                    "image_base64": image_result["image_base64"],
                    "metadata": image_result["metadata"],
                    "signal_info": {
                        "original_length": len(signal),
                        "used_segment_length": len(signal_to_use),
                        "sampling_frequency": fs,
                        "original_duration_seconds": len(signal) / fs,
                        "used_segment_duration": len(signal_to_use) / fs,
                        "style": style,
                        "segmentation_used": True,
                        "segment_start_time": best_segment['start_time'],
                        "segment_end_time": best_segment['end_time'],
                        "criticality_score": best_segment['criticality_score'],
                        "r_peaks_in_segment": best_segment['r_peaks_count']
                    },
                    "message": f"Signal segmentiran - korišćen najkritičniji deo ({best_segment['start_time']:.1f}-{best_segment['end_time']:.1f}s) za {style} sliku"
                }
                
                return jsonify(response_data)
            else:
                print(f"WARNING: Inteligentna segmentacija nije pronašla dobre segmente, koristim početak signala")
                signal = signal[:optimal_samples]
        
        # Standardni pristup (kratki signali ili specificirani duration_seconds)
        image_result = create_ekg_image_from_signal(signal, fs, duration_seconds, style)
        
        # Pripremi odgovor
        response_data = {
            "image_base64": image_result["image_base64"],
            "metadata": image_result["metadata"],
            "signal_info": {
                "original_length": len(signal),
                "sampling_frequency": fs,
                "duration_seconds": len(signal) / fs,
                "style": style,
                "segmentation_used": False
            },
            "message": f"Signal konvertovan u {style} stil EKG slike"
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"DEBUG: Error in signal to image conversion: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Greška pri konverziji signala u sliku: {str(e)}"}), 500

@api.post("/test/signal-image-roundtrip")
def test_signal_image_roundtrip():
    """Testira punu petlju: Signal -> Slika -> Analiza signala iz slike"""
    try:
        payload = request.get_json(force=True)
        signal = payload.get("signal", [])
        fs = payload.get("fs", 250)
        style = payload.get("style", "clinical")
        
        if not signal:
            return jsonify({"error": "Nedostaje signal"}), 400
        
        if len(signal) < 100:
            return jsonify({"error": "Signal je prekratak (minimum 100 uzoraka)"}), 400
        
        print(f"DEBUG: Testing roundtrip for signal length: {len(signal)}")
        
        # Testiraj punu petlju
        test_result = test_signal_to_image_conversion(signal, fs)
        
        return jsonify({
            "test_result": test_result,
            "original_signal_info": {
                "length": len(signal),
                "sampling_frequency": fs,
                "duration_seconds": len(signal) / fs
            },
            "test_style": style
        })
        
    except Exception as e:
        print(f"DEBUG: Error in roundtrip test: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Greška pri testiranju roundtrip konverzije: {str(e)}"}), 500

@api.post("/analyze/wfdb-to-image")
def analyze_wfdb_to_image():
    """Analizira WFDB fajlove i kreira sliku EKG-a - POBOLJŠANO sa .atr podrškom"""
    try:
        # Čitanje fajlova iz form-data
        files = request.files
        style = request.form.get("style", "clinical")
        duration_seconds = request.form.get("duration_seconds", None)
        if duration_seconds:
            duration_seconds = float(duration_seconds)
        
        if not files:
            return jsonify({"error": "Nedostaju fajlovi"}), 400
        
        # Konvertovanje u dict {filename: content}
        files_dict = {}
        for key in files.keys():
            file_list = files.getlist(key)
            for file in file_list:
                if file.filename:
                    files_dict[file.filename] = file.read()
        
        if not validate_wfdb_files(files_dict):
            return jsonify({"error": "Potrebni su .dat i .hea fajlovi"}), 400
        
        # Pronađi sve WFDB fajlove
        dat_content = None
        hea_content = None
        atr_content = None  # NOVO: .atr podrška
        dat_filename = ""
        atr_filename = ""
        
        for filename, content in files_dict.items():
            if filename.endswith('.dat'):
                dat_content = content
                dat_filename = filename
            elif filename.endswith('.hea'):
                hea_content = content.decode('utf-8')
            elif filename.endswith('.atr'):  # NOVO: čitaj .atr fajl
                atr_content = content
                atr_filename = filename
                print(f"DEBUG: Found .atr file for image generation: {filename}")
        
        if not dat_content or not hea_content:
            return jsonify({"error": "Potrebni su i .dat i .hea fajlovi"}), 400
        
        print(f"DEBUG: Processing WFDB to image: {dat_filename}")
        if atr_content:
            print(f"DEBUG: Will use annotations from {atr_filename} for better segmentation")
        
        # NOVO: Parsiranje sa annotations
        if atr_content:
            signals, fs, metadata, annotations = parse_wfdb_files_with_annotations(dat_content, hea_content, atr_content)
        else:
            signals, fs, metadata = parse_wfdb_files(dat_content, hea_content)
            annotations = {}
        
        # Izvuci prvi kanal za konverziju
        signal = extract_signal_for_analysis(signals, channel=0)
        
        if len(signal) < 100:
            return jsonify({"error": "Signal je prekratak (minimum 100 uzoraka)"}), 400
        
        # POBOLJŠANO: Ultra-fokusirana segmentacija za WFDB - jedan otkucaj
        if duration_seconds:
            max_samples = int(duration_seconds * fs)
        else:
            max_samples = int(1 * fs)  # SAMO 1 SEKUNDA za čist EKG otkucaj
        
        segment_info = {}
        
        if len(signal) > max_samples:
            print(f"DEBUG: WFDB signal je veliki ({len(signal)} uzoraka), tražim najbolji otkucaj")
            
            # Ultra-agresivna 1-sekundna segmentacija oko najjačeg R-pika
            critical_analysis = find_critical_segments(signal, fs, segment_duration=1, num_segments=1)
            
            if critical_analysis['critical_segments']:
                best_segment = critical_analysis['critical_segments'][0]
                signal = best_segment['signal_segment']
                
                segment_info = {
                    "segmentation_used": True,
                    "segment_start_time": best_segment['start_time'],
                    "segment_end_time": best_segment['end_time'],
                    "criticality_score": best_segment['criticality_score'],
                    "r_peaks_in_segment": best_segment['r_peaks_count'],
                    "segmentation_method": "intelligent_critical_analysis"
                }
                
                print(f"DEBUG: Izabran kritičan WFDB segment: {best_segment['start_time']:.1f}-{best_segment['end_time']:.1f}s, "
                      f"kritičnost={best_segment['criticality_score']:.1f}, R-pikovi={best_segment['r_peaks_count']}")
            else:
                # Fallback na staru metodu ako inteligentna segmentacija ne uspe
                print(f"WARNING: Inteligentna segmentacija neuspešna, koristim početak signala")
                signal = signal[:max_samples]
                segment_info = {
                    "segmentation_used": True,
                    "segmentation_method": "fallback_beginning",
                    "segment_start_time": 0,
                    "segment_end_time": len(signal) / fs
                }
        else:
            segment_info = {"segmentation_used": False}
        
        if len(signal) < fs:  # Minimum 1 sekunda
            print(f"WARNING: Signal prekratak za sliku: {len(signal)} uzoraka")
            return jsonify({"error": "Signal je prekratak za generisanje slike"}), 400
        
        print(f"DEBUG: Creating image from WFDB signal, length: {len(signal)}, fs: {fs}")
        
        # Kreiraj sliku iz signala
        image_result = create_ekg_image_from_signal(signal, fs, duration_seconds, style)
        
        # Vrati sliku i metapodatke sa informacijama o segmentaciji
        signal_info = {
            "used_segment_length": len(signal),
            "duration_seconds": len(signal) / fs,
            "sampling_frequency": fs,
            "source": "wfdb_conversion",
            "filename": dat_filename,
            "style": style,
            "has_annotations": bool(atr_content)  # NOVO: da li su korišćeni annotations
        }
        
        # Dodaj informacije o segmentaciji
        signal_info.update(segment_info)
        
        # Poruka o tome da li je korišćena segmentacija
        if segment_info.get("segmentation_used", False):
            if segment_info.get("segmentation_method") == "intelligent_critical_analysis":
                annotation_note = " (sa .atr annotations)" if atr_content else ""
                message = f"WFDB signal segmentiran - korišćen najkritičniji deo ({segment_info['segment_start_time']:.1f}-{segment_info['segment_end_time']:.1f}s) za {style} sliku{annotation_note}"
            else:
                message = f"WFDB signal skraćen na početnih {len(signal)/fs:.1f}s za {style} sliku"
        else:
            annotation_note = " (sa .atr annotations)" if atr_content else ""
            message = f"WFDB signal konvertovan u {style} stil EKG slike{annotation_note}"
        
        response_data = {
            "image_base64": image_result["image_base64"],
            "image_metadata": image_result["metadata"],
            "signal_info": signal_info,
            "wfdb_metadata": {
                "record_name": metadata.get('record_name'),
                "n_signals": metadata.get('n_signals'),
                "original_samples": metadata.get('n_samples'),
                "signals_info": metadata.get('signals', [])
            },
            "message": message
        }
        
        # NOVO: Dodaj annotation informacije ako su dostupne
        if annotations:
            response_data["annotations"] = {
                "total_annotations": annotations.get('total_annotations', 0),
                "r_peaks_count": len(annotations.get('r_peaks', [])),
                "arrhythmias_count": len(annotations.get('arrhythmias', [])),
                "annotation_types": annotations.get('annotation_types', {}),
                "source_file": atr_filename,
                "note": "Annotation podatci iz .atr fajla mogu poboljšati segmentaciju"
            }
            
            print(f"DEBUG: Image generated with {annotations.get('total_annotations', 0)} annotations from {atr_filename}")
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"DEBUG: Error in WFDB to image conversion: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Greška pri konverziji WFDB u sliku: {str(e)}"}), 500


@api.post("/generate/educational-ekg-image")
def generate_educational_ekg_image():
    """
    Generiše edukativnu EKG sliku sa rezultatima analize
    Koristi se nakon analize sirovih podataka
    """
    try:
        payload = request.get_json(force=True)
        signal = payload.get("signal", [])
        analysis_results = payload.get("analysis_results", {})
        fs = payload.get("fs", 250)
        duration_seconds = payload.get("duration_seconds", None)
        
        if not signal:
            return jsonify({"error": "Nedostaje signal"}), 400
        
        if not analysis_results:
            return jsonify({"error": "Nedostaju rezultati analize"}), 400
        
        if len(signal) < 100:
            return jsonify({"error": "Signal je prekratak (minimum 100 uzoraka)"}), 400
        
        print(f"DEBUG: Generating educational EKG image, signal length: {len(signal)}")
        
        # Generiši edukativnu sliku
        image_result = create_educational_ekg_image(signal, analysis_results, fs, duration_seconds)
        
        # Pripremi odgovor
        response_data = {
            "image_base64": image_result["image_base64"],
            "metadata": image_result["metadata"],
            "signal_info": {
                "original_length": len(signal),
                "sampling_frequency": fs,
                "duration_seconds": len(signal) / fs,
                "analysis_included": True
            },
            "message": "Edukativna EKG slika generisana sa rezultatima analize"
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"DEBUG: Error generating educational EKG image: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Greška pri generisanju edukativne EKG slike: {str(e)}"}), 500

@api.get("/info")
def api_info():
    """Informacije o dostupnim endpoint-ima"""
    return jsonify({
        "endpoints": {
            "/health": "GET - Provera zdravlja API-ja",
            "/analyze/fft": "POST - FFT analiza signala",
            "/analyze/image": "POST - Konverzija EKG slike u signal",
            "/analyze/complete": "POST - Kompletna analiza (slika ili signal)",
            "/analyze/raw-signal": "POST - Analiza direktno uvezenih sirovih signala",
            "/analyze/wfdb": "POST - Analiza WFDB formata (.dat + .hea + .atr fajlovi)",
            "/analyze/educational": "POST - Detaljana edukativna analiza sa vizualizacijama",
            "/analyze/ztransform": "POST - Z-transformacija signala",
            "/analyze/arrhythmia": "POST - Detekcija aritmija",
            "/convert/signal-to-image": "POST - Konvertuje sirove EKG podatke u sliku (POBOLJŠANO sa inteligentnom segmentacijom)",
            "/test/signal-image-roundtrip": "POST - Testira Signal -> Slika -> Analiza petlju",
            "/analyze/wfdb-to-image": "POST - Konvertuje WFDB fajlove u EKG sliku (POBOLJŠANO sa .atr annotations i inteligentnom segmentacijom)",
            "/generate/educational-ekg-image": "POST - Generiše edukativnu EKG sliku sa rezultatima analize",
            "/filter/design": "POST - Dizajn digitalnog filtera",
            "/download/wfdb/<record>/<type>": "GET - Preuzmi WFDB fajl sa PhysioNet-a",
            "/info": "GET - Ove informacije"
        },
        "version": "2.0",
        "description": "EKG analiza API - analiza slika i sirovih signala",
        "scientific_methods": [
            "Spatial Filling Index (Faust et al., 2004)",
            "Time-Frequency Analysis (STFT)",
            "Wavelet Decomposition (Yıldırım, 2018)",
            "Advanced Digital Filtering (Sörnmo & Laguna, 2005)",
            "Raw Signal Import & Analysis",
            "Image Processing & Validation"
        ],
        "input_methods": [
            "📸 EKG fotografije - JPG, PNG, WEBP",
            "📁 Sirovi signali - CSV, TXT, JSON",
            "🏥 WFDB format - .dat + .hea + .atr (MIT-BIH sa annotations)"
        ]
    })
