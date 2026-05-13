"""
Push Notification Monitoring and Mobile App Integration

This module provides comprehensive push notification monitoring:
- Real-time delivery monitoring
- Platform-specific analytics
- Device performance tracking
- Mobile app integration SDK
- Push notification optimization
- Engagement analytics
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
from statistics import mean, median

from app.config.notification_config import get_notification_config
from app.notifications.mobile_service import mobile_notification_service

logger = logging.getLogger(__name__)

@dataclass
class PushMetrics:
    """Push notification performance metrics"""
    total_sent: int = 0
    total_delivered: int = 0
    total_failed: int = 0
    total_opened: int = 0
    total_clicked: int = 0
    delivery_rate: float = 0.0
    open_rate: float = 0.0
    click_rate: float = 0.0
    failure_rate: float = 0.0
    average_delivery_time: float = 0.0

@dataclass
class PlatformMetrics:
    """Platform-specific metrics"""
    platform: str
    sent: int = 0
    delivered: int = 0
    failed: int = 0
    opened: int = 0
    clicked: int = 0
    delivery_rate: float = 0.0
    open_rate: float = 0.0
    click_rate: float = 0.0
    failure_rate: float = 0.0
    average_response_time: float = 0.0
    error_types: Dict[str, int] = None
    
    def __post_init__(self):
        if self.error_types is None:
            self.error_types = {}

@dataclass
class DeviceMetrics:
    """Device performance metrics"""
    device_id: str
    platform: str
    user_id: int
    last_active: datetime
    total_notifications: int = 0
    successful_deliveries: int = 0
    failed_deliveries: int = 0
    open_count: int = 0
    click_count: int = 0
    app_version: str = ""
    os_version: str = ""
    device_model: str = ""

class PushNotificationMonitor:
    """Comprehensive push notification monitoring system"""
    
    def __init__(self):
        self.config = get_notification_config()
        self.redis_client = None
        self.db_connection = None
        self.monitoring_active = False
        self.monitor_thread = None
        
        # Metrics storage
        self.overall_metrics = PushMetrics()
        self.platform_metrics = defaultdict(PlatformMetrics)
        self.device_metrics = defaultdict(DeviceMetrics)
        self.metrics_history = deque(maxlen=4320)  # 30 days of data
        
        # Performance tracking
        self.delivery_times = defaultdict(list)
        self.open_times = defaultdict(list)
        self.click_times = defaultdict(list)
        self.error_patterns = defaultdict(int)
        
        # Monitoring thresholds
        self.thresholds = {
            'delivery_rate_warning': 0.85,
            'delivery_rate_critical': 0.75,
            'open_rate_warning': 0.10,
            'open_rate_critical': 0.05,
            'failure_rate_warning': 0.10,
            'failure_rate_critical': 0.20
        }
        
        self._setup_connections()
        self._create_monitoring_tables()
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
            
            # SQLite monitoring database
            self.db_connection = sqlite3.connect('push_monitoring.db', check_same_thread=False)
            self.db_connection.row_factory = sqlite3.Row
            
            logger.info("Push monitoring connections established")
            
        except Exception as e:
            logger.error(f"Failed to setup push monitoring connections: {str(e)}")
    
    def _create_monitoring_tables(self):
        """Create monitoring database tables"""
        try:
            cursor = self.db_connection.cursor()
            
            # Push events table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS push_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    notification_id TEXT NOT NULL,
                    device_id TEXT NOT NULL,
                    user_id INTEGER,
                    platform TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    delivery_time REAL,
                    response_time REAL,
                    error_message TEXT,
                    error_code TEXT,
                    app_version TEXT,
                    os_version TEXT,
                    device_model TEXT
                )
            ''')
            
            # Platform metrics table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS platform_metrics (
                    platform TEXT PRIMARY KEY,
                    total_sent INTEGER DEFAULT 0,
                    total_delivered INTEGER DEFAULT 0,
                    total_failed INTEGER DEFAULT 0,
                    total_opened INTEGER DEFAULT 0,
                    total_clicked INTEGER DEFAULT 0,
                    delivery_rate REAL DEFAULT 0.0,
                    open_rate REAL DEFAULT 0.0,
                    click_rate REAL DEFAULT 0.0,
                    failure_rate REAL DEFAULT 0.0,
                    average_delivery_time REAL DEFAULT 0.0,
                    last_updated DATETIME
                )
            ''')
            
            # Device performance table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS device_performance (
                    device_id TEXT PRIMARY KEY,
                    user_id INTEGER,
                    platform TEXT,
                    last_active DATETIME,
                    total_notifications INTEGER DEFAULT 0,
                    successful_deliveries INTEGER DEFAULT 0,
                    failed_deliveries INTEGER DEFAULT 0,
                    open_count INTEGER DEFAULT 0,
                    click_count INTEGER DEFAULT 0,
                    app_version TEXT,
                    os_version TEXT,
                    device_model TEXT,
                    performance_score REAL DEFAULT 0.0
                )
            ''')
            
            # Hourly metrics table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS hourly_push_metrics (
                    hour_timestamp DATETIME PRIMARY KEY,
                    total_sent INTEGER DEFAULT 0,
                    total_delivered INTEGER DEFAULT 0,
                    total_failed INTEGER DEFAULT 0,
                    total_opened INTEGER DEFAULT 0,
                    total_clicked INTEGER DEFAULT 0
                )
            ''')
            
            self.db_connection.commit()
            logger.info("Push monitoring tables created/verified")
            
        except Exception as e:
            logger.error(f"Error creating monitoring tables: {str(e)}")
    
    def _start_monitoring(self):
        """Start push notification monitoring"""
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True
        )
        self.monitor_thread.start()
        logger.info("Push notification monitoring started")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                # Collect current metrics
                self._collect_metrics()
                
                # Update aggregations
                self._update_aggregations()
                
                # Check for alerts
                self._check_alerts()
                
                # Generate recommendations
                self._generate_recommendations()
                
                # Cleanup old data
                self._cleanup_old_data()
                
                time.sleep(300)  # Update every 5 minutes
                
            except Exception as e:
                logger.error(f"Push monitoring error: {str(e)}")
                time.sleep(60)
    
    def _collect_metrics(self):
        """Collect current push notification metrics"""
        try:
            # Get device statistics from mobile service
            device_stats = mobile_notification_service.get_device_statistics()
            
            # Update platform metrics
            for platform, count in device_stats.get('platforms', {}).items():
                if platform not in self.platform_metrics:
                    self.platform_metrics[platform] = PlatformMetrics(platform=platform)
                
                self.platform_metrics[platform].sent = count
            
            # Calculate overall metrics
            total_sent = sum(m.sent for m in self.platform_metrics.values())
            total_delivered = sum(m.delivered for m in self.platform_metrics.values())
            total_failed = sum(m.failed for m in self.platform_metrics.values())
            total_opened = sum(m.opened for m in self.platform_metrics.values())
            total_clicked = sum(m.clicked for m in self.platform_metrics.values())
            
            # Update overall metrics
            self.overall_metrics = PushMetrics(
                total_sent=total_sent,
                total_delivered=total_delivered,
                total_failed=total_failed,
                total_opened=total_opened,
                total_clicked=total_clicked,
                delivery_rate=total_delivered / max(total_sent, 1),
                open_rate=total_opened / max(total_delivered, 1),
                click_rate=total_clicked / max(total_opened, 1),
                failure_rate=total_failed / max(total_sent, 1),
                average_delivery_time=self._calculate_average_delivery_time()
            )
            
            # Store in history
            self.metrics_history.append({
                'timestamp': datetime.utcnow().isoformat(),
                'overall': asdict(self.overall_metrics),
                'platforms': {p: asdict(m) for p, m in self.platform_metrics.items()}
            })
            
        except Exception as e:
            logger.error(f"Error collecting push metrics: {str(e)}")
    
    def _calculate_average_delivery_time(self) -> float:
        """Calculate average delivery time across all platforms"""
        try:
            all_times = []
            for platform_times in self.delivery_times.values():
                all_times.extend(platform_times)
            
            if all_times:
                return mean(all_times)
            return 0.0
            
        except Exception as e:
            logger.error(f"Error calculating average delivery time: {str(e)}")
            return 0.0
    
    def _update_aggregations(self):
        """Update platform and device aggregations"""
        try:
            cursor = self.db_connection.cursor()
            
            # Update platform metrics
            for platform, metrics in self.platform_metrics.items():
                cursor.execute('''
                    INSERT OR REPLACE INTO platform_metrics
                    (platform, total_sent, total_delivered, total_failed, total_opened,
                     total_clicked, delivery_rate, open_rate, click_rate, failure_rate,
                     average_delivery_time, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    platform,
                    metrics.sent,
                    metrics.delivered,
                    metrics.failed,
                    metrics.opened,
                    metrics.clicked,
                    metrics.delivery_rate,
                    metrics.open_rate,
                    metrics.click_rate,
                    metrics.failure_rate,
                    metrics.average_delivery_time,
                    datetime.utcnow()
                ))
            
            # Update hourly metrics
            current_hour = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
            cursor.execute('''
                INSERT OR REPLACE INTO hourly_push_metrics
                (hour_timestamp, total_sent, total_delivered, total_failed,
                 total_opened, total_clicked)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                current_hour,
                self.overall_metrics.total_sent,
                self.overall_metrics.total_delivered,
                self.overall_metrics.total_failed,
                self.overall_metrics.total_opened,
                self.overall_metrics.total_clicked
            ))
            
            self.db_connection.commit()
            
        except Exception as e:
            logger.error(f"Error updating aggregations: {str(e)}")
    
    def _check_alerts(self):
        """Check for push notification alerts"""
        try:
            alerts = []
            
            # Check overall delivery rate
            if self.overall_metrics.delivery_rate < self.thresholds['delivery_rate_critical']:
                alerts.append({
                    'type': 'critical_delivery_rate',
                    'message': f"Critical push delivery rate: {self.overall_metrics.delivery_rate:.2%}",
                    'value': self.overall_metrics.delivery_rate,
                    'threshold': self.thresholds['delivery_rate_critical']
                })
            elif self.overall_metrics.delivery_rate < self.thresholds['delivery_rate_warning']:
                alerts.append({
                    'type': 'warning_delivery_rate',
                    'message': f"Low push delivery rate: {self.overall_metrics.delivery_rate:.2%}",
                    'value': self.overall_metrics.delivery_rate,
                    'threshold': self.thresholds['delivery_rate_warning']
                })
            
            # Check platform-specific issues
            for platform, metrics in self.platform_metrics.items():
                if metrics.delivery_rate < self.thresholds['delivery_rate_critical']:
                    alerts.append({
                        'type': 'critical_platform_delivery',
                        'platform': platform,
                        'message': f"Critical {platform} delivery rate: {metrics.delivery_rate:.2%}",
                        'value': metrics.delivery_rate,
                        'threshold': self.thresholds['delivery_rate_critical']
                    })
            
            # Send alerts
            for alert in alerts:
                self._send_alert(alert)
            
        except Exception as e:
            logger.error(f"Error checking push alerts: {str(e)}")
    
    def _send_alert(self, alert: Dict):
        """Send push notification alert"""
        try:
            alert_data = {
                **alert,
                'timestamp': datetime.utcnow().isoformat(),
                'service': 'push_notifications'
            }
            
            # Store in Redis
            if self.redis_client:
                self.redis_client.lpush('push_alerts', json.dumps(alert_data))
                self.redis_client.ltrim('push_alerts', 0, 99)  # Keep last 100
            
            logger.warning(f"Push notification alert: {alert['message']}")
            
        except Exception as e:
            logger.error(f"Error sending push alert: {str(e)}")
    
    def _generate_recommendations(self):
        """Generate push notification optimization recommendations"""
        try:
            recommendations = []
            
            # Platform-specific recommendations
            for platform, metrics in self.platform_metrics.items():
                if metrics.delivery_rate < 0.80:
                    recommendations.append({
                        'type': 'platform_optimization',
                        'platform': platform,
                        'priority': 'high',
                        'message': f"Low {platform} delivery rate detected",
                        'action': f'Review {platform} configuration and device tokens'
                    })
                
                if metrics.failure_rate > 0.15:
                    recommendations.append({
                        'type': 'error_analysis',
                        'platform': platform,
                        'priority': 'medium',
                        'message': f"High {platform} failure rate detected",
                        'action': f'Analyze {platform} error patterns and update device registry'
                    })
            
            # Overall recommendations
            if self.overall_metrics.open_rate < 0.10:
                recommendations.append({
                    'type': 'engagement_optimization',
                    'priority': 'medium',
                    'message': 'Low push notification open rate',
                    'action': 'Optimize notification content and timing'
                })
            
            # Store recommendations
            if recommendations:
                rec_data = {
                    'recommendations': recommendations,
                    'timestamp': datetime.utcnow().isoformat(),
                    'metrics': asdict(self.overall_metrics)
                }
                
                if self.redis_client:
                    self.redis_client.lpush('push_recommendations', json.dumps(rec_data))
                    self.redis_client.ltrim('push_recommendations', 0, 49)  # Keep last 50
            
        except Exception as e:
            logger.error(f"Error generating push recommendations: {str(e)}")
    
    def _cleanup_old_data(self):
        """Clean up old monitoring data"""
        try:
            cursor = self.db_connection.cursor()
            
            # Clean up push events older than 90 days
            cutoff_date = datetime.utcnow() - timedelta(days=90)
            cursor.execute('DELETE FROM push_events WHERE timestamp < ?', (cutoff_date,))
            
            # Clean up hourly metrics older than 30 days
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            cursor.execute('DELETE FROM hourly_push_metrics WHERE hour_timestamp < ?', (cutoff_date,))
            
            self.db_connection.commit()
            
        except Exception as e:
            logger.error(f"Error cleaning up old push data: {str(e)}")
    
    def track_push_event(self, notification_id: str, device_id: str, platform: str,
                        event_type: str, user_id: Optional[int] = None, **kwargs):
        """Track push notification event"""
        try:
            timestamp = datetime.utcnow()
            
            # Store in database
            cursor = self.db_connection.cursor()
            cursor.execute('''
                INSERT INTO push_events
                (notification_id, device_id, user_id, platform, event_type, timestamp,
                 delivery_time, response_time, error_message, error_code,
                 app_version, os_version, device_model)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                notification_id,
                device_id,
                user_id,
                platform,
                event_type,
                timestamp,
                kwargs.get('delivery_time'),
                kwargs.get('response_time'),
                kwargs.get('error_message'),
                kwargs.get('error_code'),
                kwargs.get('app_version'),
                kwargs.get('os_version'),
                kwargs.get('device_model')
            ))
            
            self.db_connection.commit()
            
            # Update metrics
            self._update_event_metrics(platform, event_type, kwargs)
            
            # Update device metrics
            if user_id:
                self._update_device_metrics(device_id, platform, user_id, event_type, kwargs)
            
            # Store in Redis for real-time tracking
            if self.redis_client:
                event_data = {
                    'notification_id': notification_id,
                    'device_id': device_id,
                    'platform': platform,
                    'event_type': event_type,
                    'timestamp': timestamp.isoformat(),
                    'user_id': user_id,
                    **kwargs
                }
                
                self.redis_client.lpush('push_events', json.dumps(event_data))
                self.redis_client.ltrim('push_events', 0, 9999)  # Keep last 10,000
            
        except Exception as e:
            logger.error(f"Error tracking push event: {str(e)}")
    
    def _update_event_metrics(self, platform: str, event_type: str, kwargs: Dict):
        """Update platform metrics based on event"""
        try:
            if platform not in self.platform_metrics:
                self.platform_metrics[platform] = PlatformMetrics(platform=platform)
            
            metrics = self.platform_metrics[platform]
            
            if event_type == 'sent':
                metrics.sent += 1
            elif event_type == 'delivered':
                metrics.delivered += 1
                delivery_time = kwargs.get('delivery_time', 0)
                if delivery_time > 0:
                    self.delivery_times[platform].append(delivery_time)
            elif event_type == 'failed':
                metrics.failed += 1
                error_code = kwargs.get('error_code', 'unknown')
                metrics.error_types[error_code] = metrics.error_types.get(error_code, 0) + 1
                self.error_patterns[error_code] += 1
            elif event_type == 'opened':
                metrics.opened += 1
                response_time = kwargs.get('response_time', 0)
                if response_time > 0:
                    self.open_times[platform].append(response_time)
            elif event_type == 'clicked':
                metrics.clicked += 1
                response_time = kwargs.get('response_time', 0)
                if response_time > 0:
                    self.click_times[platform].append(response_time)
            
            # Recalculate rates
            if metrics.sent > 0:
                metrics.delivery_rate = metrics.delivered / metrics.sent
                metrics.failure_rate = metrics.failed / metrics.sent
            
            if metrics.delivered > 0:
                metrics.open_rate = metrics.opened / metrics.delivered
                metrics.click_rate = metrics.clicked / max(metrics.opened, 1)
            
            # Calculate average response times
            if self.delivery_times[platform]:
                metrics.average_response_time = mean(self.delivery_times[platform])
            
        except Exception as e:
            logger.error(f"Error updating event metrics: {str(e)}")
    
    def _update_device_metrics(self, device_id: str, platform: str, user_id: int,
                              event_type: str, kwargs: Dict):
        """Update device performance metrics"""
        try:
            if device_id not in self.device_metrics:
                self.device_metrics[device_id] = DeviceMetrics(
                    device_id=device_id,
                    platform=platform,
                    user_id=user_id,
                    last_active=datetime.utcnow()
                )
            
            device = self.device_metrics[device_id]
            device.last_active = datetime.utcnow()
            
            if event_type == 'sent':
                device.total_notifications += 1
            elif event_type == 'delivered':
                device.successful_deliveries += 1
            elif event_type == 'failed':
                device.failed_deliveries += 1
            elif event_type == 'opened':
                device.open_count += 1
            elif event_type == 'clicked':
                device.click_count += 1
            
            # Update device info
            device.app_version = kwargs.get('app_version', device.app_version)
            device.os_version = kwargs.get('os_version', device.os_version)
            device.device_model = kwargs.get('device_model', device.device_model)
            
            # Calculate performance score
            if device.total_notifications > 0:
                success_rate = device.successful_deliveries / device.total_notifications
                engagement_rate = (device.open_count + device.click_count) / max(device.total_notifications, 1)
                device.performance_score = (success_rate * 0.7) + (engagement_rate * 0.3)
            
            # Update database
            cursor = self.db_connection.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO device_performance
                (device_id, user_id, platform, last_active, total_notifications,
                 successful_deliveries, failed_deliveries, open_count, click_count,
                 app_version, os_version, device_model, performance_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                device_id, user_id, platform, device.last_active,
                device.total_notifications, device.successful_deliveries,
                device.failed_deliveries, device.open_count, device.click_count,
                device.app_version, device.os_version, device.device_model,
                device.performance_score
            ))
            
            self.db_connection.commit()
            
        except Exception as e:
            logger.error(f"Error updating device metrics: {str(e)}")
    
    def get_push_dashboard(self, period: str = '7_days') -> Dict:
        """Get comprehensive push notification dashboard"""
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
            
            # Get overall metrics
            overall_metrics = asdict(self.overall_metrics)
            
            # Get platform breakdown
            platform_breakdown = {
                platform: asdict(metrics) 
                for platform, metrics in self.platform_metrics.items()
            }
            
            # Get device performance
            device_performance = self._get_device_performance_summary(start_date)
            
            # Get engagement analytics
            engagement_analytics = self._get_engagement_analytics(start_date)
            
            # Get error analysis
            error_analysis = self._get_error_analysis(start_date)
            
            # Get performance trends
            performance_trends = self._get_performance_trends(start_date)
            
            return {
                'period': period,
                'start_date': start_date.isoformat(),
                'end_date': datetime.utcnow().isoformat(),
                'overall_metrics': overall_metrics,
                'platform_breakdown': platform_breakdown,
                'device_performance': device_performance,
                'engagement_analytics': engagement_analytics,
                'error_analysis': error_analysis,
                'performance_trends': performance_trends
            }
            
        except Exception as e:
            logger.error(f"Error getting push dashboard: {str(e)}")
            return {'error': str(e)}
    
    def _get_device_performance_summary(self, start_date: datetime) -> Dict:
        """Get device performance summary"""
        try:
            cursor = self.db_connection.cursor()
            
            # Get top performing devices
            cursor.execute('''
                SELECT device_id, platform, user_id, total_notifications,
                       successful_deliveries, failed_deliveries, open_count, click_count,
                       performance_score, app_version, os_version, device_model
                FROM device_performance
                WHERE last_active >= ?
                ORDER BY performance_score DESC
                LIMIT 20
            ''', (start_date,))
            
            top_devices = [dict(row) for row in cursor.fetchall()]
            
            # Get platform distribution
            cursor.execute('''
                SELECT platform, COUNT(*) as device_count,
                       AVG(performance_score) as avg_score,
                       AVG(successful_deliveries * 1.0 / total_notifications) as avg_success_rate
                FROM device_performance
                WHERE last_active >= ?
                GROUP BY platform
            ''', (start_date,))
            
            platform_summary = [dict(row) for row in cursor.fetchall()]
            
            # Get app version distribution
            cursor.execute('''
                SELECT app_version, COUNT(*) as device_count,
                       AVG(performance_score) as avg_score
                FROM device_performance
                WHERE last_active >= ? AND app_version IS NOT NULL
                GROUP BY app_version
                ORDER BY device_count DESC
            ''', (start_date,))
            
            version_summary = [dict(row) for row in cursor.fetchall()]
            
            return {
                'top_devices': top_devices,
                'platform_summary': platform_summary,
                'version_summary': version_summary
            }
            
        except Exception as e:
            logger.error(f"Error getting device performance summary: {str(e)}")
            return {}
    
    def _get_engagement_analytics(self, start_date: datetime) -> Dict:
        """Get engagement analytics"""
        try:
            cursor = self.db_connection.cursor()
            
            # Get engagement metrics
            cursor.execute('''
                SELECT 
                    COUNT(DISTINCT device_id) as total_devices,
                    SUM(open_count) as total_opens,
                    SUM(click_count) as total_clicks,
                    AVG(open_count * 1.0 / total_notifications) as avg_open_rate,
                    AVG(click_count * 1.0 / total_notifications) as avg_click_rate
                FROM device_performance
                WHERE last_active >= ? AND total_notifications > 0
            ''', (start_date,))
            
            engagement_stats = dict(cursor.fetchone())
            
            # Get engagement by platform
            cursor.execute('''
                SELECT platform,
                       AVG(open_count * 1.0 / total_notifications) as avg_open_rate,
                       AVG(click_count * 1.0 / total_notifications) as avg_click_rate,
                       COUNT(*) as device_count
                FROM device_performance
                WHERE last_active >= ? AND total_notifications > 0
                GROUP BY platform
            ''', (start_date,))
            
            platform_engagement = [dict(row) for row in cursor.fetchall()]
            
            return {
                'overall': engagement_stats,
                'by_platform': platform_engagement
            }
            
        except Exception as e:
            logger.error(f"Error getting engagement analytics: {str(e)}")
            return {}
    
    def _get_error_analysis(self, start_date: datetime) -> Dict:
        """Get error analysis"""
        try:
            cursor = self.db_connection.cursor()
            
            # Get error types by platform
            cursor.execute('''
                SELECT platform, error_code, COUNT(*) as count
                FROM push_events
                WHERE event_type = 'failed' AND timestamp >= ?
                GROUP BY platform, error_code
                ORDER BY count DESC
            ''', (start_date,))
            
            error_by_platform = defaultdict(list)
            for row in cursor.fetchall():
                error_by_platform[row['platform']].append({
                    'error_code': row['error_code'],
                    'count': row['count']
                })
            
            # Get overall error patterns
            cursor.execute('''
                SELECT error_code, COUNT(*) as count
                FROM push_events
                WHERE event_type = 'failed' AND timestamp >= ?
                GROUP BY error_code
                ORDER BY count DESC
                LIMIT 10
            ''', (start_date,))
            
            top_errors = [dict(row) for row in cursor.fetchall()]
            
            return {
                'by_platform': dict(error_by_platform),
                'top_errors': top_errors
            }
            
        except Exception as e:
            logger.error(f"Error getting error analysis: {str(e)}")
            return {}
    
    def _get_performance_trends(self, start_date: datetime) -> Dict:
        """Get performance trends"""
        try:
            cursor = self.db_connection.cursor()
            
            # Get hourly metrics for trend analysis
            cursor.execute('''
                SELECT hour_timestamp, total_sent, total_delivered, total_failed,
                       total_opened, total_clicked
                FROM hourly_push_metrics
                WHERE hour_timestamp >= ?
                ORDER BY hour_timestamp
            ''', (start_date,))
            
            hourly_data = cursor.fetchall()
            
            if len(hourly_data) < 2:
                return {'trend': 'insufficient_data'}
            
            # Calculate trends
            first_half = hourly_data[:len(hourly_data)//2]
            second_half = hourly_data[len(hourly_data)//2:]
            
            first_avg_delivery = sum(row['total_delivered'] / max(row['total_sent'], 1) for row in first_half) / len(first_half)
            second_avg_delivery = sum(row['total_delivered'] / max(row['total_sent'], 1) for row in second_half) / len(second_half)
            
            first_avg_open = sum(row['total_opened'] / max(row['total_delivered'], 1) for row in first_half if row['total_delivered'] > 0) / max(sum(1 for row in first_half if row['total_delivered'] > 0), 1)
            second_avg_open = sum(row['total_opened'] / max(row['total_delivered'], 1) for row in second_half if row['total_delivered'] > 0) / max(sum(1 for row in second_half if row['total_delivered'] > 0), 1)
            
            delivery_trend = 'improving' if second_avg_delivery > first_avg_delivery else 'declining'
            open_trend = 'improving' if second_avg_open > first_avg_open else 'declining'
            
            return {
                'delivery_rate': delivery_trend,
                'open_rate': open_trend,
                'hourly_data': [
                    {
                        'hour': row['hour_timestamp'].isoformat(),
                        'sent': row['total_sent'],
                        'delivered': row['total_delivered'],
                        'failed': row['total_failed'],
                        'opened': row['total_opened'],
                        'clicked': row['total_clicked'],
                        'delivery_rate': row['total_delivered'] / max(row['total_sent'], 1),
                        'open_rate': row['total_opened'] / max(row['total_delivered'], 1) if row['total_delivered'] > 0 else 0
                    }
                    for row in hourly_data
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting performance trends: {str(e)}")
            return {'trend': 'error', 'error': str(e)}
    
    def generate_mobile_sdk_config(self) -> Dict:
        """Generate mobile SDK configuration"""
        try:
            config = {
                'api_endpoints': {
                    'register_device': '/api/mobile/register',
                    'unregister_device': '/api/mobile/unregister',
                    'track_event': '/api/mobile/track',
                    'update_preferences': '/api/mobile/preferences'
                },
                'platform_config': {
                    'ios': {
                        'apns_enabled': self.config.apns_enabled,
                        'bundle_id': self.config.apns_bundle_id,
                        'sandbox': self.config.apns_sandbox
                    },
                    'android': {
                        'fcm_enabled': self.config.fcm_enabled,
                        'sender_id': self.config.fcm_sender_id
                    },
                    'huawei': {
                        'hms_enabled': self.config.hms_enabled,
                        'app_id': self.config.hms_app_id
                    },
                    'web': {
                        'vapid_enabled': True,
                        'public_key': self.config.vapid_public_key
                    }
                },
                'tracking_config': {
                    'track_deliveries': True,
                    'track_opens': True,
                    'track_clicks': True,
                    'track_errors': True,
                    'batch_events': True,
                    'batch_size': 50,
                    'batch_interval': 60
                },
                'retry_config': {
                    'max_retries': 3,
                    'retry_delay': 5,
                    'exponential_backoff': True
                },
                'performance_config': {
                    'connection_timeout': 30,
                    'request_timeout': 10,
                    'max_concurrent_requests': 10
                }
            }
            
            return config
            
        except Exception as e:
            logger.error(f"Error generating mobile SDK config: {str(e)}")
            return {}
    
    def stop_monitoring(self):
        """Stop push notification monitoring"""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        
        if self.db_connection:
            self.db_connection.close()
        
        logger.info("Push notification monitoring stopped")

# Global push monitor instance
push_monitor = PushNotificationMonitor()
