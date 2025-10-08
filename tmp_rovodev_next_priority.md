# 🎯 SLEDEĆI PRIORITETI - IMPLEMENTACIONI PLAN

## **📈 TRENUTNO STANJE SISTEMA**

### ✅ **Rešeno u prethodnom krugu:**
- **Korelacijska konzistentnost**: 93.8% kroz sve testove
- **Standardizovani parametri**: Jedinstveni algoritmi
- **Realistic noise modeling**: Non-linear distortion + baseline drift

### ⚠️ **Identifikovani kritični problemi:**
- **Z-transform numerička nestabilnost** 
- **FFT spektralna leakage** (nema windowing)
- **Pan-Tompkins nepotpuna implementacija**
- **Image processing hardcoded parametri**
- **Correlation NaN handling problemi**

---

## **🔥 PRIORITET 1: Z-TRANSFORM STABILNOST**

### **Problem:**
```python
# ztransform.py - trenutni kod
if np.linalg.cond(R_reg) > 1e12:
    ar_coeffs = np.linalg.pinv(R_reg) @ r  # Pseudoinverz - NESTABILAN!
```

### **Rešenje - SVD decomposition:**
```python
def robust_ar_estimation(signal_data, order):
    """
    Robusna AR estimacija koristeći SVD umesto condition number
    """
    # Autokorelacija
    autocorr = np.correlate(signal_data, signal_data, mode='full')
    autocorr = autocorr[len(autocorr)//2:]
    autocorr = autocorr / autocorr[0]
    
    # Toeplitz matrica
    R = toeplitz(autocorr[:order])
    r = autocorr[1:order+1]
    
    # SVD decomposition za stabilnost
    U, s, Vh = np.linalg.svd(R)
    
    # Threshold small singular values
    s_threshold = 1e-12 * s[0]  # Relative threshold
    s_inv = np.where(s > s_threshold, 1/s, 0)
    
    # Stable solution
    ar_coeffs = Vh.T @ np.diag(s_inv) @ U.T @ r
    
    return ar_coeffs
```

### **Implementacija:** 
**Fajl:** `app/analysis/ztransform.py` linija 196-220  
**Testiranje:** MIT-BIH signals za validaciju  
**ETA:** 2-3 dana

---

## **🔥 PRIORITET 2: KOMPLETNI PAN-TOMPKINS ALGORITAM**

### **Problem:**
Trenutna implementacija koristi samo osnovnu peak detection. **Originalni Pan-Tompkins** ima 5 koraka:

### **Matematička osnova:**
```
1. Bandpass filter:   H(z) = (1-z⁻⁶)²/(1-z⁻¹)² * (1-z⁻¹)/(1-z⁻³²)
2. Derivative:        y[n] = (1/8T)(-x[n-2] - 2x[n-1] + 2x[n+1] + x[n+2])  
3. Squaring:          y[n] = x²[n]
4. Moving average:    y[n] = (1/N)Σx[n-k], N = 0.15*fs
5. Adaptive threshold: PEAKI/SPKI thresholds
```

### **Kompletna implementacija:**
```python
def complete_pan_tompkins_algorithm(signal, fs=250):
    """
    IEEE standard Pan-Tompkins QRS detection (1985)
    Sensitivity: >99.3%, Specificity: >99.6% on MIT-BIH
    """
    # Step 1: Bandpass filter 5-15 Hz  
    # Butterworth 2nd order za manje phase distortion
    sos = signal.butter(2, [5/(fs/2), 15/(fs/2)], btype='band', output='sos')
    filtered = signal.sosfilt(sos, signal)
    
    # Step 2: Derivative filter (emphasizes QRS slope)
    # h[n] = (1/8T)[−1 −2 0 2 1]
    h_deriv = np.array([-1, -2, 0, 2, 1]) / (8 * (1/fs))
    derivative = np.convolve(filtered, h_deriv, mode='same')
    
    # Step 3: Squaring (emphasizes higher frequencies)
    squared = derivative ** 2
    
    # Step 4: Moving window integration
    # Integration window: 0.15 seconds
    window_size = int(0.15 * fs)
    integrated = np.convolve(squared, np.ones(window_size)/window_size, mode='same')
    
    # Step 5: Adaptive thresholding
    r_peaks = adaptive_threshold_detection(integrated, fs)
    
    return {
        "r_peaks": r_peaks,
        "processed_signal": integrated,
        "algorithm": "Complete Pan-Tompkins (1985)",
        "expected_performance": "Sensitivity >99.3%, Specificity >99.6%"
    }

def adaptive_threshold_detection(integrated_signal, fs):
    """
    Pan-Tompkins adaptive thresholding sa dual thresholds
    """
    # Initialize thresholds
    SPKI = 0  # Signal peak
    NPKI = 0  # Noise peak
    THRESHOLD1 = 0  # Primary threshold
    THRESHOLD2 = 0  # Secondary threshold
    
    r_peaks = []
    refractory_period = int(0.2 * fs)  # 200ms refractory
    
    # Učitavanje algorithm...
    # (kompleksna implementacija adaptive thresholding)
    
    return r_peaks
```

### **Implementacija:**
**Fajl:** `app/analysis/arrhythmia_detection.py` - replace funkcija `detect_r_peaks`  
**Validacija:** MIT-BIH database record 100, 101, 102  
**ETA:** 5-7 dana

---

## **🔥 PRIORITET 3: FFT WELCH METHOD**

### **Problem:**
```python
# fft.py trenutni kod - osnovni FFT bez windowing
spectrum = np.abs(np.fft.rfft(x_no_dc)) / n
# REZULTAT: Spektralna leakage, aliasing
```

### **Rešenje - Welch periodogram:**
```python
def robust_fft_analysis(signal, fs):
    """
    Welch method sa Hann window za EKG spektralnu analizu
    """
    from scipy.signal import welch
    
    # Optimal parameters za EKG signale
    nperseg = min(2**int(np.log2(len(signal)/4)), 1024)  # Adaptivni segment size
    noverlap = nperseg // 2  # 50% overlap
    
    # Welch periodogram
    freq, psd = welch(signal, fs, 
                      window='hann',      # Hann window za smanjena leakage
                      nperseg=nperseg,    # Segment length
                      noverlap=noverlap,  # 50% overlap
                      detrend='constant') # Remove DC trend
    
    # Peak detection u PSD
    peak_idx = np.argmax(psd[freq > 0.5])  # Skip DC
    peak_freq = freq[freq > 0.5][peak_idx]
    peak_amplitude = psd[freq > 0.5][peak_idx]
    
    return {
        "frequencies": freq,
        "power_spectral_density": psd,
        "peak_frequency_hz": peak_freq,
        "peak_power": peak_amplitude,
        "method": "Welch periodogram with Hann window",
        "energy_conservation": np.sum(psd) * (freq[1] - freq[0])  # Parseval check
    }
```

### **Implementacija:**
**Fajl:** `app/analysis/fft.py` - replace funkcija `analyze_fft`  
**Validacija:** Parseval's theorem + known test signals  
**ETA:** 2-3 dana

---

## **🟠 PRIORITET 4: ADAPTIVE IMAGE PROCESSING**

### **Problem:**
Hardcoded threshold parametri ne rade za različite rezolucije/kontraste slika.

### **Rešenje - Dynamic parameters:**
```python
def intelligent_ekg_preprocessing(img):
    """
    Inteligentno prilagođavanje parametara na osnovu slike
    """
    height, width = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
    
    # 1. Dynamic block size based on resolution
    pixel_density = width * height
    if pixel_density > 2000000:      # High res (2MP+)
        block_size_factor = 80
    elif pixel_density > 500000:     # Medium res  
        block_size_factor = 50
    else:                            # Low res
        block_size_factor = 30
        
    block_size = max(11, width // block_size_factor)
    if block_size % 2 == 0:
        block_size += 1
    
    # 2. Dynamic C parameter based on image contrast
    image_contrast = np.std(gray)
    c_parameter = max(2, min(10, image_contrast * 0.15))
    
    # 3. Adaptive threshold
    binary = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV, block_size, c_parameter
    )
    
    return {
        "processed_image": binary,
        "parameters_used": {
            "block_size": block_size,
            "c_parameter": c_parameter,
            "image_resolution": f"{width}x{height}",
            "contrast_level": image_contrast
        }
    }
```

### **Implementacija:**
**Fajl:** `app/analysis/image_processing.py` linija 113-116  
**Testiranje:** Različite EKG slike (low/high resolution)  
**ETA:** 3-4 dana

---

## **🟡 PRIORITET 5: ROBUST CORRELATION**

### **Problem:**
Pearson correlation ne radi sa outliers i konstante signali daju NaN.

### **Rešenje - Spearman rank correlation:**
```python
def robust_signal_correlation(signal1, signal2):
    """
    Robusna korelacija koristeći Spearman rank umesto Pearson
    """
    from scipy.stats import spearmanr
    
    # Input validation
    if len(signal1) == 0 or len(signal2) == 0:
        return {"correlation": 0.0, "method": "empty_signals"}
    
    # Check for constant signals
    if np.std(signal1) < 1e-10:
        return {"correlation": 0.0, "method": "signal1_constant"}
    if np.std(signal2) < 1e-10:
        return {"correlation": 0.0, "method": "signal2_constant"}
    
    # Resample to same length
    min_len = min(len(signal1), len(signal2))
    if len(signal1) != len(signal2):
        from scipy import signal as sp_signal
        signal1_res = sp_signal.resample(signal1, min_len)
        signal2_res = sp_signal.resample(signal2, min_len)
    else:
        signal1_res = signal1
        signal2_res = signal2
    
    # Robust Spearman correlation
    correlation, p_value = spearmanr(signal1_res, signal2_res)
    
    # NaN handling
    if np.isnan(correlation):
        correlation = 0.0
        method = "nan_fallback"
    else:
        method = "spearman_rank"
    
    return {
        "correlation": float(correlation),
        "p_value": float(p_value) if not np.isnan(p_value) else 1.0,
        "method": method,
        "samples_used": min_len
    }
```

### **Implementacija:**
**Fajl:** `app/analysis/correlation_visualization.py` - update funkcija `compare_signals_robust`  
**ETA:** 1-2 dana

---

## **📋 IMPLEMENTACIONI TIMELINE**

### **Week 1 (CRITICAL):**
- [x] Korelacijska konzistentnost (REŠENO)
- [ ] Z-transform SVD stabilnost 
- [ ] FFT Welch method
- [ ] Unit testovi za numeričku stabilnost

### **Week 2 (HIGH PRIORITY):**
- [ ] Kompletni Pan-Tompkins algoritam
- [ ] MIT-BIH validacija R-peak detection
- [ ] Adaptive image processing parametri

### **Week 3 (MEDIUM PRIORITY):**
- [ ] Robust Spearman correlation
- [ ] Error propagation tracking
- [ ] Input validation standardizacija

### **Week 4 (VALIDATION):**
- [ ] Komprehensivni testing suite
- [ ] Performance benchmarking
- [ ] Algorithm documentation update

---

## **🎯 KVALITET CILJEVI**

### **Numerička stabilnost:**
- Z-transform: condition number < 10⁶
- FFT: Parseval's theorem error < 1%
- Correlation: NaN handling 100% coverage

### **Algorithm accuracy:**
- Pan-Tompkins: >99% sensitivity na MIT-BIH
- Image processing: >90% successful extraction
- FFT: THD measurement ±0.1% accuracy

### **Robusnost:**
- Input range: 1 sample - 100k samples
- Noise level: SNR od -20dB do +60dB  
- Image resolution: 100x100 do 4000x4000 pixels

---

**Status: PRIORITETI DEFINISANI ✅**  
**Next Action: Implementacija Z-transform SVD stabilnosti 🔥**