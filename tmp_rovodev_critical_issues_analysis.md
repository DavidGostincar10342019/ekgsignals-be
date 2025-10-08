# 🚨 KRITIČNA ANALIZA ALGORITAMA - HITNI PROBLEMI

## **📊 PREGLED ANALIZIRANIH ALGORITAMA**

### **Analizirani moduli:**
1. **FFT Analysis** (`fft.py`) - Welch method + harmonijska analiza
2. **Arrhythmia Detection** (`arrhythmia_detection.py`) - Pan-Tompkins + morfologija 
3. **Z-Transform** (`ztransform.py`) - Yule-Walker AR estimation
4. **Image Processing** (`image_processing.py`) - Kontura + spline fitting
5. **Correlation Analysis** (`correlation_visualization.py`) - Signal poređenje

---

## **🔴 KRITIČNI PROBLEMI - HITNO POTREBNE IZMENE**

### **1. Z-TRANSFORM: NUMERIČKA NESTABILNOST**

#### **❌ Problem - Loše kondiciona matrica:**
```python
# ztransform.py linija 196-211
R = np.array([autocorr[abs(i-j)] for i in range(order) for j in range(order)])
# PROBLEM: Može biti singularna matrica!

if np.linalg.cond(R_reg) > 1e12:
    ar_coeffs = np.linalg.pinv(R_reg) @ r  # Pseudoinverz
```

#### **⚠️ Matematički problem:**
**Yule-Walker jednačine:** `R * a = r`
- **R matrica** može biti **ill-conditioned** za kratke signale
- **Condition number > 10¹²** → numerička nestabilnost
- **Pseudoinverse** kao fallback nije optimalno

#### **✅ HITNO REŠENJE:**
```python
# Umesto condition number provere, koristi SVD decomposition
def robust_ar_estimation(signal, order):
    # Singular Value Decomposition za stabilno rešavanje
    U, s, Vh = np.linalg.svd(R_matrix)
    # Threshold mala singularna vrijednost
    s_thresh = np.maximum(s, 1e-12 * s[0])
    ar_coeffs = Vh.T @ np.diag(1/s_thresh) @ U.T @ r_vector
    return ar_coeffs
```

---

### **2. FFT ANALIZA: ALIASING I SPEKTRALNA LEAKAGE**

#### **❌ Problem - Nedovoljna anti-aliasing zaštita:**
```python
# fft.py linija 145-146 
freq = np.fft.rfftfreq(n, d=1.0/fs)
spectrum = np.abs(np.fft.rfft(x_no_dc)) / n
# PROBLEM: Nema windowing funkcije!
```

#### **⚠️ Matematički problem:**
**Welch metoda:** `P(f) = (1/K) * Σ|X_k(f)|²`
- **Nedostatak windowing** → spektralna leakage
- **Hann/Hamming window** potreban za EKG signale
- **Overlap-add processing** za bolju rezoluciju

#### **✅ HITNO REŠENJE:**
```python
def welch_fft_analysis(signal, fs, nperseg=1024):
    # Koristi scipy.signal.welch umesto osnovne FFT
    from scipy.signal import welch
    freq, psd = welch(signal, fs, nperseg=nperseg, 
                      window='hann', overlap=nperseg//2)
    return freq, psd
```

---

### **3. IMAGE PROCESSING: KONTOUR DETEKCIJA NESTABILNA**

#### **❌ Problem - Threshold hardcoded vrednosti:**
```python
# image_processing.py linija 113-116
binary = cv2.adaptiveThreshold(
    gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
    cv2.THRESH_BINARY_INV, 11, 2  # ← HARDCODED!
)
```

#### **⚠️ Matematički problem:**
**Adaptive threshold:** `T(x,y) = μ(x,y) - C`
- **Block size = 11** nije prilagođen rezoluciji slike
- **C = 2** može biti premalo za low-contrast EKG
- **Gaussian kernel** možda nije optimalan za linijske strukture

#### **✅ HITNO REŠENJE:**
```python
def adaptive_threshold_for_ekg(gray_img):
    height, width = gray_img.shape
    # Dynamic block size based on image resolution
    block_size = max(11, min(width//50, height//50))
    if block_size % 2 == 0:
        block_size += 1
    
    # Dynamic C based on image contrast
    image_std = np.std(gray_img)
    C = max(2, image_std * 0.1)
    
    return cv2.adaptiveThreshold(gray_img, 255, 
                                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                cv2.THRESH_BINARY_INV, block_size, C)
```

---

### **4. ARRHYTHMIA DETECTION: PAN-TOMPKINS IMPLEMENTACIJA NEPOTPUNA**

#### **❌ Problem - Nedostaju key steps:**
```python
# arrhythmia_detection.py - Pan-Tompkins algorithm
# NEDOSTAVAJU:
# 1. Derivative filter: y[n] = (1/8T)(-x[n-2] - 2x[n-1] + 2x[n+1] + x[n+2])
# 2. Squaring function: y[n] = x²[n] 
# 3. Moving window integration: y[n] = (1/N)(x[n-(N-1)] + ... + x[n])
# 4. Adaptive thresholding sa dual threshold
```

#### **⚠️ Matematički problem:**
**Pan-Tompkins jednačine:**
1. **Bandpass:** `H(z) = (1-z⁻⁶)²/(1-z⁻¹)² * (1-z⁻¹)/(1-z⁻³²)`
2. **Derivative:** `H(z) = (1/8T)(-z⁻² - 2z⁻¹ + 2z + z²)`
3. **Squaring:** `y[n] = x²[n]`
4. **Moving average:** `y[n] = (1/N)Σx[n-k]`

**TRENUTNA IMPLEMENTACIJA** koristi samo osnovnu peak detection!

#### **✅ HITNO REŠENJE:**
```python
def complete_pan_tompkins(signal, fs):
    # 1. Bandpass filter (5-15 Hz)
    sos = signal.butter(2, [5/(fs/2), 15/(fs/2)], btype='band', output='sos')
    filtered = signal.sosfilt(sos, signal)
    
    # 2. Derivative filter
    h_d = np.array([-1, -2, 0, 2, 1]) / (8 * (1/fs))
    derivative = np.convolve(filtered, h_d, mode='same')
    
    # 3. Squaring
    squared = derivative ** 2
    
    # 4. Moving window integration
    window_size = int(0.15 * fs)  # 150ms window
    integrated = np.convolve(squared, np.ones(window_size)/window_size, mode='same')
    
    # 5. Adaptive thresholding
    return detect_peaks_adaptive_threshold(integrated, fs)
```

---

### **5. CORRELATION ANALYSIS: EDGE CASES NISU POKRIVENI**

#### **❌ Problem - NaN/Inf handling:**
```python
# correlation_visualization.py linija 309-312
correlation = np.corrcoef(orig_resampled, extr_resampled)[0, 1]
# PROBLEM: Može biti NaN ako std=0
if np.isnan(correlation):
    correlation = 0.0  # Jednostavan fallback
```

#### **⚠️ Matematički problem:**
**Pearson korelacija:** `r = Σ(x-x̄)(y-ȳ) / √[Σ(x-x̄)²Σ(y-ȳ)²]`
- **Deljenja nulom** ako jedan signal konstanta
- **NaN propagation** kroz sve downstream calcualation
- **Rank correlation** bi bila robustnija alternativa

#### **✅ HITNO REŠENJE:**
```python
def robust_correlation(x, y):
    # Spearman rank correlation umesto Pearson
    from scipy.stats import spearmanr
    
    # Check za konstante signale
    if np.std(x) < 1e-10 or np.std(y) < 1e-10:
        return 0.0, "constant_signal"
    
    # Robust correlation
    corr, p_value = spearmanr(x, y)
    return corr if not np.isnan(corr) else 0.0, "valid"
```

---

## **⚡ PRIORITIZOVANE IZMENE - HITNOST RANKING**

### **🔥 CRITICAL (Hitno - ove nedelje):**
1. **Z-Transform stabilnost** - SVD umesto condition number
2. **Pan-Tompkins kompletna implementacija** - trenutna je nepotpuna
3. **FFT windowing** - dodaj Welch method

### **🟠 HIGH (Sledeće 2 nedelje):**
4. **Image processing adaptive parameters** - dinamički threshold
5. **Robust correlation** - Spearman umesto Pearson

### **🟡 MEDIUM (Mesec dana):**
6. **Error propagation tracking** - kroz sve module
7. **Input validation** - standardizovano kroz sve funkcije

---

## **🧮 MATEMATIČKA VALIDACIJA POTREBNA**

### **1. Unit testovi za kritične funkcije:**
```python
# Test numeričke stabilnosti
def test_z_transform_stability():
    # Test sa ill-conditioned matrices
    # Test sa short signals
    # Test sa constant signals

def test_pan_tompkins_mit_bih():
    # Validacija protiv MIT-BIH database
    # Expected TP/FP/FN rates

def test_fft_parseval_theorem():
    # Validacija da li je energy preserved
    # Σ|x[n]|² = (1/N)Σ|X[k]|²
```

### **2. Numerical precision tracking:**
```python
# Dodaj u sve algoritme
def track_numerical_error(input_signal, output_signal):
    input_energy = np.sum(np.abs(input_signal)**2)
    output_energy = np.sum(np.abs(output_signal)**2) 
    energy_conservation = abs(input_energy - output_energy) / input_energy
    return {"energy_error": energy_conservation}
```

---

## **📋 IMPLEMENTACIONI PLAN**

### **Week 1: Critical fixes**
- [ ] Implementiraj SVD-based Z-transform
- [ ] Dodaj Welch windowing u FFT
- [ ] Test numeričke stabilnosti

### **Week 2: Algorithm completion** 
- [ ] Kompletni Pan-Tompkins algoritam
- [ ] Adaptive image threshold parameters
- [ ] MIT-BIH validacija

### **Week 3: Robusnost**
- [ ] Spearman correlation umesto Pearson
- [ ] Input validation u svim modulima
- [ ] Error propagation tracking

### **Week 4: Testing & Documentation**
- [ ] Komprehensivni unit testovi
- [ ] Numerical precision validation
- [ ] Algorithm documentation update

---

**Status: KRITIČNI PROBLEMI IDENTIFIKOVANI ⚠️**  
**Next Action: Prioritizovane izmene po hitnosti 🔥**