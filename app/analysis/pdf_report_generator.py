"""
PDF Report Generator za EKG analizu
Generiše profesionalne PDF izveštaje sa dijagramima i objašnjenjima
"""

import io
import base64
import os
import tempfile
from datetime import datetime
import numpy as np

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from reportlab.graphics.shapes import Drawing
    from reportlab.graphics.charts.lineplots import LinePlot
    from reportlab.graphics.charts.linecharts import HorizontalLineChart
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from matplotlib.backends.backend_pdf import PdfPages
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

class EKGPDFReportGenerator:
    """Generiše profesionalne PDF izveštaje za EKG analizu"""
    
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp()
        
    def generate_comprehensive_pdf_report(self, signal_data, fs, analysis_results, 
                                        report_title="EKG Analiza Report", 
                                        patient_info=None, include_images=True):
        """
        Generiše kompletni PDF izveštaj sa svim analizama i dijagramima
        
        Args:
            signal_data: numpy array sa EKG signalom
            fs: frekvencija uzorkovanja
            analysis_results: dictionary sa rezultatima svih analiza
            report_title: naslov izveštaja
            patient_info: informacije o pacijentu (optional)
            include_images: da li uključiti dijagrame
        
        Returns:
            bytes: PDF sadržaj ili error dictionary
        """
        
        if not REPORTLAB_AVAILABLE or not MATPLOTLIB_AVAILABLE:
            return {"error": "PDF generisanje nije dostupno - nedostaju biblioteke"}
        
        try:
            # Kreiraj PDF dokument
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(
                buffer, 
                pagesize=A4,
                rightMargin=72, 
                leftMargin=72,
                topMargin=72, 
                bottomMargin=18
            )
            
            # Lista elemenata za PDF
            story = []
            styles = getSampleStyleSheet()
            
            # Custom stilovi
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=18,
                spaceAfter=30,
                alignment=1,  # Center
                textColor=colors.HexColor('#2E86AB')
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=14,
                spaceAfter=12,
                textColor=colors.HexColor('#A23B72')
            )
            
            # 1. NASLOVNICA
            story.append(Paragraph(report_title, title_style))
            story.append(Spacer(1, 20))
            
            # Informacije o analizi
            analysis_info = [
                ['Datum analize:', datetime.now().strftime('%d.%m.%Y %H:%M')],
                ['Trajanje signala:', f'{len(signal_data)/fs:.2f} sekundi'],
                ['Broj uzoraka:', str(len(signal_data))],
                ['Frekvencija uzorkovanja:', f'{fs} Hz'],
                ['Verzija softvera:', 'EKG Analyzer v3.1']
            ]
            
            # Dodaj informacije o pacijentu ako postoje
            if patient_info:
                patient_table = [
                    ['INFORMACIJE O PACIJENTU', ''],
                    ['Ime:', patient_info.get('name', 'N/A')],
                    ['Uzrast:', patient_info.get('age', 'N/A')],
                    ['Pol:', patient_info.get('gender', 'N/A')],
                    ['ID:', patient_info.get('patient_id', 'N/A')]
                ]
                analysis_info = patient_table + [['', '']] + analysis_info
            
            info_table = Table(analysis_info, colWidths=[2*inch, 3*inch])
            info_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E8F4FD')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#2E86AB')),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(info_table)
            story.append(Spacer(1, 30))
            
            # 2. IZVRŠNI REZIME
            story.append(Paragraph("IZVRŠNI REZIME", heading_style))
            
            # Generiši rezime na osnovu analiza
            summary_text = self._generate_executive_summary(analysis_results)
            story.append(Paragraph(summary_text, styles['Normal']))
            story.append(Spacer(1, 20))
            
            # 3. DIJAGRAMI (ako su uključeni)
            if include_images and signal_data is not None:
                story.append(PageBreak())
                story.append(Paragraph("SIGNAL I DIJAGRAMI", heading_style))
                
                # 3.1 Time Domain signal
                time_domain_img = self._create_time_domain_plot(signal_data, fs, analysis_results)
                if time_domain_img:
                    story.append(Paragraph("1. EKG Signal u Vremenskom Domenu", styles['Heading3']))
                    story.append(time_domain_img)
                    story.append(Spacer(1, 20))
                
                # 3.2 FFT Spektar
                if 'fft_analysis' in analysis_results:
                    fft_img = self._create_fft_spectrum_plot(signal_data, fs, analysis_results['fft_analysis'])
                    if fft_img:
                        story.append(Paragraph("2. FFT Spektralna Analiza", styles['Heading3']))
                        story.append(fft_img)
                        story.append(Spacer(1, 20))
                
                # 3.3 Z-plane diagram
                if 'z_transform' in analysis_results:
                    z_plane_img = self._create_z_plane_plot(analysis_results['z_transform'])
                    if z_plane_img:
                        story.append(Paragraph("3. Z-ravan Analiza", styles['Heading3']))
                        story.append(z_plane_img)
                        story.append(Spacer(1, 20))
            
            # 4. DETALJNI REZULTATI
            story.append(PageBreak())
            story.append(Paragraph("DETALJNI REZULTATI ANALIZE", heading_style))
            
            # 4.1 FFT Analiza
            if 'fft_analysis' in analysis_results:
                story.extend(self._create_fft_analysis_section(analysis_results['fft_analysis']))
            
            # 4.2 Z-Transform Analiza
            if 'z_transform' in analysis_results:
                story.extend(self._create_z_transform_section(analysis_results['z_transform']))
            
            # 4.3 Arrhythmia Detection
            if 'arrhythmia_detection' in analysis_results:
                story.extend(self._create_arrhythmia_section(analysis_results['arrhythmia_detection']))
            
            # 5. ZAKLJUČCI I PREPORUKE
            story.append(PageBreak())
            story.append(Paragraph("ZAKLJUČCI I PREPORUKE", heading_style))
            
            conclusions = self._generate_conclusions(analysis_results)
            story.append(Paragraph(conclusions, styles['Normal']))
            
            # 6. NAPOMENE I DISCLAIMER
            story.append(Spacer(1, 30))
            story.append(Paragraph("NAPOMENE", heading_style))
            
            disclaimer = """
            <b>VAŽNO:</b> Ovaj izveštaj je generisan automatski putem algoritama za analizu EKG signala 
            i služi isključivo u edukativne svrhe. Rezultati NE PREDSTAVLJAJU medicinsku dijagnozu 
            i ne treba ih koristiti za donošenje medicinskih odluka. Za medicinsku interpretaciju 
            EKG-a uvek konsultujte kvalifikovane zdravstvene radnike.<br/><br/>
            
            <b>Algoritmi korišćeni:</b><br/>
            • FFT analiza prema NumPy dokumentaciji (Harris et al., 2020)<br/>
            • Z-transformacija prema SciPy implementaciji (Virtanen et al., 2020)<br/>
            • R-peak detekcija koristeći SciPy find_peaks algoritam<br/>
            • Signal Complexity Measure (modificirana Acharya et al., 2018 formula)<br/><br/>
            
            <b>Verzija softvera:</b> EKG Analyzer v3.1<br/>
            <b>Datum generisanja:</b> """ + datetime.now().strftime('%d.%m.%Y %H:%M:%S')
            
            story.append(Paragraph(disclaimer, styles['Normal']))
            
            # Generiši PDF
            doc.build(story)
            
            # Vrati PDF kao bytes
            pdf_value = buffer.getvalue()
            buffer.close()
            
            return pdf_value
            
        except Exception as e:
            return {"error": f"Greška pri generisanju PDF-a: {str(e)}"}
    
    def _generate_executive_summary(self, analysis_results):
        """Generiše izvršni rezime na osnovu rezultata analize"""
        
        summary_parts = []
        
        # FFT analiza rezime
        if 'fft_analysis' in analysis_results:
            fft = analysis_results['fft_analysis']
            peak_freq = fft.get('peak_frequency_hz', 'N/A')
            summary_parts.append(f"<b>Frekvencijska analiza:</b> Dominantna frekvencija {peak_freq} Hz.")
        
        # Arrhythmia analiza rezime
        if 'arrhythmia_detection' in analysis_results:
            arr = analysis_results['arrhythmia_detection']
            heart_rate = arr.get('heart_rate', {}).get('average_bpm', 'N/A')
            rhythm = arr.get('rhythm_classification', 'nepoznat')
            summary_parts.append(f"<b>Srčani ritam:</b> {heart_rate} bpm, klasifikacija: {rhythm}.")
        
        # Z-transform analiza rezime
        if 'z_transform' in analysis_results:
            zt = analysis_results['z_transform']
            stability = zt.get('stability', {}).get('stable', False)
            stability_text = "stabilan" if stability else "nestabilan"
            summary_parts.append(f"<b>Z-transformacija:</b> Sistem je {stability_text}.")
        
        if not summary_parts:
            return "Analiza je završena uspešno. Detaljni rezultati su prikazani u sledećim sekcijama."
        
        return " ".join(summary_parts)
    
    def _create_time_domain_plot(self, signal_data, fs, analysis_results):
        """Kreira time domain plot kao ReportLab Image"""
        
        try:
            # Kreiraj matplotlib plot
            fig, ax = plt.subplots(figsize=(10, 4))
            
            time_axis = np.arange(len(signal_data)) / fs
            ax.plot(time_axis, signal_data, 'b-', linewidth=1.5, label='EKG Signal')
            
            # Dodaj R-peaks ako postoje
            if 'arrhythmia_detection' in analysis_results:
                r_peaks = analysis_results['arrhythmia_detection'].get('r_peaks', [])
                if r_peaks:
                    r_peak_times = np.array(r_peaks) / fs
                    r_peak_values = signal_data[r_peaks]
                    ax.plot(r_peak_times, r_peak_values, 'ro', markersize=6, label='R-peaks')
            
            ax.set_xlabel('Vreme (s)')
            ax.set_ylabel('Amplituda')
            ax.set_title('EKG Signal u Vremenskom Domenu')
            ax.grid(True, alpha=0.3)
            ax.legend()
            
            # Sačuvaj kao sliku
            img_path = os.path.join(self.temp_dir, 'time_domain.png')
            plt.savefig(img_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            # Kreiraj ReportLab Image
            img = Image(img_path, width=6*inch, height=2.4*inch)
            return img
            
        except Exception as e:
            print(f"Error creating time domain plot: {e}")
            return None
    
    def _create_fft_spectrum_plot(self, signal_data, fs, fft_results):
        """Kreira FFT spektar plot"""
        
        try:
            fig, ax = plt.subplots(figsize=(10, 4))
            
            # Kreiraj FFT
            n = len(signal_data)
            freq = np.fft.rfftfreq(n, d=1.0/fs)
            spectrum = np.abs(np.fft.rfft(signal_data - np.mean(signal_data))) / n
            
            ax.plot(freq, spectrum, 'g-', linewidth=1.5)
            
            # Označi peak frekvenciju
            peak_freq = fft_results.get('peak_frequency_hz', 0)
            if peak_freq > 0:
                ax.axvline(x=peak_freq, color='r', linestyle='--', 
                          label=f'Peak: {peak_freq:.2f} Hz')
            
            ax.set_xlabel('Frekvencija (Hz)')
            ax.set_ylabel('Amplituda')
            ax.set_title('FFT Spektralna Analiza')
            ax.grid(True, alpha=0.3)
            ax.set_xlim(0, 50)  # EKG opseg
            ax.legend()
            
            # Sačuvaj kao sliku
            img_path = os.path.join(self.temp_dir, 'fft_spectrum.png')
            plt.savefig(img_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            return Image(img_path, width=6*inch, height=2.4*inch)
            
        except Exception as e:
            print(f"Error creating FFT plot: {e}")
            return None
    
    def _create_z_plane_plot(self, z_transform_results):
        """Kreira Z-plane pole-zero plot"""
        
        try:
            fig, ax = plt.subplots(figsize=(6, 6))
            
            # Unit circle
            theta = np.linspace(0, 2*np.pi, 100)
            ax.plot(np.cos(theta), np.sin(theta), 'k--', alpha=0.5, label='Unit Circle')
            
            # Polovi
            poles = z_transform_results.get('poles', [])
            if poles:
                poles_array = np.array(poles)
                if np.iscomplexobj(poles_array):
                    ax.plot(poles_array.real, poles_array.imag, 'rx', markersize=10, 
                           markeredgewidth=2, label='Poles')
                else:
                    ax.plot(poles_array, np.zeros_like(poles_array), 'rx', markersize=10,
                           markeredgewidth=2, label='Poles')
            
            # Nule
            zeros = z_transform_results.get('zeros', [])
            if zeros:
                zeros_array = np.array(zeros)
                if np.iscomplexobj(zeros_array):
                    ax.plot(zeros_array.real, zeros_array.imag, 'bo', markersize=8,
                           label='Zeros')
                else:
                    ax.plot(zeros_array, np.zeros_like(zeros_array), 'bo', markersize=8,
                           label='Zeros')
            
            ax.set_xlabel('Real deo')
            ax.set_ylabel('Imaginarni deo')
            ax.set_title('Z-ravan Pole-Zero Dijagram')
            ax.grid(True, alpha=0.3)
            ax.axis('equal')
            ax.legend()
            ax.set_xlim(-1.5, 1.5)
            ax.set_ylim(-1.5, 1.5)
            
            # Sačuvaj kao sliku
            img_path = os.path.join(self.temp_dir, 'z_plane.png')
            plt.savefig(img_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            return Image(img_path, width=4*inch, height=4*inch)
            
        except Exception as e:
            print(f"Error creating Z-plane plot: {e}")
            return None
    
    def _create_fft_analysis_section(self, fft_results):
        """Kreira sekciju sa FFT analizom"""
        
        styles = getSampleStyleSheet()
        elements = []
        
        elements.append(Paragraph("FFT Spektralna Analiza", styles['Heading3']))
        
        # Tabela sa rezultatima
        fft_data = [
            ['Parameter', 'Vrednost', 'Interpretacija'],
            ['Peak frekvencija', f"{fft_results.get('peak_frequency_hz', 'N/A')} Hz", 'Dominantna frekvencija u signalu'],
            ['Peak amplituda', f"{fft_results.get('peak_amplitude', 'N/A')}", 'Jačina dominantne komponente'],
        ]
        
        # Dodaj THD ako postoji
        if 'sine_wave_analysis' in fft_results:
            sine_analysis = fft_results['sine_wave_analysis']
            thd = sine_analysis.get('thd_percent', 'N/A')
            spectral_purity = sine_analysis.get('spectral_purity_percent', 'N/A')
            
            fft_data.extend([
                ['THD', f"{thd}%", 'Total Harmonic Distortion'],
                ['Spektralna čistoća', f"{spectral_purity}%", 'Čistoća osnovne frekvencije']
            ])
        
        fft_table = Table(fft_data, colWidths=[2*inch, 1.5*inch, 2.5*inch])
        fft_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(fft_table)
        elements.append(Spacer(1, 20))
        
        return elements
    
    def _create_z_transform_section(self, z_transform_results):
        """Kreira sekciju sa Z-transform analizom"""
        
        styles = getSampleStyleSheet()
        elements = []
        
        elements.append(Paragraph("Z-Transformacija Analiza", styles['Heading3']))
        
        # Stabilnost
        stability = z_transform_results.get('stability', {})
        is_stable = stability.get('stable', False)
        max_pole_mag = stability.get('max_pole_magnitude', 'N/A')
        
        z_data = [
            ['Parameter', 'Vrednost', 'Interpretacija'],
            ['Stabilnost sistema', 'Stabilan' if is_stable else 'Nestabilan', 
             'Svi polovi unutar jediničnog kruga' if is_stable else 'Neki polovi van jediničnog kruga'],
            ['Max. magnituda pola', f"{max_pole_mag}", 'Mora biti < 1 za stabilnost'],
            ['Broj polova', str(len(z_transform_results.get('poles', []))), 'Broj polova transfer funkcije'],
            ['Broj nula', str(len(z_transform_results.get('zeros', []))), 'Broj nula transfer funkcije']
        ]
        
        z_table = Table(z_data, colWidths=[2*inch, 1.5*inch, 2.5*inch])
        z_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(z_table)
        elements.append(Spacer(1, 20))
        
        return elements
    
    def _create_arrhythmia_section(self, arrhythmia_results):
        """Kreira sekciju sa arrhythmia analizom"""
        
        styles = getSampleStyleSheet()
        elements = []
        
        elements.append(Paragraph("Analiza Srčanog Ritma", styles['Heading3']))
        
        # Heart rate podaci
        heart_rate = arrhythmia_results.get('heart_rate', {})
        avg_bpm = heart_rate.get('average_bpm', 'N/A')
        hrv = heart_rate.get('heart_rate_variability', 'N/A')
        
        arr_data = [
            ['Parameter', 'Vrednost', 'Normalne vrednosti'],
            ['Prosečna srčana frekvencija', f"{avg_bpm} bpm", '60-100 bpm (u mirovanju)'],
            ['HRV (RMSSD)', f"{hrv} ms", '20-50 ms'],
            ['Broj detektovanih R-pikova', str(len(arrhythmia_results.get('r_peaks', []))), 'Zavisi od trajanja'],
            ['Klasifikacija ritma', arrhythmia_results.get('rhythm_classification', 'N/A'), 'Normalan sinusni ritam']
        ]
        
        arr_table = Table(arr_data, colWidths=[2.5*inch, 1.5*inch, 2*inch])
        arr_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(arr_table)
        elements.append(Spacer(1, 20))
        
        return elements
    
    def _generate_conclusions(self, analysis_results):
        """Generiše zaključke na osnovu svih analiza"""
        
        conclusions = []
        
        # FFT zaključci
        if 'fft_analysis' in analysis_results:
            fft = analysis_results['fft_analysis']
            peak_freq = fft.get('peak_frequency_hz', 0)
            if 0.5 <= peak_freq <= 3.0:
                conclusions.append("FFT analiza pokazuje dominantnu frekvenciju u normalnom opsegu za EKG signale.")
            else:
                conclusions.append("FFT analiza pokazuje neočekivanu dominantnu frekvenciju - možda prisutan šum.")
        
        # Arrhythmia zaključci
        if 'arrhythmia_detection' in analysis_results:
            arr = analysis_results['arrhythmia_detection']
            avg_bpm = arr.get('heart_rate', {}).get('average_bpm', 0)
            if 60 <= avg_bpm <= 100:
                conclusions.append("Srčana frekvencija je u normalnom opsegu.")
            elif avg_bpm < 60:
                conclusions.append("Detektovana je bradikardija (sporiji srčani ritam).")
            elif avg_bpm > 100:
                conclusions.append("Detektovana je tahikardija (ubrzani srčani ritam).")
        
        # Z-transform zaključci
        if 'z_transform' in analysis_results:
            zt = analysis_results['z_transform']
            if zt.get('stability', {}).get('stable', False):
                conclusions.append("Z-transformacija potvrđuje stabilnost signala.")
            else:
                conclusions.append("Z-transformacija ukazuje na nestabilnost - potrebna dodatna analiza.")
        
        if not conclusions:
            conclusions.append("Analiza je uspešno završena. Svi parametri su izmeren i prikazani u tabelalma.")
        
        return "<br/>".join(conclusions)
    
    def cleanup(self):
        """Obriši privremene fajlove"""
        try:
            import shutil
            shutil.rmtree(self.temp_dir)
        except:
            pass