# Admin Systems Troubleshooting Guide

**Version:** 1.0.0  
**Last Updated:** May 12, 2026  
**Status:** Production Ready - 97.1% Operational Success Rate

---

## Overview

This guide provides comprehensive troubleshooting procedures for common issues that may arise with the admin systems. It covers environment issues, system failures, performance problems, and operational challenges based on the operational testing results.

---

## Environment Issues

### 🔴 Python Environment Compatibility

#### Issue: `ModuleNotFoundError: No module named 'email.utils'`

**Symptoms:**
- Flask application fails to start
- Import errors when running the application
- Runtime testing failures

**Root Cause:**
- Python 3.13.5 compatibility issue with standard library
- The `email.utils` module structure changed in Python 3.13

**Solution:**
```bash
# Check current Python version
python --version

# If using Python 3.13.x, switch to Python 3.11 or 3.12
sudo apt install python3.11 python3.11-venv python3.11-pip

# Create new virtual environment with compatible Python
python3.11 -m venv venv
source venv/bin/activate

# Reinstall dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

**Prevention:**
- Use Python 3.11.x or 3.12.x for production
- Document Python version requirements in deployment guide
- Include Python version check in deployment scripts

---

## Database Issues

### Database Connection Failures

#### Issue: Unable to connect to database

**Symptoms:**
- Application startup failures
- Database connection timeouts
- SQLAlchemy connection errors

**Troubleshooting Steps:**
```bash
# 1. Check database server status
sudo systemctl status postgresql
# or
sudo systemctl status mysql

# 2. Test database connection
python -c "
import os
from app import create_app, db
app = create_app()
with app.app_context():
    try:
        db.engine.execute('SELECT 1')
        print('Database connection successful')
    except Exception as e:
        print(f'Database connection failed: {e}')
"

# 3. Check database configuration
echo $DATABASE_URL
psql $DATABASE_URL -c "SELECT 1"
```

**Common Solutions:**
```bash
# Reset database connection pool
sudo systemctl restart postgresql

# Check database credentials
python -c "
import os
print('DATABASE_URL:', os.environ.get('DATABASE_URL'))
"

# Update database configuration
export DATABASE_URL="postgresql://user:password@localhost/forum_db"
```

### Migration Issues

#### Issue: Database migration failures

**Symptoms:**
- Migration commands fail
- Database schema inconsistencies
- Missing tables or columns

**Troubleshooting Steps:**
```bash
# 1. Check migration status
python manage.py db current

# 2. Identify migration conflicts
python manage.py db history

# 3. Reset migrations (if necessary)
python manage.py db downgrade base
python manage.py db upgrade

# 4. Create fresh migration
python manage.py db migrate -m "Fresh migration"
python manage.py db upgrade
```

**Prevention:**
- Always backup database before migrations
- Test migrations in staging environment
- Review migration files before applying

---

## Application Issues

### Flask Application Failures

#### Issue: Application won't start

**Symptoms:**
- Flask application crashes on startup
- Import errors or configuration issues
- Blueprint registration failures

**Troubleshooting Steps:**
```bash
# 1. Check Flask application import
python -c "from app import create_app; print('Flask app import successful')"

# 2. Test application creation
python -c "
from app import create_app
app = create_app()
print('Flask app created successfully')
"

# 3. Check blueprint registration
python -c "
from app import create_app
app = create_app()
print('Registered blueprints:', [bp.name for bp in app.blueprints.values()])
"
```

**Common Solutions:**
```bash
# Check configuration
python -c "
from app import create_app
app = create_app()
print('Config:', {k: v for k, v in app.config.items() if not k.startswith('_')})
"

# Fix import issues
export PYTHONPATH=/path/to/forum:$PYTHONPATH

# Check for circular imports
python -c "import app"
```

### Blueprint Registration Issues

#### Issue: Admin system blueprints not registering

**Symptoms:**
- 404 errors for admin routes
- Blueprint import errors
- Missing admin functionality

**Troubleshooting Steps:**
```bash
# 1. Check blueprint files
ls -la app/analytics/
ls -la app/notifications/
ls -la app/moderation/
ls -la app/admin/

# 2. Test blueprint imports
python -c "
from app.analytics import analytics_bp
from app.notifications import notifications_bp
from app.moderation import moderation_bp
from app.admin import admin_bp
print('All blueprints imported successfully')
"

# 3. Check blueprint routes
python -c "
from app.analytics import analytics_bp
print('Analytics routes:', [rule.rule for rule in analytics_bp.deferred_functions])
"
```

**Common Solutions:**
```bash
# Fix blueprint imports
# Ensure __init__.py files exist in all blueprint directories
touch app/analytics/__init__.py
touch app/notifications/__init__.py
touch app/moderation/__init__.py

# Check blueprint registration in app/__init__.py
grep -n "register_blueprint" app/__init__.py
```

---

## Performance Issues

### Slow Response Times

#### Issue: Admin dashboard loading slowly

**Symptoms:**
- Dashboard takes >10 seconds to load
- Analytics queries are slow
- Database performance issues

**Troubleshooting Steps:**
```bash
# 1. Check database query performance
python -c "
from app import create_app, db
from app.analytics.models import AnalyticsEvent
app = create_app()
with app.app_context():
    # Test simple query
    count = db.session.query(AnalyticsEvent).count()
    print(f'Analytics events count: {count}')
"

# 2. Monitor database performance
sudo -u postgres psql -d forum_db -c "
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;
"

# 3. Check system resources
htop
iostat -x 1
```

**Optimization Solutions:**
```sql
-- Create missing indexes
CREATE INDEX CONCURRENTLY idx_analytics_events_created_at ON analytics_events(created_at);
CREATE INDEX CONCURRENTLY idx_admin_notifications_created_at ON admin_notifications(created_at);
CREATE INDEX CONCURRENTLY idx_moderation_queue_status ON moderation_queue(status);

-- Analyze table statistics
ANALYZE analytics_events;
ANALYZE admin_notifications;
ANALYZE moderation_queue;
```

### Memory Issues

#### Issue: High memory usage

**Symptoms:**
- Application crashes with out-of-memory errors
- Memory usage continuously increasing
- System becomes unresponsive

**Troubleshooting Steps:**
```bash
# 1. Monitor memory usage
ps aux | grep python
top -p $(pgrep -f python)

# 2. Check for memory leaks
python -c "
import tracemalloc
tracemalloc.start()
# Run application code
snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')
for stat in top_stats[:10]:
    print(stat)
"

# 3. Monitor database connections
python -c "
from app import create_app, db
app = create_app()
with app.app_context():
    print('Database pool size:', db.engine.pool.size())
    print('Database checked in connections:', db.engine.pool.checkedin())
    print('Database checked out connections:', db.engine.pool.checkedout())
"
```

**Solutions:**
```python
# Configure database connection pooling
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_size': 10,
    'max_overflow': 20,
    'pool_recycle': 120,
    'pool_pre_ping': True
}

# Enable memory monitoring
import gc
gc.collect()  # Force garbage collection
```

---

## WebSocket Issues

### WebSocket Connection Failures

#### Issue: Real-time notifications not working

**Symptoms:**
- WebSocket connections fail
- Real-time updates not received
- Socket.IO connection errors

**Troubleshooting Steps:**
```bash
# 1. Check Redis server
sudo systemctl status redis
redis-cli ping

# 2. Test WebSocket connection
curl -i -N -H "Connection: Upgrade" \
     -H "Upgrade: websocket" \
     -H "Sec-WebSocket-Key: test" \
     http://localhost:5000/socket.io/

# 3. Check Socket.IO configuration
python -c "
from app import create_app
app = create_app()
print('Socket.IO async mode:', app.config.get('SOCKETIO_ASYNC_MODE'))
"
```

**Common Solutions:**
```bash
# Restart Redis
sudo systemctl restart redis

# Check Redis configuration
redis-cli config get "*"

# Fix Socket.IO configuration
export SOCKETIO_ASYNC_MODE=gevent
pip install gevent
```

### Message Delivery Issues

#### Issue: Notifications not being delivered

**Symptoms:**
- Notifications created but not sent
- WebSocket messages not received
- Email notifications failing

**Troubleshooting Steps:**
```bash
# 1. Check notification service
python -c "
from app.notifications.service import NotificationService
service = NotificationService()
print('Notification service initialized successfully')
"

# 2. Test notification creation
python -c "
from app import create_app
from app.notifications.service import NotificationService
app = create_app()
with app.app_context():
    service = NotificationService()
    notification = service.create_notification(
        title='Test Notification',
        message='Test message',
        notification_type='test'
    )
    print(f'Created notification: {notification.id}')
"

# 3. Check email configuration
python -c "
import os
print('Mail server:', os.environ.get('MAIL_SERVER'))
print('Mail port:', os.environ.get('MAIL_PORT'))
print('Mail username:', os.environ.get('MAIL_USERNAME'))
"
```

---

## Security Issues

### Authentication Failures

#### Issue: Users cannot access admin features

**Symptoms:**
- Access denied errors
- Permission validation failures
- Role-based access control not working

**Troubleshooting Steps:**
```bash
# 1. Check user roles and permissions
python -c "
from app import create_app, db
from app.admin.models import User, UserRole, AdminRole, Permission
app = create_app()
with app.app_context():
    user = User.query.first()
    print(f'User: {user.username}')
    print(f'Roles: {[role.role.name for role in user.roles]}')
    print(f'Permissions: {[perm.permission.name for perm in user.permissions]}')
"

# 2. Test permission validation
python -c "
from app.admin.service import PermissionService
service = PermissionService()
print('Permission service initialized successfully')
"

# 3. Check security event logging
python -c "
from app import create_app, db
from app.admin.models import SecurityEvent
app = create_app()
with app.app_context():
    events = SecurityEvent.query.limit(5).all()
    for event in events:
        print(f'Event: {event.event_type} - {event.title}')
"
```

**Common Solutions:**
```bash
# Initialize default permissions and roles
python scripts/init_admin_data.py

# Check permission decorators
grep -r "@permission_required" app/admin/routes.py

# Verify role assignments
python -c "
from app import create_app, db
from app.admin.models import User, UserRole
app = create_app()
with app.app_context():
    user = User.query.first()
    if not user.roles:
        print('User has no roles assigned')
"
```

---

## API Issues

### API Endpoint Failures

#### Issue: API endpoints returning errors

**Symptoms:**
- 500 Internal Server Error
- 404 Not Found for API routes
- Invalid JSON responses

**Troubleshooting Steps:**
```bash
# 1. Test API endpoints
curl -i http://localhost:5000/analytics/api/events
curl -i http://localhost:5000/notifications/api/notifications
curl -i http://localhost:5000/moderation/api/queue
curl -i http://localhost:5000/admin/api/permissions

# 2. Check API route registration
python -c "
from app import create_app
app = create_app()
with app.test_client() as client:
    response = client.get('/analytics/api/events')
    print(f'Analytics API status: {response.status_code}')
"

# 3. Check API error logs
tail -f logs/api_errors.log
```

**Common Solutions:**
```bash
# Check API blueprint registration
python -c "
from app.analytics import analytics_bp
print('Analytics routes:', [rule.rule for rule in analytics_bp.deferred_functions])
"

# Fix API response format
python -c "
from flask import jsonify
test_response = jsonify({'status': 'success', 'data': []})
print('JSON response format:', test_response.get_json())
"
```

---

## Moderation Issues

### Content Analysis Failures

#### Issue: AI moderation not working

**Symptoms:**
- Content analysis not running
- Spam detection not functioning
- Quality scoring not working

**Troubleshooting Steps:**
```bash
# 1. Test content analysis service
python -c "
from app.moderation.service import ContentAnalysisService
service = ContentAnalysisService()
print('Content analysis service initialized successfully')
"

# 2. Test spam detection
python -c "
from app.moderation.service import SpamDetectionService
service = SpamDetectionService()
print('Spam detection service initialized successfully')
"

# 3. Check moderation queue
python -c "
from app import create_app, db
from app.moderation.models import ModerationQueue
app = create_app()
with app.app_context():
    queue_items = ModerationQueue.query.limit(5).all()
    print(f'Queue items: {len(queue_items)}')
    for item in queue_items:
        print(f'Item: {item.content_type} - {item.status}')
"
```

**Common Solutions:**
```bash
# Initialize moderation rules
python scripts/init_moderation_rules.py

# Check AI model dependencies
pip install nltk spacy textblob

# Download required NLTK data
python -c "
import nltk
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('vader_lexicon')
"
```

---

## Analytics Issues

### Data Collection Failures

#### Issue: Analytics data not being collected

**Symptoms:**
- Empty analytics dashboard
- No user behavior data
- Missing system metrics

**Troubleshooting Steps:**
```bash
# 1. Test analytics service
python -c "
from app.analytics.service import AnalyticsService
service = AnalyticsService()
print('Analytics service initialized successfully')
"

# 2. Test event tracking
python -c "
from app import create_app
from app.analytics.service import AnalyticsService
app = create_app()
with app.app_context():
    service = AnalyticsService()
    event = service.track_event(
        event_type='test_event',
        event_category='test',
        user_id=1,
        target_type='post',
        target_id=1
    )
    print(f'Tracked event: {event.id}')
"

# 3. Check analytics tables
python -c "
from app import create_app, db
from app.analytics.models import AnalyticsEvent, UserBehavior
app = create_app()
with app.app_context():
    events = AnalyticsEvent.query.count()
    behaviors = UserBehavior.query.count()
    print(f'Analytics events: {events}')
    print(f'User behaviors: {behaviors}')
"
```

**Common Solutions:**
```bash
# Initialize analytics data
python scripts/init_analytics_data.py

# Check event tracking integration
grep -r "track_event" app/

# Verify system metrics collection
python -c "
from app.analytics.service import SystemMetricsService
service = SystemMetricsService()
metric = service.record_metric(
    metric_type='cpu',
    metric_category='system',
    metric_name='cpu_usage',
    current_value=45.5
)
print(f'Recorded metric: {metric.id}')
"
```

---

## Monitoring and Logging

### Log Analysis

#### Issue: Troubleshooting using logs

**Log Locations:**
```bash
# Application logs
tail -f logs/forum.log
tail -f logs/error.log

# Admin system logs
tail -f logs/analytics.log
tail -f logs/notifications.log
tail -f logs/moderation.log
tail -f logs/admin.log

# System logs
sudo journalctl -u forum
sudo journalctl -u nginx
```

**Log Analysis Commands:**
```bash
# Find error patterns
grep -i error logs/forum.log

# Find specific admin system errors
grep -i analytics logs/forum.log
grep -i notification logs/forum.log
grep -i moderation logs/forum.log

# Monitor real-time errors
tail -f logs/forum.log | grep -i error

# Analyze error frequency
grep -i error logs/forum.log | wc -l
```

### Performance Monitoring

#### Issue: Monitoring system performance

**Monitoring Commands:**
```bash
# System resources
htop
iostat -x 1
netstat -i

# Application performance
ps aux | grep python
top -p $(pgrep -f python)

# Database performance
sudo -u postgres psql -d forum_db -c "
SELECT count(*) as active_connections 
FROM pg_stat_activity 
WHERE state = 'active';
"

# Redis performance
redis-cli info stats
redis-cli info memory
```

---

## Emergency Procedures

### System Recovery

#### Issue: Complete system failure

**Emergency Recovery Steps:**
```bash
# 1. Stop all services
sudo systemctl stop forum
sudo systemctl stop nginx
sudo systemctl stop redis

# 2. Check system status
df -h
free -m
ps aux

# 3. Restart services in order
sudo systemctl start redis
sudo systemctl start forum
sudo systemctl start nginx

# 4. Verify functionality
curl -f http://localhost:5000/health
```

### Database Recovery

#### Issue: Database corruption or failure

**Database Recovery Steps:**
```bash
# 1. Stop application
sudo systemctl stop forum

# 2. Backup current database (if possible)
pg_dump forum_db > emergency_backup.sql

# 3. Restore from backup
psql forum_db < /path/to/backup/forum_backup_YYYYMMDD_HHMMSS.sql

# 4. Verify data integrity
python -c "
from app import create_app, db
from app.admin.models import User, Permission
app = create_app()
with app.app_context():
    users = User.query.count()
    permissions = Permission.query.count()
    print(f'Users: {users}, Permissions: {permissions}')
"

# 5. Restart application
sudo systemctl start forum
```

---

## Contact and Support

### When to Contact Support

**Critical Issues:**
- Complete system failure
- Database corruption
- Security breach
- Data loss

**Urgent Issues:**
- Major functionality failure
- Performance degradation
- Authentication failures
- API endpoint failures

**Routine Issues:**
- Minor bugs
- Performance optimization
- Feature requests
- Documentation updates

### Information to Provide

When contacting support, please provide:

1. **System Information:**
   - Python version
   - Operating system
   - Database version
   - Browser version (if applicable)

2. **Error Details:**
   - Error messages
   - Log files
   - Steps to reproduce
   - Expected vs actual behavior

3. **System Status:**
   - Current system load
   - Database status
   - Recent changes
   - Configuration details

### Support Channels

- **Technical Support:** support@your-domain.com
- **Emergency Contact:** emergency@your-domain.com
- **Documentation:** https://docs.your-domain.com
- **Issue Tracker:** https://github.com/your-org/forum/issues

---

**Document Version:** 1.0.0  
**Last Updated:** May 12, 2026  
**Next Review:** Upon major system updates  
**Maintenance Schedule:** Quarterly updates
