#!/bin/bash

# Production Deployment Script
# Auto Bot Solutions Forum - User Management Systems

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    print_error "This script should not be run as root"
    exit 1
fi

# Configuration
PROJECT_NAME="autobot_forum"
DEPLOYMENT_DIR="/var/www/$PROJECT_NAME"
BACKUP_DIR="/var/backups/$PROJECT_NAME"
LOG_DIR="/var/log/$PROJECT_NAME"

print_status "Starting production deployment for $PROJECT_NAME..."

# Create necessary directories
print_status "Creating directories..."
mkdir -p "$DEPLOYMENT_DIR"
mkdir -p "$BACKUP_DIR"
mkdir -p "$LOG_DIR"
mkdir -p "$DEPLOYMENT_DIR/uploads"
mkdir -p "$DEPLOYMENT_DIR/static"
mkdir -p "$DEPLOYMENT_DIR/models"

# Set permissions
print_status "Setting permissions..."
chmod 755 "$DEPLOYMENT_DIR"
chmod 755 "$BACKUP_DIR"
chmod 755 "$LOG_DIR"
chmod 755 "$DEPLOYMENT_DIR/uploads"
chmod 755 "$DEPLOYMENT_DIR/static"
chmod 755 "$DEPLOYMENT_DIR/models"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Copy environment file if it doesn't exist
if [ ! -f "$DEPLOYMENT_DIR/.env" ]; then
    print_status "Copying production environment file..."
    cp config/production.env "$DEPLOYMENT_DIR/.env"
    print_warning "Please update the environment variables in $DEPLOYMENT_DIR/.env"
fi

# Create Docker network if it doesn't exist
print_status "Setting up Docker network..."
if ! docker network inspect autobot_network &> /dev/null; then
    docker network create autobot_network
fi

# Build and start services
print_status "Building and starting services..."
cd "$DEPLOYMENT_DIR"

# Stop existing services
docker-compose -f docker-compose.production.yml down || true

# Pull latest images
print_status "Pulling latest images..."
docker-compose -f docker-compose.production.yml pull

# Build application image
print_status "Building application image..."
docker-compose -f docker-compose.production.yml build

# Start services
print_status "Starting services..."
docker-compose -f docker-compose.production.yml up -d

# Wait for services to be ready
print_status "Waiting for services to be ready..."
sleep 30

# Check service health
print_status "Checking service health..."
services=("web" "db" "redis" "celery" "nginx")

for service in "${services[@]}"; do
    if docker-compose -f docker-compose.production.yml ps "$service" | grep -q "Up"; then
        print_status "$service is running"
    else
        print_error "$service is not running"
    fi
done

# Run database migrations
print_status "Running database migrations..."
docker-compose -f docker-compose.production.yml exec web flask db upgrade

# Create initial admin user if needed
print_status "Creating initial admin user..."
docker-compose -f docker-compose.production.yml exec web python -c "
from app import create_app, db
from app.models import User
app = create_app()
with app.app_context():
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@autobotsolutions.com',
            is_admin=True,
            is_verified=True,
            is_active=True
        )
        admin.set_password('ChangeMe123!')
        db.session.add(admin)
        db.session.commit()
        print('Admin user created successfully')
    else:
        print('Admin user already exists'
"

# Set up log rotation
print_status "Setting up log rotation..."
sudo tee /etc/logrotate.d/$PROJECT_NAME > /dev/null <<EOF
$LOG_DIR/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 autobot autobot
    postrotate
        docker-compose -f $DEPLOYMENT_DIR/docker-compose.production.yml restart nginx
    endscript
}
EOF

# Set up cron jobs for maintenance
print_status "Setting up cron jobs..."
(crontab -l 2>/dev/null; echo "
# Auto Bot Solutions Forum - Maintenance Tasks
0 2 * * * cd $DEPLOYMENT_DIR && docker-compose -f docker-compose.production.yml exec web python -c 'from app.user.analytics.performance import AnalyticsPerformanceOptimizer; AnalyticsPerformanceOptimizer.cleanup_old_data()' >> $LOG_DIR/analytics_cleanup.log 2>&1
0 3 * * 0 cd $DEPLOYMENT_DIR && docker-compose -f docker-compose.production.yml exec web python -c 'from app.user.social.performance import SocialPerformanceOptimizer; SocialPerformanceOptimizer.cleanup_old_data()' >> $LOG_DIR/social_cleanup.log 2>&1
0 4 * * * cd $DEPLOYMENT_DIR && ./scripts/backup.sh >> $LOG_DIR/backup.log 2>&1
") | crontab -

# Create backup script
print_status "Creating backup script..."
cat > "$DEPLOYMENT_DIR/scripts/backup.sh" << 'EOF'
#!/bin/bash

# Backup script for Auto Bot Solutions Forum
BACKUP_DIR="/var/backups/autobot_forum"
DATE=$(date +%Y%m%d_%H%M%S)
PROJECT_NAME="autobot_forum"

# Create backup directory
mkdir -p "$BACKUP_DIR/$DATE"

# Backup database
docker-compose exec db pg_dump -U autobot_user autobot_forum > "$BACKUP_DIR/$DATE/database.sql"

# Backup uploads
tar -czf "$BACKUP_DIR/$DATE/uploads.tar.gz" uploads/

# Backup configuration
cp .env "$BACKUP_DIR/$DATE/"
cp docker-compose.production.yml "$BACKUP_DIR/$DATE/"

# Clean old backups (keep last 30 days)
find "$BACKUP_DIR" -type d -mtime +30 -exec rm -rf {} +

echo "Backup completed: $BACKUP_DIR/$DATE"
EOF

chmod +x "$DEPLOYMENT_DIR/scripts/backup.sh"

# Create health check script
print_status "Creating health check script..."
cat > "$DEPLOYMENT_DIR/scripts/health_check.sh" << 'EOF'
#!/bin/bash

# Health check script for Auto Bot Solutions Forum
PROJECT_NAME="autobot_forum"
LOG_DIR="/var/log/$PROJECT_NAME"

# Check if services are running
services=("web" "db" "redis" "celery" "nginx")
status=0

for service in "${services[@]}"; do
    if docker-compose ps "$service" | grep -q "Up"; then
        echo "[OK] $service is running"
    else
        echo "[ERROR] $service is not running"
        status=1
    fi
done

# Check disk space
disk_usage=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$disk_usage" -gt 80 ]; then
    echo "[WARNING] Disk usage is high: ${disk_usage}%"
fi

# Check memory usage
memory_usage=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
if [ "$memory_usage" -gt 80 ]; then
    echo "[WARNING] Memory usage is high: ${memory_usage}%"
fi

# Check application health
if curl -f http://localhost/health > /dev/null 2>&1; then
    echo "[OK] Application is responding"
else
    echo "[ERROR] Application is not responding"
    status=1
fi

exit $status
EOF

chmod +x "$DEPLOYMENT_DIR/scripts/health_check.sh"

# Create SSL certificate generation script
print_status "Creating SSL certificate script..."
cat > "$DEPLOYMENT_DIR/scripts/setup_ssl.sh" << 'EOF'
#!/bin/bash

# SSL certificate setup script
PROJECT_NAME="autobot_forum"
SSL_DIR="/etc/ssl/$PROJECT_NAME"

# Create SSL directory
sudo mkdir -p "$SSL_DIR"

# Generate self-signed certificate (for testing)
if [ ! -f "$SSL_DIR/autobot.crt" ]; then
    sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout "$SSL_DIR/autobot.key" \
        -out "$SSL_DIR/autobot.crt" \
        -subj "/C=US/ST=State/L=City/O=Auto Bot Solutions/CN=autobotsolutions.com"
    
    echo "Self-signed SSL certificate generated for testing"
    echo "For production, replace with proper SSL certificates"
fi

# Set permissions
sudo chmod 600 "$SSL_DIR/autobot.key"
sudo chmod 644 "$SSL_DIR/autobot.crt"

echo "SSL setup completed"
EOF

chmod +x "$DEPLOYMENT_DIR/scripts/setup_ssl.sh"

# Create deployment update script
print_status "Creating deployment update script..."
cat > "$DEPLOYMENT_DIR/scripts/update.sh" << 'EOF'
#!/bin/bash

# Deployment update script
PROJECT_NAME="autobot_forum"
DEPLOYMENT_DIR="/var/www/$PROJECT_NAME"

echo "Starting deployment update..."

# Create backup before update
$DEPLOYMENT_DIR/scripts/backup.sh

# Pull latest images
docker-compose -f docker-compose.production.yml pull

# Build new images
docker-compose -f docker-compose.production.yml build

# Update services one by one
echo "Updating web service..."
docker-compose -f docker-compose.production.yml up -d --no-deps web
sleep 10

echo "Updating celery service..."
docker-compose -f docker-compose.production.yml up -d --no-deps celery
sleep 10

echo "Updating celery-beat service..."
docker-compose -f docker-compose.production.yml up -d --no-deps celery-beat
sleep 10

echo "Updating nginx service..."
docker-compose -f docker-compose.production.yml up -d --no-deps nginx
sleep 10

# Run database migrations
docker-compose -f docker-compose.production.yml exec web flask db upgrade

# Clean up old images
docker image prune -f

echo "Deployment update completed"
EOF

chmod +x "$DEPLOYMENT_DIR/scripts/update.sh"

# Create monitoring script
print_status "Creating monitoring script..."
cat > "$DEPLOYMENT_DIR/scripts/monitor.sh" << 'EOF'
#!/bin/bash

# Monitoring script for Auto Bot Solutions Forum
PROJECT_NAME="autobot_forum"
LOG_DIR="/var/log/$PROJECT_NAME"
METRICS_FILE="$LOG_DIR/metrics.log"

# Collect system metrics
timestamp=$(date '+%Y-%m-%d %H:%M:%S')

# Docker container metrics
echo "$timestamp - Docker Metrics:" >> "$METRICS_FILE"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" >> "$METRICS_FILE"

# System metrics
echo "$timestamp - System Metrics:" >> "$METRICS_FILE"
echo "CPU: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)%" >> "$METRICS_FILE"
echo "Memory: $(free | grep Mem | awk '{printf "%.0f%%", $3/$2 * 100.0}')" >> "$METRICS_FILE"
echo "Disk: $(df / | awk 'NR==2 {print $5}')" >> "$METRICS_FILE"

# Application metrics
echo "$timestamp - Application Metrics:" >> "$METRICS_FILE"
if curl -s http://localhost/health > /dev/null; then
    response_time=$(curl -o /dev/null -s -w '%{time_total}' http://localhost/health)
    echo "Response Time: ${response_time}s" >> "$METRICS_FILE"
    echo "Status: Healthy" >> "$METRICS_FILE"
else
    echo "Status: Unhealthy" >> "$METRICS_FILE"
fi

echo "" >> "$METRICS_FILE"
EOF

chmod +x "$DEPLOYMENT_DIR/scripts/monitor.sh"

# Set up monitoring cron job
(crontab -l 2>/dev/null; echo "*/5 * * * * $DEPLOYMENT_DIR/scripts/monitor.sh") | crontab -

print_status "Deployment completed successfully!"
print_status ""
print_status "Next steps:"
print_status "1. Update environment variables in $DEPLOYMENT_DIR/.env"
print_status "2. Set up SSL certificates: $DEPLOYMENT_DIR/scripts/setup_ssl.sh"
print_status "3. Check service status: docker-compose -f $DEPLOYMENT_DIR/docker-compose.production.yml ps"
print_status "4. View logs: docker-compose -f $DEPLOYMENT_DIR/docker-compose.production.yml logs -f"
print_status "5. Run health check: $DEPLOYMENT_DIR/scripts/health_check.sh"
print_status ""
print_status "Service URLs:"
print_status "- Application: http://localhost (or your domain)"
print_status "- Grafana: http://localhost:3001 (admin/admin)"
print_status "- Prometheus: http://localhost:9090"
print_status "- Kibana: http://localhost:5601"
print_status ""
print_status "Default admin credentials:"
print_status "- Username: admin"
print_status "- Password: ChangeMe123! (change immediately)"
print_status ""
print_status "Important directories:"
print_status "- Application: $DEPLOYMENT_DIR"
print_status "- Logs: $LOG_DIR"
print_status "- Backups: $BACKUP_DIR"
print_status "- Scripts: $DEPLOYMENT_DIR/scripts/"
