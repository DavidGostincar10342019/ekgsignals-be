# 🏥 EKG Analiza API - Detaljana Dokumentacija

## 📋 Pregled

**EKG Analiza API v3.2** je napredni REST API za analizu elektrokardiograma (EKG) signala. Podržava analizu fotografija EKG zapisa, sirovih digitalnih podataka i MIT-BIH WFDB formata.

### 🎯 Osnovne informacije
- **Base URL**: `http://localhost:8000` (ili vaš deployment URL)
- **Version**: 3.2_auto_advanced_analysis
- **Content-Type**: `application/json`
- **Response Format**: JSON

### 🔬 Naučne metode
- **Spatial Filling Index** (Faust et al., 2004)
- **Time-Frequency Analysis** (STFT)
- **Wavelet Decomposition** (Yıldırım, 2018)
- **Z-Transform Pole-Zero Analysis**
- **Advanced Digital Filtering** (Sörnmo & Laguna, 2005)
- **MIT-BIH Arrhythmia Detection**

---

## 🌐 Osnovni Endpoints

### 1. Health Check
**GET** `/health`

Provera dostupnosti API-ja.

**Response:**
```json
{
  "status": "ok"
}
```

### 2. API Informacije
**GET** `/info`

Vraća kompletnu listu dostupnih endpoint-ova i metoda.

**Response:**
```json
{
  "endpoints": { ... },
  "version": "3.2_auto_advanced_analysis",
  "description": "EKG analiza API - analiza slika i sirovih signala",
  "scientific_methods": [ ... ],
  "input_methods": [ ... ]
}
```

---

## 📊 Analiza Endpoints

### 3. FFT Analiza
**POST** `/analyze/fft`

Brza Fourier transformacija digitalnog signala.

**Request Body:**
```json
{
  "signal": [0.1, 0.2, 0.15, ...],
  "fs": 250
}
```

**Parameters:**
- `signal` (array): Digitalni EKG signal
- `fs` (number): Frekvencija uzorkovanja u Hz (default: 250)

**Response:**
```json
{
  "frequencies": [0, 0.5, 1.0, ...],
  "magnitudes": [0.8, 0.4, 0.2, ...],
  "peak_frequency": 1.2,
  "peak_magnitude": 0.85,
  "dominant_frequencies": [1.2, 2.4, 3.6]
}
```

### 4. Analiza EKG Slike
**POST** `/analyze/image`

Konvertuje EKG fotografiju u digitalni signal i vrši osnovnu analizu.

**Request Body:**
```json
{
  "image": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAA...",
  "fs": 250
}
```

**Parameters:**
- `image` (string): Base64 encoded slika (JPG/PNG/WEBP)
- `fs` (number): Željena frekvencija uzorkovanja (default: 250)

**Response:**
```json
{
  "signal": [0.1, 0.2, 0.15, ...],
  "signal_info": {
    "length": 1250,
    "duration_seconds": 5.0,
    "sampling_frequency": 250,
    "quality_score": 0.85
  },
  "basic_analysis": {
    "heart_rate": {
      "average_bpm": 72,
      "min_bpm": 68,
      "max_bpm": 76
    },
    "rhythm_analysis": {
      "rhythm_type": "Regular",
      "irregularity_score": 0.1
    }
  },
  "validation": {
    "is_valid_ekg": true,
    "confidence": 0.92,
    "issues": []
  }
}
```

### 5. Kompletna Analiza
**POST** `/analyze/complete`

Sveobuhvatna analiza EKG signala ili slike sa svim dostupnim metodama.

**Request Body:**
```json
{
  "image": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAA...",
  "signal": [0.1, 0.2, 0.15, ...],
  "fs": 250,
  "analysis_type": "comprehensive"
}
```

**Parameters:**
- `image` (string, optional): Base64 encoded EKG slika
- `signal` (array, optional): Direktni digitalni signal
- `fs` (number): Frekvencija uzorkovanja (default: 250)
- `analysis_type` (string): "basic" ili "comprehensive"

**Response:**
```json
{
  "signal_info": {
    "length": 1250,
    "duration_seconds": 5.0,
    "sampling_frequency": 250,
    "source": "image_analysis"
  },
  "heart_rate_analysis": {
    "average_bpm": 72,
    "min_bpm": 68,
    "max_bpm": 76,
    "hrv_ms": 45.2,
    "r_peaks": [120, 330, 540, 750]
  },
  "arrhythmia_detection": {
    "detected": [
      {
        "type": "Bradycardia",
        "confidence": 0.85,
        "location": [0, 500]
      }
    ],
    "summary": "1 arrhythmia detected"
  },
  "signal_quality": {
    "snr_db": 25.4,
    "quality_score": 0.85,
    "assessment": "Good"
  },
  "fft_analysis": {
    "dominant_frequency": 1.2,
    "peak_magnitude": 0.85,
    "frequencies": [...],
    "magnitudes": [...]
  },
  "z_transform": {
    "stability": {
      "stable": true,
      "max_pole_magnitude": 0.85
    },
    "poles": [...],
    "zeros": [...],
    "pole_zero_plot": "base64_image_string"
  }
}
```

### 6. WFDB Analiza (MIT-BIH Format)
**POST** `/analyze/wfdb`

Analiza MIT-BIH WFDB formata (.dat + .hea + .atr fajlovi) sa ekspertskim anotacijama.

**Request Body:**
```json
{
  "files": {
    "hea_content": "100 2 360 650000\n100.dat 212 200 11 0 0 0 0 MLII\n...",
    "dat_content": "base64_encoded_binary_data",
    "atr_content": "base64_encoded_annotation_data"
  },
  "record_name": "100",
  "analysis_options": {
    "include_annotations": true,
    "validate_mit_bih": true
  }
}
```

**Response:**
```json
{
  "wfdb_info": {
    "record_name": "100",
    "sampling_frequency": 360,
    "signal_length": 650000,
    "duration_minutes": 30.0,
    "leads": ["MLII", "V1"]
  },
  "expert_annotations": {
    "total_beats": 2273,
    "annotation_types": {
      "N": 2239,
      "V": 1,
      "A": 33
    },
    "critical_events": [
      {
        "time": 5.361,
        "type": "Atrial premature beat",
        "annotation": "A"
      }
    ]
  },
  "advanced_clinical_analysis": {
    "systematic_review": {
      "rate": "Normal (75 bpm)",
      "rhythm": "Sinus rhythm with APCs",
      "axis": "Normal"
    },
    "clinical_interpretation": {
      "primary_diagnosis": "Sinus rhythm",
      "secondary_findings": ["Atrial premature complexes"],
      "recommendations": ["Routine follow-up"]
    }
  },
  "mit_bih_validation": {
    "precision": 0.98,
    "recall": 0.97,
    "f1_score": 0.975
  }
}
```# 🖼️ Vizualizacija i Utility Endpoints

## Vizualizacija Endpoints

### 7. PNG Time-Domain Grafikon
**POST** `/generate/png/time-domain`

Generiše profesionalni PNG grafikon EKG signala u vremenskom domenu.

**Request Body:**
```json
{
  "signal_data": [0.1, 0.2, 0.15, ...],
  "fs": 250,
  "title": "EKG Signal Analysis",
  "highlight_r_peaks": true
}
```

**Response:**
```json
{
  "png_base64": "iVBORw0KGgoAAAANSUhEUgAA...",
  "metadata": {
    "resolution": "1200x800",
    "format": "PNG",
    "file_size_kb": 245
  }
}
```

### 8. PNG FFT Spektar
**POST** `/generate/png/fft-spectrum`

Generiše PNG dijagram frekvencijskog spektra.

**Request Body:**
```json
{
  "signal_data": [0.1, 0.2, 0.15, ...],
  "fs": 250,
  "title": "FFT Spectrum Analysis"
}
```

**Response:**
```json
{
  "png_base64": "iVBORw0KGgoAAAANSUhEUgAA...",
  "fft_data": {
    "peak_frequency": 1.2,
    "dominant_frequencies": [1.2, 2.4, 3.6]
  }
}
```

### 9. PNG Z-Plane Dijagram
**POST** `/generate/png/z-plane`

Generiše PNG dijagram polova i nula u Z-ravnini.

**Request Body:**
```json
{
  "signal_data": [0.1, 0.2, 0.15, ...],
  "fs": 250,
  "title": "Pole-Zero Analysis"
}
```

**Response:**
```json
{
  "png_base64": "iVBORw0KGgoAAAANSUhEUgAA...",
  "stability_analysis": {
    "stable": true,
    "max_pole_magnitude": 0.856
  }
}
```

---

## 📄 Izveštaji i PDF

### 10. Integrisani Izveštaj
**POST** `/generate/complete-report`

Generiše kompletan izveštaj sa opcionalnim PDF exportom.

**Request Body:**
```json
{
  "signal_data": [0.1, 0.2, 0.15, ...],
  "fs": 250,
  "patient_info": {
    "id": "P001",
    "age": 45,
    "gender": "M"
  },
  "generate_pdf": true,
  "include_visualizations": true
}
```

**Response:**
```json
{
  "report": {
    "executive_summary": "Normal sinus rhythm detected",
    "detailed_analysis": { ... },
    "recommendations": ["Regular monitoring"],
    "visualizations": {
      "time_domain": "base64_png",
      "fft_spectrum": "base64_png",
      "pole_zero": "base64_png"
    }
  },
  "pdf_base64": "JVBERi0xLjQKMSAwIG9iago8PC...",
  "metadata": {
    "generated_at": "2024-01-15T10:30:00Z",
    "report_id": "RPT_001_20240115"
  }
}
```

### 11. Direktni PDF Download
**POST** `/generate/pdf-report`

Generiše i vraća PDF fajl direktno.

**Request Body:**
```json
{
  "analysis_results": { ... },
  "patient_info": { ... },
  "report_options": {
    "include_raw_data": false,
    "language": "sr"
  }
}
```

**Response:**
- **Content-Type**: `application/pdf`
- **Content-Disposition**: `attachment; filename="ekg_report.pdf"`
- **Body**: Binary PDF content

---

## 🔧 Utility Endpoints

### 12. Signal-to-Image Konverzija
**POST** `/convert/signal-to-image`

Konvertuje sirove EKG podatke u realističnu EKG sliku.

**Request Body:**
```json
{
  "signal_data": [0.1, 0.2, 0.15, ...],
  "fs": 250,
  "image_options": {
    "width": 1200,
    "height": 800,
    "grid_enabled": true,
    "annotations": true
  }
}
```

**Response:**
```json
{
  "generated_image": "data:image/png;base64,iVBORw0KGgo...",
  "metadata": {
    "original_signal_length": 1250,
    "image_dimensions": "1200x800",
    "compression_ratio": 0.85
  }
}
```

### 13. WFDB-to-Image Konverzija
**POST** `/analyze/wfdb-to-image`

Konvertuje WFDB fajlove u EKG sliku sa anotacijama.

**Request Body:**
```json
{
  "files": {
    "hea_content": "...",
    "dat_content": "...",
    "atr_content": "..."
  },
  "image_options": {
    "include_annotations": true,
    "highlight_arrhythmias": true
  }
}
```

**Response:**
```json
{
  "generated_image": "data:image/png;base64,iVBORw0KGgo...",
  "annotations": {
    "total_beats": 2273,
    "highlighted_events": [
      {
        "type": "Atrial premature beat",
        "location": {"x": 450, "y": 200}
      }
    ]
  }
}
```

### 14. MIT-BIH Validacija
**POST** `/validate/mitbih`

Validira algoritme protiv MIT-BIH ekspertskih anotacija.

**Request Body:**
```json
{
  "algorithm_detections": [120, 330, 540, 750],
  "expert_annotations": [118, 332, 538, 752],
  "tolerance_ms": 50
}
```

**Response:**
```json
{
  "validation_metrics": {
    "true_positives": 4,
    "false_positives": 0,
    "false_negatives": 0,
    "precision": 1.0,
    "recall": 1.0,
    "f1_score": 1.0,
    "sensitivity": 1.0,
    "specificity": 0.99
  },
  "detailed_comparison": [
    {
      "algorithm": 120,
      "expert": 118,
      "difference_ms": 2,
      "status": "TP"
    }
  ]
}
```

### 15. SNR Analiza
**POST** `/analyze/snr`

Realistična analiza Signal-to-Noise Ratio.

**Request Body:**
```json
{
  "signal_data": [0.1, 0.2, 0.15, ...],
  "fs": 250
}
```

**Response:**
```json
{
  "snr_analysis": {
    "snr_db": 25.4,
    "quality_assessment": "Good",
    "quality_score": 0.85,
    "noise_characteristics": {
      "baseline_wander": 0.1,
      "high_frequency_noise": 0.05,
      "powerline_interference": 0.02
    },
    "recommendations": [
      "Signal quality is acceptable for analysis",
      "Consider baseline correction"
    ]
  }
}
```# 🚨 Error Handling & Best Practices

## Error Response Format

Svi endpoint-ovi vraćaju konzistentan format grešaka:

```json
{
  "error": "Opis greške",
  "error_code": "INVALID_SIGNAL_FORMAT",
  "details": {
    "expected_format": "array of numbers",
    "received_format": "string"
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## HTTP Status Codes

| Status | Opis | Primer |
|--------|------|--------|
| 200 | OK | Uspešna analiza |
| 400 | Bad Request | Nevaljan format podataka |
| 404 | Not Found | Nepostojeći endpoint |
| 413 | Payload Too Large | Slika > 10MB |
| 422 | Unprocessable Entity | Signal prekratak za analizu |
| 500 | Internal Server Error | Greška u obradi |

## Česti Error Slučajevi

### 1. Nevaljan Signal Format
```json
{
  "error": "Signal mora biti array brojeva",
  "error_code": "INVALID_SIGNAL_FORMAT"
}
```

### 2. Prekratak Signal
```json
{
  "error": "Signal prekratak za analizu (minimum 100 uzoraka)",
  "error_code": "SIGNAL_TOO_SHORT",
  "details": {
    "received_length": 50,
    "minimum_required": 100
  }
}
```

### 3. Nevažeća EKG Slika
```json
{
  "error": "Slika ne sadrži valjan EKG signal",
  "error_code": "INVALID_EKG_IMAGE",
  "details": {
    "validation_score": 0.23,
    "minimum_required": 0.7
  }
}
```

---

## 📝 Praktični Primeri

### Primer 1: Osnovna FFT Analiza

**Request:**
```bash
curl -X POST http://localhost:8000/analyze/fft \
  -H "Content-Type: application/json" \
  -d '{
    "signal": [0.1, 0.2, 0.15, 0.3, 0.25, 0.1, 0.05, 0.2],
    "fs": 250
  }'
```

**Response:**
```json
{
  "frequencies": [0, 31.25, 62.5, 93.75, 125],
  "magnitudes": [0.5, 0.3, 0.1, 0.05, 0.02],
  "peak_frequency": 31.25,
  "peak_magnitude": 0.3
}
```

### Primer 2: Analiza EKG Slike

**JavaScript Example:**
```javascript
const analyzeEKGImage = async (imageFile) => {
  const formData = new FormData();
  formData.append('image', imageFile);
  
  const response = await fetch('/analyze/image', {
    method: 'POST',
    body: formData
  });
  
  return response.json();
};
```

### Primer 3: Kompletna MIT-BIH Analiza

**Python Example:**
```python
import requests
import base64

# Učitaj WFDB fajlove
with open('100.hea', 'r') as f:
    hea_content = f.read()
    
with open('100.dat', 'rb') as f:
    dat_content = base64.b64encode(f.read()).decode()
    
with open('100.atr', 'rb') as f:
    atr_content = base64.b64encode(f.read()).decode()

# API poziv
response = requests.post('http://localhost:8000/analyze/wfdb', json={
    'files': {
        'hea_content': hea_content,
        'dat_content': dat_content,
        'atr_content': atr_content
    },
    'record_name': '100',
    'analysis_options': {
        'include_annotations': True,
        'validate_mit_bih': True
    }
})

result = response.json()
print(f"Heart rate: {result['advanced_clinical_analysis']['systematic_review']['rate']}")
```

---

## ⚡ Performance & Limits

### Rate Limiting
- **Osnovni plan**: 100 zahteva/minut
- **Pro plan**: 1000 zahteva/minut
- **Enterprise**: Bez ograničenja

### Size Limits
| Tip podatka | Maximum |
|-------------|---------|
| EKG slike | 10 MB |
| Sirovi signali | 1M uzoraka |
| WFDB fajlovi | 50 MB |
| PDF izveštaji | 20 MB |

### Response Times
| Endpoint | Tipično vreme |
|----------|---------------|
| `/analyze/fft` | 50-200ms |
| `/analyze/image` | 2-5s |
| `/analyze/complete` | 5-15s |
| `/analyze/wfdb` | 10-30s |
| `/generate/pdf-report` | 3-8s |

---

## 🔒 Security & Authentication

### API Key Authentication
```bash
curl -X POST http://localhost:8000/analyze/complete \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{ ... }'
```

### HTTPS Requirements
- Svi production pozivi moraju biti preko HTTPS
- Self-signed sertifikati nisu podržani
- TLS 1.2+ obavezno

### Data Privacy
- Slike i signali se **ne čuvaju** na serveru
- Sve analize su stateless
- GDPR compliant za EU korisnike
- HIPAA compliant za US healthcare

---

## 🎯 Best Practices

### 1. Signal Quality
```javascript
// Uvek proverite kvalitet signala pre analize
const result = await fetch('/analyze/complete', {
  method: 'POST',
  body: JSON.stringify({
    signal: yourSignal,
    fs: 250
  })
});

const data = await result.json();
if (data.signal_quality.quality_score < 0.7) {
  console.warn('Signal kvalitet je nizak:', data.signal_quality.assessment);
}
```

### 2. Error Handling
```javascript
const analyzeWithErrorHandling = async (signal) => {
  try {
    const response = await fetch('/analyze/complete', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ signal, fs: 250 })
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(`API Error: ${error.error}`);
    }
    
    return response.json();
  } catch (error) {
    console.error('Analiza neuspešna:', error.message);
    return null;
  }
};
```

### 3. Batch Processing
```python
# Za veće količine podataka, koristite batch processing
def process_multiple_signals(signals):
    results = []
    for signal in signals:
        try:
            result = requests.post('/analyze/complete', 
                json={'signal': signal, 'fs': 250})
            results.append(result.json())
            time.sleep(0.1)  # Rate limiting
        except Exception as e:
            print(f"Error processing signal: {e}")
    return results
```

### 4. Caching Results
```javascript
// Cache rezultate za iste signale
const signalHash = btoa(JSON.stringify(signal));
const cachedResult = localStorage.getItem(signalHash);

if (cachedResult) {
  return JSON.parse(cachedResult);
} else {
  const result = await analyzeSignal(signal);
  localStorage.setItem(signalHash, JSON.stringify(result));
  return result;
}
```

---

## 📞 Support & Contact

### API Support
- **Email**: api-support@ekg-analiza.com
- **Documentation**: https://docs.ekg-analiza.com
- **Status Page**: https://status.ekg-analiza.com

### Technical Issues
- **GitHub Issues**: https://github.com/ekg-analiza/api/issues
- **Discord Community**: https://discord.gg/ekg-analiza
- **Stack Overflow**: Tag `ekg-analiza-api`

### Version Updates
- **Changelog**: https://changelog.ekg-analiza.com
- **Breaking Changes**: 30-day advance notice
- **Deprecation Policy**: 6 months support for old versions

---

## 📚 Additional Resources

### Scientific References
1. **Faust, O., et al. (2004)** - "Spatial Filling Index for ECG Analysis"
2. **Sörnmo, L., & Laguna, P. (2005)** - "Bioelectrical Signal Processing in Cardiac and Neurological Applications"
3. **Yıldırım, Ö. (2018)** - "Wavelet-based ECG Arrhythmia Detection"
4. **MIT-BIH Database** - PhysioNet Reference Standards

### Code Examples
- **GitHub Repository**: https://github.com/ekg-analiza/api-examples
- **Jupyter Notebooks**: Interactive analysis examples
- **Postman Collection**: Ready-to-use API tests
- **SDK Libraries**: Python, JavaScript, Java, C#

### Training Materials
- **Video Tutorials**: Step-by-step API usage
- **Webinar Series**: Advanced EKG analysis techniques
- **Certification Program**: API Expert certification
- **Medical Guidelines**: Clinical interpretation best practices