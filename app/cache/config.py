"""
Cache Configuration

This module provides configuration settings for the advanced caching system,
including Redis configuration, cache policies, and performance settings.
"""

import os
from datetime import timedelta


class CacheConfig:
    """Cache configuration settings"""
    
    # Redis Configuration
    REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
    REDIS_DB = int(os.environ.get('REDIS_DB', 0))
    REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD', None)
    REDIS_URL = os.environ.get('REDIS_URL', f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}')
    
    # Connection Settings
    REDIS_MAX_CONNECTIONS = int(os.environ.get('REDIS_MAX_CONNECTIONS', 50))
    REDIS_SOCKET_TIMEOUT = int(os.environ.get('REDIS_SOCKET_TIMEOUT', 5))
    REDIS_SOCKET_CONNECT_TIMEOUT = int(os.environ.get('REDIS_SOCKET_CONNECT_TIMEOUT', 5))
    REDIS_RETRY_ON_TIMEOUT = os.environ.get('REDIS_RETRY_ON_TIMEOUT', 'true').lower() == 'true'
    
    # Cache Policies
    DEFAULT_TTL = int(os.environ.get('CACHE_DEFAULT_TTL', 3600))  # 1 hour
    USER_CACHE_TTL = int(os.environ.get('CACHE_USER_TTL', 1800))  # 30 minutes
    SESSION_CACHE_TTL = int(os.environ.get('CACHE_SESSION_TTL', 900))  # 15 minutes
    SYSTEM_CACHE_TTL = int(os.environ.get('CACHE_SYSTEM_TTL', 7200))  # 2 hours
    
    # Cache Size Limits
    MAX_CACHE_SIZE_MB = int(os.environ.get('CACHE_MAX_SIZE_MB', 500))
    MAX_ENTRY_SIZE_BYTES = int(os.environ.get('CACHE_MAX_ENTRY_SIZE', 1048576))  # 1MB
    COMPRESSION_THRESHOLD = int(os.environ.get('CACHE_COMPRESSION_THRESHOLD', 1024))  # 1KB
    
    # Performance Settings
    CACHE_CLEANUP_INTERVAL = int(os.environ.get('CACHE_CLEANUP_INTERVAL', 300))  # 5 minutes
    CACHE_STATS_RETENTION_DAYS = int(os.environ.get('CACHE_STATS_RETENTION_DAYS', 7))
    CACHE_WARMUP_ENABLED = os.environ.get('CACHE_WARMUP_ENABLED', 'true').lower() == 'true'
    
    # Distributed Cache Settings
    INSTANCE_ID = os.environ.get('INSTANCE_ID', 'default')
    CACHE_INVALIDATION_CHANNEL = os.environ.get('CACHE_INVALIDATION_CHANNEL', 'cache_invalidation')
    
    # Monitoring Settings
    CACHE_MONITORING_ENABLED = os.environ.get('CACHE_MONITORING_ENABLED', 'true').lower() == 'true'
    CACHE_ALERT_THRESHOLD_HIT_RATIO = float(os.environ.get('CACHE_ALERT_THRESHOLD_HIT_RATIO', 0.5))
    CACHE_ALERT_THRESHOLD_SIZE_MB = float(os.environ.get('CACHE_ALERT_THRESHOLD_SIZE_MB', 500))
    
    # Cache Type Definitions
    CACHE_TYPES = {
        'general': {
            'ttl': DEFAULT_TTL,
            'max_size': MAX_CACHE_SIZE_MB * 0.4,  # 40% of total
            'compression': True
        },
        'user': {
            'ttl': USER_CACHE_TTL,
            'max_size': MAX_CACHE_SIZE_MB * 0.3,  # 30% of total
            'compression': True
        },
        'session': {
            'ttl': SESSION_CACHE_TTL,
            'max_size': MAX_CACHE_SIZE_MB * 0.1,  # 10% of total
            'compression': False
        },
        'system': {
            'ttl': SYSTEM_CACHE_TTL,
            'max_size': MAX_CACHE_SIZE_MB * 0.2,  # 20% of total
            'compression': True
        }
    }
    
    # Cache Tags
    CACHE_TAGS = {
        'user_profile': {'ttl': USER_CACHE_TTL, 'auto_invalidate': True},
        'user_preferences': {'ttl': USER_CACHE_TTL, 'auto_invalidate': True},
        'user_roles': {'ttl': USER_CACHE_TTL, 'auto_invalidate': True},
        'system_config': {'ttl': SYSTEM_CACHE_TTL, 'auto_invalidate': False},
        'navigation': {'ttl': 1800, 'auto_invalidate': True},
        'post_content': {'ttl': 3600, 'auto_invalidate': True},
        'comments': {'ttl': 1800, 'auto_invalidate': True},
        'analytics': {'ttl': 7200, 'auto_invalidate': False}
    }
    
    @classmethod
    def get_redis_config(cls):
        """Get Redis connection configuration"""
        return {
            'host': cls.REDIS_HOST,
            'port': cls.REDIS_PORT,
            'db': cls.REDIS_DB,
            'password': cls.REDIS_PASSWORD,
            'decode_responses': False,
            'socket_timeout': cls.REDIS_SOCKET_TIMEOUT,
            'socket_connect_timeout': cls.REDIS_SOCKET_CONNECT_TIMEOUT,
            'retry_on_timeout': cls.REDIS_RETRY_ON_TIMEOUT,
            'max_connections': cls.REDIS_MAX_CONNECTIONS
        }
    
    @classmethod
    def get_cache_type_config(cls, cache_type: str):
        """Get configuration for a specific cache type"""
        return cls.CACHE_TYPES.get(cache_type, cls.CACHE_TYPES['general'])
    
    @classmethod
    def get_tag_config(cls, tag: str):
        """Get configuration for a specific cache tag"""
        return cls.CACHE_TAGS.get(tag, {'ttl': cls.DEFAULT_TTL, 'auto_invalidate': False})
    
    @classmethod
    def should_compress(cls, data_size: int, cache_type: str = 'general') -> bool:
        """Determine if data should be compressed"""
        type_config = cls.get_cache_type_config(cache_type)
        return type_config['compression'] and data_size >= cls.COMPRESSION_THRESHOLD
    
    @classmethod
    def validate_cache_size(cls, cache_type: str, data_size: int) -> bool:
        """Validate if cache entry size is within limits"""
        return data_size <= cls.MAX_ENTRY_SIZE_BYTES


class CachePolicy:
    """Cache policy definitions and rules"""
    
    # Cache Invalidation Policies
    INVALIDATION_POLICIES = {
        'user_update': {
            'tags': ['user_profile', 'user_preferences', 'user_roles'],
            'patterns': [r'user:\d+:.*'],
            'delay_seconds': 0
        },
        'post_update': {
            'tags': ['post_content', 'comments'],
            'patterns': [r'post:\d+:.*'],
            'delay_seconds': 0
        },
        'system_config_update': {
            'tags': ['system_config', 'navigation'],
            'patterns': [r'system:.*'],
            'delay_seconds': 0
        },
        'session_expiry': {
            'tags': ['session'],
            'patterns': [r'session:.*'],
            'delay_seconds': 0
        }
    }
    
    # Cache Preloading Policies
    PRELOAD_POLICIES = {
        'user_login': {
            'keys': [
                'user:{user_id}:profile',
                'user:{user_id}:preferences',
                'user:{user_id}:roles',
                'system:config',
                'system:navigation'
            ],
            'priority': 'high'
        },
        'page_load': {
            'keys': [
                'system:config',
                'system:navigation',
                'system:theme_options'
            ],
            'priority': 'medium'
        }
    }
    
    # Cache Warming Policies
    WARMING_POLICIES = {
        'scheduled': {
            'interval_minutes': 60,
            'keys': [
                'system:config',
                'system:navigation',
                'system:popular_posts',
                'system:active_users'
            ],
            'enabled': True
        },
        'on_demand': {
            'trigger_threshold': 10,  # Cache misses
            'keys': [
                'system:config',
                'system:navigation'
            ],
            'enabled': True
        }
    }
    
    @classmethod
    def get_invalidation_policy(cls, event_type: str):
        """Get invalidation policy for an event type"""
        return cls.INVALIDATION_POLICIES.get(event_type, {})
    
    @classmethod
    def get_preload_policy(cls, event_type: str):
        """Get preload policy for an event type"""
        return cls.PRELOAD_POLICIES.get(event_type, {})
    
    @classmethod
    def get_warming_policy(cls, policy_type: str):
        """Get warming policy by type"""
        return cls.WARMING_POLICIES.get(policy_type, {})


class CachePerformanceConfig:
    """Performance optimization configuration"""
    
    # Serialization Settings
    SERIALIZATION_PROTOCOL = 'pickle'  # pickle, json, msgpack
    SERIALIZATION_COMPRESSION = 'zlib'  # zlib, gzip, lz4, none
    
    # Batch Operations
    BATCH_SIZE_LIMIT = int(os.environ.get('CACHE_BATCH_SIZE_LIMIT', 100))
    BATCH_TIMEOUT_SECONDS = int(os.environ.get('CACHE_BATCH_TIMEOUT', 5))
    
    # Connection Pooling
    CONNECTION_POOL_SIZE = int(os.environ.get('CACHE_CONNECTION_POOL_SIZE', 20))
    CONNECTION_POOL_TIMEOUT = int(os.environ.get('CACHE_CONNECTION_POOL_TIMEOUT', 30))
    
    # Retry Configuration
    MAX_RETRIES = int(os.environ.get('CACHE_MAX_RETRIES', 3))
    RETRY_DELAY_SECONDS = float(os.environ.get('CACHE_RETRY_DELAY', 0.1))
    RETRY_BACKOFF_FACTOR = float(os.environ.get('CACHE_RETRY_BACKOFF', 2.0))
    
    # Memory Management
    MEMORY_LIMIT_MB = int(os.environ.get('CACHE_MEMORY_LIMIT_MB', 1024))
    GC_THRESHOLD = float(os.environ.get('CACHE_GC_THRESHOLD', 0.8))
    
    @classmethod
    def get_serialization_config(cls):
        """Get serialization configuration"""
        return {
            'protocol': cls.SERIALIZATION_PROTOCOL,
            'compression': cls.SERIALIZATION_COMPRESSION
        }
    
    @classmethod
    def get_batch_config(cls):
        """Get batch operation configuration"""
        return {
            'size_limit': cls.BATCH_SIZE_LIMIT,
            'timeout_seconds': cls.BATCH_TIMEOUT_SECONDS
        }
    
    @classmethod
    def get_retry_config(cls):
        """Get retry configuration"""
        return {
            'max_retries': cls.MAX_RETRIES,
            'delay_seconds': cls.RETRY_DELAY_SECONDS,
            'backoff_factor': cls.RETRY_BACKOFF_FACTOR
        }


class CacheMonitoringConfig:
    """Cache monitoring configuration"""
    
    # Metrics Collection
    METRICS_COLLECTION_ENABLED = os.environ.get('CACHE_METRICS_ENABLED', 'true').lower() == 'true'
    METRICS_RETENTION_DAYS = int(os.environ.get('CACHE_METRICS_RETENTION_DAYS', 30))
    METRICS_AGGREGATION_INTERVAL = int(os.environ.get('CACHE_METRICS_AGGREGATION_INTERVAL', 300))  # 5 minutes
    
    # Alerting
    ALERT_ENABLED = os.environ.get('CACHE_ALERTS_ENABLED', 'true').lower() == 'true'
    ALERT_HIT_RATIO_THRESHOLD = float(os.environ.get('CACHE_ALERT_HIT_RATIO_THRESHOLD', 0.5))
    ALERT_SIZE_THRESHOLD_MB = float(os.environ.get('CACHE_ALERT_SIZE_THRESHOLD_MB', 500))
    ALERT_ERROR_RATE_THRESHOLD = float(os.environ.get('CACHE_ALERT_ERROR_RATE_THRESHOLD', 0.1))
    
    # Reporting
    REPORT_GENERATION_ENABLED = os.environ.get('CACHE_REPORTS_ENABLED', 'true').lower() == 'true'
    REPORT_SCHEDULE_HOURS = int(os.environ.get('CACHE_REPORT_SCHEDULE', 24))
    REPORT_RETENTION_DAYS = int(os.environ.get('CACHE_REPORT_RETENTION_DAYS', 90))
    
    # Health Checks
    HEALTH_CHECK_INTERVAL = int(os.environ.get('CACHE_HEALTH_CHECK_INTERVAL', 60))  # 1 minute
    HEALTH_CHECK_TIMEOUT = int(os.environ.get('CACHE_HEALTH_CHECK_TIMEOUT', 10))  # 10 seconds
    
    @classmethod
    def get_alert_thresholds(cls):
        """Get alert threshold configuration"""
        return {
            'hit_ratio': cls.ALERT_HIT_RATIO_THRESHOLD,
            'size_mb': cls.ALERT_SIZE_THRESHOLD_MB,
            'error_rate': cls.ALERT_ERROR_RATE_THRESHOLD
        }
    
    @classmethod
    def get_metrics_config(cls):
        """Get metrics collection configuration"""
        return {
            'enabled': cls.METRICS_COLLECTION_ENABLED,
            'retention_days': cls.METRICS_RETENTION_DAYS,
            'aggregation_interval': cls.METRICS_AGGREGATION_INTERVAL
        }


# Environment-specific configurations
class DevelopmentCacheConfig(CacheConfig):
    """Development environment cache configuration"""
    
    REDIS_HOST = 'localhost'
    REDIS_PORT = 6379
    REDIS_DB = 1  # Separate DB for development
    
    DEFAULT_TTL = 300  # 5 minutes for development
    CACHE_WARMUP_ENABLED = False
    CACHE_MONITORING_ENABLED = False
    
    MAX_CACHE_SIZE_MB = 50  # Smaller cache for development


class TestingCacheConfig(CacheConfig):
    """Testing environment cache configuration"""
    
    REDIS_HOST = 'localhost'
    REDIS_PORT = 6379
    REDIS_DB = 2  # Separate DB for testing
    
    DEFAULT_TTL = 60  # 1 minute for testing
    CACHE_WARMUP_ENABLED = False
    CACHE_MONITORING_ENABLED = False
    
    MAX_CACHE_SIZE_MB = 10  # Very small cache for testing


class ProductionCacheConfig(CacheConfig):
    """Production environment cache configuration"""
    
    # Production uses environment variables
    DEFAULT_TTL = 3600  # 1 hour for production
    CACHE_WARMUP_ENABLED = True
    CACHE_MONITORING_ENABLED = True
    
    MAX_CACHE_SIZE_MB = 1024  # 1GB for production
    
    # Production-specific settings
    REDIS_MAX_CONNECTIONS = 100
    REDIS_SOCKET_TIMEOUT = 2
    REDIS_SOCKET_CONNECT_TIMEOUT = 2
    
    # Production monitoring
    ALERT_HIT_RATIO_THRESHOLD = 0.7  # Higher threshold for production
    ALERT_SIZE_THRESHOLD_MB = 800  # 800MB threshold


def get_cache_config():
    """Get cache configuration based on environment"""
    env = os.environ.get('FLASK_ENV', 'development')
    
    if env == 'production':
        return ProductionCacheConfig
    elif env == 'testing':
        return TestingCacheConfig
    else:
        return DevelopmentCacheConfig
