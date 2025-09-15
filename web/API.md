# Web Audio Recorder API Documentation

This document provides comprehensive documentation for the Web Audio Recorder API endpoints and WebSocket events.

## Base URL

```
http://127.0.0.1:5000
```

## Authentication

No authentication is required for local development. For production deployment, consider implementing appropriate authentication mechanisms.

## HTTP API Endpoints

### Health and Status

#### GET /api/health

Health check endpoint for monitoring server status and connectivity.

**Response:**
```json
{
  "status": "healthy|unhealthy",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "version": "1.0.0",
  "system": {
    "audio_upload_dir": true,
    "briefs_dir": true,
    "pipeline_available": true
  },
  "statistics": {
    "active_jobs": 2,
    "total_jobs": 15,
    "error_counts": {
      "upload_errors": 0,
      "validation_errors": 1,
      "pipeline_errors": 0,
      "system_errors": 0
    }
  },
  "warnings": ["Low disk space: 1.2GB available"]
}
```

**Status Codes:**
- `200 OK`: System is healthy
- `503 Service Unavailable`: System has issues

#### GET /api/system/status

Get detailed system status and statistics.

**Response:**
```json
{
  "timestamp": "2024-01-15T10:30:00.000Z",
  "system": {
    "disk_usage": {
      "total_gb": 500.0,
      "used_gb": 450.0,
      "free_gb": 50.0,
      "usage_percent": 90.0
    },
    "directories": {
      "audio_upload": {
        "path": "/path/to/data/1_audio",
        "exists": true,
        "writable": true
      },
      "briefs_output": {
        "path": "/path/to/data/outputs",
        "exists": true,
        "writable": true
      }
    }
  },
  "jobs": {
    "total": 15,
    "running": 2,
    "completed": 12,
    "failed": 1,
    "success_rate": 0.8
  },
  "errors": {
    "upload_errors": 0,
    "validation_errors": 1,
    "pipeline_errors": 0,
    "system_errors": 0
  },
  "active_connections": 3
}
```

### Audio Upload

#### POST /api/upload-audio

Upload an audio file for processing.

**Request:**
- Content-Type: `multipart/form-data`
- Form field: `audio` (file)

**Supported Audio Formats:**
- WAV (recommended)
- MP3
- OGG
- WebM
- M4A

**File Size Limits:**
- Maximum: 100MB (configurable)
- Minimum: 1KB

**Response (Success):**
```json
{
  "success": true,
  "filename": "recording_20240115_103000.wav",
  "filepath": "/path/to/data/1_audio/recording_20240115_103000.wav",
  "size": 1024000,
  "job_id": "uuid-string",
  "message": "Audio file saved as recording_20240115_103000.wav and processing started",
  "warnings": ["Low disk space: 1.2GB available"]
}
```

**Response (Error):**
```json
{
  "error": "File too large (150.5MB). Maximum size: 100MB",
  "details": "Additional error details if available"
}
```

**Status Codes:**
- `200 OK`: File uploaded and processing started
- `400 Bad Request`: Invalid file or validation error
- `413 Payload Too Large`: File exceeds size limit
- `500 Internal Server Error`: Server error
- `503 Service Unavailable`: System not ready

### Job Management

#### GET /api/status/<job_id>

Get the status of a specific processing job.

**Parameters:**
- `job_id`: UUID of the job

**Response:**
```json
{
  "job_id": "uuid-string",
  "status": "running|completed|failed",
  "current_step": "transcription|analysis|merge",
  "progress": 0.75,
  "audio_file": "/path/to/audio.wav",
  "brief_file": "/path/to/brief.md",
  "error_message": null,
  "started_at": "2024-01-15T10:30:00.000Z",
  "completed_at": null,
  "estimated_completion": "2024-01-15T10:35:00.000Z"
}
```

**Status Codes:**
- `200 OK`: Job found
- `404 Not Found`: Job not found

#### GET /api/jobs

Get status of all jobs.

**Response:**
```json
{
  "jobs": {
    "uuid-1": { /* job status object */ },
    "uuid-2": { /* job status object */ }
  },
  "statistics": {
    "total": 15,
    "running": 2,
    "completed": 12,
    "failed": 1,
    "success_rate": 0.8,
    "average_duration_minutes": 3.5
  }
}
```

#### GET /api/jobs/<status>

Get jobs filtered by status.

**Parameters:**
- `status`: `running`, `completed`, or `failed`

**Response:**
```json
{
  "jobs": [
    { /* job status object */ },
    { /* job status object */ }
  ]
}
```

#### POST /api/jobs/<job_id>/cancel

Cancel a running job.

**Response:**
```json
{
  "success": true,
  "message": "Job cancelled"
}
```

**Status Codes:**
- `200 OK`: Job cancelled
- `400 Bad Request`: Job cannot be cancelled

#### POST /api/jobs/<job_id>/retry

Retry a failed job.

**Response:**
```json
{
  "success": true,
  "new_job_id": "new-uuid-string",
  "message": "Job retry started"
}
```

### Brief Management

#### GET /api/briefs

List all available brief files with metadata.

**Response:**
```json
{
  "briefs": [
    {
      "name": "sample_brief.md",
      "filename": "sample_brief.md",
      "size": 4457,
      "created_at": "2024-01-15T10:30:00.000Z",
      "modified_at": "2024-01-15T10:35:00.000Z",
      "preview": "# Executive Summary\n\nThis brief covers..."
    }
  ]
}
```

#### GET /api/brief/<filename>

Download a specific brief file.

**Parameters:**
- `filename`: Name of the brief file (must end with .md)

**Response:**
- Content-Type: `text/markdown`
- Content-Disposition: `attachment; filename="brief.md"`
- File content as response body

**Status Codes:**
- `200 OK`: File downloaded
- `400 Bad Request`: Invalid filename
- `404 Not Found`: File not found

## WebSocket Events

The WebSocket connection is established at the root path (`/`) and provides real-time updates for job processing.

### Client → Server Events

#### connect

Establish WebSocket connection.

**Response:**
```json
{
  "event": "connected",
  "data": {
    "message": "Connected to server"
  }
}
```

#### join_job

Join a job room to receive updates for a specific job.

**Request:**
```json
{
  "job_id": "uuid-string"
}
```

**Response:**
```json
{
  "event": "job_joined",
  "data": {
    "job_id": "uuid-string"
  }
}
```

### Server → Client Events

#### pipeline_started

Emitted when pipeline processing begins.

**Data:**
```json
{
  "job_id": "uuid-string",
  "audio_file": "/path/to/audio.wav",
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

#### pipeline_progress

Emitted during pipeline processing to show progress.

**Data:**
```json
{
  "job_id": "uuid-string",
  "step": "transcription|analysis|merge",
  "progress": 0.75,
  "message": "Processing chunk 3 of 4",
  "timestamp": "2024-01-15T10:32:30.000Z"
}
```

#### pipeline_completed

Emitted when pipeline processing completes successfully.

**Data:**
```json
{
  "job_id": "uuid-string",
  "brief_file": "/path/to/brief.md",
  "duration_seconds": 180,
  "timestamp": "2024-01-15T10:35:00.000Z"
}
```

#### pipeline_error

Emitted when pipeline processing fails.

**Data:**
```json
{
  "job_id": "uuid-string",
  "error": "Error message",
  "step": "transcription|analysis|merge",
  "timestamp": "2024-01-15T10:33:00.000Z"
}
```

## Error Handling

### Error Response Format

All API errors follow a consistent format:

```json
{
  "error": "Human-readable error message",
  "details": "Additional technical details (optional)",
  "code": "ERROR_CODE (optional)",
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

### Common Error Codes

- `INVALID_FILE_TYPE`: Unsupported audio format
- `FILE_TOO_LARGE`: File exceeds size limit
- `INSUFFICIENT_SPACE`: Not enough disk space
- `PIPELINE_UNAVAILABLE`: Pipeline dependencies missing
- `VALIDATION_FAILED`: File validation failed
- `PROCESSING_FAILED`: Pipeline processing error

### HTTP Status Codes

- `200 OK`: Request successful
- `400 Bad Request`: Invalid request or validation error
- `404 Not Found`: Resource not found
- `413 Payload Too Large`: File too large
- `500 Internal Server Error`: Server error
- `503 Service Unavailable`: Service temporarily unavailable

## Rate Limiting

Currently, no rate limiting is implemented. For production deployment, consider implementing:

- Request rate limiting per IP
- Concurrent job limits per client
- File upload frequency limits

## CORS Configuration

In development mode, CORS is configured to allow all origins (`*`). For production deployment, configure specific allowed origins using the `CORS_ORIGINS` environment variable.

## Security Considerations

### Input Validation

- File type validation based on extension and content type
- File size limits to prevent resource exhaustion
- Filename sanitization to prevent path traversal
- Content validation for audio files

### File Handling

- Secure filename generation with timestamps
- Automatic cleanup of failed uploads
- Directory traversal protection
- File permission validation

### Production Deployment

For production deployment, ensure:

- Set `SECRET_KEY` environment variable
- Configure appropriate CORS origins
- Implement authentication if needed
- Use HTTPS for secure communication
- Set up proper logging and monitoring

## Development and Testing

### Running the Development Server

```bash
cd web
python app.py
```

### Environment Variables for Development

```bash
FLASK_DEBUG=True
FLASK_ENV=development
LOG_LEVEL=DEBUG
```

### Testing API Endpoints

Use tools like curl, Postman, or HTTPie to test endpoints:

```bash
# Health check
curl http://127.0.0.1:5000/api/health

# Upload audio file
curl -X POST -F "audio=@test.wav" http://127.0.0.1:5000/api/upload-audio

# Get job status
curl http://127.0.0.1:5000/api/status/job-id

# List briefs
curl http://127.0.0.1:5000/api/briefs
```

### WebSocket Testing

Use browser developer tools or WebSocket testing tools to test real-time functionality.

## Deployment Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `FLASK_HOST` | `127.0.0.1` | Server host address |
| `FLASK_PORT` | `5000` | Server port |
| `FLASK_DEBUG` | `True` | Debug mode |
| `FLASK_ENV` | `development` | Environment |
| `SECRET_KEY` | `dev-key-change-in-production` | Flask secret key |
| `MAX_UPLOAD_SIZE_MB` | `100` | Maximum upload size |
| `LOG_LEVEL` | `INFO` | Logging level |
| `LOG_FILE` | None | Log file path |
| `CORS_ORIGINS` | `*` | Allowed CORS origins |
| `PIPELINE_TIMEOUT_MINUTES` | `30` | Pipeline timeout |

### Production Checklist

- [ ] Set secure `SECRET_KEY`
- [ ] Configure appropriate `CORS_ORIGINS`
- [ ] Set `FLASK_ENV=production`
- [ ] Set `FLASK_DEBUG=False`
- [ ] Configure logging to files
- [ ] Set up reverse proxy (nginx/Apache)
- [ ] Configure HTTPS
- [ ] Set up monitoring and alerting
- [ ] Configure backup for data directories
- [ ] Test error handling and recovery