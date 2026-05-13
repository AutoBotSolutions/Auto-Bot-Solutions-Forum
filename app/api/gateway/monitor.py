"""
Gateway Monitor

Comprehensive monitoring and analytics for API gateway including
performance metrics, health monitoring, and alerting.
"""

import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
import time
import statistics
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class MetricType(Enum):
    """Metric types"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"

@dataclass
class Alert:
    """Alert definition"""
    id: str
    name: str
    level: AlertLevel
    condition: str
    threshold: float
    window: int
    enabled: bool = True
    last_triggered: Optional[datetime] = None
    trigger_count: int = 0
    cooldown: int = 300  # 5 minutes cooldown

@dataclass
class Metric:
    """Metric data point"""
    name: str
    value: float
    timestamp: datetime
    labels: Dict[str, str] = field(default_factory=dict)
    metric_type: MetricType = MetricType.GAUGE

class GatewayMonitor:
    """Comprehensive gateway monitoring system"""
    
    def __init__(self, buffer_size: int = 10000):
        self.buffer_size = buffer_size
        self.metrics_buffer = deque(maxlen=buffer_size)
        self.counters = defaultdict(int)
        self.gauges = defaultdict(float)
        self.histograms = defaultdict(list)
        self.timers = defaultdict(list)
        self.alerts = {}
        self.alert_callbacks = []
        self.health_checks = {}
        self.performance_metrics = {
            'response_times': deque(maxlen=1000),
            'error_rates': deque(maxlen=1000),
            'throughput': deque(maxlen=1000),
            'latency_p50': deque(maxlen=100),
            'latency_p95': deque(maxlen=100),
            'latency_p99': deque(maxlen=100)
        }
        self.start_time = datetime.utcnow()
        
    def record_metric(self, name: str, value: float, labels: Dict[str, str] = None,
                      metric_type: MetricType = MetricType.GAUGE):
        """Record a metric"""
        labels = labels or {}
        metric = Metric(name, value, datetime.utcnow(), labels, metric_type)
        self.metrics_buffer.append(metric)
        
        # Update metric-specific storage
        if metric_type == MetricType.COUNTER:
            self.counters[name] += value
        elif metric_type == MetricType.GAUGE:
            self.gauges[name] = value
        elif metric_type == MetricType.HISTOGRAM:
            self.histograms[name].append(value)
            # Keep only recent values
            if len(self.histograms[name]) > 1000:
                self.histograms[name] = self.histograms[name][-1000:]
        elif metric_type == MetricType.TIMER:
            self.timers[name].append(value)
            # Keep only recent values
            if len(self.timers[name]) > 1000:
                self.timers[name] = self.timers[name][-1000:]
    
    def record_request(self, response_time: float, status_code: int, 
                      endpoint: str = None, service_name: str = None):
        """Record request metrics"""
        labels = {}
        if endpoint:
            labels['endpoint'] = endpoint
        if service_name:
            labels['service_name'] = service_name
        
        # Record response time
        self.record_metric('request_duration', response_time, labels, MetricType.TIMER)
        
        # Record request count
        self.record_metric('request_count', 1, labels, MetricType.COUNTER)
        
        # Record status code
        status_labels = labels.copy()
        status_labels['status_code'] = str(status_code)
        self.record_metric('request_status', 1, status_labels, MetricType.COUNTER)
        
        # Update performance metrics
        self.performance_metrics['response_times'].append(response_time)
        
        # Calculate error rate
        is_error = status_code >= 400
        recent_response_times = list(self.performance_metrics['response_times'])[-100:]
        
        if len(recent_response_times) > 0:
            error_count = sum(1 for _ in recent_response_times if is_error)
            error_rate = error_count / len(recent_response_times)
        else:
            error_rate = 0.0
        
        self.performance_metrics['error_rates'].append(error_rate)
        
        # Calculate throughput (requests per second)
        current_time = time.time()
        recent_requests = [
            rt for rt in list(self.performance_metrics['response_times'])[-100:]
            if current_time - rt <= 60  # Last 60 seconds
        ]
        throughput = len(recent_requests) / 60
        self.performance_metrics['throughput'].append(throughput)
        
        # Update latency percentiles
        if len(self.performance_metrics['response_times']) >= 10:
            response_times_list = list(self.performance_metrics['response_times'])
            self.performance_metrics['latency_p50'].append(statistics.median(response_times_list))
            self.performance_metrics['latency_p95'].append(
                sorted(response_times_list)[int(len(response_times_list) * 0.95)]
            )
            self.performance_metrics['latency_p99'].append(
                sorted(response_times_list)[int(len(response_times_list) * 0.99)]
            )
    
    def record_service_health(self, service_name: str, healthy: bool, 
                            response_time: float = None):
        """Record service health check"""
        labels = {'service_name': service_name}
        
        # Record health status
        self.record_metric('service_health', 1 if healthy else 0, labels, MetricType.GAUGE)
        
        # Record response time if provided
        if response_time is not None:
            self.record_metric('service_response_time', response_time, labels, MetricType.TIMER)
    
    def get_metrics_summary(self, time_window: int = 300) -> Dict[str, Any]:
        """Get metrics summary for a time window"""
        cutoff_time = datetime.utcnow() - timedelta(seconds=time_window)
        
        # Filter metrics by time window
        recent_metrics = [
            metric for metric in self.metrics_buffer
            if metric.timestamp >= cutoff_time
        ]
        
        # Calculate summary statistics
        summary = {
            'time_window': time_window,
            'total_metrics': len(recent_metrics),
            'counters': {},
            'gauges': {},
            'histograms': {},
            'timers': {},
            'performance': self._get_performance_summary(time_window)
        }
        
        # Summarize counters
        for name, value in self.counters.items():
            counter_metrics = [m for m in recent_metrics if m.name == name]
            if counter_metrics:
                summary['counters'][name] = {
                    'total': value,
                    'rate': len(counter_metrics) / time_window
                }
        
        # Summarize gauges
        for name, value in self.gauges.items():
            gauge_metrics = [m for m in recent_metrics if m.name == name]
            if gauge_metrics:
                values = [m.value for m in gauge_metrics]
                summary['gauges'][name] = {
                    'current': value,
                    'min': min(values),
                    'max': max(values),
                    'avg': statistics.mean(values)
                }
        
        # Summarize histograms
        for name, values in self.histograms.items():
            if values:
                summary['histograms'][name] = {
                    'count': len(values),
                    'min': min(values),
                    'max': max(values),
                    'avg': statistics.mean(values),
                    'p50': statistics.median(values),
                    'p95': sorted(values)[int(len(values) * 0.95)],
                    'p99': sorted(values)[int(len(values) * 0.99)]
                }
        
        # Summarize timers
        for name, values in self.timers.items():
            if values:
                summary['timers'][name] = {
                    'count': len(values),
                    'min': min(values),
                    'max': max(values),
                    'avg': statistics.mean(values),
                    'p50': statistics.median(values),
                    'p95': sorted(values)[int(len(values) * 0.95)],
                    'p99': sorted(values)[int(len(values) * 0.99)]
                }
        
        return summary
    
    def _get_performance_summary(self, time_window: int) -> Dict[str, Any]:
        """Get performance metrics summary"""
        cutoff_time = datetime.utcnow() - timedelta(seconds=time_window)
        
        summary = {}
        
        for metric_name, values in self.performance_metrics.items():
            if not values:
                summary[metric_name] = {
                    'current': 0,
                    'min': 0,
                    'max': 0,
                    'avg': 0
                }
                continue
            
            # Filter by time window (simplified - using recent values)
            recent_values = list(values)[-100:] if len(values) > 100 else list(values)
            
            if recent_values:
                summary[metric_name] = {
                    'current': recent_values[-1],
                    'min': min(recent_values),
                    'max': max(recent_values),
                    'avg': statistics.mean(recent_values)
                }
        
        return summary
    
    def create_alert(self, alert_id: str, name: str, level: AlertLevel,
                    condition: str, threshold: float, window: int = 300):
        """Create a new alert"""
        alert = Alert(
            id=alert_id,
            name=name,
            level=level,
            condition=condition,
            threshold=threshold,
            window=window
        )
        
        self.alerts[alert_id] = alert
        logger.info(f"Created alert: {name} ({alert_id})")
    
    def check_alerts(self) -> List[Alert]:
        """Check all alerts and return triggered ones"""
        triggered_alerts = []
        current_time = datetime.utcnow()
        
        for alert_id, alert in self.alerts.items():
            if not alert.enabled:
                continue
            
            # Check cooldown
            if (alert.last_triggered and 
                (current_time - alert.last_triggered).total_seconds() < alert.cooldown):
                continue
            
            # Evaluate alert condition
            if self._evaluate_alert_condition(alert):
                alert.last_triggered = current_time
                alert.trigger_count += 1
                triggered_alerts.append(alert)
                
                # Trigger alert callbacks
                for callback in self.alert_callbacks:
                    try:
                        callback(alert)
                    except Exception as e:
                        logger.error(f"Error in alert callback: {e}")
        
        return triggered_alerts
    
    def _evaluate_alert_condition(self, alert: Alert) -> bool:
        """Evaluate alert condition"""
        try:
            # Parse condition (simplified)
            if alert.condition.startswith('avg_response_time'):
                avg_response_time = self._get_avg_response_time(alert.window)
                return avg_response_time > alert.threshold
            elif alert.condition.startswith('error_rate'):
                error_rate = self._get_error_rate(alert.window)
                return error_rate > alert.threshold
            elif alert.condition.startswith('throughput'):
                throughput = self._get_throughput(alert.window)
                return throughput < alert.threshold
            elif alert.condition.startswith('service_health'):
                service_name = alert.condition.split(':')[1]
                health = self._get_service_health(service_name)
                return health < alert.threshold
            else:
                logger.warning(f"Unknown alert condition: {alert.condition}")
                return False
        except Exception as e:
            logger.error(f"Error evaluating alert condition: {e}")
            return False
    
    def _get_avg_response_time(self, window: int) -> float:
        """Get average response time for time window"""
        cutoff_time = datetime.utcnow() - timedelta(seconds=window)
        recent_metrics = [
            metric for metric in self.metrics_buffer
            if (metric.name == 'request_duration' and 
                metric.timestamp >= cutoff_time)
        ]
        
        if not recent_metrics:
            return 0.0
        
        return statistics.mean([m.value for m in recent_metrics])
    
    def _get_error_rate(self, window: int) -> float:
        """Get error rate for time window"""
        cutoff_time = datetime.utcnow() - timedelta(seconds=window)
        
        # Get total requests
        total_requests = len([
            metric for metric in self.metrics_buffer
            if (metric.name == 'request_count' and 
                metric.timestamp >= cutoff_time)
        ])
        
        if total_requests == 0:
            return 0.0
        
        # Get error requests
        error_requests = len([
            metric for metric in self.metrics_buffer
            if (metric.name == 'request_status' and 
                metric.labels.get('status_code', '').startswith('4') or
                metric.labels.get('status_code', '').startswith('5') and
                metric.timestamp >= cutoff_time)
        ])
        
        return error_requests / total_requests
    
    def _get_throughput(self, window: int) -> float:
        """Get throughput for time window"""
        cutoff_time = datetime.utcnow() - timedelta(seconds=window)
        
        requests = len([
            metric for metric in self.metrics_buffer
            if (metric.name == 'request_count' and 
                metric.timestamp >= cutoff_time)
        ])
        
        return requests / window
    
    def _get_service_health(self, service_name: str) -> float:
        """Get service health (0-1 scale)"""
        service_metrics = [
            metric for metric in self.metrics_buffer
            if (metric.name == 'service_health' and 
                metric.labels.get('service_name') == service_name)
        ]
        
        if not service_metrics:
            return 0.0
        
        # Return the most recent health value
        return service_metrics[-1].value
    
    def add_alert_callback(self, callback: Callable[[Alert], None]):
        """Add alert callback"""
        self.alert_callbacks.append(callback)
    
    def get_alerts(self) -> List[Dict[str, Any]]:
        """Get all alerts"""
        return [
            {
                'id': alert.id,
                'name': alert.name,
                'level': alert.level.value,
                'condition': alert.condition,
                'threshold': alert.threshold,
                'window': alert.window,
                'enabled': alert.enabled,
                'last_triggered': alert.last_triggered.isoformat() if alert.last_triggered else None,
                'trigger_count': alert.trigger_count
            }
            for alert in self.alerts.values()
        ]
    
    def enable_alert(self, alert_id: str):
        """Enable an alert"""
        if alert_id in self.alerts:
            self.alerts[alert_id].enabled = True
            logger.info(f"Enabled alert: {alert_id}")
    
    def disable_alert(self, alert_id: str):
        """Disable an alert"""
        if alert_id in self.alerts:
            self.alerts[alert_id].enabled = False
            logger.info(f"Disabled alert: {alert_id}")
    
    def delete_alert(self, alert_id: str):
        """Delete an alert"""
        if alert_id in self.alerts:
            del self.alerts[alert_id]
            logger.info(f"Deleted alert: {alert_id}")
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get overall gateway health status"""
        current_time = datetime.utcnow()
        uptime = (current_time - self.start_time).total_seconds()
        
        # Get recent metrics
        recent_metrics = [
            metric for metric in self.metrics_buffer
            if metric.timestamp >= current_time - timedelta(minutes=5)
        ]
        
        # Calculate health indicators
        avg_response_time = self._get_avg_response_time(300)
        error_rate = self._get_error_rate(300)
        throughput = self._get_throughput(300)
        
        # Determine overall health
        health_score = 100
        health_issues = []
        
        if avg_response_time > 1.0:
            health_score -= 20
            health_issues.append("High response time")
        
        if error_rate > 0.05:
            health_score -= 30
            health_issues.append("High error rate")
        
        if throughput < 10:
            health_score -= 10
            health_issues.append("Low throughput")
        
        health_status = "healthy"
        if health_score < 70:
            health_status = "degraded"
        if health_score < 50:
            health_status = "unhealthy"
        
        return {
            'status': health_status,
            'score': health_score,
            'uptime_seconds': uptime,
            'issues': health_issues,
            'metrics': {
                'avg_response_time': avg_response_time,
                'error_rate': error_rate,
                'throughput': throughput,
                'total_requests': len(recent_metrics)
            },
            'timestamp': current_time.isoformat()
        }
    
    def get_service_health_details(self) -> Dict[str, Any]:
        """Get detailed health information for all services"""
        service_health = {}
        
        # Group metrics by service
        service_metrics = defaultdict(list)
        for metric in self.metrics_buffer:
            service_name = metric.labels.get('service_name')
            if service_name:
                service_metrics[service_name].append(metric)
        
        # Calculate health for each service
        for service_name, metrics in service_metrics.items():
            # Get service-specific metrics
            response_times = [
                m.value for m in metrics 
                if m.name == 'service_response_time'
            ]
            health_values = [
                m.value for m in metrics 
                if m.name == 'service_health'
            ]
            
            service_health[service_name] = {
                'healthy': any(health_values) and all(health_values),
                'avg_response_time': statistics.mean(response_times) if response_times else 0,
                'last_health_check': max(
                    (m.timestamp for m in metrics if m.name == 'service_health'),
                    default=datetime.utcnow()
                ).isoformat(),
                'total_requests': len([
                    m for m in metrics if m.name == 'request_count'
                ])
            }
        
        return service_health
    
    def export_metrics(self, format: str = 'json') -> str:
        """Export metrics in specified format"""
        if format == 'json':
            return json.dumps({
                'timestamp': datetime.utcnow().isoformat(),
                'metrics': [
                    {
                        'name': metric.name,
                        'value': metric.value,
                        'timestamp': metric.timestamp.isoformat(),
                        'labels': metric.labels,
                        'type': metric.metric_type.value
                    }
                    for metric in list(self.metrics_buffer)[-1000:]  # Last 1000 metrics
                ]
            }, indent=2)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def cleanup_old_metrics(self, max_age_hours: int = 24):
        """Clean up old metrics data"""
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        
        # Remove old metrics from buffer
        original_size = len(self.metrics_buffer)
        self.metrics_buffer = deque(
            (metric for metric in self.metrics_buffer if metric.timestamp >= cutoff_time),
            maxlen=self.buffer_size
        )
        
        cleaned_count = original_size - len(self.metrics_buffer)
        logger.info(f"Cleaned up {cleaned_count} old metrics (older than {max_age_hours} hours)")
        
        return cleaned_count
