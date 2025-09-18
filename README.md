# Semantic Transcript Analysis & Question Generation

Transform your transcripts into high-leverage audience questions that create real conversation value. This AI-powered tool analyzes spoken content and generates the kind of questions that expose deep thinking, open doors for follow-up conversations, and create asymmetric value for your audience.

## Quick Start

### Setup
```bash
# Clone and setup
git clone <repository-url>
cd transcript-analysis
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt
```

### Configuration
Create a `.env` file in the backend directory with your OpenAI API key:
```bash
# In backend/.env
OPENAI_API_KEY=your_openai_api_key_here
```

### Run Analysis
```bash
# Place your transcript in data/transcripts/
python backend/main.py
```

## What You Get

### Sample Output
**Top 5 High-Leverage Questions**

1. **What specific architectural decisions would you make differently if you knew your API would need to handle 100x traffic in 6 months?**
   *Why this creates leverage: Forces discussion of proactive vs reactive scaling strategies*

2. **How do you balance the trade-off between API flexibility and performance when designing endpoints?**
   *Why this creates leverage: Exposes fundamental design philosophy and real-world constraints*

### Complete Output Package
```
📁 your-transcript/
├── 01_cleaned/ - Cleaned transcript text
├── 02_chunks/ - Semantic chunks with metadata
├── 04_questions/ - The main event: your questions!
│   ├── final_top5_questions.md - Your top 5 questions (human-readable)
│   ├── final_top5_questions.json - Machine-readable format
│   └── analysis_*.md - Detailed analysis per chunk
└── metadata/ - Processing stats and configuration
```

## How It Works

### The 3-Step Analysis Process

**Step 1: Summarization Layer**
- Extracts main arguments and claims
- Identifies supporting evidence
- Spots assumptions and biases
- Notes unanswered questions

**Step 2: Critical Thinking Layer**
- Finds weak spots in arguments
- Explores contrarian angles
- Considers future implications
- Identifies personalization hooks

**Step 3: Question Generation**
- Creates 8-10 questions per section
- Ranks by "asymmetric return" potential
- Focuses on audience value
- Synthesizes into top 5 overall

### Why This Approach Works

Traditional Q&A focuses on clarification. This tool generates questions that:
- **Expose Deep Thinking**: Go beyond surface-level understanding
- **Create Conversation Value**: Open doors for meaningful follow-up
- **Generate Asymmetric Returns**: Small questions that unlock big insights
- **Connect to Context**: Link to speaker's background and current work

## Supported Content

- **Conference Talks**: Technical presentations, keynotes
- **Podcast Transcripts**: Interview-style content
- **Workshop Content**: Educational material
- **Meeting Transcripts**: Strategic discussions
- **Webinar Content**: Any spoken presentation format

**Sweet Spot**: 5,000-50,000 characters of substantive content with clear arguments and evidence.

## Configuration

Adjust processing in `backend/config/settings.py`:

```python
INPUT_TXT = "data/transcripts/your-file.txt"  # Your transcript
BUFFER_SIZE = 3             # Semantic chunking window
BREAKPOINT_THRESHOLD = 92   # Chunk boundary sensitivity
MIN_CHUNK_SIZE = 500        # Minimum chunk size
MAX_CHUNK_SIZE = 3000       # Maximum chunk size
```

## Troubleshooting

**"No questions generated"**
- Check transcript length (needs 2,000+ characters)
- Ensure content has substantive arguments/claims
- Verify OpenAI API key is working

**"Processing failed"**
- Check internet connection for OpenAI API
- Verify API key has sufficient credits
- Try with the sample transcript first

---

# Developer Documentation

## Architecture Overview

The codebase follows a clean, modular architecture with clear separation of concerns:

```
backend/
├── config/           # Configuration and settings
├── data/            # Data layer and file management
├── processors/      # Text processing and transformation
├── services/        # Business logic and orchestration
├── utils/           # Utilities and logging
├── main.py          # Entry point and pipeline orchestration
├── openai_client.py # OpenAI API client with structured outputs
├── prompts.py       # AI prompt templates
└── schemas.py       # JSON schemas for structured responses
```

## Core Components

### 1. Text Processing Pipeline (`processors/text_processor.py`)
- **Transcript Cleaning**: Removes timestamps, speaker labels, stage directions
- **Semantic Chunking**: Uses LlamaIndex with OpenAI embeddings for intelligent text segmentation
- **Adaptive Strategies**: Automatically adjusts chunking parameters based on content length
- **Quality Control**: Post-processes chunks to ensure optimal size and continuity

### 2. Question Generation Pipeline (`services/question_pipeline.py`)
Three-step AI analysis process with structured JSON outputs:

```python
class QuestionGenerationPipeline:
    def step1_summarization(self, chunk: str)
    def step2_critical_thinking(self, summary)
    def step3_question_generation(self, critical_analysis)
    def merge_final_questions(self, all_question_sets)
```

### 3. OpenAI Client (`openai_client.py`)
Generalized interface for structured AI completions:

```python
client = OpenAIClient()
result = client.structured_completion(
    messages=messages,
    schema=schema,
    schema_name="OutputSchema",
    config=CompletionConfig(model=ModelType.GPT_5_NANO)
)
```

### 4. File Management (`data/file_manager.py`)
- Organized artifact storage with full traceability
- JSON metadata for all processing steps
- Human-readable outputs alongside machine data
- Comprehensive directory structure management

## Key Features

### Semantic Chunking
- Uses OpenAI embeddings for context-aware text segmentation
- Adaptive parameters based on content characteristics
- Post-processing for quality assurance
- Overlap handling for continuity

### Structured AI Processing
- JSON schema-validated responses
- Consistent data structures across all steps
- Error handling and graceful degradation
- Comprehensive logging and metrics

### Artifact Management
- Complete processing history preservation
- Human-readable and machine-readable formats
- Metadata tracking for reproducibility
- Organized directory structure

## Dependencies

Core dependencies:
- **OpenAI**: AI completions and embeddings
- **LlamaIndex**: Document processing and semantic chunking
- **Python-dotenv**: Environment variable management
- **Pydantic**: Data validation and schemas

See `requirements.txt` for complete dependency list.

## Extending the System

### Adding New Processing Steps
1. Create new service in `services/`
2. Add corresponding schema in `schemas.py`
3. Update orchestrator in `services/orchestrator.py`
4. Add file management in `data/file_manager.py`

### Custom Chunking Strategies
Implement in `processors/text_processor.py`:
```python
def custom_chunking_strategy(text, **params):
    # Your implementation
    return chunks
```

### New AI Models
Add to `openai_client.py`:
```python
class ModelType(Enum):
    YOUR_MODEL = "your-model-name"
```

## Performance Considerations

- **Chunking**: Adaptive strategies optimize for content type
- **AI Calls**: Structured outputs reduce parsing overhead
- **File I/O**: Efficient artifact management with metadata
- **Memory**: Streaming processing for large transcripts

## Error Handling

- Graceful degradation for failed chunks
- Comprehensive error logging
- Partial results preservation
- Recovery mechanisms for interrupted processing

## Security

- API key management through environment variables
- Input validation and sanitization
- Safe file operations with path validation
- No sensitive data in logs or artifacts

## Contributing

1. Follow the existing architecture patterns
2. Add comprehensive logging for new features
3. Include JSON schemas for structured outputs
4. Update documentation for new components
5. Test with various transcript formats and sizes

## What Makes This Different

Unlike simple Q&A generators that focus on comprehension, this tool:
- **Thinks Critically**: Identifies assumptions and weak spots
- **Considers Context**: Connects to speaker background and current trends
- **Optimizes for Value**: Ranks questions by their potential impact
- **Preserves Nuance**: Maintains the complexity of the original content
- **Creates Leverage**: Generates questions that unlock disproportionate insight

Perfect for content creators, interviewers, educators, and anyone who wants to extract maximum value from spoken content.


# sample run

```bash
❯ source .venv/bin/activate && python backend/main.py
/Users/architsingh/Documents/projects/talk-to-brief/.venv/lib/python3.9/site-packages/urllib3/__init__.py:35: NotOpenSSLWarning: urllib3 v2 only supports OpenSSL 1.1.1+, currently the 'ssl' module is compiled with 'LibreSSL 2.8.3'. See: https://github.com/urllib3/urllib3/issues/3020
  warnings.warn(

════════════════════════════════════════════════════════════════════════════════
               SEMANTIC TRANSCRIPT ANALYSIS & QUESTION GENERATION               
════════════════════════════════════════════════════════════════════════════════
ℹ Input transcript: data/transcripts/building-scalable-apis.txt
ℹ Semantic chunking: 3 sentence buffer, 92% threshold
ℹ AI Model: GPT-5-Nano
  ✓ Created cleaned directory
  ✓ Created chunks directory
  ✓ Created summaries directory
  ✓ Created metadata directory
✓ Initialized workspace: data/processed/building-scalable-apis

────────────────────────────────────────────────────────────
            Text Processing & Semantic Chunking             
────────────────────────────────────────────────────────────
   💾 Saved: data/processed/building-scalable-apis/01_cleaned/cleaned_transcript.txt
      Cleaned transcript text
   • Text reduction: 0.6%
   • Original chars: 2,625
   • Cleaned chars: 2,608
ℹ Using dense content, smaller chunks
   • Buffer size: 2
   • Threshold: 85%
ℹ Generating semantic chunks...
✓ Generated 5 semantic chunks
ℹ Post-processing chunks for quality...
ℹ Adding overlap for continuity...
✓ Generated 3 enhanced semantic chunks
   💾 Saved: data/processed/building-scalable-apis/02_chunks/chunk_index.json
      Enhanced chunk index and metadata
   • Average chunk size: 953 chars
   • Size range: 722 - 1,248 chars
   • Size variance: 526 chars
   • Quality ratio: 100.0%
✓ Transcript processed into 3 semantic chunks

════════════════════════════════════════════════════════════════════════════════
                      3-STEP QUESTION GENERATION PIPELINE                       
════════════════════════════════════════════════════════════════════════════════
ℹ Step 1: Summarization Layer - Extract main points, evidence, assumptions
ℹ Step 2: Critical Thinking Layer - Identify weak spots, contrarian angles
ℹ Step 3: Question Generation - Create high-leverage audience questions

────────────────────────────────────────────────────────────
                    Processing 3 Chunks                     
────────────────────────────────────────────────────────────
📊 Progress: [░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░] 0.0% (0/3 chunks)  ℹ Processing chunk 1 (1,248 chars)
    ℹ Step 1: Summarization Layer
      ✓ Extracted 4 main points, 3 assumptions
    ℹ Step 2: Critical Thinking Layer
      ✓ Identified 3 weak spots, 3 contrarian angles
    ℹ Step 3: Question Generation & Ranking
      ✓ Generated 9 questions (top rank: 10)
   ⏱ Chunk 1 completed in 1m 12.1s
      ℹ Top question (rank 10): If your app requires per-user personalization, can a truly s...
📊 Progress: [██████████░░░░░░░░░░░░░░░░░░░░] 33.3% (1/3 chunks)  ℹ Processing chunk 2 (722 chars)
    ℹ Step 1: Summarization Layer
      ✓ Extracted 4 main points, 3 assumptions
    ℹ Step 2: Critical Thinking Layer
      ✓ Identified 3 weak spots, 3 contrarian angles
    ℹ Step 3: Question Generation & Ranking
      ✓ Generated 9 questions (top rank: 10)
   ⏱ Chunk 2 completed in 1m 1.7s
      ℹ Top question (rank 10): If we rely on multiple DB instances to boost reads, under wh...
📊 Progress: [████████████████████░░░░░░░░░░] 66.7% (2/3 chunks)  ℹ Processing chunk 3 (890 chars)
    ℹ Step 1: Summarization Layer
      ✓ Extracted 4 main points, 3 assumptions
    ℹ Step 2: Critical Thinking Layer
      ✓ Identified 3 weak spots, 3 contrarian angles
    ℹ Step 3: Question Generation & Ranking
      ✓ Generated 9 questions (top rank: 9)
   ⏱ Chunk 3 completed in 1m 7.0s
      ℹ Top question (rank 9): Can a well-designed monolith scale as effectively as microse...
📊 Progress: [██████████████████████████████] 100.0% (3/3 chunks)

────────────────────────────────────────────────────────────
                  Chunk Processing Summary                  
────────────────────────────────────────────────────────────
   • Successful chunks: 3
   • Failed chunks: 0
   • Success rate: 100.0%

────────────────────────────────────────────────────────────
                  Final Question Synthesis                  
────────────────────────────────────────────────────────────
ℹ Merging and ranking questions from all chunks...
✓ Synthesized 5 top questions from 3 chunks
   ⏱ Question synthesis completed in 26.01s

────────────────────────────────────────────────────────────
                      Saving Artifacts                      
────────────────────────────────────────────────────────────
   💾 Saved: data/processed/building-scalable-apis/04_questions
      Question analysis directory
   💾 Saved: data/processed/building-scalable-apis/04_questions/final_top5_questions.md
      Human-readable final questions
   💾 Saved: data/processed/building-scalable-apis/04_questions/final_top5_questions.json
      Machine-readable final questions (JSON)
   ⏱ Complete question generation pipeline completed in 3m 46.8s
   💾 Saved: data/processed/building-scalable-apis/metadata/processing_metadata.json
      Pipeline configuration and statistics

════════════════════════════════════════════════════════════════════════════════
                               PIPELINE COMPLETE                                
════════════════════════════════════════════════════════════════════════════════

📁 Output Structure:
data/processed/building-scalable-apis
├── 01_cleaned/ - Cleaned transcript text
├── 02_chunks/ - 3 semantic chunks
├── 03_summaries/ - Legacy summaries (deprecated)
├── 04_questions/ - 3-step question analysis
└── metadata/ - Processing metadata & config

────────────────────────────────────────────────────────────
             High-Leverage Questions Generated              
────────────────────────────────────────────────────────────
✓ Generated 5 high-leverage questions

1. How would you design a hybrid model that preserves statelessness but still gu...
   💡 High asymmetry: challenges the default stateless approach by forcing a deep dive into patterns like CQRS/Sagas and hybrid read/write designs; connects data consistency, latency, and governance across architectures.

2. When does TTL-based caching become a correctness risk, and what signals would...
   💡 Targets a concrete, actionable correctness risk with observable signals; yields guardrails, monitoring strategies, and testable assumptions.

3. Could external dependencies be the true bottlenecks, making internal observab...
   💡 Shifts focus from internal systems to vendor reliability and integration risk; creates asymmetry by challenging assumptions about controllability and connected SLAs.

4. If tracing is noisy and causes alert fatigue, what practical heuristics separ...
   💡 Transforms observability into actionable, repeatable practices; directly improves MTTR and decision quality, with cross-cutting impact on tooling and process.

5. With AI-assisted observability auto-triage, will teams over-rely on automatio...
   💡 Probes governance and potential failure modes of automation; connects design quality, security, and operational practices in a future-facing context.

────────────────────────────────────────────────────────────
                    Pipeline Statistics                     
────────────────────────────────────────────────────────────
   • Chunks processed: 3/3
   • Success rate: 100.0%
   • Questions generated: 5
   • Average chunk size: 953 chars
   ⏱ Complete pipeline completed in 3m 48.5s
ℹ Full analysis available at: data/processed/building-scalable-apis/04_questions
~/Documents/projects/talk-to-brief v2 ?3                         3m 50s Py talk-to-brief 02:14:38 AM
❯ 
```