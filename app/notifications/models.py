"""
Real-time Admin Notifications Models

This module contains SQLAlchemy models for the notification system,
including admin notifications, templates, preferences, and delivery tracking.
"""

from datetime import datetime, timezone
from flask import current_app
from app import db
from app.models import User
import json


class AdminNotification(db.Model):
    """Model for admin notifications"""
    
    __tablename__ = 'admin_notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Notification content
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(50), nullable=False)  # security, system, moderation, user_activity
    
    # Notification metadata
    category = db.Column(db.String(50), nullable=False)
    priority = db.Column(db.String(20), nullable=False, default='medium')  # low, medium, high, critical
    severity = db.Column(db.String(20), nullable=False, default='info')  # info, warning, error, critical
    
    # Target information
    target_type = db.Column(db.String(50))  # user, post, comment, system
    target_id = db.Column(db.Integer)
    target_url = db.Column(db.String(500))
    
    # Source information
    source = db.Column(db.String(100))  # system, user, moderator, admin
    source_id = db.Column(db.Integer)
    
    # Notification data
    data = db.Column(db.JSON)  # Additional notification data
    notification_metadata = db.Column(db.JSON)  # Metadata for processing
    
    # Status and timing
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    is_acknowledged = db.Column(db.Boolean, default=False, nullable=False)
    requires_action = db.Column(db.Boolean, default=False, nullable=False)
    action_url = db.Column(db.String(500))
    
    # Delivery tracking
    delivered_at = db.Column(db.DateTime)
    read_at = db.Column(db.DateTime)
    acknowledged_at = db.Column(db.DateTime)
    expires_at = db.Column(db.DateTime)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('admin_notifications', lazy='dynamic', cascade='all, delete-orphan'))
    
    # Indexes
    __table_args__ = (
        db.Index('idx_notification_user', 'user_id'),
        db.Index('idx_notification_type', 'notification_type'),
        db.Index('idx_notification_priority', 'priority'),
        db.Index('idx_notification_created', 'created_at'),
        db.Index('idx_notification_unread', 'user_id', 'is_read'),
        db.Index('idx_notification_target', 'target_type', 'target_id'),
    )
    
    def to_dict(self):
        """Convert notification to dictionary"""
        return {
            'id': self.id,
            'title': self.title,
            'message': self.message,
            'notification_type': self.notification_type,
            'category': self.category,
            'priority': self.priority,
            'severity': self.severity,
            'target_type': self.target_type,
            'target_id': self.target_id,
            'target_url': self.target_url,
            'source': self.source,
            'source_id': self.source_id,
            'data': self.data or {},
            'metadata': self.notification_metadata or {},
            'is_read': self.is_read,
            'is_acknowledged': self.is_acknowledged,
            'requires_action': self.requires_action,
            'action_url': self.action_url,
            'delivered_at': self.delivered_at.isoformat() if self.delivered_at else None,
            'read_at': self.read_at.isoformat() if self.read_at else None,
            'acknowledged_at': self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'user_id': self.user_id
        }
    
    def __repr__(self):
        return f'<AdminNotification {self.id}: {self.title}>'


class NotificationTemplate(db.Model):
    """Model for notification templates"""
    
    __tablename__ = 'notification_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Template information
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    
    # Template content
    title_template = db.Column(db.String(200), nullable=False)
    message_template = db.Column(db.Text, nullable=False)
    
    # Template metadata
    notification_type = db.Column(db.String(50), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    default_priority = db.Column(db.String(20), nullable=False, default='medium')
    default_severity = db.Column(db.String(20), nullable=False, default='info')
    
    # Template configuration
    variables = db.Column(db.JSON)  # Template variables definition
    conditions = db.Column(db.JSON)  # Conditions for template usage
    auto_send = db.Column(db.Boolean, default=False, nullable=False)
    
    # Target configuration
    target_roles = db.Column(db.JSON)  # Roles that should receive this notification
    target_users = db.Column(db.JSON)  # Specific users that should receive this notification
    
    # Action configuration
    requires_action = db.Column(db.Boolean, default=False, nullable=False)
    action_template = db.Column(db.String(500))  # Template for action URL
    
    # Expiration
    default_expires_hours = db.Column(db.Integer, default=168)  # 7 days default
    
    # Status
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    creator = db.relationship('User', backref='created_templates')
    
    # Indexes
    __table_args__ = (
        db.Index('idx_template_type', 'notification_type'),
        db.Index('idx_template_category', 'category'),
        db.Index('idx_template_active', 'is_active'),
    )
    
    def render_title(self, variables=None):
        """Render title template with variables"""
        from jinja2 import Template
        template = Template(self.title_template)
        return template.render(variables or {})
    
    def render_message(self, variables=None):
        """Render message template with variables"""
        from jinja2 import Template
        template = Template(self.message_template)
        return template.render(variables or {})
    
    def to_dict(self):
        """Convert template to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'title_template': self.title_template,
            'message_template': self.message_template,
            'notification_type': self.notification_type,
            'category': self.category,
            'default_priority': self.default_priority,
            'default_severity': self.default_severity,
            'variables': self.variables or {},
            'conditions': self.conditions or {},
            'auto_send': self.auto_send,
            'target_roles': self.target_roles or [],
            'target_users': self.target_users or [],
            'requires_action': self.requires_action,
            'action_template': self.action_template,
            'default_expires_hours': self.default_expires_hours,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'created_by': self.created_by
        }
    
    def __repr__(self):
        return f'<NotificationTemplate {self.name}>'


class NotificationPreference(db.Model):
    """Model for user notification preferences"""
    
    __tablename__ = 'notification_preferences'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # User reference
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('user_notification_preferences', lazy='dynamic', cascade='all, delete-orphan'))
    
    # Preference settings
    notification_type = db.Column(db.String(50), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    
    # Delivery preferences
    enabled = db.Column(db.Boolean, default=True, nullable=False)
    in_app_enabled = db.Column(db.Boolean, default=True, nullable=False)
    email_enabled = db.Column(db.Boolean, default=False, nullable=False)
    sms_enabled = db.Column(db.Boolean, default=False, nullable=False)
    
    # Priority preferences
    min_priority = db.Column(db.String(20), default='low')  # minimum priority to receive
    min_severity = db.Column(db.String(20), default='info')  # minimum severity to receive
    
    # Frequency preferences
    frequency = db.Column(db.String(20), default='immediate')  # immediate, hourly, daily, weekly
    batch_size = db.Column(db.Integer, default=10)  # Max notifications per batch
    
    # Time preferences
    quiet_hours_enabled = db.Column(db.Boolean, default=False, nullable=False)
    quiet_hours_start = db.Column(db.Time)  # Start of quiet hours
    quiet_hours_end = db.Column(db.Time)  # End of quiet hours
    
    # Exclusions
    excluded_sources = db.Column(db.JSON)  # Sources to exclude
    excluded_categories = db.Column(db.JSON)  # Categories to exclude
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Indexes
    __table_args__ = (
        db.Index('idx_preference_user', 'user_id'),
        db.Index('idx_preference_type', 'notification_type'),
        db.Index('idx_preference_category', 'category'),
        db.UniqueConstraint('user_id', 'notification_type', 'category', name='uq_user_notification_type'),
    )
    
    def should_receive_notification(self, notification):
        """Check if user should receive this notification"""
        # Check if enabled
        if not self.enabled:
            return False
        
        # Check priority
        priority_levels = {'low': 1, 'medium': 2, 'high': 3, 'critical': 4}
        min_priority_level = priority_levels.get(self.min_priority, 1)
        notification_priority_level = priority_levels.get(notification.priority, 2)
        
        if notification_priority_level < min_priority_level:
            return False
        
        # Check severity
        severity_levels = {'info': 1, 'warning': 2, 'error': 3, 'critical': 4}
        min_severity_level = severity_levels.get(self.min_severity, 1)
        notification_severity_level = severity_levels.get(notification.severity, 1)
        
        if notification_severity_level < min_severity_level:
            return False
        
        # Check quiet hours
        if self.quiet_hours_enabled and self.quiet_hours_start and self.quiet_hours_end:
            current_time = datetime.utcnow().time()
            if self.quiet_hours_start <= current_time <= self.quiet_hours_end:
                return False
        
        # Check exclusions
        if self.excluded_sources and notification.source in self.excluded_sources:
            return False
        
        if self.excluded_categories and notification.category in self.excluded_categories:
            return False
        
        return True
    
    def to_dict(self):
        """Convert preference to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'notification_type': self.notification_type,
            'category': self.category,
            'enabled': self.enabled,
            'in_app_enabled': self.in_app_enabled,
            'email_enabled': self.email_enabled,
            'sms_enabled': self.sms_enabled,
            'min_priority': self.min_priority,
            'min_severity': self.min_severity,
            'frequency': self.frequency,
            'batch_size': self.batch_size,
            'quiet_hours_enabled': self.quiet_hours_enabled,
            'quiet_hours_start': self.quiet_hours_start.isoformat() if self.quiet_hours_start else None,
            'quiet_hours_end': self.quiet_hours_end.isoformat() if self.quiet_hours_end else None,
            'excluded_sources': self.excluded_sources or [],
            'excluded_categories': self.excluded_categories or [],
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def __repr__(self):
        return f'<NotificationPreference {self.user_id}:{self.notification_type}>'


class NotificationDelivery(db.Model):
    """Model for tracking notification delivery status"""
    
    __tablename__ = 'notification_deliveries'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Notification reference
    notification_id = db.Column(db.Integer, db.ForeignKey('admin_notifications.id'), nullable=False)
    notification = db.relationship('AdminNotification', backref=db.backref('deliveries', lazy='dynamic'))
    
    # Delivery information
    delivery_type = db.Column(db.String(20), nullable=False)  # in_app, email, sms, push
    delivery_status = db.Column(db.String(20), nullable=False, default='pending')  # pending, sent, delivered, failed
    
    # Delivery details
    recipient = db.Column(db.String(255))  # Email address, phone number, etc.
    delivery_address = db.Column(db.String(500))  # Full delivery address
    
    # Timing
    sent_at = db.Column(db.DateTime)
    delivered_at = db.Column(db.DateTime)
    failed_at = db.Column(db.DateTime)
    retry_count = db.Column(db.Integer, default=0, nullable=False)
    max_retries = db.Column(db.Integer, default=3, nullable=False)
    
    # Error information
    error_message = db.Column(db.Text)
    error_code = db.Column(db.String(50))
    
    # Response tracking
    opened_at = db.Column(db.DateTime)
    clicked_at = db.Column(db.DateTime)
    
    # Metadata
    delivery_data = db.Column(db.JSON)  # Additional delivery data
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Indexes
    __table_args__ = (
        db.Index('idx_delivery_notification', 'notification_id'),
        db.Index('idx_delivery_type', 'delivery_type'),
        db.Index('idx_delivery_status', 'delivery_status'),
        db.Index('idx_delivery_sent', 'sent_at'),
    )
    
    def mark_as_sent(self):
        """Mark delivery as sent"""
        self.delivery_status = 'sent'
        self.sent_at = datetime.utcnow()
    
    def mark_as_delivered(self):
        """Mark delivery as delivered"""
        self.delivery_status = 'delivered'
        self.delivered_at = datetime.utcnow()
    
    def mark_as_failed(self, error_message=None, error_code=None):
        """Mark delivery as failed"""
        self.delivery_status = 'failed'
        self.failed_at = datetime.utcnow()
        self.retry_count += 1
        self.error_message = error_message
        self.error_code = error_code
    
    def can_retry(self):
        """Check if delivery can be retried"""
        return self.delivery_status == 'failed' and self.retry_count < self.max_retries
    
    def to_dict(self):
        """Convert delivery to dictionary"""
        return {
            'id': self.id,
            'notification_id': self.notification_id,
            'delivery_type': self.delivery_type,
            'delivery_status': self.delivery_status,
            'recipient': self.recipient,
            'delivery_address': self.delivery_address,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'delivered_at': self.delivered_at.isoformat() if self.delivered_at else None,
            'failed_at': self.failed_at.isoformat() if self.failed_at else None,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'error_message': self.error_message,
            'error_code': self.error_code,
            'opened_at': self.opened_at.isoformat() if self.opened_at else None,
            'clicked_at': self.clicked_at.isoformat() if self.clicked_at else None,
            'delivery_data': self.delivery_data or {},
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def __repr__(self):
        return f'<NotificationDelivery {self.id}: {self.delivery_type}>'


class NotificationCategory(db.Model):
    """Model for notification categories"""
    
    __tablename__ = 'notification_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Category information
    name = db.Column(db.String(50), unique=True, nullable=False)
    display_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    
    # Category configuration
    icon = db.Column(db.String(50))  # Icon class for UI
    color = db.Column(db.String(20))  # Color for UI
    
    # Default settings
    default_priority = db.Column(db.String(20), default='medium')
    default_severity = db.Column(db.String(20), default='info')
    default_expires_hours = db.Column(db.Integer, default=168)  # 7 days default
    
    # Category behavior
    requires_action = db.Column(db.Boolean, default=False, nullable=False)
    auto_acknowledge = db.Column(db.Boolean, default=False, nullable=False)
    
    # Status
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Ordering
    sort_order = db.Column(db.Integer, default=0, nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Indexes
    __table_args__ = (
        db.Index('idx_category_active', 'is_active'),
        db.Index('idx_category_order', 'sort_order'),
    )
    
    def to_dict(self):
        """Convert category to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'display_name': self.display_name,
            'description': self.description,
            'icon': self.icon,
            'color': self.color,
            'default_priority': self.default_priority,
            'default_severity': self.default_severity,
            'default_expires_hours': self.default_expires_hours,
            'requires_action': self.requires_action,
            'auto_acknowledge': self.auto_acknowledge,
            'is_active': self.is_active,
            'sort_order': self.sort_order,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def __repr__(self):
        return f'<NotificationCategory {self.name}>'
