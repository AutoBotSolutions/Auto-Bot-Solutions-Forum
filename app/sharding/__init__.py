"""
Sharding Module

Database sharding system for the Auto Bot Solutions Forum with shard management,
cross-shard queries, shard failover, and load balancing.
"""

from .models import ShardCluster, Shard, CrossShardQuery, ShardFailover
from .service import DatabaseShardingService, get_database_sharding_service
from .utils import (
    ShardingStrategy, ShardStatus, FailoverStrategy, ShardInfo, QueryPlan,
    ShardSelector, QueryPlanner, FailoverManager, ConnectionPool, ShardingUtils,
    shard_selector, query_planner, failover_manager, connection_pool, sharding_utils
)
from .config import (
    DATABASE_SHARDING_ENABLED, CROSS_SHARD_QUERIES_ENABLED, SHARD_FAILOVER_ENABLED,
    LOAD_BALANCING_ENABLED, SHARD_MONITORING_ENABLED, CLUSTER_CONFIG, SHARDING_CONFIG,
    CROSS_SHARD_CONFIG, FAILOVER_CONFIG, LOAD_BALANCING_CONFIG, CONNECTION_CONFIG,
    MONITORING_CONFIG, PERFORMANCE_CONFIG, SECURITY_CONFIG, DATABASE_TYPE_CONFIGS,
    SHARD_TEMPLATES, QUERY_TEMPLATES, get_sharding_config, validate_sharding_config
)

__all__ = [
    # Models
    'ShardCluster',
    'Shard',
    'CrossShardQuery',
    'ShardFailover',
    
    # Services
    'DatabaseShardingService',
    'get_database_sharding_service',
    
    # Utilities
    'ShardingStrategy',
    'ShardStatus',
    'FailoverStrategy',
    'ShardInfo',
    'QueryPlan',
    'ShardSelector',
    'QueryPlanner',
    'FailoverManager',
    'ConnectionPool',
    'ShardingUtils',
    'shard_selector',
    'query_planner',
    'failover_manager',
    'connection_pool',
    'sharding_utils',
    
    # Configuration
    'DATABASE_SHARDING_ENABLED',
    'CROSS_SHARD_QUERIES_ENABLED',
    'SHARD_FAILOVER_ENABLED',
    'LOAD_BALANCING_ENABLED',
    'SHARD_MONITORING_ENABLED',
    'CLUSTER_CONFIG',
    'SHARDING_CONFIG',
    'CROSS_SHARD_CONFIG',
    'FAILOVER_CONFIG',
    'LOAD_BALANCING_CONFIG',
    'CONNECTION_CONFIG',
    'MONITORING_CONFIG',
    'PERFORMANCE_CONFIG',
    'SECURITY_CONFIG',
    'DATABASE_TYPE_CONFIGS',
    'SHARD_TEMPLATES',
    'QUERY_TEMPLATES',
    'get_sharding_config',
    'validate_sharding_config'
]
