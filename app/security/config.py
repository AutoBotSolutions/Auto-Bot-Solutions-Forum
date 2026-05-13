"""
Security Configuration

Configuration settings for security monitoring, threat detection, and compliance tracking.
"""

import os
from datetime import timedelta

# Security System Configuration
SECURITY_ENABLED = True
THREAT_DETECTION_ENABLED = True
AUDIT_TRAIL_ENABLED = True
COMPLIANCE_ENABLED = True

# Security Event Configuration
SECURITY_EVENT_CONFIG = {
    'retention_days': 90,
    'max_events_per_minute': 1000,
    'severity_levels': ['low', 'medium', 'high', 'critical'],
    'event_categories': ['authentication', 'authorization', 'data_access', 'system'],
    'auto_cleanup_enabled': True,
    'cleanup_interval_hours': 24
}

# Threat Detection Configuration
THREAT_DETECTION_CONFIG = {
    'enabled': True,
    'risk_threshold': 0.7,
    'confidence_threshold': 0.6,
    'detection_rules': {
        'brute_force': {
            'enabled': True,
            'failed_attempts_threshold': 5,
            'time_window_minutes': 60,
            'risk_score_multiplier': 0.2
        },
        'sql_injection': {
            'enabled': True,
            'patterns': [
                'union select',
                'drop table',
                'insert into',
                'exec(',
                'script>',
                'javascript:'
            ],
            'risk_score_multiplier': 0.8
        },
        'xss': {
            'enabled': True,
            'patterns': [
                '<script>',
                'javascript:',
                'onload=',
                'onerror=',
                'alert('
            ],
            'risk_score_multiplier': 0.6
        },
        'ddos': {
            'enabled': True,
            'requests_per_minute_threshold': 100,
            'time_window_minutes': 5,
            'risk_score_multiplier': 0.9
        },
        'suspicious_activity': {
            'enabled': True,
            'indicators': [
                'excessive_logins',
                'multiple_ip_access',
                'high_failure_rate',
                'unusual_access_patterns'
            ],
            'risk_score_multiplier': 0.4
        }
    },
    'auto_response_enabled': True,
    'notification_enabled': True
}

# Audit Trail Configuration
AUDIT_TRAIL_CONFIG = {
    'enabled': True,
    'retention_days': 365,
    'track_all_actions': True,
    'sensitive_actions': [
        'user_create',
        'user_delete',
        'role_change',
        'permission_change',
        'data_export',
        'system_config_change'
    ],
    'auto_cleanup_enabled': True,
    'cleanup_interval_days': 7,
    'compression_enabled': True
}

# Compliance Configuration
COMPLIANCE_CONFIG = {
    'enabled': True,
    'regulations': {
        'gdpr': {
            'enabled': True,
            'data_retention_days': 365,
            'consent_required': True,
            'right_to_deletion': True,
            'data_portability': True,
            'privacy_by_design': True
        },
        'ccpa': {
            'enabled': True,
            'data_retention_days': 730,
            'right_to_deletion': True,
            'data_portability': True,
            'opt_out_required': True
        },
        'hipaa': {
            'enabled': False,
            'data_retention_days': 2555,  # 7 years
            'encryption_required': True,
            'access_logs_required': True,
            'audit_trail_required': True
        },
        'sox': {
            'enabled': False,
            'data_retention_days': 2555,  # 7 years
            'audit_trail_required': True,
            'segregation_of_duties': True,
            'internal_controls': True
        }
    },
    'auto_assessment_enabled': True,
    'assessment_frequency_days': 30,
    'report_generation_enabled': True,
    'alert_thresholds': {
        'compliance_score_threshold': 0.8,
        'non_compliant_items_threshold': 5,
        'high_risk_items_threshold': 2
    }
}

# Security Monitoring Configuration
SECURITY_MONITORING_CONFIG = {
    'enabled': True,
    'real_time_monitoring': True,
    'dashboard_refresh_interval_seconds': 30,
    'alert_thresholds': {
        'failed_logins_per_hour': 10,
        'suspicious_activities_per_hour': 20,
        'high_risk_threats_per_hour': 5,
        'compliance_issues_threshold': 3
    },
    'notification_channels': {
        'email': {
            'enabled': True,
            'recipients': ['security@company.com'],
            'severity_threshold': 'high'
        },
        'slack': {
            'enabled': False,
            'webhook_url': os.getenv('SECURITY_SLACK_WEBHOOK'),
            'severity_threshold': 'critical'
        },
        'sms': {
            'enabled': False,
            'phone_numbers': [],
            'severity_threshold': 'critical'
        }
    }
}

# Data Protection Configuration
DATA_PROTECTION_CONFIG = {
    'encryption_enabled': True,
    'encryption_algorithm': 'AES-256',
    'hash_algorithm': 'SHA-256',
    'salt_length': 32,
    'sensitive_fields': [
        'password',
        'credit_card',
        'ssn',
        'api_key',
        'secret_key',
        'private_key'
    ],
    'data_masking_enabled': True,
    'anonymization_enabled': True,
    'pseudonymization_enabled': True
}

# Session Security Configuration
SESSION_SECURITY_CONFIG = {
    'fingerprinting_enabled': True,
    'session_timeout_minutes': 30,
    'max_concurrent_sessions': 3,
    'require_https': True,
    'secure_cookies': True,
    'same_site_policy': 'Strict',
    'csrf_protection': True,
    'rate_limiting': {
        'enabled': True,
        'requests_per_minute': 60,
        'burst_size': 10
    }
}

# IP Security Configuration
IP_SECURITY_CONFIG = {
    'whitelist_enabled': False,
    'whitelist_ips': [],
    'blacklist_enabled': True,
    'blacklist_ips': [],
    'geo_blocking_enabled': False,
    'blocked_countries': [],
    'rate_limiting_per_ip': {
        'enabled': True,
        'requests_per_minute': 30,
        'burst_size': 5
    },
    'suspicious_ip_detection': {
        'enabled': True,
        'threshold_score': 0.7,
        'auto_blacklist': True,
        'blacklist_duration_hours': 24
    }
}

# User Agent Security Configuration
USER_AGENT_SECURITY_CONFIG = {
    'bot_detection_enabled': True,
    'blocked_user_agents': [
        'curl',
        'wget',
        'python-requests',
        'java',
        'perl',
        'powershell'
    ],
    'suspicious_patterns': [
        'bot',
        'crawler',
        'spider',
        'scanner',
        'scraper'
    ],
    'require_browser': False,
    'allowed_browsers': [
        'chrome',
        'firefox',
        'safari',
        'edge',
        'opera'
    ]
}

# API Security Configuration
API_SECURITY_CONFIG = {
    'authentication_required': True,
    'api_key_required': False,
    'rate_limiting': {
        'enabled': True,
        'requests_per_minute': 100,
        'burst_size': 20
    },
    'cors_enabled': True,
    'cors_origins': ['https://example.com'],
    'cors_methods': ['GET', 'POST', 'PUT', 'DELETE'],
    'cors_headers': ['Content-Type', 'Authorization'],
    'input_validation': {
        'enabled': True,
        'max_request_size_mb': 10,
        'allowed_content_types': ['application/json', 'multipart/form-data'],
        'sanitize_input': True
    }
}

# Logging Configuration
SECURITY_LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file_path': 'logs/security.log',
    'max_file_size_mb': 100,
    'backup_count': 5,
    'log_to_database': True,
    'log_to_file': True,
    'log_to_syslog': False,
    'structured_logging': True,
    'log_fields': [
        'timestamp',
        'level',
        'event_type',
        'user_id',
        'ip_address',
        'user_agent',
        'request_id'
    ]
}

# Backup and Recovery Configuration
BACKUP_CONFIG = {
    'enabled': True,
    'backup_frequency_hours': 24,
    'retention_days': 30,
    'encryption_enabled': True,
    'compression_enabled': True,
    'backup_types': {
        'security_events': True,
        'audit_trail': True,
        'threat_data': True,
        'compliance_records': True
    },
    'storage_locations': {
        'local': {
            'enabled': True,
            'path': '/backups/security'
        },
        's3': {
            'enabled': False,
            'bucket': 'security-backups',
            'region': 'us-east-1'
        }
    }
}

# Integration Configuration
INTEGRATION_CONFIG = {
    'siem_integration': {
        'enabled': False,
        'endpoint': '',
        'api_key': '',
        'format': 'json'
    },
    'threat_intelligence': {
        'enabled': False,
        'providers': [
            'virustotal',
            'abuseipdb',
            'shodan'
        ],
        'update_interval_hours': 24
    },
    'identity_provider': {
        'enabled': False,
        'provider': 'saml',
        'config': {}
    }
}

# Performance Configuration
PERFORMANCE_CONFIG = {
    'cache_enabled': True,
    'cache_ttl_seconds': 300,
    'batch_processing': {
        'enabled': True,
        'batch_size': 100,
        'processing_interval_seconds': 60
    },
    'async_processing': {
        'enabled': True,
        'queue_name': 'security_queue',
        'worker_processes': 2
    },
    'database_optimization': {
        'indexing_enabled': True,
        'partitioning_enabled': False,
        'compression_enabled': True
    }
}

# Development/Testing Configuration
if os.getenv('FLASK_ENV') == 'development':
    SECURITY_ENABLED = True
    THREAT_DETECTION_ENABLED = True
    AUDIT_TRAIL_ENABLED = True
    COMPLIANCE_ENABLED = False
    
    SECURITY_EVENT_CONFIG['retention_days'] = 7
    AUDIT_TRAIL_CONFIG['retention_days'] = 30
    
    SECURITY_MONITORING_CONFIG['real_time_monitoring'] = False
    SECURITY_MONITORING_CONFIG['dashboard_refresh_interval_seconds'] = 60
    
    BACKUP_CONFIG['enabled'] = False
    
    INTEGRATION_CONFIG['siem_integration']['enabled'] = False
    INTEGRATION_CONFIG['threat_intelligence']['enabled'] = False

# Production Configuration
if os.getenv('FLASK_ENV') == 'production':
    SECURITY_ENABLED = True
    THREAT_DETECTION_ENABLED = True
    AUDIT_TRAIL_ENABLED = True
    COMPLIANCE_ENABLED = True
    
    SECURITY_EVENT_CONFIG['retention_days'] = 90
    AUDIT_TRAIL_CONFIG['retention_days'] = 365
    
    SECURITY_MONITORING_CONFIG['real_time_monitoring'] = True
    SECURITY_MONITORING_CONFIG['dashboard_refresh_interval_seconds'] = 30
    
    BACKUP_CONFIG['enabled'] = True
    BACKUP_CONFIG['backup_frequency_hours'] = 24
    
    INTEGRATION_CONFIG['siem_integration']['enabled'] = True
    INTEGRATION_CONFIG['threat_intelligence']['enabled'] = True
    
    SESSION_SECURITY_CONFIG['require_https'] = True
    SESSION_SECURITY_CONFIG['secure_cookies'] = True
    
    API_SECURITY_CONFIG['authentication_required'] = True
    API_SECURITY_CONFIG['rate_limiting']['requests_per_minute'] = 100

# Security Headers Configuration
SECURITY_HEADERS = {
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'X-XSS-Protection': '1; mode=block',
    'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
    'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';",
    'Referrer-Policy': 'strict-origin-when-cross-origin',
    'Permissions-Policy': 'geolocation=(), microphone=(), camera=()'
}

# Environment Variables
ENVIRONMENT_VARIABLES = {
    'SECURITY_ENABLED': os.getenv('SECURITY_ENABLED', 'True'),
    'THREAT_DETECTION_ENABLED': os.getenv('THREAT_DETECTION_ENABLED', 'True'),
    'AUDIT_TRAIL_ENABLED': os.getenv('AUDIT_TRAIL_ENABLED', 'True'),
    'COMPLIANCE_ENABLED': os.getenv('COMPLIANCE_ENABLED', 'True'),
    'SECURITY_LOG_LEVEL': os.getenv('SECURITY_LOG_LEVEL', 'INFO'),
    'SECURITY_ENCRYPTION_KEY': os.getenv('SECURITY_ENCRYPTION_KEY'),
    'SECURITY_SALT': os.getenv('SECURITY_SALT'),
    'SECURITY_API_KEY': os.getenv('SECURITY_API_KEY'),
    'SECURITY_WEBHOOK_SECRET': os.getenv('SECURITY_WEBHOOK_SECRET')
}

# Validation Functions
def validate_security_config():
    """Validate security configuration"""
    errors = []
    
    # Check required environment variables
    required_vars = ['SECURITY_ENCRYPTION_KEY', 'SECURITY_SALT']
    for var in required_vars:
        if not os.getenv(var):
            errors.append(f"Missing required environment variable: {var}")
    
    # Check configuration consistency
    if SESSION_SECURITY_CONFIG['require_https'] and not os.getenv('HTTPS_ENABLED'):
        errors.append("HTTPS is required but not enabled")
    
    if BACKUP_CONFIG['enabled'] and not BACKUP_CONFIG['storage_locations']['local']['enabled']:
        if not BACKUP_CONFIG['storage_locations']['s3']['enabled']:
            errors.append("Backup enabled but no storage location configured")
    
    return errors

def get_security_config():
    """Get complete security configuration"""
    return {
        'security_enabled': SECURITY_ENABLED,
        'threat_detection_enabled': THREAT_DETECTION_ENABLED,
        'audit_trail_enabled': AUDIT_TRAIL_ENABLED,
        'compliance_enabled': COMPLIANCE_ENABLED,
        'security_event_config': SECURITY_EVENT_CONFIG,
        'threat_detection_config': THREAT_DETECTION_CONFIG,
        'audit_trail_config': AUDIT_TRAIL_CONFIG,
        'compliance_config': COMPLIANCE_CONFIG,
        'security_monitoring_config': SECURITY_MONITORING_CONFIG,
        'data_protection_config': DATA_PROTECTION_CONFIG,
        'session_security_config': SESSION_SECURITY_CONFIG,
        'ip_security_config': IP_SECURITY_CONFIG,
        'user_agent_security_config': USER_AGENT_SECURITY_CONFIG,
        'api_security_config': API_SECURITY_CONFIG,
        'security_logging_config': SECURITY_LOGGING_CONFIG,
        'backup_config': BACKUP_CONFIG,
        'integration_config': INTEGRATION_CONFIG,
        'performance_config': PERFORMANCE_CONFIG,
        'security_headers': SECURITY_HEADERS
    }
