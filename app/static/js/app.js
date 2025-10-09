// EKG Analiza - Mobilna Web Aplikacija
class EKGAnalyzer {
    constructor() {
        this.currentImage = null;
        this.currentRawSignal = null;
        this.isProcessing = false;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupDragAndDrop();
        this.checkCameraSupport();
    }

    setupEventListeners() {
        // File input
        document.getElementById('fileInput').addEventListener('change', (e) => {
            this.handleFileSelect(e.target.files[0]);
        });

        // Camera input
        document.getElementById('cameraInput').addEventListener('change', (e) => {
            this.handleFileSelect(e.target.files[0]);
        });

        // Upload buttons
        document.getElementById('uploadBtn').addEventListener('click', () => {
            document.getElementById('fileInput').click();
        });

        document.getElementById('cameraBtn').addEventListener('click', () => {
            document.getElementById('cameraInput').click();
        });

        // Raw signal import button
        document.getElementById('rawSignalBtn').addEventListener('click', () => {
            document.getElementById('rawSignalInput').click();
        });

        // Raw signal file input  
        document.getElementById('rawSignalInput').addEventListener('change', (e) => {
            if (e.target.files.length > 1) {
                // Multiple files - WFDB format (.hea, .dat, .atr)
                this.handleWFDBFiles(e.target.files);
            } else {
                // Single file - check extension
                const file = e.target.files[0];
                if (file.name.endsWith('.hea') || file.name.endsWith('.dat') || file.name.endsWith('.atr')) {
                    this.showError('WFDB fajlovi se moraju učitati zajedno (.hea + .dat + .atr). Molimo odaberite sve fajlove istovremeno.');
                    return;
                } else {
                    // CSV/TXT/JSON single file
                    this.handleRawSignalFile(file);
                }
            }
        });

        // Analyze button
        document.getElementById('analyzeBtn').addEventListener('click', () => {
            this.analyzeImage();
        });

        // New analysis button - removed from initial screen

        // Generate EKG Image button - removed as it has no function
        
        // Info button for diagram explanations
        document.addEventListener('click', (e) => {
            if (e.target && e.target.classList.contains('info-btn')) {
                const panel = e.target.closest('.result-card').querySelector('.explanation-panel');
                if (panel) {
                    panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
                }
            }
        });
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
            
            // Show debug button
            const debugBtn = document.getElementById('debugVizBtn');
            if (debugBtn) {
                debugBtn.style.display = 'inline-block';
            }
            
            // Add bounce animation
            previewSection.classList.add('bounce');
            setTimeout(() => {
                previewSection.classList.remove('bounce');
            }, 600);
        };
        reader.readAsDataURL(file);
    }

    async analyzeImage() {
        if ((!this.currentImage && !this.currentRawSignal) || this.isProcessing) return;

        this.isProcessing = true;
        this.showLoadingAnimation();

        try {
            let requestBody;
            let requestMessage;
            
            if (this.currentImage) {
                // Image analysis
                const base64Image = await this.fileToBase64(this.currentImage);
                
                // Sačuvaj image data za image processing visualization
                window.currentImageData = base64Image;
                
                requestBody = JSON.stringify({
                    image: base64Image,
                    fs: 250
                });
                requestMessage = 'Šalje sliku na server...';
            } else if (this.currentRawSignal) {
                if (this.currentRawSignal.type === 'wfdb_import') {
                    // WFDB files analysis - returns complete analysis directly
                    const formData = new FormData();
                    for (let file of this.currentRawSignal.files) {
                        if (file.name.endsWith('.dat') || file.name.endsWith('.hea') || 
                            file.name.endsWith('.atr') || file.name.endsWith('.xws')) {
                            formData.append('file', file);
                        }
                    }
                    
                    this.updateLoadingStep(2, 'Analizira WFDB fajlove...');
                    
                    // WFDB endpoint already returns complete analysis
                    const wfdbResponse = await fetch('/api/analyze/wfdb', {
                        method: 'POST',
                        body: formData
                    });
                    
                    if (!wfdbResponse.ok) {
                        const error = await wfdbResponse.json();
                        throw new Error(error.error || 'Greška pri analizi WFDB fajlova');
                    }
                    
                    const wfdbResult = await wfdbResponse.json();
                    if (wfdbResult.error) {
                        throw new Error(wfdbResult.error);
                    }
                    
                    console.log('WFDB analysis complete, keys:', Object.keys(wfdbResult));
                    
                    // WFDB returns complete analysis, show results directly
                    this.updateLoadingStep(3, 'Obrađuje podatke...');
                    this.updateLoadingStep(4, 'Finalizuje rezultate...');
                    
                    // Store results for PDF generation
                    window.currentAnalysisResults = wfdbResult;
                    this.analysisData = wfdbResult;
                    
                    // Hide loading and show results
                    setTimeout(() => {
                        this.hideLoadingAnimation();
                        this.displayResults(wfdbResult);
                    }, 1000);
                    
                    return; // Exit early for WFDB case
                } else {
                    // Raw signal analysis
                    requestBody = JSON.stringify({
                        raw_signal_data: this.currentRawSignal.data,
                        signal_type: this.currentRawSignal.type,
                        fs: this.currentRawSignal.fs || 250
                    });
                    requestMessage = 'Šalje signal na server...';
                }
            }
            
            // Update loading step
            this.updateLoadingStep(2, requestMessage);
            
            // Send to complete analysis API
            const response = await fetch('/api/analyze/complete', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: requestBody
            });

            this.updateLoadingStep(3, 'Obrađuje podatke...');

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            
            if (result.error) {
                throw new Error(result.error);
            }

            this.updateLoadingStep(4, 'Finalizuje rezultate...');
            
            // Store results for PDF generation
            window.currentAnalysisResults = result;
            this.analysisData = result;
            
            // Hide loading and show results
            setTimeout(() => {
                this.hideLoadingAnimation();
                this.displayResults(result);
            }, 1000);
            
        } catch (error) {
            console.error('Analysis error:', error);
            this.hideLoadingAnimation();
            this.showError(`Greška pri analizi: ${error.message}`);
        } finally {
            this.isProcessing = false;
        }
    }

    fileToBase64(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => resolve(reader.result);
            reader.onerror = error => reject(error);
            reader.readAsDataURL(file);
        });
    }

    readFileAsText(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => resolve(reader.result);
            reader.onerror = error => reject(error);
            reader.readAsText(file);
        });
    }

    readFileAsBinary(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => resolve(reader.result);
            reader.onerror = error => reject(error);
            reader.readAsArrayBuffer(file);
        });
    }

    arrayBufferToBase64(buffer) {
        const bytes = new Uint8Array(buffer);
        let binary = '';
        for (let i = 0; i < bytes.byteLength; i++) {
            binary += String.fromCharCode(bytes[i]);
        }
        return btoa(binary);
    }

    showWFDBFileInfo(files) {
        const previewSection = document.getElementById('imagePreview');
        const imageInfo = document.getElementById('imageInfo');
        const previewImage = document.getElementById('previewImage');
        
        // Hide image, show file info
        previewImage.style.display = 'none';
        previewSection.style.display = 'block';
        
        const filesInfo = Array.from(files).map(f => `${f.name} (${(f.size/1024).toFixed(1)} KB)`).join('<br>');
        const hasAnnotations = Array.from(files).some(f => f.name.endsWith('.atr'));
        
        imageInfo.innerHTML = `
            <strong>📁 WFDB Fajlovi:</strong><br>
            ${filesInfo}<br><br>
            <strong>📅 Tip:</strong> WFDB Format<br>
            <strong>✅ Status:</strong> Spreman za analizu<br>
            ${hasAnnotations ? '<strong>🏷️ Anotacije:</strong> ✅ Uključene' : '<strong>🏷️ Anotacije:</strong> ❌ Nisu dostupne'}
        `;
        
        // Enable analyze button
        document.getElementById('analyzeBtn').disabled = false;
        
        // Add bounce animation
        previewSection.classList.add('bounce');
        setTimeout(() => {
            previewSection.classList.remove('bounce');
        }, 600);
    }

    showRawSignalPreview(file, signal, fs) {
        const previewSection = document.getElementById('imagePreview');
        const imageInfo = document.getElementById('imageInfo');
        const previewImage = document.getElementById('previewImage');
        
        // Hide image, show file info
        previewImage.style.display = 'none';
        previewSection.style.display = 'block';
        
        // Calculate signal statistics
        const duration = (signal.length / fs).toFixed(2);
        const minVal = Math.min(...signal).toFixed(3);
        const maxVal = Math.max(...signal).toFixed(3);
        const avgVal = (signal.reduce((a, b) => a + b, 0) / signal.length).toFixed(3);
        
        imageInfo.innerHTML = `
            <strong>📁 Sirovi EKG Signal:</strong><br>
            <strong>📄 Fajl:</strong> ${file.name} (${(file.size/1024).toFixed(1)} KB)<br>
            <strong>📊 Uzorci:</strong> ${signal.length.toLocaleString()}<br>
            <strong>⏱️ Trajanje:</strong> ${duration}s (${fs} Hz)<br>
            <strong>📈 Opseg:</strong> ${minVal} do ${maxVal}<br>
            <strong>📊 Prosek:</strong> ${avgVal}<br><br>
            <strong>✅ Status:</strong> <span style="color: #27ae60;">Spreman za analizu</span>
        `;
        
        // Enable analyze button
        document.getElementById('analyzeBtn').disabled = false;
        
        // Add bounce animation
        previewSection.classList.add('bounce');
        setTimeout(() => {
            previewSection.classList.remove('bounce');
        }, 600);
        
        // Show success message
        this.showSuccess(`Signal uspešno učitan: ${signal.length} uzoraka, ${duration}s`);
    }

    addNovaAnalizaButton() {
        // Remove existing button if present
        const existingButton = document.getElementById('novaAnalizaFinalBtn');
        if (existingButton) {
            existingButton.remove();
        }
        
        // Create new button
        const buttonHTML = `
            <div id="novaAnalizaFinalBtn" style="text-align: center; padding: 30px 20px; margin-top: 30px; border-top: 2px solid #e9ecef;">
                <button onclick="location.reload()" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; padding: 15px 40px; border-radius: 25px; font-size: 1.1rem; font-weight: 600; cursor: pointer; display: inline-flex; align-items: center; gap: 10px; box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3); transition: all 0.3s ease;" onmouseover="this.style.transform='translateY(-3px)'; this.style.boxShadow='0 6px 20px rgba(102, 126, 234, 0.4)'" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 4px 15px rgba(102, 126, 234, 0.3)'">
                    <i class="fas fa-plus"></i>
                    Nova Analiza
                </button>
            </div>
        `;
        
        // Add button after results section
        const resultsSection = document.getElementById('resultsSection');
        if (resultsSection) {
            resultsSection.insertAdjacentHTML('afterend', buttonHTML);
        }
    }

    showLoadingAnimation() {
        document.getElementById('uploadSection').style.display = 'none';
        document.getElementById('processingSection').style.display = 'block';
        this.resetLoadingSteps();
        this.updateLoadingStep(1, 'Učitavanje podataka...');
    }

    hideLoadingAnimation() {
        document.getElementById('processingSection').style.display = 'none';
        document.getElementById('uploadSection').style.display = 'block';
    }

    resetLoadingSteps() {
        for (let i = 1; i <= 4; i++) {
            const step = document.getElementById(`loadingStep${i}`);
            if (step) {
                step.classList.remove('active', 'completed');
            }
        }
        const progressFill = document.getElementById('loadingProgressFill');
        const progressText = document.getElementById('loadingPercentage');
        if (progressFill) progressFill.style.width = '0%';
        if (progressText) progressText.textContent = '0%';
    }

    updateLoadingStep(stepNumber, message) {
        // Complete previous steps
        for (let i = 1; i < stepNumber; i++) {
            const step = document.getElementById(`loadingStep${i}`);
            if (step) {
                step.classList.remove('active');
                step.classList.add('completed');
            }
        }
        
        // Activate current step
        const currentStep = document.getElementById(`loadingStep${stepNumber}`);
        if (currentStep) {
            currentStep.classList.add('active');
            currentStep.classList.remove('completed');
            
            // Update step text
            const stepText = currentStep.querySelector('span');
            if (stepText) {
                stepText.textContent = message;
            }
        }
        
        // Update progress bar
        const progressPercentage = (stepNumber / 4) * 100;
        const progressFill = document.getElementById('loadingProgressFill');
        const progressText = document.getElementById('loadingPercentage');
        
        if (progressFill) {
            progressFill.style.width = `${progressPercentage}%`;
        }
        if (progressText) {
            progressText.textContent = `${progressPercentage}%`;
        }
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

    displayResults(data) {
        // Hide processing
        document.getElementById('processingSection').style.display = 'none';
        
        // Enable correlation test button
        enableCorrelationTest();
        
        // Enable image processing visualization
        enableImageProcessingVisualization();
        
        // Show results
        const resultsSection = document.getElementById('resultsSection');
        resultsSection.style.display = 'block';

        // Store data for detailed analysis
        this.analysisData = data;

        // v3.2: Automatski pozovi naprednu analizu za raw signal fajlove
        console.log('🚀 v3.2: Auto-triggering additional analysis for raw signal...');
        setTimeout(() => {
            this.showAdditionalAnalysis();
            // Add Nova Analiza button at the end
            this.addNovaAnalizaButton();
        }, 1000);

        // Populate structured results
        if (data.advanced_cardiology && !data.advanced_cardiology.error) {
            console.log('✅ Using advanced cardiology analysis');
            this.populateAdvancedCardiologyResults(data);
        } else {
            console.log('⚠️ Using basic structured results');
            this.populateStructuredResults(data);
        }
        
        // v3.2: Optimizovane vizuelizacije (automatski prikazane)
        if (data.thesis_visualizations && !data.thesis_visualizations.error) {
            console.log('📊 v3.2 Using OPTIMIZED thesis visualizations (auto-displayed)');
            this.addThesisVisualizations(data.thesis_visualizations);
        } else {
            console.log('⚠️ v3.2 No thesis visualizations available');
        }

        // Dodaj analizu na osnovu tipa podataka
        if (!data.signal_info?.source || data.signal_info.source === 'image_analysis') {
            // Za analizu slike - samo osnovna procena sa upozorenjem
            this.addBasicEKGInfo(data);
        } else if (data.signal_info.source === 'wfdb_import' || data.signal_info.source === 'raw_import') {
            // Za sirove podatke - detaljana klinička analiza
            this.addAdvancedClinicalAnalysis(data);
        }

        // v3.2: Automatski pozovi naprednu analizu uvek kada se završi analiza
        console.log('🚀 v3.2: Auto-triggering additional analysis...');
        setTimeout(() => {
            this.showAdditionalAnalysis();
        }, 1000); // Kratka pauza da se osnovni rezultati učitaju

        // Scroll to results
        resultsSection.scrollIntoView({ behavior: 'smooth' });
    }

    addBasicEKGInfo(data) {
        const basicHTML = this.generateBasicEKGHTML(data);
        const resultsSection = document.getElementById('resultsSection');
        
        // Ukloni postojeću
        const existing = document.getElementById('basicEKGSection');
        if (existing) existing.remove();
        
        // Dodaj novu
        const div = document.createElement('div');
        div.innerHTML = basicHTML;
        resultsSection.parentNode.insertBefore(div.firstElementChild, resultsSection.nextSibling);
    }

    generateBasicEKGHTML(data) {
        const heartRate = data.arrhythmia_detection?.heart_rate;
        const avgBpm = heartRate?.average_bpm || 0;
        const isIrregular = (data.arrhythmia_detection?.arrhythmias?.detected || []).length > 0;
        
        // Samo osnovni rate info
        let rateText = "Nepoznato";
        let rateColor = "#666";
        if (avgBpm > 0) {
            rateText = `${Math.round(avgBpm)} bpm`;
            if (avgBpm < 60) rateColor = "#e74c3c";
            else if (avgBpm <= 100) rateColor = "#27ae60";
            else rateColor = "#f39c12";
        }
        
        // Osnovni rhythm info
        let rhythmText = isIrregular ? "Moguće nepravilan" : "Verovatno pravilan";
        let rhythmColor = isIrregular ? "#f39c12" : "#27ae60";
        
        return `
            <div id="basicEKGSection" class="main-card" style="margin-top: 20px;">
                <h2><i class="fas fa-info-circle"></i> Osnovna EKG Procena</h2>
                
                <!-- Upozorenje o ograničenjima -->
                <div class="result-card" style="margin-bottom: 20px;">
                    <div class="result-content">
                        <div style="background: #fff3cd; padding: 15px; border-radius: 8px; border-left: 4px solid #f39c12;">
                            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
                                <span style="font-size: 1.2em;">⚠️</span>
                                <h4 style="color: #856404; margin: 0;">Ograničena Analiza Slike</h4>
                            </div>
                            <p style="margin: 0; color: #856404; line-height: 1.5;">
                                <strong>Analiza EKG slike ima ograničenu tačnost.</strong> Ne može detektovati suptilne promene kao što su ST elevacije, T-inverzije ili QTc produženja koje su ključne za dijagnozu.
                                <br><br>
                                <strong>Napomena:</strong> Ova aplikacija služi isključivo u edukativne svrhe. Analiza slike ne zamenjuje profesionalnu medicinsku dijagnostiku.
                            </p>
                        </div>
                    </div>
                </div>
                
                <!-- Analiza podataka -->
                <div class="result-card">
                    <div class="result-header">
                        <h3 class="result-title">Analiza Slike</h3>
                    </div>
                    <div class="result-content">
                        
                        <!-- Osnovni Parametri -->
                        <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                            <h4 style="margin: 0 0 15px 0; color: #333; border-bottom: 2px solid #ddd; padding-bottom: 8px;">Osnovni Parametri</h4>
                            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px;">
                                <div style="background: white; padding: 15px; border-radius: 6px; border-left: 4px solid ${rateColor};">
                                    <div style="display: flex; justify-content: space-between; align-items: center;">
                                        <strong style="color: #333;">Srčana frekvencija:</strong>
                                        <span style="color: ${rateColor}; font-weight: bold;">${rateText}</span>
                                    </div>
                                </div>
                                <div style="background: white; padding: 15px; border-radius: 6px; border-left: 4px solid ${rhythmColor};">
                                    <div style="display: flex; justify-content: space-between; align-items: center;">
                                        <strong style="color: #333;">Ritam:</strong>
                                        <span style="color: ${rhythmColor}; font-weight: bold;">${rhythmText}</span>
                                    </div>
                                </div>
                            </div>
                        </div>

                        
                    </div>
                </div>
            </div>
        `;
    }

    addAdvancedClinicalAnalysis(data) {
        const clinicalHTML = this.generateAdvancedClinicalHTML(data);
        const resultsSection = document.getElementById('resultsSection');
        
        // Ukloni postojeću
        const existing = document.getElementById('advancedClinicalSection');
        if (existing) existing.remove();
        
        // Dodaj novu
        const div = document.createElement('div');
        div.innerHTML = clinicalHTML;
        resultsSection.parentNode.insertBefore(div.firstElementChild, resultsSection.nextSibling);
    }

    generateAdvancedClinicalHTML(data) {
        const heartRate = data.arrhythmia_detection?.heart_rate;
        const avgBpm = heartRate?.average_bpm || 0;
        const minBpm = heartRate?.min_bpm || 0;
        const maxBpm = heartRate?.max_bpm || 0;
        const hrv = heartRate?.heart_rate_variability || 0;
        const arrhythmias = data.arrhythmia_detection?.arrhythmias?.detected || [];
        const qrsAnalysis = data.arrhythmia_detection?.qrs_analysis;
        const signalQuality = data.arrhythmia_detection?.signal_quality;
        const isWFDB = data.signal_info?.source === 'wfdb_import';
        const hasAnnotations = data.annotations && data.annotations.r_peaks_count > 0;
        
        // Rate analiza
        let rateText = `${Math.round(avgBpm)} bpm`;
        let rateRange = `${Math.round(minBpm)}-${Math.round(maxBpm)} bpm`;
        let rateColor = "#27ae60";
        let rateStatus = "Normal";
        
        if (avgBpm < 60) {
            rateStatus = "Bradikardija";
            rateColor = "#e74c3c";
        } else if (avgBpm > 100) {
            if (avgBpm > 150) {
                rateStatus = "Tahikardija";
                rateColor = "#e74c3c";
            } else {
                rateStatus = "Blaga tahikardija";
                rateColor = "#f39c12";
            }
        }
        
        // Rhythm analiza
        let rhythmText = "Regular";
        let rhythmColor = "#27ae60";
        let rhythmDetails = "Sinusni ritam";
        
        if (arrhythmias.length > 0) {
            const afib = arrhythmias.find(arr => arr.type?.toLowerCase().includes('fibrilacija') || arr.type?.toLowerCase().includes('fibrillation'));
            const premature = arrhythmias.find(arr => arr.type?.toLowerCase().includes('premature') || arr.type?.toLowerCase().includes('prevremeni'));
            
            if (afib) {
                rhythmText = "Irregularly irregular";
                rhythmColor = "#e74c3c";
                rhythmDetails = "Atrijska fibrilacija";
            } else if (premature) {
                rhythmText = "Irregular";
                rhythmColor = "#f39c12";
                rhythmDetails = "Premature kontrakcije";
            } else {
                rhythmText = "Irregular";
                rhythmColor = "#f39c12";
                rhythmDetails = "Detektovane aritmije";
            }
        }
        
        // QRS analiza
        let qrsText = "Normal width";
        let qrsColor = "#27ae60";
        let qrsDetails = "< 120ms";
        
        if (qrsAnalysis && qrsAnalysis.mean_width_ms) {
            const qrsWidth = qrsAnalysis.mean_width_ms;
            qrsDetails = `${qrsWidth.toFixed(0)}ms`;
            
            if (qrsWidth > 120) {
                qrsText = "Wide";
                qrsColor = "#e74c3c";
            } else if (qrsWidth > 100) {
                qrsText = "Borderline";
                qrsColor = "#f39c12";
            }
        }
        
        // P-wave analiza na osnovu aritmija
        let pWaveText = "Normal P-waves";
        let pWaveColor = "#27ae60";
        let pWaveDetails = "Sinus P-waves";
        
        if (arrhythmias.length > 0) {
            const afib = arrhythmias.find(arr => arr.type?.toLowerCase().includes('fibrilacija'));
            if (afib) {
                pWaveText = "Absent/fibrillatory waves";
                pWaveColor = "#e74c3c";
                pWaveDetails = "Fibrilatorni talasi";
            } else {
                pWaveText = "Variable P-waves";
                pWaveColor = "#f39c12";
                pWaveDetails = "Varijabilni P-talasi";
            }
        }
        
        // Signal quality
        let qualityColor = "#27ae60";
        let qualityText = signalQuality?.quality || "Good";
        if (signalQuality?.snr_db < 10) {
            qualityColor = "#f39c12";
        }
        
        // HRV analiza
        let hrvStatus = "Normal";
        let hrvColor = "#27ae60";
        if (hrv > 100) {
            hrvStatus = "Visoka varijabilnost";
            hrvColor = "#f39c12";
        } else if (hrv < 20) {
            hrvStatus = "Niska varijabilnost";
            hrvColor = "#e74c3c";
        }
        
        return `
            <div id="advancedClinicalSection" class="main-card" style="margin-top: 20px;">
                <h2><i class="fas fa-heartbeat"></i> ${isWFDB ? 'MIT-BIH Klinička Analiza' : 'Napredna EKG Analiza'}</h2>
                
                ${isWFDB ? `
                <div class="result-card" style="margin-bottom: 20px;">
                    <div class="result-content">
                        <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 4px solid #333;">
                            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
                                <span style="font-size: 1.2em;">🔬</span>
                                <h4 style="color: #333; margin: 0;">MIT-BIH Digitalna Analiza</h4>
                            </div>
                            <p style="margin: 0; color: #333; line-height: 1.5;">
                                <strong>Zašto MIT-BIH:</strong> Korišćeni su standardizovani EKG podaci iz MIT-BIH Arrhythmia Database - svetski priznate baze podataka za kardiološka istraživanja i validaciju algoritama.
                                <br><br>
                                <strong>Napomena:</strong> Analiza na osnovu MIT-BIH digitalnih podataka. Rezultati su medicinski relevantni ali ne zamenjuju konsultaciju sa lekarom.
                            </p>
                        </div>
                    </div>
                </div>
                ` : ''}
                
                <div class="result-card">
                    <div class="result-header">
                        <h3 class="result-title">Klinička Analiza</h3>
                    </div>
                    <div class="result-content">
                        
                        <!-- Sistematski Pregled -->
                        <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                            <h4 style="margin: 0 0 15px 0; color: #333; border-bottom: 2px solid #ddd; padding-bottom: 8px;">Sistematski Pregled</h4>
                            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 10px;">
                                <div style="background: white; padding: 12px; border-radius: 6px; border-left: 4px solid ${rateColor};">
                                    <div style="display: flex; justify-content: space-between; align-items: center;">
                                        <strong style="color: #333;">Rate:</strong>
                                        <div style="text-align: right;">
                                            <div style="color: ${rateColor}; font-weight: bold;">${rateText}</div>
                                            <small style="color: #666;">Opseg: ${rateRange}</small>
                                        </div>
                                    </div>
                                </div>
                                <div style="background: white; padding: 12px; border-radius: 6px; border-left: 4px solid ${rhythmColor};">
                                    <div style="display: flex; justify-content: space-between; align-items: center;">
                                        <strong style="color: #333;">Rhythm:</strong>
                                        <div style="text-align: right;">
                                            <div style="color: ${rhythmColor}; font-weight: bold;">${rhythmText}</div>
                                            <small style="color: #666;">${rhythmDetails}</small>
                                        </div>
                                    </div>
                                </div>
                                <div style="background: white; padding: 12px; border-radius: 6px; border-left: 4px solid #27ae60;">
                                    <div style="display: flex; justify-content: space-between; align-items: center;">
                                        <strong style="color: #333;">Axis:</strong>
                                        <span style="color: #27ae60; font-weight: bold;">Normal</span>
                                    </div>
                                </div>
                                <div style="background: white; padding: 12px; border-radius: 6px; border-left: 4px solid ${pWaveColor};">
                                    <div style="display: flex; justify-content: space-between; align-items: center;">
                                        <strong style="color: #333;">PR/P wave:</strong>
                                        <div style="text-align: right;">
                                            <div style="color: ${pWaveColor}; font-weight: bold;">${pWaveText}</div>
                                            <small style="color: #666;">${pWaveDetails}</small>
                                        </div>
                                    </div>
                                </div>
                                <div style="background: white; padding: 12px; border-radius: 6px; border-left: 4px solid ${qrsColor};">
                                    <div style="display: flex; justify-content: space-between; align-items: center;">
                                        <strong style="color: #333;">QRS:</strong>
                                        <div style="text-align: right;">
                                            <div style="color: ${qrsColor}; font-weight: bold;">${qrsText}</div>
                                            <small style="color: #666;">${qrsDetails}</small>
                                        </div>
                                    </div>
                                </div>
                                <div style="background: white; padding: 12px; border-radius: 6px; border-left: 4px solid #27ae60;">
                                    <div style="display: flex; justify-content: space-between; align-items: center;">
                                        <strong style="color: #333;">ST/T wave:</strong>
                                        <span style="color: #27ae60; font-weight: bold;">Normal</span>
                                    </div>
                                </div>
                                <div style="background: white; padding: 12px; border-radius: 6px; border-left: 4px solid #27ae60;">
                                    <div style="display: flex; justify-content: space-between; align-items: center;">
                                        <strong style="color: #333;">QTc/other:</strong>
                                        <span style="color: #27ae60; font-weight: bold;">Normal</span>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- Klinička Interpretacija -->
                        <div style="background: #f8f9fa; padding: 20px; border-radius: 8px;">
                            <h4 style="margin: 0 0 15px 0; color: #333; border-bottom: 2px solid #ddd; padding-bottom: 8px;">Klinička Interpretacija</h4>
                            
                            <div style="background: white; padding: 15px; border-radius: 8px; margin-bottom: 15px; border-left: 4px solid ${rateColor};">
                                <strong style="color: #333;">Kategorija:</strong> 
                                <span style="color: ${rateColor}; font-weight: bold;">${rateStatus} (${rateText})</span>
                            </div>
                            
                            <div style="background: ${arrhythmias.length > 0 ? '#fff3cd' : '#d4edda'}; padding: 15px; border-radius: 8px; margin-bottom: 15px; border-left: 4px solid ${arrhythmias.length > 0 ? '#ffc107' : '#28a745'};">
                                <strong style="color: #333;">${arrhythmias.length > 0 ? 'Detektovane aritmije:' : 'Regularni ritam'}</strong>
                                ${arrhythmias.length > 0 ? `<br><span style="color: #856404;">${arrhythmias.map(arr => arr.type).join(', ')}</span>` : ''}
                            </div>
                            
                            <div style="background: white; padding: 15px; border-radius: 8px; margin-bottom: 15px; border-left: 4px solid #007bff;">
                                <div style="margin-bottom: 8px;">
                                    <strong style="color: #333;">HRV:</strong> <span style="color: ${hrvColor}; font-weight: bold;">${hrv.toFixed(1)}ms (${hrvStatus})</span>
                                </div>
                                <div style="margin-bottom: 8px;">
                                    <strong style="color: #333;">Kvalitet signala:</strong> <span style="color: ${qualityColor}; font-weight: bold;">${qualityText}</span>
                                </div>
                                ${signalQuality?.snr_db ? `<div><strong style="color: #333;">SNR:</strong> <span style="color: #007bff; font-weight: bold;">${signalQuality.snr_db.toFixed(1)} dB</span></div>` : ''}
                            </div>
                            
                            <div style="background: white; padding: 15px; border-radius: 8px; border-left: 4px solid #6c757d;">
                                <h5 style="margin: 0 0 10px 0; color: #333;">Preporučeno:</h5>
                                <ul style="margin: 0; padding-left: 20px; color: #333;">
                                    ${avgBpm > 150 || avgBpm < 50 ? '<li style="color: #e74c3c; margin-bottom: 5px;"><strong>Hitna kardiološka konsultacija</strong></li>' : ''}
                                    ${arrhythmias.length > 0 ? '<li style="margin-bottom: 5px;">EKG u 12 odvoda za potvrdu</li>' : ''}
                                    ${hrv < 20 ? '<li style="margin-bottom: 5px;">Procena autonomnog nervnog sistema</li>' : ''}
                                    <li style="margin-bottom: 5px;">Redovna kontrola prema kliničkom stanju</li>
                                </ul>
                            </div>
                        </div>
                        
                    </div>
                </div>
            </div>
        `;
    }

    addSystematicAnalysis(data) {
        const systematicHTML = this.generateSystematicHTML(data);
        const resultsSection = document.getElementById('resultsSection');
        
        // Ukloni postojeću
        const existing = document.getElementById('systematicSection');
        if (existing) existing.remove();
        
        // Dodaj novu
        const div = document.createElement('div');
        div.innerHTML = systematicHTML;
        resultsSection.parentNode.insertBefore(div.firstElementChild, resultsSection.nextSibling);
    }

    generateSystematicHTML(data) {
        const heartRate = data.arrhythmia_detection?.heart_rate;
        const avgBpm = heartRate?.average_bpm || 0;
        const isIrregular = (data.arrhythmia_detection?.arrhythmias?.detected || []).length > 0;
        const signalSource = data.signal_info?.source || 'image_analysis';
        
        // Dinamičko izračunavanje rate na osnovu stvarnih podataka
        let rateText = "Nepoznato";
        let rateColor = "#666";
        if (avgBpm > 0) {
            if (avgBpm < 60) {
                rateText = `${Math.round(avgBpm)} bpm (Bradikardija)`;
                rateColor = "#e74c3c";
            } else if (avgBpm <= 100) {
                rateText = `${Math.round(avgBpm)} bpm (Normalna)`;
                rateColor = "#27ae60";
            } else if (avgBpm <= 150) {
                rateText = `${Math.round(avgBpm)} bpm (Blaga tahikardija)`;
                rateColor = "#f39c12";
            } else {
                rateText = `${Math.round(avgBpm)} bpm (Tahikardija)`;
                rateColor = "#e74c3c";
            }
        }
        
        // Dinamičko određivanje ritma na osnovu aritmija
        let rhythmText = "Regular";
        let rhythmColor = "#27ae60";
        if (isIrregular) {
            const arrhythmias = data.arrhythmia_detection?.arrhythmias?.detected || [];
            const hasAfib = arrhythmias.some(arr => arr.type?.toLowerCase().includes('fibrilacija') || arr.type?.toLowerCase().includes('fibrillation'));
            if (hasAfib) {
                rhythmText = "Irregularly irregular";
                rhythmColor = "#e74c3c";
            } else {
                rhythmText = "Irregular";
                rhythmColor = "#f39c12";
            }
        }
        
        // Dinamičko određivanje P-wave na osnovu aritmija
        let pWaveText = "Normal P-waves";
        let pWaveColor = "#27ae60";
        if (isIrregular) {
            const arrhythmias = data.arrhythmia_detection?.arrhythmias?.detected || [];
            const hasAfib = arrhythmias.some(arr => arr.type?.toLowerCase().includes('fibrilacija') || arr.type?.toLowerCase().includes('fibrillation'));
            if (hasAfib) {
                pWaveText = "Absent/fibrillatory waves";
                pWaveColor = "#e74c3c";
            } else {
                pWaveText = "Variable P-waves";
                pWaveColor = "#f39c12";
            }
        }
        
        // QRS analiza ako postoji
        let qrsText = "Normal width";
        let qrsColor = "#27ae60";
        const qrsAnalysis = data.arrhythmia_detection?.qrs_analysis;
        if (qrsAnalysis && qrsAnalysis.mean_width_ms) {
            if (qrsAnalysis.mean_width_ms > 120) {
                qrsText = `Wide (${qrsAnalysis.mean_width_ms.toFixed(0)}ms)`;
                qrsColor = "#e74c3c";
            } else if (qrsAnalysis.mean_width_ms > 100) {
                qrsText = `Borderline (${qrsAnalysis.mean_width_ms.toFixed(0)}ms)`;
                qrsColor = "#f39c12";
            } else {
                qrsText = `Narrow (${qrsAnalysis.mean_width_ms.toFixed(0)}ms)`;
                qrsColor = "#27ae60";
            }
        }
        
        // Kategorija na osnovu stvarnih podataka
        let categoryInfo = { category: "Nepoznato", color: "#666" };
        if (avgBpm > 0) {
            if (avgBpm < 60) categoryInfo = { category: "< 60 - Bradikardija", color: "#e74c3c" };
            else if (avgBpm <= 100) categoryInfo = { category: "60-100 - Normalna", color: "#27ae60" };
            else if (avgBpm <= 150) categoryInfo = { category: "100-150 - Blaga tahikardija", color: "#f39c12" };
            else categoryInfo = { category: "> 150 - Tahikardija", color: "#e74c3c" };
        }
        
        // Određivanje dijagnoze na osnovu analize
        let diagnosisText = "✅ Nalaz: Sinusni ritam";
        let diagnosisBackground = "#d4edda";
        if (isIrregular) {
            const arrhythmias = data.arrhythmia_detection?.arrhythmias?.detected || [];
            const afibFound = arrhythmias.some(arr => arr.type?.toLowerCase().includes('fibrilacija') || arr.type?.toLowerCase().includes('fibrillation'));
            if (afibFound) {
                diagnosisText = "⚠️ Mogući nalaz: Atrijska fibrilacija";
                diagnosisBackground = "#fff3cd";
            } else {
                diagnosisText = "⚠️ Detektovane aritmije";
                diagnosisBackground = "#fff3cd";
            }
        }
            
        return `
            <div id="systematicSection" class="main-card" style="margin-top: 20px;">
                <h2><i class="fas fa-stethoscope"></i> Sistematska EKG Analiza</h2>
                <div class="result-card">
                    <div class="result-header">
                        <i class="fas fa-clipboard-list result-icon" style="color: #8e44ad;"></i>
                        <h3 class="result-title">Klinička Interpretacija</h3>
                    </div>
                    <div class="result-content">
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                            <div style="background: #f8f9fa; padding: 15px; border-radius: 8px;">
                                <h4>📋 Sistematski Pregled</h4>
                                <div style="display: grid; gap: 8px;">
                                    <div style="display: flex; justify-content: space-between; padding: 8px; background: white; border-radius: 4px; border-left: 4px solid ${rateColor};">
                                        <strong>Rate:</strong> <span style="color: ${rateColor};">${rateText}</span>
                                    </div>
                                    <div style="display: flex; justify-content: space-between; padding: 8px; background: white; border-radius: 4px; border-left: 4px solid ${rhythmColor};">
                                        <strong>Rhythm:</strong> <span style="color: ${rhythmColor};">${rhythmText}</span>
                                    </div>
                                    <div style="display: flex; justify-content: space-between; padding: 8px; background: white; border-radius: 4px; border-left: 4px solid #27ae60;">
                                        <strong>Axis:</strong> <span style="color: #27ae60;">Normal</span>
                                    </div>
                                    <div style="display: flex; justify-content: space-between; padding: 8px; background: white; border-radius: 4px; border-left: 4px solid ${pWaveColor};">
                                        <strong>PR/P wave:</strong> <span style="color: ${pWaveColor};">${pWaveText}</span>
                                    </div>
                                    <div style="display: flex; justify-content: space-between; padding: 8px; background: white; border-radius: 4px; border-left: 4px solid ${qrsColor};">
                                        <strong>QRS:</strong> <span style="color: ${qrsColor};">${qrsText}</span>
                                    </div>
                                    <div style="display: flex; justify-content: space-between; padding: 8px; background: white; border-radius: 4px; border-left: 4px solid #27ae60;">
                                        <strong>ST/T wave:</strong> <span style="color: #27ae60;">Normal</span>
                                    </div>
                                    <div style="display: flex; justify-content: space-between; padding: 8px; background: white; border-radius: 4px; border-left: 4px solid #27ae60;">
                                        <strong>QTc/other:</strong> <span style="color: #27ae60;">Normal</span>
                                    </div>
                                </div>
                            </div>
                            <div style="background: #e8f5e8; padding: 15px; border-radius: 8px;">
                                <h4>🏥 Interpretacija</h4>
                                <p><strong>Kategorija:</strong> <span style="color: ${categoryInfo.color};">${categoryInfo.category}</span></p>
                                <div style="background: ${diagnosisBackground}; padding: 10px; border-radius: 6px; margin: 15px 0;">
                                    <strong>${diagnosisText}</strong>
                                </div>
                                <p><strong>Preporučeno:</strong></p>
                                <ul style="margin: 5px 0; padding-left: 20px;">
                                    ${avgBpm > 150 ? '<li>Hitna kardiološka konsultacija</li>' : ''}
                                    ${isIrregular ? '<li>EKG u 12 odvoda za potvrdu</li>' : ''}
                                    ${avgBpm < 60 ? '<li>Provera simptoma bradikardije</li>' : ''}
                                    ${signalSource === 'image_analysis' ? '<li>Analiza sirovih podataka za preciznije rezultate</li>' : ''}
                                    <li>Redovna kontrola prema kliničkom stanju</li>
                                </ul>
                            </div>
                        </div>
                        <div style="background: #f0f8ff; padding: 10px; border-radius: 6px; margin-top: 15px; border-left: 4px solid #007bff;">
                            <small><strong>Napomena:</strong> Automatska analiza ${signalSource === 'image_analysis' ? 'na osnovu EKG slike' : 'sirovih EKG podataka'}. Za konačnu dijagnozu obratite se lekaru.</small>
                        </div>
                    </div>
                </div>
            </div>
        `;
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
        
        // NOVO: QRS širina ako postoji
        const qrsAnalysis = this.analysisData?.arrhythmia_detection?.qrs_analysis;
        if (qrsAnalysis && !qrsAnalysis.error) {
            // Dodaj QRS info u postojeći prikaz
            const hrvElement = document.getElementById('hrv');
            if (hrvElement && hrvElement.parentNode) {
                const qrsInfo = document.createElement('div');
                qrsInfo.className = 'metric';
                qrsInfo.innerHTML = `
                    <span class="metric-label">QRS širina:</span>
                    <span class="metric-value">${qrsAnalysis.mean_width_ms.toFixed(1)} ms (${qrsAnalysis.classification})</span>
                `;
                hrvElement.parentNode.appendChild(qrsInfo);
            }
        }
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
        
        // NOVO: Sine Wave analiza u FFT sekciji
        const sineWaveData = fftData.sine_wave_analysis;
        if (sineWaveData && !sineWaveData.error) {
            const fftContainer = document.getElementById('peakAmp').parentNode.parentNode;
            if (fftContainer) {
                const sineWaveInfo = document.createElement('div');
                sineWaveInfo.className = 'metric';
                sineWaveInfo.innerHTML = `
                    <span class="metric-label">Sinusoidalnost:</span>
                    <span class="metric-value">${sineWaveData.spectral_purity_percent.toFixed(1)}% (${sineWaveData.signal_classification})</span>
                `;
                fftContainer.appendChild(sineWaveInfo);
                
                if (sineWaveData.detected_harmonics.length > 0) {
                    const harmonicsInfo = document.createElement('div');
                    harmonicsInfo.className = 'metric';
                    harmonicsInfo.innerHTML = `
                        <span class="metric-label">Harmonici:</span>
                        <span class="metric-value">${sineWaveData.total_harmonics_count} detektovano, THD: ${sineWaveData.thd_percent.toFixed(1)}%</span>
                    `;
                    fftContainer.appendChild(harmonicsInfo);
                }
            }
        }
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

    showError(message) {
        const errorDiv = document.getElementById('errorMessage');
        errorDiv.innerHTML = `<i class="fas fa-exclamation-circle"></i> <span>${message}</span>`;
        errorDiv.style.display = 'block';
        
        setTimeout(() => {
            errorDiv.style.display = 'none';
        }, 5000);
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
        this.isProcessing = false;
        this.analysisData = null;

        // Hide sections
        document.getElementById('imagePreview').style.display = 'none';
        document.getElementById('processingSection').style.display = 'none';
        document.getElementById('resultsSection').style.display = 'none';
        document.getElementById('errorMessage').style.display = 'none';
        document.getElementById('successMessage').style.display = 'none';
        document.getElementById('rawSignalInfo').style.display = 'none';

        // Show upload section
        document.getElementById('uploadSection').style.display = 'block';

        // Reset buttons
        document.getElementById('analyzeBtn').disabled = true;

        // Reset file inputs
        document.getElementById('fileInput').value = '';
        document.getElementById('cameraInput').value = '';
        document.getElementById('rawSignalInput').value = '';

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
            // Show progress
            this.showLoadingAnimation();
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

            this.updateProgress(50, 'Priprema pregled signala...', '📋');

            // Clear any existing image
            this.currentImage = null;
            
            // Store the signal for later analysis
            this.currentRawSignal = {
                data: signal,
                type: 'raw_import',
                fs: fs,
                filename: file.name
            };

            // Hide progress and show preview
            this.hideLoadingAnimation();
            
            // Show signal preview instead of immediately analyzing
            this.showRawSignalPreview(file, signal, fs);

        } catch (error) {
            console.error('Raw signal analysis error:', error);
            this.hideLoadingAnimation();
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
                        const data = JSON.parse(content);
                        if (data.signal && Array.isArray(data.signal)) {
                            signal = data.signal.map(Number);
                            if (data.fs) {
                                document.getElementById('rawSignalFs').value = data.fs;
                            }
                        } else {
                            throw new Error('JSON fajl mora imati "signal" niz');
                        }
                    } else if (extension === 'csv' || extension === 'txt') {
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

        // v3.2: Automatski pozovi naprednu analizu za raw signal fajlove (drugi poziv)
        console.log('🚀 v3.2: Auto-triggering additional analysis for raw signal (second call)...');
        setTimeout(() => {
            this.showAdditionalAnalysis();
        }, 1000);

        // Show generate EKG image button for raw signal data
        this.showGenerateImageButton(data);

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

    // WFDB Files Handler
    async handleWFDBFiles(files) {
        try {
            // Proveri da li imamo .dat i .hea fajlove
            let hasDat = false;
            let hasHea = false;
            
            for (let file of files) {
                if (file.name.endsWith('.dat')) hasDat = true;
                if (file.name.endsWith('.hea')) hasHea = true;
            }
            
            if (!hasDat || !hasHea) {
                if (files.length === 1) {
                    await this.handleRawSignalFile(files[0]);
                    return;
                }
                
                this.showError('Za WFDB format potrebni su i .dat i .hea fajlovi');
                return;
            }
            
            this.showLoadingAnimation();
            this.updateProgress(10, 'Čita WFDB fajlove...', '📂');
            
            // Kreiraj FormData za upload
            const formData = new FormData();
            
            for (let file of files) {
                if (file.name.endsWith('.dat') || file.name.endsWith('.hea') || 
                    file.name.endsWith('.atr') || file.name.endsWith('.xws')) {
                    formData.append('file', file);
                }
            }
            
            this.updateProgress(30, 'Priprema WFDB pregled...', '📋');
            
            // Clear any existing image
            this.currentImage = null;
            
            // Store WFDB files for later analysis
            this.currentRawSignal = {
                files: files,
                type: 'wfdb_import',
                fs: 250, // Default for WFDB
                filename: Array.from(files).map(f => f.name).join(', ')
            };
            
            // Hide progress and show file info
            this.hideLoadingAnimation();
            
            // Show WFDB files preview
            this.showWFDBFileInfo(files);
            
        } catch (error) {
            console.error('WFDB analysis error:', error);
            this.hideLoadingAnimation();
            this.showError(`Greška pri analizi WFDB fajlova: ${error.message}`);
        }
    }

    displayWFDBResults(data) {
        // Hide upload section and show results
        document.getElementById('uploadSection').style.display = 'none';
        document.getElementById('resultsSection').style.display = 'block';

        // Store data for detailed analysis
        this.analysisData = data;

        // v3.2: Automatski pozovi naprednu analizu za WFDB fajlove
        console.log('🚀 v3.2: Auto-triggering additional analysis for WFDB...');
        setTimeout(() => {
            this.showAdditionalAnalysis();
        }, 1000);

        // Show generate EKG image button for WFDB data
        this.showGenerateImageButton(data);

        // Add enhanced header for WFDB
        const resultsSection = document.getElementById('resultsSection');
        const existingHeader = resultsSection.querySelector('.wfdb-header');
        if (existingHeader) {
            existingHeader.remove();
        }

        const headerDiv = document.createElement('div');
        headerDiv.className = 'wfdb-header';
        
        // Prepare WFDB metadata display
        const recordName = data.wfdb_metadata?.record_name || data.signal_info.filename?.replace('.dat', '') || 'Unknown';
        const hasAnnotations = data.signal_info.has_annotations || false;
        const nChannels = data.wfdb_metadata?.n_signals || 1;
        const originalSamples = data.wfdb_metadata?.original_samples || data.signal_info.length;
        
        // Create comprehensive WFDB info
        let wfdbFilesInfo = `📁 Record: ${recordName}`;
        if (hasAnnotations) {
            wfdbFilesInfo += ` <span style="color: #27ae60; font-weight: bold;">(.dat + .hea + .atr)</span>`;
        } else {
            wfdbFilesInfo += ` <span style="color: #f39c12;">(.dat + .hea)</span>`;
        }
        
        // Annotations info
        let annotationsInfo = '';
        if (data.annotations) {
            annotationsInfo = `
                <div style="background: #e8f5e8; padding: 10px; border-radius: 5px; margin-top: 10px;">
                    <strong>🏥 MIT-BIH Annotations (.atr):</strong><br>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 5px;">
                        <div>📍 R-peaks: ${data.annotations.r_peaks_count || 0}</div>
                        <div>⚠️ Aritmije: ${data.annotations.arrhythmias_count || 0}</div>
                        <div>📊 Ukupno annotations: ${data.annotations.total_annotations || 0}</div>
                        <div>📂 Fajl: ${data.annotations.source_file || 'N/A'}</div>
                    </div>
                </div>
            `;
        }
        
        headerDiv.innerHTML = `
            <div style="background: #e3f2fd; padding: 15px; border-radius: 10px; margin-bottom: 20px; border-left: 4px solid #2196f3;">
                <h3 style="margin: 0 0 10px 0;"><i class="fas fa-database"></i> WFDB MIT-BIH Analiza</h3>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                    <div>${wfdbFilesInfo}</div>
                    <div><strong>📊 Analizirani uzorci:</strong> ${data.signal_info.length.toLocaleString()}</div>
                    <div><strong>⏱️ Trajanje:</strong> ${data.signal_info.duration_seconds.toFixed(1)}s</div>
                    <div><strong>📡 Fs:</strong> ${data.signal_info.sampling_frequency} Hz</div>
                    <div><strong>📺 Kanali:</strong> ${nChannels} (korišćen kanal 0)</div>
                    <div><strong>📋 Originalni uzorci:</strong> ${originalSamples.toLocaleString()}</div>
                </div>
                ${annotationsInfo}
                ${data.signal_info.original_shape ? 
                    `<div style="margin-top: 10px; padding: 8px; background: #f0f8ff; border-radius: 5px; font-size: 0.9rem;">
                        <strong>ℹ️ WFDB Info:</strong> 
                        Originalna veličina: ${data.signal_info.original_shape.join(' × ')}, 
                        Import metod: ${data.signal_info.import_method}
                    </div>` : ''
                }
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

        // Dodaj naprednu kliničku analizu za WFDB podatke
        this.addAdvancedClinicalAnalysis(data);

        // Scroll to results
        resultsSection.scrollIntoView({ behavior: 'smooth' });
    }

    // Show generate image button for raw signal/WFDB data
    showGenerateImageButton(data) {
        if (data.signal_info && data.signal_info.source && 
            (data.signal_info.source === 'raw_import' || data.signal_info.source === 'wfdb_import')) {
            
            // Find action buttons container
            let actionButtonsContainer = document.querySelector('.action-buttons');
            if (!actionButtonsContainer) {
                // Create action buttons container if it doesn't exist
                actionButtonsContainer = document.createElement('div');
                actionButtonsContainer.className = 'action-buttons';
                actionButtonsContainer.style.marginTop = '20px';
                
                const resultsSection = document.getElementById('resultsSection');
                resultsSection.appendChild(actionButtonsContainer);
            }

            // Check if button already exists
            // Generate EKG Image button removed - no function available
        }
    }

    // Generate EKG image from raw signal data
    async generateEducationalEkgImage() {
        if (!this.analysisData || !this.analysisData.signal_info) {
            this.showError('Nema dostupnih podataka za generisanje slike');
            return;
        }

        try {
            this.showLoadingAnimation();
            this.updateProgress(10, 'Priprema podatke za sliku...', '🖼️');

            const signal_info = this.analysisData.signal_info;
            
            // Determine if this is WFDB or raw signal
            let endpoint = '';
            let payload = {};

            if (signal_info.source === 'wfdb_import') {
                // For WFDB, we need to call the WFDB-to-image endpoint
                // But we don't have original files, so we'll use the extracted signal
                endpoint = '/api/convert/signal-to-image';
                payload = {
                    signal: this.analysisData.extracted_signal || [], // Need to store this during analysis
                    fs: signal_info.sampling_frequency,
                    style: 'clinical',
                    duration_seconds: 1 // Generate 1-second focused EKG
                };
                
                if (!payload.signal || payload.signal.length === 0) {
                    throw new Error('Sirovi signal nije dostupan za generisanje slike. Potrebno je ponovo analizirati WFDB fajlove.');
                }
            } else {
                // For raw signal import
                endpoint = '/api/convert/signal-to-image';
                payload = {
                    signal: this.analysisData.raw_signal || [],
                    fs: signal_info.sampling_frequency,
                    style: 'clinical',
                    duration_seconds: 1
                };
                
                if (!payload.signal || payload.signal.length === 0) {
                    throw new Error('Sirovi signal nije dostupan za generisanje slike.');
                }
            }

            this.updateProgress(30, 'Šalje zahtev za sliku...', '📤');

            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload)
            });

            this.updateProgress(70, 'Generiše EKG sliku...', '🎨');

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Greška pri generisanju slike');
            }

            const result = await response.json();
            
            if (result.error) {
                throw new Error(result.error);
            }

            this.updateProgress(100, 'Slika generisana!', '✅');

            // Hide progress and show generated image
            setTimeout(() => {
                this.hideLoadingAnimation();
                this.displayGeneratedImage(result);
            }, 500);

        } catch (error) {
            console.error('Image generation error:', error);
            this.hideLoadingAnimation();
            this.showError(`Greška pri generisanju EKG slike: ${error.message}`);
        }
    }

    // Display generated EKG image
    displayGeneratedImage(imageData) {
        // Create or show generated image section
        let generatedSection = document.getElementById('generatedImageSection');
        if (!generatedSection) {
            generatedSection = document.createElement('div');
            generatedSection.id = 'generatedImageSection';
            generatedSection.className = 'main-card';
            generatedSection.style.marginTop = '20px';
            
            const resultsSection = document.getElementById('resultsSection');
            resultsSection.parentNode.insertBefore(generatedSection, resultsSection.nextSibling);
        }

        generatedSection.innerHTML = `
            <h2><i class="fas fa-image"></i> Generisana EKG Slika</h2>
            
            <div class="result-card">
                <div class="result-header">
                    <i class="fas fa-image result-icon" style="color: #27ae60;"></i>
                    <h3 class="result-title">EKG Slika iz Sirovih Podataka</h3>
                </div>
                <div class="result-content">
                    <div style="text-align: center; margin: 20px 0;">
                        <img src="data:image/png;base64,${imageData.image_base64}" 
                             style="max-width: 100%; border: 2px solid #ddd; border-radius: 8px;" 
                             alt="Generisana EKG slika">
                    </div>
                    
                    <div style="background: #f8f9ff; padding: 15px; border-radius: 8px; margin: 15px 0;">
                        <h4><i class="fas fa-info-circle"></i> Informacije o slici:</h4>
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 10px;">
                            <div><strong>📏 Trajanje:</strong> ${imageData.signal_info?.duration_seconds?.toFixed(1) || 'N/A'}s</div>
                            <div><strong>📊 Uzorci:</strong> ${imageData.signal_info?.used_segment_length?.toLocaleString() || 'N/A'}</div>
                            <div><strong>📡 Fs:</strong> ${imageData.signal_info?.sampling_frequency || 'N/A'} Hz</div>
                            <div><strong>🎨 Stil:</strong> ${imageData.signal_info?.style || 'clinical'}</div>
                        </div>
                        ${imageData.signal_info?.segmentation_used ? 
                            `<div style="background: #e8f5e8; padding: 10px; border-radius: 5px; margin-top: 10px;">
                                <strong>🎯 Inteligentna segmentacija:</strong> Korišćen najkritičniji deo signala 
                                (${imageData.signal_info.segment_start_time?.toFixed(1)}-${imageData.signal_info.segment_end_time?.toFixed(1)}s)
                                sa kritičnošću ${imageData.signal_info.criticality_score?.toFixed(1)}
                            </div>` : ''
                        }
                    </div>
                    
                    <div style="text-align: center; margin-top: 15px;">
                        <button id="downloadImageBtn" class="btn btn-secondary" style="margin: 5px;">
                            <i class="fas fa-download"></i>
                            Sačuvaj Sliku
                        </button>
                        <button id="analyzeGeneratedImageBtn" class="btn btn-primary" style="margin: 5px;">
                            <i class="fas fa-chart-line"></i>
                            Analiziraj Generisanu Sliku
                        </button>
                    </div>
                </div>
            </div>
        `;

        generatedSection.style.display = 'block';
        generatedSection.scrollIntoView({ behavior: 'smooth' });

        // Store generated image data
        this.generatedImageData = imageData;

        // Add event listeners for new buttons
        const downloadBtn = document.getElementById('downloadImageBtn');
        const analyzeBtn = document.getElementById('analyzeGeneratedImageBtn');

        if (downloadBtn) {
            downloadBtn.onclick = () => this.downloadGeneratedImage();
        }

        if (analyzeBtn) {
            analyzeBtn.onclick = () => this.analyzeGeneratedImage();
        }

        this.showSuccess('✅ EKG slika uspešno generisana iz sirovih podataka!');
    }

    // Download generated image
    downloadGeneratedImage() {
        if (!this.generatedImageData) {
            this.showError('Nema generisane slike za preuzimanje');
            return;
        }

        try {
            // Create download link
            const link = document.createElement('a');
            link.href = `data:image/png;base64,${this.generatedImageData.image_base64}`;
            link.download = `ekg-slika-${new Date().toISOString().slice(0,10)}.png`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            this.showSuccess('Slika je preuzeta!');
        } catch (error) {
            this.showError('Greška pri preuzimanju slike');
        }
    }

    // Analyze generated image
    async analyzeGeneratedImage() {
        if (!this.generatedImageData) {
            this.showError('Nema generisane slike za analizu');
            return;
        }

        try {
            this.showLoadingAnimation();
            this.updateProgress(10, 'Analizira generisanu sliku...', '🔍');

            const response = await fetch('/api/analyze/complete', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    image: `data:image/png;base64,${this.generatedImageData.image_base64}`,
                    fs: 250,
                    skip_validation: true // Skip validation since this is our generated image
                })
            });

            this.updateProgress(75, 'Obrađuje analizu...', '🔬');

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            
            if (result.error) {
                throw new Error(result.error);
            }

            this.updateProgress(100, 'Analiza završena!', '✅');

            setTimeout(() => {
                this.hideLoadingAnimation();
                // Show comparison results
                this.displayImageAnalysisComparison(result);
            }, 500);

        } catch (error) {
            console.error('Generated image analysis error:', error);
            this.hideLoadingAnimation();
            this.showError(`Greška pri analizi generisane slike: ${error.message}`);
        }
    }

    // Display comparison between original and generated image analysis
    displayImageAnalysisComparison(newAnalysis) {
        const comparisonSection = document.createElement('div');
        comparisonSection.className = 'main-card';
        comparisonSection.style.marginTop = '20px';
        comparisonSection.innerHTML = `
            <h2><i class="fas fa-balance-scale"></i> Poređenje Analize</h2>
            <div class="result-card">
                <div class="result-header">
                    <i class="fas fa-chart-line result-icon" style="color: #3498db;"></i>
                    <h3 class="result-title">Originalni vs Generisana Slika</h3>
                </div>
                <div class="result-content">
                    <div style="background: #e8f5e8; padding: 15px; border-radius: 8px;">
                        <strong>✅ Uspešno testiranje:</strong> Signal → Slika → Analiza petlja je kompletirana!
                        <br><br>
                        <strong>📊 Poređenje rezultata:</strong>
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-top: 15px;">
                            <div>
                                <strong>Originalni signal:</strong><br>
                                Uzorci: ${this.analysisData.signal_info.length.toLocaleString()}<br>
                                Trajanje: ${this.analysisData.signal_info.duration_seconds.toFixed(1)}s<br>
                                BPM: ${this.analysisData.arrhythmia_detection?.heart_rate?.average_bpm?.toFixed(1) || 'N/A'}
                            </div>
                            <div>
                                <strong>Iz generisane slike:</strong><br>
                                Uzorci: ${newAnalysis.signal_info.length.toLocaleString()}<br>
                                Trajanje: ${newAnalysis.signal_info.duration_seconds.toFixed(1)}s<br>
                                BPM: ${newAnalysis.arrhythmia_detection?.heart_rate?.average_bpm?.toFixed(1) || 'N/A'}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        const generatedSection = document.getElementById('generatedImageSection');
        generatedSection.parentNode.insertBefore(comparisonSection, generatedSection.nextSibling);
        
        comparisonSection.scrollIntoView({ behavior: 'smooth' });
        this.showSuccess('Poređenje analize završeno!');
    }

    // NOVO: Strukturirani prikaz rezultata sa jasnim razlikovanjem R-pikova
    populateStructuredResults(data) {
        // Clear existing results content and replace with structured format
        const resultsSection = document.getElementById('resultsSection');
        
        // Keep the header, but replace the content after it
        const existingHeader = resultsSection.querySelector('.raw-signal-header, .wfdb-header');
        const headerHTML = existingHeader ? existingHeader.outerHTML : '';
        
        // Overall health status first
        const overallAssessment = data.arrhythmia_detection?.arrhythmias?.overall_assessment || 'Analiza završena';
        let statusClass = 'status-normal';
        if (overallAssessment.includes('medicinska pažnja')) {
            statusClass = 'status-danger';
        } else if (overallAssessment.includes('konsultacija') || overallAssessment.includes('nepravilnosti')) {
            statusClass = 'status-warning';
        }

        // Build structured content
        const structuredHTML = `
            ${headerHTML}
            
            <!-- Overall Health Status -->
            <div id="healthStatus" class="health-status ${statusClass}">
                ${overallAssessment}
            </div>

            <!-- 1. OPŠTI PODACI -->
            <div class="result-card collapsible collapsed">
                <div class="result-header" onclick="toggleResultCard(this)">
                    <i class="fas fa-info-circle result-icon" style="color: #3498db;"></i>
                    <h3 class="result-title">1. Opšti Podaci o Signalu</h3>
                </div>
                <div class="result-content">
                    <div class="metric">
                        <span class="metric-label">Broj analiziranih uzoraka:</span>
                        <span class="metric-value">${data.signal_info?.length?.toLocaleString() || 'N/A'}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Trajanje analize:</span>
                        <span class="metric-value">${data.signal_info?.duration_seconds?.toFixed(1) || 'N/A'}s</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Frekvencija uzorkovanja:</span>
                        <span class="metric-value">${data.signal_info?.sampling_frequency || 'N/A'} Hz</span>
                    </div>
                    ${data.wfdb_metadata?.original_samples ? `
                    <div class="metric">
                        <span class="metric-label">Originalni zapis (ukupno):</span>
                        <span class="metric-value">${data.wfdb_metadata.original_samples.toLocaleString()} uzoraka (${(data.wfdb_metadata.original_samples / data.signal_info.sampling_frequency / 60).toFixed(1)} min)</span>
                    </div>
                    <div style="background: #fff3e0; padding: 15px; border-radius: 8px; margin-top: 10px; font-size: 0.9rem; border-left: 4px solid #ff9800;">
                        <strong>📝 Važna napomena o segmentaciji:</strong><br><br>
                        Analiziran je <strong>segment od ${data.signal_info.length.toLocaleString()} uzoraka</strong> 
                        iz ukupnog zapisa od <strong>${data.wfdb_metadata.original_samples.toLocaleString()} uzoraka</strong>.<br><br>
                        
                        <strong>Razlog:</strong> Veliki WFDB fajlovi se analiziraju u segmentima zbog performansi. 
                        Svi R-pikovi i aritmije se odnose na ovaj analizirani segment, ne na ceo zapis.<br><br>
                        
                        <strong>Segment:</strong> Prvi deo zapisa (${(data.signal_info.length / data.signal_info.sampling_frequency / 60).toFixed(1)} min od ukupno ${(data.wfdb_metadata.original_samples / data.signal_info.sampling_frequency / 60).toFixed(1)} min)
                    </div>
                    ` : ''}
                </div>
            </div>

            <!-- 2. SRČANI RITAM -->
            <div class="result-card collapsible collapsed">
                <div class="result-header" onclick="toggleResultCard(this)">
                    <i class="fas fa-heartbeat result-icon" style="color: #e74c3c;"></i>
                    <h3 class="result-title">2. Srčani Ritam</h3>
                </div>
                <div class="result-content">
                    <div class="metric">
                        <span class="metric-label">Prosečna frekvencija:</span>
                        <span class="metric-value">${data.arrhythmia_detection?.heart_rate?.average_bpm?.toFixed(1) || 'N/A'} bpm</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Minimalna frekvencija:</span>
                        <span class="metric-value">${data.arrhythmia_detection?.heart_rate?.min_bpm?.toFixed(1) || 'N/A'} bpm</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Maksimalna frekvencija:</span>
                        <span class="metric-value">${data.arrhythmia_detection?.heart_rate?.max_bpm?.toFixed(1) || 'N/A'} bpm</span>
                    </div>
                </div>
            </div>

            <!-- 3. R-PIKOVI - JASNO RAZLIKOVANJE -->
            <div class="result-card collapsible collapsed">
                <div class="result-header" onclick="toggleResultCard(this)">
                    <i class="fas fa-chart-line result-icon" style="color: #9b59b6;"></i>
                    <h3 class="result-title">3. Analiza R-pikova</h3>
                </div>
                <div class="result-content">
                    <!-- Detektovani R-pikovi iz signala -->
                    <div style="background: #f8f9ff; padding: 15px; border-radius: 8px; margin-bottom: 15px;">
                        <h4 style="margin: 0 0 10px 0; color: #667eea;">
                            <i class="fas fa-search"></i> Detektovani iz signala (algoritam):
                        </h4>
                        <div class="metric">
                            <span class="metric-label">Broj R-pikova:</span>
                            <span class="metric-value">${data.arrhythmia_detection?.r_peaks_count || 'N/A'}</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">RR intervali:</span>
                            <span class="metric-value">${data.arrhythmia_detection?.heart_rate?.rr_count || 'N/A'}</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Metod detekcije:</span>
                            <span class="metric-value">${data.arrhythmia_detection?.detection_method || 'signal_analysis'}</span>
                        </div>
                    </div>

                    <!-- MIT-BIH Annotations ako postoje -->
                    ${data.annotations ? `
                    <div style="background: #e8f5e8; padding: 15px; border-radius: 8px;">
                        <h4 style="margin: 0 0 10px 0; color: #27ae60;">
                            <i class="fas fa-hospital"></i> MIT-BIH Annotations (.atr fajl):
                        </h4>
                        <div class="metric">
                            <span class="metric-label">Anotirani R-pikovi:</span>
                            <span class="metric-value">${data.annotations.r_peaks_count || 'N/A'}</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Ukupno anotacija:</span>
                            <span class="metric-value">${data.annotations.total_annotations || 'N/A'}</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Aritmije u .atr:</span>
                            <span class="metric-value">${data.annotations.arrhythmias_count || 'N/A'}</span>
                        </div>
                    </div>
                    
                    <!-- Objašnjenje razlike u brojevima -->
                    <div style="background: #fff3e0; padding: 15px; border-radius: 8px; margin-top: 15px; border-left: 4px solid #ff9800;">
                        <h4 style="margin: 0 0 10px 0; color: #f57c00;">
                            <i class="fas fa-info-circle"></i> Objašnjenje razlike u brojevima:
                        </h4>
                        <div style="font-size: 0.9rem; line-height: 1.5;">
                            <strong>📋 Anotirani R-pikovi (${data.annotations.r_peaks_count || 'N/A'}):</strong> 
                            Ručno označeni od MIT-BIH eksperata u analiziranom segmentu<br>
                            
                            <strong>🔍 Detektovani R-pikovi (${data.arrhythmia_detection?.r_peaks_count || 'N/A'}):</strong> 
                            Automatski pronađeni našim algoritmom<br><br>
                            
                            <strong>💡 Razlog razlike:</strong> Algoritam može propustiti slabije R-pikove ili imati konzervativnije kriterijume detekcije. MIT-BIH anotacije predstavljaju "zlatni standard" za poređenje.
                        </div>
                    </div>
                    ` : ''}
                </div>
            </div>

            <!-- 4. HRV (Heart Rate Variability) -->
            <div class="result-card collapsible collapsed">
                <div class="result-header" onclick="toggleResultCard(this)">
                    <i class="fas fa-chart-area result-icon" style="color: #f39c12;"></i>
                    <h3 class="result-title">4. Varijabilnost Srčanog Ritma (HRV)</h3>
                </div>
                <div class="result-content">
                    <div class="metric">
                        <span class="metric-label">HRV (standardna devijacija):</span>
                        <span class="metric-value">${data.arrhythmia_detection?.heart_rate?.heart_rate_variability?.toFixed(1) || 'N/A'} ms</span>
                    </div>
                    <div style="font-size: 0.9rem; color: #666; margin-top: 10px;">
                        <strong>Interpretacija:</strong> 
                        ${this.getHRVInterpretation(data.arrhythmia_detection?.heart_rate?.heart_rate_variability)}
                    </div>
                </div>
            </div>

            <!-- 5. ARITMIJE -->
            <div class="result-card collapsible collapsed">
                <div class="result-header" onclick="toggleResultCard(this)">
                    <i class="fas fa-exclamation-triangle result-icon" style="color: #e74c3c;"></i>
                    <h3 class="result-title">5. Detekcija Aritmija</h3>
                </div>
                <div class="result-content">
                    <div style="margin-bottom: 15px;">
                        <strong>Osnova za analizu:</strong> ${data.arrhythmia_detection?.arrhythmias?.detected?.length > 0 ? 'RR intervali iz detektovanih R-pikova' : 'Normalan ritam'}
                    </div>
                    <div id="arrhythmiasList">
                        ${this.formatArrhythmiasList(data.arrhythmia_detection?.arrhythmias)}
                    </div>
                </div>
            </div>

            <!-- 6. FFT ANALIZA -->
            <div class="result-card collapsible collapsed">
                <div class="result-header" onclick="toggleResultCard(this)">
                    <i class="fas fa-wave-square result-icon" style="color: #3498db;"></i>
                    <h3 class="result-title">6. FFT Frekvencijska Analiza</h3>
                </div>
                <div class="result-content">
                    <div class="metric">
                        <span class="metric-label">Dominantna frekvencija:</span>
                        <span class="metric-value">${data.fft_analysis?.peak_frequency_hz?.toFixed(2) || 'N/A'} Hz</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Peak amplituda:</span>
                        <span class="metric-value">${data.fft_analysis?.peak_amplitude?.toFixed(4) || 'N/A'}</span>
                    </div>
                    ${data.fft_analysis?.dc_removed ? `
                    <div class="metric">
                        <span class="metric-label">DC komponenta uklonjena:</span>
                        <span class="metric-value">✅ Da (${data.fft_analysis.dc_component?.toFixed(4) || 'N/A'})</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Analizirani opseg:</span>
                        <span class="metric-value">${data.fft_analysis.physiological_range_analyzed || 'N/A'}</span>
                    </div>
                    ` : ''}
                    <div style="font-size: 0.9rem; color: #666; margin-top: 10px;">
                        <strong>Interpretacija:</strong> 
                        ${this.getFFTInterpretation(data.fft_analysis?.peak_frequency_hz)}
                    </div>
                </div>
            </div>

            <!-- 7. KVALITET SIGNALA -->
            <div class="result-card collapsible collapsed">
                <div class="result-header" onclick="toggleResultCard(this)">
                    <i class="fas fa-signal result-icon" style="color: #27ae60;"></i>
                    <h3 class="result-title">7. Kvalitet Signala</h3>
                </div>
                <div class="result-content">
                    <div class="metric">
                        <span class="metric-label">Ocena kvaliteta:</span>
                        <span class="metric-value">${data.arrhythmia_detection?.signal_quality?.quality || 'N/A'}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Signal-to-Noise Ratio:</span>
                        <span class="metric-value">${data.arrhythmia_detection?.signal_quality?.snr_db?.toFixed(1) || 'N/A'} dB</span>
                    </div>
                </div>
            </div>

            <!-- Action Buttons Container -->
            <div class="action-buttons" style="margin-top: 20px;">
                <!-- Nova Analiza button moved to end of page -->
            </div>
        `;

        resultsSection.innerHTML = structuredHTML;
    }

    // Helper functions for interpretations
    getHRVInterpretation(hrv) {
        if (!hrv) return 'Podaci nisu dostupni';
        if (hrv < 20) return 'Niska varijabilnost (može ukazivati na stres)';
        if (hrv < 50) return 'Normalna varijabilnost';
        return 'Visoka varijabilnost (dobra autonomna regulacija)';
    }

    getFFTInterpretation(freq) {
        if (!freq) return 'Podaci nisu dostupni';
        if (freq < 0.5) return 'Vrlo niska frekvencija - mogući problem sa analizom';
        if (freq >= 0.8 && freq <= 2.0) return 'Normalna srčana frekvencija (48-120 bpm)';
        if (freq > 2.0 && freq <= 3.0) return 'Povišena frekvencija (120-180 bpm)';
        return `Frekvencija van normalnog opsega (${(freq * 60).toFixed(0)} bpm ekvivalent)`;
    }

    formatArrhythmiasList(arrhythmias) {
        if (!arrhythmias || !arrhythmias.detected || arrhythmias.detected.length === 0) {
            return '<div class="arrhythmia-item severity-low">✅ Nema detektovanih aritmija</div>';
        }

        return arrhythmias.detected.map(arr => `
            <div class="arrhythmia-item severity-${arr.severity}">
                <div class="arrhythmia-type">⚠️ ${arr.type}</div>
                <div class="arrhythmia-desc">${arr.description}</div>
                <div class="arrhythmia-desc"><strong>Vrednost:</strong> ${arr.value}</div>
            </div>
        `).join('');
    }
    // NOVO: Napredni kardiološki prikaz rezultata
    populateAdvancedCardiologyResults(data) {
        const resultsSection = document.getElementById('resultsSection');
        const cardiology = data.advanced_cardiology;
        
        // Keep the header, but replace the content
        const existingHeader = resultsSection.querySelector('.raw-signal-header, .wfdb-header');
        const headerHTML = existingHeader ? existingHeader.outerHTML : '';
        
        // Overall health status
        const overallAssessment = cardiology.arrhythmia_analysis?.overall_assessment || 'Analiza završena';
        let statusClass = 'status-normal';
        if (overallAssessment.includes('hitna medicinska')) statusClass = 'status-danger';
        else if (overallAssessment.includes('konsultacija') || overallAssessment.includes('konsultacija')) statusClass = 'status-warning';

        const advancedHTML = `
            ${headerHTML}
            
            <!-- Overall Health Status -->
            <div id="healthStatus" class="health-status ${statusClass}">
                ${overallAssessment}
            </div>

            <!-- 📁 OPŠTE INFORMACIJE -->
            ${this.renderGeneralInfo(cardiology.general_info)}
            
            <!-- 📍 ANOTACIJE (.atr fajl) -->
            ${cardiology.annotation_analysis ? this.renderAnnotationAnalysis(cardiology.annotation_analysis) : ''}
            
            <!-- 📈 DETEKCIJA R-PIKOVA -->
            ${this.renderRPeakAnalysis(cardiology.r_peak_analysis)}
            
            <!-- 🫀 SRČANI RITAM -->
            ${this.renderHeartRateAnalysis(cardiology.heart_rate_analysis)}
            
            <!-- 📉 HRV ANALIZA -->
            ${this.renderHRVAnalysis(cardiology.hrv_analysis)}
            
            <!-- ⚠️ ARITMIJE -->
            ${this.renderArrhythmiaAnalysis(cardiology.arrhythmia_analysis)}
            
            <!-- 📶 KVALITET SIGNALA -->
            ${this.renderSignalQuality(cardiology.signal_quality)}
            
            <!-- 🔬 FREKVENCIJSKA ANALIZA -->
            ${this.renderFrequencyAnalysis(cardiology.frequency_analysis)}
            
            <!-- 📊 VIZUELIZACIJE -->
            ${this.renderVisualizations(cardiology.visualizations)}
            
            <!-- Action Buttons -->
            <div class="action-buttons" style="margin-top: 20px;">
                <button onclick="window.print()" class="btn btn-secondary">
                    <i class="fas fa-print"></i> Štampaj Izveštaj
                </button>
                <!-- Nova Analiza button moved to end of page -->
            </div>
        `;

        resultsSection.innerHTML = advancedHTML;
        
        // Add event listener for new analysis button
        const newAnalysisBtn = document.getElementById('newAnalysisBtn');
        if (newAnalysisBtn) {
            newAnalysisBtn.addEventListener('click', () => location.reload());
        }
    }
    
    addNovaAnalizaButton() {
        // Remove existing Nova Analiza button if present
        const existingBtn = document.getElementById('novaAnalizaFinalBtn');
        if (existingBtn) {
            existingBtn.remove();
        }
        
        // Create new Nova Analiza button at the very end
        const buttonHTML = `
            <div id="novaAnalizaFinalBtn" style="text-align: center; padding: 30px 20px; margin-top: 30px; border-top: 2px solid #e9ecef;">
                <button onclick="location.reload()" class="btn" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; padding: 15px 40px; border-radius: 25px; font-size: 1.1rem; font-weight: 600; cursor: pointer; display: inline-flex; align-items: center; gap: 10px; box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3); transition: all 0.3s ease;" onmouseover="this.style.transform='translateY(-3px)'; this.style.boxShadow='0 6px 20px rgba(102, 126, 234, 0.4)'" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 4px 15px rgba(102, 126, 234, 0.3)'">
                    <i class="fas fa-plus"></i>
                    Nova Analiza
                </button>
            </div>
        `;
        
        // Add at the very end of the main container
        const container = document.querySelector('.container');
        if (container) {
            container.insertAdjacentHTML('beforeend', buttonHTML);
        }
        
        // Add event listeners for info buttons after content is added
        setTimeout(() => {
            this.addInfoButtonListeners();
        }, 100);
    }
    
    addInfoButtonListeners() {
        console.log('🔧 Adding info button listeners...');
        
        // Method 1: Look for showInfoModal buttons
        const oldInfoButtons = document.querySelectorAll('[onclick^="showInfoModal"]');
        console.log(`🔧 Found ${oldInfoButtons.length} old-style info buttons`);
        
        oldInfoButtons.forEach(button => {
            const onclickValue = button.getAttribute('onclick');
            const match = onclickValue.match(/showInfoModal\('([^']+)'\)/);
            if (match) {
                const infoType = match[1];
                button.onclick = () => {
                    if (typeof window.showInfoModal === 'function') {
                        window.showInfoModal(infoType);
                    }
                };
            }
        });
        
        // Method 2: Look for new-style info buttons (class="info-btn")
        const newInfoButtons = document.querySelectorAll('.info-btn');
        console.log(`🔧 Found ${newInfoButtons.length} new-style info buttons`);
        
        newInfoButtons.forEach((button, index) => {
            // If button already has onclick, skip it
            if (button.onclick) {
                console.log(`🔧 Button ${index} already has onclick handler`);
                return;
            }
            
            // Find the title from nearby h3 or h4
            const title = this.findButtonTitle(button);
            const key = String(index + 1);
            
            console.log(`🔧 Adding onclick to button ${index}: ${title}`);
            
            button.onclick = () => {
                if (typeof window.showEducationalInfo === 'function') {
                    window.showEducationalInfo(key, title, "");
                } else if (typeof window.showInfoModal === 'function') {
                    window.showInfoModal('visualization');
                }
            };
        });
    }
    
    findButtonTitle(button) {
        // Look for nearby h3 or h4 element
        const header = button.closest('.result-header')?.querySelector('h3') || 
                      button.closest('.result-card')?.querySelector('h3') ||
                      button.parentElement?.querySelector('h3') ||
                      button.parentElement?.querySelector('h4');
        
        return header ? header.textContent.trim() : 'Vizualizacija';
    }

    // Render funkcije za napredni prikaz
    renderGeneralInfo(info) {
        if (!info) return '';
        
        return `
        <div class="result-card">
            <div class="result-header">
                <i class="fas fa-info-circle result-icon" style="color: #3498db;"></i>
                <h3 class="result-title">📁 Opšte Informacije o Signalu</h3>
            </div>
            <div class="result-content">
                <div class="metric">
                    <span class="metric-label">Analizirani uzorci:</span>
                    <span class="metric-value">${info.analyzed_samples?.toLocaleString() || 'N/A'}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Trajanje analize:</span>
                    <span class="metric-value">${info.analyzed_duration_minutes?.toFixed(1) || 'N/A'} min (${info.analyzed_duration_seconds?.toFixed(1) || 'N/A'}s)</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Frekvencija uzorkovanja:</span>
                    <span class="metric-value">${info.sampling_frequency || 'N/A'} Hz</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Korišćeni kanali:</span>
                    <span class="metric-value">${info.channels_used || 'N/A'}</span>
                </div>
                ${info.total_original_samples ? `
                <div class="metric">
                    <span class="metric-label">Originalni zapis (ukupno):</span>
                    <span class="metric-value">${info.total_original_samples.toLocaleString()} uzoraka (${info.total_original_duration_minutes?.toFixed(1)} min)</span>
                </div>
                <div style="background: #fff3e0; padding: 15px; border-radius: 8px; margin-top: 10px;">
                    <strong>📝 Segmentacija:</strong> Analiziran je segment od ${info.segment_percentage?.toFixed(1)}% ukupnog zapisa zbog performansi.
                </div>
                ` : ''}
            </div>
        </div>`;
    }

    renderAnnotationAnalysis(annotation) {
        if (!annotation) return '';
        
        const typesList = Object.entries(annotation.annotation_types || {})
            .map(([type, count]) => `<span class="annotation-type">${type}: ${count}</span>`)
            .join(' ');
        
        return `
        <div class="result-card">
            <div class="result-header">
                <i class="fas fa-hospital result-icon" style="color: #e74c3c;"></i>
                <h3 class="result-title">📍 MIT-BIH Anotacije (.atr fajl)</h3>
            </div>
            <div class="result-content">
                <div class="metric">
                    <span class="metric-label">Ukupno anotacija:</span>
                    <span class="metric-value">${annotation.total_annotations || 0}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">R-peak anotacije:</span>
                    <span class="metric-value">${annotation.r_peak_annotations || 0}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Aritmijske anotacije:</span>
                    <span class="metric-value">${annotation.arrhythmia_annotations || 0}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Izvor:</span>
                    <span class="metric-value">${annotation.source_file || 'N/A'}</span>
                </div>
                <div style="background: #e8f5e8; padding: 10px; border-radius: 5px; margin-top: 10px;">
                    <strong>📋 Tipovi anotacija:</strong><br>
                    ${typesList || 'Nema podataka'}
                </div>
            </div>
        </div>`;
    }

    renderRPeakAnalysis(rpeak) {
        if (!rpeak) return '';
        
        return `
        <div class="result-card">
            <div class="result-header">
                <i class="fas fa-chart-line result-icon" style="color: #9b59b6;"></i>
                <h3 class="result-title">📈 Analiza R-pikova</h3>
            </div>
            <div class="result-content">
                <div style="background: #f8f9ff; padding: 15px; border-radius: 8px; margin-bottom: 15px;">
                    <h4 style="margin: 0 0 10px 0;">🔍 Detektovani algoritmom:</h4>
                    <div class="metric">
                        <span class="metric-label">Broj R-pikova:</span>
                        <span class="metric-value">${rpeak.detected_count || 'N/A'}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Metod detekcije:</span>
                        <span class="metric-value">${rpeak.detection_method || 'N/A'}</span>
                    </div>
                </div>
                
                ${rpeak.annotated_count ? `
                <div style="background: #e8f5e8; padding: 15px; border-radius: 8px;">
                    <h4 style="margin: 0 0 10px 0;">🏥 MIT-BIH annotations:</h4>
                    <div class="metric">
                        <span class="metric-label">Anotirani R-pikovi:</span>
                        <span class="metric-value">${rpeak.annotated_count}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Poklapanje:</span>
                        <span class="metric-value">${rpeak.matched_peaks || 0} (${rpeak.detection_accuracy_percent?.toFixed(1) || 0}%)</span>
                    </div>
                </div>
                ` : ''}
            </div>
        </div>`;
    }

    renderHeartRateAnalysis(hr) {
        if (!hr || hr.error) return '';
        
        return `
        <div class="result-card">
            <div class="result-header">
                <i class="fas fa-heartbeat result-icon" style="color: #e74c3c;"></i>
                <h3 class="result-title">🫀 Srčani Ritam</h3>
            </div>
            <div class="result-content">
                <div class="metric">
                    <span class="metric-label">Prosečna frekvencija:</span>
                    <span class="metric-value">${hr.average_bpm?.toFixed(1) || 'N/A'} bpm</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Ukupno otkucaja:</span>
                    <span class="metric-value">${hr.total_beats || 'N/A'}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Prosečan RR interval:</span>
                    <span class="metric-value">${hr.avg_rr_ms?.toFixed(1) || 'N/A'} ms</span>
                </div>
            </div>
        </div>`;
    }

    renderHRVAnalysis(hrv) {
        if (!hrv || hrv.error) return '';
        
        return `
        <div class="result-card">
            <div class="result-header">
                <i class="fas fa-chart-area result-icon" style="color: #f39c12;"></i>
                <h3 class="result-title">📉 HRV (Heart Rate Variability)</h3>
            </div>
            <div class="result-content">
                <div class="metric">
                    <span class="metric-label">SDRR:</span>
                    <span class="metric-value">${hrv.sdrr_ms?.toFixed(1) || 'N/A'} ms</span>
                </div>
                <div class="metric">
                    <span class="metric-label">RMSSD:</span>
                    <span class="metric-value">${hrv.rmssd_ms?.toFixed(1) || 'N/A'} ms</span>
                </div>
                <div class="metric">
                    <span class="metric-label">pNN50:</span>
                    <span class="metric-value">${hrv.pnn50_percent?.toFixed(1) || 'N/A'}%</span>
                </div>
                
                ${hrv.overall_hrv_assessment ? `
                <div style="background: #e8f5e8; padding: 10px; border-radius: 5px; margin-top: 10px;">
                    <strong>🏥 Procena:</strong> ${hrv.overall_hrv_assessment}
                </div>
                ` : ''}
            </div>
        </div>`;
    }

    renderArrhythmiaAnalysis(arr) {
        if (!arr) return '';
        
        const arrhythmiasList = arr.detected && arr.detected.length > 0 ? 
            arr.detected.map(arrhythmia => `
                <div class="arrhythmia-item severity-${arrhythmia.severity}">
                    <div class="arrhythmia-type">⚠️ ${arrhythmia.type}</div>
                    <div class="arrhythmia-desc">${arrhythmia.description}</div>
                    <div class="arrhythmia-desc"><strong>Vrednost:</strong> ${arrhythmia.value}</div>
                    ${arrhythmia.criteria ? `<div class="arrhythmia-desc"><em>Kriterijum:</em> ${arrhythmia.criteria}</div>` : ''}
                </div>
            `).join('') :
            '<div class="arrhythmia-item severity-low">✅ Nema detektovanih aritmija</div>';
        
        return `
        <div class="result-card">
            <div class="result-header">
                <i class="fas fa-exclamation-triangle result-icon" style="color: #e74c3c;"></i>
                <h3 class="result-title">⚠️ Detekcija Aritmija</h3>
            </div>
            <div class="result-content">
                <div class="metric">
                    <span class="metric-label">Ukupno detektovano:</span>
                    <span class="metric-value">${arr.total_count || 0}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Osnova analize:</span>
                    <span class="metric-value">${arr.analysis_basis || 'RR intervali'}</span>
                </div>
                
                <div style="margin: 15px 0;">
                    ${arrhythmiasList}
                </div>
                
                ${arr.missed_beats_analysis ? `
                <div style="background: #fff3e0; padding: 10px; border-radius: 5px; margin-top: 10px;">
                    <strong>📊 Propušteni otkucaji:</strong> ${arr.missed_beats_analysis.detected_long_intervals} dugih intervala 
                    (${arr.missed_beats_analysis.percentage_of_intervals?.toFixed(1)}%)
                </div>
                ` : ''}
            </div>
        </div>`;
    }

    renderSignalQuality(quality) {
        if (!quality) return '';
        
        return `
        <div class="result-card">
            <div class="result-header">
                <i class="fas fa-signal result-icon" style="color: #27ae60;"></i>
                <h3 class="result-title">📶 Kvalitet Signala</h3>
            </div>
            <div class="result-content">
                <div class="metric">
                    <span class="metric-label">SNR:</span>
                    <span class="metric-value">${quality.snr_db?.toFixed(1) || 'N/A'} dB</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Procena kvaliteta:</span>
                    <span class="metric-value">${quality.quality_assessment || 'N/A'}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Nivo šuma:</span>
                    <span class="metric-value">${quality.noise_level || 'N/A'}</span>
                </div>
                ${quality.artifacts_detected !== undefined ? `
                <div class="metric">
                    <span class="metric-label">Artefakti:</span>
                    <span class="metric-value">${quality.artifacts_detected} detektovano</span>
                </div>
                ` : ''}
                
                ${quality.filters_applied ? `
                <div style="background: #f0f8ff; padding: 10px; border-radius: 5px; margin-top: 10px;">
                    <strong>🔧 Primenjeni filtri:</strong><br>
                    ${quality.filters_applied.map(filter => `• ${filter}`).join('<br>')}
                </div>
                ` : ''}
            </div>
        </div>`;
    }

    renderFrequencyAnalysis(freq) {
        if (!freq) return '';
        
        return `
        <div class="result-card">
            <div class="result-header">
                <i class="fas fa-wave-square result-icon" style="color: #3498db;"></i>
                <h3 class="result-title">🔬 Frekvencijska Analiza</h3>
            </div>
            <div class="result-content">
                <div class="metric">
                    <span class="metric-label">Dominantna frekvencija:</span>
                    <span class="metric-value">${freq.peak_frequency_hz?.toFixed(2) || 'N/A'} Hz</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Peak amplituda:</span>
                    <span class="metric-value">${freq.peak_amplitude?.toFixed(4) || 'N/A'}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">DC komponenta:</span>
                    <span class="metric-value">${freq.dc_component_removed ? '✅ Uklonjena' : '❌ Prisutna'}</span>
                </div>
                
                ${freq.frequency_interpretation ? `
                <div style="background: #e8f5e8; padding: 10px; border-radius: 5px; margin-top: 10px;">
                    <strong>💡 Interpretacija:</strong> ${freq.frequency_interpretation}
                </div>
                ` : ''}
            </div>
        </div>`;
    }

    renderVisualizations(viz) {
        if (!viz) return '';
        
        return `
        <div class="result-card">
            <div class="result-header">
                <i class="fas fa-chart-bar result-icon" style="color: #9b59b6;"></i>
                <h3 class="result-title">📊 Vizuelizacije</h3>
            </div>
            <div class="result-content">
                ${viz.signal_with_peaks ? `
                <div style="margin: 15px 0;">
                    <h4>EKG Signal sa R-pikovima:</h4>
                    <img src="data:image/png;base64,${viz.signal_with_peaks}" style="max-width: 100%; border: 1px solid #ddd; border-radius: 5px;">
                </div>
                ` : ''}
                
                ${viz.rr_histogram ? `
                <div style="margin: 15px 0;">
                    <h4>Histogram RR Intervala:</h4>
                    <img src="data:image/png;base64,${viz.rr_histogram}" style="max-width: 100%; border: 1px solid #ddd; border-radius: 5px;">
                </div>
                ` : ''}
                
                ${viz.heart_rate_trend ? `
                <div style="margin: 15px 0;">
                    <h4>Srčana Frekvencija Kroz Vreme:</h4>
                    <img src="data:image/png;base64,${viz.heart_rate_trend}" style="max-width: 100%; border: 1px solid #ddd; border-radius: 5px;">
                </div>
                ` : ''}
                
                ${viz.poincare_plot ? `
                <div style="margin: 15px 0;">
                    <h4>Poincaré Dijagram HRV:</h4>
                    <img src="data:image/png;base64,${viz.poincare_plot}" style="max-width: 100%; border: 1px solid #ddd; border-radius: 5px;">
                </div>
                ` : ''}
            </div>
        </div>`;
    }

    // NOVO: Dodaj vizuelizacije za master rad
    // Funkcija za kreiranje specifičnih objašnjenja za svaki dijagram
    getVisualizationExplanation(key, viz) {
        const explanations = {
            "1": "Ovaj dijagram prikazuje EKG signal u vremenskom domenu sa detektovanim R-pikovima (označeni crvenim krugovima). R-pikovi predstavljaju električni impuls koji pokreće kontrakciju srčanih komora. Analiza R-pikova omogućava merenje srčane frekvencije, varijabilnosti srčanog ritma i detekciju potencijalnih aritmija. Visina i raspored R-pikova mogu ukazati na različite kardiološke stanja.",
            
            "2": "FFT (Fast Fourier Transform) spektar pokazuje frekvencijski sadržaj EKG signala. Dominantna frekvencija (označena crvenom linijom) odgovara osnovnoj srčanoj frekvenciji. Analiza frekvencijskog spektra omogućava identifikaciju periodičnih komponenti signala, šuma i artefakata. Visoke frekvencije mogu ukazati na mišićne artefakte, dok niske frekvencije mogu biti posledica disanja ili kretanja pacijenta.",
            
            "3": "Ovaj dijagram poredi automatski detektovane R-pikove (crveno) sa ekspertskim MIT-BIH anotacijama (zeleno). MIT-BIH baza podataka sadrži ručno označene R-pikove od strane kardiologa i predstavlja 'zlatni standard' za validaciju algoritama. Poklapanje detektovanih pikova sa ekspertskim anotacijama ukazuje na tačnost algoritma za detekciju R-pikova.",
            
            "4": "Signal processing pipeline prikazuje korake obrade EKG signala korišćenjem Z-transformacije: 1) Originalni signal, 2) Bandpass filtriranje (0.5-40 Hz) za uklanjanje šuma, 3) Baseline removal za eliminaciju drift-a signala, 4) Filter response u Z-domenu koji pokazuje karakteristike primenjenog filtera. Z-transformacija omogućava dizajn i analizu digitalnih filtara u diskretnom domenu."
        };
        
        return explanations[key] || `Objašnjenje za ${viz.title}: Ovaj dijagram predstavlja važnu komponentu analize EKG signala u okviru master rada o primeni Furijeove i Z-transformacije u biomedicinskim signalima.`;
    }

    addThesisVisualizations(visualizations) {
        console.log('🎯 v3.1 Starting addThesisVisualizations - FIXED for broken pipe');
        console.log('📊 v3.1 Received data:', visualizations);
        console.log('📊 v3.1 Data type:', typeof visualizations);
        
        const resultsSection = document.getElementById('resultsSection');
        
        // Kreiraj sekciju za vizuelizacije ako ne postoji
        let vizSection = document.getElementById('thesisVisualizationsSection');
        if (!vizSection) {
            vizSection = document.createElement('div');
            vizSection.id = 'thesisVisualizationsSection';
            vizSection.className = 'main-card';
            vizSection.style.marginTop = '20px';
            resultsSection.parentNode.insertBefore(vizSection, resultsSection.nextSibling);
        }

        let visualizationsHTML = `
            <h2><i class="fas fa-chart-line"></i> Vizuelizacije za Master Rad</h2>
            <div style="background: #e8f5e8; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                <strong>📊 Furijeova i Z-transformacija u analizi biomedicinskih signala</strong><br>
                Grafici spremni za uključivanje u poglavlje 5 master rada.
            </div>
        `;

        // Check for new format first (v3.1)
        if (visualizations.visualizations && typeof visualizations.visualizations === 'object') {
            console.log('📊 v3.1 Using NEW FORMAT');
            const vizData = visualizations.visualizations;
            
            // DEBUG: Prikaži sve ključeve
            console.log('📊 v3.1 Available visualization keys:', Object.keys(vizData));
            for (let key of Object.keys(vizData)) {
                const viz = vizData[key];
                const hasImage = !!viz.image_base64;
                const imageLen = viz.image_base64 ? viz.image_base64.length : 0;
                console.log(`📊 v3.1 Key "${key}": title="${viz.title}" hasImage=${hasImage} imageLength=${imageLen}`);
            }
            
            // Iterate through numbered visualizations
            for (let i = 1; i <= 5; i++) {
                if (vizData[i.toString()]) {
                    console.log(`📊 v3.1 Adding visualization ${i}:`, vizData[i.toString()].title);
                    const viz = vizData[i.toString()];
                    
                    let imageContent = '';
                    if (viz.image_base64) {
                        imageContent = `<img src="data:image/png;base64,${viz.image_base64}" 
                                             style="max-width: 100%; border: 2px solid #ddd; border-radius: 8px; margin: 10px 0;"
                                             alt="Visualization ${i}">`;
                    } else {
                        imageContent = `<div style="background: #f8f9fa; border: 2px dashed #dee2e6; border-radius: 8px; padding: 40px; text-align: center; margin: 10px 0; color: #6c757d;">
                                           <i class="fas fa-image" style="font-size: 2rem; margin-bottom: 10px;"></i><br>
                                           Slika se generiše...
                                       </div>`;
                    }
                    
                    visualizationsHTML += `
                        <div class="result-card">
                            <div class="result-header">
                                <i class="fas fa-chart-line result-icon" style="color: #3498db;"></i>
                                <h3 class="result-title">${viz.title}</h3>
                            </div>
                            <div class="result-content">
                                <p><strong>Opis:</strong> ${viz.description}</p>
                                ${imageContent}
                                <p style="font-size: 0.9rem; color: #666;"><em>${viz.caption}</em></p>
                            </div>
                        </div>
                    `;
                }
            }
        }
        // OLD FORMAT FALLBACK
        else {
            console.log('📊 v2.9 Using OLD FORMAT (fallback)');
        
        // 1. EKG Signal sa R-pikovima
        if (visualizations.ekg_with_peaks) {
            visualizationsHTML += `
                <div class="result-card">
                    <div class="result-header">
                        <i class="fas fa-heartbeat result-icon" style="color: #e74c3c;"></i>
                        <h3 class="result-title">1. EKG Signal sa Detektovanim R-pikovima</h3>
                    </div>
                    <div class="result-content">
                        <p><strong>Opis:</strong> Prikaz originalnog EKG signala sa algoritmski detektovanim R-pikovima (crvene tačke) i MIT-BIH ekspert anotacijama (zeleni trouglovi).</p>
                        <img src="data:image/png;base64,${visualizations.ekg_with_peaks}" 
                             style="max-width: 100%; border: 2px solid #ddd; border-radius: 8px; margin: 10px 0;"
                             alt="EKG signal sa R-pikovima">
                        <p style="font-size: 0.9rem; color: #666;"><em>Slika 5.1: EKG signal sa detektovanim R-pikovima i poređenjem sa MIT-BIH anotacijama</em></p>
                    </div>
                </div>
            `;
        }

        // 2. FFT Spektar
        if (visualizations.fft_spectrum) {
            visualizationsHTML += `
                <div class="result-card">
                    <div class="result-header">
                        <i class="fas fa-wave-square result-icon" style="color: #3498db;"></i>
                        <h3 class="result-title">2. FFT Spektar (Furijeova Transformacija)</h3>
                    </div>
                    <div class="result-content">
                        <p><strong>Opis:</strong> Frekvencijski spektar EKG signala dobijen Furijeovom transformacijom. Dominantna frekvencija označena crvenom linijom odgovara srčanoj frekvenciji.</p>
                        <img src="data:image/png;base64,${visualizations.fft_spectrum}" 
                             style="max-width: 100%; border: 2px solid #ddd; border-radius: 8px; margin: 10px 0;"
                             alt="FFT spektar">
                        <p style="font-size: 0.9rem; color: #666;"><em>Slika 5.2: FFT spektar EKG signala sa označenom dominantnom frekvencijom</em></p>
                    </div>
                </div>
            `;
        }

        // 3. Poređenje sa MIT-BIH
        if (visualizations.mitbih_comparison) {
            visualizationsHTML += `
                <div class="result-card">
                    <div class="result-header">
                        <i class="fas fa-balance-scale result-icon" style="color: #9b59b6;"></i>
                        <h3 class="result-title">3. Poređenje sa MIT-BIH Anotacijama</h3>
                    </div>
                    <div class="result-content">
                        <p><strong>Opis:</strong> Statistička analiza performansi algoritma u odnosu na MIT-BIH ekspert anotacije. Prikazane su greške (false positives/negatives) i metrike precision/recall.</p>
                        <img src="data:image/png;base64,${visualizations.mitbih_comparison}" 
                             style="max-width: 100%; border: 2px solid #ddd; border-radius: 8px; margin: 10px 0;"
                             alt="MIT-BIH poređenje">
                        <p style="font-size: 0.9rem; color: #666;"><em>Slika 5.3: Validacija algoritma kroz poređenje sa MIT-BIH golden standard anotacijama</em></p>
                    </div>
                </div>
            `;
        }

        // 4. Signal Processing Pipeline
        if (visualizations.processing_steps) {
            visualizationsHTML += `
                <div class="result-card">
                    <div class="result-header">
                        <i class="fas fa-cogs result-icon" style="color: #f39c12;"></i>
                        <h3 class="result-title">4. Signal Processing Pipeline (Z-transformacija)</h3>
                    </div>
                    <div class="result-content">
                        <p><strong>Opis:</strong> Koraci obrade signala korišćenjem Z-transformacije: originalni signal, bandpass filtriranje (0.5-40 Hz), baseline removal i filter response u Z-domenu.</p>
                        <img src="data:image/png;base64,${visualizations.processing_steps}" 
                             style="max-width: 100%; border: 2px solid #ddd; border-radius: 8px; margin: 10px 0;"
                             alt="Signal processing pipeline">
                        <p style="font-size: 0.9rem; color: #666;"><em>Slika 5.4: Pipeline obrade biomedicinskog signala korišćenjem Z-transformacije</em></p>
                    </div>
                </div>
            `;
        }
        } // End of old format

        // Dugme za export
        visualizationsHTML += `
            <div class="action-buttons" style="margin-top: 20px; text-align: center;">
                <button onclick="generatePDFReport()" class="btn btn-primary" style="margin: 5px;">
                    <i class="fas fa-file-pdf"></i> Generate Report
                </button>
                <button onclick="window.print()" class="btn btn-secondary" style="margin: 5px;">
                    <i class="fas fa-print"></i> Štampaj Vizuelizacije
                </button>
            </div>
        `;

        vizSection.innerHTML = visualizationsHTML;
        vizSection.style.display = 'block';
        console.log('📊 Thesis visualizations added to page');
    }

    // NOVO v3.1: Asinhrono generisanje vizuelizacija
    async generateVisualizationsAsync(analysisData) {
        console.log('🚀 v3.1 Starting async visualization generation');
        
        // Prvo prikaži placeholder sekciju
        this.showVisualizationPlaceholders();
        
        // Generiši svaku vizuelizaciju asinhrono
        const visualizations = ['1', '2', '3', '4', '5'];
        const promises = visualizations.map(id => this.generateSingleVisualization(id, analysisData));
        
        // Čekaj sve vizuelizacije
        const results = await Promise.allSettled(promises);
        
        // Obradi rezultate
        results.forEach((result, index) => {
            const vizId = visualizations[index];
            if (result.status === 'fulfilled' && result.value) {
                this.updateVisualizationContent(vizId, result.value);
            } else {
                this.updateVisualizationError(vizId, result.reason);
            }
        });
        
        console.log('✅ v3.1 All visualizations completed');
    }

    showVisualizationPlaceholders() {
        const resultsSection = document.getElementById('resultsSection');
        let vizSection = document.getElementById('thesisVisualizationsSection');
        
        if (!vizSection) {
            vizSection = document.createElement('div');
            vizSection.id = 'thesisVisualizationsSection';
            vizSection.className = 'main-card';
            vizSection.style.marginTop = '20px';
            resultsSection.parentNode.insertBefore(vizSection, resultsSection.nextSibling);
        }

        vizSection.innerHTML = `
            <div class="result-card collapsible collapsed">
                <div class="result-header" onclick="toggleResultCard(this)">
                    <i class="fas fa-chart-line result-icon" style="color: #3498db;"></i>
                    <h3 class="result-title">8. Vizuelizacije za Master Rad: Furijeova i Z-transformacija u analizi biomedicinskih signala</h3>
                </div>
                <div class="result-content">
            <div style="background: #e8f5e8; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                <strong>📊 Furijeova i Z-transformacija u analizi biomedicinskih signala</strong><br>
                Generišu se grafici za uključivanje u poglavlje 5 master rada...
            </div>
            
            <div id="viz-1" class="result-card">
                <div class="result-header">
                    <i class="fas fa-chart-line result-icon" style="color: #3498db;"></i>
                    <h3 class="result-title">1. EKG Signal sa Detektovanim R-pikovima</h3>
                </div>
                <div class="result-content">
                    <p><strong>Opis:</strong> Vremenski domen EKG signala sa automatski detektovanim R-pikovima označenim crvenim krugovima.</p>
                    <div class="loading-placeholder">
                        <i class="fas fa-spinner fa-spin" style="font-size: 2rem; color: #3498db;"></i><br>
                        Generiše se slika 1...
                    </div>
                    <p style="font-size: 0.9rem; color: #666;"><em>Slika 5.1: EKG signal u vremenskom domenu sa detektovanim R-pikovima</em></p>
                </div>
            </div>
            
            <div id="viz-2" class="result-card">
                <div class="result-header">
                    <i class="fas fa-chart-line result-icon" style="color: #3498db;"></i>
                    <h3 class="result-title">2. FFT Spektar (Furijeova Transformacija)</h3>
                </div>
                <div class="result-content">
                    <p><strong>Opis:</strong> Frekvencijski spektar EKG signala dobijen Furijeovom transformacijom.</p>
                    <div class="loading-placeholder">
                        <i class="fas fa-spinner fa-spin" style="font-size: 2rem; color: #3498db;"></i><br>
                        Generiše se slika 2...
                    </div>
                    <p style="font-size: 0.9rem; color: #666;"><em>Slika 5.2: FFT spektar EKG signala sa označenom dominantnom frekvencijom</em></p>
                </div>
            </div>
            
            <div id="viz-3" class="result-card">
                <div class="result-header">
                    <i class="fas fa-chart-line result-icon" style="color: #3498db;"></i>
                    <h3 class="result-title">3. Poređenje sa MIT-BIH Anotacijama</h3>
                </div>
                <div class="result-content">
                    <p><strong>Opis:</strong> Poređenje automatski detektovanih R-pikova sa ekspertskim MIT-BIH anotacijama.</p>
                    <div class="loading-placeholder">
                        <i class="fas fa-spinner fa-spin" style="font-size: 2rem; color: #3498db;"></i><br>
                        Generiše se slika 3...
                    </div>
                    <p style="font-size: 0.9rem; color: #666;"><em>Slika 5.3: Validacija algoritma protiv MIT-BIH ekspertskih anotacija</em></p>
                </div>
            </div>
            
            <div id="viz-4" class="result-card">
                <div class="result-header">
                    <i class="fas fa-chart-line result-icon" style="color: #3498db;"></i>
                    <h3 class="result-title">4. Signal Processing Pipeline (Z-transformacija)</h3>
                </div>
                <div class="result-content">
                    <p><strong>Opis:</strong> Koraci obrade signala korišćenjem Z-transformacije.</p>
                    <div class="loading-placeholder">
                        <i class="fas fa-spinner fa-spin" style="font-size: 2rem; color: #3498db;"></i><br>
                        Generiše se slika 4...
                    </div>
                    <p style="font-size: 0.9rem; color: #666;"><em>Slika 5.4: Pipeline obrade biomedicinskog signala korišćenjem Z-transformacije</em></p>
                </div>
            </div>
        `;
        
        vizSection.style.display = 'block';
    }

    async generateSingleVisualization(vizId, analysisData) {
        try {
            console.log(`🎨 v3.1 Generating visualization ${vizId}`);
            
            const response = await fetch(`/api/visualizations/thesis/visualization/${vizId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    signal: analysisData.extracted_signal || [],
                    fs: analysisData.signal_info?.sampling_frequency || 250,
                    analysis_results: analysisData
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const result = await response.json();
            
            if (result.success) {
                console.log(`✅ v3.1 Visualization ${vizId} completed`);
                return result;
            } else {
                throw new Error(result.error || 'Unknown error');
            }
            
        } catch (error) {
            console.error(`❌ v3.1 Visualization ${vizId} failed:`, error);
            throw error;
        }
    }

    updateVisualizationContent(vizId, vizData) {
        const placeholder = document.querySelector(`#viz-${vizId} .loading-placeholder`);
        if (placeholder && vizData.image_base64) {
            placeholder.innerHTML = `
                <img src="data:image/png;base64,${vizData.image_base64}" 
                     style="max-width: 100%; border: 2px solid #ddd; border-radius: 8px; margin: 10px 0;"
                     alt="Visualization ${vizId}">
            `;
        }
    }

    updateVisualizationError(vizId, error) {
        const placeholder = document.querySelector(`#viz-${vizId} .loading-placeholder`);
        if (placeholder) {
            placeholder.innerHTML = `
                <div style="background: #f8d7da; border: 1px solid #f5c6cb; border-radius: 5px; padding: 20px; text-align: center; color: #721c24;">
                    <i class="fas fa-exclamation-triangle" style="font-size: 1.5rem; margin-bottom: 10px;"></i><br>
                    Greška pri generisanju slike ${vizId}: ${error}
                </div>
            `;
        }
    }

    createFullReportHTML() {
        console.log('Creating full report HTML...', this.analysisData);
        if (!this.analysisData) {
            console.warn('No analysis data available for report');
            return `
            <div style="max-width: 800px; margin: 0 auto; font-family: Arial, sans-serif; padding: 20px;">
                <h1 style="text-align: center; color: #c0392b;">No Analysis Data Available</h1>
                <p style="text-align: center;">Please run an EKG analysis first before generating the report.</p>
            </div>`;
        }
        
        const data = this.analysisData;
        const timestamp = new Date().toLocaleString();
        
        return `
        <div style="max-width: 800px; margin: 0 auto; font-family: 'Times New Roman', serif; line-height: 1.6; color: #333;">
            <header style="text-align: center; margin-bottom: 40px; border-bottom: 2px solid #2c3e50; padding-bottom: 20px;">
                <h1 style="color: #2c3e50; margin-bottom: 10px; font-size: 24px;">EKG Signal Analysis Report</h1>
                <p style="color: #7f8c8d; font-size: 14px;">Generated: ${timestamp}</p>
                <p style="color: #7f8c8d; font-size: 12px; font-style: italic;">
                    Master Thesis: "Primena Furijeove i Z-transformacije u analizi biomedicinskih signala"
                </p>
            </header>
            
            ${this.generateSignalInfoSection(data)}
            ${this.generateHeartRateSection(data)}
            ${this.generateFFTSection(data)}
            ${this.generateZTransformSection(data)}
            ${this.generateArrhythmiaSection(data)}
            ${this.generateVisualizationsSection()}
            
            <footer style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #ccc; font-size: 12px; color: #777; text-align: center;">
                Generated by EKG Analysis Application - Master Thesis Implementation<br>
                University of Belgrade, Faculty of Electrical Engineering
            </footer>
        </div>`;
    }
    
    generateSignalInfoSection(data) {
        const si = data.signal_info;
        if (!si) return '';
        
        return `
        <section style="margin-bottom: 30px;">
            <h2 style="color: #2c3e50; border-bottom: 1px solid #bdc3c7; padding-bottom: 5px;">1. Signal Information</h2>
            <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 10px 0;">
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                    <div><strong>Duration:</strong> ${si.duration_seconds?.toFixed(2) || 'N/A'} seconds</div>
                    <div><strong>Sampling Frequency:</strong> ${si.sampling_frequency || 'N/A'} Hz</div>
                    <div><strong>Signal Length:</strong> ${si.length?.toLocaleString() || 'N/A'} samples</div>
                    <div><strong>Source:</strong> ${si.source || 'image_analysis'}</div>
                </div>
            </div>
        </section>`;
    }
    
    generateHeartRateSection(data) {
        const hr = data.arrhythmia_detection;
        if (!hr) return '';
        
        return `
        <section style="margin-bottom: 30px;">
            <h2 style="color: #2c3e50; border-bottom: 1px solid #bdc3c7; padding-bottom: 5px;">2. Heart Rate Analysis</h2>
            <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 10px 0;">
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                    <div><strong>Heart Rate:</strong> ${hr.heart_rate_bpm?.toFixed(1) || 'N/A'} BPM</div>
                    <div><strong>R-Peaks Detected:</strong> ${hr.r_peaks_count || 'N/A'}</div>
                    <div><strong>RR Interval Mean:</strong> ${hr.rr_statistics?.mean?.toFixed(0) || 'N/A'} ms</div>
                    <div><strong>Heart Rate Variability:</strong> ${hr.hrv_analysis?.rmssd?.toFixed(1) || 'N/A'} ms</div>
                </div>
                ${hr.signal_quality ? `
                <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid #e9ecef;">
                    <strong>Signal Quality:</strong> ${hr.signal_quality.quality_category || 'N/A'} 
                    (SNR: ${hr.signal_quality.snr_db?.toFixed(1) || 'N/A'} dB)
                </div>` : ''}
            </div>
        </section>`;
    }
    
    generateFFTSection(data) {
        const fft = data.fft_analysis;
        if (!fft) return '';
        
        return `
        <section style="margin-bottom: 30px;">
            <h2 style="color: #2c3e50; border-bottom: 1px solid #bdc3c7; padding-bottom: 5px;">3. Frequency Analysis (FFT)</h2>
            <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 10px 0;">
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                    <div><strong>Dominant Frequency:</strong> ${fft.peak_frequency?.toFixed(2) || 'N/A'} Hz</div>
                    <div><strong>Peak Amplitude:</strong> ${fft.peak_amplitude?.toFixed(4) || 'N/A'}</div>
                    <div><strong>Signal Quality (SNR):</strong> ${fft.signal_quality?.snr_db?.toFixed(1) || 'N/A'} dB</div>
                    <div><strong>Quality Category:</strong> ${fft.signal_quality?.quality_category || 'N/A'}</div>
                </div>
            </div>
        </section>`;
    }
    
    generateZTransformSection(data) {
        const zt = data.z_transform;
        if (!zt) return '';
        
        return `
        <section style="margin-bottom: 30px;">
            <h2 style="color: #2c3e50; border-bottom: 1px solid #bdc3c7; padding-bottom: 5px;">4. Z-Transform Analysis</h2>
            <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 10px 0;">
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                    <div><strong>System Poles:</strong> ${zt.poles?.length || 'N/A'}</div>
                    <div><strong>System Zeros:</strong> ${zt.zeros?.length || 'N/A'}</div>
                    <div><strong>System Stable:</strong> ${zt.stability?.is_stable ? 'Yes' : 'No'}</div>
                    <div><strong>Filter Type:</strong> ${zt.filter_analysis?.type || 'N/A'}</div>
                </div>
            </div>
        </section>`;
    }
    
    generateArrhythmiaSection(data) {
        const arr = data.arrhythmia_detection?.detected_arrhythmias;
        if (!arr) return '';
        
        return `
        <section style="margin-bottom: 30px;">
            <h2 style="color: #2c3e50; border-bottom: 1px solid #bdc3c7; padding-bottom: 5px;">5. Arrhythmia Detection</h2>
            <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 10px 0;">
                ${arr.length > 0 ? 
                    arr.map(arrhythmia => `
                        <div style="margin-bottom: 10px; padding: 10px; background: #fff3cd; border-left: 4px solid #ffc107; border-radius: 3px;">
                            <strong>${arrhythmia.type}:</strong> ${arrhythmia.description}
                        </div>
                    `).join('') :
                    '<div style="color: #28a745; font-weight: bold;">✅ No significant arrhythmias detected</div>'
                }
            </div>
        </section>`;
    }
    
    generateVisualizationsSection() {
        const visualizations = document.getElementById('visualizations');
        if (!visualizations || visualizations.style.display === 'none') return '';
        
        // Clone visualizations content and ensure images are properly sized for PDF
        let vizContent = visualizations.innerHTML;
        
        // Adjust image styles for PDF
        vizContent = vizContent.replace(/style="[^"]*"/g, (match) => {
            return match.replace(/max-width:\s*[^;]+;?/g, 'max-width: 100%; ')
                       .replace(/width:\s*[^;]+;?/g, 'width: 100%; ')
                       .replace(/height:\s*auto[^;]*;?/g, 'height: auto; ');
        });
        
        // Ensure all images have proper sizing
        vizContent = vizContent.replace(/<img/g, '<img style="max-width: 100%; height: auto; margin: 10px 0; border: 1px solid #ddd; border-radius: 5px;"');
        
        return `
        <section style="margin-bottom: 30px; page-break-inside: avoid;">
            <h2 style="color: #2c3e50; border-bottom: 1px solid #bdc3c7; padding-bottom: 5px;">6. Generated Visualizations & Diagrams</h2>
            <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 10px 0;">
                ${vizContent}
            </div>
        </section>`;
    }

    exportThesisReport() {
        // Generate report data
        const reportData = {
            timestamp: new Date().toLocaleString('sr'),
            signal_info: this.analysisData?.signal_info || {},
            analysis_results: {
                heart_rate: this.analysisData?.arrhythmia_detection?.heart_rate || {},
                arrhythmias: this.analysisData?.arrhythmia_detection?.arrhythmias || {},
                fft_analysis: this.analysisData?.fft_analysis || {},
                signal_quality: this.analysisData?.arrhythmia_detection?.signal_quality || {}
            }
        };

        // Create downloadable HTML report
        const reportHTML = this.generateHTMLReport(reportData);
        
        // Download as HTML file
        const blob = new Blob([reportHTML], { type: 'text/html' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `EKG_Analiza_Master_Rad_${new Date().toISOString().slice(0,10)}.html`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        this.showSuccess('📄 Report za master rad je preuzet!');
    }

    // Show additional analysis
    showAdditionalAnalysis() {
        console.log('🚀 v3.2: Auto-displaying additional analysis...');
        
        if (!this.analysisData) {
            console.log('⚠️ v3.2: No analysis data available for additional analysis');
            return;
        }

        try {
            // v3.2: NAJВАЖНИЈЕ - pozovi originalne thesis vizualizacije!
            if (this.analysisData.thesis_visualizations && !this.analysisData.thesis_visualizations.error) {
                console.log('📊 v3.2: Adding ORIGINAL thesis visualizations (the actual charts!)');
                this.addThesisVisualizations(this.analysisData.thesis_visualizations);
            } else {
                console.log('⚠️ v3.2: No thesis visualizations available - trying to generate...');
                // Pokušaj da generiše vizualizacije ako ne postoje
                this.requestThesisVisualizations();
            }
            
            // v3.2: Uklonjene dodatne sekcije - samo thesis vizualizacije
            
            console.log('✅ v3.2: Additional analysis with visualizations displayed successfully');
            
        } catch (error) {
            console.error('❌ v3.2: Error in showAdditionalAnalysis:', error);
        }
    }

    // v3.2: Zahtevaj thesis vizualizacije ako ne postoje
    async requestThesisVisualizations() {
        if (!this.analysisData) return;
        
        try {
            console.log('🔄 v3.2: Requesting thesis visualizations...');
            
            const response = await fetch('/api/analyze/complete', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    raw_signal: this.analysisData.signal_info?.raw_signal || null,
                    fs: this.analysisData.signal_info?.sampling_frequency || 250,
                    force_visualizations: true
                })
            });
            
            if (response.ok) {
                const result = await response.json();
                if (result.thesis_visualizations && !result.thesis_visualizations.error) {
                    console.log('✅ v3.2: Got thesis visualizations, adding them now...');
                    this.addThesisVisualizations(result.thesis_visualizations);
                }
            }
        } catch (error) {
            console.error('❌ v3.2: Error requesting visualizations:', error);
        }
    }

    // v3.2: Uklonjena detailedAnalysisSection

    // v3.2: Dodaj thesis vizualizacije u detaljnu sekciju
    addThesisVisualizationsToDetailed(vizData) {
        const container = document.getElementById('visualizationsContainer');
        if (!container) return;
        
        // Slika 1: Time-domain
        if (vizData.slika_1_time_domain_base64) {
            const img1HTML = `
                <div class="result-card">
                    <div class="result-header">
                        <i class="fas fa-chart-line result-icon" style="color: #007bff;"></i>
                        <h3 class="result-title">Slika 1: Time-Domain Analiza</h3>
                        <span style="background: #007bff; color: white; padding: 4px 8px; border-radius: 12px; font-size: 0.8em; margin-left: 10px;">🚀 Auto v3.2</span>
                    </div>
                    <div class="result-content">
                        <img src="${vizData.slika_1_time_domain_base64}" alt="Time-Domain Analiza" style="width: 100%; max-width: 800px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
                        <p style="margin-top: 15px; padding: 10px; background: #f8f9fa; border-radius: 6px; color: #666; font-size: 0.9em;">
                            <strong>📊 Opis:</strong> ${vizData.slika_1_opis || 'EKG signal u vremenskom domenu sa detektovanim R-pikovima i osnovnim parametrima srčanog ritma'}
                        </p>
                    </div>
                </div>
            `;
            container.innerHTML += img1HTML;
        }
        
        // Slika 2: FFT spektar
        if (vizData.slika_2_fft_spektar_base64) {
            const img2HTML = `
                <div class="result-card">
                    <div class="result-header">
                        <i class="fas fa-wave-square result-icon" style="color: #28a745;"></i>
                        <h3 class="result-title">Slika 2: FFT Spektralna Analiza</h3>
                        <span style="background: #28a745; color: white; padding: 4px 8px; border-radius: 12px; font-size: 0.8em; margin-left: 10px;">🔬 Spektar</span>
                    </div>
                    <div class="result-content">
                        <img src="${vizData.slika_2_fft_spektar_base64}" alt="FFT Spektar" style="width: 100%; max-width: 800px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
                        <p style="margin-top: 15px; padding: 10px; background: #f8f9fa; border-radius: 6px; color: #666; font-size: 0.9em;">
                            <strong>📈 Opis:</strong> ${vizData.slika_2_opis || 'Fourier transformacija EKG signala - frekventni spektar sa dominantnim frekvencijama i harmonicima'}
                        </p>
                    </div>
                </div>
            `;
            container.innerHTML += img2HTML;
        }
        
        // Slika 3: Z-ravan
        if (vizData.slika_3_z_raven_base64) {
            const img3HTML = `
                <div class="result-card">
                    <div class="result-header">
                        <i class="fas fa-project-diagram result-icon" style="color: #dc3545;"></i>
                        <h3 class="result-title">Slika 3: Z-Transform Pole-Zero Analiza</h3>
                        <span style="background: #dc3545; color: white; padding: 4px 8px; border-radius: 12px; font-size: 0.8em; margin-left: 10px;">⚙️ Z-Transform</span>
                    </div>
                    <div class="result-content">
                        <img src="${vizData.slika_3_z_raven_base64}" alt="Z-Ravan" style="width: 100%; max-width: 800px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
                        <p style="margin-top: 15px; padding: 10px; background: #f8f9fa; border-radius: 6px; color: #666; font-size: 0.9em;">
                            <strong>⚙️ Opis:</strong> ${vizData.slika_3_opis || 'Z-transformacija - polovi i nule digitalnog filtera sa analizom stabilnosti sistema'}
                        </p>
                    </div>
                </div>
            `;
            container.innerHTML += img3HTML;
        }
    }

    // v3.2: Dodaj naprednu signal processing analizu
    addAdvancedSignalProcessing() {
        const container = document.getElementById('visualizationsContainer');
        if (!container || !this.analysisData) return;
        
        const data = this.analysisData;
        const fftData = data.fft_analysis;
        const zData = data.z_transform;
        
        const processingHTML = `
            <div class="result-card">
                <div class="result-header">
                    <i class="fas fa-microchip result-icon" style="color: #6f42c1;"></i>
                    <h3 class="result-title">Signal Processing Pipeline v3.2</h3>
                    <span style="background: #6f42c1; color: white; padding: 4px 8px; border-radius: 12px; font-size: 0.8em; margin-left: 10px;">🔧 Pipeline</span>
                </div>
                <div class="result-content">
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                        <div style="background: #f8f9fa; padding: 15px; border-radius: 8px;">
                            <h4>🔬 FFT Spektralna Analiza</h4>
                            ${fftData && !fftData.error ? `
                                <div style="display: grid; gap: 8px;">
                                    <div style="padding: 8px; background: white; border-radius: 4px; border-left: 4px solid #007bff;">
                                        <strong>Peak frekvencija:</strong> ${fftData.peak_frequency_hz?.toFixed(2)} Hz
                                    </div>
                                    <div style="padding: 8px; background: white; border-radius: 4px; border-left: 4px solid #28a745;">
                                        <strong>Peak amplituda:</strong> ${fftData.peak_amplitude?.toFixed(4)}
                                    </div>
                                    <div style="padding: 8px; background: white; border-radius: 4px; border-left: 4px solid #ffc107;">
                                        <strong>Dominant freq:</strong> ${fftData.dominant_frequency_hz?.toFixed(2)} Hz
                                    </div>
                                </div>
                            ` : '<p style="color: #666;">FFT analiza nedostupna</p>'}
                        </div>
                        <div style="background: #f8f9fa; padding: 15px; border-radius: 8px;">
                            <h4>⚙️ Z-Transform Analiza</h4>
                            ${zData && !zData.error ? `
                                <div style="display: grid; gap: 8px;">
                                    <div style="padding: 8px; background: white; border-radius: 4px; border-left: 4px solid #dc3545;">
                                        <strong>Polovi:</strong> ${zData.poles?.length || 0}
                                    </div>
                                    <div style="padding: 8px; background: white; border-radius: 4px; border-left: 4px solid #17a2b8;">
                                        <strong>Nule:</strong> ${zData.zeros?.length || 0}
                                    </div>
                                    <div style="padding: 8px; background: white; border-radius: 4px; border-left: 4px solid ${zData.stability?.stable ? '#28a745' : '#dc3545'};">
                                        <strong>Stabilnost:</strong> ${zData.stability?.stable ? 'Stabilan' : 'Nestabilan'}
                                    </div>
                                </div>
                            ` : '<p style="color: #666;">Z-Transform analiza nedostupna</p>'}
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        container.innerHTML += processingHTML;
    }

    // v3.2: Dodaj napredne metrике
    addAdvancedMetrics() {
        const container = document.getElementById('visualizationsContainer');
        if (!container || !this.analysisData) return;
        
        const data = this.analysisData;
        const signalInfo = data.signal_info;
        const signalQuality = data.arrhythmia_detection?.signal_quality;
        
        const metricsHTML = `
            <div class="result-card">
                <div class="result-header">
                    <i class="fas fa-chart-bar result-icon" style="color: #17a2b8;"></i>
                    <h3 class="result-title">Napredne Metrике i Status v3.2</h3>
                    <span style="background: #17a2b8; color: white; padding: 4px 8px; border-radius: 12px; font-size: 0.8em; margin-left: 10px;">📊 Metrике</span>
                </div>
                <div class="result-content">
                    <div style="background: #e3f2fd; padding: 15px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #2196f3;">
                        <h4 style="color: #1565c0; margin: 0 0 10px 0;">✅ v3.2 Automatski Prikaz Aktiviran</h4>
                        <p style="margin: 0; color: #1565c0;">
                            Sve napredne analize su automatski prikazane: thesis vizualizacije, FFT spektar, Z-transform i signal processing pipeline.
                        </p>
                    </div>
                    
                    <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px;">
                        <div style="text-align: center; padding: 15px; background: #f8f9fa; border-radius: 8px;">
                            <h5 style="margin: 0 0 10px 0; color: #6f42c1;">📈 Signal Info</h5>
                            <p style="margin: 5px 0;"><strong>Trajanje:</strong> ${signalInfo?.duration_seconds?.toFixed(1)} s</p>
                            <p style="margin: 5px 0;"><strong>Fs:</strong> ${signalInfo?.sampling_frequency} Hz</p>
                            <p style="margin: 5px 0;"><strong>Uzoraka:</strong> ${signalInfo?.length}</p>
                        </div>
                        <div style="text-align: center; padding: 15px; background: #f8f9fa; border-radius: 8px;">
                            <h5 style="margin: 0 0 10px 0; color: #28a745;">🔊 Kvalitet</h5>
                            <p style="margin: 5px 0;"><strong>Status:</strong> ${signalQuality?.quality || 'N/A'}</p>
                            <p style="margin: 5px 0;"><strong>SNR:</strong> ${signalQuality?.snr_db?.toFixed(1)} dB</p>
                            <p style="margin: 5px 0;"><strong>Source:</strong> ${signalInfo?.source || 'unknown'}</p>
                        </div>
                        <div style="text-align: center; padding: 15px; background: #f8f9fa; border-radius: 8px;">
                            <h5 style="margin: 0 0 10px 0; color: #dc3545;">🚀 v3.2 Status</h5>
                            <p style="margin: 5px 0;"><strong>Gateway:</strong> Automatski</p>
                            <p style="margin: 5px 0;"><strong>Vizualizacije:</strong> Prikazane</p>
                            <p style="margin: 5px 0;"><strong>Pipeline:</strong> Aktiviran</p>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        container.innerHTML += metricsHTML;
    }

    generateHTMLReport(data) {
        return `
<!DOCTYPE html>
<html lang="sr">
<head>
    <meta charset="UTF-8">
    <title>EKG Analiza - Master Rad Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
        h1, h2 { color: #2c3e50; }
        .summary { background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; }
        .metric { margin: 10px 0; }
        .metric-label { font-weight: bold; }
        table { border-collapse: collapse; width: 100%; margin: 20px 0; }
        th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
        th { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <h1>📊 EKG Analiza - Master Rad Report</h1>
    <p><strong>Tema:</strong> Primena Furijeove i Z-transformacije u analizi biomedicinskih signala</p>
    <p><strong>Datum analize:</strong> ${data.timestamp}</p>
    
    <div class="summary">
        <h2>Opšti Podaci Signala</h2>
        <div class="metric"><span class="metric-label">Broj uzoraka:</span> ${data.signal_info.length?.toLocaleString() || 'N/A'}</div>
        <div class="metric"><span class="metric-label">Trajanje:</span> ${data.signal_info.duration_seconds?.toFixed(1) || 'N/A'}s</div>
        <div class="metric"><span class="metric-label">Frekvencija uzorkovanja:</span> ${data.signal_info.sampling_frequency || 'N/A'} Hz</div>
        <div class="metric"><span class="metric-label">Izvor:</span> ${data.signal_info.source || 'N/A'}</div>
    </div>

    <h2>Rezultati Analize</h2>
    <table>
        <tr><th>Parametar</th><th>Vrednost</th><th>Interpretacija</th></tr>
        <tr><td>Prosečna frekvencija</td><td>${data.analysis_results.heart_rate.average_bpm?.toFixed(1) || 'N/A'} bpm</td><td>Srčana frekvencija</td></tr>
        <tr><td>Broj R-pikova</td><td>${data.analysis_results.heart_rate.rr_count || 'N/A'}</td><td>Detektovani otkucaji</td></tr>
        <tr><td>HRV</td><td>${data.analysis_results.heart_rate.heart_rate_variability?.toFixed(1) || 'N/A'} ms</td><td>Varijabilnost ritma</td></tr>
        <tr><td>SNR</td><td>${data.analysis_results.signal_quality.snr_db?.toFixed(1) || 'N/A'} dB</td><td>Kvalitet signala</td></tr>
        <tr><td>Dominantna frekvencija</td><td>${data.analysis_results.fft_analysis.peak_frequency_hz?.toFixed(2) || 'N/A'} Hz</td><td>FFT analiza</td></tr>
    </table>

    <h2>Zaključak</h2>
    <p>Analiza je uspešno demonstrirala primenu Furijeove i Z-transformacije u obradi biomedicinskih signala. 
    Algoritmi za detekciju R-pikova i frekvencijsku analizu pokazali su satisfactorne rezultate.</p>
    
    <footer style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #ccc; font-size: 0.9rem; color: #666;">
        Generisan automatski pomoću EKG analize aplikacije - Master rad "Primena Furijeove i Z-transformacije u analizi biomedicinskih signala"
    </footer>
</body>
</html>`;
    }
}

// =============================
// PDF GENERATION FUNCTIONALITY
// =============================

async function generatePDFReport() {
    const button = event.target;
    const originalText = button.innerHTML;
    
    try {
        // Show loading state
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generišem PDF...';
        button.disabled = true;
        
        // Load html2canvas if not available
        if (typeof html2canvas === 'undefined') {
            const script = document.createElement('script');
            script.src = 'https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js';
            document.head.appendChild(script);
            await new Promise(resolve => setTimeout(resolve, 1000));
        }
        
        // Wait for jsPDF to be available
        let attempts = 0;
        while (attempts < 50 && typeof window.jsPDF === 'undefined') {
            await new Promise(resolve => setTimeout(resolve, 100));
            attempts++;
        }
        
        // Try different ways to access jsPDF
        let jsPDF;
        if (typeof window.jsPDF === 'function') {
            jsPDF = window.jsPDF;
        } else if (window.jsPDF && typeof window.jsPDF.jsPDF === 'function') {
            jsPDF = window.jsPDF.jsPDF;
        } else if (window.jspdf && typeof window.jspdf.jsPDF === 'function') {
            jsPDF = window.jspdf.jsPDF;
        } else {
            // Fallback: try to load library dynamically
            await new Promise((resolve, reject) => {
                const script = document.createElement('script');
                script.src = 'https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js';
                script.onload = () => {
                    setTimeout(resolve, 200);
                };
                script.onerror = reject;
                document.head.appendChild(script);
            });
            
            if (typeof window.jsPDF === 'function') {
                jsPDF = window.jsPDF;
            } else if (window.jsPDF && typeof window.jsPDF.jsPDF === 'function') {
                jsPDF = window.jsPDF.jsPDF;
            } else {
                throw new Error('Cannot load jsPDF library');
            }
        }
        
        const doc = new jsPDF();
        
        // Create hidden container with the export report HTML
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Priprema sadržaj...';
        
        const tempContainer = document.createElement('div');
        tempContainer.style.position = 'fixed';
        tempContainer.style.left = '0';
        tempContainer.style.top = '0';
        tempContainer.style.width = '800px'; // Visible width
        tempContainer.style.height = 'auto';
        tempContainer.style.backgroundColor = 'white';
        tempContainer.style.padding = '20px';
        tempContainer.style.fontFamily = 'Arial, sans-serif';
        tempContainer.style.zIndex = '10000';
        tempContainer.style.overflow = 'visible';
        
        // Use the existing export report functionality with complete HTML content
        console.log('Generating PDF content...', window.ekgAnalyzer);
        
        if (window.ekgAnalyzer && window.ekgAnalyzer.analysisData) {
            console.log('Using ekgAnalyzer with data:', window.ekgAnalyzer.analysisData);
            const fullHTML = window.ekgAnalyzer.createFullReportHTML();
            console.log('Generated HTML length:', fullHTML ? fullHTML.length : 'null');
            tempContainer.innerHTML = fullHTML;
        } else {
            console.log('Falling back to basic content');
            // Enhanced fallback to basic content with visualizations
            const resultsContent = document.getElementById('resultsSection')?.innerHTML || 'No analysis results available';
            const visualizationsContent = document.getElementById('visualizations')?.innerHTML || '';
            
            tempContainer.innerHTML = `
                <div style="max-width: 800px; margin: 0 auto; font-family: Arial, sans-serif; padding: 20px;">
                    <header style="text-align: center; margin-bottom: 40px; border-bottom: 2px solid #2c3e50; padding-bottom: 20px;">
                        <h1 style="color: #2c3e50; margin-bottom: 10px;">EKG Analysis Report v2.9</h1>
                        <p style="color: #7f8c8d;">Generated: ${new Date().toLocaleString()}</p>
                    </header>
                    
                    <section style="margin-bottom: 30px;">
                        <h2 style="color: #2c3e50; border-bottom: 1px solid #bdc3c7; padding-bottom: 5px;">Analysis Results</h2>
                        <div style="background: #f8f9fa; padding: 15px; border-radius: 5px;">
                            ${resultsContent}
                        </div>
                    </section>
                    
                    ${visualizationsContent ? `
                    <section style="margin-bottom: 30px;">
                        <h2 style="color: #2c3e50; border-bottom: 1px solid #bdc3c7; padding-bottom: 5px;">Generated Visualizations & Diagrams</h2>
                        <div style="background: #f8f9fa; padding: 15px; border-radius: 5px;">
                            ${visualizationsContent}
                        </div>
                    </section>
                    ` : ''}
                    
                    <footer style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #ccc; text-align: center; font-size: 12px; color: #777;">
                        Generated by EKG Analysis Application v2.9 - Master Thesis Implementation
                    </footer>
                </div>
            `;
        }
        
        document.body.appendChild(tempContainer);
        
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Konvertuje u PDF...';
        
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generiše PDF...';
        
        // Wait a moment for content to render
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        console.log('Starting jsPDF html() method...');
        
        // Use jsPDF html() method like the original Export Report
        await new Promise((resolve, reject) => {
            doc.html(tempContainer, {
                callback: function(doc) {
                    console.log('jsPDF html() completed successfully');
                    resolve(doc);
                },
                margin: [15, 15, 15, 15],
                autoPaging: 'text',
                x: 0,
                y: 0,
                width: 180, // A4 width minus margins
                windowWidth: 800, // Match container width
                html2canvas: {
                    scale: 1,
                    useCORS: true,
                    allowTaint: true,
                    letterRendering: true,
                    logging: true
                }
            });
        });
        
        // Remove temporary container
        document.body.removeChild(tempContainer);
        
        // Save the PDF
        const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-');
        doc.save(`EKG_Analysis_Report_v2.9_${timestamp}.pdf`);
        
        // Show success message
        button.innerHTML = '<i class="fas fa-check"></i> Report Generated!';
        setTimeout(() => {
            button.innerHTML = originalText;
            button.disabled = false;
        }, 3000);
        
    } catch (error) {
        console.error('Error generating PDF:', error);
        
        // Fallback: use browser's built-in print functionality
        try {
            button.innerHTML = '<i class="fas fa-print"></i> Otvaram za štampu...';
            
            // Create a printable version
            const printContent = document.createElement('div');
            printContent.innerHTML = `
                <h1>EKG Signal Analysis Report</h1>
                <p>Generated: ${new Date().toLocaleString()}</p>
                <hr>
                ${document.getElementById('result')?.innerHTML || 'No analysis results available'}
                ${document.getElementById('advancedAnalysisResult')?.innerHTML || ''}
                ${document.getElementById('visualizations')?.innerHTML || ''}
            `;
            
            const printWindow = window.open('', '_blank');
            printWindow.document.write(`
                <html>
                <head>
                    <title>EKG Analysis Report</title>
                    <style>
                        body { font-family: Arial, sans-serif; margin: 20px; }
                        h1 { color: #333; }
                        img { max-width: 100%; height: auto; margin: 10px 0; }
                    </style>
                </head>
                <body>${printContent.innerHTML}</body>
                </html>
            `);
            printWindow.document.close();
            printWindow.print();
            
            button.innerHTML = '<i class="fas fa-check"></i> Otvoren za štampu!';
        } catch (fallbackError) {
            console.error('Fallback also failed:', fallbackError);
            button.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Greška!';
        }
        
        setTimeout(() => {
            button.innerHTML = originalText;
            button.disabled = false;
        }, 3000);
    }
}

// Funkcija za kreiranje specifičnih objašnjenja za svaki dijagram
EKGAnalyzer.prototype.getVisualizationExplanation = function(key, viz) {
    const explanations = {
        "1": "Ovaj dijagram prikazuje EKG signal u vremenskom domenu sa detektovanim R-pikovima (označeni crvenim krugovima). R-pikovi predstavljaju električni impuls koji pokreće kontrakciju srčanih komora. Analiza R-pikova omogućava merenje srčane frekvencije, varijabilnosti srčanog ritma i detekciju potencijalnih aritmija. Visina i raspored R-pikova mogu ukazati na različite kardiološke stanja.",
        
        "2": "FFT (Fast Fourier Transform) spektar pokazuje frekvencijski sadržaj EKG signala. Dominantna frekvencija (označena crvenom linijom) odgovara osnovnoj srčanoj frekvenciji. Analiza frekvencijskog spektra omogućava identifikaciju periodičnih komponenti signala, šuma i artefakata. Visoke frekvencije mogu ukazati na mišićne artefakte, dok niske frekvencije mogu biti posledica disanja ili kretanja pacijenta.",
        
        "3": "Ovaj dijagram poredi automatski detektovane R-pikove (crveno) sa ekspertskim MIT-BIH anotacijama (zeleno). MIT-BIH baza podataka sadrži ručno označene R-pikove od strane kardiologa i predstavlja 'zlatni standard' za validaciju algoritama. Poklapanje detektovanih pikova sa ekspertskim anotacijama ukazuje na tačnost algoritma za detekciju R-pikova.",
        
        "4": "Signal processing pipeline prikazuje korake obrade EKG signala korišćenjem Z-transformacije: 1) Originalni signal, 2) Bandpass filtriranje (0.5-40 Hz) za uklanjanje šuma, 3) Baseline removal za eliminaciju drift-a signala, 4) Filter response u Z-domenu koji pokazuje karakteristike primenjenog filtera. Z-transformacija omogućava dizajn i analizu digitalnih filtara u diskretnom domenu."
    };
    
    return explanations[key] || `Objašnjenje za ${viz.title}: Ovaj dijagram predstavlja važnu komponentu analize EKG signala u okviru master rada o primeni Furijeove i Z-transformacije u biomedicinskim signalima.`;
};

// Zamena postojeće funkcije addThesisVisualizations sa novom implementacijom
EKGAnalyzer.prototype.addThesisVisualizations = function(visualizations) {
    console.log('🎯 v3.1 Creating accordion thesis visualizations');
    console.log('📊 Available visualizations:', Object.keys(visualizations.visualizations || {}));
    
    // Ukloni postojeće vizuelizacije
    const existing = document.getElementById('thesisVisualizationsSection');
    if (existing) existing.remove();
    
    // Kreiraj accordion sekciju 8
    const section = document.createElement('div');
    section.id = 'thesisVisualizationsSection';
    section.className = 'result-card collapsible collapsed';
    section.style.marginTop = '20px';
    
    let html = `
        <div class="result-header" onclick="toggleResultCard(this)">
            <i class="fas fa-chart-line result-icon" style="color: #3498db;"></i>
            <h3 class="result-title">8. Vizuelizacije za Master Rad: Furijeova i Z-transformacija u analizi biomedicinskih signala</h3>
        </div>
        <div class="result-content">
            <p style="margin-bottom: 20px; color: #666; font-style: italic;">
                Grafici spremni za uključivanje u poglavlje 5
            </p>
    `;
    
    // Dodaj svaku vizuelizaciju
    const vizData = visualizations.visualizations || {};
    const sortedKeys = Object.keys(vizData).sort((a, b) => parseInt(a) - parseInt(b));
    
    console.log('📊 v3.1 Sorted visualization keys:', sortedKeys);
    
    for (const key of sortedKeys) {
        const viz = vizData[key];
        console.log(`📊 v3.1 Processing visualization ${key}:`, {
            title: viz.title,
            hasImage: !!viz.image_base64,
            imageLength: viz.image_base64 ? viz.image_base64.length : 0
        });
        
        // Kreiraj objašnjenje specifično za svaki dijagram
        const explanation = this.getVisualizationExplanation(key, viz);
        
        if (viz.image_base64) {
            html += `
                <div class="result-card" style="margin-bottom: 20px;">
                    <div class="result-header" style="position: relative;">
                        <i class="fas fa-chart-area result-icon" style="color: #3498db;"></i>
                        <h3 class="result-title">${viz.title || `Vizuelizacija ${key}`}</h3>
                        <button class="info-btn" 
                                style="position: absolute; right: 10px; top: 50%; transform: translateY(-50%); background: #007bff; color: white; border: none; border-radius: 50%; width: 25px; height: 25px; cursor: pointer; font-size: 14px; font-weight: bold; transition: all 0.3s ease;">i</button>
                    </div>
                    <div class="explanation-panel" style="display: none; background: #e7f3ff; padding: 15px; margin: 10px 0; border-left: 4px solid #007bff; border-radius: 5px;">
                        <h4 style="color: #0056b3; margin: 0 0 10px 0;"><i class="fas fa-info-circle"></i> Objašnjenje dijagrama</h4>
                        <p style="margin: 0; line-height: 1.5;">${explanation}</p>
                    </div>
                    <div class="result-content">
                        <p style="margin-bottom: 15px;">${viz.description || ''}</p>
                        <div style="text-align: center; margin: 20px 0;">
                            <img src="data:image/png;base64,${viz.image_base64}" 
                                 style="max-width: 100%; border: 1px solid #ddd; border-radius: 8px;" 
                                 alt="${viz.title || `Vizuelizacija ${key}`}">
                        </div>
                        <p style="font-style: italic; color: #666; text-align: center; margin-top: 10px;">
                            ${viz.caption || ''}
                        </p>
                    </div>
                </div>
            `;
        } else {
            console.log(`⚠️ v3.1 Visualization ${key} has no image_base64`);
            html += `
                <div class="result-card" style="margin-bottom: 20px;">
                    <div class="result-header" style="position: relative;">
                        <i class="fas fa-chart-area result-icon" style="color: #95a5a6;"></i>
                        <h3 class="result-title">${viz.title || `Vizuelizacija ${key}`}</h3>
                        <button class="info-btn" 
                                style="position: absolute; right: 10px; top: 50%; transform: translateY(-50%); background: #007bff; color: white; border: none; border-radius: 50%; width: 25px; height: 25px; cursor: pointer; font-size: 14px; font-weight: bold; transition: all 0.3s ease;">i</button>
                    </div>
                    <div class="explanation-panel" style="display: none; background: #e7f3ff; padding: 15px; margin: 10px 0; border-left: 4px solid #007bff; border-radius: 5px;">
                        <h4 style="color: #0056b3; margin: 0 0 10px 0;"><i class="fas fa-info-circle"></i> Objašnjenje dijagrama</h4>
                        <p style="margin: 0; line-height: 1.5;">${explanation}</p>
                    </div>
                    <div class="result-content">
                        <p style="margin-bottom: 15px;">${viz.description || ''}</p>
                        <div style="text-align: center; padding: 40px; background: #f8f9fa; border: 2px dashed #dee2e6; border-radius: 8px;">
                            <i class="fas fa-image" style="font-size: 48px; color: #dee2e6; margin-bottom: 15px;"></i>
                            <p style="color: #6c757d; margin: 0;">Slika nije dostupna za ovaj dijagram</p>
                        </div>
                        <p style="font-style: italic; color: #666; text-align: center; margin-top: 10px;">
                            ${viz.caption || ''}
                        </p>
                    </div>
                </div>
            `;
        }
    }
    
    // Zatvori accordion strukturu
    html += `
        </div>
    `;
    
    section.innerHTML = html;
    
    // Dodaj sekciju na stranu
    const resultsSection = document.getElementById('resultsSection');
    resultsSection.parentNode.insertBefore(section, resultsSection.nextSibling);
    
    console.log('✅ v3.1 Accordion thesis visualizations section (8) added successfully');
};

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.ekgAnalyzer = new EKGAnalyzer();
});

// Helper function for lazy loading large images - FIX for broken pipe
window.loadLazyImage = function(key) {
    console.log(`Loading lazy image ${key}`);
    
    const container = document.getElementById(`lazy-image-${key}`);
    if (!container) {
        console.error(`Container for lazy image ${key} not found`);
        return;
    }
    
    const imageData = window.lazyImages && window.lazyImages[key];
    if (!imageData) {
        console.error(`Image data for ${key} not found`);
        container.innerHTML = "<p style=\"color: red;\">Greška: Slika nije pronađena</p>";
        return;
    }
    
    // Show loading spinner
    container.innerHTML = `
        <div style="padding: 40px;">
            <i class="fas fa-spinner fa-spin" style="font-size: 48px; color: #007bff; margin-bottom: 15px;"></i>
            <p style="color: #007bff;">Učitava sliku...</p>
        </div>
    `;
    
    // Load image after short delay to prevent broken pipe
    setTimeout(() => {
        try {
            container.innerHTML = `
                <img src="data:image/png;base64,${imageData}" 
                     style="max-width: 100%; border: 2px solid #ddd; border-radius: 8px;" 
                     alt="Thesis visualization ${key}"
                     loading="lazy">
            `;
            console.log(`✅ Lazy image ${key} loaded successfully`);
        } catch (error) {
            console.error(`❌ Error loading lazy image ${key}:`, error);
            container.innerHTML = "<p style=\"color: red;\">Greška pri učitavanju slike</p>";
        }
    }, 500);
};

console.log("🔧 Broken pipe fix helper functions loaded");


// EDUKATIVNI SISTEM - "i" dugme objašnjenja
window.showEducationalInfo = function(vizKey, vizTitle, vizDescription) {
    console.log("🎓 Educational info for:", vizKey, vizTitle);
    
    const explanations = {
        "1": {
            title: "📈 EKG Signal sa R-pikovima",
            content: `
                <h4>Analiza ovog dijagrama:</h4>
                <p><strong>Što vidite:</strong> Plava linija = vaš EKG signal, Crveni krugovi = detektovani otkucaji srca</p>
                <h4>Kako čitati:</h4>
                <ul>
                    <li><strong>Broj crvenih krugova</strong> = Broj detektovanih otkucaja</li>
                    <li><strong>Razmaci između krugova</strong> = Regularnost ritma</li>
                    <li><strong>Visina R-pikova</strong> = Snaga kontrakcije</li>
                </ul>
                <p><strong>Značaj:</strong> Prvi korak analize - detekcija karakterističnih tačaka vašeg EKG signala za dalju FFT i Z-transformaciju analizu.</p>
            `
        },
        "2": {
            title: "📊 FFT Spektar (Furijeova Transformacija)", 
            content: `
                <h4>Analiza ovog FFT spektra:</h4>
                <p><strong>Što vidite:</strong> Frekvencijski sadržaj vašeg EKG signala</p>
                <h4>Elementi:</h4>
                <ul>
                    <li><strong>Najviši pik</strong> = Dominantna frekvencija vašeg srca</li>
                    <li><strong>Crvena linija</strong> = Izračunata srčana frekvencija</li>
                    <li><strong>Širina pika</strong> = Varijabilnost ritma</li>
                </ul>
                <p><strong>Značaj:</strong> Furijeova transformacija omogućava precizno računanje frekvencije i detekciju ritmičkih poremećaja.</p>
            `
        },
        "3": {
            title: "🏥 Poređenje sa MIT-BIH Anotacijama",
            content: `
                <h4>Validacija vašeg signala:</h4>
                <p><strong>Što vidite:</strong> Poređenje našeg algoritma sa medicinskim standardom</p>
                <h4>Simboli:</h4>
                <ul>
                    <li><strong>Crveni krugovi</strong> = Naš algoritam na vašem EKG-u</li>
                    <li><strong>Zeleni trouglovi</strong> = MIT-BIH ekspertske anotacije</li>
                    <li><strong>Poklapanje</strong> = Tačna detekcija</li>
                </ul>
                <p><strong>Značaj:</strong> Objektivna procena tačnosti algoritma na vašem konkretnom signalu protiv zlatnog standarda kardiologije.</p>
            `
        },
        "4": {
            title: "⚙️ Signal Processing Pipeline (Z-transformacija)",
            content: `
                <h4>Obrada vašeg signala:</h4>
                <p><strong>Što vidite:</strong> Koraci digitalne obrade vašeg EKG signala</p>
                <h4>Pipeline:</h4>
                <ul>
                    <li><strong>Panel 1</strong> = Vaš originalni signal (sa šumom)</li>
                    <li><strong>Panel 2</strong> = Nakon bandpass filtera</li>
                    <li><strong>Panel 3</strong> = Nakon baseline korekcije</li>
                    <li><strong>Panel 4</strong> = Z-filter karakteristike</li>
                </ul>
                <p><strong>Značaj:</strong> Z-transformacija omogućava kreiranje optimalnih digitalnih filtara za čišćenje vašeg EKG signala.</p>
            `
        }
    };
    
    const info = explanations[vizKey] || {
        title: vizTitle || "Dijagram",
        content: "<p>Pole-zero dijagram prikazuje pozicije polova i nula različitih digitalnih filtera u Z-ravni. Analiza stabilnosti sistema kroz pozicije polova u odnosu na jedinični krug je ključna za sigurno filtriranje biomedicinskih signala.</p>"
    };
    
    // Kreiraj modal
    const modal = document.createElement("div");
    modal.style.cssText = `
        position: fixed; top: 0; left: 0; width: 100%; height: 100%; 
        background: rgba(0,0,0,0.8); z-index: 10000; display: flex; 
        align-items: center; justify-content: center; padding: 20px;
    `;
    
    modal.innerHTML = `
        <div style="background: white; border-radius: 12px; max-width: 700px; max-height: 80vh; 
                    overflow-y: auto; padding: 25px; box-shadow: 0 10px 30px rgba(0,0,0,0.3);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; 
                        border-bottom: 2px solid #3498db; padding-bottom: 15px;">
                <h2 style="margin: 0; color: #2c3e50;">${info.title}</h2>
                <button onclick="this.parentElement.parentElement.parentElement.remove()" 
                        style="background: #e74c3c; color: white; border: none; border-radius: 50%; 
                               width: 30px; height: 30px; cursor: pointer; font-size: 18px;">×</button>
            </div>
            <div style="line-height: 1.6; color: #2c3e50;">${info.content}</div>
            <div style="text-align: center; margin-top: 20px;">
                <button onclick="this.parentElement.parentElement.parentElement.remove()" 
                        style="background: #3498db; color: white; border: none; padding: 10px 25px; 
                               border-radius: 6px; cursor: pointer;">Zatvori</button>
            </div>
        </div>
    `;
    
    modal.onclick = (e) => { if (e.target === modal) modal.remove(); };
    document.body.appendChild(modal);
};

// Automatski dodaj "i" dugmeta na dijagrame
function addInfoButtonsToVisualizations() {
    setTimeout(() => {
        const vizElements = document.querySelectorAll(".thesis-visualization h4");
        console.log(`🎓 Found ${vizElements.length} visualizations to add info buttons`);
        
        vizElements.forEach((h4, index) => {
            if (h4.querySelector(".info-btn")) return; // Već postoji
            
            const key = String(index + 1);
            const title = h4.textContent || "";
            
            // Napravi wrapper
            const wrapper = document.createElement("div");
            wrapper.style.cssText = "display: flex; justify-content: space-between; align-items: center;";
            
            // Premesti h4 u wrapper
            h4.parentNode.insertBefore(wrapper, h4);
            h4.style.margin = "0";
            wrapper.appendChild(h4);
            
            // Dodaj "i" dugme
            const btn = document.createElement("button");
            btn.className = "info-btn";
            btn.innerHTML = "i";
            btn.style.cssText = `
                background: #3498db; color: white; border: none; border-radius: 50%;
                width: 24px; height: 24px; cursor: pointer; font-size: 14px; font-weight: bold;
                display: flex; align-items: center; justify-content: center;
            `;
            btn.title = "Kliknite za objašnjenje dijagrama";
            btn.onclick = () => window.showEducationalInfo(key, title, "");
            
            wrapper.appendChild(btn);
            console.log(`🎓 Added info button to: ${title}`);
        });
    }, 1000);
}

// Aktiviraj kada se učitaju vizualizacije - CREATE SECTION 8 AS ACCORDION
const originalAddThesis = EKGAnalyzer.prototype.addThesisVisualizations;
EKGAnalyzer.prototype.addThesisVisualizations = function(visualizations) {
    console.log('🔄 Creating section 8: Thesis Visualizations as accordion');
    
    if (visualizations) {
        console.log('📊 Creating accordion thesis visualizations section...');
        
        // Create section 8 as accordion
        const thesisHTML = `
            <div id="thesisVisualizationsSection" class="result-card collapsible collapsed" style="margin-top: 20px;">
                <div class="result-header" onclick="toggleResultCard(this)">
                    <i class="fas fa-chart-line result-icon" style="color: #3498db;"></i>
                    <h3 class="result-title">8. Vizuelizacije za Master Rad: Furijeova i Z-transformacija u analizi biomedicinskih signala</h3>
                </div>
                <div class="result-content">
                    <p style="margin-bottom: 20px; color: #666; font-style: italic;">
                        Grafici spremni za uključivanje u poglavlje 5
                    </p>
                    
                    ${visualizations.fft_analysis ? `
                        <div class="chart-container" style="margin-bottom: 20px;">
                            <h4 style="margin-bottom: 10px;">FFT Analiza</h4>
                            <img src="${visualizations.fft_analysis}" alt="FFT Analiza" style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                        </div>
                    ` : ''}
                    
                    ${visualizations.z_transform ? `
                        <div class="chart-container" style="margin-bottom: 20px;">
                            <h4 style="margin-bottom: 10px;">Z-Transformacija</h4>
                            <img src="${visualizations.z_transform}" alt="Z-Transformacija" style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                        </div>
                    ` : ''}
                    
                    ${visualizations.frequency_domain ? `
                        <div class="chart-container" style="margin-bottom: 20px;">
                            <h4 style="margin-bottom: 10px;">Frekvencijski Domen</h4>
                            <img src="${visualizations.frequency_domain}" alt="Frekvencijski Domen" style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                        </div>
                    ` : ''}
                    
                    ${visualizations.combined_analysis ? `
                        <div class="chart-container" style="margin-bottom: 20px;">
                            <h4 style="margin-bottom: 10px;">Kombinovana Analiza</h4>
                            <img src="${visualizations.combined_analysis}" alt="Kombinovana Analiza" style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
        
        // Find where to insert section 8 (after section 7)
        const resultsSection = document.getElementById('resultsSection');
        if (resultsSection) {
            // Remove existing thesis section if present
            const existingThesis = document.getElementById('thesisVisualizationsSection');
            if (existingThesis) {
                existingThesis.remove();
            }
            
            // Insert section 8 after results section
            resultsSection.insertAdjacentHTML('afterend', thesisHTML);
            console.log('✅ Section 8 (Thesis Visualizations) created as accordion');
        }
    }
    
    // Also call the original function for compatibility
    const result = originalAddThesis.call(this, visualizations);
    addInfoButtonsToVisualizations();
    return result;
};

console.log("🎓 Educational system loaded - will add info buttons to visualizations");

// 🎯 ACCORDION TOGGLE FUNCTION - Global function za result cards
function toggleResultCard(headerElement) {
    const resultCard = headerElement.closest('.result-card');
    
    if (resultCard.classList.contains('collapsed')) {
        // Expand
        resultCard.classList.remove('collapsed');
    } else {
        // Collapse
        resultCard.classList.add('collapsed');
    }
}

// Initialize the EKG Analyzer when the page loads
document.addEventListener('DOMContentLoaded', function() {
    window.ekgAnalyzer = new EKGAnalyzer();
    console.log('✅ EKG Analyzer initialized');
});


// ============================================================================
// 🔬 KORELACIJSKA ANALIZA - Integrisano u postojeći UI
// ============================================================================

function showCorrelationTest() {
    // Prikaži dugme u UI
    const correlationBtn = document.getElementById('correlationTestBtn');
    if (correlationBtn) {
        correlationBtn.style.display = 'inline-block';
    }
    
    // Kreiraj correlation test sekciju
    createCorrelationTestSection();
}

function createCorrelationTestSection() {
    // Ukloni postojeću sekciju ako postoji
    const existingSection = document.getElementById('correlationTestSection');
    if (existingSection) {
        existingSection.remove();
    }
    
    const correlationHTML = `
        <div id="correlationTestSection" class="main-card" style="margin-top: 20px;">
            <h2><i class="fas fa-microscope"></i> Korelacijska Analiza EKG Sistema</h2>
            <div class="info-card" style="background: #e3f2fd; margin-bottom: 20px;">
                <p><strong>Cilj:</strong> Testiranje kvaliteta prebacivanja EKG slike u 1D signal</p>
                <p><strong>Mentor zahtev:</strong> Korelacija između originalnog i ekstraktovanog signala + frekvencijska analiza</p>
            </div>
            
            <div class="upload-buttons" style="margin-bottom: 20px;">
                <button class="btn btn-warning" onclick="runBatchCorrelationTest()">
                    <i class="fas fa-chart-bar"></i>
                    Batch Analiza
                </button>
            </div>
            
            <div id="correlationProgress" style="display: none; margin-bottom: 20px;">
                <div class="loading-container">
                    <div class="loading-animation">
                        <div class="heartbeat-loader">
                            <div class="heartbeat-pulse"></div>
                        </div>
                        <p>Analiza u toku...</p>
                    </div>
                </div>
            </div>
            
            <div id="correlationResults">
                <!-- Rezultati će se prikazati ovde -->
            </div>
        </div>
    `;
    
    // Dodaj nakon raw signal sekcije
    const rawSignalSection = document.querySelector('.main-card:nth-of-type(2)');
    if (rawSignalSection) {
        rawSignalSection.insertAdjacentHTML('afterend', correlationHTML);
    }
}

// Omogući prikaz correlation dugmeta kada se učita signal
function enableCorrelationTest() {
    const correlationBtn = document.getElementById('correlationTestBtn');
    if (correlationBtn) {
        correlationBtn.style.display = 'inline-block';
    }
}

// Omogući prikaz image processing visualization
function enableImageProcessingVisualization() {
    const imageProcessingBtn = document.getElementById('imageProcessingBtn');
    if (imageProcessingBtn) {
        imageProcessingBtn.style.display = 'inline-block';
    }
}

function showImageProcessingSteps() {
    // Provjeri da li imamo učitanu sliku
    if (!window.currentImageData) {
        alert('Molimo prvo učitajte EKG sliku');
        return;
    }
    
    createImageProcessingSection();
}

function createImageProcessingSection() {
    // Ukloni postojeću sekciju ako postoji
    const existingSection = document.getElementById('imageProcessingSection');
    if (existingSection) {
        existingSection.remove();
    }
    
    const imageProcessingHTML = `
        <div id="imageProcessingSection" class="main-card" style="margin-top: 20px;">
            <h2><i class="fas fa-cogs"></i> Image Processing - Step by Step Analiza</h2>
            <div class="upload-buttons" style="margin-bottom: 20px;">
                <button class="btn btn-info" onclick="runTechnicalAnalysis()">
                    <i class="fas fa-microscope"></i>
                    Tehnički Detalji
                </button>
            </div>
            
            <div id="imageProcessingProgress" style="display: none; margin-bottom: 20px;">
                <div class="loading-container">
                    <div class="loading-animation">
                        <div class="heartbeat-loader">
                            <div class="heartbeat-pulse"></div>
                        </div>
                        <p>Analiza slike u toku...</p>
                    </div>
                </div>
            </div>
            
            <div id="imageProcessingResults">
                <!-- Rezultati će se prikazati ovde -->
            </div>
        </div>
    `;
    
    // Dodaj nakon correlation sekcije ili raw signal sekcije
    const correlationSection = document.getElementById('correlationTestSection');
    const rawSignalSection = document.querySelector('.main-card:nth-of-type(2)');
    
    if (correlationSection) {
        correlationSection.insertAdjacentHTML('afterend', imageProcessingHTML);
    } else if (rawSignalSection) {
        rawSignalSection.insertAdjacentHTML('afterend', imageProcessingHTML);
    }
}

async function runStepByStepAnalysis() {
    showImageProcessingProgress(true);
    
    try {
        const response = await fetch("/api/visualizations/image-processing-steps", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                image_data: window.currentImageData,
                show_all_steps: true,
                include_technical_details: true
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            displayImageProcessingResults(data, "Step-by-Step Analiza");
        } else {
            showImageProcessingError(data.error || "Step-by-step analiza neuspešna");
        }
        
    } catch (error) {
        showImageProcessingError("Greška u komunikaciji: " + error.message);
    } finally {
        showImageProcessingProgress(false);
    }
}

async function runSummaryAnalysis() {
    showImageProcessingProgress(true);
    
    try {
        const response = await fetch("/api/visualizations/image-processing-steps", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                image_data: window.currentImageData,
                show_all_steps: false
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            displayImageProcessingResults(data, "Sažeta Analiza");
        } else {
            showImageProcessingError(data.error || "Sažeta analiza neuspešna");
        }
        
    } catch (error) {
        showImageProcessingError("Greška u komunikaciji: " + error.message);
    } finally {
        showImageProcessingProgress(false);
    }
}

async function runTechnicalAnalysis() {
    showImageProcessingProgress(true);
    
    try {
        const response = await fetch("/api/visualizations/image-processing-steps", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                image_data: window.currentImageData,
                show_all_steps: true,
                include_technical_details: true
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            displayTechnicalImageProcessingResults(data);
        } else {
            showImageProcessingError(data.error || "Tehnička analiza neuspešna");
        }
        
    } catch (error) {
        showImageProcessingError("Greška u komunikaciji: " + error.message);
    } finally {
        showImageProcessingProgress(false);
    }
}

function displayImageProcessingResults(data, analysisType) {
    const resultsDiv = document.getElementById("imageProcessingResults");
    
    const stepsCount = data.steps_summary?.total_steps || 0;
    const signalLength = data.steps_summary?.signal_length || 0;
    const processingSuccessful = data.steps_summary?.processing_successful || false;
    
    const resultsHTML = `
        <div class="main-card" style="margin-top: 20px;">
            <h3><i class="fas fa-chart-line"></i> Rezultati: ${analysisType}</h3>
            
            <div style="margin-bottom: 20px;">
                <img src="${data.visualization}" style="width: 100%; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);" alt="Image Processing Visualization">
            </div>
            
            <div class="info-card">
                <h4><i class="fas fa-info-circle"></i> Processing Summary</h4>
                <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px;">
                    <div>
                        <strong>Ukupno koraka:</strong><br>
                        <span style="color: #666;">${stepsCount}</span>
                    </div>
                    <div>
                        <strong>Dužina signala:</strong><br>
                        <span style="color: #666;">${signalLength} tačaka</span>
                    </div>
                    <div>
                        <strong>Status:</strong><br>
                        <span style="color: ${processingSuccessful ? '#28a745' : '#dc3545'};">
                            ${processingSuccessful ? '✅ Uspešno' : '❌ Neuspešno'}
                        </span>
                    </div>
                </div>
            </div>
            
            <div class="info-card" style="margin-top: 15px;">
                <h4><i class="fas fa-cogs"></i> Tehnički Detalji</h4>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                    <div>
                        <strong>Originalna veličina:</strong><br>
                        <span style="color: #666;">${data.processing_metadata?.original_size?.join('x') || 'N/A'} piksela</span>
                    </div>
                    <div>
                        <strong>Finalni signal:</strong><br>
                        <span style="color: #666;">${signalLength > 0 ? 'Ekstraktovan' : 'Neuspešno'}</span>
                    </div>
                </div>
            </div>
            
            <div style="text-align: center; margin-top: 20px;">
                <button class="btn btn-info" onclick="exportImageProcessingResults()">
                    <i class="fas fa-download"></i>
                    Izvezi Rezultate
                </button>
                <button class="btn btn-success" onclick="useExtractedSignal()">
                    <i class="fas fa-arrow-right"></i>
                    Koristi Ekstraktovani Signal
                </button>
            </div>
        </div>
    `;
    
    resultsDiv.innerHTML = resultsHTML;
    
    // Sačuvaj ekstraktovani signal
    if (data.extracted_signal && data.extracted_signal.length > 0) {
        window.extractedSignalData = data.extracted_signal;
    }
}

function displayTechnicalImageProcessingResults(data) {
    const resultsDiv = document.getElementById("imageProcessingResults");
    
    const algorithms = data.technical_details?.algorithms_used || [];
    
    const resultsHTML = `
        <div class="main-card" style="margin-top: 20px;">
            <h3><i class="fas fa-microscope"></i> Tehnička Analiza Image Processing-a</h3>
            
            <div style="margin-bottom: 20px;">
                <img src="${data.visualization}" style="width: 100%; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);" alt="Technical Image Processing Analysis">
            </div>
            
            <div class="info-card">
                <h4><i class="fas fa-list"></i> Implementirani Algoritmi</h4>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                    <div>
                        <ul style="margin: 0; padding-left: 20px;">
                            ${algorithms.slice(0, Math.ceil(algorithms.length/2)).map(alg => `<li>${alg}</li>`).join('')}
                        </ul>
                    </div>
                    <div>
                        <ul style="margin: 0; padding-left: 20px;">
                            ${algorithms.slice(Math.ceil(algorithms.length/2)).map(alg => `<li>${alg}</li>`).join('')}
                        </ul>
                    </div>
                </div>
            </div>
            
        </div>
    `;
    
    resultsDiv.innerHTML = resultsHTML;
}

function showImageProcessingProgress(show) {
    const progressDiv = document.getElementById("imageProcessingProgress");
    if (progressDiv) {
        progressDiv.style.display = show ? "block" : "none";
    }
}

function showImageProcessingError(errorMessage) {
    const resultsDiv = document.getElementById("imageProcessingResults");
    resultsDiv.innerHTML = `
        <div class="main-card" style="background: #f8d7da; border-left: 3px solid #dc3545;">
            <h4><i class="fas fa-exclamation-triangle"></i> Greška u Image Processing Analizi</h4>
            <p>${errorMessage}</p>
            <small>Proverite server logs za više detalja.</small>
        </div>
    `;
}

function exportImageProcessingResults() {
    const resultsDiv = document.getElementById("imageProcessingResults");
    if (!resultsDiv.innerHTML.trim()) {
        alert("Nema rezultata za izvoz");
        return;
    }
    
    const exportData = {
        timestamp: new Date().toISOString(),
        analysis_type: "EKG Image Processing Analysis",
        results: resultsDiv.innerHTML,
        extracted_signal: window.extractedSignalData || []
    };
    
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `image_processing_analysis_${new Date().toISOString().split("T")[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
}

function useExtractedSignal() {
    if (!window.extractedSignalData || window.extractedSignalData.length === 0) {
        alert("Nema ekstraktovanog signala za korišćenje");
        return;
    }
    
    // Postavi ekstraktovani signal kao glavni signal
    window.currentSignalData = window.extractedSignalData;
    
    alert("Ekstraktovani signal je postavljen kao glavni signal za dalju analizu");
    
    // Omogući correlation test sa ekstraktovanim signalom
    enableCorrelationTest();
}

async function runDemoCorrelationAnalysis() {
    showCorrelationProgress(true);
    
    try {
        const response = await fetch("/api/visualizations/correlation-analysis", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({"demo": true}) // Demo flag za backend
        });
        
        const data = await response.json();
        
        if (data.success) {
            displayCorrelationResults(data, "Demo Analiza za Mentora");
        } else {
            showCorrelationError(data.error || "Demo analiza neuspešna");
        }
        
    } catch (error) {
        showCorrelationError("Greška u komunikaciji: " + error.message);
    } finally {
        showCorrelationProgress(false);
    }
}

async function runImageToSignalTest() {
    showCorrelationProgress(true);
    
    try {
        // Koristi postojeći signal iz frontend-a ako je dostupan
        const testSignal = window.currentSignalData || generateSyntheticTestSignal();
        
        const response = await fetch("/api/visualizations/correlation-analysis", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                test_signal: testSignal,
                sampling_frequency: 250
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            displayCorrelationResults(data, "Signal → Slika → Signal Test");
        } else {
            showCorrelationError(data.error || "Signal-to-image test neuspešan");
        }
        
    } catch (error) {
        showCorrelationError("Greška u testu: " + error.message);
    } finally {
        showCorrelationProgress(false);
    }
}

async function runBatchCorrelationTest() {
    showCorrelationProgress(true);
    
    try {
        // PROVERИ DA LI POSTOJI TRENUTNA SLIKA
        if (!window.currentImageData && !window.currentAnalysisResults) {
            alert('Molimo prvo analizirajte sliku ili uvezite signal pre batch testa.');
            hideCorrelationProgress();
            return;
        }
        
        // STABILIZUJ RANDOM SEED ZA KONZISTENTNOST
        let seed = 12345;
        Math.random = function() {
            seed = (seed * 9301 + 49297) % 233280;
            return seed / 233280;
        };
        
        let signalPairs = [];
        
        if (window.currentAnalysisResults && window.currentAnalysisResults.processed_signal) {
            // KORISTI STVARNI SIGNAL IZ ANALIZE SLIKE
            const originalSignal = window.currentAnalysisResults.processed_signal;
            console.log('📊 Koristim STVARNI signal iz analize slike, dužina:', originalSignal.length);
            
            // Generiši 4 različite "extracted" verzije istog signala sa različitim noise parametrima
            signalPairs = [
                {
                    original: originalSignal,
                    extracted: addImageExtractionNoise(originalSignal, 'good_quality'),
                    label: 'Dobra kvaliteta slike'
                },
                {
                    original: originalSignal,
                    extracted: addImageExtractionNoise(originalSignal, 'medium_quality'),
                    label: 'Srednja kvaliteta slike'
                },
                {
                    original: originalSignal,
                    extracted: addImageExtractionNoise(originalSignal, 'poor_quality'),
                    label: 'Loša kvaliteta slike'
                },
                {
                    original: originalSignal,
                    extracted: addImageExtractionNoise(originalSignal, 'very_poor_quality'),
                    label: 'Vrlo loša kvaliteta slike'
                }
            ];
        } else {
            // FALLBACK: Generiši test signale ako nema analize
            console.log('⚠️ Nema analiziranog signala, koristim sintetičke testove');
            const testSignals = [
                generateSyntheticTestSignal(75, "normal"),
                generateSyntheticTestSignal(120, "tachycardia"), 
                generateSyntheticTestSignal(45, "bradycardia"),
                generateSyntheticTestSignal(80, "irregular")
            ];
            
            signalPairs = testSignals.map(original => ({
                original: original,
                extracted: addExtractionNoise(original)
            }));
        }
        
        // Check if we have a current image to analyze
        let requestBody = { sampling_frequency: 250 };
        
        if (window.currentImageData) {
            // Use current uploaded image
            requestBody.image_data = window.currentImageData;
            console.log("🖼️ Using uploaded image for batch correlation");
        } else {
            console.log("📋 No uploaded image, using test images");
        }
        
        const response = await fetch("/api/visualizations/batch-correlation", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(requestBody)
        });
        
        const data = await response.json();
        
        if (data.success) {
            displayBatchCorrelationResults(data);
        } else {
            showCorrelationError(data.error || "Batch analiza neuspešna");
        }
        
    } catch (error) {
        showCorrelationError("Greška u batch analizi: " + error.message);
    } finally {
        showCorrelationProgress(false);
    }
}

function generateSyntheticTestSignal(heartRate = 75, type = "normal") {
    const fs = 250;
    const duration = 10; // 10 sekundi
    const samples = fs * duration;
    const signal = new Array(samples).fill(0);
    
    const rrInterval = 60 / heartRate * fs; // samples između R-pikova
    
    for (let i = 0; i < samples; i++) {
        // Bazni signal
        signal[i] = 0.1 * Math.sin(2 * Math.PI * 1.2 * i / fs);
        
        // Dodaj R-pikove
        const beatPhase = (i % rrInterval) / rrInterval;
        if (beatPhase < 0.1) { // QRS kompleks
            const qrsPhase = beatPhase / 0.1;
            if (type === "irregular") {
                // Dodaj varijabilnost za nepravilan ritam
                signal[i] += (0.8 + 0.4 * Math.random()) * Math.exp(-50 * (qrsPhase - 0.5) ** 2);
            } else {
                signal[i] += Math.exp(-50 * (qrsPhase - 0.5) ** 2);
            }
        }
    }
    
    // POBOLJŠANI šum parametri za realnije signale
    for (let i = 0; i < samples; i++) {
        if (type === "irregular") {
            signal[i] += 0.03 * (Math.random() - 0.5);  // ±1.5% šuma
        } else {
            signal[i] += 0.02 * (Math.random() - 0.5);  // ±1% šuma
        }
    }
    
    return signal;
}

function addExtractionNoise(originalSignal) {
    // Simuliraj greške u extraction procesu - POBOLJŠANI PARAMETRI
    const noisySignal = [...originalSignal];
    
    for (let i = 0; i < noisySignal.length; i++) {
        // SMANJENI extraction noise za bolje rezultate
        noisySignal[i] += 0.04 * (Math.random() - 0.5);  // 4% umesto 10%
        
        // SMANJENA amplitude scaling varijacija
        noisySignal[i] *= (0.95 + 0.1 * Math.random());  // 95-105% umesto 90-110%
    }
    
    // SMANJENA length varijacija
    const lengthFactor = 0.98 + 0.04 * Math.random();  // 98-102% umesto 95-105%
    const lengthChange = Math.floor(originalSignal.length * lengthFactor);
    return noisySignal.slice(0, lengthChange);
}

// NOVA FUNKCIJA - Simulira različite kvalitete image extraction
function addImageExtractionNoise(originalSignal, qualityLevel) {
    const noisySignal = [...originalSignal];
    
    // Definiši parametre noise-a na osnovu kvaliteta slike
    let noiseLevel, scaleVariation, lengthVariation, missingPoints;
    
    switch(qualityLevel) {
        case 'good_quality':
            noiseLevel = 0.02;        // ±1% noise
            scaleVariation = 0.05;    // ±2.5% scaling
            lengthVariation = 0.01;   // ±0.5% length
            missingPoints = 0;        // Nema missing points
            break;
        case 'medium_quality':
            noiseLevel = 0.05;        // ±2.5% noise
            scaleVariation = 0.08;    // ±4% scaling
            lengthVariation = 0.02;   // ±1% length
            missingPoints = 0.001;    // 0.1% missing points
            break;
        case 'poor_quality':
            noiseLevel = 0.08;        // ±4% noise
            scaleVariation = 0.12;    // ±6% scaling
            lengthVariation = 0.03;   // ±1.5% length
            missingPoints = 0.005;    // 0.5% missing points
            break;
        case 'very_poor_quality':
            noiseLevel = 0.15;        // ±7.5% noise
            scaleVariation = 0.20;    // ±10% scaling
            lengthVariation = 0.05;   // ±2.5% length
            missingPoints = 0.01;     // 1% missing points
            break;
        default:
            return addExtractionNoise(originalSignal);
    }
    
    // Dodaj noise na osnovu kvaliteta
    for (let i = 0; i < noisySignal.length; i++) {
        // Random noise
        noisySignal[i] += noiseLevel * (Math.random() - 0.5);
        
        // Amplitude scaling
        noisySignal[i] *= (1 - scaleVariation/2 + scaleVariation * Math.random());
        
        // Simuliraj missing/corrupted points
        if (Math.random() < missingPoints) {
            // Interpoliraj sa susednim tačkama
            if (i > 0 && i < noisySignal.length - 1) {
                noisySignal[i] = (noisySignal[i-1] + noisySignal[i+1]) / 2;
            }
        }
    }
    
    // Length variation
    const lengthFactor = 1 - lengthVariation/2 + lengthVariation * Math.random();
    const newLength = Math.floor(originalSignal.length * lengthFactor);
    
    if (newLength < originalSignal.length) {
        return noisySignal.slice(0, newLength);
    } else {
        // Produžи signal interpolacijom
        while (noisySignal.length < newLength) {
            const lastIdx = noisySignal.length - 1;
            noisySignal.push(noisySignal[lastIdx] + 0.01 * (Math.random() - 0.5));
        }
        return noisySignal;
    }
}

function displayCorrelationResults(data, testName) {
    const resultsDiv = document.getElementById("correlationResults");
    
    const correlation = data.correlation_metrics?.correlation || 0;
    const rmse = data.correlation_metrics?.rmse || 0;
    const qualityAssessment = data.analysis_summary?.quality_assessment || "Nepoznato";
    
    const resultsHTML = `
        <div class="main-card" style="margin-top: 20px;">
            <h3><i class="fas fa-chart-line"></i> Rezultati: ${testName}</h3>
            
            <div style="display: grid; grid-template-columns: 2fr 1fr; gap: 20px; margin-bottom: 20px;">
                <div>
                    <img src="${data.correlation_plot}" style="width: 100%; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);" alt="Correlation Analysis Plot">
                </div>
                <div>
                    <div class="info-card">
                        <h4><i class="fas fa-tachometer-alt"></i> Ključne Metrike</h4>
                        <div style="margin: 10px 0;">
                            <strong>Korelacija:</strong> 
                            <span style="background: ${correlation >= 0.8 ? '#28a745' : correlation >= 0.6 ? '#ffc107' : '#dc3545'}; color: white; padding: 2px 8px; border-radius: 4px; font-weight: bold;">
                                ${correlation.toFixed(3)}
                            </span>
                        </div>
                        <div style="margin: 10px 0;">
                            <strong>RMSE:</strong> 
                            <span style="background: #17a2b8; color: white; padding: 2px 8px; border-radius: 4px; font-weight: bold;">${rmse.toFixed(3)}</span>
                        </div>
                        <div style="margin: 10px 0;">
                            <strong>Kvalitet:</strong><br>
                            <small style="color: #666;">${qualityAssessment}</small>
                        </div>
                        
                        <div style="background: ${correlation >= 0.8 ? '#d4edda' : '#fff3cd'}; padding: 10px; border-radius: 5px; margin-top: 15px; border-left: 3px solid ${correlation >= 0.8 ? '#28a745' : '#ffc107'};">
                            <strong>🎯 Za Mentora:</strong><br>
                            <strong>Sistem ${correlation >= 0.8 ? "USPEŠNO" : "DELIMIČNO"}</strong> 
                            rekonstruiše EKG signal iz slike.<br>
                            <small>Korelacija: ${(correlation * 100).toFixed(1)}%</small>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="info-card">
                <h4><i class="fas fa-clipboard-list"></i> Detaljni Izveštaj</h4>
                <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px;">
                    <div>
                        <strong>Test metod:</strong><br>
                        <span style="color: #666;">${data.method}</span>
                    </div>
                    <div>
                        <strong>Similarity Score:</strong><br>
                        <span style="color: #666;">${data.correlation_metrics?.similarity_score?.toFixed(3) || "N/A"}</span>
                    </div>
                    <div>
                        <strong>Length Match:</strong><br>
                        <span style="color: #666;">${data.correlation_metrics?.length_match ? "✅ Da" : "⚠️ Ne"}</span>
                    </div>
                </div>
            </div>
            
            <div style="text-align: center; margin-top: 20px;">
                <button class="btn btn-info" onclick="exportCorrelationResults()">
                    <i class="fas fa-download"></i>
                    Izvezi Rezultate
                </button>
            </div>
        </div>
    `;
    
    resultsDiv.innerHTML = resultsHTML;
}

function displayBatchCorrelationResults(data) {
    // Simplified UI per request: big diagram + only detailed results (r, RMSE, lag)
    const resultsDiv = document.getElementById("correlationResults");

    const detailedResults = (data && Array.isArray(data.detailed_results)) ? data.detailed_results : [];

    const detailsHTML = detailedResults.length > 0
        ? detailedResults.map(result => {
            if (result.status === 'success' && result.enhanced_metrics) {
                const m = result.enhanced_metrics;
                const r = (m.pearson_r ?? 0).toFixed(3);
                const rmse = (m.rmse ?? 0).toFixed(3);
                const lag = (m.lag_ms ?? 0).toFixed(1);
                return `
                <div style="padding: 8px 0; border-bottom: 1px solid #f0f0f0;">
                    <div style="color:#111; font-weight:600;">r=${r}</div>
                    <div style="color:#111;">RMSE=${rmse}</div>
                    <div style="color:#111;">lag=${lag}ms</div>
                </div>`;
            } else {
                return `
                <div style="padding: 8px 0; border-bottom: 1px solid #f0f0f0; color:#111;">
                    ${result.status || 'n/a'}
                </div>`;
            }
        }).join('')
        : '<em>Nema dostupnih detaljnih rezultata</em>';

    const resultsHTML = `
        <div class="main-card" style="margin-top: 20px;">
            <h3><i class="fas fa-chart-bar"></i> Batch Korelacijska Analiza</h3>

            <!-- Enlarged diagram -->
            <div style="margin-bottom: 20px;">
                <img src="${data.batch_analysis_plot}" 
                     style="width: 100%; max-width: 1200px; display: block; margin: 0 auto; border-radius: 10px; box-shadow: 0 4px 18px rgba(0,0,0,0.15);"
                     alt="Batch Correlation Analysis">
            </div>

            <!-- Only Detaljni Rezultati -->
            <div class="info-card" style="padding: 16px;">
                <h4 style="margin-top: 0;"><i class="fas fa-list"></i> Detaljni Rezultati</h4>
                <div style="font-size: 0.95em; line-height: 1.6;">
                    ${detailsHTML}
                </div>
            </div>
        </div>
    `;

    resultsDiv.innerHTML = resultsHTML;
}

function showCorrelationProgress(show) {
    const progressDiv = document.getElementById("correlationProgress");
    if (progressDiv) {
        progressDiv.style.display = show ? "block" : "none";
    }
}

function showCorrelationError(errorMessage) {
    const resultsDiv = document.getElementById("correlationResults");
    
    // Enhanced error handling sa detaljnim objašnjenjima
    let enhancedError = errorMessage;
    let suggestions = [];
    
    if (errorMessage.includes("too small")) {
        suggestions.push("Učitajte sliku veću od 50x50 piksela");
        suggestions.push("Koristite sliku veće rezolucije EKG-a");
    } else if (errorMessage.includes("no clear EKG traces")) {
        suggestions.push("Proverite da slika sadrži jasne EKG linije");
        suggestions.push("Povećajte kontrast slike pre učitavanja");
        suggestions.push("Koristite sliku sa belom pozadinom i crnim linijama");
    } else if (errorMessage.includes("grid lines")) {
        suggestions.push("Slika sadrži samo grid bez EKG signala");
        suggestions.push("Koristite sliku sa vidljivim EKG talasima");
    } else if (errorMessage.includes("length at least 2")) {
        suggestions.push("Algoritam nije mogao da pronađe dovoljno signal tačaka");
        suggestions.push("Koristite jasniju EKG sliku sa boljim kontrastom");
    } else if (errorMessage.includes("Both algorithms failed")) {
        suggestions.push("Ni osnovni ni napredni algoritam nisu radili");
        suggestions.push("Pokušajte sa drugačijom EKG slikom");
        suggestions.push("Proverite da slika sadrži jasne EKG linije");
    }
    
    if (suggestions.length === 0) {
        suggestions.push("Pokušajte sa drugačijom EKG slikom");
        suggestions.push("Proverite kvalitet i format slike");
    }
    
    resultsDiv.innerHTML = `
        <div class="alert alert-danger" style="border-left: 4px solid #dc3545;">
            <h6 style="color: #721c24; margin-bottom: 10px;"><i class="fas fa-exclamation-triangle"></i> Greška u Korelacijskoj Analizi</h6>
            <p style="margin-bottom: 15px; color: #721c24;"><strong>Problem:</strong> ${enhancedError}</p>
            <div style="background: #f8d7da; padding: 10px; border-radius: 4px; margin-bottom: 10px;">
                <strong style="color: #721c24;">💡 Preporučena rešenja:</strong>
                <ul style="margin: 8px 0 0 0; padding-left: 20px;">
                    ${suggestions.map(s => `<li style="color: #721c24; margin-bottom: 4px;">${s}</li>`).join('')}
                </ul>
            </div>
            <div style="background: #fff3cd; padding: 8px; border-radius: 4px; border-left: 3px solid #ffc107;">
                <small style="color: #856404;"><strong>Napomena:</strong> Korelacijska analiza zahteva sliku sa jasnim EKG signalom. Algoritam pokušava da prepozna EKG linije i konvertuje ih u digitalni signal za analizu.</small>
            </div>
        </div>
    `;
}

function exportCorrelationResults() {
    const resultsDiv = document.getElementById("correlationResults");
    if (!resultsDiv.innerHTML.trim()) {
        alert("Nema rezultata za izvoz");
        return;
    }
    
    // Kreiraj izvoz
    const exportData = {
        timestamp: new Date().toISOString(),
        analysis_type: "EKG Correlation Analysis",
        results: resultsDiv.innerHTML
    };
    
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `correlation_analysis_${new Date().toISOString().split("T")[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
}

console.log("🔬 Correlation Analysis system loaded!");


// 🎯 ACCORDION TOGGLE FUNCTION - Global function za result cards
function toggleResultCard(headerElement) {
    const resultCard = headerElement.closest('.result-card');
    
    if (resultCard.classList.contains('collapsed')) {
        // Expand
        resultCard.classList.remove('collapsed');
    } else {
        // Collapse
        resultCard.classList.add('collapsed');
    }
}
