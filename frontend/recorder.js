class VoiceRecorder {
    constructor() {
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.isRecording = false;
        this.currentBlob = null;
        
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
                const audioBlob = new Blob(this.audioChunks, { type: 'audio/wav' });
                this.currentBlob = audioBlob;
                const audioUrl = URL.createObjectURL(audioBlob);
                this.audioPlayback.src = audioUrl;
                this.audioPlayback.style.display = 'block';
                
                this.playBtn.disabled = false;
                this.saveBtn.disabled = false;
                this.updateStatus('Recording completed. You can now play or save it.');
            };
            
            this.mediaRecorder.start();
            this.isRecording = true;
            
            this.recordBtn.classList.add('recording');
            this.recordBtn.querySelector('.btn-text').textContent = 'Recording...';
            this.stopBtn.disabled = false;
            this.updateStatus('Recording in progress...');
            
        } catch (error) {
            console.error('Error accessing microphone:', error);
            this.updateStatus('Error: Could not access microphone. Please check permissions.');
        }
    }

    stopRecording() {
        if (this.mediaRecorder && this.isRecording) {
            this.mediaRecorder.stop();
            this.mediaRecorder.stream.getTracks().forEach(track => track.stop());
            
            this.isRecording = false;
            this.recordBtn.classList.remove('recording');
            this.recordBtn.querySelector('.btn-text').textContent = 'Start Recording';
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
            this.updateStatus('No recording to save.');
            return;
        }

        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const filename = `recording-${timestamp}.wav`;
        
        try {
            // Send to backend API
            const formData = new FormData();
            formData.append('audio', this.currentBlob, filename);
            
            const response = await fetch('/api/save-recording', {
                method: 'POST',
                body: formData
            });
            
            if (response.ok) {
                this.updateStatus(`Recording saved as ${filename}`);
                this.addRecordingToList(filename);
                this.resetRecorder();
            } else {
                throw new Error('Failed to save recording');
            }
        } catch (error) {
            console.error('Error saving recording:', error);
            // Fallback: download directly to browser
            this.downloadRecording(filename);
        }
    }

    downloadRecording(filename) {
        const url = URL.createObjectURL(this.currentBlob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        this.updateStatus(`Recording downloaded as ${filename}`);
        this.addRecordingToList(filename);
        this.resetRecorder();
    }

    resetRecorder() {
        this.currentBlob = null;
        this.audioPlayback.src = '';
        this.audioPlayback.style.display = 'none';
        this.playBtn.disabled = true;
        this.saveBtn.disabled = true;
    }

    addRecordingToList(filename) {
        const recordingItem = document.createElement('div');
        recordingItem.className = 'recording-item';
        recordingItem.innerHTML = `
            <span class="recording-name">${filename}</span>
            <div class="recording-actions">
                <button class="action-btn" onclick="this.parentElement.parentElement.remove()">Delete</button>
            </div>
        `;
        this.recordingsList.appendChild(recordingItem);
        
        // Save to localStorage
        this.saveRecordingToStorage(filename);
    }

    saveRecordingToStorage(filename) {
        const recordings = JSON.parse(localStorage.getItem('voiceRecordings') || '[]');
        recordings.push({
            filename,
            timestamp: new Date().toISOString()
        });
        localStorage.setItem('voiceRecordings', JSON.stringify(recordings));
    }

    loadSavedRecordings() {
        const recordings = JSON.parse(localStorage.getItem('voiceRecordings') || '[]');
        recordings.forEach(recording => {
            this.addRecordingToList(recording.filename);
        });
    }

    updateStatus(message) {
        this.statusText.textContent = message;
    }
}

// Initialize the voice recorder when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new VoiceRecorder();
});