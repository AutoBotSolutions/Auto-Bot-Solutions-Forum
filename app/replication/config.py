"""
Data Replication Configuration

Configuration settings for data replication, master-slave replication,
multi-master replication, replication monitoring, and conflict resolution.
"""

import os
from datetime import timedelta

# Data Replication Configuration
DATA_REPLICATION_ENABLED = True
MASTER_SLAVE_REPLICATION_ENABLED = True
MULTI_MASTER_REPLICATION_ENABLED = True
CONFLICT_RESOLUTION_ENABLED = True
REPLICATION_MONITORING_ENABLED = True

# Cluster Configuration
CLUSTER_CONFIG = {
    'enabled': True,
    'default_cluster_type': 'master_slave',
    'default_replication_mode': 'asynchronous',
    'default_consistency_level': 'eventual',
    'auto_cluster_creation': True,
    'health_check_interval': 300,  # 5 minutes
    'metrics_collection_interval': 60,  # 1 minute
    'max_clusters': 10,
    'max_nodes_per_cluster': 32
}

# Replication Configuration
REPLICATION_CONFIG = {
    'enabled': True,
    'modes': {
        'synchronous': {
            'enabled': True,
            'description': 'Synchronous replication with strong consistency',
            'latency_overhead': 2.0,  # 2x latency overhead
            'throughput_impact': 0.5  # 50% throughput reduction
        },
        'asynchronous': {
            'enabled': True,
            'description': 'Asynchronous replication with eventual consistency',
            'latency_overhead': 0.1,  # 10% latency overhead
            'throughput_impact': 0.1  # 10% throughput reduction
        },
        'semi_sync': {
            'enabled': True,
            'description': 'Semi-synchronous replication with balanced performance',
            'latency_overhead': 0.5,  # 50% latency overhead
            'throughput_impact': 0.3  # 30% throughput reduction
        }
    },
    'consistency_levels': {
        'strong': {
            'enabled': True,
            'description': 'Strong consistency across all nodes',
            'performance_impact': 0.6
        },
        'eventual': {
            'enabled': True,
            'description': 'Eventual consistency with high performance',
            'performance_impact': 0.1
        },
        'causal': {
            'enabled': True,
            'description': 'Causal consistency with moderate performance',
            'performance_impact': 0.3
        }
    },
    'cluster_types': {
        'master_slave': {
            'enabled': True,
            'description': 'Master-slave replication',
            'default_nodes': {'master': 1, 'slave': 2},
            'max_nodes': {'master': 1, 'slave': 31}
        },
        'multi_master': {
            'enabled': True,
            'description': 'Multi-master replication',
            'default_nodes': {'master': 3},
            'max_nodes': {'master': 32}
        },
        'hybrid': {
            'enabled': True,
            'description': 'Hybrid replication with mixed roles',
            'default_nodes': {'master': 2, 'slave': 2},
            'max_nodes': {'master': 16, 'slave': 16}
        }
    }
}

# Conflict Resolution Configuration
CONFLICT_RESOLUTION_CONFIG = {
    'enabled': True,
    'auto_resolution': True,
    'resolution_strategies': {
        'write_write': {
            'enabled': True,
            'strategy': 'timestamp',  # timestamp, priority, manual
            'description': 'Resolve write-write conflicts using timestamps'
        },
        'read_write': {
            'enabled': True,
            'strategy': 'write_priority',
            'description': 'Resolve read-write conflicts prioritizing writes'
        },
        'schema': {
            'enabled': True,
            'strategy': 'version',
            'description': 'Resolve schema conflicts using version numbers'
        },
        'data': {
            'enabled': True,
            'strategy': 'priority',
            'description': 'Resolve data conflicts using node priorities'
        }
    },
    'detection': {
        'enabled': True,
        'conflict_threshold': 1,  # Minimum conflicts to trigger resolution
        'detection_interval': 60,  # 1 minute
        'max_conflict_age': 3600  # 1 hour
    },
    'notification': {
        'enabled': True,
        'channels': ['email', 'slack'],
        'severity_levels': {
            'critical': ['email', 'slack'],
            'high': ['email', 'slack'],
            'medium': ['email'],
            'low': ['email']
        }
    }
}

# Failover Configuration
FAILOVER_CONFIG = {
    'enabled': True,
    'auto_failover': True,
    'detection': {
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
            'replication_lag',
            'throughput',
            'error_rate',
            'connection_count',
            'conflict_count',
            'node_health'
        ]
    },
    'health_checks': {
        'enabled': True,
        'interval': 300,  # 5 minutes
        'timeout': 30,  # seconds
        'checks': [
            'database_connection',
            'replication_status',
            'node_health',
            'conflict_resolution'
        ]
    },
    'alerts': {
        'enabled': True,
        'thresholds': {
            'replication_lag_ms': 1000,  # 1 second
            'error_rate': 0.05,  # 5%
            'connection_failures': 3,  # 3 consecutive failures
            'conflict_rate': 0.01,  # 1%
            'node_down': 1  # Any node down
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
    'optimization': {
        'enabled': True,
        'auto_optimization': True,
        'optimization_interval': 3600,  # 1 hour
        'optimization_strategies': {
            'minimize_lag': True,
            'maximize_throughput': True,
            'balance_load': True,
            'reduce_conflicts': True
        }
    },
    'caching': {
        'enabled': True,
        'cache_size': 1000,
        'cache_ttl': 300,  # 5 minutes
        'cache_types': ['query_results', 'replication_status', 'node_info']
    },
    'batch_operations': {
        'enabled': True,
        'batch_size': 1000,
        'flush_interval': 5000  # 5 seconds
    },
    'parallel_processing': {
        'enabled': True,
        'max_workers': 10,
        'worker_timeout': 300,
        'task_queue_size': 1000
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
        'log_all_operations': False,
        'log_conflicts': True,
        'log_failovers': True,
        'retention_days': 365
    }
}

# Development Configuration
if os.getenv('FLASK_ENV') == 'development':
    DATA_REPLICATION_ENABLED = True
    MASTER_SLAVE_REPLICATION_ENABLED = True
    MULTI_MASTER_REPLICATION_ENABLED = False
    CONFLICT_RESOLUTION_ENABLED = False
    REPLICATION_MONITORING_ENABLED = False
    
    CLUSTER_CONFIG['max_nodes_per_cluster'] = 4
    REPLICATION_CONFIG['modes']['synchronous']['enabled'] = False
    CONFLICT_RESOLUTION_CONFIG['auto_resolution'] = False
    FAILOVER_CONFIG['auto_failover'] = False
    
    MONITORING_CONFIG['enabled'] = False
    PERFORMANCE_CONFIG['optimization']['enabled'] = False

# Production Configuration
if os.getenv('FLASK_ENV') == 'production':
    DATA_REPLICATION_ENABLED = True
    MASTER_SLAVE_REPLICATION_ENABLED = True
    MULTI_MASTER_REPLICATION_ENABLED = True
    CONFLICT_RESOLUTION_ENABLED = True
    REPLICATION_MONITORING_ENABLED = True
    
    CLUSTER_CONFIG['max_nodes_per_cluster'] = 32
    REPLICATION_CONFIG['modes']['synchronous']['enabled'] = True
    CONFLICT_RESOLUTION_CONFIG['auto_resolution'] = True
    FAILOVER_CONFIG['auto_failover'] = True
    
    MONITORING_CONFIG['enabled'] = True
    PERFORMANCE_CONFIG['optimization']['enabled'] = True

# Testing Configuration
if os.getenv('FLASK_ENV') == 'testing':
    DATA_REPLICATION_ENABLED = False
    MASTER_SLAVE_REPLICATION_ENABLED = False
    MULTI_MASTER_REPLICATION_ENABLED = False
    CONFLICT_RESOLUTION_ENABLED = False
    REPLICATION_MONITORING_ENABLED = False
    
    MONITORING_CONFIG['enabled'] = False
    PERFORMANCE_CONFIG['optimization']['enabled'] = False

# Environment Variables
ENVIRONMENT_VARIABLES = {
    'DATA_REPLICATION_ENABLED': os.getenv('DATA_REPLICATION_ENABLED', 'True'),
    'MASTER_SLAVE_REPLICATION_ENABLED': os.getenv('MASTER_SLAVE_REPLICATION_ENABLED', 'True'),
    'MULTI_MASTER_REPLICATION_ENABLED': os.getenv('MULTI_MASTER_REPLICATION_ENABLED', 'True'),
    'CONFLICT_RESOLUTION_ENABLED': os.getenv('CONFLICT_RESOLUTION_ENABLED', 'True'),
    'REPLICATION_MONITORING_ENABLED': os.getenv('REPLICATION_MONITORING_ENABLED', 'True'),
    'DEFAULT_CLUSTER_TYPE': os.getenv('DEFAULT_CLUSTER_TYPE', 'master_slave'),
    'DEFAULT_REPLICATION_MODE': os.getenv('DEFAULT_REPLICATION_MODE', 'asynchronous'),
    'DEFAULT_CONSISTENCY_LEVEL': os.getenv('DEFAULT_CONSISTENCY_LEVEL', 'eventual'),
    'MAX_NODES_PER_CLUSTER': os.getenv('MAX_NODES_PER_CLUSTER', '32'),
    'HEALTH_CHECK_INTERVAL': os.getenv('HEALTH_CHECK_INTERVAL', '300'),
    'FAILOVER_DETECTION_ENABLED': os.getenv('FAILOVER_DETECTION_ENABLED', 'True'),
    'CONFLICT_AUTO_RESOLUTION': os.getenv('CONFLICT_AUTO_RESOLUTION', 'True'),
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
        'replication_support': True,
        'master_slave': True,
        'multi_master': True,
        'connection_string_format': 'mysql://{username}:{password}@{host}:{port}/{database}',
        'ssl_options': {
            'ssl_ca': None,
            'ssl_cert': None,
            'ssl_key': None,
            'ssl_verify_cert': True
        }
    },
    'postgresql': {
        'driver': 'postgresql',
        'default_port': 5432,
        'replication_support': True,
        'master_slave': True,
        'multi_master': True,
        'connection_string_format': 'postgresql://{username}:{password}@{host}:{port}/{database}',
        'ssl_options': {
            'sslmode': 'require',
            'sslcert': None,
            'sslkey': None,
            'sslrootcert': None
        }
    },
    'mongodb': {
        'driver': 'mongodb',
        'default_port': 27017,
        'replication_support': True,
        'master_slave': True,
        'multi_master': True,
        'connection_string_format': 'mongodb://{username}:{password}@{host}:{port}/{database}',
        'ssl_options': {
            'ssl': False,
            'ssl_cert_file': None,
            'ssl_key_file': None,
            'ssl_ca_file': None
        }
    }
}

# Cluster Templates
CLUSTER_TEMPLATES = {
    'small_master_slave': {
        'cluster_type': 'master_slave',
        'replication_mode': 'asynchronous',
        'consistency_level': 'eventual',
        'nodes': {
            'master': 1,
            'slave': 1
        },
        'connection_pool_size': 5,
        'failover_enabled': True
    },
    'medium_master_slave': {
        'cluster_type': 'master_slave',
        'replication_mode': 'asynchronous',
        'consistency_level': 'eventual',
        'nodes': {
            'master': 1,
            'slave': 3
        },
        'connection_pool_size': 10,
        'failover_enabled': True
    },
    'large_master_slave': {
        'cluster_type': 'master_slave',
        'replication_mode': 'semi_sync',
        'consistency_level': 'causal',
        'nodes': {
            'master': 1,
            'slave': 5
        },
        'connection_pool_size': 20,
        'failover_enabled': True
    },
    'small_multi_master': {
        'cluster_type': 'multi_master',
        'replication_mode': 'asynchronous',
        'consistency_level': 'eventual',
        'nodes': {
            'master': 2
        },
        'connection_pool_size': 5,
        'conflict_resolution': True
    },
    'medium_multi_master': {
        'cluster_type': 'multi_master',
        'replication_mode': 'semi_sync',
        'consistency_level': 'causal',
        'nodes': {
            'master': 3
        },
        'connection_pool_size': 10,
        'conflict_resolution': True
    },
    'large_multi_master': {
        'cluster_type': 'multi_master',
        'replication_mode': 'synchronous',
        'consistency_level': 'strong',
        'nodes': {
            'master': 5
        },
        'connection_pool_size': 20,
        'conflict_resolution': True
    }
}

# Node Templates
NODE_TEMPLATES = {
    'master_node': {
        'node_role': 'master',
        'node_type': 'primary',
        'priority': 1,
        'weight': 2,
        'connection_pool_size': 10,
        'failover_candidate': False
    },
    'slave_node': {
        'node_role': 'slave',
        'node_type': 'secondary',
        'priority': 2,
        'weight': 1,
        'connection_pool_size': 5,
        'failover_candidate': True
    },
    'multi_master_node': {
        'node_role': 'multi_master',
        'node_type': 'primary',
        'priority': 1,
        'weight': 1,
        'connection_pool_size': 8,
        'failover_candidate': True
    },
    'arbiter_node': {
        'node_role': 'arbiter',
        'node_type': 'arbiter',
        'priority': 3,
        'weight': 0,
        'connection_pool_size': 2,
        'failover_candidate': False
    }
}

# Validation Functions
def validate_replication_config():
    """Validate replication configuration"""
    errors = []
    
    # Check cluster configuration
    if CLUSTER_CONFIG['max_clusters'] < 1:
        errors.append("Max clusters must be at least 1")
    
    if CLUSTER_CONFIG['max_nodes_per_cluster'] < 1:
        errors.append("Max nodes per cluster must be at least 1")
    
    # Check replication configuration
    if not any(mode['enabled'] for mode in REPLICATION_CONFIG['modes'].values()):
        errors.append("At least one replication mode must be enabled")
    
    # Check conflict resolution configuration
    if CONFLICT_RESOLUTION_CONFIG['enabled']:
        if not any(strategy['enabled'] for strategy in CONFLICT_RESOLUTION_CONFIG['resolution_strategies'].values()):
            errors.append("At least one conflict resolution strategy must be enabled")
    
    # Check failover configuration
    if FAILOVER_CONFIG['detection']['failure_threshold'] < 1:
        errors.append("Failure threshold must be at least 1")
    
    if FAILOVER_CONFIG['recovery']['recovery_attempts'] < 1:
        errors.append("Recovery attempts must be at least 1")
    
    # Check connection configuration
    if CONNECTION_CONFIG['connection_pooling']['pool_size'] < 1:
        errors.append("Connection pool size must be at least 1")
    
    if CONNECTION_CONFIG['connection_pooling']['max_overflow'] < 0:
        errors.append("Max overflow must be non-negative")
    
    return errors

def get_replication_config():
    """Get complete replication configuration"""
    return {
        'data_replication_enabled': DATA_REPLICATION_ENABLED,
        'master_slave_replication_enabled': MASTER_SLAVE_REPLICATION_ENABLED,
        'multi_master_replication_enabled': MULTI_MASTER_REPLICATION_ENABLED,
        'conflict_resolution_enabled': CONFLICT_RESOLUTION_ENABLED,
        'replication_monitoring_enabled': REPLICATION_MONITORING_ENABLED,
        'cluster_config': CLUSTER_CONFIG,
        'replication_config': REPLICATION_CONFIG,
        'conflict_resolution_config': CONFLICT_RESOLUTION_CONFIG,
        'failover_config': FAILOVER_CONFIG,
        'connection_config': CONNECTION_CONFIG,
        'monitoring_config': MONITORING_CONFIG,
        'performance_config': PERFORMANCE_CONFIG,
        'security_config': SECURITY_CONFIG,
        'database_type_configs': DATABASE_TYPE_CONFIGS,
        'cluster_templates': CLUSTER_TEMPLATES,
        'node_templates': NODE_TEMPLATES
    }


# Default configurations for different deployment types
DEFAULT_CONFIGS = {
    'small': {
        'cluster_config': {'max_nodes_per_cluster': 4},
        'replication_config': {'modes': {'synchronous': {'enabled': False}}},
        'conflict_resolution_config': {'auto_resolution': False},
        'connection_config': {'connection_pooling': {'pool_size': 5}}
    },
    'medium': {
        'cluster_config': {'max_nodes_per_cluster': 8},
        'replication_config': {'modes': {'synchronous': {'enabled': True}}},
        'conflict_resolution_config': {'auto_resolution': True},
        'connection_config': {'connection_pooling': {'pool_size': 10}}
    },
    'large': {
        'cluster_config': {'max_nodes_per_cluster': 32},
        'replication_config': {'modes': {'synchronous': {'enabled': True}}},
        'conflict_resolution_config': {'auto_resolution': True},
        'connection_config': {'connection_pooling': {'pool_size': 20}}
    }
}
