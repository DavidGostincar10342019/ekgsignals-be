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
            this.toggleRawSignalInfo();
            document.getElementById('rawSignalInput').click();
        });

        // Raw signal file input
        document.getElementById('rawSignalInput').addEventListener('change', (e) => {
            if (e.target.files.length > 1) {
                // Multiple files - možda WFDB format
                this.handleWFDBFiles(e.target.files);
            } else {
                // Single file - CSV/TXT/JSON
                this.handleRawSignalFile(e.target.files[0]);
            }
        });

        // Analyze button
        document.getElementById('analyzeBtn').addEventListener('click', () => {
            this.analyzeImage();
        });

        // New analysis button
        document.getElementById('newAnalysisBtn').addEventListener('click', () => {
            this.resetApp();
        });

        // Generate EKG Image button (will be added dynamically)
        document.addEventListener('click', (e) => {
            if (e.target && e.target.id === 'generateEkgImageBtn') {
                this.generateEducationalEkgImage();
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
        if (!this.currentImage || this.isProcessing) return;

        this.isProcessing = true;
        this.showUploadProgress();

        try {
            // Convert image to base64 with progress
            const base64Image = await this.fileToBase64WithProgress(this.currentImage);
            
            // Update progress for upload
            this.updateProgress(50, 'Šalje sliku na server...', '📤');
            
            // Send to complete analysis API
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

    displayResults(data) {
        // Hide processing
        document.getElementById('processingSection').style.display = 'none';
        
        // Show results
        const resultsSection = document.getElementById('resultsSection');
        resultsSection.style.display = 'block';

        // Store data for detailed analysis
        this.analysisData = data;

        // Populate structured results
        if (data.advanced_cardiology && !data.advanced_cardiology.error) {
            console.log('✅ Using advanced cardiology analysis');
            this.populateAdvancedCardiologyResults(data);
        } else {
            console.log('⚠️ Using basic structured results');
            this.populateStructuredResults(data);
        }
        
        // NOVO: Dodaj vizuelizacije za master rad (bez kvarenja postojeće logike)
        if (data.thesis_visualizations && !data.thesis_visualizations.error) {
            console.log('📊 Adding thesis visualizations');
            this.addThesisVisualizations(data.thesis_visualizations);
        }

        // Scroll to results
        resultsSection.scrollIntoView({ behavior: 'smooth' });
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
            if (!document.getElementById('generateEkgImageBtn')) {
                const generateBtn = document.createElement('button');
                generateBtn.id = 'generateEkgImageBtn';
                generateBtn.className = 'btn btn-primary';
                generateBtn.innerHTML = '<i class="fas fa-image"></i> Generiši EKG Sliku';
                generateBtn.style.margin = '5px';
                
                actionButtonsContainer.appendChild(generateBtn);
                console.log('✅ Generate EKG image button added');
            }
        }
    }

    // Generate EKG image from raw signal data
    async generateEducationalEkgImage() {
        if (!this.analysisData || !this.analysisData.signal_info) {
            this.showError('Nema dostupnih podataka za generisanje slike');
            return;
        }

        try {
            this.showUploadProgress();
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
                this.hideUploadProgress();
                this.displayGeneratedImage(result);
            }, 500);

        } catch (error) {
            console.error('Image generation error:', error);
            this.hideUploadProgress();
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
            this.showUploadProgress();
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
                this.hideUploadProgress();
                // Show comparison results
                this.displayImageAnalysisComparison(result);
            }, 500);

        } catch (error) {
            console.error('Generated image analysis error:', error);
            this.hideUploadProgress();
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
            <div class="result-card">
                <div class="result-header">
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
            <div class="result-card">
                <div class="result-header">
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
            <div class="result-card">
                <div class="result-header">
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
            <div class="result-card">
                <div class="result-header">
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
            <div class="result-card">
                <div class="result-header">
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
            <div class="result-card">
                <div class="result-header">
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
            <div class="result-card">
                <div class="result-header">
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
                <button id="newAnalysisBtn" class="btn btn-secondary">
                    <i class="fas fa-plus"></i>
                    Nova Analiza
                </button>
                <button id="shareBtn" class="btn btn-secondary" onclick="shareResults()">
                    <i class="fas fa-share-alt"></i>
                    Podeli Rezultate
                </button>
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
                <button id="newAnalysisBtn" class="btn btn-secondary">
                    <i class="fas fa-plus"></i> Nova Analiza
                </button>
                <button onclick="window.print()" class="btn btn-secondary">
                    <i class="fas fa-print"></i> Štampaj Izveštaj
                </button>
            </div>
        `;

        resultsSection.innerHTML = advancedHTML;
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
    addThesisVisualizations(visualizations) {
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

        // Dugme za export
        visualizationsHTML += `
            <div class="action-buttons" style="margin-top: 20px; text-align: center;">
                <button id="exportThesisReport" class="btn btn-primary" style="margin: 5px;">
                    <i class="fas fa-file-pdf"></i> Export Report za Master Rad
                </button>
                <button onclick="window.print()" class="btn btn-secondary" style="margin: 5px;">
                    <i class="fas fa-print"></i> Štampaj Vizuelizacije
                </button>
            </div>
        `;

        vizSection.innerHTML = visualizationsHTML;
        
        // Add event listener for export
        const exportBtn = document.getElementById('exportThesisReport');
        if (exportBtn) {
            exportBtn.onclick = () => this.exportThesisReport();
        }

        vizSection.style.display = 'block';
        console.log('📊 Thesis visualizations added to page');
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
        console.log('🐛 DEBUG: Testing visualizations...');
        console.log('Analysis data:', this.analysisData);
        
        if (this.analysisData && this.analysisData.thesis_visualizations) {
            console.log('✅ thesis_visualizations postoje:', this.analysisData.thesis_visualizations);
            console.log('Keys:', Object.keys(this.analysisData.thesis_visualizations));
            
            if (this.analysisData.thesis_visualizations.error) {
                console.log('❌ Error u vizuelizacijama:', this.analysisData.thesis_visualizations.error);
                alert('Error: ' + this.analysisData.thesis_visualizations.error);
            } else {
                console.log('🎯 Pokušavam da dodam vizuelizacije...');
                this.addThesisVisualizations(this.analysisData.thesis_visualizations);
                alert('✅ Vizuelizacije dodane! Skroluj dole da ih vidiš.');
            }
        } else {
            console.log('❌ Nema thesis_visualizations u analysis data');
            alert('❌ Nema thesis_visualizations podataka. Backend možda ne generiše vizuelizacije.');
        }
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

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.ekgAnalyzer = new EKGAnalyzer();
});