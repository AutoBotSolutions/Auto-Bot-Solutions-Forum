"""
Content Relationships Module
Auto Bot Solutions Forum

This module provides comprehensive content relationships functionality including:
- Content versioning and history tracking
- Content analytics and performance metrics
- Content moderation and review
- Content archiving and retention
- Content recommendations and personalization
- Content relationships and categorization
"""

from .models import (
    ContentRelationship, ContentVersion, ContentAnalytics, ContentModeration,
    ContentArchive, ContentRecommendation, ContentTag, ContentCategory
)

from .service import (
    ContentService, ContentAnalyticsService, ContentModerationService, ContentRecommendationService
)

from .utils import (
    ContentValidators, ContentCalculators, ContentHelpers, ContentProcessor
)

from .config import (
    ContentRelationshipsConfig, content_config, ContentConfig, ContentModerationConfig,
    ContentAnalyticsConfig, ContentArchivingConfig, ContentRecommendationConfig
)

from .routes import content_bp

__version__ = "1.0.0"
__author__ = "Auto Bot Solutions Forum Team"

# Export main classes
__all__ = [
    # Models
    'ContentRelationship',
    'ContentVersion',
    'ContentAnalytics',
    'ContentModeration',
    'ContentArchive',
    'ContentRecommendation',
    'ContentTag',
    'ContentCategory',
    
    # Services
    'ContentService',
    'ContentAnalyticsService',
    'ContentModerationService',
    'ContentRecommendationService',
    
    # Utilities
    'ContentValidators',
    'ContentCalculators',
    'ContentHelpers',
    'ContentProcessor',
    
    # Configuration
    'ContentRelationshipsConfig',
    'content_config',
    'ContentConfig',
    'ContentModerationConfig',
    'ContentAnalyticsConfig',
    'ContentArchivingConfig',
    'ContentRecommendationConfig'
]

# Package-level convenience functions
def create_content_service():
    """Create and return a new ContentService instance"""
    return ContentService()

def create_analytics_service():
    """Create and return a new ContentAnalyticsService instance"""
    return ContentAnalyticsService()

def create_moderation_service():
    """Create and return a new ContentModerationService instance"""
    return ContentModerationService()

def create_recommendation_service():
    """Create and return a new ContentRecommendationService instance"""
    return ContentRecommendationService()

def get_config():
    """Get the global content relationships configuration"""
    return content_config

# Initialize package
def init_content_management(app):
    """Initialize content relationships system with Flask app"""
    # Register blueprint
    app.register_blueprint(content_bp)
    
    # Set up app-level configuration
    app.config.setdefault('CONTENT_VERSIONING_ENABLED', True)
    app.config.setdefault('CONTENT_AUTO_MODERATION_ENABLED', True)
    app.config.setdefault('CONTENT_ANALYTICS_ENABLED', True)
    app.config.setdefault('CONTENT_RECOMMENDATIONS_ENABLED', True)
    app.config.setdefault('CONTENT_ARCHIVING_ENABLED', True)
    app.config.setdefault('CONTENT_AUTO_SAVE_INTERVAL', 30)
    app.config.setdefault('CONTENT_MAX_VERSIONS', 10)
    app.config.setdefault('CONTENT_COLLABORATION_ENABLED', True)
    app.config.setdefault('CONTENT_SCHEDULING_ENABLED', True)
    
    # Add content relationships context processors
    @app.context_processor
    def content_relationships_context():
        return {
            'content_relationships_enabled': app.config.get('CONTENT_RELATIONSHIPS_ENABLED', True),
            'versioning_enabled': app.config.get('CONTENT_VERSIONING_ENABLED', True),
            'auto_moderation_enabled': app.config.get('CONTENT_AUTO_MODERATION_ENABLED', True),
            'analytics_enabled': app.config.get('CONTENT_ANALYTICS_ENABLED', True),
            'recommendations_enabled': app.config.get('CONTENT_RECOMMENDATIONS_ENABLED', True),
            'archiving_enabled': app.config.get('CONTENT_ARCHIVING_ENABLED', True),
            'auto_save_interval': app.config.get('CONTENT_AUTO_SAVE_INTERVAL', 30),
            'collaboration_enabled': app.config.get('CONTENT_COLLABORATION_ENABLED', True),
            'scheduling_enabled': app.config.get('CONTENT_SCHEDULING_ENABLED', True)
        }
    
    # Log initialization
    app.logger.info("Content relationships package initialized")

# Package metadata
PACKAGE_INFO = {
    'name': 'content-relationships',
    'version': __version__,
    'description': 'Comprehensive content relationships system for Auto Bot Solutions Forum',
    'features': [
        'Content versioning and history tracking',
        'Content analytics and performance metrics',
        'Content moderation and review system',
        'Content archiving and retention policies',
        'Content recommendations and personalization',
        'Content relationships and categorization',
        'Content quality scoring and analysis',
        'Trending content detection',
        'Automated content filtering',
        'Content search and discovery'
    ],
    'dependencies': [
        'flask-sqlalchemy',
        'psycopg2-binary',
        'redis',
        'numpy',
        'pandas',
        'scikit-learn'  # For recommendations
    ]
}
