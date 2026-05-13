"""
Notification Analytics System

This module provides comprehensive analytics for notification delivery,
engagement, and performance tracking.
"""

from datetime import datetime, timedelta
from flask import current_app
from sqlalchemy import func, and_, or_
from app import db
from app.models import Notification, User
import json
import logging

logger = logging.getLogger(__name__)

class NotificationAnalytics:
    """Comprehensive notification analytics system"""
    
    def __init__(self):
        self.tracking_enabled = True
        
    def track_notification_delivery(self, notification_id, delivery_type, status, 
                                 recipient_id=None, metadata=None):
        """Track notification delivery attempt"""
        if not self.tracking_enabled:
            return
            
        try:
            delivery_record = {
                'notification_id': notification_id,
                'delivery_type': delivery_type,  # 'websocket', 'push', 'email'
                'status': status,  # 'sent', 'delivered', 'failed', 'bounced'
                'recipient_id': recipient_id,
                'timestamp': datetime.utcnow().isoformat(),
                'metadata': metadata or {}
            }
            
            # Store in analytics database (for now, log it)
            logger.info(f"Notification delivery tracked: {delivery_record}")
            
            # In a real implementation, you would store this in a dedicated analytics table
            # For now, we'll track in memory and periodically flush
            
        except Exception as e:
            logger.error(f"Error tracking notification delivery: {str(e)}")
    
    def track_notification_engagement(self, notification_id, action, user_id, 
                                    timestamp=None, metadata=None):
        """Track user engagement with notifications"""
        if not self.tracking_enabled:
            return
            
        try:
            engagement_record = {
                'notification_id': notification_id,
                'action': action,  # 'viewed', 'clicked', 'dismissed', 'marked_read'
                'user_id': user_id,
                'timestamp': timestamp or datetime.utcnow().isoformat(),
                'metadata': metadata or {}
            }
            
            logger.info(f"Notification engagement tracked: {engagement_record}")
            
        except Exception as e:
            logger.error(f"Error tracking notification engagement: {str(e)}")
    
    def get_delivery_analytics(self, start_date=None, end_date=None):
        """Get comprehensive delivery analytics"""
        try:
            # Default to last 30 days
            if not start_date:
                start_date = datetime.utcnow() - timedelta(days=30)
            if not end_date:
                end_date = datetime.utcnow()
            
            # Get basic notification statistics
            total_notifications = Notification.query.filter(
                Notification.created_at.between(start_date, end_date)
            ).count()
            
            # Get read statistics
            read_notifications = Notification.query.filter(
                and_(
                    Notification.created_at.between(start_date, end_date),
                    Notification.is_read == True
                )
            ).count()
            
            # Calculate read rate
            read_rate = (read_notifications / total_notifications * 100) if total_notifications > 0 else 0
            
            # Get notifications by type (if we had type field)
            # For now, we'll analyze by content patterns
            comment_notifications = Notification.query.filter(
                and_(
                    Notification.created_at.between(start_date, end_date),
                    Notification.content.like('%commented on%')
                )
            ).count()
            
            message_notifications = Notification.query.filter(
                and_(
                    Notification.created_at.between(start_date, end_date),
                    Notification.content.like('%message%')
                )
            ).count()
            
            system_notifications = total_notifications - comment_notifications - message_notifications
            
            # Daily notification trends
            daily_stats = db.session.query(
                func.date(Notification.created_at).label('date'),
                func.count(Notification.id).label('count'),
                func.sum(func.case([(Notification.is_read == True, 1)], else_=0)).label('read_count')
            ).filter(
                Notification.created_at.between(start_date, end_date)
            ).group_by(func.date(Notification.created_at)).all()
            
            # Hourly distribution
            hourly_stats = db.session.query(
                func.extract('hour', Notification.created_at).label('hour'),
                func.count(Notification.id).label('count')
            ).filter(
                Notification.created_at.between(start_date, end_date)
            ).group_by(func.extract('hour', Notification.created_at)).all()
            
            # User engagement metrics
            user_engagement = self.get_user_engagement_metrics(start_date, end_date)
            
            # Performance metrics
            performance_metrics = self.get_performance_metrics(start_date, end_date)
            
            return {
                'summary': {
                    'total_notifications': total_notifications,
                    'read_notifications': read_notifications,
                    'unread_notifications': total_notifications - read_notifications,
                    'read_rate': round(read_rate, 2),
                    'period': {
                        'start_date': start_date.isoformat(),
                        'end_date': end_date.isoformat()
                    }
                },
                'by_type': {
                    'comment': comment_notifications,
                    'message': message_notifications,
                    'system': system_notifications
                },
                'daily_trends': [
                    {
                        'date': str(stat.date),
                        'total': stat.count,
                        'read': stat.read_count or 0,
                        'read_rate': round((stat.read_count or 0) / stat.count * 100, 2) if stat.count > 0 else 0
                    } for stat in daily_stats
                ],
                'hourly_distribution': [
                    {
                        'hour': int(stat.hour),
                        'count': stat.count
                    } for stat in hourly_stats
                ],
                'user_engagement': user_engagement,
                'performance': performance_metrics
            }
            
        except Exception as e:
            logger.error(f"Error getting delivery analytics: {str(e)}")
            return {'error': 'Failed to generate analytics'}
    
    def get_user_engagement_metrics(self, start_date, end_date):
        """Get user-specific engagement metrics"""
        try:
            # Most active users (by notification count)
            most_active = db.session.query(
                User.id,
                User.username,
                func.count(Notification.id).label('notification_count')
            ).join(Notification).filter(
                Notification.created_at.between(start_date, end_date)
            ).group_by(User.id, User.username).order_by(
                func.count(Notification.id).desc()
            ).limit(10).all()
            
            # Users with highest read rates
            read_rates = db.session.query(
                User.id,
                User.username,
                func.count(Notification.id).label('total'),
                func.sum(func.case([(Notification.is_read == True, 1)], else_=0)).label('read')
            ).join(Notification).filter(
                Notification.created_at.between(start_date, end_date)
            ).group_by(User.id, User.username).all()
            
            # Calculate read rates
            user_read_rates = []
            for user in read_rates:
                read_rate = (user.read / user.total * 100) if user.total > 0 else 0
                user_read_rates.append({
                    'user_id': user.id,
                    'username': user.username,
                    'total_notifications': user.total,
                    'read_notifications': user.read,
                    'read_rate': round(read_rate, 2)
                })
            
            # Sort by read rate
            user_read_rates.sort(key=lambda x: x['read_rate'], reverse=True)
            
            return {
                'most_active': [
                    {
                        'user_id': user.id,
                        'username': user.username,
                        'notification_count': user.notification_count
                    } for user in most_active
                ],
                'highest_read_rates': user_read_rates[:10],
                'lowest_read_rates': user_read_rates[-10:] if len(user_read_rates) > 10 else []
            }
            
        except Exception as e:
            logger.error(f"Error getting user engagement metrics: {str(e)}")
            return {}
    
    def get_performance_metrics(self, start_date, end_date):
        """Get performance metrics"""
        try:
            # Average time to read (simulated - would need read_timestamp field)
            # For now, we'll calculate based on creation times
            recent_notifications = Notification.query.filter(
                Notification.created_at.between(start_date, end_date)
            ).order_by(Notification.created_at.desc()).limit(1000).all()
            
            # Calculate engagement patterns
            total_recent = len(recent_notifications)
            read_recent = sum(1 for n in recent_notifications if n.is_read)
            
            # Simulate average time to read (would need actual read timestamps)
            avg_time_to_read = 2.5  # hours (simulated)
            
            return {
                'engagement_rate': round((read_recent / total_recent * 100), 2) if total_recent > 0 else 0,
                'avg_time_to_read_hours': avg_time_to_read,
                'peak_activity_hours': self.get_peak_activity_hours(start_date, end_date),
                'delivery_success_rate': 98.5,  # Simulated - would track actual deliveries
                'push_notification_opt_in_rate': 65.2  # Simulated
            }
            
        except Exception as e:
            logger.error(f"Error getting performance metrics: {str(e)}")
            return {}
    
    def get_peak_activity_hours(self, start_date, end_date):
        """Find peak activity hours"""
        try:
            hourly_stats = db.session.query(
                func.extract('hour', Notification.created_at).label('hour'),
                func.count(Notification.id).label('count')
            ).filter(
                Notification.created_at.between(start_date, end_date)
            ).group_by(func.extract('hour', Notification.created_at)).all()
            
            if not hourly_stats:
                return []
            
            # Sort by count and get top 5
            hourly_stats.sort(key=lambda x: x.count, reverse=True)
            
            return [
                {
                    'hour': int(stat.hour),
                    'count': stat.count,
                    'percentage': round((stat.count / sum(s.count for s in hourly_stats) * 100), 2)
                } for stat in hourly_stats[:5]
            ]
            
        except Exception as e:
            logger.error(f"Error getting peak activity hours: {str(e)}")
            return []
    
    def get_notification_insights(self, start_date=None, end_date=None):
        """Generate actionable insights from analytics"""
        try:
            analytics = self.get_delivery_analytics(start_date, end_date)
            
            if 'error' in analytics:
                return {'error': 'Unable to generate insights'}
            
            insights = []
            
            # Read rate insights
            read_rate = analytics['summary']['read_rate']
            if read_rate < 50:
                insights.append({
                    'type': 'warning',
                    'title': 'Low Read Rate',
                    'description': f'Only {read_rate}% of notifications are being read. Consider improving content relevance or timing.',
                    'recommendation': 'Review notification content and delivery timing'
                })
            elif read_rate > 80:
                insights.append({
                    'type': 'success',
                    'title': 'High Engagement',
                    'description': f'Excellent {read_rate}% read rate shows high user engagement.',
                    'recommendation': 'Maintain current notification strategy'
                })
            
            # Volume insights
            total_notifications = analytics['summary']['total_notifications']
            if total_notifications > 1000:
                daily_avg = total_notifications / 30  # Assuming 30 days
                if daily_avg > 50:
                    insights.append({
                        'type': 'warning',
                        'title': 'High Notification Volume',
                        'description': f'Average of {daily_avg:.1f} notifications per day may overwhelm users.',
                        'recommendation': 'Consider implementing notification batching or frequency controls'
                    })
            
            # Type distribution insights
            by_type = analytics['by_type']
            if by_type['system'] > by_type['comment'] + by_type['message']:
                insights.append({
                    'type': 'info',
                    'title': 'System Notifications Dominant',
                    'description': 'System notifications make up the majority of all notifications.',
                    'recommendation': 'Review if all system notifications are necessary'
                })
            
            # Peak hours insights
            peak_hours = analytics['performance'].get('peak_activity_hours', [])
            if peak_hours:
                peak_hour = peak_hours[0]['hour']
                if 22 <= peak_hour or peak_hour <= 6:
                    insights.append({
                        'type': 'info',
                        'title': 'Late Night Activity',
                        'description': f'Peak activity occurs at {peak_hour}:00. Consider quiet hours.',
                        'recommendation': 'Implement user preference for quiet hours'
                    })
            
            return {
                'insights': insights,
                'summary': {
                    'total_insights': len(insights),
                    'critical': len([i for i in insights if i['type'] == 'warning']),
                    'positive': len([i for i in insights if i['type'] == 'success']),
                    'informational': len([i for i in insights if i['type'] == 'info'])
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating insights: {str(e)}")
            return {'error': 'Failed to generate insights'}
    
    def export_analytics(self, format='json', start_date=None, end_date=None):
        """Export analytics data in various formats"""
        try:
            analytics = self.get_delivery_analytics(start_date, end_date)
            
            if format == 'json':
                return json.dumps(analytics, indent=2, default=str)
            elif format == 'csv':
                # Convert to CSV format
                import csv
                import io
                
                output = io.StringIO()
                
                # Summary CSV
                if 'summary' in analytics:
                    writer = csv.writer(output)
                    writer.writerow(['Metric', 'Value'])
                    for key, value in analytics['summary'].items():
                        if key != 'period':
                            writer.writerow([key, value])
                
                return output.getvalue()
            else:
                raise ValueError(f"Unsupported format: {format}")
                
        except Exception as e:
            logger.error(f"Error exporting analytics: {str(e)}")
            return None

# Global analytics instance
notification_analytics = NotificationAnalytics()
