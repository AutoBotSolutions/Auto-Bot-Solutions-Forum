"""
Real-time Admin Notifications System

This module provides comprehensive real-time notification functionality for the Auto Bot Solutions Forum,
including WebSocket-based admin alerts, security event notifications, system health monitoring,
content moderation alerts, and user activity threshold notifications.
"""

from .models import (
    AdminNotification,
    NotificationTemplate,
    NotificationPreference,
    NotificationDelivery,
    NotificationCategory
)

from .service import (
    NotificationService,
    AdminNotificationService,
    SecurityNotificationService,
    SystemHealthNotificationService,
    ModerationNotificationService,
    UserActivityNotificationService
)

from .forms import (
    NotificationFilterForm,
    NotificationTemplateForm,
    NotificationPreferenceForm,
    NotificationSettingsForm
)

from .routes import notifications_bp

__all__ = [
    'AdminNotification',
    'NotificationTemplate',
    'NotificationPreference',
    'NotificationDelivery',
    'NotificationCategory',
    'NotificationService',
    'AdminNotificationService',
    'SecurityNotificationService',
    'SystemHealthNotificationService',
    'ModerationNotificationService',
    'UserActivityNotificationService',
    'NotificationFilterForm',
    'NotificationTemplateForm',
    'NotificationPreferenceForm',
    'NotificationSettingsForm',
    'notifications_bp'
]
