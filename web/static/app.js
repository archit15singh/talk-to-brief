/**
 * Audio Recording Web Application
 * 
 * This JavaScript application provides a complete browser-based audio recording
 * interface for the Audio Brief Generator system. It handles microphone access,
 * audio recording, file upload, and real-time progress tracking.
 * 
 * Key Features:
 * - Browser-based audio recording using MediaRecorder API
 * - Real-time recording duration display
 * - Automatic file upload after recording
 * - WebSocket-based progress tracking
 * - Comprehensive error handling and user feedback
 * - Browser compatibility checking
 * - Network status monitoring
 * - Brief management and download
 * 
 * Architecture:
 * - AudioRecorder: Main recording functionality
 * - StatusUpdater: WebSocket communication and progress display
 * - BriefManager: Brief listing and download management
 * - NetworkMonitor: Connection status and health checking
 * 
 * Browser Support:
 * - Chrome 47+: Full support (recommended)
 * - Firefox 29+: Full support
 * - Safari 14+: Full support
 * - Edge 79+: Full support
 * 
 * Dependencies:
 * - MediaRecorder API: For audio recording
 * - WebSocket API: For real-time updates
 * - Fetch API: For HTTP requests
 * - File API: For file handling
 * 
 * Author: Audio Brief Generator Team
 * Version: 1.0.0
 */

/**
 * Main AudioRecorder class that handles all recording functionality
 * 
 * This class manages the complete recording workflow from microphone access
 * to file upload and processing initiation. It provides a clean interface
 * for browser-based audio recording with comprehensive error handling.
 * 
 * Key Responsibilities:
 * - Microphone permission management
 * - Audio recording using MediaRecorder API
 * - Real-time recording duration display
 * - File upload to server
 * - Integration with progress tracking
 * - Error handling and user feedback
 * 
 * State Management:
 * - isRecording: Current recording state
 * - mediaRecorder: MediaRecorder instance
 * - audioChunks: Recorded audio data
 * - stream: MediaStream from microphone
 * - currentJob: Active processing job ID
 * 
 * Event Handling:
 * - User interface events (start/stop buttons)
 * - MediaRecorder events (dataavailable, stop)
 * - Network and error events
 * - WebSocket events via StatusUpdater
 */
class AudioRecorder {
    constructor() {
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.stream = null;
        this.isRecording = false;
        this.startTime = null;
        this.timerInterval = null;
        this.currentJob = null;
        this.statusUpdater = null;
        this.networkStatus = 'online';
        this.lastNetworkCheck = null;
        
        this.initializeElements();
        this.bindEvents();
        this.setupNetworkMonitoring();
        this.checkBrowserSupport();
        this.performInitialHealthCheck();
    }
    
    initializeElements() {
        this.startBtn = document.getElementById('startBtn');
        this.stopBtn = document.getElementById('stopBtn');
        this.statusIndicator = document.getElementById('statusIndicator');
        this.statusDot = this.statusIndicator.querySelector('.status-dot');
        this.statusText = this.statusIndicator.querySelector('.status-text');
        this.recordingTimer = document.getElementById('recordingTimer');
        this.errorContainer = document.getElementById('errorContainer');
        this.errorText = document.getElementById('errorText');
        this.errorClose = document.getElementById('errorClose');
    }
    
    bindEvents() {
        this.startBtn.addEventListener('click', () => this.startRecording());
        this.stopBtn.addEventListener('click', () => this.stopRecording());
        this.errorClose.addEventListener('click', () => this.hideError());
    }
    
    checkBrowserSupport() {
        const compatibility = this.getBrowserCompatibility();
        
        if (!compatibility.isSupported) {
            this.showError(compatibility.message, 'error', true);
            this.startBtn.disabled = true;
            this.displayCompatibilityInfo(compatibility);
            return false;
        }
        
        if (compatibility.warnings.length > 0) {
            compatibility.warnings.forEach(warning => {
                this.showError(warning, 'warning', false);
            });
        }
        
        return true;
    }
    
    getBrowserCompatibility() {
        const result = {
            isSupported: true,
            message: '',
            warnings: [],
            features: {
                mediaDevices: !!navigator.mediaDevices,
                getUserMedia: !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia),
                mediaRecorder: !!window.MediaRecorder,
                webSocket: !!window.WebSocket,
                socketIO: !!window.io,
                fileAPI: !!(window.File && window.FileReader && window.FileList && window.Blob),
                fetch: !!window.fetch,
                promises: !!window.Promise
            }
        };
        
        // Check critical features
        if (!result.features.mediaDevices || !result.features.getUserMedia) {
            result.isSupported = false;
            result.message = 'Your browser does not support audio recording. Please use a modern browser like Chrome 47+, Firefox 29+, Safari 11+, or Edge 79+.';
            return result;
        }
        
        if (!result.features.mediaRecorder) {
            result.isSupported = false;
            result.message = 'MediaRecorder API is not supported in your browser. Please update to a newer version.';
            return result;
        }
        
        if (!result.features.fetch) {
            result.isSupported = false;
            result.message = 'Your browser is too old and missing required features. Please update your browser.';
            return result;
        }
        
        // Check for warnings
        if (!result.features.webSocket) {
            result.warnings.push('WebSocket not supported. Real-time updates may not work properly.');
        }
        
        if (!result.features.socketIO) {
            result.warnings.push('Socket.IO library not loaded. Real-time updates will use fallback polling.');
        }
        
        // Check for HTTPS requirement
        if (location.protocol !== 'https:' && location.hostname !== 'localhost' && location.hostname !== '127.0.0.1') {
            result.warnings.push('Audio recording requires HTTPS on non-localhost domains. Some features may not work.');
        }
        
        // Check for specific browser limitations
        const userAgent = navigator.userAgent.toLowerCase();
        if (userAgent.includes('safari') && !userAgent.includes('chrome')) {
            // Safari-specific checks
            if (!MediaRecorder.isTypeSupported('audio/webm')) {
                result.warnings.push('Safari detected: Some audio formats may not be supported.');
            }
        }
        
        return result;
    }
    
    displayCompatibilityInfo(compatibility) {
        const compatibilityHtml = `
            <div class="compatibility-info">
                <h3>Browser Compatibility Issue</h3>
                <p>${compatibility.message}</p>
                <div class="feature-support">
                    <h4>Feature Support:</h4>
                    <ul>
                        <li class="${compatibility.features.mediaDevices ? 'supported' : 'unsupported'}">
                            Media Devices API: ${compatibility.features.mediaDevices ? '✓' : '✗'}
                        </li>
                        <li class="${compatibility.features.getUserMedia ? 'supported' : 'unsupported'}">
                            getUserMedia: ${compatibility.features.getUserMedia ? '✓' : '✗'}
                        </li>
                        <li class="${compatibility.features.mediaRecorder ? 'supported' : 'unsupported'}">
                            MediaRecorder: ${compatibility.features.mediaRecorder ? '✓' : '✗'}
                        </li>
                        <li class="${compatibility.features.webSocket ? 'supported' : 'unsupported'}">
                            WebSocket: ${compatibility.features.webSocket ? '✓' : '✗'}
                        </li>
                        <li class="${compatibility.features.fetch ? 'supported' : 'unsupported'}">
                            Fetch API: ${compatibility.features.fetch ? '✓' : '✗'}
                        </li>
                    </ul>
                </div>
                <div class="browser-recommendations">
                    <h4>Recommended Browsers:</h4>
                    <ul>
                        <li>Chrome 47+ (recommended)</li>
                        <li>Firefox 29+</li>
                        <li>Safari 11+</li>
                        <li>Edge 79+</li>
                    </ul>
                </div>
            </div>
        `;
        
        const resultsContainer = document.getElementById('resultsContainer');
        if (resultsContainer) {
            resultsContainer.innerHTML = compatibilityHtml;
        }
    }
    
    async startRecording() {
        try {
            this.hideError();
            
            // Request microphone permission
            this.stream = await navigator.mediaDevices.getUserMedia({ 
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    sampleRate: 44100
                } 
            });
            
            // Initialize MediaRecorder
            const options = {
                mimeType: this.getSupportedMimeType(),
                audioBitsPerSecond: 128000
            };
            
            this.mediaRecorder = new MediaRecorder(this.stream, options);
            this.audioChunks = [];
            
            // Set up event handlers
            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.audioChunks.push(event.data);
                }
            };
            
            this.mediaRecorder.onstop = () => {
                this.handleRecordingStop();
            };
            
            this.mediaRecorder.onerror = (event) => {
                this.showError(`Recording error: ${event.error}`);
                this.resetRecordingState();
            };
            
            // Start recording
            this.mediaRecorder.start(1000); // Collect data every second
            this.isRecording = true;
            this.startTime = Date.now();
            
            // Update UI
            this.updateRecordingUI(true);
            this.startTimer();
            
        } catch (error) {
            this.handleRecordingError(error);
        }
    }
    
    stopRecording() {
        if (this.mediaRecorder && this.isRecording) {
            this.mediaRecorder.stop();
            this.isRecording = false;
            
            // Stop all tracks
            if (this.stream) {
                this.stream.getTracks().forEach(track => track.stop());
            }
            
            this.stopTimer();
            this.updateRecordingUI(false);
        }
    }
    
    handleRecordingStop() {
        if (this.audioChunks.length === 0) {
            this.showError('No audio data recorded. Please try again.');
            this.resetRecordingState();
            return;
        }
        
        // Create audio blob
        const audioBlob = new Blob(this.audioChunks, { 
            type: this.getSupportedMimeType() 
        });
        
        // Upload the audio file
        this.uploadAudio(audioBlob);
    }
    
    async uploadAudio(audioBlob) {
        try {
            // Update progress
            this.updateProgressStep('uploadStep', 'active', 'Preparing upload...');
            
            // Check network connectivity
            await this.checkNetworkBeforeUpload();
            
            // Validate audio blob
            if (!audioBlob || audioBlob.size === 0) {
                throw new Error('No audio data to upload');
            }
            
            // Check file size (100MB limit)
            const maxSize = 100 * 1024 * 1024; // 100MB
            if (audioBlob.size > maxSize) {
                throw new Error(`Audio file is too large (${Math.round(audioBlob.size / 1024 / 1024)}MB). Maximum size is 100MB.`);
            }
            
            // Validate audio format
            const supportedTypes = ['audio/webm', 'audio/mp4', 'audio/wav', 'audio/ogg'];
            if (!supportedTypes.some(type => audioBlob.type.includes(type.split('/')[1]))) {
                this.showError(`Audio format ${audioBlob.type} may not be supported. Proceeding anyway...`, 'warning');
            }
            
            // Create form data
            const formData = new FormData();
            const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
            const filename = `recording_${timestamp}.wav`;
            formData.append('audio', audioBlob, filename);
            
            // Update progress
            this.updateProgressStep('uploadStep', 'active', 'Uploading audio...');
            
            // Upload to server with progress tracking
            const response = await this.uploadWithProgress(formData);
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.error || `Upload failed: ${response.statusText}`);
            }
            
            const result = await response.json();
            
            // Update progress
            this.updateProgressStep('uploadStep', 'completed', 'Audio uploaded successfully');
            
            // Store current job info
            this.currentJob = {
                jobId: result.job_id,
                filename: result.filename,
                startTime: new Date()
            };
            
            // Start monitoring pipeline progress
            if (result.job_id) {
                this.monitorPipelineProgress(result.job_id);
            } else {
                throw new Error('No job ID returned from server');
            }
            
        } catch (error) {
            console.error('Upload error:', error);
            this.updateProgressStep('uploadStep', 'error', `Upload failed: ${error.message}`);
            this.showError(`Failed to upload audio: ${error.message}`);
            this.resetRecordingState();
        }
    }
    
    async uploadWithProgress(formData, retryCount = 0) {
        const maxRetries = 3;
        const retryDelay = Math.pow(2, retryCount) * 1000; // Exponential backoff
        
        return new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest();
            
            // Track upload progress
            xhr.upload.addEventListener('progress', (event) => {
                if (event.lengthComputable) {
                    const percentComplete = (event.loaded / event.total) * 100;
                    const retryText = retryCount > 0 ? ` (Retry ${retryCount}/${maxRetries})` : '';
                    this.updateProgressStep('uploadStep', 'active', 
                        `Uploading... ${Math.round(percentComplete)}%${retryText}`);
                }
            });
            
            // Handle completion
            xhr.addEventListener('load', () => {
                if (xhr.status >= 200 && xhr.status < 300) {
                    resolve({
                        ok: true,
                        status: xhr.status,
                        json: () => Promise.resolve(JSON.parse(xhr.responseText))
                    });
                } else {
                    const errorResponse = {
                        ok: false,
                        status: xhr.status,
                        statusText: xhr.statusText,
                        json: () => {
                            try {
                                return Promise.resolve(JSON.parse(xhr.responseText));
                            } catch (e) {
                                return Promise.resolve({ error: xhr.statusText });
                            }
                        }
                    };
                    
                    // Retry on server errors (5xx) but not client errors (4xx)
                    if (xhr.status >= 500 && retryCount < maxRetries) {
                        console.log(`Server error ${xhr.status}, retrying in ${retryDelay}ms...`);
                        setTimeout(() => {
                            this.uploadWithProgress(formData, retryCount + 1)
                                .then(resolve)
                                .catch(reject);
                        }, retryDelay);
                    } else {
                        resolve(errorResponse);
                    }
                }
            });
            
            // Handle network errors
            xhr.addEventListener('error', () => {
                if (retryCount < maxRetries) {
                    console.log(`Network error, retrying in ${retryDelay}ms...`);
                    this.updateProgressStep('uploadStep', 'active', 
                        `Network error, retrying in ${Math.ceil(retryDelay/1000)}s... (${retryCount + 1}/${maxRetries})`);
                    
                    setTimeout(() => {
                        this.uploadWithProgress(formData, retryCount + 1)
                            .then(resolve)
                            .catch(reject);
                    }, retryDelay);
                } else {
                    reject(new Error('Network error during upload after multiple retries'));
                }
            });
            
            // Handle timeout
            xhr.addEventListener('timeout', () => {
                if (retryCount < maxRetries) {
                    console.log(`Upload timeout, retrying in ${retryDelay}ms...`);
                    this.updateProgressStep('uploadStep', 'active', 
                        `Upload timeout, retrying in ${Math.ceil(retryDelay/1000)}s... (${retryCount + 1}/${maxRetries})`);
                    
                    setTimeout(() => {
                        this.uploadWithProgress(formData, retryCount + 1)
                            .then(resolve)
                            .catch(reject);
                    }, retryDelay);
                } else {
                    reject(new Error('Upload timeout after multiple retries'));
                }
            });
            
            // Configure and send request
            xhr.open('POST', '/api/upload-audio');
            xhr.timeout = 300000; // 5 minute timeout
            xhr.send(formData);
        });
    }
    
    async monitorPipelineProgress(jobId) {
        // Use StatusUpdater to monitor pipeline progress via WebSocket
        if (window.statusUpdater) {
            window.statusUpdater.startMonitoring(jobId);
        } else {
            console.error('StatusUpdater not available for monitoring');
            // Fallback to polling if WebSocket is not available
            this.startPollingJobStatus(jobId);
        }
    }
    
    // Fallback polling method for job status
    async startPollingJobStatus(jobId) {
        const pollInterval = 2000; // Poll every 2 seconds
        const maxPolls = 150; // Maximum 5 minutes of polling
        let pollCount = 0;
        
        const poll = async () => {
            try {
                const response = await fetch(`/api/status/${jobId}`);
                if (!response.ok) {
                    throw new Error(`Failed to get job status: ${response.statusText}`);
                }
                
                const jobData = await response.json();
                this.handleJobStatusUpdate(jobData);
                
                // Continue polling if job is still running
                if (jobData.status === 'running' && pollCount < maxPolls) {
                    pollCount++;
                    setTimeout(poll, pollInterval);
                } else if (pollCount >= maxPolls) {
                    this.showError('Job monitoring timeout. Please check the results manually.');
                }
                
            } catch (error) {
                console.error('Error polling job status:', error);
                if (pollCount < 3) { // Retry a few times
                    pollCount++;
                    setTimeout(poll, pollInterval);
                } else {
                    this.showError('Failed to monitor job progress. Please check the results manually.');
                }
            }
        };
        
        // Start polling
        setTimeout(poll, pollInterval);
    }
    
    // Handle job status updates (for polling fallback)
    handleJobStatusUpdate(jobData) {
        const { status, current_step, progress, error_message } = jobData;
        
        if (status === 'completed') {
            this.handleJobCompleted(jobData);
        } else if (status === 'failed') {
            this.handleJobFailed(jobData);
        } else if (current_step) {
            // Update progress based on current step
            this.updateProgressForStep(current_step, progress);
        }
    }
    
    updateProgressForStep(step, progress) {
        switch (step) {
            case 'validation':
                this.updateProgressStep('uploadStep', 'completed', 'Audio validated');
                this.updateProgressStep('transcriptionStep', 'active', 'Validating prerequisites...');
                break;
            case 'transcription':
                this.updateProgressStep('transcriptionStep', 'active', 'Transcribing audio...');
                break;
            case 'analysis':
                this.updateProgressStep('transcriptionStep', 'completed', 'Transcription completed');
                this.updateProgressStep('analysisStep', 'active', 'Analyzing content...');
                break;
            case 'merge':
                this.updateProgressStep('analysisStep', 'completed', 'Analysis completed');
                this.updateProgressStep('briefStep', 'active', 'Generating brief...');
                break;
        }
    }
    
    handleJobCompleted(jobData) {
        // Update all steps to completed
        this.updateProgressStep('uploadStep', 'completed', 'Audio uploaded');
        this.updateProgressStep('transcriptionStep', 'completed', 'Transcription completed');
        this.updateProgressStep('analysisStep', 'completed', 'Analysis completed');
        this.updateProgressStep('briefStep', 'completed', 'Brief generated successfully');
        
        // Update status
        this.updateStatusText('Processing completed successfully!');
        
        // Show results
        this.displayJobResults(jobData);
        
        // Clear current job
        this.currentJob = null;
    }
    
    handleJobFailed(jobData) {
        const errorMessage = jobData.error_message || 'Unknown error occurred';
        
        // Update current step to error state
        if (jobData.current_step) {
            const stepMap = {
                'validation': 'uploadStep',
                'transcription': 'transcriptionStep',
                'analysis': 'analysisStep',
                'merge': 'briefStep'
            };
            
            const stepId = stepMap[jobData.current_step] || 'uploadStep';
            this.updateProgressStep(stepId, 'error', `Error: ${errorMessage}`);
        }
        
        // Show error message
        this.showError(`Processing failed: ${errorMessage}`);
        this.updateStatusText('Processing failed');
        
        // Clear current job
        this.currentJob = null;
    }
    
    displayJobResults(jobData) {
        const resultsContainer = document.getElementById('resultsContainer');
        if (!resultsContainer) return;
        
        const duration = this.currentJob ? 
            this.calculateDuration(this.currentJob.startTime, new Date()) : 'Unknown';
        
        const briefHtml = `
            <div class="brief-result success">
                <div class="brief-header">
                    <h3 class="brief-title">Brief Generated Successfully</h3>
                    <div class="brief-actions">
                        <a href="/api/brief/${jobData.output_name}" class="btn btn-primary" download>
                            <span class="btn-icon">📄</span>
                            Download Brief
                        </a>
                    </div>
                </div>
                <div class="brief-details">
                    <p><strong>Audio File:</strong> ${jobData.audio_file.split('/').pop()}</p>
                    <p><strong>Completed:</strong> ${new Date().toLocaleString()}</p>
                    <p><strong>Processing Time:</strong> ${duration}</p>
                    <p><strong>Job ID:</strong> ${jobData.job_id}</p>
                </div>
                <div class="brief-actions-secondary">
                    <button class="btn btn-secondary" onclick="window.audioRecorder.resetRecordingState()">
                        Record Another
                    </button>
                </div>
            </div>
        `;
        
        resultsContainer.innerHTML = briefHtml;
    }
    
    calculateDuration(startTime, endTime) {
        const durationMs = endTime - startTime;
        const durationSeconds = Math.round(durationMs / 1000);
        
        if (durationSeconds < 60) {
            return `${durationSeconds} seconds`;
        } else {
            const minutes = Math.floor(durationSeconds / 60);
            const seconds = durationSeconds % 60;
            return `${minutes}m ${seconds}s`;
        }
    }
    
    // Public method to get current job status
    getCurrentJob() {
        return this.currentJob;
    }
    
    // Public method to cancel current job
    async cancelCurrentJob() {
        if (!this.currentJob || !this.currentJob.jobId) {
            this.showError('No active job to cancel');
            return false;
        }
        
        try {
            const response = await fetch(`/api/jobs/${this.currentJob.jobId}/cancel`, {
                method: 'POST'
            });
            
            if (response.ok) {
                this.showError('Job cancelled successfully');
                this.resetRecordingState();
                return true;
            } else {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.error || 'Failed to cancel job');
            }
        } catch (error) {
            console.error('Error cancelling job:', error);
            this.showError(`Failed to cancel job: ${error.message}`);
            return false;
        }
    }
    
    startTimer() {
        this.timerInterval = setInterval(() => {
            if (this.startTime) {
                const elapsed = Date.now() - this.startTime;
                const minutes = Math.floor(elapsed / 60000);
                const seconds = Math.floor((elapsed % 60000) / 1000);
                this.recordingTimer.textContent = 
                    `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
            }
        }, 1000);
    }
    
    stopTimer() {
        if (this.timerInterval) {
            clearInterval(this.timerInterval);
            this.timerInterval = null;
        }
    }
    
    updateRecordingUI(isRecording) {
        if (isRecording) {
            this.startBtn.disabled = true;
            this.stopBtn.disabled = false;
            this.statusDot.classList.add('recording');
            this.statusText.textContent = 'Recording...';
            this.recordingTimer.classList.add('active');
        } else {
            this.startBtn.disabled = false;
            this.stopBtn.disabled = true;
            this.statusDot.classList.remove('recording');
            this.statusText.textContent = 'Processing...';
            this.recordingTimer.classList.remove('active');
        }
    }
    
    resetRecordingState() {
        this.isRecording = false;
        this.startTime = null;
        this.stopTimer();
        this.recordingTimer.textContent = '00:00';
        
        this.startBtn.disabled = false;
        this.stopBtn.disabled = true;
        this.statusDot.classList.remove('recording');
        this.statusText.textContent = 'Ready to record';
        this.recordingTimer.classList.remove('active');
        
        // Clear current job
        this.currentJob = null;
        
        // Stop monitoring if active
        if (this.statusUpdater) {
            this.statusUpdater.stopMonitoring();
        }
        
        // Reset progress steps
        this.resetProgressSteps();
        
        // Clear results
        const resultsContainer = document.getElementById('resultsContainer');
        if (resultsContainer) {
            resultsContainer.innerHTML = `
                <div class="no-results">
                    <p>Complete a recording to see your brief here</p>
                </div>
            `;
        }
    }
    
    updateProgressStep(stepId, status, message) {
        const step = document.getElementById(stepId);
        if (!step) return;
        
        // Remove all status classes
        step.classList.remove('active', 'completed', 'error');
        
        // Add new status class
        if (status !== 'waiting') {
            step.classList.add(status);
        }
        
        // Update status message
        const statusElement = step.querySelector('.step-status');
        if (statusElement) {
            statusElement.textContent = message;
        }
    }
    
    resetProgressSteps() {
        const steps = ['uploadStep', 'transcriptionStep', 'analysisStep', 'briefStep'];
        steps.forEach(stepId => {
            this.updateProgressStep(stepId, 'waiting', 'Waiting...');
        });
    }
    
    updateStatusText(text) {
        if (this.statusText) {
            this.statusText.textContent = text;
        }
    }
    
    getSupportedMimeType() {
        const types = [
            'audio/webm;codecs=opus',
            'audio/webm',
            'audio/mp4',
            'audio/wav'
        ];
        
        for (const type of types) {
            if (MediaRecorder.isTypeSupported(type)) {
                return type;
            }
        }
        
        return 'audio/webm'; // Fallback
    }
    
    handleRecordingError(error) {
        console.error('Recording error:', error);
        
        let errorMessage = '';
        let errorType = 'error';
        let persistent = false;
        
        switch (error.name) {
            case 'NotAllowedError':
                errorMessage = 'Microphone access denied. Please click the microphone icon in your browser\'s address bar and allow access, then try again.';
                persistent = true;
                this.showMicrophonePermissionHelp();
                break;
                
            case 'NotFoundError':
                errorMessage = 'No microphone found. Please connect a microphone and refresh the page.';
                persistent = true;
                this.showMicrophoneSetupHelp();
                break;
                
            case 'NotReadableError':
                errorMessage = 'Microphone is already in use by another application. Please close other apps using the microphone and try again.';
                this.showMicrophoneConflictHelp();
                break;
                
            case 'OverconstrainedError':
                errorMessage = 'Microphone settings are not supported. Trying with default settings...';
                errorType = 'warning';
                this.retryWithFallbackSettings();
                return; // Don't reset state, we're retrying
                
            case 'SecurityError':
                errorMessage = 'Security error: Audio recording requires HTTPS or localhost. Please use a secure connection.';
                persistent = true;
                break;
                
            case 'AbortError':
                errorMessage = 'Recording was interrupted. Please try again.';
                errorType = 'warning';
                break;
                
            default:
                errorMessage = `Recording failed: ${error.message || 'Unknown error'}. Please try again.`;
                if (error.message && error.message.includes('network')) {
                    errorType = 'network';
                }
                break;
        }
        
        this.showError(errorMessage, errorType, persistent);
        this.resetRecordingState();
    }
    
    async retryWithFallbackSettings() {
        try {
            this.showError('Retrying with basic microphone settings...', 'info');
            
            // Try with minimal constraints
            this.stream = await navigator.mediaDevices.getUserMedia({ 
                audio: true // No specific constraints
            });
            
            // Continue with recording setup
            const options = {
                mimeType: this.getSupportedMimeType()
            };
            
            this.mediaRecorder = new MediaRecorder(this.stream, options);
            this.setupMediaRecorderEvents();
            this.mediaRecorder.start(1000);
            
            this.isRecording = true;
            this.startTime = Date.now();
            this.updateRecordingUI(true);
            this.startTimer();
            
            this.hideError(); // Hide the retry message
            
        } catch (fallbackError) {
            this.handleRecordingError(fallbackError);
        }
    }
    
    setupMediaRecorderEvents() {
        this.audioChunks = [];
        
        this.mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
                this.audioChunks.push(event.data);
            }
        };
        
        this.mediaRecorder.onstop = () => {
            this.handleRecordingStop();
        };
        
        this.mediaRecorder.onerror = (event) => {
            this.showError(`Recording error: ${event.error}`, 'error');
            this.resetRecordingState();
        };
    }
    
    showMicrophonePermissionHelp() {
        const helpHtml = `
            <div class="help-section microphone-help">
                <h3>🎤 Microphone Permission Required</h3>
                <div class="help-steps">
                    <h4>To enable microphone access:</h4>
                    <ol>
                        <li>Look for the microphone icon in your browser's address bar</li>
                        <li>Click on it and select "Allow"</li>
                        <li>If you don't see the icon, try refreshing the page</li>
                        <li>For Chrome: Go to Settings → Privacy and Security → Site Settings → Microphone</li>
                        <li>For Firefox: Click the shield icon → Permissions → Microphone</li>
                    </ol>
                </div>
                <button class="btn btn-primary" onclick="window.audioRecorder.retryMicrophoneAccess()">
                    Try Again
                </button>
            </div>
        `;
        
        const resultsContainer = document.getElementById('resultsContainer');
        if (resultsContainer) {
            resultsContainer.innerHTML = helpHtml;
        }
    }
    
    showMicrophoneSetupHelp() {
        const helpHtml = `
            <div class="help-section microphone-help">
                <h3>🎤 No Microphone Detected</h3>
                <div class="help-steps">
                    <h4>Troubleshooting steps:</h4>
                    <ol>
                        <li>Check that your microphone is properly connected</li>
                        <li>Make sure your microphone is not muted</li>
                        <li>Try unplugging and reconnecting your microphone</li>
                        <li>Check your system's audio settings</li>
                        <li>Refresh the page after connecting your microphone</li>
                    </ol>
                </div>
                <button class="btn btn-primary" onclick="location.reload()">
                    Refresh Page
                </button>
            </div>
        `;
        
        const resultsContainer = document.getElementById('resultsContainer');
        if (resultsContainer) {
            resultsContainer.innerHTML = helpHtml;
        }
    }
    
    showMicrophoneConflictHelp() {
        const helpHtml = `
            <div class="help-section microphone-help">
                <h3>🎤 Microphone In Use</h3>
                <div class="help-steps">
                    <h4>Your microphone is being used by another application:</h4>
                    <ol>
                        <li>Close other applications that might be using the microphone</li>
                        <li>Check for video calls, voice recorders, or other browser tabs</li>
                        <li>Restart your browser if the issue persists</li>
                        <li>Check your system's audio settings for active applications</li>
                    </ol>
                </div>
                <button class="btn btn-primary" onclick="window.audioRecorder.retryMicrophoneAccess()">
                    Try Again
                </button>
            </div>
        `;
        
        const resultsContainer = document.getElementById('resultsContainer');
        if (resultsContainer) {
            resultsContainer.innerHTML = helpHtml;
        }
    }
    
    async retryMicrophoneAccess() {
        this.clearAllErrors();
        const resultsContainer = document.getElementById('resultsContainer');
        if (resultsContainer) {
            resultsContainer.innerHTML = `
                <div class="no-results">
                    <p>Complete a recording to see your brief here</p>
                </div>
            `;
        }
        
        // Re-enable the start button and try again
        this.startBtn.disabled = false;
        this.checkBrowserSupport();
    }
    
    setupNetworkMonitoring() {
        // Monitor online/offline status
        window.addEventListener('online', () => {
            this.networkStatus = 'online';
            this.showError('Connection restored', 'info');
            this.performHealthCheck();
        });
        
        window.addEventListener('offline', () => {
            this.networkStatus = 'offline';
            this.showError('No internet connection. Please check your network.', 'network', true);
        });
        
        // Initial network status
        this.networkStatus = navigator.onLine ? 'online' : 'offline';
    }
    
    async performInitialHealthCheck() {
        try {
            await this.performHealthCheck();
        } catch (error) {
            console.warn('Initial health check failed:', error);
            this.showError('Server connection check failed. Some features may not work properly.', 'warning');
        }
    }
    
    async performHealthCheck() {
        if (this.networkStatus === 'offline') {
            return false;
        }
        
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 5000);
            
            const response = await fetch('/api/health', {
                method: 'GET',
                signal: controller.signal,
                cache: 'no-cache'
            });
            
            clearTimeout(timeoutId);
            this.lastNetworkCheck = Date.now();
            
            if (response.ok) {
                return true;
            } else {
                throw new Error(`Server returned ${response.status}`);
            }
        } catch (error) {
            if (error.name === 'AbortError') {
                this.showError('Server is not responding. Please check your connection.', 'network');
            } else {
                this.showError('Server connection failed. Please try again later.', 'network');
            }
            return false;
        }
    }
    
    async checkNetworkBeforeUpload() {
        if (this.networkStatus === 'offline') {
            throw new Error('No internet connection. Please check your network and try again.');
        }
        
        // Check if we need to verify server connection
        const timeSinceLastCheck = this.lastNetworkCheck ? Date.now() - this.lastNetworkCheck : Infinity;
        if (timeSinceLastCheck > 30000) { // 30 seconds
            const isHealthy = await this.performHealthCheck();
            if (!isHealthy) {
                throw new Error('Server is not responding. Please try again later.');
            }
        }
        
        return true;
    }
    
    showError(message, type = 'error', persistent = false) {
        // Create or update error container
        let errorContainer = document.getElementById('errorContainer');
        if (!errorContainer) {
            errorContainer = this.createErrorContainer();
        }
        
        const errorId = `error-${Date.now()}`;
        const errorElement = this.createErrorElement(message, type, errorId, persistent);
        
        // Add to container
        errorContainer.appendChild(errorElement);
        errorContainer.style.display = 'block';
        
        // Auto-hide non-persistent errors
        if (!persistent) {
            const hideDelay = type === 'warning' ? 8000 : 10000;
            setTimeout(() => {
                this.hideError(errorId);
            }, hideDelay);
        }
        
        // Limit number of visible errors
        this.limitVisibleErrors(errorContainer);
    }
    
    createErrorContainer() {
        const container = document.createElement('div');
        container.id = 'errorContainer';
        container.className = 'error-container';
        document.body.appendChild(container);
        return container;
    }
    
    createErrorElement(message, type, errorId, persistent) {
        const errorDiv = document.createElement('div');
        errorDiv.className = `error-message error-${type}`;
        errorDiv.id = errorId;
        
        const iconMap = {
            error: '⚠️',
            warning: '⚡',
            info: 'ℹ️',
            network: '🌐'
        };
        
        errorDiv.innerHTML = `
            <span class="error-icon">${iconMap[type] || '⚠️'}</span>
            <span class="error-text">${message}</span>
            <button class="error-close" onclick="window.audioRecorder.hideError('${errorId}')">×</button>
            ${persistent ? '<div class="error-persistent-indicator">This error requires attention</div>' : ''}
        `;
        
        return errorDiv;
    }
    
    limitVisibleErrors(container) {
        const errors = container.querySelectorAll('.error-message');
        const maxErrors = 3;
        
        if (errors.length > maxErrors) {
            // Remove oldest non-persistent errors
            for (let i = 0; i < errors.length - maxErrors; i++) {
                if (!errors[i].querySelector('.error-persistent-indicator')) {
                    errors[i].remove();
                }
            }
        }
    }
    
    hideError(errorId = null) {
        const errorContainer = document.getElementById('errorContainer');
        if (!errorContainer) return;
        
        if (errorId) {
            const errorElement = document.getElementById(errorId);
            if (errorElement) {
                errorElement.remove();
            }
        } else {
            // Hide all errors
            errorContainer.innerHTML = '';
        }
        
        // Hide container if no errors remain
        if (errorContainer.children.length === 0) {
            errorContainer.style.display = 'none';
        }
    }
    
    clearAllErrors() {
        const errorContainer = document.getElementById('errorContainer');
        if (errorContainer) {
            errorContainer.innerHTML = '';
            errorContainer.style.display = 'none';
        }
    }
}

// Status Updater Class for WebSocket communication
class StatusUpdater {
    constructor() {
        this.socket = null;
        this.currentJobId = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000; // Start with 1 second
        
        this.initializeElements();
        this.connect();
    }
    
    initializeElements() {
        this.errorContainer = document.getElementById('errorContainer');
        this.errorText = document.getElementById('errorText');
    }
    
    connect() {
        try {
            // Initialize Socket.IO connection
            this.socket = io();
            
            // Connection event handlers
            this.socket.on('connect', () => {
                console.log('Connected to server via WebSocket');
                this.isConnected = true;
                this.reconnectAttempts = 0;
                this.reconnectDelay = 1000;
                
                // Join job room if we have a current job
                if (this.currentJobId) {
                    this.joinJobRoom(this.currentJobId);
                }
            });
            
            this.socket.on('disconnect', () => {
                console.log('Disconnected from server');
                this.isConnected = false;
                this.handleDisconnection();
            });
            
            this.socket.on('connect_error', (error) => {
                console.error('Connection error:', error);
                this.handleConnectionError();
            });
            
            // Pipeline event handlers
            this.socket.on('pipeline_started', (data) => {
                this.handlePipelineStarted(data);
            });
            
            this.socket.on('pipeline_progress', (data) => {
                this.handlePipelineProgress(data);
            });
            
            this.socket.on('pipeline_completed', (data) => {
                this.handlePipelineCompleted(data);
            });
            
            this.socket.on('pipeline_error', (data) => {
                this.handlePipelineError(data);
            });
            
            // Job management events
            this.socket.on('job_joined', (data) => {
                console.log('Joined job room:', data.job_id);
            });
            
        } catch (error) {
            console.error('Failed to initialize WebSocket connection:', error);
            this.showError('Failed to connect to server. Real-time updates may not work.');
        }
    }
    
    handleDisconnection() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
            
            setTimeout(() => {
                this.connect();
            }, this.reconnectDelay);
            
            // Exponential backoff
            this.reconnectDelay = Math.min(this.reconnectDelay * 2, 30000);
        } else {
            this.showError('Lost connection to server. Please refresh the page to reconnect.');
        }
    }
    
    handleConnectionError() {
        if (!this.isConnected) {
            this.handleDisconnection();
        }
    }
    
    joinJobRoom(jobId) {
        if (this.socket && this.isConnected) {
            this.socket.emit('join_job', { job_id: jobId });
            this.currentJobId = jobId;
        }
    }
    
    handlePipelineStarted(data) {
        console.log('Pipeline started:', data);
        this.currentJobId = data.job_id;
        
        // Update UI to show pipeline has started
        this.updateProgressStep('uploadStep', 'completed', 'Audio uploaded successfully');
        this.updateProgressStep('transcriptionStep', 'active', 'Starting transcription...');
        
        // Show processing status
        this.updateStatusText('Processing audio...');
    }
    
    handlePipelineProgress(data) {
        console.log('Pipeline progress:', data);
        
        const { current_step, progress, status } = data;
        
        // Update progress based on current step
        switch (current_step) {
            case 'validation':
                this.updateProgressStep('uploadStep', 'completed', 'Audio validated');
                this.updateProgressStep('transcriptionStep', 'active', 'Validating prerequisites...');
                break;
                
            case 'transcription':
                this.updateProgressStep('transcriptionStep', 'active', 'Transcribing audio...');
                this.updateProgressStep('analysisStep', 'waiting', 'Waiting...');
                break;
                
            case 'analysis':
                this.updateProgressStep('transcriptionStep', 'completed', 'Transcription completed');
                this.updateProgressStep('analysisStep', 'active', 'Analyzing content...');
                this.updateProgressStep('briefStep', 'waiting', 'Waiting...');
                break;
                
            case 'merge':
                this.updateProgressStep('analysisStep', 'completed', 'Analysis completed');
                this.updateProgressStep('briefStep', 'active', 'Generating brief...');
                break;
        }
        
        // Update overall progress if available
        if (progress !== undefined) {
            this.updateOverallProgress(progress);
        }
    }
    
    handlePipelineCompleted(data) {
        console.log('Pipeline completed:', data);
        
        // Update all steps to completed
        this.updateProgressStep('uploadStep', 'completed', 'Audio uploaded');
        this.updateProgressStep('transcriptionStep', 'completed', 'Transcription completed');
        this.updateProgressStep('analysisStep', 'completed', 'Analysis completed');
        this.updateProgressStep('briefStep', 'completed', 'Brief generated successfully');
        
        // Update status
        this.updateStatusText('Processing completed successfully!');
        
        // Show results
        this.displayCompletedBrief(data);
        
        // Reset current job
        this.currentJobId = null;
    }
    
    handlePipelineError(data) {
        console.error('Pipeline error:', data);
        
        const errorMessage = data.error_message || 'Unknown error occurred';
        
        // Update current step to error state
        if (data.current_step) {
            const stepMap = {
                'validation': 'uploadStep',
                'transcription': 'transcriptionStep',
                'analysis': 'analysisStep',
                'merge': 'briefStep'
            };
            
            const stepId = stepMap[data.current_step] || 'uploadStep';
            this.updateProgressStep(stepId, 'error', `Error: ${errorMessage}`);
        }
        
        // Show error message
        this.showError(`Processing failed: ${errorMessage}`);
        this.updateStatusText('Processing failed');
        
        // Reset current job
        this.currentJobId = null;
    }
    
    updateProgressStep(stepId, status, message) {
        const step = document.getElementById(stepId);
        if (!step) return;
        
        // Remove all status classes
        step.classList.remove('active', 'completed', 'error', 'waiting');
        
        // Add new status class
        if (status !== 'waiting') {
            step.classList.add(status);
        }
        
        // Update status message
        const statusElement = step.querySelector('.step-status');
        if (statusElement) {
            statusElement.textContent = message;
        }
        
        // Update step indicator for completed/error states
        const indicator = step.querySelector('.step-indicator');
        if (indicator) {
            if (status === 'completed') {
                indicator.innerHTML = '<span class="step-checkmark">✓</span>';
            } else if (status === 'error') {
                indicator.innerHTML = '<span class="step-error">✗</span>';
            } else if (status === 'active') {
                indicator.innerHTML = '<span class="step-spinner">⟳</span>';
            }
        }
    }
    
    updateOverallProgress(progress) {
        // Update progress bar if it exists
        const progressBar = document.querySelector('.overall-progress-bar');
        if (progressBar) {
            const percentage = Math.round(progress * 100);
            progressBar.style.width = `${percentage}%`;
            progressBar.setAttribute('aria-valuenow', percentage);
        }
        
        // Update progress text
        const progressText = document.querySelector('.progress-text');
        if (progressText) {
            progressText.textContent = `${Math.round(progress * 100)}% complete`;
        }
    }
    
    updateStatusText(text) {
        const statusText = document.querySelector('.status-text');
        if (statusText) {
            statusText.textContent = text;
        }
    }
    
    displayCompletedBrief(data) {
        const resultsContainer = document.getElementById('resultsContainer');
        if (!resultsContainer) return;
        
        const briefHtml = `
            <div class="brief-result success">
                <div class="brief-header">
                    <h3 class="brief-title">Brief Generated Successfully</h3>
                    <div class="brief-actions">
                        <a href="/api/brief/${data.output_name}" class="btn btn-primary" download>
                            <span class="btn-icon">📄</span>
                            Download Brief
                        </a>
                    </div>
                </div>
                <div class="brief-details">
                    <p><strong>Audio File:</strong> ${data.audio_file.split('/').pop()}</p>
                    <p><strong>Completed:</strong> ${new Date(data.completed_at).toLocaleString()}</p>
                    <p><strong>Processing Time:</strong> ${this.calculateDuration(data.started_at, data.completed_at)}</p>
                </div>
                <div class="brief-actions-secondary">
                    <button class="btn btn-secondary" onclick="window.audioRecorder.resetRecordingState()">
                        Record Another
                    </button>
                </div>
            </div>
        `;
        
        resultsContainer.innerHTML = briefHtml;
    }
    
    calculateDuration(startTime, endTime) {
        const start = new Date(startTime);
        const end = new Date(endTime);
        const durationMs = end - start;
        const durationSeconds = Math.round(durationMs / 1000);
        
        if (durationSeconds < 60) {
            return `${durationSeconds} seconds`;
        } else {
            const minutes = Math.floor(durationSeconds / 60);
            const seconds = durationSeconds % 60;
            return `${minutes}m ${seconds}s`;
        }
    }
    
    showError(message) {
        if (this.errorText && this.errorContainer) {
            this.errorText.textContent = message;
            this.errorContainer.style.display = 'block';
            
            // Auto-hide after 10 seconds
            setTimeout(() => {
                this.hideError();
            }, 10000);
        }
    }
    
    hideError() {
        if (this.errorContainer) {
            this.errorContainer.style.display = 'none';
        }
    }
    
    // Public method to start monitoring a specific job
    startMonitoring(jobId) {
        this.currentJobId = jobId;
        if (this.isConnected) {
            this.joinJobRoom(jobId);
        }
    }
    
    // Public method to stop monitoring
    stopMonitoring() {
        this.currentJobId = null;
    }
    
    // Public method to check connection status
    isConnectedToServer() {
        return this.isConnected;
    }
}

// Brief Manager Class for managing briefs and job results
class BriefManager {
    constructor() {
        this.resultsContainer = document.getElementById('resultsContainer');
        this.jobHistory = [];
    }
    
    // Download a brief by name
    async downloadBrief(briefName) {
        try {
            const response = await fetch(`/api/brief/${briefName}`);
            if (!response.ok) {
                throw new Error(`Failed to download brief: ${response.statusText}`);
            }
            
            // Create download link
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = briefName;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            
        } catch (error) {
            console.error('Error downloading brief:', error);
            this.showError(`Failed to download brief: ${error.message}`);
        }
    }
    
    // Get list of available briefs
    async getBriefsList() {
        try {
            const response = await fetch('/api/briefs');
            if (!response.ok) {
                throw new Error(`Failed to get briefs list: ${response.statusText}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('Error getting briefs list:', error);
            return [];
        }
    }
    
    // Display brief results
    displayBrief(briefData) {
        if (!this.resultsContainer) return;
        
        const briefHtml = `
            <div class="brief-result success">
                <div class="brief-header">
                    <h3 class="brief-title">${briefData.filename || 'Generated Brief'}</h3>
                    <div class="brief-actions">
                        <button class="btn btn-primary" onclick="window.briefManager.downloadBrief('${briefData.filename}')">
                            <span class="btn-icon">📄</span>
                            Download
                        </button>
                    </div>
                </div>
                <div class="brief-details">
                    <p><strong>Generated:</strong> ${new Date(briefData.created_at || Date.now()).toLocaleString()}</p>
                    ${briefData.size ? `<p><strong>Size:</strong> ${this.formatFileSize(briefData.size)}</p>` : ''}
                </div>
            </div>
        `;
        
        this.resultsContainer.innerHTML = briefHtml;
    }
    
    // Display recent briefs list
    async displayRecentBriefs() {
        try {
            const briefs = await this.getBriefsList();
            
            if (!briefs || briefs.length === 0) {
                this.displayNoBriefs();
                return;
            }
            
            const briefsHtml = briefs.map(brief => `
                <div class="brief-item">
                    <div class="brief-info">
                        <h4>${brief.filename}</h4>
                        <p>Created: ${new Date(brief.created_at).toLocaleString()}</p>
                        <p>Size: ${this.formatFileSize(brief.size)}</p>
                    </div>
                    <div class="brief-actions">
                        <button class="btn btn-secondary" onclick="window.briefManager.downloadBrief('${brief.filename}')">
                            Download
                        </button>
                    </div>
                </div>
            `).join('');
            
            this.resultsContainer.innerHTML = `
                <div class="briefs-list">
                    <h3>Recent Briefs</h3>
                    ${briefsHtml}
                </div>
            `;
            
        } catch (error) {
            console.error('Error displaying recent briefs:', error);
            this.showError('Failed to load recent briefs');
        }
    }
    
    displayNoBriefs() {
        if (this.resultsContainer) {
            this.resultsContainer.innerHTML = `
                <div class="no-results">
                    <p>Complete a recording to see your brief here</p>
                </div>
            `;
        }
    }
    
    // Add job to history
    addJobToHistory(jobData) {
        this.jobHistory.unshift({
            ...jobData,
            timestamp: new Date()
        });
        
        // Keep only last 10 jobs in history
        if (this.jobHistory.length > 10) {
            this.jobHistory = this.jobHistory.slice(0, 10);
        }
    }
    
    // Get job history
    getJobHistory() {
        return this.jobHistory;
    }
    
    // Format file size for display
    formatFileSize(bytes) {
        if (!bytes) return 'Unknown';
        
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        if (bytes === 0) return '0 Bytes';
        
        const i = Math.floor(Math.log(bytes) / Math.log(1024));
        return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
    }
    
    // Show error message
    showError(message) {
        const errorContainer = document.getElementById('errorContainer');
        const errorText = document.getElementById('errorText');
        
        if (errorContainer && errorText) {
            errorText.textContent = message;
            errorContainer.style.display = 'block';
            
            setTimeout(() => {
                errorContainer.style.display = 'none';
            }, 5000);
        }
    }
    
    // Clear results display
    clearResults() {
        this.displayNoBriefs();
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Initialize StatusUpdater first for WebSocket connection
    const statusUpdater = new StatusUpdater();
    
    // Initialize other components
    const audioRecorder = new AudioRecorder();
    const briefManager = new BriefManager();
    
    // Make instances globally available
    window.audioRecorder = audioRecorder;
    window.statusUpdater = statusUpdater;
    window.briefManager = briefManager;
    
    // Connect AudioRecorder with StatusUpdater
    audioRecorder.statusUpdater = statusUpdater;
});

// Brief Management Class
class BriefManager {
    constructor() {
        this.briefs = [];
        this.isLoading = false;
        
        this.initializeElements();
        this.bindEvents();
        this.loadBriefs();
    }
    
    initializeElements() {
        this.briefsContainer = document.getElementById('briefsContainer');
        this.refreshBtn = document.getElementById('refreshBriefsBtn');
    }
    
    bindEvents() {
        if (this.refreshBtn) {
            this.refreshBtn.addEventListener('click', () => this.loadBriefs());
        }
    }
    
    async loadBriefs() {
        if (this.isLoading) return;
        
        this.isLoading = true;
        this.showLoadingState();
        
        try {
            const response = await fetch('/api/briefs');
            
            if (!response.ok) {
                throw new Error(`Failed to load briefs: ${response.statusText}`);
            }
            
            const data = await response.json();
            this.briefs = data.briefs || [];
            
            this.renderBriefs();
            
        } catch (error) {
            console.error('Error loading briefs:', error);
            this.showErrorState(error.message);
        } finally {
            this.isLoading = false;
        }
    }
    
    showLoadingState() {
        if (!this.briefsContainer) return;
        
        this.briefsContainer.innerHTML = `
            <div class="loading-briefs">
                <div class="loading-spinner">⟳</div>
                <p>Loading briefs...</p>
            </div>
        `;
    }
    
    showErrorState(message) {
        if (!this.briefsContainer) return;
        
        this.briefsContainer.innerHTML = `
            <div class="error-briefs">
                <div class="error-icon">⚠️</div>
                <p>Failed to load briefs: ${message}</p>
                <button class="btn btn-secondary" onclick="window.briefManager.loadBriefs()">
                    Try Again
                </button>
            </div>
        `;
    }
    
    renderBriefs() {
        if (!this.briefsContainer) return;
        
        if (this.briefs.length === 0) {
            this.briefsContainer.innerHTML = `
                <div class="no-briefs">
                    <div class="no-briefs-icon">📄</div>
                    <p>No briefs found</p>
                    <p class="no-briefs-subtitle">Complete a recording to generate your first brief</p>
                </div>
            `;
            return;
        }
        
        const briefsHtml = this.briefs.map(brief => this.renderBriefCard(brief)).join('');
        
        this.briefsContainer.innerHTML = `
            <div class="briefs-list">
                ${briefsHtml}
            </div>
        `;
    }
    
    renderBriefCard(brief) {
        const createdDate = new Date(brief.created_at);
        const modifiedDate = new Date(brief.modified_at);
        const fileSize = this.formatFileSize(brief.size);
        
        return `
            <div class="brief-card" data-filename="${brief.filename}">
                <div class="brief-card-header">
                    <div class="brief-info">
                        <h3 class="brief-name">${brief.name}</h3>
                        <div class="brief-meta">
                            <span class="brief-date">${createdDate.toLocaleDateString()}</span>
                            <span class="brief-size">${fileSize}</span>
                        </div>
                    </div>
                    <div class="brief-actions">
                        <button class="btn btn-primary btn-sm" onclick="window.briefManager.downloadBrief('${brief.filename}')">
                            <span class="btn-icon">📥</span>
                            Download
                        </button>
                        <button class="btn btn-secondary btn-sm" onclick="window.briefManager.previewBrief('${brief.filename}')">
                            <span class="btn-icon">👁️</span>
                            Preview
                        </button>
                    </div>
                </div>
                <div class="brief-preview">
                    <p class="brief-preview-text">${brief.preview}</p>
                </div>
                <div class="brief-card-footer">
                    <span class="brief-modified">Modified: ${modifiedDate.toLocaleString()}</span>
                </div>
            </div>
        `;
    }
    
    async downloadBrief(filename) {
        try {
            // Create a temporary link to trigger download
            const link = document.createElement('a');
            link.href = `/api/brief/${encodeURIComponent(filename)}`;
            link.download = filename;
            link.style.display = 'none';
            
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            // Show success message
            this.showDownloadSuccess(filename);
            
        } catch (error) {
            console.error('Error downloading brief:', error);
            this.showDownloadError(filename, error.message);
        }
    }
    
    async previewBrief(filename) {
        try {
            const response = await fetch(`/api/brief/${encodeURIComponent(filename)}`);
            
            if (!response.ok) {
                throw new Error(`Failed to load brief: ${response.statusText}`);
            }
            
            const briefContent = await response.text();
            this.showBriefPreview(filename, briefContent);
            
        } catch (error) {
            console.error('Error previewing brief:', error);
            this.showPreviewError(filename, error.message);
        }
    }
    
    showBriefPreview(filename, content) {
        // Create modal overlay
        const modal = document.createElement('div');
        modal.className = 'brief-preview-modal';
        modal.innerHTML = `
            <div class="brief-preview-content">
                <div class="brief-preview-header">
                    <h3>${filename}</h3>
                    <div class="brief-preview-actions">
                        <button class="btn btn-primary" onclick="window.briefManager.downloadBrief('${filename}')">
                            <span class="btn-icon">📥</span>
                            Download
                        </button>
                        <button class="btn btn-secondary" onclick="this.closest('.brief-preview-modal').remove()">
                            <span class="btn-icon">✕</span>
                            Close
                        </button>
                    </div>
                </div>
                <div class="brief-preview-body">
                    <pre class="brief-content">${this.escapeHtml(content)}</pre>
                </div>
            </div>
        `;
        
        // Add click outside to close
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });
        
        // Add escape key to close
        const handleEscape = (e) => {
            if (e.key === 'Escape') {
                modal.remove();
                document.removeEventListener('keydown', handleEscape);
            }
        };
        document.addEventListener('keydown', handleEscape);
        
        document.body.appendChild(modal);
    }
    
    showDownloadSuccess(filename) {
        this.showTemporaryMessage(`Brief "${filename}" downloaded successfully`, 'success');
    }
    
    showDownloadError(filename, error) {
        this.showTemporaryMessage(`Failed to download "${filename}": ${error}`, 'error');
    }
    
    showPreviewError(filename, error) {
        this.showTemporaryMessage(`Failed to preview "${filename}": ${error}`, 'error');
    }
    
    showTemporaryMessage(message, type = 'info') {
        // Create temporary message element
        const messageEl = document.createElement('div');
        messageEl.className = `brief-message brief-message-${type}`;
        messageEl.innerHTML = `
            <span class="message-icon">${type === 'success' ? '✓' : type === 'error' ? '⚠️' : 'ℹ️'}</span>
            <span class="message-text">${message}</span>
        `;
        
        // Add to page
        const container = this.briefsContainer.parentElement;
        if (container) {
            container.insertBefore(messageEl, this.briefsContainer);
            
            // Auto-remove after 3 seconds
            setTimeout(() => {
                if (messageEl.parentElement) {
                    messageEl.remove();
                }
            }, 3000);
        }
    }
    
    formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    // Public method to refresh briefs list
    refresh() {
        this.loadBriefs();
    }
    
    // Public method to get current briefs
    getBriefs() {
        return this.briefs;
    }
}

