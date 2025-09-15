"""
Flask Web Server for Audio Brief Generator Web Interface

This module implements a Flask-based web server that provides a browser-based
interface for the Audio Brief Generator system. It allows users to record audio
directly from their browser and automatically trigger the existing Python-based
transcription and analysis pipeline.

Key Features:
- Browser-based audio recording using MediaRecorder API
- Real-time WebSocket communication for progress updates
- File upload handling with comprehensive validation
- Integration with existing AudioBriefPipeline
- Job management and status tracking
- Brief download and management
- Comprehensive error handling and logging

Architecture:
- Flask web server with SocketIO for WebSocket support
- Static file serving for HTML/CSS/JS frontend
- RESTful API endpoints for file operations
- Background job processing with progress tracking
- Integration wrapper for existing pipeline components

Security Features:
- File type and size validation
- Filename sanitization
- Directory traversal protection
- CORS configuration
- Error logging and monitoring

Dependencies:
- Flask: Web framework
- Flask-SocketIO: WebSocket support
- Werkzeug: WSGI utilities and security
- Existing AudioBriefPipeline: Core processing logic

Author: Audio Brief Generator Team
Version: 1.0.0
"""

import os
import logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
from flask_socketio import SocketIO, emit
from werkzeug.utils import secure_filename
import uuid

# Import our pipeline runner
from pipeline_runner import WebPipelineRunner, JobManager

# Configure logging
import sys
from datetime import datetime

# Create logs directory if it doesn't exist
log_dir = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(log_dir, exist_ok=True)

# Configure logging with both file and console handlers
log_filename = os.path.join(log_dir, f'web_server_{datetime.now().strftime("%Y%m%d")}.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Set up error tracking
error_counts = {
    'upload_errors': 0,
    'validation_errors': 0,
    'pipeline_errors': 0,
    'system_errors': 0
}

def log_error_with_context(error_type: str, error_msg: str, context: dict = None):
    """
    Log error with additional context and increment error counter.
    
    Args:
        error_type: Type of error for categorization
        error_msg: Error message
        context: Additional context information
    """
    global error_counts
    
    if error_type in error_counts:
        error_counts[error_type] += 1
    
    context_str = ""
    if context:
        context_str = f" | Context: {context}"
    
    logger.error(f"[{error_type.upper()}] {error_msg}{context_str}")

def get_error_statistics():
    """Get current error statistics."""
    return error_counts.copy()

# Initialize Flask app with proper static file configuration
app = Flask(__name__, 
           static_folder='static',
           static_url_path='/static')

# Configuration will be applied by app.py
# Default settings for standalone usage
app.config['SECRET_KEY'] = 'dev-key-change-in-production'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size

# Initialize SocketIO (CORS will be configured by app.py)
socketio = SocketIO(app)

# Initialize pipeline runner and job manager
pipeline_runner = WebPipelineRunner(socketio)
job_manager = JobManager(pipeline_runner)

# Configuration
AUDIO_UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', '1_audio')
BRIEFS_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'outputs')
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'ogg', 'webm', 'm4a'}

# Ensure directories exist
os.makedirs(AUDIO_UPLOAD_FOLDER, exist_ok=True)
os.makedirs(BRIEFS_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Check if the uploaded file has an allowed extension."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_audio_file(file, max_size_mb=100):
    """
    Comprehensive audio file validation.
    
    Args:
        file: Werkzeug FileStorage object
        max_size_mb: Maximum file size in MB
        
    Returns:
        tuple: (is_valid, error_message)
    """
    try:
        # Check if file exists
        if not file:
            return False, "No file provided"
        
        # Check filename
        if not file.filename or file.filename == '':
            return False, "No filename provided"
        
        # Check file extension
        if not allowed_file(file.filename):
            return False, f"Invalid file type. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        
        # Check file size by seeking to end
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)  # Reset to beginning
        
        if file_size == 0:
            return False, "File is empty"
        
        max_size_bytes = max_size_mb * 1024 * 1024
        if file_size > max_size_bytes:
            return False, f"File too large ({file_size / 1024 / 1024:.1f}MB). Maximum size: {max_size_mb}MB"
        
        # Check for minimum file size (avoid tiny files that are likely corrupted)
        min_size_bytes = 1024  # 1KB minimum
        if file_size < min_size_bytes:
            return False, "File too small. Minimum size: 1KB"
        
        # Basic content type validation
        content_type = file.content_type or ''
        valid_content_types = [
            'audio/wav', 'audio/wave', 'audio/x-wav',
            'audio/mpeg', 'audio/mp3',
            'audio/ogg', 'audio/vorbis',
            'audio/webm',
            'audio/mp4', 'audio/m4a',
            'application/octet-stream'  # Some browsers send this for audio files
        ]
        
        if content_type and not any(ct in content_type.lower() for ct in valid_content_types):
            logger.warning(f"Suspicious content type: {content_type} for file {file.filename}")
            # Don't reject, just log warning as browsers can be inconsistent
        
        return True, None
        
    except Exception as e:
        logger.error(f"Error validating audio file: {e}")
        return False, f"File validation error: {str(e)}"

def validate_system_resources():
    """
    Validate system resources and dependencies.
    
    Returns:
        tuple: (is_valid, error_message, warnings)
    """
    warnings = []
    
    try:
        # Check disk space
        import shutil
        
        # Check space in audio upload directory
        audio_free_space = shutil.disk_usage(AUDIO_UPLOAD_FOLDER).free
        audio_free_gb = audio_free_space / (1024**3)
        
        if audio_free_gb < 0.5:  # Less than 500MB
            return False, f"Insufficient disk space in audio directory: {audio_free_gb:.1f}GB available", []
        elif audio_free_gb < 2.0:  # Less than 2GB
            warnings.append(f"Low disk space in audio directory: {audio_free_gb:.1f}GB available")
        
        # Check space in output directory
        output_free_space = shutil.disk_usage(BRIEFS_FOLDER).free
        output_free_gb = output_free_space / (1024**3)
        
        if output_free_gb < 0.5:  # Less than 500MB
            return False, f"Insufficient disk space in output directory: {output_free_gb:.1f}GB available", []
        elif output_free_gb < 2.0:  # Less than 2GB
            warnings.append(f"Low disk space in output directory: {output_free_gb:.1f}GB available")
        
        # Check directory permissions
        if not os.access(AUDIO_UPLOAD_FOLDER, os.W_OK):
            return False, "Audio upload directory is not writable", []
        
        if not os.access(BRIEFS_FOLDER, os.W_OK):
            return False, "Output directory is not writable", []
        
        # Check if pipeline dependencies are available
        try:
            from pipeline import AudioBriefPipeline
            # Try to create a dummy pipeline to check dependencies
            test_audio = os.path.join(AUDIO_UPLOAD_FOLDER, "test.wav")
            test_pipeline = AudioBriefPipeline(test_audio, "test")
            # Don't actually validate prerequisites as it might fail without a real file
        except ImportError as e:
            return False, f"Pipeline module not available: {e}", []
        except Exception as e:
            warnings.append(f"Pipeline dependency warning: {e}")
        
        return True, None, warnings
        
    except Exception as e:
        logger.error(f"Error validating system resources: {e}")
        return False, f"System validation error: {str(e)}", []

@app.route('/')
def index():
    """Serve the main recording interface."""
    try:
        logger.info("Serving main recording interface")
        return send_from_directory('static', 'index.html')
    except Exception as e:
        logger.error(f"Error serving main interface: {str(e)}")
        return jsonify({'error': 'Failed to load recording interface'}), 500

@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files with proper caching headers."""
    try:
        response = send_from_directory('static', filename)
        
        # Add caching headers for static assets
        if filename.endswith(('.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.ico')):
            # Cache static assets for 1 hour in development, 1 day in production
            cache_timeout = 3600 if app.debug else 86400
            response.cache_control.max_age = cache_timeout
            response.cache_control.public = True
        
        # Add security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        
        return response
    except Exception as e:
        logger.error(f"Error serving static file {filename}: {str(e)}")
        return jsonify({'error': 'File not found'}), 404

# Add CORS and security headers to all responses
@app.after_request
def after_request(response):
    """Add security and CORS headers to all responses."""
    # CORS headers (will be overridden by specific configuration in production)
    if app.debug:
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    
    # Security headers
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    # Don't cache API responses
    if request.path.startswith('/api/'):
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    
    return response

@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors."""
    logger.warning(f"404 error: {request.url}")
    return jsonify({'error': 'Page not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f"500 error: {str(error)}")
    return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/health')
def health_check():
    """Health check endpoint for client connectivity testing."""
    try:
        # Validate system resources
        is_valid, error_msg, warnings = validate_system_resources()
        
        health_status = {
            'status': 'healthy' if is_valid else 'unhealthy',
            'timestamp': datetime.now().isoformat(),
            'version': '1.0.0',
            'system': {
                'audio_upload_dir': os.path.exists(AUDIO_UPLOAD_FOLDER),
                'briefs_dir': os.path.exists(BRIEFS_FOLDER),
                'pipeline_available': True  # Will be set by validation
            },
            'statistics': {
                'active_jobs': len(pipeline_runner.get_active_jobs()),
                'total_jobs': len(pipeline_runner.jobs),
                'error_counts': get_error_statistics()
            }
        }
        
        if not is_valid:
            health_status['error'] = error_msg
            log_error_with_context('system_errors', error_msg)
            return jsonify(health_status), 503
        
        if warnings:
            health_status['warnings'] = warnings
        
        return jsonify(health_status), 200
        
    except Exception as e:
        error_msg = f"Health check failed: {e}"
        log_error_with_context('system_errors', error_msg)
        return jsonify({
            'status': 'unhealthy',
            'error': 'Health check failed',
            'timestamp': datetime.now().isoformat()
        }), 503

@app.route('/api/system/status')
def system_status():
    """Get detailed system status and statistics."""
    try:
        # Get job statistics
        job_stats = job_manager.get_job_statistics()
        
        # Get system resource info
        import shutil
        disk_usage = shutil.disk_usage('.')
        
        status = {
            'timestamp': datetime.now().isoformat(),
            'system': {
                'disk_usage': {
                    'total_gb': disk_usage.total / (1024**3),
                    'used_gb': (disk_usage.total - disk_usage.free) / (1024**3),
                    'free_gb': disk_usage.free / (1024**3),
                    'usage_percent': ((disk_usage.total - disk_usage.free) / disk_usage.total) * 100
                },
                'directories': {
                    'audio_upload': {
                        'path': AUDIO_UPLOAD_FOLDER,
                        'exists': os.path.exists(AUDIO_UPLOAD_FOLDER),
                        'writable': os.access(AUDIO_UPLOAD_FOLDER, os.W_OK) if os.path.exists(AUDIO_UPLOAD_FOLDER) else False
                    },
                    'briefs_output': {
                        'path': BRIEFS_FOLDER,
                        'exists': os.path.exists(BRIEFS_FOLDER),
                        'writable': os.access(BRIEFS_FOLDER, os.W_OK) if os.path.exists(BRIEFS_FOLDER) else False
                    }
                }
            },
            'jobs': job_stats,
            'errors': get_error_statistics(),
            'active_connections': len(pipeline_runner.get_active_jobs())
        }
        
        return jsonify(status), 200
        
    except Exception as e:
        error_msg = f"Failed to get system status: {e}"
        log_error_with_context('system_errors', error_msg)
        return jsonify({'error': error_msg}), 500

@app.route('/api/upload-audio', methods=['POST'])
def upload_audio():
    """Handle audio file uploads from the recording interface."""
    try:
        # Validate system resources first
        is_valid, error_msg, warnings = validate_system_resources()
        if not is_valid:
            logger.error(f"System validation failed: {error_msg}")
            return jsonify({'error': f'System not ready: {error_msg}'}), 503
        
        # Check if file is present in request
        if 'audio' not in request.files:
            error_msg = "No audio file in upload request"
            log_error_with_context('upload_errors', error_msg, {'client_ip': request.remote_addr})
            return jsonify({'error': 'No audio file provided'}), 400
        
        file = request.files['audio']
        
        # Comprehensive file validation
        is_valid, validation_error = validate_audio_file(file)
        if not is_valid:
            log_error_with_context('validation_errors', validation_error, {
                'filename': file.filename,
                'content_type': file.content_type,
                'client_ip': request.remote_addr
            })
            return jsonify({'error': validation_error}), 400
        
        # Generate unique filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        original_extension = file.filename.rsplit('.', 1)[1].lower()
        filename = f"recording_{timestamp}.{original_extension}"
        
        # Secure the filename
        filename = secure_filename(filename)
        filepath = os.path.join(AUDIO_UPLOAD_FOLDER, filename)
        
        # Check if file already exists (shouldn't happen with timestamp, but be safe)
        counter = 1
        base_filepath = filepath
        while os.path.exists(filepath):
            name_part = base_filepath.rsplit('.', 1)[0]
            ext_part = base_filepath.rsplit('.', 1)[1]
            filepath = f"{name_part}_{counter}.{ext_part}"
            filename = os.path.basename(filepath)
            counter += 1
        
        # Save the file with error handling
        try:
            file.save(filepath)
            file_size = os.path.getsize(filepath)
            
            # Verify file was saved correctly
            if file_size == 0:
                os.remove(filepath)  # Clean up empty file
                raise ValueError("File was saved but appears to be empty")
            
            logger.info(f"Audio file uploaded successfully: {filename} ({file_size} bytes)")
            
        except OSError as e:
            error_msg = f"Failed to save file {filename}: {e}"
            log_error_with_context('upload_errors', error_msg, {
                'filename': filename,
                'file_size': file_size if 'file_size' in locals() else 'unknown'
            })
            return jsonify({'error': f'Failed to save file: {str(e)}'}), 500
        except Exception as e:
            error_msg = f"Unexpected error saving file {filename}: {e}"
            log_error_with_context('upload_errors', error_msg, {'filename': filename})
            return jsonify({'error': f'File save error: {str(e)}'}), 500
        
        # Validate prerequisites before starting pipeline
        try:
            validation_results = job_manager.validate_job_prerequisites(filepath)
            failed_validations = [k for k, v in validation_results.items() if not v]
            
            if failed_validations:
                error_msg = f"Job prerequisites validation failed for {filename}: {failed_validations}"
                log_error_with_context('validation_errors', error_msg, {
                    'filename': filename,
                    'failed_validations': failed_validations,
                    'validation_results': validation_results
                })
                
                # Clean up uploaded file since we can't process it
                try:
                    os.remove(filepath)
                except Exception as cleanup_error:
                    log_error_with_context('system_errors', f"Failed to clean up file after validation failure: {cleanup_error}")
                
                error_details = {
                    'audio_file_exists': 'Audio file was not saved properly',
                    'audio_file_readable': 'Audio file is not readable',
                    'audio_file_valid': 'Audio file format or size is invalid',
                    'output_directories_writable': 'Output directories are not writable',
                    'pipeline_dependencies_available': 'Pipeline dependencies are not available',
                    'sufficient_disk_space': 'Insufficient disk space for processing'
                }
                
                detailed_errors = [error_details.get(k, k) for k in failed_validations]
                
                return jsonify({
                    'error': 'System prerequisites not met',
                    'details': detailed_errors,
                    'validation_results': validation_results
                }), 503
                
        except Exception as e:
            error_msg = f"Error during prerequisite validation for {filename}: {e}"
            log_error_with_context('validation_errors', error_msg, {'filename': filename})
            # Clean up uploaded file
            try:
                os.remove(filepath)
            except Exception:
                pass
            return jsonify({'error': f'Validation error: {str(e)}'}), 500
        
        # Start pipeline processing
        try:
            job_id = pipeline_runner.start_pipeline(filepath)
            logger.info(f"Started pipeline job {job_id} for file {filename}")
            
            response_data = {
                'success': True,
                'filename': filename,
                'filepath': filepath,
                'size': file_size,
                'job_id': job_id,
                'message': f'Audio file saved as {filename} and processing started'
            }
            
            # Include warnings if any
            if warnings:
                response_data['warnings'] = warnings
            
            return jsonify(response_data), 200
            
        except Exception as e:
            error_msg = f"Failed to start pipeline for {filename}: {e}"
            log_error_with_context('pipeline_errors', error_msg, {
                'filename': filename,
                'file_size': file_size
            })
            
            # Clean up uploaded file since processing failed
            try:
                os.remove(filepath)
                logger.info(f"Cleaned up file {filename} after pipeline start failure")
            except Exception as cleanup_error:
                log_error_with_context('system_errors', f"Failed to clean up file after pipeline failure: {cleanup_error}")
            
            return jsonify({
                'error': f'Failed to start processing: {str(e)}',
                'details': 'The uploaded file has been removed. Please try again.'
            }), 500
        
    except Exception as e:
        logger.error(f"Error uploading audio file: {str(e)}")
        return jsonify({'error': 'Failed to upload audio file'}), 500

@app.route('/api/status/<job_id>')
def get_job_status(job_id):
    """Get the status of a processing job."""
    try:
        job_status = pipeline_runner.get_job_status(job_id)
        if job_status:
            return jsonify(job_status), 200
        else:
            return jsonify({'error': 'Job not found'}), 404
    except Exception as e:
        logger.error(f"Error getting job status for {job_id}: {str(e)}")
        return jsonify({'error': 'Failed to get job status'}), 500

@app.route('/api/jobs')
def get_all_jobs():
    """Get status of all jobs."""
    try:
        return jsonify({
            'jobs': pipeline_runner.jobs,
            'statistics': job_manager.get_job_statistics()
        }), 200
    except Exception as e:
        logger.error(f"Error getting all jobs: {str(e)}")
        return jsonify({'error': 'Failed to get jobs'}), 500

@app.route('/api/jobs/<status>')
def get_jobs_by_status(status):
    """Get jobs filtered by status."""
    try:
        jobs = job_manager.get_jobs_by_status(status)
        return jsonify({'jobs': jobs}), 200
    except Exception as e:
        logger.error(f"Error getting jobs by status {status}: {str(e)}")
        return jsonify({'error': 'Failed to get jobs'}), 500

@app.route('/api/jobs/<job_id>/cancel', methods=['POST'])
def cancel_job(job_id):
    """Cancel a running job."""
    try:
        success = job_manager.cancel_job(job_id)
        if success:
            return jsonify({'success': True, 'message': 'Job cancelled'}), 200
        else:
            return jsonify({'error': 'Job could not be cancelled'}), 400
    except Exception as e:
        logger.error(f"Error cancelling job {job_id}: {str(e)}")
        return jsonify({'error': 'Failed to cancel job'}), 500

@app.route('/api/jobs/<job_id>/retry', methods=['POST'])
def retry_job(job_id):
    """Retry a failed job."""
    try:
        new_job_id = job_manager.retry_failed_job(job_id)
        if new_job_id:
            return jsonify({
                'success': True, 
                'new_job_id': new_job_id,
                'message': 'Job retry started'
            }), 200
        else:
            return jsonify({'error': 'Job could not be retried'}), 400
    except Exception as e:
        logger.error(f"Error retrying job {job_id}: {str(e)}")
        return jsonify({'error': 'Failed to retry job'}), 500

@app.route('/api/briefs')
def list_briefs():
    """List all available brief files with metadata."""
    try:
        briefs = []
        
        # Check if briefs directory exists
        if not os.path.exists(BRIEFS_FOLDER):
            logger.warning(f"Briefs folder does not exist: {BRIEFS_FOLDER}")
            return jsonify({'briefs': []}), 200
        
        # Scan for markdown files in the briefs directory
        for filename in os.listdir(BRIEFS_FOLDER):
            if filename.endswith('.md'):
                filepath = os.path.join(BRIEFS_FOLDER, filename)
                try:
                    # Get file stats
                    stat = os.stat(filepath)
                    file_size = stat.st_size
                    created_time = datetime.fromtimestamp(stat.st_ctime)
                    modified_time = datetime.fromtimestamp(stat.st_mtime)
                    
                    # Read first few lines for preview
                    preview = ""
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            lines = f.readlines()[:5]  # First 5 lines
                            preview = ''.join(lines).strip()
                            if len(lines) == 5 and len(f.readlines()) > 0:
                                preview += "..."
                    except Exception as e:
                        logger.warning(f"Could not read preview for {filename}: {e}")
                        preview = "Preview unavailable"
                    
                    briefs.append({
                        'name': filename,
                        'filename': filename,
                        'size': file_size,
                        'created_at': created_time.isoformat(),
                        'modified_at': modified_time.isoformat(),
                        'preview': preview[:200] + "..." if len(preview) > 200 else preview
                    })
                    
                except Exception as e:
                    logger.error(f"Error processing brief file {filename}: {e}")
                    continue
        
        # Sort by modification time (newest first)
        briefs.sort(key=lambda x: x['modified_at'], reverse=True)
        
        logger.info(f"Listed {len(briefs)} brief files")
        return jsonify({'briefs': briefs}), 200
        
    except Exception as e:
        logger.error(f"Error listing briefs: {str(e)}")
        return jsonify({'error': 'Failed to list briefs'}), 500

@app.route('/api/brief/<filename>')
def download_brief(filename):
    """Download a specific brief file."""
    try:
        # Secure the filename to prevent directory traversal
        filename = secure_filename(filename)
        
        # Ensure it's a markdown file
        if not filename.endswith('.md'):
            logger.warning(f"Invalid brief file requested: {filename}")
            return jsonify({'error': 'Invalid file type. Only .md files are allowed.'}), 400
        
        filepath = os.path.join(BRIEFS_FOLDER, filename)
        
        # Check if file exists
        if not os.path.exists(filepath):
            logger.warning(f"Brief file not found: {filename}")
            return jsonify({'error': 'Brief file not found'}), 404
        
        # Check if it's actually a file (not a directory)
        if not os.path.isfile(filepath):
            logger.warning(f"Requested path is not a file: {filename}")
            return jsonify({'error': 'Invalid file'}), 400
        
        logger.info(f"Serving brief file: {filename}")
        
        # Send file with appropriate headers
        return send_file(
            filepath,
            as_attachment=True,
            download_name=filename,
            mimetype='text/markdown'
        )
        
    except Exception as e:
        logger.error(f"Error downloading brief {filename}: {str(e)}")
        return jsonify({'error': 'Failed to download brief'}), 500

# WebSocket event handlers
@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    logger.info(f"Client connected: {request.sid}")
    emit('connected', {'message': 'Connected to server'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    logger.info(f"Client disconnected: {request.sid}")

@socketio.on('join_job')
def handle_join_job(data):
    """Handle client joining a job room for updates."""
    job_id = data.get('job_id')
    if job_id:
        logger.info(f"Client {request.sid} joined job room: {job_id}")
        # In a more complex setup, we'd use rooms here
        emit('job_joined', {'job_id': job_id})

# Job management functions are now handled by WebPipelineRunner and JobManager

@app.errorhandler(413)
def too_large(error):
    """Handle file too large errors."""
    logger.warning("File upload too large")
    return jsonify({'error': 'File too large. Maximum size is 100MB.'}), 413

def validate_startup_dependencies():
    """
    Validate all dependencies and system requirements on startup.
    
    Returns:
        tuple: (is_valid, error_messages, warnings)
    """
    errors = []
    warnings = []
    
    try:
        # Check Python version
        import sys
        if sys.version_info < (3, 7):
            errors.append(f"Python 3.7+ required, found {sys.version}")
        
        # Check required directories
        required_dirs = [AUDIO_UPLOAD_FOLDER, BRIEFS_FOLDER]
        for dir_path in required_dirs:
            try:
                os.makedirs(dir_path, exist_ok=True)
                if not os.access(dir_path, os.W_OK):
                    errors.append(f"Directory not writable: {dir_path}")
            except Exception as e:
                errors.append(f"Cannot create/access directory {dir_path}: {e}")
        
        # Check pipeline dependencies
        try:
            from pipeline import AudioBriefPipeline
            logger.info("Pipeline module imported successfully")
        except ImportError as e:
            errors.append(f"Pipeline module not available: {e}")
        except Exception as e:
            warnings.append(f"Pipeline import warning: {e}")
        
        # Check system resources
        is_valid, error_msg, resource_warnings = validate_system_resources()
        if not is_valid:
            errors.append(f"System resources: {error_msg}")
        warnings.extend(resource_warnings)
        
        # Check required Python packages
        required_packages = [
            'flask', 'flask_socketio', 'werkzeug'
        ]
        
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                errors.append(f"Required package not installed: {package}")
        
        return len(errors) == 0, errors, warnings
        
    except Exception as e:
        logger.error(f"Startup validation failed: {e}")
        return False, [f"Startup validation error: {e}"], []

# Graceful shutdown procedures
def cleanup_application():
    """
    Perform cleanup operations before application shutdown.
    This function is called by the signal handlers in app.py.
    """
    logger.info("Starting application cleanup...")
    
    try:
        # Cancel any running pipeline jobs
        if 'pipeline_runner' in globals():
            active_jobs = pipeline_runner.get_active_jobs()
            if active_jobs:
                logger.info(f"Cancelling {len(active_jobs)} active jobs...")
                for job_id in active_jobs:
                    try:
                        job_manager.cancel_job(job_id)
                    except Exception as e:
                        logger.warning(f"Failed to cancel job {job_id}: {e}")
        
        # Close any open file handles or database connections
        # (Add specific cleanup code here if needed)
        
        # Clean up temporary files if any
        # (Add temporary file cleanup here if needed)
        
        logger.info("Application cleanup completed")
        
    except Exception as e:
        logger.error(f"Error during application cleanup: {e}")

def configure_app_for_deployment(app_instance, config_class):
    """
    Configure the Flask app for specific deployment environment.
    
    Args:
        app_instance: Flask application instance
        config_class: Configuration class to apply
    """
    # Apply configuration
    app_instance.config.from_object(config_class)
    
    # Initialize configuration-specific settings
    config_class.init_app(app_instance)
    
    # Configure static file serving based on environment
    if config_class.DEBUG:
        # Development: serve static files through Flask
        logger.info("Development mode: Flask will serve static files")
    else:
        # Production: recommend using a reverse proxy
        logger.info("Production mode: Consider using nginx or Apache to serve static files")
        
        # Add production-specific static file headers
        @app_instance.after_request
        def add_production_headers(response):
            if request.path.startswith('/static/'):
                # Long cache for static assets in production
                response.cache_control.max_age = 31536000  # 1 year
                response.cache_control.public = True
                response.headers['Vary'] = 'Accept-Encoding'
            return response
    
    return app_instance

# Application startup is now handled by app.py
# This allows for better configuration management and testing