# Caching Infrastructure Documentation

## Overview

The Caching Infrastructure system provides enterprise-grade caching capabilities with Redis cluster support, comprehensive monitoring, automated backup strategies, and performance tuning. This system ensures high-performance data access, scalability, and reliability for production applications.

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                    Caching Infrastructure                        │
├─────────────────────────────────────────────────────────────────┤
│  CacheManager          │  RedisClusterManager  │  CacheMonitor      │
│  - Multi-level cache   │  - Cluster setup      │  - Metrics collection│
│  - Redis integration   │  - Health monitoring  │  - Alerting         │
│  - Performance tuning  │  - Failover support    │  - Real-time stats  │
├─────────────────────────────────────────────────────────────────┤
│  CacheBackupManager    │  CacheTuner           │  CacheRoutes        │
│  - Backup strategies   │  - Auto-tuning        │  - Flask API        │
│  - Automation          │  - Optimization       │  - Management      │
│  - Compression         │  - Performance analysis│  - Configuration    │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
Application Request → CacheManager → Redis Cluster → Response
        │                   │              │
        ├─ L1 Cache         ├─ Monitoring   ├─ Health Check
        ├─ L2 Cache         ├─ Backup       ├─ Failover
        └─ L3 Cache         └─ Tuning       └─ Metrics
```

## Components

### CacheManager

The central cache management system with multi-level caching support.

#### Features
- **Multi-level Caching**: L1 (memory), L2 (Redis), L3 (persistent)
- **Redis Integration**: Single instance and cluster support
- **Performance Tuning**: Automatic optimization and monitoring
- **Health Monitoring**: Real-time health checks and metrics
- **Graceful Degradation**: Fallback mechanisms for Redis failures

#### Configuration
```python
from app.infrastructure.caching import CacheManager, CacheConfig

config = CacheConfig(
    max_connections=100,
    connection_timeout=5,
    socket_timeout=5,
    max_retries=3,
    retry_delay=0.1,
    health_check_interval=30,
    backup_interval=3600,
    enable_monitoring=True,
    enable_auto_tuning=True,
    cache_strategy="write_through",
    default_ttl=3600,
    max_memory="2gb",
    eviction_policy="allkeys-lru"
)

manager = CacheManager(config)
```

#### Usage Examples

##### Basic Cache Operations
```python
# Set value in cache
success = manager.set("user:123", {"name": "John", "age": 30}, ttl=3600)

# Get value from cache
user_data = manager.get("user:123")

# Delete from cache
success = manager.delete("user:123")

# Clear cache with pattern
cleared_count = manager.clear("user:*")
```

##### Cache Level Management
```python
from app.infrastructure.caching.cache_manager import CacheLevel

# L1 Cache (Memory)
manager.set("temp_data", data, level=CacheLevel.L1)

# L2 Cache (Redis)
manager.set("user_data", data, level=CacheLevel.L2)

# L3 Cache (Persistent)
manager.set("critical_data", data, level=CacheLevel.L3)
```

##### Health Monitoring
```python
# Get health status
health = manager.health_check()

# Get performance statistics
stats = manager.get_stats()

# Get configuration
config = manager.get_config()
```

### RedisClusterManager

Manages Redis cluster setup, configuration, and operations for high-availability caching.

#### Features
- **Cluster Setup**: Automated Redis cluster configuration
- **Health Monitoring**: Real-time cluster health checks
- **Node Management**: Add/remove cluster nodes
- **Failover Support**: Automatic failover and recovery
- **Load Balancing**: Request distribution across cluster

#### Configuration
```python
from app.infrastructure.caching import RedisClusterManager, ClusterConfig

config = ClusterConfig(
    cluster_name="mycluster",
    cluster_port=16379,
    shard_count=3,
    replicas_per_shard=1,
    max_memory="2gb",
    max_memory_policy="allkeys-lru",
    timeout=5000,
    tcp_keepalive=300,
    max_connections=10000
)

cluster_manager = RedisClusterManager(config)
```

#### Usage Examples

##### Cluster Management
```python
# Get cluster information
cluster_info = cluster_manager.get_cluster_info()

# Add new node
success = cluster_manager.add_node("localhost", 7000, "master")

# Remove node
success = cluster_manager.remove_node("localhost", 7000)

# Trigger failover
success = cluster_manager.failover_node("localhost", 7000)
```

##### Node Operations
```python
# Get node statistics
node_stats = cluster_manager.get_node_stats("localhost", 7000)

# Reshard cluster
success = cluster_manager.reshard_cluster(
    "localhost", 7000,  # source
    "localhost", 7001,  # target
    1000                # slot count
)
```

### CacheMonitor

Comprehensive monitoring system for cache infrastructure with metrics collection, alerting, and analytics.

#### Features
- **Real-time Metrics**: Performance metrics collection
- **Alerting System**: Configurable alerts with thresholds
- **Historical Data**: Metrics history and trends
- **Performance Analysis**: Response time and hit rate analysis
- **Health Monitoring**: System health checks

#### Configuration
```python
from app.infrastructure.caching import CacheMonitor

monitor = CacheMonitor(buffer_size=10000)
```

#### Usage Examples

##### Metrics Collection
```python
# Record cache operation
monitor.record_cache_operation("get", True, 0.001, "node1")

# Record node statistics
node_stats = {
    'memory_usage': 1024 * 1024,
    'key_count': 1000,
    'connected_clients': 10,
    'info': {
        'instantaneous_ops_per_sec': 100,
        'keyspace_hits': 50,
        'keyspace_misses': 50
    }
}
monitor.record_node_stats("node1", node_stats)
```

##### Alert Management
```python
from app.infrastructure.caching.cache_monitor import AlertLevel

# Create alert
monitor.create_alert(
    "low_hit_rate",
    "Low Cache Hit Rate",
    AlertLevel.WARNING,
    "hit_rate",
    0.7,
    300  # 5 minutes window
)

# Get alerts
alerts = monitor.get_alerts()

# Enable/disable alerts
monitor.enable_alert("low_hit_rate")
monitor.disable_alert("low_hit_rate")
```

##### Performance Analysis
```python
# Get performance statistics
stats = monitor.get_performance_stats()

# Get metrics summary
summary = monitor.get_metrics_summary()

# Export metrics
metrics_json = monitor.export_metrics("json")
```

### CacheBackupManager

Manages backup strategies and operations for cache infrastructure with automated scheduling and restoration.

#### Features
- **Multiple Backup Types**: Full, incremental, snapshot, RDB, AOF
- **Automated Scheduling**: Configurable backup intervals
- **Compression**: Optional backup compression
- **Remote Storage**: Cloud storage integration support
- **Verification**: Backup integrity verification

#### Configuration
```python
from app.infrastructure.caching import CacheBackupManager, BackupConfig

config = BackupConfig(
    backup_dir="/var/cache/backups",
    backup_interval=3600,  # 1 hour
    retention_days=7,
    compression_enabled=True,
    encryption_enabled=False,
    remote_backup_enabled=False,
    max_concurrent_backups=2,
    backup_timeout=3600,
    verify_backup=True
)

backup_manager = CacheBackupManager(config)
```

#### Usage Examples

##### Backup Operations
```python
# Create backup
backup_id = backup_manager.create_backup(
    "daily_backup",
    "full",
    nodes=["node1:6379", "node2:6379"]
)

# Restore from backup
success = backup_manager.restore_backup(backup_id)

# Cancel backup
success = backup_manager.cancel_backup(backup_id)
```

##### Backup Management
```python
# Get backup jobs
jobs = backup_manager.get_backup_jobs()

# Get backup statistics
stats = backup_manager.get_backup_stats()

# Clean up old backups
cleaned_count = backup_manager.cleanup_old_backups()
```

### CacheTuner

Automatic performance tuning and optimization for cache infrastructure.

#### Features
- **Auto-tuning**: Automatic performance optimization
- **Multiple Strategies**: Conservative, balanced, aggressive, adaptive
- **Performance Analysis**: Hit rate and response time analysis
- **Recommendations**: Optimization suggestions
- **Configuration Updates**: Automatic configuration adjustments

#### Configuration
```python
from app.infrastructure.caching import CacheTuner, TuningConfig, TuningStrategy

config = TuningConfig(
    strategy=TuningStrategy.BALANCED,
    tuning_interval=300,  # 5 minutes
    memory_threshold=0.8,
    hit_rate_threshold=0.7,
    response_time_threshold=0.1,
    enable_auto_tuning=True,
    enable_memory_optimization=True,
    enable_ttl_optimization=True,
    enable_connection_optimization=True
)

tuner = CacheTuner(config)
```

#### Usage Examples

##### Manual Tuning
```python
# Manual memory tuning
success = tuner.manual_tune("memory", {"max_memory": "4gb"})

# Manual eviction tuning
success = tuner.manual_tune("eviction", {"policy": "allkeys-lru"})

# Manual TTL tuning
success = tuner.manual_tune("ttl", {"min_ttl": 60, "max_ttl": 86400})
```

##### Recommendations
```python
# Get tuning recommendations
recommendations = tuner.get_tuning_recommendations()

# Get tuning history
history = tuner.get_tuning_history()

# Get tuning statistics
stats = tuner.get_tuning_stats()
```

## API Endpoints

The caching infrastructure provides comprehensive REST API endpoints for management and monitoring.

### Cache Management Endpoints

#### Health and Status
```
GET /api/infrastructure/cache/health
GET /api/infrastructure/cache/stats
GET /api/infrastructure/cache/config
PUT /api/infrastructure/cache/config
```

#### Cache Operations
```
GET /api/infrastructure/cache/keys/{key}
PUT /api/infrastructure/cache/keys/{key}
DELETE /api/infrastructure/cache/keys/{key}
POST /api/infrastructure/cache/clear
```

### Redis Cluster Endpoints

#### Cluster Management
```
GET /api/infrastructure/cache/cluster/info
GET /api/infrastructure/cache/cluster/nodes
POST /api/infrastructure/cache/cluster/nodes
DELETE /api/infrastructure/cache/cluster/nodes/{host}/{port}
POST /api/infrastructure/cache/cluster/failover/{host}/{port}
POST /api/infrastructure/cache/cluster/reshard
```

### Monitoring Endpoints

#### Metrics and Alerts
```
GET /api/infrastructure/cache/monitoring/metrics
GET /api/infrastructure/cache/monitoring/alerts
POST /api/infrastructure/cache/monitoring/alerts
POST /api/infrastructure/cache/monitoring/alerts/{alert_id}/enable
POST /api/infrastructure/cache/monitoring/alerts/{alert_id}/disable
DELETE /api/infrastructure/cache/monitoring/alerts/{alert_id}
```

### Backup Endpoints

#### Backup Operations
```
GET /api/infrastructure/cache/backup/jobs
POST /api/infrastructure/cache/backup/create
POST /api/infrastructure/cache/backup/{backup_id}/restore
POST /api/infrastructure/cache/backup/{backup_id}/cancel
POST /api/infrastructure/cache/backup/cleanup
```

### Tuning Endpoints

#### Performance Tuning
```
GET /api/infrastructure/cache/tuning/recommendations
POST /api/infrastructure/cache/tuning/manual
GET /api/infrastructure/cache/tuning/history
GET /api/infrastructure/cache/tuning/stats
```

## Configuration

### Environment Variables

```bash
# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0

# Cluster Configuration
REDIS_CLUSTER_NODES=localhost:7000,localhost:7001,localhost:7002
REDIS_CLUSTER_NAME=mycluster

# Cache Configuration
CACHE_DEFAULT_TTL=3600
CACHE_MAX_MEMORY=2gb
CACHE_EVICTION_POLICY=allkeys-lru

# Backup Configuration
CACHE_BACKUP_DIR=/var/cache/backups
CACHE_BACKUP_INTERVAL=3600
CACHE_BACKUP_RETENTION_DAYS=7

# Monitoring Configuration
CACHE_MONITORING_ENABLED=true
CACHE_ALERTING_ENABLED=true
CACHE_HEALTH_CHECK_INTERVAL=30
```

### Application Configuration

```python
# config/caching.py
CACHING_CONFIG = {
    'redis': {
        'host': os.getenv('REDIS_HOST', 'localhost'),
        'port': int(os.getenv('REDIS_PORT', 6379)),
        'password': os.getenv('REDIS_PASSWORD'),
        'db': int(os.getenv('REDIS_DB', 0)),
        'cluster_nodes': [
            {'host': host, 'port': int(port)}
            for host_port in os.getenv('REDIS_CLUSTER_NODES', '').split(',')
            if host_port
        ]
    },
    'backup': {
        'dir': os.getenv('CACHE_BACKUP_DIR', '/var/cache/backups'),
        'interval': int(os.getenv('CACHE_BACKUP_INTERVAL', 3600)),
        'retention_days': int(os.getenv('CACHE_BACKUP_RETENTION_DAYS', 7)),
        'compression_enabled': True,
        'encryption_enabled': False
    },
    'monitoring': {
        'enabled': os.getenv('CACHE_MONITORING_ENABLED', 'true').lower() == 'true',
        'alerting_enabled': os.getenv('CACHE_ALERTING_ENABLED', 'true').lower() == 'true',
        'health_check_interval': int(os.getenv('CACHE_HEALTH_CHECK_INTERVAL', 30))
    }
}
```

## Performance Optimization

### Memory Optimization

#### Redis Configuration
```bash
# redis.conf
maxmemory 2gb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
```

#### Application Optimization
```python
# Use appropriate TTLs
short_ttl = 300      # 5 minutes for frequently changing data
medium_ttl = 3600    # 1 hour for user sessions
long_ttl = 86400     # 24 hours for static data

# Use compression for large values
if len(pickle.dumps(value)) > 1024:
    value = gzip.compress(pickle.dumps(value))

# Use appropriate data structures
# Use hashes for related data
cache.hmset("user:123:profile", {"name": "John", "age": 30})

# Use sets for collections
cache.sadd("user:123:permissions", "read", "write", "admin")
```

### Connection Optimization

```python
# Connection pooling
import redis
from redis.connection import ConnectionPool

pool = ConnectionPool(
    host='localhost',
    port=6379,
    max_connections=50,
    retry_on_timeout=True
)

redis_client = redis.Redis(connection_pool=pool)
```

## Security Considerations

### Authentication and Authorization

```python
# Redis authentication
redis_client = redis.Redis(
    host='localhost',
    port=6379,
    password='your_password',
    ssl=True,
    ssl_cert_reqs='required'
)

# Access control
def check_cache_permission(user_id, key):
    # Implement permission checking logic
    return user_id in get_authorized_users(key)
```

### Data Encryption

```python
import hashlib
import hmac
from cryptography.fernet import Fernet

# Encryption key
encryption_key = Fernet.generate_key()

# Encrypt sensitive data
def encrypt_data(data):
    cipher = Fernet(encryption_key)
    return cipher.encrypt(data.encode())

# Decrypt sensitive data
def decrypt_data(encrypted_data):
    cipher = Fernet(encryption_key)
    return cipher.decrypt(encrypted_data).decode()
```

## Monitoring and Alerting

### Key Metrics

#### Performance Metrics
- **Hit Rate**: Percentage of cache hits vs total requests
- **Response Time**: Average cache operation response time
- **Throughput**: Operations per second
- **Memory Usage**: Current memory consumption
- **Key Count**: Total number of keys stored

#### Health Metrics
- **Redis Status**: Connection and cluster health
- **Error Rate**: Percentage of failed operations
- **Connection Count**: Active connections
- **Eviction Rate**: Keys evicted per second

### Alert Configuration

```python
# Hit rate alert
monitor.create_alert(
    "low_hit_rate",
    "Cache hit rate below threshold",
    AlertLevel.WARNING,
    "hit_rate",
    0.7,  # 70%
    300   # 5 minutes
)

# Memory usage alert
monitor.create_alert(
    "high_memory",
    "Memory usage above threshold",
    AlertLevel.ERROR,
    "memory_usage_percent",
    0.8,  # 80%
    300   # 5 minutes
)
```

## Troubleshooting

### Common Issues

#### Redis Connection Issues
```python
# Check Redis connection
try:
    redis_client.ping()
    print("Redis connection successful")
except redis.ConnectionError:
    print("Redis connection failed")
    # Check if Redis is running
    # Check network connectivity
    # Verify configuration
```

#### Memory Issues
```python
# Check memory usage
info = redis_client.info()
memory_usage = info['used_memory']
max_memory = info['maxmemory']

if memory_usage > max_memory * 0.8:
    print("High memory usage detected")
    # Consider increasing maxmemory
    # Review eviction policy
    # Clean up unused keys
```

#### Performance Issues
```python
# Monitor slow operations
slow_log = redis_client.slowlog_get(10)
for entry in slow_log:
    print(f"Slow operation: {entry['command']}")
    print(f"Execution time: {entry['duration']} microseconds")
```

### Debug Tools

#### Redis CLI Commands
```bash
# Check Redis status
redis-cli ping

# Monitor Redis
redis-cli monitor

# Check memory usage
redis-cli info memory

# Check slow operations
redis-cli slowlog get 10
```

#### Application Debugging
```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Cache operation logging
logger.debug(f"Cache SET: key={key}, ttl={ttl}")
logger.debug(f"Cache GET: key={key}, hit={hit}")
logger.debug(f"Cache DELETE: key={key}")
```

## Best Practices

### Cache Key Design
```python
# Use consistent naming conventions
user_profile = f"user:{user_id}:profile"
user_session = f"session:{session_id}"
cache_stats = "stats:daily:2023-12-01"

# Use hierarchical keys
user_data = {
    f"user:{user_id}:profile": profile_data,
    f"user:{user_id}:preferences": preferences,
    f"user:{user_id}:permissions": permissions
}
```

### TTL Management
```python
# Use appropriate TTLs based on data characteristics
CACHE_TTLS = {
    'user_session': 3600,      # 1 hour
    'user_profile': 86400,     # 24 hours
    'api_response': 300,        # 5 minutes
    'static_config': 604800,   # 7 days
    'temp_data': 60            # 1 minute
}
```

### Error Handling
```python
# Implement robust error handling
def safe_cache_get(key, default=None):
    try:
        return cache.get(key) or default
    except redis.ConnectionError:
        logger.error("Redis connection error")
        return default
    except Exception as e:
        logger.error(f"Cache get error: {e}")
        return default
```

## Integration Examples

### Flask Integration
```python
from flask import Flask
from app.infrastructure.caching import CacheManager, CacheConfig

app = Flask(__name__)

# Initialize cache
cache_config = CacheConfig(
    enable_monitoring=True,
    enable_auto_tuning=True
)
cache_manager = CacheManager(cache_config)

@app.route('/user/<int:user_id>')
def get_user(user_id):
    # Try to get from cache
    cache_key = f"user:{user_id}"
    user_data = cache_manager.get(cache_key)
    
    if not user_data:
        # Get from database
        user_data = get_user_from_db(user_id)
        # Store in cache
        cache_manager.set(cache_key, user_data, ttl=3600)
    
    return jsonify(user_data)
```

### Django Integration
```python
from django.core.cache import cache
from app.infrastructure.caching import CacheManager

# Custom cache backend
class RedisCacheBackend:
    def __init__(self):
        self.cache_manager = CacheManager()
    
    def get(self, key, default=None):
        return self.cache_manager.get(key) or default
    
    def set(self, key, value, timeout=None):
        return self.cache_manager.set(key, value, timeout)
    
    def delete(self, key):
        return self.cache_manager.delete(key)

# Use in Django views
from django.views.decorators.cache import cache_page

@cache_page(60 * 15)  # 15 minutes
def expensive_view(request):
    # View logic here
    pass
```

## Testing

### Unit Testing
```python
import unittest
from unittest.mock import Mock, patch
from app.infrastructure.caching import CacheManager

class TestCacheManager(unittest.TestCase):
    def setUp(self):
        self.config = CacheConfig(enable_monitoring=False)
        self.cache_manager = CacheManager(self.config)
    
    def test_set_get(self):
        # Mock Redis client
        with patch.object(self.cache_manager, 'redis_client'):
            self.cache_manager.redis_client = Mock()
            self.cache_manager.redis_client.setex.return_value = True
            self.cache_manager.redis_client.get.return_value = '{"test": "data"}'
            
            # Test set
            result = self.cache_manager.set("test_key", {"test": "data"})
            self.assertTrue(result)
            
            # Test get
            result = self.cache_manager.get("test_key")
            self.assertEqual(result, {"test": "data"})
    
    def test_delete(self):
        with patch.object(self.cache_manager, 'redis_client'):
            self.cache_manager.redis_client = Mock()
            self.cache_manager.redis_client.delete.return_value = True
            
            result = self.cache_manager.delete("test_key")
            self.assertTrue(result)
```

### Integration Testing
```python
import pytest
from app.infrastructure.caching import CacheManager, CacheConfig

@pytest.fixture
def cache_manager():
    config = CacheConfig(enable_monitoring=False)
    return CacheManager(config)

def test_cache_operations(cache_manager):
    # Test cache operations
    assert cache_manager.set("test_key", "test_value")
    assert cache_manager.get("test_key") == "test_value"
    assert cache_manager.delete("test_key")
    assert cache_manager.get("test_key") is None

def test_cache_stats(cache_manager):
    # Test statistics
    stats = cache_manager.get_stats()
    assert 'hits' in stats
    assert 'misses' in stats
    assert 'sets' in stats
```

## Deployment

### Docker Configuration
```dockerfile
FROM python:3.11-slim

# Install Redis client
RUN pip install redis rediscluster

# Copy application code
COPY . /app
WORKDIR /app

# Expose Redis port
EXPOSE 6379

# Start application
CMD ["python", "app.py"]
```

### Kubernetes Configuration
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cache-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: cache-service
  template:
    metadata:
      labels:
        app: cache-service
    spec:
      containers:
      - name: cache-service
        image: myapp/cache-service:latest
        ports:
        - containerPort: 6379
        env:
        - name: REDIS_HOST
          value: "redis-cluster"
        - name: REDIS_PORT
          value: "6379"
---
apiVersion: v1
kind: Service
metadata:
  name: cache-service
spec:
  selector:
    app: cache-service
  ports:
  - port: 6379
    targetPort: 6379
```

### Production Checklist
- [ ] Redis cluster configured and tested
- [ ] Monitoring and alerting configured
- [ ] Backup strategies implemented
- [ ] Performance tuning optimized
- [ ] Security measures in place
- [ ] Health checks configured
- [ ] Load balancing tested
- [ ] Failover procedures documented
- [ ] Capacity planning completed
- [ ] Disaster recovery plan in place

## Support

For support and questions about the Caching Infrastructure system:

1. Check the [Troubleshooting Guide](./TROUBLESHOOTING.md)
2. Review the [Common Issues](./COMMON_ISSUES.md)
3. Consult the [API Documentation](./API_DOCUMENTATION.md)
4. Contact the infrastructure team

## Changelog

### Version 1.0.0 (May 12, 2026)
- Initial implementation of Caching Infrastructure
- Redis cluster support with fallback
- Comprehensive monitoring and alerting
- Automated backup strategies
- Performance tuning and optimization
- Production-ready error handling
- Full API documentation and testing
