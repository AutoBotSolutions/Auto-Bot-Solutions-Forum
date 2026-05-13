"""
Advanced Analytics Forms

This module contains Flask-WTF forms for the Advanced Analytics Dashboard,
including filters for analytics data, user behavior analysis, content performance,
system metrics, trend analysis, and predictive model management.
"""

from datetime import datetime, timedelta
from flask_wtf import FlaskForm
from wtforms import (
    StringField, TextAreaField, SelectField, IntegerField, FloatField,
    BooleanField, DateField, DateTimeField, HiddenField, FieldList,
    FormField, SelectMultipleField
)
from wtforms.validators import (
    DataRequired, Optional, NumberRange, Length, Email, URL,
    ValidationError, Regexp
)
from wtforms.widgets import TextArea, TextInput
from flask import current_app

class AnalyticsFilterForm(FlaskForm):
    """Base form for filtering analytics data"""
    
    # Date range filters
    start_date = DateField('Start Date', validators=[Optional()], default=datetime.utcnow().date() - timedelta(days=30))
    end_date = DateField('End Date', validators=[Optional()], default=datetime.utcnow().date())
    
    # Time period presets
    period_preset = SelectField('Time Period', choices=[
        ('', 'Custom Range'),
        ('today', 'Today'),
        ('yesterday', 'Yesterday'),
        ('last_7_days', 'Last 7 Days'),
        ('last_30_days', 'Last 30 Days'),
        ('last_90_days', 'Last 90 Days'),
        ('this_month', 'This Month'),
        ('last_month', 'Last Month'),
        ('this_year', 'This Year'),
        ('last_year', 'Last Year')
    ], validators=[Optional()])
    
    # Event filters
    event_type = SelectField('Event Type', choices=[
        ('', 'All Events'),
        ('view', 'Page Views'),
        ('click', 'Clicks'),
        ('vote', 'Votes'),
        ('comment', 'Comments'),
        ('search', 'Searches'),
        ('share', 'Shares'),
        ('bookmark', 'Bookmarks'),
        ('download', 'Downloads'),
        ('session', 'Sessions')
    ], validators=[Optional()])
    
    event_category = SelectField('Event Category', choices=[
        ('', 'All Categories'),
        ('upvote', 'Upvotes'),
        ('downvote', 'Downvotes'),
        ('start', 'Session Start'),
        ('end', 'Session End'),
        ('internal', 'Internal Links'),
        ('external', 'External Links')
    ], validators=[Optional()])
    
    # User filters
    user_id = IntegerField('User ID', validators=[Optional(), NumberRange(min=1)])
    user_email = StringField('User Email', validators=[Optional(), Email(), Length(max=255)])
    
    # Content filters
    target_type = SelectField('Target Type', choices=[
        ('', 'All Types'),
        ('post', 'Posts'),
        ('comment', 'Comments'),
        ('user', 'Users'),
        ('category', 'Categories')
    ], validators=[Optional()])
    
    target_id = IntegerField('Target ID', validators=[Optional(), NumberRange(min=1)])
    
    # Data aggregation
    aggregation = SelectField('Aggregation', choices=[
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly')
    ], validators=[Optional()], default='daily')
    
    # Sort options
    sort_by = SelectField('Sort By', choices=[
        ('date', 'Date'),
        ('count', 'Count'),
        ('value', 'Value'),
        ('user', 'User')
    ], validators=[Optional()], default='date')
    
    sort_order = SelectField('Sort Order', choices=[
        ('asc', 'Ascending'),
        ('desc', 'Descending')
    ], validators=[Optional()], default='desc')
    
    # Limit results
    limit = IntegerField('Limit', validators=[Optional(), NumberRange(min=1, max=1000)], default=100)
    
    def validate_end_date(self, field):
        """Validate that end date is after start date"""
        if field.data and self.start_date.data:
            if field.data < self.start_date.data:
                raise ValidationError('End date must be after start date')
    
    def validate_period_preset(self, field):
        """Validate period preset and update date fields accordingly"""
        if field.data:
            today = datetime.utcnow().date()
            
            if field.data == 'today':
                self.start_date.data = today
                self.end_date.data = today
            elif field.data == 'yesterday':
                yesterday = today - timedelta(days=1)
                self.start_date.data = yesterday
                self.end_date.data = yesterday
            elif field.data == 'last_7_days':
                self.start_date.data = today - timedelta(days=7)
                self.end_date.data = today
            elif field.data == 'last_30_days':
                self.start_date.data = today - timedelta(days=30)
                self.end_date.data = today
            elif field.data == 'last_90_days':
                self.start_date.data = today - timedelta(days=90)
                self.end_date.data = today
            elif field.data == 'this_month':
                first_day = today.replace(day=1)
                self.start_date.data = first_day
                self.end_date.data = today
            elif field.data == 'last_month':
                last_month_end = today.replace(day=1) - timedelta(days=1)
                last_month_start = last_month_end.replace(day=1)
                self.start_date.data = last_month_start
                self.end_date.data = last_month_end
            elif field.data == 'this_year':
                first_day = today.replace(month=1, day=1)
                self.start_date.data = first_day
                self.end_date.data = today
            elif field.data == 'last_year':
                last_year_end = today.replace(month=1, day=1) - timedelta(days=1)
                last_year_start = last_year_end.replace(month=1, day=1)
                self.start_date.data = last_year_start
                self.end_date.data = last_year_end

class UserBehaviorFilterForm(FlaskForm):
    """Form for filtering user behavior analytics"""
    
    # User selection
    user_id = IntegerField('User ID', validators=[Optional(), NumberRange(min=1)])
    username = StringField('Username', validators=[Optional(), Length(min=3, max=80)])
    
    # Behavior filters
    engagement_level = SelectField('Engagement Level', choices=[
        ('', 'All Levels'),
        ('highly_engaged', 'Highly Engaged'),
        ('engaged', 'Engaged'),
        ('moderately_engaged', 'Moderately Engaged'),
        ('minimally_engaged', 'Minimally Engaged'),
        ('disengaged', 'Disengaged')
    ], validators=[Optional()])
    
    activity_pattern = SelectField('Activity Pattern', choices=[
        ('', 'All Patterns'),
        ('consistent', 'Consistent'),
        ('inconsistent', 'Inconsistent'),
        ('peak_hours', 'Peak Hours'),
        ('weekend_active', 'Weekend Active'),
        ('weekday_active', 'Weekday Active')
    ], validators=[Optional()])
    
    # Device filters
    device_type = SelectField('Device Type', choices=[
        ('', 'All Devices'),
        ('desktop', 'Desktop'),
        ('mobile', 'Mobile'),
        ('tablet', 'Tablet')
    ], validators=[Optional()])
    
    # Activity metrics
    min_sessions = IntegerField('Min Sessions', validators=[Optional(), NumberRange(min=0)])
    max_sessions = IntegerField('Max Sessions', validators=[Optional(), NumberRange(min=0)])
    
    min_session_duration = FloatField('Min Session Duration (minutes)', validators=[Optional(), NumberRange(min=0)])
    max_session_duration = FloatField('Max Session Duration (minutes)', validators=[Optional(), NumberRange(min=0)])
    
    min_engagement_score = FloatField('Min Engagement Score', validators=[Optional(), NumberRange(min=0, max=100)])
    max_engagement_score = FloatField('Max Engagement Score', validators=[Optional(), NumberRange(min=0, max=100)])
    
    # Content activity
    min_posts_created = IntegerField('Min Posts Created', validators=[Optional(), NumberRange(min=0)])
    max_posts_created = IntegerField('Max Posts Created', validators=[Optional(), NumberRange(min=0)])
    
    min_comments_created = IntegerField('Min Comments Created', validators=[Optional(), NumberRange(min=0)])
    max_comments_created = IntegerField('Max Comments Created', validators=[Optional(), NumberRange(min=0)])
    
    min_votes_cast = IntegerField('Min Votes Cast', validators=[Optional(), NumberRange(min=0)])
    max_votes_cast = IntegerField('Max Votes Cast', validators=[Optional(), NumberRange(min=0)])
    
    # Date filters
    last_active_since = DateField('Last Active Since', validators=[Optional()])
    last_active_before = DateField('Last Active Before', validators=[Optional()])
    
    # Sort options
    sort_by = SelectField('Sort By', choices=[
        ('engagement_score', 'Engagement Score'),
        ('total_sessions', 'Total Sessions'),
        ('avg_session_duration', 'Avg Session Duration'),
        ('posts_created', 'Posts Created'),
        ('comments_created', 'Comments Created'),
        ('votes_cast', 'Votes Cast'),
        ('last_active', 'Last Active'),
        ('reputation_score', 'Reputation Score')
    ], validators=[Optional()], default='engagement_score')
    
    sort_order = SelectField('Sort Order', choices=[
        ('asc', 'Ascending'),
        ('desc', 'Descending')
    ], validators=[Optional()], default='desc')
    
    # Pagination
    limit = IntegerField('Limit', validators=[Optional(), NumberRange(min=1, max=500)], default=50)
    
    def validate_max_sessions(self, field):
        """Validate that max_sessions is greater than min_sessions"""
        if field.data and self.min_sessions.data:
            if field.data < self.min_sessions.data:
                raise ValidationError('Max sessions must be greater than or equal to min sessions')
    
    def validate_max_session_duration(self, field):
        """Validate that max_session_duration is greater than min_session_duration"""
        if field.data and self.min_session_duration.data:
            if field.data < self.min_session_duration.data:
                raise ValidationError('Max session duration must be greater than or equal to min session duration')
    
    def validate_max_engagement_score(self, field):
        """Validate that max_engagement_score is greater than min_engagement_score"""
        if field.data and self.min_engagement_score.data:
            if field.data < self.min_engagement_score.data:
                raise ValidationError('Max engagement score must be greater than or equal to min engagement score')

class ContentPerformanceFilterForm(FlaskForm):
    """Form for filtering content performance analytics"""
    
    # Content selection
    content_type = SelectField('Content Type', choices=[
        ('post', 'Posts'),
        ('comment', 'Comments')
    ], validators=[DataRequired()], default='post')
    
    content_id = IntegerField('Content ID', validators=[Optional(), NumberRange(min=1)])
    
    # Performance metrics
    min_performance_score = FloatField('Min Performance Score', validators=[Optional(), NumberRange(min=0, max=100)])
    max_performance_score = FloatField('Max Performance Score', validators=[Optional(), NumberRange(min=0, max=100)])
    
    min_engagement_score = FloatField('Min Engagement Score', validators=[Optional(), NumberRange(min=0, max=100)])
    max_engagement_score = FloatField('Max Engagement Score', validators=[Optional(), NumberRange(min=0, max=100)])
    
    min_quality_score = FloatField('Min Quality Score', validators=[Optional(), NumberRange(min=0, max=100)])
    max_quality_score = FloatField('Max Quality Score', validators=[Optional(), NumberRange(min=0, max=100)])
    
    # View metrics
    min_views = IntegerField('Min Views', validators=[Optional(), NumberRange(min=0)])
    max_views = IntegerField('Max Views', validators=[Optional(), NumberRange(min=0)])
    
    min_unique_views = IntegerField('Min Unique Views', validators=[Optional(), NumberRange(min=0)])
    max_unique_views = IntegerField('Max Unique Views', validators=[Optional(), NumberRange(min=0)])
    
    min_avg_view_duration = FloatField('Min Avg View Duration (seconds)', validators=[Optional(), NumberRange(min=0)])
    max_avg_view_duration = FloatField('Max Avg View Duration (seconds)', validators=[Optional(), NumberRange(min=0)])
    
    # Engagement metrics
    min_total_votes = IntegerField('Min Total Votes', validators=[Optional(), NumberRange(min=0)])
    max_total_votes = IntegerField('Max Total Votes', validators=[Optional(), NumberRange(min=0)])
    
    min_vote_ratio = FloatField('Min Vote Ratio', validators=[Optional(), NumberRange(min=0, max=1)])
    max_vote_ratio = FloatField('Max Vote Ratio', validators=[Optional(), NumberRange(min=0, max=1)])
    
    min_comments = IntegerField('Min Comments', validators=[Optional(), NumberRange(min=0)])
    max_comments = IntegerField('Max Comments', validators=[Optional(), NumberRange(min=0)])
    
    # Trend filters
    view_trend = SelectField('View Trend', choices=[
        ('', 'All Trends'),
        ('increasing', 'Increasing'),
        ('decreasing', 'Decreasing'),
        ('stable', 'Stable')
    ], validators=[Optional()])
    
    engagement_trend = SelectField('Engagement Trend', choices=[
        ('', 'All Trends'),
        ('increasing', 'Increasing'),
        ('decreasing', 'Decreasing'),
        ('stable', 'Stable')
    ], validators=[Optional()])
    
    # Date filters
    created_since = DateField('Created Since', validators=[Optional()])
    created_before = DateField('Created Before', validators=[Optional()])
    
    last_viewed_since = DateField('Last Viewed Since', validators=[Optional()])
    last_viewed_before = DateField('Last Viewed Before', validators=[Optional()])
    
    # Sort options
    sort_by = SelectField('Sort By', choices=[
        ('performance_score', 'Performance Score'),
        ('engagement_score', 'Engagement Score'),
        ('quality_score', 'Quality Score'),
        ('total_views', 'Total Views'),
        ('unique_views', 'Unique Views'),
        ('total_votes', 'Total Votes'),
        ('vote_ratio', 'Vote Ratio'),
        ('total_comments', 'Total Comments'),
        ('created_at', 'Created Date'),
        ('last_viewed', 'Last Viewed')
    ], validators=[Optional()], default='performance_score')
    
    sort_order = SelectField('Sort Order', choices=[
        ('asc', 'Ascending'),
        ('desc', 'Descending')
    ], validators=[Optional()], default='desc')
    
    # Pagination
    limit = IntegerField('Limit', validators=[Optional(), NumberRange(min=1, max=500)], default=50)
    
    def validate_max_performance_score(self, field):
        """Validate that max_performance_score is greater than min_performance_score"""
        if field.data and self.min_performance_score.data:
            if field.data < self.min_performance_score.data:
                raise ValidationError('Max performance score must be greater than or equal to min performance score')
    
    def validate_max_views(self, field):
        """Validate that max_views is greater than min_views"""
        if field.data and self.min_views.data:
            if field.data < self.min_views.data:
                raise ValidationError('Max views must be greater than or equal to min views')

class SystemMetricsFilterForm(FlaskForm):
    """Form for filtering system metrics"""
    
    # Metric selection
    metric_type = SelectField('Metric Type', choices=[
        ('', 'All Types'),
        ('performance', 'Performance'),
        ('user', 'User Activity'),
        ('database', 'Database'),
        ('security', 'Security'),
        ('business', 'Business')
    ], validators=[Optional()])
    
    metric_category = SelectField('Metric Category', choices=[
        ('', 'All Categories'),
        ('response_time', 'Response Time'),
        ('cpu', 'CPU Usage'),
        ('memory', 'Memory Usage'),
        ('disk', 'Disk Usage'),
        ('network', 'Network'),
        ('activity', 'Activity'),
        ('connections', 'Connections'),
        ('queries', 'Queries')
    ], validators=[Optional()])
    
    metric_name = StringField('Metric Name', validators=[Optional(), Length(max=100)])
    
    # Health status filters
    health_status = SelectField('Health Status', choices=[
        ('', 'All Status'),
        ('healthy', 'Healthy'),
        ('warning', 'Warning'),
        ('critical', 'Critical')
    ], validators=[Optional()])
    
    # Value ranges
    min_value = FloatField('Min Value', validators=[Optional()])
    max_value = FloatField('Max Value', validators=[Optional()])
    
    # Threshold filters
    has_threshold = BooleanField('Has Threshold', validators=[Optional()])
    min_threshold_warning = FloatField('Min Warning Threshold', validators=[Optional()])
    max_threshold_warning = FloatField('Max Warning Threshold', validators=[Optional()])
    
    min_threshold_critical = FloatField('Min Critical Threshold', validators=[Optional()])
    max_threshold_critical = FloatField('Max Critical Threshold', validators=[Optional()])
    
    # Date filters
    recorded_since = DateTimeField('Recorded Since', validators=[Optional()])
    recorded_before = DateTimeField('Recorded Before', validators=[Optional()])
    
    # Sort options
    sort_by = SelectField('Sort By', choices=[
        ('recorded_at', 'Recorded Time'),
        ('current_value', 'Current Value'),
        ('metric_name', 'Metric Name'),
        ('health_status', 'Health Status'),
        ('metric_type', 'Metric Type')
    ], validators=[Optional()], default='recorded_at')
    
    sort_order = SelectField('Sort Order', choices=[
        ('asc', 'Ascending'),
        ('desc', 'Descending')
    ], validators=[Optional()], default='desc')
    
    # Pagination
    limit = IntegerField('Limit', validators=[Optional(), NumberRange(min=1, max=500)], default=100)
    
    def validate_max_value(self, field):
        """Validate that max_value is greater than min_value"""
        if field.data and self.min_value.data:
            if field.data < self.min_value.data:
                raise ValidationError('Max value must be greater than or equal to min value')

class TrendAnalysisForm(FlaskForm):
    """Form for trend analysis configuration"""
    
    # Target selection
    target_type = SelectField('Target Type', choices=[
        ('', 'Select Target'),
        ('user', 'User'),
        ('content', 'Content'),
        ('system', 'System'),
        ('category', 'Category')
    ], validators=[DataRequired()])
    
    target_id = IntegerField('Target ID', validators=[Optional(), NumberRange(min=1)])
    
    # Metric selection
    metric_name = SelectField('Metric', choices=[
        ('', 'Select Metric'),
        ('reputation_score', 'Reputation Score'),
        ('engagement_score', 'Engagement Score'),
        ('performance_score', 'Performance Score'),
        ('total_views', 'Total Views'),
        ('response_time', 'Response Time'),
        ('cpu_usage', 'CPU Usage'),
        ('memory_usage', 'Memory Usage'),
        ('active_users', 'Active Users'),
        ('requests_per_second', 'Requests per Second')
    ], validators=[DataRequired()])
    
    # Analysis parameters
    period_days = IntegerField('Analysis Period (Days)', validators=[
        DataRequired(), NumberRange(min=7, max=365)
    ], default=30)
    
    confidence_level = SelectField('Confidence Level', choices=[
        ('0.90', '90%'),
        ('0.95', '95%'),
        ('0.99', '99%')
    ], validators=[DataRequired()], default='0.95')
    
    analysis_type = SelectField('Analysis Type', choices=[
        ('linear', 'Linear Regression'),
        ('polynomial', 'Polynomial Regression'),
        ('exponential', 'Exponential Smoothing'),
        ('seasonal', 'Seasonal Decomposition')
    ], validators=[DataRequired()], default='linear')
    
    # Advanced options
    detect_anomalies = BooleanField('Detect Anomalies', default=True)
    anomaly_threshold = FloatField('Anomaly Threshold', validators=[
        Optional(), NumberRange(min=1.0, max=5.0)
    ], default=2.5)
    
    detect_seasonality = BooleanField('Detect Seasonality', default=True)
    seasonality_period = SelectField('Seasonality Period', choices=[
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly')
    ], validators=[Optional()], default='weekly')
    
    generate_predictions = BooleanField('Generate Predictions', default=True)
    prediction_days = IntegerField('Prediction Days', validators=[
        Optional(), NumberRange(min=1, max=365)
    ], default=30)
    
    # Output options
    include_raw_data = BooleanField('Include Raw Data', default=False)
    include_charts = BooleanField('Generate Charts', default=True)
    export_format = SelectField('Export Format', choices=[
        ('json', 'JSON'),
        ('csv', 'CSV'),
        ('excel', 'Excel')
    ], validators=[Optional()], default='json')
    
    def validate_period_days(self, field):
        """Validate period_days based on target type"""
        if field.data:
            if self.target_type.data == 'system' and field.data > 90:
                raise ValidationError('System metrics analysis limited to 90 days')
            elif self.target_type.data == 'user' and field.data < 14:
                raise ValidationError('User analysis requires at least 14 days of data')
    
    def validate_target_id(self, field):
        """Validate target_id based on target_type"""
        if self.target_type.data in ['user', 'content', 'category'] and not field.data:
            raise ValidationError(f'Target ID is required for {self.target_type.data} analysis')

class PredictiveModelForm(FlaskForm):
    """Form for creating and managing predictive models"""
    
    # Basic model information
    model_name = StringField('Model Name', validators=[
        DataRequired(), Length(min=3, max=100),
        Regexp(r'^[a-zA-Z0-9_-]+$', message='Model name can only contain letters, numbers, underscores, and hyphens')
    ])
    
    model_type = SelectField('Model Type', choices=[
        ('regression', 'Regression'),
        ('classification', 'Classification'),
        ('clustering', 'Clustering'),
        ('time_series', 'Time Series')
    ], validators=[DataRequired()])
    
    prediction_target = StringField('Prediction Target', validators=[
        DataRequired(), Length(min=3, max=100)
    ])
    
    description = TextAreaField('Description', validators=[
        Optional(), Length(max=1000)
    ])
    
    # Feature selection
    feature_columns = SelectMultipleField('Feature Columns', choices=[
        ('reputation_score', 'Reputation Score'),
        ('engagement_score', 'Engagement Score'),
        ('total_sessions', 'Total Sessions'),
        ('avg_session_duration', 'Avg Session Duration'),
        ('posts_created', 'Posts Created'),
        ('comments_created', 'Comments Created'),
        ('votes_cast', 'Votes Cast'),
        ('total_views', 'Total Views'),
        ('response_time', 'Response Time'),
        ('cpu_usage', 'CPU Usage'),
        ('memory_usage', 'Memory Usage'),
        ('active_users', 'Active Users'),
        ('requests_per_second', 'Requests per Second')
    ], validators=[DataRequired()])
    
    target_column = SelectField('Target Column', choices=[
        ('reputation_score', 'Reputation Score'),
        ('engagement_score', 'Engagement Score'),
        ('performance_score', 'Performance Score'),
        ('total_views', 'Total Views'),
        ('churn_probability', 'Churn Probability'),
        ('conversion_probability', 'Conversion Probability')
    ], validators=[DataRequired()])
    
    # Training parameters
    training_period_days = IntegerField('Training Period (Days)', validators=[
        DataRequired(), NumberRange(min=30, max=365)
    ], default=90)
    
    validation_split = FloatField('Validation Split', validators=[
        DataRequired(), NumberRange(min=0.1, max=0.5)
    ], default=0.2)
    
    algorithm = SelectField('Algorithm', choices=[
        ('linear_regression', 'Linear Regression'),
        ('logistic_regression', 'Logistic Regression'),
        ('random_forest', 'Random Forest'),
        ('gradient_boosting', 'Gradient Boosting'),
        ('svm', 'Support Vector Machine'),
        ('neural_network', 'Neural Network')
    ], validators=[DataRequired()])
    
    # Model configuration
    max_depth = IntegerField('Max Depth', validators=[
        Optional(), NumberRange(min=1, max=50)
    ])
    
    n_estimators = IntegerField('Number of Estimators', validators=[
        Optional(), NumberRange(min=10, max=1000)
    ])
    
    learning_rate = FloatField('Learning Rate', validators=[
        Optional(), NumberRange(min=0.001, max=1.0)
    ])
    
    regularization = FloatField('Regularization', validators=[
        Optional(), NumberRange(min=0.0, max=10.0)
    ])
    
    # Advanced options
    cross_validation = BooleanField('Cross Validation', default=True)
    cv_folds = IntegerField('CV Folds', validators=[
        Optional(), NumberRange(min=3, max=10)
    ], default=5)
    
    feature_scaling = BooleanField('Feature Scaling', default=True)
    feature_selection = BooleanField('Feature Selection', default=False)
    
    # Performance requirements
    min_accuracy = FloatField('Min Accuracy', validators=[
        Optional(), NumberRange(min=0.0, max=1.0)
    ])
    
    min_precision = FloatField('Min Precision', validators=[
        Optional(), NumberRange(min=0.0, max=1.0)
    ])
    
    min_recall = FloatField('Min Recall', validators=[
        Optional(), NumberRange(min=0.0, max=1.0)
    ])
    
    # Deployment options
    auto_deploy = BooleanField('Auto Deploy on Training Success', default=False)
    prediction_threshold = FloatField('Prediction Threshold', validators=[
        Optional(), NumberRange(min=0.0, max=1.0)
    ])
    
    # Monitoring
    enable_monitoring = BooleanField('Enable Performance Monitoring', default=True)
    monitoring_interval = IntegerField('Monitoring Interval (Hours)', validators=[
        Optional(), NumberRange(min=1, max=168)
    ], default=24)
    
    # Retraining
    auto_retrain = BooleanField('Auto Retrain', default=False)
    retrain_interval_days = IntegerField('Retrain Interval (Days)', validators=[
        Optional(), NumberRange(min=7, max=365)
    ], default=30)
    
    performance_threshold = FloatField('Performance Threshold', validators=[
        Optional(), NumberRange(min=0.0, max=1.0)
    ], default=0.8)
    
    def validate_model_name(self, field):
        """Validate model name uniqueness"""
        if field.data:
            existing = PredictiveModel.query.filter_by(model_name=field.data).first()
            if existing:
                raise ValidationError('Model name already exists')
    
    def validate_target_column(self, field):
        """Validate target column is not in feature columns"""
        if field.data and self.feature_columns.data:
            if field.data in self.feature_columns.data:
                raise ValidationError('Target column cannot be included in feature columns')
    
    def validate_n_estimators(self, field):
        """Validate n_estimators for applicable algorithms"""
        if field.data and self.algorithm.data in ['random_forest', 'gradient_boosting']:
            if field.data < 10:
                raise ValidationError('Number of estimators must be at least 10 for ensemble methods')

class ModelTrainingForm(FlaskForm):
    """Form for training predictive models"""
    
    model_id = HiddenField('Model ID', validators=[DataRequired()])
    
    # Training options
    training_mode = SelectField('Training Mode', choices=[
        ('incremental', 'Incremental Update'),
        ('full_retrain', 'Full Retrain'),
        ('hyperparameter_tuning', 'Hyperparameter Tuning')
    ], validators=[DataRequired()], default='full_retrain')
    
    # Data options
    use_all_data = BooleanField('Use All Available Data', default=False)
    training_start_date = DateField('Training Start Date', validators=[Optional()])
    training_end_date = DateField('Training End Date', validators=[Optional()])
    
    # Hyperparameter tuning
    enable_grid_search = BooleanField('Enable Grid Search', default=False)
    param_grid = TextAreaField('Parameter Grid (JSON)', validators=[Optional()])
    
    # Validation options
    use_time_series_split = BooleanField('Use Time Series Split', default=False)
    n_splits = IntegerField('Number of Splits', validators=[
        Optional(), NumberRange(min=3, max=10)
    ], default=5)
    
    # Early stopping
    enable_early_stopping = BooleanField('Enable Early Stopping', default=False)
    patience = IntegerField('Patience', validators=[
        Optional(), NumberRange(min=1, max=100)
    ], default=10)
    
    # Output options
    save_model = BooleanField('Save Model', default=True)
    generate_report = BooleanField('Generate Training Report', default=True)
    test_predictions = BooleanField('Generate Test Predictions', default=False)
    
    def validate_training_end_date(self, field):
        """Validate training date range"""
        if field.data and self.training_start_date.data:
            if field.data < self.training_start_date.data:
                raise ValidationError('Training end date must be after start date')
    
    def validate_param_grid(self, field):
        """Validate parameter grid JSON format"""
        if field.data:
            try:
                import json
                json.loads(field.data)
            except json.JSONDecodeError:
                raise ValidationError('Parameter grid must be valid JSON')

class AnalyticsExportForm(FlaskForm):
    """Form for exporting analytics data"""
    
    # Export options
    export_type = SelectField('Export Type', choices=[
        ('events', 'Analytics Events'),
        ('user_behavior', 'User Behavior'),
        ('content_performance', 'Content Performance'),
        ('system_metrics', 'System Metrics'),
        ('trends', 'Trend Analysis'),
        ('predictions', 'Predictions')
    ], validators=[DataRequired()])
    
    # Format options
    format = SelectField('Format', choices=[
        ('csv', 'CSV'),
        ('json', 'JSON'),
        ('excel', 'Excel'),
        ('pdf', 'PDF Report')
    ], validators=[DataRequired()], default='csv')
    
    # Date range
    start_date = DateField('Start Date', validators=[Optional()], default=datetime.utcnow().date() - timedelta(days=30))
    end_date = DateField('End Date', validators=[Optional()], default=datetime.utcnow().date())
    
    # Filters (conditional based on export type)
    user_id = IntegerField('User ID', validators=[Optional(), NumberRange(min=1)])
    content_type = SelectField('Content Type', choices=[
        ('', 'All'),
        ('post', 'Posts'),
        ('comment', 'Comments')
    ], validators=[Optional()])
    
    # Data options
    include_raw_data = BooleanField('Include Raw Data', default=False)
    include_aggregations = BooleanField('Include Aggregations', default=True)
    include_charts = BooleanField('Include Charts', default=False)
    
    # Compression
    compress_file = BooleanField('Compress File', default=False)
    
    # Email options
    email_report = BooleanField('Email Report', default=False)
    email_address = StringField('Email Address', validators=[Optional(), Email()])
    
    def validate_end_date(self, field):
        """Validate that end date is after start date"""
        if field.data and self.start_date.data:
            if field.data < self.start_date.data:
                raise ValidationError('End date must be after start date')
    
    def validate_email_address(self, field):
        """Validate email address if email report is enabled"""
        if self.email_report.data and not field.data:
            raise ValidationError('Email address is required when email report is enabled')

class AnalyticsDashboardForm(FlaskForm):
    """Form for configuring analytics dashboard"""
    
    # Dashboard configuration
    dashboard_name = StringField('Dashboard Name', validators=[
        DataRequired(), Length(min=3, max=100)
    ])
    
    description = TextAreaField('Description', validators=[
        Optional(), Length(max=500)
    ])
    
    # Widget selection
    widgets = SelectMultipleField('Widgets', choices=[
        ('overview_stats', 'Overview Statistics'),
        ('user_activity', 'User Activity'),
        ('content_performance', 'Content Performance'),
        ('system_health', 'System Health'),
        ('trend_charts', 'Trend Charts'),
        ('real_time_metrics', 'Real-time Metrics'),
        ('top_content', 'Top Performing Content'),
        ('user_leaderboard', 'User Leaderboard'),
        ('engagement_metrics', 'Engagement Metrics'),
        ('conversion_funnel', 'Conversion Funnel')
    ], validators=[DataRequired()])
    
    # Layout options
    layout = SelectField('Layout', choices=[
        ('grid', 'Grid'),
        ('list', 'List'),
        ('tabs', 'Tabs')
    ], validators=[DataRequired()], default='grid')
    
    columns = IntegerField('Columns', validators=[
        DataRequired(), NumberRange(min=1, max=4)
    ], default=3)
    
    # Refresh options
    auto_refresh = BooleanField('Auto Refresh', default=False)
    refresh_interval = IntegerField('Refresh Interval (Seconds)', validators=[
        Optional(), NumberRange(min=30, max=3600)
    ], default=300)
    
    # Time range
    default_time_range = SelectField('Default Time Range', choices=[
        ('last_24_hours', 'Last 24 Hours'),
        ('last_7_days', 'Last 7 Days'),
        ('last_30_days', 'Last 30 Days'),
        ('last_90_days', 'Last 90 Days')
    ], validators=[DataRequired()], default='last_30_days')
    
    # Filters
    enable_filters = BooleanField('Enable Filters', default=True)
    filter_options = SelectMultipleField('Filter Options', choices=[
        ('date_range', 'Date Range'),
        ('user_filter', 'User Filter'),
        ('content_type', 'Content Type'),
        ('category_filter', 'Category Filter'),
        ('event_type', 'Event Type')
    ], validators=[Optional()])
    
    # Sharing options
    is_public = BooleanField('Public Dashboard', default=False)
    share_token = StringField('Share Token', validators=[Optional(), Length(min=10, max=50)])
    
    # Export options
    allow_export = BooleanField('Allow Export', default=True)
    export_formats = SelectMultipleField('Export Formats', choices=[
        ('csv', 'CSV'),
        ('json', 'JSON'),
        ('excel', 'Excel'),
        ('pdf', 'PDF')
    ], validators=[Optional()])
    
    def validate_widgets(self, field):
        """Validate widget selection"""
        if not field.data:
            raise ValidationError('At least one widget must be selected')
    
    def validate_refresh_interval(self, field):
        """Validate refresh interval"""
        if self.auto_refresh.data and not field.data:
            raise ValidationError('Refresh interval is required when auto refresh is enabled')
