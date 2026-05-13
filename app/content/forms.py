"""
Content Management Forms

This module contains forms for the enhanced content management system,
including draft management, versioning, scheduling, and collaboration features.
"""

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, DateTimeField, BooleanField, IntegerField, FloatField, ValidationError
from wtforms.validators import DataRequired, Length, Optional, NumberRange
from flask import current_app
from datetime import datetime
import json

class PostForm(FlaskForm):
    """Enhanced post form with content management features"""
    title = StringField('Title', validators=[DataRequired(), Length(min=1, max=256)])
    content = TextAreaField('Content', validators=[DataRequired()])
    category_id = SelectField('Category', coerce=int, validators=[Optional()])
    
    # Draft management
    is_draft = BooleanField('Save as Draft', default=False)
    auto_save_enabled = BooleanField('Enable Auto-save', default=True)
    
    # Scheduling
    is_scheduled = BooleanField('Schedule Publishing', default=False)
    scheduled_publish_at = DateTimeField('Publish Date', format='%Y-%m-%d %H:%M', validators=[Optional()])
    
    # Expiration
    expires_at = DateTimeField('Expires At', format='%Y-%m-%d %H:%M', validators=[Optional()])
    
    # Analytics
    engagement_score = FloatField('Engagement Score', validators=[Optional(), NumberRange(min=0.0, max=10.0)])
    
    def __init__(self, *args, **kwargs):
        super(PostForm, self).__init__(*args, **kwargs)
        if current_app and current_app.config.get('CATEGORIES'):
            self.category_id.choices = [(0, 'Select Category')] + current_app.config.get('CATEGORIES')

class DraftForm(FlaskForm):
    """Form for managing post drafts"""
    title = StringField('Title', validators=[DataRequired(), Length(min=1, max=256)])
    content = TextAreaField('Content', validators=[DataRequired()])
    auto_save_data = TextAreaField('Auto-save Data', validators=[Optional()])
    
    def validate_auto_save_data(self, field):
        """Validate auto-save data is valid JSON"""
        if field.data:
            try:
                json.loads(field.data)
            except json.JSONDecodeError:
                raise ValidationError('Auto-save data must be valid JSON')

class VersionForm(FlaskForm):
    """Form for managing post versions"""
    change_summary = StringField('Change Summary', validators=[Length(max=500)])
    version_number = IntegerField('Version Number', validators=[Optional(), NumberRange(min=1)])
    title = StringField('Title', validators=[DataRequired(), Length(min=1, max=256)])
    content = TextAreaField('Content', validators=[DataRequired()])

class ScheduleForm(FlaskForm):
    """Form for scheduling post publishing"""
    scheduled_publish_at = DateTimeField('Publish Date', format='%Y-%m-%d %H:%M', validators=[DataRequired()])
    is_scheduled = BooleanField('Enable Scheduling', default=True)
    
    def validate_scheduled_publish_at(self, field):
        """Validate that the scheduled date is in the future"""
        if field.data and field.data <= datetime.utcnow():
            raise ValidationError('Scheduled publish date must be in the future')

class CollaborationForm(FlaskForm):
    """Form for managing post collaboration"""
    user_id = IntegerField('User ID', validators=[DataRequired(), NumberRange(min=1)])
    permission_level = SelectField('Permission Level', 
                                choices=[('view', 'View Only'), ('edit', 'Edit'), ('admin', 'Admin')],
                                validators=[DataRequired()])
    is_active = BooleanField('Active', default=True)

class ContentSearchForm(FlaskForm):
    """Form for searching content with advanced filters"""
    query = StringField('Search Query', validators=[Optional()])
    content_type = SelectField('Content Type',
                              choices=[('all', 'All'), ('published', 'Published'), ('draft', 'Drafts'), ('scheduled', 'Scheduled')],
                              default='all', validators=[Optional()])
    date_from = DateTimeField('From Date', format='%Y-%m-%d', validators=[Optional()])
    date_to = DateTimeField('To Date', format='%Y-%m-%d', validators=[Optional()])
    author_id = IntegerField('Author ID', validators=[Optional(), NumberRange(min=1)])
    category_id = SelectField('Category', coerce=int, validators=[Optional()])
    
    def __init__(self, *args, **kwargs):
        super(ContentSearchForm, self).__init__(*args, **kwargs)
        if current_app and current_app.config.get('CATEGORIES'):
            self.category_id.choices = [(0, 'All Categories')] + current_app.config.get('CATEGORIES')

class BulkActionForm(FlaskForm):
    """Form for bulk actions on content"""
    action = SelectField('Action',
                         choices=[('publish', 'Publish'), ('draft', 'Save as Draft'), ('archive', 'Archive'), 
                                 ('delete', 'Delete'), ('schedule', 'Schedule')],
                         validators=[DataRequired()])
    scheduled_date = DateTimeField('Scheduled Date', format='%Y-%m-%d %H:%M', validators=[Optional()])
    
    def validate_scheduled_date(self, field):
        """Validate scheduled date when action is schedule"""
        if self.action.data == 'schedule' and not field.data:
            raise ValidationError('Scheduled date is required when scheduling content')

class ExpirationForm(FlaskForm):
    """Form for setting content expiration"""
    expires_at = DateTimeField('Expiration Date', format='%Y-%m-%d %H:%M', validators=[DataRequired()])
    notify_before = BooleanField('Notify Before Expiration', default=True)
    notification_days = IntegerField('Notify Days Before', default=7, 
                                   validators=[Optional(), NumberRange(min=1, max=30)])

class ArchiveForm(FlaskForm):
    """Form for archiving content"""
    archive_reason = TextAreaField('Archive Reason', validators=[Optional(), Length(max=500)])
    notify_users = BooleanField('Notify Affected Users', default=False)
    redirect_url = StringField('Redirect URL', validators=[Optional(), Length(max=256)])

class ContentAnalyticsForm(FlaskForm):
    """Form for content analytics settings"""
    track_views = BooleanField('Track Views', default=True)
    track_engagement = BooleanField('Track Engagement', default=True)
    engagement_weight = FloatField('Engagement Weight', default=1.0, 
                                 validators=[Optional(), NumberRange(min=0.0, max=10.0)])
    update_frequency = SelectField('Update Frequency',
                                   choices=[('realtime', 'Real-time'), ('hourly', 'Hourly'), ('daily', 'Daily')],
                                   default='daily', validators=[Optional()])

class AutoSaveSettingsForm(FlaskForm):
    """Form for configuring auto-save settings"""
    enabled = BooleanField('Enable Auto-save', default=True)
    interval = IntegerField('Auto-save Interval (seconds)', default=30,
                           validators=[Optional(), NumberRange(min=10, max=300)])
    max_versions = IntegerField('Maximum Versions to Keep', default=10,
                               validators=[Optional(), NumberRange(min=1, max=50)])
    notify_on_conflict = BooleanField('Notify on Save Conflict', default=True)

class VersionCompareForm(FlaskForm):
    """Form for comparing post versions"""
    version_from = IntegerField('From Version', validators=[DataRequired(), NumberRange(min=1)])
    version_to = IntegerField('To Version', validators=[DataRequired(), NumberRange(min=1)])
    
    def validate(self):
        """Validate that from version is less than to version"""
        if not super(VersionCompareForm, self).validate():
            return False
        
        if self.version_from.data >= self.version_to.data:
            self.version_to.errors.append('To version must be greater than from version')
            return False
        
        return True

class ContentImportForm(FlaskForm):
    """Form for importing content from external sources"""
    source_type = SelectField('Source Type',
                             choices=[('markdown', 'Markdown'), ('html', 'HTML'), ('text', 'Plain Text')],
                             validators=[DataRequired()])
    content = TextAreaField('Content', validators=[DataRequired()])
    title = StringField('Title', validators=[DataRequired(), Length(min=1, max=256)])
    category_id = SelectField('Category', coerce=int, validators=[Optional()])
    preserve_formatting = BooleanField('Preserve Formatting', default=True)
    
    def __init__(self, *args, **kwargs):
        super(ContentImportForm, self).__init__(*args, **kwargs)
        if current_app and current_app.config.get('CATEGORIES'):
            self.category_id.choices = [(0, 'Select Category')] + current_app.config.get('CATEGORIES')

class ContentExportForm(FlaskForm):
    """Form for exporting content"""
    format_type = SelectField('Export Format',
                             choices=[('markdown', 'Markdown'), ('html', 'HTML'), ('pdf', 'PDF'), ('json', 'JSON')],
                             validators=[DataRequired()])
    include_versions = BooleanField('Include Version History', default=False)
    include_comments = BooleanField('Include Comments', default=False)
    include_analytics = BooleanField('Include Analytics', default=False)
    date_from = DateTimeField('From Date', format='%Y-%m-%d', validators=[Optional()])
    date_to = DateTimeField('To Date', format='%Y-%m-%d', validators=[Optional()])

class ContentPermissionForm(FlaskForm):
    """Form for managing content permissions"""
    permission_type = SelectField('Permission Type',
                                choices=[('public', 'Public'), ('private', 'Private'), ('restricted', 'Restricted')],
                                validators=[DataRequired()])
    allowed_users = StringField('Allowed Users', validators=[Optional()])  # Comma-separated user IDs
    allowed_roles = StringField('Allowed Roles', validators=[Optional()])  # Comma-separated role names
    password_protected = BooleanField('Password Protected', default=False)
    password = StringField('Password', validators=[Optional()])
