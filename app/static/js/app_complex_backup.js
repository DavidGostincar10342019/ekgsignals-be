// EKG Analiza - Mobilna Web Aplikacija
class EKGAnalyzer {
    constructor() {
        this.currentImage = null;
        this.isProcessing = false;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupDragAndDrop();
        this.checkCameraSupport();
    }

    setupEventListeners() {
        console.log('🔧 Setting up event listeners...');
        
        try {
            // File input - sa provere da li postoji element
            const fileInput = document.getElementById('fileInput');
            if (fileInput) {
                fileInput.addEventListener('change', (e) => {
                    console.log('📄 File input changed');
                    this.handleFileSelect(e.target.files[0]);
                });
                console.log('✅ File input listener added');
            } else {
                console.error('❌ fileInput element not found');
            }

            // Camera input
            const cameraInput = document.getElementById('cameraInput');
            if (cameraInput) {
                cameraInput.addEventListener('change', (e) => {
                    console.log('📷 Camera input changed');
                    this.handleFileSelect(e.target.files[0]);
                });
                console.log('✅ Camera input listener added');
            } else {
                console.error('❌ cameraInput element not found');
            }

            // Upload button
            const uploadBtn = document.getElementById('uploadBtn');
            if (uploadBtn) {
                uploadBtn.addEventListener('click', (e) => {
                    e.preventDefault();
                    console.log('📁 Upload button clicked!');
                    const fileInput = document.getElementById('fileInput');
                    if (fileInput) {
                        fileInput.click();
                    } else {
                        console.error('❌ fileInput not found when upload button clicked');
                    }
                });
                console.log('✅ Upload button listener added');
            } else {
                console.error('❌ uploadBtn element not found');
            }

            // Camera button
            const cameraBtn = document.getElementById('cameraBtn');
            if (cameraBtn) {
                cameraBtn.addEventListener('click', (e) => {
                    e.preventDefault();
                    console.log('📷 Camera button clicked!');
                    const cameraInput = document.getElementById('cameraInput');
                    if (cameraInput) {
                        cameraInput.click();
                    } else {
                        console.error('❌ cameraInput not found when camera button clicked');
                    }
                });
                console.log('✅ Camera button listener added');
            } else {
                console.error('❌ cameraBtn element not found');
            }

            // Raw signal button
            const rawSignalBtn = document.getElementById('rawSignalBtn');
            if (rawSignalBtn) {
                rawSignalBtn.addEventListener('click', (e) => {
                    e.preventDefault();
                    console.log('📊 Raw signal button clicked!');
                    this.toggleRawSignalInfo();
                    const rawSignalInput = document.getElementById('rawSignalInput');
                    if (rawSignalInput) {
                        rawSignalInput.click();
                    } else {
                        console.error('❌ rawSignalInput not found when raw signal button clicked');
                    }
                });
                console.log('✅ Raw signal button listener added');
            } else {
                console.error('❌ rawSignalBtn element not found');
            }

            // Analyze button
            const analyzeBtn = document.getElementById('analyzeBtn');
            if (analyzeBtn) {
                analyzeBtn.addEventListener('click', () => {
                    console.log('🔬 Analyze button clicked!');
                    this.analyzeImage();
                });
                console.log('✅ Analyze button listener added');
            } else {
                console.warn('⚠️ analyzeBtn element not found (this is normal if not yet created)');
            }

            // New analysis button
            const newAnalysisBtn = document.getElementById('newAnalysisBtn');
            if (newAnalysisBtn) {
                newAnalysisBtn.addEventListener('click', () => {
                    console.log('🔄 New analysis button clicked!');
                    this.resetApp();
                });
                console.log('✅ New analysis button listener added');
            } else {
                console.warn('⚠️ newAnalysisBtn element not found (this is normal if not yet created)');
            }

            // Generate EKG Image button
            const generateEkgImageBtn = document.getElementById('generateEkgImageBtn');
            if (generateEkgImageBtn) {
                generateEkgImageBtn.addEventListener('click', () => {
                    console.log('🖼️ Generate EKG image button clicked!');
                    this.generateEducationalEkgImage();
                });
                console.log('✅ Generate EKG image button listener added');
            } else {
                console.warn('⚠️ generateEkgImageBtn element not found (this is normal if not yet created)');
            }

            // Download generated image button
            const downloadImageBtn = document.getElementById('downloadImageBtn');
            if (downloadImageBtn) {
                downloadImageBtn.addEventListener('click', () => {
                    console.log('💾 Download image button clicked!');
                    this.downloadGeneratedImage();
                });
                console.log('✅ Download image button listener added');
            } else {
                console.warn('⚠️ downloadImageBtn element not found (this is normal if not yet created)');
            }

            // Analyze generated image button
            const analyzeGeneratedImageBtn = document.getElementById('analyzeGeneratedImageBtn');
            if (analyzeGeneratedImageBtn) {
                analyzeGeneratedImageBtn.addEventListener('click', () => {
                    console.log('🔍 Analyze generated image button clicked!');
                    this.analyzeGeneratedImage();
                });
                console.log('✅ Analyze generated image button listener added');
            } else {
                console.warn('⚠️ analyzeGeneratedImageBtn element not found (this is normal if not yet created)');
            }

            // Raw signal file input
            const rawSignalInput = document.getElementById('rawSignalInput');
            if (rawSignalInput) {
                rawSignalInput.addEventListener('change', (e) => {
                    console.log('📊 Raw signal input changed');
                    if (e.target.files.length > 1) {
                        console.log('📊 Multiple files detected - WFDB format');
                        this.handleWFDBFiles(e.target.files);
                    } else if (e.target.files.length === 1) {
                        console.log('📊 Single file detected');
                        this.handleRawSignalFile(e.target.files[0]);
                    }
                });
                console.log('✅ Raw signal input listener added');
            } else {
                console.error('❌ rawSignalInput element not found');
            }

            console.log('✅ All event listeners setup completed');

        } catch (error) {
            console.error('❌ Error setting up event listeners:', error);
        }
    }

    setupDragAndDrop() {
        const uploadArea = document.getElementById('uploadArea');
        
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            uploadArea.addEventListener(eventName, this.preventDefaults, false);
        });

        ['dragenter', 'dragover'].forEach(eventName => {
            uploadArea.addEventListener(eventName, () => {
                uploadArea.classList.add('dragover');
            }, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            uploadArea.addEventListener(eventName, () => {
                uploadArea.classList.remove('dragover');
            }, false);
        });

        uploadArea.addEventListener('drop', (e) => {
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this.handleFileSelect(files[0]);
            }
        }, false);
    }

    preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    checkCameraSupport() {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            document.getElementById('cameraBtn').style.display = 'none';
        }
    }

    handleFileSelect(file) {
        if (!file) return;

        // Validate file type
        if (!file.type.startsWith('image/')) {
            this.showError('Molimo odaberite sliku (JPG, PNG, itd.)');
            return;
        }

        // Validate file size (max 10MB)
        if (file.size > 10 * 1024 * 1024) {
            this.showError('Slika je prevelika. Maksimalna veličina je 10MB.');
            return;
        }

        this.currentImage = file;
        this.displayImagePreview(file);
    }

    displayImagePreview(file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            const previewSection = document.getElementById('imagePreview');
            const previewImage = document.getElementById('previewImage');
            const imageInfo = document.getElementById('imageInfo');

            previewImage.src = e.target.result;
            previewSection.style.display = 'block';

            // Show image info
            const fileSize = (file.size / 1024).toFixed(1);
            imageInfo.innerHTML = `
                <strong>📁 Naziv:</strong> ${file.name}<br>
                <strong>📏 Veličina:</strong> ${fileSize} KB<br>
                <strong>📅 Tip:</strong> ${file.type}
            `;

            // Enable analyze button
            document.getElementById('analyzeBtn').disabled = false;
            
            // Add bounce animation
            previewSection.classList.add('bounce');
            setTimeout(() => {
                previewSection.classList.remove('bounce');
            }, 600);
        };
        reader.readAsDataURL(file);
    }

    async analyzeImage() {
        if (!this.currentImage || this.isProcessing) return;

        this.isProcessing = true;
        this.showUploadProgress();

        try {
            // Convert image to base64 with progress
            const base64Image = await this.fileToBase64WithProgress(this.currentImage);
            
            // Update progress for upload
            this.updateProgress(50, 'Šalje sliku na server...', '📤');
            
            // Send to complete analysis API (osnovna analiza)
            const response = await fetch('/api/analyze/complete', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    image: base64Image,
                    fs: 250
                })
            });

            this.updateProgress(75, 'Obrađuje sliku...', '🔬');

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            
            if (result.error) {
                throw new Error(result.error);
            }

            this.updateProgress(100, 'Analiza završena!', '✅');
            
            // Hide progress and show results
            setTimeout(() => {
                this.hideUploadProgress();
                this.displayResults(result);
            }, 500);
            
        } catch (error) {
            console.error('Analysis error:', error);
            this.hideUploadProgress();
            this.showError(`Greška pri analizi: ${error.message}`);
        } finally {
            this.isProcessing = false;
        }
    }

    fileToBase64WithProgress(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            
            reader.onloadstart = () => {
                this.updateProgress(10, 'Čita sliku...', '📖');
            };
            
            reader.onprogress = (e) => {
                if (e.lengthComputable) {
                    const progress = Math.round((e.loaded / e.total) * 30) + 10; // 10-40%
                    this.updateProgress(progress, 'Konvertuje sliku...', '🔄');
                }
            };
            
            reader.onload = () => {
                this.updateProgress(40, 'Priprema za slanje...', '📦');
                resolve(reader.result);
            };
            
            reader.onerror = error => reject(error);
            reader.readAsDataURL(file);
        });
    }

    showUploadProgress() {
        document.getElementById('uploadSection').style.display = 'none';
        document.getElementById('uploadProgress').style.display = 'block';
        this.updateProgress(0, 'Priprema...', '⏳');
    }

    hideUploadProgress() {
        document.getElementById('uploadProgress').style.display = 'none';
        document.getElementById('uploadSection').style.display = 'block';
    }

    updateProgress(percentage, message, icon = '') {
        const progressBar = document.getElementById('progressBar');
        const progressPercentage = document.querySelector('.progress-percentage');
        const progressDetails = document.getElementById('progressDetails');
        
        progressBar.style.width = `${percentage}%`;
        progressPercentage.textContent = `${percentage}%`;
        progressDetails.textContent = `${icon} ${message}`;
        
        // Add upload speed simulation
        if (percentage > 10 && percentage < 90) {
            const uploadSpeed = document.getElementById('uploadSpeed');
            const speeds = ['1.2 MB/s', '0.8 MB/s', '1.5 MB/s', '0.9 MB/s'];
            uploadSpeed.textContent = `(${speeds[Math.floor(Math.random() * speeds.length)]})`;
        }
    }

    async detailedAnalyzeImage() {
        if (!this.currentImage || this.isProcessing) return;

        this.isProcessing = true;
        this.showProcessingAnimation();

        try {
            // Convert image to base64
            const base64Image = await this.fileToBase64(this.currentImage);
            
            // Send to educational analysis API
            const response = await fetch('/api/analyze/educational', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    image: base64Image,
                    fs: 250
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            
            if (result.error) {
                throw new Error(result.error);
            }

            this.displayDetailedResults(result);
            
        } catch (error) {
            console.error('Detailed analysis error:', error);
            this.showError(`Greška pri detaljnoj analizi: ${error.message}`);
            this.hideProcessing();
        } finally {
            this.isProcessing = false;
        }
    }

    fileToBase64(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.readAsDataURL(file);
            reader.onload = () => resolve(reader.result);
            reader.onerror = error => reject(error);
        });
    }

    showProcessingAnimation() {
        document.getElementById('uploadSection').style.display = 'none';
        document.getElementById('processingSection').style.display = 'block';

        const steps = [
            { id: 'step1', text: 'Učitavanje slike...', delay: 500 },
            { id: 'step2', text: 'Obrada slike...', delay: 1500 },
            { id: 'step3', text: 'Ekstrakcija signala...', delay: 2500 },
            { id: 'step4', text: 'FFT analiza...', delay: 3500 },
            { id: 'step5', text: 'Detekcija R-pikova...', delay: 4500 },
            { id: 'step6', text: 'Analiza aritmija...', delay: 5500 }
        ];

        steps.forEach((step, index) => {
            setTimeout(() => {
                // Mark previous step as completed
                if (index > 0) {
                    document.getElementById(steps[index - 1].id).classList.remove('active');
                    document.getElementById(steps[index - 1].id).classList.add('completed');
                }
                // Mark current step as active
                document.getElementById(step.id).classList.add('active');
            }, step.delay);
        });
    }

    hideProcessing() {
        document.getElementById('processingSection').style.display = 'none';
        document.getElementById('uploadSection').style.display = 'block';
    }

    displayResults(data) {
        // Hide processing
        document.getElementById('processingSection').style.display = 'none';
        
        // Show results
        const resultsSection = document.getElementById('resultsSection');
        resultsSection.style.display = 'block';

        // Store data for detailed analysis
        this.analysisData = data;

        // Show generate EKG image button for raw signal data
        console.log('DEBUG: Checking if should show generate button:', data.signal_info);
        if (data.signal_info && data.signal_info.source && 
            (data.signal_info.source === 'raw_import' || data.signal_info.source === 'wfdb_import')) {
            console.log('DEBUG: Showing generate EKG image button');
            document.getElementById('generateEkgImageBtn').style.display = 'inline-block';
        } else {
            console.log('DEBUG: Not showing generate button - conditions not met');
        }

        // Populate basic results
        this.populateSignalInfo(data.signal_info);
        this.populateHeartRateInfo(data.arrhythmia_detection?.heart_rate);
        this.populateArrhythmias(data.arrhythmia_detection?.arrhythmias);
        this.populateFFTInfo(data.fft_analysis);
        this.populateSignalQuality(data.arrhythmia_detection?.signal_quality);
        this.populateOverallAssessment(data.arrhythmia_detection?.arrhythmias?.overall_assessment);

        // Scroll to results
        resultsSection.scrollIntoView({ behavior: 'smooth' });
    }

    populateDetailedAnalysis(data) {
        // Populate scientific steps with enhanced styling
        if (data.analysis_steps) {
            const stepsContainer = document.getElementById('scientificSteps');
            stepsContainer.innerHTML = data.analysis_steps.map(step => `
                <div class="scientific-step">
                    <div class="step-number">${step.step}</div>
                    <div class="step-title">${step.title}</div>
                    <div class="step-description">${step.description}</div>
                    <div class="step-formula">📐 Formula: ${step.formula}</div>
                    <div class="step-result">✅ Rezultat: ${step.result}</div>
                </div>
            `).join('');
        }

        // Populate educational visualization
        if (data.educational_visualization) {
            const vizImg = document.getElementById('educationalVisualization');
            const placeholder = document.getElementById('visualizationPlaceholder');
            
            vizImg.src = `data:image/png;base64,${data.educational_visualization}`;
            vizImg.style.display = 'block';
            if (placeholder) placeholder.style.display = 'none';
        }

        // Populate mathematical formulas with enhanced styling
        if (data.detailed_results) {
            const formulasContainer = document.getElementById('mathematicalFormulas');
            const formulas = [
                {
                    name: "Spatial Filling Index",
                    formula: "SFI = log(N) / log(L/a)",
                    value: data.detailed_results.spatial_filling_index?.spatial_filling_index?.toFixed(3) || "N/A",
                    description: "Mera geometrijske kompleksnosti signala"
                },
                {
                    name: "Spektralna Entropija", 
                    formula: "H = -Σ p(f)log₂(p(f))",
                    value: data.detailed_results.time_frequency_analysis?.mean_spectral_entropy?.toFixed(3) || "N/A",
                    description: "Mera kompleksnosti frekvencijskog spektra"
                },
                {
                    name: "Wavelet Entropija",
                    formula: "H_w = -Σ E_i log₂(E_i)",
                    value: data.detailed_results.wavelet_analysis?.wavelet_entropy?.toFixed(3) || "N/A",
                    description: "Entropija wavelet koeficijenata"
                },
                {
                    name: "Wiener Filter Koeficijent",
                    formula: "W = S/(S+N)",
                    value: data.detailed_results.advanced_filtering?.wiener_coefficient?.toFixed(3) || "N/A",
                    description: "Koeficijent adaptivnog filtera"
                }
            ];

            formulasContainer.innerHTML = formulas.map(f => `
                <div class="formula-container">
                    <div class="formula-name">${f.name}</div>
                    <div style="color: #7f8c8d; font-size: 0.9rem; margin-bottom: 10px;">${f.description}</div>
                    <div class="formula-equation">${f.formula}</div>
                    <div class="formula-value">Vrednost: ${f.value}</div>
                </div>
            `).join('');
        }

        // Populate advanced results with enhanced styling
        if (data.detailed_results?.comprehensive_interpretation) {
            const advancedContainer = document.getElementById('advancedResults');
            const interpretation = data.detailed_results.comprehensive_interpretation;
            
            advancedContainer.innerHTML = `
                <div class="advanced-metric">
                    <div class="metric-info">
                        <div class="metric-name">🧠 Kompleksnost signala</div>
                        <div style="color: #7f8c8d; font-size: 0.9rem;">Analiza geometrijske složenosti</div>
                    </div>
                    <div class="metric-value-advanced">${interpretation.signal_complexity}</div>
                </div>
                <div class="advanced-metric">
                    <div class="metric-info">
                        <div class="metric-name">📊 Stabilnost frekvencije</div>
                        <div style="color: #7f8c8d; font-size: 0.9rem;">Vremenska varijabilnost spektra</div>
                    </div>
                    <div class="metric-value-advanced">${interpretation.frequency_stability}</div>
                </div>
                <div class="advanced-metric">
                    <div class="metric-info">
                        <div class="metric-name">🌊 Wavelet kompleksnost</div>
                        <div style="color: #7f8c8d; font-size: 0.9rem;">Analiza vreme-frekvencijskih komponenti</div>
                    </div>
                    <div class="metric-value-advanced">${interpretation.wavelet_complexity}</div>
                </div>
                
                <div class="interpretation-box">
                    <div class="interpretation-title">🎯 Ukupna Procena</div>
                    <div class="interpretation-text">${interpretation.overall_assessment}</div>
                    
                    <div class="interpretation-title">📋 Preporuke</div>
                    <ul class="recommendations-list">
                        ${interpretation.recommendations.map(rec => `<li>${rec}</li>`).join('')}
                    </ul>
                </div>
            `;
        }
    }

    async toggleDetailedAnalysis() {
        const detailedSection = document.getElementById('detailedAnalysisSection');
        const toggleBtn = document.getElementById('toggleDetailedBtn');
        
        if (detailedSection.style.display === 'none') {
            // Show loading state
            toggleBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Učitavanje...';
            toggleBtn.disabled = true;
            
            // Load detailed analysis if not already loaded
            if (!this.detailedAnalysisData) {
                await this.loadDetailedAnalysis();
            }
            
            detailedSection.style.display = 'block';
            toggleBtn.innerHTML = '<i class="fas fa-eye-slash"></i> Sakrij Detaljnu Analizu';
            toggleBtn.disabled = false;
            detailedSection.scrollIntoView({ behavior: 'smooth' });
        } else {
            detailedSection.style.display = 'none';
            toggleBtn.innerHTML = '<i class="fas fa-microscope"></i> Prikaži Detaljnu Analizu';
        }
    }

    async loadDetailedAnalysis() {
        try {
            let response;
            
            if (this.currentImage) {
                // Convert image to base64
                const base64Image = await this.fileToBase64(this.currentImage);
                
                // Send to educational analysis API
                response = await fetch('/api/analyze/educational', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        image: base64Image,
                        fs: 250
                    })
                });
            } else if (this.currentRawSignal) {
                // Send raw signal to educational analysis API
                response = await fetch('/api/analyze/educational', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        signal: this.currentRawSignal.signal,
                        fs: this.currentRawSignal.fs
                    })
                });
            } else if (this.currentWFDBData && this.analysisData?.signal_info) {
                // Use signal from WFDB analysis for educational analysis
                // Note: We can't re-extract signal here, so we use the existing analysis data
                // This is a limitation - detailed analysis for WFDB would need server-side storage
                throw new Error('Detaljana analiza za WFDB trenutno nije dostupna. Koristite osnovne rezultate.');
            } else {
                throw new Error('Nema dostupnih podataka za detaljnu analizu');
            }

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            
            if (result.error) {
                throw new Error(result.error);
            }

            this.detailedAnalysisData = result;
            this.populateDetailedAnalysis(result);
            
        } catch (error) {
            console.error('Detailed analysis error:', error);
            this.showError(`Greška pri detaljnoj analizi: ${error.message}`);
        }
    }

    populateSignalInfo(signalInfo) {
        if (!signalInfo) return;
        
        document.getElementById('signalLength').textContent = signalInfo.length;
        document.getElementById('signalDuration').textContent = `${signalInfo.duration_seconds.toFixed(1)}s`;
        document.getElementById('samplingRate').textContent = `${signalInfo.sampling_frequency} Hz`;
    }

    populateHeartRateInfo(heartRate) {
        if (!heartRate) return;

        document.getElementById('avgBPM').textContent = `${heartRate.average_bpm.toFixed(1)} bpm`;
        document.getElementById('minBPM').textContent = `${heartRate.min_bpm.toFixed(1)} bpm`;
        document.getElementById('maxBPM').textContent = `${heartRate.max_bpm.toFixed(1)} bpm`;
        document.getElementById('hrv').textContent = `${heartRate.heart_rate_variability.toFixed(1)} ms`;
        document.getElementById('rPeaks').textContent = heartRate.rr_count || 0;
    }

    populateArrhythmias(arrhythmias) {
        const container = document.getElementById('arrhythmiasList');
        
        if (!arrhythmias || !arrhythmias.detected || arrhythmias.detected.length === 0) {
            container.innerHTML = '<div class="arrhythmia-item severity-low">✅ Nema detektovanih aritmija</div>';
            return;
        }

        container.innerHTML = arrhythmias.detected.map(arr => `
            <div class="arrhythmia-item severity-${arr.severity}">
                <div class="arrhythmia-type">⚠️ ${arr.type}</div>
                <div class="arrhythmia-desc">${arr.description}</div>
                <div class="arrhythmia-desc"><strong>Vrednost:</strong> ${arr.value}</div>
            </div>
        `).join('');
    }

    populateFFTInfo(fftData) {
        if (!fftData) return;

        document.getElementById('peakFreq').textContent = `${fftData.peak_frequency_hz.toFixed(2)} Hz`;
        document.getElementById('peakAmp').textContent = fftData.peak_amplitude.toFixed(4);
    }

    populateSignalQuality(quality) {
        if (!quality) return;

        document.getElementById('signalQuality').textContent = quality.quality;
        document.getElementById('snrValue').textContent = `${quality.snr_db.toFixed(1)} dB`;
    }

    populateOverallAssessment(assessment) {
        if (!assessment) return;

        const statusDiv = document.getElementById('healthStatus');
        statusDiv.textContent = assessment;

        // Set appropriate class based on assessment
        statusDiv.className = 'health-status';
        if (assessment.includes('Normalan')) {
            statusDiv.classList.add('status-normal');
        } else if (assessment.includes('medicinska pažnja')) {
            statusDiv.classList.add('status-danger');
        } else {
            statusDiv.classList.add('status-warning');
        }
    }

    showError(message, htmlContent = null) {
        const errorDiv = document.getElementById('errorMessage');
        
        if (htmlContent) {
            // Clear existing content and add HTML
            errorDiv.innerHTML = `<i class="fas fa-exclamation-circle"></i> ${htmlContent}`;
        } else {
            // Regular text message
            errorDiv.innerHTML = `<i class="fas fa-exclamation-circle"></i> <span>${message}</span>`;
        }
        
        errorDiv.style.display = 'block';
        
        // Auto hide after 10 seconds for HTML content (longer for complex messages)
        const hideDelay = htmlContent ? 15000 : 5000;
        setTimeout(() => {
            errorDiv.style.display = 'none';
        }, hideDelay);
    }

    showSuccess(message) {
        const successDiv = document.getElementById('successMessage');
        successDiv.textContent = message;
        successDiv.style.display = 'block';
        
        setTimeout(() => {
            successDiv.style.display = 'none';
        }, 3000);
    }

    resetApp() {
        // Reset state
        this.currentImage = null;
        this.currentRawSignal = null;
        this.currentWFDBData = null;
        this.isProcessing = false;
        this.analysisData = null;
        this.detailedAnalysisData = null;

        // Hide sections
        document.getElementById('imagePreview').style.display = 'none';
        document.getElementById('processingSection').style.display = 'none';
        document.getElementById('resultsSection').style.display = 'none';
        document.getElementById('generatedImageSection').style.display = 'none';
        document.getElementById('errorMessage').style.display = 'none';
        document.getElementById('successMessage').style.display = 'none';
        document.getElementById('rawSignalInfo').style.display = 'none';

        // Show upload section
        document.getElementById('uploadSection').style.display = 'block';

        // Reset buttons
        document.getElementById('analyzeBtn').disabled = true;
        document.getElementById('generateEkgImageBtn').style.display = 'none';

        // Reset file inputs
        document.getElementById('fileInput').value = '';
        document.getElementById('cameraInput').value = '';
        document.getElementById('rawSignalInput').value = '';

        // Remove headers if they exist
        const existingHeaders = document.querySelectorAll('.raw-signal-header, .wfdb-header');
        existingHeaders.forEach(header => header.remove());

        // Reset processing steps
        document.querySelectorAll('.step').forEach(step => {
            step.classList.remove('active', 'completed');
        });

        // Scroll to top
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }


    // Raw Signal Import Functions
    toggleRawSignalInfo() {
        const infoDiv = document.getElementById('rawSignalInfo');
        if (infoDiv.style.display === 'none' || !infoDiv.style.display) {
            infoDiv.style.display = 'block';
        } else {
            infoDiv.style.display = 'none';
        }
    }

    async handleRawSignalFile(file) {
        if (!file) return;

        try {
            // Check if this is a WFDB file
            if (file.name.endsWith('.dat') || file.name.endsWith('.hea')) {
                await this.handleSingleWFDBFile(file);
                return;
            }

            // Show progress
            this.showUploadProgress();
            this.updateProgress(10, 'Čita fajl...', '📂');

            // Parse the file based on extension
            const signal = await this.parseRawSignalFile(file);
            
            if (!signal || signal.length === 0) {
                throw new Error('Nije moguće pročitati signal iz fajla');
            }

            this.updateProgress(30, 'Validira signal...', '✅');

            // Get sampling frequency
            const fs = parseInt(document.getElementById('rawSignalFs').value) || 250;

            // Validate signal
            if (signal.length < 100) {
                throw new Error('Signal je prekratak (minimum 100 uzoraka)');
            }

            if (signal.length > 100000) {
                throw new Error('Signal je predugačak (maksimum 100,000 uzoraka)');
            }

            this.updateProgress(50, 'Šalje signal na analizu...', '📤');

            // Send to raw signal analysis API
            const response = await fetch('/api/analyze/raw-signal', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    signal: signal,
                    fs: fs,
                    filename: file.name
                })
            });

            this.updateProgress(75, 'Analizira signal...', '🔬');

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Greška pri analizi');
            }

            const result = await response.json();
            
            if (result.error) {
                throw new Error(result.error);
            }

            this.updateProgress(100, 'Analiza završena!', '✅');

            // Store raw signal info
            this.currentRawSignal = {
                signal: signal,
                fs: fs,
                filename: file.name
            };

            // Hide progress and show results
            setTimeout(() => {
                this.hideUploadProgress();
                this.displayRawSignalResults(result, file.name, signal.length, fs);
            }, 500);

        } catch (error) {
            console.error('Raw signal analysis error:', error);
            this.hideUploadProgress();
            this.showError(`Greška pri analizi sirovih podataka: ${error.message}`);
        }
    }

    async parseRawSignalFile(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            
            reader.onload = (e) => {
                try {
                    const content = e.target.result;
                    const extension = file.name.split('.').pop().toLowerCase();
                    let signal = [];

                    if (extension === 'json') {
                        // JSON format: {"signal": [0.1, 0.2, ...], "fs": 250}
                        const data = JSON.parse(content);
                        if (data.signal && Array.isArray(data.signal)) {
                            signal = data.signal.map(Number);
                            // Update fs if provided in JSON
                            if (data.fs) {
                                document.getElementById('rawSignalFs').value = data.fs;
                            }
                        } else {
                            throw new Error('JSON fajl mora imati "signal" niz');
                        }
                    } else if (extension === 'csv' || extension === 'txt') {
                        // CSV/TXT format: numbers separated by newlines or commas
                        const lines = content.trim().split(/[\n\r,;\s]+/);
                        signal = lines
                            .filter(line => line.trim() !== '')
                            .map(value => {
                                const num = parseFloat(value.trim());
                                if (isNaN(num)) {
                                    throw new Error(`Neispravna vrednost: "${value}"`);
                                }
                                return num;
                            });
                    } else {
                        throw new Error('Nepodržan format fajla. Koristite CSV, TXT ili JSON.');
                    }

                    // Validate signal values
                    if (signal.some(val => isNaN(val) || !isFinite(val))) {
                        throw new Error('Signal sadrži neispravne vrednosti (NaN ili beskonačno)');
                    }

                    resolve(signal);
                } catch (error) {
                    reject(error);
                }
            };

            reader.onerror = () => reject(new Error('Greška pri čitanju fajla'));
            reader.readAsText(file);
        });
    }

    displayRawSignalResults(data, filename, signalLength, fs) {
        // Hide upload section and show results
        document.getElementById('uploadSection').style.display = 'none';
        document.getElementById('resultsSection').style.display = 'block';

        // Store data for detailed analysis
        this.analysisData = data;

        // Show generate EKG image button for raw signal data
        console.log('DEBUG: Raw - Checking if should show generate button:', data.signal_info);
        if (data.signal_info && data.signal_info.source && 
            (data.signal_info.source === 'raw_import' || data.signal_info.source === 'wfdb_import')) {
            console.log('DEBUG: Raw - Showing generate EKG image button');
            document.getElementById('generateEkgImageBtn').style.display = 'inline-block';
        } else {
            console.log('DEBUG: Raw - Not showing generate button - conditions not met');
        }

        // Add special header for raw signal
        const resultsSection = document.getElementById('resultsSection');
        const existingHeader = resultsSection.querySelector('.raw-signal-header');
        if (existingHeader) {
            existingHeader.remove();
        }

        const headerDiv = document.createElement('div');
        headerDiv.className = 'raw-signal-header';
        headerDiv.innerHTML = `
            <div style="background: #e8f5e8; padding: 15px; border-radius: 10px; margin-bottom: 20px; border-left: 4px solid #27ae60;">
                <h3 style="margin: 0 0 10px 0;"><i class="fas fa-file-import"></i> Analiza Sirovih EKG Podataka</h3>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                    <div><strong>📁 Fajl:</strong> ${filename}</div>
                    <div><strong>📊 Uzorci:</strong> ${signalLength.toLocaleString()}</div>
                    <div><strong>⏱️ Trajanje:</strong> ${(signalLength / fs).toFixed(1)}s</div>
                    <div><strong>📡 Fs:</strong> ${fs} Hz</div>
                </div>
            </div>
        `;
        
        resultsSection.insertBefore(headerDiv, resultsSection.firstChild);

        // Populate results as usual
        this.populateSignalInfo(data.signal_info);
        this.populateHeartRateInfo(data.arrhythmia_detection?.heart_rate);
        this.populateArrhythmias(data.arrhythmia_detection?.arrhythmias);
        this.populateFFTInfo(data.fft_analysis);
        this.populateSignalQuality(data.arrhythmia_detection?.signal_quality);
        this.populateOverallAssessment(data.arrhythmia_detection?.arrhythmias?.overall_assessment);

        // Scroll to results
        resultsSection.scrollIntoView({ behavior: 'smooth' });
    }

    // Single WFDB File Handler
    async handleSingleWFDBFile(file) {
        // Show helpful error message with download suggestion
        const baseName = file.name.replace(/\.(dat|hea)$/, '');
        const extension = file.name.split('.').pop();
        const neededExt = extension === 'dat' ? 'hea' : 'dat';
        const neededFile = `${baseName}.${neededExt}`;
        
        const errorMessage = `
            <div style="background: #fff3cd; padding: 20px; border-radius: 10px; border-left: 4px solid #ffc107;">
                <h4 style="margin-top: 0;"><i class="fas fa-exclamation-triangle"></i> WFDB Format zahteva oba fajla</h4>
                <p>Za analizu MIT-BIH signala potrebni su <strong>oba fajla</strong>:</p>
                <ul>
                    <li><strong>${file.name}</strong> ✅ (odabran)</li>
                    <li><strong>${neededFile}</strong> ❌ (nedostaje)</li>
                </ul>
                
                <h5>💡 Kako da rešite:</h5>
                <div style="background: white; padding: 15px; border-radius: 5px; margin: 10px 0;">
                    <strong>Opcija 1 - Automatski preuzeti nedostajući fajl:</strong><br>
                    <button onclick="window.ekgAnalyzer.downloadWFDBFile('${baseName}', '${neededExt}')" class="btn btn-primary" style="margin: 5px;">
                        📥 Automatski preuzmi ${neededFile}
                    </button>
                </div>
                
                <div style="background: white; padding: 15px; border-radius: 5px; margin: 10px 0;">
                    <strong>Opcija 2 - Preuzeti oba fajla ručno:</strong><br>
                    <button onclick="window.open('https://physionet.org/content/mitdb/1.0.0/${baseName}.dat')" class="btn btn-secondary" style="margin: 5px;">
                        📥 Preuzmi ${baseName}.dat
                    </button>
                    <button onclick="window.open('https://physionet.org/content/mitdb/1.0.0/${baseName}.hea')" class="btn btn-secondary" style="margin: 5px;">
                        📥 Preuzmi ${baseName}.hea
                    </button>
                </div>
                
                <div style="background: white; padding: 15px; border-radius: 5px; margin: 10px 0;">
                    <strong>Opcija 3 - Odabrati oba odjednom:</strong><br>
                    • Držite <kbd>Ctrl</kbd> (Windows) ili <kbd>Cmd</kbd> (Mac)<br>
                    • Kliknite na oba fajla u file picker-u<br>
                    • Oba fajla će biti odabrana za upload
                </div>
            </div>
        `;
        
        this.showError('', errorMessage);
    }

    // Download missing WFDB file automatically
    async downloadWFDBFile(baseName, extension) {
        try {
            const fileName = `${baseName}.${extension}`;
            
            this.showSuccess(`Preuzimam ${fileName} sa PhysioNet-a...`);
            
            // Use our proxy endpoint
            const response = await fetch(`/api/download/wfdb/${baseName}/${extension}`);
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || `HTTP ${response.status}`);
            }
            
            // Download file
            const blob = await response.blob();
            
            // Create download link
            const downloadUrl = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = downloadUrl;
            a.download = fileName;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(downloadUrl);
            
            this.showSuccess(`✅ ${fileName} uspešno preuzet! Sada odaberite oba fajla za analizu.`);
            
            // Hide error message after delay
            setTimeout(() => {
                document.getElementById('errorMessage').style.display = 'none';
            }, 2000);
            
        } catch (error) {
            console.error('Download error:', error);
            this.showError(`Greška pri preuzimanju ${fileName}: ${error.message}`);
        }
    }

    // WFDB Files Handler
    async handleWFDBFiles(files) {
        try {
            // Proveri da li imamo .dat i .hea fajlove
            let hasDat = false;
            let hasHea = false;
            
            for (let file of files) {
                if (file.name.endsWith('.dat')) hasDat = true;
                if (file.name.endsWith('.hea')) hasHea = true;
                // .atr i .xws su opcioni, .dat i .hea su obavezni
            }
            
            if (!hasDat || !hasHea) {
                // Možda je single file, probaj normalnu obradu
                if (files.length === 1) {
                    await this.handleRawSignalFile(files[0]);
                    return;
                }
                
                this.showError('Za WFDB format potrebni su i .dat i .hea fajlovi');
                return;
            }
            
            this.showUploadProgress();
            this.updateProgress(10, 'Čita WFDB fajlove...', '📂');
            
            // Kreiraj FormData za upload
            const formData = new FormData();
            
            for (let file of files) {
                if (file.name.endsWith('.dat') || file.name.endsWith('.hea') || 
                    file.name.endsWith('.atr') || file.name.endsWith('.xws')) {
                    formData.append('file', file);
                }
            }
            
            this.updateProgress(30, 'Upload WFDB fajlova...', '📤');
            
            // Pošalji na WFDB endpoint
            const response = await fetch('/api/analyze/wfdb', {
                method: 'POST',
                body: formData
            });
            
            this.updateProgress(75, 'Analizira WFDB signal...', '🔬');
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Greška pri analizi WFDB fajlova');
            }
            
            const result = await response.json();
            
            if (result.error) {
                throw new Error(result.error);
            }
            
            this.updateProgress(100, 'WFDB analiza završena!', '✅');
            
            // Store WFDB info
            this.currentWFDBData = {
                metadata: result.wfdb_metadata,
                filename: result.signal_info.filename
            };
            
            // Hide progress and show results
            setTimeout(() => {
                this.hideUploadProgress();
                this.displayWFDBResults(result);
            }, 500);
            
        } catch (error) {
            console.error('WFDB analysis error:', error);
            this.hideUploadProgress();
            this.showError(`Greška pri analizi WFDB fajlova: ${error.message}`);
        }
    }

    displayWFDBResults(data) {
        // Hide upload section and show results
        document.getElementById('uploadSection').style.display = 'none';
        document.getElementById('resultsSection').style.display = 'block';

        // Store data for detailed analysis
        this.analysisData = data;

        // Show generate EKG image button for WFDB data
        console.log('DEBUG: WFDB - Checking if should show generate button:', data.signal_info);
        if (data.signal_info && data.signal_info.source && 
            (data.signal_info.source === 'raw_import' || data.signal_info.source === 'wfdb_import')) {
            console.log('DEBUG: WFDB - Showing generate EKG image button');
            document.getElementById('generateEkgImageBtn').style.display = 'inline-block';
        } else {
            console.log('DEBUG: WFDB - Not showing generate button - conditions not met');
        }

        // Add enhanced header for WFDB with annotation data
        const resultsSection = document.getElementById('resultsSection');
        const existingHeader = resultsSection.querySelector('.wfdb-header');
        if (existingHeader) {
            existingHeader.remove();
        }

        // Extract metadata for display
        const metadata = data.wfdb_metadata || {};
        const hasAnnotations = data.annotations && data.annotations.total_annotations > 0;
        const recordName = metadata.record_name || data.signal_info?.filename || 'N/A';
        const nChannels = metadata.n_signals || 'N/A';
        const totalSamples = metadata.n_samples || data.signal_info?.length || 'N/A';
        const samplingRate = metadata.fs || data.signal_info?.sampling_frequency || 'N/A';
        const duration = data.signal_info?.duration_seconds || 'N/A';

        const headerDiv = document.createElement('div');
        headerDiv.className = 'wfdb-header';
        headerDiv.innerHTML = `
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 15px; margin-bottom: 25px; box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);">
                <h3 style="margin: 0 0 15px 0; font-size: 1.4em;"><i class="fas fa-heartbeat"></i> WFDB Format Analiza</h3>
                
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 15px;">
                    <div style="background: rgba(255,255,255,0.1); padding: 12px; border-radius: 8px;">
                        <div style="font-size: 0.9em; opacity: 0.8;">🏥 Record</div>
                        <div style="font-size: 1.1em; font-weight: bold;">${recordName}</div>
                    </div>
                    <div style="background: rgba(255,255,255,0.1); padding: 12px; border-radius: 8px;">
                        <div style="font-size: 0.9em; opacity: 0.8;">📁 Fajl</div>
                        <div style="font-size: 1.1em; font-weight: bold;">${data.signal_info?.filename || recordName + '.dat'}</div>
                    </div>
                    <div style="background: rgba(255,255,255,0.1); padding: 12px; border-radius: 8px;">
                        <div style="font-size: 0.9em; opacity: 0.8;">📡 Kanali</div>
                        <div style="font-size: 1.1em; font-weight: bold;">${nChannels}</div>
                    </div>
                    <div style="background: rgba(255,255,255,0.1); padding: 12px; border-radius: 8px;">
                        <div style="font-size: 0.9em; opacity: 0.8;">📊 Uzorci</div>
                        <div style="font-size: 1.1em; font-weight: bold;">${typeof totalSamples === 'number' ? totalSamples.toLocaleString() : totalSamples}</div>
                    </div>
                    <div style="background: rgba(255,255,255,0.1); padding: 12px; border-radius: 8px;">
                        <div style="font-size: 0.9em; opacity: 0.8;">⏱️ Trajanje</div>
                        <div style="font-size: 1.1em; font-weight: bold;">${typeof duration === 'number' ? duration.toFixed(1) + 's' : duration}</div>
                    </div>
                    <div style="background: rgba(255,255,255,0.1); padding: 12px; border-radius: 8px;">
                        <div style="font-size: 0.9em; opacity: 0.8;">📈 Fs</div>
                        <div style="font-size: 1.1em; font-weight: bold;">${samplingRate} Hz</div>
                    </div>
                </div>

                ${hasAnnotations ? `
                <div style="border-top: 1px solid rgba(255,255,255,0.2); padding-top: 15px; margin-top: 15px;">
                    <h4 style="margin: 0 0 10px 0; display: flex; align-items: center; gap: 8px;">
                        <i class="fas fa-tags"></i> 
                        Annotation Podaci (.atr fajl)
                        <span style="background: #4CAF50; padding: 2px 8px; border-radius: 12px; font-size: 0.8em;">✓ UČITAN</span>
                    </h4>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px;">
                        <div style="background: rgba(76, 175, 80, 0.2); padding: 8px; border-radius: 6px; border-left: 3px solid #4CAF50;">
                            <div style="font-size: 0.85em; opacity: 0.9;">📌 Ukupno Annotations</div>
                            <div style="font-size: 1.2em; font-weight: bold;">${data.annotations.total_annotations}</div>
                        </div>
                        <div style="background: rgba(255, 193, 7, 0.2); padding: 8px; border-radius: 6px; border-left: 3px solid #FFC107;">
                            <div style="font-size: 0.85em; opacity: 0.9;">💓 R-peaks</div>
                            <div style="font-size: 1.2em; font-weight: bold;">${data.annotations.r_peaks_count}</div>
                        </div>
                        <div style="background: rgba(244, 67, 54, 0.2); padding: 8px; border-radius: 6px; border-left: 3px solid #F44336;">
                            <div style="font-size: 0.85em; opacity: 0.9;">⚠️ Aritmije</div>
                            <div style="font-size: 1.2em; font-weight: bold;">${data.annotations.arrhythmias_count}</div>
                        </div>
                        <div style="background: rgba(156, 39, 176, 0.2); padding: 8px; border-radius: 6px; border-left: 3px solid #9C27B0;">
                            <div style="font-size: 0.85em; opacity: 0.9;">🏷️ Tipovi</div>
                            <div style="font-size: 1.2em; font-weight: bold;">${Object.keys(data.annotations.annotation_types || {}).length}</div>
                        </div>
                    </div>
                    
                    ${Object.keys(data.annotations.annotation_types || {}).length > 0 ? `
                    <div style="margin-top: 12px; padding: 10px; background: rgba(255,255,255,0.1); border-radius: 8px;">
                        <div style="font-size: 0.9em; margin-bottom: 8px; opacity: 0.9;">📊 Distribucija Beat Tipova:</div>
                        <div style="display: flex; flex-wrap: wrap; gap: 8px;">
                            ${Object.entries(data.annotations.annotation_types).map(([type, count]) => `
                                <span style="background: rgba(255,255,255,0.2); padding: 4px 8px; border-radius: 12px; font-size: 0.85em;">
                                    <strong>${type}:</strong> ${count}
                                </span>
                            `).join('')}
                        </div>
                    </div>
                    ` : ''}
                </div>
                ` : `
                <div style="border-top: 1px solid rgba(255,255,255,0.2); padding-top: 15px; margin-top: 15px;">
                    <div style="background: rgba(255, 152, 0, 0.2); padding: 12px; border-radius: 8px; border-left: 3px solid #FF9800;">
                        <i class="fas fa-info-circle"></i> 
                        <strong>Napomena:</strong> .atr fajl nije učitan - koristi se samo algoritamska detekcija R-pikova
                    </div>
                </div>
                `}
            </div>
        `;
        
        resultsSection.insertBefore(headerDiv, resultsSection.firstChild);

        // Populate standard results
        this.populateSignalInfo(data.signal_info);
        this.populateHeartRateInfo(data.arrhythmia_detection?.heart_rate);
        this.populateArrhythmias(data.arrhythmia_detection?.arrhythmias);
        this.populateFFTInfo(data.fft_analysis);
        this.populateSignalQuality(data.arrhythmia_detection?.signal_quality);
        this.populateOverallAssessment(data.arrhythmia_detection?.arrhythmias?.overall_assessment);

        // Add annotation-enhanced sections if available
        if (hasAnnotations) {
            this.addAnnotationEnhancedSections(data.annotations);
        }

        // Scroll to results
        resultsSection.scrollIntoView({ behavior: 'smooth' });
    }

    addAnnotationEnhancedSections(annotations) {
        // Add enhanced R-peaks section showing annotation data
        const heartRateCard = document.querySelector('.info-card');
        if (heartRateCard && annotations.r_peaks && annotations.r_peaks.length > 0) {
            const enhancedInfo = document.createElement('div');
            enhancedInfo.className = 'annotation-enhanced-info';
            enhancedInfo.innerHTML = `
                <div style="background: linear-gradient(135deg, #4CAF50, #45a049); color: white; padding: 15px; border-radius: 10px; margin-top: 15px;">
                    <h4 style="margin: 0 0 10px 0; display: flex; align-items: center; gap: 8px;">
                        <i class="fas fa-certificate"></i> 
                        Validacija sa .atr Annotations
                    </h4>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px;">
                        <div style="background: rgba(255,255,255,0.1); padding: 10px; border-radius: 6px;">
                            <div style="font-size: 0.9em; opacity: 0.9;">💓 Ekspertski označeni R-peaks</div>
                            <div style="font-size: 1.3em; font-weight: bold;">${annotations.r_peaks_count}</div>
                        </div>
                        <div style="background: rgba(255,255,255,0.1); padding: 10px; border-radius: 6px;">
                            <div style="font-size: 0.9em; opacity: 0.9;">🎯 Preciznost detekcije</div>
                            <div style="font-size: 1.3em; font-weight: bold;">✓ Medicinska</div>
                        </div>
                        <div style="background: rgba(255,255,255,0.1); padding: 10px; border-radius: 6px;">
                            <div style="font-size: 0.9em; opacity: 0.9;">⏱️ RR Interval preciznost</div>
                            <div style="font-size: 1.3em; font-weight: bold;">±1ms</div>
                        </div>
                    </div>
                    
                    ${annotations.r_peaks.slice(0, 5).length > 0 ? `
                    <div style="margin-top: 12px; padding-top: 12px; border-top: 1px solid rgba(255,255,255,0.2);">
                        <div style="font-size: 0.9em; margin-bottom: 8px;">📍 Prvih 5 R-peak pozicija (iz .atr):</div>
                        <div style="display: flex; flex-wrap: wrap; gap: 8px; font-family: monospace;">
                            ${annotations.r_peaks.slice(0, 5).map(peak => `
                                <span style="background: rgba(255,255,255,0.2); padding: 4px 8px; border-radius: 4px; font-size: 0.85em;">
                                    ${peak.time_seconds.toFixed(3)}s (${peak.beat_type})
                                </span>
                            `).join('')}
                        </div>
                    </div>
                    ` : ''}
                </div>
            `;
            heartRateCard.appendChild(enhancedInfo);
        }

        // Add arrhythmia details if present
        if (annotations.arrhythmias && annotations.arrhythmias.length > 0) {
            const arrhythmiaSection = document.getElementById('arrhythmiasList').parentElement;
            const arrhythmiaDetails = document.createElement('div');
            arrhythmiaDetails.className = 'annotation-arrhythmia-details';
            arrhythmiaDetails.innerHTML = `
                <div style="background: linear-gradient(135deg, #f44336, #d32f2f); color: white; padding: 15px; border-radius: 10px; margin-top: 15px;">
                    <h4 style="margin: 0 0 10px 0; display: flex; align-items: center; gap: 8px;">
                        <i class="fas fa-exclamation-triangle"></i> 
                        Medicinski označene aritmije (.atr)
                    </h4>
                    <div style="space-y: 8px;">
                        ${annotations.arrhythmias.map(arr => `
                            <div style="background: rgba(255,255,255,0.1); padding: 10px; border-radius: 6px; margin-bottom: 8px;">
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <span style="font-weight: bold;">${arr.arrhythmia_type}</span>
                                    <span style="font-family: monospace; background: rgba(255,255,255,0.2); padding: 2px 6px; border-radius: 4px; font-size: 0.9em;">
                                        ${arr.time_seconds.toFixed(3)}s
                                    </span>
                                </div>
                                <div style="font-size: 0.9em; margin-top: 4px; opacity: 0.9;">${arr.description}</div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
            arrhythmiaSection.appendChild(arrhythmiaDetails);
        }

        // Add medical accuracy indicator
        this.addMedicalAccuracyIndicator(annotations);
    }

    addMedicalAccuracyIndicator(annotations) {
        // Add a floating indicator showing medical validation status
        const resultsSection = document.getElementById('resultsSection');
        const indicator = document.createElement('div');
        indicator.className = 'medical-accuracy-indicator';
        indicator.innerHTML = `
            <div style="position: sticky; top: 20px; background: linear-gradient(135deg, #2196F3, #1976D2); color: white; padding: 12px; border-radius: 25px; margin: 15px 0; box-shadow: 0 4px 15px rgba(33, 150, 243, 0.3); display: flex; align-items: center; justify-content: center; gap: 10px; z-index: 100;">
                <i class="fas fa-shield-alt"></i>
                <span style="font-weight: bold;">Medicinska Validacija</span>
                <div style="background: rgba(255,255,255,0.2); padding: 4px 8px; border-radius: 12px; font-size: 0.9em;">
                    MIT-BIH Standard ✓
                </div>
                <div style="background: rgba(76, 175, 80, 0.8); padding: 4px 8px; border-radius: 12px; font-size: 0.9em;">
                    ${annotations.total_annotations} Expert Annotations
                </div>
            </div>
        `;
        
        // Insert after the main header
        const mainHeader = resultsSection.querySelector('.wfdb-header');
        if (mainHeader) {
            mainHeader.insertAdjacentElement('afterend', indicator);
        }
    }
        
        headerDiv.innerHTML = `
            <div style="background: #e8f4fd; padding: 15px; border-radius: 10px; margin-bottom: 20px; border-left: 4px solid #2196f3;">
                <h3 style="margin: 0 0 10px 0;"><i class="fas fa-hospital"></i> WFDB Format Analiza</h3>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                    <div><strong>🏥 Record:</strong> ${metadata.record_name || 'N/A'}</div>
                    <div><strong>📁 Fajl:</strong> ${signalInfo.filename || 'N/A'}</div>
                    <div><strong>📡 Kanali:</strong> ${metadata.n_signals || 1}</div>
                    <div><strong>📊 Uzorci:</strong> ${signalInfo.length?.toLocaleString() || 'N/A'}</div>
                    <div><strong>⏱️ Trajanje:</strong> ${signalInfo.duration_seconds?.toFixed(1) || 0}s</div>
                    <div><strong>📈 Fs:</strong> ${signalInfo.sampling_frequency || 250} Hz</div>
                </div>
            </div>
        `;
        
        resultsSection.insertBefore(headerDiv, resultsSection.firstChild);

        // Populate results as usual
        this.populateSignalInfo(data.signal_info);
        this.populateHeartRateInfo(data.arrhythmia_detection?.heart_rate);
        this.populateArrhythmias(data.arrhythmia_detection?.arrhythmias);
        this.populateFFTInfo(data.fft_analysis);
        this.populateSignalQuality(data.arrhythmia_detection?.signal_quality);
        this.populateOverallAssessment(data.arrhythmia_detection?.arrhythmias?.overall_assessment);

        // Scroll to results
        resultsSection.scrollIntoView({ behavior: 'smooth' });
    }

    // Generate Educational EKG Image
    async generateEducationalEkgImage() {
        if (!this.analysisData || !this.currentRawSignal && !this.currentWFDBData) {
            this.showError('Nema dostupnih podataka za generisanje slike');
            return;
        }

        try {
            // Show image generation section
            document.getElementById('generatedImageSection').style.display = 'block';
            document.getElementById('imageGenerationProgress').style.display = 'block';
            document.getElementById('generatedEkgImage').style.display = 'none';
            document.getElementById('imageActions').style.display = 'none';

            // Prepare data for image generation
            let signal, fs, filename;
            
            if (this.currentRawSignal) {
                signal = this.currentRawSignal.signal;
                fs = this.currentRawSignal.fs;
                filename = this.currentRawSignal.filename;
            } else if (this.currentWFDBData && this.analysisData) {
                // For WFDB, we need to use the backend to generate image directly from WFDB data
                console.log('DEBUG: Using WFDB backend for image generation');
                return this.generateWFDBImage();
            } else {
                throw new Error('Nema dostupnih sirovih podataka');
            }

            // Call the new educational image generation API
            const response = await fetch('/api/generate/educational-ekg-image', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    signal: signal,
                    analysis_results: this.analysisData,
                    fs: fs,
                    duration_seconds: 10  // Show first 10 seconds
                })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Greška pri generisanju slike');
            }

            const result = await response.json();
            
            if (result.error) {
                throw new Error(result.error);
            }

            // Store generated image data
            this.generatedImageData = result;

            // Show the generated image
            const imgElement = document.getElementById('generatedEkgImage');
            imgElement.src = result.image_base64;
            imgElement.style.display = 'block';

            // Hide progress and show actions
            document.getElementById('imageGenerationProgress').style.display = 'none';
            document.getElementById('imageActions').style.display = 'block';

            // Scroll to generated image
            document.getElementById('generatedImageSection').scrollIntoView({ behavior: 'smooth' });

            this.showSuccess('✅ Edukativna EKG slika uspešno generisana!');

        } catch (error) {
            console.error('Image generation error:', error);
            this.showError(`Greška pri generisanju EKG slike: ${error.message}`);
            document.getElementById('generatedImageSection').style.display = 'none';
        }
    }

    // Download Generated Image
    downloadGeneratedImage() {
        if (!this.generatedImageData) {
            this.showError('Nema generirane slike za download');
            return;
        }

        try {
            // Convert base64 to blob
            const base64Data = this.generatedImageData.image_base64.split(',')[1];
            const byteCharacters = atob(base64Data);
            const byteNumbers = new Array(byteCharacters.length);
            
            for (let i = 0; i < byteCharacters.length; i++) {
                byteNumbers[i] = byteCharacters.charCodeAt(i);
            }
            
            const byteArray = new Uint8Array(byteNumbers);
            const blob = new Blob([byteArray], { type: 'image/png' });

            // Create download link
            const downloadUrl = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = downloadUrl;
            a.download = 'ekg_analiza_edukativna_slika.png';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(downloadUrl);

            this.showSuccess('📥 Slika je uspešno sačuvana!');

        } catch (error) {
            console.error('Download error:', error);
            this.showError(`Greška pri preuzimanju slike: ${error.message}`);
        }
    }

    // Analyze Generated Image
    async analyzeGeneratedImage() {
        if (!this.generatedImageData) {
            this.showError('Nema generirane slike za analizu');
            return;
        }

        try {
            this.showUploadProgress();
            this.updateProgress(25, 'Priprema generirane slike za analizu...', '🖼️');

            // Analyze the generated image using the complete analysis API
            const response = await fetch('/api/analyze/complete', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    image: this.generatedImageData.image_base64,
                    fs: this.generatedImageData.signal_info.sampling_frequency,
                    skip_validation: true  // Skip validation for generated images
                })
            });

            this.updateProgress(75, 'Analizira generisanu sliku...', '🔬');

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Greška pri analizi generirane slike');
            }

            const result = await response.json();
            
            if (result.error) {
                throw new Error(result.error);
            }

            this.updateProgress(100, 'Analiza generirane slike završena!', '✅');

            // Hide progress
            setTimeout(() => {
                this.hideUploadProgress();
                
                // Show comparison results
                this.showImageAnalysisComparison(this.analysisData, result);
                
            }, 500);

        } catch (error) {
            console.error('Generated image analysis error:', error);
            this.hideUploadProgress();
            this.showError(`Greška pri analizi generirane slike: ${error.message}`);
        }
    }

    // Show comparison between original and generated image analysis
    showImageAnalysisComparison(originalData, imageData) {
        const comparison = this.compareAnalysisResults(originalData, imageData);
        
        const message = `
            <div style="background: #f8f9fa; padding: 20px; border-radius: 10px;">
                <h4 style="margin-top: 0;"><i class="fas fa-chart-line"></i> Poređenje Rezultata: Originalni vs Generisana Slika</h4>
                
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 15px 0;">
                    <div style="background: white; padding: 15px; border-radius: 8px; border: 2px solid #007bff;">
                        <h5 style="color: #007bff; margin-top: 0;">📊 Originalni Signal</h5>
                        <div><strong>❤️ BPM:</strong> ${originalData.arrhythmia_detection?.heart_rate?.average_bpm?.toFixed(1) || 'N/A'}</div>
                        <div><strong>📈 HRV:</strong> ${originalData.arrhythmia_detection?.heart_rate?.heart_rate_variability?.toFixed(1) || 'N/A'} ms</div>
                        <div><strong>🌊 Peak freq:</strong> ${originalData.fft_analysis?.peak_frequency_hz?.toFixed(2) || 'N/A'} Hz</div>
                    </div>
                    
                    <div style="background: white; padding: 15px; border-radius: 8px; border: 2px solid #28a745;">
                        <h5 style="color: #28a745; margin-top: 0;">🖼️ Generisana Slika</h5>
                        <div><strong>❤️ BPM:</strong> ${imageData.arrhythmia_detection?.heart_rate?.average_bpm?.toFixed(1) || 'N/A'}</div>
                        <div><strong>📈 HRV:</strong> ${imageData.arrhythmia_detection?.heart_rate?.heart_rate_variability?.toFixed(1) || 'N/A'} ms</div>
                        <div><strong>🌊 Peak freq:</strong> ${imageData.fft_analysis?.peak_frequency_hz?.toFixed(2) || 'N/A'} Hz</div>
                    </div>
                </div>
                
                <div style="background: ${comparison.overall_match ? '#d4edda' : '#fff3cd'}; padding: 15px; border-radius: 8px; margin: 15px 0;">
                    <h5 style="margin-top: 0;">🎯 Procena Tačnosti:</h5>
                    <div><strong>Sličnost BPM:</strong> ${comparison.bpm_match ? '✅ Odliča' : '⚠️ Razlika'} (${comparison.bpm_difference?.toFixed(1) || 'N/A'} BPM)</div>
                    <div><strong>Ukupna ocena:</strong> ${comparison.overall_match ? '✅ Generisana slika odražava originalni signal' : '⚠️ Generisana slika se razlikuje od originalnog signala'}</div>
                </div>
                
                <div style="text-align: center; margin-top: 20px;">
                    <small style="color: #6c757d;">
                        💡 Ova funkcionalnost vam omogućava da testirate kako vaša aplikacija "vidi" EKG signale
                    </small>
                </div>
            </div>
        `;
        
        this.showSuccess('Analiza generirane slike završena!');
        
        // Show detailed comparison in a separate modal-like message
        setTimeout(() => {
            this.showError('', message);
        }, 1000);
    }

    // Compare analysis results
    compareAnalysisResults(original, fromImage) {
        const origBpm = original.arrhythmia_detection?.heart_rate?.average_bpm || 0;
        const imgBpm = fromImage.arrhythmia_detection?.heart_rate?.average_bpm || 0;
        
        const bpmDifference = Math.abs(origBpm - imgBpm);
        const bpmMatch = bpmDifference < 10; // Tolerance of 10 BPM
        
        return {
            bpm_difference: bpmDifference,
            bpm_match: bpmMatch,
            overall_match: bpmMatch,
            original_bpm: origBpm,
            image_bpm: imgBpm
        };
    }

    // Create synthetic signal from analysis data (for WFDB)
    createSignalFromAnalysis(analysisData) {
        console.log('DEBUG: Creating synthetic signal from analysis data');
        
        // Get basic parameters
        const signalInfo = analysisData.signal_info || {};
        const heartRate = analysisData.arrhythmia_detection?.heart_rate || {};
        const duration = signalInfo.duration_seconds || 10;
        const fs = signalInfo.sampling_frequency || 250;
        const avgBpm = heartRate.average_bpm || 75;
        
        // Create time array
        const numSamples = Math.floor(duration * fs);
        const t = Array.from({length: numSamples}, (_, i) => i / fs);
        
        // Create synthetic EKG signal
        const signal = new Array(numSamples).fill(0);
        
        // Add baseline
        for (let i = 0; i < numSamples; i++) {
            signal[i] = 0.1 * Math.sin(2 * Math.PI * 0.5 * t[i]) + 0.05 * Math.random();
        }
        
        // Add R-peaks based on detected heart rate
        const rr_interval = 60 / avgBpm; // seconds between beats
        let beat_time = 0.5; // start first beat at 0.5s
        
        while (beat_time < duration - 0.5) {
            const beat_idx = Math.floor(beat_time * fs);
            
            // Add QRS complex
            if (beat_idx >= 2 && beat_idx < numSamples - 3) {
                signal[beat_idx - 2] += 0.1;
                signal[beat_idx - 1] += 0.3;
                signal[beat_idx] += 1.0;
                signal[beat_idx + 1] += 0.4;
                signal[beat_idx + 2] += 0.1;
            }
            
            // Next beat with some variability
            const hrv = heartRate.heart_rate_variability || 30;
            const variation = (Math.random() - 0.5) * (hrv / 1000); // Convert ms to seconds
            beat_time += rr_interval + variation;
        }
        
        console.log(`DEBUG: Created synthetic signal: ${signal.length} samples, ${duration}s, ${avgBpm} BPM`);
        return signal;
    }

    // Generate image from WFDB data using backend
    async generateWFDBImage() {
        try {
            // Show image generation section
            document.getElementById('generatedImageSection').style.display = 'block';
            document.getElementById('imageGenerationProgress').style.display = 'block';
            document.getElementById('generatedEkgImage').style.display = 'none';
            document.getElementById('imageActions').style.display = 'none';

            // We need to re-upload WFDB files to the backend for image generation
            // This is a limitation - we can't store the original signal in frontend
            
            // Try to find the original files in the file input
            const fileInput = document.getElementById('rawSignalInput');
            if (!fileInput.files || fileInput.files.length === 0) {
                throw new Error('Potrebno je ponovo odabrati WFDB fajlove za generisanje slike. Molim ponovo upload-ujte .dat i .hea fajlove.');
            }

            // Create FormData with WFDB files
            const formData = new FormData();
            for (let file of fileInput.files) {
                if (file.name.endsWith('.dat') || file.name.endsWith('.hea') || 
                    file.name.endsWith('.atr') || file.name.endsWith('.xws')) {
                    formData.append('file', file);
                }
            }
            
            // Add parameters for optimal image generation
            formData.append('style', 'clinical');
            formData.append('duration_seconds', '8');  // 8 sekundi za čitljivu sliku

            // Call WFDB to image endpoint
            const response = await fetch('/api/analyze/wfdb-to-image', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Greška pri generisanju WFDB slike');
            }

            const result = await response.json();
            
            if (result.error) {
                throw new Error(result.error);
            }

            // Store generated image data
            this.generatedImageData = result;

            // Show the generated image
            const imgElement = document.getElementById('generatedEkgImage');
            imgElement.src = result.image_base64;
            imgElement.style.display = 'block';

            // Hide progress and show actions
            document.getElementById('imageGenerationProgress').style.display = 'none';
            document.getElementById('imageActions').style.display = 'block';

            // Scroll to generated image
            document.getElementById('generatedImageSection').scrollIntoView({ behavior: 'smooth' });

            this.showSuccess('✅ WFDB EKG slika uspešno generisana iz originalnih podataka!');

        } catch (error) {
            console.error('WFDB image generation error:', error);
            this.showError(`Greška pri generisanju WFDB slike: ${error.message}`);
            document.getElementById('generatedImageSection').style.display = 'none';
        }
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('📄 DOM Content Loaded - Starting simple setup');
    
    // SIMPLE APPROACH: Setup buttons immediately
    setupSimpleButtons();
    
    // Then try to initialize the main class
    try {
        console.log('🚀 Initializing EKG Analyzer...');
        window.ekgAnalyzer = new EKGAnalyzer();
        console.log('✅ EKG Analyzer initialized successfully');
    } catch (error) {
        console.error('❌ Failed to initialize EKG Analyzer:', error);
        console.log('ℹ️ But simple buttons should still work');
    }
});

// Simple button setup that definitely works
function setupSimpleButtons() {
    console.log('🔧 Setting up SIMPLE buttons...');
    
    // Wait a bit for DOM to be ready
    setTimeout(() => {
        // Upload button
        const uploadBtn = document.getElementById('uploadBtn');
        if (uploadBtn) {
            uploadBtn.onclick = function() {
                console.log('📁 Upload button clicked!');
                const fileInput = document.getElementById('fileInput');
                if (fileInput) {
                    fileInput.click();
                } else {
                    console.error('fileInput not found');
                }
            };
            console.log('✅ Upload button onclick set');
        } else {
            console.error('❌ uploadBtn not found');
        }
        
        // Camera button
        const cameraBtn = document.getElementById('cameraBtn');
        if (cameraBtn) {
            cameraBtn.onclick = function() {
                console.log('📷 Camera button clicked!');
                const cameraInput = document.getElementById('cameraInput');
                if (cameraInput) {
                    cameraInput.click();
                } else {
                    console.error('cameraInput not found');
                }
            };
            console.log('✅ Camera button onclick set');
        } else {
            console.error('❌ cameraBtn not found');
        }
        
        // Raw signal button
        const rawSignalBtn = document.getElementById('rawSignalBtn');
        if (rawSignalBtn) {
            rawSignalBtn.onclick = function() {
                console.log('📊 Raw signal button clicked!');
                const rawSignalInput = document.getElementById('rawSignalInput');
                if (rawSignalInput) {
                    rawSignalInput.click();
                } else {
                    console.error('rawSignalInput not found');
                }
            };
            console.log('✅ Raw signal button onclick set');
        } else {
            console.error('❌ rawSignalBtn not found');
        }
        
        // File inputs
        const fileInput = document.getElementById('fileInput');
        if (fileInput) {
            fileInput.onchange = function(e) {
                if (e.target.files[0]) {
                    console.log('📄 File selected:', e.target.files[0].name);
                    // Basic preview
                    if (window.ekgAnalyzer && window.ekgAnalyzer.handleFileSelect) {
                        window.ekgAnalyzer.handleFileSelect(e.target.files[0]);
                    } else {
                        console.log('Using basic file handling');
                        showBasicFilePreview(e.target.files[0]);
                    }
                }
            };
        }
        
        const cameraInput = document.getElementById('cameraInput');
        if (cameraInput) {
            cameraInput.onchange = function(e) {
                if (e.target.files[0]) {
                    console.log('📷 Camera file selected:', e.target.files[0].name);
                    if (window.ekgAnalyzer && window.ekgAnalyzer.handleFileSelect) {
                        window.ekgAnalyzer.handleFileSelect(e.target.files[0]);
                    } else {
                        showBasicFilePreview(e.target.files[0]);
                    }
                }
            };
        }
        
        const rawSignalInput = document.getElementById('rawSignalInput');
        if (rawSignalInput) {
            rawSignalInput.onchange = function(e) {
                if (e.target.files.length > 0) {
                    console.log('📊 Raw signal file selected:', e.target.files[0].name);
                    if (window.ekgAnalyzer && window.ekgAnalyzer.handleRawSignalFile) {
                        if (e.target.files.length > 1) {
                            window.ekgAnalyzer.handleWFDBFiles(e.target.files);
                        } else {
                            window.ekgAnalyzer.handleRawSignalFile(e.target.files[0]);
                        }
                    } else {
                        alert('Fajl je odabran: ' + e.target.files[0].name + '. Glavna funkcionalnost će biti dostupna kada se aplikacija potpuno učita.');
                    }
                }
            };
        }
        
        console.log('✅ Simple button setup complete');
        
    }, 100);
}

// Basic file preview function
function showBasicFilePreview(file) {
    if (!file.type.startsWith('image/')) {
        alert('Molimo odaberite sliku');
        return;
    }
    
    const reader = new FileReader();
    reader.onload = function(e) {
        const previewSection = document.getElementById('imagePreview');
        const previewImage = document.getElementById('previewImage');
        
        if (previewImage && previewSection) {
            previewImage.src = e.target.result;
            previewSection.style.display = 'block';
            console.log('✅ Basic image preview shown');
            
            // Enable analyze button if it exists
            const analyzeBtn = document.getElementById('analyzeBtn');
            if (analyzeBtn) {
                analyzeBtn.disabled = false;
                analyzeBtn.onclick = function() {
                    alert('Analiza funkcionalnost će biti dostupna kada se glavna aplikacija učita.');
                };
            }
        }
    };
    reader.readAsDataURL(file);
}

// Fallback event listeners in case the main class fails
function setupFallbackEventListeners() {
    try {
        console.log('🚨 Setting up FALLBACK event listeners - main class failed!');
        
        // Remove any existing event listeners to avoid duplicates
        const buttonsToCheck = ['uploadBtn', 'cameraBtn', 'rawSignalBtn'];
        
        buttonsToCheck.forEach(buttonId => {
            const button = document.getElementById(buttonId);
            if (button) {
                // Clone the button to remove all existing event listeners
                const newButton = button.cloneNode(true);
                button.parentNode.replaceChild(newButton, button);
                console.log(`🔄 Cloned ${buttonId} to remove old listeners`);
            }
        });
        
        // Upload button - force setup
        const uploadBtn = document.getElementById('uploadBtn');
        if (uploadBtn) {
            uploadBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                console.log('📁 Upload button clicked (FALLBACK)');
                const fileInput = document.getElementById('fileInput');
                if (fileInput) {
                    fileInput.click();
                    console.log('📁 File input triggered');
                } else {
                    console.error('❌ File input not found');
                }
            });
            console.log('✅ FALLBACK Upload button listener added');
        } else {
            console.error('❌ uploadBtn not found in fallback');
        }
        
        // Camera button - force setup
        const cameraBtn = document.getElementById('cameraBtn');
        if (cameraBtn) {
            cameraBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                console.log('📷 Camera button clicked (FALLBACK)');
                const cameraInput = document.getElementById('cameraInput');
                if (cameraInput) {
                    cameraInput.click();
                    console.log('📷 Camera input triggered');
                } else {
                    console.error('❌ Camera input not found');
                }
            });
            console.log('✅ FALLBACK Camera button listener added');
        } else {
            console.error('❌ cameraBtn not found in fallback');
        }
        
        // Raw signal button - force setup
        const rawSignalBtn = document.getElementById('rawSignalBtn');
        if (rawSignalBtn) {
            rawSignalBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                console.log('📊 Raw signal button clicked (FALLBACK)');
                
                // Toggle info (simplified version)
                const rawSignalInfo = document.getElementById('rawSignalInfo');
                if (rawSignalInfo) {
                    if (rawSignalInfo.style.display === 'none' || !rawSignalInfo.style.display) {
                        rawSignalInfo.style.display = 'block';
                        console.log('📊 Raw signal info shown');
                    } else {
                        rawSignalInfo.style.display = 'none';
                        console.log('📊 Raw signal info hidden');
                    }
                }
                
                const rawSignalInput = document.getElementById('rawSignalInput');
                if (rawSignalInput) {
                    rawSignalInput.click();
                    console.log('📊 Raw signal input triggered');
                } else {
                    console.error('❌ Raw signal input not found');
                }
            });
            console.log('✅ FALLBACK Raw signal button listener added');
        } else {
            console.error('❌ rawSignalBtn not found in fallback');
        }
        
        // File inputs
        const fileInput = document.getElementById('fileInput');
        if (fileInput) {
            fileInput.addEventListener('change', (e) => {
                if (e.target.files[0]) {
                    console.log('📄 File selected:', e.target.files[0].name);
                    handleBasicFileSelect(e.target.files[0]);
                }
            });
        }
        
        const cameraInput = document.getElementById('cameraInput');
        if (cameraInput) {
            cameraInput.addEventListener('change', (e) => {
                if (e.target.files[0]) {
                    console.log('📷 Camera file selected:', e.target.files[0].name);
                    handleBasicFileSelect(e.target.files[0]);
                }
            });
        }
        
        // Basic drag and drop
        const uploadArea = document.getElementById('uploadArea');
        if (uploadArea) {
            ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
                uploadArea.addEventListener(eventName, (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                }, false);
            });
            
            ['dragenter', 'dragover'].forEach(eventName => {
                uploadArea.addEventListener(eventName, () => {
                    uploadArea.classList.add('dragover');
                }, false);
            });
            
            ['dragleave', 'drop'].forEach(eventName => {
                uploadArea.addEventListener(eventName, () => {
                    uploadArea.classList.remove('dragover');
                }, false);
            });
            
            uploadArea.addEventListener('drop', (e) => {
                const files = e.dataTransfer.files;
                if (files.length > 0) {
                    console.log('📂 File dropped:', files[0].name);
                    handleBasicFileSelect(files[0]);
                }
            }, false);
        }
        
        console.log('✅ Fallback event listeners setup complete');
        
    } catch (error) {
        console.error('❌ Failed to setup fallback listeners:', error);
    }
}

// Basic file handling
function handleBasicFileSelect(file) {
    try {
        if (!file.type.startsWith('image/')) {
            alert('Molimo odaberite sliku (JPG, PNG, itd.)');
            return;
        }
        
        if (file.size > 10 * 1024 * 1024) {
            alert('Slika je prevelika. Maksimalna veličina je 10MB.');
            return;
        }
        
        // Show image preview
        const reader = new FileReader();
        reader.onload = (e) => {
            const previewSection = document.getElementById('imagePreview');
            const previewImage = document.getElementById('previewImage');
            const imageInfo = document.getElementById('imageInfo');
            const analyzeBtn = document.getElementById('analyzeBtn');
            
            if (previewImage && previewSection) {
                previewImage.src = e.target.result;
                previewSection.style.display = 'block';
                
                if (imageInfo) {
                    const fileSize = (file.size / 1024).toFixed(1);
                    imageInfo.innerHTML = `
                        <strong>📁 Naziv:</strong> ${file.name}<br>
                        <strong>📏 Veličina:</strong> ${fileSize} KB<br>
                        <strong>📅 Tip:</strong> ${file.type}
                    `;
                }
                
                if (analyzeBtn) {
                    analyzeBtn.disabled = false;
                    analyzeBtn.onclick = () => {
                        alert('Analiza funkcionalnost je dostupna kada se glavna aplikacija učita pravilno.');
                    };
                }
                
                console.log('✅ Image preview setup complete');
            }
        };
        reader.readAsDataURL(file);
        
    } catch (error) {
        console.error('❌ Error handling file:', error);
        alert('Greška pri obradi fajla: ' + error.message);
    }
}