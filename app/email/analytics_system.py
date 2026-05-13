"""
Email Analytics and Monitoring System

This module provides comprehensive email analytics and monitoring:
- Delivery performance analytics
- Engagement tracking (opens, clicks)
- Bounce and spam analysis
- Real-time monitoring dashboard
- Performance optimization recommendations
- Automated reporting
"""

import time
import json
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import redis
import sqlite3
from sqlalchemy import text, func
import pandas as pd

from app.config.notification_config import get_notification_config
from app.email.notification_service import email_notification_service

logger = logging.getLogger(__name__)

@dataclass
class EmailMetrics:
    """Email performance metrics"""
    total_sent: int = 0
    total_delivered: int = 0
    total_opened: int = 0
    total_clicked: int = 0
    total_bounced: int = 0
    total_spam: int = 0
    delivery_rate: float = 0.0
    open_rate: float = 0.0
    click_rate: float = 0.0
    bounce_rate: float = 0.0
    spam_rate: float = 0.0
    average_delivery_time: float = 0.0

@dataclass
class EngagementMetrics:
    """Email engagement metrics"""
    open_times: List[datetime] = None
    click_times: List[datetime] = None
    click_urls: List[str] = None
    device_types: Dict[str, int] = None
    geographic_data: Dict[str, int] = None
    
    def __post_init__(self):
        if self.open_times is None:
            self.open_times = []
        if self.click_times is None:
            self.click_times = []
        if self.click_urls is None:
            self.click_urls = []
        if self.device_types is None:
            self.device_types = {}
        if self.geographic_data is None:
            self.geographic_data = {}

class EmailAnalytics:
    """Comprehensive email analytics system"""
    
    def __init__(self):
        self.config = get_notification_config()
        self.redis_client = None
        self.db_connection = None
        self.monitoring_active = False
        self.monitor_thread = None
        
        # Analytics storage
        self.metrics_history = deque(maxlen=4320)  # 30 days of data (every 10 minutes)
        self.engagement_data = defaultdict(EngagementMetrics)
        self.bounce_analysis = defaultdict(list)
        self.spam_analysis = defaultdict(list)
        
        # Performance tracking
        self.delivery_times = deque(maxlen=10000)
        self.open_times = deque(maxlen=10000)
        self.click_times = deque(maxlen=10000)
        
        # Monitoring thresholds
        self.thresholds = {
            'delivery_rate_warning': 0.90,
            'delivery_rate_critical': 0.80,
            'open_rate_warning': 0.15,
            'open_rate_critical': 0.10,
            'bounce_rate_warning': 0.05,
            'bounce_rate_critical': 0.10,
            'spam_rate_warning': 0.01,
            'spam_rate_critical': 0.02
        }
        
        self._setup_connections()
        self._create_analytics_tables()
        self._start_monitoring()
    
    def _setup_connections(self):
        """Setup database and Redis connections"""
        try:
            # Redis connection
            self.redis_client = redis.from_url(
                self.config.redis_url,
                db=self.config.redis_notification_db,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            self.redis_client.ping()
            
            # SQLite analytics database
            self.db_connection = sqlite3.connect('email_analytics.db', check_same_thread=False)
            self.db_connection.row_factory = sqlite3.Row
            
            logger.info("Analytics connections established")
            
        except Exception as e:
            logger.error(f"Failed to setup analytics connections: {str(e)}")
    
    def _create_analytics_tables(self):
        """Create analytics database tables"""
        try:
            cursor = self.db_connection.cursor()
            
            # Email events table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS email_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    user_id INTEGER,
                    notification_type TEXT,
                    delivery_time REAL,
                    user_agent TEXT,
                    ip_address TEXT,
                    device_type TEXT,
                    geographic_location TEXT,
                    click_url TEXT,
                    bounce_reason TEXT,
                    spam_reason TEXT
                )
            ''')
            
            # Daily metrics table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS daily_metrics (
                    date DATE PRIMARY KEY,
                    total_sent INTEGER DEFAULT 0,
                    total_delivered INTEGER DEFAULT 0,
                    total_opened INTEGER DEFAULT 0,
                    total_clicked INTEGER DEFAULT 0,
                    total_bounced INTEGER DEFAULT 0,
                    total_spam INTEGER DEFAULT 0,
                    delivery_rate REAL DEFAULT 0.0,
                    open_rate REAL DEFAULT 0.0,
                    click_rate REAL DEFAULT 0.0,
                    bounce_rate REAL DEFAULT 0.0,
                    spam_rate REAL DEFAULT 0.0,
                    average_delivery_time REAL DEFAULT 0.0
                )
            ''')
            
            # Hourly metrics table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS hourly_metrics (
                    hour_timestamp DATETIME PRIMARY KEY,
                    total_sent INTEGER DEFAULT 0,
                    total_delivered INTEGER DEFAULT 0,
                    total_opened INTEGER DEFAULT 0,
                    total_clicked INTEGER DEFAULT 0,
                    total_bounced INTEGER DEFAULT 0,
                    total_spam INTEGER DEFAULT 0
                )
            ''')
            
            # User engagement table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_engagement (
                    user_id INTEGER,
                    email_id TEXT,
                    first_opened DATETIME,
                    last_opened DATETIME,
                    open_count INTEGER DEFAULT 0,
                    click_count INTEGER DEFAULT 0,
                    clicked_urls TEXT,
                    device_types TEXT,
                    PRIMARY KEY (user_id, email_id)
                )
            ''')
            
            self.db_connection.commit()
            logger.info("Analytics tables created/verified")
            
        except Exception as e:
            logger.error(f"Error creating analytics tables: {str(e)}")
    
    def _start_monitoring(self):
        """Start analytics monitoring"""
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True
        )
        self.monitor_thread.start()
        logger.info("Email analytics monitoring started")
    
    def _monitoring_loop(self):
        """Main analytics monitoring loop"""
        while self.monitoring_active:
            try:
                # Collect current metrics
                self._collect_metrics()
                
                # Update aggregations
                self._update_aggregations()
                
                # Check for alerts
                self._check_analytics_alerts()
                
                # Generate recommendations
                self._generate_recommendations()
                
                # Cleanup old data
                self._cleanup_old_data()
                
                time.sleep(600)  # Update every 10 minutes
                
            except Exception as e:
                logger.error(f"Analytics monitoring error: {str(e)}")
                time.sleep(60)
    
    def _collect_metrics(self):
        """Collect current email metrics"""
        try:
            # Get basic statistics from email service
            stats = email_notification_service.get_delivery_statistics()
            
            # Calculate rates
            total_sent = stats.get('sent', 0)
            total_delivered = stats.get('delivered', 0)
            total_opened = stats.get('opened', 0)
            total_clicked = stats.get('clicked', 0)
            total_bounced = stats.get('bounced', 0)
            total_spam = stats.get('spam', 0)
            
            delivery_rate = total_delivered / max(total_sent, 1)
            open_rate = total_opened / max(total_delivered, 1)
            click_rate = total_clicked / max(total_opened, 1)
            bounce_rate = total_bounced / max(total_sent, 1)
            spam_rate = total_spam / max(total_sent, 1)
            
            # Calculate average delivery time
            avg_delivery_time = self._calculate_average_delivery_time()
            
            # Create metrics object
            current_metrics = EmailMetrics(
                total_sent=total_sent,
                total_delivered=total_delivered,
                total_opened=total_opened,
                total_clicked=total_clicked,
                total_bounced=total_bounced,
                total_spam=total_spam,
                delivery_rate=delivery_rate,
                open_rate=open_rate,
                click_rate=click_rate,
                bounce_rate=bounce_rate,
                spam_rate=spam_rate,
                average_delivery_time=avg_delivery_time
            )
            
            # Store in history
            self.metrics_history.append({
                'timestamp': datetime.utcnow().isoformat(),
                'metrics': asdict(current_metrics)
            })
            
            # Store in database
            self._store_hourly_metrics(current_metrics)
            
        except Exception as e:
            logger.error(f"Error collecting metrics: {str(e)}")
    
    def _calculate_average_delivery_time(self) -> float:
        """Calculate average email delivery time"""
        try:
            if self.delivery_times:
                return sum(self.delivery_times) / len(self.delivery_times)
            return 0.0
        except Exception as e:
            logger.error(f"Error calculating average delivery time: {str(e)}")
            return 0.0
    
    def _store_hourly_metrics(self, metrics: EmailMetrics):
        """Store hourly metrics in database"""
        try:
            cursor = self.db_connection.cursor()
            
            # Get current hour timestamp
            current_hour = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
            
            # Insert or update hourly metrics
            cursor.execute('''
                INSERT OR REPLACE INTO hourly_metrics 
                (hour_timestamp, total_sent, total_delivered, total_opened, 
                 total_clicked, total_bounced, total_spam)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                current_hour,
                metrics.total_sent,
                metrics.total_delivered,
                metrics.total_opened,
                metrics.total_clicked,
                metrics.total_bounced,
                metrics.total_spam
            ))
            
            self.db_connection.commit()
            
        except Exception as e:
            logger.error(f"Error storing hourly metrics: {str(e)}")
    
    def _update_aggregations(self):
        """Update daily and weekly aggregations"""
        try:
            cursor = self.db_connection.cursor()
            
            # Update daily metrics
            today = datetime.utcnow().date()
            
            # Get today's hourly data
            cursor.execute('''
                SELECT 
                    SUM(total_sent) as sent,
                    SUM(total_delivered) as delivered,
                    SUM(total_opened) as opened,
                    SUM(total_clicked) as clicked,
                    SUM(total_bounced) as bounced,
                    SUM(total_spam) as spam
                FROM hourly_metrics
                WHERE DATE(hour_timestamp) = ?
            ''', (today,))
            
            result = cursor.fetchone()
            
            if result and result['sent'] > 0:
                delivery_rate = result['delivered'] / result['sent']
                open_rate = result['opened'] / max(result['delivered'], 1)
                click_rate = result['clicked'] / max(result['opened'], 1)
                bounce_rate = result['bounced'] / result['sent']
                spam_rate = result['spam'] / result['sent']
                
                # Update daily metrics
                cursor.execute('''
                    INSERT OR REPLACE INTO daily_metrics 
                    (date, total_sent, total_delivered, total_opened, total_clicked,
                     total_bounced, total_spam, delivery_rate, open_rate, click_rate,
                     bounce_rate, spam_rate, average_delivery_time)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    today,
                    result['sent'],
                    result['delivered'],
                    result['opened'],
                    result['clicked'],
                    result['bounced'],
                    result['spam'],
                    delivery_rate,
                    open_rate,
                    click_rate,
                    bounce_rate,
                    spam_rate,
                    self._calculate_average_delivery_time()
                ))
            
            self.db_connection.commit()
            
        except Exception as e:
            logger.error(f"Error updating aggregations: {str(e)}")
    
    def _check_analytics_alerts(self):
        """Check for analytics alerts and thresholds"""
        try:
            if not self.metrics_history:
                return
            
            current_metrics = self.metrics_history[-1]['metrics']
            alerts = []
            
            # Check delivery rate
            if current_metrics['delivery_rate'] < self.thresholds['delivery_rate_critical']:
                alerts.append({
                    'type': 'critical_delivery_rate',
                    'message': f"Critical delivery rate: {current_metrics['delivery_rate']:.2%}",
                    'value': current_metrics['delivery_rate'],
                    'threshold': self.thresholds['delivery_rate_critical']
                })
            elif current_metrics['delivery_rate'] < self.thresholds['delivery_rate_warning']:
                alerts.append({
                    'type': 'warning_delivery_rate',
                    'message': f"Low delivery rate: {current_metrics['delivery_rate']:.2%}",
                    'value': current_metrics['delivery_rate'],
                    'threshold': self.thresholds['delivery_rate_warning']
                })
            
            # Check open rate
            if current_metrics['open_rate'] < self.thresholds['open_rate_critical']:
                alerts.append({
                    'type': 'critical_open_rate',
                    'message': f"Critical open rate: {current_metrics['open_rate']:.2%}",
                    'value': current_metrics['open_rate'],
                    'threshold': self.thresholds['open_rate_critical']
                })
            elif current_metrics['open_rate'] < self.thresholds['open_rate_warning']:
                alerts.append({
                    'type': 'warning_open_rate',
                    'message': f"Low open rate: {current_metrics['open_rate']:.2%}",
                    'value': current_metrics['open_rate'],
                    'threshold': self.thresholds['open_rate_warning']
                })
            
            # Check bounce rate
            if current_metrics['bounce_rate'] > self.thresholds['bounce_rate_critical']:
                alerts.append({
                    'type': 'critical_bounce_rate',
                    'message': f"Critical bounce rate: {current_metrics['bounce_rate']:.2%}",
                    'value': current_metrics['bounce_rate'],
                    'threshold': self.thresholds['bounce_rate_critical']
                })
            elif current_metrics['bounce_rate'] > self.thresholds['bounce_rate_warning']:
                alerts.append({
                    'type': 'warning_bounce_rate',
                    'message': f"High bounce rate: {current_metrics['bounce_rate']:.2%}",
                    'value': current_metrics['bounce_rate'],
                    'threshold': self.thresholds['bounce_rate_warning']
                })
            
            # Send alerts
            for alert in alerts:
                self._send_analytics_alert(alert)
            
        except Exception as e:
            logger.error(f"Error checking analytics alerts: {str(e)}")
    
    def _send_analytics_alert(self, alert: Dict):
        """Send analytics alert"""
        try:
            alert_data = {
                **alert,
                'timestamp': datetime.utcnow().isoformat(),
                'service': 'email_analytics'
            }
            
            # Store in Redis
            if self.redis_client:
                self.redis_client.lpush('analytics_alerts', json.dumps(alert_data))
                self.redis_client.ltrim('analytics_alerts', 0, 99)  # Keep last 100
            
            logger.warning(f"Email analytics alert: {alert['message']}")
            
        except Exception as e:
            logger.error(f"Error sending analytics alert: {str(e)}")
    
    def _generate_recommendations(self):
        """Generate performance optimization recommendations"""
        try:
            if not self.metrics_history:
                return
            
            current_metrics = self.metrics_history[-1]['metrics']
            recommendations = []
            
            # Delivery rate recommendations
            if current_metrics['delivery_rate'] < 0.90:
                recommendations.append({
                    'type': 'delivery_optimization',
                    'priority': 'high',
                    'message': 'Consider reviewing email content and sender reputation',
                    'action': 'Review email templates and authenticate sending domain'
                })
            
            # Open rate recommendations
            if current_metrics['open_rate'] < 0.15:
                recommendations.append({
                    'type': 'subject_optimization',
                    'priority': 'medium',
                    'message': 'Low open rate detected',
                    'action': 'Test different subject lines and sending times'
                })
            
            # Bounce rate recommendations
            if current_metrics['bounce_rate'] > 0.05:
                recommendations.append({
                    'type': 'list_cleaning',
                    'priority': 'high',
                    'message': 'High bounce rate detected',
                    'action': 'Clean email list and verify email addresses'
                })
            
            # Store recommendations
            if recommendations:
                rec_data = {
                    'recommendations': recommendations,
                    'timestamp': datetime.utcnow().isoformat(),
                    'metrics': current_metrics
                }
                
                if self.redis_client:
                    self.redis_client.lpush('analytics_recommendations', json.dumps(rec_data))
                    self.redis_client.ltrim('analytics_recommendations', 0, 49)  # Keep last 50
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
    
    def _cleanup_old_data(self):
        """Clean up old analytics data"""
        try:
            cursor = self.db_connection.cursor()
            
            # Clean up hourly data older than 90 days
            cutoff_date = datetime.utcnow() - timedelta(days=90)
            cursor.execute('DELETE FROM hourly_metrics WHERE hour_timestamp < ?', (cutoff_date,))
            
            # Clean up email events older than 1 year
            cutoff_date = datetime.utcnow() - timedelta(days=365)
            cursor.execute('DELETE FROM email_events WHERE timestamp < ?', (cutoff_date,))
            
            self.db_connection.commit()
            
        except Exception as e:
            logger.error(f"Error cleaning up old data: {str(e)}")
    
    def track_email_event(self, email_id: str, event_type: str, 
                          user_id: Optional[int] = None, **kwargs):
        """Track email event (sent, delivered, opened, clicked, bounced, spam)"""
        try:
            timestamp = datetime.utcnow()
            
            # Store in database
            cursor = self.db_connection.cursor()
            cursor.execute('''
                INSERT INTO email_events 
                (email_id, event_type, timestamp, user_id, notification_type,
                 delivery_time, user_agent, ip_address, device_type, geographic_location,
                 click_url, bounce_reason, spam_reason)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                email_id,
                event_type,
                timestamp,
                user_id,
                kwargs.get('notification_type'),
                kwargs.get('delivery_time'),
                kwargs.get('user_agent'),
                kwargs.get('ip_address'),
                kwargs.get('device_type'),
                kwargs.get('geographic_location'),
                kwargs.get('click_url'),
                kwargs.get('bounce_reason'),
                kwargs.get('spam_reason')
            ))
            
            self.db_connection.commit()
            
            # Update engagement data
            if event_type == 'opened':
                self.open_times.append(time.time())
                if user_id:
                    self._update_user_engagement(user_id, email_id, 'open', timestamp)
            
            elif event_type == 'clicked':
                self.click_times.append(time.time())
                if user_id:
                    self._update_user_engagement(user_id, email_id, 'click', timestamp, kwargs.get('click_url'))
            
            elif event_type == 'delivered':
                delivery_time = kwargs.get('delivery_time', 0)
                if delivery_time > 0:
                    self.delivery_times.append(delivery_time)
            
            # Store in Redis for real-time tracking
            if self.redis_client:
                event_data = {
                    'email_id': email_id,
                    'event_type': event_type,
                    'timestamp': timestamp.isoformat(),
                    'user_id': user_id,
                    **kwargs
                }
                
                self.redis_client.lpush('email_events', json.dumps(event_data))
                self.redis_client.ltrim('email_events', 0, 9999)  # Keep last 10,000
            
        except Exception as e:
            logger.error(f"Error tracking email event: {str(e)}")
    
    def _update_user_engagement(self, user_id: int, email_id: str, 
                               event_type: str, timestamp: datetime, **kwargs):
        """Update user engagement data"""
        try:
            cursor = self.db_connection.cursor()
            
            # Check if engagement record exists
            cursor.execute('''
                SELECT * FROM user_engagement WHERE user_id = ? AND email_id = ?
            ''', (user_id, email_id))
            
            existing = cursor.fetchone()
            
            if existing:
                # Update existing record
                if event_type == 'open':
                    cursor.execute('''
                        UPDATE user_engagement 
                        SET open_count = open_count + 1,
                            last_opened = ?,
                            device_types = ?,
                            first_opened = COALESCE(first_opened, ?)
                        WHERE user_id = ? AND email_id = ?
                    ''', (timestamp, kwargs.get('device_type'), timestamp, user_id, email_id))
                
                elif event_type == 'click':
                    cursor.execute('''
                        UPDATE user_engagement 
                        SET click_count = click_count + 1,
                            clicked_urls = ?,
                            last_opened = COALESCE(last_opened, ?)
                        WHERE user_id = ? AND email_id = ?
                    ''', (kwargs.get('click_url'), timestamp, user_id, email_id))
            else:
                # Create new record
                cursor.execute('''
                    INSERT INTO user_engagement 
                    (user_id, email_id, first_opened, last_opened, open_count, 
                     click_count, clicked_urls, device_types)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    user_id, email_id,
                    timestamp if event_type == 'open' else None,
                    timestamp,
                    1 if event_type == 'open' else 0,
                    1 if event_type == 'click' else 0,
                    kwargs.get('click_url') if event_type == 'click' else None,
                    kwargs.get('device_type') if event_type == 'open' else None
                ))
            
            self.db_connection.commit()
            
        except Exception as e:
            logger.error(f"Error updating user engagement: {str(e)}")
    
    def get_analytics_dashboard(self, period: str = '7_days') -> Dict:
        """Get comprehensive analytics dashboard"""
        try:
            # Determine date range
            if period == '24_hours':
                start_date = datetime.utcnow() - timedelta(hours=24)
            elif period == '7_days':
                start_date = datetime.utcnow() - timedelta(days=7)
            elif period == '30_days':
                start_date = datetime.utcnow() - timedelta(days=30)
            else:
                start_date = datetime.utcnow() - timedelta(days=7)
            
            # Get metrics
            metrics = self._get_period_metrics(start_date)
            
            # Get engagement data
            engagement = self._get_engagement_metrics(start_date)
            
            # Get bounce analysis
            bounce_analysis = self._get_bounce_analysis(start_date)
            
            # Get performance trends
            trends = self._get_performance_trends(start_date)
            
            # Get top performing content
            top_content = self._get_top_performing_content(start_date)
            
            return {
                'period': period,
                'start_date': start_date.isoformat(),
                'end_date': datetime.utcnow().isoformat(),
                'metrics': metrics,
                'engagement': engagement,
                'bounce_analysis': bounce_analysis,
                'trends': trends,
                'top_content': top_content
            }
            
        except Exception as e:
            logger.error(f"Error getting analytics dashboard: {str(e)}")
            return {'error': str(e)}
    
    def _get_period_metrics(self, start_date: datetime) -> Dict:
        """Get metrics for specified period"""
        try:
            cursor = self.db_connection.cursor()
            
            if start_date.date() == datetime.utcnow().date():
                # Today's data from hourly metrics
                cursor.execute('''
                    SELECT 
                        SUM(total_sent) as sent,
                        SUM(total_delivered) as delivered,
                        SUM(total_opened) as opened,
                        SUM(total_clicked) as clicked,
                        SUM(total_bounced) as bounced,
                        SUM(total_spam) as spam
                    FROM hourly_metrics
                    WHERE hour_timestamp >= ?
                ''', (start_date,))
            else:
                # Historical data from daily metrics
                cursor.execute('''
                    SELECT 
                        SUM(total_sent) as sent,
                        SUM(total_delivered) as delivered,
                        SUM(total_opened) as opened,
                        SUM(total_clicked) as clicked,
                        SUM(total_bounced) as bounced,
                        SUM(total_spam) as spam
                    FROM daily_metrics
                    WHERE date >= ?
                ''', (start_date.date(),))
            
            result = cursor.fetchone()
            
            if result and result['sent'] > 0:
                return {
                    'total_sent': result['sent'],
                    'total_delivered': result['delivered'],
                    'total_opened': result['opened'],
                    'total_clicked': result['clicked'],
                    'total_bounced': result['bounced'],
                    'total_spam': result['spam'],
                    'delivery_rate': result['delivered'] / result['sent'],
                    'open_rate': result['opened'] / max(result['delivered'], 1),
                    'click_rate': result['clicked'] / max(result['opened'], 1),
                    'bounce_rate': result['bounced'] / result['sent'],
                    'spam_rate': result['spam'] / result['sent']
                }
            
            return {
                'total_sent': 0,
                'total_delivered': 0,
                'total_opened': 0,
                'total_clicked': 0,
                'total_bounced': 0,
                'total_spam': 0,
                'delivery_rate': 0.0,
                'open_rate': 0.0,
                'click_rate': 0.0,
                'bounce_rate': 0.0,
                'spam_rate': 0.0
            }
            
        except Exception as e:
            logger.error(f"Error getting period metrics: {str(e)}")
            return {}
    
    def _get_engagement_metrics(self, start_date: datetime) -> Dict:
        """Get engagement metrics"""
        try:
            cursor = self.db_connection.cursor()
            
            # Get engagement statistics
            cursor.execute('''
                SELECT 
                    COUNT(DISTINCT user_id) as unique_users,
                    SUM(open_count) as total_opens,
                    SUM(click_count) as total_clicks,
                    AVG(open_count) as avg_opens_per_user,
                    AVG(click_count) as avg_clicks_per_user
                FROM user_engagement
                WHERE first_opened >= ?
            ''', (start_date,))
            
            result = cursor.fetchone()
            
            # Get device type distribution
            cursor.execute('''
                SELECT device_type, COUNT(*) as count
                FROM user_engagement
                WHERE device_type IS NOT NULL AND first_opened >= ?
                GROUP BY device_type
                ORDER BY count DESC
            ''', (start_date,))
            
            device_types = dict(cursor.fetchall())
            
            # Get click URL distribution
            cursor.execute('''
                SELECT clicked_urls, COUNT(*) as count
                FROM user_engagement
                WHERE clicked_urls IS NOT NULL AND first_opened >= ?
                GROUP BY clicked_urls
                ORDER BY count DESC
                LIMIT 10
            ''', (start_date,))
            
            top_urls = dict(cursor.fetchall())
            
            return {
                'unique_users': result['unique_users'] if result else 0,
                'total_opens': result['total_opens'] if result else 0,
                'total_clicks': result['total_clicks'] if result else 0,
                'avg_opens_per_user': result['avg_opens_per_user'] if result else 0,
                'avg_clicks_per_user': result['avg_clicks_per_user'] if result else 0,
                'device_types': device_types,
                'top_clicked_urls': top_urls
            }
            
        except Exception as e:
            logger.error(f"Error getting engagement metrics: {str(e)}")
            return {}
    
    def _get_bounce_analysis(self, start_date: datetime) -> Dict:
        """Get bounce analysis"""
        try:
            cursor = self.db_connection.cursor()
            
            # Get bounce reasons
            cursor.execute('''
                SELECT bounce_reason, COUNT(*) as count
                FROM email_events
                WHERE event_type = 'bounced' AND timestamp >= ?
                GROUP BY bounce_reason
                ORDER BY count DESC
            ''', (start_date,))
            
            bounce_reasons = dict(cursor.fetchall())
            
            # Get spam reasons
            cursor.execute('''
                SELECT spam_reason, COUNT(*) as count
                FROM email_events
                WHERE event_type = 'spam' AND timestamp >= ?
                GROUP BY spam_reason
                ORDER BY count DESC
            ''', (start_date,))
            
            spam_reasons = dict(cursor.fetchall())
            
            return {
                'bounce_reasons': bounce_reasons,
                'spam_reasons': spam_reasons,
                'total_bounces': sum(bounce_reasons.values()),
                'total_spam': sum(spam_reasons.values())
            }
            
        except Exception as e:
            logger.error(f"Error getting bounce analysis: {str(e)}")
            return {}
    
    def _get_performance_trends(self, start_date: datetime) -> Dict:
        """Get performance trends"""
        try:
            cursor = self.db_connection.cursor()
            
            # Get daily metrics for trend analysis
            cursor.execute('''
                SELECT date, delivery_rate, open_rate, click_rate, bounce_rate
                FROM daily_metrics
                WHERE date >= ?
                ORDER BY date
            ''', (start_date.date(),))
            
            daily_data = cursor.fetchall()
            
            if len(daily_data) < 2:
                return {'trend': 'insufficient_data'}
            
            # Calculate trends
            first_half = daily_data[:len(daily_data)//2]
            second_half = daily_data[len(daily_data)//2:]
            
            first_avg_delivery = sum(row['delivery_rate'] for row in first_half) / len(first_half)
            second_avg_delivery = sum(row['delivery_rate'] for row in second_half) / len(second_half)
            
            first_avg_open = sum(row['open_rate'] for row in first_half) / len(first_half)
            second_avg_open = sum(row['open_rate'] for row in second_half) / len(second_half)
            
            first_avg_bounce = sum(row['bounce_rate'] for row in first_half) / len(first_half)
            second_avg_bounce = sum(row['bounce_rate'] for row in second_half) / len(second_half)
            
            delivery_trend = 'improving' if second_avg_delivery > first_avg_delivery else 'declining'
            open_trend = 'improving' if second_avg_open > first_avg_open else 'declining'
            bounce_trend = 'improving' if second_avg_bounce < first_avg_bounce else 'declining'
            
            return {
                'delivery_rate': delivery_trend,
                'open_rate': open_trend,
                'bounce_rate': bounce_trend,
                'daily_data': [
                    {
                        'date': row['date'].isoformat(),
                        'delivery_rate': row['delivery_rate'],
                        'open_rate': row['open_rate'],
                        'click_rate': row['click_rate'],
                        'bounce_rate': row['bounce_rate']
                    }
                    for row in daily_data
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting performance trends: {str(e)}")
            return {'trend': 'error', 'error': str(e)}
    
    def _get_top_performing_content(self, start_date: datetime) -> Dict:
        """Get top performing content"""
        try:
            cursor = self.db_connection.cursor()
            
            # Get top notification types by open rate
            cursor.execute('''
                SELECT 
                    e.notification_type,
                    COUNT(*) as sent,
                    SUM(CASE WHEN ee.event_type = 'opened' THEN 1 ELSE 0 END) as opened
                FROM email_events e
                LEFT JOIN email_events ee ON e.email_id = ee.email_id AND ee.event_type = 'opened'
                WHERE e.event_type = 'sent' AND e.timestamp >= ?
                GROUP BY e.notification_type
                HAVING sent > 10
                ORDER BY (CAST(opened AS FLOAT) / sent) DESC
                LIMIT 10
            ''', (start_date,))
            
            top_types = []
            for row in cursor.fetchall():
                top_types.append({
                    'notification_type': row['notification_type'],
                    'sent': row['sent'],
                    'opened': row['opened'],
                    'open_rate': row['opened'] / row['sent']
                })
            
            return {
                'top_notification_types': top_types
            }
            
        except Exception as e:
            logger.error(f"Error getting top performing content: {str(e)}")
            return {}
    
    def generate_report(self, report_type: str = 'weekly', 
                       format_type: str = 'json') -> Dict:
        """Generate analytics report"""
        try:
            # Determine date range
            if report_type == 'daily':
                start_date = datetime.utcnow() - timedelta(days=1)
            elif report_type == 'weekly':
                start_date = datetime.utcnow() - timedelta(days=7)
            elif report_type == 'monthly':
                start_date = datetime.utcnow() - timedelta(days=30)
            else:
                start_date = datetime.utcnow() - timedelta(days=7)
            
            # Get dashboard data
            dashboard_data = self.get_analytics_dashboard(
                f"{start_date.days}_days" if start_date.days < 30 else '30_days'
            )
            
            # Add report metadata
            report = {
                'report_type': report_type,
                'generated_at': datetime.utcnow().isoformat(),
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': datetime.utcnow().isoformat()
                },
                'data': dashboard_data,
                'recommendations': self._get_current_recommendations()
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            return {'error': str(e)}
    
    def _get_current_recommendations(self) -> List[Dict]:
        """Get current analytics recommendations"""
        try:
            if self.redis_client:
                recommendations_data = self.redis_client.lrange('analytics_recommendations', 0, 4)
                if recommendations_data:
                    latest = json.loads(recommendations_data[0])
                    return latest.get('recommendations', [])
            
            return []
            
        except Exception as e:
            logger.error(f"Error getting recommendations: {str(e)}")
            return []
    
    def stop_monitoring(self):
        """Stop analytics monitoring"""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        
        if self.db_connection:
            self.db_connection.close()
        
        logger.info("Email analytics monitoring stopped")

# Global analytics instance
email_analytics = EmailAnalytics()
