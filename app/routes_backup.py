from flask import Blueprint, jsonify, request, render_template
from .analysis.fft import analyze_fft
from .analysis.ztransform import z_transform_analysis, digital_filter_design
from .analysis.image_processing import process_ekg_image, preprocess_for_analysis
from .analysis.arrhythmia_detection import detect_arrhythmias
from .analysis.advanced_ekg_analysis import comprehensive_ekg_analysis
from .analysis.educational_visualization import create_step_by_step_analysis

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
            image_result = process_ekg_image(payload["image"])
            if "error" in image_result:
                return jsonify(image_result), 400
            
            signal = image_result["signal"]
            fs = payload.get("fs", 250)
            
            # Predobrada signala
            signal, fs = preprocess_for_analysis(signal, fs)
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
        
        # 4. Napredna analiza (naučni algoritmi)
        results["advanced_analysis"] = comprehensive_ekg_analysis(signal, fs)
        
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
            image_result = process_ekg_image(payload["image"])
            if "error" in image_result:
                return jsonify(image_result), 400
            
            signal = image_result["signal"]
            fs = payload.get("fs", 250)
            
            # Predobrada signala
            signal, fs = preprocess_for_analysis(signal, fs)
        else:
            return jsonify({"error": "Potreban je 'signal' ili 'image' parametar"}), 400
        
        # Kreiranje step-by-step edukativne analize
        educational_result = create_step_by_step_analysis(signal, fs)
        
        return jsonify(educational_result)
        
    except Exception as e:
        return jsonify({"error": f"Greška u edukativnoj analizi: {str(e)}"}), 500

@api.get("/info")
def api_info():
    """Informacije o dostupnim endpoint-ima"""
    return jsonify({
        "endpoints": {
            "/health": "GET - Provera zdravlja API-ja",
            "/analyze/fft": "POST - FFT analiza signala",
            "/analyze/image": "POST - Konverzija EKG slike u signal",
            "/analyze/complete": "POST - Kompletna analiza (slika ili signal)",
            "/analyze/educational": "POST - Detaljana edukativna analiza sa vizualizacijama",
            "/analyze/ztransform": "POST - Z-transformacija signala",
            "/analyze/arrhythmia": "POST - Detekcija aritmija",
            "/filter/design": "POST - Dizajn digitalnog filtera",
            "/info": "GET - Ove informacije"
        },
        "version": "2.0",
        "description": "EKG analiza API - napredni algoritmi iz naučnih radova",
        "scientific_methods": [
            "Spatial Filling Index (Faust et al., 2004)",
            "Time-Frequency Analysis (STFT)",
            "Wavelet Decomposition (Yıldırım, 2018)",
            "Advanced Digital Filtering (Sörnmo & Laguna, 2005)",
            "Educational Visualization with Formulas"
        ]
    })
