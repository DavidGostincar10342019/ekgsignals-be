# Projektna Dokumentacija
## Automatizovana Obrada EKG Signala - Kombinacija FFT i Z-Transformacije

### Verzija: 1.0
### Datum: 2024

---

## Sadržaj

1. [Pregled Projekta](#1-pregled-projekta)
2. [Arhitektura Sistema](#2-arhitektura-sistema)
3. [Tehnička Specifikacija](#3-tehnička-specifikacija)
4. [API Dokumentacija](#4-api-dokumentacija)
5. [Moduli i Komponente](#5-moduli-i-komponente)
6. [Instalacija i Pokretanje](#6-instalacija-i-pokretanje)
7. [Testiranje](#7-testiranje)
8. [Deployment](#8-deployment)
9. [Održavanje](#9-održavanje)

---

## 1. Pregled Projekta

### 1.1 Cilj Projekta
Razvoj kompletnog sistema za digitalnu obradu i analizu elektrokardiograma (EKG) koji kombinuje:
- **Image Processing**: Konverzija papirnih EKG zapisa u digitalne signale
- **Signal Processing**: FFT analiza i Z-transformacija
- **Machine Learning**: Rule-based klasifikacija aritmija
- **Validation**: MIT-BIH dataset evaluacija

### 1.2 Ključne Funkcionalnosti
- ✅ Digitalizacija EKG slika (PNG/JPG → 1D signal)
- ✅ WFDB format podrška (.hea/.dat/.atr)
- ✅ FFT spektralna analiza
- ✅ Z-transformacija za stabilnost sistema
- ✅ R-peak detekcija i HRV analiza
- ✅ Korelacijska analiza originalnog vs ekstraktovanog signala
- ✅ Batch processing i vizualizacija rezultata

### 1.3 Tehnologije
- **Backend**: Python 3.8+, Flask REST API
- **Signal Processing**: NumPy, SciPy, OpenCV
- **Visualization**: Matplotlib, PIL
- **Medical Data**: WFDB biblioteka
- **Frontend**: HTML5, JavaScript (ES6), CSS3

---

## 2. Arhitektura Sistema

### 2.1 Blok Dijagram
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Ulazni Sloj   │    │   Obrada Sloj    │    │  Izlazni Sloj   │
├─────────────────┤    ├──────────────────┤    ├─────────────────┤
│ • EKG Slike     │───▶│ • Image Proc.    │───▶│ • JSON Rezultati│
│ • WFDB Fajlovi  │    │ • Signal Proc.   │    │ • PNG Grafikoni │
│ • Upload API    │    │ • FFT/Z-Transform│    │ • PDF Izveštaji │
│                 │    │ • Correlation    │    │ • Web Interface │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### 2.2 Komponente Sistema

#### 2.2.1 Flask Backend (app/)
- **main.py**: WSGI entry point
- **routes.py**: Core API endpoints
- **routes_visualizations.py**: Visualization API
- **routes_pdf.py**: PDF generation API

#### 2.2.2 Analysis Engine (app/analysis/)
- **unified_image_processing.py**: Image → Signal pipeline
- **fft.py**: Fourier analysis module  
- **ztransform.py**: Z-transform and stability
- **arrhythmia_detection.py**: R-peak detection + HRV
- **correlation_visualization.py**: Signal correlation analysis
- **wfdb_reader.py**: MIT-BIH data parser
- **mitbih_validator.py**: Performance evaluation

#### 2.2.3 Frontend (app/static/, app/templates/)
- **index.html**: Single-page application
- **app.js**: Client-side logic and API calls
- **style.css**: UI styling
- **Images**: Icons and test samples

---

## 3. Tehnička Specifikacija

### 3.1 Image Processing Pipeline
```python
# Korak 1: Predobrada
grayscale = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
blurred = cv2.GaussianBlur(grayscale, (3, 3), 0)

# Korak 2: Binarizacija
binary = cv2.adaptiveThreshold(blurred, 255, 
    cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)

# Korak 3: Grid Detection & Removal
horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
grid_mask = cv2.add(horizontal_grid, vertical_grid)
cleaned = cv2.subtract(binary, grid_mask)

# Korak 4: Contour Detection
contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

# Korak 5: Spline Reconstruction
from scipy.interpolate import splprep, splev
tck, u = splprep([x_coords, y_coords], s=0)
signal_1d = splev(u_new, tck)
```

### 3.2 Signal Processing Algorithms

#### 3.2.1 FFT Analysis
```python
# Diskretna Furijeova Transformacija
fft_values = np.fft.rfft(signal_array)
freq = np.fft.rfftfreq(len(signal_array), d=1/fs)
magnitude = np.abs(fft_values)

# Welch Method za Power Spectral Density
frequencies, psd = signal.welch(signal_array, fs=fs, 
                               window='hann', nperseg=1024, noverlap=512)

# Dominantna frekvencija
peak_idx = np.argmax(magnitude[1:]) + 1
peak_frequency_hz = freq[peak_idx]
```

#### 3.2.2 Z-Transform Analysis
```python
# Z-transformacija: X(z) = Σ x[n]z^(-n)
# Butterworth Band-pass Filter (0.5-40 Hz)
low = 0.5 / nyquist
high = 40 / nyquist
b, a = signal.butter(order, [low, high], btype='band')

# Pol-nula analiza
zeros, poles, gain = signal.tf2zpk(b, a)

# Stabilnost sistema: |z| < 1
pole_magnitudes = np.abs(poles)
stable = np.max(pole_magnitudes) < 1.0
```

#### 3.2.3 Arrhythmia Detection
```python
# Rule-based klasifikacija
def classify_rhythm(heart_rate, rr_variability):
    if heart_rate > 100:
        return "Tahikardija"
    elif heart_rate < 60:
        return "Bradikardija"
    elif rr_variability > threshold:
        return "Nepravilan ritam"
    else:
        return "Normalan sinusni ritam"
```

### 3.3 Correlation Analysis
```python
# Pearson korelacija
def correlation_analysis(original_signal, extracted_signal):
    # Poravnavanje signala (lag compensation)
    lag = find_optimal_lag(original_signal, extracted_signal)
    aligned_signal = np.roll(extracted_signal, lag)
    
    # Metrike
    pearson_r = np.corrcoef(original_signal, aligned_signal)[0, 1]
    rmse = np.sqrt(np.mean((original_signal - aligned_signal)**2))
    lag_ms = lag * 1000 / sampling_rate
    
    return {"r": pearson_r, "rmse": rmse, "lag_ms": lag_ms}
```

---

## 4. API Dokumentacija

### 4.1 Core Endpoints

#### POST /api/analyze_image
**Opis**: Konvertuje EKG sliku u digitalni signal
```json
Request:
{
  "image": "base64_encoded_image"
}

Response:
{
  "status": "success",
  "signal": [0.1, 0.2, -0.1, ...],
  "sampling_rate": 250,
  "processing_steps": {
    "grayscale": "completed",
    "binarization": "completed", 
    "grid_removal": "completed",
    "signal_extraction": "completed"
  },
  "visualization": "/static/generated_plots/step_by_step_analysis.png"
}
```

#### POST /api/run_fft_analysis
**Opis**: FFT spektralna analiza signala
```json
Request:
{
  "signal": [0.1, 0.2, -0.1, ...],
  "sampling_rate": 250
}

Response:
{
  "peak_frequency_hz": 1.2,
  "dominant_frequencies": [1.2, 2.4, 3.6],
  "thd": 0.05,
  "spectral_purity": 0.92,
  "fft_plot": "/static/generated_plots/fft_spectrum.png"
}
```

#### POST /api/comprehensive_analysis
**Opis**: Kompletna analiza (FFT + Z-transform + arrhythmia)
```json
Response:
{
  "fft_analysis": {...},
  "z_transform": {
    "stable": true,
    "poles": [...],
    "zeros": [...],
    "max_pole_magnitude": 0.95
  },
  "arrhythmia_detection": {
    "heart_rate": 72,
    "rhythm_classification": "Normalan sinusni ritam",
    "r_peaks": [125, 375, 625, ...],
    "rr_intervals": [250, 250, 248, ...]
  },
  "correlation_analysis": {
    "pearson_r": 0.85,
    "rmse": 0.12,
    "lag_ms": 15.0
  }
}
```

#### POST /api/analyze_wfdb
**Opis**: Analiza MIT-BIH WFDB fajlova
```json
Request:
{
  "record_path": "mitbih/100"
}

Response:
{
  "record_info": {
    "duration_sec": 1800,
    "sampling_rate": 360,
    "leads": ["MLII", "V1"]
  },
  "validation_results": {
    "precision": 0.94,
    "recall": 0.92,
    "f1_score": 0.93,
    "tolerance_ms": 50
  }
}
```

### 4.2 Visualization Endpoints

#### POST /api/generate_time_domain_plot
**Opis**: Generiše vremenski dijagram signala
```json
Request:
{
  "signal": [...],
  "r_peaks": [125, 375, 625],
  "title": "EKG Signal sa R-pikovima"
}

Response:
{
  "plot_url": "/static/generated_plots/time_domain_plot.png"
}
```

#### POST /api/generate_z_plane_plot
**Opis**: Pol-nula dijagram u Z-ravni
```json
Response:
{
  "plot_url": "/static/generated_plots/z_plane_analysis.png",
  "stability_info": {
    "stable": true,
    "poles_inside_unit_circle": 8,
    "zeros_count": 6
  }
}
```

---

## 5. Moduli i Komponente

### 5.1 Image Processing (app/analysis/unified_image_processing.py)

#### Klase:
- `ImageProcessor`: Glavna klasa za obradu slika
- `GridRemover`: Specijalizovana klasa za uklanjanje mreže
- `SignalExtractor`: Ekstrakcija 1D signala iz kontura

#### Ključne Funkcije:
```python
def process_ekg_image_to_signal(image_path: str) -> dict:
    """
    Kompletan pipeline: slika → signal
    
    Args:
        image_path: Putanja do EKG slike
        
    Returns:
        dict: {
            'signal': numpy.array,
            'sampling_rate': int,
            'processing_metadata': dict,
            'visualization': str
        }
    """
```

### 5.2 FFT Analysis (app/analysis/fft.py)

#### Ključne Funkcije:
```python
def analyze_ekg_signal_fft(signal: np.array, fs: int = 250) -> dict:
    """
    FFT analiza EKG signala
    
    Args:
        signal: 1D numpy array
        fs: Sampling rate u Hz
        
    Returns:
        dict: FFT rezultati sa spektralnim metrikama
    """

def calculate_thd(magnitude: np.array, peak_idx: int) -> float:
    """
    Total Harmonic Distortion kalkulacija
    """
```

### 5.3 Z-Transform (app/analysis/ztransform.py)

#### Ključne Funkcije:
```python
def z_transform_analysis(signal: np.array, fs: int = 250) -> dict:
    """
    Z-domen analiza signala
    
    Returns:
        dict: {
            'poles': list,
            'zeros': list, 
            'stable': bool,
            'ar_coefficients': list,
            'filter_response': dict
        }
    """

def design_butterworth_filter(low_freq: float, high_freq: float, 
                             fs: int, order: int = 4) -> tuple:
    """
    Projektovanje Butterworth band-pass filtera
    """
```

### 5.4 Arrhythmia Detection (app/analysis/arrhythmia_detection.py)

#### Ključne Funkcije:
```python
def detect_r_peaks(signal: np.array, fs: int = 250) -> np.array:
    """
    R-peak detekcija kombinovanjem morfološke analize i SciPy
    """

def calculate_hrv_parameters(rr_intervals: np.array) -> dict:
    """
    Heart Rate Variability parametri:
    - RMSSD, SDNN, pNN50, triangular index
    """

def classify_arrhythmia(heart_rate: float, rr_intervals: np.array) -> dict:
    """
    Rule-based klasifikacija aritmija
    """
```

### 5.5 MIT-BIH Validation (app/analysis/mitbih_validator.py)

#### Ključne Funkcije:
```python
def validate_against_mitbih(detected_peaks: np.array, 
                           reference_annotations: np.array,
                           tolerance_ms: int = 50) -> dict:
    """
    Evaluacija performansi na MIT-BIH datasetu
    
    Returns:
        dict: Precision, Recall, F1-score, Accuracy
    """
```

---

## 6. Instalacija i Pokretanje

### 6.1 Sistemski Zahtevi
- **Python**: 3.8 ili noviji
- **RAM**: Minimum 4GB (preporučeno 8GB)
- **Disk**: 2GB slobodnog prostora
- **OS**: Windows 10/11, macOS 10.15+, Ubuntu 18.04+

### 6.2 Instalacija Dependencies
```bash
# 1. Kloniranje repozitorijuma
git clone https://github.com/username/ekg-analysis-system.git
cd ekg-analysis-system

# 2. Kreiranje virtualnog okruženja
python -m venv venv
source venv/bin/activate  # Linux/macOS
# ili
venv\Scripts\activate     # Windows

# 3. Instalacija paketa
pip install -r requirements.txt
```

### 6.3 Konfiguracija
```python
# config.py
class Config:
    SECRET_KEY = 'your-secret-key-here'
    UPLOAD_FOLDER = 'uploads/'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'hea', 'dat', 'atr'}
    
    # Signal processing
    DEFAULT_SAMPLING_RATE = 250
    BUTTERWORTH_ORDER = 4
    BANDPASS_LOW = 0.5
    BANDPASS_HIGH = 40.0
    
    # MIT-BIH validation
    TOLERANCE_MS = 50
```

### 6.4 Pokretanje Sistema
```bash
# Development mode
python run.sh
# ili
flask run --debug

# Production mode
python wsgi.py

# Dostupno na: http://localhost:5000
```

### 6.5 Docker Deployment
```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["python", "wsgi.py"]
```

```bash
# Docker komande
docker build -t ekg-analysis .
docker run -p 5000:5000 ekg-analysis
```

---

## 7. Testiranje

### 7.1 Unit Tests
```bash
# Pokretanje svih testova
python -m pytest tests/ -v

# Specifični test moduli
python -m pytest tests/test_image_processing.py
python -m pytest tests/test_fft_analysis.py
python -m pytest tests/test_correlation.py
```

### 7.2 Test Coverage
```python
# Test fajlovi:
tests/
├── conftest.py                    # Test konfiguracija
├── test_image_processing.py       # Image processing pipeline
├── test_fft_analysis.py          # FFT analiza testovi
├── test_ztransform.py             # Z-transform testovi
├── test_arrhythmia_detection.py  # Arrhythmia detection
├── test_correlation.py           # Correlation analysis
├── test_wfdb_reader.py           # WFDB format reader
└── test_api_endpoints.py         # Flask API testovi
```

### 7.3 Integration Tests
```python
# test_comprehensive_analysis.py
def test_complete_pipeline():
    """Test kompletnog pipeline-a: slika → signal → analiza"""
    image_path = "tests/data/test_ekg.png"
    
    # 1. Image processing
    result = process_ekg_image_to_signal(image_path)
    assert result['status'] == 'success'
    
    # 2. Signal analysis
    signal = result['signal']
    fft_result = analyze_ekg_signal_fft(signal)
    zt_result = z_transform_analysis(signal)
    
    # 3. Validation
    assert fft_result['peak_frequency_hz'] > 0
    assert zt_result['stable'] == True
```

### 7.4 Performance Tests
```python
# test_performance.py
def test_image_processing_speed():
    """Test brzine obrade slika"""
    start_time = time.time()
    result = process_ekg_image_to_signal("test_image.png")
    processing_time = time.time() - start_time
    
    assert processing_time < 5.0  # Manje od 5 sekundi
    assert result['status'] == 'success'

def test_batch_correlation_performance():
    """Test batch korelacijske analize"""
    images = ["test1.png", "test2.png", "test3.png"]
    start_time = time.time()
    
    results = run_batch_correlation_analysis(images)
    total_time = time.time() - start_time
    
    assert total_time < 30.0  # Manje od 30 sekundi za 3 slike
```

---

## 8. Deployment

### 8.1 Production Environment Setup

#### 8.1.1 Heroku Deployment
```bash
# Kreiranje Heroku aplikacije
heroku create ekg-analysis-app

# Environment variables
heroku config:set SECRET_KEY=your-production-secret-key
heroku config:set FLASK_ENV=production

# Deploy
git push heroku main
```

#### 8.1.2 AWS EC2 Deployment
```bash
# EC2 Instance setup
sudo apt update
sudo apt install python3-pip nginx

# Aplikacija setup
git clone https://github.com/username/ekg-analysis-system.git
cd ekg-analysis-system
pip3 install -r requirements.txt

# Nginx konfiguracija
sudo nano /etc/nginx/sites-available/ekg-analysis
```

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /static {
        alias /path/to/app/static;
    }
}
```

#### 8.1.3 Cloud Storage Setup
```python
# Za slike i rezultate
import boto3

def upload_to_s3(file_path, bucket_name, object_name):
    s3_client = boto3.client('s3')
    s3_client.upload_file(file_path, bucket_name, object_name)
```

### 8.2 Monitoring i Logging
```python
# logging_config.py
import logging
from logging.handlers import RotatingFileHandler

def setup_logging(app):
    if not app.debug:
        file_handler = RotatingFileHandler('logs/ekg_analysis.log',
                                         maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
```

### 8.3 Security Considerations
- **Input Validation**: Validacija upload fajlova
- **Rate Limiting**: Ograničavanje API poziva
- **HTTPS**: SSL sertifikati za production
- **Environment Variables**: Bezbedno čuvanje tajnih ključeva
- **Error Handling**: Graceful error responses

---

## 9. Održavanje

### 9.1 Backup Strategija
```bash
# Database backup (ako se koristi)
pg_dump ekg_analysis_db > backup_$(date +%Y%m%d).sql

# Fajl backup
tar -czf ekg_analysis_backup_$(date +%Y%m%d).tar.gz /path/to/app
```

### 9.2 Performance Monitoring
- **Response Times**: API endpoint performance
- **Memory Usage**: RAM consumption tracking
- **Error Rates**: Exception monitoring
- **User Analytics**: Usage patterns

### 9.3 Updates i Maintenance
```bash
# Dependency updates
pip list --outdated
pip install --upgrade package_name

# Security updates
pip audit
```

### 9.4 Troubleshooting

#### Common Issues:
1. **Memory Error**: Povećati RAM ili optimizovati batch processing
2. **Slow Image Processing**: Smanjiti rezoluciju ili optimizovati algoritme
3. **FFT Errors**: Proveriti sampling rate i signal length
4. **WFDB Format Issues**: Validirati .hea/.dat/.atr fajlove

#### Debug Mode:
```python
# app/main.py
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
```

---

## 10. Appendix

### 10.1 Glossary
- **FFT**: Fast Fourier Transform
- **Z-Transform**: Z-transformacija za analizu diskretnih sistema
- **HRV**: Heart Rate Variability
- **MIT-BIH**: MIT-Boston's Beth Israel Hospital database
- **WFDB**: WaveForm DataBase format

### 10.2 References
- MIT-BIH Arrhythmia Database: https://physionet.org/content/mitdb/
- SciPy Signal Processing: https://docs.scipy.org/doc/scipy/reference/signal.html
- OpenCV Documentation: https://docs.opencv.org/

### 10.3 License
MIT License - slobodno korišćenje za edukativne i istraživačke svrhe.

---

**Projektna Dokumentacija v1.0**  
**Poslednja izmena**: 2024  
**Autor**: Master Rad - Automatizovana Obrada EKG Signala