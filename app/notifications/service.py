"""
Real-time Admin Notifications Service Layer

This module contains service classes for handling notification logic,
including notification creation, delivery, preferences, and real-time updates.
"""

from datetime import datetime, timedelta, timezone
from flask import current_app, url_for
from sqlalchemy import and_, or_, desc, func
from app import db
from app.models import User
from .models import (
    AdminNotification, NotificationTemplate, NotificationPreference,
    NotificationDelivery, NotificationCategory
)
from app.websockets.events import emit_to_admins
import json


class NotificationService:
    """Base service for notification management"""
    
    def __init__(self):
        self.default_expires_hours = 168  # 7 days
    
    def create_notification(self, title, message, notification_type, category,
                           user_id=None, priority='medium', severity='info',
                           target_type=None, target_id=None, target_url=None,
                           source='system', source_id=None, data=None,
                           metadata=None, requires_action=False, action_url=None,
                           expires_hours=None):
        """Create a new notification"""
        
        # Get category for defaults
        category_obj = NotificationCategory.query.filter_by(name=category).first()
        if category_obj:
            default_priority = category_obj.default_priority
            default_severity = category_obj.default_severity
            default_expires = category_obj.default_expires_hours
        else:
            default_priority = 'medium'
            default_severity = 'info'
            default_expires = self.default_expires_hours
        
        # Use provided values or defaults
        notification = AdminNotification(
            title=title,
            message=message,
            notification_type=notification_type,
            category=category,
            priority=priority or default_priority,
            severity=severity or default_severity,
            target_type=target_type,
            target_id=target_id,
            target_url=target_url,
            source=source,
            source_id=source_id,
            data=data or {},
            notification_metadata=metadata or {},
            requires_action=requires_action or (category_obj.requires_action if category_obj else False),
            action_url=action_url,
            expires_at=datetime.utcnow() + timedelta(hours=expires_hours or default_expires),
            user_id=user_id
        )
        
        db.session.add(notification)
        db.session.commit()
        
        # Mark as delivered
        notification.delivered_at = datetime.utcnow()
        db.session.commit()
        
        return notification
    
    def create_notification_from_template(self, template_name, user_id, variables=None):
        """Create notification from template"""
        
        template = NotificationTemplate.query.filter_by(name=template_name, is_active=True).first()
        if not template:
            raise ValueError(f"Template '{template_name}' not found or inactive")
        
        # Render templates
        title = template.render_title(variables)
        message = template.render_message(variables)
        
        # Create notification
        notification = self.create_notification(
            title=title,
            message=message,
            notification_type=template.notification_type,
            category=template.category,
            user_id=user_id,
            priority=template.default_priority,
            severity=template.default_severity,
            requires_action=template.requires_action,
            action_url=template.action_template,
            expires_hours=template.default_expires_hours,
            data={'template_name': template_name, 'variables': variables}
        )
        
        return notification
    
    def get_user_notifications(self, user_id, unread_only=False, limit=50, offset=0):
        """Get notifications for a user"""
        
        query = AdminNotification.query.filter_by(user_id=user_id)
        
        if unread_only:
            query = query.filter_by(is_read=False)
        
        notifications = query.order_by(desc(AdminNotification.created_at)).offset(offset).limit(limit).all()
        
        return notifications
    
    def get_unread_count(self, user_id):
        """Get count of unread notifications for a user"""
        
        count = AdminNotification.query.filter_by(user_id=user_id, is_read=False).count()
        return count
    
    def mark_as_read(self, notification_id, user_id):
        """Mark notification as read"""
        
        notification = AdminNotification.query.filter_by(id=notification_id, user_id=user_id).first()
        if notification and not notification.is_read:
            notification.is_read = True
            notification.read_at = datetime.utcnow()
            db.session.commit()
            
            # Send WebSocket update
            emit_to_admins('notification_read', {
                'notification_id': notification_id,
                'unread_count': self.get_unread_count(user_id)
            })
        
        return notification
    
    def mark_all_as_read(self, user_id):
        """Mark all notifications as read for a user"""
        
        notifications = AdminNotification.query.filter_by(user_id=user_id, is_read=False).all()
        
        for notification in notifications:
            notification.is_read = True
            notification.read_at = datetime.utcnow()
        
        db.session.commit()
        
        # Send WebSocket update
        emit_to_admins('all_notifications_read', {
            'user_id': user_id,
            'unread_count': 0
        })
        
        return len(notifications)
    
    def acknowledge_notification(self, notification_id, user_id):
        """Acknowledge notification"""
        
        notification = AdminNotification.query.filter_by(id=notification_id, user_id=user_id).first()
        if notification and not notification.is_acknowledged:
            notification.is_acknowledged = True
            notification.acknowledged_at = datetime.utcnow()
            db.session.commit()
            
            # Send WebSocket update
            emit_to_admins('notification_acknowledged', {
                'notification_id': notification_id
            })
        
        return notification
    
    def delete_notification(self, notification_id, user_id):
        """Delete notification"""
        
        notification = AdminNotification.query.filter_by(id=notification_id, user_id=user_id).first()
        if notification:
            db.session.delete(notification)
            db.session.commit()
            
            # Send WebSocket update
            emit_to_admins('notification_deleted', {
                'notification_id': notification_id,
                'unread_count': self.get_unread_count(user_id)
            })
        
        return notification
    
    def cleanup_expired_notifications(self):
        """Clean up expired notifications"""
        
        expired = AdminNotification.query.filter(
            AdminNotification.expires_at < datetime.utcnow()
        ).all()
        
        for notification in expired:
            db.session.delete(notification)
        
        db.session.commit()
        
        return len(expired)


class AdminNotificationService(NotificationService):
    """Service for admin-specific notifications"""
    
    def notify_admins(self, title, message, category='admin', priority='medium', 
                     severity='info', data=None, metadata=None):
        """Send notification to all admin users"""
        
        admin_users = User.query.filter_by(is_admin=True).all()
        notifications = []
        
        for admin in admin_users:
            notification = self.create_notification(
                title=title,
                message=message,
                notification_type='admin',
                category=category,
                user_id=admin.id,
                priority=priority,
                severity=severity,
                data=data,
                metadata=metadata
            )
            notifications.append(notification)
        
        # Send WebSocket update to all admins
        emit_to_admins('admin_notification', {
            'title': title,
            'message': message,
            'category': category,
            'priority': priority,
            'severity': severity,
            'data': data,
            'count': len(notifications)
        })
        
        return notifications
    
    def notify_moderators(self, title, message, category='moderation', data=None):
        """Send notification to all moderator users"""
        
        moderator_users = User.query.filter(
            or_(User.is_admin == True, User.is_moderator == True)
        ).all()
        
        notifications = []
        
        for moderator in moderator_users:
            notification = self.create_notification(
                title=title,
                message=message,
                notification_type='moderation',
                category=category,
                user_id=moderator.id,
                data=data
            )
            notifications.append(notification)
        
        # Send WebSocket update
        emit_to_admins('moderator_notification', {
            'title': title,
            'message': message,
            'category': category,
            'data': data,
            'count': len(notifications)
        })
        
        return notifications


class SecurityNotificationService(NotificationService):
    """Service for security-related notifications"""
    
    def notify_security_event(self, event_type, description, user_id=None, 
                            ip_address=None, severity='warning', data=None):
        """Send security event notification"""
        
        title = f"Security Event: {event_type}"
        message = f"Security event detected: {description}"
        
        if ip_address:
            message += f" from IP: {ip_address}"
        
        # Send to all admins
        admin_service = AdminNotificationService()
        notifications = admin_service.notify_admins(
            title=title,
            message=message,
            category='security',
            priority='high',
            severity=severity,
            data={
                'event_type': event_type,
                'ip_address': ip_address,
                'user_id': user_id,
                **(data or {})
            }
        )
        
        return notifications
    
    def notify_failed_login(self, username, ip_address, user_id=None):
        """Notify about failed login attempt"""
        
        return self.notify_security_event(
            event_type='failed_login',
            description=f"Failed login attempt for user: {username}",
            user_id=user_id,
            ip_address=ip_address,
            severity='warning',
            data={'username': username}
        )
    
    def notify_suspicious_activity(self, description, user_id=None, ip_address=None, data=None):
        """Notify about suspicious activity"""
        
        return self.notify_security_event(
            event_type='suspicious_activity',
            description=description,
            user_id=user_id,
            ip_address=ip_address,
            severity='error',
            data=data
        )
    
    def notify_brute_force_attempt(self, ip_address, attempt_count):
        """Notify about brute force attempt"""
        
        return self.notify_security_event(
            event_type='brute_force',
            description=f"Brute force attack detected from {ip_address} ({attempt_count} attempts)",
            ip_address=ip_address,
            severity='critical',
            data={'attempt_count': attempt_count}
        )
    
    def notify_privilege_escalation(self, user_id, old_role, new_role):
        """Notify about privilege escalation"""
        
        user = User.query.get(user_id)
        username = user.username if user else f"User {user_id}"
        
        return self.notify_security_event(
            event_type='privilege_escalation',
            description=f"Privilege escalation for {username}: {old_role} → {new_role}",
            user_id=user_id,
            severity='warning',
            data={
                'username': username,
                'old_role': old_role,
                'new_role': new_role
            }
        )


class SystemHealthNotificationService(NotificationService):
    """Service for system health notifications"""
    
    def notify_system_alert(self, alert_type, description, severity='warning', 
                          metric_value=None, threshold=None, data=None):
        """Send system health alert"""
        
        title = f"System Alert: {alert_type}"
        message = f"System health alert: {description}"
        
        if metric_value is not None:
            message += f" (Current: {metric_value})"
        if threshold is not None:
            message += f" (Threshold: {threshold})"
        
        # Send to all admins
        admin_service = AdminNotificationService()
        notifications = admin_service.notify_admins(
            title=title,
            message=message,
            category='system_health',
            priority='high' if severity == 'critical' else 'medium',
            severity=severity,
            data={
                'alert_type': alert_type,
                'metric_value': metric_value,
                'threshold': threshold,
                **(data or {})
            }
        )
        
        return notifications
    
    def notify_high_cpu_usage(self, cpu_usage, threshold=80):
        """Notify about high CPU usage"""
        
        return self.notify_system_alert(
            alert_type='high_cpu_usage',
            description=f"CPU usage is critically high",
            severity='critical' if cpu_usage > 90 else 'warning',
            metric_value=cpu_usage,
            threshold=threshold,
            data={'metric': 'cpu_usage', 'unit': '%'}
        )
    
    def notify_high_memory_usage(self, memory_usage, threshold=85):
        """Notify about high memory usage"""
        
        return self.notify_system_alert(
            alert_type='high_memory_usage',
            description=f"Memory usage is critically high",
            severity='critical' if memory_usage > 95 else 'warning',
            metric_value=memory_usage,
            threshold=threshold,
            data={'metric': 'memory_usage', 'unit': '%'}
        )
    
    def notify_disk_space_low(self, disk_usage, threshold=90):
        """Notify about low disk space"""
        
        return self.notify_system_alert(
            alert_type='disk_space_low',
            description=f"Disk space is running low",
            severity='critical' if disk_usage > 95 else 'warning',
            metric_value=disk_usage,
            threshold=threshold,
            data={'metric': 'disk_usage', 'unit': '%'}
        )
    
    def notify_database_error(self, error_message, error_code=None):
        """Notify about database error"""
        
        return self.notify_system_alert(
            alert_type='database_error',
            description=f"Database error occurred: {error_message}",
            severity='critical',
            data={
                'error_message': error_message,
                'error_code': error_code
            }
        )
    
    def notify_service_down(self, service_name, duration=None):
        """Notify about service downtime"""
        
        message = f"Service {service_name} is down"
        if duration:
            message += f" (Down for {duration})"
        
        return self.notify_system_alert(
            alert_type='service_down',
            description=message,
            severity='critical',
            data={
                'service_name': service_name,
                'duration': duration
            }
        )


class ModerationNotificationService(NotificationService):
    """Service for moderation-related notifications"""
    
    def notify_content_reported(self, content_type, content_id, reporter_id, reason):
        """Notify about reported content"""
        
        reporter = User.query.get(reporter_id)
        reporter_name = reporter.username if reporter else f"User {reporter_id}"
        
        title = f"Content Reported: {content_type.title()}"
        message = f"{content_type.title()} #{content_id} reported by {reporter_name}"
        message += f"\nReason: {reason}"
        
        # Send to moderators
        moderator_service = AdminNotificationService()
        notifications = moderator_service.notify_moderators(
            title=title,
            message=message,
            category='content_report',
            data={
                'content_type': content_type,
                'content_id': content_id,
                'reporter_id': reporter_id,
                'reason': reason
            }
        )
        
        return notifications
    
    def notify_spam_detected(self, content_type, content_id, confidence_score, user_id=None):
        """Notify about detected spam"""
        
        title = f"Spam Detected: {content_type.title()}"
        message = f"{content_type.title()} #{content_id} detected as spam"
        message += f"\nConfidence: {confidence_score:.2f}"
        
        if user_id:
            user = User.query.get(user_id)
            username = user.username if user else f"User {user_id}"
            message += f"\nUser: {username}"
        
        # Send to moderators
        moderator_service = AdminNotificationService()
        notifications = moderator_service.notify_moderators(
            title=title,
            message=message,
            category='spam_detection',
            priority='high',
            severity='warning',
            data={
                'content_type': content_type,
                'content_id': content_id,
                'confidence_score': confidence_score,
                'user_id': user_id
            }
        )
        
        return notifications
    
    def notify_moderation_action(self, action, content_type, content_id, moderator_id, reason=None):
        """Notify about moderation action taken"""
        
        moderator = User.query.get(moderator_id)
        moderator_name = moderator.username if moderator else f"Moderator {moderator_id}"
        
        title = f"Moderation Action: {action.title()}"
        message = f"{moderator_name} {action.lower()} {content_type} #{content_id}"
        
        if reason:
            message += f"\nReason: {reason}"
        
        # Send to all moderators
        moderator_service = AdminNotificationService()
        notifications = moderator_service.notify_moderators(
            title=title,
            message=message,
            category='moderation_action',
            data={
                'action': action,
                'content_type': content_type,
                'content_id': content_id,
                'moderator_id': moderator_id,
                'reason': reason
            }
        )
        
        return notifications
    
    def notify_user_suspended(self, user_id, reason, duration, moderator_id):
        """Notify about user suspension"""
        
        user = User.query.get(user_id)
        username = user.username if user else f"User {user_id}"
        
        moderator = User.query.get(moderator_id)
        moderator_name = moderator.username if moderator else f"Moderator {moderator_id}"
        
        title = "User Suspended"
        message = f"{moderator_name} suspended {username}"
        message += f"\nReason: {reason}"
        message += f"\nDuration: {duration}"
        
        # Send to all moderators
        moderator_service = AdminNotificationService()
        notifications = moderator_service.notify_moderators(
            title=title,
            message=message,
            category='user_suspended',
            priority='high',
            severity='warning',
            data={
                'user_id': user_id,
                'username': username,
                'reason': reason,
                'duration': duration,
                'moderator_id': moderator_id
            }
        )
        
        return notifications


class UserActivityNotificationService(NotificationService):
    """Service for user activity threshold notifications"""
    
    def notify_user_activity_threshold(self, user_id, activity_type, threshold, current_value):
        """Notify when user activity exceeds threshold"""
        
        user = User.query.get(user_id)
        username = user.username if user else f"User {user_id}"
        
        title = f"User Activity Threshold: {activity_type}"
        message = f"User {username} exceeded {activity_type} threshold"
        message += f"\nThreshold: {threshold}"
        message += f"\nCurrent: {current_value}"
        
        # Send to admins
        admin_service = AdminNotificationService()
        notifications = admin_service.notify_admins(
            title=title,
            message=message,
            category='user_activity',
            priority='medium',
            severity='info',
            data={
                'user_id': user_id,
                'username': username,
                'activity_type': activity_type,
                'threshold': threshold,
                'current_value': current_value
            }
        )
        
        return notifications
    
    def notify_user_inactivity(self, user_id, days_inactive):
        """Notify about user inactivity"""
        
        user = User.query.get(user_id)
        username = user.username if user else f"User {user_id}"
        
        title = "User Inactivity Alert"
        message = f"User {username} inactive for {days_inactive} days"
        
        # Send to admins
        admin_service = AdminNotificationService()
        notifications = admin_service.notify_admins(
            title=title,
            message=message,
            category='user_inactivity',
            priority='low',
            severity='info',
            data={
                'user_id': user_id,
                'username': username,
                'days_inactive': days_inactive
            }
        )
        
        return notifications
    
    def notify_new_user_surge(self, user_count, time_period_hours):
        """Notify about surge in new user registrations"""
        
        title = "New User Surge Alert"
        message = f"{user_count} new users registered in the last {time_period_hours} hours"
        
        # Send to admins
        admin_service = AdminNotificationService()
        notifications = admin_service.notify_admins(
            title=title,
            message=message,
            category='user_registration',
            priority='medium',
            severity='info',
            data={
                'user_count': user_count,
                'time_period_hours': time_period_hours
            }
        )
        
        return notifications
    
    def notify_user_engagement_drop(self, user_id, engagement_score, drop_percentage):
        """Notify about significant drop in user engagement"""
        
        user = User.query.get(user_id)
        username = user.username if user else f"User {user_id}"
        
        title = "User Engagement Drop"
        message = f"User {username} engagement dropped by {drop_percentage}%"
        message += f"\nCurrent score: {engagement_score}"
        
        # Send to admins
        admin_service = AdminNotificationService()
        notifications = admin_service.notify_admins(
            title=title,
            message=message,
            category='user_engagement',
            priority='medium',
            severity='warning',
            data={
                'user_id': user_id,
                'username': username,
                'engagement_score': engagement_score,
                'drop_percentage': drop_percentage
            }
        )
        
        return notifications


class NotificationPreferenceService:
    """Service for managing notification preferences"""
    
    def get_user_preferences(self, user_id):
        """Get all notification preferences for a user"""
        
        preferences = NotificationPreference.query.filter_by(user_id=user_id).all()
        return preferences
    
    def get_user_preference(self, user_id, notification_type, category):
        """Get specific preference for user"""
        
        preference = NotificationPreference.query.filter_by(
            user_id=user_id,
            notification_type=notification_type,
            category=category
        ).first()
        
        return preference
    
    def set_user_preference(self, user_id, notification_type, category, **kwargs):
        """Set notification preference for user"""
        
        preference = self.get_user_preference(user_id, notification_type, category)
        
        if not preference:
            preference = NotificationPreference(
                user_id=user_id,
                notification_type=notification_type,
                category=category
            )
            db.session.add(preference)
        
        # Update preference fields
        for key, value in kwargs.items():
            if hasattr(preference, key):
                setattr(preference, key, value)
        
        db.session.commit()
        return preference
    
    def create_default_preferences(self, user_id):
        """Create default preferences for a new user"""
        
        default_preferences = [
            # Security notifications
            {'notification_type': 'security', 'category': 'login', 'enabled': True, 'priority': 'low'},
            {'notification_type': 'security', 'category': 'failed_login', 'enabled': True, 'priority': 'low'},
            {'notification_type': 'security', 'category': 'suspicious_activity', 'enabled': True, 'priority': 'medium'},
            
            # System notifications
            {'notification_type': 'system', 'category': 'system_health', 'enabled': True, 'priority': 'medium'},
            {'notification_type': 'system', 'category': 'maintenance', 'enabled': True, 'priority': 'medium'},
            
            # Moderation notifications (for moderators)
            {'notification_type': 'moderation', 'category': 'content_report', 'enabled': True, 'priority': 'medium'},
            {'notification_type': 'moderation', 'category': 'spam_detection', 'enabled': True, 'priority': 'medium'},
            
            # User activity notifications
            {'notification_type': 'user_activity', 'category': 'user_registration', 'enabled': True, 'priority': 'low'},
            {'notification_type': 'user_activity', 'category': 'user_inactivity', 'enabled': False, 'priority': 'low'},
        ]
        
        for pref_data in default_preferences:
            self.set_user_preference(user_id, **pref_data)
        
        return len(default_preferences)


class NotificationDeliveryService:
    """Service for managing notification delivery"""
    
    def __init__(self):
        self.max_retries = 3
    
    def create_delivery(self, notification_id, delivery_type, recipient=None, delivery_address=None):
        """Create delivery record"""
        
        delivery = NotificationDelivery(
            notification_id=notification_id,
            delivery_type=delivery_type,
            recipient=recipient,
            delivery_address=delivery_address
        )
        
        db.session.add(delivery)
        db.session.commit()
        
        return delivery
    
    def mark_delivered(self, delivery_id):
        """Mark delivery as delivered"""
        
        delivery = NotificationDelivery.query.get(delivery_id)
        if delivery:
            delivery.mark_as_delivered()
            db.session.commit()
        
        return delivery
    
    def mark_failed(self, delivery_id, error_message=None, error_code=None):
        """Mark delivery as failed"""
        
        delivery = NotificationDelivery.query.get(delivery_id)
        if delivery:
            delivery.mark_as_failed(error_message, error_code)
            db.session.commit()
        
        return delivery
    
    def retry_failed_deliveries(self):
        """Retry failed deliveries"""
        
        failed_deliveries = NotificationDelivery.query.filter_by(
            delivery_status='failed'
        ).filter(
            NotificationDelivery.retry_count < NotificationDelivery.max_retries
        ).all()
        
        retried_count = 0
        
        for delivery in failed_deliveries:
            # Reset for retry
            delivery.delivery_status = 'pending'
            delivery.retry_count += 1
            delivery.sent_at = None
            delivery.failed_at = None
            delivery.error_message = None
            delivery.error_code = None
            
            retried_count += 1
        
        db.session.commit()
        return retried_count
    
    def get_delivery_stats(self, notification_id):
        """Get delivery statistics for a notification"""
        
        deliveries = NotificationDelivery.query.filter_by(notification_id=notification_id).all()
        
        stats = {
            'total': len(deliveries),
            'pending': 0,
            'sent': 0,
            'delivered': 0,
            'failed': 0,
            'opened': 0,
            'clicked': 0
        }
        
        for delivery in deliveries:
            stats[delivery.delivery_status] += 1
            if delivery.opened_at:
                stats['opened'] += 1
            if delivery.clicked_at:
                stats['clicked'] += 1
        
        return stats


class NotificationTemplateService:
    """Service for managing notification templates"""
    
    def __init__(self):
        pass
    
    def create_template(self, name, display_name, description, subject_template, 
                       message_template, notification_type, category, 
                       default_priority='medium', default_severity='info',
                       default_expires_hours=168, is_active=True, 
                       variables=None, metadata=None):
        """Create a new notification template"""
        
        template = NotificationTemplate(
            name=name,
            display_name=display_name,
            description=description,
            subject_template=subject_template,
            message_template=message_template,
            notification_type=notification_type,
            category=category,
            default_priority=default_priority,
            default_severity=default_severity,
            default_expires_hours=default_expires_hours,
            is_active=is_active,
            variables=variables or [],
            metadata=metadata or {}
        )
        
        db.session.add(template)
        db.session.commit()
        return template
    
    def get_template(self, template_id):
        """Get a template by ID"""
        return NotificationTemplate.query.get(template_id)
    
    def get_template_by_name(self, name):
        """Get a template by name"""
        return NotificationTemplate.query.filter_by(name=name).first()
    
    def get_templates(self, notification_type=None, category=None, is_active=True):
        """Get templates with optional filters"""
        query = NotificationTemplate.query
        
        if notification_type:
            query = query.filter_by(notification_type=notification_type)
        
        if category:
            query = query.filter_by(category=category)
        
        if is_active is not None:
            query = query.filter_by(is_active=is_active)
        
        return query.order_by(NotificationTemplate.display_name).all()
    
    def update_template(self, template_id, **kwargs):
        """Update a template"""
        template = self.get_template(template_id)
        if not template:
            return None
        
        for key, value in kwargs.items():
            if hasattr(template, key):
                setattr(template, key, value)
        
        template.updated_at = datetime.utcnow()
        db.session.commit()
        return template
    
    def delete_template(self, template_id):
        """Delete a template"""
        template = self.get_template(template_id)
        if not template:
            return False
        
        db.session.delete(template)
        db.session.commit()
        return True
    
    def render_template(self, template_id, context=None):
        """Render a template with context variables"""
        template = self.get_template(template_id)
        if not template:
            return None, None
        
        context = context or {}
        
        try:
            # Render subject template
            subject = template.subject_template
            for var in template.variables:
                placeholder = f"{{{{{var}}}}}"
                value = context.get(var, f"[{var}]")
                subject = subject.replace(placeholder, str(value))
            
            # Render message template
            message = template.message_template
            for var in template.variables:
                placeholder = f"{{{{{var}}}}}"
                value = context.get(var, f"[{var}]")
                message = message.replace(placeholder, str(value))
            
            return subject, message
        
        except Exception as e:
            current_app.logger.error(f"Error rendering template {template_id}: {str(e)}")
            return template.subject_template, template.message_template
    
    def get_template_variables(self, template_id):
        """Get variables used in a template"""
        template = self.get_template(template_id)
        if not template:
            return []
        
        return template.variables or []
    
    def validate_template(self, subject_template, message_template, variables=None):
        """Validate template syntax and variables"""
        errors = []
        variables = variables or []
        
        # Check for unmatched variables
        import re
        
        # Find all variables in templates
        subject_vars = re.findall(r'\{\{(\w+)\}\}', subject_template)
        message_vars = re.findall(r'\{\{(\w+)\}\}', message_template)
        
        all_vars = set(subject_vars + message_vars)
        
        # Check if all variables are defined
        for var in all_vars:
            if var not in variables:
                errors.append(f"Undefined variable: {var}")
        
        # Check if defined variables are used
        for var in variables:
            if var not in all_vars:
                errors.append(f"Unused variable: {var}")
        
        return errors
    
    def get_template_usage_stats(self, template_id):
        """Get usage statistics for a template"""
        template = self.get_template(template_id)
        if not template:
            return None
        
        # Count notifications created using this template
        notifications_count = AdminNotification.query.filter_by(
            template_id=template_id
        ).count()
        
        return {
            'template_id': template_id,
            'template_name': template.name,
            'notifications_created': notifications_count,
            'last_used': None  # Could be enhanced to track last usage
        }
    
    def duplicate_template(self, template_id, new_name, new_display_name=None):
        """Duplicate an existing template"""
        template = self.get_template(template_id)
        if not template:
            return None
        
        new_display_name = new_display_name or f"{template.display_name} (Copy)"
        
        new_template = NotificationTemplate(
            name=new_name,
            display_name=new_display_name,
            description=template.description,
            subject_template=template.subject_template,
            message_template=template.message_template,
            notification_type=template.notification_type,
            category=template.category,
            default_priority=template.default_priority,
            default_severity=template.default_severity,
            default_expires_hours=template.default_expires_hours,
            is_active=False,  # Start as inactive
            variables=template.variables.copy(),
            metadata=template.metadata.copy()
        )
        
        db.session.add(new_template)
        db.session.commit()
        return new_template
    
    def get_template_categories(self):
        """Get all unique template categories"""
        categories = db.session.query(
            NotificationTemplate.category,
            func.count(NotificationTemplate.id).label('count')
        ).group_by(NotificationTemplate.category).all()
        
        return [{'category': cat, 'count': count} for cat, count in categories]
    
    def get_template_types(self):
        """Get all unique template types"""
        types = db.session.query(
            NotificationTemplate.notification_type,
            func.count(NotificationTemplate.id).label('count')
        ).group_by(NotificationTemplate.notification_type).all()
        
        return [{'type': t, 'count': count} for t, count in types]
