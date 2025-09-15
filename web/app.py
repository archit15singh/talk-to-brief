#!/usr/bin/env python3
"""
Main Flask application entry point for the Web Audio Recorder.

This module serves as the entry point for the web interface that allows users
to record audio directly from their browser and automatically trigger the
existing Audio Brief Generator pipeline.

Features:
- Environment variable configuration for development/production
- Comprehensive startup validation and dependency checks
- Graceful error handling and logging setup
- Support for both development and production deployment modes
"""

import os
import sys
import logging
import signal
from pathlib import Path
from typing import Tuple, List

# Add the parent directory to the Python path to import existing pipeline modules
sys.path.append(str(Path(__file__).parent.parent))

class AppConfig:
    """Application configuration management."""
    
    def __init__(self):
        """Initialize configuration from environment variables."""
        # Server configuration
        self.host = os.getenv('FLASK_HOST', '127.0.0.1')
        self.port = int(os.getenv('FLASK_PORT', 5000))
        self.debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
        
        # Environment detection
        self.environment = os.getenv('FLASK_ENV', 'development').lower()
        self.is_production = self.environment == 'production'
        self.is_development = self.environment == 'development'
        
        # Security configuration
        self.secret_key = os.getenv('SECRET_KEY', 'dev-key-change-in-production')
        if self.is_production and self.secret_key == 'dev-key-change-in-production':
            raise ValueError("SECRET_KEY must be set in production environment")
        
        # File upload configuration
        self.max_content_length = int(os.getenv('MAX_UPLOAD_SIZE_MB', 100)) * 1024 * 1024
        
        # Logging configuration
        self.log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
        self.log_file = os.getenv('LOG_FILE', None)
        
        # CORS configuration
        self.cors_origins = os.getenv('CORS_ORIGINS', '*').split(',')
        
        # Pipeline configuration
        self.pipeline_timeout = int(os.getenv('PIPELINE_TIMEOUT_MINUTES', 30))
        
    def validate(self) -> Tuple[bool, List[str]]:
        """
        Validate configuration settings.
        
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        # Validate port range
        if not (1 <= self.port <= 65535):
            errors.append(f"Invalid port number: {self.port}")
        
        # Validate log level
        valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if self.log_level not in valid_log_levels:
            errors.append(f"Invalid log level: {self.log_level}")
        
        # Validate file size limits
        if self.max_content_length < 1024:  # Less than 1KB
            errors.append(f"Max upload size too small: {self.max_content_length} bytes")
        
        # Validate timeout
        if self.pipeline_timeout < 1:
            errors.append(f"Pipeline timeout too small: {self.pipeline_timeout} minutes")
        
        return len(errors) == 0, errors

def setup_logging(config: AppConfig) -> None:
    """
    Set up application logging based on configuration.
    
    Args:
        config: Application configuration
    """
    # Create logs directory if it doesn't exist
    log_dir = Path(__file__).parent / 'logs'
    log_dir.mkdir(exist_ok=True)
    
    # Configure logging format
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Set up handlers
    handlers = []
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(log_format))
    handlers.append(console_handler)
    
    # File handler if specified or in production
    if config.log_file or config.is_production:
        log_file = config.log_file or str(log_dir / 'app.log')
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(log_format))
        handlers.append(file_handler)
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, config.log_level),
        format=log_format,
        handlers=handlers,
        force=True  # Override any existing configuration
    )
    
    # Set specific logger levels for noisy libraries
    if not config.debug:
        logging.getLogger('werkzeug').setLevel(logging.WARNING)
        logging.getLogger('socketio').setLevel(logging.WARNING)
        logging.getLogger('engineio').setLevel(logging.WARNING)

def validate_dependencies() -> Tuple[bool, List[str], List[str]]:
    """
    Validate all required dependencies and system requirements.
    
    Returns:
        Tuple of (is_valid, error_messages, warnings)
    """
    errors = []
    warnings = []
    logger = logging.getLogger(__name__)
    
    try:
        # Check Python version
        if sys.version_info < (3, 7):
            errors.append(f"Python 3.7+ required, found {sys.version}")
        
        # Check required Python packages
        required_packages = [
            ('flask', 'Flask web framework'),
            ('flask_socketio', 'WebSocket support'),
            ('werkzeug', 'WSGI utilities'),
        ]
        
        for package, description in required_packages:
            try:
                __import__(package)
                logger.debug(f"✓ {description} available")
            except ImportError:
                errors.append(f"Required package missing: {package} ({description})")
        
        # Check pipeline dependencies
        try:
            # Try to import the pipeline module
            from pipeline import AudioBriefPipeline
            logger.info("✓ Pipeline module available")
            
            # Check if we can access the pipeline class
            if not hasattr(AudioBriefPipeline, '__init__'):
                warnings.append("Pipeline class may not be properly implemented")
                
        except ImportError as e:
            errors.append(f"Pipeline module not available: {e}")
        except Exception as e:
            warnings.append(f"Pipeline import warning: {e}")
        
        # Check system directories
        web_dir = Path(__file__).parent
        project_root = web_dir.parent
        
        required_dirs = [
            (project_root / 'data' / '1_audio', 'Audio upload directory'),
            (project_root / 'data' / 'outputs', 'Brief output directory'),
            (web_dir / 'static', 'Static files directory'),
        ]
        
        for dir_path, description in required_dirs:
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                if not os.access(dir_path, os.W_OK):
                    errors.append(f"{description} not writable: {dir_path}")
                else:
                    logger.debug(f"✓ {description} accessible")
            except Exception as e:
                errors.append(f"Cannot create/access {description}: {e}")
        
        # Check static files exist
        static_files = [
            (web_dir / 'static' / 'index.html', 'Main HTML file'),
            (web_dir / 'static' / 'app.js', 'JavaScript application'),
            (web_dir / 'static' / 'style.css', 'CSS stylesheet'),
        ]
        
        for file_path, description in static_files:
            if not file_path.exists():
                errors.append(f"{description} missing: {file_path}")
            else:
                logger.debug(f"✓ {description} found")
        
        # Check disk space
        import shutil
        try:
            disk_usage = shutil.disk_usage(project_root)
            free_gb = disk_usage.free / (1024**3)
            
            if free_gb < 0.5:  # Less than 500MB
                errors.append(f"Insufficient disk space: {free_gb:.1f}GB available")
            elif free_gb < 2.0:  # Less than 2GB
                warnings.append(f"Low disk space: {free_gb:.1f}GB available")
            else:
                logger.debug(f"✓ Sufficient disk space: {free_gb:.1f}GB available")
                
        except Exception as e:
            warnings.append(f"Could not check disk space: {e}")
        
        return len(errors) == 0, errors, warnings
        
    except Exception as e:
        logger.error(f"Dependency validation failed: {e}")
        return False, [f"Dependency validation error: {e}"], []

def setup_signal_handlers(app_instance=None):
    """
    Set up signal handlers for graceful shutdown.
    
    Args:
        app_instance: Flask app instance for cleanup
    """
    logger = logging.getLogger(__name__)
    
    def signal_handler(signum, frame):
        """Handle shutdown signals."""
        signal_name = signal.Signals(signum).name
        logger.info(f"Received {signal_name}, shutting down gracefully...")
        
        # Perform application cleanup
        try:
            from web_server import cleanup_application
            cleanup_application()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
        
        logger.info("Shutdown complete")
        sys.exit(0)
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # Termination signal
    
    # Handle SIGTERM for Docker/systemd compatibility
    if hasattr(signal, 'SIGHUP'):
        signal.signal(signal.SIGHUP, signal_handler)  # Hangup signal

def create_app(config: AppConfig):
    """
    Create and configure the Flask application.
    
    Args:
        config: Application configuration
        
    Returns:
        Configured Flask app and SocketIO instance
    """
    # Import here to avoid circular imports
    from web_server import app, socketio, configure_app_for_deployment
    from config import get_config
    
    # Get the appropriate configuration class
    config_class = get_config(config.environment)
    
    # Configure the app for the deployment environment
    configure_app_for_deployment(app, config_class)
    
    # Override with runtime configuration
    app.config['SECRET_KEY'] = config.secret_key
    app.config['MAX_CONTENT_LENGTH'] = config.max_content_length
    
    # Configure SocketIO with appropriate CORS settings
    socketio_config = {
        'cors_allowed_origins': config.cors_origins,
        'async_mode': 'threading',  # Use threading for better compatibility
        'ping_timeout': 60,
        'ping_interval': 25
    }
    
    if config.is_production:
        # Production-specific SocketIO settings
        socketio_config.update({
            'logger': False,  # Disable SocketIO logging in production
            'engineio_logger': False
        })
    
    # Reinitialize SocketIO with proper configuration
    socketio.init_app(app, **socketio_config)
    
    return app, socketio

def main():
    """Main entry point for the Flask application."""
    # Initialize configuration
    try:
        config = AppConfig()
        
        # Validate configuration
        is_valid, config_errors = config.validate()
        if not is_valid:
            print("Configuration errors:")
            for error in config_errors:
                print(f"  - {error}")
            sys.exit(1)
            
    except Exception as e:
        print(f"Configuration error: {e}")
        sys.exit(1)
    
    # Set up logging
    setup_logging(config)
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 60)
    logger.info("Starting Web Audio Recorder Application")
    logger.info("=" * 60)
    logger.info(f"Environment: {config.environment}")
    logger.info(f"Debug mode: {config.debug}")
    logger.info(f"Host: {config.host}")
    logger.info(f"Port: {config.port}")
    logger.info(f"Max upload size: {config.max_content_length / 1024 / 1024:.0f}MB")
    
    # Validate dependencies
    logger.info("Validating dependencies...")
    is_valid, errors, warnings = validate_dependencies()
    
    if errors:
        logger.error("Startup validation failed:")
        for error in errors:
            logger.error(f"  ✗ {error}")
        logger.error("Cannot start server. Please fix the above issues.")
        sys.exit(1)
    
    if warnings:
        logger.warning("Startup warnings:")
        for warning in warnings:
            logger.warning(f"  ⚠ {warning}")
    
    logger.info("✓ All dependency validations passed")
    
    # Create and configure the application
    try:
        app, socketio = create_app(config)
        logger.info("✓ Flask application created successfully")
    except Exception as e:
        logger.error(f"Failed to create Flask application: {e}")
        sys.exit(1)
    
    # Set up signal handlers for graceful shutdown
    setup_signal_handlers(app)
    
    # Start the server
    logger.info("=" * 60)
    logger.info(f"🚀 Web Audio Recorder ready at http://{config.host}:{config.port}")
    logger.info("Press Ctrl+C to stop the server")
    logger.info("=" * 60)
    
    try:
        # Use SocketIO's run method for WebSocket support
        socketio.run(
            app, 
            host=config.host, 
            port=config.port, 
            debug=config.debug,
            use_reloader=config.debug,  # Only use reloader in debug mode
            log_output=config.debug     # Control log output
        )
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()