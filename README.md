# Audio Brief Generator

A complete pipeline for converting audio files into structured, actionable briefs using AI analysis.

## Features

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
├── data/                    # All data artifacts
│   ├── audio/               # Input audio files
│   ├── transcripts/         # Generated transcripts
│   ├── partials/            # Individual chunk analyses
│   └── outputs/             # Final briefs
└── requirements.txt         # Python dependencies
```

## Installation

1. Clone the repository
2. Create virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up your OpenAI API key:
   - Create a `.env` file in the project root
   - Add your OpenAI API key:
   ```
   OPENAI_API_KEY=your-api-key-here
   ```
   - **Important**: Ensure you have GPT-4 access on your OpenAI account
   - **Security**: Never commit the `.env` file to version control

5. Set up audio recording (optional):
```bash
python setup_recording.py
```

6. Validate your setup:
```bash
python validate_setup.py
```

## Usage

### Live Recording + Processing (New!)

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

### Common Issues

1. **Missing API Key**: Ensure `OPENAI_API_KEY` is set in your environment
2. **Audio Format**: Verify your audio file is in a supported format
3. **Memory Issues**: For very long audio files, consider splitting them first
4. **Network Timeouts**: Check internet connection for GPT-4 API calls

### Performance Tips

- Use shorter audio files (< 2 hours) for optimal performance
- Ensure stable internet connection for API calls
- Monitor API usage and rate limits
- Use SSD storage for faster I/O operations

## License

MIT License - see LICENSE file for details.