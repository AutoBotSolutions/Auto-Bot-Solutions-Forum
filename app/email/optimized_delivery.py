"""
Optimized Email Delivery System with Queue Monitoring

This module provides advanced email delivery optimization including:
- Intelligent queue management
- Delivery rate limiting
- Bounce handling
- Performance monitoring
- Retry strategies
- Analytics tracking
"""

import asyncio
import time
import json
import logging
import smtplib
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor
import redis
import psutil

from app.config.notification_config import get_notification_config
from app.email.notification_service import EmailNotificationService

logger = logging.getLogger(__name__)

@dataclass
class EmailDeliveryMetrics:
    """Email delivery metrics"""
    total_sent: int = 0
    total_failed: int = 0
    total_bounced: int = 0
    total_opened: int = 0
    total_clicked: int = 0
    average_delivery_time: float = 0.0
    queue_size: int = 0
    processing_rate: float = 0.0
    error_rate: float = 0.0
    last_updated: datetime = None

@dataclass
class QueueMetrics:
    """Queue performance metrics"""
    queue_size: int = 0
    processing_rate: float = 0.0
    average_wait_time: float = 0.0
    workers_active: int = 0
    workers_idle: int = 0
    throughput: float = 0.0
    backlog_age: float = 0.0

class EmailDeliveryOptimizer:
    """Advanced email delivery optimizer with monitoring"""
    
    def __init__(self):
        self.config = get_notification_config()
        self.redis_client = None
        self.email_service = EmailNotificationService()
        
        # Performance tracking
        self.metrics = EmailDeliveryMetrics()
        self.queue_metrics = QueueMetrics()
        self.delivery_times = deque(maxlen=1000)
        self.error_history = deque(maxlen=100)
        
        # Rate limiting
        self.rate_limiter = RateLimiter(
            max_rate=100,  # emails per minute
            time_window=60
        )
        
        # Worker management
        self.workers = []
        self.worker_stats = defaultdict(dict)
        self.max_workers = self.config.email_queue_workers
        
        # Monitoring
        self.monitoring_active = False
        self.monitor_thread = None
        
        # Analytics
        self.delivery_analytics = DeliveryAnalytics()
        
        self._setup_redis()
        self._start_monitoring()
    
    def _setup_redis(self):
        """Setup Redis connection for queue management"""
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
            logger.info("Redis connection established for email optimizer")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
    
    def _start_monitoring(self):
        """Start performance monitoring"""
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_performance,
            daemon=True
        )
        self.monitor_thread.start()
    
    def _monitor_performance(self):
        """Monitor email delivery performance"""
        while self.monitoring_active:
            try:
                # Update queue metrics
                self._update_queue_metrics()
                
                # Update delivery metrics
                self._update_delivery_metrics()
                
                # Check for performance issues
                self._check_performance_alerts()
                
                # Cleanup old data
                self._cleanup_old_data()
                
                time.sleep(30)  # Monitor every 30 seconds
                
            except Exception as e:
                logger.error(f"Performance monitoring error: {str(e)}")
                time.sleep(10)
    
    def _update_queue_metrics(self):
        """Update queue performance metrics"""
        if not self.redis_client:
            return
        
        try:
            # Get queue size
            queue_size = self.redis_client.llen('email_queue')
            self.queue_metrics.queue_size = queue_size
            
            # Get processing rate
            processing_rate = self._calculate_processing_rate()
            self.queue_metrics.processing_rate = processing_rate
            
            # Get worker status
            active_workers = len([w for w in self.workers if w.is_alive()])
            self.queue_metrics.workers_active = active_workers
            self.queue_metrics.workers_idle = self.max_workers - active_workers
            
            # Calculate throughput
            self.queue_metrics.throughput = self._calculate_throughput()
            
            # Calculate backlog age
            self.queue_metrics.backlog_age = self._calculate_backlog_age()
            
        except Exception as e:
            logger.error(f"Error updating queue metrics: {str(e)}")
    
    def _update_delivery_metrics(self):
        """Update delivery performance metrics"""
        try:
            # Get delivery statistics from Redis
            stats = self.email_service.get_delivery_statistics()
            
            self.metrics.total_sent = stats.get('sent', 0)
            self.metrics.total_failed = stats.get('failed', 0)
            self.metrics.total_bounced = stats.get('bounced', 0)
            self.metrics.total_opened = stats.get('opened', 0)
            self.metrics.total_clicked = stats.get('clicked', 0)
            
            # Calculate average delivery time
            if self.delivery_times:
                self.metrics.average_delivery_time = sum(self.delivery_times) / len(self.delivery_times)
            
            # Calculate error rate
            total_deliveries = self.metrics.total_sent + self.metrics.total_failed
            if total_deliveries > 0:
                self.metrics.error_rate = self.metrics.total_failed / total_deliveries
            
            self.metrics.last_updated = datetime.utcnow()
            
        except Exception as e:
            logger.error(f"Error updating delivery metrics: {str(e)}")
    
    def _calculate_processing_rate(self) -> float:
        """Calculate email processing rate (emails/minute)"""
        try:
            if not self.redis_client:
                return 0.0
            
            # Get processed count from last minute
            current_time = time.time()
            one_minute_ago = current_time - 60
            
            processed_count = 0
            pattern = "email_processed:*"
            
            for key in self.redis_client.scan_iter(match=pattern):
                timestamp = float(key.split(":")[1])
                if timestamp >= one_minute_ago:
                    processed_count += self.redis_client.get(key) or 0
            
            return processed_count
            
        except Exception as e:
            logger.error(f"Error calculating processing rate: {str(e)}")
            return 0.0
    
    def _calculate_throughput(self) -> float:
        """Calculate queue throughput"""
        try:
            if self.queue_metrics.workers_active == 0:
                return 0.0
            
            return self.queue_metrics.processing_rate / self.queue_metrics.workers_active
            
        except Exception as e:
            logger.error(f"Error calculating throughput: {str(e)}")
            return 0.0
    
    def _calculate_backlog_age(self) -> float:
        """Calculate average backlog age in minutes"""
        try:
            if not self.redis_client or self.queue_metrics.queue_size == 0:
                return 0.0
            
            # Get timestamps from queue items
            total_age = 0
            sample_size = min(100, self.queue_metrics.queue_size)
            
            for i in range(sample_size):
                queue_item = self.redis_client.lindex('email_queue', i)
                if queue_item:
                    email_data = json.loads(queue_item)
                    created_at = email_data.get('created_at', time.time())
                    age = time.time() - created_at
                    total_age += age
            
            return (total_age / sample_size) / 60  # Convert to minutes
            
        except Exception as e:
            logger.error(f"Error calculating backlog age: {str(e)}")
            return 0.0
    
    def _check_performance_alerts(self):
        """Check for performance issues and send alerts"""
        alerts = []
        
        # Queue size alert
        if self.queue_metrics.queue_size > 1000:
            alerts.append({
                'type': 'queue_backlog',
                'message': f"Email queue backlog: {self.queue_metrics.queue_size} emails",
                'severity': 'warning'
            })
        
        # Error rate alert
        if self.metrics.error_rate > 0.1:  # 10% error rate
            alerts.append({
                'type': 'high_error_rate',
                'message': f"High error rate: {self.metrics.error_rate:.2%}",
                'severity': 'critical'
            })
        
        # Delivery time alert
        if self.metrics.average_delivery_time > 30:  # 30 seconds
            alerts.append({
                'type': 'slow_delivery',
                'message': f"Slow delivery time: {self.metrics.average_delivery_time:.2f}s",
                'severity': 'warning'
            })
        
        # Worker alert
        if self.queue_metrics.workers_active < self.max_workers * 0.5:
            alerts.append({
                'type': 'worker_shortage',
                'message': f"Worker shortage: {self.queue_metrics.workers_active}/{self.max_workers} active",
                'severity': 'warning'
            })
        
        # Send alerts
        for alert in alerts:
            self._send_alert(alert)
    
    def _send_alert(self, alert: Dict):
        """Send performance alert"""
        try:
            # Store alert in Redis
            alert_data = {
                **alert,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            self.redis_client.lpush('email_alerts', json.dumps(alert_data))
            self.redis_client.ltrim('email_alerts', 0, 99)  # Keep last 100 alerts
            
            logger.warning(f"Email delivery alert: {alert['message']}")
            
        except Exception as e:
            logger.error(f"Error sending alert: {str(e)}")
    
    def _cleanup_old_data(self):
        """Clean up old monitoring data"""
        try:
            if not self.redis_client:
                return
            
            # Clean up old processing records
            cutoff_time = time.time() - 3600  # 1 hour ago
            pattern = "email_processed:*"
            
            for key in self.redis_client.scan_iter(match=pattern):
                timestamp = float(key.split(":")[1])
                if timestamp < cutoff_time:
                    self.redis_client.delete(key)
            
        except Exception as e:
            logger.error(f"Error cleaning up old data: {str(e)}")
    
    def optimize_delivery(self, email_data: Dict) -> Dict:
        """Optimize email delivery with intelligent routing"""
        try:
            # Check rate limits
            if not self.rate_limiter.can_send():
                return {
                    'success': False,
                    'error': 'Rate limit exceeded',
                    'retry_after': self.rate_limiter.retry_after()
                }
            
            # Optimize delivery strategy
            delivery_strategy = self._select_delivery_strategy(email_data)
            
            # Apply optimizations
            optimized_email = self._apply_optimizations(email_data, delivery_strategy)
            
            # Queue for delivery
            queue_result = self._queue_optimized_email(optimized_email)
            
            # Track optimization
            self._track_optimization(email_data, delivery_strategy, queue_result)
            
            return queue_result
            
        except Exception as e:
            logger.error(f"Error optimizing delivery: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _select_delivery_strategy(self, email_data: Dict) -> str:
        """Select optimal delivery strategy based on email characteristics"""
        priority = email_data.get('priority', 'normal')
        recipient_count = len(email_data.get('recipients', []))
        
        if priority == 'urgent':
            return 'immediate'
        elif recipient_count > 100:
            return 'bulk_batch'
        elif recipient_count > 10:
            return 'batch'
        else:
            return 'standard'
    
    def _apply_optimizations(self, email_data: Dict, strategy: str) -> Dict:
        """Apply delivery optimizations based on strategy"""
        optimized = email_data.copy()
        
        if strategy == 'immediate':
            optimized['delivery_priority'] = 'high'
            optimized['retry_attempts'] = 5
            optimized['retry_delay'] = 1
        elif strategy == 'bulk_batch':
            optimized['delivery_priority'] = 'low'
            optimized['batch_size'] = 50
            optimized['delay_between_batches'] = 2
        elif strategy == 'batch':
            optimized['delivery_priority'] = 'normal'
            optimized['batch_size'] = 10
            optimized['delay_between_batches'] = 1
        else:
            optimized['delivery_priority'] = 'normal'
            optimized['retry_attempts'] = 3
            optimized['retry_delay'] = 5
        
        return optimized
    
    def _queue_optimized_email(self, optimized_email: Dict) -> Dict:
        """Queue optimized email for delivery"""
        try:
            if not self.redis_client:
                return {
                    'success': False,
                    'error': 'Redis not available'
                }
            
            # Add optimization metadata
            optimized_email['queued_at'] = time.time()
            optimized_email['optimization_applied'] = True
            
            # Queue with priority
            priority = optimized_email.get('delivery_priority', 'normal')
            queue_key = f"email_queue_{priority}"
            
            self.redis_client.rpush(queue_key, json.dumps(optimized_email))
            
            return {
                'success': True,
                'queue_key': queue_key,
                'priority': priority,
                'message': 'Email queued for optimized delivery'
            }
            
        except Exception as e:
            logger.error(f"Error queuing optimized email: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _track_optimization(self, email_data: Dict, strategy: str, result: Dict):
        """Track optimization performance"""
        try:
            tracking_data = {
                'strategy': strategy,
                'success': result.get('success', False),
                'timestamp': time.time(),
                'email_type': email_data.get('type', 'unknown'),
                'recipient_count': len(email_data.get('recipients', []))
            }
            
            # Store in analytics
            self.delivery_analytics.record_optimization(tracking_data)
            
        except Exception as e:
            logger.error(f"Error tracking optimization: {str(e)}")
    
    def get_performance_report(self) -> Dict:
        """Get comprehensive performance report"""
        try:
            report = {
                'timestamp': datetime.utcnow().isoformat(),
                'delivery_metrics': asdict(self.metrics),
                'queue_metrics': asdict(self.queue_metrics),
                'worker_status': self._get_worker_status(),
                'rate_limiter_status': self.rate_limiter.get_status(),
                'recent_alerts': self._get_recent_alerts(),
                'optimization_stats': self.delivery_analytics.get_optimization_stats()
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating performance report: {str(e)}")
            return {}
    
    def _get_worker_status(self) -> List[Dict]:
        """Get status of all workers"""
        worker_status = []
        
        for i, worker in enumerate(self.workers):
            status = {
                'worker_id': i,
                'alive': worker.is_alive(),
                'thread_id': worker.ident,
                'processed_count': self.worker_stats.get(i, {}).get('processed', 0),
                'error_count': self.worker_stats.get(i, {}).get('errors', 0),
                'last_activity': self.worker_stats.get(i, {}).get('last_activity')
            }
            worker_status.append(status)
        
        return worker_status
    
    def _get_recent_alerts(self) -> List[Dict]:
        """Get recent performance alerts"""
        try:
            if not self.redis_client:
                return []
            
            alerts = []
            alert_items = self.redis_client.lrange('email_alerts', 0, 9)  # Last 10 alerts
            
            for item in alert_items:
                alerts.append(json.loads(item))
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error getting recent alerts: {str(e)}")
            return []

class RateLimiter:
    """Intelligent rate limiting for email delivery"""
    
    def __init__(self, max_rate: int, time_window: int):
        self.max_rate = max_rate
        self.time_window = time_window
        self.requests = deque()
        self.lock = threading.Lock()
    
    def can_send(self) -> bool:
        """Check if we can send an email"""
        with self.lock:
            current_time = time.time()
            
            # Remove old requests
            while self.requests and self.requests[0] <= current_time - self.time_window:
                self.requests.popleft()
            
            # Check if we're under the limit
            return len(self.requests) < self.max_rate
    
    def record_send(self):
        """Record a send attempt"""
        with self.lock:
            self.requests.append(time.time())
    
    def retry_after(self) -> int:
        """Get seconds until next send is allowed"""
        with self.lock:
            if not self.requests:
                return 0
            
            oldest_request = self.requests[0]
            retry_time = oldest_request + self.time_window - time.time()
            return max(0, int(retry_time))
    
    def get_status(self) -> Dict:
        """Get rate limiter status"""
        with self.lock:
            current_time = time.time()
            recent_requests = sum(1 for req in self.requests if req >= current_time - self.time_window)
            
            return {
                'current_rate': recent_requests,
                'max_rate': self.max_rate,
                'time_window': self.time_window,
                'utilization': recent_requests / self.max_rate,
                'retry_after': self.retry_after()
            }

class DeliveryAnalytics:
    """Analytics for email delivery optimization"""
    
    def __init__(self):
        self.optimization_data = defaultdict(list)
        self.delivery_times = defaultdict(list)
        self.error_patterns = defaultdict(int)
    
    def record_optimization(self, tracking_data: Dict):
        """Record optimization data"""
        strategy = tracking_data['strategy']
        self.optimization_data[strategy].append(tracking_data)
        
        # Keep only recent data
        if len(self.optimization_data[strategy]) > 1000:
            self.optimization_data[strategy].pop(0)
    
    def record_delivery_time(self, strategy: str, delivery_time: float):
        """Record delivery time"""
        self.delivery_times[strategy].append(delivery_time)
        
        # Keep only recent data
        if len(self.delivery_times[strategy]) > 1000:
            self.delivery_times[strategy].pop(0)
    
    def record_error(self, error_type: str):
        """Record error pattern"""
        self.error_patterns[error_type] += 1
    
    def get_optimization_stats(self) -> Dict:
        """Get optimization statistics"""
        stats = {}
        
        for strategy, data in self.optimization_data.items():
            if data:
                success_count = sum(1 for d in data if d['success'])
                total_count = len(data)
                
                stats[strategy] = {
                    'total_optimizations': total_count,
                    'success_rate': success_count / total_count,
                    'average_recipients': sum(d['recipient_count'] for d in data) / total_count,
                    'delivery_times': self.delivery_times.get(strategy, [])
                }
        
        return stats

# Global optimizer instance
email_delivery_optimizer = EmailDeliveryOptimizer()
