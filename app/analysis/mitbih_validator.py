"""
MIT-BIH Database Validation - R-peak Performance Analysis
Implementira precision/recall/F1 score za R-peak detekciju
"""

import numpy as np
import wfdb
from scipy.signal import find_peaks

class MITBIHValidator:
    """
    MIT-BIH annotation validator
    
    Reference:
    - Goldberger, A. L., et al. (2020). PhysioBank, PhysioToolkit, and PhysioNet: 
      Components of a new research resource for complex physiologic signals. 
      Circulation, 101(23), e215-e220. DOI: 10.1161/01.CIR.101.23.e215
    """
    
    def __init__(self, tolerance_ms=50):
        """
        Args:
            tolerance_ms: Tolerancija za poklapanje R-pikova u milisekundama
        """
        self.tolerance_ms = tolerance_ms
    
    def load_mitbih_annotations(self, record_path):
        """
        Učitava MIT-BIH anotacije (.atr fajl)
        
        Returns:
            dict: Anotacije sa R-peak lokacijama
        """
        try:
            # Učitaj anotacije
            annotation = wfdb.rdann(record_path, 'atr')
            
            # Filtriraj samo beat anotacije (R-pikovi)
            beat_annotations = ['N', 'L', 'R', 'B', 'A', 'a', 'J', 'S', 'V', 'r', 
                              'F', 'e', 'j', 'n', 'E', '/', 'f', 'Q', '?']
            
            r_peak_indices = []
            beat_types = []
            
            for i, ann_symbol in enumerate(annotation.symbol):
                if ann_symbol in beat_annotations:
                    r_peak_indices.append(annotation.sample[i])
                    beat_types.append(ann_symbol)
            
            return {
                "r_peak_indices": np.array(r_peak_indices),
                "beat_types": beat_types,
                "total_beats": len(r_peak_indices),
                "annotation_symbols": annotation.symbol,
                "sample_indices": annotation.sample
            }
            
        except Exception as e:
            return {"error": f"Failed to load MIT-BIH annotations: {str(e)}"}
    
    def compare_r_peaks(self, detected_peaks, ground_truth_peaks, fs=360):
        """
        Poredi detektovane R-pikove sa MIT-BIH ground truth
        
        Args:
            detected_peaks: numpy array detektovanih R-peak indeksa
            ground_truth_peaks: numpy array ground truth R-peak indeksa
            fs: sampling frequency (MIT-BIH default: 360 Hz)
        
        Returns:
            dict: Performance metrije (precision, recall, F1)
        """
        try:
            tolerance_samples = int(self.tolerance_ms * fs / 1000)
            
            # Convert to arrays
            detected = np.array(detected_peaks)
            ground_truth = np.array(ground_truth_peaks)
            
            if len(detected) == 0:
                return {
                    "precision": 0.0,
                    "recall": 0.0,
                    "f1_score": 0.0,
                    "true_positives": 0,
                    "false_positives": 0,
                    "false_negatives": len(ground_truth),
                    "detected_count": 0,
                    "ground_truth_count": len(ground_truth),
                    "tolerance_ms": self.tolerance_ms
                }
            
            # True Positives: detektovani pik blizu ground truth pika
            true_positives = 0
            matched_gt = set()
            matched_detected = set()
            
            for i, det_peak in enumerate(detected):
                # Pronađi najbliži ground truth pik
                distances = np.abs(ground_truth - det_peak)
                min_distance_idx = np.argmin(distances)
                min_distance = distances[min_distance_idx]
                
                if min_distance <= tolerance_samples and min_distance_idx not in matched_gt:
                    true_positives += 1
                    matched_gt.add(min_distance_idx)
                    matched_detected.add(i)
            
            # False Positives: detektovani pikovi koji nisu pokriveni
            false_positives = len(detected) - true_positives
            
            # False Negatives: ground truth pikovi koji nisu detektovani
            false_negatives = len(ground_truth) - true_positives
            
            # Metrije
            precision = true_positives / len(detected) if len(detected) > 0 else 0.0
            recall = true_positives / len(ground_truth) if len(ground_truth) > 0 else 0.0
            f1_score = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
            
            return {
                "precision": float(precision),
                "recall": float(recall),
                "f1_score": float(f1_score),
                "true_positives": int(true_positives),
                "false_positives": int(false_positives),
                "false_negatives": int(false_negatives),
                "detected_count": len(detected),
                "ground_truth_count": len(ground_truth),
                "tolerance_ms": self.tolerance_ms,
                "tolerance_samples": tolerance_samples,
                "performance_category": self._get_performance_category(f1_score)
            }
            
        except Exception as e:
            return {"error": f"R-peak comparison failed: {str(e)}"}
    
    def _get_performance_category(self, f1_score):
        """Kategorije performansi na osnovu F1 score"""
        if f1_score >= 0.95:
            return "Odličan"
        elif f1_score >= 0.90:
            return "Vrlo dobar"
        elif f1_score >= 0.80:
            return "Dobar"
        elif f1_score >= 0.70:
            return "Osrednji"
        else:
            return "Potrebno poboljšanje"
    
    def generate_validation_report(self, signal, detected_peaks, record_path, fs=360):
        """
        Generiše kompletni validacijski izveštaj
        
        Returns:
            dict: Potpuni performance report
        """
        try:
            # Load ground truth
            annotations = self.load_mitbih_annotations(record_path)
            if "error" in annotations:
                return annotations
            
            # Compare peaks
            performance = self.compare_r_peaks(
                detected_peaks, 
                annotations["r_peak_indices"], 
                fs
            )
            
            if "error" in performance:
                return performance
            
            # Calculate additional metrics
            signal_length_sec = len(signal) / fs
            detected_hr = len(detected_peaks) / signal_length_sec * 60 if signal_length_sec > 0 else 0
            ground_truth_hr = len(annotations["r_peak_indices"]) / signal_length_sec * 60 if signal_length_sec > 0 else 0
            
            # Heart rate variability (simple)
            if len(detected_peaks) > 1:
                rr_intervals = np.diff(detected_peaks) / fs * 1000  # ms
                hrv_rmssd = float(np.sqrt(np.mean(np.diff(rr_intervals)**2)))
                hrv_sdnn = float(np.std(rr_intervals))
            else:
                hrv_rmssd = 0.0
                hrv_sdnn = 0.0
            
            return {
                "signal_info": {
                    "duration_sec": float(signal_length_sec),
                    "sampling_frequency": fs,
                    "total_samples": len(signal)
                },
                "detection_performance": performance,
                "heart_rate_analysis": {
                    "detected_hr_bpm": float(detected_hr),
                    "ground_truth_hr_bpm": float(ground_truth_hr),
                    "hr_error_bpm": float(abs(detected_hr - ground_truth_hr)),
                    "hr_error_percent": float(abs(detected_hr - ground_truth_hr) / ground_truth_hr * 100) if ground_truth_hr > 0 else 0
                },
                "hrv_analysis": {
                    "rmssd_ms": hrv_rmssd,
                    "sdnn_ms": hrv_sdnn,
                    "rr_intervals_count": len(detected_peaks) - 1 if len(detected_peaks) > 1 else 0
                },
                "annotation_info": {
                    "total_annotations": annotations["total_beats"],
                    "beat_types": list(set(annotations["beat_types"])),
                    "annotation_file": f"{record_path}.atr"
                },
                "validation_summary": {
                    "overall_score": performance["f1_score"],
                    "performance_category": performance["performance_category"],
                    "recommendation": self._get_recommendation(performance["f1_score"])
                }
            }
            
        except Exception as e:
            return {"error": f"Validation report generation failed: {str(e)}"}
    
    def _get_recommendation(self, f1_score):
        """Preporuke na osnovu performansi"""
        if f1_score >= 0.95:
            return "Algoritam je spreman za kliničku evaluaciju"
        elif f1_score >= 0.90:
            return "Odličen algoritam, manje fine-tuning potreban"
        elif f1_score >= 0.80:
            return "Dobar algoritam, potrebno poboljšanje detekcije"
        elif f1_score >= 0.70:
            return "Potrebno značajno poboljšanje algoritma"
        else:
            return "Algoritam zahteva redesign"