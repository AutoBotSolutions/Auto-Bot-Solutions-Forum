"""
Advanced Analytics Models

This module contains the database models for the advanced analytics system,
including analytics events, user behavior tracking, content performance metrics,
system monitoring, trend analysis, and predictive models.
"""

from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from app import db
from sqlalchemy import Index, CheckConstraint, func as sql_func
import json

class AnalyticsEvent(db.Model):
    """Track all analytics events for comprehensive system monitoring"""
    __tablename__ = 'analytics_events'
    
    id = db.Column(db.Integer, primary_key=True)
    event_type = db.Column(db.String(50), nullable=False, index=True)
    event_category = db.Column(db.String(50), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True, index=True)
    session_id = db.Column(db.String(128), nullable=True, index=True)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.Text, nullable=True)
    
    # Event data
    target_type = db.Column(db.String(50), nullable=True, index=True)  # post, comment, user, etc.
    target_id = db.Column(db.Integer, nullable=True, index=True)
    event_data = db.Column(db.JSON, nullable=True)  # Additional event metadata
    event_value = db.Column(db.Float, nullable=True)  # Numeric value for events
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    processed_at = db.Column(db.DateTime, nullable=True)  # When event was processed
    
    # Relationships
    user = db.relationship('User', backref='analytics_events', lazy=True)
    
    # Constraints
    __table_args__ = (
        CheckConstraint('event_value >= -999999', name='check_event_value_min'),
        CheckConstraint('event_value <= 999999', name='check_event_value_max'),
        Index('idx_analytics_events_type_category', 'event_type', 'event_category'),
        Index('idx_analytics_events_user_time', 'user_id', 'created_at'),
        Index('idx_analytics_events_target', 'target_type', 'target_id'),
        Index('idx_analytics_events_session', 'session_id', 'created_at'),
    )
    
    def __repr__(self):
        return f'<AnalyticsEvent {self.event_type}:{self.event_category}>'
    
    def to_dict(self):
        """Convert event to dictionary"""
        return {
            'id': self.id,
            'event_type': self.event_type,
            'event_category': self.event_category,
            'user_id': self.user_id,
            'session_id': self.session_id,
            'ip_address': self.ip_address,
            'target_type': self.target_type,
            'target_id': self.target_id,
            'event_data': self.event_data,
            'event_value': self.event_value,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None
        }

class UserBehavior(db.Model):
    """Track detailed user behavior patterns and analytics"""
    __tablename__ = 'user_behavior'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True, index=True)
    
    # Session analytics
    total_sessions = db.Column(db.Integer, default=0, nullable=False)
    avg_session_duration = db.Column(db.Float, default=0.0, nullable=False)  # in minutes
    total_session_duration = db.Column(db.Float, default=0.0, nullable=False)  # in minutes
    last_session_start = db.Column(db.DateTime, nullable=True)
    last_session_end = db.Column(db.DateTime, nullable=True)
    
    # Activity patterns
    most_active_hour = db.Column(db.Integer, nullable=True)  # 0-23
    most_active_day = db.Column(db.Integer, nullable=True)  # 0-6 (Sunday=0)
    activity_consistency = db.Column(db.Float, default=0.0, nullable=False)  # 0-1 score
    peak_activity_hour = db.Column(db.Integer, nullable=True)
    
    # Content interaction
    posts_viewed = db.Column(db.Integer, default=0, nullable=False)
    posts_created = db.Column(db.Integer, default=0, nullable=False)
    comments_created = db.Column(db.Integer, default=0, nullable=False)
    votes_cast = db.Column(db.Integer, default=0, nullable=False)
    bookmarks_created = db.Column(db.Integer, default=0, nullable=False)
    searches_performed = db.Column(db.Integer, default=0, nullable=False)
    
    # Engagement metrics
    avg_time_on_page = db.Column(db.Float, default=0.0, nullable=False)  # in seconds
    bounce_rate = db.Column(db.Float, default=0.0, nullable=False)  # 0-1
    pages_per_session = db.Column(db.Float, default=0.0, nullable=False)
    engagement_score = db.Column(db.Float, default=0.0, nullable=False)  # 0-100
    
    # Navigation patterns
    most_visited_category = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)
    preferred_content_type = db.Column(db.String(50), nullable=True)  # post, comment, etc.
    search_patterns = db.Column(db.JSON, nullable=True)  # Common search terms and patterns
    
    # Device and browser analytics
    primary_device_type = db.Column(db.String(50), nullable=True)  # desktop, mobile, tablet
    primary_browser = db.Column(db.String(50), nullable=True)
    primary_os = db.Column(db.String(50), nullable=True)
    device_changes = db.Column(db.Integer, default=0, nullable=False)
    
    # Timestamps
    first_seen = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_active = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = db.relationship('User', backref='behavior_analytics', lazy=True, uselist=False)
    most_visited_category_rel = db.relationship('Category', backref='behavior_users', lazy=True)
    
    # Constraints
    __table_args__ = (
        CheckConstraint('avg_session_duration >= 0', name='check_avg_session_duration'),
        CheckConstraint('avg_session_duration <= 1440', name='check_avg_session_duration_max'),  # 24 hours
        CheckConstraint('activity_consistency >= 0', name='check_activity_consistency_min'),
        CheckConstraint('activity_consistency <= 1', name='check_activity_consistency_max'),
        CheckConstraint('bounce_rate >= 0', name='check_bounce_rate_min'),
        CheckConstraint('bounce_rate <= 1', name='check_bounce_rate_max'),
        CheckConstraint('engagement_score >= 0', name='check_engagement_score_min'),
        CheckConstraint('engagement_score <= 100', name='check_engagement_score_max'),
        CheckConstraint('most_active_hour >= 0', name='check_most_active_hour_min'),
        CheckConstraint('most_active_hour <= 23', name='check_most_active_hour_max'),
        CheckConstraint('most_active_day >= 0', name='check_most_active_day_min'),
        CheckConstraint('most_active_day <= 6', name='check_most_active_day_max'),
    )
    
    def __repr__(self):
        return f'<UserBehavior {self.user_id}: {self.engagement_score}>'
    
    def to_dict(self):
        """Convert behavior to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'total_sessions': self.total_sessions,
            'avg_session_duration': self.avg_session_duration,
            'total_session_duration': self.total_session_duration,
            'last_session_start': self.last_session_start.isoformat() if self.last_session_start else None,
            'last_session_end': self.last_session_end.isoformat() if self.last_session_end else None,
            'most_active_hour': self.most_active_hour,
            'most_active_day': self.most_active_day,
            'activity_consistency': self.activity_consistency,
            'peak_activity_hour': self.peak_activity_hour,
            'posts_viewed': self.posts_viewed,
            'posts_created': self.posts_created,
            'comments_created': self.comments_created,
            'votes_cast': self.votes_cast,
            'bookmarks_created': self.bookmarks_created,
            'searches_performed': self.searches_performed,
            'avg_time_on_page': self.avg_time_on_page,
            'bounce_rate': self.bounce_rate,
            'pages_per_session': self.pages_per_session,
            'engagement_score': self.engagement_score,
            'most_visited_category': self.most_visited_category,
            'preferred_content_type': self.preferred_content_type,
            'search_patterns': self.search_patterns,
            'primary_device_type': self.primary_device_type,
            'primary_browser': self.primary_browser,
            'primary_os': self.primary_os,
            'device_changes': self.device_changes,
            'first_seen': self.first_seen.isoformat() if self.first_seen else None,
            'last_active': self.last_active.isoformat() if self.last_active else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class ContentPerformance(db.Model):
    """Track performance metrics for content (posts, comments, etc.)"""
    __tablename__ = 'content_performance'
    
    id = db.Column(db.Integer, primary_key=True)
    content_type = db.Column(db.String(50), nullable=False, index=True)  # post, comment
    content_id = db.Column(db.Integer, nullable=False, index=True)
    
    # View metrics
    total_views = db.Column(db.Integer, default=0, nullable=False)
    unique_views = db.Column(db.Integer, default=0, nullable=False)
    avg_view_duration = db.Column(db.Float, default=0.0, nullable=False)  # in seconds
    view_count_by_day = db.Column(db.JSON, nullable=True)  # Daily view counts
    
    # Engagement metrics
    total_votes = db.Column(db.Integer, default=0, nullable=False)
    upvotes = db.Column(db.Integer, default=0, nullable=False)
    downvotes = db.Column(db.Integer, default=0, nullable=False)
    vote_ratio = db.Column(db.Float, default=0.0, nullable=False)  # 0-1
    weighted_score = db.Column(db.Float, default=0.0, nullable=False)
    
    # Comment metrics
    total_comments = db.Column(db.Integer, default=0, nullable=False)
    unique_commenters = db.Column(db.Integer, default=0, nullable=False)
    avg_comment_length = db.Column(db.Float, default=0.0, nullable=False)
    comment_response_time = db.Column(db.Float, default=0.0, nullable=False)  # avg time to first comment
    
    # Sharing metrics
    shares_count = db.Column(db.Integer, default=0, nullable=False)
    bookmarks_count = db.Column(db.Integer, default=0, nullable=False)
    external_links = db.Column(db.Integer, default=0, nullable=False)
    
    # Quality metrics
    read_ratio = db.Column(db.Float, default=0.0, nullable=False)  # views that read to end
    scroll_depth = db.Column(db.Float, default=0.0, nullable=False)  # avg scroll depth
    time_to_first_click = db.Column(db.Float, default=0.0, nullable=False)  # in seconds
    click_through_rate = db.Column(db.Float, default=0.0, nullable=False)  # 0-1
    
    # Performance score
    quality_score = db.Column(db.Float, default=0.0, nullable=False)  # 0-100
    engagement_score = db.Column(db.Float, default=0.0, nullable=False)  # 0-100
    performance_score = db.Column(db.Float, default=0.0, nullable=False)  # 0-100
    
    # Trend metrics
    view_trend = db.Column(db.String(20), nullable=True)  # increasing, decreasing, stable
    engagement_trend = db.Column(db.String(20), nullable=True)
    performance_trend = db.Column(db.String(20), nullable=True)
    
    # Timestamps
    first_viewed = db.Column(db.DateTime, nullable=True)
    last_viewed = db.Column(db.DateTime, nullable=True)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Constraints
    __table_args__ = (
        CheckConstraint('avg_view_duration >= 0', name='check_avg_view_duration'),
        CheckConstraint('vote_ratio >= 0', name='check_vote_ratio_min'),
        CheckConstraint('vote_ratio <= 1', name='check_vote_ratio_max'),
        CheckConstraint('read_ratio >= 0', name='check_read_ratio_min'),
        CheckConstraint('read_ratio <= 1', name='check_read_ratio_max'),
        CheckConstraint('scroll_depth >= 0', name='check_scroll_depth_min'),
        CheckConstraint('scroll_depth <= 1', name='check_scroll_depth_max'),
        CheckConstraint('click_through_rate >= 0', name='check_ctr_min'),
        CheckConstraint('click_through_rate <= 1', name='check_ctr_max'),
        CheckConstraint('quality_score >= 0', name='check_quality_score_min'),
        CheckConstraint('quality_score <= 100', name='check_quality_score_max'),
        CheckConstraint('engagement_score >= 0', name='check_engagement_score_min'),
        CheckConstraint('engagement_score <= 100', name='check_engagement_score_max'),
        CheckConstraint('performance_score >= 0', name='check_performance_score_min'),
        CheckConstraint('performance_score <= 100', name='check_performance_score_max'),
        Index('idx_content_performance_content', 'content_type', 'content_id'),
        Index('idx_content_performance_scores', 'performance_score', 'engagement_score'),
        Index('idx_content_performance_trends', 'view_trend', 'engagement_trend'),
        Index('idx_content_performance_views', 'total_views', 'unique_views'),
    )
    
    def __repr__(self):
        return f'<ContentPerformance {self.content_type}:{self.content_id}>'
    
    def to_dict(self):
        """Convert performance to dictionary"""
        return {
            'id': self.id,
            'content_type': self.content_type,
            'content_id': self.content_id,
            'total_views': self.total_views,
            'unique_views': self.unique_views,
            'avg_view_duration': self.avg_view_duration,
            'view_count_by_day': self.view_count_by_day,
            'total_votes': self.total_votes,
            'upvotes': self.upvotes,
            'downvotes': self.downvotes,
            'vote_ratio': self.vote_ratio,
            'weighted_score': self.weighted_score,
            'total_comments': self.total_comments,
            'unique_commenters': self.unique_commenters,
            'avg_comment_length': self.avg_comment_length,
            'comment_response_time': self.comment_response_time,
            'shares_count': self.shares_count,
            'bookmarks_count': self.bookmarks_count,
            'external_links': self.external_links,
            'read_ratio': self.read_ratio,
            'scroll_depth': self.scroll_depth,
            'time_to_first_click': self.time_to_first_click,
            'click_through_rate': self.click_through_rate,
            'quality_score': self.quality_score,
            'engagement_score': self.engagement_score,
            'performance_score': self.performance_score,
            'view_trend': self.view_trend,
            'engagement_trend': self.engagement_trend,
            'performance_trend': self.performance_trend,
            'first_viewed': self.first_viewed.isoformat() if self.first_viewed else None,
            'last_viewed': self.last_viewed.isoformat() if self.last_viewed else None,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class SystemMetrics(db.Model):
    """Track system performance and health metrics"""
    __tablename__ = 'system_metrics'
    
    id = db.Column(db.Integer, primary_key=True)
    metric_type = db.Column(db.String(50), nullable=False, index=True)
    metric_category = db.Column(db.String(50), nullable=False, index=True)
    metric_name = db.Column(db.String(100), nullable=False, index=True)
    
    # Metric values
    current_value = db.Column(db.Float, nullable=False)
    previous_value = db.Column(db.Float, nullable=True)
    min_value = db.Column(db.Float, nullable=True)
    max_value = db.Column(db.Float, nullable=True)
    avg_value = db.Column(db.Float, nullable=True)
    
    # Health indicators
    health_status = db.Column(db.String(20), nullable=False, default='healthy')  # healthy, warning, critical
    threshold_warning = db.Column(db.Float, nullable=True)
    threshold_critical = db.Column(db.Float, nullable=True)
    
    # Performance metrics
    response_time = db.Column(db.Float, nullable=True)  # in milliseconds
    cpu_usage = db.Column(db.Float, nullable=True)  # percentage
    memory_usage = db.Column(db.Float, nullable=True)  # percentage
    disk_usage = db.Column(db.Float, nullable=True)  # percentage
    network_io = db.Column(db.Float, nullable=True)  # bytes per second
    
    # User metrics
    active_users = db.Column(db.Integer, nullable=True)
    concurrent_sessions = db.Column(db.Integer, nullable=True)
    requests_per_second = db.Column(db.Float, nullable=True)
    error_rate = db.Column(db.Float, nullable=True)  # percentage
    
    # Database metrics
    db_connections = db.Column(db.Integer, nullable=True)
    db_query_time = db.Column(db.Float, nullable=True)  # average query time in ms
    db_size = db.Column(db.Float, nullable=True)  # in GB
    cache_hit_rate = db.Column(db.Float, nullable=True)  # percentage
    
    # Additional data
    metric_data = db.Column(db.JSON, nullable=True)  # Additional metric metadata
    tags = db.Column(db.JSON, nullable=True)  # Tags for categorization
    
    # Timestamps
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Constraints
    __table_args__ = (
        CheckConstraint('health_status IN ("healthy", "warning", "critical")', name='check_health_status'),
        CheckConstraint('cpu_usage >= 0', name='check_cpu_usage_min'),
        CheckConstraint('cpu_usage <= 100', name='check_cpu_usage_max'),
        CheckConstraint('memory_usage >= 0', name='check_memory_usage_min'),
        CheckConstraint('memory_usage <= 100', name='check_memory_usage_max'),
        CheckConstraint('disk_usage >= 0', name='check_disk_usage_min'),
        CheckConstraint('disk_usage <= 100', name='check_disk_usage_max'),
        CheckConstraint('error_rate >= 0', name='check_error_rate_min'),
        CheckConstraint('error_rate <= 100', name='check_error_rate_max'),
        CheckConstraint('cache_hit_rate >= 0', name='check_cache_hit_rate_min'),
        CheckConstraint('cache_hit_rate <= 100', name='check_cache_hit_rate_max'),
        Index('idx_system_metrics_type_category', 'metric_type', 'metric_category'),
        Index('idx_system_metrics_health', 'health_status', 'recorded_at'),
        Index('idx_system_metrics_performance', 'response_time', 'cpu_usage', 'memory_usage'),
    )
    
    def __repr__(self):
        return f'<SystemMetrics {self.metric_type}:{self.metric_name}>'
    
    def to_dict(self):
        """Convert metrics to dictionary"""
        return {
            'id': self.id,
            'metric_type': self.metric_type,
            'metric_category': self.metric_category,
            'metric_name': self.metric_name,
            'current_value': self.current_value,
            'previous_value': self.previous_value,
            'min_value': self.min_value,
            'max_value': self.max_value,
            'avg_value': self.avg_value,
            'health_status': self.health_status,
            'threshold_warning': self.threshold_warning,
            'threshold_critical': self.threshold_critical,
            'response_time': self.response_time,
            'cpu_usage': self.cpu_usage,
            'memory_usage': self.memory_usage,
            'disk_usage': self.disk_usage,
            'network_io': self.network_io,
            'active_users': self.active_users,
            'concurrent_sessions': self.concurrent_sessions,
            'requests_per_second': self.requests_per_second,
            'error_rate': self.error_rate,
            'db_connections': self.db_connections,
            'db_query_time': self.db_query_time,
            'db_size': self.db_size,
            'cache_hit_rate': self.cache_hit_rate,
            'metric_data': self.metric_data,
            'tags': self.tags,
            'recorded_at': self.recorded_at.isoformat() if self.recorded_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class TrendAnalysis(db.Model):
    """Store trend analysis results for various metrics"""
    __tablename__ = 'trend_analysis'
    
    id = db.Column(db.Integer, primary_key=True)
    analysis_type = db.Column(db.String(50), nullable=False, index=True)
    target_type = db.Column(db.String(50), nullable=False, index=True)  # user, content, system
    target_id = db.Column(db.Integer, nullable=True, index=True)
    metric_name = db.Column(db.String(100), nullable=False, index=True)
    
    # Analysis parameters
    period_days = db.Column(db.Integer, nullable=False, default=30)
    data_points = db.Column(db.Integer, nullable=False, default=0)
    confidence_level = db.Column(db.Float, nullable=False, default=0.95)  # 0-1
    
    # Trend results
    trend_direction = db.Column(db.String(20), nullable=False)  # increasing, decreasing, stable
    trend_strength = db.Column(db.Float, nullable=False)  # 0-1 strength of trend
    slope = db.Column(db.Float, nullable=False)  # trend slope
    correlation = db.Column(db.Float, nullable=True)  # correlation coefficient
    
    # Statistical measures
    mean_value = db.Column(db.Float, nullable=False)
    median_value = db.Column(db.Float, nullable=False)
    std_deviation = db.Column(db.Float, nullable=False)
    variance = db.Column(db.Float, nullable=False)
    
    # Predictions
    predicted_value_7d = db.Column(db.Float, nullable=True)  # 7 days prediction
    predicted_value_30d = db.Column(db.Float, nullable=True)  # 30 days prediction
    prediction_confidence = db.Column(db.Float, nullable=True)  # 0-1
    
    # Anomaly detection
    is_anomaly = db.Column(db.Boolean, default=False, nullable=False)
    anomaly_score = db.Column(db.Float, nullable=True)  # 0-1
    anomaly_reason = db.Column(db.Text, nullable=True)
    
    # Seasonality
    has_seasonality = db.Column(db.Boolean, default=False, nullable=False)
    seasonal_pattern = db.Column(db.JSON, nullable=True)  # Seasonal pattern data
    
    # Analysis data
    raw_data = db.Column(db.JSON, nullable=True)  # Raw data points
    processed_data = db.Column(db.JSON, nullable=True)  # Processed analysis data
    analysis_config = db.Column(db.JSON, nullable=True)  # Analysis configuration
    
    # Timestamps
    analysis_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    next_analysis = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Constraints
    __table_args__ = (
        CheckConstraint('trend_direction IN ("increasing", "decreasing", "stable")', name='check_trend_direction'),
        CheckConstraint('trend_strength >= 0', name='check_trend_strength_min'),
        CheckConstraint('trend_strength <= 1', name='check_trend_strength_max'),
        CheckConstraint('confidence_level >= 0', name='check_confidence_level_min'),
        CheckConstraint('confidence_level <= 1', name='check_confidence_level_max'),
        CheckConstraint('prediction_confidence >= 0', name='check_prediction_confidence_min'),
        CheckConstraint('prediction_confidence <= 1', name='check_prediction_confidence_max'),
        CheckConstraint('anomaly_score >= 0', name='check_anomaly_score_min'),
        CheckConstraint('anomaly_score <= 1', name='check_anomaly_score_max'),
        Index('idx_trend_analysis_target', 'target_type', 'target_id', 'metric_name'),
        Index('idx_trend_analysis_type', 'analysis_type', 'analysis_date'),
        Index('idx_trend_analysis_anomaly', 'is_anomaly', 'anomaly_score'),
    )
    
    def __repr__(self):
        return f'<TrendAnalysis {self.analysis_type}:{self.metric_name}>'
    
    def to_dict(self):
        """Convert trend analysis to dictionary"""
        return {
            'id': self.id,
            'analysis_type': self.analysis_type,
            'target_type': self.target_type,
            'target_id': self.target_id,
            'metric_name': self.metric_name,
            'period_days': self.period_days,
            'data_points': self.data_points,
            'confidence_level': self.confidence_level,
            'trend_direction': self.trend_direction,
            'trend_strength': self.trend_strength,
            'slope': self.slope,
            'correlation': self.correlation,
            'mean_value': self.mean_value,
            'median_value': self.median_value,
            'std_deviation': self.std_deviation,
            'variance': self.variance,
            'predicted_value_7d': self.predicted_value_7d,
            'predicted_value_30d': self.predicted_value_30d,
            'prediction_confidence': self.prediction_confidence,
            'is_anomaly': self.is_anomaly,
            'anomaly_score': self.anomaly_score,
            'anomaly_reason': self.anomaly_reason,
            'has_seasonality': self.has_seasonality,
            'seasonal_pattern': self.seasonal_pattern,
            'raw_data': self.raw_data,
            'processed_data': self.processed_data,
            'analysis_config': self.analysis_config,
            'analysis_date': self.analysis_date.isoformat() if self.analysis_date else None,
            'next_analysis': self.next_analysis.isoformat() if self.next_analysis else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class PredictiveModel(db.Model):
    """Store predictive models and their performance metrics"""
    __tablename__ = 'predictive_models'
    
    id = db.Column(db.Integer, primary_key=True)
    model_name = db.Column(db.String(100), nullable=False, unique=True, index=True)
    model_type = db.Column(db.String(50), nullable=False, index=True)  # regression, classification, clustering
    prediction_target = db.Column(db.String(100), nullable=False, index=True)  # what we're predicting
    
    # Model configuration
    model_config = db.Column(db.JSON, nullable=False)  # Model parameters and configuration
    feature_columns = db.Column(db.JSON, nullable=False)  # Features used by the model
    target_column = db.Column(db.String(100), nullable=False)  # Target column
    
    # Training data
    training_samples = db.Column(db.Integer, nullable=False)
    training_start_date = db.Column(db.DateTime, nullable=False)
    training_end_date = db.Column(db.DateTime, nullable=False)
    validation_samples = db.Column(db.Integer, nullable=False)
    
    # Performance metrics
    accuracy = db.Column(db.Float, nullable=True)  # 0-1 for classification
    precision = db.Column(db.Float, nullable=True)  # 0-1
    recall = db.Column(db.Float, nullable=True)  # 0-1
    f1_score = db.Column(db.Float, nullable=True)  # 0-1
    mse = db.Column(db.Float, nullable=True)  # Mean squared error for regression
    mae = db.Column(db.Float, nullable=True)  # Mean absolute error
    r2_score = db.Column(db.Float, nullable=True)  # R-squared for regression
    
    # Model status
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_trained = db.Column(db.Boolean, default=False, nullable=False)
    model_version = db.Column(db.String(20), nullable=False, default='1.0')
    
    # Prediction data
    last_prediction_date = db.Column(db.DateTime, nullable=True)
    total_predictions = db.Column(db.Integer, default=0, nullable=False)
    successful_predictions = db.Column(db.Integer, default=0, nullable=False)
    
    # Model file storage (if applicable)
    model_file_path = db.Column(db.String(500), nullable=True)
    model_size = db.Column(db.Integer, nullable=True)  # in bytes
    
    # Metadata
    description = db.Column(db.Text, nullable=True)
    tags = db.Column(db.JSON, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_trained_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    creator = db.relationship('User', backref='created_models', lazy=True)
    
    # Constraints
    __table_args__ = (
        CheckConstraint('accuracy >= 0', name='check_accuracy_min'),
        CheckConstraint('accuracy <= 1', name='check_accuracy_max'),
        CheckConstraint('precision >= 0', name='check_precision_min'),
        CheckConstraint('precision <= 1', name='check_precision_max'),
        CheckConstraint('recall >= 0', name='check_recall_min'),
        CheckConstraint('recall <= 1', name='check_recall_max'),
        CheckConstraint('f1_score >= 0', name='check_f1_score_min'),
        CheckConstraint('f1_score <= 1', name='check_f1_score_max'),
        CheckConstraint('r2_score >= -1', name='check_r2_score_min'),
        CheckConstraint('r2_score <= 1', name='check_r2_score_max'),
        Index('idx_predictive_models_target', 'prediction_target', 'is_active'),
        Index('idx_predictive_models_type', 'model_type', 'is_trained'),
        Index('idx_predictive_models_performance', 'accuracy', 'f1_score'),
    )
    
    def __repr__(self):
        return f'<PredictiveModel {self.model_name}:{self.model_type}>'
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'model_name': self.model_name,
            'model_type': self.model_type,
            'prediction_target': self.prediction_target,
            'model_config': self.model_config,
            'feature_columns': self.feature_columns,
            'target_column': self.target_column,
            'training_samples': self.training_samples,
            'training_start_date': self.training_start_date.isoformat() if self.training_start_date else None,
            'training_end_date': self.training_end_date.isoformat() if self.training_end_date else None,
            'validation_samples': self.validation_samples,
            'accuracy': self.accuracy,
            'precision': self.precision,
            'recall': self.recall,
            'f1_score': self.f1_score,
            'mse': self.mse,
            'mae': self.mae,
            'r2_score': self.r2_score,
            'is_active': self.is_active,
            'is_trained': self.is_trained,
            'model_version': self.model_version,
            'last_prediction_date': self.last_prediction_date.isoformat() if self.last_prediction_date else None,
            'total_predictions': self.total_predictions,
            'successful_predictions': self.successful_predictions,
            'model_file_path': self.model_file_path,
            'model_size': self.model_size,
            'description': self.description,
            'tags': self.tags,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_trained_at': self.last_trained_at.isoformat() if self.last_trained_at else None
        }

# Helper functions for analytics initialization
class UserActivity(db.Model):
    """User behavior tracking model for comprehensive user activity analytics"""
    __tablename__ = 'user_activity'
    __table_args__ = (
        Index('idx_user_activity_user_time', 'user_id', 'activity_timestamp'),
        Index('idx_user_activity_type', 'activity_type'),
        Index('idx_user_activity_session', 'session_id', 'activity_timestamp'),
        {'extend_existing': True}
    )
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    session_id = db.Column(db.String(128), nullable=True, index=True)
    activity_type = db.Column(db.String(50), nullable=False, index=True)  # login, logout, post, comment, like, share, view
    activity_category = db.Column(db.String(50), nullable=False, index=True)  # engagement, content, social, system
    activity_timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Activity details
    target_type = db.Column(db.String(50), nullable=True, index=True)  # post, comment, user, etc.
    target_id = db.Column(db.Integer, nullable=True, index=True)
    activity_value = db.Column(db.Float, nullable=True)  # Numeric value for activity
    activity_duration = db.Column(db.Float, nullable=True)  # Duration in seconds
    activity_metadata = db.Column(db.JSON)  # Additional activity metadata
    
    # Context information
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.Text, nullable=True)
    referrer = db.Column(db.String(500), nullable=True)
    page_url = db.Column(db.String(1000), nullable=True)
    
    # Geolocation data
    country = db.Column(db.String(2), nullable=True)
    region = db.Column(db.String(100), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    
    # Device information
    device_type = db.Column(db.String(20), nullable=True)  # desktop, mobile, tablet
    browser = db.Column(db.String(50), nullable=True)
    operating_system = db.Column(db.String(50), nullable=True)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('user_activities', lazy='dynamic', cascade='all, delete-orphan'))
    
    def __repr__(self):
        return f'<UserActivity {self.user_id}:{self.activity_type}:{self.activity_timestamp}>'
    
    @classmethod
    def track_activity(cls, user_id, activity_type, activity_category, session_id=None, 
                      target_type=None, target_id=None, activity_value=None, 
                      activity_duration=None, metadata=None, ip_address=None, 
                      user_agent=None, referrer=None, page_url=None, 
                      country=None, region=None, city=None, device_type=None, 
                      browser=None, operating_system=None):
        """Track a user activity"""
        activity = cls(
            user_id=user_id,
            session_id=session_id,
            activity_type=activity_type,
            activity_category=activity_category,
            target_type=target_type,
            target_id=target_id,
            activity_value=activity_value,
            activity_duration=activity_duration,
            activity_metadata=metadata or {},
            ip_address=ip_address,
            user_agent=user_agent,
            referrer=referrer,
            page_url=page_url,
            country=country,
            region=region,
            city=city,
            device_type=device_type,
            browser=browser,
            operating_system=operating_system
        )
        db.session.add(activity)
        db.session.commit()
        return activity
    
    @classmethod
    def get_user_activities(cls, user_id, activity_type=None, start_date=None, end_date=None, limit=None):
        """Get activities for a user"""
        query = cls.query.filter_by(user_id=user_id)
        
        if activity_type:
            query = query.filter_by(activity_type=activity_type)
        
        if start_date:
            query = query.filter(cls.activity_timestamp >= start_date)
        
        if end_date:
            query = query.filter(cls.activity_timestamp <= end_date)
        
        return query.order_by(cls.activity_timestamp.desc()).limit(limit).all()
    
    @classmethod
    def get_activity_summary(cls, user_id, days=30):
        """Get activity summary for a user"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        activities = cls.query.filter(
            cls.user_id == user_id,
            cls.activity_timestamp >= start_date
        ).all()
        
        summary = {
            'total_activities': len(activities),
            'by_type': {},
            'by_category': {},
            'by_day': {},
            'engagement_score': 0.0
        }
        
        for activity in activities:
            # Count by type
            activity_type = activity.activity_type
            if activity_type not in summary['by_type']:
                summary['by_type'][activity_type] = 0
            summary['by_type'][activity_type] += 1
            
            # Count by category
            activity_category = activity.activity_category
            if activity_category not in summary['by_category']:
                summary['by_category'][activity_category] = 0
            summary['by_category'][activity_category] += 1
            
            # Count by day
            day_key = activity.activity_timestamp.strftime('%Y-%m-%d')
            if day_key not in summary['by_day']:
                summary['by_day'][day_key] = 0
            summary['by_day'][day_key] += 1
        
        # Calculate engagement score
        engagement_activities = ['post', 'comment', 'like', 'share']
        engagement_count = sum(summary['by_type'].get(activity_type, 0) for activity_type in engagement_activities)
        summary['engagement_score'] = (engagement_count / max(len(activities), 1)) * 100
        
        return summary


class ContentAnalytics(db.Model):
    """Content performance data model for comprehensive content analytics"""
    __tablename__ = 'content_analytics'
    __table_args__ = (
        Index('idx_content_analytics_target', 'target_type', 'target_id'),
        Index('idx_content_analytics_time', 'analytics_timestamp'),
        Index('idx_content_analytics_metric', 'metric_type'),
        {'extend_existing': True}
    )
    
    id = db.Column(db.Integer, primary_key=True)
    target_type = db.Column(db.String(50), nullable=False, index=True)  # post, comment, user, etc.
    target_id = db.Column(db.Integer, nullable=False, index=True)
    metric_type = db.Column(db.String(50), nullable=False, index=True)  # views, likes, shares, comments, engagement
    metric_value = db.Column(db.Float, nullable=False)
    metric_change = db.Column(db.Float, nullable=True)  # Change from previous period
    metric_change_percent = db.Column(db.Float, nullable=True)  # Percentage change
    analytics_timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Analytics metadata
    analytics_period = db.Column(db.String(20), default='daily')  # hourly, daily, weekly, monthly
    period_start = db.Column(db.DateTime, nullable=False)
    period_end = db.Column(db.DateTime, nullable=False)
    
    # Additional metrics
    unique_views = db.Column(db.Integer, default=0)
    total_views = db.Column(db.Integer, default=0)
    bounce_rate = db.Column(db.Float, default=0.0)
    avg_time_on_page = db.Column(db.Float, default=0.0)  # in seconds
    conversion_rate = db.Column(db.Float, default=0.0)
    
    # Engagement metrics
    likes_count = db.Column(db.Integer, default=0)
    shares_count = db.Column(db.Integer, default=0)
    comments_count = db.Column(db.Integer, default=0)
    saves_count = db.Column(db.Integer, default=0)
    reports_count = db.Column(db.Integer, default=0)
    
    # Quality metrics
    quality_score = db.Column(db.Float, default=0.0)  # 0-100
    relevance_score = db.Column(db.Float, default=0.0)  # 0-100
    sentiment_score = db.Column(db.Float, default=0.0)  # -1 to 1
    
    # Metadata
    analytics_metadata = db.Column(db.JSON)  # Additional analytics metadata
    
    def __repr__(self):
        return f'<ContentAnalytics {self.target_type}:{self.target_id}:{self.metric_type}>'
    
    @classmethod
    def track_metric(cls, target_type, target_id, metric_type, metric_value, 
                    analytics_period='daily', period_start=None, period_end=None,
                    unique_views=None, total_views=None, bounce_rate=None,
                    avg_time_on_page=None, conversion_rate=None, likes_count=None,
                    shares_count=None, comments_count=None, saves_count=None,
                    reports_count=None, quality_score=None, relevance_score=None,
                    sentiment_score=None, metadata=None):
        """Track a content analytics metric"""
        # Set default period if not provided
        if not period_start:
            period_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        if not period_end:
            if analytics_period == 'hourly':
                period_end = period_start + timedelta(hours=1)
            elif analytics_period == 'daily':
                period_end = period_start + timedelta(days=1)
            elif analytics_period == 'weekly':
                period_end = period_start + timedelta(weeks=1)
            elif analytics_period == 'monthly':
                period_end = period_start + timedelta(days=30)
            else:
                period_end = period_start + timedelta(days=1)
        
        # Check if metric already exists for this period
        existing = cls.query.filter_by(
            target_type=target_type,
            target_id=target_id,
            metric_type=metric_type,
            analytics_period=analytics_period,
            period_start=period_start
        ).first()
        
        if existing:
            # Update existing metric
            previous_value = existing.metric_value
            existing.metric_value = metric_value
            existing.metric_change = metric_value - previous_value
            existing.metric_change_percent = ((metric_value - previous_value) / max(previous_value, 1)) * 100
            
            # Update additional metrics
            if unique_views is not None:
                existing.unique_views = unique_views
            if total_views is not None:
                existing.total_views = total_views
            if bounce_rate is not None:
                existing.bounce_rate = bounce_rate
            if avg_time_on_page is not None:
                existing.avg_time_on_page = avg_time_on_page
            if conversion_rate is not None:
                existing.conversion_rate = conversion_rate
            if likes_count is not None:
                existing.likes_count = likes_count
            if shares_count is not None:
                existing.shares_count = shares_count
            if comments_count is not None:
                existing.comments_count = comments_count
            if saves_count is not None:
                existing.saves_count = saves_count
            if reports_count is not None:
                existing.reports_count = reports_count
            if quality_score is not None:
                existing.quality_score = quality_score
            if relevance_score is not None:
                existing.relevance_score = relevance_score
            if sentiment_score is not None:
                existing.sentiment_score = sentiment_score
            if metadata is not None:
                existing.analytics_metadata = metadata
            
            existing.analytics_timestamp = datetime.utcnow()
            db.session.commit()
            return existing
        else:
            # Create new metric
            analytics = cls(
                target_type=target_type,
                target_id=target_id,
                metric_type=metric_type,
                metric_value=metric_value,
                analytics_period=analytics_period,
                period_start=period_start,
                period_end=period_end,
                unique_views=unique_views or 0,
                total_views=total_views or 0,
                bounce_rate=bounce_rate or 0.0,
                avg_time_on_page=avg_time_on_page or 0.0,
                conversion_rate=conversion_rate or 0.0,
                likes_count=likes_count or 0,
                shares_count=shares_count or 0,
                comments_count=comments_count or 0,
                saves_count=saves_count or 0,
                reports_count=reports_count or 0,
                quality_score=quality_score or 0.0,
                relevance_score=relevance_score or 0.0,
                sentiment_score=sentiment_score or 0.0,
                analytics_metadata=metadata or {}
            )
            db.session.add(analytics)
            db.session.commit()
            return analytics
    
    @classmethod
    def get_content_metrics(cls, target_type, target_id, metric_type=None, 
                          analytics_period='daily', start_date=None, end_date=None, limit=None):
        """Get analytics metrics for content"""
        query = cls.query.filter_by(
            target_type=target_type,
            target_id=target_id,
            analytics_period=analytics_period
        )
        
        if metric_type:
            query = query.filter_by(metric_type=metric_type)
        
        if start_date:
            query = query.filter(cls.period_start >= start_date)
        
        if end_date:
            query = query.filter(cls.period_end <= end_date)
        
        return query.order_by(cls.period_start.desc()).limit(limit).all()
    
    @classmethod
    def get_content_summary(cls, target_type, target_id, days=30):
        """Get comprehensive content analytics summary"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        metrics = cls.query.filter(
            cls.target_type == target_type,
            cls.target_id == target_id,
            cls.period_start >= start_date
        ).all()
        
        summary = {
            'total_views': 0,
            'unique_views': 0,
            'avg_engagement': 0.0,
            'quality_score': 0.0,
            'sentiment_score': 0.0,
            'daily_metrics': {}
        }
        
        for metric in metrics:
            # Aggregate totals
            if metric.metric_type == 'views':
                summary['total_views'] += int(metric.metric_value)
            elif metric.metric_type == 'unique_views':
                summary['unique_views'] += int(metric.metric_value)
            
            # Calculate averages
            if metric.quality_score:
                summary['quality_score'] = (summary['quality_score'] + metric.quality_score) / 2
            if metric.sentiment_score:
                summary['sentiment_score'] = (summary['sentiment_score'] + metric.sentiment_score) / 2
            
            # Daily breakdown
            day_key = metric.period_start.strftime('%Y-%m-%d')
            if day_key not in summary['daily_metrics']:
                summary['daily_metrics'][day_key] = {
                    'views': 0,
                    'likes': 0,
                    'shares': 0,
                    'comments': 0
                }
            
            if metric.metric_type == 'views':
                summary['daily_metrics'][day_key]['views'] += int(metric.metric_value)
            elif metric.metric_type == 'likes':
                summary['daily_metrics'][day_key]['likes'] += int(metric.metric_value)
            elif metric.metric_type == 'shares':
                summary['daily_metrics'][day_key]['shares'] += int(metric.metric_value)
            elif metric.metric_type == 'comments':
                summary['daily_metrics'][day_key]['comments'] += int(metric.metric_value)
        
        # Calculate engagement rate
        total_interactions = summary['daily_metrics'].get('likes', 0) + \
                           summary['daily_metrics'].get('shares', 0) + \
                           summary['daily_metrics'].get('comments', 0)
        summary['avg_engagement'] = (total_interactions / max(summary['total_views'], 1)) * 100
        
        return summary


def initialize_analytics_tables():
    """Initialize analytics tables with default data"""
    from datetime import datetime, timedelta
    
    # Create default system metrics
    default_metrics = [
        {
            'metric_type': 'performance',
            'metric_category': 'response_time',
            'metric_name': 'avg_response_time',
            'current_value': 150.0,
            'threshold_warning': 500.0,
            'threshold_critical': 1000.0,
            'health_status': 'healthy'
        },
        {
            'metric_type': 'performance',
            'metric_category': 'cpu',
            'metric_name': 'cpu_usage',
            'current_value': 25.0,
            'threshold_warning': 70.0,
            'threshold_critical': 90.0,
            'health_status': 'healthy'
        },
        {
            'metric_type': 'performance',
            'metric_category': 'memory',
            'metric_name': 'memory_usage',
            'current_value': 45.0,
            'threshold_warning': 75.0,
            'threshold_critical': 90.0,
            'health_status': 'healthy'
        },
        {
            'metric_type': 'user',
            'metric_category': 'activity',
            'metric_name': 'active_users',
            'current_value': 0.0,
            'health_status': 'healthy'
        },
        {
            'metric_type': 'database',
            'metric_category': 'performance',
            'metric_name': 'avg_query_time',
            'current_value': 25.0,
            'threshold_warning': 100.0,
            'threshold_critical': 500.0,
            'health_status': 'healthy'
        }
    ]
    
    for metric_data in default_metrics:
        existing = SystemMetrics.query.filter_by(
            metric_type=metric_data['metric_type'],
            metric_category=metric_data['metric_category'],
            metric_name=metric_data['metric_name']
        ).first()
        
        if not existing:
            metric = SystemMetrics(**metric_data)
            db.session.add(metric)
    
    db.session.commit()
    print("Analytics tables initialized successfully")
