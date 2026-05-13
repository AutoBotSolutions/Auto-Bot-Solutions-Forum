"""
Cache Utilities
Helper functions and utilities for cache management
"""

import json
import hashlib
from datetime import datetime, timedelta
from typing import Any, Optional, Dict, List, Union, Callable
from flask import request, g
from functools import wraps

from .redis_cache import CACHE_TTL

def cache_key_builder(*args, **kwargs) -> str:
    """Build cache key from function arguments"""
    parts = []
    
    # Add function name if first arg is callable
    if args and callable(args[0]):
        parts.append(args[0].__name__)
        args = args[1:]
    
    # Add arguments
    for arg in args:
        if isinstance(arg, (str, int, float, bool)):
            parts.append(str(arg))
        elif isinstance(arg, dict):
            # Sort dict keys for consistency
            sorted_items = sorted(arg.items())
            parts.append(json.dumps(sorted_items, sort_keys=True))
        elif isinstance(arg, (list, tuple)):
            parts.append(json.dumps(arg, sort_keys=True))
        elif arg is not None:
            parts.append(str(arg))
    
    # Add keyword arguments
    if kwargs:
        sorted_kwargs = sorted(kwargs.items())
        parts.append(json.dumps(sorted_kwargs, sort_keys=True))
    
    # Create hash for long keys
    key_string = ":".join(parts)
    if len(key_string) > 200:
        key_string = hashlib.md5(key_string.encode()).hexdigest()
    
    return key_string


def api_cache_key_builder(request, func_name: str, *args, **kwargs) -> str:
    """Build cache key for API responses"""
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
        
        # Add user context if available
        if hasattr(g, 'current_user') and g.current_user:
            parts.append(f"user:{g.current_user.id}")
    
    # Add function arguments
    for arg in args:
        if isinstance(arg, (str, int, float, bool)):
            parts.append(str(arg))
    
    # Create key
    key_string = ":".join(parts)
    if len(key_string) > 200:
        key_string = hashlib.md5(key_string.encode()).hexdigest()
    
    return key_string


def user_cache_key_builder(user_id: int, resource: str, *args, **kwargs) -> str:
    """Build cache key for user-specific resources"""
    parts = [f"user:{user_id}", resource]
    
    # Add additional arguments
    for arg in args:
        if isinstance(arg, (str, int, float, bool)):
            parts.append(str(arg))
    
    # Add keyword arguments
    if kwargs:
        sorted_kwargs = sorted(kwargs.items())
        parts.append(json.dumps(sorted_kwargs, sort_keys=True))
    
    return ":".join(parts)


def object_cache_key_builder(object_type: str, object_id: int, resource: str, *args, **kwargs) -> str:
    """Build cache key for object-specific resources"""
    parts = [f"{object_type}:{object_id}", resource]
    
    # Add additional arguments
    for arg in args:
        if isinstance(arg, (str, int, float, bool)):
            parts.append(str(arg))
    
    # Add keyword arguments
    if kwargs:
        sorted_kwargs = sorted(kwargs.items())
        parts.append(json.dumps(sorted_kwargs, sort_keys=True))
    
    return ":".join(parts)


def cache_ttl(ttl: Union[int, str]) -> int:
    """Convert TTL value to seconds"""
    if isinstance(ttl, str):
        return CACHE_TTL.get(ttl.upper(), CACHE_TTL['MEDIUM'])
    return ttl


def get_cache_ttl_for_endpoint(request) -> int:
    """Get appropriate TTL for API endpoint"""
    if not request:
        return CACHE_TTL['MEDIUM']
    
    # Different TTLs for different endpoints
    endpoint = request.endpoint or request.path
    
    # Static content - longer TTL
    if endpoint in ['api.posts', 'api.users', 'api.categories']:
        return CACHE_TTL['LONG']
    
    # Dynamic content - shorter TTL
    if endpoint in ['api.posts.search', 'api.users.search']:
        return CACHE_TTL['SHORT']
    
    # User-specific content - medium TTL
    if 'user' in endpoint:
        return CACHE_TTL['MEDIUM']
    
    # Default TTL
    return CACHE_TTL['MEDIUM']


def get_cache_tags_for_endpoint(request) -> List[str]:
    """Get appropriate cache tags for API endpoint"""
    tags = []
    
    if not request:
        return tags
    
    # Add user tag if user is authenticated
    if hasattr(g, 'current_user') and g.current_user:
        tags.append(f"user:{g.current_user.id}")
    
    # Add endpoint-specific tags
    endpoint = request.endpoint or request.path
    if 'posts' in endpoint:
        tags.append('posts')
    if 'users' in endpoint:
        tags.append('users')
    if 'comments' in endpoint:
        tags.append('comments')
    
    # Add method tag
    tags.append(request.method.lower())
    
    return tags


def serialize_for_cache(data: Any) -> bytes:
    """Serialize data for cache storage"""
    if isinstance(data, (str, int, float, bool)):
        return str(data).encode('utf-8')
    elif isinstance(data, (dict, list, tuple)):
        return json.dumps(data, default=str).encode('utf-8')
    else:
        # For complex objects, try to serialize as dict
        try:
            if hasattr(data, 'to_dict'):
                return json.dumps(data.to_dict(), default=str).encode('utf-8')
            elif hasattr(data, '__dict__'):
                return json.dumps(data.__dict__, default=str).encode('utf-8')
            else:
                return str(data).encode('utf-8')
        except Exception:
            return str(data).encode('utf-8')


def deserialize_from_cache(data: bytes) -> Any:
    """Deserialize data from cache storage"""
    if data is None:
        return None
    
    try:
        # Try JSON first
        try:
            return json.loads(data.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            pass
        
        # Return as string
        return data.decode('utf-8')
    except Exception as e:
        return None


def cache_key_hash(key: str) -> str:
    """Create hash of cache key for long keys"""
    return hashlib.md5(key.encode()).hexdigest()


def is_cacheable_response(response) -> bool:
    """Check if response should be cached"""
    if not response:
        return False
    
    # Check status code
    if hasattr(response, 'status_code'):
        if response.status_code != 200:
            return False
    
    # Check content type
    if hasattr(response, 'headers'):
        content_type = response.headers.get('Content-Type', '')
        if 'application/json' not in content_type and 'text/html' not in content_type:
            return False
    
    # Check cache control headers
    if hasattr(response, 'headers'):
        cache_control = response.headers.get('Cache-Control', '')
        if 'no-cache' in cache_control or 'private' in cache_control:
            return False
    
    return True


def get_cache_control_headers(ttl: int) -> Dict[str, str]:
    """Generate cache control headers"""
    headers = {}
    
    if ttl > 0:
        headers['Cache-Control'] = f'public, max-age={ttl}'
        headers['Expires'] = (datetime.utcnow() + timedelta(seconds=ttl)).strftime('%a, %d %b %Y %H:%M:%S GMT')
    else:
        headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        headers['Pragma'] = 'no-cache'
        headers['Expires'] = '0'
    
    return headers


def build_cache_key_pattern(prefix: str, **kwargs) -> str:
    """Build cache key pattern for invalidation"""
    parts = [prefix]
    
    # Add key-value pairs
    for key, value in sorted(kwargs.items()):
        if value is not None:
            parts.append(f"{key}:{value}")
    
    return ":".join(parts)


def extract_cache_info(headers: Dict[str, str]) -> Dict[str, Any]:
    """Extract cache information from response headers"""
    cache_info = {}
    
    # Cache-Control
    cache_control = headers.get('Cache-Control', '')
    if cache_control:
        cache_info['cache_control'] = cache_control
        
        # Parse max-age
        if 'max-age=' in cache_control:
            for directive in cache_control.split(','):
                directive = directive.strip()
                if directive.startswith('max-age='):
                    try:
                        cache_info['max_age'] = int(directive.split('=')[1])
                    except ValueError:
                        pass
    
    # ETag
    etag = headers.get('ETag')
    if etag:
        cache_info['etag'] = etag
    
    # Last-Modified
    last_modified = headers.get('Last-Modified')
    if last_modified:
        cache_info['last_modified'] = last_modified
    
    return cache_info


def validate_cache_key(key: str) -> bool:
    """Validate cache key format"""
    if not key:
        return False
    
    # Check length
    if len(key) > 255:
        return False
    
    # Check for invalid characters
    invalid_chars = [' ', '\t', '\n', '\r']
    for char in invalid_chars:
        if char in key:
            return False
    
    return True


def normalize_cache_key(key: str) -> str:
    """Normalize cache key"""
    # Convert to lowercase
    key = key.lower()
    
    # Replace spaces with underscores
    key = key.replace(' ', '_')
    
    # Remove invalid characters
    key = ''.join(c for c in key if c.isalnum() or c in ['_', ':', '-'])
    
    # Truncate if too long
    if len(key) > 255:
        key = key[:250] + hashlib.md5(key.encode()).hexdigest()[:5]
    
    return key


def create_cache_tag(tags: List[str]) -> str:
    """Create cache tag from list of tags"""
    if not tags:
        return ""
    
    # Sort tags for consistency
    sorted_tags = sorted(tags)
    
    # Join with separator
    return "|".join(sorted_tags)


def parse_cache_tag(tag_string: str) -> List[str]:
    """Parse cache tag string back to list"""
    if not tag_string:
        return []
    
    return tag_string.split("|")


def get_cache_stats_summary(stats: Dict[str, Any]) -> Dict[str, Any]:
    """Create summary of cache statistics"""
    summary = {}
    
    # Basic stats
    summary['total_requests'] = stats.get('total_requests', 0)
    summary['hits'] = stats.get('hits', 0)
    summary['misses'] = stats.get('misses', 0)
    summary['hit_rate'] = stats.get('hit_rate_percent', 0)
    
    # Performance indicators
    if summary['total_requests'] > 0:
        summary['performance'] = 'good'
        if summary['hit_rate'] < 50:
            summary['performance'] = 'poor'
        elif summary['hit_rate'] < 75:
            summary['performance'] = 'fair'
    else:
        summary['performance'] = 'unknown'
    
    # Recommendations
    summary['recommendations'] = []
    
    if summary['hit_rate'] < 50:
        summary['recommendations'].append("Consider increasing TTL values")
    
    if summary['hit_rate'] < 30:
        summary['recommendations'].append("Review cache warming strategies")
    
    if not stats.get('cache_available', False):
        summary['recommendations'].append("Cache service is not available")
    
    return summary


# Decorators for cache management

def cache_with_tags(tags: List[str], ttl: int = None):
    """Decorator to cache with tags"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # This would be implemented with the actual cache service
            # For now, just pass through
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def invalidate_cache_on_change(*tags: str):
    """Decorator to invalidate cache when data changes"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Execute function
            result = f(*args, **kwargs)
            
            # Invalidate cache tags
            # This would be implemented with the actual cache manager
            # For now, just pass through
            
            return result
        return decorated_function
    return decorator


def conditional_cache(condition: bool, ttl: int = None):
    """Decorator to conditionally cache response"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # This would be implemented with the actual cache service
            # For now, just pass through
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# Cache warming utilities

def create_warmup_task(key: str, warmer_func: Callable, ttl: int, interval: int = 3600):
    """Create a cache warming task"""
    def warmup_task():
        try:
            data = warmer_func()
            # This would use the actual cache service
            # For now, just return the data
            return data
        except Exception as e:
            # Log error but don't crash
            print(f"Cache warming error for {key}: {e}")
            return None
    
    return warmup_task


def schedule_warmup(tasks: List[Callable]):
    """Schedule multiple cache warming tasks"""
    # This would be implemented with a task scheduler like Celery
    # For now, just return the tasks
    return tasks


# Cache monitoring utilities

def monitor_cache_performance(cache_service) -> Dict[str, Any]:
    """Monitor cache performance metrics"""
    metrics = {
        'timestamp': datetime.utcnow().isoformat(),
        'cache_available': cache_service.is_available(),
        'response_times': [],
        'error_rates': {},
        'memory_usage': {}
    }
    
    if cache_service.is_available():
        try:
            # Get Redis info
            info = cache_service.get_info()
            
            # Memory usage
            if info.get('used_memory'):
                metrics['memory_usage'] = {
                    'used_bytes': info['used_memory'],
                    'used_mb': info['used_memory'] / (1024 * 1024),
                    'used_gb': info['used_memory'] / (1024 * 1024 * 1024),
                    'used_human': info.get('used_memory_human', 'Unknown')
                }
            
            # Connection info
            metrics['connected_clients'] = info.get('connected_clients', 0)
            metrics['redis_version'] = info.get('redis_version', 'Unknown')
            
        except Exception as e:
            metrics['error'] = str(e)
    
    return metrics


def generate_cache_report(cache_manager) -> Dict[str, Any]:
    """Generate comprehensive cache report"""
    report = {
        'generated_at': datetime.utcnow().isoformat(),
        'cache_stats': cache_manager.get_cache_stats(),
        'cache_info': cache_manager.cache_service.get_info(),
        'optimization_results': cache_manager.optimize_cache(),
        'configuration': cache_manager.export_cache_config()
    }
    
    return report
