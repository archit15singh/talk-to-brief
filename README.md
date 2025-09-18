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
pip install -r requirements.txt
```

### Configuration
Create a `.env` file with your OpenAI API key:
```
OPENAI_API_KEY=your_openai_api_key_here
```

### Run Analysis
```bash
# Place your transcript in data/transcripts/
python src/main.py
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

Adjust processing in `src/config/settings.py`:

```python
INPUT_TXT = "data/transcripts/your-file.md"  # Your transcript
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
src/
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