# Deployment Guide

This guide provides detailed instructions for deploying the AutoBot Solutions Forum to a production server.

## Table of Contents

1. [Development Deployment](#development-deployment)
2. [Server Preparation](#server-preparation)
3. [Docker Deployment](#docker-deployment)
4. [Manual Deployment](#manual-deployment)
5. [SSL Configuration](#ssl-configuration)
6. [Security Hardening](#security-hardening)
7. [Monitoring and Logging](#monitoring-and-logging)
8. [Backup Strategy](#backup-strategy)
9. [Disaster Recovery](#disaster-recovery)

## Development Deployment

### Prerequisites

- Python 3.8 or higher
- Git
- At least 2GB RAM
- 1GB free disk space
- Redis server (for email queue and session storage)
- SMTP email provider (for email functionality)

### Quick Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/AutoBotSolutions/repo-forum.git
   cd repo-forum
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Redis server**
   ```bash
   # Ubuntu/Debian
   sudo apt-get update
   sudo apt-get install redis-server
   sudo systemctl start redis-server
   sudo systemctl enable redis-server
   
   # macOS
   brew install redis
   brew services start redis
   
   # Windows
   # Download Redis for Windows or use WSL
   ```

5. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

6. **Initialize database**
   ```bash
   python init_db.py
   ```

   This will:
   - Create SQLite database (forum.db)
   - Create default admin user (username: admin, password: admin123)

7. **Run the application**
   ```bash
   python run.py
   ```

   The application will be available at `http://localhost:5000`

## Environment Configuration

### Required Environment Variables

Create a `.env` file with the following configuration:

```bash
# Basic Flask Configuration
SECRET_KEY=your-super-secret-key-here
WTF_CSRF_SECRET_KEY=your-csrf-secret-key-here
FLASK_ENV=production

# Database Configuration
DATABASE_URL=sqlite:///forum.db

# Email Configuration (Required for email functionality)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USE_SSL=false
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=your-email@gmail.com
MAIL_MAX_EMAILS=10
MAIL_SUPPRESS_SEND=false

# Email Queue Configuration
MAIL_QUEUE_ENABLED=true
MAIL_QUEUE_URL=redis://localhost:6379/0
MAIL_RETRY_ATTEMPTS=3
MAIL_RETRY_DELAY=60

# Two-Factor Authentication Configuration
TWO_FA_ENABLED=true
TWO_FA_ISSUER=AutoBotSolutions Forum
TWO_FA_ENCRYPTION_KEY=your-encryption-key-here
TWO_FA_REQUIRED_FOR_ADMIN=false
TWO_FA_REMEMBER_DEVICE_DAYS=30

# Session Security
SESSION_COOKIE_SECURE=true
SESSION_COOKIE_HTTPONLY=true
SESSION_COOKIE_SAMESITE=Lax
PERMANENT_SESSION_LIFETIME=3600
```

### Generate Security Keys

```bash
# Generate SECRET_KEY
python -c "import secrets; print(f'SECRET_KEY={secrets.token_hex(32)}')"

# Generate CSRF_SECRET_KEY
python -c "import secrets; print(f'WTF_CSRF_SECRET_KEY={secrets.token_hex(32)}')"

# Generate 2FA_ENCRYPTION_KEY
python -c "from cryptography.fernet import Fernet; print(f'TWO_FA_ENCRYPTION_KEY={Fernet.generate_key().decode()}')"
```

### Email Provider Setup

#### Gmail Configuration
1. Enable 2FA on your Gmail account
2. Generate an App Password:
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Generate new app password for "AutoBot Forum"
3. Use the app password in `MAIL_PASSWORD`

#### SendGrid Configuration
```bash
MAIL_SERVER=smtp.sendgrid.net
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=apikey
MAIL_PASSWORD=your-sendgrid-api-key
```

#### Outlook Configuration
```bash
MAIL_SERVER=smtp-mail.outlook.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-outlook@outlook.com
MAIL_PASSWORD=your-password
```

## Dependencies

### Core Authentication Dependencies
```txt
Flask==3.0.0
Flask-SQLAlchemy==3.1.1
Flask-Login==0.6.3
Flask-WTF==1.2.1
Flask-Migrate==4.0.5
Flask-Limiter==3.5.0
Werkzeug==3.0.1
Jinja2==3.1.2
```

### Email Integration Dependencies
```txt
redis==5.0.1
celery==5.3.4
```

### Two-Factor Authentication Dependencies
```txt
pyotp==2.9.0
qrcode[pil]==7.4.2
cryptography==41.0.7
```

### Additional Dependencies
```txt
requests==2.31.0
gunicorn==21.2.0
PyYAML==6.0.1
psutil==5.9.6
```

### Install Dependencies
```bash
# Install all dependencies
pip install -r requirements.txt

# Or install specific authentication dependencies
pip install Flask Flask-SQLAlchemy Flask-Login Flask-WTF Flask-Migrate Flask-Limiter
pip install redis celery pyotp "qrcode[pil]" cryptography
```

## Production Deployment

### System Requirements

- **CPU**: 2+ cores recommended
- **RAM**: 4GB+ recommended
- **Storage**: 20GB+ SSD recommended
- **OS**: Ubuntu 20.04+ / CentOS 8+ / Debian 11+
- **Python**: 3.8+
- **Redis**: 6.0+
- **Database**: PostgreSQL 12+ (production) / SQLite (development)

### Production Setup Steps

1. **Server Preparation**
   ```bash
   # Update system
   sudo apt update && sudo apt upgrade -y
   
   # Install Python and dependencies
   sudo apt install python3 python3-pip python3-venv nginx redis-server postgresql
   
   # Create application user
   sudo adduser --system --group appuser
   ```

2. **Application Setup**
   ```bash
   # Clone repository
   cd /var/www
   sudo git clone https://github.com/AutoBotSolutions/repo-forum.git
   sudo chown -R appuser:appuser repo-forum
   cd repo-forum
   
   # Create virtual environment
   sudo -u appuser python3 -m venv venv
   sudo -u appuser venv/bin/pip install -r requirements.txt
   ```

3. **Database Setup**
   ```bash
   # PostgreSQL setup
   sudo -u postgres createuser appuser
   sudo -u postgres createdb -O appuser forum_db
   
   # Configure database URL in .env
   DATABASE_URL=postgresql://appuser:password@localhost/forum_db
   ```

4. **Redis Setup**
   ```bash
   # Configure Redis
   sudo nano /etc/redis/redis.conf
   
   # Update configuration
   bind 127.0.0.1
   port 6379
   requirepass your-redis-password
   
   # Restart Redis
   sudo systemctl restart redis-server
   sudo systemctl enable redis-server
   ```

5. **Environment Configuration**
   ```bash
   # Create production .env file
   sudo -u appuser cp .env.example .env
   sudo -u appuser nano .env
   
   # Set production values
   FLASK_ENV=production
   SECRET_KEY=your-production-secret-key
   MAIL_SERVER=your-smtp-server
   TWO_FA_ENCRYPTION_KEY=your-production-encryption-key
   ```

6. **Application Services**
   ```bash
   # Create systemd service file
   sudo nano /etc/systemd/system/forum.service
   ```

   ```ini
   [Unit]
   Description=AutoBot Solutions Forum
   After=network.target

   [Service]
   User=appuser
   Group=appuser
   WorkingDirectory=/var/www/repo-forum
   Environment=PATH=/var/www/repo-forum/venv/bin
   ExecStart=/var/www/repo-forum/venv/bin/gunicorn --workers 3 --bind unix:forum.sock -m 007 run:app
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

   ```bash
   # Enable and start service
   sudo systemctl daemon-reload
   sudo systemctl enable forum
   sudo systemctl start forum
   ```

7. **Nginx Configuration**
   ```bash
   sudo nano /etc/nginx/sites-available/forum
   ```

   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       return 301 https://$server_name$request_uri;
   }

   server {
       listen 443 ssl http2;
       server_name your-domain.com;

       ssl_certificate /path/to/ssl/cert.pem;
       ssl_certificate_key /path/to/ssl/key.pem;

       location / {
           include proxy_params;
           proxy_pass http://unix:/var/www/repo-forum/forum.sock;
       }

       location /static {
           alias /var/www/repo-forum/app/static;
       }
   }
   ```

   ```bash
   # Enable site
   sudo ln -s /etc/nginx/sites-available/forum /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```

## SSL Configuration

### Let's Encrypt Setup
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Generate SSL certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

## Security Hardening

### Firewall Configuration
```bash
# Configure UFW
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw deny 6379  # Redis (internal only)
```

### Security Headers
```bash
# Add security headers to Nginx
sudo nano /etc/nginx/snippets/security-headers.conf
```

```nginx
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header X-Content-Type-Options "nosniff" always;
add_header Referrer-Policy "no-referrer-when-downgrade" always;
add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
```

## Monitoring and Logging

### Application Logging
```bash
# Configure logging
sudo nano /var/www/repo-forum/logging.conf
```

```ini
[loggers]
keys=root,forum

[handlers]
keys=consoleHandler,fileHandler

[formatters]
keys=simpleFormatter

[logger_root]
level=INFO
handlers=consoleHandler,fileHandler

[logger_forum]
level=INFO
handlers=consoleHandler,fileHandler
qualname=forum
propagate=0

[handler_consoleHandler]
class=StreamHandler
level=INFO
formatter=simpleFormatter
args=(sys.stdout,)

[handler_fileHandler]
class=FileHandler
level=INFO
formatter=simpleFormatter
args=('/var/log/forum/app.log',)

[formatter_simpleFormatter]
format=%(asctime)s - %(name)s - %(levelname)s - %(message)s
```

### Log Rotation
```bash
sudo nano /etc/logrotate.d/forum
```

```
/var/log/forum/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 appuser appuser
    postrotate
        systemctl reload forum
    endscript
}
```

## Backup Strategy

### Database Backup
```bash
# Create backup script
sudo nano /usr/local/bin/backup-forum.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/var/backups/forum"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="forum_db"

# Create backup directory
mkdir -p $BACKUP_DIR

# Database backup
pg_dump $DB_NAME > $BACKUP_DIR/db_backup_$DATE.sql

# Application files backup
tar -czf $BACKUP_DIR/app_backup_$DATE.tar.gz /var/www/repo-forum

# Clean old backups (keep 30 days)
find $BACKUP_DIR -name "*.sql" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
```

```bash
# Make executable and schedule
sudo chmod +x /usr/local/bin/backup-forum.sh
sudo crontab -e
# Add: 0 2 * * * /usr/local/bin/backup-forum.sh
```

## Testing Deployment

### Pre-deployment Checklist
- [ ] All environment variables configured
- [ ] Database connection working
- [ ] Redis connection working
- [ ] Email sending tested
- [ ] 2FA functionality tested
- [ ] SSL certificate installed
- [ ] Security headers configured
- [ ] Logging configured
- [ ] Backup script tested

### Post-deployment Verification
```bash
# Test application
curl -I https://your-domain.com

# Test database connection
python -c "
from app import create_app
app = create_app()
with app.app_context():
    from app.models import User
    print(f'Database connected: {User.query.count()} users')
"

# Test Redis connection
redis-cli ping

# Test email sending
python -c "
from app import create_app
from app.email.queue import EmailQueueManager
app = create_app()
with app.app_context():
    stats = EmailQueueManager.get_queue_statistics()
    print(f'Email queue status: {stats}')
"

# Test 2FA functionality
python -c "
from app import create_app
from app.auth.two_factor import two_fa_service
app = create_app()
with app.app_context():
    secret = two_fa_service.generate_totp_secret()
    print(f'2FA working: secret generated')
"
```

## Troubleshooting

### Common Issues

#### Application Won't Start
```bash
# Check logs
sudo journalctl -u forum -f

# Check permissions
sudo -u appuser ls -la /var/www/repo-forum

# Check environment
sudo -u appuser cat .env
```

#### Email Not Working
```bash
# Test SMTP connection
python -c "
import smtplib
server = smtplib.SMTP('smtp.gmail.com', 587)
server.starttls()
server.login('your-email@gmail.com', 'your-password')
print('SMTP connection successful')
"

# Check Redis
redis-cli ping
```

#### 2FA Not Working
```bash
# Check 2FA configuration
python -c "
from app import create_app
app = create_app()
with app.app_context():
    print(f'2FA enabled: {app.config.get(\"TWO_FA_ENABLED\")}')
    print(f'Encryption key configured: {bool(app.config.get(\"TWO_FA_ENCRYPTION_KEY\"))}')
"
```

### Performance Monitoring
```bash
# Monitor system resources
htop
iotop
df -h

# Monitor application
sudo journalctl -u forum -f
tail -f /var/log/forum/app.log

# Monitor Redis
redis-cli info stats
```
   - Add 5 initial categories
   - Add 5 initial badges

6. **Start the forum**
   ```bash
   python run.py
   ```

7. **Access the forum**
   - Open http://localhost:5000
   - Login with admin/admin123
   - **IMPORTANT:** Change the admin password after first login

### Development Notes

- **Database**: Uses SQLite by default for development
- **Email**: Tokens are displayed in flash messages (no SMTP required)
- **Rate Limiting**: Uses in-memory storage (not Redis)
- **Debug Mode**: Enabled by default
- **Static Files**: Served by Flask development server

### Adding Initial Data

If you need to re-add categories and badges:
```bash
python add_initial_data.py
```

## Server Preparation

### Minimum Requirements

- **CPU**: 2 cores
- **RAM**: 4GB
- **Storage**: 20GB SSD
- **OS**: Ubuntu 20.04 LTS or later
- **Network**: Stable internet connection

### Initial Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install essential packages
sudo apt install -y curl git wget vim ufw fail2ban

# Create dedicated user for the forum
sudo adduser forum
sudo usermod -aG sudo forum

# Switch to forum user
su - forum
```

### Configure Firewall

```bash
# Allow SSH
sudo ufw allow ssh

# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

## Docker Deployment (Recommended)

### Install Docker and Docker Compose

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh

```bash
# Build and start containers
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

### Initialize Database

```bash
# Run initialization script
docker-compose exec app python init_db.py

# Follow prompts to create admin user and sync repos
```

### Verify Deployment

```bash
# Check if app is responding
curl http://localhost:5000

# Check database connection
docker-compose exec db psql -U forum_user -d forum_db -c "SELECT version();"
```

## Manual Deployment

### Install Dependencies

```bash
# Install Python and PostgreSQL
sudo apt install -y python3 python3-pip python3-venv postgresql postgresql-contrib nginx

# Install Python dependencies
cd /path/to/repo-forum
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Configure PostgreSQL

```bash
# Switch to postgres user
sudo -u postgres psql

# Create database and user
CREATE USER forum_user WITH PASSWORD 'secure_password';
CREATE DATABASE forum_db OWNER forum_user;
GRANT ALL PRIVILEGES ON DATABASE forum_db TO forum_user;
\q
```

### Configure Application

```bash
# Set environment variables
export SECRET_KEY='your-secret-key'
export DATABASE_URL='postgresql://forum_user:secure_password@localhost:5432/forum_db'
export FLASK_ENV=production

# Initialize database
python init_db.py
```

### Configure Gunicorn

```bash
# Install gunicorn
pip install gunicorn

# Test gunicorn
gunicorn --workers 4 --bind 0.0.0.0:5000 run:app
```

### Configure Systemd Service

```bash
sudo nano /etc/systemd/system/forum.service
```

**Service file content:**
```ini
[Unit]
Description=AutoBot Forum Application
After=network.target postgresql.service

[Service]
User=forum
Group=forum
WorkingDirectory=/home/forum/repo-forum
Environment="PATH=/home/forum/repo-forum/venv/bin"
EnvironmentFile=/home/forum/repo-forum/.env
ExecStart=/home/forum/repo-forum/venv/bin/gunicorn \
    --workers 4 \
    --threads 2 \
    --worker-class sync \
    --bind unix:/home/forum/repo-forum/forum.sock \
    --timeout 120 \
    --access-logfile /var/log/forum/access.log \
    --error-logfile /var/log/forum/error.log \
    run:app

[Install]
WantedBy=multi-user.target
```

```bash
# Create log directory
sudo mkdir -p /var/log/forum
sudo chown forum:forum /var/log/forum

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable forum
sudo systemctl start forum
sudo systemctl status forum
```

## SSL Configuration

### Using Let's Encrypt (Certbot)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d your-domain.com

# Test auto-renewal
sudo certbot renew --dry-run
```

### Manual SSL Configuration

```bash
# Create SSL directory
sudo mkdir -p /etc/nginx/ssl

# Generate self-signed certificate (for testing)
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/nginx/ssl/key.pem \
    -out /etc/nginx/ssl/cert.pem

# For production, use CA-signed certificates
```

### Update Nginx Configuration

```bash
sudo nano /etc/nginx/sites-available/forum
```

**Enable HTTPS in nginx.conf** by uncommenting the HTTPS server block and configuring your certificates.

## Security Hardening

### 1. Application Security

```bash
# Generate strong secrets
python3 -c "import secrets; print(secrets.token_hex(32))"

# Update .env with strong values
nano .env
```

### 2. Database Security

```bash
# Configure PostgreSQL for SSL
sudo nano /etc/postgresql/15/main/postgresql.conf
```

Add to postgresql.conf:
```
ssl = on
ssl_cert_file = '/etc/ssl/certs/ssl-cert-snakeoil.pem'
ssl_key_file = '/etc/ssl/private/ssl-cert-snakeoil.key'
```

### 3. System Security

```bash
# Install fail2ban
sudo apt install fail2ban

# Configure fail2ban
sudo cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local
sudo nano /etc/fail2ban/jail.local

# Enable service
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### 4. Network Security

```bash
# Configure UFW
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow http
sudo ufw allow https
sudo ufw enable
```

### 5. Regular Updates

```bash
# Enable unattended upgrades
sudo apt install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

## Monitoring and Logging

### Application Logs

```bash
# Docker logs
docker-compose logs -f app
docker-compose logs -f db

# Systemd logs
sudo journalctl -u forum -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Database Monitoring

```bash
# Connect to database
docker-compose exec db psql -U forum_user -d forum_db

# Check connections
SELECT count(*) FROM pg_stat_activity;

# Check table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### System Monitoring

```bash
# Install monitoring tools
sudo apt install htop iotop nethogs

# Check system resources
htop
```

## Backup Strategy

### Database Backups

```bash
# Create backup script
nano /home/forum/backup.sh
```

**Backup script content:**
```bash
#!/bin/bash
BACKUP_DIR="/home/forum/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/forum_db_$DATE.sql"

mkdir -p $BACKUP_DIR

# Backup database
docker-compose exec -T db pg_dump -U forum_user forum_db > $BACKUP_FILE

# Compress backup
gzip $BACKUP_FILE

# Keep only last 7 days
find $BACKUP_DIR -name "forum_db_*.sql.gz" -mtime +7 -delete

echo "Backup completed: $BACKUP_FILE.gz"
```

```bash
# Make script executable
chmod +x /home/forum/backup.sh

# Add to crontab (daily at 2 AM)
crontab -e
```

Add to crontab:
```
0 2 * * * /home/forum/backup.sh >> /home/forum/backup.log 2>&1
```

### File Backups

```bash
# Backup application files
tar -czf /home/forum/backups/app_$(date +%Y%m%d).tar.gz /home/forum/repo-forum

# Backup configuration
tar -czf /home/forum/backups/config_$(date +%Y%m%d).tar.gz /home/forum/repo-forum/.env
```

### Offsite Backups

Consider using:
- AWS S3 or similar cloud storage
- rsync to remote server
- Backup services like Backblaze

## Disaster Recovery

### Restore Database

```bash
# Stop application
docker-compose stop app

# Restore from backup
gunzip < backup.sql.gz | docker-compose exec -T db psql -U forum_user -d forum_db

# Restart application
docker-compose start app
```

### Server Migration

```bash
# On new server, follow deployment guide
# Then transfer data:

# Transfer database backup
scp user@old-server:/home/forum/backups/latest.sql.gz .

# Restore database
gunzip < latest.sql.gz | docker-compose exec -T db psql -U forum_user -d forum_db

# Transfer application files
rsync -avz user@old-server:/home/forum/repo-forum/ /home/forum/repo-forum/
```

### Emergency Procedures

**If application is down:**
1. Check logs: `docker-compose logs`
2. Check services: `docker-compose ps`
3. Restart services: `docker-compose restart`
4. Check system resources: `htop`

**If database is corrupted:**
1. Stop application
2. Restore from latest backup
3. Verify data integrity
4. Restart application

**If server is compromised:**
1. Immediately disconnect from network
2. Assess damage
3. Rebuild server from scratch
4. Restore from clean backups
5. Change all passwords and secrets
6. Review security logs

## Performance Tuning

### PostgreSQL Tuning

```bash
# Edit PostgreSQL configuration
sudo nano /etc/postgresql/15/main/postgresql.conf
```

Recommended settings for 4GB RAM:
```
shared_buffers = 1GB
effective_cache_size = 3GB
maintenance_work_mem = 256MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
work_mem = 2621kB
min_wal_size = 1GB
max_wal_size = 4GB
```

### Gunicorn Tuning

Adjust workers based on CPU cores:
```bash
# Formula: (2 x CPU cores) + 1
# For 2 cores: 5 workers
# For 4 cores: 9 workers
```

## Support and Maintenance

### Regular Maintenance Tasks

**Daily:**
- Check application logs
- Monitor disk space
- Verify backups completed

**Weekly:**
- Review security logs
- Check for updates
- Test backup restoration

**Monthly:**
- Review performance metrics
- Update dependencies
- Security audit

### Getting Help

- Check logs first: `docker-compose logs`
- Review this documentation
- Check GitHub issues
- Contact system administrator

## Appendix

### Useful Commands

```bash
# Docker commands
docker-compose ps
docker-compose logs -f
docker-compose restart app
docker-compose exec app bash

# Database commands
docker-compose exec db psql -U forum_user -d forum_db
pg_dump -U forum_user forum_db > backup.sql
psql -U forum_user forum_db < backup.sql

# System commands
sudo systemctl status nginx
sudo systemctl restart nginx
sudo journalctl -u forum -f
```

### Configuration Files Reference

- `.env` - Environment variables
- `config.py` - Application configuration
- `nginx.conf` - Nginx configuration
- `docker-compose.yml` - Docker services definition
- `Dockerfile` - Application container definition

### Port Reference

- 5000 - Application (internal)
- 80 - HTTP (public)
- 443 - HTTPS (public)
- 5432 - PostgreSQL (internal)
