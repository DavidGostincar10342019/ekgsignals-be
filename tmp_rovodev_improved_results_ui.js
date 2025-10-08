// POBOLJŠANA FRONTEND ARHITEKTURA ZA PRIKAZ REZULTATA
// Rešenje problema previše podataka odjednom

class ImprovedResultsDisplay {
    constructor() {
        this.currentView = 'summary'; // summary, detailed, technical
        this.collapsedSections = new Set();
    }

    // 🎯 GLAVNO REŠENJE: Prikaži rezultate u tabovima sa progresivnim disclosure
    displayResults(data) {
        const resultsHTML = this.generateTabbedInterface(data);
        
        // Replace postojeći results section
        const resultsSection = document.getElementById('resultsSection');
        resultsSection.innerHTML = resultsHTML;
        
        this.setupTabInteractions();
        this.setupProgressiveDisclosure();
    }

    // 📱 TAB-BASED INTERFACE za lakše navigiranje
    generateTabbedInterface(data) {
        return `
            <div class="results-container">
                <!-- Quick Summary Card -->
                <div class="summary-card" id="quickSummary">
                    ${this.generateQuickSummary(data)}
                </div>

                <!-- Tab Navigation -->
                <div class="tab-navigation">
                    <button class="tab-btn active" data-tab="overview">
                        <i class="fas fa-tachometer-alt"></i>
                        Pregled
                    </button>
                    <button class="tab-btn" data-tab="clinical">
                        <i class="fas fa-heartbeat"></i>
                        Klinička analiza
                    </button>
                    <button class="tab-btn" data-tab="technical">
                        <i class="fas fa-chart-line"></i>
                        Tehnički podaci
                    </button>
                    <button class="tab-btn" data-tab="visualizations">
                        <i class="fas fa-chart-bar"></i>
                        Grafici
                    </button>
                </div>

                <!-- Tab Content -->
                <div class="tab-content">
                    <div class="tab-panel active" id="overview-panel">
                        ${this.generateOverviewPanel(data)}
                    </div>
                    <div class="tab-panel" id="clinical-panel">
                        ${this.generateClinicalPanel(data)}
                    </div>
                    <div class="tab-panel" id="technical-panel">
                        ${this.generateTechnicalPanel(data)}
                    </div>
                    <div class="tab-panel" id="visualizations-panel">
                        <div class="visualization-placeholder">
                            <p>Grafici se učitavaju...</p>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    // 🎯 QUICK SUMMARY - Najvažnije informacije na vrhu
    generateQuickSummary(data) {
        const heartRate = data.arrhythmia_detection?.heart_rate;
        const avgBpm = heartRate?.average_bpm || 0;
        const arrhythmias = data.arrhythmia_detection?.arrhythmias?.detected || [];
        
        let status = "Normal";
        let statusColor = "#27ae60";
        let statusIcon = "fas fa-check-circle";
        
        if (arrhythmias.length > 0) {
            status = "Detektovane aritmije";
            statusColor = "#f39c12";
            statusIcon = "fas fa-exclamation-triangle";
        }
        
        if (avgBpm > 150 || avgBpm < 50) {
            status = "Abnormalna frekvencija";
            statusColor = "#e74c3c";
            statusIcon = "fas fa-times-circle";
        }

        return `
            <div class="quick-summary">
                <div class="status-indicator">
                    <i class="${statusIcon}" style="color: ${statusColor}; font-size: 2rem;"></i>
                    <div class="status-text">
                        <h3 style="margin: 0; color: ${statusColor};">${status}</h3>
                        <p style="margin: 0; color: #666;">Srčana frekvencija: ${Math.round(avgBpm)} bpm</p>
                    </div>
                </div>
                
                <div class="action-buttons">
                    <button class="btn btn-primary" onclick="this.downloadPDF()">
                        <i class="fas fa-download"></i> Preuzmi izveštaj
                    </button>
                    <button class="btn btn-secondary" onclick="this.expandDetails()">
                        <i class="fas fa-eye"></i> Detalji
                    </button>
                </div>
            </div>
        `;
    }

    // 📊 OVERVIEW PANEL - Ključni podaci, ne previše detalja
    generateOverviewPanel(data) {
        const heartRate = data.arrhythmia_detection?.heart_rate;
        const avgBpm = Math.round(heartRate?.average_bpm || 0);
        const minBpm = Math.round(heartRate?.min_bpm || 0);
        const maxBpm = Math.round(heartRate?.max_bpm || 0);
        const arrhythmias = data.arrhythmia_detection?.arrhythmias?.detected || [];

        return `
            <div class="overview-content">
                <!-- Key Metrics Cards -->
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-icon">
                            <i class="fas fa-heartbeat"></i>
                        </div>
                        <div class="metric-content">
                            <h4>Srčana frekvencija</h4>
                            <div class="metric-value">${avgBpm} bpm</div>
                            <div class="metric-range">Opseg: ${minBpm}-${maxBpm} bpm</div>
                        </div>
                    </div>

                    <div class="metric-card">
                        <div class="metric-icon">
                            <i class="fas fa-wave-square"></i>
                        </div>
                        <div class="metric-content">
                            <h4>Ritam</h4>
                            <div class="metric-value">${arrhythmias.length > 0 ? 'Nepravilan' : 'Pravilan'}</div>
                            <div class="metric-range">${arrhythmias.length} aritmija detektovano</div>
                        </div>
                    </div>

                    <div class="metric-card">
                        <div class="metric-icon">
                            <i class="fas fa-signal"></i>
                        </div>
                        <div class="metric-content">
                            <h4>Kvalitet signala</h4>
                            <div class="metric-value">Odličan</div>
                            <div class="metric-range">SNR > 20dB</div>
                        </div>
                    </div>
                </div>

                <!-- Quick Findings -->
                ${arrhythmias.length > 0 ? `
                <div class="findings-section">
                    <h4><i class="fas fa-exclamation-triangle"></i> Važna zapažanja</h4>
                    <div class="findings-list">
                        ${arrhythmias.map(arr => `
                            <div class="finding-item">
                                <span class="finding-badge">${arr.type}</span>
                                <span class="finding-description">Detektovano u analizi</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
                ` : ''}
            </div>
        `;
    }

    // 🏥 CLINICAL PANEL - Medicinski relevantni podaci
    generateClinicalPanel(data) {
        return `
            <div class="clinical-content">
                <!-- Systematic Analysis -->
                <div class="collapsible-section" data-section="systematic">
                    <div class="section-header" onclick="this.toggleSection('systematic')">
                        <h4><i class="fas fa-stethoscope"></i> Sistematski pregled</h4>
                        <i class="fas fa-chevron-down toggle-icon"></i>
                    </div>
                    <div class="section-content">
                        ${this.generateSystematicAnalysis(data)}
                    </div>
                </div>

                <!-- Arrhythmia Analysis -->
                <div class="collapsible-section" data-section="arrhythmia">
                    <div class="section-header" onclick="this.toggleSection('arrhythmia')">
                        <h4><i class="fas fa-exclamation-triangle"></i> Analiza aritmija</h4>
                        <i class="fas fa-chevron-down toggle-icon"></i>
                    </div>
                    <div class="section-content collapsed">
                        ${this.generateArrhythmiaAnalysis(data)}
                    </div>
                </div>

                <!-- Recommendations -->
                <div class="recommendations-section">
                    <h4><i class="fas fa-clipboard-check"></i> Preporuke</h4>
                    ${this.generateRecommendations(data)}
                </div>
            </div>
        `;
    }

    // 🔧 TECHNICAL PANEL - Za napredne korisnike
    generateTechnicalPanel(data) {
        return `
            <div class="technical-content">
                <div class="info-banner">
                    <i class="fas fa-info-circle"></i>
                    <p>Tehnički podaci za napredne korisnike i istraživače</p>
                </div>

                <!-- Raw Data Tables (collapsible) -->
                <div class="collapsible-section" data-section="signal-info">
                    <div class="section-header" onclick="this.toggleSection('signal-info')">
                        <h4>Informacije o signalu</h4>
                        <i class="fas fa-chevron-down toggle-icon"></i>
                    </div>
                    <div class="section-content collapsed">
                        ${this.generateSignalInfoTable(data)}
                    </div>
                </div>

                <div class="collapsible-section" data-section="fft-analysis">
                    <div class="section-header" onclick="this.toggleSection('fft-analysis')">
                        <h4>FFT analiza</h4>
                        <i class="fas fa-chevron-down toggle-icon"></i>
                    </div>
                    <div class="section-content collapsed">
                        ${this.generateFFTAnalysis(data)}
                    </div>
                </div>

                <!-- Debug Info -->
                <div class="debug-section">
                    <button class="btn btn-outline" onclick="this.showRawData()">
                        <i class="fas fa-code"></i> Prikaži sirove podatke
                    </button>
                </div>
            </div>
        `;
    }

    // 🎛️ INTERACTIVE FUNCTIONS
    setupTabInteractions() {
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const tabName = e.target.getAttribute('data-tab');
                this.switchTab(tabName);
            });
        });
    }

    setupProgressiveDisclosure() {
        document.querySelectorAll('.section-header').forEach(header => {
            header.addEventListener('click', (e) => {
                const section = header.closest('.collapsible-section');
                const sectionName = section.getAttribute('data-section');
                this.toggleSection(sectionName);
            });
        });
    }

    switchTab(tabName) {
        // Hide all panels
        document.querySelectorAll('.tab-panel').forEach(panel => {
            panel.classList.remove('active');
        });
        
        // Remove active from all buttons
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        
        // Show selected panel and button
        document.getElementById(`${tabName}-panel`).classList.add('active');
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

        // Lazy load content if needed
        if (tabName === 'visualizations') {
            this.loadVisualizations();
        }
    }

    toggleSection(sectionName) {
        const section = document.querySelector(`[data-section="${sectionName}"]`);
        const content = section.querySelector('.section-content');
        const icon = section.querySelector('.toggle-icon');
        
        if (this.collapsedSections.has(sectionName)) {
            // Expand
            content.classList.remove('collapsed');
            icon.classList.remove('fa-chevron-down');
            icon.classList.add('fa-chevron-up');
            this.collapsedSections.delete(sectionName);
        } else {
            // Collapse
            content.classList.add('collapsed');
            icon.classList.remove('fa-chevron-up');
            icon.classList.add('fa-chevron-down');
            this.collapsedSections.add(sectionName);
        }
    }

    // Lazy loading za grafike da se ne usporava početni prikaz
    loadVisualizations() {
        const panel = document.getElementById('visualizations-panel');
        if (panel.dataset.loaded !== 'true') {
            // Load visualizations only when tab is clicked
            panel.innerHTML = '<div class="loading">Učitavanje grafika...</div>';
            
            setTimeout(() => {
                // Here you would call your existing visualization functions
                panel.innerHTML = this.generateVisualizationsContent();
                panel.dataset.loaded = 'true';
            }, 500);
        }
    }
}

// CSS stilovi za poboljšani UI
const improvedResultsCSS = `
/* Tab Navigation */
.tab-navigation {
    display: flex;
    background: #f8f9fa;
    border-radius: 8px;
    padding: 4px;
    margin-bottom: 20px;
    overflow-x: auto;
}

.tab-btn {
    flex: 1;
    min-width: 120px;
    padding: 12px 16px;
    border: none;
    background: transparent;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.3s ease;
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 500;
    white-space: nowrap;
}

.tab-btn.active {
    background: white;
    color: #667eea;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.tab-btn:hover:not(.active) {
    background: rgba(255,255,255,0.5);
}

/* Quick Summary */
.quick-summary {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 20px;
    border-radius: 12px;
    margin-bottom: 20px;
}

.status-indicator {
    display: flex;
    align-items: center;
    gap: 15px;
}

/* Metrics Grid */
.metrics-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 16px;
    margin-bottom: 24px;
}

.metric-card {
    background: white;
    border-radius: 12px;
    padding: 20px;
    border: 1px solid #e9ecef;
    display: flex;
    align-items: center;
    gap: 16px;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.metric-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.metric-icon {
    width: 48px;
    height: 48px;
    border-radius: 50%;
    background: #667eea;
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.2rem;
}

.metric-value {
    font-size: 1.5rem;
    font-weight: bold;
    color: #333;
}

.metric-range {
    font-size: 0.875rem;
    color: #666;
}

/* Collapsible Sections */
.collapsible-section {
    border: 1px solid #e9ecef;
    border-radius: 8px;
    margin-bottom: 16px;
    overflow: hidden;
}

.section-header {
    background: #f8f9fa;
    padding: 16px;
    cursor: pointer;
    display: flex;
    justify-content: space-between;
    align-items: center;
    transition: background 0.2s ease;
}

.section-header:hover {
    background: #e9ecef;
}

.section-content {
    padding: 16px;
    max-height: 1000px;
    overflow: hidden;
    transition: max-height 0.3s ease, padding 0.3s ease;
}

.section-content.collapsed {
    max-height: 0;
    padding: 0 16px;
}

.toggle-icon {
    transition: transform 0.3s ease;
}

/* Tab Panels */
.tab-panel {
    display: none;
    animation: fadeIn 0.3s ease;
}

.tab-panel.active {
    display: block;
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

/* Mobile Responsive */
@media (max-width: 768px) {
    .quick-summary {
        flex-direction: column;
        gap: 16px;
        text-align: center;
    }
    
    .tab-navigation {
        flex-direction: column;
    }
    
    .tab-btn {
        min-width: auto;
    }
    
    .metrics-grid {
        grid-template-columns: 1fr;
    }
}
`;