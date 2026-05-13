"""
WebSocket Notification Events

This module contains WebSocket event handlers for real-time notifications,
including admin alerts, security events, system health monitoring, and user activity notifications.
"""

from flask import current_app
from flask_login import current_user
from app.websockets.events import emit_to_user, emit_to_admins, emit_to_moderators
from app.notifications.service import (
    AdminNotificationService, SecurityNotificationService,
    SystemHealthNotificationService, ModerationNotificationService,
    UserActivityNotificationService
)
import json


def emit_notification_created(notification):
    """Emit notification created event"""
    
    data = {
        'notification_id': notification.id,
        'title': notification.title,
        'message': notification.message,
        'notification_type': notification.notification_type,
        'category': notification.category,
        'priority': notification.priority,
        'severity': notification.severity,
        'requires_action': notification.requires_action,
        'action_url': notification.action_url,
        'target_type': notification.target_type,
        'target_id': notification.target_id,
        'created_at': notification.created_at.isoformat(),
        'data': notification.data or {}
    }
    
    # Emit to the specific user
    emit_to_user(notification.user_id, 'notification_created', data)
    
    # Also emit to admins if it's a system notification
    if notification.notification_type in ['security', 'system', 'moderation']:
        emit_to_admins('admin_notification_created', data)


def emit_notification_read(notification_id, user_id, unread_count):
    """Emit notification read event"""
    
    data = {
        'notification_id': notification_id,
        'user_id': user_id,
        'unread_count': unread_count
    }
    
    emit_to_user(user_id, 'notification_read', data)
    
    # Also emit to admins for system monitoring
    emit_to_admins('notification_read_admin', data)


def emit_notification_acknowledged(notification_id):
    """Emit notification acknowledged event"""
    
    data = {
        'notification_id': notification_id,
        'acknowledged_at': current_app.extensions['moment'].utcnow().isoformat()
    }
    
    # Emit to all admins for monitoring
    emit_to_admins('notification_acknowledged', data)


def emit_notification_deleted(notification_id, user_id, unread_count):
    """Emit notification deleted event"""
    
    data = {
        'notification_id': notification_id,
        'user_id': user_id,
        'unread_count': unread_count
    }
    
    emit_to_user(user_id, 'notification_deleted', data)
    
    # Also emit to admins for system monitoring
    emit_to_admins('notification_deleted_admin', data)


def emit_all_notifications_read(user_id):
    """Emit all notifications read event"""
    
    data = {
        'user_id': user_id,
        'unread_count': 0,
        'read_at': current_app.extensions['moment'].utcnow().isoformat()
    }
    
    emit_to_user(user_id, 'all_notifications_read', data)
    
    # Also emit to admins for monitoring
    emit_to_admins('all_notifications_read_admin', data)


def emit_security_alert(event_type, description, severity, data=None):
    """Emit security alert to all admins"""
    
    notification_service = SecurityNotificationService()
    
    # Create notification
    notifications = notification_service.notify_security_event(
        event_type=event_type,
        description=description,
        severity=severity,
        data=data
    )
    
    # Emit real-time alert
    alert_data = {
        'event_type': event_type,
        'description': description,
        'severity': severity,
        'data': data or {},
        'timestamp': current_app.extensions['moment'].utcnow().isoformat(),
        'notification_count': len(notifications)
    }
    
    emit_to_admins('security_alert', alert_data)
    
    return notifications


def emit_system_alert(alert_type, description, severity, metric_value=None, threshold=None, data=None):
    """Emit system health alert to all admins"""
    
    system_service = SystemHealthNotificationService()
    
    # Create notification
    notifications = system_service.notify_system_alert(
        alert_type=alert_type,
        description=description,
        severity=severity,
        metric_value=metric_value,
        threshold=threshold,
        data=data
    )
    
    # Emit real-time alert
    alert_data = {
        'alert_type': alert_type,
        'description': description,
        'severity': severity,
        'metric_value': metric_value,
        'threshold': threshold,
        'data': data or {},
        'timestamp': current_app.extensions['moment'].utcnow().isoformat(),
        'notification_count': len(notifications)
    }
    
    emit_to_admins('system_alert', alert_data)
    
    return notifications


def emit_moderation_alert(content_type, content_id, reporter_id, reason, data=None):
    """Emit moderation alert to all moderators"""
    
    moderation_service = ModerationNotificationService()
    
    # Create notification
    notifications = moderation_service.notify_content_reported(
        content_type=content_type,
        content_id=content_id,
        reporter_id=reporter_id,
        reason=reason
    )
    
    # Emit real-time alert
    alert_data = {
        'content_type': content_type,
        'content_id': content_id,
        'reporter_id': reporter_id,
        'reason': reason,
        'data': data or {},
        'timestamp': current_app.extensions['moment'].utcnow().isoformat(),
        'notification_count': len(notifications)
    }
    
    emit_to_moderators('moderation_alert', alert_data)
    
    return notifications


def emit_user_activity_alert(user_id, activity_type, threshold, current_value, data=None):
    """Emit user activity alert to all admins"""
    
    activity_service = UserActivityNotificationService()
    
    # Create notification
    notifications = activity_service.notify_user_activity_threshold(
        user_id=user_id,
        activity_type=activity_type,
        threshold=threshold,
        current_value=current_value
    )
    
    # Emit real-time alert
    alert_data = {
        'user_id': user_id,
        'activity_type': activity_type,
        'threshold': threshold,
        'current_value': current_value,
        'data': data or {},
        'timestamp': current_app.extensions['moment'].utcnow().isoformat(),
        'notification_count': len(notifications)
    }
    
    emit_to_admins('user_activity_alert', alert_data)
    
    return notifications


def emit_real_time_metrics(metrics):
    """Emit real-time system metrics to all admins"""
    
    data = {
        'metrics': metrics,
        'timestamp': current_app.extensions['moment'].utcnow().isoformat()
    }
    
    emit_to_admins('real_time_metrics', data)


def emit_user_online_status(user_id, is_online):
    """Emit user online status change"""
    
    data = {
        'user_id': user_id,
        'is_online': is_online,
        'timestamp': current_app.extensions['moment'].utcnow().isoformat()
    }
    
    # Emit to all admins and moderators
    emit_to_admins('user_status_change', data)
    emit_to_moderators('user_status_change', data)


def emit_new_user_registration(user_id, username, email):
    """Emit new user registration alert"""
    
    data = {
        'user_id': user_id,
        'username': username,
        'email': email,
        'timestamp': current_app.extensions['moment'].utcnow().isoformat()
    }
    
    emit_to_admins('new_user_registration', data)


def emit_bulk_notification_created(notification_count, notification_type):
    """Emit bulk notification created event"""
    
    data = {
        'notification_count': notification_count,
        'notification_type': notification_type,
        'timestamp': current_app.extensions['moment'].utcnow().isoformat()
    }
    
    emit_to_admins('bulk_notification_created', data)


def emit_notification_stats_update(stats):
    """Emit notification statistics update"""
    
    data = {
        'stats': stats,
        'timestamp': current_app.extensions['moment'].utcnow().isoformat()
    }
    
    emit_to_admins('notification_stats_update', data)


# Event handlers for WebSocket connections
def handle_notification_subscribe(socketio, data):
    """Handle notification subscription"""
    
    user_id = current_user.id if current_user.is_authenticated else None
    
    if user_id:
        # Send unread count
        from .service import NotificationService
        notification_service = NotificationService()
        unread_count = notification_service.get_unread_count(user_id)
        
        socketio.emit('unread_count', {
            'unread_count': unread_count
        })
        
        # Send recent notifications
        recent_notifications = notification_service.get_user_notifications(
            user_id, limit=5
        )
        
        socketio.emit('recent_notifications', {
            'notifications': [n.to_dict() for n in recent_notifications]
        })


def handle_notification_mark_read(socketio, data):
    """Handle notification mark read event"""
    
    user_id = current_user.id if current_user.is_authenticated else None
    notification_id = data.get('notification_id')
    
    if user_id and notification_id:
        from .service import NotificationService
        notification_service = NotificationService()
        
        notification = notification_service.mark_as_read(notification_id, user_id)
        
        if notification:
            emit_notification_read(notification_id, user_id, notification_service.get_unread_count(user_id))


def handle_notification_acknowledge(socketio, data):
    """Handle notification acknowledge event"""
    
    user_id = current_user.id if current_user.is_authenticated else None
    notification_id = data.get('notification_id')
    
    if user_id and notification_id:
        from .service import NotificationService
        notification_service = NotificationService()
        
        notification = notification_service.acknowledge_notification(notification_id, user_id)
        
        if notification:
            emit_notification_acknowledged(notification_id)


def handle_notification_delete(socketio, data):
    """Handle notification delete event"""
    
    user_id = current_user.id if current_user.is_authenticated else None
    notification_id = data.get('notification_id')
    
    if user_id and notification_id:
        from .service import NotificationService
        notification_service = NotificationService()
        
        notification = notification_service.delete_notification(notification_id, user_id)
        
        if notification:
            emit_notification_deleted(notification_id, user_id, notification_service.get_unread_count(user_id))


def handle_mark_all_read(socketio, data):
    """Handle mark all notifications read event"""
    
    user_id = current_user.id if current_user.is_authenticated else None
    
    if user_id:
        from .service import NotificationService
        notification_service = NotificationService()
        
        count = notification_service.mark_all_as_read(user_id)
        
        if count > 0:
            emit_all_notifications_read(user_id)


def handle_get_unread_count(socketio, data):
    """Handle get unread count event"""
    
    user_id = current_user.id if current_user.is_authenticated else None
    
    if user_id:
        from .service import NotificationService
        notification_service = NotificationService()
        
        unread_count = notification_service.get_unread_count(user_id)
        
        socketio.emit('unread_count', {
            'unread_count': unread_count
        })


def handle_get_recent_notifications(socketio, data):
    """Handle get recent notifications event"""
    
    user_id = current_user.id if current_user.is_authenticated else None
    limit = data.get('limit', 5)
    
    if user_id:
        from .service import NotificationService
        notification_service = NotificationService()
        
        notifications = notification_service.get_user_notifications(
            user_id, limit=limit
        )
        
        socketio.emit('recent_notifications', {
            'notifications': [n.to_dict() for n in notifications]
        })


# System monitoring events
def handle_failed_login_attempt(socketio, data):
    """Handle failed login attempt"""
    
    username = data.get('username')
    ip_address = data.get('ip_address')
    user_id = data.get('user_id')
    
    if username and ip_address:
        emit_security_alert(
            event_type='failed_login',
            description=f"Failed login attempt for user: {username}",
            severity='warning',
            data={
                'username': username,
                'ip_address': ip_address,
                'user_id': user_id
            }
        )


def handle_suspicious_activity(socketio, data):
    """Handle suspicious activity detection"""
    
    description = data.get('description')
    user_id = data.get('user_id')
    ip_address = data.get('ip_address')
    severity = data.get('severity', 'warning')
    activity_data = data.get('data', {})
    
    if description:
        emit_security_alert(
            event_type='suspicious_activity',
            description=description,
            severity=severity,
            user_id=user_id,
            ip_address=ip_address,
            data=activity_data
        )


def handle_system_health_warning(socketio, data):
    """Handle system health warning"""
    
    alert_type = data.get('alert_type')
    description = data.get('description')
    severity = data.get('severity', 'warning')
    metric_value = data.get('metric_value')
    threshold = data.get('threshold')
    health_data = data.get('data', {})
    
    if alert_type and description:
        emit_system_alert(
            alert_type=alert_type,
            description=description,
            severity=severity,
            metric_value=metric_value,
            threshold=threshold,
            data=health_data
        )


def handle_content_report(socketio, data):
    """Handle content report"""
    
    content_type = data.get('content_type')
    content_id = data.get('content_id')
    reporter_id = data.get('reporter_id')
    reason = data.get('reason')
    report_data = data.get('data', {})
    
    if content_type and content_id and reporter_id and reason:
        emit_moderation_alert(
            content_type=content_type,
            content_id=content_id,
            reporter_id=reporter_id,
            reason=reason,
            data=report_data
        )


def handle_user_activity_threshold(socketio, data):
    """Handle user activity threshold exceeded"""
    
    user_id = data.get('user_id')
    activity_type = data.get('activity_type')
    threshold = data.get('threshold')
    current_value = data.get('current_value')
    activity_data = data.get('data', {})
    
    if user_id and activity_type and threshold and current_value:
        emit_user_activity_alert(
            user_id=user_id,
            activity_type=activity_type,
            threshold=threshold,
            current_value=current_value,
            data=activity_data
        )


# Notification preference updates
def handle_preference_update(socketio, data):
    """Handle notification preference update"""
    
    user_id = current_user.id if current_user.is_authenticated else None
    
    if user_id:
        # Emit preference update to user
        socketio.emit('preference_updated', data)
        
        # Also emit to admins for monitoring
        emit_to_admins('user_preference_updated', {
            'user_id': user_id,
            'preferences': data,
            'timestamp': current_app.extensions['moment'].utcnow().isoformat()
        })


# Notification delivery tracking
def handle_notification_delivery_status(socketio, data):
    """Handle notification delivery status update"""
    
    notification_id = data.get('notification_id')
    delivery_type = data.get('delivery_type')
    status = data.get('status')
    recipient = data.get('recipient')
    
    if notification_id and delivery_type and status:
        delivery_data = {
            'notification_id': notification_id,
            'delivery_type': delivery_type,
            'status': status,
            'recipient': recipient,
            'timestamp': current_app.extensions['moment'].utcnow().isoformat()
        }
        
        # Emit to admins for monitoring
        emit_to_admins('notification_delivery_status', delivery_data)
