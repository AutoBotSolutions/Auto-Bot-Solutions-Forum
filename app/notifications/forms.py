"""
Real-time Admin Notifications Forms

This module contains Flask-WTF forms for the notification system,
including notification filters, template management, and user preferences.
"""

from datetime import datetime, time
from flask_wtf import FlaskForm
from wtforms import (
    StringField, TextAreaField, SelectField, IntegerField, FloatField,
    BooleanField, DateTimeField, TimeField, HiddenField, FieldList,
    FormField, SelectMultipleField
)
from wtforms.validators import (
    DataRequired, Optional, NumberRange, Length, Email, URL,
    ValidationError, Regexp
)
from flask import current_app
from .models import NotificationTemplate


class NotificationFilterForm(FlaskForm):
    """Form for filtering notifications"""
    
    # Basic filters
    notification_type = SelectField('Notification Type', choices=[
        ('', 'All Types'),
        ('admin', 'Admin'),
        ('security', 'Security'),
        ('system', 'System'),
        ('moderation', 'Moderation'),
        ('user_activity', 'User Activity')
    ], validators=[Optional()])
    
    category = SelectField('Category', choices=[
        ('', 'All Categories'),
        ('login', 'Login'),
        ('failed_login', 'Failed Login'),
        ('suspicious_activity', 'Suspicious Activity'),
        ('system_health', 'System Health'),
        ('maintenance', 'Maintenance'),
        ('content_report', 'Content Report'),
        ('spam_detection', 'Spam Detection'),
        ('user_registration', 'User Registration'),
        ('user_inactivity', 'User Inactivity')
    ], validators=[Optional()])
    
    priority = SelectField('Priority', choices=[
        ('', 'All Priorities'),
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical')
    ], validators=[Optional()])
    
    severity = SelectField('Severity', choices=[
        ('', 'All Severities'),
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical')
    ], validators=[Optional()])
    
    # Status filters
    is_read = SelectField('Read Status', choices=[
        ('', 'All'),
        ('true', 'Read'),
        ('false', 'Unread')
    ], validators=[Optional()])
    
    is_acknowledged = SelectField('Acknowledged', choices=[
        ('', 'All'),
        ('true', 'Acknowledged'),
        ('false', 'Not Acknowledged')
    ], validators=[Optional()])
    
    requires_action = SelectField('Requires Action', choices=[
        ('', 'All'),
        ('true', 'Requires Action'),
        ('false', 'No Action Required')
    ], validators=[Optional()])
    
    # Date filters
    created_since = DateTimeField('Created Since', validators=[Optional()])
    created_before = DateTimeField('Created Before', validators=[Optional()])
    
    # Target filters
    target_type = SelectField('Target Type', choices=[
        ('', 'All Types'),
        ('user', 'User'),
        ('post', 'Post'),
        ('comment', 'Comment'),
        ('system', 'System')
    ], validators=[Optional()])
    
    target_id = IntegerField('Target ID', validators=[Optional(), NumberRange(min=1)])
    
    # Search
    search = StringField('Search', validators=[Optional(), Length(max=200)])
    
    # Pagination
    limit = IntegerField('Limit', validators=[Optional(), NumberRange(min=1, max=100)], default=50)
    
    def validate_created_before(self, field):
        """Validate that created_before is after created_since"""
        if field.data and self.created_since.data:
            if field.data < self.created_since.data:
                raise ValidationError('End date must be after start date')


class NotificationTemplateForm(FlaskForm):
    """Form for creating and editing notification templates"""
    
    # Basic information
    name = StringField('Template Name', validators=[
        DataRequired(), Length(min=3, max=100),
        Regexp(r'^[a-zA-Z0-9_-]+$', message='Template name can only contain letters, numbers, underscores, and hyphens')
    ])
    
    description = TextAreaField('Description', validators=[
        Optional(), Length(max=500)
    ])
    
    # Template content
    title_template = StringField('Title Template', validators=[
        DataRequired(), Length(min=5, max=200)
    ])
    
    message_template = TextAreaField('Message Template', validators=[
        DataRequired(), Length(min=10, max=2000)
    ])
    
    # Template metadata
    notification_type = SelectField('Notification Type', choices=[
        ('admin', 'Admin'),
        ('security', 'Security'),
        ('system', 'System'),
        ('moderation', 'Moderation'),
        ('user_activity', 'User Activity')
    ], validators=[DataRequired()])
    
    category = SelectField('Category', choices=[
        ('login', 'Login'),
        ('failed_login', 'Failed Login'),
        ('suspicious_activity', 'Suspicious Activity'),
        ('system_health', 'System Health'),
        ('maintenance', 'Maintenance'),
        ('content_report', 'Content Report'),
        ('spam_detection', 'Spam Detection'),
        ('user_registration', 'User Registration'),
        ('user_inactivity', 'User Inactivity')
    ], validators=[DataRequired()])
    
    default_priority = SelectField('Default Priority', choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical')
    ], validators=[DataRequired()], default='medium')
    
    default_severity = SelectField('Default Severity', choices=[
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical')
    ], validators=[DataRequired()], default='info')
    
    # Template configuration
    auto_send = BooleanField('Auto Send', default=False)
    
    requires_action = BooleanField('Requires Action', default=False)
    action_template = StringField('Action URL Template', validators=[
        Optional(), Length(max=500), URL()
    ])
    
    default_expires_hours = IntegerField('Default Expiration (Hours)', validators=[
        DataRequired(), NumberRange(min=1, max=8760)  # Max 1 year
    ], default=168)
    
    # Target configuration
    target_roles = SelectMultipleField('Target Roles', choices=[
        ('admin', 'Admin'),
        ('moderator', 'Moderator'),
        ('user', 'User')
    ], validators=[Optional()])
    
    target_users = StringField('Target Users (comma-separated IDs)', validators=[
        Optional()
    ])
    
    def validate_name(self, field):
        """Validate template name uniqueness"""
        if field.data:
            existing = NotificationTemplate.query.filter_by(name=field.data).first()
            if existing:
                raise ValidationError('Template name already exists')
    
    def validate_target_users(self, field):
        """Validate target users format"""
        if field.data:
            try:
                user_ids = [int(uid.strip()) for uid in field.data.split(',') if uid.strip()]
                if len(user_ids) > 100:
                    raise ValidationError('Maximum 100 target users allowed')
            except ValueError:
                raise ValidationError('Invalid user ID format. Use comma-separated integers.')
    
    def validate_action_template(self, field):
        """Validate action template if requires_action is True"""
        if self.requires_action.data and not field.data:
            raise ValidationError('Action URL is required when action is required')


class NotificationPreferenceForm(FlaskForm):
    """Form for managing notification preferences"""
    
    # Basic settings
    notification_type = SelectField('Notification Type', choices=[
        ('admin', 'Admin'),
        ('security', 'Security'),
        ('system', 'System'),
        ('moderation', 'Moderation'),
        ('user_activity', 'User Activity')
    ], validators=[DataRequired()])
    
    category = SelectField('Category', choices=[
        ('login', 'Login'),
        ('failed_login', 'Failed Login'),
        ('suspicious_activity', 'Suspicious Activity'),
        ('system_health', 'System Health'),
        ('maintenance', 'Maintenance'),
        ('content_report', 'Content Report'),
        ('spam_detection', 'Spam Detection'),
        ('user_registration', 'User Registration'),
        ('user_inactivity', 'User Inactivity')
    ], validators=[DataRequired()])
    
    # Enable/disable
    enabled = BooleanField('Enable Notifications', default=True)
    
    # Delivery preferences
    in_app_enabled = BooleanField('In-App Notifications', default=True)
    email_enabled = BooleanField('Email Notifications', default=False)
    sms_enabled = BooleanField('SMS Notifications', default=False)
    
    # Priority preferences
    min_priority = SelectField('Minimum Priority', choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical')
    ], validators=[DataRequired()], default='low')
    
    min_severity = SelectField('Minimum Severity', choices=[
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical')
    ], validators=[DataRequired()], default='info')
    
    # Frequency preferences
    frequency = SelectField('Frequency', choices=[
        ('immediate', 'Immediate'),
        ('hourly', 'Hourly'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly')
    ], validators=[DataRequired()], default='immediate')
    
    batch_size = IntegerField('Batch Size', validators=[
        Optional(), NumberRange(min=1, max=100)
    ], default=10)
    
    # Quiet hours
    quiet_hours_enabled = BooleanField('Enable Quiet Hours', default=False)
    quiet_hours_start = TimeField('Quiet Hours Start', validators=[Optional()])
    quiet_hours_end = TimeField('Quiet Hours End', validators=[Optional()])
    
    # Exclusions
    excluded_sources = StringField('Excluded Sources', validators=[
        Optional()
    ])
    
    excluded_categories = StringField('Excluded Categories', validators=[
        Optional()
    ])
    
    def validate_quiet_hours_end(self, field):
        """Validate quiet hours end time"""
        if self.quiet_hours_enabled.data and self.quiet_hours_start.data and field.data:
            if field.data <= self.quiet_hours_start.data:
                raise ValidationError('End time must be after start time')
    
    def validate_excluded_sources(self, field):
        """Validate excluded sources format"""
        if field.data:
            sources = [s.strip() for s in field.data.split(',') if s.strip()]
            if len(sources) > 20:
                raise ValidationError('Maximum 20 excluded sources allowed')
    
    def validate_excluded_categories(self, field):
        """Validate excluded categories format"""
        if field.data:
            categories = [c.strip() for c in field.data.split(',') if c.strip()]
            if len(categories) > 20:
                raise ValidationError('Maximum 20 excluded categories allowed')


class NotificationSettingsForm(FlaskForm):
    """Form for global notification settings"""
    
    # Global settings
    enable_notifications = BooleanField('Enable Notifications', default=True)
    
    # Default preferences
    default_priority = SelectField('Default Priority', choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical')
    ], validators=[DataRequired()], default='medium')
    
    default_severity = SelectField('Default Severity', choices=[
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical')
    ], validators=[DataRequired()], default='info')
    
    default_expires_hours = IntegerField('Default Expiration (Hours)', validators=[
        DataRequired(), NumberRange(min=1, max=8760)
    ], default=168)
    
    # Delivery settings
    enable_email_notifications = BooleanField('Enable Email Notifications', default=True)
    enable_sms_notifications = BooleanField('Enable SMS Notifications', default=False)
    
    # Batch settings
    batch_size = IntegerField('Batch Size', validators=[
        DataRequired(), NumberRange(min=1, max=1000)
    ], default=100)
    
    batch_interval_minutes = IntegerField('Batch Interval (Minutes)', validators=[
        DataRequired(), NumberRange(min=1, max=1440)  # Max 24 hours
    ], default=5)
    
    # Cleanup settings
    cleanup_enabled = BooleanField('Enable Cleanup', default=True)
    cleanup_days = IntegerField('Cleanup After Days', validators=[
        DataRequired(), NumberRange(min=1, max=365)
    ], default=30)
    
    # Retry settings
    max_retries = IntegerField('Max Retries', validators=[
        DataRequired(), NumberRange(min=0, max=10)
    ], default=3)
    
    retry_delay_minutes = IntegerField('Retry Delay (Minutes)', validators=[
        DataRequired(), NumberRange(min=1, max=1440)
    ], default=15)
    
    # Rate limiting
    rate_limit_enabled = BooleanField('Enable Rate Limiting', default=True)
    max_notifications_per_hour = IntegerField('Max Notifications Per Hour', validators=[
        DataRequired(), NumberRange(min=1, max=10000)
    ], default=100)
    
    # WebSocket settings
    enable_websocket_notifications = BooleanField('Enable WebSocket Notifications', default=True)
    websocket_timeout_seconds = IntegerField('WebSocket Timeout (Seconds)', validators=[
        DataRequired(), NumberRange(min=1, max=300)
    ], default=30)


class CreateNotificationForm(FlaskForm):
    """Form for creating manual notifications"""
    
    # Recipients
    target_users = SelectMultipleField('Target Users', choices=[], validators=[Optional()])
    target_roles = SelectMultipleField('Target Roles', choices=[
        ('admin', 'Admin'),
        ('moderator', 'Moderator'),
        ('user', 'User')
    ], validators=[Optional()])
    
    send_to_all = BooleanField('Send to All Users', default=False)
    
    # Notification content
    title = StringField('Title', validators=[
        DataRequired(), Length(min=3, max=200)
    ])
    
    message = TextAreaField('Message', validators=[
        DataRequired(), Length(min=10, max=2000)
    ])
    
    # Notification metadata
    notification_type = SelectField('Notification Type', choices=[
        ('admin', 'Admin'),
        ('security', 'Security'),
        ('system', 'System'),
        ('moderation', 'Moderation'),
        ('user_activity', 'User Activity')
    ], validators=[DataRequired()])
    
    category = SelectField('Category', choices=[
        ('announcement', 'Announcement'),
        ('maintenance', 'Maintenance'),
        ('security', 'Security'),
        ('system', 'System'),
        ('moderation', 'Moderation')
    ], validators=[DataRequired()])
    
    priority = SelectField('Priority', choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical')
    ], validators=[DataRequired()], default='medium')
    
    severity = SelectField('Severity', choices=[
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical')
    ], validators=[DataRequired()], default='info')
    
    # Action settings
    requires_action = BooleanField('Requires Action', default=False)
    action_url = StringField('Action URL', validators=[
        Optional(), Length(max=500), URL()
    ])
    
    # Expiration
    expires_hours = IntegerField('Expires After (Hours)', validators=[
        Optional(), NumberRange(min=1, max=8760)
    ], default=168)
    
    def validate_target_users(self, field):
        """Validate target users selection"""
        if not field.data and not self.target_roles.data and not self.send_to_all.data:
            raise ValidationError('Please select target users, roles, or send to all users')
    
    def validate_action_url(self, field):
        """Validate action URL if requires_action is True"""
        if self.requires_action.data and not field.data:
            raise ValidationError('Action URL is required when action is required')


class NotificationCategoryForm(FlaskForm):
    """Form for managing notification categories"""
    
    # Basic information
    name = StringField('Category Name', validators=[
        DataRequired(), Length(min=3, max=50),
        Regexp(r'^[a-zA-Z0-9_-]+$', message='Category name can only contain letters, numbers, underscores, and hyphens')
    ])
    
    display_name = StringField('Display Name', validators=[
        DataRequired(), Length(min=3, max=100)
    ])
    
    description = TextAreaField('Description', validators=[
        Optional(), Length(max=500)
    ])
    
    # UI settings
    icon = StringField('Icon Class', validators=[
        Optional(), Length(max=50)
    ])
    
    color = StringField('Color', validators=[
        Optional(), Length(max=20),
        Regexp(r'^#[0-9A-Fa-f]{6}$', message='Color must be a valid hex color (e.g., #FF5733)')
    ])
    
    # Default settings
    default_priority = SelectField('Default Priority', choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical')
    ], validators=[DataRequired()], default='medium')
    
    default_severity = SelectField('Default Severity', choices=[
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical')
    ], validators=[DataRequired()], default='info')
    
    default_expires_hours = IntegerField('Default Expiration (Hours)', validators=[
        DataRequired(), NumberRange(min=1, max=8760)
    ], default=168)
    
    # Category behavior
    requires_action = BooleanField('Requires Action by Default', default=False)
    auto_acknowledge = BooleanField('Auto Acknowledge', default=False)
    
    # Status
    is_active = BooleanField('Active', default=True)
    
    # Ordering
    sort_order = IntegerField('Sort Order', validators=[
        Optional(), NumberRange(min=0, max=9999)
    ], default=0)
    
    def validate_name(self, field):
        """Validate category name uniqueness"""
        if field.data:
            existing = NotificationCategory.query.filter_by(name=field.data).first()
            if existing:
                raise ValidationError('Category name already exists')


class BulkNotificationForm(FlaskForm):
    """Form for bulk notification operations"""
    
    operation = SelectField('Operation', choices=[
        ('mark_read', 'Mark as Read'),
        ('mark_unread', 'Mark as Unread'),
        ('acknowledge', 'Acknowledge'),
        ('delete', 'Delete')
    ], validators=[DataRequired()])
    
    notification_ids = HiddenField('Notification IDs', validators=[DataRequired()])
    
    def validate_notification_ids(self, field):
        """Validate notification IDs format"""
        if field.data:
            try:
                ids = [int(nid) for nid in field.data.split(',') if nid.strip()]
                if len(ids) == 0:
                    raise ValidationError('No valid notification IDs provided')
                if len(ids) > 100:
                    raise ValidationError('Maximum 100 notifications can be processed at once')
            except ValueError:
                raise ValidationError('Invalid notification ID format')


class NotificationSearchForm(FlaskForm):
    """Form for advanced notification search"""
    
    # Search terms
    query = StringField('Search Query', validators=[
        Optional(), Length(min=2, max=200)
    ])
    
    # Filters
    notification_type = SelectField('Notification Type', choices=[
        ('', 'All Types'),
        ('admin', 'Admin'),
        ('security', 'Security'),
        ('system', 'System'),
        ('moderation', 'Moderation'),
        ('user_activity', 'User Activity')
    ], validators=[Optional()])
    
    category = SelectField('Category', choices=[
        ('', 'All Categories')
    ], validators=[Optional()])
    
    priority = SelectField('Priority', choices=[
        ('', 'All Priorities'),
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical')
    ], validators=[Optional()])
    
    severity = SelectField('Severity', choices=[
        ('', 'All Severities'),
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical')
    ], validators=[Optional()])
    
    # Date range
    date_range = SelectField('Date Range', choices=[
        ('', 'Custom Range'),
        ('today', 'Today'),
        ('yesterday', 'Yesterday'),
        ('last_7_days', 'Last 7 Days'),
        ('last_30_days', 'Last 30 Days'),
        ('last_90_days', 'Last 90 Days')
    ], validators=[Optional()])
    
    start_date = DateTimeField('Start Date', validators=[Optional()])
    end_date = DateTimeField('End Date', validators=[Optional()])
    
    # Sort options
    sort_by = SelectField('Sort By', choices=[
        ('created_at', 'Created Date'),
        ('priority', 'Priority'),
        ('severity', 'Severity'),
        ('title', 'Title')
    ], validators=[Optional()], default='created_at')
    
    sort_order = SelectField('Sort Order', choices=[
        ('desc', 'Newest First'),
        ('asc', 'Oldest First')
    ], validators=[Optional()], default='desc')
    
    # Results
    limit = IntegerField('Results per Page', validators=[
        Optional(), NumberRange(min=10, max=100)
    ], default=50)
    
    def validate_end_date(self, field):
        """Validate end date is after start date"""
        if field.data and self.start_date.data:
            if field.data < self.start_date.data:
                raise ValidationError('End date must be after start date')


class UserNotificationPreferencesForm(FlaskForm):
    """Form for user notification preferences UI"""
    
    # Push notification settings
    push_notifications_enabled = BooleanField('Enable Push Notifications', default=True)
    
    push_comment_notifications = BooleanField('Comment Notifications', default=True)
    push_message_notifications = BooleanField('Message Notifications', default=True)
    push_system_notifications = BooleanField('System Notifications', default=False)
    push_moderation_notifications = BooleanField('Moderation Notifications', default=False)
    
    # Email notification settings
    email_notifications_enabled = BooleanField('Enable Email Notifications', default=True)
    
    email_comment_notifications = BooleanField('Email Comment Notifications', default=True)
    email_message_notifications = BooleanField('Email Message Notifications', default=True)
    email_system_notifications = BooleanField('Email System Notifications', default=False)
    email_moderation_notifications = BooleanField('Email Moderation Notifications', default=False)
    
    email_digest_frequency = SelectField('Email Digest Frequency', choices=[
        ('immediate', 'Immediate'),
        ('hourly', 'Hourly Digest'),
        ('daily', 'Daily Digest'),
        ('weekly', 'Weekly Digest'),
        ('never', 'Never')
    ], validators=[DataRequired()], default='immediate')
    
    # Quiet hours settings
    quiet_hours_enabled = BooleanField('Enable Quiet Hours', default=False)
    quiet_hours_start = TimeField('Quiet Hours Start', validators=[Optional()], default=time(22, 0))
    quiet_hours_end = TimeField('Quiet Hours End', validators=[Optional()], default=time(8, 0))
    
    quiet_hours_push = BooleanField('Disable Push During Quiet Hours', default=True)
    quiet_hours_email = BooleanField('Disable Email During Quiet Hours', default=False)
    
    # Notification frequency settings
    max_notifications_per_hour = IntegerField('Max Notifications Per Hour', validators=[
        Optional(), NumberRange(min=1, max=100)
    ], default=20)
    
    batch_notifications = BooleanField('Batch Similar Notifications', default=True)
    batch_window_minutes = IntegerField('Batch Window (Minutes)', validators=[
        Optional(), NumberRange(min=1, max=60)
    ], default=5)
    
    # Advanced settings
    notification_sound_enabled = BooleanField('Enable Notification Sound', default=True)
    notification_desktop_enabled = BooleanField('Enable Desktop Notifications', default=True)
    
    # Privacy settings
    show_online_status = BooleanField('Show Online Status in Notifications', default=True)
    show_email_in_notifications = BooleanField('Show Email Address in Notifications', default=False)
    
    def validate_quiet_hours_end(self, field):
        """Validate quiet hours end time"""
        if self.quiet_hours_enabled.data and self.quiet_hours_start.data and field.data:
            if field.data <= self.quiet_hours_start.data:
                raise ValidationError('End time must be after start time')
    
    def validate_max_notifications_per_hour(self, field):
        """Validate max notifications per hour"""
        if field.data and field.data < 1:
            raise ValidationError('Must allow at least 1 notification per hour')


class NotificationSearchAdvancedForm(FlaskForm):
    """Advanced form for notification search and filtering"""
    
    # Search terms
    search_query = StringField('Search', validators=[Optional(), Length(max=200)])
    
    # Notification type filters
    types = SelectMultipleField('Notification Types', choices=[
        ('comment', 'Comments'),
        ('message', 'Messages'),
        ('system', 'System'),
        ('moderation', 'Moderation'),
        ('security', 'Security'),
        ('admin', 'Admin')
    ], validators=[Optional()])
    
    # Status filters
    is_read = SelectField('Read Status', choices=[
        ('', 'All'),
        ('read', 'Read'),
        ('unread', 'Unread')
    ], validators=[Optional()])
    
    # Priority filters
    priorities = SelectMultipleField('Priorities', choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ], validators=[Optional()])
    
    # Date range filters
    date_range = SelectField('Date Range', choices=[
        ('', 'Custom Range'),
        ('today', 'Today'),
        ('yesterday', 'Yesterday'),
        ('last_7_days', 'Last 7 Days'),
        ('last_30_days', 'Last 30 Days'),
        ('last_90_days', 'Last 90 Days'),
        ('this_year', 'This Year'),
        ('last_year', 'Last Year')
    ], validators=[Optional()])
    
    start_date = DateTimeField('Start Date', validators=[Optional()])
    end_date = DateTimeField('End Date', validators=[Optional()])
    
    # Sorting options
    sort_by = SelectField('Sort By', choices=[
        ('created_at', 'Date Created'),
        ('read_at', 'Date Read'),
        ('priority', 'Priority'),
        ('type', 'Type'),
        ('content', 'Content')
    ], validators=[Optional()], default='created_at')
    
    sort_order = SelectField('Sort Order', choices=[
        ('desc', 'Newest First'),
        ('asc', 'Oldest First')
    ], validators=[Optional()], default='desc')
    
    # Display options
    per_page = SelectField('Results Per Page', choices=[
        ('10', '10'),
        ('25', '25'),
        ('50', '50'),
        ('100', '100')
    ], validators=[Optional()], default='25')
    
    # Advanced options
    include_archived = BooleanField('Include Archived Notifications', default=False)
    show_only_unread = BooleanField('Show Only Unread', default=False)
    
    def validate_end_date(self, field):
        """Validate end date is after start date"""
        if field.data and self.start_date.data:
            if field.data < self.start_date.data:
                raise ValidationError('End date must be after start date')


class NotificationArchiveForm(FlaskForm):
    """Form for notification archiving operations"""
    
    # Archive options
    archive_read_older_than = SelectField('Archive Read Notifications Older Than', choices=[
        ('', 'Don\'t Auto-Archive'),
        ('7_days', '7 Days'),
        ('30_days', '30 Days'),
        ('90_days', '90 Days'),
        ('180_days', '180 Days'),
        ('365_days', '1 Year')
    ], validators=[Optional()])
    
    archive_unread_older_than = SelectField('Archive Unread Notifications Older Than', choices=[
        ('', 'Don\'t Auto-Archive'),
        ('30_days', '30 Days'),
        ('90_days', '90 Days'),
        ('180_days', '180 Days'),
        ('365_days', '1 Year'),
        ('730_days', '2 Years')
    ], validators=[Optional()])
    
    # Manual archive options
    notification_ids = TextAreaField('Notification IDs to Archive', validators=[
        Optional()
    ])
    
    archive_all_read = BooleanField('Archive All Read Notifications', default=False)
    archive_all_older_than = DateTimeField('Archive All Notifications Older Than', validators=[Optional()])
    
    # Archive settings
    keep_important = BooleanField('Keep Important Notifications', default=True)
    keep_unread = BooleanField('Keep Unread Notifications', default=True)
    
    def validate_notification_ids(self, field):
        """Validate notification IDs format"""
        if field.data:
            try:
                ids = [int(nid.strip()) for nid in field.data.split(',') if nid.strip()]
                if len(ids) > 1000:
                    raise ValidationError('Maximum 1000 notifications can be archived at once')
            except ValueError:
                raise ValidationError('Invalid notification ID format. Use comma-separated integers.')
    
    def validate_archive_all_older_than(self, field):
        """Validate archive date"""
        if field.data and field.data > datetime.utcnow():
            raise ValidationError('Archive date cannot be in the future')


class NotificationScheduleForm(FlaskForm):
    """Form for notification scheduling and timing"""
    
    # Global scheduling
    enable_scheduling = BooleanField('Enable Notification Scheduling', default=False)
    
    # Daily schedule
    daily_digest_enabled = BooleanField('Enable Daily Digest', default=False)
    daily_digest_time = TimeField('Daily Digest Time', validators=[Optional()], default=time(9, 0))
    
    weekly_summary_enabled = BooleanField('Enable Weekly Summary', default=False)
    weekly_summary_day = SelectField('Weekly Summary Day', choices=[
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
        ('sunday', 'Sunday')
    ], validators=[Optional()], default='monday')
    
    weekly_summary_time = TimeField('Weekly Summary Time', validators=[Optional()], default=time(9, 0))
    
    # Quiet hours (enhanced)
    quiet_hours_enabled = BooleanField('Enable Quiet Hours', default=False)
    quiet_hours_start = TimeField('Quiet Hours Start', validators=[Optional()], default=time(22, 0))
    quiet_hours_end = TimeField('Quiet Hours End', validators=[Optional()], default=time(8, 0))
    
    quiet_hours_weekdays_only = BooleanField('Quiet Hours Weekdays Only', default=False)
    
    # Do Not Disturb
    do_not_disturb_enabled = BooleanField('Enable Do Not Disturb', default=False)
    do_not_disturb_start = DateTimeField('Do Not Disturb Start', validators=[Optional()])
    do_not_disturb_end = DateTimeField('Do Not Disturb End', validators=[Optional()])
    
    # Smart scheduling
    smart_scheduling_enabled = BooleanField('Enable Smart Scheduling', default=False)
    max_notifications_per_hour = IntegerField('Max Notifications Per Hour', validators=[
        Optional(), NumberRange(min=1, max=100)
    ], default=20)
    
    delay_low_priority = BooleanField('Delay Low Priority Notifications', default=False)
    delay_hours_start = TimeField('Delay Start Time', validators=[Optional()], default=time(22, 0))
    delay_hours_end = TimeField('Delay End Time', validators=[Optional()], default=time(8, 0))
    
    def validate_quiet_hours_end(self, field):
        """Validate quiet hours end time"""
        if self.quiet_hours_enabled.data and self.quiet_hours_start.data and field.data:
            if field.data <= self.quiet_hours_start.data:
                raise ValidationError('End time must be after start time')
    
    def validate_do_not_disturb_end(self, field):
        """Validate do not disturb end time"""
        if self.do_not_disturb_enabled.data and self.do_not_disturb_start.data and field.data:
            if field.data <= self.do_not_disturb_start.data:
                raise ValidationError('End time must be after start time')
    
    def validate_delay_hours_end(self, field):
        """Validate delay hours end time"""
        if self.delay_low_priority.data and self.delay_hours_start.data and field.data:
            if field.data <= self.delay_hours_start.data:
                raise ValidationError('End time must be after start time')


class NotificationGroupingForm(FlaskForm):
    """Form for notification grouping and organization"""
    
    # Grouping preferences
    enable_grouping = BooleanField('Enable Notification Grouping', default=True)
    
    group_by_type = BooleanField('Group by Notification Type', default=True)
    group_by_priority = BooleanField('Group by Priority', default=False)
    group_by_source = BooleanField('Group by Source', default=False)
    
    # Grouping settings
    max_group_size = IntegerField('Maximum Group Size', validators=[
        Optional(), NumberRange(min=2, max=50)
    ], default=10)
    
    group_timeout_minutes = IntegerField('Group Timeout (Minutes)', validators=[
        Optional(), NumberRange(min=1, max=60)
    ], default=5)
    
    # Smart grouping
    smart_grouping_enabled = BooleanField('Enable Smart Grouping', default=False)
    group_similar_content = BooleanField('Group Similar Content', default=False)
    content_similarity_threshold = FloatField('Content Similarity Threshold', validators=[
        Optional(), NumberRange(min=0.1, max=1.0)
    ], default=0.8)
    
    # Display preferences
    show_group_count = BooleanField('Show Group Count', default=True)
    expand_groups_on_click = BooleanField('Expand Groups on Click', default=True)
    auto_expand_important = BooleanField('Auto Expand Important Groups', default=True)
    
    def validate_content_similarity_threshold(self, field):
        """Validate similarity threshold"""
        if field.data and (field.data < 0.1 or field.data > 1.0):
            raise ValidationError('Similarity threshold must be between 0.1 and 1.0')
