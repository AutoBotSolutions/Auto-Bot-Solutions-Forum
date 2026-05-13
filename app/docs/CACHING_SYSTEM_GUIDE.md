# Advanced Caching System Guide

## Overview

The Advanced Caching System provides Redis-based caching with comprehensive analytics, distributed caching support, and intelligent cache management. This guide covers implementation details, usage patterns, and best practices.

## Quick Start

### Basic Caching

```python
from app.cache.service import cache_service

# Set cache
cache_service.set("user_profile_123", user_data, ttl=3600)

# Get cache
cached_data = cache_service.get("user_profile_123")

# Delete cache
cache_service.delete("user_profile_123")
```

### Advanced Caching with Analytics

```python
from app.cache.models import CacheEntry, CacheAnalytics

# Set cache with analytics
cache_entry = CacheEntry.set_cache(
    key="user_profile_123",
    value=user_data,
    ttl=3600,
    tag="user_profile",
    cache_type="user"
)

# Track cache performance
CacheAnalytics.track_metric(
    metric_type="hit",
    cache_type="user",
    value=1.0
)
```

## Core Components

### CacheEntry Model

The `CacheEntry` model provides Redis-based cache storage with compression and analytics.

#### Key Features
- **Data Compression**: Automatic compression for large objects
- **TTL Management**: Flexible expiration policies
- **Access Tracking**: Monitor cache usage patterns
- **Tag-based Organization**: Logical cache grouping

#### Usage Examples

```python
from app.cache.models import CacheEntry

# Basic cache set
cache_entry = CacheEntry.set_cache(
    key="product_456",
    value=product_data,
    ttl=7200,  # 2 hours
    tag="product"
)

# Get with automatic decompression
cached_product = CacheEntry.get_cache("product_456")

# Check if cache exists
exists = CacheEntry.cache_exists("product_456")

# Get cache statistics
stats = CacheEntry.get_cache_stats("product_456")
```

### CacheService

The `CacheService` provides high-level caching operations with Redis backend.

#### Methods

```python
from app.cache.service import cache_service

# Basic operations
cache_service.set(key, value, ttl=None, tag=None)
cache_service.get(key)
cache_service.delete(key)
cache_service.clear()

# Advanced operations
cache_service.set_many(key_value_dict, ttl=None)
cache_service.get_many(key_list)
cache_service.increment(key, amount=1)
cache_service.expire(key, ttl)

# Statistics and monitoring
cache_service.get_stats()
cache_service.get_info()
```

#### Usage Examples

```python
# User session caching
session_data = {
    'user_id': 123,
    'username': 'john_doe',
    'last_activity': datetime.utcnow()
}

cache_service.set(
    f"session_{session_id}",
    session_data,
    ttl=1800,  # 30 minutes
    tag="session"
)

# Product catalog caching
products = Product.query.filter_by(category='electronics').all()
cache_service.set(
    "electronics_products",
    [p.to_dict() for p in products],
    ttl=3600,
    tag="product_catalog"
)

# Retrieve and use
cached_products = cache_service.get("electronics_products")
if cached_products:
    return cached_products
else:
    # Fetch from database
    products = Product.query.filter_by(category='electronics').all()
    cache_service.set("electronics_products", products, ttl=3600)
    return products
```

### DistributedCacheService

The `DistributedCacheService` provides multi-instance distributed caching capabilities.

#### Features
- **Global Invalidation**: Cache invalidation across all instances
- **Cluster Management**: Redis cluster support
- **Synchronization**: Cache synchronization between instances

#### Usage Examples

```python
from app.cache.service import distributed_cache

# Global cache operations
distributed_cache.set_global("global_config", config_data)
distributed_cache.invalidate_global("user_*")  # Invalidate all user caches

# Cluster operations
distributed_cache.get_cluster_info()
distributed_cache.get_node_status()

# Distributed cache warming
distributed_cache.warm_cache_cluster([
    "popular_products",
    "user_sessions",
    "system_config"
])
```

## Cache Analytics

### CacheAnalytics Model

Track cache performance metrics and usage patterns.

```python
from app.cache.models import CacheAnalytics

# Track cache hit
CacheAnalytics.track_metric(
    metric_type="hit",
    cache_type="user",
    cache_key="user_profile_123",
    value=1.0,
    metadata={"response_time": 0.05}
)

# Track cache miss
CacheAnalytics.track_metric(
    metric_type="miss",
    cache_type="product",
    cache_key="product_456",
    value=1.0
)

# Get performance metrics
metrics = CacheAnalytics.get_performance_metrics(hours=24)
```

### Performance Monitoring

```python
# Cache hit rate analysis
hit_rate = CacheAnalytics.get_hit_rate(cache_type="user", hours=24)

# Response time analysis
avg_response_time = CacheAnalytics.get_avg_response_time(hours=1)

# Cache size analysis
cache_size = CacheAnalytics.get_cache_size_by_type()

# Popular cache keys
popular_keys = CacheAnalytics.get_popular_keys(limit=10)
```

## Cache Dependencies

### CacheDependency Model

Manage cache dependencies for intelligent invalidation.

```python
from app.cache.models import CacheDependency

# Create dependency
CacheDependency.add_dependency(
    parent_key="user_123_data",
    child_key="user_123_profile",
    dependency_type="automatic"
)

# Invalidate dependents
CacheDependency.invalidate_dependents("user_123_data")

# Get dependency graph
dependencies = CacheDependency.get_dependency_graph("user_123_data")
```

### Common Dependency Patterns

```python
# User data dependencies
CacheDependency.add_dependency("user_123", "user_123_profile")
CacheDependency.add_dependency("user_123", "user_123_posts")
CacheDependency.add_dependency("user_123", "user_123_settings")

# Product dependencies
CacheDependency.add_dependency("product_456", "product_456_reviews")
CacheDependency.add_dependency("product_456", "product_456_inventory")
CacheDependency.add_dependency("product_456", "product_456_recommendations")
```

## Cache Utilities

### CacheWarmer

Pre-warm cache with frequently accessed data.

```python
from app.cache.utils import CacheWarmer

warmer = CacheWarmer()

# Add warmup jobs
warmer.add_warmup_job(
    key="popular_products",
    warmup_func=get_popular_products,
    priority="high",
    schedule="0 */6 * * *"  # Every 6 hours
)

# Execute warmup
warmer.warm_cache("popular_products")

# Warm all jobs
warmer.warm_all()
```

### CacheOptimizer

Analyze and optimize cache usage patterns.

```python
from app.cache.utils import CacheOptimizer

optimizer = CacheOptimizer()

# Analyze cache usage
analysis = optimizer.analyze_cache_usage(days=7)

# Get optimization recommendations
recommendations = optimizer.get_recommendations()

# Apply optimizations
optimizer.apply_optimizations(recommendations)
```

### CacheKeyGenerator

Generate consistent and versioned cache keys.

```python
from app.cache.utils import CacheKeyGenerator

key_gen = CacheKeyGenerator()

# Generate user cache key
user_key = key_gen.generate_key("user", user_id=123, version="v1")

# Generate product cache key
product_key = key_gen.generate_key("product", product_id=456, category="electronics")

# Validate cache key
is_valid = key_gen.validate_key(user_key)
```

## Configuration

### Cache Configuration

```python
# app/cache/config.py
CACHE_CONFIG = {
    'redis_url': 'redis://localhost:6379/0',
    'default_ttl': 3600,
    'compression_threshold': 1024,
    'max_memory': '256mb',
    'eviction_policy': 'allkeys-lru',
    'distributed_enabled': True,
    'analytics_enabled': True,
    'dependency_tracking': True
}
```

### Environment-Specific Configuration

```python
# Development
CACHE_CONFIG = {
    'redis_url': 'redis://localhost:6379/0',
    'default_ttl': 300,
    'compression_threshold': 512,
    'analytics_enabled': False
}

# Production
CACHE_CONFIG = {
    'redis_url': 'redis://cache-cluster:6379/0',
    'default_ttl': 3600,
    'compression_threshold': 1024,
    'distributed_enabled': True,
    'analytics_enabled': True,
    'cluster_nodes': ['redis-node1:6379', 'redis-node2:6379']
}
```

## Best Practices

### Cache Key Design

```python
# Good cache key patterns
"user_profile_{user_id}"
"product_catalog_{category}_{page}"
"search_results_{query_hash}_{page}"
"system_config_{environment}"

# Bad cache key patterns (too generic)
"user_data"
"products"
"config"
```

### TTL Strategies

```python
# Short TTL (5-15 minutes)
- User sessions
- Temporary data
- Search results

# Medium TTL (1-6 hours)
- User profiles
- Product catalogs
- System settings

# Long TTL (24 hours+)
- Static configuration
- Master data
- Popular content
```

### Cache Invalidation

```python
# Manual invalidation
cache_service.delete("user_profile_123")

# Tag-based invalidation
cache_service.delete_by_tag("user_profile")

# Pattern-based invalidation
cache_service.delete_by_pattern("user_*")

# Dependency-based invalidation
CacheDependency.invalidate_dependents("user_123")
```

### Error Handling

```python
from app.cache.service import cache_service
import logging

logger = logging.getLogger(__name__)

def get_user_profile(user_id):
    cache_key = f"user_profile_{user_id}"
    
    try:
        # Try cache first
        cached_data = cache_service.get(cache_key)
        if cached_data:
            return cached_data
    except Exception as e:
        logger.warning(f"Cache error: {e}")
    
    # Fallback to database
    try:
        user = User.query.get(user_id)
        if user:
            profile_data = user.to_dict()
            # Cache the result
            try:
                cache_service.set(cache_key, profile_data, ttl=3600)
            except Exception as e:
                logger.warning(f"Cache set error: {e}")
            return profile_data
    except Exception as e:
        logger.error(f"Database error: {e}")
        raise
```

## Monitoring and Debugging

### Cache Monitoring

```python
from app.cache.models import CacheAnalytics
from app.cache.service import cache_service

# Get cache statistics
stats = cache_service.get_stats()
print(f"Cache hit rate: {stats['hit_rate']:.2%}")
print(f"Memory usage: {stats['memory_usage']}")
print(f"Total keys: {stats['total_keys']}")

# Get performance metrics
metrics = CacheAnalytics.get_performance_metrics(hours=24)
print(f"Average response time: {metrics['avg_response_time']:.3f}s")
print(f"Cache operations: {metrics['total_operations']}")
```

### Debugging Tools

```python
# Cache key inspection
cache_info = cache_service.get_info("user_profile_123")
print(f"Key exists: {cache_info['exists']}")
print(f"TTL: {cache_info['ttl']}")
print(f"Size: {cache_info['size']} bytes")

# Dependency inspection
dependencies = CacheDependency.get_dependency_graph("user_123")
print(f"Parent dependencies: {len(dependencies['parents'])}")
print(f"Child dependencies: {len(dependencies['children'])}")
```

## Integration Examples

### Flask Application Integration

```python
from flask import Flask
from app.cache.service import cache_service

app = Flask(__name__)

@app.route('/user/<int:user_id>')
def get_user(user_id):
    cache_key = f"user_profile_{user_id}"
    
    # Try cache first
    cached_user = cache_service.get(cache_key)
    if cached_user:
        return cached_user
    
    # Fetch from database
    user = User.query.get_or_404(user_id)
    user_data = user.to_dict()
    
    # Cache the result
    cache_service.set(cache_key, user_data, ttl=3600)
    
    return user_data

@app.route('/user/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    user.update_from_json(request.json)
    db.session.commit()
    
    # Invalidate cache
    cache_service.delete(f"user_profile_{user_id}")
    
    return user.to_dict()
```

### Background Task Integration

```python
from celery import Celery
from app.cache.service import cache_service

celery = Celery('cache_tasks')

@celery.task
def warm_user_cache(user_ids):
    """Warm cache for multiple users"""
    for user_id in user_ids:
        try:
            user = User.query.get(user_id)
            if user:
                cache_key = f"user_profile_{user_id}"
                cache_service.set(cache_key, user.to_dict(), ttl=3600)
        except Exception as e:
            print(f"Error warming cache for user {user_id}: {e}")

@celery.task
def invalidate_user_cache(user_id):
    """Invalidate all user-related cache"""
    patterns = [
        f"user_profile_{user_id}",
        f"user_posts_{user_id}",
        f"user_settings_{user_id}"
    ]
    
    for pattern in patterns:
        cache_service.delete(pattern)
```

## Performance Tips

### Memory Optimization

```python
# Use compression for large objects
cache_service.set("large_data", data, ttl=3600, compress=True)

# Set appropriate TTL to prevent memory bloat
cache_service.set("temp_data", data, ttl=300)  # 5 minutes

# Monitor memory usage
stats = cache_service.get_stats()
if stats['memory_usage'] > 0.8:  # 80% of max memory
    cache_service.clear_expired()
```

### Query Optimization

```python
# Batch cache operations
keys = ["user_1", "user_2", "user_3"]
values = cache_service.get_many(keys)

# Use pattern-based operations
cache_service.delete_by_pattern("temp_*")

# Leverage cache dependencies
CacheDependency.add_dependency("user_123", "user_123_posts")
# When user_123 changes, posts cache is automatically invalidated
```

---

*Guide Last Updated: May 13, 2026*  
*Implementation Status: Production Ready*
