from flask import Blueprint, jsonify, request, render_template, send_file
import numpy as np

# Create Blueprint
main = Blueprint('main', __name__)

# Import za seaborn styling
try:
    import matplotlib
    matplotlib.use('Agg')  # Set non-interactive backend
    import matplotlib.pyplot as plt
    # Try to use seaborn style, fallback to default if not available
    try:
        plt.style.use('seaborn-v0_8')
    except:
        try:
            plt.style.use('seaborn')
        except:
            pass  # Use default style
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

def convert_numpy_to_json_serializable(obj):
    """Recursively converts NumPy types to JSON-serializable Python types"""
    import math
    
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        val = float(obj)
        # Handle Infinity and NaN
        if math.isnan(val):
            return None  # Convert NaN to null
        elif math.isinf(val):
            return None  # Convert Infinity to null
        else:
            return val
    elif isinstance(obj, (float, int)):
        # Handle regular Python float/int that might be inf/nan
        if isinstance(obj, float):
            if math.isnan(obj):
                return None
            elif math.isinf(obj):
                return None
        return obj
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_numpy_to_json_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_to_json_serializable(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(convert_numpy_to_json_serializable(item) for item in obj)
    else:
        return obj

def safe_jsonify(data):
    """Safe jsonify that converts NumPy types first"""
    converted_data = convert_numpy_to_json_serializable(data)
    return jsonify(converted_data)
from .analysis.fft import analyze_fft
from .analysis.ztransform import z_transform_analysis, digital_filter_design
from .analysis.image_processing import process_ekg_image, preprocess_for_analysis
from .analysis.improved_image_processing import process_ekg_image_improved, analyze_ekg_rhythm_from_image
from .analysis.arrhythmia_detection import detect_arrhythmias
from .analysis.advanced_ekg_analysis import comprehensive_ekg_analysis
from .analysis.educational_visualization import create_step_by_step_analysis
from .analysis.wfdb_reader import parse_wfdb_files, validate_wfdb_files, extract_signal_for_analysis, parse_wfdb_files_with_annotations
from .analysis.advanced_cardiology_analysis import advanced_ekg_analysis
from .analysis.simple_thesis_viz import create_simple_thesis_visualizations
from .analysis.signal_to_image import create_ekg_image_from_signal, test_signal_to_image_conversion
from .analysis.educational_ekg_image import create_educational_ekg_image
from .analysis.intelligent_signal_segmentation import find_critical_segments
from datetime import datetime

# api = Blueprint("api", __name__)  # Replaced with main above

@main.get("/")
def index():
    """Glavna stranica mobilne web aplikacije"""
    return render_template('index.html')

@main.get("/health")
def health():
    return jsonify(status="ok")

@main.post("/analyze/fft")
def analyze_fft_endpoint():
    """FFT analiza digitalnog signala"""
    payload = request.get_json(force=True)
    signal = payload.get("signal", [])
    fs = payload.get("fs", 250)
    result = analyze_fft(signal, fs)
    return jsonify(result)

@main.post("/analyze/image")
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

@main.post("/analyze/complete")
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
                image_result = process_ekg_image_improved(payload["image"], skip_validation=skip_validation)
                
                if "error" in image_result:
                    # Fallback na staru verziju
                    print("DEBUG: Improved processing failed, trying original...")
                    image_result = process_ekg_image(payload["image"], skip_validation=skip_validation)
                    
                    if "error" in image_result:
                        print(f"DEBUG: Both processing methods failed: {image_result['error']}")
                        return jsonify(image_result), 400
                
                print(f"DEBUG: Image processing result keys: {list(image_result.keys())}")
                
                if "error" in image_result:
                    print(f"DEBUG: Image processing error: {image_result["error"]}")
                    return jsonify(image_result), 400
                
                signal = image_result["signal"]
                fs = payload.get("fs", 250)
                print(f"DEBUG: Extracted signal length: {len(signal)}")
                
                # Predobrada signala - koristi iz improved_image_processing
                from .analysis.improved_image_processing import preprocess_for_analysis as preprocess_improved
                try:
                    signal, fs = preprocess_improved(signal, fs)
                except Exception as e:
                    print(f"DEBUG: Improved preprocessing failed: {e}, using original")
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
        
        # 4. Fokus na Furijeovu i Z-transformaciju (tema rada)
        # results["advanced_cardiology"] = advanced_ekg_analysis(signal, fs, annotations=None, wfdb_metadata=None)
        
        # 5. Osnovne informacije + poboljšane image info
        image_info = {}
        if "image" in payload:
            # Ako je signal dobijen iz slike, dodaj image metadata
            image_info = {
                "source": "image_analysis",
                "processing_method": "improved_multi_lead_detection" if hasattr(locals(), 'image_result') and "detected_leads" in locals().get('image_result', {}) else "basic_contour",
                "detected_leads": locals().get('image_result', {}).get("detected_leads", 1),
                "estimated_heart_rate_from_image": locals().get('image_result', {}).get("estimated_heart_rate", {})
            }
        else:
            image_info = {
                "source": "direct_signal",
                "processing_method": "direct_input"
            }
        
        results["signal_info"] = {
            "length": len(signal),
            "duration_seconds": len(signal) / fs,
            "sampling_frequency": fs,
            **image_info
        }
        
        # 5.5. NOVA: Analiza ritma iz slike (pre algoritamske analize)
        try:
            results["image_rhythm_analysis"] = analyze_ekg_rhythm_from_image(signal)
            print(f"DEBUG: Image rhythm analysis: {results['image_rhythm_analysis']['heart_rate_bpm']} bpm")
        except Exception as e:
            print(f"DEBUG: Image rhythm analysis failed: {str(e)}")
            results["image_rhythm_analysis"] = {"error": str(e)}
        
        # 6. NOVO: Jednostavne vizuelizacije za master rad
        # VRAĆENO v3.1: Optimizovane vizuelizacije - samo ako nisu zahtevane brže analize
        try:
            print("DEBUG v3.1 ROUTES: Pozivam OPTIMIZOVANE vizuelizacije...")
            results["thesis_visualizations"] = create_simple_thesis_visualizations(
                signal, fs, results, annotations=None
            )
            print("DEBUG v3.1 ROUTES: Optimizovane vizuelizacije uspešne")
        except Exception as e:
            print(f"ERROR v3.1 ROUTES: Optimizovane vizuelizacije neuspešne: {str(e)}")
            results["thesis_visualizations"] = {"error": f"Vizuelizacije neuspešne: {str(e)}"}
        
        return safe_jsonify(results)
        
    except Exception as e:
        return jsonify({"error": f"Greška pri kompletnoj analizi: {str(e)}"}), 500

@main.post("/analyze/ztransform")
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

@main.post("/analyze/arrhythmia")
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

@main.post("/analyze/raw-signal")
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
        
        # 4. Fokus na Furijeovu i Z-transformaciju (tema rada)
        # results["advanced_cardiology"] = advanced_ekg_analysis(signal, fs, annotations=None, wfdb_metadata=None)
        
        # 5. Osnovne informacije sa dodatnim metapodacima
        results["signal_info"] = {
            "length": len(signal),
            "duration_seconds": len(signal) / fs,
            "sampling_frequency": fs,
            "source": "raw_import",
            "filename": filename,
            "import_method": "direct_file_upload"
        }
        
        # 6. NOVO: Jednostavne vizuelizacije za master rad (raw signal)
        try:
            print("DEBUG v3.0 ROUTES: Pozivam create_simple_thesis_visualizations (raw signal)...")
            results["thesis_visualizations"] = create_simple_thesis_visualizations(
                signal, fs, results, annotations=None
            )
            print("DEBUG v3.0 ROUTES: Raw signal simple visualizations created successfully")
        except Exception as e:
            print(f"DEBUG: Raw signal simple visualizations failed: {str(e)}")
            results["thesis_visualizations"] = {"error": f"Vizuelizacije neuspešne: {str(e)}"}
        
        return safe_jsonify(results)
        
    except Exception as e:
        print(f"DEBUG: Error in raw signal analysis: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Greška pri analizi sirovih podataka: {str(e)}"}), 500

@main.post("/analyze/wfdb")
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
        
        # 4. Fokus na Furijeovu i Z-transformaciju (tema rada)
        # results["advanced_cardiology"] = advanced_ekg_analysis(signal, fs, annotations=annotations, wfdb_metadata=wfdb_meta)
        
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
                "source_file": atr_filename,
                "samples": annotations.get('r_peaks', [])  # Dodano za vizuelizacije
            }
            
            # POBOLJŠANO: Koristi annotation R-pikove za bolju analizu aritmija
            if annotations.get('r_peaks'):
                print(f"DEBUG: Using {len(annotations['r_peaks'])} annotated R-peaks for enhanced arrhythmia detection")
                # Možete dodati logiku koja koristi tačne R-peak pozicije iz annotations
        
        # 8. VRAĆENO v3.1: WFDB vizuelizacije sa optimizovanom slikom 3
        try:
            print("DEBUG v3.1 ROUTES: Pozivam OPTIMIZOVANE WFDB vizuelizacije...")
            print(f"DEBUG v3.1 ROUTES: Annotations type: {type(annotations)}")
            print(f"DEBUG v3.1 ROUTES: Annotations keys: {list(annotations.keys()) if isinstance(annotations, dict) else 'Not dict'}")
            if annotations and 'r_peaks' in annotations:
                print(f"DEBUG v3.1 ROUTES: R-peaks count: {len(annotations['r_peaks'])}")
                if annotations['r_peaks']:
                    print(f"DEBUG v3.1 ROUTES: Prvi R-peak: {annotations['r_peaks'][0]}")
            results["thesis_visualizations"] = create_simple_thesis_visualizations(
                signal, fs, results, annotations=annotations
            )
            print("DEBUG v3.1 ROUTES: WFDB optimizovane vizuelizacije uspešne")
        except Exception as e:
            print(f"ERROR v3.1 ROUTES: WFDB optimizovane vizuelizacije neuspešne: {str(e)}")
            results["thesis_visualizations"] = {"error": f"Vizuelizacije neuspešne: {str(e)}"}
        
        return safe_jsonify(results)
        
    except Exception as e:
        print(f"DEBUG: Error in WFDB analysis: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Greška pri analizi WFDB fajlova: {str(e)}"}), 500

@main.get("/download/wfdb/<record_name>/<file_type>")
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

@main.post("/filter/design")
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

@main.post("/analyze/educational")
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

@main.post("/convert/signal-to-image")
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

@main.post("/test/signal-image-roundtrip")
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

@main.post("/analyze/wfdb-to-image")
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


@main.post("/generate/educational-ekg-image")
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

@main.get("/info")
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
            "/generate/png/time-domain": "POST - 🖼️ PNG time-domain grafikon (matplotlib backend)",
            "/generate/png/fft-spectrum": "POST - 🖼️ PNG FFT spektar (profesionalni dijagram)",
            "/generate/png/z-plane": "POST - 🖼️ PNG Z-ravan pole-zero analiza",
            "/validate/mitbih": "POST - 🔬 MIT-BIH validacija (TP/FP/FN, precision/recall/F1)",
            "/analyze/snr": "POST - 📊 REALISTIČNI SNR ANALIZA (Odličan/Dobar/Osrednji/Loš)",
            "/generate/complete-report": "POST - 📊 INTEGRISANI IZVEŠTAJ sa opcionalnim PDF (generate_pdf: true)",
            "/generate/pdf-report": "POST - 📄 DIREKTNI PDF DOWNLOAD (samo PDF fajl)",
            "/generate/pdf-from-analysis": "POST - 📄 PDF iz postojećih rezultata analize",
            "/info": "GET - Ove informacije"
        },
        "version": "3.0_auto_advanced_debug",
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

# =============================================================================
# PNG VISUALIZATION ENDPOINTS - Backend matplotlib implementacija
# =============================================================================

@main.route('/generate/png/time-domain', methods=['POST'])
def generate_time_domain_png():
    """
    Generiše PNG grafikon time-domain analize
    
    Reference:
    - Singh, A., et al. (2018). FFT-based analysis of ECG signals. IET Signal Processing.
    """
    try:
        from .analysis.visualization_generator import EKGVisualizationGenerator
        from .analysis.arrhythmia_detection import detect_r_peaks
        
        data = request.get_json()
        signal_data = data.get('signal_data', [])
        fs = data.get('fs', 250)
        title = data.get('title', 'EKG Signal Analysis')
        
        if not signal_data:
            return jsonify({"error": "signal_data je obavezan"}), 400
        
        signal_array = np.array(signal_data, dtype=float)
        
        # R-peak detekcija za vizualizaciju
        try:
            r_peaks_result = detect_r_peaks(signal_array, fs)
            if isinstance(r_peaks_result, dict) and 'error' not in r_peaks_result:
                r_peaks = r_peaks_result.get('r_peaks', [])
            elif isinstance(r_peaks_result, (list, np.ndarray)):
                r_peaks = list(r_peaks_result)
            else:
                r_peaks = []
        except Exception as e:
            print(f"R-peak detection error: {e}")
            r_peaks = []
        
        # Generiši PNG
        viz_gen = EKGVisualizationGenerator()
        png_path = viz_gen.generate_time_domain_plot(signal_array, fs, r_peaks, title)
        
        if isinstance(png_path, dict) and "error" in png_path:
            return jsonify(png_path), 500
        
        return send_file(png_path, as_attachment=True, download_name="ekg_time_domain.png")
        
    except Exception as e:
        return jsonify({"error": f"PNG generation failed: {str(e)}"}), 500

@main.route('/generate/png/fft-spectrum', methods=['POST'])
def generate_fft_spectrum_png():
    """
    Generiše PNG grafikon FFT spektralne analize
    
    Reference:
    - Hong, S., et al. (2020). Hybrid frequency-time methods for ECG analysis. 
      Circulation Research. DOI: 10.1161/CIRCRESAHA.119.316681
    """
    try:
        from .analysis.visualization_generator import EKGVisualizationGenerator
        
        data = request.get_json()
        signal_data = data.get('signal_data', [])
        fs = data.get('fs', 250)
        title = data.get('title', 'FFT Spektralna Analiza')
        
        if not signal_data:
            return jsonify({"error": "signal_data je obavezan"}), 400
        
        signal_array = np.array(signal_data, dtype=float)
        
        # Generiši PNG
        viz_gen = EKGVisualizationGenerator()
        png_path = viz_gen.generate_fft_spectrum_plot(signal_array, fs, title)
        
        if isinstance(png_path, dict) and "error" in png_path:
            return jsonify(png_path), 500
        
        return send_file(png_path, as_attachment=True, download_name="ekg_fft_spectrum.png")
        
    except Exception as e:
        return jsonify({"error": f"PNG generation failed: {str(e)}"}), 500

@main.route('/generate/png/z-plane', methods=['POST'])
def generate_z_plane_png():
    """
    Generiše PNG grafikon Z-ravan pole-zero analize
    
    Reference:
    - Zhang, T., et al. (2021). Pole-zero analysis using Z-transform for ECG signal 
      stability detection. Biomedical Signal Processing. DOI: 10.1016/j.bspc.2021.102543
    """
    try:
        from .analysis.visualization_generator import EKGVisualizationGenerator
        from .analysis.ztransform import z_transform_analysis
        
        data = request.get_json()
        signal_data = data.get('signal_data', [])
        fs = data.get('fs', 250)
        title = data.get('title', 'Z-Ravan Analiza')
        
        if not signal_data:
            return jsonify({"error": "signal_data je obavezan"}), 400
        
        signal_array = np.array(signal_data, dtype=float)
        
        # Z-transform analiza
        z_result = z_transform_analysis(signal_array, fs)
        if "error" in z_result:
            return jsonify(z_result), 500
        
        poles = z_result.get('poles', [])
        zeros = z_result.get('zeros', [])
        
        # Generiši PNG
        viz_gen = EKGVisualizationGenerator()
        png_path = viz_gen.generate_pole_zero_plot(poles, zeros, title)
        
        if isinstance(png_path, dict) and "error" in png_path:
            return jsonify(png_path), 500
        
        return send_file(png_path, as_attachment=True, download_name="z_plane_analysis.png")
        
    except Exception as e:
        return jsonify({"error": f"PNG generation failed: {str(e)}"}), 500

# =============================================================================
# MIT-BIH VALIDATION ENDPOINT
# =============================================================================

@main.route('/validate/mitbih', methods=['POST'])
def validate_against_mitbih():
    """
    MIT-BIH database validacija - precision/recall/F1 score
    
    Reference:
    - Goldberger, A. L., et al. (2020). PhysioBank, PhysioToolkit, and PhysioNet: 
      Components of a new research resource for complex physiologic signals. 
      Circulation, 101(23), e215-e220. DOI: 10.1161/01.CIR.101.23.e215
    """
    try:
        from .analysis.mitbih_validator import MITBIHValidator
        from .analysis.arrhythmia_detection import detect_r_peaks
        
        data = request.get_json()
        signal_data = data.get('signal_data', [])
        record_path = data.get('record_path', '')
        fs = data.get('fs', 360)  # MIT-BIH default
        tolerance_ms = data.get('tolerance_ms', 50)
        
        if not signal_data:
            return jsonify({"error": "signal_data je obavezan"}), 400
        
        if not record_path:
            return jsonify({"error": "record_path je obavezan za MIT-BIH validaciju"}), 400
        
        signal_array = np.array(signal_data, dtype=float)
        
        # Detektuj R-pikove
        r_peaks_result = detect_r_peaks(signal_array, fs)
        if "error" in r_peaks_result:
            return jsonify(r_peaks_result), 500
        
        detected_peaks = r_peaks_result.get('r_peaks', [])
        
        # MIT-BIH validacija
        validator = MITBIHValidator(tolerance_ms=tolerance_ms)
        validation_report = validator.generate_validation_report(
            signal_array, detected_peaks, record_path, fs
        )
        
        if "error" in validation_report:
            return jsonify(validation_report), 500
        
        return safe_jsonify({
            "validation_report": validation_report,
            "detection_results": r_peaks_result,
            "input_parameters": {
                "record_path": record_path,
                "tolerance_ms": tolerance_ms,
                "sampling_frequency": fs,
                "signal_length": len(signal_array)
            }
        })
        
    except Exception as e:
        return jsonify({"error": f"MIT-BIH validation failed: {str(e)}"}), 500

# =============================================================================
# INTEGRISANI IZVEŠTAJ - One-click complete analysis
# =============================================================================

@main.route('/generate/complete-report', methods=['POST'])
def generate_complete_analysis_report():
    """
    INTEGRISANI IZVEŠTAJ - Jednim klikom kompletna analiza
    
    Vraća: Fs, trajanje, R-pikovi, HR/HRV, FFT peak, realistični SNR + PNG linkovi
    
    Reference:
    - Singh, A., et al. (2018). FFT-based analysis of ECG signals. IET Signal Processing.
    - IEEE Std 1057-2017: Standard for Digitizing Waveform Recorders (SNR calculation)
    """
    try:
        from .analysis.visualization_generator import EKGVisualizationGenerator
        from .analysis.arrhythmia_detection import detect_r_peaks
        from .analysis.fft import analyze_fft
        from .analysis.ztransform import z_transform_analysis
        # from .analysis.advanced_ekg_analysis import analyze_ekg_signal  # Not needed for complete report
        from scipy import signal as scipy_signal
        from datetime import datetime
        
        data = request.get_json()
        signal_data = data.get('signal_data', [])
        fs = data.get('fs', 250)
        title = data.get('title', 'EKG Complete Analysis Report')
        include_mitbih = data.get('include_mitbih_validation', False)
        record_path = data.get('record_path', '')
        
        if not signal_data:
            return jsonify({"error": "signal_data je obavezan"}), 400
        
        signal_array = np.array(signal_data, dtype=float)
        signal_length_sec = len(signal_array) / fs
        
        # =================================================================
        # 1. OSNOVNE INFORMACIJE
        # =================================================================
        basic_info = {
            "sampling_frequency_hz": fs,
            "signal_duration_sec": float(signal_length_sec),
            "total_samples": len(signal_array),
            "signal_range": {
                "min": float(np.min(signal_array)),
                "max": float(np.max(signal_array)),
                "mean": float(np.mean(signal_array)),
                "std": float(np.std(signal_array))
            }
        }
        
        # =================================================================
        # 2. R-PEAK DETEKCIJA I HR/HRV ANALIZA
        # =================================================================
        try:
            r_peaks_raw = detect_r_peaks(signal_array, fs)
            # detect_r_peaks vraća numpy array direktno
            if isinstance(r_peaks_raw, np.ndarray):
                r_peaks = r_peaks_raw.tolist()
            elif isinstance(r_peaks_raw, list):
                r_peaks = r_peaks_raw
            else:
                r_peaks = []
        except Exception as e:
            print(f"R-peak detection failed: {e}")
            r_peaks = []
        
        # Kreiraj r_peaks_result format za kompatibilnost
        r_peaks_result = {"r_peaks": r_peaks} if r_peaks else {"error": "No R-peaks detected"}
        
        hr_hrv_analysis = {}
        if len(r_peaks) > 0:
            
            if len(r_peaks) > 1:
                # Heart Rate
                heart_rate_bpm = len(r_peaks) / signal_length_sec * 60
                
                # HRV analiza
                rr_intervals = np.diff(r_peaks) / fs * 1000  # ms
                hrv_rmssd = float(np.sqrt(np.mean(np.diff(rr_intervals)**2)))
                hrv_sdnn = float(np.std(rr_intervals))
                hrv_pnn50 = float(np.sum(np.abs(np.diff(rr_intervals)) > 50) / len(rr_intervals) * 100)
                
                hr_hrv_analysis = {
                    "r_peaks_count": len(r_peaks),
                    "heart_rate_bpm": float(heart_rate_bpm),
                    "rr_intervals_ms": rr_intervals.tolist(),
                    "hrv_metrics": {
                        "rmssd_ms": hrv_rmssd,
                        "sdnn_ms": hrv_sdnn,
                        "pnn50_percent": hrv_pnn50,
                        "mean_rr_ms": float(np.mean(rr_intervals)),
                        "min_rr_ms": float(np.min(rr_intervals)),
                        "max_rr_ms": float(np.max(rr_intervals))
                    }
                }
        
        # =================================================================
        # 3. FFT ANALIZA - DOMINANTNA FREKVENCIJA
        # =================================================================
        fft_result = analyze_fft(signal_array, fs)
        fft_peak_analysis = {}
        
        if "error" not in fft_result:
            spectrum = fft_result.get('spectrum', [])
            frequencies = fft_result.get('frequencies', [])
            
            if spectrum and frequencies:
                # Fiziološki relevantni opseg (0.5-10 Hz)
                freq_array = np.array(frequencies)
                spectrum_array = np.array(spectrum)
                physio_mask = (freq_array >= 0.5) & (freq_array <= 10.0)
                
                if np.any(physio_mask):
                    physio_spectrum = spectrum_array[physio_mask]
                    physio_freq = freq_array[physio_mask]
                    
                    peak_idx = np.argmax(physio_spectrum)
                    dominant_freq = physio_freq[peak_idx]
                    peak_amplitude = physio_spectrum[peak_idx]
                    
                    fft_peak_analysis = {
                        "dominant_frequency_hz": float(dominant_freq),
                        "peak_amplitude": float(peak_amplitude),
                        "frequency_category": _categorize_frequency(dominant_freq),
                        "physiological_range_power": float(np.sum(physio_spectrum**2))
                    }
        
        # =================================================================
        # 4. REALISTIČNI SNR PO SEGMENTIMA
        # =================================================================
        snr_analysis = {}
        try:
            # Jednostavan bandpass filter za "čist" signal
            nyquist = fs / 2
            low_freq = 0.5 / nyquist
            high_freq = 40 / nyquist
            b, a = scipy_signal.butter(4, [low_freq, high_freq], btype='band')
            filtered_signal = scipy_signal.filtfilt(b, a, signal_array)
            
            # SNR kalkulacija po segmentima
            viz_gen = EKGVisualizationGenerator()
            snr_result = viz_gen.calculate_realistic_snr(signal_array, filtered_signal, fs, 10)
            
            if "error" not in snr_result:
                snr_analysis = snr_result
                
        except Exception as e:
            snr_analysis = {"error": f"SNR calculation failed: {str(e)}"}
        
        # =================================================================
        # 5. Z-TRANSFORM STABILNOST
        # =================================================================
        z_analysis = {}
        z_result = z_transform_analysis(signal_array, fs)
        if "error" not in z_result:
            stability = z_result.get('stability', {})
            z_analysis = {
                "system_stable": stability.get('stable', False),
                "max_pole_magnitude": stability.get('max_pole_magnitude', 0),
                "pole_count": stability.get('pole_count', 0),
                "stability_message": stability.get('message', 'Unknown')
            }
        
        # =================================================================
        # 6. MIT-BIH VALIDACIJA (opcionalno)
        # =================================================================
        mitbih_validation = {}
        if include_mitbih and record_path:
            try:
                from .analysis.mitbih_validator import MITBIHValidator
                validator = MITBIHValidator(tolerance_ms=50)
                validation_report = validator.generate_validation_report(
                    signal_array, r_peaks, record_path, fs
                )
                if "error" not in validation_report:
                    mitbih_validation = validation_report
            except Exception as e:
                mitbih_validation = {"error": f"MIT-BIH validation failed: {str(e)}"}
        
        # =================================================================
        # 7. KOMPLETNI IZVEŠTAJ
        # =================================================================
        complete_report = {
            "report_metadata": {
                "generated_at": datetime.now().isoformat(),
                "title": title,
                "analysis_version": "3.1_production"
            },
            "signal_information": basic_info,
            "cardiac_analysis": {
                "r_peak_detection": r_peaks_result,
                "heart_rate_variability": hr_hrv_analysis
            },
            "frequency_analysis": {
                "fft_results": fft_result,
                "dominant_frequency": fft_peak_analysis
            },
            "signal_quality": {
                "snr_analysis": snr_analysis,
                "z_transform_stability": z_analysis
            },
            "validation": {
                "mitbih_comparison": mitbih_validation if mitbih_validation else "Not requested"
            },
            "png_visualizations": {
                "note": "Use separate PNG endpoints to generate visualizations",
                "available_endpoints": [
                    "/generate/png/time-domain",
                    "/generate/png/fft-spectrum", 
                    "/generate/png/z-plane"
                ]
            },
            "summary": {
                "overall_quality": _assess_overall_quality(snr_analysis, z_analysis, hr_hrv_analysis),
                "recommendations": _generate_recommendations(snr_analysis, fft_peak_analysis, hr_hrv_analysis)
            }
        }
        
        # NOVO: SNR ANALIZA ZA QUALITET ASSESSMENT
        try:
            from .analysis.visualization_generator import EKGVisualizationGenerator
            from .analysis.advanced_ekg_analysis import advanced_filtering
            
            signal_array = np.array(signal, dtype=float)
            
            # Filtered signal za SNR
            try:
                filtered_signal = advanced_filtering(signal_array, fs)
            except Exception:
                # Fallback filtering
                from scipy.signal import butter, filtfilt
                nyquist = fs / 2
                low_cutoff = 40 / nyquist
                b, a = butter(4, low_cutoff, btype='low')
                filtered_signal = filtfilt(b, a, signal_array)
            
            # Calculate SNR
            viz_gen = EKGVisualizationGenerator()
            snr_results = viz_gen.calculate_realistic_snr(signal_array, filtered_signal, fs, 10)
            
            if "error" not in snr_results:
                complete_report["signal_quality"] = {
                    "snr_db": round(snr_results["mean_snr_db"], 2),
                    "quality_category": snr_results["overall_category"],
                    "quality_score": round(8.5 if snr_results["mean_snr_db"] >= 20 else 
                                         7.0 if snr_results["mean_snr_db"] >= 15 else
                                         5.5 if snr_results["mean_snr_db"] >= 10 else 3.0, 1),
                    "professional_assessment": f"Signal kategorisan kao '{snr_results['overall_category']}' kvalitet",
                    "segments_analyzed": snr_results["num_segments"]
                }
                print(f"DEBUG: SNR analysis: {snr_results['mean_snr_db']:.1f} dB ({snr_results['overall_category']})")
        except Exception as e:
            print(f"DEBUG: SNR analysis failed: {str(e)}")
            complete_report["signal_quality"] = {"error": f"SNR analysis failed: {str(e)}"}

        # NOVO: MIT-BIH VALIDACIJA (ako je zatražena)
        if payload.get("include_mitbih_validation", False):
            try:
                from .analysis.mitbih_validator import validate_against_mitbih
                
                # MIT-BIH validacija sa TP/FP/FN
                mitbih_result = validate_against_mitbih(
                    signal_array, fs, 
                    record_name=payload.get("mitbih_record", "100"),
                    annotations=payload.get("mitbih_annotations", None),
                    tolerance_ms=payload.get("mitbih_tolerance_ms", 50)
                )
                
                if "error" not in mitbih_result:
                    complete_report["mitbih_validation"] = {
                        "precision": mitbih_result["precision"],
                        "recall": mitbih_result["recall"], 
                        "f1_score": mitbih_result["f1_score"],
                        "true_positives": mitbih_result["true_positives"],
                        "false_positives": mitbih_result["false_positives"],
                        "false_negatives": mitbih_result["false_negatives"],
                        "performance_grade": mitbih_result["performance_grade"],
                        "clinical_reliability": mitbih_result["clinical_reliability"],
                        "summary": mitbih_result["summary"]
                    }
                    print(f"DEBUG: MIT-BIH validation: F1={mitbih_result['f1_score']:.3f}")
                else:
                    complete_report["mitbih_validation"] = mitbih_result
                    
            except Exception as e:
                print(f"DEBUG: MIT-BIH validation failed: {str(e)}")
                complete_report["mitbih_validation"] = {"error": f"MIT-BIH validation failed: {str(e)}"}

        # NOVO: PDF GENERISANJE SA POBOLJŠANJIMA
        if payload.get("generate_pdf", False):
            print("DEBUG: Generating PDF report...")
            try:
                from .analysis.pdf_report_generator import EKGPDFReportGenerator
                
                pdf_generator = EKGPDFReportGenerator()
                signal_array = np.array(signal, dtype=float)
                
                patient_info = payload.get("patient_info", None)
                report_title = payload.get("report_title", "EKG Analiza Report")
                
                pdf_content = pdf_generator.generate_comprehensive_pdf_report(
                    signal_data=signal_array,
                    fs=fs,
                    analysis_results=complete_report,
                    report_title=report_title,
                    patient_info=patient_info,
                    include_images=include_images
                )
                
                # Cleanup PDF generator
                pdf_generator.cleanup()
                
                if isinstance(pdf_content, dict) and "error" in pdf_content:
                    print(f"DEBUG: PDF generation failed: {pdf_content['error']}")
                    complete_report["pdf_error"] = pdf_content["error"]
                else:
                    print("DEBUG: PDF generated successfully")
                    # Dodaj PDF kao base64 u JSON odgovor
                    import base64
                    complete_report["pdf_report"] = {
                        "pdf_base64": base64.b64encode(pdf_content).decode('utf-8'),
                        "filename": f"ekg_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                        "size_bytes": len(pdf_content),
                        "success": True
                    }
                        
            except Exception as e:
                print(f"DEBUG: PDF generation exception: {str(e)}")
                complete_report["pdf_error"] = f"PDF generation failed: {str(e)}"

        return safe_jsonify(complete_report)
        
    except Exception as e:
        return jsonify({"error": f"Complete report generation failed: {str(e)}"}), 500

def _categorize_frequency(freq_hz):
    """Kategorizuje dominantnu frekvenciju"""
    if 0.5 <= freq_hz <= 3:
        return "P-wave range (0.5-3 Hz)"
    elif 1 <= freq_hz <= 5:
        return "T-wave range (1-5 Hz)"
    elif 5 <= freq_hz <= 15:
        return "QRS complex range (5-15 Hz)"
    else:
        return "Outside typical ECG range"

def _assess_overall_quality(snr_analysis, z_analysis, hr_hrv_analysis):
    """Procenjuje ukupni kvalitet signala"""
    quality_score = 0
    
    # SNR contribution
    if snr_analysis and "mean_snr_db" in snr_analysis:
        if snr_analysis["mean_snr_db"] >= 20:
            quality_score += 3
        elif snr_analysis["mean_snr_db"] >= 15:
            quality_score += 2
        elif snr_analysis["mean_snr_db"] >= 10:
            quality_score += 1
    
    # Stability contribution
    if z_analysis and z_analysis.get("system_stable", False):
        quality_score += 2
    
    # HR detection contribution
    if hr_hrv_analysis and "heart_rate_bpm" in hr_hrv_analysis:
        hr = hr_hrv_analysis["heart_rate_bpm"]
        if 60 <= hr <= 100:  # Normal HR range
            quality_score += 2
        elif 50 <= hr <= 120:  # Acceptable range
            quality_score += 1
    
    if quality_score >= 6:
        return "Odličan"
    elif quality_score >= 4:
        return "Dobar"
    elif quality_score >= 2:
        return "Osrednji"
    else:
        return "Potrebno poboljšanje"

def _generate_recommendations(snr_analysis, fft_analysis, hr_hrv_analysis):
    """Generiše preporuke na osnovu analize"""
    recommendations = []
    
    if snr_analysis and "mean_snr_db" in snr_analysis:
        if snr_analysis["mean_snr_db"] < 15:
            recommendations.append("Potrebno poboljšanje kvaliteta signala - razmotriti dodatno filtriranje")
    
    if fft_analysis and "dominant_frequency_hz" in fft_analysis:
        freq = fft_analysis["dominant_frequency_hz"]
        if freq < 0.5 or freq > 15:
            recommendations.append("Dominantna frekvencija van fiziološkog opsega - proveriti signal")
    
    if hr_hrv_analysis and "heart_rate_bpm" in hr_hrv_analysis:
        hr = hr_hrv_analysis["heart_rate_bpm"]
        if hr < 50:
            recommendations.append("Bradikardija detektovana - potrebna medicinska evaluacija")
        elif hr > 120:
            recommendations.append("Tahikardija detektovana - potrebna medicinska evaluacija")
    
    if not recommendations:
        recommendations.append("Signal je u normalnim parametrima")
    
    return recommendations
