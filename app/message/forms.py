from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, TextAreaField, SelectField, BooleanField, IntegerField, DateField, HiddenField, SelectMultipleField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, NumberRange
from datetime import datetime

class MessageForm(FlaskForm):
    receiver_id = SelectField('To', coerce=int, validators=[DataRequired()])
    content = TextAreaField('Message', validators=[DataRequired(), Length(min=1)])
    submit = SubmitField('Send Message')

class MessageSearchForm(FlaskForm):
    """Form for advanced message search with filtering options"""
    query = StringField('Search Query', validators=[Optional(), Length(max=500)])
    
    # Date filters
    date_from = DateField('From Date', validators=[Optional()])
    date_to = DateField('To Date', validators=[Optional()])
    
    # Sender filter
    sender_id = SelectField('Sender', coerce=int, validators=[Optional()])
    
    # Status filters
    is_read = SelectField('Read Status', choices=[
        ('', 'All'),
        ('1', 'Read'),
        ('0', 'Unread')
    ], validators=[Optional()], coerce=lambda x: x if x == '' else bool(int(x)))
    
    # Priority filter
    priority = SelectField('Priority', choices=[
        ('', 'All'),
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ], validators=[Optional()])
    
    # Attachment filter
    has_attachments = SelectField('Attachments', choices=[
        ('', 'All'),
        ('1', 'With Attachments'),
        ('0', 'Without Attachments')
    ], validators=[Optional()], coerce=lambda x: x if x == '' else bool(int(x)))
    
    # Thread filter
    thread_id = SelectField('Thread', coerce=int, validators=[Optional()])
    
    # Sort options
    sort_by = SelectField('Sort By', choices=[
        ('relevance', 'Relevance'),
        ('date', 'Date'),
        ('sender', 'Sender')
    ], default='relevance', validators=[Optional()])
    
    # Search type
    search_type = SelectField('Search Type', choices=[
        ('basic', 'Basic'),
        ('advanced', 'Advanced'),
        ('boolean', 'Boolean')
    ], default='basic', validators=[Optional()])
    
    # Pagination
    page = IntegerField('Page', default=1, validators=[Optional(), NumberRange(min=1)])
    per_page = SelectField('Results per page', choices=[
        ('10', '10'),
        ('20', '20'),
        ('50', '50'),
        ('100', '100')
    ], default='20', coerce=int, validators=[Optional()])
    
    submit = SubmitField('Search')
    clear = SubmitField('Clear')

class MessageThreadForm(FlaskForm):
    """Form for creating and managing message threads"""
    subject = StringField('Subject', validators=[Optional(), Length(max=255)])
    participants = SelectMultipleField('Participants', coerce=int, validators=[DataRequired()])
    
    # Thread settings
    thread_type = SelectField('Thread Type', choices=[
        ('private', 'Private'),
        ('group', 'Group'),
        ('system', 'System')
    ], default='private', validators=[Optional()])
    
    priority = SelectField('Priority', choices=[
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ], default='normal', validators=[Optional()])
    
    submit = SubmitField('Create Thread')

class MessageForwardForm(FlaskForm):
    """Form for forwarding messages"""
    forward_to = SelectField('Forward To', coerce=int, validators=[DataRequired()])
    forward_note = TextAreaField('Note', validators=[Optional(), Length(max=1000)])
    
    # Forward options
    is_private_forward = BooleanField('Hide Original Sender')
    include_attachments = BooleanField('Include Attachments', default=True)
    
    submit = SubmitField('Forward Message')

class MessageAttachmentForm(FlaskForm):
    """Form for message file attachments"""
    file = StringField('File', validators=[DataRequired(), Length(max=255)])
    
    # File validation (client-side)
    max_size = HiddenField(default='10485760')  # 10MB
    
    submit = SubmitField('Upload Attachment')

class MessageTemplateForm(FlaskForm):
    """Form for creating and managing message templates"""
    name = StringField('Template Name', validators=[DataRequired(), Length(max=100)])
    content = TextAreaField('Template Content', validators=[DataRequired(), Length(min=1, max=5000)])
    
    # Template metadata
    category = SelectField('Category', choices=[
        ('general', 'General'),
        ('welcome', 'Welcome'),
        ('support', 'Support'),
        ('announcement', 'Announcement'),
        ('personal', 'Personal')
    ], default='general', validators=[Optional()])
    
    variables = TextAreaField('Variables', validators=[Optional(), Length(max=500)],
                              description='List variables in format: {{variable_name}}')
    
    is_public = BooleanField('Public Template', default=False)
    
    submit = SubmitField('Save Template')

class MessageComposeForm(FlaskForm):
    """Enhanced message composition form"""
    receiver_id = SelectField('To', coerce=int, validators=[DataRequired()])
    subject = StringField('Subject', validators=[Optional(), Length(max=255)])
    content = TextAreaField('Message', validators=[DataRequired(), Length(min=1)])
    
    # Rich text options
    content_format = SelectField('Format', choices=[
        ('text', 'Plain Text'),
        ('html', 'HTML'),
        ('markdown', 'Markdown')
    ], default='text', validators=[Optional()])
    
    # Message options
    priority = SelectField('Priority', choices=[
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ], default='normal', validators=[Optional()])
    
    # Thread options
    create_thread = BooleanField('Create New Thread')
    thread_subject = StringField('Thread Subject', validators=[Optional(), Length(max=255)])
    
    # Template options
    use_template = SelectField('Use Template', coerce=int, validators=[Optional()])
    
    submit = SubmitField('Send Message')
    save_draft = SubmitField('Save Draft')

class MessageAttachmentForm(FlaskForm):
    """Form for file attachment upload and management"""
    
    file = FileField('File', validators=[
        FileRequired(),
        FileAllowed([
            'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg',  # Images
            'pdf', 'doc', 'docx', 'txt', 'rtf', 'odt', 'xls', 'xlsx', 'ppt', 'pptx',  # Documents
            'mp4', 'avi', 'mov', 'wmv', 'flv', 'webm', 'mkv',  # Videos
            'mp3', 'wav', 'ogg', 'flac', 'aac', 'm4a', 'wma',  # Audio
            'zip', 'rar', '7z', 'tar', 'gz', 'bz2'  # Archives
        ], 'Invalid file type. Please upload an image, document, video, audio, or archive file.')
    ])
    
    message_id = HiddenField('Message ID', validators=[DataRequired()])
    
    # Attachment options
    is_public = BooleanField('Make attachment publicly accessible', default=False)
    
    submit = SubmitField('Upload Attachment')

class MessageForwardForm(FlaskForm):
    """Form for message forwarding"""
    
    forward_to = SelectField('Forward To', coerce=int, validators=[DataRequired()])
    forward_note = TextAreaField('Forward Note (Optional)', validators=[Optional(), Length(max=500)])
    
    # Forward options
    include_attachments = BooleanField('Include attachments', default=True)
    create_thread = BooleanField('Create new thread', default=False)
    thread_subject = StringField('Thread Subject', validators=[Optional(), Length(max=255)])
    
    submit = SubmitField('Forward Message')

class MessageQuoteForm(FlaskForm):
    """Form for message quoting"""
    
    message_id = HiddenField('Message ID', validators=[DataRequired()])
    quote_style = SelectField('Quote Style', choices=[
        ('standard', 'Standard'),
        ('markdown', 'Markdown'),
        ('html', 'HTML')
    ], default='standard')
    
    submit = SubmitField('Quote Message')

class MessageExportForm(FlaskForm):
    """Form for message export"""
    
    message_id = HiddenField('Message ID', validators=[DataRequired()])
    export_format = SelectField('Export Format', choices=[
        ('json', 'JSON'),
        ('txt', 'Plain Text'),
        ('html', 'HTML'),
        ('markdown', 'Markdown')
    ], default='json')
    
    include_attachments = BooleanField('Include attachments', default=True)
    include_metadata = BooleanField('Include metadata', default=True)
    
    submit = SubmitField('Export Message')
