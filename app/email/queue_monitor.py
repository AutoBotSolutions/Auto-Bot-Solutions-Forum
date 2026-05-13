"""
Email Queue Monitoring System

This module provides comprehensive monitoring for the email queue system:
- Real-time queue status monitoring
- Performance metrics tracking
- Alert system for queue issues
- Historical data analysis
- Queue health checks
"""

import time
import json
import logging
import threading
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import redis
import psutil

from app.config.notification_config import get_notification_config

logger = logging.getLogger(__name__)

@dataclass
class QueueHealthStatus:
    """Queue health status"""
    status: str  # healthy, warning, critical
    queue_size: int
    processing_rate: float
    error_rate: float
    average_wait_time: float
    worker_utilization: float
    last_updated: datetime
    alerts: List[str]

@dataclass
class QueuePerformanceMetrics:
    """Queue performance metrics"""
    throughput: float  # emails/minute
    latency: float      # average wait time in seconds
    utilization: float  # worker utilization percentage
    error_rate: float   # error percentage
    backlog_age: float  # oldest item age in minutes
    success_rate: float  # delivery success rate

class EmailQueueMonitor:
    """Advanced email queue monitoring system"""
    
    def __init__(self):
        self.config = get_notification_config()
        self.redis_client = None
        self.monitoring_active = False
        self.monitor_thread = None
        
        # Metrics storage
        self.current_metrics = QueuePerformanceMetrics()
        self.health_status = QueueHealthStatus(
            status='unknown',
            queue_size=0,
            processing_rate=0.0,
            error_rate=0.0,
            average_wait_time=0.0,
            worker_utilization=0.0,
            last_updated=datetime.utcnow(),
            alerts=[]
        )
        
        # Historical data
        self.metrics_history = deque(maxlen=1440)  # 24 hours of data (1 per minute)
        self.alert_history = deque(maxlen=100)     # Last 100 alerts
        
        # Health thresholds
        self.thresholds = {
            'queue_size_warning': 500,
            'queue_size_critical': 1000,
            'error_rate_warning': 0.05,  # 5%
            'error_rate_critical': 0.10,  # 10%
            'latency_warning': 300,       # 5 minutes
            'latency_critical': 600,      # 10 minutes
            'utilization_warning': 0.80,  # 80%
            'utilization_critical': 0.95  # 95%
        }
        
        self._setup_redis()
        self._start_monitoring()
    
    def _setup_redis(self):
        """Setup Redis connection"""
        try:
            self.redis_client = redis.from_url(
                self.config.redis_url,
                db=self.config.redis_notification_db,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            self.redis_client.ping()
            logger.info("Redis connection established for queue monitor")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
    
    def _start_monitoring(self):
        """Start queue monitoring"""
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True
        )
        self.monitor_thread.start()
        logger.info("Queue monitoring started")
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                # Collect current metrics
                self._collect_metrics()
                
                # Update health status
                self._update_health_status()
                
                # Check for alerts
                self._check_alerts()
                
                # Store historical data
                self._store_historical_data()
                
                # Cleanup old data
                self._cleanup_old_data()
                
                time.sleep(60)  # Monitor every minute
                
            except Exception as e:
                logger.error(f"Queue monitoring error: {str(e)}")
                time.sleep(10)
    
    def _collect_metrics(self):
        """Collect current queue metrics"""
        try:
            if not self.redis_client:
                return
            
            # Get queue sizes for all priority levels
            queue_sizes = {}
            total_queue_size = 0
            
            for priority in ['high', 'normal', 'low']:
                queue_key = f"email_queue_{priority}"
                size = self.redis_client.llen(queue_key)
                queue_sizes[priority] = size
                total_queue_size += size
            
            # Calculate processing rate
            processing_rate = self._calculate_processing_rate()
            
            # Calculate error rate
            error_rate = self._calculate_error_rate()
            
            # Calculate average wait time
            avg_wait_time = self._calculate_average_wait_time()
            
            # Calculate worker utilization
            worker_utilization = self._calculate_worker_utilization()
            
            # Calculate backlog age
            backlog_age = self._calculate_backlog_age()
            
            # Calculate success rate
            success_rate = self._calculate_success_rate()
            
            # Update metrics
            self.current_metrics = QueuePerformanceMetrics(
                throughput=processing_rate,
                latency=avg_wait_time,
                utilization=worker_utilization,
                error_rate=error_rate,
                backlog_age=backlog_age,
                success_rate=success_rate
            )
            
        except Exception as e:
            logger.error(f"Error collecting metrics: {str(e)}")
    
    def _calculate_processing_rate(self) -> float:
        """Calculate emails processed per minute"""
        try:
            current_time = time.time()
            one_minute_ago = current_time - 60
            
            processed_count = 0
            
            # Check processed email keys
            for key in self.redis_client.scan_iter(match="email_processed:*"):
                timestamp = float(key.split(":")[1])
                if timestamp >= one_minute_ago:
                    processed_count += int(self.redis_client.get(key) or 0)
            
            return processed_count
            
        except Exception as e:
            logger.error(f"Error calculating processing rate: {str(e)}")
            return 0.0
    
    def _calculate_error_rate(self) -> float:
        """Calculate error rate"""
        try:
            # Get recent error count
            current_time = time.time()
            one_hour_ago = current_time - 3600
            
            error_count = 0
            total_count = 0
            
            for key in self.redis_client.scan_iter(match="email_stats:*"):
                if key.endswith('_failed'):
                    error_count += int(self.redis_client.get(key) or 0)
                elif key.endswith('_sent'):
                    total_count += int(self.redis_client.get(key) or 0)
            
            if total_count == 0:
                return 0.0
            
            return error_count / total_count
            
        except Exception as e:
            logger.error(f"Error calculating error rate: {str(e)}")
            return 0.0
    
    def _calculate_average_wait_time(self) -> float:
        """Calculate average wait time in queue"""
        try:
            total_wait_time = 0
            sample_size = min(50, self.redis_client.llen('email_queue_normal'))
            
            for i in range(sample_size):
                queue_item = self.redis_client.lindex('email_queue_normal', i)
                if queue_item:
                    email_data = json.loads(queue_item)
                    queued_at = email_data.get('queued_at', time.time())
                    wait_time = time.time() - queued_at
                    total_wait_time += wait_time
            
            return total_wait_time / sample_size if sample_size > 0 else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating average wait time: {str(e)}")
            return 0.0
    
    def _calculate_worker_utilization(self) -> float:
        """Calculate worker utilization"""
        try:
            # Get active workers from Redis
            active_workers = 0
            max_workers = self.config.email_queue_workers
            
            for key in self.redis_client.scan_iter(match="worker_status:*"):
                worker_data = json.loads(self.redis_client.get(key) or '{}')
                if worker_data.get('status') == 'active':
                    active_workers += 1
            
            return active_workers / max_workers if max_workers > 0 else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating worker utilization: {str(e)}")
            return 0.0
    
    def _calculate_backlog_age(self) -> float:
        """Calculate age of oldest item in queue"""
        try:
            oldest_item = self.redis_client.lindex('email_queue_normal', -1)  # Last item
            if oldest_item:
                email_data = json.loads(oldest_item)
                queued_at = email_data.get('queued_at', time.time())
                return (time.time() - queued_at) / 60  # Convert to minutes
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Error calculating backlog age: {str(e)}")
            return 0.0
    
    def _calculate_success_rate(self) -> float:
        """Calculate delivery success rate"""
        try:
            sent_count = int(self.redis_client.get('email_stats:sent') or 0)
            failed_count = int(self.redis_client.get('email_stats:failed') or 0)
            
            total_count = sent_count + failed_count
            if total_count == 0:
                return 1.0  # 100% if no deliveries attempted
            
            return sent_count / total_count
            
        except Exception as e:
            logger.error(f"Error calculating success rate: {str(e)}")
            return 0.0
    
    def _update_health_status(self):
        """Update queue health status"""
        try:
            alerts = []
            status = 'healthy'
            
            # Check queue size
            total_queue_size = (self.redis_client.llen('email_queue_high') + 
                              self.redis_client.llen('email_queue_normal') + 
                              self.redis_client.llen('email_queue_low'))
            
            if total_queue_size > self.thresholds['queue_size_critical']:
                status = 'critical'
                alerts.append(f"Critical queue size: {total_queue_size}")
            elif total_queue_size > self.thresholds['queue_size_warning']:
                status = 'warning'
                alerts.append(f"High queue size: {total_queue_size}")
            
            # Check error rate
            if self.current_metrics.error_rate > self.thresholds['error_rate_critical']:
                status = 'critical'
                alerts.append(f"Critical error rate: {self.current_metrics.error_rate:.2%}")
            elif self.current_metrics.error_rate > self.thresholds['error_rate_warning']:
                status = 'warning'
                alerts.append(f"High error rate: {self.current_metrics.error_rate:.2%}")
            
            # Check latency
            if self.current_metrics.latency > self.thresholds['latency_critical']:
                status = 'critical'
                alerts.append(f"Critical latency: {self.current_metrics.latency:.1f}s")
            elif self.current_metrics.latency > self.thresholds['latency_warning']:
                status = 'warning'
                alerts.append(f"High latency: {self.current_metrics.latency:.1f}s")
            
            # Check utilization
            if self.current_metrics.utilization > self.thresholds['utilization_critical']:
                status = 'critical'
                alerts.append(f"Critical utilization: {self.current_metrics.utilization:.1%}")
            elif self.current_metrics.utilization > self.thresholds['utilization_warning']:
                status = 'warning'
                alerts.append(f"High utilization: {self.current_metrics.utilization:.1%}")
            
            # Update health status
            self.health_status = QueueHealthStatus(
                status=status,
                queue_size=total_queue_size,
                processing_rate=self.current_metrics.throughput,
                error_rate=self.current_metrics.error_rate,
                average_wait_time=self.current_metrics.latency,
                worker_utilization=self.current_metrics.utilization,
                last_updated=datetime.utcnow(),
                alerts=alerts
            )
            
        except Exception as e:
            logger.error(f"Error updating health status: {str(e)}")
    
    def _check_alerts(self):
        """Check for and send alerts"""
        try:
            if self.health_status.status in ['warning', 'critical']:
                alert_data = {
                    'status': self.health_status.status,
                    'queue_size': self.health_status.queue_size,
                    'error_rate': self.health_status.error_rate,
                    'latency': self.health_status.average_wait_time,
                    'utilization': self.health_status.worker_utilization,
                    'alerts': self.health_status.alerts,
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                # Store alert
                self.redis_client.lpush('queue_alerts', json.dumps(alert_data))
                self.redis_client.ltrim('queue_alerts', 0, 99)  # Keep last 100
                
                # Add to history
                self.alert_history.append(alert_data)
                
                # Log alert
                logger.warning(f"Queue alert: {self.health_status.status.upper()} - {', '.join(self.health_status.alerts)}")
            
        except Exception as e:
            logger.error(f"Error checking alerts: {str(e)}")
    
    def _store_historical_data(self):
        """Store historical metrics data"""
        try:
            historical_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'metrics': asdict(self.current_metrics),
                'health_status': asdict(self.health_status)
            }
            
            self.metrics_history.append(historical_data)
            
            # Store in Redis for long-term retention
            self.redis_client.hset(
                'queue_metrics_history',
                str(int(time.time())),
                json.dumps(historical_data)
            )
            
        except Exception as e:
            logger.error(f"Error storing historical data: {str(e)}")
    
    def _cleanup_old_data(self):
        """Clean up old monitoring data"""
        try:
            # Clean up old metrics history (keep 7 days)
            cutoff_time = time.time() - (7 * 24 * 3600)  # 7 days ago
            
            for key in self.redis_client.hkeys('queue_metrics_history'):
                timestamp = int(key)
                if timestamp < cutoff_time:
                    self.redis_client.hdel('queue_metrics_history', key)
            
            # Clean up old processed email records (keep 1 hour)
            cutoff_time = time.time() - 3600
            
            for key in self.redis_client.scan_iter(match="email_processed:*"):
                timestamp = float(key.split(":")[1])
                if timestamp < cutoff_time:
                    self.redis_client.delete(key)
            
        except Exception as e:
            logger.error(f"Error cleaning up old data: {str(e)}")
    
    def get_queue_status(self) -> Dict:
        """Get current queue status"""
        try:
            if not self.redis_client:
                return {'error': 'Redis not available'}
            
            # Get queue sizes by priority
            queue_sizes = {}
            total_size = 0
            
            for priority in ['high', 'normal', 'low']:
                queue_key = f"email_queue_{priority}"
                size = self.redis_client.llen(queue_key)
                queue_sizes[priority] = size
                total_size += size
            
            # Get worker status
            worker_status = self._get_worker_status()
            
            return {
                'queue_sizes': queue_sizes,
                'total_size': total_size,
                'health_status': asdict(self.health_status),
                'current_metrics': asdict(self.current_metrics),
                'worker_status': worker_status,
                'thresholds': self.thresholds
            }
            
        except Exception as e:
            logger.error(f"Error getting queue status: {str(e)}")
            return {'error': str(e)}
    
    def _get_worker_status(self) -> List[Dict]:
        """Get status of all workers"""
        try:
            workers = []
            
            for key in self.redis_client.scan_iter(match="worker_status:*"):
                worker_data = json.loads(self.redis_client.get(key) or '{}')
                workers.append(worker_data)
            
            return workers
            
        except Exception as e:
            logger.error(f"Error getting worker status: {str(e)}")
            return []
    
    def get_performance_report(self, hours: int = 24) -> Dict:
        """Get performance report for specified time period"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            # Filter historical data
            relevant_data = [
                data for data in self.metrics_history
                if datetime.fromisoformat(data['timestamp']) >= cutoff_time
            ]
            
            if not relevant_data:
                return {'error': 'No data available for specified period'}
            
            # Calculate aggregates
            avg_throughput = sum(data['metrics']['throughput'] for data in relevant_data) / len(relevant_data)
            avg_latency = sum(data['metrics']['latency'] for data in relevant_data) / len(relevant_data)
            avg_utilization = sum(data['metrics']['utilization'] for data in relevant_data) / len(relevant_data)
            avg_error_rate = sum(data['metrics']['error_rate'] for data in relevant_data) / len(relevant_data)
            
            # Get alert count
            alert_count = sum(1 for data in relevant_data if data['health_status']['status'] != 'healthy')
            
            return {
                'period_hours': hours,
                'data_points': len(relevant_data),
                'averages': {
                    'throughput': avg_throughput,
                    'latency': avg_latency,
                    'utilization': avg_utilization,
                    'error_rate': avg_error_rate
                },
                'alert_count': alert_count,
                'current_status': asdict(self.health_status),
                'trends': self._calculate_trends(relevant_data)
            }
            
        except Exception as e:
            logger.error(f"Error generating performance report: {str(e)}")
            return {'error': str(e)}
    
    def _calculate_trends(self, data: List[Dict]) -> Dict:
        """Calculate performance trends"""
        try:
            if len(data) < 2:
                return {'trend': 'insufficient_data'}
            
            # Compare first half to second half
            mid_point = len(data) // 2
            first_half = data[:mid_point]
            second_half = data[mid_point:]
            
            first_avg_throughput = sum(d['metrics']['throughput'] for d in first_half) / len(first_half)
            second_avg_throughput = sum(d['metrics']['throughput'] for d in second_half) / len(second_half)
            
            first_avg_latency = sum(d['metrics']['latency'] for d in first_half) / len(first_half)
            second_avg_latency = sum(d['metrics']['latency'] for d in second_half) / len(second_half)
            
            first_avg_error_rate = sum(d['metrics']['error_rate'] for d in first_half) / len(first_half)
            second_avg_error_rate = sum(d['metrics']['error_rate'] for d in second_half) / len(second_half)
            
            throughput_trend = 'improving' if second_avg_throughput > first_avg_throughput else 'declining'
            latency_trend = 'improving' if second_avg_latency < first_avg_latency else 'declining'
            error_trend = 'improving' if second_avg_error_rate < first_avg_error_rate else 'declining'
            
            return {
                'throughput': throughput_trend,
                'latency': latency_trend,
                'error_rate': error_trend,
                'overall': self._calculate_overall_trend(throughput_trend, latency_trend, error_trend)
            }
            
        except Exception as e:
            logger.error(f"Error calculating trends: {str(e)}")
            return {'trend': 'error', 'error': str(e)}
    
    def _calculate_overall_trend(self, throughput_trend: str, latency_trend: str, error_trend: str) -> str:
        """Calculate overall trend"""
        improving_count = sum(1 for trend in [throughput_trend, latency_trend, error_trend] if trend == 'improving')
        
        if improving_count >= 2:
            return 'improving'
        elif improving_count == 1:
            return 'stable'
        else:
            return 'declining'
    
    def get_recent_alerts(self, limit: int = 10) -> List[Dict]:
        """Get recent alerts"""
        try:
            if not self.redis_client:
                return []
            
            alerts = []
            alert_items = self.redis_client.lrange('queue_alerts', 0, limit - 1)
            
            for item in alert_items:
                alerts.append(json.loads(item))
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error getting recent alerts: {str(e)}")
            return []
    
    def stop_monitoring(self):
        """Stop queue monitoring"""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("Queue monitoring stopped")

# Global queue monitor instance
queue_monitor = EmailQueueMonitor()
