"""
Real-time Configuration

Configuration settings for WebSocket session management, real-time event processing,
streaming data handling, and real-time analytics.
"""

import os
from datetime import timedelta

# Real-time System Configuration
REALTIME_ENABLED = True
WEBSOCKET_ENABLED = True
EVENT_PROCESSING_ENABLED = True
STREAM_PROCESSING_ENABLED = True
REALTIME_ANALYTICS_ENABLED = True

# WebSocket Configuration
WEBSOCKET_CONFIG = {
    'enabled': True,
    'host': '0.0.0.0',
    'port': 5000,
    'path': '/ws',
    'cors_enabled': True,
    'cors_origins': ['*'],
    'compression': True,
    'per_message_deflate': True,
    'max_connections': 1000,
    'ping_interval': 25,  # seconds
    'ping_timeout': 60,   # seconds
    'close_timeout': 1,    # seconds
    'max_message_size': 16777216,  # 16MB
    'max_queue_size': 32,
    'allow_unsafe_compression': False,
    'compression_level': 6
}

# Session Management Configuration
SESSION_CONFIG = {
    'enabled': True,
    'timeout_minutes': 30,
    'max_concurrent_sessions': 3,
    'require_authentication': True,
    'track_activity': True,
    'auto_cleanup': True,
    'cleanup_interval_hours': 1,
    'session_fingerprinting': True,
    'risk_scoring': True,
    'max_risk_score': 0.8,
    'suspicious_action_threshold': 100  # actions per minute
}

# Room Management Configuration
ROOM_CONFIG = {
    'enabled': True,
    'max_rooms': 1000,
    'max_users_per_room': 100,
    'room_persistence': True,
    'auto_cleanup_empty_rooms': True,
    'cleanup_interval_minutes': 10,
    'room_types': {
        'public': {'max_users': 100, 'persistent': True},
        'private': {'max_users': 10, 'persistent': True},
        'temporary': {'max_users': 50, 'persistent': False},
        'system': {'max_users': 1000, 'persistent': True}
    },
    'default_room_type': 'public'
}

# Event Processing Configuration
EVENT_PROCESSING_CONFIG = {
    'enabled': True,
    'queue_size': 10000,
    'batch_size': 10,
    'processing_interval_ms': 100,
    'max_processing_threads': 2,
    'retry_attempts': 3,
    'retry_delay_ms': 1000,
    'dead_letter_queue': True,
    'event_ttl_hours': 24,
    'priority_levels': {
        'critical': 1,
        'high': 2,
        'medium': 5,
        'low': 10
    },
    'event_types': {
        'message': {'ttl_hours': 1, 'persistent': False},
        'notification': {'ttl_hours': 24, 'persistent': True},
        'system': {'ttl_hours': 168, 'persistent': True},
        'user_action': {'ttl_hours': 24, 'persistent': True},
        'status_update': {'ttl_hours': 1, 'persistent': False}
    }
}

# Streaming Data Configuration
STREAM_CONFIG = {
    'enabled': True,
    'queue_size': 10000,
    'batch_size': 50,
    'processing_interval_ms': 200,
    'max_processing_threads': 3,
    'retry_attempts': 3,
    'retry_delay_ms': 2000,
    'dead_letter_queue': True,
    'data_retention_hours': 24,
    'compression_enabled': True,
    'schema_validation': True,
    'quality_scoring': True,
    'stream_types': {
        'user_activity': {'priority': 5, 'ttl_hours': 24},
        'system_metrics': {'priority': 2, 'ttl_hours': 168},
        'chat': {'priority': 3, 'ttl_hours': 24},
        'notifications': {'priority': 1, 'ttl_hours': 48},
        'performance': {'priority': 2, 'ttl_hours': 168},
        'analytics': {'priority': 4, 'ttl_hours': 72}
    }
}

# Real-time Analytics Configuration
ANALYTICS_CONFIG = {
    'enabled': True,
    'cache_ttl_seconds': 60,
    'update_interval_seconds': 5,
    'batch_processing': True,
    'batch_size': 100,
    'aggregation_periods': ['realtime', '1m', '5m', '15m', '1h', '1d'],
    'metrics_retention_days': 30,
    'alert_thresholds': {
        'active_users_warning': 50,
        'active_users_critical': 100,
        'message_rate_warning': 1000,
        'message_rate_critical': 5000,
        'error_rate_warning': 5.0,
        'error_rate_critical': 10.0
    },
    'metric_types': {
        'active_users': {'type': 'gauge', 'unit': 'count'},
        'message_rate': {'type': 'counter', 'unit': 'per_minute'},
        'error_rate': {'type': 'gauge', 'unit': 'percent'},
        'latency': {'type': 'histogram', 'unit': 'milliseconds'},
        'throughput': {'type': 'counter', 'unit': 'bytes_per_second'}
    }
}

# Security Configuration
REALTIME_SECURITY_CONFIG = {
    'enabled': True,
    'authentication_required': True,
    'authorization_required': True,
    'rate_limiting': {
        'enabled': True,
        'messages_per_minute': 60,
        'connections_per_minute': 10,
        'events_per_minute': 100,
        'burst_size': 10
    },
    'input_validation': {
        'enabled': True,
        'max_message_size': 1048576,  # 1MB
        'allowed_event_types': ['message', 'notification', 'system', 'user_action', 'status_update'],
        'sanitize_html': True,
        'filter_profanity': True
    },
    'session_security': {
        'fingerprinting': True,
        'risk_scoring': True,
        'max_risk_score': 0.8,
        'auto_disconnect_risky': True,
        'monitor_concurrent_sessions': True
    },
    'data_protection': {
        'encrypt_sensitive_data': True,
        'mask_personal_info': True,
        'audit_logging': True,
        'data_retention_policy': True
    }
}

# Performance Configuration
PERFORMANCE_CONFIG = {
    'connection_pooling': {
        'enabled': True,
        'max_connections': 1000,
        'connection_timeout': 30,
        'idle_timeout': 300
    },
    'caching': {
        'enabled': True,
        'cache_type': 'redis',  # memory, redis, memcached
        'ttl_seconds': 300,
        'max_size': 10000
    },
    'batch_processing': {
        'enabled': True,
        'batch_size': 50,
        'flush_interval_ms': 100
    },
    'compression': {
        'enabled': True,
        'algorithm': 'gzip',
        'level': 6,
        'min_size': 1024  # Only compress messages larger than 1KB
    },
    'monitoring': {
        'enabled': True,
        'metrics_interval_seconds': 10,
        'performance_logging': True,
        'slow_query_threshold_ms': 100
    }
}

# Monitoring and Logging Configuration
MONITORING_CONFIG = {
    'enabled': True,
    'log_level': 'INFO',
    'log_format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file_path': 'logs/realtime.log',
    'max_file_size_mb': 100,
    'backup_count': 5,
    'metrics_collection': {
        'enabled': True,
        'interval_seconds': 10,
        'retention_days': 7
    },
    'health_checks': {
        'enabled': True,
        'interval_seconds': 30,
        'endpoints': ['/health', '/health/realtime']
    },
    'alerts': {
        'enabled': True,
        'channels': ['email', 'slack'],
        'thresholds': {
            'connection_count_warning': 800,
            'connection_count_critical': 950,
            'error_rate_warning': 5.0,
            'error_rate_critical': 10.0,
            'latency_warning': 1000,
            'latency_critical': 5000
        }
    }
}

# Integration Configuration
INTEGRATION_CONFIG = {
    'message_queue': {
        'enabled': False,
        'type': 'redis',  # redis, rabbitmq, kafka
        'host': 'localhost',
        'port': 6379,
        'db': 0
    },
    'database': {
        'connection_pool_size': 20,
        'max_overflow': 30,
        'pool_timeout': 30,
        'pool_recycle': 3600
    },
    'external_apis': {
        'enabled': False,
        'webhook_endpoints': [],
        'notification_services': []
    },
    'third_party_services': {
        'analytics': {
            'enabled': False,
            'provider': 'mixpanel',
            'api_key': ''
        },
        'monitoring': {
            'enabled': False,
            'provider': 'datadog',
            'api_key': ''
        }
    }
}

# Development Configuration
if os.getenv('FLASK_ENV') == 'development':
    REALTIME_ENABLED = True
    WEBSOCKET_ENABLED = True
    EVENT_PROCESSING_ENABLED = True
    STREAM_PROCESSING_ENABLED = True
    REALTIME_ANALYTICS_ENABLED = True
    
    WEBSOCKET_CONFIG['max_connections'] = 100
    SESSION_CONFIG['timeout_minutes'] = 60
    EVENT_PROCESSING_CONFIG['queue_size'] = 1000
    STREAM_CONFIG['queue_size'] = 1000
    ANALYTICS_CONFIG['cache_ttl_seconds'] = 300
    
    MONITORING_CONFIG['log_level'] = 'DEBUG'
    MONITORING_CONFIG['metrics_collection']['interval_seconds'] = 30
    PERFORMANCE_CONFIG['monitoring']['performance_logging'] = True

# Production Configuration
if os.getenv('FLASK_ENV') == 'production':
    REALTIME_ENABLED = True
    WEBSOCKET_ENABLED = True
    EVENT_PROCESSING_ENABLED = True
    STREAM_PROCESSING_ENABLED = True
    REALTIME_ANALYTICS_ENABLED = True
    
    WEBSOCKET_CONFIG['max_connections'] = 1000
    SESSION_CONFIG['timeout_minutes'] = 30
    EVENT_PROCESSING_CONFIG['queue_size'] = 10000
    STREAM_CONFIG['queue_size'] = 10000
    ANALYTICS_CONFIG['cache_ttl_seconds'] = 60
    
    MONITORING_CONFIG['log_level'] = 'INFO'
    MONITORING_CONFIG['metrics_collection']['interval_seconds'] = 10
    PERFORMANCE_CONFIG['monitoring']['performance_logging'] = False
    
    REALTIME_SECURITY_CONFIG['rate_limiting']['messages_per_minute'] = 60
    REALTIME_SECURITY_CONFIG['rate_limiting']['connections_per_minute'] = 10

# Testing Configuration
if os.getenv('FLASK_ENV') == 'testing':
    REALTIME_ENABLED = True
    WEBSOCKET_ENABLED = False  # Disabled in testing
    EVENT_PROCESSING_ENABLED = True
    STREAM_PROCESSING_ENABLED = True
    REALTIME_ANALYTICS_ENABLED = True
    
    WEBSOCKET_CONFIG['max_connections'] = 10
    SESSION_CONFIG['timeout_minutes'] = 5
    EVENT_PROCESSING_CONFIG['queue_size'] = 100
    STREAM_CONFIG['queue_size'] = 100
    ANALYTICS_CONFIG['cache_ttl_seconds'] = 10
    
    MONITORING_CONFIG['log_level'] = 'WARNING'
    MONITORING_CONFIG['metrics_collection']['enabled'] = False
    PERFORMANCE_CONFIG['monitoring']['performance_logging'] = False

# Environment Variables
ENVIRONMENT_VARIABLES = {
    'REALTIME_ENABLED': os.getenv('REALTIME_ENABLED', 'True'),
    'WEBSOCKET_ENABLED': os.getenv('WEBSOCKET_ENABLED', 'True'),
    'EVENT_PROCESSING_ENABLED': os.getenv('EVENT_PROCESSING_ENABLED', 'True'),
    'STREAM_PROCESSING_ENABLED': os.getenv('STREAM_PROCESSING_ENABLED', 'True'),
    'REALTIME_ANALYTICS_ENABLED': os.getenv('REALTIME_ANALYTICS_ENABLED', 'True'),
    'WEBSOCKET_HOST': os.getenv('WEBSOCKET_HOST', '0.0.0.0'),
    'WEBSOCKET_PORT': os.getenv('WEBSOCKET_PORT', '5000'),
    'REDIS_URL': os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    'REALTIME_SECRET_KEY': os.getenv('REALTIME_SECRET_KEY'),
    'REALTIME_ENCRYPTION_KEY': os.getenv('REALTIME_ENCRYPTION_KEY')
}

# WebSocket Event Types
WEBSOCKET_EVENT_TYPES = {
    'connection': {
        'connected': 'Client connected',
        'disconnected': 'Client disconnected',
        'error': 'Connection error',
        'timeout': 'Connection timeout'
    },
    'chat': {
        'message': 'Chat message',
        'typing': 'User typing',
        'join': 'User joined chat',
        'leave': 'User left chat',
        'room_created': 'Room created',
        'room_deleted': 'Room deleted'
    },
    'notification': {
        'new': 'New notification',
        'read': 'Notification read',
        'dismissed': 'Notification dismissed'
    },
    'system': {
        'status': 'System status update',
        'maintenance': 'System maintenance',
        'shutdown': 'System shutdown',
        'restart': 'System restart'
    },
    'user': {
        'online': 'User online',
        'offline': 'User offline',
        'status_change': 'User status changed',
        'profile_update': 'User profile updated'
    }
}

# Stream Data Schemas
STREAM_DATA_SCHEMAS = {
    'user_activity': {
        'user_id': {'type': int, 'required': True},
        'activity_type': {'type': str, 'required': True},
        'activity_data': {'type': dict, 'required': False},
        'timestamp': {'type': str, 'required': True},
        'ip_address': {'type': str, 'required': False},
        'user_agent': {'type': str, 'required': False}
    },
    'system_metrics': {
        'metric_name': {'type': str, 'required': True},
        'metric_value': {'type': float, 'required': True},
        'metric_unit': {'type': str, 'required': False},
        'timestamp': {'type': str, 'required': True},
        'tags': {'type': dict, 'required': False}
    },
    'chat': {
        'message_id': {'type': str, 'required': True},
        'room_id': {'type': str, 'required': True},
        'user_id': {'type': int, 'required': True},
        'message': {'type': str, 'required': True},
        'message_type': {'type': str, 'required': False},
        'timestamp': {'type': str, 'required': True}
    },
    'notifications': {
        'notification_id': {'type': str, 'required': True},
        'user_id': {'type': int, 'required': True},
        'notification_type': {'type': str, 'required': True},
        'title': {'type': str, 'required': True},
        'message': {'type': str, 'required': True},
        'data': {'type': dict, 'required': False},
        'timestamp': {'type': str, 'required': True}
    },
    'performance': {
        'metric_name': {'type': str, 'required': True},
        'value': {'type': float, 'required': True},
        'unit': {'type': str, 'required': False},
        'tags': {'type': dict, 'required': False},
        'timestamp': {'type': str, 'required': True}
    },
    'analytics': {
        'metric_name': {'type': str, 'required': True},
        'metric_value': {'type': float, 'required': True},
        'metric_type': {'type': str, 'required': True},
        'dimensions': {'type': dict, 'required': False},
        'timestamp': {'type': str, 'required': True}
    }
}

# Validation Functions
def validate_realtime_config():
    """Validate real-time configuration"""
    errors = []
    
    # Check required environment variables
    required_vars = ['REALTIME_SECRET_KEY']
    for var in required_vars:
        if not os.getenv(var):
            errors.append(f"Missing required environment variable: {var}")
    
    # Check configuration consistency
    if WEBSOCKET_CONFIG['max_connections'] > 10000:
        errors.append("WebSocket max_connections too high (max 10000)")
    
    if SESSION_CONFIG['timeout_minutes'] > 1440:  # 24 hours
        errors.append("Session timeout too long (max 24 hours)")
    
    if EVENT_PROCESSING_CONFIG['queue_size'] > 100000:
        errors.append("Event queue size too large (max 100000)")
    
    return errors

def get_realtime_config():
    """Get complete real-time configuration"""
    return {
        'realtime_enabled': REALTIME_ENABLED,
        'websocket_enabled': WEBSOCKET_ENABLED,
        'event_processing_enabled': EVENT_PROCESSING_ENABLED,
        'stream_processing_enabled': STREAM_PROCESSING_ENABLED,
        'realtime_analytics_enabled': REALTIME_ANALYTICS_ENABLED,
        'websocket_config': WEBSOCKET_CONFIG,
        'session_config': SESSION_CONFIG,
        'room_config': ROOM_CONFIG,
        'event_processing_config': EVENT_PROCESSING_CONFIG,
        'stream_config': STREAM_CONFIG,
        'analytics_config': ANALYTICS_CONFIG,
        'realtime_security_config': REALTIME_SECURITY_CONFIG,
        'performance_config': PERFORMANCE_CONFIG,
        'monitoring_config': MONITORING_CONFIG,
        'integration_config': INTEGRATION_CONFIG
    }
