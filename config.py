import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///forum.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
    GITHUB_ORG = 'AutoBotSolutions'
    
    # CSRF Protection
    WTF_CSRF_ENABLED = True
    WTF_CSRF_SECRET_KEY = os.environ.get('WTF_CSRF_SECRET_KEY') or 'csrf-secret-key-change-in-production'
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hour
    
    # Server Configuration
    SERVER_NAME = os.environ.get('SERVER_NAME', 'localhost:5000')
    APPLICATION_ROOT = '/'
    PREFERRED_URL_SCHEME = 'http'
    
    # Email Configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'false').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', MAIL_USERNAME)
    MAIL_MAX_EMAILS = os.environ.get('MAIL_MAX_EMAILS', 10)
    MAIL_SUPPRESS_SEND = os.environ.get('MAIL_SUPPRESS_SEND', 'false').lower() in ['true', 'on', '1']
    
    # Email Queue Configuration
    MAIL_QUEUE_ENABLED = os.environ.get('MAIL_QUEUE_ENABLED', 'true').lower() in ['true', 'on', '1']
    MAIL_QUEUE_URL = os.environ.get('MAIL_QUEUE_URL', 'redis://localhost:6379/0')
    MAIL_RETRY_ATTEMPTS = int(os.environ.get('MAIL_RETRY_ATTEMPTS', 3))
    MAIL_RETRY_DELAY = int(os.environ.get('MAIL_RETRY_DELAY', 60))  # seconds
    
    # Two-Factor Authentication Configuration
    TWO_FA_ENABLED = os.environ.get('TWO_FA_ENABLED', 'true').lower() in ['true', 'on', '1']
    TWO_FA_ISSUER = os.environ.get('TWO_FA_ISSUER', 'AutoBotSolutions Forum')
    TWO_FA_ENCRYPTION_KEY = os.environ.get('TWO_FA_ENCRYPTION_KEY')
    TWO_FA_REQUIRED_FOR_ADMIN = os.environ.get('TWO_FA_REQUIRED_FOR_ADMIN', 'false').lower() in ['true', 'on', '1']
    TWO_FA_REMEMBER_DEVICE_DAYS = int(os.environ.get('TWO_FA_REMEMBER_DEVICE_DAYS', 30))
    
    # Social Login Configuration
    SOCIAL_LOGIN_ENABLED = os.environ.get('SOCIAL_LOGIN_ENABLED', 'true').lower() in ['true', 'on', '1']
    
    # Google OAuth2 Configuration
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
    
    # GitHub OAuth2 Configuration
    GITHUB_CLIENT_ID = os.environ.get('GITHUB_CLIENT_ID')
    GITHUB_CLIENT_SECRET = os.environ.get('GITHUB_CLIENT_SECRET')
    
    # Social Login Settings
    SOCIAL_AUTO_LINK_EMAIL = os.environ.get('SOCIAL_AUTO_LINK_EMAIL', 'true').lower() in ['true', 'on', '1']
    SOCIAL_IMPORT_PROFILE = os.environ.get('SOCIAL_IMPORT_PROFILE', 'true').lower() in ['true', 'on', '1']
    SOCIAL_SESSION_TIMEOUT = int(os.environ.get('SOCIAL_SESSION_TIMEOUT', 600))  # 10 minutes
    
    # Advanced Session Management Configuration
    SESSION_MANAGEMENT_ENABLED = os.environ.get('SESSION_MANAGEMENT_ENABLED', 'true').lower() in ['true', 'on', '1']
    REDIS_SESSION_URL = os.environ.get('REDIS_SESSION_URL', 'redis://localhost:6379/1')
    SESSION_TIMEOUT = int(os.environ.get('SESSION_TIMEOUT', 1800))  # 30 minutes
    PERMANENT_SESSION_LIFETIME = int(os.environ.get('PERMANENT_SESSION_LIFETIME', 3600))  # 1 hour
    MAX_CONCURRENT_SESSIONS = int(os.environ.get('MAX_CONCURRENT_SESSIONS', 5))
    AUTO_REVOKE_INACTIVE = os.environ.get('AUTO_REVOKE_INACTIVE', 'true').lower() in ['true', 'on', '1']
    INACTIVE_SESSION_TIMEOUT = int(os.environ.get('INACTIVE_SESSION_TIMEOUT', 1800))  # 30 minutes
    
    # Security Monitoring Configuration
    SECURITY_MONITORING_ENABLED = os.environ.get('SECURITY_MONITORING_ENABLED', 'true').lower() in ['true', 'on', '1']
    SUSPICIOUS_ACTIVITY_DETECTION = os.environ.get('SUSPICIOUS_ACTIVITY_DETECTION', 'true').lower() in ['true', 'on', '1']
    SECURITY_ALERT_EMAIL = os.environ.get('SECURITY_ALERT_EMAIL')
    SESSION_ANALYTICS_ENABLED = os.environ.get('SESSION_ANALYTICS_ENABLED', 'true').lower() in ['true', 'on', '1']
    
    # Advanced Search Configuration
    SEARCH_ENABLED = os.environ.get('SEARCH_ENABLED', 'true').lower() in ['true', 'on', '1']
    ELASTICSEARCH_URL = os.environ.get('ELASTICSEARCH_URL', 'http://localhost:9200')
    ELASTICSEARCH_INDEX = os.environ.get('ELASTICSEARCH_INDEX', 'forum_search')
    SEARCH_CACHE_ENABLED = os.environ.get('SEARCH_CACHE_ENABLED', 'true').lower() in ['true', 'on', '1']
    SEARCH_CACHE_TIMEOUT = int(os.environ.get('SEARCH_CACHE_TIMEOUT', 300))  # 5 minutes
    SEARCH_RESULTS_PER_PAGE_OPTIONS = [10, 20, 50, 100]
    SEARCH_MAX_RESULTS_PER_PAGE = int(os.environ.get('SEARCH_MAX_RESULTS_PER_PAGE', 100))
    SEARCH_ANALYTICS_ENABLED = os.environ.get('SEARCH_ANALYTICS_ENABLED', 'true').lower() in ['true', 'on', '1']
    SEARCH_HIGHLIGHT_ENABLED = os.environ.get('SEARCH_HIGHLIGHT_ENABLED', 'true').lower() in ['true', 'on', '1']
    SEARCH_FUZZINESS = os.environ.get('SEARCH_FUZZINESS', 'AUTO')
    SEARCH_MIN_QUERY_LENGTH = int(os.environ.get('SEARCH_MIN_QUERY_LENGTH', 1))
    SEARCH_MAX_QUERY_LENGTH = int(os.environ.get('SEARCH_MAX_QUERY_LENGTH', 255))
    SEARCH_INDEXING_BATCH_SIZE = int(os.environ.get('SEARCH_INDEXING_BATCH_SIZE', 100))
    SEARCH_REINDEX_INTERVAL = int(os.environ.get('SEARCH_REINDEX_INTERVAL', 3600))  # 1 hour
    
    # WebSocket Configuration
    WEBSOCKET_ENABLED = os.environ.get('WEBSOCKET_ENABLED', 'true').lower() == 'true'
    WEBSOCKET_ASYNC_MODE = os.environ.get('WEBSOCKET_ASYNC_MODE', 'threading')  # threading, eventlet, or gevent
    WEBSOCKET_PING_TIMEOUT = int(os.environ.get('WEBSOCKET_PING_TIMEOUT', 60))  # seconds
    WEBSOCKET_PING_INTERVAL = int(os.environ.get('WEBSOCKET_PING_INTERVAL', 25))  # seconds
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')  # For WebSocket session management
    
    # Content Management Configuration
    CONTENT_MANAGEMENT_ENABLED = os.environ.get('CONTENT_MANAGEMENT_ENABLED', 'true').lower() == 'true'
    CONTENT_AUTO_SAVE_INTERVAL = int(os.environ.get('CONTENT_AUTO_SAVE_INTERVAL', 30))  # seconds
    CONTENT_MAX_VERSIONS = int(os.environ.get('CONTENT_MAX_VERSIONS', 10))  # Maximum versions to keep
    CONTENT_COLLABORATION_ENABLED = os.environ.get('CONTENT_COLLABORATION_ENABLED', 'true').lower() == 'true'
    CONTENT_SCHEDULING_ENABLED = os.environ.get('CONTENT_SCHEDULING_ENABLED', 'true').lower() == 'true'
    CONTENT_ANALYTICS_ENABLED = os.environ.get('CONTENT_ANALYTICS_ENABLED', 'true').lower() == 'true'
    CONTENT_EXPIRATION_ENABLED = os.environ.get('CONTENT_EXPIRATION_ENABLED', 'true').lower() == 'true'
    CONTENT_ARCHIVING_ENABLED = os.environ.get('CONTENT_ARCHIVING_ENABLED', 'true').lower() == 'true'
    CONTENT_IMPORT_ENABLED = os.environ.get('CONTENT_IMPORT_ENABLED', 'true').lower() == 'true'
    CONTENT_EXPORT_ENABLED = os.environ.get('CONTENT_EXPORT_ENABLED', 'true').lower() == 'true'

    # File Management Configuration
    FILE_MANAGEMENT_ENABLED = os.environ.get('FILE_MANAGEMENT_ENABLED', 'true').lower() == 'true'
    STORAGE_PROVIDER = os.environ.get('STORAGE_PROVIDER', 'local')  # local, s3, gcs
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'uploads')
    MAX_FILE_SIZE = int(os.environ.get('MAX_FILE_SIZE', 50 * 1024 * 1024))  # 50MB
    ALLOWED_EXTENSIONS = os.environ.get('ALLOWED_EXTENSIONS', 
        'jpg,jpeg,png,gif,webp,pdf,doc,docx,xls,xlsx,ppt,pptx,txt,zip,rar').split(',')
    
    # AWS S3 Configuration
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
    AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
    AWS_S3_BUCKET = os.environ.get('AWS_S3_BUCKET')
    
    # Google Cloud Storage Configuration
    GCS_BUCKET = os.environ.get('GCS_BUCKET')
    GCS_PROJECT_ID = os.environ.get('GCS_PROJECT_ID')
    
    # File Processing Configuration
    AUTO_GENERATE_THUMBNAILS = os.environ.get('AUTO_GENERATE_THUMBNAILS', 'true').lower() == 'true'
    THUMBNAIL_SIZES = os.environ.get('THUMBNAIL_SIZES', '150x150,300x300,800x800').split(',')
    IMAGE_OPTIMIZATION_QUALITY = int(os.environ.get('IMAGE_OPTIMIZATION_QUALITY', 85))
    ENABLE_FILE_ANALYTICS = os.environ.get('ENABLE_FILE_ANALYTICS', 'true').lower() == 'true'
    FILE_RETENTION_DAYS = int(os.environ.get('FILE_RETENTION_DAYS', 365))
