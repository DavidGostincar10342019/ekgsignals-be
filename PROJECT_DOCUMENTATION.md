# 📊 EKG Analiza - Mobilna Web Aplikacija

## 📋 Pregled Projekta

**EKG Analiza** je napredna mobilna web aplikacija koja omogućava upload fotografija EKG signala i njihovu automatsku analizu koristeći naučne algoritme iz biomedicinskog inženjerstva. Aplikacija kombinuje digitalizaciju slika sa spektralnom analizom signala za detekciju aritmija i procenu zdravlja srca.

### 🎯 Ključne Funkcionalnosti

- **📱 Mobilna optimizacija** - Responsive design za telefone i tablete
- **📷 Camera capture** - Direktno fotografisanje EKG papira
- **🖼️ Image upload** - Import postojećih EKG slika
- **🔍 Inteligentna validacija** - Automatska provera da li je slika stvarno EKG
- **🧮 Napredna analiza** - Implementacija algoritma iz naučnih radova
- **📚 Edukativna komponenta** - Objašnjenja algoritma i rezultata
- **⚡ Real-time processing** - Brza analiza sa progress bar-om

---

## 🏗️ Arhitektura Sistema

### Frontend (Client-Side)
```
HTML5 + CSS3 + Vanilla JavaScript
├── Responsive UI optimizovan za mobilne uređaje
├── PWA funkcionalnost (Add to Home Screen)
├── File upload sa drag & drop podrškom
├── Real-time progress tracking
├── Interactive modals sa edukativnim sadržajem
└── Error handling sa user-friendly porukama
```

### Backend (Server-Side)
```
Python 3.8+ + Flask Framework
├── REST API sa 9 endpoint-a
├── OpenCV za obradu slika
├── NumPy/SciPy za numeričke operacije
├── Matplotlib za vizualizacije (Agg backend)
├── Modularni dizajn sa odvojenim analizama
└── Comprehensive error handling i logging
```

### Data Flow
```
Slika → Base64 → HTTP POST → Validacija → OpenCV → 
Signal Extraction → Preprocessing → Analysis → JSON Response
```

---

## 📁 Struktura Projekta

```
biosignals-be/
├── app/
│   ├── __init__.py                 # Flask aplikacija setup
│   ├── main.py                     # Entry point
│   ├── routes.py                   # API endpoints (9 ruta)
│   ├── analysis/                   # Analitički moduli
│   │   ├── __init__.py
│   │   ├── fft.py                  # FFT frekvencijska analiza
│   │   ├── ztransform.py           # Z-transformacija i stabilnost
│   │   ├── image_processing.py     # OpenCV obrada slika
│   │   ├── arrhythmia_detection.py # Detekcija aritmija i HRV
│   │   ├── advanced_ekg_analysis.py # Napredni algoritmi
│   │   └── educational_visualization.py # Edukativne vizualizacije
│   ├── static/                     # Frontend assets
│   │   ├── css/
│   │   │   └── style.css          # Responsive CSS (1000+ linija)
│   │   ├── js/
│   │   │   └── app.js             # JavaScript logika (500+ linija)
│   │   ├── images/                # PWA ikone
│   │   ├── manifest.json          # PWA manifest
│   │   └── sw.js                  # Service Worker
│   └── templates/
│       └── index.html             # Glavna HTML stranica
├── tests/                         # Test suite
│   ├── conftest.py
│   ├── test_health.py
│   └── test_ekg_analysis.py
├── requirements.txt               # Python zavisnosti
├── wsgi.py                       # WSGI konfiguracija
├── pythonanywhere_setup.md       # Deployment guide
├── DEPLOYMENT_GUIDE.md           # Detaljno deployment uputstvo
├── DATA_FLOW_EXPLANATION.md      # Objašnjenje toka podataka
├── Master_Rad_David_Gostincar.md # Kompletni master rad
└── README.md                     # Osnovna dokumentacija
```

---

## 🔬 Implementirani Naučni Algoritmi

### 1. Spatial Filling Index (SFI)
**Izvor:** Faust, O., Acharya, U. R., & Adeli, H. (2004)

```python
SFI = log(N) / log(L/a)
```

**Parametri:**
- `N` - broj tačaka signala
- `L` - ukupna dužina putanje signala
- `a` - prosečna amplituda signala

**Interpretacija:**
- SFI < 1.0: Jednostavan signal, mogući artefakt
- 1.0 ≤ SFI < 1.3: Normalna kompleksnost
- SFI ≥ 1.3: Visoka kompleksnost, mogući patološki signal

### 2. Time-Frequency Analiza (STFT)
**Izvor:** Proakis, J. G., & Manolakis, D. G. (2007)

```python
STFT(n,k) = Σ x[m]w[n-m]e^(-j2πkm/N)
```

**Funkcionalnost:**
- Kratko-vremenska Furijeova transformacija
- Spektralna entropija za kompleksnost
- Dominantne frekvencije kroz vreme

### 3. Z-Transformacija i Analiza Stabilnosti
**Izvor:** Proakis & Manolakis (2007)

```python
X(z) = Σ x[n]z^(-n)
H(z) = B(z)/A(z)
```

**Analiza:**
- Autoregresivni (AR) model signala
- Polovi i nule u z-ravni
- Stabilnost sistema (polovi unutar jediničnog kruga)

### 4. Wavelet Dekompozicija
**Izvor:** Yıldırım, Ö. (2018)

```python
WT(a,b) = (1/√a) ∫ x(t)ψ*((t-b)/a)dt
```

**Implementacija:**
- Simplified wavelet analiza (bez PyWavelets zavisnosti)
- Kaskadni filtri za simulaciju wavelet dekompozicije
- Wavelet entropija za karakterizaciju signala

### 5. Napredni Digitalni Filtri
**Izvor:** Sörnmo, L., & Laguna, P. (2005)

**Filter kaskada:**
1. High-pass (0.5 Hz) - baseline wander removal
2. Notch (50 Hz) - power line interference
3. Low-pass (40 Hz) - EMG noise removal
4. Adaptive Wiener filter - residual noise

---

## 🌐 API Dokumentacija

### Base URL
```
http://localhost:8000/api
```

### Endpoints

#### 1. `GET /health`
**Opis:** Health check endpoint
**Response:**
```json
{
  "status": "ok"
}
```

#### 2. `POST /analyze/complete`
**Opis:** Kompletna analiza EKG signala (osnovna + napredna)
**Request:**
```json
{
  "image": "data:image/png;base64,iVBORw0KGgoAAAA...",
  "fs": 250
}
```
**Response:**
```json
{
  "signal_info": {
    "length": 2500,
    "duration_seconds": 10.0,
    "sampling_frequency": 250
  },
  "fft_analysis": {
    "peak_frequency_hz": 1.2,
    "peak_amplitude": 0.85,
    "frequencies": [...],
    "spectrum": [...]
  },
  "arrhythmia_detection": {
    "heart_rate": {
      "average_bpm": 72.5,
      "min_bpm": 68.2,
      "max_bpm": 76.8,
      "heart_rate_variability": 45.2
    },
    "arrhythmias": {
      "detected": [],
      "overall_assessment": "Normalan ritam"
    },
    "r_peaks": [125, 375, 625, 875, 1125],
    "signal_quality": {
      "quality": "Dobar",
      "snr_db": 18.5
    }
  },
  "z_transform": {
    "poles": [{"real": 0.85, "imag": 0.12}],
    "zeros": [],
    "stability": {
      "stable": true,
      "message": "Sistem je stabilan"
    }
  },
  "advanced_analysis": {
    "spatial_filling_index": {
      "spatial_filling_index": 1.15,
      "interpretation": "Normalna kompleksnost"
    },
    "time_frequency_analysis": {
      "mean_spectral_entropy": 2.34
    },
    "wavelet_analysis": {
      "wavelet_entropy": 2.67
    }
  }
}
```

#### 3. `POST /analyze/educational`
**Opis:** Detaljana edukativna analiza sa vizualizacijama
**Request:** Isti kao `/analyze/complete`
**Response:**
```json
{
  "analysis_steps": [
    {
      "step": 1,
      "title": "Učitavanje i predobrada signala",
      "description": "Signal je učitan i pripremljen za analizu...",
      "formula": "x_clean[n] = HPF(LPF(x[n]))",
      "result": "Signal spreman za analizu"
    }
  ],
  "educational_visualization": "base64_encoded_image",
  "detailed_results": { /* kompletni rezultati */ }
}
```

#### 4. `POST /analyze/image`
**Opis:** Samo digitalizacija EKG slike u signal
**Request:**
```json
{
  "image": "data:image/png;base64,..."
}
```

#### 5. `POST /analyze/fft`
**Opis:** Samo FFT analiza signala
**Request:**
```json
{
  "signal": [0.1, 0.2, 0.8, ...],
  "fs": 250
}
```

#### 6. `POST /analyze/ztransform`
**Opis:** Samo Z-transformacija signala

#### 7. `POST /analyze/arrhythmia`
**Opis:** Samo detekcija aritmija

#### 8. `POST /filter/design`
**Opis:** Dizajn digitalnog filtera

#### 9. `GET /info`
**Opis:** Informacije o API-ju i dostupnim endpoint-ima

---

## 🔍 Validacija EKG Slika

### Algoritam Validacije

```python
def validate_ekg_image(img):
    # 1. Format validacija (landscape)
    # 2. Kontrast analiza (min 20)
    # 3. Line density (0.5% - 50%)
    # 4. Grid detekcija (horizontalne + vertikalne linije)
    # 5. Signal kontinuitet
    # 6. Horizontal coverage (min 30%)
    # 7. Signal variability (R-pikovi)
    
    return {
        "is_valid": True/False,
        "reason": "Objašnjenje",
        "confidence": 0-100
    }
```

### Kriterijumi Prihvatanja

✅ **Prihvaćene slike:**
- EKG papir sa grid-om
- Jasne EKG krivulje
- Landscape format
- Dobar kontrast (>20)
- Horizontalna pokrivenost >30%

❌ **Odbačene slike:**
- Obične fotografije
- Čisto obojene slike
- Portrait format
- Slab kontrast (<20)
- Bez grid-a ili signala

---

## 🎨 Frontend Funkcionalnosti

### Responsive Design
- **Mobile-first** pristup
- **Touch-friendly** interface
- **PWA** podrška (Add to Home Screen)
- **Offline** funkcionalnost sa Service Worker

### User Experience
- **Progress bar** sa real-time updates
- **Drag & drop** upload
- **Camera capture** direktno sa telefona
- **Error handling** sa jasnim porukama
- **Info modals** sa edukativnim sadržajem

### Edukativna Komponenta
- **Info dugmad (i)** za svaku sekciju
- **Step-by-step** objašnjenja algoritma
- **Vizuelni primeri** EKG slika
- **Matematičke formule** sa interpretacijom
- **Klinički značaj** rezultata

---

## 🔒 Bezbednost i Privacy

### Data Handling
- **Slike se NE čuvaju** na serveru
- **In-memory processing** - sve u RAM-u
- **Automatsko brisanje** nakon analize
- **Nema baze podataka** za korisničke podatke

### Validacija
- **File type** validacija (samo slike)
- **Size limit** (maksimalno 10MB)
- **Content validation** (samo EKG slike)
- **Input sanitization** za sve API pozive

### Error Handling
- **Graceful failure** - aplikacija ne krahira
- **User-friendly** poruke greške
- **Debug informacije** za development
- **Fallback** vrednosti za edge cases

---

## 🚀 Deployment

### Lokalno Pokretanje
```bash
# Kloniranje repozitorijuma
git clone <repo-url>
cd biosignals-be

# Kreiranje virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ili
.venv\Scripts\activate     # Windows

# Instalacija zavisnosti
pip install -r requirements.txt

# Pokretanje aplikacije
python -m app.main
```

### PythonAnywhere Deployment
1. **Upload koda** na PythonAnywhere
2. **Instalacija zavisnosti** u konzoli
3. **Web app konfiguracija** (Manual, Python 3.10)
4. **WSGI setup** sa `wsgi.py` fajlom
5. **Static files** mapping za `/static/`

**Detaljno uputstvo:** `pythonanywhere_setup.md`

---

## 🧪 Testiranje

### Test Suite
```bash
# Pokretanje svih testova
pytest tests/

# Pokretanje specifičnog testa
pytest tests/test_ekg_analysis.py -v

# Test coverage
pytest --cov=app tests/
```

### Test Kategorije
- **Unit testovi** - pojedinačne funkcije
- **Integration testovi** - API endpoint-i
- **Validation testovi** - EKG slika validacija
- **Performance testovi** - brzina obrade

### Manual Testing
- **Browser testiranje** - različiti browseri
- **Mobile testiranje** - telefoni i tableti
- **Network testiranje** - spore konekcije
- **Error testiranje** - edge cases

---

## 📊 Performance Metrije

### Brzina Obrade
- **Image validation:** ~0.5s
- **Signal extraction:** ~1.0s
- **Complete analysis:** ~2-3s
- **Educational analysis:** ~4-5s

### Memorijska Potrošnja
- **Base aplikacija:** ~50MB RAM
- **Per request:** ~10-20MB dodatno
- **Peak usage:** ~100MB za velike slike
- **Garbage collection:** Automatsko oslobađanje

### Supported Formats
- **Image formats:** PNG, JPEG, WEBP
- **Max file size:** 10MB
- **Min resolution:** 400x300px
- **Max resolution:** 4000x3000px

---

## 🔧 Konfiguracija

### Environment Variables
```bash
FLASK_ENV=development          # development/production
FLASK_DEBUG=True              # True/False
SECRET_KEY=your-secret-key    # Za session security
PORT=8000                     # Server port
```

### Dependencies
```
Flask==3.1.0                 # Web framework
opencv-python==4.10.0.84     # Image processing
numpy==2.1.3                 # Numerical operations
scipy==1.14.1                # Scientific computing
matplotlib==3.9.2            # Plotting (Agg backend)
Pillow==11.3.0               # Image handling
PyWavelets==1.4.1            # Wavelet transforms (optional)
requests==2.32.3             # HTTP client (testing)
pytest==8.3.4               # Testing framework
```

---

## 📚 Edukativni Sadržaj

### Info Modals
1. **Koraci Naučne Analize** - Step-by-step proces
2. **Matematičke Formule** - Formule sa interpretacijom
3. **Edukativna Vizualizacija** - Kako čitati dijagrame
4. **Napredni Rezultati** - Klinički značaj
5. **EKG Primer Guide** - Kako fotografisati EKG

### Vizualizacije
- **SVG EKG simulacija** - Interaktivni primer
- **Progress animacije** - Real-time feedback
- **Color-coded rezultati** - Intuitivno razumevanje
- **Responsive charts** - Mobilno optimizovano

---

## 🐛 Troubleshooting

### Česte Greške

#### 1. "OpenCV nije dostupan"
```bash
pip install opencv-python
```

#### 2. "Matplotlib GUI greška"
- **Uzrok:** Pokušaj kreiranja GUI van main thread-a
- **Rešenje:** `matplotlib.use('Agg')` u kodu

#### 3. "JSON serialization greška"
- **Uzrok:** NumPy tipovi u JSON response
- **Rešenje:** Eksplicitna konverzija u Python tipove

#### 4. "Port 5000 zauzet"
```bash
# Promena porta u main.py
app.run(debug=True, port=8000)
```

#### 5. "Slika nije prihvaćena"
- **Uzrok:** Previše striktna validacija
- **Rešenje:** Adjustovanje parametara u `validate_ekg_image()`

### Debug Mode
```python
# Aktiviranje debug poruka
print(f"DEBUG: {variable}")
import traceback
traceback.print_exc()
```

---

## 🔮 Buduće Funkcionalnosti

### Kratkoročno (1-3 meseca)
- [ ] **Machine Learning** klasifikacija aritmija
- [ ] **Real-time monitoring** za kontinuirane signale
- [ ] **PDF export** rezultata analize
- [ ] **Multi-language** podrška (EN, DE, FR)

### Srednjoročno (3-6 meseci)
- [ ] **12-lead EKG** analiza
- [ ] **Cloud storage** integracija
- [ ] **User accounts** i istorija analiza
- [ ] **Telemedicina** funkcionalnosti

### Dugoročno (6+ meseci)
- [ ] **Mobile app** (React Native/Flutter)
- [ ] **AI-powered** dijagnostika
- [ ] **Integration** sa medicinskim sistemima
- [ ] **Clinical validation** studije

---

## 👥 Tim i Kontakt

### Razvoj
- **Developer:** David Gostinčar
- **Mentor:** [Ime mentora]
- **Institucija:** Mašinski fakultet, Univerzitet u Beogradu

### Tehnička Podrška
- **GitHub:** [Repository URL]
- **Email:** [kontakt email]
- **Dokumentacija:** Ovaj fajl + inline komentari

### Licenca
- **MIT License** - Open source
- **Edukativna upotreba** dozvoljena
- **Komercijalna upotreba** uz dozvolu

---

## 📖 Reference

### Naučni Radovi
1. Faust, O., Acharya, U. R., & Adeli, H. (2004). Analysis of cardiac signals using spatial filling index and time–frequency domain.
2. Proakis, J. G., & Manolakis, D. G. (2007). Digital Signal Processing: Principles, Algorithms, and Applications.
3. Sörnmo, L., & Laguna, P. (2005). Electrocardiogram Signal Processing.
4. Yıldırım, Ö. (2018). A novel wavelet sequence based on deep bidirectional LSTM network model for ECG signal classification.

### Tehnička Dokumentacija
- **Flask:** https://flask.palletsprojects.com/
- **OpenCV:** https://docs.opencv.org/
- **NumPy:** https://numpy.org/doc/
- **SciPy:** https://docs.scipy.org/

---

## ⚠️ Medicinski Disclaimer

**VAŽNO UPOZORENJE:** Ova aplikacija je razvijena isključivo u edukativne i istraživačke svrhe. Rezultati analize **NE SMEJU** biti korišćeni za:

- Medicinsku dijagnostiku
- Donošenje kliničkih odluka  
- Zamenu profesionalne medicinske konsultacije
- Tretman pacijenata

Za sve medicinske potrebe, obratite se kvalifikovanom lekaru ili kardiologu.

---

*Poslednje ažuriranje: Septembar 2025*
*Verzija dokumentacije: 1.0*