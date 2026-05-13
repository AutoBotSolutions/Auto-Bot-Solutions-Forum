"""
Notification System Configuration

This module handles loading and validating notification system configuration
from environment variables and provides a centralized configuration interface.
"""

import os
from typing import Dict, List, Optional, Union
from dataclasses import dataclass, field
from datetime import timedelta


@dataclass
class NotificationConfig:
    """Notification system configuration class"""
    
    # Core Settings
    enabled: bool = True
    max_length: int = 500
    rate_limit: str = "100 per hour"
    batch_size: int = 100
    archive_days: int = 30
    
    # WebSocket Settings
    websocket_url: str = "ws://localhost:5003"
    websocket_host: str = "localhost"
    websocket_port: int = 5003
    websocket_debug: bool = False
    websocket_secret_key: str = ""
    websocket_cors_origins: List[str] = field(default_factory=lambda: ["http://localhost:5000"])
    websocket_max_connections: int = 1000
    websocket_heartbeat_interval: int = 25
    websocket_heartbeat_timeout: int = 60
    
    # Email Settings
    email_enabled: bool = True
    smtp_server: str = ""
    smtp_port: int = 587
    smtp_use_tls: bool = True
    smtp_use_ssl: bool = False
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_default_sender: str = "noreply@yourdomain.com"
    smtp_default_sender_name: str = "AutoBot Solutions Forum"
    email_batch_size: int = 50
    email_retry_attempts: int = 3
    email_retry_delay: int = 5
    email_queue_enabled: bool = True
    email_queue_workers: int = 4
    email_queue_max_size: int = 1000
    email_queue_processing_interval: int = 30
    email_template_dir: str = "app/templates/email/notifications"
    email_template_cache_enabled: bool = True
    
    # Push Notification Settings
    push_enabled: bool = True
    push_batch_size: int = 100
    push_retry_attempts: int = 3
    push_retry_delay: int = 2
    vapid_public_key: str = ""
    vapid_private_key: str = ""
    vapid_subject: str = "mailto:admin@yourdomain.com"
    
    # APNS Settings
    apns_enabled: bool = True
    apns_key_file: str = ""
    apns_key_id: str = ""
    apns_team_id: str = ""
    apns_bundle_id: str = ""
    apns_sandbox: bool = True
    
    # FCM Settings
    fcm_enabled: bool = True
    fcm_server_key: str = ""
    fcm_sender_id: str = ""
    
    # HMS Settings
    hms_enabled: bool = True
    hms_app_id: str = ""
    hms_app_secret: str = ""
    
    # Mobile Settings
    mobile_enabled: bool = True
    mobile_max_devices_per_user: int = 10
    mobile_device_expiry_days: int = 365
    mobile_cleanup_interval: int = 24
    mobile_platforms_enabled: List[str] = field(default_factory=lambda: ["ios", "android", "huawei", "web"])
    mobile_notification_types: List[str] = field(default_factory=lambda: ["forum_activity", "messages", "moderation", "security", "system", "marketing"])
    
    # Translation Settings
    translation_enabled: bool = True
    translation_default_language: str = "en"
    translation_cache_enabled: bool = True
    translation_cache_ttl: int = 3600
    translation_supported_languages: List[str] = field(default_factory=lambda: ["en", "es", "fr", "de", "it", "pt", "ru", "zh", "ja", "ko", "ar", "hi"])
    translation_api_enabled: bool = False
    translation_api_key: str = ""
    translation_api_url: str = ""
    
    # Filtering Settings
    filtering_enabled: bool = True
    filtering_cache_enabled: bool = True
    filtering_cache_ttl: int = 1800
    filtering_max_custom_filters: int = 50
    
    # Grouping Settings
    grouping_enabled: bool = True
    grouping_similarity_threshold: float = 0.7
    grouping_max_group_size: int = 20
    grouping_cache_enabled: bool = True
    
    # Pattern Analysis Settings
    pattern_analysis_enabled: bool = True
    pattern_analysis_min_data_points: int = 10
    pattern_analysis_cache_ttl: int = 7200
    
    # Archiving Settings
    archiving_enabled: bool = True
    archiving_auto_enabled: bool = True
    archiving_schedule: str = "0 2 * * *"
    archiving_batch_size: int = 500
    archiving_read_older_than_days: int = 90
    archiving_unread_older_than_days: int = 365
    archiving_keep_important: bool = True
    archiving_keep_unread: bool = True
    archiving_storage_type: str = "database"
    archiving_retention_days: int = 1095
    archiving_compression_enabled: bool = True
    
    # Scheduling Settings
    scheduling_enabled: bool = True
    scheduling_timezone: str = "UTC"
    scheduling_batch_size: int = 100
    digest_enabled: bool = True
    digest_default_time: str = "09:00"
    digest_weekly_day: str = "monday"
    digest_max_notifications: int = 50
    quiet_hours_enabled: bool = True
    quiet_hours_default_start: str = "22:00"
    quiet_hours_default_end: str = "08:00"
    quiet_hours_weekend_enabled: bool = True
    quiet_hours_weekend_start: str = "23:00"
    quiet_hours_weekend_end: str = "09:00"
    
    # Analytics Settings
    analytics_enabled: bool = True
    analytics_retention_days: int = 365
    analytics_batch_size: int = 1000
    performance_monitoring_enabled: bool = True
    performance_sample_rate: float = 0.1
    performance_slow_query_threshold: int = 1000
    error_tracking_enabled: bool = True
    error_notification_email: str = "admin@yourdomain.com"
    error_webhook_url: str = ""
    
    # Security Settings
    security_enabled: bool = True
    encryption_enabled: bool = False
    signature_enabled: bool = True
    rate_limiting_enabled: bool = True
    rate_limit_notifications: int = 100
    rate_limit_window: int = 3600
    rate_limit_strategy: str = "sliding-window"
    access_control_enabled: bool = True
    permission_check_enabled: bool = True
    admin_override_enabled: bool = True
    
    # Development Settings
    debug_notifications: bool = False
    debug_level: str = "INFO"
    log_queries: bool = False
    test_mode: bool = False
    test_email_recipient: str = "test@yourdomain.com"
    test_mobile_device_token: str = "test-device-token"
    
    # Redis Settings
    redis_url: str = "redis://localhost:6379/0"
    redis_notification_db: int = 1
    redis_cache_db: int = 2
    redis_queue_db: int = 3
    redis_connection_pool_size: int = 10
    redis_connection_timeout: int = 5
    redis_socket_timeout: int = 5
    redis_retry_on_timeout: bool = True
    
    # Database Settings
    db_pool_size: int = 20
    db_max_overflow: int = 30
    db_pool_timeout: int = 30
    db_indexing_enabled: bool = True
    db_partitioning_enabled: bool = False
    db_sharding_enabled: bool = False
    
    # Logging Settings
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_file: str = "logs/notifications.log"
    log_max_size: int = 10485760  # 10MB
    log_backup_count: int = 5
    
    # Feature Flags
    feature_advanced_filtering: bool = True
    feature_smart_grouping: bool = True
    feature_ai_translations: bool = False
    feature_voice_notifications: bool = False
    feature_video_notifications: bool = False
    beta_features_enabled: bool = False
    
    # Compliance Settings
    gdpr_compliance_enabled: bool = True
    data_retention_days: int = 2555  # 7 years
    anonymization_enabled: bool = True
    privacy_mode_enabled: bool = False
    content_encryption_enabled: bool = False
    metadata_encryption_enabled: bool = False
    
    # Health Check Settings
    health_check_enabled: bool = True
    health_check_interval: int = 60
    health_check_timeout: int = 10
    metrics_enabled: bool = True
    metrics_endpoint: str = "/metrics"
    metrics_port: int = 9090
    
    # Alerting Settings
    alerting_enabled: bool = True
    alerting_webhook_url: str = ""
    alerting_threshold_error_rate: float = 0.05
    alerting_threshold_response_time: int = 1000


class NotificationConfigLoader:
    """Loads and validates notification configuration from environment variables"""
    
    def __init__(self):
        self.config = NotificationConfig()
        self.load_config()
        self.validate_config()
    
    def load_config(self):
        """Load configuration from environment variables"""
        
        # Core Settings
        self.config.enabled = self._get_bool('NOTIFICATION_ENABLED', True)
        self.config.max_length = self._get_int('NOTIFICATION_MAX_LENGTH', 500)
        self.config.rate_limit = self._get_str('NOTIFICATION_RATE_LIMIT', "100 per hour")
        self.config.batch_size = self._get_int('NOTIFICATION_BATCH_SIZE', 100)
        self.config.archive_days = self._get_int('NOTIFICATION_ARCHIVE_DAYS', 30)
        
        # WebSocket Settings
        self.config.websocket_url = self._get_str('WEBSOCKET_NOTIFICATION_URL', "ws://localhost:5003")
        self.config.websocket_host = self._get_str('WEBSOCKET_NOTIFICATION_HOST', "localhost")
        self.config.websocket_port = self._get_int('WEBSOCKET_NOTIFICATION_PORT', 5003)
        self.config.websocket_debug = self._get_bool('WEBSOCKET_NOTIFICATION_DEBUG', False)
        self.config.websocket_secret_key = self._get_str('WEBSOCKET_SECRET_KEY', "")
        self.config.websocket_cors_origins = self._get_list('WEBSOCKET_CORS_ALLOWED_ORIGINS', ["http://localhost:5000"])
        self.config.websocket_max_connections = self._get_int('WEBSOCKET_MAX_CONNECTIONS', 1000)
        self.config.websocket_heartbeat_interval = self._get_int('WEBSOCKET_HEARTBEAT_INTERVAL', 25)
        self.config.websocket_heartbeat_timeout = self._get_int('WEBSOCKET_HEARTBEAT_TIMEOUT', 60)
        
        # Email Settings
        self.config.email_enabled = self._get_bool('EMAIL_NOTIFICATION_ENABLED', True)
        self.config.smtp_server = self._get_str('SMTP_NOTIFICATION_SERVER', "")
        self.config.smtp_port = self._get_int('SMTP_NOTIFICATION_PORT', 587)
        self.config.smtp_use_tls = self._get_bool('SMTP_NOTIFICATION_USE_TLS', True)
        self.config.smtp_use_ssl = self._get_bool('SMTP_NOTIFICATION_USE_SSL', False)
        self.config.smtp_username = self._get_str('SMTP_NOTIFICATION_USERNAME', "")
        self.config.smtp_password = self._get_str('SMTP_NOTIFICATION_PASSWORD', "")
        self.config.smtp_default_sender = self._get_str('SMTP_NOTIFICATION_DEFAULT_SENDER', "noreply@yourdomain.com")
        self.config.smtp_default_sender_name = self._get_str('SMTP_NOTIFICATION_DEFAULT_SENDER_NAME', "AutoBot Solutions Forum")
        self.config.email_batch_size = self._get_int('EMAIL_NOTIFICATION_BATCH_SIZE', 50)
        self.config.email_retry_attempts = self._get_int('EMAIL_NOTIFICATION_RETRY_ATTEMPTS', 3)
        self.config.email_retry_delay = self._get_int('EMAIL_NOTIFICATION_RETRY_DELAY', 5)
        self.config.email_queue_enabled = self._get_bool('EMAIL_QUEUE_ENABLED', True)
        self.config.email_queue_workers = self._get_int('EMAIL_QUEUE_WORKERS', 4)
        self.config.email_queue_max_size = self._get_int('EMAIL_QUEUE_MAX_SIZE', 1000)
        self.config.email_queue_processing_interval = self._get_int('EMAIL_QUEUE_PROCESSING_INTERVAL', 30)
        self.config.email_template_dir = self._get_str('EMAIL_TEMPLATE_DIR', "app/templates/email/notifications")
        self.config.email_template_cache_enabled = self._get_bool('EMAIL_TEMPLATE_CACHE_ENABLED', True)
        
        # Push Notification Settings
        self.config.push_enabled = self._get_bool('PUSH_NOTIFICATION_ENABLED', True)
        self.config.push_batch_size = self._get_int('PUSH_NOTIFICATION_BATCH_SIZE', 100)
        self.config.push_retry_attempts = self._get_int('PUSH_NOTIFICATION_RETRY_ATTEMPTS', 3)
        self.config.push_retry_delay = self._get_int('PUSH_NOTIFICATION_RETRY_DELAY', 2)
        self.config.vapid_public_key = self._get_str('VAPID_PUBLIC_KEY', "")
        self.config.vapid_private_key = self._get_str('VAPID_PRIVATE_KEY', "")
        self.config.vapid_subject = self._get_str('VAPID_SUBJECT', "mailto:admin@yourdomain.com")
        
        # APNS Settings
        self.config.apns_enabled = self._get_bool('APNS_ENABLED', True)
        self.config.apns_key_file = self._get_str('APNS_KEY_FILE', "")
        self.config.apns_key_id = self._get_str('APNS_KEY_ID', "")
        self.config.apns_team_id = self._get_str('APNS_TEAM_ID', "")
        self.config.apns_bundle_id = self._get_str('APNS_BUNDLE_ID', "")
        self.config.apns_sandbox = self._get_bool('APNS_SANDBOX', True)
        
        # FCM Settings
        self.config.fcm_enabled = self._get_bool('FCM_ENABLED', True)
        self.config.fcm_server_key = self._get_str('FCM_SERVER_KEY', "")
        self.config.fcm_sender_id = self._get_str('FCM_SENDER_ID', "")
        
        # HMS Settings
        self.config.hms_enabled = self._get_bool('HMS_ENABLED', True)
        self.config.hms_app_id = self._get_str('HMS_APP_ID', "")
        self.config.hms_app_secret = self._get_str('HMS_APP_SECRET', "")
        
        # Mobile Settings
        self.config.mobile_enabled = self._get_bool('MOBILE_NOTIFICATION_ENABLED', True)
        self.config.mobile_max_devices_per_user = self._get_int('MOBILE_NOTIFICATION_MAX_DEVICES_PER_USER', 10)
        self.config.mobile_device_expiry_days = self._get_int('MOBILE_NOTIFICATION_DEVICE_EXPIRY_DAYS', 365)
        self.config.mobile_cleanup_interval = self._get_int('MOBILE_NOTIFICATION_CLEANUP_INTERVAL', 24)
        self.config.mobile_platforms_enabled = self._get_list('MOBILE_PLATFORMS_ENABLED', ["ios", "android", "huawei", "web"])
        self.config.mobile_notification_types = self._get_list('MOBILE_NOTIFICATION_TYPES', ["forum_activity", "messages", "moderation", "security", "system", "marketing"])
        
        # Translation Settings
        self.config.translation_enabled = self._get_bool('TRANSLATION_ENABLED', True)
        self.config.translation_default_language = self._get_str('TRANSLATION_DEFAULT_LANGUAGE', "en")
        self.config.translation_cache_enabled = self._get_bool('TRANSLATION_CACHE_ENABLED', True)
        self.config.translation_cache_ttl = self._get_int('TRANSLATION_CACHE_TTL', 3600)
        self.config.translation_supported_languages = self._get_list('TRANSLATION_SUPPORTED_LANGUAGES', ["en", "es", "fr", "de", "it", "pt", "ru", "zh", "ja", "ko", "ar", "hi"])
        self.config.translation_api_enabled = self._get_bool('TRANSLATION_API_ENABLED', False)
        self.config.translation_api_key = self._get_str('TRANSLATION_API_KEY', "")
        self.config.translation_api_url = self._get_str('TRANSLATION_API_URL', "")
        
        # Filtering Settings
        self.config.filtering_enabled = self._get_bool('FILTERING_ENABLED', True)
        self.config.filtering_cache_enabled = self._get_bool('FILTERING_CACHE_ENABLED', True)
        self.config.filtering_cache_ttl = self._get_int('FILTERING_CACHE_TTL', 1800)
        self.config.filtering_max_custom_filters = self._get_int('FILTERING_MAX_CUSTOM_FILTERS', 50)
        
        # Grouping Settings
        self.config.grouping_enabled = self._get_bool('GROUPING_ENABLED', True)
        self.config.grouping_similarity_threshold = self._get_float('GROUPING_SIMILARITY_THRESHOLD', 0.7)
        self.config.grouping_max_group_size = self._get_int('GROUPING_MAX_GROUP_SIZE', 20)
        self.config.grouping_cache_enabled = self._get_bool('GROUPING_CACHE_ENABLED', True)
        
        # Pattern Analysis Settings
        self.config.pattern_analysis_enabled = self._get_bool('PATTERN_ANALYSIS_ENABLED', True)
        self.config.pattern_analysis_min_data_points = self._get_int('PATTERN_ANALYSIS_MIN_DATA_POINTS', 10)
        self.config.pattern_analysis_cache_ttl = self._get_int('PATTERN_ANALYSIS_CACHE_TTL', 7200)
        
        # Archiving Settings
        self.config.archiving_enabled = self._get_bool('ARCHIVING_ENABLED', True)
        self.config.archiving_auto_enabled = self._get_bool('ARCHIVING_AUTO_ENABLED', True)
        self.config.archiving_schedule = self._get_str('ARCHIVING_SCHEDULE', "0 2 * * *")
        self.config.archiving_batch_size = self._get_int('ARCHIVING_BATCH_SIZE', 500)
        self.config.archiving_read_older_than_days = self._get_int('ARCHIVING_READ_OLDER_THAN_DAYS', 90)
        self.config.archiving_unread_older_than_days = self._get_int('ARCHIVING_UNREAD_OLDER_THAN_DAYS', 365)
        self.config.archiving_keep_important = self._get_bool('ARCHIVING_KEEP_IMPORTANT', True)
        self.config.archiving_keep_unread = self._get_bool('ARCHIVING_KEEP_UNREAD', True)
        self.config.archiving_storage_type = self._get_str('ARCHIVING_STORAGE_TYPE', "database")
        self.config.archiving_retention_days = self._get_int('ARCHIVING_RETENTION_DAYS', 1095)
        self.config.archiving_compression_enabled = self._get_bool('ARCHIVING_COMPRESSION_ENABLED', True)
        
        # Scheduling Settings
        self.config.scheduling_enabled = self._get_bool('SCHEDULING_ENABLED', True)
        self.config.scheduling_timezone = self._get_str('SCHEDULING_TIMEZONE', "UTC")
        self.config.scheduling_batch_size = self._get_int('SCHEDULING_BATCH_SIZE', 100)
        self.config.digest_enabled = self._get_bool('DIGEST_ENABLED', True)
        self.config.digest_default_time = self._get_str('DIGEST_DEFAULT_TIME', "09:00")
        self.config.digest_weekly_day = self._get_str('DIGEST_WEEKLY_DAY', "monday")
        self.config.digest_max_notifications = self._get_int('DIGEST_MAX_NOTIFICATIONS', 50)
        self.config.quiet_hours_enabled = self._get_bool('QUIET_HOURS_ENABLED', True)
        self.config.quiet_hours_default_start = self._get_str('QUIET_HOURS_DEFAULT_START', "22:00")
        self.config.quiet_hours_default_end = self._get_str('QUIET_HOURS_DEFAULT_END', "08:00")
        self.config.quiet_hours_weekend_enabled = self._get_bool('QUIET_HOURS_WEEKEND_ENABLED', True)
        self.config.quiet_hours_weekend_start = self._get_str('QUIET_HOURS_WEEKEND_START', "23:00")
        self.config.quiet_hours_weekend_end = self._get_str('QUIET_HOURS_WEEKEND_END', "09:00")
        
        # Analytics Settings
        self.config.analytics_enabled = self._get_bool('NOTIFICATION_ANALYTICS_ENABLED', True)
        self.config.analytics_retention_days = self._get_int('ANALYTICS_RETENTION_DAYS', 365)
        self.config.analytics_batch_size = self._get_int('ANALYTICS_BATCH_SIZE', 1000)
        self.config.performance_monitoring_enabled = self._get_bool('PERFORMANCE_MONITORING_ENABLED', True)
        self.config.performance_sample_rate = self._get_float('PERFORMANCE_SAMPLE_RATE', 0.1)
        self.config.performance_slow_query_threshold = self._get_int('PERFORMANCE_SLOW_QUERY_THRESHOLD', 1000)
        self.config.error_tracking_enabled = self._get_bool('ERROR_TRACKING_ENABLED', True)
        self.config.error_notification_email = self._get_str('ERROR_NOTIFICATION_EMAIL', "admin@yourdomain.com")
        self.config.error_webhook_url = self._get_str('ERROR_WEBHOOK_URL', "")
        
        # Security Settings
        self.config.security_enabled = self._get_bool('NOTIFICATION_SECURITY_ENABLED', True)
        self.config.encryption_enabled = self._get_bool('NOTIFICATION_ENCRYPTION_ENABLED', False)
        self.config.signature_enabled = self._get_bool('NOTIFICATION_SIGNATURE_ENABLED', True)
        self.config.rate_limiting_enabled = self._get_bool('RATE_LIMITING_ENABLED', True)
        self.config.rate_limit_notifications = self._get_int('RATE_LIMIT_NOTIFICATIONS', 100)
        self.config.rate_limit_window = self._get_int('RATE_LIMIT_WINDOW', 3600)
        self.config.rate_limit_strategy = self._get_str('RATE_LIMIT_STRATEGY', "sliding-window")
        self.config.access_control_enabled = self._get_bool('ACCESS_CONTROL_ENABLED', True)
        self.config.permission_check_enabled = self._get_bool('NOTIFICATION_PERMISSION_CHECK', True)
        self.config.admin_override_enabled = self._get_bool('ADMIN_NOTIFICATION_OVERRIDE', True)
        
        # Development Settings
        self.config.debug_notifications = self._get_bool('DEBUG_NOTIFICATIONS', False)
        self.config.debug_level = self._get_str('NOTIFICATION_DEBUG_LEVEL', "INFO")
        self.config.log_queries = self._get_bool('NOTIFICATION_LOG_QUERIES', False)
        self.config.test_mode = self._get_bool('TEST_NOTIFICATION_MODE', False)
        self.config.test_email_recipient = self._get_str('TEST_EMAIL_RECIPIENT', "test@yourdomain.com")
        self.config.test_mobile_device_token = self._get_str('TEST_MOBILE_DEVICE_TOKEN', "test-device-token")
        
        # Redis Settings
        self.config.redis_url = self._get_str('REDIS_URL', "redis://localhost:6379/0")
        self.config.redis_notification_db = self._get_int('REDIS_NOTIFICATION_DB', 1)
        self.config.redis_cache_db = self._get_int('REDIS_CACHE_DB', 2)
        self.config.redis_queue_db = self._get_int('REDIS_QUEUE_DB', 3)
        self.config.redis_connection_pool_size = self._get_int('REDIS_CONNECTION_POOL_SIZE', 10)
        self.config.redis_connection_timeout = self._get_int('REDIS_CONNECTION_TIMEOUT', 5)
        self.config.redis_socket_timeout = self._get_int('REDIS_SOCKET_TIMEOUT', 5)
        self.config.redis_retry_on_timeout = self._get_bool('REDIS_RETRY_ON_TIMEOUT', True)
        
        # Database Settings
        self.config.db_pool_size = self._get_int('DATABASE_NOTIFICATION_POOL_SIZE', 20)
        self.config.db_max_overflow = self._get_int('DATABASE_NOTIFICATION_MAX_OVERFLOW', 30)
        self.config.db_pool_timeout = self._get_int('DATABASE_NOTIFICATION_POOL_TIMEOUT', 30)
        self.config.db_indexing_enabled = self._get_bool('NOTIFICATION_DB_INDEXING_ENABLED', True)
        self.config.db_partitioning_enabled = self._get_bool('NOTIFICATION_DB_PARTITIONING_ENABLED', False)
        self.config.db_sharding_enabled = self._get_bool('NOTIFICATION_DB_SHARDING_ENABLED', False)
        
        # Logging Settings
        self.config.log_level = self._get_str('NOTIFICATION_LOG_LEVEL', "INFO")
        self.config.log_format = self._get_str('NOTIFICATION_LOG_FORMAT', "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        self.config.log_file = self._get_str('NOTIFICATION_LOG_FILE', "logs/notifications.log")
        self.config.log_max_size = self._get_int('NOTIFICATION_LOG_MAX_SIZE', 10485760)
        self.config.log_backup_count = self._get_int('NOTIFICATION_LOG_BACKUP_COUNT', 5)
        
        # Feature Flags
        self.config.feature_advanced_filtering = self._get_bool('FEATURE_ADVANCED_FILTERING', True)
        self.config.feature_smart_grouping = self._get_bool('FEATURE_SMART_GROUPING', True)
        self.config.feature_ai_translations = self._get_bool('FEATURE_AI_TRANSLATIONS', False)
        self.config.feature_voice_notifications = self._get_bool('FEATURE_VOICE_NOTIFICATIONS', False)
        self.config.feature_video_notifications = self._get_bool('FEATURE_VIDEO_NOTIFICATIONS', False)
        self.config.beta_features_enabled = self._get_bool('BETA_FEATURES_ENABLED', False)
        
        # Compliance Settings
        self.config.gdpr_compliance_enabled = self._get_bool('GDPR_COMPLIANCE_ENABLED', True)
        self.config.data_retention_days = self._get_int('NOTIFICATION_DATA_RETENTION_DAYS', 2555)
        self.config.anonymization_enabled = self._get_bool('NOTIFICATION_ANONYMIZATION_ENABLED', True)
        self.config.privacy_mode_enabled = self._get_bool('PRIVACY_MODE_ENABLED', False)
        self.config.content_encryption_enabled = self._get_bool('NOTIFICATION_CONTENT_ENCRYPTION', False)
        self.config.metadata_encryption_enabled = self._get_bool('NOTIFICATION_METADATA_ENCRYPTION', False)
        
        # Health Check Settings
        self.config.health_check_enabled = self._get_bool('HEALTH_CHECK_ENABLED', True)
        self.config.health_check_interval = self._get_int('HEALTH_CHECK_INTERVAL', 60)
        self.config.health_check_timeout = self._get_int('HEALTH_CHECK_TIMEOUT', 10)
        self.config.metrics_enabled = self._get_bool('METRICS_ENABLED', True)
        self.config.metrics_endpoint = self._get_str('METRICS_ENDPOINT', "/metrics")
        self.config.metrics_port = self._get_int('METRICS_PORT', 9090)
        
        # Alerting Settings
        self.config.alerting_enabled = self._get_bool('ALERTING_ENABLED', True)
        self.config.alerting_webhook_url = self._get_str('ALERTING_WEBHOOK_URL', "")
        self.config.alerting_threshold_error_rate = self._get_float('ALERTING_THRESHOLD_ERROR_RATE', 0.05)
        self.config.alerting_threshold_response_time = self._get_int('ALERTING_THRESHOLD_RESPONSE_TIME', 1000)
    
    def validate_config(self):
        """Validate configuration values"""
        errors = []
        
        # Validate core settings
        if self.config.max_length <= 0:
            errors.append("NOTIFICATION_MAX_LENGTH must be greater than 0")
        
        if self.config.batch_size <= 0:
            errors.append("NOTIFICATION_BATCH_SIZE must be greater than 0")
        
        # Validate WebSocket settings
        if self.config.websocket_port <= 0 or self.config.websocket_port > 65535:
            errors.append("WEBSOCKET_NOTIFICATION_PORT must be between 1 and 65535")
        
        if self.config.websocket_max_connections <= 0:
            errors.append("WEBSOCKET_MAX_CONNECTIONS must be greater than 0")
        
        # Validate email settings
        if self.config.email_enabled and not self.config.smtp_server:
            errors.append("SMTP_NOTIFICATION_SERVER is required when EMAIL_NOTIFICATION_ENABLED is true")
        
        if self.config.smtp_port <= 0 or self.config.smtp_port > 65535:
            errors.append("SMTP_NOTIFICATION_PORT must be between 1 and 65535")
        
        # Validate mobile settings
        if self.config.mobile_max_devices_per_user <= 0:
            errors.append("MOBILE_NOTIFICATION_MAX_DEVICES_PER_USER must be greater than 0")
        
        # Validate translation settings
        if self.config.translation_default_language not in self.config.translation_supported_languages:
            errors.append(f"TRANSLATION_DEFAULT_LANGUAGE '{self.config.translation_default_language}' must be in TRANSLATION_SUPPORTED_LANGUAGES")
        
        # Validate grouping settings
        if not 0 <= self.config.grouping_similarity_threshold <= 1:
            errors.append("GROUPING_SIMILARITY_THRESHOLD must be between 0 and 1")
        
        if self.config.grouping_max_group_size <= 0:
            errors.append("GROUPING_MAX_GROUP_SIZE must be greater than 0")
        
        # Validate archiving settings
        if self.config.archiving_read_older_than_days < 0:
            errors.append("ARCHIVING_READ_OLDER_THAN_DAYS must be non-negative")
        
        if self.config.archiving_unread_older_than_days < 0:
            errors.append("ARCHIVING_UNREAD_OLDER_THAN_DAYS must be non-negative")
        
        # Validate scheduling settings
        if self.config.digest_max_notifications <= 0:
            errors.append("DIGEST_MAX_NOTIFICATIONS must be greater than 0")
        
        # Validate security settings
        if self.config.rate_limit_notifications <= 0:
            errors.append("RATE_LIMIT_NOTIFICATIONS must be greater than 0")
        
        if self.config.rate_limit_window <= 0:
            errors.append("RATE_LIMIT_WINDOW must be greater than 0")
        
        # Validate database settings
        if self.config.db_pool_size <= 0:
            errors.append("DATABASE_NOTIFICATION_POOL_SIZE must be greater than 0")
        
        # Validate feature flags
        if self.config.performance_sample_rate < 0 or self.config.performance_sample_rate > 1:
            errors.append("PERFORMANCE_SAMPLE_RATE must be between 0 and 1")
        
        if self.config.alerting_threshold_error_rate < 0 or self.config.alerting_threshold_error_rate > 1:
            errors.append("ALERTING_THRESHOLD_ERROR_RATE must be between 0 and 1")
        
        if errors:
            raise ValueError(f"Configuration validation failed: {'; '.join(errors)}")
    
    def get_config(self) -> NotificationConfig:
        """Get the loaded configuration"""
        return self.config
    
    def _get_bool(self, key: str, default: bool = False) -> bool:
        """Get boolean value from environment"""
        value = os.getenv(key, str(default)).lower()
        return value in ('true', '1', 'yes', 'on')
    
    def _get_int(self, key: str, default: int = 0) -> int:
        """Get integer value from environment"""
        try:
            return int(os.getenv(key, str(default)))
        except ValueError:
            return default
    
    def _get_float(self, key: str, default: float = 0.0) -> float:
        """Get float value from environment"""
        try:
            return float(os.getenv(key, str(default)))
        except ValueError:
            return default
    
    def _get_str(self, key: str, default: str = "") -> str:
        """Get string value from environment"""
        return os.getenv(key, default)
    
    def _get_list(self, key: str, default: List[str] = None) -> List[str]:
        """Get list value from environment"""
        if default is None:
            default = []
        value = os.getenv(key, "")
        if value:
            return [item.strip() for item in value.split(',')]
        return default


# Global configuration instance
notification_config = NotificationConfigLoader().get_config()


def get_notification_config() -> NotificationConfig:
    """Get the global notification configuration"""
    return notification_config


def is_notification_enabled() -> bool:
    """Check if notification system is enabled"""
    return notification_config.enabled


def is_feature_enabled(feature: str) -> bool:
    """Check if a specific feature is enabled"""
    feature_map = {
        'advanced_filtering': notification_config.feature_advanced_filtering,
        'smart_grouping': notification_config.feature_smart_grouping,
        'ai_translations': notification_config.feature_ai_translations,
        'voice_notifications': notification_config.feature_voice_notifications,
        'video_notifications': notification_config.feature_video_notifications,
        'beta_features': notification_config.beta_features_enabled
    }
    return feature_map.get(feature, False)


def is_service_enabled(service: str) -> bool:
    """Check if a specific service is enabled"""
    service_map = {
        'email': notification_config.email_enabled,
        'push': notification_config.push_enabled,
        'mobile': notification_config.mobile_enabled,
        'translation': notification_config.translation_enabled,
        'filtering': notification_config.filtering_enabled,
        'grouping': notification_config.grouping_enabled,
        'archiving': notification_config.archiving_enabled,
        'scheduling': notification_config.scheduling_enabled,
        'analytics': notification_config.analytics_enabled,
        'apns': notification_config.apns_enabled,
        'fcm': notification_config.fcm_enabled,
        'hms': notification_config.hms_enabled,
        'websocket': notification_config.enabled  # WebSocket is part of core system
    }
    return service_map.get(service, False)
