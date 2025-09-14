# Requirements

**Core Goal:** 30min audio → 1-page brief in ≤6 minutes

## Essential Requirements

1. **Audio → Transcript**: Local transcription with word-level timestamps using faster-whisper (large-v3 model)
2. **Two-Pass Analysis**: Parallel chunk processing (~1200 words/chunk) → intelligent merge using GPT-4  
3. **Structured Output**: Generate brief.md with approach script, 5 questions, highlights, claims/assumptions/trade-offs
4. **Simple Setup**: pip install + OPENAI_API_KEY only
5. **Multi-Format Support**: Accept wav, mp3, m4a audio inputs