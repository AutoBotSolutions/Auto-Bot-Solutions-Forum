#!/bin/bash

# Analytics Infrastructure Setup Script
# Auto Bot Solutions Forum - Analytics Database Setup

set -e

echo "Setting up Analytics Infrastructure for Auto Bot Solutions Forum..."

# Configuration
ANALYTICS_DB_NAME="forum_analytics"
ANALYTICS_DB_USER="analytics_user"
ANALYTICS_DB_PASSWORD="analytics_password"
ANALYTICS_DB_HOST="localhost"
ANALYTICS_DB_PORT="5432"

# Create directories
echo "Creating analytics directories..."
mkdir -p /var/log/analytics
mkdir -p /var/lib/analytics
mkdir -p /etc/analytics
mkdir -p /opt/analytics/pipeline
mkdir -p /opt/analytics/monitoring
mkdir -p /opt/analytics/backup

# Set permissions
echo "Setting permissions..."
chmod 755 /var/log/analytics
chmod 755 /var/lib/analytics
chmod 755 /etc/analytics
chmod 755 /opt/analytics
chown -R analytics:analytics /var/log/analytics
chown -R analytics:analytics /var/lib/analytics
chown -R analytics:analytics /etc/analytics
chown -R analytics:analytics /opt/analytics

# Create analytics user if it doesn't exist
echo "Creating analytics user..."
if ! id "analytics" &>/dev/null; then
    useradd -m -s /bin/bash analytics
    echo "Analytics user created successfully"
else
    echo "Analytics user already exists"
fi

# Install required packages
echo "Installing required packages..."
apt-get update
apt-get install -y postgresql postgresql-contrib python3-pip python3-venv
apt-get install -y redis-server
apt-get install -y python3-pandas python3-numpy python3-scipy
apt-get install -y apache2-utils
apt-get install -y htop iotop

# Install Python dependencies
echo "Installing Python dependencies..."
pip3 install --upgrade pip
pip3 install pandas==1.5.3
pip3 install numpy==1.21.0
pip3 install scipy==1.7.0
pip3 install sqlalchemy==1.4.23
pip3 install sqlalchemy-utils==0.37.8
pip3 install psycopg2-binary==2.9.1
pip3 install redis==3.5.3
pip3 install celery==5.2.3
pip3 install flower==1.0.9
pip3 install schedule==1.1.0
pip3 install prometheus-client==0.11.0
pip3 install grafana-api==1.0.3

# Setup PostgreSQL database
echo "Setting up PostgreSQL analytics database..."
sudo -u postgres psql -c "CREATE DATABASE $ANALYTICS_DB_NAME;" || echo "Database may already exist"
sudo -u postgres psql -c "CREATE USER $ANALYTICS_DB_USER WITH PASSWORD '$ANALYTICS_DB_PASSWORD';" || echo "User may already exist"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $ANALYTICS_DB_NAME TO $ANALYTICS_DB_USER;"
sudo -u postgres psql -c "ALTER USER $ANALYTICS_DB_USER CREATEDB;"

# Setup Redis for analytics caching
echo "Setting up Redis for analytics..."
systemctl enable redis-server
systemctl start redis-server

# Create analytics database schema
echo "Creating analytics database schema..."
sudo -u postgres psql -d $ANALYTICS_DB_NAME -c "
CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";
CREATE EXTENSION IF NOT EXISTS \"pg_stat_statements\";
CREATE EXTENSION IF NOT EXISTS \"pg_trgm\";

CREATE SCHEMA IF NOT EXISTS analytics;
CREATE SCHEMA IF NOT EXISTS pipeline;
CREATE SCHEMA IF NOT EXISTS monitoring;

-- Analytics tables
CREATE TABLE IF NOT EXISTS analytics.user_activity (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INTEGER NOT NULL,
    activity_type VARCHAR(50) NOT NULL,
    activity_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    session_id VARCHAR(100),
    ip_address INET,
    user_agent TEXT,
    device_type VARCHAR(50),
    location_country VARCHAR(2),
    location_city VARCHAR(100),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS analytics.content_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content_id INTEGER NOT NULL,
    content_type VARCHAR(50) NOT NULL,
    action_type VARCHAR(50) NOT NULL,
    action_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    user_id INTEGER,
    session_id VARCHAR(100),
    duration_seconds INTEGER,
    engagement_score FLOAT,
    sentiment_score FLOAT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS analytics.system_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_name VARCHAR(100) NOT NULL,
    metric_value FLOAT NOT NULL,
    metric_unit VARCHAR(20),
    metric_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    tags JSONB,
    source VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Pipeline tables
CREATE TABLE IF NOT EXISTS pipeline.data_pipeline (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pipeline_name VARCHAR(100) NOT NULL,
    pipeline_type VARCHAR(50) NOT NULL,
    source_system VARCHAR(50) NOT NULL,
    target_system VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    configuration JSONB,
    last_run TIMESTAMP WITH TIME ZONE,
    next_run TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS pipeline.pipeline_run (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pipeline_id UUID REFERENCES pipeline.data_pipeline(id),
    run_status VARCHAR(20) DEFAULT 'pending',
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    records_processed INTEGER DEFAULT 0,
    records_failed INTEGER DEFAULT 0,
    error_message TEXT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Monitoring tables
CREATE TABLE IF NOT EXISTS monitoring.anomaly_detection (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    anomaly_type VARCHAR(50) NOT NULL,
    anomaly_severity VARCHAR(20) DEFAULT 'medium',
    metric_name VARCHAR(100) NOT NULL,
    expected_value FLOAT,
    actual_value FLOAT,
    deviation_percentage FLOAT,
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resolved_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) DEFAULT 'active',
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_user_activity_user_timestamp ON analytics.user_activity(user_id, activity_timestamp);
CREATE INDEX IF NOT EXISTS idx_user_activity_type_timestamp ON analytics.user_activity(activity_type, activity_timestamp);
CREATE INDEX IF NOT EXISTS idx_content_analytics_content_timestamp ON analytics.content_analytics(content_id, action_timestamp);
CREATE INDEX IF NOT EXISTS idx_system_metrics_name_timestamp ON analytics.system_metrics(metric_name, metric_timestamp);
CREATE INDEX IF NOT EXISTS idx_pipeline_pipeline_status ON pipeline.data_pipeline(status);
CREATE INDEX IF NOT EXISTS idx_pipeline_run_pipeline_run ON pipeline.pipeline_run(pipeline_id, run_status);
CREATE INDEX IF NOT EXISTS idx_anomaly_detection_type_detected ON monitoring.anomaly_detection(anomaly_type, detected_at);
"

# Setup Celery for background processing
echo "Setting up Celery for analytics processing..."
cat > /etc/analytics/celery.conf << EOF
# Celery Configuration
broker_url = redis://localhost:6379/0
result_backend = redis://localhost:6379/0
task_serializer = json
accept_content = ['json']
result_serializer = json
timezone = UTC
enable_utc = true

# Analytics specific settings
task_routes = {
    'analytics.tasks.*': {'queue': 'analytics'},
    'pipeline.tasks.*': {'queue': 'pipeline'},
    'monitoring.tasks.*': {'queue': 'monitoring'}
}

# Worker settings
worker_prefetch_multiplier = 4
worker_max_tasks_per_child = 1000
worker_max_memory_per_child = 200000

# Task timeouts
task_soft_time_limit = 300
task_time_limit = 3600
EOF

# Create systemd service files
echo "Creating systemd service files..."
cat > /etc/systemd/system/analytics-worker.service << EOF
[Unit]
Description=Analytics Celery Worker
After=network.target redis.service postgresql.service

[Service]
Type=forking
User=analytics
Group=analytics
WorkingDirectory=/opt/analytics
Environment=PATH=/opt/analytics/venv/bin
ExecStart=/opt/analytics/venv/bin/celery -A analytics worker --loglevel=info
ExecStop=/bin/kill -s TERM \$MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

cat > /etc/systemd/system/analytics-beat.service << EOF
[Unit]
Description=Analytics Celery Beat Scheduler
After=network.target redis.service postgresql.service

[Service]
Type=simple
User=analytics
Group=analytics
WorkingDirectory=/opt/analytics
Environment=PATH=/opt/analytics/venv/bin
ExecStart=/opt/analytics/venv/bin/celery -A analytics beat --loglevel=info
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

cat > /etc/systemd/system/analytics-flower.service << EOF
[Unit]
Description=Analytics Flower Monitoring
After=network.target redis.service

[Service]
Type=simple
User=analytics
Group=analytics
WorkingDirectory=/opt/analytics
Environment=PATH=/opt/analytics/venv/bin
ExecStart=/opt/analytics/venv/bin/flower --port=5555
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start services
echo "Enabling and starting services..."
systemctl daemon-reload
systemctl enable analytics-worker
systemctl enable analytics-beat
systemctl enable analytics-flower
systemctl start analytics-worker
systemctl start analytics-beat
systemctl start analytics-flower

# Setup monitoring
echo "Setting up monitoring..."
cat > /etc/analytics/prometheus.yml << EOF
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "/etc/analytics/rules/*.yml"

scrape_configs:
  - job_name: 'celery'
    static_configs:
      - targets: ['localhost:5555']
    metrics_path: '/metrics'
    scrape_interval: 15s

  - job_name: 'analytics_db'
    static_configs:
      - targets: ['localhost:5432']
    metrics_path: '/metrics'
    scrape_interval: 15s

  - job_name: 'redis'
    static_configs:
      - targets: ['localhost:6379']
    metrics_path: '/metrics'
    scrape_interval: 15s
EOF

# Create virtual environment
echo "Creating Python virtual environment..."
cd /opt/analytics
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Create requirements file
cat > /opt/analytics/requirements.txt << EOF
# Core dependencies
pandas==1.5.3
numpy==1.21.0
scipy==1.7.0
sqlalchemy==1.4.23
sqlalchemy-utils==0.37.8
psycopg2-binary==2.9.1
redis==3.5.3

# Background processing
celery==5.2.3
flower==1.0.9
kombu==5.2.3

# Monitoring and metrics
prometheus-client==0.11.0
grafana-api==1.0.3
schedule==1.1.0

# Analytics specific
scikit-learn==0.24.2
matplotlib==3.4.2
seaborn==0.11.0
plotly==5.1.0
jupyter==1.0.0

# Utilities
python-dotenv==0.19.0
pyyaml==5.4.1
click==8.0.1
requests==2.26.0
EOF

echo "Analytics Infrastructure setup completed successfully!"
echo ""
echo "Next steps:"
echo "1. Configure your database connections in /etc/analytics/"
echo "2. Start your analytics pipelines with: celery -A analytics worker"
echo "3. Monitor with Flower: http://localhost:5555"
echo "4. Check logs: tail -f /var/log/analytics/*.log"
echo ""
echo "Analytics Infrastructure is ready for use!"
