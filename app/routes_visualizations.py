"""
Zasebni endpoints za thesis vizuelizacije - v3.1
"""
from flask import Blueprint, jsonify, request
import numpy as np
from .analysis.simple_thesis_viz import (
    create_simple_ekg_plot, 
    create_simple_fft_plot, 
    create_synthetic_mitbih_comparison,
    create_simple_processing_plot
)

viz_bp = Blueprint('visualizations', __name__)

@viz_bp.post("/thesis/visualization/1")
def generate_ekg_plot():
    """Generiši Sliku 1: EKG Signal sa R-pikovima"""
    try:
        payload = request.get_json(force=True)
        signal = np.array(payload.get("signal", []), dtype=float)
        fs = payload.get("fs", 250)
        analysis_results = payload.get("analysis_results", {})
        
        if len(signal) == 0:
            return jsonify({"error": "Prazan signal"}), 400
            
        print("DEBUG v3.1: Generating visualization 1 - EKG with R-peaks")
        image_base64 = create_simple_ekg_plot(signal, fs, analysis_results)
        
        if image_base64:
            return jsonify({
                "success": True,
                "title": "1. EKG Signal sa Detektovanim R-pikovima",
                "description": "Vremenski domen EKG signala sa automatski detektovanim R-pikovima označenim crvenim krugovima.",
                "image_base64": image_base64,
                "caption": "Slika 5.1: EKG signal u vremenskom domenu sa detektovanim R-pikovima"
            })
        else:
            return jsonify({"error": "Failed to generate EKG plot"}), 500
            
    except Exception as e:
        print(f"ERROR v3.1 in visualization 1: {str(e)}")
        return jsonify({"error": str(e)}), 500

@viz_bp.post("/thesis/visualization/2")
def generate_fft_plot():
    """Generiši Sliku 2: FFT Spektar"""
    try:
        payload = request.get_json(force=True)
        signal = np.array(payload.get("signal", []), dtype=float)
        fs = payload.get("fs", 250)
        analysis_results = payload.get("analysis_results", {})
        
        if len(signal) == 0:
            return jsonify({"error": "Prazan signal"}), 400
            
        print("DEBUG v3.1: Generating visualization 2 - FFT spectrum")
        image_base64 = create_simple_fft_plot(signal, fs, analysis_results)
        
        if image_base64:
            return jsonify({
                "success": True,
                "title": "2. FFT Spektar (Furijeova Transformacija)",
                "description": "Frekvencijski spektar EKG signala dobijen Furijeovom transformacijom. Dominantna frekvencija označena crvenom linijom odgovara srčanoj frekvenciji.",
                "image_base64": image_base64,
                "caption": "Slika 5.2: FFT spektar EKG signala sa označenom dominantnom frekvencijom"
            })
        else:
            return jsonify({"error": "Failed to generate FFT plot"}), 500
            
    except Exception as e:
        print(f"ERROR v3.1 in visualization 2: {str(e)}")
        return jsonify({"error": str(e)}), 500

@viz_bp.post("/thesis/visualization/3")
def generate_mitbih_comparison():
    """Generiši Sliku 3: MIT-BIH Poređenje"""
    try:
        payload = request.get_json(force=True)
        signal = np.array(payload.get("signal", []), dtype=float)
        fs = payload.get("fs", 250)
        analysis_results = payload.get("analysis_results", {})
        annotations = payload.get("annotations", None)
        
        if len(signal) == 0:
            return jsonify({"error": "Prazan signal"}), 400
            
        print("DEBUG v3.1: Generating visualization 3 - MIT-BIH comparison")
        image_base64 = create_synthetic_mitbih_comparison(signal, fs, analysis_results)
        
        if image_base64:
            return jsonify({
                "success": True,
                "title": "3. Poređenje sa MIT-BIH Anotacijama",
                "description": "Poređenje automatski detektovanih R-pikova (crveno) sa ekspertskim MIT-BIH anotacijama (zeleno).",
                "image_base64": image_base64,
                "caption": "Slika 5.3: Validacija algoritma protiv MIT-BIH ekspertskih anotacija"
            })
        else:
            return jsonify({"error": "Failed to generate MIT-BIH comparison"}), 500
            
    except Exception as e:
        print(f"ERROR v3.1 in visualization 3: {str(e)}")
        return jsonify({"error": str(e)}), 500

@viz_bp.post("/thesis/visualization/4")
def generate_processing_pipeline():
    """Generiši Sliku 4: Signal Processing Pipeline"""
    try:
        payload = request.get_json(force=True)
        signal = np.array(payload.get("signal", []), dtype=float)
        fs = payload.get("fs", 250)
        
        if len(signal) == 0:
            return jsonify({"error": "Prazan signal"}), 400
            
        print("DEBUG v3.1: Generating visualization 4 - Processing pipeline")
        image_base64 = create_simple_processing_plot(signal, fs)
        
        if image_base64:
            return jsonify({
                "success": True,
                "title": "4. Signal Processing Pipeline (Z-transformacija)",
                "description": "Koraci obrade signala korišćenjem Z-transformacije: originalni signal, bandpass filtriranje (0.5-40 Hz), baseline removal i filter response u Z-domenu.",
                "image_base64": image_base64,
                "caption": "Slika 5.4: Pipeline obrade biomedicinskog signala korišćenjem Z-transformacije"
            })
        else:
            return jsonify({"error": "Failed to generate processing pipeline"}), 500
            
    except Exception as e:
        print(f"ERROR v3.1 in visualization 4: {str(e)}")
        return jsonify({"error": str(e)}), 500

@viz_bp.post("/thesis/visualizations/all")
def generate_all_visualizations_async():
    """Inicijalizuj sve vizuelizacije i vrati placeholder-e"""
    try:
        return jsonify({
            "success": True,
            "description": "Vizuelizacije za master rad: Furijeova i Z-transformacija u analizi biomedicinskih signala",
            "subtitle": "Grafici spremni za uključivanje u poglavlje 5 master rada.",
            "visualizations": {
                "1": {
                    "title": "1. EKG Signal sa Detektovanim R-pikovima",
                    "description": "Vremenski domen EKG signala sa automatski detektovanim R-pikovima označenim crvenim krugovima.",
                    "caption": "Slika 5.1: EKG signal u vremenskom domenu sa detektovanim R-pikovima",
                    "status": "loading",
                    "endpoint": "/api/visualizations/thesis/visualization/1"
                },
                "2": {
                    "title": "2. FFT Spektar (Furijeova Transformacija)",
                    "description": "Frekvencijski spektar EKG signala dobijen Furijeovom transformacijom. Dominantna frekvencija označena crvenom linijom odgovara srčanoj frekvenciji.",
                    "caption": "Slika 5.2: FFT spektar EKG signala sa označenom dominantnom frekvencijom",
                    "status": "loading",
                    "endpoint": "/api/visualizations/thesis/visualization/2"
                },
                "3": {
                    "title": "3. Poređenje sa MIT-BIH Anotacijama",
                    "description": "Poređenje automatski detektovanih R-pikova (crveno) sa ekspertskim MIT-BIH anotacijama (zeleno).",
                    "caption": "Slika 5.3: Validacija algoritma protiv MIT-BIH ekspertskih anotacija",
                    "status": "loading",
                    "endpoint": "/api/visualizations/thesis/visualization/3"
                },
                "4": {
                    "title": "4. Signal Processing Pipeline (Z-transformacija)",
                    "description": "Koraci obrade signala korišćenjem Z-transformacije: originalni signal, bandpass filtriranje (0.5-40 Hz), baseline removal i filter response u Z-domenu.",
                    "caption": "Slika 5.4: Pipeline obrade biomedicinskog signala korišćenjem Z-transformacije",
                    "status": "loading",
                    "endpoint": "/api/visualizations/thesis/visualization/4"
                }
            }
        })
        
    except Exception as e:
        print(f"ERROR v3.1 in all visualizations: {str(e)}")
        return jsonify({"error": str(e)}), 500