import numpy as np
try:
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("Warning: Matplotlib not available. Plots will be disabled.")

from scipy import signal
import io
import base64

def z_transform_analysis(digital_signal, fs=250):
    """
    Implementira Z-transformaciju i analizu nultih tačaka i polova
    
    Args:
        digital_signal: 1D numpy array digitalnog signala
        fs: Frekvencija uzorkovanja
    
    Returns:
        dict: Rezultati Z-transformacije sa analizom
    """
    try:
        signal_array = np.array(digital_signal, dtype=float)
        
        if len(signal_array) == 0:
            return {"error": "Prazan signal"}
        
        # Kreiranje sistema iz signala (autoregresivni model)
        # Koristimo Yule-Walker metodu za AR model
        order = min(10, len(signal_array) // 4)  # Adaptivni red modela
        
        # AR koeficijenti
        ar_coeffs = estimate_ar_coefficients(signal_array, order)
        
        # Kreiranje transfer funkcije
        # H(z) = 1 / (1 + a1*z^-1 + a2*z^-2 + ... + an*z^-n)
        denominator = np.concatenate([[1], ar_coeffs])
        numerator = [1]
        
        # Pronalaženje polova i nultih tačaka
        zeros = np.roots(numerator) if len(numerator) > 1 else []
        poles = np.roots(denominator) if len(denominator) > 1 else []
        
        # Analiza stabilnosti
        stability_analysis = analyze_stability(poles)
        
        # Frekvencijski odziv
        w, h = signal.freqz(numerator, denominator, worN=512, fs=fs)
        
        # Generisanje dijagrama polova i nultih tačaka
        pole_zero_plot = create_pole_zero_plot(zeros, poles)
        
        return {
            "ar_coefficients": ar_coeffs.tolist(),
            "zeros": [{"real": float(complex(z).real), "imag": float(complex(z).imag)} for z in zeros],
            "poles": [{"real": float(complex(p).real), "imag": float(complex(p).imag)} for p in poles],
            "stability": stability_analysis,
            "frequency_response": {
                "frequencies": w.tolist(),
                "magnitude": np.abs(h).tolist(),
                "phase": np.angle(h).tolist()
            },
            "pole_zero_plot": pole_zero_plot,
            "fs": fs
        }
        
    except Exception as e:
        return {"error": f"Greška u Z-transformaciji: {str(e)}"}

def estimate_ar_coefficients(signal_data, order):
    """
    Procena AR koeficijenata koristeći Yule-Walker metodu
    """
    # Normalizacija signala
    signal_data = signal_data - np.mean(signal_data)
    
    # Autokorelacijska funkcija
    autocorr = np.correlate(signal_data, signal_data, mode='full')
    autocorr = autocorr[len(autocorr)//2:]
    autocorr = autocorr / autocorr[0]  # Normalizacija
    
    # Yule-Walker jednačine
    if len(autocorr) <= order:
        order = len(autocorr) - 1
    
    if order <= 0:
        return np.array([0.1])  # Default vrednost
    
    # Kreiranje Toeplitz matrice
    R = np.array([autocorr[abs(i-j)] for i in range(order) for j in range(order)]).reshape(order, order)
    r = autocorr[1:order+1]
    
    try:
        # Rešavanje Yule-Walker jednačina
        ar_coeffs = np.linalg.solve(R, r)
        return ar_coeffs
    except np.linalg.LinAlgError:
        # Ako matrica nije invertibilna, koristi pseudoinverz
        ar_coeffs = np.linalg.pinv(R) @ r
        return ar_coeffs

def analyze_stability(poles):
    """
    Analiza stabilnosti sistema na osnovu polova
    """
    if len(poles) == 0:
        return {"stable": True, "message": "Nema polova"}
    
    # Provera da li su svi polovi unutar jediničnog kruga
    pole_magnitudes = np.abs(poles)
    max_magnitude = np.max(pole_magnitudes)
    
    stable = max_magnitude < 1.0
    
    analysis = {
        "stable": bool(stable),
        "max_pole_magnitude": float(max_magnitude),
        "pole_count": int(len(poles)),
        "poles_inside_unit_circle": int(np.sum(pole_magnitudes < 1.0)),
        "message": "Sistem je stabilan" if stable else "Sistem je nestabilan"
    }
    
    return analysis

def create_pole_zero_plot(zeros, poles):
    """
    Kreira dijagram polova i nultih tačaka u Z-ravnini
    """
    if not MATPLOTLIB_AVAILABLE:
        return "Matplotlib nije dostupan za kreiranje dijagrama"
    
    try:
        # Ensure we're using non-interactive backend
        plt.ioff()  # Turn off interactive mode
        fig, ax = plt.subplots(1, 1, figsize=(8, 8))
        
        # Jedinični krug
        theta = np.linspace(0, 2*np.pi, 100)
        unit_circle_x = np.cos(theta)
        unit_circle_y = np.sin(theta)
        ax.plot(unit_circle_x, unit_circle_y, 'k--', alpha=0.5, label='Jedinični krug')
        
        # Polovi (x)
        if len(poles) > 0:
            pole_real = [complex(p).real for p in poles]
            pole_imag = [complex(p).imag for p in poles]
            ax.scatter(pole_real, pole_imag, marker='x', s=100, c='red', label='Polovi')
        
        # Nulte tačke (o)
        if len(zeros) > 0:
            zero_real = [complex(z).real for z in zeros]
            zero_imag = [complex(z).imag for z in zeros]
            ax.scatter(zero_real, zero_imag, marker='o', s=100, c='blue', facecolors='none', label='Nulte tačke')
        
        ax.set_xlim(-2, 2)
        ax.set_ylim(-2, 2)
        ax.set_xlabel('Realni deo')
        ax.set_ylabel('Imaginarni deo')
        ax.set_title('Dijagram polova i nultih tačaka u Z-ravnini')
        ax.grid(True, alpha=0.3)
        ax.legend()
        ax.set_aspect('equal')
        
        # Konverzija u base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        plot_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close(fig)  # Explicitly close the figure
        plt.clf()       # Clear the current figure
        
        return plot_base64
        
    except Exception as e:
        return f"Greška pri kreiranju dijagrama: {str(e)}"

def digital_filter_design(cutoff_freq, fs=250, filter_type='lowpass'):
    """
    Dizajn digitalnog filtera za EKG signal
    
    Args:
        cutoff_freq: Granična frekvencija
        fs: Frekvencija uzorkovanja
        filter_type: Tip filtera ('lowpass', 'highpass', 'bandpass')
    
    Returns:
        dict: Koeficijenti filtera i analiza
    """
    try:
        nyquist = fs / 2
        normalized_cutoff = cutoff_freq / nyquist
        
        # Butterworth filter dizajn
        order = 4
        if filter_type == 'bandpass':
            # Za EKG: 0.5-40 Hz
            low = 0.5 / nyquist
            high = 40 / nyquist
            b, a = signal.butter(order, [low, high], btype='band')
        else:
            b, a = signal.butter(order, normalized_cutoff, btype=filter_type)
        
        # Analiza filtera
        w, h = signal.freqz(b, a, worN=512, fs=fs)
        
        return {
            "numerator": b.tolist(),
            "denominator": a.tolist(),
            "frequency_response": {
                "frequencies": w.tolist(),
                "magnitude_db": (20 * np.log10(np.abs(h))).tolist(),
                "phase": np.angle(h).tolist()
            },
            "filter_type": filter_type,
            "cutoff_frequency": cutoff_freq,
            "order": order
        }
        
    except Exception as e:
        return {"error": f"Greška u dizajnu filtera: {str(e)}"}