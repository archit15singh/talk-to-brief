class VoiceRecorder {
    constructor() {
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.isRecording = false;
        this.currentBlob = null;
        this.savedRecordings = [];

        this.initializeElements();
        this.setupEventListeners();
        this.loadSavedRecordings();
    }

    initializeElements() {
        this.recordBtn = document.getElementById('recordBtn');
        this.stopBtn = document.getElementById('stopBtn');
        this.playBtn = document.getElementById('playBtn');
        this.saveBtn = document.getElementById('saveBtn');
        this.audioPlayback = document.getElementById('audioPlayback');
        this.statusText = document.getElementById('statusText');
        this.recordingsList = document.getElementById('recordingsList');
    }

    setupEventListeners() {
        this.recordBtn.addEventListener('click', () => this.toggleRecording());
        this.stopBtn.addEventListener('click', () => this.stopRecording());
        this.playBtn.addEventListener('click', () => this.playRecording());
        this.saveBtn.addEventListener('click', () => this.saveRecording());
    }

    async toggleRecording() {
        if (!this.isRecording) {
            await this.startRecording();
        } else {
            this.stopRecording();
        }
    }

    async startRecording() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

            this.mediaRecorder = new MediaRecorder(stream);
            this.audioChunks = [];

            this.mediaRecorder.ondataavailable = (event) => {
                this.audioChunks.push(event.data);
            };

            this.mediaRecorder.onstop = () => {
                const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });
                this.currentBlob = audioBlob;
                const audioUrl = URL.createObjectURL(audioBlob);
                this.audioPlayback.src = audioUrl;
                this.audioPlayback.classList.remove('hidden');

                this.playBtn.disabled = false;
                this.saveBtn.disabled = false;
                this.updateStatus('Recording completed. You can play or save it.', 'success');
            };

            this.mediaRecorder.start();
            this.isRecording = true;

            // Update UI for recording state
            this.recordBtn.classList.add('recording', 'animate-pulse');
            this.recordBtn.querySelector('i').className = 'fas fa-stop text-3xl';
            this.recordBtn.querySelector('.recording-indicator').classList.add('animate-ping', 'opacity-75');
            this.stopBtn.disabled = false;
            this.updateStatus('Recording in progress... Click the button again to stop.', 'warning');

        } catch (error) {
            console.error('Error accessing microphone:', error);
            this.updateStatus('Error: Could not access microphone. Please check permissions.', 'error');
        }
    }

    stopRecording() {
        if (this.mediaRecorder && this.isRecording) {
            this.mediaRecorder.stop();
            this.mediaRecorder.stream.getTracks().forEach(track => track.stop());

            this.isRecording = false;
            this.recordBtn.classList.remove('recording', 'animate-pulse');
            this.recordBtn.querySelector('i').className = 'fas fa-microphone text-3xl';
            this.recordBtn.querySelector('.recording-indicator').classList.remove('animate-ping', 'opacity-75');
            this.stopBtn.disabled = true;
        }
    }

    playRecording() {
        if (this.audioPlayback.src) {
            this.audioPlayback.play();
        }
    }

    async saveRecording() {
        if (!this.currentBlob) {
            this.updateStatus('No recording to save', 'error');
            return;
        }

        this.updateStatus('Saving recording...', 'info');

        try {
            const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
            const filename = `recording-${timestamp}.webm`;

            const formData = new FormData();
            formData.append('audio', this.currentBlob, filename);

            const response = await fetch('/api/save-recording', {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                const result = await response.json();
                this.updateStatus(`Recording saved as ${result.filename}`, 'success');
                this.savedRecordings.push({
                    filename: result.filename,
                    timestamp: new Date().toLocaleString(),
                    path: result.path
                });
                this.updateRecordingsList();

                // Reset for next recording
                this.currentBlob = null;
                this.audioPlayback.classList.add('hidden');
                this.playBtn.disabled = true;
                this.saveBtn.disabled = true;
            } else {
                throw new Error('Failed to save recording');
            }

        } catch (error) {
            console.error('Error saving recording:', error);
            this.updateStatus('Error saving recording. Please try again.', 'error');
        }
    }

    loadSavedRecordings() {
        // In a real app, you'd load this from the server
        // For now, we'll just show the ones saved in this session
        this.updateRecordingsList();
    }

    updateRecordingsList() {
        if (this.savedRecordings.length === 0) {
            this.recordingsList.innerHTML = `
                <div class="text-center py-4 text-base-content/60">
                    <i class="fas fa-microphone text-2xl mb-2"></i>
                    <p>No recordings saved yet</p>
                </div>
            `;
            return;
        }

        this.recordingsList.innerHTML = this.savedRecordings.map(recording => `
            <div class="flex items-center justify-between p-3 bg-base-200 rounded-lg">
                <div>
                    <p class="font-medium">${recording.filename}</p>
                    <p class="text-sm text-base-content/60">${recording.timestamp}</p>
                </div>
                <div class="flex gap-2">
                    <button class="btn btn-ghost btn-sm" onclick="app.downloadRecording('${recording.filename}')">
                        <i class="fas fa-download"></i>
                    </button>
                </div>
            </div>
        `).join('');
    }

    downloadRecording(filename) {
        // Create a download link for the recording
        const recording = this.savedRecordings.find(r => r.filename === filename);
        if (recording) {
            window.open(`/data/raw-source/${filename}`, '_blank');
        }
    }

    updateStatus(message, type = 'info') {
        if (!this.statusText) return;

        this.statusText.textContent = message;
        const alertElement = this.statusText.parentElement;

        // Remove existing alert classes
        alertElement.classList.remove('alert-info', 'alert-success', 'alert-warning', 'alert-error');

        // Add new alert class based on type
        alertElement.classList.add(`alert-${type}`);

        // Update icon based on type
        const icon = alertElement.querySelector('i');
        if (icon) {
            icon.className = `fas ${this.getIconForType(type)}`;
        }
    }

    getIconForType(type) {
        const icons = {
            info: 'fa-info-circle',
            success: 'fa-check-circle',
            warning: 'fa-exclamation-triangle',
            error: 'fa-exclamation-circle'
        };
        return icons[type] || icons.info;
    }
}

// Theme toggle function
function toggleTheme() {
    const html = document.documentElement;
    const currentTheme = html.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    html.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
}

// Initialize theme from localStorage
function initializeTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
}

// Global app instance
let app;

// Initialize the application when the page loads
document.addEventListener('DOMContentLoaded', () => {
    initializeTheme();
    app = new VoiceRecorder();
});