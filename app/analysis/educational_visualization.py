"""
Edukativna vizualizacija EKG analize
Prikazuje step-by-step kako je signal obrađen sa formulama i objašnjenjima
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch
import io
import base64

def create_educational_analysis_visualization(ekg_signal, analysis_results, fs=250):
    """
    Kreira edukativnu vizualizaciju koja pokazuje:
    1. Originalni signal sa označenim karakteristikama
    2. Korake obrade sa formulama
    3. Rezultate svake analize
    4. Interpretaciju rezultata
    """
    # Kreiranje figure sa subplotovima
    fig = plt.figure(figsize=(16, 20))
    
    # 1. Originalni signal sa anotacijama
    ax1 = plt.subplot(6, 2, (1, 2))
    plot_original_signal_with_annotations(ax1, ekg_signal, analysis_results, fs)
    
    # 2. Spatial Filling Index objašnjenje
    ax2 = plt.subplot(6, 2, 3)
    plot_sfi_explanation(ax2, analysis_results['spatial_filling_index'])
    
    # 3. Time-Frequency analiza
    ax3 = plt.subplot(6, 2, 4)
    plot_time_frequency_explanation(ax3, analysis_results['time_frequency_analysis'])
    
    # 4. Wavelet dekompozicija
    ax4 = plt.subplot(6, 2, (5, 6))
    plot_wavelet_decomposition(ax4, analysis_results['wavelet_analysis'])
    
    # 5. Filtering steps
    ax5 = plt.subplot(6, 2, (7, 8))
    plot_filtering_steps(ax5, analysis_results['advanced_filtering'], fs)
    
    # 6. Formule i matematika
    ax6 = plt.subplot(6, 2, 9)
    plot_mathematical_formulas(ax6, analysis_results)
    
    # 7. Interpretacija rezultata
    ax7 = plt.subplot(6, 2, 10)
    plot_interpretation_summary(ax7, analysis_results['comprehensive_interpretation'])
    
    # 8. R-pikovi i karakteristike
    ax8 = plt.subplot(6, 2, (11, 12))
    plot_ekg_characteristics(ax8, ekg_signal, analysis_results, fs)
    
    plt.tight_layout(pad=3.0)
    
    # Konverzija u base64
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight', facecolor='white')
    buffer.seek(0)
    plot_base64 = base64.b64encode(buffer.getvalue()).decode()
    plt.close(fig)
    
    return plot_base64

def plot_original_signal_with_annotations(ax, ekg_signal, results, fs):
    """Prikazuje originalni signal sa anotacijama"""
    t = np.linspace(0, len(ekg_signal)/fs, len(ekg_signal))
    
    ax.plot(t, ekg_signal, 'b-', linewidth=1.5, label='Originalni EKG signal')
    
    # Dodavanje anotacija za različite delove EKG-a
    if len(ekg_signal) > 100:
        # Simulacija P, QRS, T talasa
        peak_indices = np.where(np.array(ekg_signal) > np.mean(ekg_signal) + 0.5*np.std(ekg_signal))[0]
        if len(peak_indices) > 0:
            for i, peak_idx in enumerate(peak_indices[:3]):  # Prva 3 pika
                ax.annotate(f'R{i+1}', xy=(t[peak_idx], ekg_signal[peak_idx]), 
                           xytext=(t[peak_idx], ekg_signal[peak_idx] + 0.3),
                           arrowprops=dict(arrowstyle='->', color='red'),
                           fontsize=10, ha='center', color='red')
    
    ax.set_xlabel('Vreme (s)')
    ax.set_ylabel('Amplituda (mV)')
    ax.set_title('EKG Signal sa Označenim Karakteristikama', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.legend()
    
    # Dodavanje info box-a
    info_text = f"Dužina signala: {len(ekg_signal)} uzoraka\n"
    info_text += f"Trajanje: {len(ekg_signal)/fs:.1f} s\n"
    info_text += f"Sampling rate: {fs} Hz"
    
    ax.text(0.02, 0.98, info_text, transform=ax.transAxes, fontsize=9,
            verticalalignment='top', bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))

def plot_sfi_explanation(ax, sfi_results):
    """Objašnjava Spatial Filling Index"""
    ax.axis('off')
    
    # Naslov
    ax.text(0.5, 0.95, 'Spatial Filling Index (SFI)', 
            ha='center', va='top', fontsize=12, fontweight='bold', transform=ax.transAxes)
    
    # Formula
    formula_text = r'$SFI = \frac{\log(N)}{\log(L/a)}$'
    ax.text(0.5, 0.8, formula_text, ha='center', va='center', fontsize=14, 
            transform=ax.transAxes, bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.7))
    
    # Objašnjenje parametara
    explanation = f"""
Gde je:
• N = {sfi_results['signal_points']} (broj tačaka)
• L = {sfi_results['total_path_length']:.2f} (ukupna putanja)
• a = {sfi_results['average_amplitude']:.3f} (prosečna amplituda)

SFI = {sfi_results['spatial_filling_index']:.3f}

Interpretacija:
{sfi_results['interpretation']}
    """
    
    ax.text(0.05, 0.6, explanation, ha='left', va='top', fontsize=9, 
            transform=ax.transAxes, bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.7))

def plot_time_frequency_explanation(ax, tf_results):
    """Objašnjava Time-Frequency analizu"""
    ax.axis('off')
    
    # Naslov
    ax.text(0.5, 0.95, 'Time-Frequency Analiza', 
            ha='center', va='top', fontsize=12, fontweight='bold', transform=ax.transAxes)
    
    # STFT formula
    formula_text = r'$STFT(n,k) = \sum_{m} x[m]w[n-m]e^{-j2\pi km/N}$'
    ax.text(0.5, 0.8, formula_text, ha='center', va='center', fontsize=12, 
            transform=ax.transAxes, bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.7))
    
    # Rezultati
    explanation = f"""
Spektralna entropija: {tf_results['mean_spectral_entropy']:.3f}

Objašnjenje:
• STFT deli signal na kratke segmente
• Analizira frekvencijski sadržaj kroz vreme
• Entropija meri kompleksnost spektra
• Viša entropija = kompleksniji signal

Interpretacija:
{tf_results['interpretation']}
    """
    
    ax.text(0.05, 0.6, explanation, ha='left', va='top', fontsize=9, 
            transform=ax.transAxes, bbox=dict(boxstyle='round', facecolor='lightcoral', alpha=0.7))

def plot_wavelet_decomposition(ax, wavelet_results):
    """Prikazuje wavelet dekompoziciju"""
    # Prikaz energija po nivoima
    levels = [d['level'] for d in wavelet_results['details']]
    energies = [d['energy'] for d in wavelet_results['details']]
    
    bars = ax.bar(levels, energies, color='skyblue', alpha=0.7, edgecolor='navy')
    ax.set_xlabel('Wavelet nivo (frekvencijski opseg)')
    ax.set_ylabel('Energija')
    ax.set_title(f'Wavelet Dekompozicija ({wavelet_results["wavelet_type"]})', fontweight='bold')
    
    # Dodavanje vrednosti na barove
    for bar, energy in zip(bars, energies):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                f'{energy:.2f}', ha='center', va='bottom', fontsize=8)
    
    # Formula i objašnjenje
    formula_text = r'$WT(a,b) = \frac{1}{\sqrt{a}} \int x(t)\psi^*\left(\frac{t-b}{a}\right)dt$'
    ax.text(0.02, 0.98, formula_text, transform=ax.transAxes, fontsize=10,
            bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.7))
    
    interpretation_text = f"Wavelet entropija: {wavelet_results['wavelet_entropy']:.2f}\n"
    interpretation_text += f"Interpretacija: {wavelet_results['interpretation']}"
    ax.text(0.02, 0.15, interpretation_text, transform=ax.transAxes, fontsize=8,
            bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.7))

def plot_filtering_steps(ax, filtering_results, fs):
    """Prikazuje korake filtriranja"""
    # Prikaz originalnog i filtriranog signala
    original = np.array(filtering_results['original_signal'])
    filtered = np.array(filtering_results['adaptive_filtered'])
    
    t = np.linspace(0, len(original)/fs, len(original))
    
    ax.plot(t, original, 'r-', alpha=0.7, label='Originalni signal', linewidth=1)
    ax.plot(t, filtered, 'b-', label='Filtrirani signal', linewidth=1.5)
    
    ax.set_xlabel('Vreme (s)')
    ax.set_ylabel('Amplituda')
    ax.set_title('Koraci Filtriranja', fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Info o filterima
    filters_text = "Primenjeni filtri:\n"
    for i, filter_desc in enumerate(filtering_results['filters_applied'], 1):
        filters_text += f"{i}. {filter_desc}\n"
    
    ax.text(0.02, 0.98, filters_text, transform=ax.transAxes, fontsize=8,
            verticalalignment='top', bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))

def plot_mathematical_formulas(ax, results):
    """Prikazuje sve matematičke formule"""
    ax.axis('off')
    
    ax.text(0.5, 0.95, 'Matematičke Formule', 
            ha='center', va='top', fontsize=12, fontweight='bold', transform=ax.transAxes)
    
    formulas_text = """
1. Spatial Filling Index:
   SFI = log(N) / log(L/a)

2. STFT:
   X(n,k) = Σ x[m]w[n-m]e^(-j2πkm/N)

3. Wavelet Transform:
   WT(a,b) = (1/√a) ∫ x(t)ψ*((t-b)/a)dt

4. Wiener Filter:
   W = S/(S+N)

5. Spektralna Entropija:
   H = -Σ p(f)log₂(p(f))
    """
    
    ax.text(0.05, 0.8, formulas_text, ha='left', va='top', fontsize=9, 
            transform=ax.transAxes, fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.7))

def plot_interpretation_summary(ax, interpretation):
    """Prikazuje sažetak interpretacije"""
    ax.axis('off')
    
    ax.text(0.5, 0.95, 'Interpretacija Rezultata', 
            ha='center', va='top', fontsize=12, fontweight='bold', transform=ax.transAxes)
    
    summary_text = f"""
Kompleksnost signala: {interpretation['signal_complexity']}
Stabilnost frekvencije: {interpretation['frequency_stability']}
Wavelet kompleksnost: {interpretation['wavelet_complexity']}

UKUPNA OCENA:
{interpretation['overall_assessment']}

PREPORUKE:
"""
    
    for rec in interpretation['recommendations']:
        summary_text += f"• {rec}\n"
    
    # Boja pozadine na osnovu ocene
    if "medicinska" in interpretation['overall_assessment'].lower():
        bg_color = 'lightcoral'
    elif "normalan" in interpretation['overall_assessment'].lower():
        bg_color = 'lightgreen'
    else:
        bg_color = 'lightyellow'
    
    ax.text(0.05, 0.8, summary_text, ha='left', va='top', fontsize=9, 
            transform=ax.transAxes, bbox=dict(boxstyle='round', facecolor=bg_color, alpha=0.8))

def plot_ekg_characteristics(ax, ekg_signal, results, fs):
    """Prikazuje EKG karakteristike sa objašnjenjima"""
    t = np.linspace(0, len(ekg_signal)/fs, len(ekg_signal))
    
    ax.plot(t, ekg_signal, 'b-', linewidth=1.5)
    
    # Dodavanje legendi za EKG komponente
    ax.axhline(y=np.mean(ekg_signal), color='gray', linestyle='--', alpha=0.5, label='Baseline')
    
    # Označavanje različitih delova EKG-a
    mean_val = np.mean(ekg_signal)
    std_val = np.std(ekg_signal)
    
    # P talas region (pre R pika)
    ax.axhspan(mean_val - 0.2*std_val, mean_val + 0.2*std_val, alpha=0.2, color='green', label='P talas region')
    
    # QRS kompleks region
    ax.axhspan(mean_val + 0.3*std_val, mean_val + std_val, alpha=0.2, color='red', label='QRS kompleks')
    
    # T talas region (posle R pika)
    ax.axhspan(mean_val, mean_val + 0.4*std_val, alpha=0.2, color='blue', label='T talas region')
    
    ax.set_xlabel('Vreme (s)')
    ax.set_ylabel('Amplituda (mV)')
    ax.set_title('EKG Komponente i Karakteristike', fontweight='bold')
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3)
    
    # Dodavanje objašnjenja EKG komponenti
    explanation_text = """
P talas: Depolarizacija pretkomora
QRS: Depolarizacija komora
T talas: Repolarizacija komora
ST segment: Izoelektrična linija
    """
    
    ax.text(0.02, 0.98, explanation_text, transform=ax.transAxes, fontsize=8,
            verticalalignment='top', bbox=dict(boxstyle='round', facecolor='lightcyan', alpha=0.8))

def create_step_by_step_analysis(ekg_signal, fs=250):
    """
    Kreira step-by-step analizu sa objašnjenjima
    """
    from .advanced_ekg_analysis import comprehensive_ekg_analysis
    
    # Pokreni komprehensivnu analizu
    analysis_results = comprehensive_ekg_analysis(ekg_signal, fs)
    
    # Kreiraj edukativnu vizualizaciju
    educational_plot = create_educational_analysis_visualization(ekg_signal, analysis_results, fs)
    
    # Kreiraj detaljno objašnjenje
    detailed_explanation = {
        "analysis_steps": [
            {
                "step": 1,
                "title": "Učitavanje i predobrada signala",
                "description": "Signal je učitan i pripremljen za analizu. Uklonjen je baseline drift i šum.",
                "formula": "x_clean[n] = HPF(LPF(x[n]))",
                "result": "Signal spreman za analizu"
            },
            {
                "step": 2,
                "title": "Spatial Filling Index (SFI)",
                "description": "Meri geometrijsku kompleksnost signala kroz odnos broja tačaka i ukupne putanje.",
                "formula": "SFI = log(N) / log(L/a)",
                "result": f"SFI = {analysis_results['spatial_filling_index']['spatial_filling_index']:.3f}"
            },
            {
                "step": 3,
                "title": "Time-Frequency analiza",
                "description": "STFT analiza pokazuje kako se frekvencijski sadržaj menja kroz vreme.",
                "formula": "STFT(n,k) = Σ x[m]w[n-m]e^(-j2πkm/N)",
                "result": f"Spektralna entropija = {analysis_results['time_frequency_analysis']['mean_spectral_entropy']:.3f}"
            },
            {
                "step": 4,
                "title": "Wavelet dekompozicija",
                "description": "Dekompozicija signala na različite frekvencijske komponente.",
                "formula": "WT(a,b) = (1/√a) ∫ x(t)ψ*((t-b)/a)dt",
                "result": f"Wavelet entropija = {analysis_results['wavelet_analysis']['wavelet_entropy']:.3f}"
            },
            {
                "step": 5,
                "title": "Napredni filtri",
                "description": "Primena kaskade filtara za uklanjanje različitih tipova šuma.",
                "formula": "y[n] = Wiener(LPF(Notch(HPF(x[n]))))",
                "result": f"SNR poboljšan za {analysis_results['advanced_filtering']['wiener_coefficient']:.2f}"
            },
            {
                "step": 6,
                "title": "Interpretacija rezultata",
                "description": "Kombinovanje svih analiza za medicinsku interpretaciju.",
                "formula": "Kombinovana analiza svih parametara",
                "result": analysis_results['comprehensive_interpretation']['overall_assessment']
            }
        ],
        "educational_visualization": educational_plot,
        "detailed_results": analysis_results
    }
    
    return detailed_explanation