"""
Grafičko prikazivanje korelacijskih rezultata za EKG signal rekonstrukciju
Vizualizuje kvalitet prebacivanja Slika → 1D Signal → Analiza
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from scipy import signal
from scipy.stats import pearsonr
import io
import base64

def create_correlation_analysis_plot(original_signal, extracted_signal, fs=250, 
                                   correlation_result=None, analysis_comparison=None):
    """
    Kreira komprehensivnu vizualizaciju korelacijske analize
    
    Args:
        original_signal: Originalni EKG signal
        extracted_signal: Signal ekstraktovan iz slike
        fs: Sampling frequency
        correlation_result: Rezultat korelacije iz compare_signals()
        analysis_comparison: Poređenje FFT/aritmija analiza
    
    Returns:
        dict: Base64 slike i metadata
    """
    
    # Setup figure sa grid layout
    fig = plt.figure(figsize=(16, 12))
    gs = gridspec.GridSpec(4, 3, figure=fig, hspace=0.4, wspace=0.3)
    
    # Konvertuj u numpy arrays
    original = np.array(original_signal)
    extracted = np.array(extracted_signal)
    
    # Normalizuj signale za bolju vizualizaciju
    orig_norm = _normalize_signal(original)
    extr_norm = _normalize_signal(extracted)
    
    # Izračunaj vremenske ose
    t_orig = np.linspace(0, len(original) / fs, len(original))
    t_extr = np.linspace(0, len(extracted) / fs, len(extracted))
    
    # 1. VREMENSKI DOMENI (gornji red)
    _plot_time_domain_comparison(fig, gs, orig_norm, extr_norm, t_orig, t_extr, correlation_result)
    
    # 2. FREKVENCIJSKI DOMENI (drugi red)
    _plot_frequency_domain_comparison(fig, gs, orig_norm, extr_norm, fs)
    
    # 3. KORELACIJSKA ANALIZA (treći red)
    _plot_correlation_analysis(fig, gs, orig_norm, extr_norm, correlation_result)
    
    # 4. PERFORMANCE METRICS (četvrti red)
    _plot_performance_metrics(fig, gs, correlation_result, analysis_comparison)
    
    # Glavni naslov
    fig.suptitle('EKG Signal Rekonstrukcija - Korelacijska Analiza', 
                 fontsize=16, fontweight='bold', y=0.98)
    
    return _save_plot_as_base64(fig)

def _normalize_signal(signal):
    """Normalizuje signal za vizualizaciju"""
    signal = np.array(signal)
    return (signal - np.mean(signal)) / np.std(signal)

def _plot_time_domain_comparison(fig, gs, orig_norm, extr_norm, t_orig, t_extr, correlation_result):
    """Grafikon vremenskih domena - originalni vs ekstraktovani"""
    
    # Panel 1: Originalni signal
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.plot(t_orig, orig_norm, 'b-', linewidth=1.5, alpha=0.8, label='Originalni signal')
    ax1.set_title('Originalni EKG Signal', fontweight='bold')
    ax1.set_xlabel('Vreme (s)')
    ax1.set_ylabel('Amplituda (norm.)')
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    
    # Panel 2: Ekstraktovani signal
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.plot(t_extr, extr_norm, 'r-', linewidth=1.5, alpha=0.8, label='Ekstraktovani signal')
    ax2.set_title('Signal Ekstraktovan iz Slike', fontweight='bold')
    ax2.set_xlabel('Vreme (s)')
    ax2.set_ylabel('Amplituda (norm.)')
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    
    # Panel 3: Overlay poređenje
    ax3 = fig.add_subplot(gs[0, 2])
    
    # Resample signals na istu dužinu za overlay
    min_len = min(len(orig_norm), len(extr_norm))
    orig_resampled = signal.resample(orig_norm, min_len)
    extr_resampled = signal.resample(extr_norm, min_len)
    t_common = np.linspace(0, max(t_orig[-1], t_extr[-1]), min_len)
    
    ax3.plot(t_common, orig_resampled, 'b-', linewidth=2, alpha=0.7, label='Originalni')
    ax3.plot(t_common, extr_resampled, 'r--', linewidth=2, alpha=0.7, label='Ekstraktovani')
    
    # Dodaj korelaciju u naslov
    if correlation_result and 'correlation' in correlation_result:
        corr = correlation_result['correlation']
        ax3.set_title(f'Overlay Poređenje (r={corr:.3f})', fontweight='bold')
    else:
        ax3.set_title('Overlay Poređenje', fontweight='bold')
    
    ax3.set_xlabel('Vreme (s)')
    ax3.set_ylabel('Amplituda (norm.)')
    ax3.grid(True, alpha=0.3)
    ax3.legend()

def _plot_frequency_domain_comparison(fig, gs, orig_norm, extr_norm, fs):
    """Grafikon frekvencijskih domena - FFT poređenje"""
    
    # FFT originalnog signala
    freqs_orig, psd_orig = signal.welch(orig_norm, fs, nperseg=min(1024, len(orig_norm)//4))
    
    # FFT ekstraktovanog signala
    freqs_extr, psd_extr = signal.welch(extr_norm, fs, nperseg=min(1024, len(extr_norm)//4))
    
    # Panel 1: Originalni spektar
    ax1 = fig.add_subplot(gs[1, 0])
    ax1.semilogy(freqs_orig, psd_orig, 'b-', linewidth=2, alpha=0.8)
    ax1.set_title('FFT - Originalni Signal', fontweight='bold')
    ax1.set_xlabel('Frekvencija (Hz)')
    ax1.set_ylabel('PSD (dB)')
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(0, 50)  # Focus na EKG opseg
    
    # Panel 2: Ekstraktovani spektar
    ax2 = fig.add_subplot(gs[1, 1])
    ax2.semilogy(freqs_extr, psd_extr, 'r-', linewidth=2, alpha=0.8)
    ax2.set_title('FFT - Ekstraktovani Signal', fontweight='bold')
    ax2.set_xlabel('Frekvencija (Hz)')
    ax2.set_ylabel('PSD (dB)')
    ax2.grid(True, alpha=0.3)
    ax2.set_xlim(0, 50)
    
    # Panel 3: Spektralno poređenje
    ax3 = fig.add_subplot(gs[1, 2])
    
    # Interpoliraj na zajedničke frekvencije
    common_freqs = np.linspace(0, min(freqs_orig[-1], freqs_extr[-1]), 100)
    psd_orig_interp = np.interp(common_freqs, freqs_orig, psd_orig)
    psd_extr_interp = np.interp(common_freqs, freqs_extr, psd_extr)
    
    ax3.semilogy(common_freqs, psd_orig_interp, 'b-', linewidth=2, alpha=0.7, label='Originalni')
    ax3.semilogy(common_freqs, psd_extr_interp, 'r--', linewidth=2, alpha=0.7, label='Ekstraktovani')
    
    # Izračunaj spektralnu korelaciju
    spectral_corr = np.corrcoef(np.log(psd_orig_interp + 1e-10), np.log(psd_extr_interp + 1e-10))[0, 1]
    
    ax3.set_title(f'Spektralno Poređenje (r={spectral_corr:.3f})', fontweight='bold')
    ax3.set_xlabel('Frekvencija (Hz)')
    ax3.set_ylabel('PSD (dB)')
    ax3.grid(True, alpha=0.3)
    ax3.legend()
    ax3.set_xlim(0, 50)

def _plot_correlation_analysis(fig, gs, orig_norm, extr_norm, correlation_result):
    """Detaljana korelacijska analiza"""
    
    # Resample na istu dužinu
    min_len = min(len(orig_norm), len(extr_norm))
    orig_resampled = signal.resample(orig_norm, min_len)
    extr_resampled = signal.resample(extr_norm, min_len)
    
    # Panel 1: Scatter plot korelacije
    ax1 = fig.add_subplot(gs[2, 0])
    
    # Sample svaki N-ti point za čitljivost
    step = max(1, min_len // 1000)
    scatter_orig = orig_resampled[::step]
    scatter_extr = extr_resampled[::step]
    
    ax1.scatter(scatter_orig, scatter_extr, alpha=0.6, s=20, c='purple')
    
    # Fit line
    z = np.polyfit(scatter_orig, scatter_extr, 1)
    p = np.poly1d(z)
    x_line = np.linspace(min(scatter_orig), max(scatter_orig), 100)
    ax1.plot(x_line, p(x_line), 'r-', linewidth=2, alpha=0.8)
    
    # Perfect correlation line
    ax1.plot(x_line, x_line, 'k--', alpha=0.5, label='Perfect correlation')
    
    if correlation_result and 'correlation' in correlation_result:
        corr = correlation_result['correlation']
        ax1.set_title(f'Signal Korelacija (r={corr:.3f})', fontweight='bold')
    else:
        corr = np.corrcoef(scatter_orig, scatter_extr)[0, 1]
        ax1.set_title(f'Signal Korelacija (r={corr:.3f})', fontweight='bold')
    
    ax1.set_xlabel('Originalni Signal')
    ax1.set_ylabel('Ekstraktovani Signal')
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    
    # Panel 2: Difference plot
    ax2 = fig.add_subplot(gs[2, 1])
    
    difference = orig_resampled - extr_resampled
    t = np.linspace(0, len(difference), len(difference))
    
    ax2.plot(t, difference, 'g-', linewidth=1, alpha=0.8)
    ax2.axhline(y=0, color='k', linestyle='--', alpha=0.5)
    ax2.fill_between(t, difference, alpha=0.3, color='green')
    
    rmse = np.sqrt(np.mean(difference**2))
    mae = np.mean(np.abs(difference))
    
    ax2.set_title(f'Razlika Signala (RMSE={rmse:.3f})', fontweight='bold')
    ax2.set_xlabel('Samples')
    ax2.set_ylabel('Originalni - Ekstraktovani')
    ax2.grid(True, alpha=0.3)
    
    # Panel 3: Cross-correlation
    ax3 = fig.add_subplot(gs[2, 2])
    
    # Cross-correlation
    xcorr = np.correlate(orig_resampled, extr_resampled, mode='full')
    xcorr = xcorr / np.max(xcorr)  # Normalize
    
    lags = np.arange(-len(extr_resampled) + 1, len(orig_resampled))
    
    # Plot samo oko centra
    center = len(xcorr) // 2
    plot_range = min(200, len(xcorr) // 4)
    start_idx = center - plot_range
    end_idx = center + plot_range
    
    ax3.plot(lags[start_idx:end_idx], xcorr[start_idx:end_idx], 'purple', linewidth=2)
    ax3.axvline(x=0, color='r', linestyle='--', alpha=0.7, label='Zero lag')
    
    # Pronađi peak
    max_idx = np.argmax(xcorr[start_idx:end_idx]) + start_idx
    max_lag = lags[max_idx]
    max_corr = xcorr[max_idx]
    
    ax3.axvline(x=max_lag, color='g', linestyle='-', alpha=0.7, label=f'Peak lag={max_lag}')
    
    ax3.set_title(f'Cross-Correlation (peak={max_corr:.3f})', fontweight='bold')
    ax3.set_xlabel('Lag (samples)')
    ax3.set_ylabel('Correlation')
    ax3.grid(True, alpha=0.3)
    ax3.legend()

def _plot_performance_metrics(fig, gs, correlation_result, analysis_comparison):
    """Performance metrics i summary"""
    
    # Panel 1: Correlation metrics bar chart
    ax1 = fig.add_subplot(gs[3, 0])
    
    metrics = []
    values = []
    colors = []
    
    if correlation_result:
        if 'correlation' in correlation_result:
            metrics.append('Correlation')
            values.append(correlation_result['correlation'])
            colors.append('blue')
        
        if 'similarity_score' in correlation_result:
            metrics.append('Similarity')
            values.append(correlation_result['similarity_score'])
            colors.append('green')
        
        if 'rmse' in correlation_result:
            # Konvertuj RMSE u score (1 - rmse za better is higher)
            rmse_score = max(0, 1 - correlation_result['rmse'])
            metrics.append('RMSE Score')
            values.append(rmse_score)
            colors.append('orange')
    
    if metrics:
        bars = ax1.bar(metrics, values, color=colors, alpha=0.7)
        ax1.set_ylim(0, 1)
        ax1.set_title('Reconstruction Quality Metrics', fontweight='bold')
        ax1.set_ylabel('Score')
        ax1.grid(True, alpha=0.3, axis='y')
        
        # Dodaj vrednosti na barove
        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                    f'{value:.3f}', ha='center', va='bottom', fontweight='bold')
    else:
        ax1.text(0.5, 0.5, 'No correlation data available', 
                ha='center', va='center', transform=ax1.transAxes)
        ax1.set_title('Reconstruction Quality Metrics', fontweight='bold')
    
    # Panel 2: Quality assessment pie chart
    ax2 = fig.add_subplot(gs[3, 1])
    
    if correlation_result and 'correlation' in correlation_result:
        corr = correlation_result['correlation']
        
        # Kategorije kvaliteta
        if corr >= 0.9:
            quality = 'Odličan'
            color = 'green'
        elif corr >= 0.8:
            quality = 'Vrlo dobar'
            color = 'lightgreen'
        elif corr >= 0.7:
            quality = 'Dobar'
            color = 'yellow'
        elif corr >= 0.6:
            quality = 'Osrednji'
            color = 'orange'
        else:
            quality = 'Potrebno poboljšanje'
            color = 'red'
        
        # Pie chart sa quality assessment
        # Osiguraj da su values non-negative i u opsegu [0,1]
        corr_safe = max(0, min(1, abs(corr)))
        sizes = [corr_safe, 1-corr_safe] if corr_safe < 1 else [1]
        labels = [f'{quality}\n({corr:.1%})', 'Gap'] if corr_safe < 1 else [f'{quality}\n({corr:.1%})']
        colors_pie = [color, 'lightgray'] if corr_safe < 1 else [color]
        
        # Temporarily replace pie chart with bar chart to avoid errors
        ax2.bar([0, 1], [corr_safe, 1-corr_safe], color=colors_pie, width=0.6)
        ax2.set_xticks([0, 1])
        ax2.set_xticklabels(['Kvalitet', 'Gap'])
        ax2.set_ylim(0, 1)
        ax2.set_ylabel('Procenat')
        ax2.set_title('Kvalitet Rekonstrukcije', fontweight='bold')
    else:
        ax2.text(0.5, 0.5, 'No quality data', ha='center', va='center', transform=ax2.transAxes)
        ax2.set_title('Kvalitet Rekonstrukcije', fontweight='bold')
    
    # Panel 3: Summary tekstualni prikaz
    ax3 = fig.add_subplot(gs[3, 2])
    ax3.axis('off')
    
    summary_text = "SUMMARY IZVEŠTAJ\n\n"
    
    if correlation_result:
        if 'correlation' in correlation_result:
            corr = correlation_result['correlation']
            summary_text += f"• Korelacija: {corr:.3f}\n"
            
            if corr >= 0.9:
                summary_text += "• Status: ODLIČAN ✅\n"
                summary_text += "• Sistem spreman za production\n"
            elif corr >= 0.8:
                summary_text += "• Status: VRLO DOBAR ✅\n"
                summary_text += "• Minimalne optimizacije potrebne\n"
            elif corr >= 0.7:
                summary_text += "• Status: DOBAR ⚠️\n"
                summary_text += "• Potrebne optimizacije\n"
            else:
                summary_text += "• Status: POTREBNO POBOLJŠANJE ❌\n"
                summary_text += "• Značajne izmene potrebne\n"
        
        if 'rmse' in correlation_result:
            rmse = correlation_result['rmse']
            summary_text += f"• RMSE: {rmse:.3f}\n"
        
        if 'length_match' in correlation_result:
            length_match = correlation_result['length_match']
            summary_text += f"• Dužina signala: {'✅' if length_match else '⚠️'}\n"
    
    summary_text += "\nPREPORUKE:\n"
    if correlation_result and correlation_result.get('correlation', 0) >= 0.8:
        summary_text += "• Demonstracija mentoru ✅\n"
        summary_text += "• MIT-BIH validacija ✅\n"
        summary_text += "• Performance optimizacija"
    else:
        summary_text += "• Poboljšanje image processing\n"
        summary_text += "• Optimizacija edge detection\n"
        summary_text += "• Testiranje sa več slika"
    
    ax3.text(0.05, 0.95, summary_text, transform=ax3.transAxes, fontsize=10,
            verticalalignment='top', fontfamily='monospace',
            bbox=dict(boxstyle="round,pad=0.5", facecolor='lightblue', alpha=0.8))

def _save_plot_as_base64(fig):
    """Konvertuje matplotlib figuru u base64 string"""
    
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight', 
                facecolor='white', edgecolor='none')
    buf.seek(0)
    
    # Base64 encoding
    image_base64 = base64.b64encode(buf.read()).decode('utf-8')
    
    plt.close(fig)  # Oslobodi memoriju
    
    return {
        'image_base64': f"data:image/png;base64,{image_base64}",
        'width': fig.get_figwidth() * fig.dpi,
        'height': fig.get_figheight() * fig.dpi,
        'format': 'PNG'
    }

def create_batch_correlation_report(signal_image_pairs, fs=250):
    """
    Kreira batch report za multiple signal-image testove
    
    Args:
        signal_image_pairs: Lista (original_signal, extracted_signal) parova
        fs: Sampling frequency
    
    Returns:
        dict: Comprehensive batch analysis report
    """
    
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    
    correlations = []
    rmse_values = []
    similarity_scores = []
    
    # Analiziraj svaki par
    for i, (original, extracted) in enumerate(signal_image_pairs):
        # Normalizuj
        orig_norm = _normalize_signal(original)
        extr_norm = _normalize_signal(extracted)
        
        # Resample na istu dužinu
        min_len = min(len(orig_norm), len(extr_norm))
        orig_resampled = signal.resample(orig_norm, min_len)
        extr_resampled = signal.resample(extr_norm, min_len)
        
        # Korelacija
        corr = np.corrcoef(orig_resampled, extr_resampled)[0, 1]
        correlations.append(corr)
        
        # RMSE
        rmse = np.sqrt(np.mean((orig_resampled - extr_resampled)**2))
        rmse_values.append(rmse)
        
        # Similarity score
        similarity = corr * (1 - rmse)
        similarity_scores.append(similarity)
    
    # Plot 1: Correlation histogram
    axes[0, 0].hist(correlations, bins=10, alpha=0.7, color='blue', edgecolor='black')
    axes[0, 0].axvline(np.mean(correlations), color='red', linestyle='--', 
                       label=f'Mean: {np.mean(correlations):.3f}')
    axes[0, 0].set_title('Distribution of Correlations')
    axes[0, 0].set_xlabel('Correlation')
    axes[0, 0].set_ylabel('Frequency')
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)
    
    # Plot 2: RMSE histogram
    axes[0, 1].hist(rmse_values, bins=10, alpha=0.7, color='orange', edgecolor='black')
    axes[0, 1].axvline(np.mean(rmse_values), color='red', linestyle='--',
                       label=f'Mean: {np.mean(rmse_values):.3f}')
    axes[0, 1].set_title('Distribution of RMSE')
    axes[0, 1].set_xlabel('RMSE')
    axes[0, 1].set_ylabel('Frequency')
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)
    
    # Plot 3: Correlation vs RMSE scatter
    axes[1, 0].scatter(correlations, rmse_values, alpha=0.7, color='purple')
    axes[1, 0].set_xlabel('Correlation')
    axes[1, 0].set_ylabel('RMSE')
    axes[1, 0].set_title('Correlation vs RMSE')
    axes[1, 0].grid(True, alpha=0.3)
    
    # Plot 4: Summary statistics
    axes[1, 1].axis('off')
    
    stats_text = f"""BATCH ANALYSIS SUMMARY

Number of tests: {len(signal_image_pairs)}

CORRELATION:
• Mean: {np.mean(correlations):.3f}
• Std:  {np.std(correlations):.3f}
• Min:  {np.min(correlations):.3f}
• Max:  {np.max(correlations):.3f}

RMSE:
• Mean: {np.mean(rmse_values):.3f}
• Std:  {np.std(rmse_values):.3f}
• Min:  {np.min(rmse_values):.3f}
• Max:  {np.max(rmse_values):.3f}

QUALITY ASSESSMENT:
• Excellent (r>0.9): {sum(1 for c in correlations if c > 0.9)}
• Good (r>0.8):      {sum(1 for c in correlations if c > 0.8)}
• Fair (r>0.7):      {sum(1 for c in correlations if c > 0.7)}
• Poor (r<0.7):      {sum(1 for c in correlations if c < 0.7)}
"""
    
    axes[1, 1].text(0.05, 0.95, stats_text, transform=axes[1, 1].transAxes,
                    fontsize=10, verticalalignment='top', fontfamily='monospace',
                    bbox=dict(boxstyle="round,pad=0.5", facecolor='lightgreen', alpha=0.8))
    
    plt.tight_layout()
    plt.suptitle('Batch Correlation Analysis Report', fontsize=14, fontweight='bold')
    
    return _save_plot_as_base64(fig)

def generate_correlation_demo_for_mentor():
    """
    Generiše demonstration za mentora sa test podacima
    """
    
    # Kreiraj test podatke
    from .signal_to_image import create_normal_ekg_signal, create_tachycardia_signal
    
    # Normal EKG
    normal_signal, fs = create_normal_ekg_signal(duration=10, fs=250)
    
    # Simuliraj extraction proces (dodaj neki noise i distortion)
    extracted_signal = normal_signal + 0.1 * np.random.randn(len(normal_signal))
    extracted_signal = signal.resample(extracted_signal, int(len(normal_signal) * 0.95))  # Malo skrati
    
    # Kalkuliši korelaciju
    from .signal_to_image import compare_signals
    correlation_result = compare_signals(normal_signal, extracted_signal, fs)
    
    # Kreiraj vizualizaciju
    plot_result = create_correlation_analysis_plot(
        normal_signal, extracted_signal, fs, correlation_result
    )
    
    return {
        'correlation_plot': plot_result,
        'correlation_result': correlation_result,
        'test_info': {
            'original_length': len(normal_signal),
            'extracted_length': len(extracted_signal),
            'test_type': 'Normal EKG with simulated extraction noise'
        }
    }