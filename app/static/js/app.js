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

        // Add enhanced header for WFDB
        const resultsSection = document.getElementById('resultsSection');
        const existingHeader = resultsSection.querySelector('.wfdb-header');
        if (existingHeader) {
            existingHeader.remove();
        }

        const headerDiv = document.createElement('div');
        headerDiv.className = 'wfdb-header';
        headerDiv.innerHTML = `
            <div style="background: #e3f2fd; padding: 15px; border-radius: 10px; margin-bottom: 20px; border-left: 4px solid #2196f3;">
                <h3 style="margin: 0 0 10px 0;"><i class="fas fa-database"></i> WFDB MIT-BIH Analiza</h3>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                    <div><strong>📁 Record:</strong> ${data.signal_info.filename || 'Unknown'}</div>
                    <div><strong>📊 Samples:</strong> ${data.signal_info.length.toLocaleString()}</div>
                    <div><strong>⏱️ Duration:</strong> ${data.signal_info.duration_seconds.toFixed(1)}s</div>
                    <div><strong>📡 Fs:</strong> ${data.signal_info.sampling_frequency} Hz</div>
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
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.ekgAnalyzer = new EKGAnalyzer();
});