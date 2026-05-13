"""
Advanced Caching Service

This module provides Redis-based caching functionality with distributed caching,
cache invalidation tracking, analytics, and dependency management.
"""

import redis
import json
import pickle
import zlib
from datetime import datetime, timedelta
from flask import current_app
from app import db
from app.cache.models import CacheEntry, CacheInvalidation, CacheAnalytics, CacheDependency
from typing import Any, Optional, Dict, List, Union


class CacheService:
    """Advanced Redis-based caching service"""
    
    def __init__(self):
        self.redis_client = None
        self._init_redis()
    
    def _init_redis(self):
        """Initialize Redis client"""
        try:
            self.redis_client = redis.Redis(
                host=current_app.config.get('REDIS_HOST', 'localhost'),
                port=current_app.config.get('REDIS_PORT', 6379),
                db=current_app.config.get('REDIS_DB', 0),
                password=current_app.config.get('REDIS_PASSWORD', None),
                decode_responses=False,
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_timeout=True
            )
            # Test connection
            self.redis_client.ping()
        except Exception as e:
            current_app.logger.warning(f"Redis connection failed, falling back to database caching: {e}")
            self.redis_client = None
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from cache"""
        start_time = datetime.utcnow()
        
        # Try Redis first
        if self.redis_client:
            try:
                value = self.redis_client.get(key)
                if value is not None:
                    # Track hit
                    response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                    CacheAnalytics.track_metric('hit', response_time, cache_type=self._get_cache_type(key), cache_key=key)
                    return pickle.loads(value)
                else:
                    # Track miss
                    response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                    CacheAnalytics.track_metric('miss', response_time, cache_type=self._get_cache_type(key), cache_key=key)
            except Exception as e:
                current_app.logger.error(f"Redis get error for key {key}: {e}")
        
        # Fallback to database cache
        value = CacheEntry.get_cache(key)
        if value is not None:
            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            CacheAnalytics.track_metric('hit', response_time, cache_type=self._get_cache_type(key), cache_key=key)
            return value
        else:
            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            CacheAnalytics.track_metric('miss', response_time, cache_type=self._get_cache_type(key), cache_key=key)
        
        return default
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None, tag: Optional[str] = None, cache_type: str = 'general') -> bool:
        """Set a value in cache"""
        start_time = datetime.utcnow()
        
        # Serialize value
        serialized = pickle.dumps(value)
        
        # Set in Redis if available
        if self.redis_client:
            try:
                if ttl:
                    self.redis_client.setex(key, ttl, serialized)
                else:
                    self.redis_client.set(key, serialized)
                
                # Track set operation
                response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                CacheAnalytics.track_metric('set', response_time, cache_type=cache_type, cache_key=key, cache_tag=tag)
                
                # Also store in database for analytics
                CacheEntry.set_cache(key, value, ttl, tag, cache_type, compress=False)
                return True
            except Exception as e:
                current_app.logger.error(f"Redis set error for key {key}: {e}")
        
        # Fallback to database cache
        CacheEntry.set_cache(key, value, ttl, tag, cache_type)
        
        # Track set operation
        response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        CacheAnalytics.track_metric('set', response_time, cache_type=cache_type, cache_key=key, cache_tag=tag)
        
        return True
    
    def delete(self, key: str) -> bool:
        """Delete a value from cache"""
        # Delete from Redis if available
        if self.redis_client:
            try:
                self.redis_client.delete(key)
            except Exception as e:
                current_app.logger.error(f"Redis delete error for key {key}: {e}")
        
        # Delete from database
        result = CacheEntry.delete_cache(key)
        
        if result:
            # Track invalidation
            CacheInvalidation.track_invalidation(key, invalidation_type='manual')
            CacheAnalytics.track_metric('delete', cache_type=self._get_cache_type(key), cache_key=key)
        
        return result
    
    def clear(self, cache_type: Optional[str] = None, tag: Optional[str] = None) -> int:
        """Clear cache entries"""
        cleared_count = 0
        
        # Clear from Redis if available
        if self.redis_client:
            try:
                if cache_type:
                    # Get all keys for this cache type
                    pattern = f"*{cache_type}*"
                    keys = self.redis_client.keys(pattern)
                    if keys:
                        self.redis_client.delete(*keys)
                        cleared_count += len(keys)
                elif tag:
                    # Tag-based clearing would require a different approach in Redis
                    # For now, clear all and rely on database for tag filtering
                    self.redis_client.flushdb()
                    cleared_count = self.redis_client.dbsize()
                else:
                    # Clear all
                    cleared_count = self.redis_client.dbsize()
                    self.redis_client.flushdb()
            except Exception as e:
                current_app.logger.error(f"Redis clear error: {e}")
        
        # Clear from database
        if cache_type:
            db_cleared = CacheEntry.clear_by_type(cache_type)
        elif tag:
            db_cleared = CacheEntry.clear_by_tag(tag)
        else:
            db_cleared = CacheEntry.query.count()
            CacheEntry.query.delete()
            db.session.commit()
        
        cleared_count += db_cleared
        
        # Track clear operation
        CacheAnalytics.track_metric('clear', value=cleared_count, cache_type=cache_type, cache_tag=tag)
        
        return cleared_count
    
    def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """Get multiple values from cache"""
        result = {}
        
        if self.redis_client:
            try:
                # Try Redis pipeline for efficiency
                pipeline = self.redis_client.pipeline()
                for key in keys:
                    pipeline.get(key)
                
                values = pipeline.execute()
                
                for i, key in enumerate(keys):
                    if values[i] is not None:
                        try:
                            result[key] = pickle.loads(values[i])
                            CacheAnalytics.track_metric('hit', cache_type=self._get_cache_type(key), cache_key=key)
                        except Exception:
                            result[key] = None
                            CacheAnalytics.track_metric('miss', cache_type=self._get_cache_type(key), cache_key=key)
                    else:
                        result[key] = None
                        CacheAnalytics.track_metric('miss', cache_type=self._get_cache_type(key), cache_key=key)
            except Exception as e:
                current_app.logger.error(f"Redis get_many error: {e}")
        
        # Fallback to database for missing keys
        for key in keys:
            if key not in result:
                value = CacheEntry.get_cache(key)
                result[key] = value
                if value is not None:
                    CacheAnalytics.track_metric('hit', cache_type=self._get_cache_type(key), cache_key=key)
                else:
                    CacheAnalytics.track_metric('miss', cache_type=self._get_cache_type(key), cache_key=key)
        
        return result
    
    def set_many(self, mapping: Dict[str, Any], ttl: Optional[int] = None, tag: Optional[str] = None, cache_type: str = 'general') -> bool:
        """Set multiple values in cache"""
        success = True
        
        if self.redis_client:
            try:
                pipeline = self.redis_client.pipeline()
                for key, value in mapping.items():
                    serialized = pickle.dumps(value)
                    if ttl:
                        pipeline.setex(key, ttl, serialized)
                    else:
                        pipeline.set(key, serialized)
                
                pipeline.execute()
                
                # Track set operations
                for key in mapping.keys():
                    CacheAnalytics.track_metric('set', cache_type=cache_type, cache_key=key, cache_tag=tag)
                
                # Also store in database for analytics
                for key, value in mapping.items():
                    CacheEntry.set_cache(key, value, ttl, tag, cache_type, compress=False)
            except Exception as e:
                current_app.logger.error(f"Redis set_many error: {e}")
                success = False
        
        # Fallback to database
        for key, value in mapping.items():
            CacheEntry.set_cache(key, value, ttl, tag, cache_type)
            CacheAnalytics.track_metric('set', cache_type=cache_type, cache_key=key, cache_tag=tag)
        
        return success
    
    def invalidate_by_tag(self, tag: str) -> int:
        """Invalidate all cache entries with a specific tag"""
        return CacheDependency.invalidate_by_tag(tag)
    
    def invalidate_by_pattern(self, pattern: str) -> int:
        """Invalidate cache entries matching a pattern"""
        return CacheDependency.invalidate_by_pattern(pattern)
    
    def add_dependency(self, parent_key: str, child_key: str, dependency_type: str = 'manual') -> bool:
        """Add a cache dependency"""
        try:
            CacheDependency.add_dependency(parent_key, child_key, dependency_type)
            return True
        except Exception as e:
            current_app.logger.error(f"Cache dependency error: {e}")
            return False
    
    def invalidate_dependents(self, parent_key: str) -> List[str]:
        """Invalidate all dependent cache entries"""
        return CacheDependency.invalidate_dependents(parent_key)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        stats = {
            'database_stats': CacheEntry.get_cache_stats(),
            'invalidation_stats': CacheInvalidation.get_invalidation_stats(hours=24),
            'performance_metrics': CacheAnalytics.get_performance_metrics(hours=1),
            'cache_type_performance': CacheAnalytics.get_cache_type_performance(hours=1),
            'trending_keys': CacheAnalytics.get_trending_keys(hours=1, limit=10),
            'dependency_stats': CacheDependency.get_dependency_stats()
        }
        
        # Add Redis stats if available
        if self.redis_client:
            try:
                redis_info = self.redis_client.info()
                stats['redis_stats'] = {
                    'used_memory': redis_info.get('used_memory', 0),
                    'used_memory_human': redis_info.get('used_memory_human', '0B'),
                    'connected_clients': redis_info.get('connected_clients', 0),
                    'total_commands_processed': redis_info.get('total_commands_processed', 0),
                    'keyspace_hits': redis_info.get('keyspace_hits', 0),
                    'keyspace_misses': redis_info.get('keyspace_misses', 0),
                    'hit_ratio': redis_info.get('keyspace_hits', 0) / max(redis_info.get('keyspace_hits', 0) + redis_info.get('keyspace_misses', 0), 1)
                }
            except Exception as e:
                current_app.logger.error(f"Redis stats error: {e}")
        
        return stats
    
    def cleanup_expired(self) -> int:
        """Clean up expired cache entries"""
        # Clean up database entries
        db_cleared = CacheEntry.clear_expired()
        
        # Redis handles TTL automatically
        redis_cleared = 0
        
        return db_cleared + redis_cleared
    
    def _get_cache_type(self, key: str) -> str:
        """Determine cache type from key"""
        if ':' in key:
            parts = key.split(':')
            if len(parts) >= 2:
                return parts[0]
        return 'general'


class DistributedCacheService:
    """Distributed caching service for multi-instance deployments"""
    
    def __init__(self):
        self.cache_service = CacheService()
        self.instance_id = current_app.config.get('INSTANCE_ID', 'default')
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get value from distributed cache"""
        distributed_key = f"{self.instance_id}:{key}"
        return self.cache_service.get(distributed_key, default)
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None, tag: Optional[str] = None, cache_type: str = 'distributed') -> bool:
        """Set value in distributed cache"""
        distributed_key = f"{self.instance_id}:{key}"
        return self.cache_service.set(distributed_key, value, ttl, tag, cache_type)
    
    def delete(self, key: str) -> bool:
        """Delete value from distributed cache"""
        distributed_key = f"{self.instance_id}:{key}"
        return self.cache_service.delete(distributed_key)
    
    def invalidate_global(self, key: str) -> bool:
        """Invalidate cache across all instances"""
        # Try to invalidate from all instances
        # This would typically use Redis pub/sub or a message queue
        success = True
        
        # Delete from local instance
        local_key = f"{self.instance_id}:{key}"
        if not self.cache_service.delete(local_key):
            success = False
        
        # Here you would typically publish an invalidation message
        # to other instances via Redis pub/sub or message queue
        
        return success
    
    def get_global_stats(self) -> Dict[str, Any]:
        """Get global cache statistics across all instances"""
        stats = self.cache_service.get_stats()
        stats['instance_id'] = self.instance_id
        stats['cache_type'] = 'distributed'
        return stats


# Cache decorators for easy use
def cache_result(ttl: int = 3600, tag: Optional[str] = None, cache_type: str = 'general'):
    """Decorator to cache function results"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Generate cache key
            import hashlib
            key_data = f"{func.__name__}:{args}:{kwargs}"
            cache_key = f"{cache_type}:{hashlib.md5(key_data.encode()).hexdigest()}"
            
            cache_service = CacheService()
            
            # Try to get from cache
            result = cache_service.get(cache_key)
            if result is not None:
                return result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_service.set(cache_key, result, ttl, tag, cache_type)
            
            return result
        return wrapper
    return decorator


def cache_user_data(ttl: int = 1800, tag: Optional[str] = None):
    """Decorator to cache user-specific data"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Extract user_id from first argument or kwargs
            user_id = None
            if args and hasattr(args[0], 'id'):
                user_id = args[0].id
            elif 'user_id' in kwargs:
                user_id = kwargs['user_id']
            elif 'user' in kwargs and hasattr(kwargs['user'], 'id'):
                user_id = kwargs['user'].id
            
            if not user_id:
                return func(*args, **kwargs)
            
            # Generate cache key
            import hashlib
            key_data = f"{func.__name__}:{user_id}:{args}:{kwargs}"
            cache_key = f"user:{user_id}:{hashlib.md5(key_data.encode()).hexdigest()}"
            
            cache_service = CacheService()
            
            # Try to get from cache
            result = cache_service.get(cache_key)
            if result is not None:
                return result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_service.set(cache_key, result, ttl, tag, 'user')
            
            return result
        return wrapper
    return decorator


# Global cache service instance
cache_service = CacheService()
distributed_cache = DistributedCacheService()
