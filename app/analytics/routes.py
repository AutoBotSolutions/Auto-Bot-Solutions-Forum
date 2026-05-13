"""
Advanced Analytics Routes

This module contains Flask routes for the Advanced Analytics Dashboard,
including real-time analytics, user behavior analysis, content performance metrics,
system monitoring, trend analysis, and predictive analytics endpoints.
"""

from datetime import datetime, timedelta, timezone
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from sqlalchemy import and_, or_, desc, asc, func
from werkzeug.exceptions import NotFound, BadRequest

from app import db
from app.models import User, Post, Comment, Category
from .models import (
    AnalyticsEvent, UserBehavior, ContentPerformance, 
    SystemMetrics, TrendAnalysis, PredictiveModel
)
from .service import (
    AnalyticsService, UserBehaviorService, ContentPerformanceService,
    SystemMetricsService, TrendAnalysisService, PredictiveAnalyticsService
)
from .forms import (
    AnalyticsFilterForm, UserBehaviorFilterForm, ContentPerformanceFilterForm,
    SystemMetricsFilterForm, TrendAnalysisForm, PredictiveModelForm,
    ModelTrainingForm, AnalyticsExportForm, AnalyticsDashboardForm
)

# Create blueprint
analytics_bp = Blueprint('analytics', __name__, url_prefix='/analytics')

# Initialize services
analytics_service = AnalyticsService()
user_behavior_service = UserBehaviorService()
content_performance_service = ContentPerformanceService()
system_metrics_service = SystemMetricsService()
trend_analysis_service = TrendAnalysisService()
predictive_analytics_service = PredictiveAnalyticsService()

# Main analytics dashboard
@analytics_bp.route('/')
@login_required
def dashboard():
    """Main analytics dashboard"""
    # Get quick stats
    stats = {
        'total_events': AnalyticsEvent.query.count(),
        'total_users': User.query.count(),
        'total_posts': Post.query.count(),
        'total_comments': Comment.query.count(),
        'active_users_today': get_active_users_count(days=1),
        'active_users_week': get_active_users_count(days=7),
        'system_health': system_metrics_service.get_system_health()
    }
    
    # Get recent events
    recent_events = AnalyticsEvent.query.order_by(desc(AnalyticsEvent.created_at)).limit(10).all()
    
    # Get top performing content
    top_posts = content_performance_service.get_top_performing_content('post', limit=5)
    
    # Get system metrics
    system_metrics = system_metrics_service.get_performance_metrics()
    
    return render_template('analytics/dashboard.html',
                         stats=stats,
                         recent_events=recent_events,
                         top_posts=top_posts,
                         system_metrics=system_metrics)

@analytics_bp.route('/events')
@login_required
def events():
    """Analytics events page"""
    form = AnalyticsFilterForm(request.args)
    
    # Build query
    query = AnalyticsEvent.query
    
    # Apply filters
    if form.start_date.data:
        query = query.filter(AnalyticsEvent.created_at >= form.start_date.data)
    if form.end_date.data:
        end_date = datetime.combine(form.end_date.data, datetime.max.time())
        query = query.filter(AnalyticsEvent.created_at <= end_date)
    
    if form.event_type.data:
        query = query.filter(AnalyticsEvent.event_type == form.event_type.data)
    if form.event_category.data:
        query = query.filter(AnalyticsEvent.event_category == form.event_category.data)
    if form.user_id.data:
        query = query.filter(AnalyticsEvent.user_id == form.user_id.data)
    if form.target_type.data:
        query = query.filter(AnalyticsEvent.target_type == form.target_type.data)
    if form.target_id.data:
        query = query.filter(AnalyticsEvent.target_id == form.target_id.data)
    
    # Apply sorting
    if form.sort_by.data == 'date':
        if form.sort_order.data == 'asc':
            query = query.order_by(AnalyticsEvent.created_at.asc())
        else:
            query = query.order_by(AnalyticsEvent.created_at.desc())
    elif form.sort_by.data == 'count':
        # Group by event type and sort by count
        events = query.with_entities(
            AnalyticsEvent.event_type,
            func.count(AnalyticsEvent.id).label('count')
        ).group_by(AnalyticsEvent.event_type)
        
        if form.sort_order.data == 'asc':
            events = events.order_by(func.count(AnalyticsEvent.id).asc())
        else:
            events = events.order_by(func.count(AnalyticsEvent.id).desc())
        
        events = events.limit(form.limit.data or 100).all()
        
        return render_template('analytics/events_summary.html',
                             events=events,
                             form=form)
    else:
        query = query.order_by(AnalyticsEvent.created_at.desc())
    
    # Apply limit
    events = query.limit(form.limit.data or 100).all()
    
    return render_template('analytics/events.html',
                         events=events,
                         form=form)

@analytics_bp.route('/user-behavior')
@login_required
def user_behavior():
    """User behavior analytics page"""
    form = UserBehaviorFilterForm(request.args)
    
    # Build query
    query = UserBehavior.query
    
    # Apply filters
    if form.user_id.data:
        query = query.filter(UserBehavior.user_id == form.user_id.data)
    
    if form.min_sessions.data:
        query = query.filter(UserBehavior.total_sessions >= form.min_sessions.data)
    if form.max_sessions.data:
        query = query.filter(UserBehavior.total_sessions <= form.max_sessions.data)
    
    if form.min_engagement_score.data:
        query = query.filter(UserBehavior.engagement_score >= form.min_engagement_score.data)
    if form.max_engagement_score.data:
        query = query.filter(UserBehavior.engagement_score <= form.max_engagement_score.data)
    
    if form.min_posts_created.data:
        query = query.filter(UserBehavior.posts_created >= form.min_posts_created.data)
    if form.max_posts_created.data:
        query = query.filter(UserBehavior.posts_created <= form.max_posts_created.data)
    
    if form.last_active_since.data:
        query = query.filter(UserBehavior.last_active >= form.last_active_since.data)
    if form.last_active_before.data:
        last_active_before = datetime.combine(form.last_active_before.data, datetime.max.time())
        query = query.filter(UserBehavior.last_active <= last_active_before)
    
    # Apply sorting
    if form.sort_by.data == 'engagement_score':
        if form.sort_order.data == 'asc':
            query = query.order_by(UserBehavior.engagement_score.asc())
        else:
            query = query.order_by(UserBehavior.engagement_score.desc())
    elif form.sort_by.data == 'total_sessions':
        if form.sort_order.data == 'asc':
            query = query.order_by(UserBehavior.total_sessions.asc())
        else:
            query = query.order_by(UserBehavior.total_sessions.desc())
    elif form.sort_by.data == 'last_active':
        if form.sort_order.data == 'asc':
            query = query.order_by(UserBehavior.last_active.asc())
        else:
            query = query.order_by(UserBehavior.last_active.desc())
    else:
        query = query.order_by(UserBehavior.engagement_score.desc())
    
    # Apply limit
    behaviors = query.limit(form.limit.data or 50).all()
    
    return render_template('analytics/user_behavior.html',
                         behaviors=behaviors,
                         form=form)

@analytics_bp.route('/content-performance')
@login_required
def content_performance():
    """Content performance analytics page"""
    form = ContentPerformanceFilterForm(request.args)
    
    # Build query
    query = ContentPerformance.query
    
    # Apply filters
    if form.content_type.data:
        query = query.filter(ContentPerformance.content_type == form.content_type.data)
    if form.content_id.data:
        query = query.filter(ContentPerformance.content_id == form.content_id.data)
    
    if form.min_performance_score.data:
        query = query.filter(ContentPerformance.performance_score >= form.min_performance_score.data)
    if form.max_performance_score.data:
        query = query.filter(ContentPerformance.performance_score <= form.max_performance_score.data)
    
    if form.min_views.data:
        query = query.filter(ContentPerformance.total_views >= form.min_views.data)
    if form.max_views.data:
        query = query.filter(ContentPerformance.total_views <= form.max_views.data)
    
    if form.view_trend.data:
        query = query.filter(ContentPerformance.view_trend == form.view_trend.data)
    
    if form.created_since.data:
        query = query.filter(ContentPerformance.created_at >= form.created_since.data)
    if form.created_before.data:
        created_before = datetime.combine(form.created_before.data, datetime.max.time())
        query = query.filter(ContentPerformance.created_at <= created_before)
    
    # Apply sorting
    if form.sort_by.data == 'performance_score':
        if form.sort_order.data == 'asc':
            query = query.order_by(ContentPerformance.performance_score.asc())
        else:
            query = query.order_by(ContentPerformance.performance_score.desc())
    elif form.sort_by.data == 'total_views':
        if form.sort_order.data == 'asc':
            query = query.order_by(ContentPerformance.total_views.asc())
        else:
            query = query.order_by(ContentPerformance.total_views.desc())
    elif form.sort_by.data == 'created_at':
        if form.sort_order.data == 'asc':
            query = query.order_by(ContentPerformance.created_at.asc())
        else:
            query = query.order_by(ContentPerformance.created_at.desc())
    else:
        query = query.order_by(ContentPerformance.performance_score.desc())
    
    # Apply limit
    performances = query.limit(form.limit.data or 50).all()
    
    return render_template('analytics/content_performance.html',
                         performances=performances,
                         form=form)

@analytics_bp.route('/system-metrics')
@login_required
def system_metrics():
    """System metrics monitoring page"""
    form = SystemMetricsFilterForm(request.args)
    
    # Build query
    query = SystemMetrics.query
    
    # Apply filters
    if form.metric_type.data:
        query = query.filter(SystemMetrics.metric_type == form.metric_type.data)
    if form.metric_category.data:
        query = query.filter(SystemMetrics.metric_category == form.metric_category.data)
    if form.metric_name.data:
        query = query.filter(SystemMetrics.metric_name.like(f'%{form.metric_name.data}%'))
    
    if form.health_status.data:
        query = query.filter(SystemMetrics.health_status == form.health_status.data)
    
    if form.min_value.data:
        query = query.filter(SystemMetrics.current_value >= form.min_value.data)
    if form.max_value.data:
        query = query.filter(SystemMetrics.current_value <= form.max_value.data)
    
    if form.recorded_since.data:
        query = query.filter(SystemMetrics.recorded_at >= form.recorded_since.data)
    if form.recorded_before.data:
        query = query.filter(SystemMetrics.recorded_at <= form.recorded_before.data)
    
    # Apply sorting
    if form.sort_by.data == 'recorded_at':
        if form.sort_order.data == 'asc':
            query = query.order_by(SystemMetrics.recorded_at.asc())
        else:
            query = query.order_by(SystemMetrics.recorded_at.desc())
    elif form.sort_by.data == 'current_value':
        if form.sort_order.data == 'asc':
            query = query.order_by(SystemMetrics.current_value.asc())
        else:
            query = query.order_by(SystemMetrics.current_value.desc())
    else:
        query = query.order_by(SystemMetrics.recorded_at.desc())
    
    # Apply limit
    metrics = query.limit(form.limit.data or 100).all()
    
    # Get system health summary
    health_summary = system_metrics_service.get_system_health()
    
    return render_template('analytics/system_metrics.html',
                         metrics=metrics,
                         health_summary=health_summary,
                         form=form)

@analytics_bp.route('/trends')
@login_required
def trends():
    """Trend analysis page"""
    form = TrendAnalysisForm(request.args)
    
    trends = []
    if form.validate():
        try:
            # Get trend analysis
            target_id = form.target_id.data if form.target_id.data else None
            trend = trend_analysis_service.analyze_trend(
                target_type=form.target_type.data,
                target_id=target_id,
                metric_name=form.metric_name.data,
                period_days=form.period_days.data
            )
            trends = [trend]
        except Exception as e:
            flash(f'Error analyzing trend: {str(e)}', 'error')
    
    return render_template('analytics/trends.html',
                         trends=trends,
                         form=form)

@analytics_bp.route('/predictive-models')
@login_required
def predictive_models():
    """Predictive models management page"""
    models = PredictiveModel.query.filter_by(is_active=True).all()
    
    return render_template('analytics/predictive_models.html',
                         models=models)

@analytics_bp.route('/predictive-models/create', methods=['GET', 'POST'])
@login_required
def create_predictive_model():
    """Create new predictive model"""
    form = PredictiveModelForm()
    
    if form.validate_on_submit():
        try:
            model = predictive_analytics_service.create_predictive_model(
                model_name=form.model_name.data,
                model_type=form.model_type.data,
                prediction_target=form.prediction_target.data,
                model_config={
                    'algorithm': form.algorithm.data,
                    'max_depth': form.max_depth.data,
                    'n_estimators': form.n_estimators.data,
                    'learning_rate': form.learning_rate.data,
                    'regularization': form.regularization.data,
                    'cross_validation': form.cross_validation.data,
                    'cv_folds': form.cv_folds.data,
                    'feature_scaling': form.feature_scaling.data,
                    'feature_selection': form.feature_selection.data
                },
                feature_columns=form.feature_columns.data,
                target_column=form.target_column.data,
                description=form.description.data
            )
            
            flash('Predictive model created successfully!', 'success')
            return redirect(url_for('analytics.predictive_models'))
            
        except Exception as e:
            flash(f'Error creating model: {str(e)}', 'error')
    
    return render_template('analytics/create_predictive_model.html',
                         form=form)

@analytics_bp.route('/predictive-models/<int:model_id>/train', methods=['GET', 'POST'])
@login_required
def train_predictive_model(model_id):
    """Train predictive model"""
    model = PredictiveModel.query.get_or_404(model_id)
    
    form = ModelTrainingForm()
    form.model_id.data = model_id
    
    if form.validate_on_submit():
        try:
            # Generate training data (simplified)
            training_data = generate_training_data(model)
            
            # Train model
            result = predictive_analytics_service.train_model(model_id, training_data)
            
            flash('Model trained successfully!', 'success')
            return redirect(url_for('analytics.predictive_models'))
            
        except Exception as e:
            flash(f'Error training model: {str(e)}', 'error')
    
    return render_template('analytics/train_predictive_model.html',
                         model=model,
                         form=form)

@analytics_bp.route('/predictive-models/<int:model_id>/predict', methods=['GET', 'POST'])
@login_required
def make_prediction(model_id):
    """Make prediction using trained model"""
    model = PredictiveModel.query.get_or_404(model_id)
    
    if not model.is_trained:
        flash('Model must be trained before making predictions', 'warning')
        return redirect(url_for('analytics.predictive_models'))
    
    if request.method == 'POST':
        try:
            # Get features from form
            features = {}
            for feature in model.feature_columns:
                features[feature] = float(request.form.get(feature, 0))
            
            # Make prediction
            result = predictive_analytics_service.make_prediction(model_id, features)
            
            return render_template('analytics/prediction_result.html',
                                 model=model,
                                 result=result)
            
        except Exception as e:
            flash(f'Error making prediction: {str(e)}', 'error')
    
    return render_template('analytics/make_prediction.html',
                         model=model,
                         feature_columns=model.feature_columns)

# API endpoints
@analytics_bp.route('/api/events')
@login_required
def api_events():
    """API endpoint for analytics events"""
    form = AnalyticsFilterForm(request.args)
    
    # Get event statistics
    stats = analytics_service.get_event_statistics(
        event_type=form.event_type.data,
        event_category=form.event_category.data,
        user_id=form.user_id.data,
        start_date=form.start_date.data,
        end_date=form.end_date.data
    )
    
    return jsonify(stats)

@analytics_bp.route('/api/user-behavior/<int:user_id>')
@login_required
def api_user_behavior(user_id):
    """API endpoint for user behavior data"""
    behavior = user_behavior_service.get_user_behavior_summary(user_id)
    insights = user_behavior_service.get_behavior_insights(user_id)
    
    return jsonify({
        'behavior': behavior,
        'insights': insights
    })

@analytics_bp.route('/api/content-performance/<string:content_type>/<int:content_id>')
@login_required
def api_content_performance(content_type, content_id):
    """API endpoint for content performance data"""
    performance = content_performance_service.get_content_insights(content_type, content_id)
    
    return jsonify(performance)

@analytics_bp.route('/api/system-health')
@login_required
def api_system_health():
    """API endpoint for system health data"""
    health = system_metrics_service.get_system_health()
    performance = system_metrics_service.get_performance_metrics()
    user_metrics = system_metrics_service.get_user_metrics()
    db_metrics = system_metrics_service.get_database_metrics()
    
    return jsonify({
        'health': health,
        'performance': performance,
        'user_metrics': user_metrics,
        'database_metrics': db_metrics
    })

@analytics_bp.route('/api/trends')
@login_required
def api_trends():
    """API endpoint for trend analysis data"""
    target_type = request.args.get('target_type')
    target_id = request.args.get('target_id', type=int)
    metric_name = request.args.get('metric_name')
    period_days = request.args.get('period_days', 30, type=int)
    
    if not all([target_type, metric_name]):
        return jsonify({'error': 'Missing required parameters'}), 400
    
    try:
        trend = trend_analysis_service.analyze_trend(target_type, target_id, metric_name, period_days)
        return jsonify(trend.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/api/real-time-metrics')
@login_required
def api_real_time_metrics():
    """API endpoint for real-time metrics"""
    # Get current metrics
    current_metrics = {
        'active_users': get_active_users_count(minutes=5),
        'requests_per_minute': get_requests_per_minute(),
        'system_load': get_system_load(),
        'memory_usage': get_memory_usage(),
        'disk_usage': get_disk_usage()
    }
    
    return jsonify(current_metrics)

@analytics_bp.route('/api/track-event', methods=['POST'])
@login_required
def api_track_event():
    """API endpoint for tracking analytics events"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    try:
        event = analytics_service.track_event(
            event_type=data.get('event_type'),
            event_category=data.get('event_category'),
            user_id=data.get('user_id', current_user.id),
            target_type=data.get('target_type'),
            target_id=data.get('target_id'),
            event_data=data.get('event_data'),
            event_value=data.get('event_value'),
            session_id=data.get('session_id'),
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        return jsonify({'success': True, 'event_id': event.id})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/api/export')
@login_required
def api_export():
    """API endpoint for exporting analytics data"""
    form = AnalyticsExportForm(request.args)
    
    if not form.validate():
        return jsonify({'error': 'Invalid parameters'}), 400
    
    try:
        # Get data based on export type
        if form.export_type.data == 'events':
            data = get_events_export_data(form)
        elif form.export_type.data == 'user_behavior':
            data = get_user_behavior_export_data(form)
        elif form.export_type.data == 'content_performance':
            data = get_content_performance_export_data(form)
        elif form.export_type.data == 'system_metrics':
            data = get_system_metrics_export_data(form)
        else:
            return jsonify({'error': 'Invalid export type'}), 400
        
        # Format data based on format type
        if form.format.data == 'json':
            return jsonify(data)
        elif form.format.data == 'csv':
            return generate_csv_export(data, form.export_type.data)
        else:
            return jsonify({'error': 'Format not supported'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Helper functions
def get_active_users_count(days=1, minutes=None):
    """Get count of active users"""
    if minutes:
        start_time = datetime.utcnow() - timedelta(minutes=minutes)
    else:
        start_time = datetime.utcnow() - timedelta(days=days)
    
    # Count users with events in the time period
    active_users = db.session.query(func.count(func.distinct(AnalyticsEvent.user_id))).filter(
        AnalyticsEvent.created_at >= start_time
    ).scalar()
    
    return active_users or 0

def get_requests_per_minute():
    """Get requests per minute"""
    one_minute_ago = datetime.utcnow() - timedelta(minutes=1)
    
    requests = AnalyticsEvent.query.filter(
        AnalyticsEvent.created_at >= one_minute_ago
    ).count()
    
    return requests

def get_system_load():
    """Get system load (simplified)"""
    # In a real implementation, this would use system monitoring libraries
    # For now, return a mock value
    return 45.5

def get_memory_usage():
    """Get memory usage (simplified)"""
    # In a real implementation, this would use system monitoring libraries
    # For now, return a mock value
    return 62.3

def get_disk_usage():
    """Get disk usage (simplified)"""
    # In a real implementation, this would use system monitoring libraries
    # For now, return a mock value
    return 78.9

def generate_training_data(model):
    """Generate training data for predictive model"""
    # This is a simplified implementation
    # In a real implementation, you'd gather actual data from the database
    
    training_data = []
    
    # Get sample data based on model type
    if model.prediction_target == 'reputation_score':
        users = User.query.limit(100).all()
        for user in users:
            # Get user behavior data
            behavior = UserBehavior.query.filter_by(user_id=user.id).first()
            if behavior:
                training_data.append({
                    'reputation_score': user.reputation_score if hasattr(user, 'reputation_score') else 0,
                    'engagement_score': behavior.engagement_score,
                    'total_sessions': behavior.total_sessions,
                    'avg_session_duration': behavior.avg_session_duration,
                    'posts_created': behavior.posts_created,
                    'comments_created': behavior.comments_created,
                    'votes_cast': behavior.votes_cast
                })
    
    return training_data

def get_events_export_data(form):
    """Get events data for export"""
    query = AnalyticsEvent.query
    
    # Apply filters
    if form.start_date.data:
        query = query.filter(AnalyticsEvent.created_at >= form.start_date.data)
    if form.end_date.data:
        end_date = datetime.combine(form.end_date.data, datetime.max.time())
        query = query.filter(AnalyticsEvent.created_at <= end_date)
    if form.user_id.data:
        query = query.filter(AnalyticsEvent.user_id == form.user_id.data)
    
    events = query.all()
    
    return [event.to_dict() for event in events]

def get_user_behavior_export_data(form):
    """Get user behavior data for export"""
    query = UserBehavior.query
    
    # Apply filters
    if form.user_id.data:
        query = query.filter(UserBehavior.user_id == form.user_id.data)
    if form.min_engagement_score.data:
        query = query.filter(UserBehavior.engagement_score >= form.min_engagement_score.data)
    
    behaviors = query.all()
    
    return [behavior.to_dict() for behavior in behaviors]

def get_content_performance_export_data(form):
    """Get content performance data for export"""
    query = ContentPerformance.query
    
    # Apply filters
    if form.content_type.data:
        query = query.filter(ContentPerformance.content_type == form.content_type.data)
    if form.min_performance_score.data:
        query = query.filter(ContentPerformance.performance_score >= form.min_performance_score.data)
    
    performances = query.all()
    
    return [performance.to_dict() for performance in performances]

def get_system_metrics_export_data(form):
    """Get system metrics data for export"""
    query = SystemMetrics.query
    
    # Apply filters
    if form.metric_type.data:
        query = query.filter(SystemMetrics.metric_type == form.metric_type.data)
    if form.health_status.data:
        query = query.filter(SystemMetrics.health_status == form.health_status.data)
    
    metrics = query.all()
    
    return [metric.to_dict() for metric in metrics]

def generate_csv_export(data, export_type):
    """Generate CSV export"""
    import csv
    from io import StringIO
    
    output = StringIO()
    
    if data:
        # Use keys from first item as header
        fieldnames = data[0].keys()
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    
    # Create response
    from flask import Response
    response = Response(output.getvalue(), mimetype='text/csv')
    response.headers['Content-Disposition'] = f'attachment; filename={export_type}_export.csv'
    
    return response

# Error handlers
@analytics_bp.errorhandler(404)
def not_found(error):
    return render_template('analytics/404.html'), 404

@analytics_bp.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('analytics/500.html'), 500
