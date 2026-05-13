"""
Distributed Cache Configuration

Configuration settings for Redis integration, cluster management, cache synchronization,
and failover handling for distributed caching.
"""

import os
from datetime import timedelta

# Distributed Cache Configuration
DISTRIBUTED_CACHE_ENABLED = True
REDIS_INTEGRATION_ENABLED = True
CLUSTER_MANAGEMENT_ENABLED = True
CACHE_SYNCHRONIZATION_ENABLED = True
FAILOVER_ENABLED = True

# Redis Configuration
REDIS_CONFIG = {
    'host': 'localhost',
    'port': 6379,
    'db': 0,
    'password': None,
    'socket_timeout': 30,
    'socket_connect_timeout': 30,
    'retry_on_timeout': True,
    'max_connections': 100,
    'health_check_interval': 30,
    'decode_responses': True,
    'ssl': False,
    'ssl_cert_reqs': None,
    'ssl_ca_certs': None,
    'ssl_ca_data': None,
    'ssl_certfile': None,
    'ssl_keyfile': None
}

# Cluster Configuration
CLUSTER_CONFIG = {
    'enabled': True,
    'discovery_method': 'config',  # config, sentinel, dns
    'startup_nodes': [
        {'host': 'localhost', 'port': 7000},
        {'host': 'localhost', 'port': 7001},
        {'host': 'localhost', 'port': 7002}
    ],
    'max_connections': 100,
    'skip_full_coverage_check': True,
    'read_from_replicas': True,
    'replica_ratio': 0.1,
    'cluster_down_retry_attempts': 3,
    'cluster_down_retry_delay': 1,
    'require_full_coverage': False,
    'reconnect_on_failure': True,
    'max_connections_per_node': 32
}

# Sentinel Configuration
SENTINEL_CONFIG = {
    'enabled': False,
    'sentinels': [
        {'host': 'localhost', 'port': 26379},
        {'host': 'localhost', 'port': 26380},
        {'host': 'localhost', 'port': 26381}
    ],
    'service_name': 'mymaster',
    'socket_timeout': 30,
    'connect_timeout': 30,
    'retry_on_timeout': True,
    'max_connections': 100,
    'decode_responses': True
}

# Sharding Configuration
SHARDING_CONFIG = {
    'enabled': True,
    'strategy': 'hash_slot',  # hash_slot, consistent_hash, modulo, range, random
    'shard_count': 16384,
    'hash_function': 'crc16',
    'replication_factor': 1,
    'auto_rebalance': True,
    'rebalance_threshold': 0.2,  # 20% imbalance threshold
    'migrations_enabled': True,
    'migration_batch_size': 100,
    'migration_timeout': 300
}

# Replication Configuration
REPLICATION_CONFIG = {
    'enabled': True,
    'strategy': 'master_slave',  # master_slave, multi_master, read_write_split, eventual_consistency
    'replication_factor': 1,
    'sync_mode': 'async',  # sync, async
    'ack_timeout': 30,
    'retry_replication': True,
    'max_replication_attempts': 3,
    'replication_delay': 0.1,  # seconds
    'consistency_level': 'eventual',  # strong, eventual, weak
    'read_from_replicas': True,
    'write_to_master_only': True
}

# Synchronization Configuration
SYNCHRONIZATION_CONFIG = {
    'enabled': True,
    'auto_sync': True,
    'sync_interval': 300,  # 5 minutes
    'sync_batch_size': 1000,
    'sync_timeout': 300,
    'max_sync_attempts': 3,
    'sync_retry_delay': 60,
    'compression_enabled': True,
    'encryption_enabled': False,
    'sync_types': {
        'full': {'enabled': True, 'interval': 86400},  # Daily
        'incremental': {'enabled': True, 'interval': 300},  # 5 minutes
        'key_based': {'enabled': True, 'interval': 60}  # 1 minute
    },
    'filter_patterns': ['*', 'cache:*', 'session:*'],
    'exclude_patterns': ['temp:*', 'lock:*'],
    'priority_keys': ['user:*', 'config:*', 'system:*']
}

# Failover Configuration
FAILOVER_CONFIG = {
    'enabled': True,
    'auto_failover': True,
    'failover_timeout': 30,
    'max_failover_attempts': 3,
    'health_check_interval': 10,  # seconds
    'node_timeout': 5,  # seconds
    'quorum_size': 2,
    'parallel_syncs': True,
    'failover_strategy': 'promote_slave',  # promote_slave, add_node, restart_cluster
    'recovery_strategy': 'automatic',  # automatic, manual
    'downtime_threshold': 30,  # seconds
    'data_loss_threshold': 0.01,  # 1% data loss threshold
    'notification_enabled': True,
    'notification_channels': ['email', 'slack']
}

# Cache Configuration
CACHE_CONFIG = {
    'default_ttl': 3600,  # 1 hour
    'max_ttl': 86400 * 30,  # 30 days
    'min_ttl': 60,  # 1 minute
    'compression_threshold': 1024,  # 1KB
    'compression_algorithm': 'gzip',
    'serialization_format': 'json',
    'key_prefix': 'forum:',
    'key_separator': ':',
    'max_key_length': 250,
    'max_value_size': 1048576,  # 1MB
    'eviction_policy': 'allkeys-lru',
    'max_memory_policy': 'volatile-lru',
    'lazy_expire': True
}

# Performance Configuration
PERFORMANCE_CONFIG = {
    'connection_pooling': {
        'enabled': True,
        'max_connections': 100,
        'max_connections_per_node': 32,
        'connection_timeout': 30,
        'idle_timeout': 300,
        'health_check_interval': 30
    },
    'pipelining': {
        'enabled': True,
        'max_pipeline_size': 100,
        'pipeline_timeout': 10
    },
    'batching': {
        'enabled': True,
        'batch_size': 100,
        'batch_timeout': 5
    },
    'caching': {
        'enabled': True,
        'local_cache_size': 1000,
        'local_cache_ttl': 60
    },
    'monitoring': {
        'enabled': True,
        'metrics_interval': 10,
        'performance_logging': True,
        'slow_query_threshold': 1000  # milliseconds
    }
}

# Security Configuration
SECURITY_CONFIG = {
    'authentication': {
        'enabled': False,
        'username': None,
        'password': None
    },
    'encryption': {
        'enabled': False,
        'algorithm': 'AES-256',
        'key': None,
        'iv': None
    },
    'access_control': {
        'enabled': True,
        'allowed_commands': ['GET', 'SET', 'DELETE', 'EXISTS', 'TTL', 'EXPIRE'],
        'blocked_commands': ['FLUSHALL', 'FLUSHDB', 'CONFIG', 'SHUTDOWN'],
        'key_pattern_access': {
            'read': ['*', 'cache:*', 'session:*'],
            'write': ['cache:*', 'session:*'],
            'admin': ['system:*', 'config:*']
        }
    },
    'audit_logging': {
        'enabled': True,
        'log_all_commands': False,
        'log_sensitive_commands': True,
        'sensitive_patterns': ['password', 'secret', 'token', 'key']
    }
}

# Monitoring Configuration
MONITORING_CONFIG = {
    'enabled': True,
    'metrics_collection': {
        'enabled': True,
        'interval': 10,  # seconds
        'retention_days': 7,
        'metrics': [
            'memory_usage',
            'hit_rate',
            'response_time',
            'error_rate',
            'connection_count',
            'operations_per_second'
        ]
    },
    'health_checks': {
        'enabled': True,
        'interval': 30,  # seconds
        'timeout': 5,  # seconds
        'checks': [
            'connection',
            'memory',
            'disk',
            'replication',
            'cluster'
        ]
    },
    'alerts': {
        'enabled': True,
        'thresholds': {
            'memory_usage': 0.9,  # 90%
            'hit_rate': 0.8,  # 80%
            'response_time': 1000,  # 1 second
            'error_rate': 0.05,  # 5%
            'connection_count': 80  # 80% of max connections
        },
        'channels': ['email', 'slack'],
        'cooldown': 300  # 5 minutes
    },
    'dashboard': {
        'enabled': True,
        'refresh_interval': 30,  # seconds
        'max_data_points': 1000
    }
}

# Backup Configuration
BACKUP_CONFIG = {
    'enabled': True,
    'backup_interval': 86400,  # Daily
    'retention_days': 30,
    'compression': True,
    'encryption': False,
    'backup_types': {
        'rdb': {'enabled': True, 'interval': 86400},
        'aof': {'enabled': True, 'interval': 3600},
        'full': {'enabled': True, 'interval': 604800}  # Weekly
    },
    'storage': {
        'local': {
            'enabled': True,
            'path': '/backups/redis'
        },
        's3': {
            'enabled': False,
            'bucket': 'redis-backups',
            'region': 'us-east-1'
        }
    },
    'verification': {
        'enabled': True,
        'verify_backups': True,
        'restore_test': False
    }
}

# Development Configuration
if os.getenv('FLASK_ENV') == 'development':
    DISTRIBUTED_CACHE_ENABLED = True
    REDIS_INTEGRATION_ENABLED = True
    CLUSTER_MANAGEMENT_ENABLED = False  # Single Redis instance
    CACHE_SYNCHRONIZATION_ENABLED = False
    FAILOVER_ENABLED = False
    
    REDIS_CONFIG = {
        'host': 'localhost',
        'port': 6379,
        'db': 0,
        'max_connections': 10
    }
    
    CLUSTER_CONFIG['enabled'] = False
    SHARDING_CONFIG['enabled'] = False
    REPLICATION_CONFIG['replication_factor'] = 0
    
    MONITORING_CONFIG['metrics_collection']['interval'] = 60
    MONITORING_CONFIG['health_checks']['interval'] = 60
    BACKUP_CONFIG['enabled'] = False

# Production Configuration
if os.getenv('FLASK_ENV') == 'production':
    DISTRIBUTED_CACHE_ENABLED = True
    REDIS_INTEGRATION_ENABLED = True
    CLUSTER_MANAGEMENT_ENABLED = True
    CACHE_SYNCHRONIZATION_ENABLED = True
    FAILOVER_ENABLED = True
    
    REDIS_CONFIG = {
        'host': os.getenv('REDIS_HOST', 'redis-cluster'),
        'port': int(os.getenv('REDIS_PORT', 6379)),
        'password': os.getenv('REDIS_PASSWORD'),
        'max_connections': 1000,
        'socket_timeout': 30,
        'socket_connect_timeout': 30
    }
    
    CLUSTER_CONFIG = {
        'enabled': True,
        'startup_nodes': [
            {'host': os.getenv('REDIS_NODE1_HOST', 'redis-node1'), 'port': int(os.getenv('REDIS_NODE1_PORT', 7000))},
            {'host': os.getenv('REDIS_NODE2_HOST', 'redis-node2'), 'port': int(os.getenv('REDIS_NODE2_PORT', 7001))},
            {'host': os.getenv('REDIS_NODE3_HOST', 'redis-node3'), 'port': int(os.getenv('REDIS_NODE3_PORT', 7002))}
        ],
        'max_connections': 1000
    }
    
    SHARDING_CONFIG['replication_factor'] = 1
    REPLICATION_CONFIG['replication_factor'] = 1
    
    MONITORING_CONFIG['metrics_collection']['interval'] = 10
    MONITORING_CONFIG['health_checks']['interval'] = 30
    BACKUP_CONFIG['enabled'] = True

# Testing Configuration
if os.getenv('FLASK_ENV') == 'testing':
    DISTRIBUTED_CACHE_ENABLED = False
    REDIS_INTEGRATION_ENABLED = False
    CLUSTER_MANAGEMENT_ENABLED = False
    CACHE_SYNCHRONIZATION_ENABLED = False
    FAILOVER_ENABLED = False
    
    MONITORING_CONFIG['enabled'] = False
    BACKUP_CONFIG['enabled'] = False

# Environment Variables
ENVIRONMENT_VARIABLES = {
    'DISTRIBUTED_CACHE_ENABLED': os.getenv('DISTRIBUTED_CACHE_ENABLED', 'True'),
    'REDIS_HOST': os.getenv('REDIS_HOST', 'localhost'),
    'REDIS_PORT': os.getenv('REDIS_PORT', '6379'),
    'REDIS_PASSWORD': os.getenv('REDIS_PASSWORD'),
    'REDIS_DB': os.getenv('REDIS_DB', '0'),
    'REDIS_CLUSTER_ENABLED': os.getenv('REDIS_CLUSTER_ENABLED', 'False'),
    'REDIS_SENTINEL_ENABLED': os.getenv('REDIS_SENTINEL_ENABLED', 'False'),
    'REDIS_SENTINEL_SERVICE_NAME': os.getenv('REDIS_SENTINEL_SERVICE_NAME', 'mymaster'),
    'REDIS_MAX_CONNECTIONS': os.getenv('REDIS_MAX_CONNECTIONS', '100'),
    'REDIS_SOCKET_TIMEOUT': os.getenv('REDIS_SOCKET_TIMEOUT', '30'),
    'CACHE_DEFAULT_TTL': os.getenv('CACHE_DEFAULT_TTL', '3600'),
    'CACHE_KEY_PREFIX': os.getenv('CACHE_KEY_PREFIX', 'forum:'),
    'CACHE_MAX_MEMORY': os.getenv('CACHE_MAX_MEMORY', '256mb'),
    'CACHE_EVICTION_POLICY': os.getenv('CACHE_EVICTION_POLICY', 'allkeys-lru')
}

# Key Patterns
CACHE_KEY_PATTERNS = {
    'user': 'user:{user_id}',
    'session': 'session:{session_id}',
    'cache': 'cache:{key}',
    'config': 'config:{key}',
    'system': 'system:{key}',
    'temp': 'temp:{key}',
    'lock': 'lock:{key}',
    'rate_limit': 'rate_limit:{identifier}',
    'analytics': 'analytics:{type}:{id}',
    'search': 'search:{query_hash}',
    'notification': 'notification:{user_id}',
    'permission': 'permission:{user_id}:{resource}',
    'audit': 'audit:{audit_id}'
}

# TTL Configuration
CACHE_TTL_CONFIG = {
    'short': 60,  # 1 minute
    'medium': 300,  # 5 minutes
    'long': 3600,  # 1 hour
    'extended': 86400,  # 1 day
    'session': 1800,  # 30 minutes
    'user_cache': 3600,  # 1 hour
    'config_cache': 86400,  # 1 day
    'temp_cache': 300,  # 5 minutes
    'lock_cache': 30,  # 30 seconds
    'rate_limit': 3600,  # 1 hour
    'analytics_cache': 300,  # 5 minutes
    'search_cache': 1800,  # 30 minutes
    'notification_cache': 86400,  # 1 day
    'permission_cache': 3600,  # 1 hour
    'audit_cache': 86400  # 1 day
}

# Validation Functions
def validate_distributed_cache_config():
    """Validate distributed cache configuration"""
    errors = []
    
    # Check required environment variables
    if CLUSTER_CONFIG['enabled']:
        if not CLUSTER_CONFIG['startup_nodes']:
            errors.append("Cluster startup nodes not configured")
    
    if SENTINEL_CONFIG['enabled']:
        if not SENTINEL_CONFIG['sentinels']:
            errors.append("Sentinel servers not configured")
    
    # Check configuration consistency
    if SHARDING_CONFIG['replication_factor'] < 0:
        errors.append("Replication factor must be non-negative")
    
    if REPLICATION_CONFIG['replication_factor'] < 0:
        errors.append("Replication factor must be non-negative")
    
    # Check Redis connection settings
    if REDIS_CONFIG['port'] < 1 or REDIS_CONFIG['port'] > 65535:
        errors.append("Invalid Redis port number")
    
    if REDIS_CONFIG['max_connections'] < 1:
        errors.append("Max connections must be positive")
    
    return errors

def get_distributed_cache_config():
    """Get complete distributed cache configuration"""
    return {
        'distributed_cache_enabled': DISTRIBUTED_CACHE_ENABLED,
        'redis_integration_enabled': REDIS_INTEGRATION_ENABLED,
        'cluster_management_enabled': CLUSTER_MANAGEMENT_ENABLED,
        'cache_synchronization_enabled': CACHE_SYNCHRONIZATION_ENABLED,
        'failover_enabled': FAILOVER_ENABLED,
        'redis_config': REDIS_CONFIG,
        'cluster_config': CLUSTER_CONFIG,
        'sentinel_config': SENTINEL_CONFIG,
        'sharding_config': SHARDING_CONFIG,
        'replication_config': REPLICATION_CONFIG,
        'synchronization_config': SYNCHRONIZATION_CONFIG,
        'failover_config': FAILOVER_CONFIG,
        'cache_config': CACHE_CONFIG,
        'performance_config': PERFORMANCE_CONFIG,
        'security_config': SECURITY_CONFIG,
        'monitoring_config': MONITORING_CONFIG,
        'backup_config': BACKUP_CONFIG,
        'cache_key_patterns': CACHE_KEY_PATTERNS,
        'cache_ttl_config': CACHE_TTL_CONFIG
    }


# Default configurations for different deployment types
DEFAULT_CONFIGS = {
    'standalone': {
        'cluster_config': {'enabled': False},
        'sharding_config': {'enabled': False},
        'replication_config': {'replication_factor': 0},
        'failover_config': {'enabled': False}
    },
    'cluster': {
        'cluster_config': {'enabled': True},
        'sharding_config': {'enabled': True},
        'replication_config': {'replication_factor': 1},
        'failover_config': {'enabled': True}
    },
    'sentinel': {
        'sentinel_config': {'enabled': True},
        'replication_config': {'replication_factor': 1},
        'failover_config': {'enabled': True}
    },
    'multi_master': {
        'replication_config': {'strategy': 'multi_master'},
        'failover_config': {'enabled': True}
    }
}
