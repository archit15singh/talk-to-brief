"""
WSGI configuration for production deployment.

This module provides a WSGI application object for use with production
WSGI servers like Gunicorn, uWSGI, or mod_wsgi.

Usage with Gunicorn:
    gunicorn --bind 0.0.0.0:5000 --workers 4 wsgi:application

Usage with uWSGI:
    uwsgi --http :5000 --wsgi-file wsgi.py --callable application
"""

import os
import sys
from pathlib import Path

# Add the parent directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set production environment
os.environ.setdefault('FLASK_ENV', 'production')

# Import the application
from app import AppConfig, create_app, setup_logging

# Create configuration
config = AppConfig()

# Set up logging for production
setup_logging(config)

# Create the WSGI application
app, socketio = create_app(config)

# WSGI application object
application = socketio

# For compatibility with some WSGI servers
if __name__ == "__main__":
    # This won't be called in production, but useful for testing
    socketio.run(app, host=config.host, port=config.port, debug=False)