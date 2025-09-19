"""
PDF-specific endpoints for EKG analysis
"""

from flask import Blueprint, jsonify, request, send_file, Response
import numpy as np
import io
import base64
from datetime import datetime

# PDF blueprint
pdf_bp = Blueprint('pdf', __name__)

@pdf_bp.post("/generate/pdf-report")
def generate_pdf_report_only():
    """
    Generiše SAMO PDF izveštaj (bez JSON-a) - optimizovano za download
    
    Input:
    - signal: EKG signal kao lista brojeva
    - fs: frekvencija uzorkovanja (default: 250)
    - report_title: naslov izveštaja (default: "EKG Analiza Report")
    - patient_info: {name, age, gender, patient_id} (optional)
    - include_images: boolean da li uključiti dijagrame (default: true)
    
    Returns:
    - PDF fajl za direktan download
    """
    try:
        payload = request.get_json(force=True)
        signal = payload.get("signal", [])
        fs = payload.get("fs", 250)
        include_images = payload.get("include_images", True)
        report_title = payload.get("report_title", "EKG Analiza Report")
        patient_info = payload.get("patient_info", None)
        
        if not signal:
            return jsonify({"error": "Nedostaje signal"}), 400
        
        if len(signal) < 100:
            return jsonify({"error": "Signal je prekratak (minimum 100 uzoraka)"}), 400
        
        print(f"DEBUG: Generating PDF report for signal length: {len(signal)}")
        
        # Prvo izvršiti sve analize
        from .analysis.fft import analyze_fft
        from .analysis.ztransform import z_transform_analysis
        from .analysis.arrhythmia_detection import detect_arrhythmias
        
        signal_array = np.array(signal, dtype=float)
        
        # Analize potrebne za PDF
        analysis_results = {
            "fft_analysis": analyze_fft(signal, fs),
            "z_transform": z_transform_analysis(signal, fs),
            "arrhythmia_detection": detect_arrhythmias(signal, fs),
            "signal_info": {
                "length": len(signal),
                "duration_seconds": len(signal) / fs,
                "sampling_frequency": fs,
                "source": "pdf_report_request"
            }
        }
        
        print("DEBUG: All analyses completed, generating PDF...")
        
        # Generiši PDF
        from .analysis.pdf_report_generator import EKGPDFReportGenerator
        
        pdf_generator = EKGPDFReportGenerator()
        
        pdf_content = pdf_generator.generate_comprehensive_pdf_report(
            signal_data=signal_array,
            fs=fs,
            analysis_results=analysis_results,
            report_title=report_title,
            patient_info=patient_info,
            include_images=include_images
        )
        
        # Cleanup
        pdf_generator.cleanup()
        
        if isinstance(pdf_content, dict) and "error" in pdf_content:
            return jsonify(pdf_content), 500
        
        print("DEBUG: PDF generated successfully, sending as download")
        
        # Kreiraj filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if patient_info and patient_info.get('name'):
            patient_name = patient_info['name'].replace(' ', '_')
            filename = f"EKG_Report_{patient_name}_{timestamp}.pdf"
        else:
            filename = f"EKG_Report_{timestamp}.pdf"
        
        # Vrati PDF kao download
        return Response(
            pdf_content,
            mimetype='application/pdf',
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"',
                'Content-Type': 'application/pdf',
                'Content-Length': str(len(pdf_content))
            }
        )
        
    except Exception as e:
        print(f"DEBUG: PDF generation error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"PDF generation failed: {str(e)}"}), 500

@pdf_bp.post("/generate/pdf-from-analysis")
def generate_pdf_from_existing_analysis():
    """
    Generiše PDF iz već izvršenih analiza
    
    Input:
    - signal: EKG signal kao lista brojeva
    - fs: frekvencija uzorkovanja
    - analysis_results: kompletan rezultat analize (iz /analyze/complete)
    - report_title, patient_info, include_images
    
    Returns:
    - PDF fajl za direktan download
    """
    try:
        payload = request.get_json(force=True)
        signal = payload.get("signal", [])
        fs = payload.get("fs", 250)
        analysis_results = payload.get("analysis_results", {})
        include_images = payload.get("include_images", True)
        report_title = payload.get("report_title", "EKG Analiza Report")
        patient_info = payload.get("patient_info", None)
        
        if not signal:
            return jsonify({"error": "Nedostaje signal"}), 400
        
        if not analysis_results:
            return jsonify({"error": "Nedostaju rezultati analize"}), 400
        
        print(f"DEBUG: Generating PDF from existing analysis results")
        
        # Generiši PDF
        from .analysis.pdf_report_generator import EKGPDFReportGenerator
        
        pdf_generator = EKGPDFReportGenerator()
        signal_array = np.array(signal, dtype=float)
        
        pdf_content = pdf_generator.generate_comprehensive_pdf_report(
            signal_data=signal_array,
            fs=fs,
            analysis_results=analysis_results,
            report_title=report_title,
            patient_info=patient_info,
            include_images=include_images
        )
        
        # Cleanup
        pdf_generator.cleanup()
        
        if isinstance(pdf_content, dict) and "error" in pdf_content:
            return jsonify(pdf_content), 500
        
        # Kreiraj filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"EKG_Report_from_Analysis_{timestamp}.pdf"
        
        # Vrati PDF kao download
        return Response(
            pdf_content,
            mimetype='application/pdf',
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"',
                'Content-Type': 'application/pdf'
            }
        )
        
    except Exception as e:
        print(f"DEBUG: PDF from analysis error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"PDF generation failed: {str(e)}"}), 500