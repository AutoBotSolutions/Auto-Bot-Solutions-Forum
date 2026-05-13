"""
Content Relationships Configuration
Auto Bot Solutions Forum

This module provides configuration settings for content relationships,
including content types, moderation, analytics, and archiving.
"""

import os
from typing import Dict, Any, List
from dataclasses import dataclass


@dataclass
class ContentConfig:
    """Configuration for content relationships"""
    
    # Content types and their properties
    CONTENT_TYPES = {
        'post': {
            'name': 'Post',
            'max_length': 5000,
            'requires_moderation': False,
            'allow_comments': True,
            'allow_sharing': True,
            'default_visibility': 'public'
        },
        'comment': {
            'name': 'Comment',
            'max_length': 2000,
            'requires_moderation': False,
            'allow_comments': False,
            'allow_sharing': True,
            'default_visibility': 'public'
        },
        'article': {
            'name': 'Article',
            'max_length': 10000,
            'requires_moderation': True,
            'allow_comments': True,
            'allow_sharing': True,
            'default_visibility': 'public'
        },
        'page': {
            'name': 'Page',
            'max_length': 20000,
            'requires_moderation': True,
            'allow_comments': False,
            'allow_sharing': True,
            'default_visibility': 'public'
        },
        'story': {
            'name': 'Story',
            'max_length': 15000,
            'requires_moderation': False,
            'allow_comments': True,
            'allow_sharing': True,
            'default_visibility': 'public'
        },
        'tutorial': {
            'name': 'Tutorial',
            'max_length': 20000,
            'requires_moderation': True,
            'allow_comments': True,
            'allow_sharing': True,
            'default_visibility': 'public'
        },
        'news': {
            'name': 'News',
            'max_length': 3000,
            'requires_moderation': True,
            'allow_comments': True,
            'allow_sharing': True,
            'default_visibility': 'public'
        },
        'blog': {
            'name': 'Blog',
            'max_length': 8000,
            'requires_moderation': False,
            'allow_comments': True,
            'allow_sharing': True,
            'default_visibility': 'public'
        }
    }
    
    # Content status levels
    CONTENT_STATUS = {
        'draft': {
            'name': 'Draft',
            'is_public': False,
            'can_edit': True,
            'can_delete': True
        },
        'published': {
            'name': 'Published',
            'is_public': True,
            'can_edit': True,
            'can_delete': True
        },
        'archived': {
            'name': 'Archived',
            'is_public': False,
            'can_edit': False,
            'can_delete': True
        },
        'deleted': {
            'name': 'Deleted',
            'is_public': False,
            'can_edit': False,
            'can_delete': False
        }
    }
    
    # Visibility levels
    VISIBILITY_LEVELS = {
        'public': {
            'name': 'Public',
            'description': 'Visible to everyone',
            'indexable': True
        },
        'private': {
            'name': 'Private',
            'description': 'Visible only to author',
            'indexable': False
        },
        'friends': {
            'name': 'Friends',
            'description': 'Visible to friends only',
            'indexable': False
        },
        'unlisted': {
            'name': 'Unlisted',
            'description': 'Visible with direct link only',
            'indexable': False
        }
    }
    
    # Content limits
    MAX_TITLE_LENGTH = 255
    MAX_CONTENT_LENGTH = 50000
    MAX_TAGS_PER_CONTENT = 10
    MAX_CATEGORIES_PER_CONTENT = 5
    MAX_VERSIONS_PER_CONTENT = 100
    
    # Quality thresholds
    MIN_QUALITY_SCORE = 0.3
    GOOD_QUALITY_SCORE = 0.6
    EXCELLENT_QUALITY_SCORE = 0.8
    
    # Engagement thresholds
    LOW_ENGAGEMENT_RATE = 0.01
    AVERAGE_ENGAGEMENT_RATE = 0.05
    HIGH_ENGAGEMENT_RATE = 0.1
    
    # Versioning settings
    VERSIONING_ENABLED = True
    AUTO_VERSION_ON_UPDATE = True
    VERSION_RETENTION_DAYS = 365


@dataclass
class ContentModerationConfig:
    """Configuration for content moderation"""
    
    # Moderation status levels
    MODERATION_STATUS = {
        'pending': {
            'name': 'Pending Review',
            'requires_action': True,
            'auto_approve': False
        },
        'approved': {
            'name': 'Approved',
            'requires_action': False,
            'auto_approve': True
        },
        'rejected': {
            'name': 'Rejected',
            'requires_action': False,
            'auto_approve': False
        },
        'flagged': {
            'name': 'Flagged',
            'requires_action': True,
            'auto_approve': False
        }
    }
    
    # Priority levels
    PRIORITY_LEVELS = {
        'low': {
            'name': 'Low Priority',
            'weight': 1,
            'response_time_hours': 72
        },
        'normal': {
            'name': 'Normal Priority',
            'weight': 2,
            'response_time_hours': 24
        },
        'high': {
            'name': 'High Priority',
            'weight': 3,
            'response_time_hours': 8
        },
        'urgent': {
            'name': 'Urgent Priority',
            'weight': 4,
            'response_time_hours': 2
        }
    }
    
    # Moderation categories
    MODERATION_CATEGORIES = {
        'spam': {
            'name': 'Spam',
            'severity': 2,
            'auto_reject': True
        },
        'inappropriate': {
            'name': 'Inappropriate Content',
            'severity': 3,
            'auto_reject': False
        },
        'offensive': {
            'name': 'Offensive Content',
            'severity': 4,
            'auto_reject': True
        },
        'hate': {
            'name': 'Hate Speech',
            'severity': 5,
            'auto_reject': True
        },
        'violence': {
            'name': 'Violence',
            'severity': 4,
            'auto_reject': True
        },
        'copyright': {
            'name': 'Copyright Violation',
            'severity': 3,
            'auto_reject': False
        },
        'misinformation': {
            'name': 'Misinformation',
            'severity': 3,
            'auto_reject': False
        }
    }
    
    # Auto-moderation settings
    AUTO_MODERATION_ENABLED = True
    AUTO_MODERATION_THRESHOLD = 0.7
    AUTO_FLAG_THRESHOLD = 0.6
    AUTO_REJECT_THRESHOLD = 0.8
    
    # User reporting thresholds
    REPORT_THRESHOLD_AUTO_FLAG = 5
    REPORT_THRESHOLD_AUTO_REJECT = 10
    REPORT_THRESHOLD_URGENT = 15
    
    # Moderation queue limits
    MAX_PENDING_PER_MODERATOR = 50
    MODERATION_BATCH_SIZE = 20
    MODERATION_TIMEOUT_HOURS = 48
    
    # Content filtering
    CONTENT_FILTERING_ENABLED = True
    PROFANITY_FILTER_ENABLED = True
    SPAM_DETECTION_ENABLED = True
    PLAGIARISM_DETECTION_ENABLED = False  # Requires external service


@dataclass
class ContentAnalyticsConfig:
    """Configuration for content analytics"""
    
    # Analytics calculation settings
    ANALYTICS_CALCULATION_INTERVAL = 3600  # 1 hour
    ANALYTICS_RETENTION_DAYS = 365
    ANALYTICS_BATCH_SIZE = 100
    
    # Engagement weights
    ENGAGEMENT_WEIGHTS = {
        'like': 1.0,
        'comment': 2.0,
        'share': 3.0,
        'bookmark': 1.5,
        'download': 2.5,
        'view': 0.1
    }
    
    # Quality score weights
    QUALITY_WEIGHTS = {
        'content_length': 0.2,
        'title_quality': 0.15,
        'summary_quality': 0.1,
        'metadata_completeness': 0.1,
        'tag_relevance': 0.15,
        'category_appropriateness': 0.1,
        'readability': 0.1,
        'originality': 0.1
    }
    
    # Trending calculation
    TRENDING_CALCULATION_INTERVAL = 300  # 5 minutes
    TRENDING_TIME_WINDOW_HOURS = 24
    TRENDING_MIN_VIEWS = 10
    TRENDING_MIN_ENGAGEMENT = 5
    
    # Performance metrics
    PERFORMANCE_GRADE_THRESHOLDS = {
        'A': 0.8,
        'B': 0.6,
        'C': 0.4,
        'D': 0.2,
        'F': 0.0
    }
    
    # Recommendation settings
    RECOMMENDATION_CACHE_TTL = 1800  # 30 minutes
    RECOMMENDATION_LIMIT_USERS = 20
    RECOMMENDATION_LIMIT_SIMILAR = 10
    RECOMMENDATION_LIMIT_TRENDING = 20
    RECOMMENDATION_MIN_SCORE = 0.3
    
    # Similarity thresholds
    CONTENT_SIMILARITY_THRESHOLD = 0.3
    TAG_SIMILARITY_WEIGHT = 0.4
    CATEGORY_SIMILARITY_WEIGHT = 0.3
    TEXT_SIMILARITY_WEIGHT = 0.2
    TYPE_SIMILARITY_WEIGHT = 0.1


@dataclass
class ContentArchivingConfig:
    """Configuration for content archiving"""
    
    # Archive reasons
    ARCHIVE_REASONS = {
        'old': {
            'name': 'Old Content',
            'default_retention_days': 365,
            'auto_delete': True
        },
        'deleted': {
            'name': 'Deleted Content',
            'default_retention_days': 30,
            'auto_delete': True
        },
        'policy': {
            'name': 'Policy Violation',
            'default_retention_days': 90,
            'auto_delete': True
        },
        'legal': {
            'name': 'Legal Requirement',
            'default_retention_days': 2555,  # 7 years
            'auto_delete': False
        },
        'manual': {
            'name': 'Manual Archive',
            'default_retention_days': 365,
            'auto_delete': True
        }
    }
    
    # Retention policies
    RETENTION_POLICIES = {
        'short_term': {
            'name': 'Short Term',
            'days': 30,
            'description': 'Content archived for 30 days'
        },
        'standard': {
            'name': 'Standard',
            'days': 365,
            'description': 'Content archived for 1 year'
        },
        'long_term': {
            'name': 'Long Term',
            'days': 1825,  # 5 years
            'description': 'Content archived for 5 years'
        },
        'permanent': {
            'name': 'Permanent',
            'days': None,
            'description': 'Content archived permanently'
        }
    }
    
    # Compression settings
    COMPRESSION_ENABLED = True
    COMPRESSION_TYPE = 'gzip'
    COMPRESSION_LEVEL = 6
    
    # Storage settings
    STORAGE_LOCATION = '/var/lib/forum/archives'
    STORAGE_TYPE = 'filesystem'  # filesystem, s3, database
    
    # Cleanup settings
    CLEANUP_INTERVAL_HOURS = 24
    CLEANUP_BATCH_SIZE = 100
    DELETE_EXPIRED_ARCHIVES = True
    
    # Access tracking
    TRACK_ARCHIVE_ACCESS = True
    ACCESS_LOG_RETENTION_DAYS = 90


@dataclass
class ContentRecommendationConfig:
    """Configuration for content recommendations"""
    
    # Recommendation types
    RECOMMENDATION_TYPES = {
        'similar': {
            'name': 'Similar Content',
            'algorithm': 'content_similarity',
            'weight': 0.3
        },
        'trending': {
            'name': 'Trending Content',
            'algorithm': 'trending_score',
            'weight': 0.2
        },
        'personalized': {
            'name': 'Personalized',
            'algorithm': 'user_preferences',
            'weight': 0.4
        },
        'collaborative': {
            'name': 'Collaborative',
            'algorithm': 'collaborative_filtering',
            'weight': 0.1
        }
    }
    
    # Recommendation algorithms
    ALGORITHM_WEIGHTS = {
        'content_similarity': 0.3,
        'trending_score': 0.2,
        'user_preferences': 0.4,
        'collaborative_filtering': 0.1
    }
    
    # User preference factors
    USER_PREFERENCE_WEIGHTS = {
        'content_type': 0.3,
        'tags': 0.4,
        'categories': 0.2,
        'author': 0.1
    }
    
    # Performance tracking
    TRACK_RECOMMENDATION_PERFORMANCE = True
    PERFORMANCE_UPDATE_INTERVAL = 3600  # 1 hour
    PERFORMANCE_RETENTION_DAYS = 30
    
    # Diversity settings
    DIVERSITY_FACTOR = 0.2  # Add randomness for diversity
    MAX_SAME_TYPE_RECOMMENDATIONS = 5
    MAX_SAME_AUTHOR_RECOMMENDATIONS = 3
    
    # Freshness settings
    FRESHNESS_WEIGHT = 0.1  # Prefer newer content
    MAX_CONTENT_AGE_DAYS = 365  # Don't recommend content older than 1 year
    
    # Feedback integration
    FEEDBACK_ENABLED = True
    FEEDBACK_WEIGHT = 0.3  # Weight user feedback in future recommendations
    NEGATIVE_FEEDBACK_THRESHOLD = 0.3  # Threshold for negative feedback


class ContentRelationshipsConfig:
    """Main content relationships configuration class"""
    
    def __init__(self):
        self.content = ContentConfig()
        self.moderation = ContentModerationConfig()
        self.analytics = ContentAnalyticsConfig()
        self.archiving = ContentArchivingConfig()
        self.recommendations = ContentRecommendationConfig()
        
        # Load environment-specific settings
        self._load_environment_settings()
    
    def _load_environment_settings(self):
        """Load settings from environment variables"""
        # Content settings
        self.VERSIONING_ENABLED = os.getenv('CONTENT_VERSIONING_ENABLED', 'true').lower() == 'true'
        self.MAX_CONTENT_LENGTH = int(os.getenv('CONTENT_MAX_LENGTH', self.content.MAX_CONTENT_LENGTH))
        self.MAX_TAGS_PER_CONTENT = int(os.getenv('CONTENT_MAX_TAGS', self.content.MAX_TAGS_PER_CONTENT))
        
        # Moderation settings
        self.AUTO_MODERATION_ENABLED = os.getenv('CONTENT_AUTO_MODERATION_ENABLED', 'true').lower() == 'true'
        self.CONTENT_FILTERING_ENABLED = os.getenv('CONTENT_FILTERING_ENABLED', 'true').lower() == 'true'
        self.PROFANITY_FILTER_ENABLED = os.getenv('CONTENT_PROFANITY_FILTER', 'true').lower() == 'true'
        
        # Analytics settings
        self.ANALYTICS_ENABLED = os.getenv('CONTENT_ANALYTICS_ENABLED', 'true').lower() == 'true'
        self.RECOMMENDATIONS_ENABLED = os.getenv('CONTENT_RECOMMENDATIONS_ENABLED', 'true').lower() == 'true'
        
        # Archiving settings
        self.ARCHIVING_ENABLED = os.getenv('CONTENT_ARCHIVING_ENABLED', 'true').lower() == 'true'
        self.COMPRESSION_ENABLED = os.getenv('CONTENT_COMPRESSION_ENABLED', 'true').lower() == 'true'
        
        # Storage settings
        self.STORAGE_LOCATION = os.getenv('CONTENT_STORAGE_LOCATION', self.archiving.STORAGE_LOCATION)
        self.STORAGE_TYPE = os.getenv('CONTENT_STORAGE_TYPE', self.archiving.STORAGE_TYPE)
    
    def get_content_type_config(self, content_type: str) -> Dict[str, Any]:
        """Get configuration for a specific content type"""
        return self.content.CONTENT_TYPES.get(content_type, {})
    
    def get_content_status_config(self, status: str) -> Dict[str, Any]:
        """Get configuration for a specific content status"""
        return self.content.CONTENT_STATUS.get(status, {})
    
    def get_visibility_config(self, visibility: str) -> Dict[str, Any]:
        """Get configuration for a specific visibility level"""
        return self.content.VISIBILITY_LEVELS.get(visibility, {})
    
    def get_moderation_status_config(self, status: str) -> Dict[str, Any]:
        """Get configuration for a specific moderation status"""
        return self.moderation.MODERATION_STATUS.get(status, {})
    
    def get_priority_config(self, priority: str) -> Dict[str, Any]:
        """Get configuration for a specific priority level"""
        return self.moderation.PRIORITY_LEVELS.get(priority, {})
    
    def get_moderation_category_config(self, category: str) -> Dict[str, Any]:
        """Get configuration for a specific moderation category"""
        return self.moderation.MODERATION_CATEGORIES.get(category, {})
    
    def get_archive_reason_config(self, reason: str) -> Dict[str, Any]:
        """Get configuration for a specific archive reason"""
        return self.archiving.ARCHIVE_REASONS.get(reason, {})
    
    def get_retention_policy_config(self, policy: str) -> Dict[str, Any]:
        """Get configuration for a specific retention policy"""
        return self.archiving.RETENTION_POLICIES.get(policy, {})
    
    def get_recommendation_type_config(self, recommendation_type: str) -> Dict[str, Any]:
        """Get configuration for a specific recommendation type"""
        return self.recommendations.RECOMMENDATION_TYPES.get(recommendation_type, {})
    
    def validate_content_length(self, content_type: str, content: str) -> Dict[str, Any]:
        """Validate content length for a specific type"""
        content_config = self.get_content_type_config(content_type)
        max_length = content_config.get('max_length', self.content.MAX_CONTENT_LENGTH)
        
        return {
            'valid': len(content) <= max_length,
            'current_length': len(content),
            'max_length': max_length,
            'excess_length': max(0, len(content) - max_length)
        }
    
    def validate_content_creation(self, content_type: str, user_id: int) -> Dict[str, Any]:
        """Validate if user can create content of a specific type"""
        content_config = self.get_content_type_config(content_type)
        
        # Check if content type exists
        if not content_config:
            return {
                'valid': False,
                'error': 'Invalid content type'
            }
        
        # Check moderation requirements
        requires_moderation = content_config.get('requires_moderation', False)
        
        # Check user permissions (simplified)
        # In a real system, you'd check user roles and permissions
        
        return {
            'valid': True,
            'requires_moderation': requires_moderation,
            'default_visibility': content_config.get('default_visibility', 'public')
        }
    
    def get_engagement_weight(self, engagement_type: str) -> float:
        """Get engagement weight for a specific type"""
        return self.analytics.ENGAGEMENT_WEIGHTS.get(engagement_type, 1.0)
    
    def get_quality_weight(self, quality_factor: str) -> float:
        """Get quality weight for a specific factor"""
        return self.analytics.QUALITY_WEIGHTS.get(quality_factor, 0.1)
    
    def calculate_quality_score(self, content_data: Dict[str, Any]) -> float:
        """Calculate quality score based on content data"""
        score = 0.0
        
        # Content length factor
        content_length = len(content_data.get('content', ''))
        if 100 <= content_length <= 2000:
            score += self.get_quality_weight('content_length')
        elif 2000 < content_length <= 5000:
            score += self.get_quality_weight('content_length') * 0.8
        elif content_length > 5000:
            score += self.get_quality_weight('content_length') * 0.5
        
        # Title quality factor
        title = content_data.get('title', '')
        if title and len(title.strip()) > 0:
            score += self.get_quality_weight('title_quality')
        
        # Summary quality factor
        summary = content_data.get('summary', '')
        if summary and len(summary.strip()) > 0:
            score += self.get_quality_weight('summary_quality')
        
        # Metadata completeness factor
        metadata = content_data.get('metadata', {})
        if metadata:
            score += self.get_quality_weight('metadata_completeness')
        
        # Tag relevance factor
        tags = content_data.get('tags', [])
        if tags:
            score += min(1.0, len(tags) * self.get_quality_weight('tag_relevance'))
        
        # Category appropriateness factor
        categories = content_data.get('categories', [])
        if categories:
            score += min(1.0, len(categories) * self.get_quality_weight('category_appropriateness'))
        
        return min(1.0, score)
    
    def get_performance_grade(self, score: float) -> str:
        """Get performance grade based on score"""
        thresholds = self.analytics.PERFORMANCE_GRADE_THRESHOLDS
        
        for grade, threshold in thresholds.items():
            if score >= threshold:
                return grade
        
        return 'F'
    
    def get_recommendation_weights(self) -> Dict[str, float]:
        """Get recommendation algorithm weights"""
        return self.recommendations.ALGORITHM_WEIGHTS
    
    def get_user_preference_weights(self) -> Dict[str, float]:
        """Get user preference weights"""
        return self.recommendations.USER_PREFERENCE_WEIGHTS
    
    def should_auto_moderate(self, content_type: str) -> bool:
        """Check if content type should be auto-moderated"""
        if not self.AUTO_MODERATION_ENABLED:
            return False
        
        content_config = self.get_content_type_config(content_type)
        return content_config.get('requires_moderation', False)
    
    def should_auto_flag(self, confidence_score: float) -> bool:
        """Check if content should be auto-flagged"""
        return (self.AUTO_MODERATION_ENABLED and 
                confidence_score >= self.moderation.AUTO_FLAG_THRESHOLD)
    
    def should_auto_reject(self, confidence_score: float) -> bool:
        """Check if content should be auto-rejected"""
        return (self.AUTO_MODERATION_ENABLED and 
                confidence_score >= self.moderation.AUTO_REJECT_THRESHOLD)
    
    def get_archive_retention_days(self, reason: str) -> int:
        """Get retention days for archive reason"""
        reason_config = self.get_archive_reason_config(reason)
        return reason_config.get('default_retention_days', self.archiving.RETENTION_POLICIES['standard']['days'])
    
    def should_compress_archive(self) -> bool:
        """Check if archives should be compressed"""
        return self.COMPRESSION_ENABLED and self.archiving.COMPRESSION_ENABLED
    
    def get_storage_settings(self) -> Dict[str, Any]:
        """Get storage configuration"""
        return {
            'location': self.STORAGE_LOCATION,
            'type': self.STORAGE_TYPE,
            'compression_enabled': self.should_compress_archive(),
            'compression_type': self.archiving.COMPRESSION_TYPE,
            'compression_level': self.archiving.COMPRESSION_LEVEL
        }
    
    def is_content_type_valid(self, content_type: str) -> bool:
        """Check if content type is valid"""
        return content_type in self.content.CONTENT_TYPES
    
    def is_status_valid(self, status: str) -> bool:
        """Check if content status is valid"""
        return status in self.content.CONTENT_STATUS
    
    def is_visibility_valid(self, visibility: str) -> bool:
        """Check if visibility level is valid"""
        return visibility in self.content.VISIBILITY_LEVELS
    
    def is_moderation_status_valid(self, status: str) -> bool:
        """Check if moderation status is valid"""
        return status in self.moderation.MODERATION_STATUS
    
    def is_priority_valid(self, priority: str) -> bool:
        """Check if priority level is valid"""
        return priority in self.moderation.PRIORITY_LEVELS
    
    def export_config(self) -> Dict[str, Any]:
        """Export all configuration settings"""
        return {
            'content': {
                'types': self.content.CONTENT_TYPES,
                'status': self.content.CONTENT_STATUS,
                'visibility': self.content.VISIBILITY_LEVELS,
                'limits': {
                    'max_title_length': self.content.MAX_TITLE_LENGTH,
                    'max_content_length': self.content.MAX_CONTENT_LENGTH,
                    'max_tags_per_content': self.content.MAX_TAGS_PER_CONTENT,
                    'max_categories_per_content': self.content.MAX_CATEGORIES_PER_CONTENT
                },
                'quality_thresholds': {
                    'min': self.content.MIN_QUALITY_SCORE,
                    'good': self.content.GOOD_QUALITY_SCORE,
                    'excellent': self.content.EXCELLENT_QUALITY_SCORE
                },
                'engagement_thresholds': {
                    'low': self.content.LOW_ENGAGEMENT_RATE,
                    'average': self.content.AVERAGE_ENGAGEMENT_RATE,
                    'high': self.content.HIGH_ENGAGEMENT_RATE
                },
                'versioning': {
                    'enabled': self.VERSIONING_ENABLED,
                    'auto_version_on_update': self.content.AUTO_VERSION_ON_UPDATE,
                    'retention_days': self.content.VERSION_RETENTION_DAYS
                }
            },
            'moderation': {
                'status': self.moderation.MODERATION_STATUS,
                'priority': self.moderation.PRIORITY_LEVELS,
                'categories': self.moderation.MODERATION_CATEGORIES,
                'auto_moderation': {
                    'enabled': self.AUTO_MODERATION_ENABLED,
                    'threshold': self.moderation.AUTO_MODERATION_THRESHOLD,
                    'flag_threshold': self.moderation.AUTO_FLAG_THRESHOLD,
                    'reject_threshold': self.moderation.AUTO_REJECT_THRESHOLD
                },
                'reporting': {
                    'auto_flag_threshold': self.moderation.REPORT_THRESHOLD_AUTO_FLAG,
                    'auto_reject_threshold': self.moderation.REPORT_THRESHOLD_AUTO_REJECT,
                    'urgent_threshold': self.moderation.REPORT_THRESHOLD_URGENT
                },
                'content_filtering': {
                    'enabled': self.CONTENT_FILTERING_ENABLED,
                    'profanity_filter': self.PROFANITY_FILTER_ENABLED,
                    'spam_detection': self.moderation.SPAM_DETECTION_ENABLED,
                    'plagiarism_detection': self.moderation.PLAGIARISM_DETECTION_ENABLED
                }
            },
            'analytics': {
                'enabled': self.ANALYTICS_ENABLED,
                'engagement_weights': self.analytics.ENGAGEMENT_WEIGHTS,
                'quality_weights': self.analytics.QUALITY_WEIGHTS,
                'trending': {
                    'calculation_interval': self.analytics.TRENDING_CALCULATION_INTERVAL,
                    'time_window_hours': self.analytics.TRENDING_TIME_WINDOW_HOURS,
                    'min_views': self.analytics.TRENDING_MIN_VIEWS,
                    'min_engagement': self.analytics.TRENDING_MIN_ENGAGEMENT
                },
                'performance': {
                    'grade_thresholds': self.analytics.PERFORMANCE_GRADE_THRESHOLDS
                },
                'recommendations': {
                    'enabled': self.RECOMMENDATIONS_ENABLED,
                    'cache_ttl': self.analytics.RECOMMENDATION_CACHE_TTL,
                    'limits': {
                        'users': self.analytics.RECOMMENDATION_LIMIT_USERS,
                        'similar': self.analytics.RECOMMENDATION_LIMIT_SIMILAR,
                        'trending': self.analytics.RECOMMENDATION_LIMIT_TRENDING
                    },
                    'min_score': self.analytics.RECOMMENDATION_MIN_SCORE
                }
            },
            'archiving': {
                'enabled': self.ARCHIVING_ENABLED,
                'reasons': self.archiving.ARCHIVE_REASONS,
                'retention_policies': self.archiving.RETENTION_POLICIES,
                'compression': {
                    'enabled': self.should_compress_archive(),
                    'type': self.archiving.COMPRESSION_TYPE,
                    'level': self.archiving.COMPRESSION_LEVEL
                },
                'storage': self.get_storage_settings(),
                'cleanup': {
                    'interval_hours': self.archiving.CLEANUP_INTERVAL_HOURS,
                    'batch_size': self.archiving.CLEANUP_BATCH_SIZE,
                    'delete_expired': self.archiving.DELETE_EXPIRED_ARCHIVES
                }
            },
            'recommendations': {
                'types': self.recommendations.RECOMMENDATION_TYPES,
                'algorithm_weights': self.recommendations.ALGORITHM_WEIGHTS,
                'user_preference_weights': self.recommendations.USER_PREFERENCE_WEIGHTS,
                'diversity': {
                    'factor': self.recommendations.DIVERSITY_FACTOR,
                    'max_same_type': self.recommendations.MAX_SAME_TYPE_RECOMMENDATIONS,
                    'max_same_author': self.recommendations.MAX_SAME_AUTHOR_RECOMMENDATIONS
                },
                'freshness': {
                    'weight': self.recommendations.FRESHNESS_WEIGHT,
                    'max_age_days': self.recommendations.MAX_CONTENT_AGE_DAYS
                },
                'feedback': {
                    'enabled': self.recommendations.FEEDBACK_ENABLED,
                    'weight': self.recommendations.FEEDBACK_WEIGHT,
                    'negative_threshold': self.recommendations.NEGATIVE_FEEDBACK_THRESHOLD
                }
            }
        }


# Global configuration instance
content_config = ContentRelationshipsConfig()
