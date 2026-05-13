"""
File Management Forms

This module contains forms for the advanced file management system,
including file uploads, sharing, permissions, and analytics.
"""

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, BooleanField, IntegerField, DateTimeField, FileField, HiddenField
from wtforms.validators import DataRequired, Length, Optional, NumberRange, ValidationError
from flask import current_app
from datetime import datetime, timedelta
import os

class FileUploadForm(FlaskForm):
    """Form for file uploads"""
    file = FileField('File', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[Optional(), Length(max=500)])
    is_public = BooleanField('Public Access', default=False)
    folder = StringField('Folder', validators=[Optional(), Length(max=100)])
    tags = StringField('Tags', validators=[Optional(), Length(max=200)])  # Comma-separated
    
    def validate_file(self, field):
        """Validate file upload"""
        if field.data:
            file = field.data
            filename = file.filename
            
            # Check file size (50MB max)
            max_size = current_app.config.get('MAX_FILE_SIZE', 50 * 1024 * 1024)
            if len(file.getvalue()) > max_size:
                raise ValidationError(f'File size exceeds maximum allowed size of {max_size // 1024 // 1024}MB')
            
            # Check file extension
            allowed_extensions = current_app.config.get('ALLOWED_EXTENSIONS', 
                ['jpg', 'jpeg', 'png', 'gif', 'webp', 'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt', 'zip', 'rar'])
            
            if not ('.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions):
                raise ValidationError('File type not allowed')

class FileEditForm(FlaskForm):
    """Form for editing file metadata"""
    description = TextAreaField('Description', validators=[Optional(), Length(max=500)])
    is_public = BooleanField('Public Access', default=False)
    tags = StringField('Tags', validators=[Optional(), Length(max=200)])
    expires_at = DateTimeField('Expires At', format='%Y-%m-%d %H:%M', validators=[Optional()])
    
    def validate_expires_at(self, field):
        """Validate expiration date is in the future"""
        if field.data and field.data <= datetime.utcnow():
            raise ValidationError('Expiration date must be in the future')

class FileShareForm(FlaskForm):
    """Form for sharing files with other users"""
    user_id = IntegerField('User ID', validators=[DataRequired(), NumberRange(min=1)])
    permission_level = SelectField('Permission Level', 
                                choices=[('view', 'View Only'), ('download', 'Download'), ('edit', 'Edit')],
                                validators=[DataRequired()])
    expires_at = DateTimeField('Expires At', format='%Y-%m-%d %H:%M', validators=[Optional()])
    message = TextAreaField('Message', validators=[Optional(), Length(max=200)])
    
    def validate_expires_at(self, field):
        """Validate expiration date is in the future"""
        if field.data and field.data <= datetime.utcnow():
            raise ValidationError('Expiration date must be in the future')

class FileSearchForm(FlaskForm):
    """Form for searching files"""
    query = StringField('Search Query', validators=[Optional()])
    file_type = SelectField('File Type',
                           choices=[('all', 'All Files'), ('image', 'Images'), ('document', 'Documents'),
                                  ('video', 'Videos'), ('audio', 'Audio'), ('other', 'Other')],
                           default='all', validators=[Optional()])
    uploaded_by = IntegerField('Uploaded By', validators=[Optional(), NumberRange(min=1)])
    date_from = DateTimeField('From Date', format='%Y-%m-%d', validators=[Optional()])
    date_to = DateTimeField('To Date', format='%Y-%m-%d', validators=[Optional()])
    tags = StringField('Tags', validators=[Optional()])  # Comma-separated
    
    def __init__(self, *args, **kwargs):
        super(FileSearchForm, self).__init__(*args, **kwargs)

class BulkFileActionForm(FlaskForm):
    """Form for bulk actions on files"""
    action = SelectField('Action',
                        choices=[('delete', 'Delete'), ('share', 'Share'), ('move', 'Move'), ('tag', 'Add Tags')],
                        validators=[DataRequired()])
    target_folder = StringField('Target Folder', validators=[Optional(), Length(max=100)])
    tags = StringField('Tags', validators=[Optional(), Length(max=200)])  # Comma-separated
    message = TextAreaField('Message', validators=[Optional(), Length(max=200)])

class ImageProcessingForm(FlaskForm):
    """Form for image processing operations"""
    operation = SelectField('Operation',
                          choices=[('resize', 'Resize'), ('crop', 'Crop'), ('optimize', 'Optimize')],
                          validators=[DataRequired()])
    width = IntegerField('Width', validators=[Optional(), NumberRange(min=1, max=5000)])
    height = IntegerField('Height', validators=[Optional(), NumberRange(min=1, max=5000)])
    maintain_aspect = BooleanField('Maintain Aspect Ratio', default=True)
    quality = IntegerField('Quality', default=85, validators=[Optional(), NumberRange(min=1, max=100)])
    crop_x = IntegerField('Crop X', validators=[Optional(), NumberRange(min=0)])
    crop_y = IntegerField('Crop Y', validators=[Optional(), NumberRange(min=0)])
    crop_width = IntegerField('Crop Width', validators=[Optional(), NumberRange(min=1)])
    crop_height = IntegerField('Crop Height', validators=[Optional(), NumberRange(min=1)])

class FileAnalyticsForm(FlaskForm):
    """Form for file analytics and reporting"""
    date_from = DateTimeField('From Date', format='%Y-%m-%d', validators=[Optional()])
    date_to = DateTimeField('To Date', format='%Y-%m-%d', validators=[Optional()])
    report_type = SelectField('Report Type',
                             choices=[('summary', 'Summary'), ('detailed', 'Detailed'), ('usage', 'Usage Patterns')],
                             default='summary', validators=[Optional()])
    file_id = IntegerField('File ID', validators=[Optional(), NumberRange(min=1)])
    user_id = IntegerField('User ID', validators=[Optional(), NumberRange(min=1)])

class FolderCreateForm(FlaskForm):
    """Form for creating folders"""
    name = StringField('Folder Name', validators=[DataRequired(), Length(min=1, max=100)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=200)])
    is_public = BooleanField('Public Folder', default=False)
    parent_folder = StringField('Parent Folder', validators=[Optional(), Length(max=100)])
    
    def validate_name(self, field):
        """Validate folder name"""
        if field.data:
            # Check for invalid characters
            invalid_chars = ['<', '>', ':', '"', '|', '?', '*', '/']
            if any(char in field.data for char in invalid_chars):
                raise ValidationError('Folder name contains invalid characters')

class FileLinkForm(FlaskForm):
    """Form for creating shareable links"""
    expires_in = SelectField('Expires In',
                            choices=[('1h', '1 Hour'), ('24h', '24 Hours'), ('7d', '7 Days'), ('30d', '30 Days'), ('never', 'Never')],
                            default='7d', validators=[Optional()])
    max_downloads = IntegerField('Max Downloads', validators=[Optional(), NumberRange(min=1, max=1000)])
    password = StringField('Password', validators=[Optional(), Length(min=4, max=50)])
    require_login = BooleanField('Require Login', default=True)
    
    def validate_max_downloads(self, field):
        """Validate max downloads"""
        if field.data and field.data < 1:
            raise ValidationError('Max downloads must be at least 1')

class FileImportForm(FlaskForm):
    """Form for importing files from URLs"""
    url = StringField('File URL', validators=[DataRequired(), Length(max=500)])
    filename = StringField('Filename', validators=[Optional(), Length(max=255)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=500)])
    folder = StringField('Folder', validators=[Optional(), Length(max=100)])
    is_public = BooleanField('Public Access', default=False)
    
    def validate_url(self, field):
        """Validate URL format"""
        if field.data:
            if not (field.data.startswith('http://') or field.data.startswith('https://')):
                raise ValidationError('URL must start with http:// or https://')

class FileExportForm(FlaskForm):
    """Form for exporting files"""
    export_format = SelectField('Export Format',
                               choices=[('zip', 'ZIP Archive'), ('tar', 'TAR Archive')],
                               default='zip', validators=[Optional()])
    include_metadata = BooleanField('Include Metadata', default=True)
    include_thumbnails = BooleanField('Include Thumbnails', default=False)
    date_from = DateTimeField('From Date', format='%Y-%m-%d', validators=[Optional()])
    date_to = DateTimeField('To Date', format='%Y-%m-%d', validators=[Optional()])
    file_types = SelectField('File Types',
                             choices=[('all', 'All Files'), ('image', 'Images'), ('document', 'Documents')],
                             default='all', validators=[Optional()])

class FilePermissionForm(FlaskForm):
    """Form for managing file permissions"""
    permission_type = SelectField('Permission Type',
                                 choices=[('private', 'Private'), ('public', 'Public'), ('restricted', 'Restricted')],
                                 validators=[DataRequired()])
    allowed_users = StringField('Allowed Users', validators=[Optional()])  # Comma-separated user IDs
    allowed_roles = StringField('Allowed Roles', validators=[Optional()])  # Comma-separated role names
    expires_at = DateTimeField('Expires At', format='%Y-%m-%d %H:%M', validators=[Optional()])
    
    def validate_allowed_users(self, field):
        """Validate allowed users format"""
        if field.data:
            try:
                user_ids = [int(uid.strip()) for uid in field.data.split(',')]
                if any(uid < 1 for uid in user_ids):
                    raise ValidationError('User IDs must be positive integers')
            except ValueError:
                raise ValidationError('Invalid user ID format')

class FileVersionForm(FlaskForm):
    """Form for managing file versions"""
    version_description = TextAreaField('Version Description', validators=[Optional(), Length(max=200)])
    create_backup = BooleanField('Create Backup', default=True)
    notify_users = BooleanField('Notify Users', default=False)

class FileCommentForm(FlaskForm):
    """Form for adding comments to files"""
    comment = TextAreaField('Comment', validators=[DataRequired(), Length(min=1, max=500)])
    is_private = BooleanField('Private Comment', default=False)

class FileTagForm(FlaskForm):
    """Form for managing file tags"""
    tags = StringField('Tags', validators=[Optional(), Length(max=200)])
    action = SelectField('Action',
                        choices=[('add', 'Add Tags'), ('remove', 'Remove Tags'), ('replace', 'Replace Tags')],
                        default='add', validators=[Optional()])
    
    def validate_tags(self, field):
        """Validate tags format"""
        if field.data:
            tags = [tag.strip() for tag in field.data.split(',')]
            if len(tags) > 10:
                raise ValidationError('Maximum 10 tags allowed')
            for tag in tags:
                if len(tag) > 50:
                    raise ValidationError('Each tag must be less than 50 characters')

class FileReportForm(FlaskForm):
    """Form for generating file reports"""
    report_type = SelectField('Report Type',
                             choices=[('storage', 'Storage Usage'), ('activity', 'Activity Report'), 
                                   ('popular', 'Popular Files'), ('user_stats', 'User Statistics')],
                             validators=[DataRequired()])
    date_range = SelectField('Date Range',
                            choices=[('today', 'Today'), ('week', 'This Week'), ('month', 'This Month'), 
                                   ('year', 'This Year'), ('custom', 'Custom')],
                            default='month', validators=[Optional()])
    date_from = DateTimeField('From Date', format='%Y-%m-%d', validators=[Optional()])
    date_to = DateTimeField('To Date', format='%Y-%m-%d', validators=[Optional()])
    include_charts = BooleanField('Include Charts', default=True)
    export_format = SelectField('Export Format',
                                choices=[('html', 'HTML'), ('pdf', 'PDF'), ('csv', 'CSV')],
                                default='html', validators=[Optional()])

class FileSettingsForm(FlaskForm):
    """Form for file management settings"""
    auto_generate_thumbnails = BooleanField('Auto-generate Thumbnails', default=True)
    thumbnail_sizes = StringField('Thumbnail Sizes', validators=[Optional(), Length(max=100)])
    max_file_size = IntegerField('Max File Size (MB)', validators=[Optional(), NumberRange(min=1, max=1000)])
    allowed_extensions = StringField('Allowed Extensions', validators=[Optional(), Length(max=500)])
    storage_provider = SelectField('Storage Provider',
                                 choices=[('local', 'Local'), ('s3', 'AWS S3'), ('gcs', 'Google Cloud Storage')],
                                 validators=[Optional()])
    enable_analytics = BooleanField('Enable Analytics', default=True)
    retention_days = IntegerField('File Retention Days', validators=[Optional(), NumberRange(min=1, max=3650)])
    
    def validate_thumbnail_sizes(self, field):
        """Validate thumbnail sizes format"""
        if field.data:
            try:
                sizes = [size.strip() for size in field.data.split(',')]
                for size in sizes:
                    if 'x' not in size:
                        raise ValidationError('Thumbnail sizes must be in format WIDTHxHEIGHT')
                    width, height = size.split('x')
                    int(width) and int(height)  # Validate they are numbers
            except:
                raise ValidationError('Invalid thumbnail sizes format')
    
    def validate_allowed_extensions(self, field):
        """Validate allowed extensions format"""
        if field.data:
            extensions = [ext.strip().lower().lstrip('.') for ext in field.data.split(',')]
            if len(extensions) > 50:
                raise ValidationError('Too many extensions allowed')
