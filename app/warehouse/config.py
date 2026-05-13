"""
Data Warehouse Configuration

Configuration settings for analytics data warehouse, aggregation pipelines,
historical data storage, and data archiving.
"""

import os
from datetime import timedelta

# Data Warehouse Configuration
DATA_WAREHOUSE_ENABLED = True
WAREHOUSE_PROCESSING_ENABLED = True
DATA_ARCHIVING_ENABLED = True
DATA_RETENTION_ENABLED = True
AGGREGATION_ENABLED = True

# Warehouse Configuration
WAREHOUSE_CONFIG = {
    'enabled': True,
    'default_storage_engine': 'postgresql',  # postgresql, mysql, clickhouse, snowflake
    'default_retention_days': 365,
    'default_compression': True,
    'default_encryption': False,
    'auto_partitioning': True,
    'partition_granularity': 'daily',  # hourly, daily, weekly, monthly
    'max_warehouse_size': 1099511627776,  # 1TB
    'health_check_interval': 300,  # 5 minutes
    'cleanup_interval': 86400  # 24 hours
}

# Storage Configuration
STORAGE_CONFIG = {
    'postgresql': {
        'enabled': True,
        'host': os.getenv('POSTGRES_HOST', 'localhost'),
        'port': int(os.getenv('POSTGRES_PORT', 5432)),
        'database': os.getenv('POSTGRES_DB', 'forum_warehouse'),
        'username': os.getenv('POSTGRES_USER', 'postgres'),
        'password': os.getenv('POSTGRES_PASSWORD'),
        'pool_size': 20,
        'max_overflow': 30,
        'pool_timeout': 30,
        'pool_recycle': 3600,
        'echo': False
    },
    'mysql': {
        'enabled': False,
        'host': os.getenv('MYSQL_HOST', 'localhost'),
        'port': int(os.getenv('MYSQL_PORT', 3306)),
        'database': os.getenv('MYSQL_DB', 'forum_warehouse'),
        'username': os.getenv('MYSQL_USER', 'mysql'),
        'password': os.getenv('MYSQL_PASSWORD'),
        'charset': 'utf8mb4',
        'pool_size': 20,
        'pool_timeout': 30
    },
    'clickhouse': {
        'enabled': False,
        'host': os.getenv('CLICKHOUSE_HOST', 'localhost'),
        'port': int(os.getenv('CLICKHOUSE_PORT', 9000)),
        'database': os.getenv('CLICKHOUSE_DB', 'forum_warehouse'),
        'username': os.getenv('CLICKHOUSE_USER', 'default'),
        'password': os.getenv('CLICKHOUSE_PASSWORD'),
        'compression': 'lz4'
    },
    'snowflake': {
        'enabled': False,
        'account': os.getenv('SNOWFLAKE_ACCOUNT'),
        'user': os.getenv('SNOWFLAKE_USER'),
        'password': os.getenv('SNOWFLAKE_PASSWORD'),
        'warehouse': os.getenv('SNOWFLAKE_WAREHOUSE'),
        'database': os.getenv('SNOWFLAKE_DATABASE'),
        'schema': os.getenv('SNOWFLAKE_SCHEMA')
    }
}

# Aggregation Configuration
AGGREGATION_CONFIG = {
    'enabled': True,
    'max_concurrent_pipelines': 10,
    'default_batch_size': 1000,
    'max_batch_size': 10000,
    'processing_timeout': 3600,  # 1 hour
    'retry_attempts': 3,
    'retry_delay': 60,  # seconds
    'aggregation_types': {
        'hourly': {'interval': 3600, 'retention_days': 90},
        'daily': {'interval': 86400, 'retention_days': 365},
        'weekly': {'interval': 604800, 'retention_days': 1095},
        'monthly': {'interval': 2592000, 'retention_days': 1825}
    },
    'performance': {
        'enable_parallel_processing': True,
        'max_workers': 4,
        'memory_limit': 1073741824,  # 1GB
        'temp_storage_limit': 2147483648  # 2GB
    }
}

# Historical Data Configuration
HISTORICAL_CONFIG = {
    'enabled': True,
    'default_retention_days': 2555,  # 7 years
    'compression_enabled': True,
    'compression_algorithm': 'gzip',
    'encryption_enabled': False,
    'encryption_algorithm': 'aes256',
    'storage_tiers': {
        'hot': {'retention_days': 30, 'compression': False},
        'warm': {'retention_days': 365, 'compression': True},
        'cold': {'retention_days': 1825, 'compression': True},
        'archive': {'retention_days': 3650, 'compression': True}
    },
    'data_quality': {
        'enabled': True,
        'quality_score_threshold': 0.8,
        'completeness_threshold': 0.9,
        'accuracy_threshold': 0.95
    },
    'partitioning': {
        'enabled': True,
        'partition_column': 'data_timestamp',
        'partition_granularity': 'monthly'
    }
}

# Archiving Configuration
ARCHIVING_CONFIG = {
    'enabled': True,
    'default_retention_days': 2555,  # 7 years
    'compression_enabled': True,
    'compression_level': 6,
    'encryption_enabled': False,
    'archive_types': {
        'full': {'enabled': True, 'frequency': 'monthly', 'retention_days': 3650},
        'incremental': {'enabled': True, 'frequency': 'daily', 'retention_days': 2555},
        'snapshot': {'enabled': True, 'frequency': 'weekly', 'retention_days': 1825},
        'delta': {'enabled': True, 'frequency': 'hourly', 'retention_days': 90}
    },
    'storage': {
        'local': {
            'enabled': True,
            'path': '/archives/warehouse',
            'compression': True,
            'encryption': False
        },
        's3': {
            'enabled': False,
            'bucket': os.getenv('S3_ARCHIVE_BUCKET'),
            'region': os.getenv('S3_REGION', 'us-east-1'),
            'access_key': os.getenv('S3_ACCESS_KEY'),
            'secret_key': os.getenv('S3_SECRET_KEY'),
            'compression': True,
            'encryption': True
        },
        'glacier': {
            'enabled': False,
            'vault': os.getenv('GLACIER_VAULT'),
            'region': os.getenv('GLACIER_REGION', 'us-east-1'),
            'access_key': os.getenv('GLACIER_ACCESS_KEY'),
            'secret_key': os.getenv('GLACIER_SECRET_KEY')
        }
    },
    'verification': {
        'enabled': True,
        'verify_after_creation': True,
        'verify_integrity': True,
        'verify_period_days': 30
    }
}

# Retention Configuration
RETENTION_CONFIG = {
    'enabled': True,
    'default_retention_days': 2555,  # 7 years
    'policies': {
        'user_data': {'retention_days': 2555, 'archive_before_delete': True},
        'system_data': {'retention_days': 1825, 'archive_before_delete': True},
        'analytics_data': {'retention_days': 1095, 'archive_before_delete': True},
        'audit_data': {'retention_days': 3650, 'archive_before_delete': True},
        'temp_data': {'retention_days': 30, 'archive_before_delete': False}
    },
    'cleanup': {
        'enabled': True,
        'cleanup_interval': 86400,  # 24 hours
        'batch_size': 1000,
        'max_cleanup_time': 3600  # 1 hour
    },
    'compliance': {
        'gdpr_retention_days': 2555,  # 7 years
        'ccpa_retention_days': 730,  # 2 years
        'hipaa_retention_days': 2555,  # 7 years
        'sox_retention_days': 2555  # 7 years
    }
}

# Performance Configuration
PERFORMANCE_CONFIG = {
    'query_optimization': {
        'enabled': True,
        'auto_index_creation': True,
        'query_cache_enabled': True,
        'query_timeout': 300,  # 5 minutes
        'max_query_memory': 1073741824  # 1GB
    },
    'connection_pooling': {
        'enabled': True,
        'max_connections': 100,
        'min_connections': 10,
        'connection_timeout': 30,
        'idle_timeout': 300
    },
    'caching': {
        'enabled': True,
        'cache_type': 'redis',  # memory, redis, memcached
        'cache_size': 1073741824,  # 1GB
        'cache_ttl': 3600,  # 1 hour
        'cache_key_prefix': 'warehouse:'
    },
    'parallel_processing': {
        'enabled': True,
        'max_workers': 4,
        'worker_timeout': 3600,
        'task_queue_size': 1000
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
            'storage_usage',
            'query_performance',
            'pipeline_status',
            'data_quality',
            'archive_status'
        ]
    },
    'health_checks': {
        'enabled': True,
        'interval': 300,  # 5 minutes
        'timeout': 30,  # seconds
        'checks': [
            'database_connection',
            'storage_space',
            'processing_queue',
            'archive_storage'
        ]
    },
    'alerts': {
        'enabled': True,
        'thresholds': {
            'storage_usage': 0.9,  # 90%
            'query_time': 300000,  # 5 minutes
            'pipeline_failure_rate': 0.1,  # 10%
            'data_quality_score': 0.8,  # 80%
            'archive_failure_rate': 0.05  # 5%
        },
        'channels': ['email', 'slack'],
        'cooldown': 300  # 5 minutes
    },
    'dashboard': {
        'enabled': True,
        'refresh_interval': 300,  # 5 minutes
        'max_data_points': 1000,
        'chart_types': ['line', 'bar', 'pie', 'gauge']
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
            'analyst': ['read', 'write'],
            'viewer': ['read']
        }
    },
    'encryption': {
        'enabled': False,
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

# Backup Configuration
BACKUP_CONFIG = {
    'enabled': True,
    'backup_interval': 86400,  # Daily
    'retention_days': 30,
    'compression': True,
    'encryption': False,
    'backup_types': {
        'full': {'enabled': True, 'interval': 604800},  # Weekly
        'incremental': {'enabled': True, 'interval': 86400},  # Daily
        'differential': {'enabled': False, 'interval': 43200}  # 12 hours
    },
    'storage': {
        'local': {
            'enabled': True,
            'path': '/backups/warehouse'
        },
        's3': {
            'enabled': False,
            'bucket': 'warehouse-backups',
            'region': 'us-east-1'
        }
    },
    'verification': {
        'enabled': True,
        'verify_backups': True,
        'restore_test': False,
        'integrity_check': True
    }
}

# Development Configuration
if os.getenv('FLASK_ENV') == 'development':
    DATA_WAREHOUSE_ENABLED = True
    WAREHOUSE_PROCESSING_ENABLED = True
    DATA_ARCHIVING_ENABLED = False
    DATA_RETENTION_ENABLED = False
    
    WAREHOUSE_CONFIG['default_retention_days'] = 7
    WAREHOUSE_CONFIG['max_warehouse_size'] = 1073741824  # 1GB
    
    AGGREGATION_CONFIG['max_concurrent_pipelines'] = 2
    AGGREGATION_CONFIG['default_batch_size'] = 100
    
    HISTORICAL_CONFIG['default_retention_days'] = 7
    HISTORICAL_CONFIG['compression_enabled'] = False
    
    ARCHIVING_CONFIG['enabled'] = False
    RETENTION_CONFIG['enabled'] = False
    
    MONITORING_CONFIG['metrics_collection']['interval'] = 300
    MONITORING_CONFIG['health_checks']['interval'] = 600
    
    BACKUP_CONFIG['enabled'] = False

# Production Configuration
if os.getenv('FLASK_ENV') == 'production':
    DATA_WAREHOUSE_ENABLED = True
    WAREHOUSE_PROCESSING_ENABLED = True
    DATA_ARCHIVING_ENABLED = True
    DATA_RETENTION_ENABLED = True
    
    WAREHOUSE_CONFIG['default_retention_days'] = 2555
    WAREHOUSE_CONFIG['max_warehouse_size'] = 1099511627776  # 1TB
    
    AGGREGATION_CONFIG['max_concurrent_pipelines'] = 10
    AGGREGATION_CONFIG['default_batch_size'] = 1000
    
    HISTORICAL_CONFIG['default_retention_days'] = 2555
    HISTORICAL_CONFIG['compression_enabled'] = True
    
    ARCHIVING_CONFIG['enabled'] = True
    RETENTION_CONFIG['enabled'] = True
    
    MONITORING_CONFIG['metrics_collection']['interval'] = 60
    MONITORING_CONFIG['health_checks']['interval'] = 300
    
    BACKUP_CONFIG['enabled'] = True

# Testing Configuration
if os.getenv('FLASK_ENV') == 'testing':
    DATA_WAREHOUSE_ENABLED = False
    WAREHOUSE_PROCESSING_ENABLED = False
    DATA_ARCHIVING_ENABLED = False
    DATA_RETENTION_ENABLED = False
    
    MONITORING_CONFIG['enabled'] = False
    BACKUP_CONFIG['enabled'] = False

# Environment Variables
ENVIRONMENT_VARIABLES = {
    'DATA_WAREHOUSE_ENABLED': os.getenv('DATA_WAREHOUSE_ENABLED', 'True'),
    'WAREHOUSE_PROCESSING_ENABLED': os.getenv('WAREHOUSE_PROCESSING_ENABLED', 'True'),
    'DATA_ARCHIVING_ENABLED': os.getenv('DATA_ARCHIVING_ENABLED', 'True'),
    'DATA_RETENTION_ENABLED': os.getenv('DATA_RETENTION_ENABLED', 'True'),
    'POSTGRES_HOST': os.getenv('POSTGRES_HOST', 'localhost'),
    'POSTGRES_PORT': os.getenv('POSTGRES_PORT', '5432'),
    'POSTGRES_DB': os.getenv('POSTGRES_DB', 'forum_warehouse'),
    'POSTGRES_USER': os.getenv('POSTGRES_USER', 'postgres'),
    'POSTGRES_PASSWORD': os.getenv('POSTGRES_PASSWORD'),
    'MYSQL_HOST': os.getenv('MYSQL_HOST', 'localhost'),
    'MYSQL_PORT': os.getenv('MYSQL_PORT', '3306'),
    'MYSQL_DB': os.getenv('MYSQL_DB', 'forum_warehouse'),
    'MYSQL_USER': os.getenv('MYSQL_USER', 'mysql'),
    'MYSQL_PASSWORD': os.getenv('MYSQL_PASSWORD'),
    'CLICKHOUSE_HOST': os.getenv('CLICKHOUSE_HOST', 'localhost'),
    'CLICKHOUSE_PORT': os.getenv('CLICKHOUSE_PORT', '9000'),
    'CLICKHOUSE_DB': os.getenv('CLICKHOUSE_DB', 'forum_warehouse'),
    'CLICKHOUSE_USER': os.getenv('CLICKHOUSE_USER', 'default'),
    'CLICKHOUSE_PASSWORD': os.getenv('CLICKHOUSE_PASSWORD'),
    'SNOWFLAKE_ACCOUNT': os.getenv('SNOWFLAKE_ACCOUNT'),
    'SNOWFLAKE_USER': os.getenv('SNOWFLAKE_USER'),
    'SNOWFLAKE_PASSWORD': os.getenv('SNOWFLAKE_PASSWORD'),
    'SNOWFLAKE_WAREHOUSE': os.getenv('SNOWFLAKE_WAREHOUSE'),
    'SNOWFLAKE_DATABASE': os.getenv('SNOWFLAKE_DATABASE'),
    'SNOWFLAKE_SCHEMA': os.getenv('SNOWFLAKE_SCHEMA'),
    'S3_ARCHIVE_BUCKET': os.getenv('S3_ARCHIVE_BUCKET'),
    'S3_REGION': os.getenv('S3_REGION', 'us-east-1'),
    'S3_ACCESS_KEY': os.getenv('S3_ACCESS_KEY'),
    'S3_SECRET_KEY': os.getenv('S3_SECRET_KEY'),
    'GLACIER_VAULT': os.getenv('GLACIER_VAULT'),
    'GLACIER_REGION': os.getenv('GLACIER_REGION', 'us-east-1'),
    'GLACIER_ACCESS_KEY': os.getenv('GLACIER_ACCESS_KEY'),
    'GLACIER_SECRET_KEY': os.getenv('GLACIER_SECRET_KEY')
}

# Schema Templates
SCHEMA_TEMPLATES = {
    'user_analytics': {
        'table_name': 'user_analytics',
        'columns': {
            'user_id': 'INTEGER',
            'event_type': 'VARCHAR(50)',
            'event_timestamp': 'TIMESTAMP',
            'session_id': 'VARCHAR(100)',
            'ip_address': 'VARCHAR(45)',
            'user_agent': 'TEXT',
            'event_data': 'JSON',
            'created_at': 'TIMESTAMP'
        },
        'indexes': [
            'user_id',
            'event_timestamp',
            'event_type',
            'session_id'
        ],
        'partition_by': 'event_timestamp'
    },
    'content_analytics': {
        'table_name': 'content_analytics',
        'columns': {
            'content_id': 'INTEGER',
            'content_type': 'VARCHAR(50)',
            'action_type': 'VARCHAR(50)',
            'user_id': 'INTEGER',
            'action_timestamp': 'TIMESTAMP',
            'action_data': 'JSON',
            'created_at': 'TIMESTAMP'
        },
        'indexes': [
            'content_id',
            'action_timestamp',
            'content_type',
            'user_id'
        ],
        'partition_by': 'action_timestamp'
    },
    'system_metrics': {
        'table_name': 'system_metrics',
        'columns': {
            'metric_name': 'VARCHAR(100)',
            'metric_value': 'FLOAT',
            'metric_unit': 'VARCHAR(20)',
            'metric_timestamp': 'TIMESTAMP',
            'tags': 'JSON',
            'created_at': 'TIMESTAMP'
        },
        'indexes': [
            'metric_name',
            'metric_timestamp',
            'tags'
        ],
        'partition_by': 'metric_timestamp'
    }
}

# Aggregation Templates
AGGREGATION_TEMPLATES = {
    'daily_user_activity': {
        'name': 'daily_user_activity',
        'type': 'daily',
        'source_tables': ['user_analytics'],
        'group_by_fields': ['user_id', 'DATE(event_timestamp)'],
        'aggregate_functions': [
            {'field': 'user_id', 'type': 'count', 'alias': 'activity_count'},
            {'field': 'session_id', 'type': 'count_distinct', 'alias': 'unique_sessions'}
        ],
        'target_table': 'daily_user_activity_summary'
    },
    'daily_content_metrics': {
        'name': 'daily_content_metrics',
        'type': 'daily',
        'source_tables': ['content_analytics'],
        'group_by_fields': ['content_id', 'DATE(action_timestamp)'],
        'aggregate_functions': [
            {'field': 'user_id', 'type': 'count_distinct', 'alias': 'unique_users'},
            {'field': 'action_type', 'type': 'count', 'alias': 'action_count'}
        ],
        'target_table': 'daily_content_metrics'
    },
    'hourly_system_metrics': {
        'name': 'hourly_system_metrics',
        'type': 'hourly',
        'source_tables': ['system_metrics'],
        'group_by_fields': ['metric_name', 'DATE_TRUNC(hour, metric_timestamp)'],
        'aggregate_functions': [
            {'field': 'metric_value', 'type': 'avg', 'alias': 'avg_value'},
            {'field': 'metric_value', 'type': 'min', 'alias': 'min_value'},
            {'field': 'metric_value', 'type': 'max', 'alias': 'max_value'}
        ],
        'target_table': 'hourly_system_metrics_summary'
    }
}

# Validation Functions
def validate_warehouse_config():
    """Validate warehouse configuration"""
    errors = []
    
    # Check required environment variables
    if STORAGE_CONFIG['postgresql']['enabled']:
        required_vars = ['POSTGRES_HOST', 'POSTGRES_PORT', 'POSTGRES_DB', 'POSTGRES_USER']
        for var in required_vars:
            if not os.getenv(var):
                errors.append(f"Missing required PostgreSQL environment variable: {var}")
    
    # Check configuration consistency
    if WAREHOUSE_CONFIG['max_warehouse_size'] <= 0:
        errors.append("Max warehouse size must be positive")
    
    if AGGREGATION_CONFIG['max_concurrent_pipelines'] < 1:
        errors.append("Max concurrent pipelines must be at least 1")
    
    if AGGREGATION_CONFIG['default_batch_size'] < 1:
        errors.append("Default batch size must be at least 1")
    
    if HISTORICAL_CONFIG['default_retention_days'] < 0:
        errors.append("Default retention days must be non-negative")
    
    return errors

def get_warehouse_config():
    """Get complete warehouse configuration"""
    return {
        'data_warehouse_enabled': DATA_WAREHOUSE_ENABLED,
        'warehouse_processing_enabled': WAREHOUSE_PROCESSING_ENABLED,
        'data_archiving_enabled': DATA_ARCHIVING_ENABLED,
        'data_retention_enabled': DATA_RETENTION_ENABLED,
        'aggregation_enabled': AGGREGATION_ENABLED,
        'warehouse_config': WAREHOUSE_CONFIG,
        'storage_config': STORAGE_CONFIG,
        'aggregation_config': AGGREGATION_CONFIG,
        'historical_config': HISTORICAL_CONFIG,
        'archiving_config': ARCHIVING_CONFIG,
        'retention_config': RETENTION_CONFIG,
        'performance_config': PERFORMANCE_CONFIG,
        'monitoring_config': MONITORING_CONFIG,
        'security_config': SECURITY_CONFIG,
        'backup_config': BACKUP_CONFIG,
        'schema_templates': SCHEMA_TEMPLATES,
        'aggregation_templates': AGGREGATION_TEMPLATES
    }


# Default configurations for different deployment types
DEFAULT_CONFIGS = {
    'small': {
        'warehouse_config': {'max_warehouse_size': 1073741824},  # 1GB
        'aggregation_config': {'max_concurrent_pipelines': 2},
        'historical_config': {'default_retention_days': 365}
    },
    'medium': {
        'warehouse_config': {'max_warehouse_size': 10737418240},  # 10GB
        'aggregation_config': {'max_concurrent_pipelines': 5},
        'historical_config': {'default_retention_days': 1825}
    },
    'large': {
        'warehouse_config': {'max_warehouse_size': 1099511627776},  # 1TB
        'aggregation_config': {'max_concurrent_pipelines': 10},
        'historical_config': {'default_retention_days': 3650}
    }
}
