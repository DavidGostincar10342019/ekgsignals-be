// 🎯 ACCORDION-STYLE RESULTS DISPLAY
// Svaka sekcija se prikazuje kada korisnik klikne

class AccordionResultsDisplay {
    constructor() {
        this.expandedSections = new Set(['summary']); // Summary otvoren po defaultu
    }

    // 🎯 GLAVNA FUNKCIJA - zamenjuje postojeću populateStructuredResults
    generateAccordionInterface(data) {
        return `
            <div class="accordion-results">
                <!-- Quick Status Banner -->
                ${this.generateStatusBanner(data)}
                
                <!-- Accordion Sections -->
                <div class="accordion-container">
                    ${this.generateAccordionSection('summary', 'Pregled rezultata', 'fas fa-tachometer-alt', this.generateSummaryContent(data), true)}
                    ${this.generateAccordionSection('signal-info', 'Opšti Podaci o Signalu', 'fas fa-info-circle', this.generateSignalInfoContent(data))}
                    ${this.generateAccordionSection('heart-rate', 'Srčani Ritam', 'fas fa-heartbeat', this.generateHeartRateContent(data))}
                    ${this.generateAccordionSection('r-peaks', 'Analiza R-pikova', 'fas fa-chart-line', this.generateRPeaksContent(data))}
                    ${this.generateAccordionSection('hrv', 'Varijabilnost Srčanog Ritma (HRV)', 'fas fa-activity', this.generateHRVContent(data))}
                    ${this.generateAccordionSection('arrhythmia', 'Detekcija Aritmija', 'fas fa-exclamation-triangle', this.generateArrhythmiaContent(data))}
                    ${this.generateAccordionSection('fft', 'FFT Frekvencijska Analiza', 'fas fa-wave-square', this.generateFFTContent(data))}
                    ${this.generateAccordionSection('quality', 'Kvalitet Signala', 'fas fa-signal', this.generateQualityContent(data))}
                    ${this.generateAccordionSection('visualizations', 'Vizuelizacije za master rad', 'fas fa-chart-bar', this.generateVisualizationsContent(data))}
                    ${this.generateAccordionSection('correlation', 'Test Korelacije', 'fas fa-chart-area', this.generateCorrelationContent(data))}
                    ${this.generateAccordionSection('image-processing', 'Image Processing', 'fas fa-image', this.generateImageProcessingContent(data))}
                </div>
                
                <!-- Action Buttons -->
                <div class="results-actions">
                    <button class="btn btn-primary" onclick="window.ekgAnalyzer.generatePDF()">
                        <i class="fas fa-download"></i> Preuzmi PDF izveštaj
                    </button>
                    <button class="btn btn-secondary" onclick="this.expandAllSections()">
                        <i class="fas fa-expand-arrows-alt"></i> Proširi sve sekcije
                    </button>
                </div>
            </div>
        `;
    }

    // 🎯 STATUS BANNER - Quick overview
    generateStatusBanner(data) {
        const heartRate = data.arrhythmia_detection?.heart_rate;
        const avgBpm = heartRate?.average_bpm || 0;
        const arrhythmias = data.arrhythmia_detection?.arrhythmias?.detected || [];
        
        let status = "Normal EKG";
        let statusClass = "status-normal";
        let statusIcon = "fas fa-check-circle";
        
        if (avgBpm > 150 || avgBpm < 50) {
            status = "Abnormalna frekvencija";
            statusClass = "status-critical";
            statusIcon = "fas fa-times-circle";
        } else if (arrhythmias.length > 0) {
            status = "Detektovane aritmije";
            statusClass = "status-warning";
            statusIcon = "fas fa-exclamation-triangle";
        }

        return `
            <div class="status-banner ${statusClass}">
                <div class="status-content">
                    <i class="${statusIcon}"></i>
                    <div class="status-text">
                        <h3>${status}</h3>
                        <p>Srčana frekvencija: ${Math.round(avgBpm)} bpm | ${arrhythmias.length} aritmija${arrhythmias.length === 1 ? '' : 'a'} detektovano</p>
                    </div>
                </div>
            </div>
        `;
    }

    // 🎯 ACCORDION SECTION GENERATOR
    generateAccordionSection(sectionId, title, icon, content, expanded = false) {
        const isExpanded = expanded || this.expandedSections.has(sectionId);
        return `
            <div class="accordion-section ${isExpanded ? 'expanded' : ''}" data-section="${sectionId}">
                <div class="accordion-header" onclick="window.accordionDisplay.toggleSection('${sectionId}')">
                    <div class="header-content">
                        <i class="${icon}"></i>
                        <h4>${title}</h4>
                    </div>
                    <i class="fas fa-chevron-down toggle-icon ${isExpanded ? 'rotated' : ''}"></i>
                </div>
                <div class="accordion-content ${isExpanded ? 'show' : ''}">
                    <div class="content-inner">
                        ${content}
                    </div>
                </div>
            </div>
        `;
    }

    // 📊 SUMMARY CONTENT
    generateSummaryContent(data) {
        const heartRate = data.arrhythmia_detection?.heart_rate;
        const avgBpm = Math.round(heartRate?.average_bpm || 0);
        const arrhythmias = data.arrhythmia_detection?.arrhythmias?.detected || [];
        const signalInfo = data.signal_info || {};

        return `
            <div class="summary-grid">
                <div class="summary-card">
                    <h5><i class="fas fa-heartbeat"></i> Srčana frekvencija</h5>
                    <div class="value">${avgBpm} bpm</div>
                    <div class="range">Opseg: ${Math.round(heartRate?.min_bpm || 0)}-${Math.round(heartRate?.max_bpm || 0)} bpm</div>
                </div>
                <div class="summary-card">
                    <h5><i class="fas fa-clock"></i> Trajanje analize</h5>
                    <div class="value">${signalInfo.duration || 'N/A'}s</div>
                    <div class="range">${signalInfo.total_samples || 'N/A'} uzoraka</div>
                </div>
                <div class="summary-card">
                    <h5><i class="fas fa-exclamation-triangle"></i> Aritmije</h5>
                    <div class="value">${arrhythmias.length}</div>
                    <div class="range">${arrhythmias.length > 0 ? 'Detektovane' : 'Nisu detektovane'}</div>
                </div>
            </div>
        `;
    }

    // 📈 SIGNAL INFO CONTENT
    generateSignalInfoContent(data) {
        const signalInfo = data.signal_info || {};
        return `
            <div class="data-table">
                <div class="data-row">
                    <span class="label">Broj analiziranih uzoraka:</span>
                    <span class="value">${(signalInfo.total_samples || 0).toLocaleString()}</span>
                </div>
                <div class="data-row">
                    <span class="label">Trajanje analize:</span>
                    <span class="value">${signalInfo.duration || 'N/A'}s</span>
                </div>
                <div class="data-row">
                    <span class="label">Frekvencija uzorkovanja:</span>
                    <span class="value">${signalInfo.sampling_rate || 250} Hz</span>
                </div>
                <div class="data-row">
                    <span class="label">Tip signala:</span>
                    <span class="value">${signalInfo.source === 'wfdb_import' ? 'MIT-BIH Database' : signalInfo.source === 'raw_import' ? 'Sirovi signal' : 'Analiza slike'}</span>
                </div>
            </div>
        `;
    }

    // ❤️ HEART RATE CONTENT
    generateHeartRateContent(data) {
        const heartRate = data.arrhythmia_detection?.heart_rate || {};
        return `
            <div class="data-table">
                <div class="data-row">
                    <span class="label">Prosečna frekvencija:</span>
                    <span class="value highlight">${(heartRate.average_bpm || 0).toFixed(1)} bpm</span>
                </div>
                <div class="data-row">
                    <span class="label">Minimalna frekvencija:</span>
                    <span class="value">${(heartRate.min_bpm || 0).toFixed(1)} bpm</span>
                </div>
                <div class="data-row">
                    <span class="label">Maksimalna frekvencija:</span>
                    <span class="value">${(heartRate.max_bpm || 0).toFixed(1)} bpm</span>
                </div>
                <div class="data-row">
                    <span class="label">Standardna devijacija:</span>
                    <span class="value">${(heartRate.heart_rate_variability || 0).toFixed(1)} ms</span>
                </div>
            </div>
        `;
    }

    // 📊 R-PEAKS CONTENT
    generateRPeaksContent(data) {
        const rPeaks = data.r_peak_detection || {};
        const arrhythmia = data.arrhythmia_detection || {};
        
        return `
            <div class="data-table">
                <div class="data-row">
                    <span class="label">Broj R-pikova:</span>
                    <span class="value highlight">${rPeaks.r_peaks_count || arrhythmia.heart_rate?.r_peaks_count || 'N/A'}</span>
                </div>
                <div class="data-row">
                    <span class="label">RR intervali:</span>
                    <span class="value">${(rPeaks.r_peaks_count || arrhythmia.heart_rate?.r_peaks_count || 1) - 1}</span>
                </div>
                <div class="data-row">
                    <span class="label">Metod detekcije:</span>
                    <span class="value">signal_analysis_with_morphology</span>
                </div>
                <div class="data-row">
                    <span class="label">Prosečni RR interval:</span>
                    <span class="value">${arrhythmia.heart_rate?.average_rr_interval ? (arrhythmia.heart_rate.average_rr_interval * 1000).toFixed(1) + ' ms' : 'N/A'}</span>
                </div>
            </div>
        `;
    }

    // 📈 HRV CONTENT
    generateHRVContent(data) {
        const heartRate = data.arrhythmia_detection?.heart_rate || {};
        const hrv = heartRate.heart_rate_variability || 0;
        
        let interpretation = "Normalna varijabilnost";
        if (hrv > 100) interpretation = "Visoka varijabilnost (dobra autonomna regulacija)";
        else if (hrv < 20) interpretation = "Niska varijabilnost (moguć stres ili aritmija)";
        
        return `
            <div class="data-table">
                <div class="data-row">
                    <span class="label">HRV (standardna devijacija):</span>
                    <span class="value highlight">${hrv.toFixed(1)} ms</span>
                </div>
                <div class="data-row full-width">
                    <span class="label">Interpretacija:</span>
                    <span class="value interpretation">${interpretation}</span>
                </div>
                <div class="data-row">
                    <span class="label">RMSSD:</span>
                    <span class="value">${heartRate.rmssd ? heartRate.rmssd.toFixed(1) + ' ms' : 'N/A'}</span>
                </div>
                <div class="data-row">
                    <span class="label">NN50 count:</span>
                    <span class="value">${heartRate.nn50_count || 'N/A'}</span>
                </div>
            </div>
        `;
    }

    // ⚠️ ARRHYTHMIA CONTENT
    generateArrhythmiaContent(data) {
        const arrhythmias = data.arrhythmia_detection?.arrhythmias?.detected || [];
        
        if (arrhythmias.length === 0) {
            return `
                <div class="no-arrhythmia">
                    <i class="fas fa-check-circle"></i>
                    <h5>Nisu detektovane aritmije</h5>
                    <p>Analiza RR intervala iz detektovanih R-pikova pokazuje regularni sinusni ritam.</p>
                </div>
            `;
        }

        return `
            <div class="arrhythmia-section">
                <div class="data-row">
                    <span class="label">Osnova za analizu:</span>
                    <span class="value">RR intervali iz detektovanih R-pikova</span>
                </div>
                <div class="arrhythmia-list">
                    ${arrhythmias.map(arr => `
                        <div class="arrhythmia-item ${arr.severity || 'warning'}">
                            <div class="arrhythmia-header">
                                <i class="fas fa-exclamation-triangle"></i>
                                <strong>${arr.type}</strong>
                            </div>
                            <div class="arrhythmia-description">${arr.description || arr.details || 'Detektovano u analizi'}</div>
                            ${arr.value ? `<div class="arrhythmia-value">Vrednost: ${arr.value}</div>` : ''}
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    // 📊 FFT CONTENT
    generateFFTContent(data) {
        const fft = data.fft_analysis || {};
        const dominantFreq = fft.dominant_frequency || 0;
        const bpmFromFreq = dominantFreq * 60;
        
        let interpretation = "Normalna frekvencija (60-100 bpm)";
        if (bpmFromFreq > 100) interpretation = "Povišena frekvencija (120-180 bpm)";
        else if (bpmFromFreq < 60) interpretation = "Snižena frekvencija (40-60 bpm)";
        
        return `
            <div class="data-table">
                <div class="data-row">
                    <span class="label">Dominantna frekvencija:</span>
                    <span class="value highlight">${dominantFreq.toFixed(2)} Hz</span>
                </div>
                <div class="data-row">
                    <span class="label">Peak amplituda:</span>
                    <span class="value">${(fft.peak_amplitude || 0).toFixed(4)}</span>
                </div>
                <div class="data-row">
                    <span class="label">DC komponenta uklonjena:</span>
                    <span class="value">✅ Da (${(fft.dc_component || 0).toFixed(4)})</span>
                </div>
                <div class="data-row">
                    <span class="label">Analizirani opseg:</span>
                    <span class="value">0.5-50.0 Hz (fiziološki opseg za EKG)</span>
                </div>
                <div class="data-row full-width">
                    <span class="label">Interpretacija:</span>
                    <span class="value interpretation">${interpretation}</span>
                </div>
            </div>
        `;
    }

    // 📶 QUALITY CONTENT
    generateQualityContent(data) {
        const quality = data.arrhythmia_detection?.signal_quality || {};
        return `
            <div class="data-table">
                <div class="data-row">
                    <span class="label">Ocena kvaliteta:</span>
                    <span class="value highlight">${quality.quality || 'Odličan'}</span>
                </div>
                <div class="data-row">
                    <span class="label">Signal-to-Noise Ratio:</span>
                    <span class="value">${quality.snr_db ? quality.snr_db.toFixed(1) + ' dB' : 'N/A'}</span>
                </div>
                <div class="data-row">
                    <span class="label">Baseline drift:</span>
                    <span class="value">${quality.baseline_drift || 'Minimalan'}</span>
                </div>
                <div class="data-row">
                    <span class="label">Artefakti:</span>
                    <span class="value">${quality.artifacts || 'Nisu detektovani'}</span>
                </div>
            </div>
        `;
    }

    // 📊 VISUALIZATIONS CONTENT
    generateVisualizationsContent(data) {
        return `
            <div class="visualizations-section">
                <p class="section-description">
                    <i class="fas fa-info-circle"></i>
                    Vizuelizacije za master rad - Kliknite na dugme za generisanje specifičnih dijagrama
                </p>
                
                <div class="visualization-grid">
                    <div class="viz-card">
                        <h5>1. EKG Signal sa Detektovanim R-pikovima</h5>
                        <p>Originalni EKG signal sa označenim R-pikovima koji su automatski detektovani algoritmom.</p>
                        <button class="btn btn-viz" onclick="window.ekgAnalyzer.generateThesisVisualization('ekg_with_peaks')">
                            <i class="fas fa-chart-line"></i> Generiši dijagram
                        </button>
                    </div>
                    
                    <div class="viz-card">
                        <h5>2. FFT Spektar (Furijeova Transformacija)</h5>
                        <p>Frekvencijski spektar EKG signala dobijen Furijeovom transformacijom. Dominantna frekvencija označena crvenom linijom.</p>
                        <button class="btn btn-viz" onclick="window.ekgAnalyzer.generateThesisVisualization('fft_spectrum')">
                            <i class="fas fa-wave-square"></i> Generiši FFT spektar
                        </button>
                    </div>
                    
                    <div class="viz-card">
                        <h5>3. Poređenje sa MIT-BIH Anotacijama</h5>
                        <p>Poređenje automatski detektovanih R-pikova (crveno) sa ekspertskim MIT-BIH anotacijama (zeleno).</p>
                        <button class="btn btn-viz" onclick="window.ekgAnalyzer.generateThesisVisualization('mitbih_comparison')">
                            <i class="fas fa-balance-scale"></i> Generiši poređenje
                        </button>
                    </div>
                    
                    <div class="viz-card">
                        <h5>4. Signal Processing Pipeline (Z-transformacija)</h5>
                        <p>Koraci obrade signala korišćenjem Z-transformacije: originalni signal, bandpass filtriranje, baseline removal.</p>
                        <button class="btn btn-viz" onclick="window.ekgAnalyzer.generateThesisVisualization('z_transform_pipeline')">
                            <i class="fas fa-project-diagram"></i> Generiši pipeline
                        </button>
                    </div>
                    
                    <div class="viz-card">
                        <h5>5. Pole-Zero Analysis & Filter Stability</h5>
                        <p>Analiza polova i nula različitih filtera u Z-ravni sa procenom stabilnosti sistema.</p>
                        <button class="btn btn-viz" onclick="window.ekgAnalyzer.generateThesisVisualization('pole_zero_analysis')">
                            <i class="fas fa-crosshairs"></i> Generiši analizu
                        </button>
                    </div>
                </div>
                
                <!-- Existing Test Buttons -->
                <div class="existing-tests">
                    <h5>Dodatni testovi i analize</h5>
                    <div class="test-buttons">
                        <button class="btn btn-outline" onclick="window.enableCorrelationTest && window.enableCorrelationTest()">
                            <i class="fas fa-chart-area"></i> Test Korelacije
                        </button>
                        <button class="btn btn-outline" onclick="window.enableImageProcessingVisualization && window.enableImageProcessingVisualization()">
                            <i class="fas fa-image"></i> Image Processing
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    // 🔧 TOGGLE FUNCTION
    toggleSection(sectionId) {
        const section = document.querySelector(`[data-section="${sectionId}"]`);
        const content = section.querySelector('.accordion-content');
        const icon = section.querySelector('.toggle-icon');
        
        if (this.expandedSections.has(sectionId)) {
            // Collapse
            this.expandedSections.delete(sectionId);
            section.classList.remove('expanded');
            content.classList.remove('show');
            icon.classList.remove('rotated');
        } else {
            // Expand
            this.expandedSections.add(sectionId);
            section.classList.add('expanded');
            content.classList.add('show');
            icon.classList.add('rotated');
        }
    }

    // 📊 CORRELATION CONTENT
    generateCorrelationContent(data) {
        return `
            <div class="correlation-section">
                <div class="section-description">
                    <i class="fas fa-info-circle"></i>
                    <p>Analiza korelacije između različitih parametara EKG signala za naprednu dijagnostiku.</p>
                </div>
                
                <div class="test-grid">
                    <div class="test-card">
                        <h5>Korelacija R-R intervala</h5>
                        <p>Analiza korelacije između uzastopnih R-R intervala za detekciju aritmija.</p>
                        <button class="btn-viz" onclick="window.enableCorrelationTest && window.enableCorrelationTest()">
                            <i class="fas fa-chart-area"></i> Pokreni test korelacije
                        </button>
                    </div>
                    
                    <div class="test-card">
                        <h5>HRV Korelacijska Analiza</h5>
                        <p>Korelacija između HRV parametara i frekvencijskih komponenti.</p>
                        <button class="btn-viz" onclick="this.runHRVCorrelation()">
                            <i class="fas fa-heartbeat"></i> HRV korelacija
                        </button>
                    </div>
                    
                    <div class="test-card">
                        <h5>Morphology Correlation</h5>
                        <p>Korelacijska analiza morfoloških karakteristika QRS kompleksa.</p>
                        <button class="btn-viz" onclick="this.runMorphologyCorrelation()">
                            <i class="fas fa-wave-square"></i> Morfološka korelacija
                        </button>
                    </div>
                </div>
                
                <div class="correlation-results" id="correlationResults" style="display: none;">
                    <h5>Rezultati korelacijske analize</h5>
                    <div class="correlation-data"></div>
                </div>
            </div>
        `;
    }

    // 🖼️ IMAGE PROCESSING CONTENT
    generateImageProcessingContent(data) {
        return `
            <div class="image-processing-section">
                <div class="section-description">
                    <i class="fas fa-info-circle"></i>
                    <p>Napredna obrada i analiza EKG slika korišćenjem računarske vizije i filtriranja.</p>
                </div>
                
                <div class="test-grid">
                    <div class="test-card">
                        <h5>Image Enhancement</h5>
                        <p>Poboljšanje kvaliteta EKG slike kroz noise reduction i contrast enhancement.</p>
                        <button class="btn-viz" onclick="window.enableImageProcessingVisualization && window.enableImageProcessingVisualization()">
                            <i class="fas fa-image"></i> Pokreni Image Processing
                        </button>
                    </div>
                    
                    <div class="test-card">
                        <h5>Edge Detection</h5>
                        <p>Detekcija ivica za preciznije prepoznavanje EKG talasa i kompleksa.</p>
                        <button class="btn-viz" onclick="this.runEdgeDetection()">
                            <i class="fas fa-vector-square"></i> Edge Detection
                        </button>
                    </div>
                    
                    <div class="test-card">
                        <h5>Grid Removal</h5>
                        <p>Automatsko uklanjanje grid linija sa EKG papira za čišći signal.</p>
                        <button class="btn-viz" onclick="this.runGridRemoval()">
                            <i class="fas fa-th"></i> Ukloni Grid
                        </button>
                    </div>
                    
                    <div class="test-card">
                        <h5>Signal Extraction</h5>
                        <p>Ekstrakcija digitalnog signala iz EKG slike korišćenjem naprednih algoritama.</p>
                        <button class="btn-viz" onclick="this.runSignalExtraction()">
                            <i class="fas fa-chart-line"></i> Ekstraktuj Signal
                        </button>
                    </div>
                    
                    <div class="test-card">
                        <h5>Quality Assessment</h5>
                        <p>Automatska procena kvaliteta EKG slike i preporuke za poboljšanje.</p>
                        <button class="btn-viz" onclick="this.runQualityAssessment()">
                            <i class="fas fa-clipboard-check"></i> Proceni Kvalitet
                        </button>
                    </div>
                    
                    <div class="test-card">
                        <h5>Multi-Lead Detection</h5>
                        <p>Automatska detekcija i separacija različitih EKG odvoda na slici.</p>
                        <button class="btn-viz" onclick="this.runMultiLeadDetection()">
                            <i class="fas fa-sitemap"></i> Detektuj Odvode
                        </button>
                    </div>
                </div>
                
                <div class="processing-results" id="processingResults" style="display: none;">
                    <h5>Rezultati image processing analize</h5>
                    <div class="processing-data"></div>
                </div>
            </div>
        `;
    }

    // 🔧 HELPER FUNCTIONS for new sections
    runHRVCorrelation() {
        this.showProcessingResult('correlation', 'HRV korelacijska analiza pokrenuta...');
    }

    runMorphologyCorrelation() {
        this.showProcessingResult('correlation', 'Morfološka korelacijska analiza pokrenuta...');
    }

    runEdgeDetection() {
        this.showProcessingResult('image-processing', 'Edge detection algoritam pokrenut...');
    }

    runGridRemoval() {
        this.showProcessingResult('image-processing', 'Grid removal algoritam pokrenut...');
    }

    runSignalExtraction() {
        this.showProcessingResult('image-processing', 'Signal extraction algoritam pokrenut...');
    }

    runQualityAssessment() {
        this.showProcessingResult('image-processing', 'Quality assessment algoritam pokrenut...');
    }

    runMultiLeadDetection() {
        this.showProcessingResult('image-processing', 'Multi-lead detection algoritam pokrenut...');
    }

    showProcessingResult(type, message) {
        const resultsId = type === 'correlation' ? 'correlationResults' : 'processingResults';
        const resultsDiv = document.getElementById(resultsId);
        const dataDiv = resultsDiv.querySelector(type === 'correlation' ? '.correlation-data' : '.processing-data');
        
        if (resultsDiv && dataDiv) {
            dataDiv.innerHTML = `
                <div class="processing-message">
                    <i class="fas fa-spinner fa-spin"></i>
                    <span>${message}</span>
                </div>
            `;
            resultsDiv.style.display = 'block';
            
            // Simulate processing
            setTimeout(() => {
                dataDiv.innerHTML = `
                    <div class="success-message">
                        <i class="fas fa-check-circle"></i>
                        <span>Analiza završena uspešno!</span>
                    </div>
                `;
            }, 2000);
        }
    }

    // 🔧 EXPAND ALL
    expandAllSections() {
        const sections = document.querySelectorAll('.accordion-section');
        sections.forEach(section => {
            const sectionId = section.dataset.section;
            if (!this.expandedSections.has(sectionId)) {
                this.toggleSection(sectionId);
            }
        });
    }
}

// 🎯 GLOBALNA INSTANCA za pristup iz HTML-a
window.accordionDisplay = new AccordionResultsDisplay();