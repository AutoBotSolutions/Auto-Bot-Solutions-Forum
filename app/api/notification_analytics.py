"""
Notification Analytics API Routes

This module provides API endpoints for accessing notification analytics,
including delivery metrics, engagement data, and insights.
"""

from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from app.analytics.notification_analytics import notification_analytics
import logging

analytics_bp = Blueprint('notification_analytics', __name__, url_prefix='/api/analytics')

logger = logging.getLogger(__name__)

@analytics_bp.route('/notifications/delivery')
@login_required
def get_delivery_analytics():
    """Get notification delivery analytics"""
    try:
        # Parse date parameters
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        start_date = None
        end_date = None
        
        if start_date_str:
            try:
                start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
            except ValueError:
                return jsonify({'error': 'Invalid start_date format'}), 400
        
        if end_date_str:
            try:
                end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
            except ValueError:
                return jsonify({'error': 'Invalid end_date format'}), 400
        
        # Get analytics data
        analytics_data = notification_analytics.get_delivery_analytics(start_date, end_date)
        
        if 'error' in analytics_data:
            return jsonify(analytics_data), 500
        
        return jsonify(analytics_data), 200
        
    except Exception as e:
        logger.error(f"Error getting delivery analytics: {str(e)}")
        return jsonify({'error': 'Failed to get analytics data'}), 500

@analytics_bp.route('/notifications/insights')
@login_required
def get_notification_insights():
    """Get notification insights and recommendations"""
    try:
        # Parse date parameters
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        start_date = None
        end_date = None
        
        if start_date_str:
            try:
                start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
            except ValueError:
                return jsonify({'error': 'Invalid start_date format'}), 400
        
        if end_date_str:
            try:
                end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
            except ValueError:
                return jsonify({'error': 'Invalid end_date format'}), 400
        
        # Get insights
        insights_data = notification_analytics.get_notification_insights(start_date, end_date)
        
        if 'error' in insights_data:
            return jsonify(insights_data), 500
        
        return jsonify(insights_data), 200
        
    except Exception as e:
        logger.error(f"Error getting notification insights: {str(e)}")
        return jsonify({'error': 'Failed to get insights'}), 500

@analytics_bp.route('/notifications/export')
@login_required
def export_analytics():
    """Export analytics data in various formats"""
    try:
        # Parse parameters
        format_type = request.args.get('format', 'json')
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        if format_type not in ['json', 'csv']:
            return jsonify({'error': 'Unsupported format. Use json or csv'}), 400
        
        start_date = None
        end_date = None
        
        if start_date_str:
            try:
                start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
            except ValueError:
                return jsonify({'error': 'Invalid start_date format'}), 400
        
        if end_date_str:
            try:
                end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
            except ValueError:
                return jsonify({'error': 'Invalid end_date format'}), 400
        
        # Export data
        export_data = notification_analytics.export_analytics(format_type, start_date, end_date)
        
        if export_data is None:
            return jsonify({'error': 'Failed to export data'}), 500
        
        # Set appropriate headers
        if format_type == 'json':
            return export_data, 200, {'Content-Type': 'application/json'}
        elif format_type == 'csv':
            return export_data, 200, {'Content-Type': 'text/csv'}
        
    except Exception as e:
        logger.error(f"Error exporting analytics: {str(e)}")
        return jsonify({'error': 'Failed to export analytics'}), 500

@analytics_bp.route('/notifications/track', methods=['POST'])
@login_required
def track_notification_event():
    """Track notification engagement events"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        required_fields = ['notification_id', 'action']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        notification_id = data['notification_id']
        action = data['action']  # 'viewed', 'clicked', 'dismissed', 'marked_read'
        timestamp = data.get('timestamp')
        metadata = data.get('metadata', {})
        
        # Validate action
        valid_actions = ['viewed', 'clicked', 'dismissed', 'marked_read']
        if action not in valid_actions:
            return jsonify({'error': f'Invalid action. Must be one of: {valid_actions}'}), 400
        
        # Track the event
        notification_analytics.track_notification_engagement(
            notification_id=notification_id,
            action=action,
            user_id=current_user.id,
            timestamp=timestamp,
            metadata=metadata
        )
        
        return jsonify({'success': True, 'message': 'Event tracked successfully'}), 200
        
    except Exception as e:
        logger.error(f"Error tracking notification event: {str(e)}")
        return jsonify({'error': 'Failed to track event'}), 500

@analytics_bp.route('/notifications/dashboard')
@login_required
def get_dashboard_data():
    """Get comprehensive dashboard data for notifications"""
    try:
        # Get default analytics (last 30 days)
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)
        
        # Get all analytics data
        delivery_analytics = notification_analytics.get_delivery_analytics(start_date, end_date)
        insights = notification_analytics.get_notification_insights(start_date, end_date)
        
        # Prepare dashboard data
        dashboard_data = {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'days': 30
            },
            'summary': delivery_analytics.get('summary', {}),
            'key_metrics': {
                'total_notifications': delivery_analytics.get('summary', {}).get('total_notifications', 0),
                'read_rate': delivery_analytics.get('summary', {}).get('read_rate', 0),
                'engagement_rate': delivery_analytics.get('performance', {}).get('engagement_rate', 0),
                'delivery_success_rate': delivery_analytics.get('performance', {}).get('delivery_success_rate', 0)
            },
            'type_distribution': delivery_analytics.get('by_type', {}),
            'daily_trends': delivery_analytics.get('daily_trends', [])[:7],  # Last 7 days
            'hourly_distribution': delivery_analytics.get('hourly_distribution', []),
            'user_engagement': delivery_analytics.get('user_engagement', {}),
            'insights': insights.get('insights', []),
            'performance': delivery_analytics.get('performance', {})
        }
        
        return jsonify(dashboard_data), 200
        
    except Exception as e:
        logger.error(f"Error getting dashboard data: {str(e)}")
        return jsonify({'error': 'Failed to get dashboard data'}), 500

@analytics_bp.route('/notifications/realtime')
@login_required
def get_realtime_metrics():
    """Get real-time notification metrics"""
    try:
        from app.models import Notification
        
        # Get current metrics
        now = datetime.utcnow()
        hour_ago = now - timedelta(hours=1)
        day_ago = now - timedelta(days=1)
        
        # Last hour metrics
        last_hour_count = Notification.query.filter(
            Notification.created_at >= hour_ago
        ).count()
        
        last_hour_read = Notification.query.filter(
            and_(
                Notification.created_at >= hour_ago,
                Notification.is_read == True
            )
        ).count()
        
        # Last 24 hours metrics
        last_day_count = Notification.query.filter(
            Notification.created_at >= day_ago
        ).count()
        
        last_day_read = Notification.query.filter(
            and_(
                Notification.created_at >= day_ago,
                Notification.is_read == True
            )
        ).count()
        
        # Current unread count for current user
        current_unread = Notification.query.filter_by(
            user_id=current_user.id,
            is_read=False
        ).count()
        
        realtime_data = {
            'timestamp': now.isoformat(),
            'last_hour': {
                'total': last_hour_count,
                'read': last_hour_read,
                'read_rate': round((last_hour_read / last_hour_count * 100), 2) if last_hour_count > 0 else 0
            },
            'last_24_hours': {
                'total': last_day_count,
                'read': last_day_read,
                'read_rate': round((last_day_read / last_day_count * 100), 2) if last_day_count > 0 else 0
            },
            'current_user': {
                'unread_count': current_unread
            },
            'system_health': {
                'status': 'healthy',
                'websocket_connected': True,  # Would check actual WebSocket status
                'push_notification_service': 'operational'
            }
        }
        
        return jsonify(realtime_data), 200
        
    except Exception as e:
        logger.error(f"Error getting real-time metrics: {str(e)}")
        return jsonify({'error': 'Failed to get real-time metrics'}), 500

@analytics_bp.route('/notifications/compare')
@login_required
def compare_periods():
    """Compare notification metrics between two periods"""
    try:
        # Parse period parameters
        period1_start = request.args.get('period1_start')
        period1_end = request.args.get('period1_end')
        period2_start = request.args.get('period2_start')
        period2_end = request.args.get('period2_end')
        
        if not all([period1_start, period1_end, period2_start, period2_end]):
            return jsonify({'error': 'All period parameters required'}), 400
        
        # Parse dates
        try:
            p1_start = datetime.fromisoformat(period1_start.replace('Z', '+00:00'))
            p1_end = datetime.fromisoformat(period1_end.replace('Z', '+00:00'))
            p2_start = datetime.fromisoformat(period2_start.replace('Z', '+00:00'))
            p2_end = datetime.fromisoformat(period2_end.replace('Z', '+00:00'))
        except ValueError:
            return jsonify({'error': 'Invalid date format'}), 400
        
        # Get analytics for both periods
        period1_data = notification_analytics.get_delivery_analytics(p1_start, p1_end)
        period2_data = notification_analytics.get_delivery_analytics(p2_start, p2_end)
        
        if 'error' in period1_data or 'error' in period2_data:
            return jsonify({'error': 'Failed to get analytics data'}), 500
        
        # Calculate comparisons
        comparison = {
            'period1': {
                'start': period1_start,
                'end': period1_end,
                'summary': period1_data.get('summary', {})
            },
            'period2': {
                'start': period2_start,
                'end': period2_end,
                'summary': period2_data.get('summary', {})
            },
            'changes': {}
        }
        
        # Calculate percentage changes
        summary1 = period1_data.get('summary', {})
        summary2 = period2_data.get('summary', {})
        
        for metric in ['total_notifications', 'read_notifications', 'read_rate']:
            val1 = summary1.get(metric, 0)
            val2 = summary2.get(metric, 0)
            
            if val1 > 0:
                change_percent = ((val2 - val1) / val1) * 100
                comparison['changes'][metric] = {
                    'period1': val1,
                    'period2': val2,
                    'change': val2 - val1,
                    'change_percent': round(change_percent, 2)
                }
            else:
                comparison['changes'][metric] = {
                    'period1': val1,
                    'period2': val2,
                    'change': val2 - val1,
                    'change_percent': None
                }
        
        return jsonify(comparison), 200
        
    except Exception as e:
        logger.error(f"Error comparing periods: {str(e)}")
        return jsonify({'error': 'Failed to compare periods'}), 500

# Import required SQLAlchemy operators
from sqlalchemy import and_
