"""
Reputation and Voting Forms

This module defines the Flask-WTF forms for the enhanced voting and reputation system,
including voting forms, reputation filtering, and analytics forms.
"""

from flask_wtf import FlaskForm
from wtforms import (
    StringField, TextAreaField, SelectField, IntegerField, FloatField,
    BooleanField, DateField, DateTimeField, HiddenField, SubmitField,
    FieldList, FormField
)
from wtforms.validators import (
    DataRequired, Length, NumberRange, Optional, Regexp, Email,
    ValidationError
)
from wtforms.widgets import TextArea, TextInput
from flask import request

class VotingForm(FlaskForm):
    """Basic voting form"""
    vote_type = SelectField('Vote Type', choices=[
        ('upvote', 'Upvote'),
        ('downvote', 'Downvote')
    ], validators=[DataRequired()])
    
    target_type = HiddenField(validators=[DataRequired()])
    target_id = HiddenField(validators=[DataRequired(), NumberRange(min=1)])
    
    submit = SubmitField('Vote')

class ReasonVotingForm(FlaskForm):
    """Voting form with reason and category"""
    vote_type = SelectField('Vote Type', choices=[
        ('upvote', 'Upvote'),
        ('downvote', 'Downvote')
    ], validators=[DataRequired()])
    
    reason_category = SelectField('Reason Category', choices=[
        ('', '-- Select Reason --'),
        ('helpful', 'Helpful'),
        ('informative', 'Informative'),
        ('well_written', 'Well Written'),
        ('accurate', 'Accurate'),
        ('comprehensive', 'Comprehensive'),
        ('controversial', 'Controversial'),
        ('offensive', 'Offensive'),
        ('spam', 'Spam'),
        ('duplicate', 'Duplicate'),
        ('off_topic', 'Off Topic'),
        ('unclear', 'Unclear'),
        ('incomplete', 'Incomplete'),
        ('outdated', 'Outdated'),
        ('biased', 'Biased'),
        ('low_quality', 'Low Quality')
    ], validators=[Optional()])
    
    reason = TextAreaField('Reason', validators=[
        Optional(),
        Length(min=10, max=500, message='Reason must be between 10 and 500 characters')
    ], render_kw={'placeholder': 'Please provide a reason for your vote (optional but recommended)', 'rows': 3})
    
    target_type = HiddenField(validators=[DataRequired()])
    target_id = HiddenField(validators=[DataRequired(), NumberRange(min=1)])
    
    submit = SubmitField('Vote')
    
    def validate_reason(self, field):
        """Validate reason field"""
        if self.reason_category.data and not field.data:
            raise ValidationError('Please provide a reason when selecting a category.')

class ReputationFilterForm(FlaskForm):
    """Form for filtering reputation data"""
    user_id = IntegerField('User ID', validators=[Optional(), NumberRange(min=1)])
    username = StringField('Username', validators=[Optional(), Length(min=2, max=50)])
    
    min_reputation = IntegerField('Min Reputation', validators=[Optional(), NumberRange(min=-1000)])
    max_reputation = IntegerField('Max Reputation', validators=[Optional(), NumberRange(max=10000)])
    
    min_voting_power = FloatField('Min Voting Power', validators=[Optional(), NumberRange(min=0.1, max=10.0)])
    max_voting_power = FloatField('Max Voting Power', validators=[Optional(), NumberRange(min=0.1, max=10.0)])
    
    reputation_level = SelectField('Reputation Level', choices=[
        ('', '-- All Levels --'),
        ('Newcomer', 'Newcomer'),
        ('Member', 'Member'),
        ('Trusted', 'Trusted'),
        ('Expert', 'Expert'),
        ('Master', 'Master'),
        ('Legend', 'Legend')
    ], validators=[Optional()])
    
    min_votes_cast = IntegerField('Min Votes Cast', validators=[Optional(), NumberRange(min=0)])
    max_votes_cast = IntegerField('Max Votes Cast', validators=[Optional(), NumberRange(min=0)])
    
    min_posts_created = IntegerField('Min Posts Created', validators=[Optional(), NumberRange(min=0)])
    max_posts_created = IntegerField('Max Posts Created', validators=[Optional(), NumberRange(min=0)])
    
    sort_by = SelectField('Sort By', choices=[
        ('reputation_score', 'Reputation Score'),
        ('voting_power', 'Voting Power'),
        ('trust_score', 'Trust Score'),
        ('total_votes_cast', 'Total Votes Cast'),
        ('posts_created', 'Posts Created'),
        ('comments_created', 'Comments Created'),
        ('current_streak', 'Current Streak'),
        ('created_at', 'Created At'),
        ('updated_at', 'Last Updated')
    ], default='reputation_score')
    
    sort_order = SelectField('Sort Order', choices=[
        ('desc', 'Descending'),
        ('asc', 'Ascending')
    ], default='desc')
    
    limit = IntegerField('Results per page', default=50, validators=[NumberRange(min=10, max=100)])
    
    submit = SubmitField('Filter')

class VotingAnalyticsForm(FlaskForm):
    """Form for voting analytics"""
    user_id = IntegerField('User ID', validators=[Optional(), NumberRange(min=1)])
    username = StringField('Username', validators=[Optional(), Length(min=2, max=50)])
    
    date_range = SelectField('Date Range', choices=[
        ('7', 'Last 7 Days'),
        ('30', 'Last 30 Days'),
        ('90', 'Last 90 Days'),
        ('365', 'Last Year'),
        ('custom', 'Custom Range')
    ], default='30')
    
    start_date = DateField('Start Date', validators=[Optional()])
    end_date = DateField('End Date', validators=[Optional()])
    
    vote_type = SelectField('Vote Type', choices=[
        ('', 'All Votes'),
        ('upvote', 'Upvotes Only'),
        ('downvote', 'Downvotes Only')
    ], validators=[Optional()])
    
    target_type = SelectField('Target Type', choices=[
        ('', 'All Targets'),
        ('post', 'Posts Only'),
        ('comment', 'Comments Only')
    ], validators=[Optional()])
    
    reason_category = SelectField('Reason Category', choices=[
        ('', 'All Categories'),
        ('helpful', 'Helpful'),
        ('informative', 'Informative'),
        ('well_written', 'Well Written'),
        ('accurate', 'Accurate'),
        ('comprehensive', 'Comprehensive'),
        ('controversial', 'Controversial'),
        ('offensive', 'Offensive'),
        ('spam', 'Spam'),
        ('duplicate', 'Duplicate'),
        ('off_topic', 'Off Topic'),
        ('unclear', 'Unclear'),
        ('incomplete', 'Incomplete'),
        ('outdated', 'Outdated'),
        ('biased', 'Biased'),
        ('low_quality', 'Low Quality')
    ], validators=[Optional()])
    
    include_patterns = BooleanField('Include Voting Patterns', default=True)
    
    submit = SubmitField('Analyze')
    
    def validate(self):
        """Custom validation for date range"""
        if not super().validate():
            return False
        
        if self.date_range.data == 'custom':
            if not self.start_date.data or not self.end_date.data:
                self.start_date.errors.append('Both start and end dates are required for custom range')
                return False
            
            if self.start_date.data > self.end_date.data:
                self.start_date.errors.append('Start date must be before end date')
                return False
        
        return True

class ReputationLevelForm(FlaskForm):
    """Form for managing reputation levels"""
    level_name = StringField('Level Name', validators=[
        DataRequired(),
        Length(min=2, max=50),
        Regexp(r'^[A-Za-z\s]+$', message='Level name must contain only letters and spaces')
    ])
    
    level_order = IntegerField('Level Order', validators=[
        DataRequired(),
        NumberRange(min=0, max=10)
    ])
    
    min_reputation = IntegerField('Min Reputation', validators=[
        DataRequired(),
        NumberRange(min=0)
    ])
    
    max_reputation = IntegerField('Max Reputation', validators=[
        DataRequired(),
        NumberRange(min=1)
    ])
    
    voting_power_multiplier = FloatField('Voting Power Multiplier', validators=[
        DataRequired(),
        NumberRange(min=0.1, max=10.0)
    ], default=1.0)
    
    daily_vote_limit = IntegerField('Daily Vote Limit', validators=[
        DataRequired(),
        NumberRange(min=1, max=1000)
    ], default=10)
    
    badge_color = SelectField('Badge Color', choices=[
        ('primary', 'Primary Blue'),
        ('secondary', 'Secondary Gray'),
        ('success', 'Success Green'),
        ('danger', 'Danger Red'),
        ('warning', 'Warning Yellow'),
        ('info', 'Info Cyan'),
        ('light', 'Light'),
        ('dark', 'Dark')
    ], default='secondary')
    
    badge_icon = StringField('Badge Icon', validators=[
        Optional(),
        Length(max=50)
    ], render_kw={'placeholder': 'fa-star (Font Awesome icon class)'})
    
    description = TextAreaField('Description', validators=[
        Optional(),
        Length(max=500)
    ], render_kw={'rows': 3})
    
    special_permissions = TextAreaField('Special Permissions', validators=[
        Optional()
    ], render_kw={'placeholder': 'JSON format: {"can_moderate": true, "can_edit_wiki": false}', 'rows': 2})
    
    is_active = BooleanField('Active', default=True)
    
    submit = SubmitField('Save Level')
    
    def validate_max_reputation(self, field):
        """Validate max reputation is greater than min reputation"""
        if field.data <= self.min_reputation.data:
            raise ValidationError('Max reputation must be greater than min reputation')
    
    def validate_special_permissions(self, field):
        """Validate special permissions JSON format"""
        if field.data:
            try:
                import json
                json.loads(field.data)
            except json.JSONDecodeError:
                raise ValidationError('Special permissions must be valid JSON')

class ReputationAdjustmentForm(FlaskForm):
    """Form for manual reputation adjustments"""
    user_id = IntegerField('User ID', validators=[DataRequired(), NumberRange(min=1)])
    
    adjustment_type = SelectField('Adjustment Type', choices=[
        ('add', 'Add Points'),
        ('subtract', 'Subtract Points'),
        ('set', 'Set Points'),
        ('multiply', 'Multiply Points')
    ], validators=[DataRequired()])
    
    adjustment_value = FloatField('Adjustment Value', validators=[DataRequired()])
    
    reason = TextAreaField('Reason', validators=[
        DataRequired(),
        Length(min=10, max=500)
    ], render_kw={'rows': 3})
    
    is_penalty = BooleanField('This is a penalty', default=False)
    
    notify_user = BooleanField('Notify user', default=True)
    
    submit = SubmitField('Adjust Reputation')

class BulkReputationAdjustmentForm(FlaskForm):
    """Form for bulk reputation adjustments"""
    adjustment_type = SelectField('Adjustment Type', choices=[
        ('add', 'Add Points'),
        ('subtract', 'Subtract Points'),
        ('multiply', 'Multiply Points')
    ], validators=[DataRequired()])
    
    adjustment_value = FloatField('Adjustment Value', validators=[DataRequired()])
    
    target_criteria = SelectField('Target Criteria', choices=[
        ('all', 'All Users'),
        ('level', 'By Reputation Level'),
        ('min_reputation', 'Minimum Reputation'),
        ('max_reputation', 'Maximum Reputation'),
        ('inactive', 'Inactive Users'),
        ('new_users', 'New Users (joined in last 30 days)')
    ], validators=[DataRequired()])
    
    reputation_level = SelectField('Reputation Level', choices=[
        ('Newcomer', 'Newcomer'),
        ('Member', 'Member'),
        ('Trusted', 'Trusted'),
        ('Expert', 'Expert'),
        ('Master', 'Master'),
        ('Legend', 'Legend')
    ], validators=[Optional()])
    
    min_reputation = IntegerField('Minimum Reputation', validators=[Optional(), NumberRange(min=-1000)])
    max_reputation = IntegerField('Maximum Reputation', validators=[Optional(), NumberRange(max=10000)])
    
    inactive_days = IntegerField('Inactive for (days)', default=90, validators=[NumberRange(min=1)])
    
    reason = TextAreaField('Reason', validators=[
        DataRequired(),
        Length(min=10, max=500)
    ], render_kw={'rows': 3})
    
    is_penalty = BooleanField('This is a penalty', default=False)
    
    notify_users = BooleanField('Notify users', default=True)
    
    submit = SubmitField('Bulk Adjust')

class VotingPatternAnalysisForm(FlaskForm):
    """Form for voting pattern analysis"""
    user_id = IntegerField('User ID', validators=[Optional(), NumberRange(min=1)])
    username = StringField('Username', validators=[Optional(), Length(min=2, max=50)])
    
    analysis_type = SelectField('Analysis Type', choices=[
        ('consistency', 'Consistency Analysis'),
        ('bias', 'Bias Analysis'),
        ('timing', 'Timing Analysis'),
        ('quality', 'Quality Analysis'),
        ('all', 'All Patterns')
    ], default='all')
    
    sample_size = IntegerField('Sample Size (votes)', default=100, validators=[NumberRange(min=20, max=1000)])
    
    confidence_threshold = FloatField('Confidence Threshold', default=0.8, validators=[NumberRange(min=0.1, max=1.0)])
    
    include_recommendations = BooleanField('Include Recommendations', default=True)
    
    submit = SubmitField('Analyze Patterns')

class ReputationHistoryForm(FlaskForm):
    """Form for viewing reputation history"""
    user_id = IntegerField('User ID', validators=[Optional(), NumberRange(min=1)])
    username = StringField('Username', validators=[Optional(), Length(min=2, max=50)])
    
    date_range = SelectField('Date Range', choices=[
        ('7', 'Last 7 Days'),
        ('30', 'Last 30 Days'),
        ('90', 'Last 90 Days'),
        ('365', 'Last Year'),
        ('all', 'All Time')
    ], default='30')
    
    event_type = SelectField('Event Type', choices=[
        ('', 'All Events'),
        ('vote_received', 'Votes Received'),
        ('vote_cast', 'Votes Cast'),
        ('level_change', 'Level Changes'),
        ('adjustment', 'Manual Adjustments'),
        ('streak', 'Streak Events'),
        ('penalty', 'Penalties'),
        ('bonus', 'Bonuses')
    ], validators=[Optional()])
    
    include_details = BooleanField('Include Details', default=True)
    
    submit = SubmitField('View History')

class ReputationLeaderboardForm(FlaskForm):
    """Form for reputation leaderboard"""
    leaderboard_type = SelectField('Leaderboard Type', choices=[
        ('reputation', 'Top Reputation'),
        ('voting_power', 'Highest Voting Power'),
        ('trust_score', 'Highest Trust Score'),
        ('most_votes', 'Most Votes Cast'),
        ('most_posts', 'Most Posts Created'),
        ('longest_streak', 'Longest Activity Streak'),
        ('most_helpful', 'Most Helpful Votes'),
        ('most_quality', 'Highest Quality Score')
    ], default='reputation')
    
    time_period = SelectField('Time Period', choices=[
        ('current', 'Current'),
        ('weekly', 'This Week'),
        ('monthly', 'This Month'),
        ('quarterly', 'This Quarter'),
        ('yearly', 'This Year')
    ], default='current')
    
    limit = IntegerField('Results', default=50, validators=[NumberRange(min=10, max=100)])
    
    include_anonymous = BooleanField('Include Anonymous Users', default=False)
    
    submit = SubmitField('View Leaderboard')

class CustomReasonCategoryForm(FlaskForm):
    """Form for adding custom reason categories"""
    category_name = StringField('Category Name', validators=[
        DataRequired(),
        Length(min=2, max=50),
        Regexp(r'^[a-z_]+$', message='Category name must contain only lowercase letters and underscores')
    ])
    
    display_name = StringField('Display Name', validators=[
        DataRequired(),
        Length(min=2, max=50)
    ])
    
    description = TextAreaField('Description', validators=[
        Optional(),
        Length(max=200)
    ], render_kw={'rows': 2})
    
    color = SelectField('Color', choices=[
        ('primary', 'Primary'),
        ('secondary', 'Secondary'),
        ('success', 'Success'),
        ('danger', 'Danger'),
        ('warning', 'Warning'),
        ('info', 'Info')
    ], default='secondary')
    
    is_positive = BooleanField('Positive Category', default=True)
    
    submit = SubmitField('Add Category')

class VotingSettingsForm(FlaskForm):
    """Form for user voting settings"""
    show_voting_reasons = BooleanField('Show voting reasons', default=True)
    require_voting_reasons = BooleanField('Require voting reasons for downvotes', default=False)
    
    default_reason_category = SelectField('Default reason category', choices=[
        ('', '-- Select Default --'),
        ('helpful', 'Helpful'),
        ('informative', 'Informative'),
        ('well_written', 'Well Written'),
        ('accurate', 'Accurate'),
        ('comprehensive', 'Comprehensive')
    ], validators=[Optional()])
    
    enable_voting_analytics = BooleanField('Enable voting analytics', default=True)
    show_voting_power = BooleanField('Show voting power', default=True)
    
    vote_notifications = SelectField('Vote notifications', choices=[
        ('all', 'All votes'),
        ('upvotes', 'Upvotes only'),
        ('downvotes', 'Downvotes only'),
        ('none', 'No notifications')
    ], default='upvotes')
    
    auto_analyze_patterns = BooleanField('Auto-analyze voting patterns', default=True)
    
    submit = SubmitField('Save Settings')
