"""
Cache Monitor

Comprehensive monitoring system for cache infrastructure including
performance metrics, health checks, alerting, and analytics.
"""

import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
import time
import threading
import queue
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
class CacheAlert:
    """Cache alert definition"""
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
class CacheMetric:
    """Cache metric data point"""
    name: str
    value: float
    timestamp: datetime
    labels: Dict[str, str] = field(default_factory=dict)
    metric_type: MetricType = MetricType.GAUGE
    node_id: Optional[str] = None

@dataclass
class CachePerformanceStats:
    """Cache performance statistics"""
    hit_rate: float = 0.0
    miss_rate: float = 0.0
    avg_response_time: float = 0.0
    p95_response_time: float = 0.0
    p99_response_time: float = 0.0
    throughput: float = 0.0
    memory_usage: int = 0
    key_count: int = 0
    eviction_rate: float = 0.0
    connection_count: int = 0
    error_rate: float = 0.0

class CacheMonitor:
    """Comprehensive cache monitoring system"""
    
    def __init__(self, buffer_size: int = 10000):
        self.buffer_size = buffer_size
        self.metrics_buffer = deque(maxlen=buffer_size)
        self.alerts = {}
        self.alert_callbacks = []
        self.monitoring_enabled = True
        self.alerting_enabled = True
        
        # Performance tracking
        self.response_times = deque(maxlen=1000)
        self.hit_rates = deque(maxlen=100)
        self.memory_usage = deque(maxlen=100)
        self.key_counts = deque(maxlen=100)
        
        # Node-specific metrics
        self.node_metrics = defaultdict(lambda: deque(maxlen=1000))
        
        # Alert state tracking
        self.alert_state = {}
        
        # Start monitoring thread
        self._start_monitoring()
    
    def _start_monitoring(self):
        """Start background monitoring thread"""
        def monitoring_loop():
            while self.monitoring_enabled:
                try:
                    self._process_metrics()
                    self._check_alerts()
                    time.sleep(60)  # Check every minute
                except Exception as e:
                    logger.error(f"Monitoring loop error: {e}")
                    time.sleep(10)
        
        monitor_thread = threading.Thread(target=monitoring_loop, daemon=True)
        monitor_thread.start()
        logger.info("Cache monitoring started")
    
    def record_metric(self, name: str, value: float, labels: Dict[str, str] = None,
                     metric_type: MetricType = MetricType.GAUGE, node_id: str = None):
        """Record a cache metric"""
        labels = labels or {}
        metric = CacheMetric(name, value, datetime.utcnow(), labels, metric_type, node_id)
        self.metrics_buffer.append(metric)
        
        # Update performance tracking
        if name == 'response_time':
            self.response_times.append(value)
        elif name == 'hit_rate':
            self.hit_rates.append(value)
        elif name == 'memory_usage':
            self.memory_usage.append(value)
        elif name == 'key_count':
            self.key_counts.append(value)
        
        # Node-specific tracking
        if node_id:
            self.node_metrics[node_id].append(metric)
    
    def record_cache_operation(self, operation: str, hit: bool, response_time: float, 
                             node_id: str = None, key: str = None):
        """Record cache operation"""
        labels = {
            'operation': operation,
            'hit': str(hit),
            'key': key or 'unknown'
        }
        
        # Record operation metrics
        self.record_metric('cache_operation', 1, labels, MetricType.COUNTER, node_id)
        self.record_metric('response_time', response_time, labels, MetricType.TIMER, node_id)
        
        if hit:
            self.record_metric('cache_hit', 1, labels, MetricType.COUNTER, node_id)
        else:
            self.record_metric('cache_miss', 1, labels, MetricType.COUNTER, node_id)
    
    def record_node_stats(self, node_id: str, stats: Dict[str, Any]):
        """Record node-specific statistics"""
        timestamp = datetime.utcnow()
        
        # Record basic metrics
        if 'memory_usage' in stats:
            self.record_metric('memory_usage', stats['memory_usage'], {}, MetricType.GAUGE, node_id)
        
        if 'key_count' in stats:
            self.record_metric('key_count', stats['key_count'], {}, MetricType.GAUGE, node_id)
        
        if 'connected_clients' in stats:
            self.record_metric('connected_clients', stats['connected_clients'], {}, MetricType.GAUGE, node_id)
        
        if 'evicted_keys' in stats:
            self.record_metric('evicted_keys', stats['evicted_keys'], {}, MetricType.COUNTER, node_id)
        
        # Record Redis-specific metrics
        if 'info' in stats:
            info = stats['info']
            
            # Performance metrics
            if 'instantaneous_ops_per_sec' in info:
                self.record_metric('ops_per_sec', info['instantaneous_ops_per_sec'], {}, MetricType.GAUGE, node_id)
            
            if 'keyspace_hits' in info:
                self.record_metric('keyspace_hits', info['keyspace_hits'], {}, MetricType.COUNTER, node_id)
            
            if 'keyspace_misses' in info:
                self.record_metric('keyspace_misses', info['keyspace_misses'], {}, MetricType.COUNTER, node_id)
            
            # Memory metrics
            if 'used_memory' in info:
                self.record_metric('used_memory', info['used_memory'], {}, MetricType.GAUGE, node_id)
            
            if 'used_memory_rss' in info:
                self.record_metric('used_memory_rss', info['used_memory_rss'], {}, MetricType.GAUGE, node_id)
            
            # Connection metrics
            if 'connected_clients' in info:
                self.record_metric('connected_clients', info['connected_clients'], {}, MetricType.GAUGE, node_id)
            
            if 'blocked_clients' in info:
                self.record_metric('blocked_clients', info['blocked_clients'], {}, MetricType.GAUGE, node_id)
    
    def get_performance_stats(self, time_window: int = 300) -> CachePerformanceStats:
        """Get performance statistics for a time window"""
        cutoff_time = datetime.utcnow() - timedelta(seconds=time_window)
        
        # Filter metrics by time window
        recent_metrics = [
            metric for metric in self.metrics_buffer
            if metric.timestamp >= cutoff_time
        ]
        
        stats = CachePerformanceStats()
        
        # Calculate hit rate
        hits = sum(1 for m in recent_metrics if m.name == 'cache_hit')
        misses = sum(1 for m in recent_metrics if m.name == 'cache_miss')
        total = hits + misses
        stats.hit_rate = hits / total if total > 0 else 0
        stats.miss_rate = misses / total if total > 0 else 0
        
        # Calculate response time statistics
        response_times = [m.value for m in recent_metrics if m.name == 'response_time']
        if response_times:
            stats.avg_response_time = statistics.mean(response_times)
            stats.p95_response_time = sorted(response_times)[int(len(response_times) * 0.95)]
            stats.p99_response_time = sorted(response_times)[int(len(response_times) * 0.99)]
        
        # Calculate throughput
        operations = sum(1 for m in recent_metrics if m.name == 'cache_operation')
        stats.throughput = operations / time_window if time_window > 0 else 0
        
        # Get latest memory and key counts
        memory_metrics = [m for m in recent_metrics if m.name == 'memory_usage']
        if memory_metrics:
            stats.memory_usage = int(memory_metrics[-1].value)
        
        key_metrics = [m for m in recent_metrics if m.name == 'key_count']
        if key_metrics:
            stats.key_count = int(key_metrics[-1].value)
        
        # Calculate eviction rate
        evictions = sum(1 for m in recent_metrics if m.name == 'evicted_keys')
        stats.eviction_rate = evictions / time_window if time_window > 0 else 0
        
        # Get connection count
        conn_metrics = [m for m in recent_metrics if m.name == 'connected_clients']
        if conn_metrics:
            stats.connection_count = int(conn_metrics[-1].value)
        
        return stats
    
    def get_node_performance_stats(self, node_id: str, time_window: int = 300) -> Optional[CachePerformanceStats]:
        """Get performance statistics for a specific node"""
        cutoff_time = datetime.utcnow() - timedelta(seconds=time_window)
        
        # Filter node metrics by time window
        recent_metrics = [
            metric for metric in self.node_metrics[node_id]
            if metric.timestamp >= cutoff_time
        ]
        
        if not recent_metrics:
            return None
        
        stats = CachePerformanceStats()
        
        # Calculate hit rate
        hits = sum(1 for m in recent_metrics if m.name == 'cache_hit')
        misses = sum(1 for m in recent_metrics if m.name == 'cache_miss')
        total = hits + misses
        stats.hit_rate = hits / total if total > 0 else 0
        stats.miss_rate = misses / total if total > 0 else 0
        
        # Calculate response time statistics
        response_times = [m.value for m in recent_metrics if m.name == 'response_time']
        if response_times:
            stats.avg_response_time = statistics.mean(response_times)
            stats.p95_response_time = sorted(response_times)[int(len(response_times) * 0.95)]
            stats.p99_response_time = sorted(response_times)[int(len(response_times) * 0.99)]
        
        # Calculate throughput
        operations = sum(1 for m in recent_metrics if m.name == 'cache_operation')
        stats.throughput = operations / time_window if time_window > 0 else 0
        
        # Get latest metrics
        memory_metrics = [m for m in recent_metrics if m.name == 'memory_usage']
        if memory_metrics:
            stats.memory_usage = int(memory_metrics[-1].value)
        
        key_metrics = [m for m in recent_metrics if m.name == 'key_count']
        if key_metrics:
            stats.key_count = int(key_metrics[-1].value)
        
        return stats
    
    def create_alert(self, alert_id: str, name: str, level: AlertLevel,
                    condition: str, threshold: float, window: int = 300):
        """Create a new cache alert"""
        alert = CacheAlert(
            id=alert_id,
            name=name,
            level=level,
            condition=condition,
            threshold=threshold,
            window=window
        )
        
        self.alerts[alert_id] = alert
        logger.info(f"Created cache alert: {name} ({alert_id})")
    
    def _process_metrics(self):
        """Process and aggregate metrics"""
        try:
            # Calculate rolling statistics
            if len(self.response_times) > 100:
                # Keep only recent metrics
                while len(self.response_times) > 1000:
                    self.response_times.popleft()
            
            # Calculate hit rate
            if len(self.hit_rates) > 0:
                current_hit_rate = self.hit_rates[-1]
                if current_hit_rate < 0.5:
                    logger.warning(f"Low hit rate detected: {current_hit_rate:.2%}")
            
            # Check memory usage
            if len(self.memory_usage) > 0:
                current_memory = self.memory_usage[-1]
                if current_memory > 1024 * 1024 * 1024:  # 1GB
                    logger.warning(f"High memory usage: {current_memory / 1024 / 1024:.2f} MB")
            
        except Exception as e:
            logger.error(f"Error processing metrics: {e}")
    
    def _check_alerts(self):
        """Check all alerts and trigger if needed"""
        if not self.alerting_enabled:
            return
        
        for alert_id, alert in self.alerts.items():
            if not alert.enabled:
                continue
            
            # Check cooldown
            if (alert.last_triggered and 
                (datetime.utcnow() - alert.last_triggered).total_seconds() < alert.cooldown):
                continue
            
            # Evaluate alert condition
            if self._evaluate_alert_condition(alert):
                alert.last_triggered = datetime.utcnow()
                alert.trigger_count += 1
                
                # Trigger alert callbacks
                for callback in self.alert_callbacks:
                    try:
                        callback(alert)
                    except Exception as e:
                        logger.error(f"Error in alert callback: {e}")
                
                logger.warning(f"Cache alert triggered: {alert.name} ({alert.level.value})")
    
    def _evaluate_alert_condition(self, alert: CacheAlert) -> bool:
        """Evaluate alert condition"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(seconds=alert.window)
            
            if alert.condition.startswith('hit_rate'):
                # Get hit rate for time window
                recent_metrics = [
                    m for m in self.metrics_buffer
                    if (m.name == 'cache_hit' or m.name == 'cache_miss') and 
                    m.timestamp >= cutoff_time
                ]
                
                hits = sum(1 for m in recent_metrics if m.name == 'cache_hit')
                misses = sum(1 for m in recent_metrics if m.name == 'cache_miss')
                total = hits + misses
                
                if total > 0:
                    hit_rate = hits / total
                    return hit_rate < alert.threshold
            
            elif alert.condition.startswith('response_time'):
                # Get average response time
                recent_metrics = [
                    m for m in self.metrics_buffer
                    if m.name == 'response_time' and m.timestamp >= cutoff_time
                ]
                
                if recent_metrics:
                    avg_response_time = statistics.mean([m.value for m in recent_metrics])
                    return avg_response_time > alert.threshold
            
            elif alert.condition.startswith('memory_usage'):
                # Get latest memory usage
                recent_metrics = [
                    m for m in self.metrics_buffer
                    if m.name == 'memory_usage' and m.timestamp >= cutoff_time
                ]
                
                if recent_metrics:
                    memory_usage = recent_metrics[-1].value
                    return memory_usage > alert.threshold
            
            elif alert.condition.startswith('error_rate'):
                # Get error rate
                recent_metrics = [
                    m for m in self.metrics_buffer
                    if m.name == 'cache_error' and m.timestamp >= cutoff_time
                ]
                
                total_operations = sum(1 for m in self.metrics_buffer 
                                    if m.name == 'cache_operation' and m.timestamp >= cutoff_time)
                
                if total_operations > 0:
                    error_rate = len(recent_metrics) / total_operations
                    return error_rate > alert.threshold
            
            elif alert.condition.startswith('node_down'):
                # Check if any node is down
                recent_metrics = [
                    m for m in self.metrics_buffer
                    if m.name == 'node_status' and m.timestamp >= cutoff_time
                ]
                
                for metric in recent_metrics:
                    if metric.value == 0:  # 0 means down
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error evaluating alert condition: {e}")
            return False
    
    def add_alert_callback(self, callback: Callable[[CacheAlert], None]):
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
            logger.info(f"Enabled cache alert: {alert_id}")
    
    def disable_alert(self, alert_id: str):
        """Disable an alert"""
        if alert_id in self.alerts:
            self.alerts[alert_id].enabled = False
            logger.info(f"Disabled cache alert: {alert_id}")
    
    def delete_alert(self, alert_id: str):
        """Delete an alert"""
        if alert_id in self.alerts:
            del self.alerts[alert_id]
            logger.info(f"Deleted cache alert: {alert_id}")
    
    def get_metrics_summary(self, time_window: int = 300) -> Dict[str, Any]:
        """Get metrics summary for a time window"""
        cutoff_time = datetime.utcnow() - timedelta(seconds=time_window)
        
        # Filter metrics by time window
        recent_metrics = [
            metric for metric in self.metrics_buffer
            if metric.timestamp >= cutoff_time
        ]
        
        # Group metrics by name
        metrics_by_name = defaultdict(list)
        for metric in recent_metrics:
            metrics_by_name[metric.name].append(metric)
        
        # Calculate summary for each metric
        summary = {}
        for name, metrics in metrics_by_name.items():
            values = [m.value for m in metrics]
            
            if name in ['cache_hit', 'cache_miss', 'cache_operation', 'evicted_keys']:
                # Counter metrics
                summary[name] = {
                    'count': len(values),
                    'rate': len(values) / time_window if time_window > 0 else 0,
                    'type': 'counter'
                }
            else:
                # Gauge metrics
                summary[name] = {
                    'current': values[-1] if values else 0,
                    'min': min(values) if values else 0,
                    'max': max(values) if values else 0,
                    'avg': statistics.mean(values) if values else 0,
                    'type': 'gauge'
                }
        
        return {
            'time_window': time_window,
            'total_metrics': len(recent_metrics),
            'summary': summary,
            'performance': self.get_performance_stats(time_window)
        }
    
    def get_node_metrics_summary(self, node_id: str, time_window: int = 300) -> Optional[Dict[str, Any]]:
        """Get metrics summary for a specific node"""
        cutoff_time = datetime.utcnow() - timedelta(seconds=time_window)
        
        # Filter node metrics by time window
        recent_metrics = [
            metric for metric in self.node_metrics[node_id]
            if metric.timestamp >= cutoff_time
        ]
        
        if not recent_metrics:
            return None
        
        # Group metrics by name
        metrics_by_name = defaultdict(list)
        for metric in recent_metrics:
            metrics_by_name[metric.name].append(metric)
        
        # Calculate summary for each metric
        summary = {}
        for name, metrics in metrics_by_name.items():
            values = [m.value for m in metrics]
            
            if name in ['cache_hit', 'cache_miss', 'cache_operation', 'evicted_keys']:
                # Counter metrics
                summary[name] = {
                    'count': len(values),
                    'rate': len(values) / time_window if time_window > 0 else 0,
                    'type': 'counter'
                }
            else:
                # Gauge metrics
                summary[name] = {
                    'current': values[-1] if values else 0,
                    'min': min(values) if values else 0,
                    'max': max(values) if values else 0,
                    'avg': statistics.mean(values) if values else 0,
                    'type': 'gauge'
                }
        
        return {
            'node_id': node_id,
            'time_window': time_window,
            'total_metrics': len(recent_metrics),
            'summary': summary,
            'performance': self.get_node_performance_stats(node_id, time_window)
        }
    
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
                        'type': metric.metric_type.value,
                        'node_id': metric.node_id
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
        
        # Clean up node metrics
        for node_id in list(self.node_metrics.keys()):
            original_node_size = len(self.node_metrics[node_id])
            self.node_metrics[node_id] = deque(
                (metric for metric in self.node_metrics[node_id] if metric.timestamp >= cutoff_time),
                maxlen=1000
            )
        
        cleaned_count = original_size - len(self.metrics_buffer)
        logger.info(f"Cleaned up {cleaned_count} old cache metrics (older than {max_age_hours} hours)")
        
        return cleaned_count
    
    def get_monitoring_status(self) -> Dict[str, Any]:
        """Get monitoring system status"""
        return {
            'monitoring_enabled': self.monitoring_enabled,
            'alerting_enabled': self.alerting_enabled,
            'total_metrics': len(self.metrics_buffer),
            'total_alerts': len(self.alerts),
            'enabled_alerts': len([a for a in self.alerts.values() if a.enabled]),
            'buffer_size': self.buffer_size,
            'node_count': len(self.node_metrics),
            'last_update': datetime.utcnow().isoformat()
        }
    
    def shutdown(self):
        """Shutdown monitoring system"""
        try:
            # Stop monitoring
            self.monitoring_enabled = False
            self.alerting_enabled = False
            
            logger.info("Cache monitor shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during cache monitor shutdown: {e}")
