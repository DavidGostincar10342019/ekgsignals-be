// EKG Analiza - Jednostavna verzija koja radi
console.log('Loading EKG Analyzer...');

// Jednostavna klasa za EKG analizu
class SimpleEKGAnalyzer {
    constructor() {
        this.currentImage = null;
        this.isProcessing = false;
        console.log('SimpleEKGAnalyzer created');
    }

    handleFileSelect(file) {
        if (!file) return;

        // Validate file type
        if (!file.type.startsWith('image/')) {
            alert('Molimo odaberite sliku (JPG, PNG, itd.)');
            return;
        }

        // Validate file size (max 10MB)
        if (file.size > 10 * 1024 * 1024) {
            alert('Slika je prevelika. Maksimalna veličina je 10MB.');
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

            if (previewImage && previewSection) {
                previewImage.src = e.target.result;
                previewSection.style.display = 'block';

                // Show image info
                if (imageInfo) {
                    const fileSize = (file.size / 1024).toFixed(1);
                    imageInfo.innerHTML = `
                        <strong>📁 Naziv:</strong> ${file.name}<br>
                        <strong>📏 Veličina:</strong> ${fileSize} KB<br>
                        <strong>📅 Tip:</strong> ${file.type}
                    `;
                }

                // Enable analyze button
                const analyzeBtn = document.getElementById('analyzeBtn');
                if (analyzeBtn) {
                    analyzeBtn.disabled = false;
                }
                
                console.log('Image preview displayed');
            }
        };
        reader.readAsDataURL(file);
    }

    async analyzeImage() {
        if (!this.currentImage || this.isProcessing) return;

        this.isProcessing = true;
        console.log('Starting analysis...');

        try {
            // Show processing
            this.showProcessing();
            
            // Convert image to base64
            const base64Image = await this.fileToBase64(this.currentImage);
            
            // Send to API
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

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            
            if (result.error) {
                throw new Error(result.error);
            }

            this.displayResults(result);
            
        } catch (error) {
            console.error('Analysis error:', error);
            alert(`Greška pri analizi: ${error.message}`);
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

    showProcessing() {
        const uploadSection = document.getElementById('uploadSection');
        const processingSection = document.getElementById('processingSection');
        
        if (uploadSection) uploadSection.style.display = 'none';
        if (processingSection) processingSection.style.display = 'block';
    }

    hideProcessing() {
        const uploadSection = document.getElementById('uploadSection');
        const processingSection = document.getElementById('processingSection');
        
        if (uploadSection) uploadSection.style.display = 'block';
        if (processingSection) processingSection.style.display = 'none';
    }

    displayResults(data) {
        this.hideProcessing();
        
        const resultsSection = document.getElementById('resultsSection');
        if (resultsSection) {
            resultsSection.style.display = 'block';
            resultsSection.scrollIntoView({ behavior: 'smooth' });
        }

        // Populate basic results
        this.populateSignalInfo(data.signal_info);
        this.populateHeartRateInfo(data.arrhythmia_detection?.heart_rate);
        this.populateArrhythmias(data.arrhythmia_detection?.arrhythmias);
        
        console.log('Results displayed');
    }

    populateSignalInfo(signalInfo) {
        if (!signalInfo) return;
        
        const elements = {
            'signalLength': signalInfo.length,
            'signalDuration': `${signalInfo.duration_seconds.toFixed(1)}s`,
            'samplingRate': `${signalInfo.sampling_frequency} Hz`
        };

        for (const [id, value] of Object.entries(elements)) {
            const element = document.getElementById(id);
            if (element) element.textContent = value;
        }
    }

    populateHeartRateInfo(heartRate) {
        if (!heartRate) return;

        const elements = {
            'avgBPM': `${heartRate.average_bpm.toFixed(1)} bpm`,
            'minBPM': `${heartRate.min_bpm.toFixed(1)} bpm`,
            'maxBPM': `${heartRate.max_bpm.toFixed(1)} bpm`,
            'hrv': `${heartRate.heart_rate_variability.toFixed(1)} ms`,
            'rPeaks': heartRate.rr_count || 0
        };

        for (const [id, value] of Object.entries(elements)) {
            const element = document.getElementById(id);
            if (element) element.textContent = value;
        }
    }

    populateArrhythmias(arrhythmias) {
        const container = document.getElementById('arrhythmiasList');
        if (!container) return;
        
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

    resetApp() {
        this.currentImage = null;
        this.isProcessing = false;

        // Hide sections
        const sections = ['imagePreview', 'processingSection', 'resultsSection'];
        sections.forEach(id => {
            const element = document.getElementById(id);
            if (element) element.style.display = 'none';
        });

        // Show upload section
        const uploadSection = document.getElementById('uploadSection');
        if (uploadSection) uploadSection.style.display = 'block';

        // Reset buttons
        const analyzeBtn = document.getElementById('analyzeBtn');
        if (analyzeBtn) analyzeBtn.disabled = true;

        // Reset file inputs
        const inputs = ['fileInput', 'cameraInput', 'rawSignalInput'];
        inputs.forEach(id => {
            const element = document.getElementById(id);
            if (element) element.value = '';
        });

        console.log('App reset');
    }
}

// Setup drag and drop
function setupDragAndDrop() {
    const uploadArea = document.getElementById('uploadArea');
    if (!uploadArea) return;
    
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, preventDefaults, false);
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
        if (files.length > 0 && window.ekgAnalyzer) {
            window.ekgAnalyzer.handleFileSelect(files[0]);
        }
    }, false);
}

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

// Jednostavno postavljanje dugmića
function setupButtons() {
    console.log('Setting up buttons...');

    // Upload button
    const uploadBtn = document.getElementById('uploadBtn');
    if (uploadBtn) {
        uploadBtn.onclick = function() {
            console.log('Upload button clicked');
            const fileInput = document.getElementById('fileInput');
            if (fileInput) {
                fileInput.click();
            }
        };
        console.log('Upload button setup complete');
    }

    // Camera button
    const cameraBtn = document.getElementById('cameraBtn');
    if (cameraBtn) {
        cameraBtn.onclick = function() {
            console.log('Camera button clicked');
            const cameraInput = document.getElementById('cameraInput');
            if (cameraInput) {
                cameraInput.click();
            }
        };
        console.log('Camera button setup complete');
    }

    // Raw signal button
    const rawSignalBtn = document.getElementById('rawSignalBtn');
    if (rawSignalBtn) {
        rawSignalBtn.onclick = function() {
            console.log('Raw signal button clicked');
            const rawSignalInput = document.getElementById('rawSignalInput');
            if (rawSignalInput) {
                rawSignalInput.click();
            }
        };
        console.log('Raw signal button setup complete');
    }

    // Analyze button
    const analyzeBtn = document.getElementById('analyzeBtn');
    if (analyzeBtn) {
        analyzeBtn.onclick = function() {
            if (window.ekgAnalyzer) {
                window.ekgAnalyzer.analyzeImage();
            }
        };
        console.log('Analyze button setup complete');
    }

    // New analysis button
    const newAnalysisBtn = document.getElementById('newAnalysisBtn');
    if (newAnalysisBtn) {
        newAnalysisBtn.onclick = function() {
            if (window.ekgAnalyzer) {
                window.ekgAnalyzer.resetApp();
            }
        };
        console.log('New analysis button setup complete');
    }

    // File inputs
    const fileInput = document.getElementById('fileInput');
    if (fileInput) {
        fileInput.onchange = function(e) {
            if (e.target.files[0] && window.ekgAnalyzer) {
                console.log('File selected:', e.target.files[0].name);
                window.ekgAnalyzer.handleFileSelect(e.target.files[0]);
            }
        };
    }

    const cameraInput = document.getElementById('cameraInput');
    if (cameraInput) {
        cameraInput.onchange = function(e) {
            if (e.target.files[0] && window.ekgAnalyzer) {
                console.log('Camera file selected:', e.target.files[0].name);
                window.ekgAnalyzer.handleFileSelect(e.target.files[0]);
            }
        };
    }

    const rawSignalInput = document.getElementById('rawSignalInput');
    if (rawSignalInput) {
        rawSignalInput.onchange = function(e) {
            if (e.target.files[0]) {
                console.log('Raw signal file selected:', e.target.files[0].name);
                alert('Raw signal functionality: ' + e.target.files[0].name);
            }
        };
    }

    console.log('All buttons setup complete');
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, initializing...');
    
    // Setup buttons first
    setupButtons();
    
    // Setup drag and drop
    setupDragAndDrop();
    
    // Create analyzer instance
    window.ekgAnalyzer = new SimpleEKGAnalyzer();
    
    console.log('Initialization complete');
});

console.log('EKG Analyzer script loaded');