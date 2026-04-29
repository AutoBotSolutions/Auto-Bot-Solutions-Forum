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

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env if needed (defaults work for development)
   ```

5. **Initialize database**
   ```bash
   python init_db.py
   ```

   This will:
   - Create SQLite database (forum.db)
   - Create default admin user (username: admin, password: admin123)
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
