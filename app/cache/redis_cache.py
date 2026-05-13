"""
Redis-based Caching Service
Provides Redis-based response caching for API endpoints
"""

import json
import pickle
import hashlib
from datetime import datetime, timedelta
from typing import Any, Optional, Dict, List, Union
from functools import wraps
from flask import current_app, request, g
import redis
import logging

logger = logging.getLogger(__name__)

class RedisCacheService:
    """Redis-based caching service for API responses"""
    
    def __init__(self, redis_url: str = None, key_prefix: str = "api_cache:"):
        """Initialize Redis cache service"""
        self.redis_url = redis_url or current_app.config.get('REDIS_CACHE_URL', 'redis://localhost:6379/3')
        self.key_prefix = key_prefix
        self.default_ttl = current_app.config.get('CACHE_DEFAULT_TTL', 3600)  # 1 hour default
        self._redis_client = None
        
    @property
    def redis_client(self):
        """Get Redis client (lazy initialization)"""
        if self._redis_client is None:
            try:
                self._redis_client = redis.from_url(
                    self.redis_url,
                    decode_responses=False,  # Handle binary data properly
                    socket_timeout=5,
                    socket_connect_timeout=5,
                    retry_on_timeout=True
                )
                # Test connection
                self._redis_client.ping()
                logger.info("Redis cache service connected successfully")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                self._redis_client = None
        
        return self._redis_client
    
    def is_available(self) -> bool:
        """Check if Redis is available"""
        try:
            if self.redis_client:
                self.redis_client.ping()
                return True
            return False
        except Exception:
            return False
    
    def _make_key(self, key: str) -> str:
        """Create full cache key with prefix"""
        return f"{self.key_prefix}{key}"
    
    def _serialize_value(self, value: Any) -> bytes:
        """Serialize value for Redis storage"""
        try:
            if isinstance(value, (str, int, float, bool)):
                return str(value).encode('utf-8')
            elif isinstance(value, (dict, list, tuple)):
                return json.dumps(value, default=str).encode('utf-8')
            else:
                return pickle.dumps(value)
        except Exception as e:
            logger.error(f"Error serializing value: {e}")
            raise
    
    def _deserialize_value(self, value: bytes, original_type: type = None) -> Any:
        """Deserialize value from Redis storage"""
        if value is None:
            return None
        
        try:
            # Try JSON first (most common)
            try:
                return json.loads(value.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError):
                pass
            
            # Try pickle
            try:
                return pickle.loads(value)
            except (pickle.PickleError, TypeError):
                pass
            
            # Return as string
            return value.decode('utf-8')
        except Exception as e:
            logger.error(f"Error deserializing value: {e}")
            return None
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.is_available():
            return None
        
        try:
            full_key = self._make_key(key)
            value = self.redis_client.get(full_key)
            
            if value is not None:
                logger.debug(f"Cache hit for key: {key}")
                return self._deserialize_value(value)
            else:
                logger.debug(f"Cache miss for key: {key}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting cache key {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """Set value in cache with TTL"""
        if not self.is_available():
            return False
        
        try:
            full_key = self._make_key(key)
            serialized_value = self._serialize_value(value)
            expire_time = ttl or self.default_ttl
            
            result = self.redis_client.setex(full_key, expire_time, serialized_value)
            
            if result:
                logger.debug(f"Cache set for key: {key}, TTL: {expire_time}s")
            else:
                logger.warning(f"Failed to set cache key: {key}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error setting cache key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self.is_available():
            return False
        
        try:
            full_key = self._make_key(key)
            result = self.redis_client.delete(full_key)
            
            if result:
                logger.debug(f"Cache deleted for key: {key}")
            
            return result > 0
            
        except Exception as e:
            logger.error(f"Error deleting cache key {key}: {e}")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """Delete keys matching pattern"""
        if not self.is_available():
            return 0
        
        try:
            full_pattern = self._make_key(pattern)
            keys = self.redis_client.keys(full_pattern)
            
            if keys:
                result = self.redis_client.delete(*keys)
                logger.debug(f"Cache deleted {result} keys matching pattern: {pattern}")
                return result
            
            return 0
            
        except Exception as e:
            logger.error(f"Error deleting cache pattern {pattern}: {e}")
            return 0
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        if not self.is_available():
            return False
        
        try:
            full_key = self._make_key(key)
            return self.redis_client.exists(full_key) > 0
            
        except Exception as e:
            logger.error(f"Error checking cache key {key}: {e}")
            return False
    
    def expire(self, key: str, ttl: int) -> bool:
        """Set expiration for existing key"""
        if not self.is_available():
            return False
        
        try:
            full_key = self._make_key(key)
            return self.redis_client.expire(full_key, ttl)
            
        except Exception as e:
            logger.error(f"Error setting expiration for cache key {key}: {e}")
            return False
    
    def ttl(self, key: str) -> int:
        """Get TTL for key"""
        if not self.is_available():
            return -1
        
        try:
            full_key = self._make_key(key)
            return self.redis_client.ttl(full_key)
            
        except Exception as e:
            logger.error(f"Error getting TTL for cache key {key}: {e}")
            return -1
    
    def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment numeric value"""
        if not self.is_available():
            return None
        
        try:
            full_key = self._make_key(key)
            return self.redis_client.incr(full_key, amount)
            
        except Exception as e:
            logger.error(f"Error incrementing cache key {key}: {e}")
            return None
    
    def get_multiple(self, keys: List[str]) -> Dict[str, Any]:
        """Get multiple values from cache"""
        if not self.is_available():
            return {}
        
        try:
            full_keys = [self._make_key(key) for key in keys]
            values = self.redis_client.mget(full_keys)
            
            result = {}
            for i, key in enumerate(keys):
                if values[i] is not None:
                    result[key] = self._deserialize_value(values[i])
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting multiple cache keys: {e}")
            return {}
    
    def set_multiple(self, mapping: Dict[str, Any], ttl: int = None) -> bool:
        """Set multiple values in cache"""
        if not self.is_available():
            return False
        
        try:
            expire_time = ttl or self.default_ttl
            
            # Use pipeline for better performance
            pipe = self.redis_client.pipeline()
            
            for key, value in mapping.items():
                full_key = self._make_key(key)
                serialized_value = self._serialize_value(value)
                pipe.setex(full_key, expire_time, serialized_value)
            
            pipe.execute()
            logger.debug(f"Cache set for {len(mapping)} keys")
            return True
            
        except Exception as e:
            logger.error(f"Error setting multiple cache keys: {e}")
            return False
    
    def clear_all(self) -> bool:
        """Clear all cache keys with prefix"""
        if not self.is_available():
            return False
        
        try:
            pattern = self._make_key("*")
            keys = self.redis_client.keys(pattern)
            
            if keys:
                result = self.redis_client.delete(*keys)
                logger.info(f"Cache cleared: {result} keys deleted")
                return True
            
            return True
            
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False
    
    def get_info(self) -> Dict[str, Any]:
        """Get Redis cache information"""
        if not self.is_available():
            return {}
        
        try:
            info = self.redis_client.info()
            
            # Get cache-specific info
            pattern = self._make_key("*")
            cache_keys = self.redis_client.keys(pattern)
            
            return {
                'redis_version': info.get('redis_version'),
                'connected_clients': info.get('connected_clients'),
                'used_memory': info.get('used_memory'),
                'used_memory_human': info.get('used_memory_human'),
                'cache_keys_count': len(cache_keys),
                'cache_keys': [key.decode('utf-8').replace(self.key_prefix, '') for key in cache_keys[:10]],  # First 10 keys
                'is_available': True
            }
            
        except Exception as e:
            logger.error(f"Error getting cache info: {e}")
            return {'is_available': False, 'error': str(e)}
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on cache service"""
        health = {
            'status': 'healthy',
            'redis_available': False,
            'response_time': None,
            'error': None
        }
        
        try:
            start_time = datetime.utcnow()
            
            # Test Redis connection
            if self.is_available():
                health['redis_available'] = True
                
                # Test basic operations
                test_key = f"health_check_{datetime.utcnow().timestamp()}"
                test_value = "test_value"
                
                # Test set
                if self.set(test_key, test_value, ttl=10):
                    # Test get
                    retrieved_value = self.get(test_key)
                    if retrieved_value == test_value:
                        # Test delete
                        self.delete(test_key)
                        
                        # Calculate response time
                        end_time = datetime.utcnow()
                        health['response_time'] = (end_time - start_time).total_seconds() * 1000  # ms
                    else:
                        health['status'] = 'error'
                        health['error'] = 'Value mismatch'
                else:
                    health['status'] = 'error'
                    health['error'] = 'Failed to set test value'
            else:
                health['status'] = 'error'
                health['error'] = 'Redis not available'
                
        except Exception as e:
            health['status'] = 'error'
            health['error'] = str(e)
            logger.error(f"Cache health check failed: {e}")
        
        return health


# Decorators for caching

def cache_response(ttl: int = None, key_prefix: str = "", cache_key_func=None):
    """Decorator to cache API responses"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Generate cache key
            if cache_key_func:
                cache_key = cache_key_func(request, *args, **kwargs)
            else:
                cache_key = _default_cache_key_builder(request, f.__name__, *args, **kwargs)
            
            if key_prefix:
                cache_key = f"{key_prefix}:{cache_key}"
            
            # Try to get from cache
            cache_service = current_app.extensions.get('cache_service')
            if cache_service:
                cached_response = cache_service.get(cache_key)
                if cached_response is not None:
                    logger.debug(f"Cache hit for {cache_key}")
                    return cached_response
            
            # Execute function
            response = f(*args, **kwargs)
            
            # Cache the response
            if cache_service and hasattr(response, 'status_code') and response.status_code == 200:
                cache_service.set(cache_key, response.get_data(), ttl)
                logger.debug(f"Cache set for {cache_key}")
            
            return response
        
        return decorated_function
    return decorator


def cache_key_builder(*args, **kwargs):
    """Build cache key from function arguments"""
    parts = []
    
    # Add function name
    if args and callable(args[0]):
        parts.append(args[0].__name__)
        args = args[1:]
    
    # Add string arguments
    for arg in args:
        if isinstance(arg, (str, int, float, bool)):
            parts.append(str(arg))
        elif isinstance(arg, dict):
            # Sort dict keys for consistency
            sorted_items = sorted(arg.items())
            parts.append(json.dumps(sorted_items, sort_keys=True))
        elif isinstance(arg, (list, tuple)):
            parts.append(json.dumps(arg, sort_keys=True))
    
    # Add keyword arguments
    if kwargs:
        sorted_kwargs = sorted(kwargs.items())
        parts.append(json.dumps(sorted_kwargs, sort_keys=True))
    
    # Create hash for long keys
    key_string = ":".join(parts)
    if len(key_string) > 200:
        key_string = hashlib.md5(key_string.encode()).hexdigest()
    
    return key_string


def _default_cache_key_builder(request, func_name, *args, **kwargs):
    """Default cache key builder for API responses"""
    parts = [func_name]
    
    # Add request method
    if request:
        parts.append(request.method)
        
        # Add endpoint
        parts.append(request.endpoint or request.path)
        
        # Add query parameters
        if request.args:
            sorted_args = sorted(request.args.items())
            parts.append(json.dumps(sorted_args, sort_keys=True))
        
        # Add JSON data for POST/PUT
        if request.method in ['POST', 'PUT'] and request.get_json():
            parts.append(json.dumps(request.get_json(), sort_keys=True))
    
    # Add function arguments
    for arg in args:
        if isinstance(arg, (str, int, float, bool)):
            parts.append(str(arg))
    
    # Create key
    key_string = ":".join(parts)
    if len(key_string) > 200:
        key_string = hashlib.md5(key_string.encode()).hexdigest()
    
    return key_string


def cache_ttl(ttl: int):
    """Helper function to define cache TTL constants"""
    return ttl


# Cache TTL constants
CACHE_TTL = {
    'VERY_SHORT': 60,      # 1 minute
    'SHORT': 300,          # 5 minutes
    'MEDIUM': 1800,        # 30 minutes
    'LONG': 3600,          # 1 hour
    'VERY_LONG': 86400,    # 24 hours
    'WEEK': 604800,        # 1 week
    'MONTH': 2592000       # 1 month
}
