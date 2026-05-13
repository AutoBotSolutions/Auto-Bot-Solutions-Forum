"""
Advanced User Analytics Routes

This module contains routes for advanced user analytics including:
- User behavior analytics
- Engagement metrics tracking
- User performance dashboards
- Predictive analytics
- User segmentation
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app, send_file
from flask_login import login_required, current_user
from app import db
from app.models import User
from app.user.analytics.models import (
    UserBehavior, UserEngagement, UserPerformance, UserSegment, 
    UserPrediction, UserDashboard, SegmentUser
)
from app.admin.roles.models import Role, RoleAnalytics
from app.user.analytics.forms import (
    AnalyticsDateRangeForm, UserBehaviorFilterForm, EngagementMetricsForm,
    PerformanceMetricsForm, UserSegmentForm, EditUserSegmentForm,
    PredictionConfigForm, UserSearchForm, DashboardConfigForm,
    WidgetConfigForm, AnalyticsExportForm, AnalyticsSettingsForm,
    ComparisonForm
)
import json
import csv
import io
from datetime import datetime, timedelta
from sqlalchemy import func

analytics_bp = Blueprint('analytics', __name__, url_prefix='/analytics')

# User Behavior Analytics

@analytics_bp.route('/behaviors')
@login_required
def user_behaviors():
    """User behavior analytics dashboard"""
    form = UserBehaviorFilterForm()
    behaviors = []
    
    # Apply filters
    if request.args.get('filter'):
        form.behavior_type.data = request.args.get('behavior_type', 'all')
        form.target_type.data = request.args.get('target_type', 'all')
        form.action.data = request.args.get('action', '')
        form.session_id.data = request.args.get('session_id', '')
        
        # Get filtered behaviors
        behaviors = UserBehavior.get_user_behaviors(
            current_user.id,
            behavior_type=form.behavior_type.data if form.behavior_type.data != 'all' else None,
            days=30,
            limit=100
        )
        
        # Apply additional filters
        if form.target_type.data != 'all':
            behaviors = [b for b in behaviors if b.target_type == form.target_type.data]
        
        if form.action.data:
            behaviors = [b for b in behaviors if form.action.data.lower() in b.action.lower()]
        
        if form.session_id.data:
            behaviors = [b for b in behaviors if b.session_id == form.session_id.data]
    else:
        behaviors = UserBehavior.get_user_behaviors(current_user.id, days=30, limit=100)
    
    # Calculate behavior statistics
    behavior_stats = {}
    for behavior in behaviors:
        behavior_type = behavior.behavior_type
        if behavior_type not in behavior_stats:
            behavior_stats[behavior_type] = 0
        behavior_stats[behavior_type] += 1
    
    return render_template('analytics/user_behaviors.html',
                         behaviors=behaviors,
                         behavior_stats=behavior_stats,
                         form=form)

@analytics_bp.route('/behaviors/track', methods=['POST'])
@login_required
def track_behavior():
    """Track user behavior (AJAX endpoint)"""
    data = request.get_json()
    
    behavior = UserBehavior.track_behavior(
        user_id=current_user.id,
        behavior_type=data.get('behavior_type'),
        action=data.get('action'),
        target_type=data.get('target_type'),
        target_id=data.get('target_id'),
        session_id=data.get('session_id'),
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent'),
        referrer=request.referrer,
        duration=data.get('duration'),
        metadata=data.get('metadata')
    )
    
    return jsonify({'success': True, 'behavior_id': behavior.id})

# Engagement Metrics

@analytics_bp.route('/engagement')
@login_required
def user_engagement():
    """User engagement metrics dashboard"""
    form = EngagementMetricsForm()
    
    # Get engagement trend
    period = request.args.get('period', '30')
    try:
        days = int(period)
    except:
        days = 30
    
    engagement_trend = UserEngagement.get_engagement_trend(current_user.id, days=days)
    
    # Calculate engagement statistics
    if engagement_trend:
        total_engagement = sum(e.engagement_score for e in engagement_trend)
        avg_engagement = total_engagement / len(engagement_trend)
        max_engagement = max(e.engagement_score for e in engagement_trend)
        min_engagement = min(e.engagement_score for e in engagement_trend)
    else:
        total_engagement = avg_engagement = max_engagement = min_engagement = 0
    
    # Get latest engagement data
    latest_engagement = UserEngagement.query.filter_by(user_id=current_user.id).order_by(
        UserEngagement.date.desc()
    ).first()
    
    return render_template('analytics/user_engagement.html',
                         engagement_trend=engagement_trend,
                         total_engagement=total_engagement,
                         avg_engagement=avg_engagement,
                         max_engagement=max_engagement,
                         min_engagement=min_engagement,
                         latest_engagement=latest_engagement,
                         form=form)

@analytics_bp.route('/engagement/calculate', methods=['POST'])
@login_required
def calculate_engagement():
    """Calculate engagement metrics"""
    date_str = request.form.get('date')
    if date_str:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
    else:
        date = datetime.utcnow().date()
    
    engagement = UserEngagement.calculate_daily_engagement(current_user.id, date)
    
    if engagement:
        flash(f'Engagement calculated for {date}: {engagement.engagement_score}', 'success')
    else:
        flash('Unable to calculate engagement.', 'error')
    
    return redirect(url_for('analytics.user_engagement'))

# Performance Metrics

@analytics_bp.route('/performance')
@login_required
def user_performance():
    """User performance metrics dashboard"""
    form = PerformanceMetricsForm()
    
    period = request.args.get('period', 'weekly')
    metrics = UserPerformance.query.filter_by(
        user_id=current_user.id,
        period=period
    ).order_by(UserPerformance.period_end.desc()).limit(20).all()
    
    # Group metrics by type
    performance_data = {}
    for metric in metrics:
        if metric.metric_type not in performance_data:
            performance_data[metric.metric_type] = []
        performance_data[metric.metric_type].append(metric)
    
    return render_template('analytics/user_performance.html',
                         performance_data=performance_data,
                         metrics=metrics,
                         form=form)

@analytics_bp.route('/performance/calculate', methods=['POST'])
@login_required
def calculate_performance():
    """Calculate performance metrics"""
    period = request.form.get('period', 'weekly')
    
    metrics = UserPerformance.calculate_performance_metrics(current_user.id, period)
    
    flash(f'Performance metrics calculated for {period} period.', 'success')
    return redirect(url_for('analytics.user_performance'))

# User Segmentation

@analytics_bp.route('/segments')
@login_required
def user_segments():
    """User segmentation dashboard"""
    segments = UserSegment.query.filter_by(is_active=True).all()
    
    # Get user's segment memberships
    user_segments = [segment for segment in segments if current_user in segment.users]
    
    return render_template('analytics/user_segments.html',
                         segments=segments,
                         user_segments=user_segments)

@analytics_bp.route('/segments/create', methods=['GET', 'POST'])
@login_required
def create_segment():
    """Create a new user segment"""
    form = UserSegmentForm()
    
    if form.validate_on_submit():
        # Build criteria from form
        criteria = {}
        
        if form.segment_type.data in ['activity', 'engagement', 'behavior']:
            if form.min_posts.data is not None:
                criteria['min_posts'] = form.min_posts.data
            if form.max_posts.data is not None:
                criteria['max_posts'] = form.max_posts.data
            if form.min_comments.data is not None:
                criteria['min_comments'] = form.min_comments.data
            if form.max_comments.data is not None:
                criteria['max_comments'] = form.max_comments.data
            if form.min_engagement_score.data is not None:
                criteria['min_engagement_score'] = form.min_engagement_score.data
            if form.max_engagement_score.data is not None:
                criteria['max_engagement_score'] = form.max_engagement_score.data
            if form.min_session_duration.data is not None:
                criteria['min_session_duration'] = form.min_session_duration.data
            if form.login_frequency.data != 'any':
                criteria['login_frequency'] = form.login_frequency.data
            if form.last_login_days.data is not None:
                criteria['last_login_days'] = form.last_login_days.data
        
        segment = UserSegment.create_segment(
            name=form.name.data,
            description=form.description.data,
            segment_type=form.segment_type.data,
            criteria=criteria
        )
        
        flash(f'Segment "{segment.name}" created with {segment.user_count} users.', 'success')
        return redirect(url_for('analytics.user_segments'))
    
    return render_template('analytics/create_segment.html', form=form)

@analytics_bp.route('/segments/<int:segment_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_segment(segment_id):
    """Edit a user segment"""
    segment = UserSegment.query.get_or_404(segment_id)
    form = EditUserSegmentForm()
    
    if form.validate_on_submit():
        segment.name = form.name.data
        segment.description = form.description.data
        segment.is_active = form.is_active.data
        segment.updated_at = datetime.utcnow()
        
        db.session.commit()
        flash(f'Segment "{segment.name}" updated successfully.', 'success')
        return redirect(url_for('analytics.user_segments'))
    
    # Pre-fill form
    form.name.data = segment.name
    form.description.data = segment.description
    form.is_active.data = segment.is_active
    
    return render_template('analytics/edit_segment.html', form=form, segment=segment)

@analytics_bp.route('/segments/<int:segment_id>/apply', methods=['POST'])
@login_required
def apply_segment(segment_id):
    """Apply segmentation criteria"""
    segment = UserSegment.query.get_or_404(segment_id)
    
    matched_users = segment.apply_segmentation()
    
    flash(f'Segment "{segment.name}" updated with {len(matched_users)} users.', 'success')
    return redirect(url_for('analytics.user_segments'))

# Predictive Analytics

@analytics_bp.route('/predictions')
@login_required
def user_predictions():
    """User predictions dashboard"""
    form = PredictionConfigForm()
    
    # Get user's predictions
    predictions = UserPrediction.query.filter_by(user_id=current_user.id).order_by(
        UserPrediction.created_at.desc()
    ).limit(20).all()
    
    # Group predictions by type
    prediction_data = {}
    for prediction in predictions:
        if prediction.prediction_type not in prediction_data:
            prediction_data[prediction.prediction_type] = []
        prediction_data[prediction.prediction_type].append(prediction)
    
    return render_template('analytics/user_predictions.html',
                         prediction_data=prediction_data,
                         predictions=predictions,
                         form=form)

@analytics_bp.route('/predictions/generate', methods=['POST'])
@login_required
def generate_predictions():
    """Generate user predictions"""
    form = PredictionConfigForm()
    
    if form.validate_on_submit():
        prediction_type = form.prediction_type.data
        prediction_period = int(form.prediction_period.data)
        target_date = datetime.utcnow().date() + timedelta(days=prediction_period)
        
        if prediction_type == 'churn':
            prediction = UserPrediction.predict_churn_risk(current_user.id, prediction_period)
        else:
            # Generate other types of predictions (simplified)
            prediction = UserPrediction.create_prediction(
                user_id=current_user.id,
                prediction_type=prediction_type,
                prediction_value=0.5,  # Default value
                confidence=0.6,
                target_date=target_date,
                metadata={'method': 'basic_algorithm'}
            )
        
        flash(f'{prediction_type.title()} prediction generated.', 'success')
        return redirect(url_for('analytics.user_predictions'))
    
    return redirect(url_for('analytics.user_predictions'))

# User Dashboards

@analytics_bp.route('/dashboards')
@login_required
def user_dashboards():
    """User analytics dashboards"""
    dashboards = UserDashboard.query.filter_by(user_id=current_user.id).all()
    
    return render_template('analytics/user_dashboards.html',
                         dashboards=dashboards)

@analytics_bp.route('/dashboards/create', methods=['GET', 'POST'])
@login_required
def create_dashboard():
    """Create a new analytics dashboard"""
    form = DashboardConfigForm()
    
    if form.validate_on_submit():
        # Build layout and widgets from form
        layout = {
            'columns': int(form.layout_columns.data),
            'auto_refresh': form.auto_refresh.data,
            'refresh_interval': int(form.refresh_interval.data) if form.auto_refresh.data else None
        }
        
        widgets = UserDashboard.get_default_widgets()
        
        dashboard = UserDashboard.create_dashboard(
            user_id=current_user.id,
            name=form.name.data,
            dashboard_type=form.dashboard_type.data,
            layout=layout,
            widgets=widgets
        )
        
        if form.is_default.data:
            # Set as default (unset others)
            UserDashboard.query.filter_by(user_id=current_user.id, is_default=True).update({'is_default': False})
            dashboard.is_default = True
        
        dashboard.is_public = form.is_public.data
        db.session.commit()
        
        flash(f'Dashboard "{dashboard.name}" created successfully.', 'success')
        return redirect(url_for('analytics.user_dashboards'))
    
    return render_template('analytics/create_dashboard.html', form=form)

@analytics_bp.route('/dashboards/<int:dashboard_id>')
@login_required
def view_dashboard(dashboard_id):
    """View an analytics dashboard"""
    dashboard = UserDashboard.query.get_or_404(dashboard_id)
    
    # Check if user can view this dashboard
    if dashboard.user_id != current_user.id and not dashboard.is_public:
        flash('You do not have permission to view this dashboard.', 'error')
        return redirect(url_for('analytics.user_dashboards'))
    
    # Get dashboard data
    dashboard_data = get_dashboard_data(dashboard)
    
    return render_template('analytics/view_dashboard.html',
                         dashboard=dashboard,
                         dashboard_data=dashboard_data)

def get_dashboard_data(dashboard):
    """Get data for dashboard widgets"""
    data = {}
    
    for widget_id, widget_config in dashboard.widgets.items():
        if widget_config['type'] == 'stats':
            data[widget_id] = get_widget_stats(widget_config, dashboard.user_id)
        elif widget_config['type'] == 'chart':
            data[widget_id] = get_widget_chart(widget_config, dashboard.user_id)
        elif widget_config['type'] == 'list':
            data[widget_id] = get_widget_list(widget_config, dashboard.user_id)
    
    return data

def get_widget_stats(widget_config, user_id):
    """Get statistics data for a widget"""
    metrics = widget_config.get('metrics', [])
    stats = {}
    
    if 'posts' in metrics:
        stats['posts'] = UserBehavior.query.filter_by(user_id=user_id, behavior_type='post').count()
    if 'comments' in metrics:
        stats['comments'] = UserBehavior.query.filter_by(user_id=user_id, behavior_type='comment').count()
    if 'likes' in metrics:
        stats['likes'] = UserBehavior.query.filter_by(user_id=user_id, behavior_type='like').count()
    if 'engagement' in metrics:
        latest_engagement = UserEngagement.query.filter_by(user_id=user_id).order_by(
            UserEngagement.date.desc()
        ).first()
        stats['engagement'] = latest_engagement.engagement_score if latest_engagement else 0
    
    return stats

def get_widget_chart(widget_config, user_id):
    """Get chart data for a widget"""
    chart_type = widget_config.get('chart_type', 'line')
    data_source = widget_config.get('data_source', 'user_behaviors')
    
    if data_source == 'user_behaviors':
        # Get daily behavior counts
        days = 30
        daily_data = []
        
        for i in range(days):
            date = datetime.utcnow().date() - timedelta(days=i)
            count = UserBehavior.query.filter(
                UserBehavior.user_id == user_id,
                func.date(UserBehavior.created_at) == date
            ).count()
            daily_data.append({
                'date': date.isoformat(),
                'count': count
            })
        
        return {
            'type': chart_type,
            'data': sorted(daily_data, key=lambda x: x['date'])
        }
    
    return {}

def get_widget_list(widget_config, user_id):
    """Get list data for a widget"""
    limit = widget_config.get('limit', 10)
    
    behaviors = UserBehavior.query.filter_by(user_id=user_id).order_by(
        UserBehavior.created_at.desc()
    ).limit(limit).all()
    
    return [
        {
            'id': b.id,
            'type': b.behavior_type,
            'action': b.action,
            'created_at': b.created_at.isoformat()
        }
        for b in behaviors
    ]

# Analytics Export

@analytics_bp.route('/export', methods=['GET', 'POST'])
@login_required
def export_analytics():
    """Export analytics data"""
    form = AnalyticsExportForm()
    
    if form.validate_on_submit():
        export_type = form.export_type.data
        export_format = form.export_format.data
        date_range = int(form.date_range.data)
        
        # Get data based on export type
        if export_type == 'behaviors':
            data = get_behaviors_export(current_user.id, date_range)
        elif export_type == 'engagement':
            data = get_engagement_export(current_user.id, date_range)
        elif export_type == 'performance':
            data = get_performance_export(current_user.id, date_range)
        else:
            flash('Invalid export type.', 'error')
            return redirect(url_for('analytics.export_analytics'))
        
        # Export in requested format
        if export_format == 'csv':
            return export_csv(data, export_type)
        elif export_format == 'json':
            return export_json(data, export_type)
        elif export_format == 'xlsx':
            return export_excel(data, export_type)
        else:
            flash('Export format not implemented.', 'error')
            return redirect(url_for('analytics.export_analytics'))
    
    return render_template('analytics/export_analytics.html', form=form)

def get_behaviors_export(user_id, days):
    """Get behaviors data for export"""
    since_date = datetime.utcnow() - timedelta(days=days)
    behaviors = UserBehavior.query.filter(
        UserBehavior.user_id == user_id,
        UserBehavior.created_at >= since_date
    ).all()
    
    return [
        {
            'id': b.id,
            'behavior_type': b.behavior_type,
            'target_type': b.target_type,
            'target_id': b.target_id,
            'action': b.action,
            'duration': b.duration,
            'created_at': b.created_at.isoformat()
        }
        for b in behaviors
    ]

def get_engagement_export(user_id, days):
    """Get engagement data for export"""
    since_date = datetime.utcnow().date() - timedelta(days=days)
    engagements = UserEngagement.query.filter(
        UserEngagement.user_id == user_id,
        UserEngagement.date >= since_date
    ).all()
    
    return [
        {
            'date': e.date.isoformat(),
            'total_actions': e.total_actions,
            'login_count': e.login_count,
            'post_count': e.post_count,
            'comment_count': e.comment_count,
            'like_count': e.like_count,
            'share_count': e.share_count,
            'view_count': e.view_count,
            'session_duration': e.session_duration,
            'pages_viewed': e.pages_viewed,
            'bounce_rate': e.bounce_rate,
            'engagement_score': e.engagement_score
        }
        for e in engagements
    ]

def get_performance_export(user_id, days):
    """Get performance data for export"""
    since_date = datetime.utcnow().date() - timedelta(days=days)
    performances = UserPerformance.query.filter(
        UserPerformance.user_id == user_id,
        UserPerformance.period_end >= since_date
    ).all()
    
    return [
        {
            'metric_type': p.metric_type,
            'metric_name': p.metric_name,
            'metric_value': p.metric_value,
            'previous_value': p.previous_value,
            'change_percentage': p.change_percentage,
            'period': p.period,
            'period_start': p.period_start.isoformat(),
            'period_end': p.period_end.isoformat()
        }
        for p in performances
    ]

def export_csv(data, export_type):
    """Export data as CSV"""
    output = io.StringIO()
    
    if data:
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
    
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'{export_type}_export.csv'
    )

def export_json(data, export_type):
    """Export data as JSON"""
    return send_file(
        io.BytesIO(json.dumps(data, indent=2).encode('utf-8')),
        mimetype='application/json',
        as_attachment=True,
        download_name=f'{export_type}_export.json'
    )

def export_excel(data, export_type):
    """Export data as Excel (placeholder)"""
    # This would require a library like openpyxl
    flash('Excel export not implemented yet.', 'info')
    return redirect(url_for('analytics.export_analytics'))

# Analytics Settings

@analytics_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def analytics_settings():
    """Analytics settings"""
    form = AnalyticsSettingsForm()
    
    if form.validate_on_submit():
        # Save settings (would need to add fields to User model)
        settings = {
            'track_behaviors': form.track_behaviors.data,
            'track_engagement': form.track_engagement.data,
            'track_sessions': form.track_sessions.data,
            'enable_predictions': form.enable_predictions.data,
            'data_retention_days': form.data_retention_days.data,
            'aggregation_frequency': form.aggregation_frequency.data,
            'enable_anonymous_tracking': form.enable_anonymous_tracking.data,
            'enable_ip_tracking': form.enable_ip_tracking.data
        }
        
        # Store in user analytics preferences field (would need to add to User model)
        current_user.analytics_preferences = json.dumps(settings)
        db.session.commit()
        
        flash('Analytics settings updated successfully.', 'success')
        return redirect(url_for('analytics.analytics_settings'))
    
    # Load current settings
    if hasattr(current_user, 'analytics_preferences') and current_user.analytics_preferences:
        try:
            settings = json.loads(current_user.analytics_preferences)
            form.track_behaviors.data = settings.get('track_behaviors', True)
            form.track_engagement.data = settings.get('track_engagement', True)
            form.track_sessions.data = settings.get('track_sessions', True)
            form.enable_predictions.data = settings.get('enable_predictions', True)
            form.data_retention_days.data = settings.get('data_retention_days', 365)
            form.aggregation_frequency.data = settings.get('aggregation_frequency', 'daily')
            form.enable_anonymous_tracking.data = settings.get('enable_anonymous_tracking', False)
            form.enable_ip_tracking.data = settings.get('enable_ip_tracking', True)
        except:
            pass  # Use defaults
    
    return render_template('analytics/analytics_settings.html', form=form)

@analytics_bp.route('/role-analytics')
@login_required
def role_analytics():
    """Role analytics dashboard"""
    if not current_user.is_admin:
        flash('Access denied.', 'error')
        return redirect(url_for('main.index'))
    
    form = RoleAnalyticsForm()
    
    # Populate role choices
    form.role_id.choices = [(r.id, r.display_name) for r in Role.query.filter_by(is_active=True).all()]
    
    analytics_data = {}
    
    if request.args.get('role_id'):
        role_id = int(request.args.get('role_id'))
        days = int(request.args.get('date_range', 30))
        
        # Get role analytics
        analytics = RoleAnalytics.get_role_trends(role_id, days=days)
        analytics_data['trends'] = analytics
        
        # Get current role stats
        role = Role.query.get(role_id)
        analytics_data['current_stats'] = {
            'user_count': role.get_user_count(),
            'level': role.level,
            'is_admin': role.is_admin_role
        }
    
    return render_template('analytics/role_analytics.html',
                         form=form,
                         analytics_data=analytics_data)
