"""
Advanced User Analytics Forms

This module contains forms for user analytics including:
- User behavior analytics forms
- Engagement metrics forms
- User performance dashboard forms
- Predictive analytics forms
- User segmentation forms
"""

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SelectField, SubmitField, IntegerField, FloatField, DateField, HiddenField
from wtforms.validators import DataRequired, Length, Optional, NumberRange
from app.models import User


class AnalyticsDateRangeForm(FlaskForm):
    """Form for analytics date range selection"""
    start_date = DateField('Start Date', validators=[Optional()])
    end_date = DateField('End Date', validators=[Optional()])
    period = SelectField('Period', choices=[
        ('7', 'Last 7 Days'),
        ('30', 'Last 30 Days'),
        ('90', 'Last 90 Days'),
        ('365', 'Last Year'),
        ('custom', 'Custom Range')
    ], validators=[DataRequired()])
    
    submit = SubmitField('Apply Filter')


class UserBehaviorFilterForm(FlaskForm):
    """Form for filtering user behavior analytics"""
    behavior_type = SelectField('Behavior Type', choices=[
        ('all', 'All Behaviors'),
        ('login', 'Logins'),
        ('post', 'Posts'),
        ('comment', 'Comments'),
        ('like', 'Likes'),
        ('share', 'Shares'),
        ('view', 'Views')
    ], validators=[DataRequired()])
    
    target_type = SelectField('Target Type', choices=[
        ('all', 'All Targets'),
        ('post', 'Posts'),
        ('comment', 'Comments'),
        ('user', 'Users'),
        ('profile', 'Profiles')
    ], validators=[DataRequired()])
    
    action = StringField('Action Filter', validators=[Optional(), Length(max=100)])
    session_id = StringField('Session ID', validators=[Optional(), Length(max=255)])
    
    submit = SubmitField('Filter Behaviors')


class EngagementMetricsForm(FlaskForm):
    """Form for engagement metrics configuration"""
    metric_type = SelectField('Metric Type', choices=[
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly')
    ], validators=[DataRequired()])
    
    include_metrics = SelectField('Include Metrics', choices=[
        ('all', 'All Metrics'),
        ('actions', 'Actions Only'),
        ('engagement', 'Engagement Only'),
        ('sessions', 'Sessions Only')
    ], validators=[DataRequired()])
    
    compare_period = BooleanField('Compare with Previous Period')
    export_format = SelectField('Export Format', choices=[
        ('none', 'No Export'),
        ('csv', 'CSV'),
        ('json', 'JSON'),
        ('pdf', 'PDF')
    ], validators=[DataRequired()])
    
    submit = SubmitField('Generate Report')


class PerformanceMetricsForm(FlaskForm):
    """Form for performance metrics configuration"""
    metric_category = SelectField('Metric Category', choices=[
        ('all', 'All Metrics'),
        ('content', 'Content Metrics'),
        ('engagement', 'Engagement Metrics'),
        ('growth', 'Growth Metrics'),
        ('activity', 'Activity Metrics')
    ], validators=[DataRequired()])
    
    period = SelectField('Period', choices=[
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly')
    ], validators=[DataRequired()])
    
    show_trends = BooleanField('Show Trends')
    show_comparisons = BooleanField('Show Comparisons')
    show_predictions = BooleanField('Show Predictions')
    
    submit = SubmitField('Generate Metrics')


class UserSegmentForm(FlaskForm):
    """Form for creating user segments"""
    name = StringField('Segment Name', validators=[DataRequired(), Length(min=2, max=100)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=500)])
    segment_type = SelectField('Segment Type', choices=[
        ('activity', 'Activity Based'),
        ('engagement', 'Engagement Based'),
        ('behavior', 'Behavior Based'),
        ('demographic', 'Demographic Based'),
        ('custom', 'Custom Criteria')
    ], validators=[DataRequired()])
    
    # Activity criteria
    min_posts = IntegerField('Minimum Posts', validators=[Optional(), NumberRange(min=0)])
    max_posts = IntegerField('Maximum Posts', validators=[Optional(), NumberRange(min=0)])
    min_comments = IntegerField('Minimum Comments', validators=[Optional(), NumberRange(min=0)])
    max_comments = IntegerField('Maximum Comments', validators=[Optional(), NumberRange(min=0)])
    
    # Engagement criteria
    min_engagement_score = FloatField('Minimum Engagement Score', validators=[Optional(), NumberRange(min=0)])
    max_engagement_score = FloatField('Maximum Engagement Score', validators=[Optional(), NumberRange(min=0)])
    min_session_duration = IntegerField('Minimum Session Duration (seconds)', validators=[Optional(), NumberRange(min=0)])
    
    # Behavior criteria
    login_frequency = SelectField('Login Frequency', choices=[
        ('any', 'Any'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly')
    ], validators=[DataRequired()])
    
    last_login_days = IntegerField('Last Login Within Days', validators=[Optional(), NumberRange(min=1)])
    
    submit = SubmitField('Create Segment')


class EditUserSegmentForm(FlaskForm):
    """Form for editing user segments"""
    name = StringField('Segment Name', validators=[DataRequired(), Length(min=2, max=100)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=500)])
    is_active = BooleanField('Active Segment')
    
    submit = SubmitField('Update Segment')


class PredictionConfigForm(FlaskForm):
    """Form for prediction configuration"""
    prediction_type = SelectField('Prediction Type', choices=[
        ('churn', 'Churn Risk'),
        ('engagement', 'Engagement Level'),
        ('growth', 'Growth Potential'),
        ('activity', 'Activity Level'),
        ('retention', 'Retention Probability')
    ], validators=[DataRequired()])
    
    prediction_period = SelectField('Prediction Period', choices=[
        ('7', '7 Days'),
        ('30', '30 Days'),
        ('90', '90 Days'),
        ('180', '180 Days')
    ], validators=[DataRequired()])
    
    confidence_threshold = FloatField('Confidence Threshold', validators=[
        DataRequired(), NumberRange(min=0.0, max=1.0)
    ])
    
    include_factors = SelectField('Include Factors', choices=[
        ('all', 'All Factors'),
        ('behavior', 'Behavior Only'),
        ('engagement', 'Engagement Only'),
        ('demographic', 'Demographic Only'),
        ('custom', 'Custom Factors')
    ], validators=[DataRequired()])
    
    submit = SubmitField('Generate Predictions')


class UserSearchForm(FlaskForm):
    """Form for searching users in analytics"""
    search_term = StringField('Search Users', validators=[Optional(), Length(max=100)])
    search_type = SelectField('Search Type', choices=[
        ('username', 'Username'),
        ('email', 'Email'),
        ('activity', 'Activity Level'),
        ('engagement', 'Engagement Level'),
        ('segment', 'User Segment')
    ], validators=[DataRequired()])
    
    segment_filter = SelectField('Filter by Segment', choices=[
        ('all', 'All Users'),
        ('high_engagement', 'High Engagement'),
        ('low_engagement', 'Low Engagement'),
        ('inactive', 'Inactive Users'),
        ('new_users', 'New Users')
    ], validators=[DataRequired()])
    
    submit = SubmitField('Search Users')


class DashboardConfigForm(FlaskForm):
    """Form for dashboard configuration"""
    name = StringField('Dashboard Name', validators=[DataRequired(), Length(min=2, max=100)])
    dashboard_type = SelectField('Dashboard Type', choices=[
        ('overview', 'Overview'),
        ('activity', 'Activity'),
        ('engagement', 'Engagement'),
        ('performance', 'Performance'),
        ('custom', 'Custom')
    ], validators=[DataRequired()])
    
    layout_columns = SelectField('Layout Columns', choices=[
        ('1', 'Single Column'),
        ('2', 'Two Columns'),
        ('3', 'Three Columns'),
        ('4', 'Four Columns')
    ], validators=[DataRequired()])
    
    auto_refresh = BooleanField('Auto Refresh')
    refresh_interval = SelectField('Refresh Interval', choices=[
        ('30', '30 Seconds'),
        ('60', '1 Minute'),
        ('300', '5 Minutes'),
        ('900', '15 Minutes')
    ], validators=[DataRequired()])
    
    is_public = BooleanField('Public Dashboard')
    is_default = BooleanField('Set as Default')
    
    submit = SubmitField('Save Dashboard')


class WidgetConfigForm(FlaskForm):
    """Form for widget configuration"""
    widget_id = HiddenField('Widget ID', validators=[DataRequired()])
    widget_type = SelectField('Widget Type', choices=[
        ('stats', 'Statistics'),
        ('chart', 'Chart'),
        ('table', 'Table'),
        ('list', 'List'),
        ('gauge', 'Gauge'),
        ('metric', 'Metric Card')
    ], validators=[DataRequired()])
    
    title = StringField('Widget Title', validators=[Optional(), Length(max=100)])
    data_source = SelectField('Data Source', choices=[
        ('user_behaviors', 'User Behaviors'),
        ('user_engagement', 'User Engagement'),
        ('user_performance', 'User Performance'),
        ('user_predictions', 'User Predictions')
    ], validators=[DataRequired()])
    
    chart_type = SelectField('Chart Type', choices=[
        ('line', 'Line Chart'),
        ('bar', 'Bar Chart'),
        ('pie', 'Pie Chart'),
        ('area', 'Area Chart'),
        ('scatter', 'Scatter Plot')
    ], validators=[DataRequired()])
    
    limit = IntegerField('Data Limit', validators=[Optional(), NumberRange(min=1, max=1000)])
    
    submit = SubmitField('Update Widget')


class AnalyticsExportForm(FlaskForm):
    """Form for analytics data export"""
    export_type = SelectField('Export Type', choices=[
        ('behaviors', 'User Behaviors'),
        ('engagement', 'Engagement Metrics'),
        ('performance', 'Performance Metrics'),
        ('predictions', 'Predictions'),
        ('segments', 'User Segments')
    ], validators=[DataRequired()])
    
    export_format = SelectField('Export Format', choices=[
        ('csv', 'CSV'),
        ('json', 'JSON'),
        ('xlsx', 'Excel'),
        ('pdf', 'PDF Report')
    ], validators=[DataRequired()])
    
    date_range = SelectField('Date Range', choices=[
        ('7', 'Last 7 Days'),
        ('30', 'Last 30 Days'),
        ('90', 'Last 90 Days'),
        ('365', 'Last Year'),
        ('all', 'All Time')
    ], validators=[DataRequired()])
    
    include_headers = BooleanField('Include Headers')
    include_metadata = BooleanField('Include Metadata')
    
    submit = SubmitField('Export Data')


class AnalyticsSettingsForm(FlaskForm):
    """Form for analytics settings"""
    track_behaviors = BooleanField('Track User Behaviors')
    track_engagement = BooleanField('Track Engagement Metrics')
    track_sessions = BooleanField('Track Session Data')
    enable_predictions = BooleanField('Enable Predictive Analytics')
    
    data_retention_days = IntegerField('Data Retention Days', validators=[
        Optional(), NumberRange(min=30, max=3650)
    ])
    
    aggregation_frequency = SelectField('Aggregation Frequency', choices=[
        ('realtime', 'Real-time'),
        ('hourly', 'Hourly'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly')
    ], validators=[DataRequired()])
    
    enable_anonymous_tracking = BooleanField('Enable Anonymous Tracking')
    enable_ip_tracking = BooleanField('Enable IP Tracking')
    
    submit = SubmitField('Save Settings')


class ComparisonForm(FlaskForm):
    """Form for comparing analytics data"""
    comparison_type = SelectField('Comparison Type', choices=[
        ('users', 'User Comparison'),
        ('periods', 'Period Comparison'),
        ('segments', 'Segment Comparison')
    ], validators=[DataRequired()])
    
    primary_user = StringField('Primary User', validators=[Optional(), Length(max=100)])
    comparison_users = StringField('Comparison Users', validators=[Optional(), Length(max=500)])
    
    primary_period = SelectField('Primary Period', choices=[
        ('7', 'Last 7 Days'),
        ('30', 'Last 30 Days'),
        ('90', 'Last 90 Days')
    ], validators=[DataRequired()])
    
    comparison_period = SelectField('Comparison Period', choices=[
        ('7', 'Last 7 Days'),
        ('30', 'Last 30 Days'),
        ('90', 'Last 90 Days')
    ], validators=[DataRequired()])
    
    metrics = SelectField('Metrics to Compare', choices=[
        ('all', 'All Metrics'),
        ('engagement', 'Engagement Only'),
        ('activity', 'Activity Only'),
        ('growth', 'Growth Only')
    ], validators=[DataRequired()])
    
    submit = SubmitField('Compare')
