# Web Audio Recorder Deployment Guide

This guide provides comprehensive instructions for deploying the Web Audio Recorder in various environments.

## Table of Contents

1. [Development Deployment](#development-deployment)
2. [Production Deployment](#production-deployment)
3. [Docker Deployment](#docker-deployment)
4. [Environment Configuration](#environment-configuration)
5. [Security Considerations](#security-considerations)
6. [Monitoring and Logging](#monitoring-and-logging)
7. [Troubleshooting](#troubleshooting)

## Development Deployment

### Quick Start

1. **Install Dependencies**:
```bash
# Core dependencies
pip install -r requirements.txt

# Web interface dependencies
pip install -r web/requirements_web.txt
```

2. **Set Environment Variables**:
```bash
export OPENAI_API_KEY="your-api-key-here"
export FLASK_ENV=development
export FLASK_DEBUG=True
```

3. **Start the Server**:
```bash
cd web
python app.py
```

4. **Access the Interface**:
   - Open browser to `http://127.0.0.1:5000`
   - Allow microphone permissions when prompted

### Development Configuration

Create a `.env` file in the project root:

```bash
# Required
OPENAI_API_KEY=your-api-key-here

# Development settings
FLASK_ENV=development
FLASK_DEBUG=True
FLASK_HOST=127.0.0.1
FLASK_PORT=5000

# Optional development settings
LOG_LEVEL=DEBUG
MAX_UPLOAD_SIZE_MB=100
CORS_ORIGINS=*
```

### Development Features

- **Hot Reload**: Automatic server restart on code changes
- **Debug Mode**: Detailed error messages and stack traces
- **CORS**: Permissive CORS settings for development
- **Logging**: Verbose logging to console and files

## Production Deployment

### Prerequisites

- Python 3.7+
- Virtual environment
- Reverse proxy (nginx/Apache recommended)
- SSL certificate for HTTPS
- Process manager (systemd/supervisor)

### Production Setup

1. **Create Production Environment**:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r web/requirements_web.txt
```

2. **Set Production Environment Variables**:
```bash
export FLASK_ENV=production
export FLASK_DEBUG=False
export SECRET_KEY="your-secure-secret-key"
export OPENAI_API_KEY="your-api-key"
export FLASK_HOST=0.0.0.0
export FLASK_PORT=5000
export CORS_ORIGINS="https://yourdomain.com"
export LOG_FILE="/var/log/audio-recorder/app.log"
```

3. **Create Systemd Service** (`/etc/systemd/system/audio-recorder.service`):
```ini
[Unit]
Description=Audio Brief Generator Web Interface
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/path/to/audio-brief-generator
Environment=PATH=/path/to/audio-brief-generator/.venv/bin
Environment=FLASK_ENV=production
Environment=FLASK_DEBUG=False
Environment=SECRET_KEY=your-secure-secret-key
Environment=OPENAI_API_KEY=your-api-key
Environment=FLASK_HOST=0.0.0.0
Environment=FLASK_PORT=5000
ExecStart=/path/to/audio-brief-generator/.venv/bin/python web/app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

4. **Start and Enable Service**:
```bash
sudo systemctl daemon-reload
sudo systemctl enable audio-recorder
sudo systemctl start audio-recorder
```

### Nginx Configuration

Create `/etc/nginx/sites-available/audio-recorder`:

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /path/to/ssl/cert.pem;
    ssl_certificate_key /path/to/ssl/key.pem;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";

    # File upload size limit
    client_max_body_size 100M;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Static files (optional optimization)
    location /static/ {
        alias /path/to/audio-brief-generator/web/static/;
        expires 1d;
        add_header Cache-Control "public, immutable";
    }
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/audio-recorder /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## Docker Deployment

### Dockerfile

Create `Dockerfile` in the project root:

```dockerfile
FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt web/requirements_web.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements_web.txt

# Copy application code
COPY . .

# Create data directories
RUN mkdir -p data/1_audio data/outputs data/transcripts data/partials web/logs

# Set permissions
RUN chmod -R 755 data web/logs

# Expose port
EXPOSE 5000

# Set environment variables
ENV FLASK_ENV=production
ENV FLASK_DEBUG=False
ENV FLASK_HOST=0.0.0.0
ENV FLASK_PORT=5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

# Start application
CMD ["python", "web/app.py"]
```

### Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  audio-recorder:
    build: .
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - FLASK_DEBUG=False
      - SECRET_KEY=${SECRET_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - CORS_ORIGINS=${CORS_ORIGINS:-*}
    volumes:
      - ./data:/app/data
      - ./web/logs:/app/web/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/ssl/certs:ro
    depends_on:
      - audio-recorder
    restart: unless-stopped
```

### Docker Deployment Commands

```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f audio-recorder

# Scale (if needed)
docker-compose up -d --scale audio-recorder=2

# Update
docker-compose pull
docker-compose up -d
```

## Environment Configuration

### Required Environment Variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `OPENAI_API_KEY` | Yes | OpenAI API key with GPT-4 access | `sk-...` |
| `SECRET_KEY` | Production | Flask secret key | `your-secure-key` |

### Optional Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `FLASK_HOST` | `127.0.0.1` | Server bind address |
| `FLASK_PORT` | `5000` | Server port |
| `FLASK_ENV` | `development` | Environment mode |
| `FLASK_DEBUG` | `True` | Debug mode |
| `MAX_UPLOAD_SIZE_MB` | `100` | Max file upload size |
| `LOG_LEVEL` | `INFO` | Logging level |
| `LOG_FILE` | None | Log file path |
| `CORS_ORIGINS` | `*` | Allowed CORS origins |
| `PIPELINE_TIMEOUT_MINUTES` | `30` | Processing timeout |

### Configuration Files

Create `web/config.py` for advanced configuration:

```python
import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key'
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_UPLOAD_SIZE_MB', 100)) * 1024 * 1024

class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False

class TestingConfig(Config):
    DEBUG = True
    TESTING = True

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
```

## Security Considerations

### Production Security Checklist

- [ ] Set secure `SECRET_KEY` (use `python -c "import secrets; print(secrets.token_hex(32))"`)
- [ ] Configure specific `CORS_ORIGINS` (not `*`)
- [ ] Use HTTPS with valid SSL certificates
- [ ] Set up firewall rules (only allow necessary ports)
- [ ] Configure rate limiting (nginx/reverse proxy)
- [ ] Set up log monitoring and alerting
- [ ] Regular security updates for dependencies
- [ ] File upload validation and scanning
- [ ] Secure file storage permissions

### File Security

```bash
# Set secure permissions
chmod 750 /path/to/audio-brief-generator
chmod 640 /path/to/audio-brief-generator/.env
chown -R www-data:www-data /path/to/audio-brief-generator/data
chmod 755 /path/to/audio-brief-generator/data
```

### Network Security

- Use HTTPS for all communication
- Configure CSP headers
- Implement rate limiting
- Monitor for suspicious activity
- Use fail2ban for brute force protection

## Monitoring and Logging

### Log Configuration

Production logging setup in `web/app.py`:

```python
import logging
from logging.handlers import RotatingFileHandler

if not app.debug:
    file_handler = RotatingFileHandler(
        'logs/audio-recorder.log', 
        maxBytes=10240000, 
        backupCount=10
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
```

### Health Monitoring

Set up monitoring for:

- Application health: `GET /api/health`
- System resources: `GET /api/system/status`
- Error rates and response times
- Disk space and memory usage
- Processing job success rates

### Log Analysis

Use tools like:
- **ELK Stack**: Elasticsearch, Logstash, Kibana
- **Grafana**: For metrics visualization
- **Prometheus**: For metrics collection
- **Sentry**: For error tracking

## Troubleshooting

### Common Deployment Issues

**Port Already in Use**:
```bash
# Find process using port
sudo lsof -i :5000
# Kill process
sudo kill -9 <PID>
```

**Permission Denied**:
```bash
# Fix file permissions
sudo chown -R www-data:www-data /path/to/app
sudo chmod -R 755 /path/to/app
```

**SSL Certificate Issues**:
```bash
# Test SSL configuration
openssl s_client -connect yourdomain.com:443
# Check certificate expiry
openssl x509 -in cert.pem -text -noout
```

**WebSocket Connection Fails**:
- Check firewall settings
- Verify proxy configuration
- Test WebSocket endpoint directly

### Performance Optimization

**File Upload Performance**:
- Increase nginx `client_max_body_size`
- Optimize disk I/O with SSD storage
- Monitor disk space usage

**Processing Performance**:
- Monitor CPU and memory usage
- Optimize concurrent job limits
- Use faster storage for temporary files

**Network Performance**:
- Enable gzip compression
- Use CDN for static assets
- Optimize WebSocket message frequency

### Backup and Recovery

**Data Backup**:
```bash
# Backup data directory
tar -czf backup-$(date +%Y%m%d).tar.gz data/

# Backup configuration
cp .env config-backup-$(date +%Y%m%d).env
```

**Database Backup** (if using database):
```bash
# PostgreSQL example
pg_dump audio_recorder > backup-$(date +%Y%m%d).sql
```

**Recovery Procedure**:
1. Stop the application
2. Restore data from backup
3. Verify configuration
4. Start application
5. Test functionality

### Scaling Considerations

For high-traffic deployments:

- **Load Balancing**: Use multiple application instances
- **Database**: Consider PostgreSQL for job persistence
- **Queue System**: Use Redis/Celery for job processing
- **File Storage**: Use object storage (S3/MinIO)
- **Caching**: Implement Redis caching
- **CDN**: Use CDN for static assets

This completes the comprehensive deployment guide for the Web Audio Recorder system.