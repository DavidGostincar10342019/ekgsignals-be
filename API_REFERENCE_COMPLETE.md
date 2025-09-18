# 📚 KOMPLETNA API REFERENCA
## EKG Analiza - Svih 21 Endpoint-a

---

## 🎯 BRZI PREGLED

| Kategorija | Endpoint-i | Opis |
|------------|------------|------|
| **Osnovni** | 7 | Health, Complete Analysis, FFT, Z-Transform, Arrhythmia, Image, Info |
| **Napredni** | 8 | Raw Signal, WFDB, Educational, Filters, Conversions |
| **PNG Generation** | 3 | Time Domain, FFT Spectrum, Z-Plane |
| **Validacija** | 3 | MIT-BIH, Roundtrip Testing, Complete Reports |

---

## 1. OSNOVNI ENDPOINT-I

### `GET /api/health`
```bash
curl -X GET http://localhost:8000/api/health
```
**Response:** `{"status": "ok"}`

### `POST /api/analyze/complete`
```bash
curl -X POST http://localhost:8000/api/analyze/complete \
  -H "Content-Type: application/json" \
  -d '{"image": "data:image/png;base64,iVBOR...", "fs": 250}'
```

### `POST /api/analyze/fft`
```bash
curl -X POST http://localhost:8000/api/analyze/fft \
  -H "Content-Type: application/json" \
  -d '{"signal": [0.1, 0.2, 0.3, ...], "fs": 250}'
```

### `POST /api/analyze/ztransform`
```bash
curl -X POST http://localhost:8000/api/analyze/ztransform \
  -H "Content-Type: application/json" \
  -d '{"signal": [0.1, 0.2, 0.3, ...], "fs": 250}'
```

### `POST /api/analyze/arrhythmia`
```bash
curl -X POST http://localhost:8000/api/analyze/arrhythmia \
  -H "Content-Type: application/json" \
  -d '{"signal": [0.1, 0.2, 0.3, ...], "fs": 250}'
```

### `POST /api/analyze/image`
```bash
curl -X POST http://localhost:8000/api/analyze/image \
  -H "Content-Type: application/json" \
  -d '{"image": "data:image/png;base64,iVBOR..."}'
```

### `GET /api/info`
```bash
curl -X GET http://localhost:8000/api/info
```

---

## 2. NAPREDNI ENDPOINT-I

### `POST /api/analyze/raw-signal`
**Funkcija:** Kompletna analiza sirovih EKG podataka
```bash
curl -X POST http://localhost:8000/api/analyze/raw-signal \
  -H "Content-Type: application/json" \
  -d '{"signal": [array], "fs": 250, "apply_filters": true}'
```

### `POST /api/analyze/wfdb`
**Funkcija:** MIT-BIH WFDB fajl analiza
```bash
curl -X POST http://localhost:8000/api/analyze/wfdb \
  -H "Content-Type: application/json" \
  -d '{"wfdb_files": {"dat": "base64_data", "hea": "base64_header"}}'
```

### `GET /api/download/wfdb/<record>/<type>`
**Funkcija:** Download WFDB fajlova
```bash
curl -X GET http://localhost:8000/api/download/wfdb/100/dat
curl -X GET http://localhost:8000/api/download/wfdb/100/hea
```

### `POST /api/filter/design`
**Funkcija:** Dizajn digitalnih filtara
```bash
curl -X POST http://localhost:8000/api/filter/design \
  -H "Content-Type: application/json" \
  -d '{"cutoff_freq": 40, "fs": 250, "filter_type": "lowpass"}'
```

### `POST /api/analyze/educational`
**Funkcija:** Edukativna analiza sa objašnjenjima
```bash
curl -X POST http://localhost:8000/api/analyze/educational \
  -H "Content-Type: application/json" \
  -d '{"signal": [array], "fs": 250, "detail_level": "comprehensive"}'
```

### `POST /api/convert/signal-to-image`
**Funkcija:** Signal → EKG slika konverzija
```bash
curl -X POST http://localhost:8000/api/convert/signal-to-image \
  -H "Content-Type: application/json" \
  -d '{"signal": [array], "fs": 250, "style": "clinical"}'
```

### `POST /api/test/signal-image-roundtrip`
**Funkcija:** Test signal → image → signal
```bash
curl -X POST http://localhost:8000/api/test/signal-image-roundtrip \
  -H "Content-Type: application/json" \
  -d '{"signal": [array], "fs": 250}'
```

### `POST /api/analyze/wfdb-to-image`
**Funkcija:** WFDB → EKG slika
```bash
curl -X POST http://localhost:8000/api/analyze/wfdb-to-image \
  -H "Content-Type: application/json" \
  -d '{"wfdb_files": {...}, "style": "clinical", "duration_sec": 10}'
```

---

## 3. PNG GENERISANJE

### `POST /api/generate/png/time-domain`
**Funkcija:** Publication-ready PNG (300 DPI)
```bash
curl -X POST http://localhost:8000/api/generate/png/time-domain \
  -H "Content-Type: application/json" \
  -d '{"signal": [array], "fs": 250, "title": "EKG Signal Analysis"}'
```

### `POST /api/generate/png/fft-spectrum`
**Funkcija:** FFT spektar PNG
```bash
curl -X POST http://localhost:8000/api/generate/png/fft-spectrum \
  -H "Content-Type: application/json" \
  -d '{"signal": [array], "fs": 250, "highlight_bands": true}'
```

### `POST /api/generate/png/z-plane`
**Funkcija:** Z-ravan pole-zero dijagram
```bash
curl -X POST http://localhost:8000/api/generate/png/z-plane \
  -H "Content-Type: application/json" \
  -d '{"signal": [array], "fs": 250, "show_stability": true}'
```

---

## 4. VALIDACIJA I IZVEŠTAVANJE

### `POST /api/validate/mitbih`
**Funkcija:** MIT-BIH standard validacija
```bash
curl -X POST http://localhost:8000/api/validate/mitbih \
  -H "Content-Type: application/json" \
  -d '{"signal": [array], "fs": 250, "record_name": "100"}'
```

### `POST /api/generate/educational-ekg-image`
**Funkcija:** Edukativne EKG slike
```bash
curl -X POST http://localhost:8000/api/generate/educational-ekg-image \
  -H "Content-Type: application/json" \
  -d '{"signal": [array], "analysis_type": "complete", "annotations": true}'
```

### `POST /api/generate/complete-report`
**Funkcija:** Kompletni izveštaj (JSON + PNG)
```bash
curl -X POST http://localhost:8000/api/generate/complete-report \
  -H "Content-Type: application/json" \
  -d '{"signal": [array], "fs": 250, "include_images": true, "format": "comprehensive"}'
```

---

## 5. PRIMERI RESPONSE-A

### FFT Analiza Response:
```json
{
  "peak_frequency_hz": 1.5,
  "peak_amplitude": 0.85,
  "sine_wave_analysis": {
    "spectral_purity_percent": 89.5,
    "thd_percent": 3.2,
    "sine_wave_confidence": "visoka"
  }
}
```

### Z-Transform Response:
```json
{
  "ar_coefficients": [0.5, -0.2],
  "poles": [{"real": 0.4, "imag": 0.3}],
  "stability": {
    "stable": true,
    "max_pole_magnitude": 0.89
  }
}
```

### Arrhythmia Detection Response:
```json
{
  "heart_rate": {
    "average_bpm": 75.2,
    "heart_rate_variability": 45.8
  },
  "arrhythmias": {
    "detected": [
      {
        "type": "Normalan ritam",
        "severity": "low"
      }
    ]
  }
}
```

---

## 6. ERROR RESPONSES

### Standardni Error Format:
```json
{
  "error": "Opis greške",
  "code": "ERROR_CODE",
  "details": {
    "parameter": "problematic_value"
  }
}
```

### Česti Error Kodovi:
- `INVALID_SIGNAL` - Neispravan signal format
- `INSUFFICIENT_DATA` - Nedovoljno podataka za analizu
- `PROCESSING_ERROR` - Greška tokom obrade
- `VALIDATION_FAILED` - Validacija ulaza neuspešna

---

## 7. RATE LIMITING I PERFORMANCE

### Preporučeni Limits:
- **Health checks:** Bez ograničenja
- **Osnovne analize:** 10 req/min
- **PNG generisanje:** 5 req/min
- **Kompleksne analize:** 3 req/min

### Performance Metrics:
- **FFT analiza:** ~50ms (1000 samples)
- **Image processing:** ~200ms (standard EKG)
- **Complete analysis:** ~500ms
- **PNG generation:** ~1s (300 DPI)

---

*API Referenca - Verzija 4.0*  
*Sve 21 endpoint-a dokumentovano sa primerima*  
*Poslednja izmena: {{ current_date }}*