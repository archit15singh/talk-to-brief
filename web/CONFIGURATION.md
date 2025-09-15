# Web Audio Recorder Configuration Guide

This document provides comprehensive configuration options for the Web Audio Recorder system.

## Table of Contents

1. [Environment Variables](#environment-variables)
2. [Configuration Classes](#configuration-classes)
3. [Flask Configuration](#flask-configuration)
4. [WebSocket Configuration](#websocket-configuration)
5. [File Upload Configuration](#file-upload-configuration)
6. [Logging Configuration](#logging-configuration)
7. [Security Configuration](#security-configuration)
8. [Pipeline Configuration](#pipeline-configuration)
9. [Development vs Production](#development-vs-production)

## Environment Variables

### Core Configuration

#### OPENAI_API_KEY (Required)
- **Description**: OpenAI API key with GPT-4 access
- **Required**: Yes
- **Example**: `sk-proj-...`
- **Security**: Never commit to version control

#### SECRET_KEY
- **Description**: Flask secret key for session security
- **Required**: Production only
- **Default**: `dev-key-change-in-production`
- **Example**: `your-secure-random-key-here`
- **Generation**: `python -c "import secrets; print(secrets.token_hex(32))"`

### Server Configuration

#### FLASK_HOST
- **Description**: Server bind address
- **Default**: `127.0.0.1`
- **Development**: `127.0.0.1` (localhost only)
- **Production**: `0.0.0.0` (all interfaces)
- **Example**: `0.0.0.0`

#### FLASK_PORT
- **Description**: Server port number
- **Default**: `5000`
- **Range**: `1-65535`
- **Example**: `8080`

#### FLASK_ENV
- **Description**: Flask environment mode
- **Default**: `development`
- **Options**: `development`, `production`, `testing`
- **Impact**: Affects debug mode, logging, error handling

#### FLASK_DEBUG
- **Description**: Enable Flask debug mode
- **Default**: `True`
- **Options**: `True`, `False`
- **Production**: Should be `False`

### File Upload Configuration

#### MAX_UPLOAD_SIZE_MB
- **Description**: Maximum file upload size in megabytes
- **Default**: `100`
- **Range**: `1-1000` (practical limits)
- **Example**: `200`
- **Impact**: Affects both Flask and nginx configuration

### Logging Configuration

#### LOG_LEVEL
- **Description**: Application logging level
- **Default**: `INFO`
- **Options**: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
- **Development**: `DEBUG` for verbose output
- **Production**: `INFO` or `WARNING`

#### LOG_FILE
- **Description**: Path to log file
- **Default**: None (console only)
- **Example**: `/var/log/audio-recorder/app.log`
- **Production**: Recommended to set for persistent logging

### Security Configuration

#### CORS_ORIGINS
- **Description**: Allowed CORS origins (comma-separated)
- **Default**: `*` (all origins)
- **Development**: `*` for convenience
- **Production**: Specific domains only
- **Example**: `https://yourdomain.com,https://www.yourdomain.com`

### Pipeline Configuration

#### PIPELINE_TIMEOUT_MINUTES
- **Description**: Maximum time for pipeline processing
- **Default**: `30`
- **Range**: `5-120` (practical limits)
- **Example**: `45`
- **Impact**: Prevents runaway processes

## Configuration Classes

The application uses configuration classes defined in `web/config.py`:

```python
class Config:
    """Base configuration class with common settings."""
    
    # Security
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-change-in-production'
    
    # File uploads
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_UPLOAD_SIZE_MB', 100)) * 1024 * 1024
    
    # CORS
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*').split(',')
    
    # Pipeline
    PIPELINE_TIMEOUT = int(os.environ.get('PIPELINE_TIMEOUT_MINUTES', 30)) * 60

class DevelopmentConfig(Config):
    """Development environment configuration."""
    DEBUG = True
    TESTING = False
    
    # Development-specific settings
    WTF_CSRF_ENABLED = False
    SEND_FILE_MAX_AGE_DEFAULT = 0

class ProductionConfig(Config):
    """Production environment configuration."""
    DEBUG = False
    TESTING = False
    
    # Production-specific settings
    WTF_CSRF_ENABLED = True
    SEND_FILE_MAX_AGE_DEFAULT = 31536000  # 1 year
    
    # Security headers
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

class TestingConfig(Config):
    """Testing environment configuration."""
    DEBUG = True
    TESTING = True
    WTF_CSRF_ENABLED = False
```

## Flask Configuration

### Core Flask Settings

```python
# Application configuration
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB

# Session configuration
app.config['SESSION_COOKIE_SECURE'] = True  # HTTPS only
app.config['SESSION_COOKIE_HTTPONLY'] = True  # No JavaScript access
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF protection

# File serving
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000  # 1 year cache
```

### Security Headers

```python
@app.after_request
def security_headers(response):
    """Add security headers to all responses."""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response
```

## WebSocket Configuration

### SocketIO Settings

```python
socketio_config = {
    'cors_allowed_origins': ['https://yourdomain.com'],
    'async_mode': 'threading',
    'ping_timeout': 60,
    'ping_interval': 25,
    'logger': False,  # Production
    'engineio_logger': False  # Production
}

socketio = SocketIO(app, **socketio_config)
```

### WebSocket Events Configuration

```python
# Event emission settings
PROGRESS_UPDATE_INTERVAL = 2  # seconds
MAX_RECONNECT_ATTEMPTS = 5
RECONNECT_DELAY = 1000  # milliseconds
```

## File Upload Configuration

### Upload Validation

```python
# Allowed file extensions
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'ogg', 'webm', 'm4a'}

# File size limits
MIN_FILE_SIZE = 1024  # 1KB
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

# Content type validation
ALLOWED_CONTENT_TYPES = [
    'audio/wav', 'audio/wave', 'audio/x-wav',
    'audio/mpeg', 'audio/mp3',
    'audio/ogg', 'audio/vorbis',
    'audio/webm',
    'audio/mp4', 'audio/m4a'
]
```

### Directory Configuration

```python
# Upload directories
AUDIO_UPLOAD_FOLDER = 'data/1_audio'
BRIEFS_FOLDER = 'data/outputs'
TRANSCRIPTS_FOLDER = 'data/transcripts'
PARTIALS_FOLDER = 'data/partials'

# Ensure directories exist
for folder in [AUDIO_UPLOAD_FOLDER, BRIEFS_FOLDER, TRANSCRIPTS_FOLDER, PARTIALS_FOLDER]:
    os.makedirs(folder, exist_ok=True)
```

## Logging Configuration

### Development Logging

```python
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('web/logs/debug.log')
    ]
)
```

### Production Logging

```python
from logging.handlers import RotatingFileHandler

# Configure rotating file handler
file_handler = RotatingFileHandler(
    'logs/audio-recorder.log',
    maxBytes=10 * 1024 * 1024,  # 10MB
    backupCount=10
)

file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))

file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)
```

### Log Categories

```python
# Configure specific loggers
logging.getLogger('werkzeug').setLevel(logging.WARNING)
logging.getLogger('socketio').setLevel(logging.WARNING)
logging.getLogger('engineio').setLevel(logging.WARNING)
logging.getLogger('pipeline').setLevel(logging.INFO)
```

## Security Configuration

### HTTPS Configuration

```python
# Force HTTPS in production
if not app.debug:
    @app.before_request
    def force_https():
        if not request.is_secure and request.headers.get('X-Forwarded-Proto') != 'https':
            return redirect(request.url.replace('http://', 'https://'))
```

### Content Security Policy

```python
@app.after_request
def csp_header(response):
    """Add Content Security Policy header."""
    csp = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "media-src 'self' blob:; "
        "connect-src 'self' ws: wss:; "
        "img-src 'self' data:;"
    )
    response.headers['Content-Security-Policy'] = csp
    return response
```

### Rate Limiting Configuration

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Apply to upload endpoint
@app.route('/api/upload-audio', methods=['POST'])
@limiter.limit("10 per minute")
def upload_audio():
    # Implementation
    pass
```

## Pipeline Configuration

### Pipeline Integration Settings

```python
# Pipeline execution settings
PIPELINE_CONFIG = {
    'max_workers': 4,  # Parallel processing
    'chunk_size': 1200,  # Words per chunk
    'model': 'gpt-4',  # OpenAI model
    'timeout': 30 * 60,  # 30 minutes
    'retry_attempts': 3,
    'retry_delay': 5  # seconds
}
```

### Job Management Configuration

```python
# Job lifecycle settings
JOB_CONFIG = {
    'max_concurrent_jobs': 5,
    'job_cleanup_interval': 3600,  # 1 hour
    'failed_job_retention': 24 * 3600,  # 24 hours
    'completed_job_retention': 7 * 24 * 3600,  # 7 days
    'progress_update_interval': 2  # seconds
}
```

## Development vs Production

### Development Configuration

```bash
# .env.development
FLASK_ENV=development
FLASK_DEBUG=True
FLASK_HOST=127.0.0.1
FLASK_PORT=5000
LOG_LEVEL=DEBUG
CORS_ORIGINS=*
SECRET_KEY=dev-key-change-in-production
MAX_UPLOAD_SIZE_MB=100
```

### Production Configuration

```bash
# .env.production
FLASK_ENV=production
FLASK_DEBUG=False
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
LOG_LEVEL=INFO
LOG_FILE=/var/log/audio-recorder/app.log
CORS_ORIGINS=https://yourdomain.com
SECRET_KEY=your-secure-production-key
MAX_UPLOAD_SIZE_MB=200
PIPELINE_TIMEOUT_MINUTES=45
```

### Configuration Loading

```python
def get_config(env_name):
    """Get configuration class based on environment."""
    config_map = {
        'development': DevelopmentConfig,
        'production': ProductionConfig,
        'testing': TestingConfig
    }
    return config_map.get(env_name, DevelopmentConfig)

# Load configuration
env = os.environ.get('FLASK_ENV', 'development')
config_class = get_config(env)
app.config.from_object(config_class)
```

### Environment-Specific Features

#### Development Features
- Hot reload on code changes
- Detailed error pages
- Permissive CORS settings
- Console logging
- Debug toolbar (optional)

#### Production Features
- Error logging to files
- Security headers
- HTTPS enforcement
- Rate limiting
- Performance monitoring
- Log rotation

### Configuration Validation

```python
def validate_config():
    """Validate configuration settings."""
    errors = []
    
    # Required settings
    if not app.config.get('SECRET_KEY') or app.config['SECRET_KEY'] == 'dev-key-change-in-production':
        if app.config['ENV'] == 'production':
            errors.append("SECRET_KEY must be set in production")
    
    # OpenAI API key
    if not os.environ.get('OPENAI_API_KEY'):
        errors.append("OPENAI_API_KEY is required")
    
    # File size limits
    max_size = app.config.get('MAX_CONTENT_LENGTH', 0)
    if max_size < 1024:  # Less than 1KB
        errors.append("MAX_CONTENT_LENGTH too small")
    
    return errors

# Validate on startup
config_errors = validate_config()
if config_errors:
    for error in config_errors:
        app.logger.error(f"Configuration error: {error}")
    sys.exit(1)
```

This configuration guide provides comprehensive coverage of all configuration options available in the Web Audio Recorder system.