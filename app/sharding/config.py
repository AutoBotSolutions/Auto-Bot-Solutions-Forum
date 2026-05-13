"""
Database Sharding Configuration

Configuration settings for database sharding, shard management, cross-shard queries,
shard failover, and load balancing.
"""

import os
from datetime import timedelta

# Database Sharding Configuration
DATABASE_SHARDING_ENABLED = True
CROSS_SHARD_QUERIES_ENABLED = True
SHARD_FAILOVER_ENABLED = True
LOAD_BALANCING_ENABLED = True
SHARD_MONITORING_ENABLED = True

# Cluster Configuration
CLUSTER_CONFIG = {
    'enabled': True,
    'default_sharding_strategy': 'hash',
    'default_shard_count': 4,
    'auto_shard_creation': True,
    'auto_shard_rebalancing': True,
    'health_check_interval': 300,  # 5 minutes
    'metrics_collection_interval': 60,  # 1 minute
    'max_clusters': 10,
    'max_shards_per_cluster': 32
}

# Sharding Configuration
SHARDING_CONFIG = {
    'enabled': True,
    'strategies': {
        'hash': {
            'enabled': True,
            'algorithm': 'md5',
            'seed': 12345
        },
        'range': {
            'enabled': True,
            'auto_range_detection': True,
            'range_size': 1000
        },
        'directory': {
            'enabled': True,
            'cache_size': 10000,
            'cache_ttl': 3600  # 1 hour
        },
        'consistent_hash': {
            'enabled': True,
            'virtual_nodes': 150,
            'replication_factor': 1
        }
    },
    'shard_key_fields': {
        'user': ['user_id'],
        'content': ['content_id'],
        'forum': ['forum_id'],
        'analytics': ['timestamp', 'user_id']
    },
    'rebalancing': {
        'enabled': True,
        'threshold': 0.2,  # 20% imbalance threshold
        'auto_rebalance': True,
        'rebalance_interval': 86400  # 24 hours
    }
}

# Cross-Shard Query Configuration
CROSS_SHARD_CONFIG = {
    'enabled': True,
    'max_concurrent_queries': 100,
    'query_timeout': 300,  # 5 minutes
    'max_shards_per_query': 32,
    'result_aggregation': {
        'enabled': True,
        'max_result_size': 1000000,  # 1M records
        'aggregation_timeout': 60  # 1 minute
    },
    'execution_strategies': {
        'parallel': {
            'enabled': True,
            'max_threads': 10,
            'thread_timeout': 300
        },
        'sequential': {
            'enabled': True,
            'shard_timeout': 60
        },
        'hybrid': {
            'enabled': True,
            'parallel_threshold': 4,
            'max_parallel_shards': 8
        }
    },
    'optimization': {
        'enabled': True,
        'query_caching': True,
        'plan_caching': True,
        'result_caching': True,
        'cache_ttl': 300  # 5 minutes
    },
    'shard_selection': {
        'intelligent_selection': True,
        'performance_based_routing': True,
        'load_aware_routing': True
    }
}

# Failover Configuration
FAILOVER_CONFIG = {
    'enabled': True,
    'auto_failover': True,
    'failover_detection': {
        'enabled': True,
        'health_check_interval': 30,  # 30 seconds
        'failure_threshold': 3,  # 3 consecutive failures
        'recovery_threshold': 2  # 2 consecutive successes
    },
    'strategies': {
        'automatic': {
            'enabled': True,
            'selection_criteria': 'priority',  # priority, load, performance
            'promotion_delay': 5,  # seconds
            'demote_failed': True
        },
        'manual': {
            'enabled': True,
            'require_approval': True,
            'approval_timeout': 300  # 5 minutes
        },
        'scheduled': {
            'enabled': True,
            'maintenance_window': '02:00-04:00',
            'notification_required': True
        }
    },
    'recovery': {
        'enabled': True,
        'auto_recovery': True,
        'recovery_attempts': 3,
        'recovery_delay': 60,  # 1 minute
        'health_verification': True
    },
    'notification': {
        'enabled': True,
        'channels': ['email', 'slack', 'webhook'],
        'severity_levels': {
            'critical': ['email', 'slack', 'webhook'],
            'warning': ['email', 'slack'],
            'info': ['email']
        }
    }
}

# Load Balancing Configuration
LOAD_BALANCING_CONFIG = {
    'enabled': True,
    'default_strategy': 'round_robin',
    'strategies': {
        'round_robin': {
            'enabled': True,
            'description': 'Round-robin load balancing'
        },
        'least_connections': {
            'enabled': True,
            'description': 'Route to shard with least active connections'
        },
        'weighted': {
            'enabled': True,
            'description': 'Weighted load balancing based on shard weight'
        },
        'performance_based': {
            'enabled': True,
            'description': 'Route to shard with best performance metrics'
        },
        'geographic': {
            'enabled': False,
            'description': 'Route to geographically closest shard'
        }
    },
    'health_aware_routing': {
        'enabled': True,
        'exclude_unhealthy': True,
        'prefer_healthy': True,
        'health_weight_factor': 0.8
    },
    'connection_pooling': {
        'enabled': True,
        'min_connections_per_shard': 1,
        'max_connections_per_shard': 10,
        'connection_timeout': 30,
        'idle_timeout': 300,
        'max_lifetime': 3600  # 1 hour
    }
}

# Connection Configuration
CONNECTION_CONFIG = {
    'enabled': True,
    'default_timeout': 30,
    'max_retries': 3,
    'retry_delay': 1,  # seconds
    'connection_pooling': {
        'enabled': True,
        'pool_size': 10,
        'max_overflow': 20,
        'pool_timeout': 30,
        'pool_recycle': 3600
    },
    'ssl': {
        'enabled': False,
        'cert_file': None,
        'key_file': None,
        'ca_file': None,
        'verify_cert': True
    },
    'authentication': {
        'enabled': True,
        'method': 'password',  # password, cert, kerberos
        'encryption': True,
        'key_rotation_days': 90
    }
}

# Monitoring Configuration
MONITORING_CONFIG = {
    'enabled': True,
    'metrics_collection': {
        'enabled': True,
        'interval': 60,  # seconds
        'retention_days': 30,
        'metrics': [
            'connection_count',
            'query_performance',
            'shard_health',
            'failover_events',
            'load_balancing_stats'
        ]
    },
    'health_checks': {
        'enabled': True,
        'interval': 300,  # 5 minutes
        'timeout': 30,  # seconds
        'checks': [
            'database_connection',
            'shard_availability',
            'performance_metrics',
            'replication_status'
        ]
    },
    'alerts': {
        'enabled': True,
        'thresholds': {
            'shard_down': 1,  # Any shard down
            'connection_pool_exhaustion': 0.9,  # 90% pool usage
            'query_time': 5000,  # 5 seconds
            'error_rate': 0.05,  # 5% error rate
            'replication_lag': 300  # 5 minutes
        },
        'channels': ['email', 'slack'],
        'cooldown': 300  # 5 minutes
    },
    'dashboard': {
        'enabled': True,
        'refresh_interval': 300,  # 5 minutes
        'max_data_points': 1000,
        'chart_types': ['line', 'bar', 'pie', 'gauge', 'heatmap']
    }
}

# Performance Configuration
PERFORMANCE_CONFIG = {
    'query_optimization': {
        'enabled': True,
        'query_caching': True,
        'plan_caching': True,
        'result_caching': True,
        'cache_size': 1000,
        'cache_ttl': 300  # 5 minutes
    },
    'parallel_processing': {
        'enabled': True,
        'max_workers': 10,
        'worker_timeout': 300,
        'task_queue_size': 1000
    },
    'batch_operations': {
        'enabled': True,
        'batch_size': 1000,
        'flush_interval': 5000  # 5 seconds
    },
    'compression': {
        'enabled': True,
        'algorithm': 'gzip',
        'compression_level': 6,
        'min_size': 1024  # 1KB
    }
}

# Security Configuration
SECURITY_CONFIG = {
    'authentication': {
        'enabled': True,
        'method': 'database',  # database, ldap, oauth
        'session_timeout': 3600,  # 1 hour
        'max_login_attempts': 5
    },
    'authorization': {
        'enabled': True,
        'rbac_enabled': True,
        'default_role': 'viewer',
        'roles': {
            'admin': ['read', 'write', 'delete', 'manage'],
            'operator': ['read', 'write'],
            'viewer': ['read']
        }
    },
    'encryption': {
        'enabled': True,
        'algorithm': 'aes256',
        'key_rotation_days': 90,
        'encrypt_at_rest': True,
        'encrypt_in_transit': True
    },
    'audit_logging': {
        'enabled': True,
        'log_all_queries': False,
        'log_sensitive_operations': True,
        'retention_days': 365
    }
}

# Development Configuration
if os.getenv('FLASK_ENV') == 'development':
    DATABASE_SHARDING_ENABLED = True
    CROSS_SHARD_QUERIES_ENABLED = True
    SHARD_FAILOVER_ENABLED = False
    LOAD_BALANCING_ENABLED = False
    SHARD_MONITORING_ENABLED = False
    
    CLUSTER_CONFIG['default_shard_count'] = 2
    SHARDING_CONFIG['rebalancing']['enabled'] = False
    CROSS_SHARD_CONFIG['max_concurrent_queries'] = 10
    FAILOVER_CONFIG['auto_failover'] = False
    LOAD_BALANCING_CONFIG['connection_pooling']['max_connections_per_shard'] = 5
    
    MONITORING_CONFIG['enabled'] = False
    PERFORMANCE_CONFIG['query_optimization']['enabled'] = False

# Production Configuration
if os.getenv('FLASK_ENV') == 'production':
    DATABASE_SHARDING_ENABLED = True
    CROSS_SHARD_QUERIES_ENABLED = True
    SHARD_FAILOVER_ENABLED = True
    LOAD_BALANCING_ENABLED = True
    SHARD_MONITORING_ENABLED = True
    
    CLUSTER_CONFIG['default_shard_count'] = 4
    SHARDING_CONFIG['rebalancing']['enabled'] = True
    CROSS_SHARD_CONFIG['max_concurrent_queries'] = 100
    FAILOVER_CONFIG['auto_failover'] = True
    LOAD_BALANCING_CONFIG['connection_pooling']['max_connections_per_shard'] = 20
    
    MONITORING_CONFIG['enabled'] = True
    PERFORMANCE_CONFIG['query_optimization']['enabled'] = True

# Testing Configuration
if os.getenv('FLASK_ENV') == 'testing':
    DATABASE_SHARDING_ENABLED = False
    CROSS_SHARD_QUERIES_ENABLED = False
    SHARD_FAILOVER_ENABLED = False
    LOAD_BALANCING_ENABLED = False
    SHARD_MONITORING_ENABLED = False
    
    MONITORING_CONFIG['enabled'] = False
    PERFORMANCE_CONFIG['query_optimization']['enabled'] = False

# Environment Variables
ENVIRONMENT_VARIABLES = {
    'DATABASE_SHARDING_ENABLED': os.getenv('DATABASE_SHARDING_ENABLED', 'True'),
    'CROSS_SHARD_QUERIES_ENABLED': os.getenv('CROSS_SHARD_QUERIES_ENABLED', 'True'),
    'SHARD_FAILOVER_ENABLED': os.getenv('SHARD_FAILOVER_ENABLED', 'True'),
    'LOAD_BALANCING_ENABLED': os.getenv('LOAD_BALANCING_ENABLED', 'True'),
    'SHARD_MONITORING_ENABLED': os.getenv('SHARD_MONITORING_ENABLED', 'True'),
    'DEFAULT_SHARD_COUNT': os.getenv('DEFAULT_SHARD_COUNT', '4'),
    'SHARDING_STRATEGY': os.getenv('SHARDING_STRATEGY', 'hash'),
    'MAX_CONCURRENT_QUERIES': os.getenv('MAX_CONCURRENT_QUERIES', '100'),
    'QUERY_TIMEOUT': os.getenv('QUERY_TIMEOUT', '300'),
    'HEALTH_CHECK_INTERVAL': os.getenv('HEALTH_CHECK_INTERVAL', '300'),
    'FAILOVER_DETECTION_ENABLED': os.getenv('FAILOVER_DETECTION_ENABLED', 'True'),
    'LOAD_BALANCING_STRATEGY': os.getenv('LOAD_BALANCING_STRATEGY', 'round_robin'),
    'CONNECTION_POOL_SIZE': os.getenv('CONNECTION_POOL_SIZE', '10'),
    'SSL_ENABLED': os.getenv('SSL_ENABLED', 'False'),
    'SSL_CERT_FILE': os.getenv('SSL_CERT_FILE'),
    'SSL_KEY_FILE': os.getenv('SSL_KEY_FILE'),
    'SSL_CA_FILE': os.getenv('SSL_CA_FILE')
}

# Database Type Configurations
DATABASE_TYPE_CONFIGS = {
    'mysql': {
        'driver': 'mysql',
        'default_port': 3306,
        'connection_string_format': 'mysql://{username}:{password}@{host}:{port}/{database}',
        'ssl_options': {
            'ssl_ca': None,
            'ssl_cert': None,
            'ssl_key': None,
            'ssl_verify_cert': True
        },
        'pool_options': {
            'pool_size': 10,
            'max_overflow': 20,
            'pool_timeout': 30,
            'pool_recycle': 3600
        }
    },
    'postgresql': {
        'driver': 'postgresql',
        'default_port': 5432,
        'connection_string_format': 'postgresql://{username}:{password}@{host}:{port}/{database}',
        'ssl_options': {
            'sslmode': 'require',
            'sslcert': None,
            'sslkey': None,
            'sslrootcert': None
        },
        'pool_options': {
            'pool_size': 10,
            'max_overflow': 20,
            'pool_timeout': 30,
            'pool_recycle': 3600
        }
    },
    'mongodb': {
        'driver': 'mongodb',
        'default_port': 27017,
        'connection_string_format': 'mongodb://{username}:{password}@{host}:{port}/{database}',
        'ssl_options': {
            'ssl': False,
            'ssl_cert_file': None,
            'ssl_key_file': None,
            'ssl_ca_file': None
        },
        'pool_options': {
            'maxPoolSize': 10,
            'minPoolSize': 1,
            'maxIdleTimeMS': 30000,
            'serverSelectionTimeoutMS': 30000
        }
    }
}

# Shard Templates
SHARD_TEMPLATES = {
    'user_shard': {
        'shard_key': 'user_id',
        'sharding_strategy': 'hash',
        'database_type': 'mysql',
        'table_prefix': 'user',
        'indexes': ['user_id', 'username', 'email', 'created_at'],
        'replication': {
            'enabled': True,
            'factor': 1
        }
    },
    'content_shard': {
        'shard_key': 'content_id',
        'sharding_strategy': 'hash',
        'database_type': 'mysql',
        'table_prefix': 'content',
        'indexes': ['content_id', 'title', 'author_id', 'created_at'],
        'replication': {
            'enabled': True,
            'factor': 1
        }
    },
    'forum_shard': {
        'shard_key': 'forum_id',
        'sharding_strategy': 'range',
        'database_type': 'mysql',
        'table_prefix': 'forum',
        'indexes': ['forum_id', 'title', 'created_at', 'updated_at'],
        'replication': {
            'enabled': True,
            'factor': 1
        }
    },
    'analytics_shard': {
        'shard_key': 'timestamp',
        'sharding_strategy': 'range',
        'database_type': 'postgresql',
        'table_prefix': 'analytics',
        'indexes': ['timestamp', 'user_id', 'event_type'],
        'replication': {
            'enabled': False,
            'factor': 0
        }
    }
}

# Query Templates
QUERY_TEMPLATES = {
    'user_lookup': {
        'type': 'select',
        'sharding_strategy': 'hash',
        'target_shards': 'single',
        'template': 'SELECT * FROM users WHERE user_id = {user_id}'
    },
    'content_search': {
        'type': 'select',
        'sharding_strategy': 'all',
        'target_shards': 'all',
        'template': 'SELECT * FROM content WHERE title LIKE {search_term} ORDER BY created_at DESC LIMIT {limit}'
    },
    'user_analytics': {
        'type': 'select',
        'sharding_strategy': 'hash',
        'target_shards': 'single',
        'template': 'SELECT COUNT(*) FROM analytics WHERE user_id = {user_id} AND timestamp BETWEEN {start_date} AND {end_date}'
    },
    'cross_shard_aggregation': {
        'type': 'select',
        'sharding_strategy': 'all',
        'target_shards': 'all',
        'template': 'SELECT COUNT(*) as total, SUM(value) as total_value FROM metrics WHERE timestamp BETWEEN {start_date} AND {end_date}'
    }
}

# Validation Functions
def validate_sharding_config():
    """Validate sharding configuration"""
    errors = []
    
    # Check cluster configuration
    if CLUSTER_CONFIG['default_shard_count'] < 1:
        errors.append("Default shard count must be at least 1")
    
    if CLUSTER_CONFIG['max_shards_per_cluster'] < 1:
        errors.append("Max shards per cluster must be at least 1")
    
    # Check cross-shard configuration
    if CROSS_SHARD_CONFIG['max_concurrent_queries'] < 1:
        errors.append("Max concurrent queries must be at least 1")
    
    if CROSS_SHARD_CONFIG['max_shards_per_query'] < 1:
        errors.append("Max shards per query must be at least 1")
    
    if CROSS_SHARD_CONFIG['query_timeout'] < 1:
        errors.append("Query timeout must be at least 1 second")
    
    # Check failover configuration
    if FAILOVER_CONFIG['failover_detection']['failure_threshold'] < 1:
        errors.append("Failure threshold must be at least 1")
    
    if FAILOVER_CONFIG['recovery']['recovery_attempts'] < 1:
        errors.append("Recovery attempts must be at least 1")
    
    # Check load balancing configuration
    if LOAD_BALANCING_CONFIG['connection_pooling']['min_connections_per_shard'] < 0:
        errors.append("Min connections per shard must be non-negative")
    
    if LOAD_BALANCING_CONFIG['connection_pooling']['max_connections_per_shard'] < 1:
        errors.append("Max connections per shard must be at least 1")
    
    return errors

def get_sharding_config():
    """Get complete sharding configuration"""
    return {
        'database_sharding_enabled': DATABASE_SHARDING_ENABLED,
        'cross_shard_queries_enabled': CROSS_SHARD_QUERIES_ENABLED,
        'shard_failover_enabled': SHARD_FAILOVER_ENABLED,
        'load_balancing_enabled': LOAD_BALANCING_ENABLED,
        'shard_monitoring_enabled': SHARD_MONITORING_ENABLED,
        'cluster_config': CLUSTER_CONFIG,
        'sharding_config': SHARDING_CONFIG,
        'cross_shard_config': CROSS_SHARD_CONFIG,
        'failover_config': FAILOVER_CONFIG,
        'load_balancing_config': LOAD_BALANCING_CONFIG,
        'connection_config': CONNECTION_CONFIG,
        'monitoring_config': MONITORING_CONFIG,
        'performance_config': PERFORMANCE_CONFIG,
        'security_config': SECURITY_CONFIG,
        'database_type_configs': DATABASE_TYPE_CONFIGS,
        'shard_templates': SHARD_TEMPLATES,
        'query_templates': QUERY_TEMPLATES
    }


# Default configurations for different deployment types
DEFAULT_CONFIGS = {
    'small': {
        'cluster_config': {'default_shard_count': 2, 'max_shards_per_cluster': 4},
        'cross_shard_config': {'max_concurrent_queries': 10, 'max_shards_per_query': 4},
        'load_balancing_config': {'connection_pooling': {'max_connections_per_shard': 5}}
    },
    'medium': {
        'cluster_config': {'default_shard_count': 4, 'max_shards_per_cluster': 8},
        'cross_shard_config': {'max_concurrent_queries': 50, 'max_shards_per_query': 16},
        'load_balancing_config': {'connection_pooling': {'max_connections_per_shard': 10}}
    },
    'large': {
        'cluster_config': {'default_shard_count': 8, 'max_shards_per_cluster': 32},
        'cross_shard_config': {'max_concurrent_queries': 100, 'max_shards_per_query': 32},
        'load_balancing_config': {'connection_pooling': {'max_connections_per_shard': 20}}
    }
}
