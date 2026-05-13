"""
Advanced User Analytics Package

This package contains all advanced user analytics functionality including:
- User behavior analytics
- Engagement metrics tracking
- User performance dashboards
- Predictive analytics
- User segmentation
"""

from .models import (
    UserBehavior, UserEngagement, UserPerformance, UserSegment, 
    UserPrediction, UserDashboard, SegmentUser
)

from .forms import (
    AnalyticsDateRangeForm, UserBehaviorFilterForm, EngagementMetricsForm,
    PerformanceMetricsForm, UserSegmentForm, EditUserSegmentForm,
    PredictionConfigForm, UserSearchForm, DashboardConfigForm,
    WidgetConfigForm, AnalyticsExportForm, AnalyticsSettingsForm,
    ComparisonForm
)

from .routes import analytics_bp

__all__ = [
    # Models
    'UserBehavior', 'UserEngagement', 'UserPerformance', 'UserSegment', 
    'UserPrediction', 'UserDashboard', 'SegmentUser',
    
    # Forms
    'AnalyticsDateRangeForm', 'UserBehaviorFilterForm', 'EngagementMetricsForm',
    'PerformanceMetricsForm', 'UserSegmentForm', 'EditUserSegmentForm',
    'PredictionConfigForm', 'UserSearchForm', 'DashboardConfigForm',
    'WidgetConfigForm', 'AnalyticsExportForm', 'AnalyticsSettingsForm',
    'ComparisonForm',
    
    # Blueprint
    'analytics_bp'
]
