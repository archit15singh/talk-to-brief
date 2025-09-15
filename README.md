# Audio Brief Generator

A complete pipeline for converting audio files into structured, actionable briefs using AI analysis.

## Features

- **Web Interface**: Browser-based recording with real-time progress tracking
- **Live Audio Recording**: Record talks/presentations in real-time with automatic silence detection
- **Audio Transcription**: Fast transcription with timestamps using faster-whisper (base model)
- **Intelligent Chunking**: Smart segmentation respecting sentence boundaries (~1200 words)
- **Parallel Analysis**: Concurrent GPT-4 processing for optimal performance
- **Structured Output**: Organized briefs with conversation starters, strategic questions, and key insights
- **End-to-End Workflow**: Record → Transcribe → Analyze → Generate Brief in one command

## Project Structure

```
├── pipeline.py              # Pipeline launcher (runs src/pipeline.py)
├── record_and_process.py    # Recording launcher (runs src/record_and_process.py)
├── setup_recording.py       # Setup launcher (runs src/setup_recording.py)
├── src/                     # All source code and configuration
│   ├── pipeline.py          # Main orchestrator script
│   ├── record_and_process.py # Live recording + full pipeline
│   ├── setup_recording.py   # Audio recording setup script
│   ├── record_audio.py      # Live audio recording
│   ├── transcribe.py        # Audio → timestamped transcript
│   ├── analyze_chunk.py     # Transcript → parallel GPT-4 analysis
│   ├── merge_brief.py       # Partials → final brief
│   ├── validate_setup.py    # Setup validation
│   └── config/              # Configuration and prompts
│       ├── per_chunk.md     # GPT-4 analysis prompt template
│       └── merge.md         # Brief merging instructions
├── web/                     # Web interface
│   ├── app.py               # Flask application entry point
│   ├── web_server.py        # Main web server and API routes
│   ├── pipeline_runner.py   # Pipeline integration for web
│   ├── config.py            # Web application configuration
│   ├── requirements_web.txt # Web-specific dependencies
│   ├── static/              # Frontend files
│   │   ├── index.html       # Main recording interface
│   │   ├── app.js           # JavaScript application logic
│   │   └── style.css        # Interface styling
│   ├── templates/           # Jinja2 templates (if needed)
│   └── logs/                # Web server logs
├── data/                    # All data artifacts
│   ├── 1_audio/             # Input audio files (web uploads)
│   ├── audio/               # Input audio files (command line)
│   ├── transcripts/         # Generated transcripts
│   ├── partials/            # Individual chunk analyses
│   └── outputs/             # Final briefs
└── requirements.txt         # Core Python dependencies
```

## Installation

1. Clone the repository
2. Create virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install core dependencies:
```bash
pip install -r requirements.txt
```

4. Install web interface dependencies:
```bash
pip install -r web/requirements_web.txt
```

5. Set up your OpenAI API key:
   - Create a `.env` file in the project root
   - Add your OpenAI API key:
   ```
   OPENAI_API_KEY=your-api-key-here
   ```
   - **Important**: Ensure you have GPT-4 access on your OpenAI account
   - **Security**: Never commit the `.env` file to version control

6. Set up audio recording (optional for command line):
```bash
python setup_recording.py
```

7. Validate your setup:
```bash
python validate_setup.py
```

### Web Interface Setup

For the web interface, additional configuration options are available:

**Environment Variables** (optional):
```bash
# Server configuration
FLASK_HOST=127.0.0.1          # Server host (default: 127.0.0.1)
FLASK_PORT=5000               # Server port (default: 5000)
FLASK_DEBUG=True              # Debug mode (default: True)
FLASK_ENV=development         # Environment (development/production)

# Security
SECRET_KEY=your-secret-key    # Required for production

# Upload limits
MAX_UPLOAD_SIZE_MB=100        # Max file size in MB (default: 100)

# Logging
LOG_LEVEL=INFO                # Logging level (default: INFO)
LOG_FILE=web/logs/app.log     # Log file path (optional)
```

## Usage

### Web Interface (Recommended)

The easiest way to use the Audio Brief Generator is through the web interface:

1. **Start the web server**:
```bash
# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Start the web interface
cd web
python app.py
```

2. **Open your browser** and navigate to `http://127.0.0.1:5000`

3. **Record audio** directly in your browser:
   - Click "Start Recording" to begin
   - Speak into your microphone
   - Click "Stop Recording" when finished
   - The system automatically processes your audio and generates a brief

4. **Download your brief** when processing completes

#### Web Interface Features

- **Browser-based recording**: No additional software needed
- **Real-time progress**: See transcription and analysis progress
- **Automatic processing**: Pipeline starts immediately after recording
- **Brief management**: Download and preview generated briefs
- **Error handling**: Clear error messages and troubleshooting guidance
- **Cross-browser support**: Works in Chrome, Firefox, Safari, and Edge

#### Browser Requirements

- **Microphone access**: Required for recording
- **Modern browser**: Chrome 47+, Firefox 29+, Safari 14+, Edge 79+
- **JavaScript enabled**: Required for the recording interface
- **Stable internet**: Needed for AI processing

### Live Recording + Processing (Command Line)

Record a talk/presentation and automatically process it:

```bash
# Interactive mode with device selection
python record_and_process.py --interactive

# Quick start with default settings
python record_and_process.py

# With specific settings
python record_and_process.py --filename "my_talk.wav" --device 1
```

### Audio Recording Only

Record audio without processing:

```bash
# Interactive recording setup
python src/record_audio.py --interactive

# List available microphones
python src/record_audio.py --list-devices

# Test your microphone
python src/record_audio.py --test

# Record with specific device
python src/record_audio.py --device 1 --filename "recording.wav"
```

### Complete Pipeline (Existing Audio)

Process an existing audio file from start to finish:

```bash
python pipeline.py data/audio/your_file.mp3
```

With custom output name:
```bash
python pipeline.py data/audio/your_file.mp3 --output-name "my_talk"
```

### Individual Steps

Run specific pipeline steps:

```bash
# Step 1: Transcription only
python pipeline.py data/audio/your_file.mp3 --step transcribe

# Step 2: Analysis only (requires existing transcript)
python pipeline.py data/audio/your_file.mp3 --step analyze

# Step 3: Brief generation only (requires existing partials)
python pipeline.py data/audio/your_file.mp3 --step merge
```

### Direct Script Usage

You can also run individual scripts directly from the src directory:

```bash
# From project root
python src/transcribe.py data/audio/your_file.mp3 data/transcripts/output.txt
python src/analyze_chunk.py data/transcripts/input.txt data/partials/output_dir
python src/merge_brief.py data/partials/input_dir data/outputs/brief.md

# Or from src directory
cd src
python transcribe.py ../data/audio/your_file.mp3 ../data/transcripts/output.txt
python analyze_chunk.py ../data/transcripts/input.txt ../data/partials/output_dir
python merge_brief.py ../data/partials/input_dir ../data/outputs/brief.md
```

## Recording Workflow

### Live Recording During a Talk

1. **Setup**: Run `python setup_recording.py` to install audio dependencies
2. **Test**: Use `python src/record_audio.py --test` to verify your microphone
3. **Record**: Start `python record_and_process.py --interactive` before your talk
4. **Present**: The system records automatically with silence detection
5. **Process**: After recording stops, the full pipeline runs automatically
6. **Review**: Your brief is ready in `data/outputs/`

### Recording Features

- **Auto-silence detection**: Stops recording after 30 seconds of silence
- **Real-time monitoring**: Shows recording status and duration
- **Device selection**: Choose from available microphones
- **Quality validation**: Tests audio levels before recording
- **Flexible formats**: Saves as high-quality WAV files

## Example Run Logs

Here's what a typical pipeline execution looks like:

### Raw Terminal Output

```bash
❯ source .venv/bin/activate && python pipeline.py data/1_audio/sample.mp3
/Users/architsingh/Documents/projects/talk-to-brief/.venv/lib/python3.9/site-packages/urllib3/__init__.py:35: NotOpenSSLWarning: urllib3 v2 only supports OpenSSL 1.1.1+, currently the 'ssl' module is compiled with 'LibreSSL 2.8.3'. See: https://github.com/urllib3/urllib3/issues/3020
warnings.warn(
2025-09-15 04:46:13,513 - INFO - Audio file validation passed: data/1_audio/sample.mp3 (34.1 MB)
Audio Brief Generator Pipeline
Audio: data/1_audio/sample.mp3
Output: data/outputs/sample_brief.md
Started: 2025-09-15 04:46:13

Validating prerequisites...
2025-09-15 04:46:13,514 - INFO - Audio file validation passed: data/1_audio/sample.mp3 (34.1 MB)
✓ Audio file validated
✓ OpenAI API key validated
✓ Configuration files found
All prerequisites validated successfully!

============================================================
STEP 1: TRANSCRIPTION
============================================================
Audio file: data/1_audio/sample.mp3
Output: data/transcripts/sample_transcript.txt
2025-09-15 04:46:13,514 - INFO - Audio file validation passed: data/1_audio/sample.mp3 (34.1 MB)
2025-09-15 04:46:13,514 - INFO - Loading faster-whisper small model...
2025-09-15 04:46:14,960 - INFO - Starting transcription: data/1_audio/sample.mp3
2025-09-15 04:46:16,406 - INFO - Processing audio with duration 14:54.600
2025-09-15 04:46:19,401 - INFO - VAD filter removed 00:34.328 of audio
2025-09-15 04:46:19,877 - INFO - Detected language: en (probability: 1.00)
2025-09-15 04:46:19,877 - INFO - Audio duration: 894.60 seconds
2025-09-15 04:48:47,105 - INFO - Processed 123 segments
2025-09-15 04:48:47,106 - INFO - Transcript saved successfully: data/transcripts/sample_transcript.txt
✓ Transcription completed successfully

============================================================
STEP 2: CHUNK ANALYSIS
============================================================
Transcript: data/transcripts/sample_transcript.txt
Partials output: data/partials/sample/
Created 2 chunks for analysis
Processing 2 chunks in parallel (max 4 workers)...
2025-09-15 04:49:04,922 - INFO - HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
✓ Chunk 0 (1194 words)
2025-09-15 04:49:11,251 - INFO - HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
✓ Chunk 1 (1149 words)
Saved: data/partials/sample/chunk_00.json
Saved: data/partials/sample/chunk_01.json
✓ All 2 chunks processed successfully

============================================================
STEP 3: BRIEF GENERATION
============================================================
Partials: data/partials/sample/
Output: data/outputs/sample_brief.md
Found 2 partial files to merge
Loading partials from: data/partials/sample
Found 2 successful partial analyses
Merging analyses using GPT-4...
Calling GPT-4 for intelligent merging...
2025-09-15 04:49:36,235 - INFO - HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
GPT-4 merging completed successfully
Brief generated successfully: data/outputs/sample_brief.md
✓ Brief generation completed successfully

Generated brief: data/outputs/sample_brief.md (4457 bytes)

============================================================
PIPELINE COMPLETED SUCCESSFULLY
============================================================
Final brief: data/outputs/sample_brief.md
Total duration: 0:03:22.727592
Completed: 2025-09-15 04:49:36
```

### Complete Pipeline Run

```bash
$ python pipeline.py data/audio/sample.mp3
🎵 Starting Audio Brief Generator Pipeline
📁 Processing: data/audio/sample.mp3
📝 Output name: sample

=== STEP 1: TRANSCRIPTION ===
🎤 Transcribing audio with faster-whisper...
⏱️  Audio duration: 45:32
📄 Transcript saved: data/transcripts/sample_transcript.txt
✅ Transcription complete (2.3 minutes)

=== STEP 2: ANALYSIS ===
📊 Analyzing transcript in chunks...
🔄 Created 8 chunks (~1200 words each)
🚀 Starting parallel analysis with 4 workers...
  ✓ Chunk 1/8 complete (12.4s)
  ✓ Chunk 2/8 complete (15.1s)
  ✓ Chunk 3/8 complete (11.8s)
  ✓ Chunk 4/8 complete (13.7s)
  ✓ Chunk 5/8 complete (14.2s)
  ✓ Chunk 6/8 complete (12.9s)
  ✓ Chunk 7/8 complete (16.3s)
  ✓ Chunk 8/8 complete (10.8s)
💾 Analysis saved: data/partials/sample/
✅ Analysis complete (3.1 minutes)

=== STEP 3: BRIEF GENERATION ===
📋 Merging 8 partial analyses...
🔗 Combining insights and removing duplicates...
📝 Generating final brief structure...
💾 Brief saved: data/outputs/sample_brief.md
✅ Brief generation complete (0.2 minutes)

🎉 Pipeline complete! Total time: 5.6 minutes
📄 Final brief: data/outputs/sample_brief.md
```

### Live Recording Example

```bash
$ python record_and_process.py --interactive
🎙️  Interactive Recording Mode
========================================

Available audio input devices:
  0: Built-in Microphone (channels: 1)
  1: USB Headset (channels: 1)
  2: External Mic (channels: 2)

Select device ID (or press Enter for default): 1
Testing audio input for 2 seconds...
Speak into your microphone...
Audio test results:
  Max volume: 0.1234
  Average volume: 0.0456
✓ Audio levels look good!

Enter recording filename (or press Enter for auto): 
Enter brief output name (or press Enter for auto): 
Auto-stop on silence? (y/n, default: y): y

Ready to record!
Press Enter to start recording...

📹 STEP 1: RECORDING AUDIO
------------------------------
Starting recording: data/audio/talk_20241215_143022.wav
🔴 Recording... Press Ctrl+C to stop
Recording... 60s (silence: 0.0s)
Recording... 120s (silence: 0.0s)
...
Auto-stopping after 30s of silence
✅ Recording completed: data/audio/talk_20241215_143022.wav
  Duration: 1847.3 seconds
  File size: 35.2 MB

🔄 STEP 2: PROCESSING THROUGH PIPELINE
----------------------------------------
[Full pipeline execution follows...]
```

### Individual Step Examples

**Transcription only:**
```bash
$ python pipeline.py data/audio/sample.mp3 --step transcribe
🎵 Starting Audio Brief Generator Pipeline
📁 Processing: data/audio/sample.mp3
📝 Output name: sample

=== STEP 1: TRANSCRIPTION ===
🎤 Transcribing audio with faster-whisper...
⏱️  Audio duration: 45:32
📄 Transcript saved: data/transcripts/sample_transcript.txt
✅ Transcription complete (2.3 minutes)

✨ Transcription step complete!
```

**Analysis with existing transcript:**
```bash
$ python pipeline.py data/audio/sample.mp3 --step analyze
🎵 Starting Audio Brief Generator Pipeline
📁 Processing: data/audio/sample.mp3
📝 Output name: sample

=== STEP 2: ANALYSIS ===
📊 Found existing transcript: data/transcripts/sample_transcript.txt
🔄 Created 8 chunks (~1200 words each)
🚀 Starting parallel analysis with 4 workers...
  ✓ All chunks processed successfully
💾 Analysis saved: data/partials/sample/
✅ Analysis complete (3.1 minutes)

✨ Analysis step complete!
```

**Error handling example:**
```bash
$ python pipeline.py data/audio/nonexistent.mp3
🎵 Starting Audio Brief Generator Pipeline
📁 Processing: data/audio/nonexistent.mp3
❌ Error: Audio file not found: data/audio/nonexistent.mp3
💡 Tip: Check the file path and ensure the audio file exists
```

## Output Structure

For an audio file named `sample.mp3`, the pipeline generates:

```
data/
├── transcripts/sample_transcript.txt    # Timestamped transcript
├── partials/sample/                     # Individual analyses
│   ├── chunk_00.json
│   ├── chunk_01.json
│   └── ...
└── outputs/sample_brief.md              # Final structured brief
```

## Brief Format

The generated brief includes:

1. **Executive Summary** - Overview of content and insights
2. **Approach Scripts** - Conversation starters with specific timestamps
3. **Strategic Questions** - High-signal, outcome-oriented questions
4. **Timeline Highlights** - Chronological key moments
5. **Claims, Assumptions & Trade-offs** - Critical decision points

## Configuration

### Analysis Prompt

Customize the GPT-4 analysis by editing `config/per_chunk.md`. The prompt controls:
- Output format and structure
- Analysis depth and focus
- Word count limits
- Specific instructions for each section

### Pipeline Parameters

Key parameters can be adjusted in the source files:
- **Chunk size**: Modify `target_words` in `analyze_chunk.py` (default: 1200)
- **Parallel workers**: Adjust `max_workers` in `analyze_chunk.py` (default: 4)
- **GPT-4 model**: Change model in `analyze_chunk.py` (default: "gpt-4")

## Requirements

- Python 3.8+
- OpenAI API key with GPT-4 access
- Audio files in supported formats: WAV, MP3, M4A, MP4, FLAC, OGG
- Sufficient disk space for transcripts and analysis files

## Troubleshooting

### Web Interface Issues

#### Recording Problems

**Microphone not working:**
- **Chrome/Edge**: Click the microphone icon in the address bar and allow access
- **Firefox**: Click "Allow" when prompted for microphone access
- **Safari**: Go to Safari > Preferences > Websites > Microphone and allow access
- **Check system**: Ensure your microphone is working in other applications

**"MediaRecorder not supported" error:**
- Update your browser to the latest version
- Supported browsers: Chrome 47+, Firefox 29+, Safari 14+, Edge 79+
- Try a different browser if the issue persists

**Recording stops immediately:**
- Check microphone permissions in browser settings
- Ensure microphone is not being used by another application
- Try refreshing the page and allowing permissions again

**No audio captured:**
- Check system audio levels and microphone settings
- Test microphone in system settings or other applications
- Try using a different microphone or audio input device

#### Upload and Processing Issues

**"File too large" error:**
- Maximum file size is 100MB by default
- For longer recordings, use the command-line interface instead
- Check available disk space

**Processing fails or gets stuck:**
- Check internet connection for AI processing
- Verify OpenAI API key is valid and has GPT-4 access
- Check server logs in `web/logs/` for detailed error messages
- Try refreshing the page and uploading again

**"System not ready" error:**
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check that data directories exist and are writable
- Verify sufficient disk space (at least 500MB free)

#### Connection Issues

**Cannot connect to server:**
- Ensure the web server is running: `python web/app.py`
- Check the correct URL: `http://127.0.0.1:5000`
- Verify no firewall is blocking the connection
- Try a different port if 5000 is in use

**WebSocket connection fails:**
- Disable browser extensions that might block WebSockets
- Check corporate firewall settings
- Try using a different network connection

### Command Line Issues

**Missing API Key**: Ensure `OPENAI_API_KEY` is set in your environment
**Audio Format**: Verify your audio file is in a supported format
**Memory Issues**: For very long audio files, consider splitting them first
**Network Timeouts**: Check internet connection for GPT-4 API calls

### Browser Compatibility

#### Fully Supported Browsers
- **Chrome 47+**: Full feature support, recommended
- **Firefox 29+**: Full feature support
- **Safari 14+**: Full feature support (macOS/iOS)
- **Edge 79+**: Full feature support

#### Limited Support
- **Safari 13 and below**: MediaRecorder API not available
- **Internet Explorer**: Not supported
- **Chrome 46 and below**: Limited MediaRecorder support

#### Required Browser Features
- **MediaRecorder API**: For audio recording
- **WebSocket support**: For real-time updates
- **File API**: For file uploads
- **Fetch API**: For server communication

#### Mobile Browser Support
- **iOS Safari 14+**: Supported
- **Chrome Mobile 47+**: Supported
- **Firefox Mobile 29+**: Supported
- **Samsung Internet 5+**: Supported

**Note**: Mobile recording may have different audio quality and format limitations.

### Performance Tips

- Use shorter audio files (< 2 hours) for optimal performance
- Ensure stable internet connection for API calls
- Monitor API usage and rate limits
- Use SSD storage for faster I/O operations
- Close unnecessary browser tabs during processing
- Use the web interface for files under 100MB, command line for larger files

### Getting Help

If you encounter issues not covered here:

1. **Check the logs**: Look in `web/logs/` for detailed error messages
2. **Test system health**: Visit `http://127.0.0.1:5000/api/health` for system status
3. **Validate setup**: Run `python validate_setup.py` to check dependencies
4. **Try command line**: Use the command-line interface as an alternative
5. **Check browser console**: Open developer tools (F12) and check for JavaScript errors

## License

MIT License - see LICENSE file for details.