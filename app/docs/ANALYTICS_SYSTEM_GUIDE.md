# Analytics and Metrics System Guide

## Overview

The Analytics and Metrics System provides comprehensive user behavior tracking, content performance analysis, system health monitoring, and predictive analytics capabilities. This guide covers implementation details, usage patterns, and best practices.

## Quick Start

### Basic Activity Tracking

```python
from app.analytics.models import UserActivity

# Track user activity
UserActivity.track_activity(
    user_id=123,
    activity_type="login",
    activity_category="engagement",
    session_id="session_123",
    ip_address="192.168.1.1"
)
```

### Content Analytics

```python
from app.analytics.models import ContentAnalytics

# Track content performance
ContentAnalytics.track_metric(
    target_type="post",
    target_id=456,
    metric_type="views",
    metric_value=1.0,
    unique_views=1
)
```

## Core Components

### UserActivity Model

The `UserActivity` model provides comprehensive user behavior tracking with geolocation and device data.

#### Key Features
- **Activity Tracking**: Detailed user action logging
- **Session Management**: Session-based activity grouping
- **Geolocation**: IP-based location tracking
- **Device Detection**: Browser and device identification
- **Performance Metrics**: Activity duration and timing

#### Usage Examples

```python
from app.analytics.models import UserActivity

# Track login activity
UserActivity.track_activity(
    user_id=current_user.id,
    activity_type="login",
    activity_category="engagement",
    session_id=session_id,
    ip_address=request.remote_addr,
    user_agent=request.headers.get('User-Agent'),
    page_url=request.url
)

# Track content interaction
UserActivity.track_activity(
    user_id=current_user.id,
    activity_type="post_view",
    activity_category="engagement",
    target_type="post",
    target_id=post.id,
    activity_duration=5.2,  # seconds spent viewing
    referrer=request.referrer
)

# Track social interaction
UserActivity.track_activity(
    user_id=current_user.id,
    activity_type="like",
    activity_category="social",
    target_type="post",
    target_id=post.id,
    activity_value=1.0
)

# Get user activity summary
summary = UserActivity.get_activity_summary(user_id=123, days=30)
print(f"Total activities: {summary['total_activities']}")
print(f"Engagement score: {summary['engagement_score']:.1f}%")
print(f"Activities by type: {summary['by_type']}")
```

### ContentAnalytics Model

The `ContentAnalytics` model provides content performance metrics with quality scoring and sentiment analysis.

#### Key Features
- **Performance Tracking**: Views, likes, shares, comments
- **Quality Scoring**: Automated content quality assessment
- **Sentiment Analysis**: Content sentiment evaluation
- **Engagement Metrics**: Comprehensive engagement tracking
- **Trend Analysis**: Performance trends over time

#### Usage Examples

```python
from app.analytics.models import ContentAnalytics

# Track content views
ContentAnalytics.track_metric(
    target_type="post",
    target_id=post.id,
    metric_type="views",
    metric_value=1.0,
    unique_views=1,
    total_views=1,
    avg_time_on_page=15.5,
    bounce_rate=0.3
)

# Track engagement metrics
ContentAnalytics.track_metric(
    target_type="post",
    target_id=post.id,
    metric_type="engagement",
    metric_value=5.0,
    likes_count=10,
    shares_count=3,
    comments_count=2,
    saves_count=1
)

# Track content quality
ContentAnalytics.track_metric(
    target_type="post",
    target_id=post.id,
    metric_type="quality",
    metric_value=8.5,
    quality_score=8.5,
    relevance_score=9.0,
    sentiment_score=0.7
)

# Get content performance summary
summary = ContentAnalytics.get_content_summary("post", post.id, days=30)
print(f"Total views: {summary['total_views']}")
print(f"Average engagement: {summary['avg_engagement']:.1f}%")
print(f"Quality score: {summary['quality_score']:.1f}")
print(f"Daily metrics: {summary['daily_metrics']}")
```

### SystemMetrics Model

The `SystemMetrics` model provides system performance monitoring with health tracking.

#### Key Features
- **Performance Monitoring**: CPU, memory, disk usage
- **Health Tracking**: System health status monitoring
- **Threshold Alerts**: Configurable warning and critical thresholds
- **Historical Data**: Performance trend tracking
- **Automated Collection**: Scheduled metric collection

#### Usage Examples

```python
from app.analytics.models import SystemMetrics

# Track system performance
SystemMetrics(
    metric_type="system",
    metric_category="performance",
    metric_name="cpu_usage",
    current_value=75.5,
    threshold_warning=80.0,
    threshold_critical=95.0,
    health_status="healthy"
).save()

# Track database performance
SystemMetrics(
    metric_type="database",
    metric_category="performance",
    metric_name="avg_query_time",
    current_value=125.0,
    threshold_warning=200.0,
    threshold_critical=500.0,
    health_status="healthy"
).save()

# Track user activity metrics
SystemMetrics(
    metric_type="user",
    metric_category="activity",
    metric_name="active_users",
    current_value=1250,
    health_status="healthy"
).save()

# Get system health status
health_metrics = SystemMetrics.query.filter_by(
    metric_type="system",
    metric_category="performance"
).all()

for metric in health_metrics:
    print(f"{metric.metric_name}: {metric.current_value} ({metric.health_status})")
```

### PredictiveModel Model

The `PredictiveModel` model provides machine learning model management with performance tracking.

#### Key Features
- **Model Management**: Model versioning and lifecycle management
- **Performance Tracking**: Accuracy, precision, recall metrics
- **Prediction Logging**: Prediction history and outcomes
- **Model Comparison**: Performance comparison between models
- **Automated Retraining**: Scheduled model retraining

#### Usage Examples

```python
from app.analytics.models import PredictiveModel

# Create predictive model
model = PredictiveModel(
    model_name="user_churn_prediction",
    model_type="classification",
    model_version="1.0",
    description="Predicts user churn based on activity patterns",
    accuracy=0.85,
    precision=0.82,
    recall=0.88,
    f1_score=0.85,
    model_size=1024000,  # bytes
    created_by="data_scientist",
    tags=["churn", "classification", "user_behavior"]
)
model.save()

# Track model performance
model.update_performance(
    accuracy=0.87,
    precision=0.84,
    recall=0.90,
    f1_score=0.87
)

# Log prediction
prediction = model.log_prediction(
    input_data={"user_id": 123, "activity_score": 0.75},
    prediction_result=0.2,  # 20% churn probability
    confidence=0.92,
    actual_outcome=None  # Will be updated later
)

# Get model performance history
performance_history = model.get_performance_history(days=30)
```

## Analytics Implementation

### Flask Application Integration

```python
from flask import Flask, request
from app.analytics.models import UserActivity, ContentAnalytics

app = Flask(__name__)

@app.before_request
def track_request():
    """Track all requests for analytics"""
    if current_user.is_authenticated:
        UserActivity.track_activity(
            user_id=current_user.id,
            activity_type="page_view",
            activity_category="navigation",
            page_url=request.url,
            referrer=request.referrer,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )

@app.after_request
def track_response(response):
    """Track response analytics"""
    if hasattr(request, 'post_id'):
        ContentAnalytics.track_metric(
            target_type="post",
            target_id=request.post_id,
            metric_type="views",
            metric_value=1.0,
            unique_views=1 if not session.get(f'viewed_post_{request.post_id}') else 0
        )
        session[f'viewed_post_{request.post_id}'] = True
    
    return response
```

### Background Analytics Processing

```python
from celery import Celery
from app.analytics.models import UserActivity, ContentAnalytics, SystemMetrics

celery = Celery('analytics_tasks')

@celery.task
def process_user_activity_batch(activity_data):
    """Process batch of user activities"""
    for data in activity_data:
        UserActivity.track_activity(**data)

@celery.task
def generate_daily_analytics():
    """Generate daily analytics reports"""
    from datetime import datetime, timedelta
    
    yesterday = datetime.utcnow() - timedelta(days=1)
    
    # User activity summary
    active_users = UserActivity.query.filter(
        UserActivity.activity_timestamp >= yesterday.date()
    ).distinct(UserActivity.user_id).count()
    
    SystemMetrics(
        metric_type="user",
        metric_category="activity",
        metric_name="daily_active_users",
        current_value=active_users
    ).save()
    
    # Content performance summary
    popular_content = ContentAnalytics.get_popular_content(
        start_date=yesterday.date(),
        limit=10
    )
    
    for content in popular_content:
        print(f"Popular content: {content['target_id']} ({content['total_views']} views)")

@celery.task
def update_system_metrics():
    """Collect system performance metrics"""
    import psutil
    
    # CPU usage
    cpu_percent = psutil.cpu_percent(interval=1)
    SystemMetrics(
        metric_type="system",
        metric_category="performance",
        metric_name="cpu_usage",
        current_value=cpu_percent
    ).save()
    
    # Memory usage
    memory = psutil.virtual_memory()
    SystemMetrics(
        metric_type="system",
        metric_category="performance",
        metric_name="memory_usage",
        current_value=memory.percent
    ).save()
    
    # Disk usage
    disk = psutil.disk_usage('/')
    disk_percent = (disk.used / disk.total) * 100
    SystemMetrics(
        metric_type="system",
        metric_category="performance",
        metric_name="disk_usage",
        current_value=disk_percent
    ).save()
```

### Analytics Dashboards

```python
from flask import Blueprint, jsonify, render_template
from app.analytics.models import UserActivity, ContentAnalytics, SystemMetrics

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/dashboard')
def analytics_dashboard():
    """Main analytics dashboard"""
    return render_template('analytics/dashboard.html')

@analytics_bp.route('/api/user-activity')
def user_activity_api():
    """User activity analytics API"""
    days = request.args.get('days', 30, type=int)
    
    # Daily active users
    daily_users = UserActivity.get_daily_active_users(days=days)
    
    # Activity by type
    activity_by_type = UserActivity.get_activity_by_type(days=days)
    
    # Top users by activity
    top_users = UserActivity.get_top_users(days=days, limit=10)
    
    return jsonify({
        'daily_users': daily_users,
        'activity_by_type': activity_by_type,
        'top_users': top_users
    })

@analytics_bp.route('/api/content-performance')
def content_performance_api():
    """Content performance analytics API"""
    days = request.args.get('days', 30, type=int)
    
    # Popular content
    popular_content = ContentAnalytics.get_popular_content(days=days, limit=20)
    
    # Content quality trends
    quality_trends = ContentAnalytics.get_quality_trends(days=days)
    
    # Engagement metrics
    engagement_metrics = ContentAnalytics.get_engagement_metrics(days=days)
    
    return jsonify({
        'popular_content': popular_content,
        'quality_trends': quality_trends,
        'engagement_metrics': engagement_metrics
    })

@analytics_bp.route('/api/system-health')
def system_health_api():
    """System health analytics API"""
    # Current system metrics
    current_metrics = SystemMetrics.get_current_metrics()
    
    # System health status
    health_status = SystemMetrics.get_health_status()
    
    # Performance trends
    performance_trends = SystemMetrics.get_performance_trends(days=7)
    
    return jsonify({
        'current_metrics': current_metrics,
        'health_status': health_status,
        'performance_trends': performance_trends
    })
```

## Advanced Analytics Features

### User Behavior Analysis

```python
from app.analytics.models import UserActivity

# User segmentation
def segment_users(days=30):
    """Segment users based on activity patterns"""
    start_date = datetime.utcnow() - timedelta(days=days)
    
    users = UserActivity.query.filter(
        UserActivity.activity_timestamp >= start_date
    ).all()
    
    segments = {
        'power_users': [],      # High activity
        'regular_users': [],    # Medium activity
        'casual_users': [],     # Low activity
        'dormant_users': []     # No activity
    }
    
    # Analyze each user's activity
    user_activities = {}
    for activity in users:
        if activity.user_id not in user_activities:
            user_activities[activity.user_id] = []
        user_activities[activity.user_id].append(activity)
    
    for user_id, activities in user_activities.items():
        total_activities = len(activities)
        engagement_score = calculate_engagement_score(activities)
        
        if engagement_score >= 80:
            segments['power_users'].append(user_id)
        elif engagement_score >= 50:
            segments['regular_users'].append(user_id)
        elif engagement_score >= 20:
            segments['casual_users'].append(user_id)
        else:
            segments['dormant_users'].append(user_id)
    
    return segments

def calculate_engagement_score(activities):
    """Calculate engagement score based on activities"""
    score = 0
    for activity in activities:
        if activity.activity_type in ['post', 'comment', 'like', 'share']:
            score += 10
        elif activity.activity_type in ['view', 'login']:
            score += 5
        elif activity.activity_type in ['profile_update', 'settings_change']:
            score += 3
    
    # Normalize to 0-100 scale
    max_possible_score = len(activities) * 10
    return min((score / max_possible_score) * 100, 100) if max_possible_score > 0 else 0
```

### Content Performance Prediction

```python
from app.analytics.models import ContentAnalytics, PredictiveModel

def predict_content_performance(content_data):
    """Predict content performance using machine learning"""
    model = PredictiveModel.query.filter_by(
        model_name="content_performance_prediction"
    ).first()
    
    if not model:
        return None
    
    # Extract features from content
    features = {
        'content_length': len(content_data.get('content', '')),
        'title_length': len(content_data.get('title', '')),
        'has_images': bool(content_data.get('images')),
        'has_videos': bool(content_data.get('videos')),
        'category': content_data.get('category'),
        'author_activity': get_author_activity_score(content_data.get('author_id')),
        'posting_time': extract_time_features(content_data.get('created_at'))
    }
    
    # Make prediction
    prediction = model.predict(features)
    
    return {
        'predicted_views': prediction.get('views'),
        'predicted_engagement': prediction.get('engagement'),
        'confidence': prediction.get('confidence'),
        'recommendations': generate_content_recommendations(features, prediction)
    }

def generate_content_recommendations(features, prediction):
    """Generate content improvement recommendations"""
    recommendations = []
    
    if features['content_length'] < 500:
        recommendations.append("Consider adding more detailed content")
    
    if not features['has_images']:
        recommendations.append("Add relevant images to increase engagement")
    
    if prediction['engagement'] < 0.3:
        recommendations.append("Content may need a more compelling title")
    
    return recommendations
```

### Real-time Analytics

```python
from flask_socketio import SocketIO, emit
from app.analytics.models import UserActivity, SystemMetrics

socketio = SocketIO()

@socketio.on('user_activity')
def handle_user_activity(data):
    """Handle real-time user activity"""
    UserActivity.track_activity(
        user_id=data['user_id'],
        activity_type=data['activity_type'],
        activity_category=data['activity_category'],
        **data.get('additional_data', {})
    )
    
    # Broadcast to analytics dashboard
    emit('activity_update', {
        'user_id': data['user_id'],
        'activity_type': data['activity_type'],
        'timestamp': datetime.utcnow().isoformat()
    }, broadcast=True)

@socketio.on('system_metrics')
def handle_system_metrics(data):
    """Handle real-time system metrics"""
    SystemMetrics(
        metric_type=data['metric_type'],
        metric_category=data['metric_category'],
        metric_name=data['metric_name'],
        current_value=data['current_value']
    ).save()
    
    # Broadcast to monitoring dashboard
    emit('metrics_update', data, broadcast=True)
```

## Configuration

### Analytics Configuration

```python
# app/analytics/config.py
ANALYTICS_CONFIG = {
    'tracking_enabled': True,
    'batch_processing': True,
    'batch_size': 100,
    'retention_days': 365,
    'real_time_enabled': True,
    'prediction_enabled': True,
    'dashboard_enabled': True,
    'export_enabled': True
}

# Data retention policies
RETENTION_POLICIES = {
    'user_activity': 365,      # days
    'content_analytics': 730,  # days
    'system_metrics': 90,       # days
    'predictions': 365         # days
}

# Privacy settings
PRIVACY_CONFIG = {
    'anonymize_ip_addresses': True,
    'retain_user_agents': False,
    'data_minimization': True,
    'gdpr_compliance': True
}
```

## Best Practices

### Data Collection

```python
# Collect only necessary data
UserActivity.track_activity(
    user_id=user.id,
    activity_type="page_view",
    activity_category="navigation",
    page_url=request.url,
    # Only collect IP if needed for analytics
    ip_address=request.remote_addr if ANALYTICS_CONFIG['track_ips'] else None
)

# Use batch processing for high-volume data
def batch_track_activities(activities):
    """Track multiple activities efficiently"""
    batch_size = ANALYTICS_CONFIG['batch_size']
    
    for i in range(0, len(activities), batch_size):
        batch = activities[i:i + batch_size]
        process_user_activity_batch.delay(batch)
```

### Performance Optimization

```python
# Use database indexes for queries
class UserActivity(db.Model):
    # ... existing fields ...
    
    __table_args__ = (
        Index('idx_user_activity_user_time', 'user_id', 'activity_timestamp'),
        Index('idx_user_activity_type', 'activity_type'),
        Index('idx_user_activity_session', 'session_id', 'activity_timestamp'),
    )

# Use aggregation for analytics queries
def get_daily_stats(date):
    """Get aggregated daily statistics"""
    return db.session.query(
        UserActivity.activity_type,
        func.count(UserActivity.id).label('count'),
        func.avg(UserActivity.activity_duration).label('avg_duration')
    ).filter(
        func.date(UserActivity.activity_timestamp) == date
    ).group_by(UserActivity.activity_type).all()
```

### Privacy and Compliance

```python
from app.analytics.models import UserActivity

def anonymize_user_data(user_id):
    """Anonymize user data for privacy compliance"""
    activities = UserActivity.query.filter_by(user_id=user_id).all()
    
    for activity in activities:
        activity.ip_address = None  # Remove IP
        activity.user_agent = None  # Remove user agent
        activity.user_id = None      # Remove user reference
    
    db.session.commit()

def export_user_data(user_id):
    """Export user data for GDPR compliance"""
    activities = UserActivity.query.filter_by(user_id=user_id).all()
    
    return {
        'user_id': user_id,
        'activities': [activity.to_dict() for activity in activities],
        'export_date': datetime.utcnow().isoformat()
    }
```

## Monitoring and Debugging

### Analytics Monitoring

```python
from app.analytics.models import SystemMetrics

def check_analytics_health():
    """Check analytics system health"""
    health_status = {
        'database_connection': check_database_connection(),
        'data_collection_rate': check_data_collection_rate(),
        'storage_usage': check_storage_usage(),
        'processing_lag': check_processing_lag()
    }
    
    return health_status

def check_data_collection_rate():
    """Check if data collection is within expected range"""
    recent_activities = UserActivity.query.filter(
        UserActivity.activity_timestamp >= datetime.utcnow() - timedelta(hours=1)
    ).count()
    
    expected_rate = 100  # activities per hour
    return {
        'current_rate': recent_activities,
        'expected_rate': expected_rate,
        'status': 'healthy' if recent_activities >= expected_rate * 0.8 else 'warning'
    }
```

### Debugging Tools

```python
# Analytics query debugging
def debug_user_activity(user_id, days=7):
    """Debug user activity tracking"""
    activities = UserActivity.query.filter_by(user_id=user_id).all()
    
    print(f"User {user_id} activities ({len(activities)} total):")
    for activity in activities[-10:]:  # Last 10 activities
        print(f"  {activity.activity_timestamp}: {activity.activity_type}")
    
    # Check for missing activities
    expected_activities = ['login', 'page_view', 'post_view']
    missing = [a for a in expected_activities if a not in [act.activity_type for act in activities]]
    if missing:
        print(f"Missing activity types: {missing}")

# Performance debugging
def debug_analytics_performance():
    """Debug analytics performance issues"""
    import time
    
    start_time = time.time()
    
    # Test query performance
    activities = UserActivity.query.filter(
        UserActivity.activity_timestamp >= datetime.utcnow() - timedelta(days=1)
    ).limit(1000).all()
    
    query_time = time.time() - start_time
    
    print(f"Query time: {query_time:.3f}s")
    print(f"Activities returned: {len(activities)}")
    
    if query_time > 1.0:
        print("WARNING: Slow query detected")
```

---

*Guide Last Updated: May 13, 2026*  
*Implementation Status: Production Ready*
