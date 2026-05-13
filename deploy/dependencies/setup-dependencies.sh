#!/bin/bash

# Additional Dependencies Setup Script
# Auto Bot Solutions Forum - Complete Dependencies Installation

set -e

echo "Setting up Additional Dependencies for Auto Bot Solutions Forum..."

# Configuration
PYTHON_VERSION="3.11"
VENV_NAME="forum_venv"
REQUIREMENTS_FILE="/home/robbie/Desktop/repo-forum/requirements.txt"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root for security reasons"
   exit 1
fi

# Check Python version
print_status "Checking Python version..."
if command -v python3 &> /dev/null; then
    PYTHON_INSTALLED=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    print_success "Python $PYTHON_INSTALLED is installed"
else
    print_error "Python 3 is not installed"
    exit 1
fi

# Check if pip is installed
print_status "Checking pip..."
if command -v pip3 &> /dev/null; then
    print_success "pip3 is installed"
else
    print_error "pip3 is not installed"
    exit 1
fi

# Create virtual environment if it doesn't exist
print_status "Creating virtual environment..."
if [ ! -d "/home/robbie/Desktop/repo-forum/$VENV_NAME" ]; then
    python3 -m venv "/home/robbie/Desktop/repo-forum/$VENV_NAME"
    print_success "Virtual environment created"
else
    print_warning "Virtual environment already exists"
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source "/home/robbie/Desktop/repo-forum/$VENV_NAME/bin/activate"

# Upgrade pip
print_status "Upgrading pip..."
pip install --upgrade pip

# Install system dependencies
print_status "Installing system dependencies..."

# Update package lists
sudo apt-get update

# Install essential system packages
print_status "Installing essential system packages..."
sudo apt-get install -y \
    build-essential \
    python3-dev \
    python3-pip \
    python3-venv \
    python3-setuptools \
    python3-wheel \
    libpq-dev \
    libffi-dev \
    libssl-dev \
    libjpeg-dev \
    libpng-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libwebp-dev \
    libharfbuzz-dev \
    libfribidi-dev \
    libxcb-xinerama0 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgsl-dev \
    libopenblas-dev \
    liblapack-dev \
    gfortran \
    git \
    curl \
    wget \
    unzip \
    htop \
    iotop \
    tree \
    vim \
    nano

# Install PostgreSQL client libraries
print_status "Installing PostgreSQL client libraries..."
sudo apt-get install -y \
    postgresql-client \
    postgresql-common

# Install Redis
print_status "Installing Redis..."
sudo apt-get install -y redis-server

# Install Java (required for Elasticsearch)
print_status "Installing Java..."
sudo apt-get install -y openjdk-11-jdk

# Install Node.js (for development tools)
print_status "Installing Node.js..."
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install Elasticsearch
print_status "Installing Elasticsearch..."
if ! command -v elasticsearch &> /dev/null; then
    # Add Elasticsearch repository
    wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | sudo apt-key add -
    echo "deb https://artifacts.elastic.co/packages/7.x/apt stable main" | sudo tee /etc/apt/sources.list.d/elastic-7.x.list
    sudo apt-get update
    sudo apt-get install -y elasticsearch
    print_success "Elasticsearch installed"
else
    print_warning "Elasticsearch is already installed"
fi

# Install Kibana
print_status "Installing Kibana..."
if ! command -v kibana &> /dev/null; then
    sudo apt-get install -y kibana
    print_success "Kibana installed"
else
    print_warning "Kibana is already installed"
fi

# Install monitoring tools
print_status "Installing monitoring tools..."
sudo apt-get install -y \
    prometheus \
    grafana \
    node-exporter

# Install Python dependencies
print_status "Installing Python dependencies..."

# Check if requirements file exists
if [ -f "$REQUIREMENTS_FILE" ]; then
    print_status "Installing dependencies from requirements.txt..."
    
    # Install dependencies in batches to avoid memory issues
    print_status "Installing core Flask dependencies..."
    pip install Flask==3.0.0 Flask-SQLAlchemy==3.1.1 Flask-Login==0.6.3 Flask-WTF==1.2.1 Flask-Migrate==4.0.5 Flask-Limiter==3.5.0
    
    print_status "Installing database dependencies..."
    pip install sqlalchemy-utils==0.37.8 alembic==1.12.1 psycopg2-binary==2.9.9
    
    print_status "Installing analytics dependencies..."
    pip install pandas==2.1.4 numpy==1.25.2 scipy==1.11.4 matplotlib==3.8.2 seaborn==0.13.0 plotly==5.17.0
    pip install statsmodels==0.14.0 scikit-learn==1.3.2 xgboost==2.0.2 lightgbm==4.1.0
    
    print_status "Installing search dependencies..."
    pip install elasticsearch==7.17.9 elasticsearch-py==7.17.9 elasticsearch-dsl==7.4.0
    
    print_status "Installing monitoring dependencies..."
    pip install prometheus-client==0.19.0 grafana-api==1.0.3 flower==2.0.1
    
    print_status "Installing background processing dependencies..."
    pip install celery==5.3.4 redis==5.0.1 kombu==5.3.4 schedule==1.2.0
    
    print_status "Installing data validation dependencies..."
    pip install great-expectations==0.18.5 pandera==0.17.2 cerberus==1.3.5
    
    print_status "Installing logging dependencies..."
    pip install structlog==23.2.0 loguru==0.7.2 sentry-sdk[flask]==1.38.0
    
    print_status "Installing API dependencies..."
    pip install fastapi==0.104.1 uvicorn==0.24.0 pydantic==2.5.0 httpx==0.25.2
    
    print_status "Installing security dependencies..."
    pip install passlib[bcrypt]==1.7.4 python-jose[cryptography]==3.3.0 blinker==1.6.3
    
    print_status "Installing development dependencies..."
    pip install pytest==7.4.3 pytest-cov==4.1.0 pytest-mock==3.12.0 black==23.11.0 flake8==6.1.0 mypy==1.7.1
    
    print_status "Installing remaining dependencies..."
    pip install -r "$REQUIREMENTS_FILE"
    
    print_success "All Python dependencies installed"
else
    print_error "Requirements file not found at $REQUIREMENTS_FILE"
    exit 1
fi

# Install NLTK data
print_status "Installing NLTK data..."
python3 -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet'); nltk.download('averaged_perceptron_tagger')"

# Install spaCy model
print_status "Installing spaCy model..."
python3 -m spacy download en_core_web_sm

# Configure services
print_status "Configuring services..."

# Enable and start Redis
sudo systemctl enable redis-server
sudo systemctl start redis-server

# Enable and start Elasticsearch
sudo systemctl enable elasticsearch
sudo systemctl start elasticsearch

# Enable and start Kibana
sudo systemctl enable kibana
sudo systemctl start kibana

# Enable and start Prometheus
sudo systemctl enable prometheus
sudo systemctl start prometheus

# Enable and start Grafana
sudo systemctl enable grafana-server
sudo systemctl start grafana-server

# Wait for services to start
print_status "Waiting for services to start..."
sleep 30

# Test services
print_status "Testing services..."

# Test Redis
if redis-cli ping | grep -q "PONG"; then
    print_success "Redis is running"
else
    print_error "Redis is not running"
fi

# Test Elasticsearch
if curl -s http://localhost:9200 > /dev/null; then
    print_success "Elasticsearch is running"
else
    print_error "Elasticsearch is not running"
fi

# Test Kibana
if curl -s http://localhost:5601/api/status > /dev/null; then
    print_success "Kibana is running"
else
    print_error "Kibana is not running"
fi

# Test Grafana
if curl -s http://localhost:3000/api/health > /dev/null; then
    print_success "Grafana is running"
else
    print_error "Grafana is not running"
fi

# Create configuration files
print_status "Creating configuration files..."

# Create environment file
if [ ! -f "/home/robbie/Desktop/repo-forum/.env" ]; then
    cat > "/home/robbie/Desktop/repo-forum/.env" << EOF
# Auto Bot Solutions Forum Environment Configuration

# Database Configuration
DATABASE_URL=postgresql://forum_user:forum_password@localhost:5432/forum_production
ANALYTICS_DATABASE_URL=postgresql://analytics_user:analytics_password@localhost:5432/forum_analytics

# Redis Configuration
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Elasticsearch Configuration
ELASTICSEARCH_URL=http://localhost:9200
ELASTICSEARCH_INDEX_PREFIX=forum

# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=your-secret-key-here

# Monitoring Configuration
PROMETHEUS_URL=http://localhost:9090
GRAFANA_URL=http://localhost:3000

# Security Configuration
JWT_SECRET_KEY=your-jwt-secret-key-here
ENCRYPTION_KEY=your-encryption-key-here

# Email Configuration
MAIL_SERVER=smtp.example.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@example.com
MAIL_PASSWORD=your-email-password

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=/var/log/forum/app.log

# Performance Configuration
CACHE_TYPE=redis
CACHE_DEFAULT_TIMEOUT=300

# Development Configuration
TESTING=False
DEBUG=True
EOF
    print_success "Environment file created"
else
    print_warning "Environment file already exists"
fi

# Create startup scripts
print_status "Creating startup scripts..."

# Create development startup script
cat > "/home/robbie/Desktop/repo-forum/start-dev.sh" << 'EOF'
#!/bin/bash

# Development Startup Script
# Auto Bot Solutions Forum

echo "Starting Auto Bot Solutions Forum in development mode..."

# Activate virtual environment
source forum_venv/bin/activate

# Set environment variables
export FLASK_ENV=development
export FLASK_DEBUG=True

# Start Redis (if not running)
if ! pgrep -x "redis-server" > /dev/null; then
    echo "Starting Redis..."
    redis-server --daemonize yes
fi

# Start Elasticsearch (if not running)
if ! pgrep -f "elasticsearch" > /dev/null; then
    echo "Starting Elasticsearch..."
    sudo systemctl start elasticsearch
fi

# Start Celery worker
echo "Starting Celery worker..."
celery -A app.celery worker --loglevel=info --detach

# Start Celery beat
echo "Starting Celery beat..."
celery -A app.celery beat --loglevel=info --detach

# Start Flask application
echo "Starting Flask application..."
python app.py

echo "Development environment started!"
echo "Flask app: http://localhost:5000"
echo "Kibana: http://localhost:5601"
echo "Grafana: http://localhost:3000"
EOF

chmod +x "/home/robbie/Desktop/repo-forum/start-dev.sh"

# Create production startup script
cat > "/home/robbie/Desktop/repo-forum/start-prod.sh" << 'EOF'
#!/bin/bash

# Production Startup Script
# Auto Bot Solutions Forum

echo "Starting Auto Bot Solutions Forum in production mode..."

# Activate virtual environment
source forum_venv/bin/activate

# Set environment variables
export FLASK_ENV=production
export FLASK_DEBUG=False

# Start Redis (if not running)
if ! pgrep -x "redis-server" > /dev/null; then
    echo "Starting Redis..."
    sudo systemctl start redis-server
fi

# Start Elasticsearch (if not running)
if ! pgrep -f "elasticsearch" > /dev/null; then
    echo "Starting Elasticsearch..."
    sudo systemctl start elasticsearch
fi

# Start Celery worker
echo "Starting Celery worker..."
celery -A app.celery worker --loglevel=info --detach

# Start Celery beat
echo "Starting Celery beat..."
celery -A app.celery beat --loglevel=info --detach

# Start Gunicorn
echo "Starting Gunicorn..."
gunicorn --workers 4 --bind 0.0.0.0:5000 app:app

echo "Production environment started!"
echo "Application: http://localhost:5000"
echo "Kibana: http://localhost:5601"
echo "Grafana: http://localhost:3000"
EOF

chmod +x "/home/robbie/Desktop/repo-forum/start-prod.sh"

# Create testing script
cat > "/home/robbie/Desktop/repo-forum/test-deps.sh" << 'EOF'
#!/bin/bash

# Dependencies Test Script
# Auto Bot Solutions Forum

echo "Testing installed dependencies..."

# Activate virtual environment
source forum_venv/bin/activate

# Test Python packages
echo "Testing Python packages..."

python3 -c "
import sys
packages = [
    'flask', 'sqlalchemy', 'pandas', 'numpy', 'scipy',
    'matplotlib', 'seaborn', 'plotly', 'scikit-learn',
    'elasticsearch', 'redis', 'celery', 'prometheus_client',
    'pytest', 'black', 'flake8', 'mypy'
]

failed = []
for package in packages:
    try:
        __import__(package)
        print(f'✓ {package}')
    except ImportError as e:
        print(f'✗ {package}: {e}')
        failed.append(package)

if failed:
    print(f'Failed packages: {failed}')
    sys.exit(1)
else:
    print('All packages imported successfully!')
"

# Test services
echo "Testing services..."

# Test Redis
if redis-cli ping | grep -q "PONG"; then
    echo "✓ Redis is running"
else
    echo "✗ Redis is not running"
fi

# Test Elasticsearch
if curl -s http://localhost:9200 > /dev/null; then
    echo "✓ Elasticsearch is running"
else
    echo "✗ Elasticsearch is not running"
fi

# Test Kibana
if curl -s http://localhost:5601/api/status > /dev/null; then
    echo "✓ Kibana is running"
else
    echo "✗ Kibana is not running"
fi

# Test Grafana
if curl -s http://localhost:3000/api/health > /dev/null; then
    echo "✓ Grafana is running"
else
    echo "✗ Grafana is not running"
fi

echo "Dependency testing completed!"
EOF

chmod +x "/home/robbie/Desktop/repo-forum/test-deps.sh"

# Create documentation
print_status "Creating documentation..."

cat > "/home/robbie/Desktop/repo-forum/DEPENDENCIES.md" << 'EOF'
# Additional Dependencies Documentation

This document outlines the additional dependencies installed for the Auto Bot Solutions Forum.

## System Dependencies

### Essential Packages
- build-essential - Build tools for compiling packages
- python3-dev - Python development headers
- libpq-dev - PostgreSQL development headers
- libffi-dev - Foreign Function Interface library
- libssl-dev - SSL development headers

### Database Dependencies
- postgresql-client - PostgreSQL client tools
- libpq-dev - PostgreSQL development library

### Search Dependencies
- openjdk-11-jdk - Java Development Kit (required for Elasticsearch)

### Monitoring Dependencies
- prometheus - Monitoring system
- grafana - Visualization platform
- node-exporter - System metrics exporter

## Python Dependencies

### Core Flask Dependencies
- Flask==3.0.0 - Web framework
- Flask-SQLAlchemy==3.1.1 - Database ORM
- Flask-Login==0.6.3 - User authentication
- Flask-WTF==1.2.1 - Form handling
- Flask-Migrate==4.0.5 - Database migrations
- Flask-Limiter==3.5.0 - Rate limiting

### Database Dependencies
- sqlalchemy-utils==0.37.8 - Database utilities
- alembic==1.12.1 - Database migration tool
- psycopg2-binary==2.9.9 - PostgreSQL adapter

### Analytics Dependencies
- pandas==2.1.4 - Data manipulation
- numpy==1.25.2 - Numerical computing
- scipy==1.11.4 - Scientific computing
- matplotlib==3.8.2 - Plotting library
- seaborn==0.13.0 - Statistical visualization
- plotly==5.17.0 - Interactive charts
- statsmodels==0.14.0 - Statistical models
- scikit-learn==1.3.2 - Machine learning
- xgboost==2.0.2 - Gradient boosting
- lightgbm==4.1.0 - Light gradient boosting

### Search Dependencies
- elasticsearch==7.17.9 - Elasticsearch Python client
- elasticsearch-py==7.17.9 - Elasticsearch client
- elasticsearch-dsl==7.4.0 - Elasticsearch DSL

### Monitoring Dependencies
- prometheus-client==0.19.0 - Prometheus client
- grafana-api==1.0.3 - Grafana API client
- flower==2.0.1 - Celery monitoring

### Background Processing
- celery==5.3.4 - Distributed task queue
- redis==5.0.1 - Redis client
- kombu==5.3.4 - Messaging library
- schedule==1.2.0 - Task scheduling

### Data Validation
- great-expectations==0.18.5 - Data validation
- pandera==0.17.2 - Data validation framework
- cerberus==1.3.5 - Data validation

### Logging
- structlog==23.2.0 - Structured logging
- loguru==0.7.2 - Logging library
- sentry-sdk[flask]==1.38.0 - Error tracking

### API Dependencies
- fastapi==0.104.1 - Modern API framework
- uvicorn==0.24.0 - ASGI server
- pydantic==2.5.0 - Data validation
- httpx==0.25.2 - HTTP client

### Security Dependencies
- passlib[bcrypt]==1.7.4 - Password hashing
- python-jose[cryptography]==3.3.0 - JWT handling
- blinker==1.6.3 - Signaling support

### Development Dependencies
- pytest==7.4.3 - Testing framework
- pytest-cov==4.1.0 - Coverage testing
- pytest-mock==3.12.0 - Mocking library
- black==23.11.0 - Code formatter
- flake8==6.1.0 - Linter
- mypy==1.7.1 - Type checker

## Services

### Redis
- Port: 6379
- Purpose: Caching and message broker
- Configuration: /etc/redis/redis.conf

### Elasticsearch
- Port: 9200
- Purpose: Search and analytics
- Configuration: /etc/elasticsearch/elasticsearch.yml

### Kibana
- Port: 5601
- Purpose: Elasticsearch visualization
- Configuration: /etc/kibana/kibana.yml

### Prometheus
- Port: 9090
- Purpose: Metrics collection
- Configuration: /etc/prometheus/prometheus.yml

### Grafana
- Port: 3000
- Purpose: Dashboard visualization
- Configuration: /etc/grafana/grafana.ini

## Usage

### Development
```bash
# Start development environment
./start-dev.sh
```

### Production
```bash
# Start production environment
./start-prod.sh
```

### Testing
```bash
# Test dependencies
./test-deps.sh
```

### Virtual Environment
```bash
# Activate virtual environment
source forum_venv/bin/activate

# Deactivate virtual environment
deactivate
```

## Configuration

### Environment Variables
See `.env` file for configuration options.

### Service Configuration
Each service has its own configuration file in `/etc/` directory.

## Troubleshooting

### Common Issues

1. **Virtual Environment Issues**
   - Ensure virtual environment is activated
   - Check Python version compatibility

2. **Service Not Starting**
   - Check service logs: `sudo journalctl -u service-name`
   - Verify configuration files

3. **Package Installation Issues**
   - Update package lists: `sudo apt-get update`
   - Clear pip cache: `pip cache purge`

4. **Memory Issues**
   - Increase swap space
   - Monitor memory usage: `htop`

### Logs
- Application logs: `/var/log/forum/`
- Service logs: `sudo journalctl -u service-name`
- System logs: `/var/log/syslog`

## Maintenance

### Updates
```bash
# Update system packages
sudo apt-get update && sudo apt-get upgrade

# Update Python packages
pip install --upgrade -r requirements.txt
```

### Cleanup
```bash
# Clean pip cache
pip cache purge

# Clean old logs
sudo find /var/log -name "*.log" -mtime +30 -delete
```

## Security

### Best Practices
- Keep packages updated
- Use virtual environments
- Limit service permissions
- Monitor security advisories

### Access Control
- Configure firewall rules
- Use strong passwords
- Enable SSL/TLS
- Regular security audits
EOF

print_success "Documentation created"

# Final verification
print_status "Performing final verification..."

# Check if all critical services are running
services_running=true

if ! redis-cli ping | grep -q "PONG"; then
    print_error "Redis is not running"
    services_running=false
fi

if ! curl -s http://localhost:9200 > /dev/null; then
    print_error "Elasticsearch is not running"
    services_running=false
fi

if ! curl -s http://localhost:5601/api/status > /dev/null; then
    print_error "Kibana is not running"
    services_running=false
fi

if ! curl -s http://localhost:3000/api/health > /dev/null; then
    print_error "Grafana is not running"
    services_running=false
fi

# Check if Python packages can be imported
source "/home/robbie/Desktop/repo-forum/$VENV_NAME/bin/activate"

critical_packages=("flask" "sqlalchemy" "pandas" "numpy" "elasticsearch" "redis" "celery")
packages_ok=true

for package in "${critical_packages[@]}"; do
    if ! python3 -c "import $package" 2>/dev/null; then
        print_error "Failed to import $package"
        packages_ok=false
    fi
done

# Final status
if [ "$services_running" = true ] && [ "$packages_ok" = true ]; then
    print_success "Additional dependencies setup completed successfully!"
    echo ""
    echo "Services running:"
    echo "  - Redis: http://localhost:6379"
    echo "  - Elasticsearch: http://localhost:9200"
    echo "  - Kibana: http://localhost:5601"
    echo "  - Grafana: http://localhost:3000"
    echo ""
    echo "Virtual environment: /home/robbie/Desktop/repo-forum/$VENV_NAME"
    echo "Requirements file: $REQUIREMENTS_FILE"
    echo ""
    echo "Next steps:"
    echo "1. Configure your environment variables in .env file"
    echo "2. Run './test-deps.sh' to verify all dependencies"
    echo "3. Use './start-dev.sh' for development or './start-prod.sh' for production"
    echo "4. Access services at their respective URLs"
    echo ""
    echo "Documentation available in DEPENDENCIES.md"
else
    print_error "Some services or packages are not working correctly"
    echo "Please check the error messages above and resolve the issues"
    exit 1
fi
