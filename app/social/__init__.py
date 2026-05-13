"""
Social Relationships Package
Auto Bot Solutions Forum

This package provides comprehensive social relationship functionality including:
- User connections (follow, friend, block, mute)
- Social groups and communities
- Social analytics and insights
- Activity feeds and recommendations
- Privacy and permissions management
"""

from .models import (
    UserConnection, UserSocialProfile, UserGroup, UserGroupMembership,
    UserInteraction, UserRelationshipAnalytics, UserSocialActivity
)

from .service import (
    SocialService, GroupService, SocialAnalyticsService, SocialActivityService
)

from .utils import (
    SocialValidators, SocialCalculators, SocialHelpers, SocialActivityProcessor
)

from .config import (
    SocialConfig, social_config, SocialConnectionConfig, SocialGroupConfig,
    SocialAnalyticsConfig, SocialActivityConfig, SocialPrivacyConfig
)

__version__ = "1.0.0"
__author__ = "Auto Bot Solutions Forum Team"

# Export main classes
__all__ = [
    # Models
    'UserConnection',
    'UserSocialProfile', 
    'UserGroup',
    'UserGroupMembership',
    'UserInteraction',
    'UserRelationshipAnalytics',
    'UserSocialActivity',
    
    # Services
    'SocialService',
    'GroupService', 
    'SocialAnalyticsService',
    'SocialActivityService',
    
    # Utilities
    'SocialValidators',
    'SocialCalculators',
    'SocialHelpers',
    'SocialActivityProcessor',
    
    # Configuration
    'SocialConfig',
    'social_config',
    'SocialConnectionConfig',
    'SocialGroupConfig',
    'SocialAnalyticsConfig',
    'SocialActivityConfig',
    'SocialPrivacyConfig'
]

# Package-level convenience functions
def create_social_service():
    """Create and return a new SocialService instance"""
    return SocialService()

def create_group_service():
    """Create and return a new GroupService instance"""
    return GroupService()

def create_analytics_service():
    """Create and return a new SocialAnalyticsService instance"""
    return SocialAnalyticsService()

def create_activity_service():
    """Create and return a new SocialActivityService instance"""
    return SocialActivityService()

def get_config():
    """Get the global social configuration"""
    return social_config

# Initialize package
def init_app(app):
    """Initialize the social relationships package with Flask app"""
    # Register any Flask extensions or blueprints if needed
    # This can be used for future Flask integration
    
    # Set up any app-level configuration
    app.config.setdefault('SOCIAL_ANALYTICS_ENABLED', True)
    app.config.setdefault('SOCIAL_RECOMMENDATIONS_ENABLED', True)
    app.config.setdefault('SOCIAL_CONTENT_FILTERING_ENABLED', True)
    
    # Log initialization
    app.logger.info("Social relationships package initialized")

# Package metadata
PACKAGE_INFO = {
    'name': 'social-relationships',
    'version': __version__,
    'description': 'Comprehensive social relationships system for Auto Bot Solutions Forum',
    'features': [
        'User connections and relationships',
        'Social groups and communities',
        'Real-time social analytics',
        'Activity feeds and recommendations',
        'Privacy and permissions management',
        'Social graph analysis',
        'Trending content detection'
    ],
    'dependencies': [
        'flask-sqlalchemy',
        'psycopg2-binary',
        'redis',
        'numpy',
        'pandas'
    ]
}
