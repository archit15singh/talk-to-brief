"""
Simple API server to serve processed data from backend/data/processed
"""
import json
import os
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import shutil

app = FastAPI(title="Processed Data API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for frontend
app.mount("/static", StaticFiles(directory="../frontend"), name="static")

# Base paths (relative to backend folder when running from backend/)
PROCESSED_DATA_PATH = Path("../data/processed")
RAW_SOURCE_PATH = Path("../data/raw-source")

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {"message": "Processed Data API with Voice Recorder", "version": "1.0.0", "recorder": "/recorder"}

@app.get("/datasets")
async def list_datasets():
    """List all available datasets"""
    datasets = []
    if PROCESSED_DATA_PATH.exists():
        for item in PROCESSED_DATA_PATH.iterdir():
            if item.is_dir():
                datasets.append(item.name)
    return {"datasets": datasets}

@app.get("/datasets/{dataset_name}")
async def get_dataset_info(dataset_name: str):
    """Get information about a specific dataset"""
    dataset_path = PROCESSED_DATA_PATH / dataset_name
    
    if not dataset_path.exists():
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    # Get all subdirectories and their contents
    structure = {}
    for item in dataset_path.iterdir():
        if item.is_dir():
            files = [f.name for f in item.iterdir() if f.is_file()]
            structure[item.name] = files
    
    return {
        "dataset": dataset_name,
        "structure": structure
    }

@app.get("/datasets/{dataset_name}/cleaned")
async def get_cleaned_data(dataset_name: str):
    """Get cleaned transcript data"""
    cleaned_path = PROCESSED_DATA_PATH / dataset_name / "01_cleaned"
    
    if not cleaned_path.exists():
        raise HTTPException(status_code=404, detail="Cleaned data not found")
    
    # Read cleaned transcript
    transcript_file = cleaned_path / "cleaned_transcript.txt"
    metadata_file = cleaned_path / "cleaning_metadata.json"
    
    result = {}
    
    if transcript_file.exists():
        with open(transcript_file, 'r', encoding='utf-8') as f:
            result["transcript"] = f.read()
    
    if metadata_file.exists():
        with open(metadata_file, 'r', encoding='utf-8') as f:
            result["metadata"] = json.load(f)
    
    return result

@app.get("/datasets/{dataset_name}/chunks")
async def get_chunks(dataset_name: str):
    """Get all chunks for a dataset"""
    chunks_path = PROCESSED_DATA_PATH / dataset_name / "02_chunks"
    
    if not chunks_path.exists():
        raise HTTPException(status_code=404, detail="Chunks not found")
    
    # Read chunk index
    index_file = chunks_path / "chunk_index.json"
    chunks = []
    
    if index_file.exists():
        with open(index_file, 'r', encoding='utf-8') as f:
            chunk_index = json.load(f)
        
        # Read each chunk file
        for chunk_info in chunk_index.get("chunks", []):
            chunk_file = chunks_path / chunk_info.get("file", "")
            if chunk_file.exists():
                with open(chunk_file, 'r', encoding='utf-8') as f:
                    chunks.append({
                        "id": chunk_info.get("chunk_id"),
                        "filename": chunk_info.get("file"),
                        "content": f.read(),
                        "metadata": chunk_info
                    })
    
    return {"chunks": chunks}

@app.get("/datasets/{dataset_name}/chunks/{chunk_id}")
async def get_chunk(dataset_name: str, chunk_id: str):
    """Get a specific chunk by ID"""
    chunks_path = PROCESSED_DATA_PATH / dataset_name / "02_chunks"
    
    if not chunks_path.exists():
        raise HTTPException(status_code=404, detail="Chunks not found")
    
    # Find the chunk file
    chunk_file = chunks_path / f"chunk_{chunk_id.zfill(3)}.txt"
    
    if not chunk_file.exists():
        raise HTTPException(status_code=404, detail="Chunk not found")
    
    with open(chunk_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    return {
        "chunk_id": chunk_id,
        "content": content
    }

@app.get("/datasets/{dataset_name}/summaries")
async def get_summaries(dataset_name: str):
    """Get summaries for a dataset"""
    summaries_path = PROCESSED_DATA_PATH / dataset_name / "03_summaries"
    
    if not summaries_path.exists():
        raise HTTPException(status_code=404, detail="Summaries not found")
    
    summaries = []
    for file in summaries_path.glob("*.json"):
        with open(file, 'r', encoding='utf-8') as f:
            summary_data = json.load(f)
            summaries.append({
                "filename": file.name,
                "data": summary_data
            })
    
    return {"summaries": summaries}

@app.get("/datasets/{dataset_name}/questions")
async def get_questions(dataset_name: str):
    """Get questions for a dataset"""
    questions_path = PROCESSED_DATA_PATH / dataset_name / "04_questions"
    
    if not questions_path.exists():
        raise HTTPException(status_code=404, detail="Questions not found")
    
    questions = []
    for file in questions_path.glob("*.json"):
        with open(file, 'r', encoding='utf-8') as f:
            question_data = json.load(f)
            questions.append({
                "filename": file.name,
                "data": question_data
            })
    
    return {"questions": questions}

@app.post("/api/save-recording")
async def save_recording(audio: UploadFile = File(...)):
    """Save uploaded audio recording to data/raw-source"""
    try:
        # Ensure the raw-source directory exists
        RAW_SOURCE_PATH.mkdir(parents=True, exist_ok=True)
        
        # Save the uploaded file
        file_path = RAW_SOURCE_PATH / audio.filename
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(audio.file, buffer)
        
        return {
            "message": "Recording saved successfully",
            "filename": audio.filename,
            "path": str(file_path)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving recording: {str(e)}")

@app.get("/recorder")
async def serve_frontend():
    """Serve the frontend application"""
    from fastapi.responses import FileResponse
    return FileResponse("../frontend/index.html")

def start_server():
    """Start the voice recorder application server"""
    # Ensure the raw-source directory exists
    RAW_SOURCE_PATH.mkdir(parents=True, exist_ok=True)
    
    print("Starting Voice Recorder & Data API Server...")
    print("Frontend available at: http://localhost:8000/recorder")
    print("API docs available at: http://localhost:8000/docs")
    print("Press Ctrl+C to stop the server")
    
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    start_server()