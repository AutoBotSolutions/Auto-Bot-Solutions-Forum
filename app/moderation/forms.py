"""
Automated Content Moderation Forms

This module contains Flask-WTF forms for the content moderation system,
including moderation queue management, rule configuration, and content analysis forms.
"""

from flask import current_app
from flask_wtf import FlaskForm
from wtforms import (
    StringField, TextAreaField, SelectField, IntegerField, FloatField,
    BooleanField, DateTimeField, FieldList, FormField, SelectMultipleField,
    HiddenField, SubmitField
)
from wtforms.validators import (
    DataRequired, Optional, NumberRange, Length, Email, URL,
    ValidationError, Regexp
)
from .models import ModerationRule, ModerationPattern


class ModerationQueueForm(FlaskForm):
    """Form for moderation queue filtering and management"""
    
    # Filter options
    status = SelectField('Status', choices=[
        ('', 'All Status'),
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('flagged', 'Flagged')
    ], filters=[lambda x: x or None])
    
    priority = SelectField('Priority', choices=[
        ('', 'All Priorities'),
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical')
    ], filters=[lambda x: x or None])
    
    content_type = SelectField('Content Type', choices=[
        ('', 'All Types'),
        ('post', 'Posts'),
        ('comment', 'Comments'),
        ('user_profile', 'User Profiles')
    ], filters=[lambda x: x or None])
    
    # Date range filters
    date_from = DateTimeField('Date From', format='%Y-%m-%d %H:%M', validators=[Optional()])
    date_to = DateTimeField('Date To', format='%Y-%m-%d %H:%M', validators=[Optional()])
    
    # Score filters
    min_spam_score = FloatField('Min Spam Score', validators=[Optional(), NumberRange(min=0.0, max=1.0)])
    max_spam_score = FloatField('Max Spam Score', validators=[Optional(), NumberRange(min=0.0, max=1.0)])
    
    min_quality_score = FloatField('Min Quality Score', validators=[Optional(), NumberRange(min=0.0, max=1.0)])
    max_quality_score = FloatField('Max Quality Score', validators=[Optional(), NumberRange(min=0.0, max=1.0)])
    
    # Search
    search = StringField('Search', validators=[Optional(), Length(max=255)])
    
    # Pagination
    limit = SelectField('Items per page', choices=[
        ('10', '10'),
        ('25', '25'),
        ('50', '50'),
        ('100', '100')
    ], default='25')
    
    def validate_date_from(self, field):
        """Validate date range"""
        if field.data and self.date_to.data:
            if field.data > self.date_to.data:
                raise ValidationError('Date from must be before date to')


class ContentAnalysisForm(FlaskForm):
    """Form for content analysis filtering"""
    
    # Content filters
    content_type = SelectField('Content Type', choices=[
        ('', 'All Types'),
        ('post', 'Posts'),
        ('comment', 'Comments'),
        ('user_profile', 'User Profiles')
    ], filters=[lambda x: x or None])
    
    language = SelectField('Language', choices=[
        ('', 'All Languages'),
        ('en', 'English'),
        ('es', 'Spanish'),
        ('fr', 'French'),
        ('de', 'German'),
        ('other', 'Other')
    ], filters=[lambda x: x or None])
    
    sentiment = SelectField('Sentiment', choices=[
        ('', 'All Sentiments'),
        ('positive', 'Positive'),
        ('negative', 'Negative'),
        ('neutral', 'Neutral')
    ], filters=[lambda x: x or None])
    
    # Quality score filters
    min_grammar_score = FloatField('Min Grammar Score', validators=[Optional(), NumberRange(min=0.0, max=1.0)])
    min_spelling_score = FloatField('Min Spelling Score', validators=[Optional(), NumberRange(min=0.0, max=1.0)])
    min_coherence_score = FloatField('Min Coherence Score', validators=[Optional(), NumberRange(min=0.0, max=1.0)])
    
    # Word count filters
    min_word_count = IntegerField('Min Word Count', validators=[Optional(), NumberRange(min=0)])
    max_word_count = IntegerField('Max Word Count', validators=[Optional(), NumberRange(min=0)])
    
    # Readability filters
    min_readability = FloatField('Min Readability', validators=[Optional(), NumberRange(min=0.0, max=1.0)])
    max_readability = FloatField('Max Readability', validators=[Optional(), NumberRange(min=0.0, max=1.0)])
    
    # Date range
    date_from = DateTimeField('Date From', format='%Y-%m-%d %H:%M', validators=[Optional()])
    date_to = DateTimeField('Date To', format='%Y-%m-%d %H:%M', validators=[Optional()])
    
    # Search
    search = StringField('Search', validators=[Optional(), Length(max=255)])
    
    # Pagination
    limit = SelectField('Items per page', choices=[
        ('10', '10'),
        ('25', '25'),
        ('50', '50'),
        ('100', '100')
    ], default='25')


class ModerationActionForm(FlaskForm):
    """Form for creating moderation actions"""
    
    action_type = SelectField('Action Type', choices=[
        ('approve', 'Approve'),
        ('reject', 'Reject'),
        ('delete', 'Delete'),
        ('warn', 'Warn'),
        ('suspend', 'Suspend'),
        ('flag', 'Flag'),
        ('edit', 'Edit')
    ], validators=[DataRequired()])
    
    action_reason = SelectField('Action Reason', choices=[
        ('spam', 'Spam'),
        ('inappropriate', 'Inappropriate Content'),
        ('low_quality', 'Low Quality'),
        ('off_topic', 'Off Topic'),
        ('harassment', 'Harassment'),
        ('copyright', 'Copyright Violation'),
        ('duplicate', 'Duplicate Content'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    
    action_description = TextAreaField('Description', validators=[
        DataRequired(),
        Length(min=10, max=1000)
    ])
    
    severity = SelectField('Severity', choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical')
    ], default='medium')
    
    confidence = FloatField('Confidence', validators=[
        DataRequired(),
        NumberRange(min=0.0, max=1.0)
    ], default=0.8)
    
    automated = BooleanField('Automated Action', default=False)
    
    # Appeal settings
    appealable = BooleanField('Allow Appeal', default=False)
    appeal_deadline = DateTimeField('Appeal Deadline', format='%Y-%m-%d %H:%M', validators=[Optional()])
    
    # Target information
    target_type = HiddenField('Target Type', validators=[DataRequired()])
    target_id = HiddenField('Target ID', validators=[DataRequired()])
    
    submit = SubmitField('Create Action')
    
    def validate_appeal_deadline(self, field):
        """Validate appeal deadline"""
        if self.appealable.data and not field.data:
            raise ValidationError('Appeal deadline is required when appeal is allowed')


class ModerationRuleForm(FlaskForm):
    """Form for creating and editing moderation rules"""
    
    name = StringField('Rule Name', validators=[
        DataRequired(),
        Length(min=3, max=100),
        Regexp(r'^[a-zA-Z0-9_\-\s]+$', message='Only letters, numbers, spaces, hyphens, and underscores allowed')
    ])
    
    description = TextAreaField('Description', validators=[
        DataRequired(),
        Length(min=10, max=500)
    ])
    
    rule_type = SelectField('Rule Type', choices=[
        ('keyword', 'Keyword Matching'),
        ('pattern', 'Pattern Matching'),
        ('spam', 'Spam Detection'),
        ('quality', 'Quality Assessment'),
        ('toxicity', 'Toxicity Detection'),
        ('behavioral', 'Behavioral Analysis')
    ], validators=[DataRequired()])
    
    content_types = SelectMultipleField('Content Types', choices=[
        ('post', 'Posts'),
        ('comment', 'Comments'),
        ('user_profile', 'User Profiles')
    ])
    
    action_type = SelectField('Action Type', choices=[
        ('approve', 'Approve'),
        ('reject', 'Reject'),
        ('delete', 'Delete'),
        ('warn', 'Warn'),
        ('flag', 'Flag'),
        ('queue', 'Add to Queue')
    ], validators=[DataRequired()])
    
    priority = IntegerField('Priority', validators=[
        DataRequired(),
        NumberRange(min=1, max=10)
    ], default=5)
    
    confidence_threshold = FloatField('Confidence Threshold', validators=[
        DataRequired(),
        NumberRange(min=0.0, max=1.0)
    ], default=0.7)
    
    auto_apply = BooleanField('Auto Apply', default=False)
    
    # Rule conditions (JSON field - will be handled in JavaScript)
    conditions = HiddenField('Conditions', validators=[DataRequired()])
    
    patterns = HiddenField('Patterns', validators=[Optional()])
    
    action_parameters = HiddenField('Action Parameters', validators=[Optional()])
    
    submit = SubmitField('Save Rule')
    
    def validate_name(self, field):
        """Validate rule name uniqueness"""
        if field.data:
            existing_rule = ModerationRule.query.filter_by(name=field.data).first()
            if existing_rule and hasattr(self, 'rule_id') and existing_rule.id != self.rule_id:
                raise ValidationError('Rule name already exists')


class SpamDetectionForm(FlaskForm):
    """Form for spam detection filtering"""
    
    # Detection filters
    is_spam = SelectField('Spam Status', choices=[
        ('', 'All'),
        ('true', 'Spam'),
        ('false', 'Not Spam')
    ], filters=[lambda x: x == 'true' if x else None])
    
    spam_type = SelectField('Spam Type', choices=[
        ('', 'All Types'),
        ('promotional', 'Promotional'),
        ('scam', 'Scam'),
        ('phishing', 'Phishing'),
        ('adult', 'Adult'),
        ('medical', 'Medical'),
        ('financial', 'Financial'),
        ('other', 'Other')
    ], filters=[lambda x: x or None])
    
    # Score filters
    min_overall_score = FloatField('Min Overall Score', validators=[Optional(), NumberRange(min=0.0, max=1.0)])
    max_overall_score = FloatField('Max Overall Score', validators=[Optional(), NumberRange(min=0.0, max=1.0)])
    
    min_confidence = FloatField('Min Confidence', validators=[Optional(), NumberRange(min=0.0, max=1.0)])
    
    # Content filters
    content_type = SelectField('Content Type', choices=[
        ('', 'All Types'),
        ('post', 'Posts'),
        ('comment', 'Comments'),
        ('user_profile', 'User Profiles')
    ], filters=[lambda x: x or None])
    
    # Date filters
    date_from = DateTimeField('Date From', format='%Y-%m-%d %H:%M', validators=[Optional()])
    date_to = DateTimeField('Date To', format='%Y-%m-%d %H:%M', validators=[Optional()])
    
    # Search
    search = StringField('Search', validators=[Optional(), Length(max=255)])
    
    # Pagination
    limit = SelectField('Items per page', choices=[
        ('10', '10'),
        ('25', '25'),
        ('50', '50'),
        ('100', '100')
    ], default='25')


class ContentQualityForm(FlaskForm):
    """Form for content quality filtering"""
    
    # Quality filters
    quality_grade = SelectField('Quality Grade', choices=[
        ('', 'All Grades'),
        ('A', 'A'),
        ('B', 'B'),
        ('C', 'C'),
        ('D', 'D'),
        ('F', 'F')
    ], filters=[lambda x: x or None])
    
    # Score filters
    min_overall_score = FloatField('Min Overall Score', validators=[Optional(), NumberRange(min=0.0, max=1.0)])
    max_overall_score = FloatField('Max Overall Score', validators=[Optional(), NumberRange(min=0.0, max=1.0)])
    
    min_content_quality = FloatField('Min Content Quality', validators=[Optional(), NumberRange(min=0.0, max=1.0)])
    min_presentation_quality = FloatField('Min Presentation Quality', validators=[Optional(), NumberRange(min=0.0, max=1.0)])
    min_originality_score = FloatField('Min Originality Score', validators=[Optional(), NumberRange(min=0.0, max=1.0)])
    
    # Individual quality scores
    min_grammar_score = FloatField('Min Grammar Score', validators=[Optional(), NumberRange(min=0.0, max=1.0)])
    min_spelling_score = FloatField('Min Spelling Score', validators=[Optional(), NumberRange(min=0.0, max=1.0)])
    min_structure_score = FloatField('Min Structure Score', validators=[Optional(), NumberRange(min=0.0, max=1.0)])
    min_coherence_score = FloatField('Min Coherence Score', validators=[Optional(), NumberRange(min=0.0, max=1.0)])
    
    # Content filters
    content_type = SelectField('Content Type', choices=[
        ('', 'All Types'),
        ('post', 'Posts'),
        ('comment', 'Comments'),
        ('user_profile', 'User Profiles')
    ], filters=[lambda x: x or None])
    
    # Word count filters
    min_word_count = IntegerField('Min Word Count', validators=[Optional(), NumberRange(min=0)])
    max_word_count = IntegerField('Max Word Count', validators=[Optional(), NumberRange(min=0)])
    
    # Date filters
    date_from = DateTimeField('Date From', format='%Y-%m-%d %H:%M', validators=[Optional()])
    date_to = DateTimeField('Date To', format='%Y-%m-%d %H:%M', validators=[Optional()])
    
    # Search
    search = StringField('Search', validators=[Optional(), Length(max=255)])
    
    # Pagination
    limit = SelectField('Items per page', choices=[
        ('10', '10'),
        ('25', '25'),
        ('50', '50'),
        ('100', '100')
    ], default='25')


class ModerationPatternForm(FlaskForm):
    """Form for creating and editing moderation patterns"""
    
    name = StringField('Pattern Name', validators=[
        DataRequired(),
        Length(min=3, max=100),
        Regexp(r'^[a-zA-Z0-9_\-\s]+$', message='Only letters, numbers, spaces, hyphens, and underscores allowed')
    ])
    
    description = TextAreaField('Description', validators=[
        DataRequired(),
        Length(min=10, max=500)
    ])
    
    pattern_type = SelectField('Pattern Type', choices=[
        ('regex', 'Regular Expression'),
        ('keyword', 'Keyword List'),
        ('behavioral', 'Behavioral Pattern'),
        ('metadata', 'Metadata Pattern')
    ], validators=[DataRequired()])
    
    category = SelectField('Category', choices=[
        ('spam', 'Spam'),
        ('toxicity', 'Toxicity'),
        ('quality', 'Quality'),
        ('security', 'Security'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    
    severity = SelectField('Severity', choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical')
    ], default='medium')
    
    match_type = SelectField('Match Type', choices=[
        ('any', 'Any Match'),
        ('all', 'All Matches'),
        ('exact', 'Exact Match')
    ], default='any')
    
    case_sensitive = BooleanField('Case Sensitive', default=False)
    weight = FloatField('Weight', validators=[
        DataRequired(),
        NumberRange(min=0.1, max=10.0)
    ], default=1.0)
    
    # Pattern data (JSON field - will be handled in JavaScript)
    pattern_data = HiddenField('Pattern Data', validators=[DataRequired()])
    
    submit = SubmitField('Save Pattern')
    
    def validate_name(self, field):
        """Validate pattern name uniqueness"""
        if field.data:
            existing_pattern = ModerationPattern.query.filter_by(name=field.data).first()
            if existing_pattern and hasattr(self, 'pattern_id') and existing_pattern.id != self.pattern_id:
                raise ValidationError('Pattern name already exists')


class ModerationSettingsForm(FlaskForm):
    """Form for moderation system settings"""
    
    # General settings
    enable_automated_moderation = BooleanField('Enable Automated Moderation', default=True)
    enable_spam_detection = BooleanField('Enable Spam Detection', default=True)
    enable_quality_assessment = BooleanField('Enable Quality Assessment', default=True)
    
    # Threshold settings
    spam_threshold = FloatField('Spam Threshold', validators=[
        DataRequired(),
        NumberRange(min=0.0, max=1.0)
    ], default=0.7)
    
    quality_threshold = FloatField('Quality Threshold', validators=[
        DataRequired(),
        NumberRange(min=0.0, max=1.0)
    ], default=0.3)
    
    auto_action_threshold = FloatField('Auto Action Threshold', validators=[
        DataRequired(),
        NumberRange(min=0.0, max=1.0)
    ], default=0.8)
    
    # Queue settings
    max_queue_age = IntegerField('Max Queue Age (hours)', validators=[
        DataRequired(),
        NumberRange(min=1, max=168)
    ], default=24)
    
    auto_process_interval = IntegerField('Auto Process Interval (minutes)', validators=[
        DataRequired(),
        NumberRange(min=1, max=1440)
    ], default=5)
    
    # Notification settings
    notify_moderators = BooleanField('Notify Moderators', default=True)
    notify_admins = BooleanField('Notify Admins', default=True)
    
    # Email settings
    enable_email_notifications = BooleanField('Enable Email Notifications', default=True)
    moderation_email = StringField('Moderation Email', validators=[Optional(), Email()])
    
    # Performance settings
    max_concurrent_analyses = IntegerField('Max Concurrent Analyses', validators=[
        DataRequired(),
        NumberRange(min=1, max=100)
    ], default=10)
    
    analysis_timeout = IntegerField('Analysis Timeout (seconds)', validators=[
        DataRequired(),
        NumberRange(min=1, max=300)
    ], default=30)
    
    # Caching settings
    enable_caching = BooleanField('Enable Result Caching', default=True)
    cache_ttl = IntegerField('Cache TTL (minutes)', validators=[
        DataRequired(),
        NumberRange(min=1, max=1440)
    ], default=60)
    
    submit = SubmitField('Save Settings')


class BulkModerationForm(FlaskForm):
    """Form for bulk moderation actions"""
    
    action_type = SelectField('Action Type', choices=[
        ('approve', 'Approve'),
        ('reject', 'Reject'),
        ('delete', 'Delete'),
        ('flag', 'Flag'),
        ('queue', 'Add to Queue')
    ], validators=[DataRequired()])
    
    action_reason = SelectField('Action Reason', choices=[
        ('spam', 'Spam'),
        ('inappropriate', 'Inappropriate Content'),
        ('low_quality', 'Low Quality'),
        ('off_topic', 'Off Topic'),
        ('harassment', 'Harassment'),
        ('copyright', 'Copyright Violation'),
        ('duplicate', 'Duplicate Content'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    
    action_description = TextAreaField('Description', validators=[
        DataRequired(),
        Length(min=10, max=1000)
    ])
    
    severity = SelectField('Severity', choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical')
    ], default='medium')
    
    confidence = FloatField('Confidence', validators=[
        DataRequired(),
        NumberRange(min=0.0, max=1.0)
    ], default=0.8)
    
    # Selected items (hidden field - will be populated by JavaScript)
    selected_items = HiddenField('Selected Items', validators=[DataRequired()])
    
    submit = SubmitField('Apply Bulk Action')


class ModerationSearchForm(FlaskForm):
    """Form for advanced moderation search"""
    
    query = StringField('Search Query', validators=[
        DataRequired(),
        Length(min=2, max=255)
    ])
    
    search_type = SelectField('Search Type', choices=[
        ('content', 'Content'),
        ('user', 'User'),
        ('metadata', 'Metadata'),
        ('all', 'All Fields')
    ], default='all')
    
    content_types = SelectMultipleField('Content Types', choices=[
        ('post', 'Posts'),
        ('comment', 'Comments'),
        ('user_profile', 'User Profiles')
    ])
    
    date_range = SelectField('Date Range', choices=[
        ('', 'Any Time'),
        ('today', 'Today'),
        ('week', 'This Week'),
        ('month', 'This Month'),
        ('year', 'This Year'),
        ('custom', 'Custom Range')
    ], filters=[lambda x: x or None])
    
    date_from = DateTimeField('Date From', format='%Y-%m-%d %H:%M', validators=[Optional()])
    date_to = DateTimeField('Date To', format='%Y-%m-%d %H:%M', validators=[Optional()])
    
    # Advanced filters
    min_spam_score = FloatField('Min Spam Score', validators=[Optional(), NumberRange(min=0.0, max=1.0)])
    max_spam_score = FloatField('Max Spam Score', validators=[Optional(), NumberRange(min=0.0, max=1.0)])
    
    min_quality_score = FloatField('Min Quality Score', validators=[Optional(), NumberRange(min=0.0, max=1.0)])
    max_quality_score = FloatField('Max Quality Score', validators=[Optional(), NumberRange(min=0.0, max=1.0)])
    
    status = SelectMultipleField('Status', choices=[
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('flagged', 'Flagged')
    ])
    
    priority = SelectMultipleField('Priority', choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical')
    ])
    
    # Results settings
    sort_by = SelectField('Sort By', choices=[
        ('relevance', 'Relevance'),
        ('date', 'Date'),
        ('spam_score', 'Spam Score'),
        ('quality_score', 'Quality Score'),
        ('priority', 'Priority')
    ], default='relevance')
    
    sort_order = SelectField('Sort Order', choices=[
        ('desc', 'Descending'),
        ('asc', 'Ascending')
    ], default='desc')
    
    limit = SelectField('Results per page', choices=[
        ('10', '10'),
        ('25', '25'),
        ('50', '50'),
        ('100', '100')
    ], default='25')
    
    submit = SubmitField('Search')
    
    def validate_date_range(self, field):
        """Validate date range"""
        if field.data == 'custom':
            if not self.date_from.data or not self.date_to.data:
                raise ValidationError('Custom date range requires both from and to dates')
            
            if self.date_from.data > self.date_to.data:
                raise ValidationError('Date from must be before date to')


class ContentReviewForm(FlaskForm):
    """Form for manual content review"""
    
    review_decision = SelectField('Review Decision', choices=[
        ('approve', 'Approve'),
        ('reject', 'Reject'),
        ('delete', 'Delete'),
        ('flag', 'Flag'),
        ('edit', 'Edit'),
        ('escalate', 'Escalate')
    ], validators=[DataRequired()])
    
    review_notes = TextAreaField('Review Notes', validators=[
        DataRequired(),
        Length(min=10, max=1000)
    ])
    
    confidence = FloatField('Confidence', validators=[
        DataRequired(),
        NumberRange(min=0.0, max=1.0)
    ], default=0.8)
    
    # Action details
    action_reason = SelectField('Action Reason', choices=[
        ('spam', 'Spam'),
        ('inappropriate', 'Inappropriate Content'),
        ('low_quality', 'Low Quality'),
        ('off_topic', 'Off Topic'),
        ('harassment', 'Harassment'),
        ('copyright', 'Copyright Violation'),
        ('duplicate', 'Duplicate Content'),
        ('false_positive', 'False Positive'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    
    # Appeal settings
    allow_appeal = BooleanField('Allow Appeal', default=True)
    appeal_deadline_days = IntegerField('Appeal Deadline (days)', validators=[
        Optional(),
        NumberRange(min=1, max=365)
    ], default=7)
    
    # Content edits (if edit action)
    edited_content = TextAreaField('Edited Content', validators=[Optional(), Length(max=10000)])
    
    # Target information
    queue_id = HiddenField('Queue ID', validators=[DataRequired()])
    
    submit = SubmitField('Submit Review')
    
    def validate_edited_content(self, field):
        """Validate edited content"""
        if self.review_decision.data == 'edit' and not field.data:
            raise ValidationError('Edited content is required for edit action')


class ModerationReportForm(FlaskForm):
    """Form for moderation reporting"""
    
    report_type = SelectField('Report Type', choices=[
        ('daily', 'Daily Report'),
        ('weekly', 'Weekly Report'),
        ('monthly', 'Monthly Report'),
        ('custom', 'Custom Range')
    ], validators=[DataRequired()])
    
    date_from = DateTimeField('Date From', format='%Y-%m-%d', validators=[Optional()])
    date_to = DateTimeField('Date To', format='%Y-%m-%d', validators=[Optional()])
    
    # Report content
    include_queue_stats = BooleanField('Include Queue Statistics', default=True)
    include_action_stats = BooleanField('Include Action Statistics', default=True)
    include_performance_stats = BooleanField('Include Performance Statistics', default=True)
    include_quality_trends = BooleanField('Include Quality Trends', default=True)
    include_spam_trends = BooleanField('Include Spam Trends', default=True)
    
    # Export format
    export_format = SelectField('Export Format', choices=[
        ('html', 'HTML Report'),
        ('pdf', 'PDF Report'),
        ('csv', 'CSV Data'),
        ('json', 'JSON Data')
    ], default='html')
    
    # Email options
    send_email = BooleanField('Send via Email', default=False)
    email_recipients = StringField('Email Recipients', validators=[Optional(), Length(max=500)])
    
    submit = SubmitField('Generate Report')
    
    def validate_date_range(self, field):
        """Validate date range"""
        if self.report_type.data == 'custom':
            if not self.date_from.data or not self.date_to.data:
                raise ValidationError('Custom report requires both from and to dates')
            
            if self.date_from.data > self.date_to.data:
                raise ValidationError('Date from must be before date to')
    
    def validate_email_recipients(self, field):
        """Validate email recipients"""
        if self.send_email.data and not field.data:
            raise ValidationError('Email recipients are required when sending via email')


class ModerationQueueFilterForm(FlaskForm):
    """Form for filtering moderation queue items"""
    
    # Basic filters
    status = SelectField('Status', choices=[
        ('', 'All Status'),
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('flagged', 'Flagged'),
        ('auto_approved', 'Auto Approved'),
        ('auto_rejected', 'Auto Rejected')
    ], filters=[lambda x: x or None])
    
    priority = SelectField('Priority', choices=[
        ('', 'All Priorities'),
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical')
    ], filters=[lambda x: x or None])
    
    content_type = SelectField('Content Type', choices=[
        ('', 'All Types'),
        ('post', 'Posts'),
        ('comment', 'Comments'),
        ('user_profile', 'User Profiles'),
        ('message', 'Messages'),
        ('file', 'Files')
    ], filters=[lambda x: x or None])
    
    # Content analysis filters
    spam_score_min = FloatField('Min Spam Score', validators=[Optional(), NumberRange(min=0, max=1)])
    spam_score_max = FloatField('Max Spam Score', validators=[Optional(), NumberRange(min=0, max=1)])
    quality_score_min = FloatField('Min Quality Score', validators=[Optional(), NumberRange(min=0, max=1)])
    quality_score_max = FloatField('Max Quality Score', validators=[Optional(), NumberRange(min=0, max=1)])
    
    # Date range filters
    date_from = DateTimeField('Date From', format='%Y-%m-%d %H:%M', validators=[Optional()])
    date_to = DateTimeField('Date To', format='%Y-%m-%d %H:%M', validators=[Optional()])
    
    # User filters
    user_id = IntegerField('User ID', validators=[Optional()])
    reviewer_id = IntegerField('Reviewer ID', validators=[Optional()])
    
    # Text search
    content_search = StringField('Content Search', validators=[Optional(), Length(max=200)])
    
    # Action filters
    requires_review = BooleanField('Requires Review', default=False)
    auto_processed = BooleanField('Auto Processed', default=False)
    has_appeal = BooleanField('Has Appeal', default=False)
    
    # Sorting options
    sort_by = SelectField('Sort By', choices=[
        ('created_at', 'Created Date'),
        ('updated_at', 'Updated Date'),
        ('priority', 'Priority'),
        ('spam_score', 'Spam Score'),
        ('quality_score', 'Quality Score'),
        ('content_type', 'Content Type')
    ], default='created_at')
    
    sort_order = SelectField('Sort Order', choices=[
        ('desc', 'Descending'),
        ('asc', 'Ascending')
    ], default='desc')
    
    # Pagination
    per_page = SelectField('Per Page', choices=[
        ('10', '10'),
        ('25', '25'),
        ('50', '50'),
        ('100', '100')
    ], default='25')
    
    # Action buttons
    apply_filter = SubmitField('Apply Filter')
    reset_filter = SubmitField('Reset')
    
    def validate_date_range(self, field):
        """Validate date range"""
        if self.date_from.data and self.date_to.data:
            if self.date_from.data > self.date_to.data:
                raise ValidationError('Date from must be before date to')
    
    def validate_score_range(self, field):
        """Validate score ranges"""
        if self.spam_score_min.data and self.spam_score_max.data:
            if self.spam_score_min.data > self.spam_score_max.data:
                raise ValidationError('Min spam score must be less than max spam score')
        
        if self.quality_score_min.data and self.quality_score_max.data:
            if self.quality_score_min.data > self.quality_score_max.data:
                raise ValidationError('Min quality score must be less than max quality score')
    
    def get_filter_params(self):
        """Get filter parameters as dictionary"""
        params = {}
        
        # Add non-empty filters
        if self.status.data:
            params['status'] = self.status.data
        
        if self.priority.data:
            params['priority'] = self.priority.data
        
        if self.content_type.data:
            params['content_type'] = self.content_type.data
        
        if self.spam_score_min.data is not None:
            params['spam_score_min'] = self.spam_score_min.data
        
        if self.spam_score_max.data is not None:
            params['spam_score_max'] = self.spam_score_max.data
        
        if self.quality_score_min.data is not None:
            params['quality_score_min'] = self.quality_score_min.data
        
        if self.quality_score_max.data is not None:
            params['quality_score_max'] = self.quality_score_max.data
        
        if self.date_from.data:
            params['date_from'] = self.date_from.data
        
        if self.date_to.data:
            params['date_to'] = self.date_to.data
        
        if self.user_id.data:
            params['user_id'] = self.user_id.data
        
        if self.reviewer_id.data:
            params['reviewer_id'] = self.reviewer_id.data
        
        if self.content_search.data:
            params['content_search'] = self.content_search.data
        
        if self.requires_review.data:
            params['requires_review'] = self.requires_review.data
        
        if self.auto_processed.data:
            params['auto_processed'] = self.auto_processed.data
        
        if self.has_appeal.data:
            params['has_appeal'] = self.has_appeal.data
        
        # Sorting
        params['sort_by'] = self.sort_by.data
        params['sort_order'] = self.sort_order.data
        params['per_page'] = int(self.per_page.data)
        
        return params
    
    def reset_form_data(self):
        """Reset form to default values"""
        self.status.data = ''
        self.priority.data = ''
        self.content_type.data = ''
        self.spam_score_min.data = None
        self.spam_score_max.data = None
        self.quality_score_min.data = None
        self.quality_score_max.data = None
        self.date_from.data = None
        self.date_to.data = None
        self.user_id.data = None
        self.reviewer_id.data = None
        self.content_search.data = ''
        self.requires_review.data = False
        self.auto_processed.data = False
        self.has_appeal.data = False
        self.sort_by.data = 'created_at'
        self.sort_order.data = 'desc'
        self.per_page.data = '25'
