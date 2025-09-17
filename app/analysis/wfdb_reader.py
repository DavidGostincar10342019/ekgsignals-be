"""
WFDB Format Reader - za čitanje MIT-BIH i slične baze podataka
Podržava .dat, .hea, .atr formate
NOVO: Implementirana podrška za .atr annotation fajlove
"""

import struct
import numpy as np
import re
from typing import Tuple, Dict, Optional, List
import io

def read_header_file(header_content: str) -> Dict:
    """
    Čita WFDB header (.hea) fajl i izvlači metapodatke
    
    Args:
        header_content: Sadržaj .hea fajla kao string
        
    Returns:
        Dict sa metapodacima (fs, broj kanala, gain, itd.)
    """
    lines = header_content.strip().split('\n')
    
    if not lines:
        raise ValueError("Prazan header fajl")
    
    # Prva linija: record_name n_signals fs n_samples
    first_line = lines[0].split()
    
    if len(first_line) < 3:
        raise ValueError("Neispravna prva linija header fajla")
    
    metadata = {
        'record_name': first_line[0],
        'n_signals': int(first_line[1]) if len(first_line) > 1 else 1,
        'fs': float(first_line[2]) if len(first_line) > 2 else 250,
        'n_samples': int(first_line[3]) if len(first_line) > 3 else 0,
        'signals': []
    }
    
    # Čitanje linija za svaki signal
    for i in range(1, min(len(lines), metadata['n_signals'] + 1)):
        signal_line = lines[i].strip()
        if signal_line:
            # Parsiranje: filename format(x gain(baseline)/units
            parts = signal_line.split()
            if len(parts) >= 3:
                signal_info = {
                    'filename': parts[0],
                    'format': parts[1],
                    'gain': 200.0,  # default
                    'baseline': 0,
                    'units': 'mV',
                    'description': ''
                }
                
                # Parsiranje gain(baseline)/units
                if len(parts) > 2:
                    gain_part = parts[2]
                    try:
                        if '(' in gain_part:
                            gain_str = gain_part.split('(')[0]
                            signal_info['gain'] = float(gain_str) if gain_str else 200.0
                        else:
                            signal_info['gain'] = float(gain_part)
                    except ValueError:
                        signal_info['gain'] = 200.0
                
                # Description (ako postoji)
                if len(parts) > 3:
                    signal_info['description'] = ' '.join(parts[3:])
                
                metadata['signals'].append(signal_info)
    
    return metadata

def read_dat_file_212(dat_content: bytes, n_samples: int, n_signals: int = 2) -> np.ndarray:
    """
    Čita WFDB .dat fajl u format 212 (uobičajeno za MIT-BIH)
    
    Args:
        dat_content: Binarni sadržaj .dat fajla
        n_samples: Broj uzoraka po signalu
        n_signals: Broj signala (obično 2 za MIT-BIH)
        
    Returns:
        numpy array sa signalima [samples, channels]
    """
    if n_signals != 2:
        # Za sada podržavamo samo 2-kanalni format 212
        return read_dat_file_16(dat_content, n_samples, n_signals)
    
    # Format 212: 3 bajta za 2 uzorka od 12 bita
    bytes_per_group = 3
    samples_per_group = 2
    
    expected_bytes = (n_samples * bytes_per_group) // samples_per_group
    if n_samples % samples_per_group:
        expected_bytes += bytes_per_group
    
    if len(dat_content) < expected_bytes:
        print(f"Warning: Expected {expected_bytes} bytes, got {len(dat_content)}")
        # Nastavi sa onim što imamo
        n_samples = (len(dat_content) * samples_per_group) // bytes_per_group
    
    signals = np.zeros((n_samples, n_signals), dtype=np.int16)
    
    try:
        for i in range(0, n_samples - 1, 2):
            byte_idx = (i * 3) // 2
            
            if byte_idx + 2 >= len(dat_content):
                break
                
            # Čitanje 3 bajta
            b0, b1, b2 = dat_content[byte_idx:byte_idx + 3]
            
            # Dekodiranje 2 uzorka od 12 bita
            sample1 = (b1 & 0x0F) << 8 | b0
            sample2 = b2 << 4 | (b1 & 0xF0) >> 4
            
            # Konverzija u signed 12-bit
            if sample1 & 0x800:
                sample1 -= 0x1000
            if sample2 & 0x800:
                sample2 -= 0x1000
            
            if i < n_samples:
                signals[i, 0] = sample1
            if i + 1 < n_samples:
                signals[i + 1, 0] = sample2
            
            # Za MIT-BIH, drugi kanal je obično isti signal
            if i < n_samples:
                signals[i, 1] = sample1
            if i + 1 < n_samples:
                signals[i + 1, 1] = sample2
                
    except Exception as e:
        print(f"Warning: Error reading format 212: {e}")
        # Fallback na format 16
        return read_dat_file_16(dat_content, n_samples, n_signals)
    
    return signals

def read_dat_file_16(dat_content: bytes, n_samples: int, n_signals: int) -> np.ndarray:
    """
    Čita WFDB .dat fajl u format 16 (16-bit samples)
    
    Args:
        dat_content: Binarni sadržaj .dat fajla
        n_samples: Broj uzoraka po signalu
        n_signals: Broj signala
        
    Returns:
        numpy array sa signalima [samples, channels]
    """
    bytes_per_sample = 2  # 16-bit
    expected_bytes = n_samples * n_signals * bytes_per_sample
    
    if len(dat_content) < expected_bytes:
        print(f"Warning: Expected {expected_bytes} bytes, got {len(dat_content)}")
        # Smanji broj uzoraka na osnovu dostupnih podataka
        n_samples = len(dat_content) // (n_signals * bytes_per_sample)
    
    # Čitanje kao 16-bit little-endian integers
    data = np.frombuffer(dat_content[:n_samples * n_signals * bytes_per_sample], 
                        dtype=np.int16)
    
    # Reshaping u [samples, channels]
    if n_signals > 1:
        signals = data.reshape(n_samples, n_signals)
    else:
        signals = data.reshape(-1, 1)
    
    return signals

def convert_to_physical_units(signals: np.ndarray, metadata: Dict) -> np.ndarray:
    """
    Konvertuje digitalne vrednosti u fizičke jedinice (mV)
    
    Args:
        signals: Digitalni signali
        metadata: Metapodaci sa gain informacijama
        
    Returns:
        Signali u fizičkim jedinicama
    """
    physical_signals = signals.astype(np.float64)
    
    for i, signal_info in enumerate(metadata['signals']):
        if i < signals.shape[1]:
            gain = signal_info.get('gain', 200.0)
            baseline = signal_info.get('baseline', 0)
            
            if gain != 0:
                # (digital_value - baseline) / gain = physical_value
                physical_signals[:, i] = (physical_signals[:, i] - baseline) / gain
    
    return physical_signals

def parse_wfdb_files(dat_content: bytes, hea_content: str) -> Tuple[np.ndarray, float, Dict]:
    """
    Glavna funkcija za parsiranje WFDB fajlova
    
    Args:
        dat_content: Binarni sadržaj .dat fajla
        hea_content: Tekstualni sadržaj .hea fajla
        
    Returns:
        Tuple (signals, fs, metadata)
    """
    # Čitanje metapodataka
    metadata = read_header_file(hea_content)
    
    print(f"DEBUG: WFDB metadata: {metadata}")
    
    n_samples = metadata.get('n_samples', 0)
    n_signals = metadata.get('n_signals', 2)
    fs = metadata.get('fs', 250)
    
    # Ako nema eksplicitnog broja uzoraka, proceni na osnovu veličine fajla
    if n_samples == 0:
        # Pretpostavka: format 212 (3 bajta za 2 uzorka)
        n_samples = (len(dat_content) * 2) // 3
        print(f"DEBUG: Estimated n_samples: {n_samples}")
    
    # Čitanje signala
    signals = read_dat_file_212(dat_content, n_samples, n_signals)
    
    # Konverzija u fizičke jedinice
    physical_signals = convert_to_physical_units(signals, metadata)
    
    print(f"DEBUG: Signal shape: {physical_signals.shape}, fs: {fs}")
    
    return physical_signals, fs, metadata

def validate_wfdb_files(files_dict: Dict[str, bytes]) -> bool:
    """
    Validira da li su potrebni WFDB fajlovi prisutni
    
    Args:
        files_dict: Dict sa fajlovima {filename: content}
        
    Returns:
        True ako su validni
    """
    has_dat = any(name.endswith('.dat') for name in files_dict.keys())
    has_hea = any(name.endswith('.hea') for name in files_dict.keys())
    
    return has_dat and has_hea

def read_atr_file(atr_content: bytes, fs: float = 250) -> Dict:
    """
    Čita WFDB .atr annotation fajl
    
    Args:
        atr_content: Binarni sadržaj .atr fajla
        fs: Sampling frequency (Hz)
        
    Returns:
        Dict sa annotation podacima
    """
    annotations = {
        'annotations': [],
        'r_peaks': [],
        'arrhythmias': [],
        'total_annotations': 0,
        'annotation_types': {}
    }
    
    try:
        # MIT-BIH .atr format: svaki annotation je 2 bajta
        # Format: [ANNTYP][TIME_BYTES]
        
        atr_data = np.frombuffer(atr_content, dtype=np.uint8)
        
        print(f"DEBUG: Reading .atr file, {len(atr_data)} bytes")
        
        i = 0
        current_time = 0
        
        while i < len(atr_data) - 1:
            # Čitaj annotation type i time
            anntyp = int(atr_data[i])  # Konvertuj u Python int
            time_byte = int(atr_data[i + 1])  # Konvertuj u Python int
            
            # Dekodiranje vremena
            if time_byte == 0:
                # Extended time format - sledeća 2 bajta su vreme
                if i + 3 < len(atr_data):
                    time_increment = (int(atr_data[i + 2]) << 8) | int(atr_data[i + 3])
                    i += 4
                else:
                    break
            else:
                time_increment = time_byte
                i += 2
            
            current_time += time_increment
            
            # Konvertuj u sekunde
            time_seconds = current_time / fs
            
            # Mapiraj annotation tipove
            annotation_info = decode_annotation_type(anntyp)
            
            annotation = {
                'time_samples': int(current_time),  # Konvertuj u Python int
                'time_seconds': float(time_seconds),  # Konvertuj u Python float
                'type_code': int(anntyp),  # Konvertuj u Python int
                'type_name': annotation_info['name'],
                'category': annotation_info['category'],
                'description': annotation_info['description']
            }
            
            annotations['annotations'].append(annotation)
            
            # Grupiši po tipovima
            if annotation_info['category'] == 'beat':
                annotations['r_peaks'].append({
                    'time_samples': int(current_time),  # Konvertuj u Python int
                    'time_seconds': float(time_seconds),  # Konvertuj u Python float
                    'beat_type': annotation_info['name']
                })
            elif annotation_info['category'] == 'arrhythmia':
                annotations['arrhythmias'].append({
                    'time_samples': int(current_time),  # Konvertuj u Python int
                    'time_seconds': float(time_seconds),  # Konvertuj u Python float
                    'arrhythmia_type': annotation_info['name'],
                    'description': annotation_info['description']
                })
            
            # Statistike
            type_name = annotation_info['name']
            if type_name not in annotations['annotation_types']:
                annotations['annotation_types'][type_name] = 0
            annotations['annotation_types'][type_name] += 1
        
        annotations['total_annotations'] = len(annotations['annotations'])
        
        print(f"DEBUG: Parsed {annotations['total_annotations']} annotations")
        print(f"DEBUG: Found {len(annotations['r_peaks'])} R-peaks")
        print(f"DEBUG: Found {len(annotations['arrhythmias'])} arrhythmia markers")
        
        return annotations
        
    except Exception as e:
        print(f"ERROR: Failed to read .atr file: {str(e)}")
        return {
            'annotations': [],
            'r_peaks': [],
            'arrhythmias': [],
            'total_annotations': 0,
            'annotation_types': {},
            'error': str(e)
        }

def decode_annotation_type(anntyp: int) -> Dict:
    """
    Dekodira MIT-BIH annotation tipove
    """
    # MIT-BIH annotation codes
    annotation_map = {
        1: {'name': 'N', 'category': 'beat', 'description': 'Normal beat'},
        2: {'name': 'L', 'category': 'beat', 'description': 'Left bundle branch block beat'},
        3: {'name': 'R', 'category': 'beat', 'description': 'Right bundle branch block beat'},
        4: {'name': 'A', 'category': 'beat', 'description': 'Atrial premature beat'},
        5: {'name': 'a', 'category': 'beat', 'description': 'Aberrated atrial premature beat'},
        6: {'name': 'J', 'category': 'beat', 'description': 'Nodal (junctional) premature beat'},
        7: {'name': 'S', 'category': 'beat', 'description': 'Supraventricular premature beat'},
        8: {'name': 'V', 'category': 'beat', 'description': 'Premature ventricular contraction'},
        9: {'name': 'F', 'category': 'beat', 'description': 'Fusion of ventricular and normal beat'},
        10: {'name': '[', 'category': 'arrhythmia', 'description': 'Start of ventricular flutter/fibrillation'},
        11: {'name': '!', 'category': 'arrhythmia', 'description': 'Ventricular flutter wave'},
        12: {'name': ']', 'category': 'arrhythmia', 'description': 'End of ventricular flutter/fibrillation'},
        13: {'name': 'e', 'category': 'beat', 'description': 'Atrial escape beat'},
        14: {'name': 'j', 'category': 'beat', 'description': 'Nodal (junctional) escape beat'},
        16: {'name': 'E', 'category': 'beat', 'description': 'Ventricular escape beat'},
        18: {'name': '/', 'category': 'beat', 'description': 'Paced beat'},
        19: {'name': 'f', 'category': 'beat', 'description': 'Fusion of paced and normal beat'},
        22: {'name': 'Q', 'category': 'beat', 'description': 'Unclassifiable beat'},
        23: {'name': '?', 'category': 'beat', 'description': 'Beat not classified during learning'},
        25: {'name': '(', 'category': 'arrhythmia', 'description': 'Rhythm change'},
        26: {'name': ')', 'category': 'arrhythmia', 'description': 'Rhythm change'},
        27: {'name': 'p', 'category': 'wave', 'description': 'Peak of P-wave'},
        28: {'name': 't', 'category': 'wave', 'description': 'Peak of T-wave'},
        29: {'name': 'u', 'category': 'wave', 'description': 'Peak of U-wave'},
        30: {'name': '`', 'category': 'measurement', 'description': 'Non-conducted P-wave'},
        31: {'name': "'", 'category': 'measurement', 'description': 'Isolated QRS-like artifact'},
        32: {'name': '^', 'category': 'measurement', 'description': 'Non-conducted P-wave'},
        33: {'name': '|', 'category': 'measurement', 'description': 'Isolated QRS-like artifact'},
        34: {'name': '~', 'category': 'noise', 'description': 'Change in signal quality'},
        35: {'name': '+', 'category': 'measurement', 'description': 'Rhythm change'},
        36: {'name': 's', 'category': 'arrhythmia', 'description': 'ST change'},
        37: {'name': 'T', 'category': 'arrhythmia', 'description': 'T-wave change'},
        38: {'name': '*', 'category': 'measurement', 'description': 'Systole'},
        39: {'name': 'D', 'category': 'measurement', 'description': 'Diastole'},
        40: {'name': '"', 'category': 'measurement', 'description': 'Comment annotation'},
        41: {'name': '=', 'category': 'measurement', 'description': 'Measurement annotation'},
        42: {'name': 'U', 'category': 'beat', 'description': 'Unclassifiable beat'},
    }
    
    return annotation_map.get(anntyp, {
        'name': f'Unknown_{anntyp}',
        'category': 'unknown',
        'description': f'Unknown annotation type {anntyp}'
    })

def extract_signal_for_analysis(signals: np.ndarray, channel: int = 0) -> List[float]:
    """
    Izvlači jedan kanal signala za analizu
    
    Args:
        signals: Multi-channel signali
        channel: Koji kanal da izvuče (0 = prvi)
        
    Returns:
        Lista sa vrednostima signala
    """
    if signals.shape[1] <= channel:
        channel = 0  # Fallback na prvi kanal
    
    signal_channel = signals[:, channel]
    
    # Konvertuj u listu float vrednosti
    return signal_channel.astype(float).tolist()

def parse_wfdb_files_with_annotations(dat_content: bytes, hea_content: str, atr_content: bytes = None) -> Tuple[np.ndarray, float, Dict, Dict]:
    """
    NOVA FUNKCIJA: Parsira WFDB fajlove uključujući .atr annotations
    
    Args:
        dat_content: Binarni sadržaj .dat fajla
        hea_content: Tekstualni sadržaj .hea fajla
        atr_content: Binarni sadržaj .atr fajla (opciono)
        
    Returns:
        (signals, fs, metadata, annotations)
    """
    # Parsiraj osnovne fajlove
    signals, fs, metadata = parse_wfdb_files(dat_content, hea_content)
    
    # Parsiraj annotations ako su dostupni
    annotations = {}
    if atr_content:
        annotations = read_atr_file(atr_content, fs)
        print(f"DEBUG: Integrated {annotations['total_annotations']} annotations with signal data")
    else:
        print(f"DEBUG: No .atr file provided, skipping annotations")
    
    return signals, fs, metadata, annotations