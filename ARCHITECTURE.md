# 📋 Arhitektura EKG Analiza Sistema

## 🎯 Pregled Projekta

**EKG Analiza** je napredna web aplikacija za digitalnu obradu i analizu elektrokardiografskih signala. Sistem omogućava uvoz EKG podataka iz slika papirnih zapisa ili digitalnih formata, njihovu obradu pomoću naprednih signal processing algoritma, te medicinsku interpretaciju rezultata.

### Verzija: 3.2
### Tehnologija: Flask-based Web Application
### Jezik: Python 3.x
### Ciljna grupa: Medicinski stručnjaci, studenti medicine, istraživači

---

## 🏗️ Sistemska Arhitektura

### Arhitekturni Pattern: MVC (Model-View-Controller)

```
┌─────────────────────────────────────────────────────────────┐
│                    CLIENT SIDE (Browser)                    │
├─────────────────────────────────────────────────────────────┤
│  Frontend (View)                                           │
│  • HTML5 Template (Jinja2)                               │
│  • CSS3 + Custom Styles                                  │
│  • JavaScript ES6+ (Vanilla JS)                          │
│  • PWA Support (Manifest + Service Worker)               │
└─────────────────────────────────────────────────────────────┘
                              │
                         HTTP/HTTPS
                              │
┌─────────────────────────────────────────────────────────────┐
│                     SERVER SIDE (Flask)                    │
├─────────────────────────────────────────────────────────────┤
│  Application Layer (Controller)                           │
│  • Flask Application Factory                             │
│  • Blueprint Routing System                              │
│  • RESTful API Endpoints                                 │
│  • Request/Response Handling                             │
├─────────────────────────────────────────────────────────────┤
│  Business Logic Layer (Model)                            │
│  • Signal Processing Modules                             │
│  • Mathematical Analysis Engines                         │
│  • Image Processing Pipeline                             │
│  • Medical Interpretation Logic                          │
├─────────────────────────────────────────────────────────────┤
│  Data Access Layer                                       │
│  • File System Operations                                │
│  • MIT-BIH Database Integration                          │
│  • Temporary Data Management                             │
│  • Configuration Management                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 Struktura Projekta

### Hijerarhijska Organizacija

```
biosignals-be/
├── 📄 main.py                    # Application entry point
├── 📄 wsgi.py                    # WSGI deployment configuration
├── 📄 requirements.txt           # Python dependencies
├── 📄 run.sh                     # Deployment script
├── 📄 ARCHITECTURE.md           # Ova dokumentacija
├── 📄 API_DOCUMENTATION.md      # API reference
├── 📄 README.md                 # Project overview
│
├── 📂 app/                      # Main application package
│   ├── 📄 __init__.py           # Flask factory pattern
│   ├── 📄 main.py               # Application initialization
│   ├── 📄 routes.py             # Primary API routes (1800+ lines)
│   ├── 📄 routes_backup.py      # Backup routing logic
│   ├── 📄 routes_pdf.py         # PDF generation endpoints
│   ├── 📄 routes_visualizations.py # Visualization endpoints
│   │
│   ├── 📂 analysis/             # Core analysis modules
│   │   ├── 📄 __init__.py
│   │   ├── 📄 advanced_cardiology_analysis.py
│   │   ├── 📄 advanced_ekg_analysis.py      # Main EKG algorithms
│   │   ├── 📄 arrhythmia_detection.py       # Arrhythmia classification
│   │   ├── 📄 correlation_visualization.py  # Signal correlation
│   │   ├── 📄 educational_ekg_image.py
│   │   ├── 📄 educational_visualization.py
│   │   ├── 📄 fft.py                       # Frequency domain analysis
│   │   ├── 📄 image_processing.py          # Image → Signal conversion
│   │   ├── 📄 image_processing_visualization.py # Step-by-step visualization
│   │   ├── 📄 improved_image_processing.py
│   │   ├── 📄 intelligent_signal_segmentation.py
│   │   ├── 📄 mitbih_validator.py          # MIT-BIH validation
│   │   ├── 📄 pdf_report_generator.py      # Medical reports
│   │   ├── 📄 signal_to_image.py          # Signal processing utilities
│   │   ├── 📄 simple_thesis_viz.py
│   │   ├── 📄 thesis_visualizations.py
│   │   ├── 📄 visualization_generator.py
│   │   ├── 📄 wfdb_reader.py              # WFDB format support
│   │   └── 📄 ztransform.py               # Z-domain analysis
│   │
│   ├── 📂 static/               # Frontend assets
│   │   ├── 📄 manifest.json     # PWA manifest
│   │   ├── 📄 sw.js            # Service worker
│   │   ├── 📂 css/
│   │   │   └── 📄 style.css     # Main stylesheet
│   │   ├── 📂 js/
│   │   │   ├── 📄 app.js        # Main application logic (4500+ lines)
│   │   │   └── 📄 app_*.js      # Backup versions
│   │   └── 📂 images/           # PWA icons
│   │
│   └── 📂 templates/            # Jinja2 templates
│       └── 📄 index.html        # Single-page application
│
├── 📂 tests/                    # Test suite
│   ├── 📄 conftest.py          # Test configuration
│   ├── 📄 test_ekg_analysis.py # Core functionality tests
│   ├── 📄 test_health.py       # Health check tests
│   └── 📄 test_mathematical_validation.py # Algorithm validation
│
├── 📂 generated_plots/         # Runtime generated visualizations
└── 📂 ekgsignals-*/            # Deployment versions
```

---

## 🔧 Komponente Sistema

### 1. **Frontend Layer**

#### **Tehnologije:**
- HTML5 + Jinja2 Templates
- CSS3 + Custom Design System
- Vanilla JavaScript (ES6+)
- PWA (Progressive Web App)
- Font Awesome Icons

#### **Ključne Komponente:**
```javascript
class EKGAnalyzer {
    // Main application controller
    constructor()
    init()
    setupEventListeners()
    setupDragAndDrop()
    
    // File handling
    handleFileSelect()
    displayImagePreview()
    fileToBase64()
    
    // Analysis workflow
    analyzeImage()
    displayResults()
    
    // Visualization management
    showCorrelationTest()
    showImageProcessingSteps()
}
```

#### **UI Komponente:**
- **Upload Interface**: Drag & drop, camera capture, file browser
- **Processing Animation**: Real-time progress with heartbeat loader
- **Results Dashboard**: Structured medical interpretation
- **Interactive Visualizations**: Charts, graphs, signal plots
- **Export Tools**: PDF reports, data export

### 2. **Backend Layer**

#### **Flask Application Structure:**
```python
# app/__init__.py - Factory Pattern
def create_app():
    app = Flask(__name__)
    app.register_blueprint(main)
    return app

# app/routes.py - API Controllers
@main.route('/api/analyze/complete', methods=['POST'])
@main.route('/api/analyze/fft', methods=['POST'])
@main.route('/api/analyze/arrhythmia', methods=['POST'])
@main.route('/api/visualizations/correlation-analysis', methods=['POST'])
@main.route('/api/visualizations/image-processing-steps', methods=['POST'])
```

#### **Ključni Moduli:**

**A) Image Processing Pipeline**
```python
# app/analysis/image_processing.py
def process_ekg_image(image_data, fs=250):
    # 1. Dekodiranje slike
    # 2. Grayscale konverzija
    # 3. Adaptivna binarizacija
    # 4. Grid detection & removal
    # 5. Morfološko filtriranje
    # 6. Kontura detekcija
    # 7. 1D signal ekstrakcija
    return extracted_signal
```

**B) Signal Analysis Engine**
```python
# app/analysis/advanced_ekg_analysis.py
def comprehensive_ekg_analysis(signal, fs):
    # Time domain analysis
    # Frequency domain analysis
    # Wavelet decomposition
    # HRV calculation
    # QRS morphology
    return analysis_results
```

**C) Arrhythmia Detection**
```python
# app/analysis/arrhythmia_detection.py
def classify_arrhythmias(r_peaks, signal, fs):
    # Bradycardia detection (< 60 bpm)
    # Tachycardia detection (> 100 bpm)
    # Atrial fibrillation
    # Ventricular ectopics
    return detected_arrhythmias
```

**D) Mathematical Processing**
```python
# app/analysis/fft.py
def analyze_fft(signal, fs):
    # Welch's method
    # Spectral analysis
    # Harmonic detection
    return fft_results

# app/analysis/ztransform.py
def z_transform_analysis(signal):
    # AR model fitting
    # Pole-zero analysis
    # System stability
    return z_analysis
```

---

## 🔄 Data Flow Arhitektura

### Request-Response Cycle

```
┌─────────────┐    HTTP POST     ┌─────────────┐
│   Browser   │ ──────────────► │   Flask     │
│             │                 │  Router     │
└─────────────┘                 └─────────────┘
       ▲                               │
       │                               ▼
       │                        ┌─────────────┐
       │                        │ Controller  │
       │                        │ (routes.py) │
       │                        └─────────────┘
       │                               │
       │                               ▼
       │                        ┌─────────────┐
       │                        │  Business   │
       │                        │   Logic     │
       │                        │ (analysis/) │
       │                        └─────────────┘
       │                               │
       │                               ▼
       │                        ┌─────────────┐
       │                        │ Processing  │
       │                        │  Pipeline   │
       │                        └─────────────┘
       │                               │
       │                               ▼
       │                        ┌─────────────┐
       │                        │   Results   │
       │                        │ Generation  │
       │                        └─────────────┘
       │                               │
       │         JSON Response         ▼
       └─────────────────────────────────────────
```

### Processing Pipeline Flow

```
Input Data → Validation → Processing → Analysis → Visualization → Output

├─ Image Upload
│  ├─ Base64 Decoding
│  ├─ Format Validation
│  └─ Size Verification
│
├─ Signal Extraction
│  ├─ OpenCV Processing
│  ├─ Grid Removal
│  ├─ Contour Detection
│  └─ 1D Conversion
│
├─ Signal Analysis
│  ├─ Time Domain (R-peaks, HRV, BPM)
│  ├─ Frequency Domain (FFT, PSD)
│  ├─ Z-Domain (Poles, Zeros, Stability)
│  └─ Medical Interpretation
│
├─ Arrhythmia Detection
│  ├─ Pattern Recognition
│  ├─ Classification Logic
│  └─ Medical Validation
│
└─ Results Generation
   ├─ Visualization Creation
   ├─ Report Generation
   └─ JSON Response
```

Kreiram sada ostatak dokumentacije u sledećem odgovoru...
