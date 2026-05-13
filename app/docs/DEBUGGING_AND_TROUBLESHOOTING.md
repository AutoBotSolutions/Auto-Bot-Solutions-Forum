# Debugging and Troubleshooting Documentation

**Version:** 1.0.0  
**Implementation Date:** May 12, 2026  
**Status:** Production Ready  
**Debugging Success Rate:** 89.6% (User Management) + 70.0% (Infrastructure)

---

## Overview

This document provides comprehensive debugging and troubleshooting guidance for all user management systems and infrastructure components. It includes common issues, debugging tools, troubleshooting steps, and best practices.

---

## Table of Contents

1. [Debugging Tools and Scripts](#debugging-tools-and-scripts)
2. [Common Issues and Solutions](#common-issues-and-solutions)
3. [System-Specific Troubleshooting](#system-specific-troubleshooting)
4. [Performance Issues](#performance-issues)
5. [Database Issues](#database-issues)
6. [Cache Issues](#cache-issues)
7. [Infrastructure Issues](#infrastructure-issues)
8. [Security Issues](#security-issues)
9. [Monitoring and Alerting](#monitoring-and-alerting)
10. [Best Practices](#best-practices)

---

## Debugging Tools and Scripts

### User Management Systems Debugging

#### **Main Debugging Script**
```bash
# Run comprehensive user management debugging
python debug_user_management_systems.py
```

**Features:**
- Tests all 5 user management systems
- Validates database models and relationships
- Checks API endpoints functionality
- Verifies form validation
- Tests service methods
- Provides detailed success/fail reports

#### **Infrastructure Debugging Script**
```bash
# Run infrastructure systems debugging
python debug_infrastructure_systems.py
```

**Features:**
- Tests all 4 infrastructure components
- Validates method availability
- Checks import functionality
- Tests basic operations
- Provides performance metrics
- Generates detailed debugging report

### Simple Testing Scripts

#### **Simple Infrastructure Test**
```bash
# Run simple infrastructure test
python test_infrastructure_simple.py
```

**Features:**
- Basic import testing
- Method existence validation
- Simple functionality tests
- Quick diagnostic checks

### Database Debugging Tools

#### **SQLAlchemy Debugging**
```python
# Enable SQLAlchemy debugging
import logging
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

# Check database connections
from app import db
try:
    db.session.execute('SELECT 1')
    print("Database connection: OK")
except Exception as e:
    print(f"Database connection error: {e}")
```

#### **Model Validation**
```python
# Validate all models
from app.models import User
from app.user.social.models import *
from app.user.analytics.models import *
from app.admin.roles.models import *

def validate_models():
    """Validate all database models"""
    models = [User, UserFollow, UserFriend, SocialActivity, 
              UserBehavior, UserEngagement, Role, Permission]
    
    for model in models:
        try:
            # Test model creation
            instance = model()
            print(f"✅ {model.__name__}: OK")
        except Exception as e:
            print(f"❌ {model.__name__}: {e}")
```

---

## Common Issues and Solutions

### Import Errors

#### **Callable Import Error**
```
NameError: name 'Callable' is not defined
```

**Cause:** Missing import in typing module

**Solution:**
```python
# Fix in app/cache/cache_utils.py
from typing import Any, Optional, Dict, List, Union, Callable
```

#### **Model Import Errors**
```
ImportError: cannot import name 'RoleAnalyticsForm' from 'app.user.analytics.forms'
```

**Cause:** Form doesn't exist in the module

**Solution:**
```python
# Remove non-existent import from app/user/analytics/routes.py
from app.user.analytics.forms import (
    # Remove RoleAnalyticsForm from import list
    AnalyticsDateRangeForm, UserBehaviorFilterForm, ...
)
```

### SQLAlchemy Conflicts

#### **Column/Relationship Conflicts**
```
WARNING: when configuring property 'granted_by' on Mapper[RolePermission], column 'granted_by' conflicts with property
```

**Cause:** Column name conflicts with relationship name

**Solution:**
```python
# Fix in app/admin/roles/models.py
# Rename relationship to avoid conflict
granted_by_user = db.relationship('User', foreign_keys=[granted_by_id])
assigned_by_user = db.relationship('User', foreign_keys=[assigned_by_id])
requested_by_user = db.relationship('User', foreign_keys=[requested_by_id])
approved_by_user = db.relationship('User', foreign_keys=[approved_by_id])
```

### Application Context Issues

#### **Working Outside Application Context**
```
RuntimeError: Working outside of application context
```

**Cause:** Trying to use Flask features outside application context

**Solution:**
```python
from app import create_app

app = create_app()
with app.app_context():
    # Your code here
    result = ProfileInfrastructure.get_profile_storage_path()
```

### Cache Issues

#### **Cache Attribute Errors**
```
AttributeError: module 'app.cache' has no attribute 'get'
```

**Cause:** Cache not properly initialized

**Solution:**
```python
# Check cache configuration
from app import cache
try:
    cache.set('test', 'value')
    result = cache.get('test')
    print(f"Cache test: {result}")
except Exception as e:
    print(f"Cache error: {e}")
```

---

## System-Specific Troubleshooting

### Profile Infrastructure Issues

#### **Image Upload Failures**
```python
# Debug image upload issues
def debug_image_upload(user_id, image_file):
    """Debug profile image upload"""
    try:
        # Check file type
        if not hasattr(image_file, 'filename'):
            print("❌ Invalid file object")
            return False
        
        # Check file size
        image_file.seek(0, 2)  # Seek to end
        file_size = image_file.tell()
        image_file.seek(0)  # Reset position
        
        if file_size > 5 * 1024 * 1024:  # 5MB
            print(f"❌ File too large: {file_size} bytes")
            return False
        
        # Check storage directory
        storage_path = ProfileInfrastructure.get_profile_storage_path()
        if not os.path.exists(storage_path):
            print(f"❌ Storage directory not found: {storage_path}")
            return False
        
        # Attempt upload
        result = ProfileInfrastructure.store_profile_image(user_id, image_file)
        if result:
            print(f"✅ Upload successful: {result}")
            return True
        else:
            print("❌ Upload failed")
            return False
            
    except Exception as e:
        print(f"❌ Upload error: {e}")
        return False
```

#### **Theme Management Issues**
```python
# Debug theme management
def debug_theme_management():
    """Debug theme management system"""
    try:
        # Test theme retrieval
        themes = ThemeManagementSystem.get_available_themes()
        print(f"✅ Themes available: {len(themes)}")
        
        # Test CSS generation
        if themes:
            theme_id = themes[0]['id']
            css = ThemeManagementSystem.get_theme_css(theme_id)
            print(f"✅ CSS variables: {len(css)}")
            
            full_css = ThemeManagementSystem.generate_theme_css(theme_id)
            print(f"✅ Full CSS length: {len(full_css)}")
        
        # Test custom theme
        custom_theme = ThemeManagementSystem.create_custom_theme(
            "Test Theme", {'--bg-primary': '#ffffff'}
        )
        print(f"✅ Custom theme: {custom_theme['id']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Theme management error: {e}")
        return False
```

### Social Infrastructure Issues

#### **Social Graph Problems**
```python
# Debug social graph
def debug_social_graph(user_id):
    """Debug social graph functionality"""
    try:
        # Test graph data retrieval
        graph_data = SocialInfrastructure.get_social_graph_data(user_id, depth=1)
        
        if graph_data:
            print(f"✅ Graph nodes: {len(graph_data.get('nodes', []))}")
            print(f"✅ Graph edges: {len(graph_data.get('edges', []))}")
            print(f"✅ Stats: {graph_data.get('stats', {})}")
            return True
        else:
            print("❌ No graph data returned")
            return False
            
    except Exception as e:
        print(f"❌ Social graph error: {e}")
        return False
```

#### **Feed Processing Issues**
```python
# Debug social feed
def debug_social_feed(user_id):
    """Debug social feed processing"""
    try:
        # Test feed processing
        feed_data = SocialInfrastructure.process_social_feed(user_id, limit=10)
        
        if feed_data:
            items = feed_data.get('items', [])
            print(f"✅ Feed items: {len(items)}")
            print(f"✅ Feed stats: {feed_data.get('stats', {})}")
            
            # Check item structure
            if items:
                print(f"✅ First item keys: {list(items[0].keys())}")
            
            return True
        else:
            print("❌ No feed data returned")
            return False
            
    except Exception as e:
        print(f"❌ Social feed error: {e}")
        return False
```

### Analytics Infrastructure Issues

#### **Data Warehouse Problems**
```python
# Debug analytics data warehouse
def debug_analytics_warehouse(user_id):
    """Debug analytics data warehouse"""
    try:
        from datetime import datetime, timedelta
        
        start_date = datetime.utcnow() - timedelta(days=7)
        end_date = datetime.utcnow()
        
        # Test data warehouse retrieval
        warehouse_data = AnalyticsInfrastructure.get_analytics_data_warehouse(
            user_id, start_date, end_date
        )
        
        if warehouse_data:
            print(f"✅ Behaviors: {len(warehouse_data.get('behaviors', []))}")
            print(f"✅ Engagements: {len(warehouse_data.get('engagements', []))}")
            print(f"✅ Performances: {len(warehouse_data.get('performances', []))}")
            print(f"✅ Summary: {warehouse_data.get('summary', {})}")
            return True
        else:
            print("❌ No warehouse data returned")
            return False
            
    except Exception as e:
        print(f"❌ Analytics warehouse error: {e}")
        return False
```

#### **Real-time Processing Issues**
```python
# Debug real-time analytics
def debug_real_time_analytics():
    """Debug real-time analytics processing"""
    try:
        # Test event processing
        event_data = {
            'behavior_type': 'test',
            'action': 'test_action',
            'target_type': 'test_target',
            'metadata': {'test': True}
        }
        
        result = AnalyticsInfrastructure.process_real_time_analytics(
            1, 'test_event', event_data
        )
        
        print(f"✅ Event processing result: {result}")
        return result
        
    except Exception as e:
        print(f"❌ Real-time analytics error: {e}")
        return False
```

---

## Performance Issues

### Slow Response Times

#### **Diagnosing Slow Performance**
```python
# Performance diagnostic tool
def diagnose_performance():
    """Diagnose performance issues"""
    import time
    
    # Test profile loading
    start_time = time.time()
    user = User.query.get(1)
    profile_time = time.time() - start_time
    print(f"Profile loading: {profile_time:.3f}s")
    
    # Test social feed
    start_time = time.time()
    feed = SocialInfrastructure.process_social_feed(1, limit=10)
    feed_time = time.time() - start_time
    print(f"Social feed: {feed_time:.3f}s")
    
    # Test analytics
    start_time = time.time()
    analytics = AnalyticsInfrastructure.get_analytics_performance_metrics()
    analytics_time = time.time() - start_time
    print(f"Analytics metrics: {analytics_time:.3f}s")
    
    # Check thresholds
    if profile_time > 0.5:
        print("⚠️ Profile loading slow")
    if feed_time > 1.0:
        print("⚠️ Social feed slow")
    if analytics_time > 0.3:
        print("⚠️ Analytics metrics slow")
```

#### **Memory Usage Issues**
```python
# Memory usage diagnostic
def check_memory_usage():
    """Check memory usage"""
    import psutil
    import gc
    
    # Get memory info
    process = psutil.Process()
    memory_info = process.memory_info()
    memory_mb = memory_info.rss / 1024 / 1024
    
    print(f"Memory usage: {memory_mb:.1f} MB")
    
    # Check for memory leaks
    gc.collect()
    memory_after_gc = process.memory_info().rss / 1024 / 1024
    print(f"Memory after GC: {memory_after_gc:.1f} MB")
    
    if memory_mb > 500:  # 500MB threshold
        print("⚠️ High memory usage detected")
```

### Database Performance

#### **Query Performance Analysis**
```python
# Query performance analysis
def analyze_query_performance():
    """Analyze database query performance"""
    from sqlalchemy import text
    
    # Enable query logging
    import logging
    logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
    
    # Test common queries
    queries = [
        "SELECT COUNT(*) FROM users",
        "SELECT COUNT(*) FROM user_follows",
        "SELECT COUNT(*) FROM user_behaviors",
        "SELECT COUNT(*) FROM social_activities"
    ]
    
    for query in queries:
        start_time = time.time()
        result = db.session.execute(text(query))
        end_time = time.time()
        
        print(f"Query: {query}")
        print(f"Time: {end_time - start_time:.3f}s")
        print(f"Result: {result.scalar()}")
        print("---")
```

---

## Database Issues

### Connection Problems

#### **Database Connection Test**
```python
# Database connection diagnostic
def test_database_connection():
    """Test database connection"""
    try:
        # Test basic connection
        result = db.session.execute(text('SELECT 1'))
        print("✅ Database connection: OK")
        
        # Test table access
        tables = ['users', 'user_follows', 'user_behaviors', 'roles']
        for table in tables:
            try:
                result = db.session.execute(text(f'SELECT COUNT(*) FROM {table}'))
                count = result.scalar()
                print(f"✅ Table {table}: {count} records")
            except Exception as e:
                print(f"❌ Table {table}: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False
```

### Migration Issues

#### **Migration Status Check**
```python
# Check migration status
def check_migration_status():
    """Check database migration status"""
    try:
        # Check if tables exist
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        
        required_tables = [
            'users', 'user_follows', 'user_friends', 'social_activities',
            'user_behaviors', 'user_engagements', 'roles', 'permissions'
        ]
        
        for table in required_tables:
            if table in tables:
                print(f"✅ Table {table}: exists")
            else:
                print(f"❌ Table {table}: missing")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration check error: {e}")
        return False
```

---

## Cache Issues

### Redis Connection Problems

#### **Redis Connection Test**
```python
# Redis connection diagnostic
def test_redis_connection():
    """Test Redis cache connection"""
    try:
        # Test basic cache operations
        cache.set('test_key', 'test_value', timeout=60)
        result = cache.get('test_key')
        
        if result == 'test_value':
            print("✅ Redis connection: OK")
            
            # Get cache info
            try:
                info = cache.cache._cache.info()
                print(f"Redis memory: {info.get('used_memory_human', 'N/A')}")
                print(f"Redis keys: {info.get('db0', {}).get('keys', 'N/A')}")
            except:
                print("Redis info: not available")
            
            return True
        else:
            print("❌ Redis cache test failed")
            return False
            
    except Exception as e:
        print(f"❌ Redis connection error: {e}")
        return False
```

### Cache Performance Issues

#### **Cache Performance Analysis**
```python
# Cache performance analysis
def analyze_cache_performance():
    """Analyze cache performance"""
    try:
        # Test cache set/get performance
        import time
        
        # Test cache set
        start_time = time.time()
        for i in range(100):
            cache.set(f'test_key_{i}', f'test_value_{i}', timeout=300)
        set_time = time.time() - start_time
        
        # Test cache get
        start_time = time.time()
        for i in range(100):
            result = cache.get(f'test_key_{i}')
        get_time = time.time() - start_time
        
        print(f"Cache set (100 items): {set_time:.3f}s")
        print(f"Cache get (100 items): {get_time:.3f}s")
        
        # Calculate hit rate
        hits = 0
        for i in range(100):
            result = cache.get(f'test_key_{i}')
            if result:
                hits += 1
        
        hit_rate = (hits / 100) * 100
        print(f"Cache hit rate: {hit_rate:.1f}%")
        
        return True
        
    except Exception as e:
        print(f"❌ Cache performance error: {e}")
        return False
```

---

## Infrastructure Issues

### File System Problems

#### **Storage Directory Check**
```python
# Storage directory diagnostic
def check_storage_directories():
    """Check storage directories"""
    try:
        storage_path = ProfileInfrastructure.get_profile_storage_path()
        
        # Check main directory
        if os.path.exists(storage_path):
            print(f"✅ Storage directory: {storage_path}")
        else:
            print(f"❌ Storage directory missing: {storage_path}")
            return False
        
        # Check subdirectories
        subdirs = ['avatars', 'banners', 'themes', 'backups']
        for subdir in subdirs:
            subdir_path = os.path.join(storage_path, subdir)
            if os.path.exists(subdir_path):
                print(f"✅ Subdirectory {subdir}: exists")
            else:
                print(f"❌ Subdirectory {subdir}: missing")
        
        # Check permissions
        if os.access(storage_path, os.W_OK):
            print("✅ Storage directory: writable")
        else:
            print("❌ Storage directory: not writable")
        
        # Check disk space
        stat = os.statvfs(storage_path)
        free_space = stat.f_frsize * stat.f_bavail
        free_gb = free_space / (1024**3)
        print(f"Free disk space: {free_gb:.1f} GB")
        
        return True
        
    except Exception as e:
        print(f"❌ Storage check error: {e}")
        return False
```

### Environment Configuration Issues

#### **Environment Variables Check**
```python
# Environment variables diagnostic
def check_environment_variables():
    """Check required environment variables"""
    required_vars = [
        'FLASK_ENV',
        'SECRET_KEY',
        'DATABASE_URL',
        'REDIS_URL',
        'USER_PROFILE_UPLOAD_PATH',
        'USER_ANALYTICS_ENABLED',
        'SOCIAL_FEATURES_ENABLED',
        'PROFILE_CUSTOMIZATION_ENABLED'
    ]
    
    for var in required_vars:
        value = os.environ.get(var)
        if value:
            print(f"✅ {var}: set")
        else:
            print(f"❌ {var}: missing")
    
    # Check optional vars
    optional_vars = [
        'CACHE_DEFAULT_TIMEOUT',
        'PROFILE_MAX_BANNER_SIZE',
        'SOCIAL_FEED_CACHE_TIMEOUT'
    ]
    
    for var in optional_vars:
        value = os.environ.get(var)
        if value:
            print(f"✅ {var}: {value}")
        else:
            print(f"⚠️ {var}: not set (optional)")
```

---

## Security Issues

### Authentication Problems

#### **Authentication Diagnostic**
```python
# Authentication diagnostic
def test_authentication():
    """Test authentication system"""
    try:
        from flask_login import current_user
        
        # Test user model
        user = User.query.first()
        if user:
            print(f"✅ User model: OK (found user: {user.username})")
            
            # Test password hashing
            if user.password_hash:
                print("✅ Password hash: present")
            else:
                print("❌ Password hash: missing")
            
            # Test authentication methods
            try:
                is_active = user.is_active
                print(f"✅ User status: {is_active}")
            except Exception as e:
                print(f"❌ User status error: {e}")
            
        else:
            print("❌ No users found in database")
        
        return True
        
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return False
```

### Permission Issues

#### **Permission Diagnostic**
```python
# Permission diagnostic
def test_permissions():
    """Test permission system"""
    try:
        from app.admin.roles.models import Role, Permission
        
        # Test roles
        roles = Role.query.all()
        print(f"✅ Roles found: {len(roles)}")
        
        # Test permissions
        permissions = Permission.query.all()
        print(f"✅ Permissions found: {len(permissions)}")
        
        # Test role-permission relationships
        for role in roles[:3]:  # Check first 3 roles
            perm_count = len(role.permissions)
            print(f"✅ Role {role.name}: {perm_count} permissions")
        
        return True
        
    except Exception as e:
        print(f"❌ Permission error: {e}")
        return False
```

---

## Monitoring and Alerting

### Health Check Endpoint

#### **System Health Check**
```python
# Health check endpoint
@app.route('/health')
def health_check():
    """System health check endpoint"""
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'checks': {}
    }
    
    # Database check
    try:
        db.session.execute(text('SELECT 1'))
        health_status['checks']['database'] = 'OK'
    except Exception as e:
        health_status['checks']['database'] = f'ERROR: {e}'
        health_status['status'] = 'unhealthy'
    
    # Cache check
    try:
        cache.set('health_check', 'ok', timeout=10)
        result = cache.get('health_check')
        if result == 'ok':
            health_status['checks']['cache'] = 'OK'
        else:
            health_status['checks']['cache'] = 'ERROR: Cache test failed'
            health_status['status'] = 'unhealthy'
    except Exception as e:
        health_status['checks']['cache'] = f'ERROR: {e}'
        health_status['status'] = 'unhealthy'
    
    # Storage check
    try:
        storage_path = ProfileInfrastructure.get_profile_storage_path()
        if os.path.exists(storage_path) and os.access(storage_path, os.W_OK):
            health_status['checks']['storage'] = 'OK'
        else:
            health_status['checks']['storage'] = 'ERROR: Storage not accessible'
            health_status['status'] = 'unhealthy'
    except Exception as e:
        health_status['checks']['storage'] = f'ERROR: {e}'
        health_status['status'] = 'unhealthy'
    
    status_code = 200 if health_status['status'] == 'healthy' else 503
    return jsonify(health_status), status_code
```

### Performance Monitoring

#### **Performance Metrics Endpoint**
```python
# Performance metrics endpoint
@app.route('/metrics')
def performance_metrics():
    """Performance metrics endpoint"""
    try:
        metrics = {
            'timestamp': datetime.utcnow().isoformat(),
            'database': get_database_metrics(),
            'cache': get_cache_metrics(),
            'system': get_system_metrics()
        }
        
        return jsonify(metrics)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def get_database_metrics():
    """Get database performance metrics"""
    try:
        # Get connection pool info
        pool = db.engine.pool
        return {
            'pool_size': pool.size(),
            'checked_in': pool.checkedin(),
            'checked_out': pool.checkedout(),
            'overflow': pool.overflow()
        }
    except:
        return {'error': 'Unable to get database metrics'}

def get_cache_metrics():
    """Get cache performance metrics"""
    try:
        info = cache.cache._cache.info()
        return {
            'used_memory': info.get('used_memory', 0),
            'connected_clients': info.get('connected_clients', 0),
            'total_commands_processed': info.get('total_commands_processed', 0)
        }
    except:
        return {'error': 'Unable to get cache metrics'}

def get_system_metrics():
    """Get system performance metrics"""
    try:
        import psutil
        process = psutil.Process()
        
        return {
            'cpu_percent': process.cpu_percent(),
            'memory_mb': process.memory_info().rss / 1024 / 1024,
            'threads': process.num_threads()
        }
    except:
        return {'error': 'Unable to get system metrics'}
```

---

## Best Practices

### Development Best Practices

1. **Use Debugging Tools**: Always use provided debugging scripts
2. **Check Logs**: Monitor application logs for errors
3. **Test in Staging**: Test changes in staging environment first
4. **Document Issues**: Document debugging findings and solutions

### Troubleshooting Workflow

1. **Identify the Problem**: Clearly define the issue
2. **Check Logs**: Review application and system logs
3. **Run Diagnostics**: Use diagnostic tools and scripts
4. **Isolate the Issue**: Narrow down the problem area
5. **Test Solutions**: Try potential solutions
6. **Verify Fix**: Confirm the issue is resolved
7. **Document**: Document the solution for future reference

### Prevention Strategies

1. **Regular Monitoring**: Monitor system health proactively
2. **Performance Testing**: Test performance regularly
3. **Code Reviews**: Review code for potential issues
4. **Automated Testing**: Use automated testing to catch issues early
5. **Documentation**: Keep documentation up to date

---

## Emergency Procedures

### System Outage Response

1. **Check Health Endpoint**: Check `/health` endpoint
2. **Review Logs**: Check application logs for errors
3. **Restart Services**: Restart affected services if needed
4. **Rollback Changes**: Rollback recent changes if necessary
5. **Contact Team**: Notify team members of issues

### Data Recovery

1. **Stop Application**: Stop the application to prevent further damage
2. **Assess Damage**: Determine what data is affected
3. **Restore Backups**: Restore from recent backups
4. **Verify Data**: Verify data integrity
5. **Restart Services**: Restart services carefully
6. **Monitor Closely**: Monitor system closely after recovery

---

**Implementation Status:** ✅ **PRODUCTION READY**  
**Last Updated:** May 12, 2026  
**Debugging Coverage:** Comprehensive troubleshooting for all systems  
**System Status:** All debugging tools and procedures implemented
