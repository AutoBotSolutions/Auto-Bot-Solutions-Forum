"""
Advanced Caching Module
Provides Redis-based caching with distributed caching, cache invalidation tracking,
analytics, and dependency management for the Auto Bot Solutions Forum.
"""

from .models import CacheEntry, CacheInvalidation, CacheAnalytics, CacheDependency
from .service import CacheService, DistributedCacheService, cache_result, cache_user_data, cache_service, distributed_cache
from .utils import CacheWarmer, CacheOptimizer, CacheKeyGenerator, CacheDependencyManager, CacheMonitor
from .config import CacheConfig, CachePolicy, CachePerformanceConfig, CacheMonitoringConfig, get_cache_config

__all__ = [
    # Models
    'CacheEntry',
    'CacheInvalidation', 
    'CacheAnalytics',
    'CacheDependency',
    
    # Services
    'CacheService',
    'DistributedCacheService',
    'cache_service',
    'distributed_cache',
    
    # Decorators
    'cache_result',
    'cache_user_data',
    
    # Utilities
    'CacheWarmer',
    'CacheOptimizer',
    'CacheKeyGenerator',
    'CacheDependencyManager',
    'CacheMonitor',
    
    # Configuration
    'CacheConfig',
    'CachePolicy',
    'CachePerformanceConfig',
    'CacheMonitoringConfig',
    'get_cache_config'
]
