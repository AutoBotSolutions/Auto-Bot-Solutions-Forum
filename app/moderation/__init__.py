"""
Automated Content Moderation System

This module provides comprehensive AI-powered content moderation functionality for the Auto Bot Solutions Forum,
including automated spam detection, content quality scoring, moderation queue management, and automated moderation actions.
"""

from .models import (
    ModerationQueue,
    ContentAnalysis,
    ModerationAction,
    ModerationRule,
    SpamDetection,
    ContentQuality,
    ModerationPattern,
    ModerationHistory
)

from .service import (
    ModerationService,
    ContentAnalysisService,
    SpamDetectionService,
    ContentQualityService,
    ModerationQueueService,
    ModerationRuleService,
    AutomatedModerationService
)

from .forms import (
    ModerationQueueForm,
    ContentAnalysisForm,
    ModerationActionForm,
    ModerationRuleForm,
    SpamDetectionForm,
    ContentQualityForm,
    ModerationPatternForm,
    ModerationSettingsForm
)

from .routes import moderation_bp

__all__ = [
    'ModerationQueue',
    'ContentAnalysis',
    'ModerationAction',
    'ModerationRule',
    'SpamDetection',
    'ContentQuality',
    'ModerationPattern',
    'ModerationHistory',
    'ModerationService',
    'ContentAnalysisService',
    'SpamDetectionService',
    'ContentQualityService',
    'ModerationQueueService',
    'ModerationRuleService',
    'AutomatedModerationService',
    'ModerationQueueForm',
    'ContentAnalysisForm',
    'ModerationActionForm',
    'ModerationRuleForm',
    'SpamDetectionForm',
    'ContentQualityForm',
    'ModerationPatternForm',
    'ModerationSettingsForm',
    'moderation_bp'
]
