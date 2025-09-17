# 🔄 EKG Aplikacija - Flow Podataka

## 📱 Kompletan put slike kroz sistem

### 1. **Frontend (Browser/Mobilni telefon)**
```
Korisnik → Upload slike → JavaScript → Base64 konverzija → HTTP POST
```

#### Šta se dešava:
- Korisnik bira sliku (camera ili file upload)
- JavaScript čita fajl sa `FileReader` API-jem
- Slika se konvertuje u **Base64 string** format
- Kreira se JSON payload: `{"image": "data:image/png;base64,iVBORw0KGgoAAAA...", "fs": 250}`
- Šalje se HTTP POST zahtev na `/api/analyze/complete`

#### Gde se slika čuva:
- **Privremeno u browser memoriji** kao Base64 string
- **NE čuva se na disk** - samo u RAM-u
- **Automatski se briše** kada se završi analiza

---

### 2. **Network Layer (HTTP)**
```
Browser → Internet → Server (localhost:8000 ili PythonAnywhere)
```

#### Šta se dešava:
- HTTP POST zahtev sa JSON payload-om
- Content-Type: `application/json`
- Slika putuje kao Base64 string unutar JSON-a
- Server prima zahtev na Flask route `/api/analyze/complete`

---

### 3. **Backend (Python/Flask Server)**
```
HTTP Request → Flask Route → Image Processing → Analysis → JSON Response
```

#### Korak po korak:

##### 3.1 **Flask Route (`routes.py`)**
```python
@api.post("/analyze/complete")
def complete_ekg_analysis():
    payload = request.get_json(force=True)
    image_data = payload.get("image", "")  # Base64 string
```

##### 3.2 **Image Processing (`image_processing.py`)**
```python
def process_ekg_image(image_data):
    # 1. Dekodiranje Base64 → bytes
    image_bytes = base64.b64decode(image_data.split(',')[1])
    
    # 2. bytes → NumPy array → OpenCV slika
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    # 3. Validacija da li je EKG
    validation_result = validate_ekg_image(img)
    
    # 4. Ekstrakcija digitalnog signala
    signal = extract_ekg_signal(img)
    
    return {"signal": signal, "validation": validation_result}
```

##### 3.3 **Signal Analysis (različiti moduli)**
```python
# FFT analiza
fft_result = analyze_fft(signal, fs)

# Z-transformacija  
z_result = z_transform_analysis(signal, fs)

# Detekcija aritmija
arrhythmia_result = detect_arrhythmias(signal, fs)

# Kombinovanje rezultata
complete_result = {
    "fft_analysis": fft_result,
    "z_transform": z_result, 
    "arrhythmia_detection": arrhythmia_result,
    "signal_info": {...}
}
```

##### 3.4 **JSON Response**
```python
return jsonify(complete_result)  # Šalje nazad JSON
```

---

### 4. **Gde se podaci čuvaju tokom obrade**

#### ❌ **Šta se NE čuva trajno:**
- **Originalna slika** - briše se iz memorije nakon obrade
- **Base64 string** - postoji samo tokom HTTP zahteva
- **OpenCV slika objekti** - Python garbage collector ih briše
- **Privremeni fajlovi** - ne kreiraju se

#### ✅ **Šta postoji privremeno u RAM-u:**
- **HTTP request payload** (JSON sa Base64)
- **OpenCV slika** (numpy array)
- **Ekstraktovani signal** (lista brojeva)
- **Rezultati analize** (dictionary objekti)

#### 🔄 **Lifecycle podataka:**
```
Upload → RAM (Base64) → RAM (OpenCV) → RAM (Signal) → RAM (Results) → JSON Response → Garbage Collection
```

---

### 5. **Response Flow (Nazad ka Frontend-u)**
```
Python Results → JSON → HTTP Response → JavaScript → DOM Update
```

#### Šta se dešava:
- Python kreira JSON response sa rezultatima
- HTTP response se šalje nazad browser-u
- JavaScript prima JSON podatke
- DOM se ažurira sa rezultatima analize
- Progress bar se sakriva, rezultati se prikazuju

---

## 🔒 **Bezbednost i Privacy**

### ✅ **Privatnost:**
- **Slike se NE čuvaju** na serveru
- **Nema baze podataka** za slike
- **Nema log fajlova** sa slikama
- **Automatsko brisanje** iz memorije

### 🛡️ **Bezbednost:**
- **Validacija slika** - samo EKG slike se obrađuju
- **Size limit** - maksimalno 10MB
- **Format validacija** - samo PNG/JPEG
- **Error handling** - graceful failure

---

## 📊 **Performance Optimizacije**

### 🚀 **Brzina:**
- **In-memory obrada** - bez disk I/O
- **Numpy vectorization** - brze matematičke operacije
- **Optimizovani algoritmi** - efikasni OpenCV filtri
- **JSON streaming** - direktna serijalizacija

### 💾 **Memorija:**
- **Garbage collection** - automatsko oslobađanje memorije
- **Streaming processing** - ne čuva sve u memoriji istovremeno
- **Optimizovane biblioteke** - NumPy, OpenCV, SciPy

---

## 🔧 **Tehnički Stack**

### **Frontend:**
- **HTML5** - struktura
- **CSS3** - styling i animacije
- **Vanilla JavaScript** - logika (bez framework-a)
- **FileReader API** - čitanje fajlova
- **Fetch API** - HTTP komunikacija

### **Backend:**
- **Python 3.8+** - programski jezik
- **Flask** - web framework
- **OpenCV** - obrada slike
- **NumPy/SciPy** - numeričke operacije
- **Matplotlib** - vizualizacije (Agg backend)

### **Komunikacija:**
- **HTTP/HTTPS** - protokol
- **JSON** - format podataka
- **Base64** - enkodiranje slika
- **REST API** - arhitektura

---

## 🎯 **Zaključak**

**Slika NIKAD ne napušta RAM memoriju servera!**

1. **Upload** → Slika u browser memoriji
2. **HTTP** → Base64 string u JSON-u
3. **Server** → Privremeno u RAM-u tokom obrade
4. **Analysis** → Matematičke operacije u memoriji
5. **Response** → JSON rezultati
6. **Cleanup** → Automatsko brisanje iz memorije

**Rezultat:** Brza, bezbedna, privatna analiza bez čuvanja podataka! 🚀