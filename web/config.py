"""
Configuration management for the Web Audio Recorder application.

This module provides configuration classes for different deployment environments
including development, testing, and production settings.
"""

import os
from pathlib import Path


class BaseConfig:
    """Base configuration with common settings."""
    
    # Application settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-change-in-production')
    
    # File upload settings
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_UPLOAD_SIZE_MB', 100)) * 1024 * 1024
    UPLOAD_FOLDER = Path(__file__).parent.parent / 'data' / '1_audio'
    BRIEFS_FOLDER = Path(__file__).parent.parent / 'data' / 'outputs'
    
    # Allowed file extensions
    ALLOWED_EXTENSIONS = {'wav', 'mp3', 'ogg', 'webm', 'm4a'}
    
    # Pipeline settings
    PIPELINE_TIMEOUT_MINUTES = int(os.getenv('PIPELINE_TIMEOUT_MINUTES', 30))
    
    # Logging settings
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
    LOG_DIR = Path(__file__).parent / 'logs'
    
    # CORS settings
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')
    
    # Static file settings
    STATIC_FOLDER = 'static'
    STATIC_URL_PATH = '/static'
    
    # Session settings
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour
    
    @classmethod
    def init_app(cls, app):
        """Initialize application with this configuration."""
        # Ensure required directories exist
        cls.UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
        cls.BRIEFS_FOLDER.mkdir(parents=True, exist_ok=True)
        cls.LOG_DIR.mkdir(parents=True, exist_ok=True)


class DevelopmentConfig(BaseConfig):
    """Development configuration."""
    
    DEBUG = True
    TESTING = False
    
    # Development server settings
    HOST = os.getenv('FLASK_HOST', '127.0.0.1')
    PORT = int(os.getenv('FLASK_PORT', 5000))
    
    # More permissive CORS for development
    CORS_ORIGINS = ['*']
    
    # Development logging
    LOG_LEVEL = 'DEBUG'
    
    # Enable Flask development features
    EXPLAIN_TEMPLATE_LOADING = True
    
    @classmethod
    def init_app(cls, app):
        """Initialize development-specific settings."""
        super().init_app(app)
        
        # Development-specific initialization
        import logging
        logging.getLogger('werkzeug').setLevel(logging.INFO)


class ProductionConfig(BaseConfig):
    """Production configuration."""
    
    DEBUG = False
    TESTING = False
    
    # Production server settings
    HOST = os.getenv('FLASK_HOST', '0.0.0.0')
    PORT = int(os.getenv('FLASK_PORT', 5000))
    
    # Stricter security settings
    SECRET_KEY = os.getenv('SECRET_KEY')
    
    # Production logging
    LOG_LEVEL = 'WARNING'
    
    # More restrictive CORS
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:5000').split(',')
    
    # Security headers
    SEND_FILE_MAX_AGE_DEFAULT = 31536000  # 1 year for static files
    
    @classmethod
    def init_app(cls, app):
        """Initialize production-specific settings."""
        super().init_app(app)
        
        if not cls.SECRET_KEY:
            raise ValueError("SECRET_KEY environment variable must be set in production")
        
        # Production-specific initialization
        import logging
        
        # Set up file logging for production
        log_file = cls.LOG_DIR / 'production.log'
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.WARNING)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.WARNING)


class TestingConfig(BaseConfig):
    """Testing configuration."""
    
    DEBUG = True
    TESTING = True
    
    # Test-specific settings
    WTF_CSRF_ENABLED = False
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # Smaller limit for tests
    
    # Use temporary directories for testing
    UPLOAD_FOLDER = Path('/tmp/test_audio')
    BRIEFS_FOLDER = Path('/tmp/test_briefs')
    
    @classmethod
    def init_app(cls, app):
        """Initialize testing-specific settings."""
        super().init_app(app)
        
        # Clean up test directories
        import shutil
        for folder in [cls.UPLOAD_FOLDER, cls.BRIEFS_FOLDER]:
            if folder.exists():
                shutil.rmtree(folder)
            folder.mkdir(parents=True, exist_ok=True)


# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config(config_name=None):
    """
    Get configuration class based on environment.
    
    Args:
        config_name: Configuration name ('development', 'production', 'testing')
                    If None, uses FLASK_ENV environment variable
    
    Returns:
        Configuration class
    """
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    return config.get(config_name, config['default'])