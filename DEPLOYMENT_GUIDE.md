# 📱 EKG Analiza - Mobilna Web Aplikacija

## 🚀 Kompletna implementacija

### ✅ Implementirane funkcionalnosti:

#### 📱 **Frontend (Mobilna Web Aplikacija)**
- **Responsive design** optimizovan za mobilne telefone
- **Camera capture** - direktno fotografisanje EKG-a
- **File upload** - import iz galerije telefona
- **Drag & Drop** podrška za desktop
- **Real-time animacije** tokom obrade
- **PWA funkcionalnost** (Add to Home Screen)
- **Offline podrška** sa Service Worker
- **Touch-friendly interface** sa velikim dugmadima

#### 🔬 **Backend API**
- **8 REST endpoint-a** za kompletnu funkcionalnost
- **OpenCV obrada slike** - konverzija EKG fotografije u signal
- **FFT analiza** - frekvencijska dekompozicija
- **Z-transformacija** - analiza stabilnosti sistema
- **R-pik detekcija** - automatsko pronalaženje otkucaja
- **Klasifikacija aritmija** - bradikardija, tahikardija, nepravilan ritam
- **Signal quality assessment** - procena kvaliteta signala

#### 🏥 **Medicinska analiza**
- **Heart Rate Variability (HRV)** kalkulacija
- **BPM analiza** sa min/max vrednostima
- **Aritmija detekcija** sa objašnjenjima
- **Signal-to-Noise Ratio** procena
- **Medicinski disclaimer** za bezbednost

## 📲 Kako koristiti aplikaciju:

### 1. **Fotografisanje EKG-a**
- Otvorite aplikaciju na telefonu
- Kliknite "Fotografiši EKG"
- Usmerite kameru na EKG zapis
- Fotografišite jasno i stabilno

### 2. **Upload iz galerije**
- Kliknite "Odaberi iz galerije"
- Odaberite EKG sliku
- Podržani formati: JPG, PNG, WEBP

### 3. **Analiza**
- Kliknite "Analiziraj EKG"
- Pratite animaciju obrade (6 koraka)
- Pregledajte detaljne rezultate

## 🌐 PythonAnywhere Deployment

### Korak 1: Priprema
```bash
# Na PythonAnywhere Bash konzoli
git clone https://github.com/your-repo/ekg-analiza.git
cd ekg-analiza
pip3.10 install --user -r requirements.txt
```

### Korak 2: Web App konfiguracija
1. **Web tab** → "Add a new web app"
2. **Manual configuration** → Python 3.10
3. **Source code**: `/home/yourusername/ekg-analiza`
4. **WSGI file** edituj:

```python
import sys
import os

path = '/home/yourusername/ekg-analiza'
if path not in sys.path:
    sys.path.append(path)

from app import create_app
application = create_app()
```

### Korak 3: Static files
- **URL**: `/static/`
- **Directory**: `/home/yourusername/ekg-analiza/app/static/`

### Korak 4: Reload
Kliknite "Reload" dugme.

**Vaša aplikacija**: `https://yourusername.pythonanywhere.com`

## 📱 PWA instalacija na telefon

### Android:
1. Otvorite aplikaciju u Chrome
2. Menu → "Add to Home screen"
3. Aplikacija će raditi kao native app

### iOS:
1. Otvorite u Safari
2. Share button → "Add to Home Screen"
3. Aplikacija će biti dostupna sa home screen-a

## 🔧 Tehnički detalji

### Frontend stack:
- **HTML5** sa semantic markup
- **CSS3** sa flexbox/grid layout
- **Vanilla JavaScript** (bez framework-a)
- **PWA** sa Service Worker
- **Font Awesome** ikone

### Backend stack:
- **Python 3.10+**
- **Flask** web framework
- **OpenCV** za obradu slike
- **NumPy/SciPy** za signal processing
- **Matplotlib** za vizualizacije

### API Endpoints:
```
GET  /                     - Glavna stranica
GET  /api/health          - Health check
POST /api/analyze/image   - Obrada slike
POST /api/analyze/complete - Kompletna analiza
POST /api/analyze/fft     - FFT analiza
POST /api/analyze/ztransform - Z-transformacija
POST /api/analyze/arrhythmia - Detekcija aritmija
POST /api/filter/design   - Dizajn filtara
GET  /api/info           - API dokumentacija
```

## 🧪 Testiranje

### Lokalno testiranje:
```bash
python -m app.main
# Otvorite http://localhost:5000
```

### Mobilno testiranje:
1. **Chrome DevTools** → Device Toolbar
2. Odaberite mobilni uređaj
3. Testirajte touch interakcije

### API testiranje:
```bash
pytest tests/
python example_usage.py
```

## 🔒 Bezbednost

### Validacija:
- **File type** validacija (samo slike)
- **File size** limit (10MB)
- **Input sanitization** za API
- **Error handling** sa user-friendly porukama

### Privacy:
- **Slike se ne čuvaju** na serveru
- **Lokalna obrada** podataka
- **HTTPS** za production (PythonAnywhere)

## 📈 Performance optimizacija

### Frontend:
- **Lazy loading** slika
- **Minified CSS/JS** za production
- **Service Worker caching**
- **Optimized images**

### Backend:
- **Efficient algorithms** za signal processing
- **Memory management** za velike slike
- **Error recovery** za robusnost

## 🚨 Medicinski disclaimer

⚠️ **VAŽNO**: Aplikacija je namenjena isključivo za:
- **Edukativne svrhe**
- **Preliminarnu analizu**
- **Demonstraciju tehnologije**

**NE koristiti za**:
- Medicinsku dijagnostiku
- Kliničke odluke
- Zamenu za lekarsku konsultaciju

## 📞 Podrška

Za tehničku podršku ili pitanja:
- Proverite logs u PythonAnywhere
- Testirajte lokalno za debugging
- Proverite browser konzolu za frontend greške

## 🎯 Buduće funkcionalnosti

- [ ] **Machine Learning** klasifikacija
- [ ] **Real-time monitoring** 
- [ ] **PDF izvoz** rezultata
- [ ] **Multi-language** podrška
- [ ] **Cloud storage** integracija
- [ ] **Telemedicina** funkcionalnosti