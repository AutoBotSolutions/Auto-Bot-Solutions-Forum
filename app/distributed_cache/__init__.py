"""
Distributed Cache Module

Distributed caching system for the Auto Bot Solutions Forum with Redis integration,
cluster management, cache synchronization, and failover handling.
"""

from .models import CacheCluster, CacheNode, CacheSynchronization, CacheFailover
from .service import DistributedCacheService, get_distributed_cache_service
from .utils import (
    CacheShardingStrategy, CacheReplicationStrategy, CacheKeyInfo,
    CacheSharding, CacheReplication, CacheConsistencyChecker, CachePerformanceMonitor,
    CacheKeyManager, CacheUtils, cache_sharding, cache_replication,
    cache_consistency_checker, cache_performance_monitor, cache_key_manager
)
from .config import (
    DISTRIBUTED_CACHE_ENABLED, REDIS_INTEGRATION_ENABLED, CLUSTER_MANAGEMENT_ENABLED,
    CACHE_SYNCHRONIZATION_ENABLED, FAILOVER_ENABLED, REDIS_CONFIG, CLUSTER_CONFIG,
    SENTINEL_CONFIG, SHARDING_CONFIG, REPLICATION_CONFIG, SYNCHRONIZATION_CONFIG,
    FAILOVER_CONFIG, CACHE_CONFIG, PERFORMANCE_CONFIG, SECURITY_CONFIG, MONITORING_CONFIG,
    BACKUP_CONFIG, CACHE_KEY_PATTERNS, CACHE_TTL_CONFIG, get_distributed_cache_config,
    validate_distributed_cache_config
)

__all__ = [
    # Models
    'CacheCluster',
    'CacheNode',
    'CacheSynchronization',
    'CacheFailover',
    
    # Services
    'DistributedCacheService',
    'get_distributed_cache_service',
    
    # Utilities
    'CacheShardingStrategy',
    'CacheReplicationStrategy',
    'CacheKeyInfo',
    'CacheSharding',
    'CacheReplication',
    'CacheConsistencyChecker',
    'CachePerformanceMonitor',
    'CacheKeyManager',
    'CacheUtils',
    'cache_sharding',
    'cache_replication',
    'cache_consistency_checker',
    'cache_performance_monitor',
    'cache_key_manager',
    
    # Configuration
    'DISTRIBUTED_CACHE_ENABLED',
    'REDIS_INTEGRATION_ENABLED',
    'CLUSTER_MANAGEMENT_ENABLED',
    'CACHE_SYNCHRONIZATION_ENABLED',
    'FAILOVER_ENABLED',
    'REDIS_CONFIG',
    'CLUSTER_CONFIG',
    'SENTINEL_CONFIG',
    'SHARDING_CONFIG',
    'REPLICATION_CONFIG',
    'SYNCHRONIZATION_CONFIG',
    'FAILOVER_CONFIG',
    'CACHE_CONFIG',
    'PERFORMANCE_CONFIG',
    'SECURITY_CONFIG',
    'MONITORING_CONFIG',
    'BACKUP_CONFIG',
    'CACHE_KEY_PATTERNS',
    'CACHE_TTL_CONFIG',
    'get_distributed_cache_config',
    'validate_distributed_cache_config'
]
