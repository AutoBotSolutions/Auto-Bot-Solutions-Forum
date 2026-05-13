"""
Social Relationships Configuration
Auto Bot Solutions Forum

This module provides configuration settings for social relationships,
including connection types, group settings, and analytics parameters.
"""

import os
from typing import Dict, Any, List
from dataclasses import dataclass


@dataclass
class SocialConnectionConfig:
    """Configuration for social connections"""
    
    # Connection types and their properties
    CONNECTION_TYPES = {
        'follow': {
            'name': 'Follow',
            'mutual': False,
            'requires_approval': False,
            'max_connections': 10000,
            'default_strength': 0.1,
            'strength_increment': 0.05,
            'visibility': 'public'
        },
        'friend': {
            'name': 'Friend',
            'mutual': True,
            'requires_approval': True,
            'max_connections': 1000,
            'default_strength': 0.3,
            'strength_increment': 0.1,
            'visibility': 'friends'
        },
        'block': {
            'name': 'Block',
            'mutual': False,
            'requires_approval': False,
            'max_connections': 1000,
            'default_strength': 0.0,
            'strength_increment': 0.0,
            'visibility': 'private'
        },
        'mute': {
            'name': 'Mute',
            'mutual': False,
            'requires_approval': False,
            'max_connections': 500,
            'default_strength': 0.0,
            'strength_increment': 0.0,
            'visibility': 'private'
        }
    }
    
    # Connection strength settings
    MIN_CONNECTION_STRENGTH = 0.0
    MAX_CONNECTION_STRENGTH = 1.0
    DEFAULT_CONNECTION_STRENGTH = 0.1
    
    # Interaction weights for strength calculation
    INTERACTION_WEIGHTS = {
        'like': 0.05,
        'comment': 0.1,
        'share': 0.15,
        'message': 0.2,
        'mention': 0.1,
        'tag': 0.05,
        'react': 0.08,
        'bookmark': 0.12
    }
    
    # Connection limits
    MAX_FOLLOWING = 5000
    MAX_FOLLOWERS = 10000
    MAX_FRIENDS = 1000
    MAX_BLOCKS = 1000
    MAX_MUTES = 500
    
    # Time decay settings
    STRENGTH_DECAY_DAYS = 90
    ACTIVITY_DECAY_HOURS = 24 * 7  # 1 week


@dataclass
class SocialGroupConfig:
    """Configuration for social groups"""
    
    # Group types and their properties
    GROUP_TYPES = {
        'community': {
            'name': 'Community',
            'max_members': 10000,
            'default_privacy': 'public',
            'require_approval': False,
            'allow_invites': True,
            'moderated': False
        },
        'organization': {
            'name': 'Organization',
            'max_members': 5000,
            'default_privacy': 'private',
            'require_approval': True,
            'allow_invites': True,
            'moderated': True
        },
        'team': {
            'name': 'Team',
            'max_members': 100,
            'default_privacy': 'private',
            'require_approval': True,
            'allow_invites': True,
            'moderated': True
        },
        'club': {
            'name': 'Club',
            'max_members': 1000,
            'default_privacy': 'public',
            'require_approval': False,
            'allow_invites': True,
            'moderated': False
        },
        'project': {
            'name': 'Project',
            'max_members': 50,
            'default_privacy': 'private',
            'require_approval': True,
            'allow_invites': True,
            'moderated': True
        }
    }
    
    # Group privacy levels
    PRIVACY_LEVELS = {
        'public': {
            'name': 'Public',
            'discoverable': True,
            'join_directly': True,
            'require_approval': False
        },
        'private': {
            'name': 'Private',
            'discoverable': False,
            'join_directly': False,
            'require_approval': True
        },
        'invite_only': {
            'name': 'Invite Only',
            'discoverable': False,
            'join_directly': False,
            'require_approval': True
        }
    }
    
    # Group roles and permissions
    GROUP_ROLES = {
        'owner': {
            'name': 'Owner',
            'permissions': ['all'],
            'can_promote': True,
            'can_demote': True,
            'can_remove': True
        },
        'admin': {
            'name': 'Admin',
            'permissions': ['manage_members', 'manage_content', 'moderate', 'view_analytics'],
            'can_promote': True,
            'can_demote': False,
            'can_remove': True
        },
        'moderator': {
            'name': 'Moderator',
            'permissions': ['moderate', 'manage_content'],
            'can_promote': False,
            'can_demote': False,
            'can_remove': False
        },
        'member': {
            'name': 'Member',
            'permissions': ['view_content', 'participate'],
            'can_promote': False,
            'can_demote': False,
            'can_remove': False
        }
    }
    
    # Group limits
    MAX_GROUPS_PER_USER = 100
    MAX_MEMBERS_PER_GROUP = 10000
    MAX_ADMINS_PER_GROUP = 10
    MAX_MODERATORS_PER_GROUP = 50
    
    # Group activity settings
    ACTIVITY_CALCULATION_DAYS = 30
    INACTIVE_MEMBER_DAYS = 90
    CONTRIBUTION_SCORE_INCREMENT = 0.1
    MAX_CONTRIBUTION_SCORE = 1.0


@dataclass
class SocialAnalyticsConfig:
    """Configuration for social analytics"""
    
    # Analytics calculation settings
    ANALYTICS_CALCULATION_INTERVAL = 3600  # 1 hour in seconds
    ANALYTICS_RETENTION_DAYS = 365
    ANALYTICS_BATCH_SIZE = 100
    
    # Influence score calculation
    INFLUENCE_FOLLOWERS_WEIGHT = 0.4
    INFLUENCE_ACTIVITY_WEIGHT = 0.2
    INFLUENCE_ENGAGEMENT_WEIGHT = 0.2
    INFLUENCE_RECENCY_WEIGHT = 0.1
    INFLUENCE_QUALITY_WEIGHT = 0.1
    
    # Network metrics
    NETWORK_ANALYSIS_DEPTH = 3
    CLUSTERING_MIN_SIZE = 3
    MUTUAL_CONNECTION_THRESHOLD = 0.5
    
    # Recommendation settings
    RECOMMENDATION_CACHE_TTL = 1800  # 30 minutes
    RECOMMENDATION_LIMIT_USERS = 20
    RECOMMENDATION_LIMIT_GROUPS = 10
    RECOMMENDATION_LIMIT_CONTENT = 50
    
    # Recommendation weights
    RECOMMENDATION_MUTUAL_FRIENDS_WEIGHT = 0.4
    RECOMMENDATION_SIMILAR_INTERESTS_WEIGHT = 0.3
    RECOMMENDATION_ACTIVITY_LEVEL_WEIGHT = 0.2
    RECOMMENDATION_PROXIMITY_WEIGHT = 0.1
    
    # Trending content settings
    TRENDING_CALCULATION_INTERVAL = 300  # 5 minutes
    TRENDING_RETENTION_HOURS = 24
    TRENDING_MIN_ENGAGEMENT = 5


@dataclass
class SocialActivityConfig:
    """Configuration for social activities"""
    
    # Activity types
    ACTIVITY_TYPES = {
        'post': {
            'name': 'Post',
            'visibility': 'public',
            'engagement_weight': 1.0,
            'trending_weight': 1.0
        },
        'comment': {
            'name': 'Comment',
            'visibility': 'public',
            'engagement_weight': 0.5,
            'trending_weight': 0.3
        },
        'like': {
            'name': 'Like',
            'visibility': 'public',
            'engagement_weight': 0.1,
            'trending_weight': 0.1
        },
        'share': {
            'name': 'Share',
            'visibility': 'public',
            'engagement_weight': 0.3,
            'trending_weight': 0.5
        },
        'follow': {
            'name': 'Follow',
            'visibility': 'public',
            'engagement_weight': 0.2,
            'trending_weight': 0.0
        },
        'friend_request': {
            'name': 'Friend Request',
            'visibility': 'private',
            'engagement_weight': 0.0,
            'trending_weight': 0.0
        },
        'join_group': {
            'name': 'Join Group',
            'visibility': 'public',
            'engagement_weight': 0.2,
            'trending_weight': 0.0
        },
        'create_group': {
            'name': 'Create Group',
            'visibility': 'public',
            'engagement_weight': 0.3,
            'trending_weight': 0.0
        }
    }
    
    # Activity visibility levels
    VISIBILITY_LEVELS = {
        'public': {
            'name': 'Public',
            'description': 'Visible to everyone'
        },
        'friends': {
            'name': 'Friends',
            'description': 'Visible to friends only'
        },
        'private': {
            'name': 'Private',
            'description': 'Visible only to you'
        },
        'custom': {
            'name': 'Custom',
            'description': 'Visible to selected users'
        }
    }
    
    # Engagement calculation weights
    ENGAGEMENT_WEIGHTS = {
        'like': 1.0,
        'comment': 2.0,
        'share': 3.0,
        'view': 0.1,
        'bookmark': 1.5,
        'react': 1.2
    }
    
    # Activity limits
    MAX_CONTENT_LENGTH = 2000
    MAX_ACTIVITY_PER_DAY = 100
    MAX_HASHTAGS = 10
    MAX_MENTIONS = 20
    
    # Content filtering
    CONTENT_FILTERING_ENABLED = True
    SPAM_DETECTION_ENABLED = True
    MODERATION_QUEUE_ENABLED = True
    
    # Time decay settings
    ACTIVITY_DECAY_HOURS = 24 * 7  # 1 week
    TRENDING_DECAY_HOURS = 24 * 1  # 1 day


@dataclass
class SocialPrivacyConfig:
    """Configuration for social privacy settings"""
    
    # Default privacy settings
    DEFAULT_PRIVACY_LEVELS = {
        'profile': 'public',
        'posts': 'public',
        'friends': 'public',
        'groups': 'public',
        'activity': 'public'
    }
    
    # Privacy levels
    PRIVACY_LEVELS = {
        'public': {
            'name': 'Public',
            'description': 'Everyone can see',
            'indexable': True
        },
        'friends': {
            'name': 'Friends',
            'description': 'Only friends can see',
            'indexable': False
        },
        'private': {
            'name': 'Private',
            'description': 'Only you can see',
            'indexable': False
        }
    }
    
    # Data retention settings
    DATA_RETENTION_DAYS = {
        'activities': 365,
        'interactions': 365,
        'connections': 2555,  # 7 years
        'analytics': 365
    }
    
    # Blocking and muting
    BLOCK_HIDE_PROFILE = True
    BLOCK_HIDE_ACTIVITIES = True
    BLOCK_PREVENT_INTERACTION = True
    MUTE_HIDE_ACTIVITIES = True
    MUTE_ALLOW_INTERACTION = True
    
    # Age restrictions
    MINIMUM_AGE = 13
    AGE_RESTRICTED_CONTENT = 18
    
    # Content moderation
    AUTO_MODERATION_ENABLED = True
    MANUAL_REVIEW_THRESHOLD = 0.7
    CONTENT_REPORT_THRESHOLD = 5


class SocialConfig:
    """Main social configuration class"""
    
    def __init__(self):
        self.connection = SocialConnectionConfig()
        self.group = SocialGroupConfig()
        self.analytics = SocialAnalyticsConfig()
        self.activity = SocialActivityConfig()
        self.privacy = SocialPrivacyConfig()
        
        # Load environment-specific settings
        self._load_environment_settings()
    
    def _load_environment_settings(self):
        """Load settings from environment variables"""
        # Connection settings
        self.MAX_FOLLOWING = int(os.getenv('SOCIAL_MAX_FOLLOWING', self.connection.MAX_FOLLOWING))
        self.MAX_FRIENDS = int(os.getenv('SOCIAL_MAX_FRIENDS', self.connection.MAX_FRIENDS))
        self.MAX_BLOCKS = int(os.getenv('SOCIAL_MAX_BLOCKS', self.connection.MAX_BLOCKS))
        
        # Group settings
        self.MAX_GROUPS_PER_USER = int(os.getenv('SOCIAL_MAX_GROUPS_PER_USER', self.group.MAX_GROUPS_PER_USER))
        self.MAX_MEMBERS_PER_GROUP = int(os.getenv('SOCIAL_MAX_MEMBERS_PER_GROUP', self.group.MAX_MEMBERS_PER_GROUP))
        
        # Analytics settings
        self.ANALYTICS_ENABLED = os.getenv('SOCIAL_ANALYTICS_ENABLED', 'true').lower() == 'true'
        self.RECOMMENDATIONS_ENABLED = os.getenv('SOCIAL_RECOMMENDATIONS_ENABLED', 'true').lower() == 'true'
        
        # Activity settings
        self.CONTENT_FILTERING_ENABLED = os.getenv('SOCIAL_CONTENT_FILTERING_ENABLED', 'true').lower() == 'true'
        self.AUTO_MODERATION_ENABLED = os.getenv('SOCIAL_AUTO_MODERATION_ENABLED', 'true').lower() == 'true'
        
        # Privacy settings
        self.DEFAULT_PRIVACY = os.getenv('SOCIAL_DEFAULT_PRIVACY', 'public')
        self.DATA_RETENTION_DAYS = int(os.getenv('SOCIAL_DATA_RETENTION_DAYS', self.privacy.DATA_RETENTION_DAYS['activities']))
    
    def get_connection_type_config(self, connection_type: str) -> Dict[str, Any]:
        """Get configuration for a specific connection type"""
        return self.connection.CONNECTION_TYPES.get(connection_type, {})
    
    def get_group_type_config(self, group_type: str) -> Dict[str, Any]:
        """Get configuration for a specific group type"""
        return self.group.GROUP_TYPES.get(group_type, {})
    
    def get_group_role_config(self, role: str) -> Dict[str, Any]:
        """Get configuration for a specific group role"""
        return self.group.GROUP_ROLES.get(role, {})
    
    def get_activity_type_config(self, activity_type: str) -> Dict[str, Any]:
        """Get configuration for a specific activity type"""
        return self.activity.ACTIVITY_TYPES.get(activity_type, {})
    
    def get_privacy_level_config(self, privacy_level: str) -> Dict[str, Any]:
        """Get configuration for a specific privacy level"""
        return self.privacy.PRIVACY_LEVELS.get(privacy_level, {})
    
    def validate_connection_limits(self, user_id: int, connection_type: str) -> Dict[str, Any]:
        """Validate if user can create more connections of a type"""
        from .models import UserConnection
        
        # Get current connection count
        current_count = UserConnection.query.filter_by(
            user_id=user_id,
            connection_type=connection_type,
            status='active'
        ).count()
        
        # Get limit for this connection type
        connection_config = self.get_connection_type_config(connection_type)
        max_connections = connection_config.get('max_connections', 1000)
        
        return {
            'can_create': current_count < max_connections,
            'current_count': current_count,
            'max_connections': max_connections,
            'remaining_slots': max_connections - current_count
        }
    
    def validate_group_limits(self, user_id: int) -> Dict[str, Any]:
        """Validate if user can create more groups"""
        from .models import UserGroup
        
        # Get current group count
        current_count = UserGroup.query.filter_by(creator_id=user_id).count()
        
        return {
            'can_create': current_count < self.MAX_GROUPS_PER_USER,
            'current_count': current_count,
            'max_groups': self.MAX_GROUPS_PER_USER,
            'remaining_slots': self.MAX_GROUPS_PER_USER - current_count
        }
    
    def get_connection_strength_increment(self, interaction_type: str) -> float:
        """Get strength increment for an interaction type"""
        return self.connection.INTERACTION_WEIGHTS.get(interaction_type, 0.05)
    
    def get_engagement_weight(self, engagement_type: str) -> float:
        """Get engagement weight for an engagement type"""
        return self.activity.ENGAGEMENT_WEIGHTS.get(engagement_type, 1.0)
    
    def calculate_influence_score(self, profile_data: Dict[str, Any]) -> float:
        """Calculate influence score based on profile data"""
        followers = profile_data.get('followers_count', 0)
        activity = profile_data.get('posts_count', 0)
        engagement = profile_data.get('avg_post_engagement', 0.0)
        recency_score = profile_data.get('recency_score', 0.0)
        quality_score = profile_data.get('quality_score', 0.0)
        
        # Apply weights
        followers_score = min(1.0, followers / 1000.0) * self.analytics.INFLUENCE_FOLLOWERS_WEIGHT
        activity_score = min(1.0, activity / 100.0) * self.analytics.INFLUENCE_ACTIVITY_WEIGHT
        engagement_score = min(1.0, engagement / 50.0) * self.analytics.INFLUENCE_ENGAGEMENT_WEIGHT
        recency_score = recency_score * self.analytics.INFLUENCE_RECENCY_WEIGHT
        quality_score = quality_score * self.analytics.INFLUENCE_QUALITY_WEIGHT
        
        return followers_score + activity_score + engagement_score + recency_score + quality_score
    
    def get_recommendation_weights(self) -> Dict[str, float]:
        """Get recommendation algorithm weights"""
        return {
            'mutual_friends': self.analytics.RECOMMENDATION_MUTUAL_FRIENDS_WEIGHT,
            'similar_interests': self.analytics.RECOMMENDATION_SIMILAR_INTERESTS_WEIGHT,
            'activity_level': self.analytics.RECOMMENDATION_ACTIVITY_LEVEL_WEIGHT,
            'proximity': self.analytics.RECOMMENDATION_PROXIMITY_WEIGHT
        }
    
    def is_activity_type_trending(self, activity_type: str) -> bool:
        """Check if an activity type contributes to trending"""
        activity_config = self.get_activity_type_config(activity_type)
        return activity_config.get('trending_weight', 0.0) > 0.0
    
    def get_data_retention_days(self, data_type: str) -> int:
        """Get data retention period for a data type"""
        return self.privacy.DATA_RETENTION_DAYS.get(data_type, 365)
    
    def should_filter_content(self) -> bool:
        """Check if content filtering is enabled"""
        return self.CONTENT_FILTERING_ENABLED and self.activity.CONTENT_FILTERING_ENABLED
    
    def should_auto_moderate(self) -> bool:
        """Check if auto moderation is enabled"""
        return self.AUTO_MODERATION_ENABLED and self.activity.AUTO_MODERATION_ENABLED
    
    def get_activity_visibility_rules(self, visibility: str) -> Dict[str, Any]:
        """Get visibility rules for an activity"""
        visibility_config = self.get_privacy_level_config(visibility)
        
        rules = {
            'is_public': visibility == 'public',
            'is_private': visibility == 'private',
            'is_friends_only': visibility == 'friends',
            'is_custom': visibility == 'custom',
            'indexable': visibility_config.get('indexable', True)
        }
        
        return rules
    
    def export_config(self) -> Dict[str, Any]:
        """Export all configuration settings"""
        return {
            'connection': {
                'types': self.connection.CONNECTION_TYPES,
                'limits': {
                    'max_following': self.MAX_FOLLOWING,
                    'max_friends': self.MAX_FRIENDS,
                    'max_blocks': self.MAX_BLOCKS
                },
                'interaction_weights': self.connection.INTERACTION_WEIGHTS
            },
            'group': {
                'types': self.group.GROUP_TYPES,
                'privacy_levels': self.group.PRIVACY_LEVELS,
                'roles': self.group.GROUP_ROLES,
                'limits': {
                    'max_groups_per_user': self.MAX_GROUPS_PER_USER,
                    'max_members_per_group': self.MAX_MEMBERS_PER_GROUP
                }
            },
            'analytics': {
                'enabled': self.ANALYTICS_ENABLED,
                'recommendations_enabled': self.RECOMMENDATIONS_ENABLED,
                'influence_weights': {
                    'followers': self.analytics.INFLUENCE_FOLLOWERS_WEIGHT,
                    'activity': self.analytics.INFLUENCE_ACTIVITY_WEIGHT,
                    'engagement': self.analytics.INFLUENCE_ENGAGEMENT_WEIGHT,
                    'recency': self.analytics.INFLUENCE_RECENCY_WEIGHT,
                    'quality': self.analytics.INFLUENCE_QUALITY_WEIGHT
                }
            },
            'activity': {
                'types': self.activity.ACTIVITY_TYPES,
                'visibility_levels': self.activity.VISIBILITY_LEVELS,
                'engagement_weights': self.activity.ENGAGEMENT_WEIGHTS,
                'content_filtering': self.CONTENT_FILTERING_ENABLED,
                'auto_moderation': self.AUTO_MODERATION_ENABLED
            },
            'privacy': {
                'default_levels': self.privacy.DEFAULT_PRIVACY_LEVELS,
                'data_retention': self.privacy.DATA_RETENTION_DAYS,
                'content_filtering': self.CONTENT_FILTERING_ENABLED
            }
        }


# Global configuration instance
social_config = SocialConfig()
