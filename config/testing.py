"""
Testing Configuration

This module contains configuration settings for testing environment.
"""

import os
from datetime import timedelta

class TestingConfig:
    """Testing configuration settings"""
    
    # Basic Flask settings
    SECRET_KEY = 'test-secret-key-for-testing-only'
    TESTING = True
    DEBUG = True
    
    # Database settings
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Cache settings
    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 300
    
    # Security settings
    WTF_CSRF_ENABLED = False
    SESSION_PROTECTION = None
    
    # Upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER = 'uploads/test'
    
    # Mail settings (disabled for testing)
    MAIL_SERVER = 'localhost'
    MAIL_PORT = 587
    MAIL_USE_TLS = False
    MAIL_USERNAME = None
    MAIL_PASSWORD = None
    
    # Redis settings (optional for testing)
    REDIS_URL = 'redis://localhost:6379/1'
    
    # User management settings
    USER_PROFILE_UPLOAD_PATH = 'uploads/test/profiles'
    USER_ANALYTICS_ENABLED = True
    SOCIAL_FEATURES_ENABLED = True
    PROFILE_CUSTOMIZATION_ENABLED = True
    USER_ROLE_MANAGEMENT_ENABLED = True
    
    # Performance settings
    PROFILE_CACHE_TIMEOUT = 60
    ANALYTICS_CACHE_TIMEOUT = 60
    SOCIAL_CACHE_TIMEOUT = 60
    
    # Rate limiting (disabled for testing)
    RATELIMIT_ENABLED = False
    
    # Logging settings
    LOG_LEVEL = 'DEBUG'
    LOG_TO_STDOUT = True
    
    # Pagination
    POSTS_PER_PAGE = 10
    USERS_PER_PAGE = 20
    
    # Session settings
    PERMANENT_SESSION_LIFETIME = timedelta(hours=1)
    
    # JWT settings
    JWT_SECRET_KEY = 'test-jwt-secret-key'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # API settings
    API_TITLE = 'Auto Bot Solutions Forum API (Test)'
    API_VERSION = 'v1'
    
    # Celery settings (disabled for testing)
    CELERY_BROKER_URL = 'redis://localhost:6379/2'
    CELERY_RESULT_BACKEND = 'redis://localhost:6379/2'
    CELERY_TASK_ALWAYS_EAGER = True
    
    # Testing specific settings
    PRESERVE_CONTEXT_ON_EXCEPTION = False
    PROPAGATE_EXCEPTIONS = True
    
    @staticmethod
    def init_app(app):
        """Initialize app with testing configuration"""
        # Create upload directory if it doesn't exist
        upload_path = os.path.join(app.root_path, '..', app.config['UPLOAD_FOLDER'])
        os.makedirs(upload_path, exist_ok=True)
        
        # Create profile upload directory
        profile_upload_path = os.path.join(app.root_path, '..', app.config['USER_PROFILE_UPLOAD_PATH'])
        os.makedirs(profile_upload_path, exist_ok=True)
