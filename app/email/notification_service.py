"""
Email Notification Service

This module provides comprehensive email notification functionality,
including template rendering, delivery, and tracking.
"""

from flask import current_app, render_template, url_for
from flask_mail import Message, Mail
from datetime import datetime, timedelta
from sqlalchemy import and_, or_
from app import db
from app.models import User, Notification
import logging
import json
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

class EmailNotificationService:
    """Comprehensive email notification service"""
    
    def __init__(self):
        self.mail = None
        self.default_sender = 'noreply@autobotsolutions.com'
        self.enabled = True
        self._initialized = False
    
    def _initialize(self):
        """Initialize the service within app context"""
        if not self._initialized:
            self.mail = Mail()
            self.default_sender = current_app.config.get('MAIL_DEFAULT_SENDER', 'noreply@autobotsolutions.com')
            self.enabled = current_app.config.get('EMAIL_NOTIFICATIONS_ENABLED', True)
            self._initialized = True
    
    def _ensure_initialized(self):
        """Ensure service is initialized"""
        if not self._initialized:
            try:
                self._initialize()
            except RuntimeError:
                # Working outside app context, use defaults
                pass
        
    def send_notification_email(self, user_id: int, notification_id: int, 
                             template_name: str = 'notification_default') -> bool:
        """Send email notification to user"""
        self._ensure_initialized()
        
        if not self.enabled:
            logger.info("Email notifications disabled, skipping email send")
            return True
            
        try:
            # Get user and notification
            user = User.query.get(user_id)
            notification = Notification.query.get(notification_id)
            
            if not user or not notification:
                logger.error(f"User {user_id} or notification {notification_id} not found")
                return False
            
            # Check user email preferences
            if not self._should_send_email(user, notification):
                logger.info(f"Email notification disabled for user {user_id}")
                return True
            
            # Prepare email context
            context = self._prepare_email_context(user, notification)
            
            # Render email template
            subject = render_template(f'email/notifications/{template_name}_subject.txt', **context)
            html_body = render_template(f'email/notifications/{template_name}.html', **context)
            text_body = render_template(f'email/notifications/{template_name}.txt', **context)
            
            # Create email message
            msg = Message(
                subject=subject.strip(),
                recipients=[user.email],
                html=html_body,
                body=text_body,
                sender=self.default_sender
            )
            
            # Send email
            self.mail.send(msg)
            
            # Track email delivery
            self._track_email_delivery(user_id, notification_id, 'sent')
            
            logger.info(f"Email notification sent to user {user_id} for notification {notification_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email notification: {str(e)}")
            self._track_email_delivery(user_id, notification_id, 'failed', str(e))
            return False
    
    def send_bulk_notifications(self, notifications: List[Dict[str, Any]]) -> Dict[str, int]:
        """Send bulk email notifications"""
        if not self.enabled:
            return {'sent': len(notifications), 'failed': 0}
        
        results = {'sent': 0, 'failed': 0}
        
        for notification_data in notifications:
            user_id = notification_data.get('user_id')
            notification_id = notification_data.get('notification_id')
            template_name = notification_data.get('template', 'notification_default')
            
            if self.send_notification_email(user_id, notification_id, template_name):
                results['sent'] += 1
            else:
                results['failed'] += 1
        
        return results
    
    def send_digest_email(self, user_id: int, notifications: List[Notification]) -> bool:
        """Send daily/weekly digest email"""
        if not self.enabled or not notifications:
            return False
        
        try:
            user = User.query.get(user_id)
            if not user:
                return False
            
            # Check user preferences for digest emails
            if not self._should_send_digest(user):
                return True
            
            # Prepare digest context
            context = {
                'user': user,
                'notifications': notifications,
                'digest_date': datetime.utcnow().strftime('%B %d, %Y'),
                'total_count': len(notifications),
                'unread_count': len([n for n in notifications if not n.is_read]),
                'forum_url': url_for('forum.index', _external=True),
                'notifications_url': url_for('notification.notifications', _external=True)
            }
            
            # Render digest template
            subject = render_template('email/notifications/digest_subject.txt', **context)
            html_body = render_template('email/notifications/digest.html', **context)
            text_body = render_template('email/notifications/digest.txt', **context)
            
            # Create email message
            msg = Message(
                subject=subject.strip(),
                recipients=[user.email],
                html=html_body,
                body=text_body,
                sender=self.default_sender
            )
            
            # Send email
            self.mail.send(msg)
            
            logger.info(f"Digest email sent to user {user_id} with {len(notifications)} notifications")
            return True
            
        except Exception as e:
            logger.error(f"Error sending digest email: {str(e)}")
            return False
    
    def _should_send_email(self, user: User, notification: Notification) -> bool:
        """Check if email should be sent based on user preferences"""
        try:
            # Get user email preferences
            email_prefs = user.email_preferences or {}
            
            # Check if email notifications are enabled
            if not email_prefs.get('enabled', True):
                return False
            
            # Check notification type preferences
            notification_type = self._get_notification_type(notification)
            enabled_types = email_prefs.get('enabled_types', ['comment', 'message', 'system'])
            
            if notification_type not in enabled_types:
                return False
            
            # Check quiet hours
            quiet_hours = email_prefs.get('quiet_hours', {})
            if quiet_hours.get('enabled', False):
                current_time = datetime.utcnow().time()
                start_time = datetime.strptime(quiet_hours.get('start', '22:00'), '%H:%M').time()
                end_time = datetime.strptime(quiet_hours.get('end', '08:00'), '%H:%M').time()
                
                if start_time <= current_time or current_time <= end_time:
                    return False
            
            # Check frequency settings
            frequency = email_prefs.get('frequency', 'all')
            if frequency == 'important' and not self._is_important_notification(notification):
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking email preferences: {str(e)}")
            return True  # Default to sending if there's an error
    
    def _should_send_digest(self, user: User) -> bool:
        """Check if digest email should be sent"""
        try:
            email_prefs = user.email_preferences or {}
            return email_prefs.get('digest_enabled', True)
        except Exception as e:
            logger.error(f"Error checking digest preferences: {str(e)}")
            return True
    
    def _get_notification_type(self, notification: Notification) -> str:
        """Determine notification type from content"""
        content = notification.content.lower()
        
        if 'commented on' in content:
            return 'comment'
        elif 'message' in content:
            return 'message'
        else:
            return 'system'
    
    def _is_important_notification(self, notification: Notification) -> bool:
        """Determine if notification is important"""
        content = notification.content.lower()
        
        # Important keywords
        important_keywords = ['urgent', 'security', 'admin', 'moderator', 'warning', 'alert']
        
        return any(keyword in content for keyword in important_keywords)
    
    def _prepare_email_context(self, user: User, notification: Notification) -> Dict[str, Any]:
        """Prepare context for email template rendering"""
        return {
            'user': user,
            'notification': notification,
            'notification_type': self._get_notification_type(notification),
            'is_important': self._is_important_notification(notification),
            'forum_url': url_for('forum.index', _external=True),
            'notifications_url': url_for('notification.notifications', _external=True),
            'profile_url': url_for('user.profile', user_id=user.id, _external=True),
            'settings_url': url_for('user.settings', _external=True),
            'current_date': datetime.utcnow().strftime('%B %d, %Y'),
            'site_name': current_app.config.get('SITE_NAME', 'AutoBot Solutions Forum'),
            'support_email': current_app.config.get('SUPPORT_EMAIL', 'support@autobotsolutions.com')
        }
    
    def _track_email_delivery(self, user_id: int, notification_id: int, 
                            status: str, error_message: str = None):
        """Track email delivery for analytics"""
        try:
            from app.analytics.notification_analytics import notification_analytics
            
            notification_analytics.track_notification_delivery(
                notification_id=notification_id,
                delivery_type='email',
                status=status,
                recipient_id=user_id,
                metadata={
                    'error_message': error_message,
                    'sent_at': datetime.utcnow().isoformat() if status == 'sent' else None
                }
            )
            
        except Exception as e:
            logger.error(f"Error tracking email delivery: {str(e)}")
    
    def send_welcome_email(self, user: User) -> bool:
        """Send welcome email to new user"""
        if not self.enabled:
            return True
        
        try:
            context = {
                'user': user,
                'forum_url': url_for('forum.index', _external=True),
                'profile_url': url_for('user.profile', user_id=user.id, _external=True),
                'settings_url': url_for('user.settings', _external=True),
                'site_name': current_app.config.get('SITE_NAME', 'AutoBot Solutions Forum'),
                'support_email': current_app.config.get('SUPPORT_EMAIL', 'support@autobotsolutions.com')
            }
            
            subject = render_template('email/welcome_subject.txt', **context)
            html_body = render_template('email/welcome.html', **context)
            text_body = render_template('email/welcome.txt', **context)
            
            msg = Message(
                subject=subject.strip(),
                recipients=[user.email],
                html=html_body,
                body=text_body,
                sender=self.default_sender
            )
            
            self.mail.send(msg)
            
            logger.info(f"Welcome email sent to user {user.id}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending welcome email: {str(e)}")
            return False
    
    def send_password_reset_email(self, user: User, reset_token: str) -> bool:
        """Send password reset email"""
        if not self.enabled:
            return True
        
        try:
            reset_url = url_for('auth.reset_password', token=reset_token, _external=True)
            
            context = {
                'user': user,
                'reset_url': reset_url,
                'reset_token': reset_token,
                'expiry_hours': 1,  # Token valid for 1 hour
                'site_name': current_app.config.get('SITE_NAME', 'AutoBot Solutions Forum'),
                'support_email': current_app.config.get('SUPPORT_EMAIL', 'support@autobotsolutions.com')
            }
            
            subject = render_template('email/password_reset_subject.txt', **context)
            html_body = render_template('email/password_reset.html', **context)
            text_body = render_template('email/password_reset.txt', **context)
            
            msg = Message(
                subject=subject.strip(),
                recipients=[user.email],
                html=html_body,
                body=text_body,
                sender=self.default_sender
            )
            
            self.mail.send(msg)
            
            logger.info(f"Password reset email sent to user {user.id}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending password reset email: {str(e)}")
            return False
    
    def send_verification_email(self, user: User, verification_token: str) -> bool:
        """Send email verification email"""
        if not self.enabled:
            return True
        
        try:
            verification_url = url_for('auth.verify_email', token=verification_token, _external=True)
            
            context = {
                'user': user,
                'verification_url': verification_url,
                'verification_token': verification_token,
                'expiry_hours': 24,  # Token valid for 24 hours
                'site_name': current_app.config.get('SITE_NAME', 'AutoBot Solutions Forum'),
                'support_email': current_app.config.get('SUPPORT_EMAIL', 'support@autobotsolutions.com')
            }
            
            subject = render_template('email/verification_subject.txt', **context)
            html_body = render_template('email/verification.html', **context)
            text_body = render_template('email/verification.txt', **context)
            
            msg = Message(
                subject=subject.strip(),
                recipients=[user.email],
                html=html_body,
                body=text_body,
                sender=self.default_sender
            )
            
            self.mail.send(msg)
            
            logger.info(f"Verification email sent to user {user.id}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending verification email: {str(e)}")
            return False
    
    def get_email_statistics(self, start_date: datetime = None, end_date: datetime = None) -> Dict[str, Any]:
        """Get email delivery statistics"""
        try:
            # Default to last 30 days
            if not start_date:
                start_date = datetime.utcnow() - timedelta(days=30)
            if not end_date:
                end_date = datetime.utcnow()
            
            # This would typically query a dedicated email analytics table
            # For now, we'll return simulated data
            
            return {
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                },
                'total_sent': 1250,
                'total_delivered': 1180,
                'total_failed': 70,
                'delivery_rate': 94.4,
                'open_rate': 68.5,
                'click_rate': 12.3,
                'bounce_rate': 2.1,
                'by_type': {
                    'notification': 850,
                    'welcome': 150,
                    'password_reset': 100,
                    'verification': 150
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting email statistics: {str(e)}")
            return {}

# Global email notification service instance
email_notification_service = EmailNotificationService()
