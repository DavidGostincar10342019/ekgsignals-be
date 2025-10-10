# EKG Analiza API

## 📚 Academic Foundation

This project implements established algorithms from peer-reviewed literature following academic integrity standards:

### Core Algorithms
- **R-peak Detection**: Pan-Tompkins algorithm (1985) [1]
- **Spectral Analysis**: Welch's method (1967) [2] 
- **AR Modeling**: Yule-Walker estimation (Kay, 1988) [3]
- **QRS Analysis**: Multi-method approach based on clinical guidelines [4,5]

### Medical Compliance
- Follows AHA/ACCF/HRS recommendations [6]
- Implements IEEE standards for biomedical signal processing
- Based on MIT-BIH database validation studies [7]

### Key References
[1] Pan & Tompkins (1985). "A real-time QRS detection algorithm." IEEE Trans Biomed Eng, 32(3), 230-236.  
[2] Welch (1967). "The use of fast Fourier transform for power spectra estimation." IEEE Trans Audio Electroacoustics, 15(2), 70-73.  
[3] Kay (1988). "Modern Spectral Estimation: Theory and Application." Prentice Hall.  
[4] Surawicz et al. (2009). "AHA/ACCF/HRS recommendations for ECG standardization." J Am Coll Cardiol, 53(11), 976-981.  
[5] Kligfield et al. (2007). "Recommendations for ECG standardization." Circulation, 115(10), 1306-1324.  
[6] Roonizi (2024). "ECG signal decomposition using Fourier analysis." EURASIP Journal, 2024, 71.  
[7] MIT-BIH Arrhythmia Database. PhysioNet.

📖 **Complete bibliography available in [REFERENCES.md](REFERENCES.md)**

---

# EKG Analiza API - Kombinacija FFT i Z-Transformacije

Kompletna Flask aplikacija za automatizovanu obradu i analizu elektrokardiograma (EKG) koja kombinuje napredne metode digitalne obrade signala, uključujući FFT spektralnu analizu i Z-transformaciju za procenu stabilnosti sistema.

## 🚀 Ključne Funkcionalnosti

### 🖼️ **Image Processing Pipeline**
- **Digitalizacija papirnih EKG zapisa** - Konverzija fotografija u 1D signale
- **Višestepeni algoritam**: Grayscale → Adaptivna binarizacija → Grid removal → Spline fitting
- **Napredna obrada**: Morfološko filtriranje, kontura detekcija, perspektiva korekcija
- **Kvalitet kontrola**: Step-by-step vizualizacija procesa

### 📊 **Signal Processing & Analysis**
- **FFT Analiza** - Spektralna analiza sa Welch metodom, dominantne frekvencije, THD kalkulacija
- **Z-Transformacija** - Pol-nula analiza, sistemska stabilnost, Butterworth filter design (0.5-40 Hz)
- **Korelacijska analiza** - Pearson korelacija, RMSE, lag compensation između originalnog i ekstraktovanog signala
- **Band-pass filtriranje** - Uklanjanje baseline drift-a i visokofrekventnog šuma

### 💓 **Cardiovascular Analysis**
- **R-peak detekcija** - Kombinovana morfološka analiza i SciPy peak detection
- **HRV parametri** - RMSSD, SDNN, pNN50, triangular index
- **Rule-based klasifikacija** - Tahikardija (>100 BPM), bradikardija (<60 BPM), nepravilan ritam
- **Arrhythmia detection** - Automatska identifikacija nepravilnosti ritma

### 🏥 **MIT-BIH Database Integration**
- **WFDB format podrška** - .hea/.dat/.atr fajlovi za standardne medicinske baze
- **Validacija performansi** - Precision/Recall/F1-score sa ±50ms tolerancijom
- **Benchmark evaluacija** - Standardizovano testiranje na MIT-BIH Arrhythmia Database
- **Reference comparison** - Poređenje sa anotiranim podacima

### 📈 **Advanced Visualizations**
- **Step-by-step analiza** - Vizualizacija svih 13 faza image processing-a
- **Batch korelacijska analiza** - Multiple signal comparison sa agregatnim statistikama
- **Interaktivni dijagrami** - Lightbox funkcionalnost za uvećavanje
- **Pol-nula dijagrami** - Z-domen analiza sa stabilnosnim indikatorima
- **Time-domain plots** - EKG signali sa anotiranim R-pikovima

### 🔧 **Technical Features**
- **REST API**: Flask-based endpoints za sve funkcionalnosti
- **Modularni dizajn**: Nezavisni moduli za image processing, signal analysis, validation
- **JSON responses**: Strukturirani rezultati pogodni za frontend integraciju
- **Error handling**: Robusno rukovanje greškama i validacija ulaza
- **Performance optimized**: Optimizovani algoritmi za brzinu i preciznost

---

## 🔗 Ključni API Endpoints

### 🖼️ **Image Processing**
```bash
POST /api/analyze_image              # Image → 1D signal conversion
POST /api/step_by_step_analysis      # Detaljni step-by-step prikaz (13 koraka)
POST /api/technical_analysis         # Tehnička analiza image processing-a
```

### 📊 **Signal Analysis**
```bash
POST /api/run_fft_analysis           # FFT spektralna analiza
POST /api/z_transform_analysis       # Z-transform pol-nula analiza
POST /api/comprehensive_analysis     # Kompletna analiza (FFT + Z + HRV)
```

### 💓 **Cardiovascular**
```bash
POST /api/arrhythmia_detection       # R-peak detekcija + klasifikacija
POST /api/correlation_analysis       # Korelacijska analiza signala
POST /api/batch_correlation          # Batch korelacijska analiza
```

### 🏥 **MIT-BIH Integration**
```bash
POST /api/analyze_wfdb               # WFDB format analiza
POST /api/mitbih_validation          # MIT-BIH performance validation
```

### 📈 **Visualizations**
```bash
POST /api/generate_time_domain_plot  # Time-domain grafikoni
POST /api/generate_fft_spectrum      # FFT spektar dijagrami
POST /api/generate_z_plane_plot      # Pol-nula dijagrami u Z-ravni
```

---

## 💻 Brza Instalacija

```bash
# Kloniranje repozitorijuma
git clone https://github.com/username/ekg-analysis-system.git
cd ekg-analysis-system

# Virtualko okruženje
python -m venv venv
source venv/bin/activate  # Linux/macOS
# ili venv\Scripts\activate  # Windows

# Instalacija
pip install -r requirements.txt

# Pokretanje
python run.sh
# Dostupno na: http://localhost:5000
```

---

## 🚀 Primeri Korišćenja

### 1. **Image Processing - EKG fotografija → digitalni signal**
```javascript
// Upload EKG slike
const formData = new FormData();
formData.append('image', file);

fetch('/api/analyze_image', {
    method: 'POST',
    body: formData
})
.then(response => response.json())
.then(data => {
    console.log('Ekstraktovani signal:', data.signal);
    console.log('Sampling rate:', data.sampling_rate);
});
```

### 2. **Korelacijska analiza - kvalitet rekonstrukcije**
```javascript
// Batch korelacijska analiza
fetch('/api/batch_correlation', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        images: ['test1.png', 'test2.png'],
        reference_signals: [signal1, signal2]
    })
})
.then(response => response.json())
.then(data => {
    console.log('Pearson r:', data.summary_statistics.mean_pearson_r);
    console.log('RMSE:', data.summary_statistics.mean_rmse);
});
```

### 3. **MIT-BIH validacija - performance evaluacija**
```javascript
// MIT-BIH dataset testing
fetch('/api/analyze_wfdb', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        record_path: 'mitbih/100',
        tolerance_ms: 50
    })
})
.then(response => response.json())
.then(data => {
    console.log('Precision:', data.validation_results.precision);
    console.log('Recall:', data.validation_results.recall);
    console.log('F1-score:', data.validation_results.f1_score);
});
```

---

## 🛠️ Tehnologije

### **Backend**
- **Python 3.8+** - Core programming language
- **Flask** - REST API framework
- **NumPy** - Numerical computations
- **SciPy** - Signal processing (FFT, filters, peak detection)
- **OpenCV** - Computer vision and image processing
- **Matplotlib** - Visualization and plotting

### **Signal Processing**
- **scipy.signal** - FFT, Welch method, Butterworth filters
- **scipy.interpolate** - Spline fitting for signal reconstruction
- **numpy.fft** - Fast Fourier Transform implementations
- **WFDB** - MIT-BIH database reader

### **Medical Analysis**
- **Pan-Tompkins algorithm** - R-peak detection
- **HRV analysis** - Heart Rate Variability metrics
- **Rule-based classification** - Arrhythmia detection
- **±50ms tolerance** - Standard MIT-BIH evaluation

### **Frontend**
- **HTML5** - Modern web interface
- **JavaScript ES6** - Client-side logic
- **CSS3** - Responsive styling
- **Lightbox functionality** - Interactive image viewing

---

---

## 📊 Rezultati i Performance

### **Image Processing Pipeline**
- ✅ **13-step algoritam** - Kompletna digitalizacija EKG slika
- ✅ **Grid removal** - Efikasno uklanjanje mreže sa papirnih zapisa
- ✅ **Spline reconstruction** - Glatka rekonstrukcija EKG traga
- ✅ **Step-by-step visualizacija** - Transparentnost procesa

### **Signal Analysis Performance**
- ✅ **FFT analiza** - Welch method sa 1024-point window, 50% overlap
- ✅ **Z-transform stabilnost** - Butterworth filter pol-nula analiza
- ✅ **Korelacijska analiza** - Pearson r ~0.7 za test slike
- ✅ **Real-time processing** - Optimizovani algoritmi za brzinu

### **MIT-BIH Validation Results**
- ✅ **±50ms tolerancija** - Standardizovana evaluacija
- ✅ **R-peak detection** - Precision/Recall/F1-score metrike
- ✅ **WFDB format** - Puna kompatibilnost sa MIT-BIH database
- ✅ **Benchmark ready** - Reproducible results

### **Key Features Implemented**
- 🔬 **Rule-based klasifikacija** (tahikardija >100 BPM, bradikardija <60 BPM)
- 📈 **Batch processing** - Multiple signal analysis
- 🖼️ **Lightbox UI** - Interactive diagram viewing
- 📊 **JSON API responses** - Strukturirani izlazni format
- 🏥 **Medical compliance** - Follows AHA/ACCF guidelines

---

## 📁 Struktura Projekta

```
ekg-analysis-system/
├── app/
│   ├── analysis/                    # Core analysis modules
│   │   ├── unified_image_processing.py     # Image → Signal pipeline
│   │   ├── fft.py                          # FFT spectral analysis
│   │   ├── ztransform.py                   # Z-transform & stability
│   │   ├── arrhythmia_detection.py         # R-peak & HRV analysis
│   │   ├── correlation_visualization.py    # Signal correlation
│   │   ├── wfdb_reader.py                  # MIT-BIH data parser
│   │   └── mitbih_validator.py             # Performance evaluation
│   ├── static/
│   │   ├── js/app.js                       # Frontend logic
│   │   ├── css/style.css                   # UI styling
│   │   └── images/                         # Test samples & icons
│   ├── templates/index.html                # Single-page application
│   ├── routes.py                           # Core API endpoints
│   ├── routes_visualizations.py            # Visualization API
│   └── main.py                             # Flask application
├── tests/                                  # Test suite
├── generated_plots/                        # Output visualizations
├── requirements.txt                        # Python dependencies
├── Projektna_dokumentacija.md              # Complete documentation
└── README.md                               # This file
```

---

## Instalacija

```bash
# Kloniranje repozitorijuma
git clone <repo-url>
cd ekg-analysis

# Instalacija zavisnosti
pip install -r requirements.txt

# Pokretanje aplikacije
python -m app.main
# ili
./run.sh
```

## API Endpoints

### GET `/api/health`
Provera zdravlja API-ja
```json
{"status": "ok"}
```

### POST `/api/analyze/image`
Konverzija EKG slike u digitalni signal
```json
{
  "image": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQ..."
}
```

### POST `/api/analyze/complete`
Kompletna analiza (slika ili signal)
```json
{
  "signal": [0.1, 0.2, 0.8, 0.3, ...],
  "fs": 250
}
```
ili
```json
{
  "image": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQ...",
  "fs": 250
}
```

### POST `/api/analyze/raw-signal`
Analiza direktno uvezenih sirovih EKG signala
```json
{
  "signal": [0.1, 0.2, 0.8, 0.3, ...],
  "fs": 250,
  "filename": "moj_ekg_signal.csv"
}
```

### POST `/api/analyze/wfdb`
Analiza WFDB formata (MIT-BIH baze)
```bash
curl -X POST /api/analyze/wfdb \
  -F "file=@record.dat" \
  -F "file=@record.hea"
```

### POST `/api/analyze/fft`
FFT analiza signala
```json
{
  "signal": [0.1, 0.2, 0.3, ...],
  "fs": 250
}
```

### POST `/api/analyze/ztransform`
Z-transformacija i analiza stabilnosti
```json
{
  "signal": [0.1, 0.2, 0.3, ...],
  "fs": 250
}
```

### POST `/api/analyze/arrhythmia`
Detekcija aritmija
```json
{
  "signal": [0.1, 0.2, 0.3, ...],
  "fs": 250
}
```

### POST `/api/filter/design`
Dizajn digitalnog filtera
```json
{
  "cutoff_frequency": 40,
  "fs": 250,
  "type": "lowpass"
}
```

## Primer Korišćenja

### 📸 Analiza EKG Slike
```python
import requests
import base64

# 1. Analiza slike
with open('ekg_slika.jpg', 'rb') as f:
    image_data = base64.b64encode(f.read()).decode()

response = requests.post('http://localhost:8000/api/analyze/complete', 
                        json={'image': f'data:image/jpeg;base64,{image_data}'})

result = response.json()

# 2. Rezultati analize
print("FFT Analiza:", result['fft_analysis'])
print("Z-Transform:", result['z_transform']['stability'])
print("Aritmije:", result['arrhythmia_detection']['arrhythmias'])
```

### 📁 Analiza Sirovih EKG Podataka
```python
import requests
import json

# 1. Učitaj signal iz fajla
with open('moj_ekg_signal.csv', 'r') as f:
    signal = [float(line.strip()) for line in f.readlines()]

# 2. Šalji na analizu
response = requests.post('http://localhost:8000/api/analyze/raw-signal', 
                        json={
                            'signal': signal,
                            'fs': 250,  # frekvencija uzorkovanja
                            'filename': 'moj_ekg_signal.csv'
                        })

result = response.json()

# 3. Rezultati analize
print("Srčana frekvencija:", result['arrhythmia_detection']['heart_rate'])
print("R-pikovi:", len(result['arrhythmia_detection']['r_peaks']))
print("Aritmije:", result['arrhythmia_detection']['arrhythmias'])
```

### 📋 Podržani formati sirovih signala

**CSV/TXT format:**
```
0.1
0.12
0.11
0.13
...
```

**JSON format:**
```json
{
  "signal": [0.1, 0.12, 0.11, 0.13, ...],
  "fs": 250,
  "metadata": {
    "description": "EKG zapis pacijenta",
    "duration_seconds": 10
  }
}
```

**WFDB format (MIT-BIH):**
```
111.hea  - Header fajl sa metapodacima
111.dat  - Binarni signal podataci
111.atr  - Annotations (opciono)
```

### 🏥 Analiza WFDB signala
```bash
# Download MIT-BIH record
wget https://physionet.org/files/mitdb/1.0.0/111.dat
wget https://physionet.org/files/mitdb/1.0.0/111.hea

# Analiziraj u aplikaciji - odaberi oba fajla odjednom
```

## Struktura Projekta

```
app/
├── __init__.py          # Flask aplikacija
├── main.py              # Entry point
├── routes.py            # API rute
└── analysis/
    ├── fft.py           # FFT analiza
    ├── ztransform.py    # Z-transformacija
    ├── image_processing.py  # Obrada slike
    └── arrhythmia_detection.py  # Detekcija aritmija

tests/
├── test_health.py       # Osnovni testovi
└── test_ekg_analysis.py # Testovi EKG analize
```

## Tehnologije

- **Backend**: Python/Flask
- **Obrada Slike**: OpenCV, Pillow
- **Analiza Signala**: NumPy, SciPy
- **Vizualizacija**: Matplotlib
- **Testiranje**: pytest

## Medicinski Disclaimer

⚠️ **VAŽNO**: Ovaj sistem je namenjen isključivo za edukativne svrhe i preliminarnu analizu. 
NE koristi za medicinsku dijagnostiku bez konsultacije sa kvalifikovanim lekarom.

## Razvoj i Testiranje

```bash
# Pokretanje testova
pytest tests/

# Pokretanje sa debug modom
python -m app.main
```

## Buduće Funkcionalnosti

- [ ] Napredna detekcija aritmija (AFib, VT, VF)
- [ ] Machine Learning klasifikacija
- [ ] Real-time analiza
- [ ] Mobilna aplikacija
- [ ] Izvoz rezultata u PDF
- [ ] Baza podataka za čuvanje analiza
- [ ] Batch obrada više signala
- [ ] Statistički izvештaji

## Licenca

MIT License - videti LICENSE fajl za detalje.