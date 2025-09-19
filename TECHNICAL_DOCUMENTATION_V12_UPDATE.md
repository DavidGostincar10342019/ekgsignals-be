# 📚 TEHNIČKA DOKUMENTACIJA - VERZIJA 12 UPDATE

## 🎯 Najnovije Implementirane Funkcionalnosti

### 1. Dugme "i" sa Objašnjenjima Dijagrama

**Funkcionalnost:** Dodano dugme "i" pored svakog od 4 dijagrama master rada sa specifičnim objašnjenjima.

**Implementacija:**
- **Fajl:** `app/static/js/app.js`
- **Funkcija:** `addThesisVisualizations()` - proširena sa dugmetom "i"
- **Nova funkcija:** `getVisualizationExplanation(key, viz)` - generiše objašnjenja

**Objekti dijagrama:**
1. **Dijagram 1:** EKG signal sa R-pikovima
2. **Dijagram 2:** FFT spektar (Furijeova transformacija)  
3. **Dijagram 3:** MIT-BIH poređenje
4. **Dijagram 4:** Z-transformacija pipeline

**Kod struktura:**
```javascript
// Dugme "i" sa onclick event
<button class="info-btn" 
        style="position: absolute; right: 10px; top: 50%; ...">i</button>

// Panel sa objašnjenjem
<div class="explanation-panel" style="display: none; ...">
    <h4>Objašnjenje dijagrama</h4>
    <p>${explanation}</p>
</div>
```

### 2. Dinamička Klinička Analiza na Osnovu Tipa Podataka

**Problem rešen:** Uklonjena neprecizna "Sistematska EKG Analiza" za analizu slika, dodana precizna analiza za sirove podatke.

**Tri tipa analize:**

#### A) **Analiza Slika** → `addBasicEKGInfo()`
- ⚠️ Ograničena analiza sa upozorenjem
- Samo osnovni parametri (frekvencija, ritam)
- Jasno upozorenje o ograničenjima

#### B) **WFDB (.dat/.hea/.atr)** → `addAdvancedClinicalAnalysis()`
- ✅ **MIT-BIH Klinička Analiza**
- Precizni klinički parametri
- Ekspertske anotacije
- Medicinski relevantni rezultati

#### C) **Sirovi Podatci (CSV/JSON)** → `addAdvancedClinicalAnalysis()`
- 🔬 **Napredna EKG Analiza**
- Pouzdani parametri za kliničku procenu

### 3. Klinički Parametri - Implementacija

**Dinamički parametri umesto fiksnih:**

```javascript
// Rate analiza
let rateText = `${Math.round(avgBpm)} bpm`;
let rateRange = `${Math.round(minBpm)}-${Math.round(maxBpm)} bpm`;

// Rhythm analiza na osnovu aritmija
if (arrhythmias.length > 0) {
    const afib = arrhythmias.find(arr => 
        arr.type?.toLowerCase().includes('fibrilacija'));
    if (afib) {
        rhythmText = "Irregularly irregular";
        rhythmDetails = "Atrijska fibrilacija";
    }
}

// P-wave analiza
if (afib) {
    pWaveText = "Absent/fibrillatory waves";
    pWaveDetails = "Fibrilatorni talasi";
}

// QRS analiza
if (qrsAnalysis && qrsAnalysis.mean_width_ms) {
    const qrsWidth = qrsAnalysis.mean_width_ms;
    if (qrsWidth > 120) {
        qrsText = `Wide (${qrsWidth.toFixed(0)}ms)`;
    }
}
```

### 4. Sistematski Pregled Format

**Implementirani parametri (identični sa zahtevom):**
- **Rate:** Dinamički izračunato na osnovu analize
- **Rhythm:** Regular/Irregular/Irregularly irregular  
- **Axis:** Normal (statički)
- **PR/P wave:** Dinamički na osnovu aritmija
- **QRS:** Narrow/Wide sa ms vrednostima
- **ST/T wave:** Normal (statički) 
- **QTc/other:** Normal (statički)

### 5. Pozivanje Funkcija - Flow Diagram

```
displayResults(data) 
├── image_analysis → addBasicEKGInfo(data)
└── wfdb_import/raw_import → addAdvancedClinicalAnalysis(data)

displayWFDBResults(data)
└── addAdvancedClinicalAnalysis(data)  // NOVO DODANO

displayRawSignalResults(data) 
└── addAdvancedClinicalAnalysis(data)
```

### 6. Objašnjenja Dijagrama - Sadržaj

**Dijagram 1 - EKG Signal sa R-pikovima:**
> "Ovaj dijagram prikazuje EKG signal u vremenskom domenu sa detektovanim R-pikovima (označeni crvenim krugovima). R-pikovi predstavljaju električni impuls koji pokreće kontrakciju srčanih komora..."

**Dijagram 2 - FFT Spektar:**
> "FFT (Fast Fourier Transform) spektar pokazuje frekvencijski sadržaj EKG signala. Dominantna frekvencija odgovara osnovnoj srčanoj frekvenciji..."

**Dijagram 3 - MIT-BIH Poređenje:**
> "Ovaj dijagram poredi automatski detektovane R-pikove (crveno) sa ekspertskim MIT-BIH anotacijama (zeleno). MIT-BIH baza podataka predstavlja 'zlatni standard'..."

**Dijagram 4 - Z-transformacija Pipeline:**
> "Signal processing pipeline prikazuje korake obrade EKG signala korišćenjem Z-transformacije: originalni signal, bandpass filtriranje, baseline removal..."

### 7. CSS Stilovi za Nova Dugmad

```css
.info-btn {
    position: absolute;
    right: 10px;
    top: 50%;
    transform: translateY(-50%);
    background: #007bff;
    color: white;
    border: none;
    border-radius: 50%;
    width: 25px;
    height: 25px;
    cursor: pointer;
    font-size: 14px;
    font-weight: bold;
    transition: all 0.3s ease;
}

.explanation-panel {
    display: none;
    background: #e7f3ff;
    padding: 15px;
    margin: 10px 0;
    border-left: 4px solid #007bff;
    border-radius: 5px;
}
```

### 8. Event Handling - Dugme "i"

```javascript
// Event listener za info dugmad
document.addEventListener('click', (e) => {
    if (e.target && e.target.classList.contains('info-btn')) {
        const panel = e.target.closest('.result-card')
                             .querySelector('.explanation-panel');
        if (panel) {
            panel.style.display = panel.style.display === 'none' 
                                 ? 'block' : 'none';
        }
    }
});
```

### 9. Medicinska Sigurnost

**Implementirane mere:**
- Jasno razlikovanje između analize slika i sirovih podataka
- Upozoenja o ograničenjima analize slika
- Napomene o medicinskoj relevantnosti
- Preporuke za konsultaciju sa lekarom

### 10. Kompatibilnost

**Podržani formati:**
- **Slike:** JPG, PNG (osnovna analiza)
- **WFDB:** .dat, .hea, .atr (napredna analiza)
- **Sirovi:** CSV, TXT, JSON (napredna analiza)

---

## 🔧 Ključne Izmene u Kodu

### Funkcije Dodane/Modifikovane:

1. **`getVisualizationExplanation(key, viz)`** - NOVA
2. **`addAdvancedClinicalAnalysis(data)`** - NOVA  
3. **`generateAdvancedClinicalHTML(data)`** - NOVA
4. **`addBasicEKGInfo(data)`** - NOVA
5. **`addThesisVisualizations()`** - MODIFIKOVANA
6. **`displayWFDBResults()`** - MODIFIKOVANA

### Fajlovi Izmenjeni:
- `app/static/js/app.js` - Glavne funkcionalnosti
- Event handling za dugmad
- CSS stilovi integrisani u HTML

---

## 📊 Tehnički Dijagram - Novi Flow

```
EKG Analiza Input
    ↓
┌─────────────────┐
│   Tip Podataka  │
└─────────────────┘
    ↓
┌─────────┬─────────────┬─────────────┐
│  Slika  │  WFDB Files │ Raw Signal  │
└─────────┴─────────────┴─────────────┘
    ↓           ↓             ↓
┌─────────┐ ┌─────────┐ ┌─────────────┐
│ Basic   │ │Advanced │ │ Advanced    │
│ EKG     │ │Clinical │ │ Clinical    │
│ Info    │ │Analysis │ │ Analysis    │
└─────────┘ └─────────┘ └─────────────┘
    ↓           ↓             ↓
┌─────────┐ ┌─────────┐ ┌─────────────┐
│Warning  │ │MIT-BIH  │ │ Raw Data    │
│Limited  │ │Precise  │ │ Reliable    │
│Analysis │ │Analysis │ │ Analysis    │
└─────────┘ └─────────┘ └─────────────┘
```

---

*Dokumentacija ažurirana: Decembar 2024*  
*Verzija aplikacije: 12*  
*Autor: David Gostinčar - Master Rad*