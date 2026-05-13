"""
Real-time Monitor

Comprehensive monitoring system for real-time infrastructure including
WebSocket connections, event streaming, performance metrics, and alerting.
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
import psutil

logger = logging.getLogger(__name__)

class MetricType(Enum):
    """Metric types"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"

class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class RealtimeMetric:
    """Real-time metric data point"""
    name: str
    value: float
    timestamp: datetime
    labels: Dict[str, str] = field(default_factory=dict)
    metric_type: MetricType = MetricType.GAUGE
    node_id: Optional[str] = None

@dataclass
class RealtimeAlert:
    """Real-time alert definition"""
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
class ConnectionMetrics:
    """Connection metrics"""
    total_connections: int = 0
    active_connections: int = 0
    new_connections_per_second: float = 0.0
    disconnections_per_second: float = 0.0
    avg_connection_duration: float = 0.0
    messages_per_connection: float = 0.0
    bytes_per_connection: float = 0.0
    error_rate: float = 0.0

@dataclass
class EventMetrics:
    """Event metrics"""
    total_events: int = 0
    events_per_second: float = 0.0
    processed_events: int = 0
    failed_events: int = 0
    avg_processing_time: float = 0.0
    queue_size: int = 0
    subscriptions: int = 0
    active_subscriptions: int = 0

@dataclass
class SystemMetrics:
    """System metrics"""
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    disk_usage: float = 0.0
    network_io: float = 0.0
    open_files: int = 0
    thread_count: int = 0
    process_count: int = 0

class RealtimeMonitor:
    """Comprehensive real-time monitoring system"""
    
    def __init__(self, buffer_size: int = 10000):
        self.buffer_size = buffer_size
        self.metrics_buffer = deque(maxlen=buffer_size)
        self.alerts = {}
        self.alert_callbacks = []
        self.monitoring_enabled = True
        self.alerting_enabled = True
        
        # Metrics tracking
        self.connection_metrics = ConnectionMetrics()
        self.event_metrics = EventMetrics()
        self.system_metrics = SystemMetrics()
        
        # Historical data
        self.connection_history = deque(maxlen=1000)
        self.event_history = deque(maxlen=1000)
        self.system_history = deque(maxlen=1000)
        
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
                    self._collect_system_metrics()
                    self._process_metrics()
                    self._check_alerts()
                    time.sleep(30)  # Check every 30 seconds
                except Exception as e:
                    logger.error(f"Monitoring loop error: {e}")
                    time.sleep(10)
        
        monitor_thread = threading.Thread(target=monitoring_loop, daemon=True)
        monitor_thread.start()
        logger.info("Real-time monitoring started")
    
    def record_metric(self, name: str, value: float, labels: Dict[str, str] = None,
                     metric_type: MetricType = MetricType.GAUGE, node_id: str = None):
        """Record a real-time metric"""
        labels = labels or {}
        metric = RealtimeMetric(name, value, datetime.utcnow(), labels, metric_type, node_id)
        self.metrics_buffer.append(metric)
        
        # Update specific metrics
        if name.startswith('connection_'):
            self._update_connection_metrics(name, value)
        elif name.startswith('event_'):
            self._update_event_metrics(name, value)
        elif name.startswith('system_'):
            self._update_system_metrics(name, value)
        
        # Node-specific tracking
        if node_id:
            self.node_metrics[node_id].append(metric)
    
    def _update_connection_metrics(self, name: str, value: float):
        """Update connection metrics"""
        if name == 'connection_total':
            self.connection_metrics.total_connections = int(value)
        elif name == 'connection_active':
            self.connection_metrics.active_connections = int(value)
        elif name == 'connection_new_rate':
            self.connection_metrics.new_connections_per_second = value
        elif name == 'connection_disconnect_rate':
            self.connection_metrics.disconnections_per_second = value
        elif name == 'connection_avg_duration':
            self.connection_metrics.avg_connection_duration = value
        elif name == 'connection_messages_per_connection':
            self.connection_metrics.messages_per_connection = value
        elif name == 'connection_bytes_per_connection':
            self.connection_metrics.bytes_per_connection = value
        elif name == 'connection_error_rate':
            self.connection_metrics.error_rate = value
    
    def _update_event_metrics(self, name: str, value: float):
        """Update event metrics"""
        if name == 'event_total':
            self.event_metrics.total_events = int(value)
        elif name == 'event_rate':
            self.event_metrics.events_per_second = value
        elif name == 'event_processed':
            self.event_metrics.processed_events = int(value)
        elif name == 'event_failed':
            self.event_metrics.failed_events = int(value)
        elif name == 'event_avg_processing_time':
            self.event_metrics.avg_processing_time = value
        elif name == 'event_queue_size':
            self.event_metrics.queue_size = int(value)
        elif name == 'event_subscriptions':
            self.event_metrics.subscriptions = int(value)
        elif name == 'event_active_subscriptions':
            self.event_metrics.active_subscriptions = int(value)
    
    def _update_system_metrics(self, name: str, value: float):
        """Update system metrics"""
        if name == 'system_cpu':
            self.system_metrics.cpu_usage = value
        elif name == 'system_memory':
            self.system_metrics.memory_usage = value
        elif name == 'system_disk':
            self.system_metrics.disk_usage = value
        elif name == 'system_network':
            self.system_metrics.network_io = value
        elif name == 'system_open_files':
            self.system_metrics.open_files = int(value)
        elif name == 'system_threads':
            self.system_metrics.thread_count = int(value)
        elif name == 'system_processes':
            self.system_metrics.process_count = int(value)
    
    def _collect_system_metrics(self):
        """Collect system metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            self.record_metric('system_cpu', cpu_percent, metric_type=MetricType.GAUGE)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            self.record_metric('system_memory', memory_percent, metric_type=MetricType.GAUGE)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            self.record_metric('system_disk', disk_percent, metric_type=MetricType.GAUGE)
            
            # Network I/O
            network = psutil.net_io_counters()
            network_bytes = network.bytes_sent + network.bytes_recv
            self.record_metric('system_network', network_bytes, metric_type=COUNTER)
            
            # Open files
            self.record_metric('system_open_files', len(psutil.open_files()), metric_type=GAUGE)
            
            # Thread count
            self.record_metric('system_threads', threading.active_count(), metric_type=GAUGE)
            
            # Process count
            self.record_metric('system_processes', len(psutil.pids()), metric_type=GAUGE)
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
    
    def _process_metrics(self):
        """Process and aggregate metrics"""
        try:
            # Calculate rolling statistics
            current_time = datetime.utcnow()
            
            # Update connection history
            self.connection_history.append({
                'timestamp': current_time,
                'total_connections': self.connection_metrics.total_connections,
                'active_connections': self.connection_metrics.active_connections,
                'new_connections_per_second': self.connection_metrics.new_connections_per_second,
                'disconnections_per_second': self.connection_metrics.disconnections_per_second,
                'avg_connection_duration': self.connection_metrics.avg_connection_duration,
                'messages_per_connection': self.connection_metrics.messages_per_connection,
                'bytes_per_connection': self.connection_metrics.bytes_per_connection,
                'error_rate': self.connection_metrics.error_rate
            })
            
            # Update event history
            self.event_history.append({
                'timestamp': current_time,
                'total_events': self.event_metrics.total_events,
                'events_per_second': self.event_metrics.events_per_second,
                'processed_events': self.event_metrics.processed_events,
                'failed_events': self.event_metrics.failed_events,
                'avg_processing_time': self.event_metrics.avg_processing_time,
                'queue_size': self.event_metrics.queue_size,
                'subscriptions': self.event_metrics.subscriptions,
                'active_subscriptions': self.event_metrics.active_subscriptions
            })
            
            # Update system history
            self.system_history.append({
                'timestamp': current_time,
                'cpu_usage': self.system_metrics.cpu_usage,
                'memory_usage': self.system_metrics.memory_usage,
                'disk_usage': self.system_metrics.disk_usage,
                'network_io': self.system_metrics.network_io,
                'open_files': self.system_metrics.open_files,
                'thread_count': self.system_metrics.thread_count,
                'process_count': self.system_metrics.process_count
            })
            
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
                
                logger.warning(f"Real-time alert triggered: {alert.name} ({alert.level.value})")
    
    def _evaluate_alert_condition(self, alert: RealtimeAlert) -> bool:
        """Evaluate alert condition"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(seconds=alert.window)
            
            if alert.condition.startswith('connection_active'):
                # Check active connections
                if self.connection_metrics.active_connections > alert.threshold:
                    return True
            
            elif alert.condition.startswith('connection_error_rate'):
                # Check connection error rate
                if self.connection_metrics.error_rate > alert.threshold:
                    return True
            
            elif alert.condition.startswith('event_rate'):
                # Check event rate
                if self.event_metrics.events_per_second > alert.threshold:
                    return True
            
            elif alert.condition.startswith('event_failed_rate'):
                # Check event failure rate
                if self.event_metrics.total_events > 0:
                    failed_rate = self.event_metrics.failed_events / self.event_metrics.total_events
                    if failed_rate > alert.threshold:
                        return True
            
            elif alert.condition.startswith('system_cpu'):
                # Check CPU usage
                if self.system_metrics.cpu_usage > alert.threshold:
                    return True
            
            elif alert.condition.startswith('system_memory'):
                # Check memory usage
                if self.system_metrics.memory_usage > alert.threshold:
                    return True
            
            elif alert.condition.startswith('system_disk'):
                # Check disk usage
                if self.system_metrics.disk_usage > alert.threshold:
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error evaluating alert condition: {e}")
            return False
    
    def create_alert(self, alert_id: str, name: str, level: AlertLevel,
                    condition: str, threshold: float, window: int = 300):
        """Create a new real-time alert"""
        alert = RealtimeAlert(
            id=alert_id,
            name=name,
            level=level,
            condition=condition,
            threshold=threshold,
            window=window
        )
        
        self.alerts[alert_id] = alert
        logger.info(f"Created real-time alert: {name} ({alert_id})")
    
    def add_alert_callback(self, callback: Callable[[RealtimeAlert], None]):
        """Add alert callback"""
        self.alert_callbacks.append(callback)
    
    def get_connection_metrics(self, time_window: int = 300) -> Dict[str, Any]:
        """Get connection metrics for a time window"""
        cutoff_time = datetime.utcnow() - timedelta(seconds=time_window)
        
        # Filter recent metrics
        recent_metrics = [
            metric for metric in list(self.connection_history)
            if metric['timestamp'] >= cutoff_time
        ]
        
        if not recent_metrics:
            return {}
        
        # Calculate averages
        avg_new_connections = statistics.mean([m['new_connections_per_second'] for m in recent_metrics])
        avg_disconnections = statistics.mean([m['disconnections_per_second'] for m in recent_metrics])
        avg_duration = statistics.mean([m['avg_connection_duration'] for m in recent_metrics])
        avg_messages = statistics.mean([m['messages_per_connection'] for m in recent_metrics])
        avg_bytes = statistics.mean([m['bytes_per_connection'] for m in recent_metrics])
        avg_error_rate = statistics.mean([m['error_rate'] for m in recent_metrics])
        
        return {
            'time_window': time_window,
            'total_connections': self.connection_metrics.total_connections,
            'active_connections': self.connection_metrics.active_connections,
            'new_connections_per_second': avg_new_connections,
            'disconnections_per_second': avg_disconnections,
            'avg_connection_duration': avg_duration,
            'messages_per_connection': avg_messages,
            'bytes_per_connection': avg_bytes,
            'error_rate': avg_error_rate
        }
    
    def get_event_metrics(self, time_window: int = 300) -> Dict[str, Any]:
        """Get event metrics for a time window"""
        cutoff_time = datetime.utcnow() - timedelta(seconds=time_window)
        
        # Filter recent metrics
        recent_metrics = [
            metric for metric in list(self.event_history)
            if metric['timestamp'] >= cutoff_time
        ]
        
        if not recent_metrics:
            return {}
        
        # Calculate averages
        avg_event_rate = statistics.mean([m['events_per_second'] for m in recent_metrics])
        avg_processing_time = statistics.mean([m['avg_processing_time'] for m in recent_metrics])
        avg_queue_size = statistics.mean([m['queue_size'] for m in recent_metrics])
        
        return {
            'time_window': time_window,
            'total_events': self.event_metrics.total_events,
            'events_per_second': avg_event_rate,
            'processed_events': self.event_metrics.processed_events,
            'failed_events': self.event_metrics.failed_events,
            'avg_processing_time': avg_processing_time,
            'queue_size': avg_queue_size,
            'subscriptions': self.event_metrics.subscriptions,
            'active_subscriptions': self.event_metrics.active_subscriptions
        }
    
    def get_system_metrics(self, time_window: int = 300) -> Dict[str, Any]:
        """Get system metrics for a time window"""
        cutoff_time = datetime.utcnow() - timedelta(seconds=time_window)
        
        # Filter recent metrics
        recent_metrics = [
            metric for metric in list(self.system_history)
            if metric['timestamp'] >= cutoff_time
        ]
        
        if not recent_metrics:
            return {}
        
        # Calculate averages
        avg_cpu = statistics.mean([m['cpu_usage'] for m in recent_metrics])
        avg_memory = statistics.mean([m['memory_usage'] for m in recent_metrics])
        avg_disk = statistics.mean([m['disk_usage'] for m in recent_metrics])
        avg_network = statistics.mean([m['network_io'] for m in recent_metrics])
        avg_open_files = statistics.mean([m['open_files'] for m in recent_metrics])
        avg_threads = statistics.mean([m['thread_count'] for m in recent_metrics])
        avg_processes = statistics.mean([m['process_count'] for m in recent_metrics])
        
        return {
            'time_window': time_window,
            'cpu_usage': avg_cpu,
            'memory_usage': avg_memory,
            'disk_usage': avg_disk,
            'network_io': avg_network,
            'open_files': avg_open_files,
            'thread_count': avg_threads,
            'process_count': avg_processes
        }
    
    def get_comprehensive_metrics(self, time_window: int = 300) -> Dict[str, Any]:
        """Get comprehensive metrics for all components"""
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'time_window': time_window,
            'connection_metrics': self.get_connection_metrics(time_window),
            'event_metrics': self.get_event_metrics(time_window),
            'system_metrics': self.get_system_metrics(time_window),
            'alerts': {
                'total': len(self.alerts),
                'enabled': len([a for a in self.alerts.values() if a.enabled]),
                'triggered': len([a for a in self.alerts.values() if a.last_triggered])
            }
        }
    
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
            logger.info(f"Enabled real-time alert: {alert_id}")
    
    def disable_alert(self, alert_id: str):
        """Disable an alert"""
        if alert_id in self.alerts:
            self.alerts[alert_id].enabled = False
            logger.info(f"Disabled real-time alert: {alert_id}")
    
    def delete_alert(self, alert_id: str):
        """Delete an alert"""
        if alert_id in self.alerts:
            del self.alerts[alert_id]
            logger.info(f"Deleted real-time alert: {alert_id}")
    
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
            
            if name in ['connection_total', 'connection_active', 'event_total', 'event_processed']:
                # Counter metrics
                summary[name] = {
                    'current': values[-1] if values else 0,
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
            'summary': summary
        }
    
    def export_metrics(self, format: str = 'json') -> str:
        """Export metrics in specified format"""
        if format == 'json':
            return json.dumps({
                'timestamp': datetime.utcnow().isoformat(),
                'connection_metrics': self.connection_metrics.__dict__,
                'event_metrics': self.event_metrics.__dict__,
                'system_metrics': self.system_metrics.__dict__,
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
        
        # Clean up history
        cleaned_connection = len(self.connection_history)
        self.connection_history = deque(
            (metric for metric in self.connection_history if metric['timestamp'] >= cutoff_time),
            maxlen=1000
        )
        
        cleaned_event = len(self.event_history)
        self.event_history = deque(
            (metric for metric in self.event_history if metric['timestamp'] >= cutoff_time),
            maxlen=1000
        )
        
        cleaned_system = len(self.system_history)
        self.system_history = deque(
            (metric for metric in self.system_history if metric['timestamp'] >= cutoff_time),
            maxlen=1000
        )
        
        cleaned_count = original_size - len(self.metrics_buffer)
        logger.info(f"Cleaned up {cleaned_count} old real-time metrics (older than {max_age_hours} hours)")
        
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
            
            logger.info("Real-time monitor shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during real-time monitor shutdown: {e}")
