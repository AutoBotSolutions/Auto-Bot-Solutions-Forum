"""
Advanced Analytics System

This module provides comprehensive analytics and reporting functionality for the Auto Bot Solutions Forum,
including real-time analytics, user behavior analysis, content performance metrics, system monitoring,
and predictive analytics with trend analysis.
"""

from .models import (
    AnalyticsEvent,
    UserBehavior,
    ContentPerformance,
    SystemMetrics,
    TrendAnalysis,
    PredictiveModel
)

from .service import (
    AnalyticsService,
    UserBehaviorService,
    ContentPerformanceService,
    SystemMetricsService,
    TrendAnalysisService,
    PredictiveAnalyticsService
)

from .forms import (
    AnalyticsFilterForm,
    UserBehaviorFilterForm,
    ContentPerformanceFilterForm,
    SystemMetricsFilterForm,
    TrendAnalysisForm,
    PredictiveModelForm
)

from .routes import analytics_bp

__all__ = [
    'AnalyticsEvent',
    'UserBehavior',
    'ContentPerformance',
    'SystemMetrics',
    'TrendAnalysis',
    'PredictiveModel',
    'AnalyticsService',
    'UserBehaviorService',
    'ContentPerformanceService',
    'SystemMetricsService',
    'TrendAnalysisService',
    'PredictiveAnalyticsService',
    'AnalyticsFilterForm',
    'UserBehaviorFilterForm',
    'ContentPerformanceFilterForm',
    'SystemMetricsFilterForm',
    'TrendAnalysisForm',
    'PredictiveModelForm',
    'analytics_bp'
]
