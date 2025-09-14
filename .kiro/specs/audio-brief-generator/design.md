# Design

**Pipeline:** `audio file` → `transcribe.py` → `analyze_chunk.py` → `merge_brief.py` → `brief.md`

## Two-Pass Flow

1. **Pass 1**: Split transcript into ~4 chunks (1200 words each) → parallel GPT-4 calls → save partials
2. **Pass 2**: Merge partials → deduplicate → final brief.md

## Core Scripts

- `transcribe.py`: faster-whisper (large-v3) → word-level timestamped transcript
- `analyze_chunk.py`: intelligent chunking + parallel GPT-4 → partials/*.json  
- `merge_brief.py`: merge partials → brief.md

## Technical Details

- **Model**: faster-whisper large-v3 for accuracy
- **Chunking**: ~1200 words/chunk with sentence boundary respect
- **API**: GPT-4 with 10 RPM parallel processing
- **Formats**: Support wav, mp3, m4a inputs

## Output Format
```markdown
# Approach Script (3 lines)
# Five Questions ([mm:ss] timestamps)  
# Timeline Highlights (8-12 bullets)
# Claims/Assumptions/Trade-offs
```