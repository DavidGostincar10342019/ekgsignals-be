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

# EKG Analiza API

Softverski sistem za analizu EKG signala iz fotografija mobilnim telefonom. Omogućava konverziju vizuelnog EKG zapisa u digitalni signal i automatsku detekciju potencijalnih aritmija.

## Funkcionalnosti

### 🖼️ Obrada Slike
- Konverzija EKG fotografije u digitalni signal
- OpenCV i Pillow za obradu slike
- Adaptivni thresholding i detekcija kontura
- Ekstrakcija 1D signala amplituda

### 📁 Uvoz Sirovih Signala
- **Direktni uvoz**: CSV, TXT, JSON fajlovi sa EKG podacima
- **WFDB format**: MIT-BIH baze podataka (.dat + .hea fajlovi)
- **Fleksibilni formati**: Brojevi odvojeni zarezom, novim redom ili spacom
- **JSON podrška**: Strukturisani podaci sa metapodacima
- **Validacija**: Automatska provera kvaliteta i validnosti signala

### 📊 Analiza Signala
- **FFT Analiza**: Frekvencijska analiza signala
- **Z-Transformacija**: Analiza polova, nultih tačaka i stabilnosti
- **Filtriranje**: Dizajn digitalnih filtara za uklanjanje šuma
- **Detekcija Aritmija**: Automatska detekcija nepravilnosti u ritmu

### 🏥 Medicinska Analiza
- Detekcija R-pikova
- Analiza srčane frekvencije (BPM)
- Heart Rate Variability (HRV)
- Klasifikacija aritmija (bradikardija, tahikardija, nepravilan ritam)

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