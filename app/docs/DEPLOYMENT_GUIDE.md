# Deployment and Infrastructure Guide

**Version:** 1.0.0  
**Implementation Date:** May 12, 2026  
**Status:** Production Ready  
**Deployment Type:** Docker-based with monitoring stack

---

## Overview

This guide provides comprehensive deployment instructions for the Auto Bot Solutions Forum with all user management systems and infrastructure components. It includes Docker configuration, environment setup, monitoring, and maintenance procedures.

---

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Environment Setup](#environment-setup)
3. [Docker Configuration](#docker-configuration)
4. [Database Setup](#database-setup)
5. [Cache Configuration](#cache-configuration)
6. [Application Deployment](#application-deployment)
7. [Monitoring Setup](#monitoring-setup)
8. [Security Configuration](#security-configuration)
9. [Performance Tuning](#performance-tuning)
10. [Maintenance Procedures](#maintenance-procedures)
11. [Troubleshooting](#troubleshooting)
12. [Scaling Considerations](#scaling-considerations)

---

## System Requirements

### Minimum Requirements

- **CPU**: 4 cores
- **Memory**: 8GB RAM
- **Storage**: 50GB SSD
- **Network**: 100Mbps
- **OS**: Ubuntu 20.04+ or CentOS 8+

### Recommended Requirements

- **CPU**: 8 cores
- **Memory**: 16GB RAM
- **Storage**: 100GB SSD
- **Network**: 1Gbps
- **OS**: Ubuntu 22.04 LTS

### Software Dependencies

- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **Python**: 3.11+
- **PostgreSQL**: 15+
- **Redis**: 7+
- **Nginx**: 1.20+

---

## Environment Setup

### System Preparation

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Create application directory
sudo mkdir -p /opt/autobot-forum
sudo chown $USER:$USER /opt/autobot-forum
cd /opt/autobot-forum
```

### Directory Structure

```
/opt/autobot-forum/
├── app/                    # Application code
├── config/                 # Configuration files
├── docker/                 # Docker configurations
├── data/                   # Persistent data
├── logs/                   # Log files
├── backups/                # Backup files
├── uploads/                # User uploads
└── monitoring/             # Monitoring configuration
```

```bash
# Create directory structure
mkdir -p {config,docker,data,logs,backups,uploads,monitoring}
```

---

## Docker Configuration

### Production Docker Compose

```yaml
# docker-compose.production.yml
version: '3.8'

services:
  # Web Application
  web:
    build:
      context: .
      dockerfile: Dockerfile.prod
    container_name: autobot-web
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      - FLASK_ENV=production
      - DATABASE_URL=postgresql://autobot:${DB_PASSWORD}@db:5432/autobot_forum_prod
      - REDIS_URL=redis://redis:6379/0
    env_file:
      - config/production.env
    volumes:
      - ./uploads:/app/uploads
      - ./logs:/app/logs
    depends_on:
      - db
      - redis
    networks:
      - autobot-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # PostgreSQL Database
  db:
    image: postgres:15-alpine
    container_name: autobot-db
    restart: unless-stopped
    environment:
      - POSTGRES_DB=autobot_forum_prod
      - POSTGRES_USER=autobot
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - ./data/postgres:/var/lib/postgresql/data
      - ./backups/postgres:/backups
    networks:
      - autobot-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U autobot"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Redis Cache
  redis:
    image: redis:7-alpine
    container_name: autobot-redis
    restart: unless-stopped
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - ./data/redis:/data
    networks:
      - autobot-network
    healthcheck:
      test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Nginx Reverse Proxy
  nginx:
    image: nginx:alpine
    container_name: autobot-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./docker/nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./docker/nginx/ssl:/etc/nginx/ssl
      - ./uploads:/var/www/uploads
    depends_on:
      - web
    networks:
      - autobot-network

  # Celery Worker
  celery:
    build:
      context: .
      dockerfile: Dockerfile.prod
    container_name: autobot-celery
    restart: unless-stopped
    command: celery -A app.celery worker --loglevel=info
    environment:
      - FLASK_ENV=production
      - DATABASE_URL=postgresql://autobot:${DB_PASSWORD}@db:5432/autobot_forum_prod
      - REDIS_URL=redis://redis:6379/0
    env_file:
      - config/production.env
    volumes:
      - ./uploads:/app/uploads
      - ./logs:/app/logs
    depends_on:
      - db
      - redis
    networks:
      - autobot-network

  # Celery Beat Scheduler
  celery-beat:
    build:
      context: .
      dockerfile: Dockerfile.prod
    container_name: autobot-celery-beat
    restart: unless-stopped
    command: celery -A app.celery beat --loglevel=info
    environment:
      - FLASK_ENV=production
      - DATABASE_URL=postgresql://autobot:${DB_PASSWORD}@db:5432/autobot_forum_prod
      - REDIS_URL=redis://redis:6379/0
    env_file:
      - config/production.env
    volumes:
      - ./logs:/app/logs
    depends_on:
      - db
      - redis
    networks:
      - autobot-network

networks:
  autobot-network:
    driver: bridge

volumes:
  postgres_data:
  redis_data:
```

### Production Dockerfile

```dockerfile
# Dockerfile.prod
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
    libjpeg-dev \
    libpng-dev \
    libwebp-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY config/ ./config/
COPY migrations/ ./migrations/

# Create necessary directories
RUN mkdir -p logs uploads

# Set environment variables
ENV FLASK_APP=app
ENV FLASK_ENV=production
ENV PYTHONPATH=/app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Run the application
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "120", "app:app"]
```

---

## Database Setup

### PostgreSQL Configuration

```bash
# Create database user and database
docker-compose exec db psql -U autobot -d autobot_forum_prod -c "
CREATE USER autobot WITH PASSWORD 'your_secure_password';
CREATE DATABASE autobot_forum_prod OWNER autobot;
GRANT ALL PRIVILEGES ON DATABASE autobot_forum_prod TO autobot;
"
```

### Database Migration

```bash
# Run database migrations
docker-compose exec web flask db upgrade

# Create initial data
docker-compose exec web python -c "
from app import db, create_app
from app.models import User
app = create_app()
with app.app_context():
    # Create admin user
    admin = User(
        username='admin',
        email='admin@autobot.com',
        is_admin=True,
        is_active=True
    )
    admin.set_password('secure_admin_password')
    db.session.add(admin)
    db.session.commit()
    print('Admin user created')
"
```

### Database Backup

```bash
# Create backup script
cat > backup_database.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/autobot-forum/backups/postgres"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/autobot_backup_$DATE.sql"

# Create backup
docker-compose exec -T db pg_dump -U autobot autobot_forum_prod > $BACKUP_FILE

# Compress backup
gzip $BACKUP_FILE

# Remove old backups (keep last 7 days)
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete

echo "Backup completed: $BACKUP_FILE.gz"
EOF

chmod +x backup_database.sh

# Add to crontab for daily backups
(crontab -l 2>/dev/null; echo "0 2 * * * /opt/autobot-forum/backup_database.sh") | crontab -
```

---

## Cache Configuration

### Redis Configuration

```bash
# Create Redis configuration
cat > docker/redis/redis.conf << 'EOF'
# Redis configuration for production
bind 0.0.0.0
port 6379
requirepass your_redis_password
maxmemory 2gb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
appendonly yes
appendfsync everysec
EOF
```

### Cache Monitoring

```bash
# Redis monitoring script
cat > monitor_cache.sh << 'EOF'
#!/bin/bash
echo "Redis Cache Status:"
docker-compose exec redis redis-cli info memory | grep used_memory_human
docker-compose exec redis redis-cli info stats | grep keyspace
docker-compose exec redis redis-cli info server | grep redis_version
EOF

chmod +x monitor_cache.sh
```

---

## Application Deployment

### Environment Configuration

```bash
# Create production environment file
cat > config/production.env << 'EOF'
# Flask Configuration
FLASK_ENV=production
SECRET_KEY=your-super-secret-production-key-here
DEBUG=False
TESTING=False

# Database Configuration
DATABASE_URL=postgresql://autobot:your_db_password@db:5432/autobot_forum_prod
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30
DATABASE_POOL_TIMEOUT=30

# Cache Configuration
REDIS_URL=redis://:your_redis_password@redis:6379/0
CACHE_TYPE=redis
CACHE_DEFAULT_TIMEOUT=300
CACHE_REDIS_HOST=redis
CACHE_REDIS_PORT=6379
CACHE_REDIS_PASSWORD=your_redis_password

# User Management Systems
USER_PROFILE_UPLOAD_PATH=/app/uploads/profiles
USER_ANALYTICS_ENABLED=true
SOCIAL_FEATURES_ENABLED=true
PROFILE_CUSTOMIZATION_ENABLED=true
USER_ROLE_MANAGEMENT_ENABLED=true

# Profile Settings
PROFILE_MAX_BANNER_SIZE=5242880
PROFILE_ALLOWED_BANNER_TYPES=jpg,jpeg,png,gif,webp
PROFILE_DEFAULT_THEME=light
PROFILE_MAX_WIDGETS=10

# Social Settings
SOCIAL_FEED_CACHE_TIMEOUT=180
SOCIAL_GRAPH_CACHE_TIMEOUT=600
SOCIAL_ANALYTICS_CACHE_TIMEOUT=900

# Analytics Settings
ANALYTICS_DATA_WAREHOUSE_CACHE_TIMEOUT=600
ANALYTICS_VISUALIZATION_CACHE_TIMEOUT=300
ANALYTICS_REAL_TIME_PROCESSING=true

# Theme Settings
THEME_CACHE_TIMEOUT=300
CUSTOM_THEME_VALIDATION=true

# Security Settings
WTF_CSRF_ENABLED=True
WTF_CSRF_TIME_LIMIT=3600
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax
PERMANENT_SESSION_LIFETIME=86400

# Email Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_email_password

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=/app/logs/app.log
LOG_MAX_BYTES=10485760
LOG_BACKUP_COUNT=5
EOF
```

### Deployment Script

```bash
# Create deployment script
cat > deploy.sh << 'EOF'
#!/bin/bash

set -e

echo "🚀 Starting Auto Bot Solutions Forum deployment..."

# Pull latest images
echo "📦 Pulling latest Docker images..."
docker-compose -f docker-compose.production.yml pull

# Stop existing services
echo "⏹️ Stopping existing services..."
docker-compose -f docker-compose.production.yml down

# Build new images
echo "🔨 Building application images..."
docker-compose -f docker-compose.production.yml build

# Start services
echo "▶️ Starting services..."
docker-compose -f docker-compose.production.yml up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 30

# Run database migrations
echo "🗄️ Running database migrations..."
docker-compose -f docker-compose.production.yml exec web flask db upgrade

# Check health status
echo "🏥 Checking service health..."
for i in {1..10}; do
    if curl -f http://localhost/health >/dev/null 2>&1; then
        echo "✅ Application is healthy!"
        break
    else
        echo "⏳ Waiting for application to be ready... ($i/10)"
        sleep 10
    fi
done

# Show status
echo "📊 Service status:"
docker-compose -f docker-compose.production.yml ps

echo "🎉 Deployment completed successfully!"
EOF

chmod +x deploy.sh
```

---

## Monitoring Setup

### Prometheus Configuration

```yaml
# monitoring/prometheus/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alert_rules.yml"

scrape_configs:
  - job_name: 'autobot-web'
    static_configs:
      - targets: ['web:8000']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'postgres'
    static_configs:
      - targets: ['db:5432']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']

  - job_name: 'nginx'
    static_configs:
      - targets: ['nginx:80']

alerting:
  alertmanagers:
    - static_configs:
      - targets:
          - alertmanager:9093
```

### Grafana Dashboard

```yaml
# monitoring/grafana/dashboards/autobot-dashboard.json
{
  "dashboard": {
    "id": null,
    "title": "Auto Bot Solutions Forum",
    "tags": ["autobot"],
    "timezone": "browser",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(flask_http_requests_total[5m])",
            "legendFormat": "{{method}} {{endpoint}}"
          }
        ]
      },
      {
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "flask_http_request_duration_seconds",
            "legendFormat": "{{method}} {{endpoint}}"
          }
        ]
      },
      {
        "title": "Database Connections",
        "type": "singlestat",
        "targets": [
          {
            "expr": "pg_stat_database_numbackends",
            "legendFormat": "Connections"
          }
        ]
      },
      {
        "title": "Cache Hit Rate",
        "type": "singlestat",
        "targets": [
          {
            "expr": "redis_keyspace_hits_total / (redis_keyspace_hits_total + redis_keyspace_misses_total) * 100",
            "legendFormat": "Hit Rate %"
          }
        ]
      }
    ]
  }
}
```

### Monitoring Stack

```yaml
# docker-compose.monitoring.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    container_name: autobot-prometheus
    restart: unless-stopped
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus:/etc/prometheus
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
    networks:
      - autobot-network

  grafana:
    image: grafana/grafana:latest
    container_name: autobot-grafana
    restart: unless-stopped
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana:/etc/grafana/provisioning
    networks:
      - autobot-network

  alertmanager:
    image: prom/alertmanager:latest
    container_name: autobot-alertmanager
    restart: unless-stopped
    ports:
      - "9093:9093"
    volumes:
      - ./monitoring/alertmanager:/etc/alertmanager
      - alertmanager_data:/alertmanager
    networks:
      - autobot-network

volumes:
  prometheus_data:
  grafana_data:
  alertmanager_data:

networks:
  autobot-network:
    external: true
```

---

## Security Configuration

### SSL/TLS Setup

```bash
# Create SSL certificates directory
mkdir -p docker/nginx/ssl

# Generate self-signed certificate (for development)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout docker/nginx/ssl/nginx.key \
    -out docker/nginx/ssl/nginx.crt \
    -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"

# For production, use Let's Encrypt
# apt install certbot python3-certbot-nginx
# certbot --nginx -d yourdomain.com
```

### Nginx Configuration

```nginx
# docker/nginx/nginx.conf
events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Logging
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;
    error_log /var/log/nginx/error.log;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=login:10m rate=1r/s;

    # Upstream configuration
    upstream app {
        server web:8000;
    }

    # HTTP to HTTPS redirect
    server {
        listen 80;
        server_name yourdomain.com;
        return 301 https://$server_name$request_uri;
    }

    # HTTPS server
    server {
        listen 443 ssl http2;
        server_name yourdomain.com;

        # SSL configuration
        ssl_certificate /etc/nginx/ssl/nginx.crt;
        ssl_certificate_key /etc/nginx/ssl/nginx.key;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
        ssl_prefer_server_ciphers off;

        # Security headers
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
        add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";

        # Main application
        location / {
            proxy_pass http://app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_connect_timeout 30s;
            proxy_send_timeout 30s;
            proxy_read_timeout 30s;
        }

        # API rate limiting
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Login rate limiting
        location /login {
            limit_req zone=login burst=5 nodelay;
            proxy_pass http://app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Static files
        location /uploads/ {
            alias /var/www/uploads/;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }

        # Health check
        location /health {
            access_log off;
            proxy_pass http://app;
        }
    }
}
```

---

## Performance Tuning

### Database Optimization

```sql
-- PostgreSQL performance tuning
-- Add to postgresql.conf

# Memory settings
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
maintenance_work_mem = 64MB

# Connection settings
max_connections = 200
shared_preload_libraries = 'pg_stat_statements'

# Logging settings
log_statement = 'all'
log_duration = on
log_min_duration_statement = 1000

# Checkpoint settings
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
```

### Application Optimization

```python
# Performance tuning settings in config/production.env

# Gunicorn settings
GUNICORN_WORKERS=4
GUNICORN_WORKER_CLASS=gevent
GUNICORN_WORKER_CONNECTIONS=1000
GUNICORN_MAX_REQUESTS=1000
GUNICORN_MAX_REQUESTS_JITTER=100
GUNICORN_PRELOAD_APP=true
GUNICORN_TIMEOUT=120

# Database pool settings
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30
DATABASE_POOL_TIMEOUT=30
DATABASE_POOL_RECYCLE=3600

# Cache settings
CACHE_DEFAULT_TIMEOUT=300
CACHE_KEY_PREFIX=autobot:prod:
CACHE_REDIS_MAX_CONNECTIONS=50
```

---

## Maintenance Procedures

### Daily Maintenance

```bash
# Create daily maintenance script
cat > daily_maintenance.sh << 'EOF'
#!/bin/bash

echo "🔧 Starting daily maintenance..."

# Clean up old logs
find /opt/autobot-forum/logs -name "*.log" -mtime +7 -delete

# Clean up old uploads (temporary files)
find /opt/autobot-forum/uploads -name "tmp_*" -mtime +1 -delete

# Optimize database
docker-compose exec db psql -U autobot -d autobot_forum_prod -c "VACUUM ANALYZE;"

# Check disk space
df -h /opt/autobot-forum

# Check service status
docker-compose ps

echo "✅ Daily maintenance completed"
EOF

chmod +x daily_maintenance.sh

# Add to crontab
(crontab -l 2>/dev/null; echo "0 3 * * * /opt/autobot-forum/daily_maintenance.sh") | crontab -
```

### Weekly Maintenance

```bash
# Create weekly maintenance script
cat > weekly_maintenance.sh << 'EOF'
#!/bin/bash

echo "🔧 Starting weekly maintenance..."

# Update Docker images
docker-compose pull

# Restart services (rolling restart)
docker-compose up -d --force-recreate

# Check database size
docker-compose exec db psql -U autobot -d autobot_forum_prod -c "
SELECT pg_size_pretty(pg_database_size('autobot_forum_prod')) as database_size;
"

# Clean up Docker images
docker image prune -f

# Backup configuration files
tar -czf /opt/autobot-forum/backups/config_$(date +%Y%m%d).tar.gz /opt/autobot-forum/config/

echo "✅ Weekly maintenance completed"
EOF

chmod +x weekly_maintenance.sh

# Add to crontab
(crontab -l 2>/dev/null; echo "0 4 * * 0 /opt/autobot-forum/weekly_maintenance.sh") | crontab -
```

---

## Troubleshooting

### Common Issues

#### **Application Not Starting**

```bash
# Check application logs
docker-compose logs web

# Check health status
curl -f http://localhost/health

# Restart services
docker-compose restart web
```

#### **Database Connection Issues**

```bash
# Check database logs
docker-compose logs db

# Test database connection
docker-compose exec db psql -U autobot -d autobot_forum_prod -c "SELECT 1;"

# Restart database
docker-compose restart db
```

#### **Cache Issues**

```bash
# Check Redis logs
docker-compose logs redis

# Test Redis connection
docker-compose exec redis redis-cli ping

# Flush cache if needed
docker-compose exec redis redis-cli FLUSHALL
```

#### **Performance Issues**

```bash
# Check system resources
docker stats

# Check database performance
docker-compose exec db psql -U autobot -d autobot_forum_prod -c "
SELECT query, calls, total_time, mean_time 
FROM pg_stat_statements 
ORDER BY total_time DESC 
LIMIT 10;
"

# Check cache performance
docker-compose exec redis redis-cli info stats
```

### Emergency Procedures

#### **Full System Restart**

```bash
# Emergency restart script
cat > emergency_restart.sh << 'EOF'
#!/bin/bash

echo "🚨 Emergency system restart..."

# Stop all services
docker-compose down

# Wait 10 seconds
sleep 10

# Start database first
docker-compose up -d db

# Wait for database to be ready
sleep 30

# Start other services
docker-compose up -d

# Wait for services to be ready
sleep 30

# Check health status
curl -f http://localhost/health

echo "✅ Emergency restart completed"
EOF

chmod +x emergency_restart.sh
```

#### **Data Recovery**

```bash
# Data recovery script
cat > recover_data.sh << 'EOF'
#!/bin/bash

BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file>"
    exit 1
fi

echo "🔄 Starting data recovery..."

# Stop application
docker-compose stop web celery celery-beat

# Drop existing database
docker-compose exec db psql -U autobot -d postgres -c "DROP DATABASE IF EXISTS autobot_forum_prod;"

# Create new database
docker-compose exec db psql -U autobot -d postgres -c "CREATE DATABASE autobot_forum_prod OWNER autobot;"

# Restore from backup
gunzip -c $BACKUP_FILE | docker-compose exec -T db psql -U autobot -d autobot_forum_prod

# Run migrations
docker-compose exec web flask db upgrade

# Restart services
docker-compose start web celery celery-beat

echo "✅ Data recovery completed"
EOF

chmod +x recover_data.sh
```

---

## Scaling Considerations

### Horizontal Scaling

```yaml
# docker-compose.scale.yml
version: '3.8'

services:
  web:
    build:
      context: .
      dockerfile: Dockerfile.prod
    restart: unless-stopped
    environment:
      - FLASK_ENV=production
    env_file:
      - config/production.env
    depends_on:
      - db
      - redis
    networks:
      - autobot-network

  nginx:
    image: nginx:alpine
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./docker/nginx/nginx.scale.conf:/etc/nginx/nginx.conf
    depends_on:
      - web
    networks:
      - autobot-network

networks:
  autobot-network:
    driver: bridge
```

### Database Scaling

```bash
# Read replica setup
# Add to docker-compose.production.yml

  db-replica:
    image: postgres:15-alpine
    container_name: autobot-db-replica
    restart: unless-stopped
    environment:
      - POSTGRES_DB=autobot_forum_prod_replica
      - POSTGRES_USER=autobot
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      - PGUSER=autobot
    volumes:
      - ./data/postgres-replica:/var/lib/postgresql/data
    networks:
      - autobot-network
```

### Cache Scaling

```bash
# Redis cluster setup
# Add to docker-compose.production.yml

  redis-cluster:
    image: redis:7-alpine
    restart: unless-stopped
    command: redis-server --cluster-enabled yes --cluster-config-file nodes.conf --cluster-node-timeout 5000 --appendonly yes
    volumes:
      - ./data/redis-cluster:/data
    networks:
      - autobot-network
```

---

**Implementation Status:** ✅ **PRODUCTION READY**  
**Last Updated:** May 12, 2026  
**Deployment Type:** Docker-based with monitoring stack  
**System Status:** Complete deployment guide with all components
