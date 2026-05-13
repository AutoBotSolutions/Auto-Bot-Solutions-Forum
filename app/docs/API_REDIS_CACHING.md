# Redis Caching Implementation

## Overview

The Redis caching system provides high-performance response caching with intelligent invalidation, warming strategies, and comprehensive analytics for optimal API performance.

## 🏗️ Architecture

### Components

- **RedisCacheService**: Core caching service with Redis operations
- **CacheManager**: Intelligent cache management and optimization
- **CacheUtils**: Utility functions for key building and serialization
- **Cache Invalidation**: Pattern-based and dependency tracking
- **Cache Warming**: Predefined strategies for cache preloading
- **Cache Analytics**: Performance monitoring and optimization

### Cache Flow

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   API        │───▶│   Cache     │───▶│   Redis     │───▶│   Response  │
│   Request   │    │   Check     │    │   Storage   │    │   Return    │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
       │                   │                   │                   │
       │                   │                   │                   │
       ▼                   ▼                   ▼                   ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Cache     │    │   Cache     │    │   Cache     │    │   Cache     │
│   Miss      │    │   Store     │    │   Update    │    │   Analytics  │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

## 🔧 Implementation Details

### RedisCacheService Class

```python
class RedisCacheService:
    """Redis-based caching service"""
    
    def __init__(self, redis_url: str = None, db: int = 0, **kwargs):
        """Initialize Redis cache service"""
        self.redis_client = redis.Redis(
            host=kwargs.get('host', 'localhost'),
            port=kwargs.get('port', 6379),
            db=db,
            decode_responses=True,
            socket_connect_timeout=kwargs.get('timeout', 5),
            socket_timeout=kwargs.get('timeout', 5)
        )
    
    def get(self, key: str, default=None):
        """Get value from cache"""
    
    def set(self, key: str, value, ttl: int = None):
        """Set value in cache with optional TTL"""
    
    def delete(self, key: str):
        """Delete key from cache"""
    
    def exists(self, key: str):
        """Check if key exists in cache"""
    
    def clear(self, pattern: str = None):
        """Clear cache keys matching pattern"""
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
```

### CacheManager Class

```python
class CacheManager:
    """Intelligent cache management"""
    
    def __init__(self, cache_service: RedisCacheService):
        """Initialize cache manager"""
        self.cache_service = cache_service
        self.invalidation_rules = {}
        self.dependency_graph = {}
    
    def register_invalidation_rule(self, pattern: str, dependencies: List[str]):
        """Register cache invalidation rule"""
    
    def invalidate_cache(self, key: str, cascade: bool = True):
        """Invalidate cache key and dependencies"""
    
    def warm_cache(self, strategy: str, **kwargs):
        """Warm cache using predefined strategy"""
    
    def optimize_cache(self):
        """Optimize cache performance"""
```

### CacheUtils Functions

```python
def cache_key_builder(prefix: str, *args, **kwargs) -> str:
    """Build cache key from components"""

def cache_ttl(ttl_type: str, custom_ttl: int = None) -> int:
    """Get TTL for cache type"""

def serialize_data(data: Any, use_json: bool = True) -> Any:
    """Serialize data for caching"""

def deserialize_data(data: Any, use_json: bool = True) -> Any:
    """Deserialize cached data"""
```

## 🚀 Usage Examples

### Basic Caching

```python
from app.cache.redis_cache import RedisCacheService
from app.cache.cache_utils import cache_key_builder, cache_ttl

# Initialize cache service
cache_service = RedisCacheService()

# Set cache value
cache_service.set(
    key=cache_key_builder("user", 123),
    value={"id": 123, "name": "John Doe"},
    ttl=cache_ttl("medium")
)

# Get cache value
user_data = cache_service.get(cache_key_builder("user", 123))
if user_data:
    print(f"User: {user_data['name']}")
else:
    print("User not found in cache")
```

### Advanced Caching with Manager

```python
from app.cache.cache_manager import CacheManager

# Initialize cache manager
cache_manager = CacheManager(cache_service)

# Register invalidation rule
cache_manager.register_invalidation_rule(
    pattern="user:*",
    dependencies=["posts:*", "comments:*"]
)

# Cache user data
cache_manager.cache_service.set(
    key="user:123",
    value=user_data,
    ttl=3600
)

# Invalidate user cache (will also invalidate posts and comments)
cache_manager.invalidate_cache("user:123")
```

### Cache Decorator

```python
from functools import wraps
from app.cache.redis_cache import RedisCacheService

cache_service = RedisCacheService()

def cache_result(ttl: int = 3600, key_prefix: str = ""):
    """Decorator to cache function results"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Build cache key
            cache_key = f"{key_prefix}:{f.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Try to get from cache
            cached_result = cache_service.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function
            result = f(*args, **kwargs)
            
            # Cache result
            cache_service.set(cache_key, result, ttl)
            
            return result
        return decorated_function
    return decorator

# Usage
@cache_result(ttl=1800, key_prefix="posts")
def get_post(post_id: int):
    # Expensive database query
    return Post.query.get(post_id)
```

### Cache Warming

```python
# Warm cache for popular content
cache_manager.warm_cache(
    strategy="popular_posts",
    limit=100,
    ttl=3600
)

# Warm user cache
cache_manager.warm_cache(
    strategy="active_users",
    days=7,
    ttl=7200
)
```

## 🔗 Cache Configuration

### Redis Configuration

```python
# Redis connection settings
REDIS_CONFIG = {
    'host': 'localhost',
    'port': 6379,
    'db': 0,
    'password': None,
    'socket_timeout': 5,
    'socket_connect_timeout': 5,
    'retry_on_timeout': True,
    'health_check_interval': 30
}

# Cache settings
CACHE_CONFIG = {
    'default_ttl': 3600,  # 1 hour
    'max_connections': 50,
    'connection_pool_kwargs': {
        'max_connections': 50,
        'retry_on_timeout': True
    }
}
```

### Environment Variables

```bash
# Redis Configuration
REDIS_CACHE_URL=redis://localhost:6379/0
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=your-redis-password

# Cache Configuration
CACHE_DEFAULT_TTL=3600
CACHE_MAX_CONNECTIONS=50
CACHE_ENABLED=true
CACHE_DEBUG=false
```

### Flask Configuration

```python
# Flask cache configuration
app.config['CACHE_TYPE'] = 'redis'
app.config['CACHE_REDIS_URL'] = os.environ.get('REDIS_CACHE_URL')
app.config['CACHE_DEFAULT_TIMEOUT'] = 3600
app.config['CACHE_KEY_PREFIX'] = 'forum_cache'
```

## 📊 Cache Analytics

### Performance Metrics

```python
class CacheAnalytics:
    """Cache performance analytics"""
    
    def __init__(self, cache_service: RedisCacheService):
        self.cache_service = cache_service
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        
        # Get Redis info
        redis_info = self.cache_service.redis_client.info()
        
        # Calculate metrics
        hit_rate = self._calculate_hit_rate(redis_info)
        memory_usage = redis_info.get('used_memory', 0)
        total_keys = redis_info.get('db0', {}).get('keys', 0)
        
        return {
            'hit_rate': hit_rate,
            'memory_usage': memory_usage,
            'total_keys': total_keys,
            'connected_clients': redis_info.get('connected_clients', 0),
            'total_commands': redis_info.get('total_commands_processed', 0),
            'avg_response_time': self._get_avg_response_time()
        }
    
    def get_key_stats(self, pattern: str = "*") -> Dict[str, Any]:
        """Get statistics for keys matching pattern"""
        
        keys = self.cache_service.redis_client.keys(pattern)
        
        stats = {
            'total_keys': len(keys),
            'key_sizes': {},
            'key_ttls': {},
            'key_types': {}
        }
        
        for key in keys[:100]:  # Limit to first 100 keys
            key_type = self.cache_service.redis_client.type(key)
            key_size = self.cache_service.redis_client.memory_usage(key)
            key_ttl = self.cache_service.redis_client.ttl(key)
            
            stats['key_sizes'][key] = key_size
            stats['key_ttls'][key] = key_ttl
            stats['key_types'][key_type] = stats['key_types'].get(key_type, 0) + 1
        
        return stats
```

### Cache Monitoring

```python
class CacheMonitor:
    """Real-time cache monitoring"""
    
    def __init__(self, cache_service: RedisCacheService):
        self.cache_service = cache_service
        self.alerts = []
    
    def check_cache_health(self) -> Dict[str, Any]:
        """Check cache health status"""
        
        redis_info = self.cache_service.redis_client.info()
        
        health_status = {
            'status': 'healthy',
            'issues': [],
            'warnings': []
        }
        
        # Check memory usage
        memory_usage = redis_info.get('used_memory', 0)
        max_memory = redis_info.get('maxmemory', 0)
        
        if max_memory > 0:
            memory_usage_percent = (memory_usage / max_memory) * 100
            if memory_usage_percent > 90:
                health_status['status'] = 'critical'
                health_status['issues'].append(f"High memory usage: {memory_usage_percent:.1f}%")
            elif memory_usage_percent > 75:
                health_status['warnings'].append(f"Memory usage: {memory_usage_percent:.1f}%")
        
        # Check connection
        try:
            self.cache_service.redis_client.ping()
        except redis.ConnectionError:
            health_status['status'] = 'critical'
            health_status['issues'].append("Redis connection failed")
        
        return health_status
    
    def get_slow_queries(self, threshold_ms: int = 100) -> List[Dict[str, Any]]:
        """Get slow cache operations"""
        
        # This would require Redis slowlog configuration
        slow_queries = []
        
        try:
            slowlog = self.cache_service.redis_client.slowlog_get(10)
            for entry in slowlog:
                if entry['duration'] > threshold_ms * 1000:  # Convert to microseconds
                    slow_queries.append({
                        'command': entry['command'],
                        'duration': entry['duration'],
                        'timestamp': entry['timestamp']
                    })
        except redis.ResponseError:
            pass
        
        return slow_queries
```

## 🔧 Cache Strategies

### Cache Warming Strategies

```python
class CacheWarmingStrategies:
    """Predefined cache warming strategies"""
    
    @staticmethod
    def popular_posts(cache_manager: CacheManager, limit: int = 100):
        """Warm cache with popular posts"""
        
        # Get most viewed posts
        popular_posts = Post.query.order_by(Post.view_count.desc()).limit(limit).all()
        
        for post in popular_posts:
            cache_key = f"post:{post.id}"
            post_data = {
                'id': post.id,
                'title': post.title,
                'content': post.content,
                'author': post.author.username,
                'view_count': post.view_count
            }
            
            cache_manager.cache_service.set(
                key=cache_key,
                value=post_data,
                ttl=3600
            )
    
    @staticmethod
    def active_users(cache_manager: CacheManager, days: int = 7):
        """Warm cache with active user data"""
        
        # Get recently active users
        active_users = User.query.filter(
            User.last_login >= datetime.utcnow() - timedelta(days=days)
        ).all()
        
        for user in active_users:
            cache_key = f"user:{user.id}"
            user_data = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'last_login': user.last_login.isoformat()
            }
            
            cache_manager.cache_service.set(
                key=cache_key,
                value=user_data,
                ttl=7200
            )
    
    @staticmethod
    def forum_categories(cache_manager: CacheManager):
        """Warm cache with forum categories"""
        
        categories = Category.query.all()
        
        for category in categories:
            cache_key = f"category:{category.id}"
            category_data = {
                'id': category.id,
                'name': category.name,
                'description': category.description,
                'post_count': category.posts.count()
            }
            
            cache_manager.cache_service.set(
                key=cache_key,
                value=category_data,
                ttl=86400  # 24 hours
            )
```

### Cache Invalidation Strategies

```python
class CacheInvalidationStrategies:
    """Cache invalidation strategies"""
    
    @staticmethod
    def user_based_invalidation(cache_manager: CacheManager, user_id: int):
        """Invalidate all user-related cache"""
        
        patterns = [
            f"user:{user_id}",
            f"user:{user_id}:*",
            f"posts:by_user:{user_id}",
            f"comments:by_user:{user_id}"
        ]
        
        for pattern in patterns:
            cache_manager.cache_service.clear(pattern)
    
    @staticmethod
    def post_based_invalidation(cache_manager: CacheManager, post_id: int):
        """Invalidate all post-related cache"""
        
        patterns = [
            f"post:{post_id}",
            f"post:{post_id}:*",
            f"posts:recent",
            f"posts:popular",
            f"comments:post:{post_id}"
        ]
        
        for pattern in patterns:
            cache_manager.cache_service.clear(pattern)
    
    @staticmethod
    def tag_based_invalidation(cache_manager: CacheManager, tag_name: str):
        """Invalidate cache related to specific tag"""
        
        # Find posts with this tag
        tagged_posts = Post.query.filter(Post.tags.contains([tag_name])).all()
        
        for post in tagged_posts:
            CacheInvalidationStrategies.post_based_invalidation(cache_manager, post.id)
```

## 🛡️ Security Considerations

### Cache Security

```python
class SecureCacheService(RedisCacheService):
    """Secure Redis cache service"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.encryption_key = kwargs.get('encryption_key')
    
    def set_secure(self, key: str, value, ttl: int = None, encrypt: bool = False):
        """Set value with optional encryption"""
        
        if encrypt and self.encryption_key:
            value = self._encrypt_data(value)
        
        # Add metadata
        cache_data = {
            'data': value,
            'encrypted': encrypt,
            'timestamp': time.time(),
            'checksum': self._calculate_checksum(value)
        }
        
        return self.set(key, cache_data, ttl)
    
    def get_secure(self, key: str):
        """Get value with security validation"""
        
        cache_data = self.get(key)
        if not cache_data:
            return None
        
        # Validate checksum
        if not self._validate_checksum(cache_data['data'], cache_data['checksum']):
            self.delete(key)  # Remove corrupted data
            return None
        
        # Decrypt if needed
        if cache_data.get('encrypted') and self.encryption_key:
            return self._decrypt_data(cache_data['data'])
        
        return cache_data['data']
    
    def _encrypt_data(self, data: Any) -> str:
        """Encrypt data for secure storage"""
        # Implement encryption logic
        pass
    
    def _decrypt_data(self, encrypted_data: str) -> Any:
        """Decrypt data from secure storage"""
        # Implement decryption logic
        pass
    
    def _calculate_checksum(self, data: Any) -> str:
        """Calculate data checksum"""
        import hashlib
        return hashlib.sha256(str(data).encode()).hexdigest()
    
    def _validate_checksum(self, data: Any, checksum: str) -> bool:
        """Validate data checksum"""
        return self._calculate_checksum(data) == checksum
```

### Access Control

```python
class CacheAccessControl:
    """Cache access control"""
    
    def __init__(self, cache_service: RedisCacheService):
        self.cache_service = cache_service
        self.access_rules = {}
    
    def set_access_rule(self, pattern: str, permissions: List[str]):
        """Set access rule for cache pattern"""
        self.access_rules[pattern] = permissions
    
    def check_access(self, key: str, user_permissions: List[str]) -> bool:
        """Check if user has access to cache key"""
        
        for pattern, required_permissions in self.access_rules.items():
            if self._match_pattern(key, pattern):
                # Check if user has required permissions
                if not any(perm in user_permissions for perm in required_permissions):
                    return False
        
        return True
    
    def _match_pattern(self, key: str, pattern: str) -> bool:
        """Match key against pattern"""
        # Implement pattern matching logic
        import fnmatch
        return fnmatch.fnmatch(key, pattern)
```

## 🧪 Testing

### Unit Tests

```python
import pytest
import redis
from app.cache.redis_cache import RedisCacheService
from app.cache.cache_utils import cache_key_builder, cache_ttl

class TestRedisCacheService:
    
    @pytest.fixture
    def cache_service(self):
        """Create test cache service"""
        return RedisCacheService(db=1)  # Use test database
    
    def test_set_and_get(self, cache_service):
        """Test basic set and get operations"""
        key = "test:key"
        value = {"message": "Hello, Redis!"}
        
        # Set value
        result = cache_service.set(key, value, ttl=60)
        assert result is True
        
        # Get value
        cached_value = cache_service.get(key)
        assert cached_value == value
    
    def test_cache_expiration(self, cache_service):
        """Test cache expiration"""
        key = "test:expire"
        value = {"message": "This will expire"}
        
        # Set with short TTL
        cache_service.set(key, value, ttl=1)
        
        # Should exist immediately
        assert cache_service.exists(key) is True
        
        # Wait for expiration
        import time
        time.sleep(2)
        
        # Should be expired
        assert cache_service.exists(key) is False
        assert cache_service.get(key) is None
    
    def test_cache_delete(self, cache_service):
        """Test cache deletion"""
        key = "test:delete"
        value = {"message": "This will be deleted"}
        
        # Set value
        cache_service.set(key, value)
        assert cache_service.exists(key) is True
        
        # Delete value
        result = cache_service.delete(key)
        assert result is True
        assert cache_service.exists(key) is False
    
    def test_cache_clear_pattern(self, cache_service):
        """Test pattern-based cache clearing"""
        # Set multiple keys
        keys = ["test:pattern:1", "test:pattern:2", "other:key"]
        for key in keys:
            cache_service.set(key, {"data": key})
        
        # Clear pattern
        deleted_count = cache_service.clear("test:pattern:*")
        assert deleted_count == 2
        
        # Check remaining key
        assert cache_service.exists("other:key") is True
```

### Integration Tests

```python
def test_cache_integration(client, cache_service):
    """Test cache integration with Flask application"""
    
    # Make request that should be cached
    response = client.get('/api/posts/1')
    assert response.status_code == 200
    
    # Check if response is cached
    cached_data = cache_service.get('post:1')
    assert cached_data is not None
    
    # Make second request (should hit cache)
    response2 = client.get('/api/posts/1')
    assert response2.status_code == 200
    
    # Verify cache was hit (faster response)
    # This would require response time measurement
```

## 🔍 Troubleshooting

### Common Issues

1. **Redis Connection Failed**
   - Check Redis server is running
   - Verify connection parameters
   - Check network connectivity

2. **Cache Misses**
   - Verify cache keys are correct
   - Check TTL settings
   - Monitor cache hit rate

3. **Memory Issues**
   - Monitor Redis memory usage
   - Implement cache eviction policies
   - Consider Redis cluster

4. **Performance Issues**
   - Check Redis slowlog
   - Monitor connection pool
   - Optimize cache key patterns

### Debug Tools

```python
def debug_cache_performance(cache_service: RedisCacheService):
    """Debug cache performance issues"""
    
    # Get Redis info
    info = cache_service.redis_client.info()
    
    print("=== Cache Performance Debug ===")
    print(f"Used Memory: {info.get('used_memory', 0)} bytes")
    print(f"Connected Clients: {info.get('connected_clients', 0)}")
    print(f"Total Commands: {info.get('total_commands_processed', 0)}")
    print(f"Keyspace Hits: {info.get('keyspace_hits', 0)}")
    print(f"Keyspace Misses: {info.get('keyspace_misses', 0)}")
    
    # Calculate hit rate
    hits = info.get('keyspace_hits', 0)
    misses = info.get('keyspace_misses', 0)
    total = hits + misses
    
    if total > 0:
        hit_rate = (hits / total) * 100
        print(f"Hit Rate: {hit_rate:.2f}%")
    
    # Get slow queries
    try:
        slowlog = cache_service.redis_client.slowlog_get(5)
        print("=== Slow Queries ===")
        for entry in slowlog:
            print(f"Command: {entry['command']}")
            print(f"Duration: {entry['duration']} μs")
            print(f"Timestamp: {entry['timestamp']}")
            print("---")
    except redis.ResponseError:
        print("Slowlog not available")
```

## 📚 References

- [Redis Documentation](https://redis.io/documentation)
- [Redis Best Practices](https://redis.io/topics/memory-optimization)
- [Caching Strategies](https://docs.microsoft.com/en-us/azure/architecture/best-practices/caching)

---

**Last Updated**: May 12, 2026  
**Version**: 1.0.0  
**Component**: Redis Caching Service
