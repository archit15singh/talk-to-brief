# Data Folder Hierarchy

This folder contains all pipeline artifacts with full traceability from source transcripts to final summaries.

## Structure

```
data/
├── transcripts/                    # Source transcript files
│   └── building-scalable-apis.md   # Raw transcript input
│
└── processed/                      # Pipeline processing artifacts
    └── {transcript-name}/          # One folder per processed transcript
        ├── 01_cleaned/             # Text cleaning stage
        │   ├── cleaned_transcript.txt
        │   └── cleaning_metadata.json
        │
        ├── 02_chunks/              # Semantic chunking stage  
        │   ├── chunk_001.txt
        │   ├── chunk_002.txt
        │   ├── ...
        │   └── chunk_index.json
        │
        ├── 03_summaries/           # Summarization stage
        │   ├── summary_001.txt
        │   ├── summary_002.txt
        │   ├── ...
        │   └── summary_index.json
        │
        └── metadata/               # Overall processing metadata
            └── processing_metadata.json
```

## Traceability

Each artifact maintains full traceability:

1. **Source → Cleaned**: `cleaning_metadata.json` tracks text reduction stats
2. **Cleaned → Chunks**: `chunk_index.json` maps chunks with previews and stats  
3. **Chunks → Summaries**: Each `summary_XXX.txt` includes source chunk reference
4. **Overall**: `processing_metadata.json` contains full pipeline configuration and stats

## File Contents

### Metadata Files

- **cleaning_metadata.json**: Character counts, reduction ratios
- **chunk_index.json**: Chunk mapping, sizes, previews, chunking config
- **summary_index.json**: Summary mapping, compression ratios, source links
- **processing_metadata.json**: Pipeline config, timestamps, overall stats

### Content Files

- **cleaned_transcript.txt**: Processed transcript (timestamps/speakers removed)
- **chunk_XXX.txt**: Individual semantic chunks
- **summary_XXX.txt**: Summaries with traceability headers

## Usage

```python
# Run pipeline (saves all artifacts)
python pipeline.py

# Trace artifacts for a transcript
python trace_artifacts.py
```

## Benefits

- **Full Traceability**: Track any summary back to its source chunk and original transcript
- **Reproducibility**: All processing parameters and timestamps preserved
- **Debugging**: Inspect intermediate stages when results are unexpected
- **Analytics**: Compare processing stats across different configurations
- **Incremental Processing**: Skip stages that are already complete