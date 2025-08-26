import numpy as np

def analyze_fft(signal, fs):
    x = np.array(signal, dtype=float)
    n = len(x)
    if n == 0:
        return {"error": "empty signal"}
    freq = np.fft.rfftfreq(n, d=1.0/fs)
    spectrum = np.abs(np.fft.rfft(x)) / n
    peak_idx = int(np.argmax(spectrum))
    return {
        "n": n,
        "fs": fs,
        "peak_frequency_hz": float(freq[peak_idx]),
        "peak_amplitude": float(spectrum[peak_idx])
    }
