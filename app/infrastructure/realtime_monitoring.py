"""
Real-time Infrastructure Monitoring and Load Balancing

This module provides comprehensive real-time monitoring for the notification system:
- WebSocket server monitoring
- Load balancing across multiple instances
- Performance metrics collection
- Health checks and failover
- Auto-scaling recommendations
- Real-time alerting
"""

import time
import json
import logging
import threading
import asyncio
import psutil
import socket
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import redis
import requests
from flask import current_app

from app.config.notification_config import get_notification_config

logger = logging.getLogger(__name__)

@dataclass
class ServerMetrics:
    """Server performance metrics"""
    server_id: str
    cpu_usage: float
    memory_usage: float
    active_connections: int
    message_rate: float
    error_rate: float
    response_time: float
    uptime: float
    last_updated: datetime
    health_status: str

@dataclass
class LoadBalancerConfig:
    """Load balancer configuration"""
    algorithm: str  # round_robin, least_connections, weighted
    health_check_interval: int
    max_connections_per_server: int
    failover_timeout: int
    sticky_sessions: bool

class RealtimeMonitor:
    """Real-time infrastructure monitoring system"""
    
    def __init__(self):
        self.config = get_notification_config()
        self.redis_client = None
        self.monitoring_active = False
        self.monitor_thread = None
        
        # Server identification
        self.server_id = self._get_server_id()
        self.server_metrics = ServerMetrics(
            server_id=self.server_id,
            cpu_usage=0.0,
            memory_usage=0.0,
            active_connections=0,
            message_rate=0.0,
            error_rate=0.0,
            response_time=0.0,
            uptime=0.0,
            last_updated=datetime.utcnow(),
            health_status='unknown'
        )
        
        # Load balancing
        self.load_balancer = LoadBalancer()
        self.lb_config = LoadBalancerConfig(
            algorithm='least_connections',
            health_check_interval=30,
            max_connections_per_server=1000,
            failover_timeout=60,
            sticky_sessions=False
        )
        
        # Metrics storage
        self.metrics_history = deque(maxlen=1440)  # 24 hours of data
        self.alert_history = deque(maxlen=100)
        
        # Performance tracking
        self.connection_times = deque(maxlen=1000)
        self.message_counts = defaultdict(int)
        self.error_counts = defaultdict(int)
        
        # Health thresholds
        self.thresholds = {
            'cpu_warning': 70.0,
            'cpu_critical': 90.0,
            'memory_warning': 80.0,
            'memory_critical': 95.0,
            'connections_warning': 800,
            'connections_critical': 950,
            'error_rate_warning': 0.05,
            'error_rate_critical': 0.10,
            'response_time_warning': 1.0,
            'response_time_critical': 2.0
        }
        
        self._setup_redis()
        self._start_monitoring()
    
    def _get_server_id(self) -> str:
        """Generate unique server identifier"""
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
        timestamp = int(time.time())
        return f"server_{hostname}_{ip_address}_{timestamp}"
    
    def _setup_redis(self):
        """Setup Redis connection for distributed monitoring"""
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
            logger.info("Redis connection established for real-time monitoring")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
    
    def _start_monitoring(self):
        """Start real-time monitoring"""
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True
        )
        self.monitor_thread.start()
        
        # Start load balancer
        self.load_balancer.start()
        
        logger.info(f"Real-time monitoring started for server {self.server_id}")
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                # Collect server metrics
                self._collect_server_metrics()
                
                # Update health status
                self._update_health_status()
                
                # Check for alerts
                self._check_alerts()
                
                # Update load balancer
                self._update_load_balancer()
                
                # Store metrics
                self._store_metrics()
                
                # Cleanup old data
                self._cleanup_old_data()
                
                time.sleep(30)  # Monitor every 30 seconds
                
            except Exception as e:
                logger.error(f"Real-time monitoring error: {str(e)}")
                time.sleep(10)
    
    def _collect_server_metrics(self):
        """Collect current server performance metrics"""
        try:
            # CPU usage
            cpu_usage = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            
            # Active connections (WebSocket)
            active_connections = self._get_active_connections()
            
            # Message rate (messages per second)
            message_rate = self._calculate_message_rate()
            
            # Error rate
            error_rate = self._calculate_error_rate()
            
            # Response time
            response_time = self._calculate_average_response_time()
            
            # Uptime
            uptime = time.time() - self._get_start_time()
            
            # Update server metrics
            self.server_metrics = ServerMetrics(
                server_id=self.server_id,
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                active_connections=active_connections,
                message_rate=message_rate,
                error_rate=error_rate,
                response_time=response_time,
                uptime=uptime,
                last_updated=datetime.utcnow(),
                health_status=self.server_metrics.health_status
            )
            
        except Exception as e:
            logger.error(f"Error collecting server metrics: {str(e)}")
    
    def _get_active_connections(self) -> int:
        """Get active WebSocket connections"""
        try:
            if hasattr(current_app, 'extensions') and 'socketio' in current_app.extensions:
                socketio = current_app.extensions['socketio']
                # Get connection count from Socket.IO
                return len(getattr(socketio, 'rooms', {}))
            return 0
        except Exception as e:
            logger.error(f"Error getting active connections: {str(e)}")
            return 0
    
    def _calculate_message_rate(self) -> float:
        """Calculate messages per second"""
        try:
            current_time = time.time()
            one_minute_ago = current_time - 60
            
            recent_messages = 0
            for timestamp in self.message_counts:
                if timestamp >= one_minute_ago:
                    recent_messages += self.message_counts[timestamp]
            
            return recent_messages / 60.0
            
        except Exception as e:
            logger.error(f"Error calculating message rate: {str(e)}")
            return 0.0
    
    def _calculate_error_rate(self) -> float:
        """Calculate error rate"""
        try:
            current_time = time.time()
            one_minute_ago = current_time - 60
            
            total_messages = 0
            total_errors = 0
            
            for timestamp in self.message_counts:
                if timestamp >= one_minute_ago:
                    total_messages += self.message_counts[timestamp]
                    total_errors += self.error_counts.get(timestamp, 0)
            
            return total_errors / max(total_messages, 1)
            
        except Exception as e:
            logger.error(f"Error calculating error rate: {str(e)}")
            return 0.0
    
    def _calculate_average_response_time(self) -> float:
        """Calculate average response time"""
        try:
            if self.connection_times:
                return sum(self.connection_times) / len(self.connection_times)
            return 0.0
        except Exception as e:
            logger.error(f"Error calculating average response time: {str(e)}")
            return 0.0
    
    def _get_start_time(self) -> float:
        """Get application start time"""
        try:
            return psutil.boot_time()
        except:
            return time.time()
    
    def _update_health_status(self):
        """Update server health status"""
        try:
            alerts = []
            status = 'healthy'
            
            # Check CPU usage
            if self.server_metrics.cpu_usage > self.thresholds['cpu_critical']:
                status = 'critical'
                alerts.append(f"Critical CPU usage: {self.server_metrics.cpu_usage:.1f}%")
            elif self.server_metrics.cpu_usage > self.thresholds['cpu_warning']:
                status = 'warning'
                alerts.append(f"High CPU usage: {self.server_metrics.cpu_usage:.1f}%")
            
            # Check memory usage
            if self.server_metrics.memory_usage > self.thresholds['memory_critical']:
                status = 'critical'
                alerts.append(f"Critical memory usage: {self.server_metrics.memory_usage:.1f}%")
            elif self.server_metrics.memory_usage > self.thresholds['memory_warning']:
                status = 'warning'
                alerts.append(f"High memory usage: {self.server_metrics.memory_usage:.1f}%")
            
            # Check connections
            if self.server_metrics.active_connections > self.thresholds['connections_critical']:
                status = 'critical'
                alerts.append(f"Critical connection count: {self.server_metrics.active_connections}")
            elif self.server_metrics.active_connections > self.thresholds['connections_warning']:
                status = 'warning'
                alerts.append(f"High connection count: {self.server_metrics.active_connections}")
            
            # Check error rate
            if self.server_metrics.error_rate > self.thresholds['error_rate_critical']:
                status = 'critical'
                alerts.append(f"Critical error rate: {self.server_metrics.error_rate:.2%}")
            elif self.server_metrics.error_rate > self.thresholds['error_rate_warning']:
                status = 'warning'
                alerts.append(f"High error rate: {self.server_metrics.error_rate:.2%}")
            
            # Check response time
            if self.server_metrics.response_time > self.thresholds['response_time_critical']:
                status = 'critical'
                alerts.append(f"Critical response time: {self.server_metrics.response_time:.2f}s")
            elif self.server_metrics.response_time > self.thresholds['response_time_warning']:
                status = 'warning'
                alerts.append(f"High response time: {self.server_metrics.response_time:.2f}s")
            
            # Update health status
            self.server_metrics.health_status = status
            
            # Send alerts if needed
            if status in ['warning', 'critical']:
                self._send_alert(status, alerts)
            
        except Exception as e:
            logger.error(f"Error updating health status: {str(e)}")
    
    def _check_alerts(self):
        """Check for performance alerts and thresholds"""
        try:
            # Auto-scaling recommendations
            if self.server_metrics.active_connections > self.thresholds['connections_warning']:
                self._recommend_scaling('scale_up', 'High connection count')
            
            if (self.server_metrics.cpu_usage > self.thresholds['cpu_warning'] or 
                self.server_metrics.memory_usage > self.thresholds['memory_warning']):
                self._recommend_scaling('scale_up', 'High resource usage')
            
            # Load balancing recommendations
            if self.server_metrics.response_time > self.thresholds['response_time_warning']:
                self._recommend_load_balancing('redistribute', 'High response time')
            
        except Exception as e:
            logger.error(f"Error checking alerts: {str(e)}")
    
    def _send_alert(self, severity: str, messages: List[str]):
        """Send monitoring alert"""
        try:
            alert_data = {
                'server_id': self.server_id,
                'severity': severity,
                'messages': messages,
                'metrics': asdict(self.server_metrics),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Store alert in Redis
            if self.redis_client:
                self.redis_client.lpush('infrastructure_alerts', json.dumps(alert_data))
                self.redis_client.ltrim('infrastructure_alerts', 0, 99)  # Keep last 100
            
            # Add to local history
            self.alert_history.append(alert_data)
            
            # Log alert
            logger.warning(f"Infrastructure alert [{severity.upper()}]: {', '.join(messages)}")
            
        except Exception as e:
            logger.error(f"Error sending alert: {str(e)}")
    
    def _recommend_scaling(self, action: str, reason: str):
        """Recommend auto-scaling action"""
        try:
            recommendation = {
                'action': action,
                'reason': reason,
                'server_id': self.server_id,
                'metrics': {
                    'cpu': self.server_metrics.cpu_usage,
                    'memory': self.server_metrics.memory_usage,
                    'connections': self.server_metrics.active_connections
                },
                'timestamp': datetime.utcnow().isoformat()
            }
            
            if self.redis_client:
                self.redis_client.lpush('scaling_recommendations', json.dumps(recommendation))
                self.redis_client.ltrim('scaling_recommendations', 0, 49)  # Keep last 50
            
            logger.info(f"Scaling recommendation: {action} - {reason}")
            
        except Exception as e:
            logger.error(f"Error recommending scaling: {str(e)}")
    
    def _recommend_load_balancing(self, action: str, reason: str):
        """Recommend load balancing action"""
        try:
            recommendation = {
                'action': action,
                'reason': reason,
                'server_id': self.server_id,
                'metrics': {
                    'connections': self.server_metrics.active_connections,
                    'response_time': self.server_metrics.response_time
                },
                'timestamp': datetime.utcnow().isoformat()
            }
            
            if self.redis_client:
                self.redis_client.lpush('load_balancing_recommendations', json.dumps(recommendation))
                self.redis_client.ltrim('load_balancing_recommendations', 0, 49)  # Keep last 50
            
            logger.info(f"Load balancing recommendation: {action} - {reason}")
            
        except Exception as e:
            logger.error(f"Error recommending load balancing: {str(e)}")
    
    def _update_load_balancer(self):
        """Update load balancer with current metrics"""
        try:
            self.load_balancer.update_server_metrics(self.server_id, self.server_metrics)
        except Exception as e:
            logger.error(f"Error updating load balancer: {str(e)}")
    
    def _store_metrics(self):
        """Store metrics in Redis and local history"""
        try:
            # Store in local history
            self.metrics_history.append(asdict(self.server_metrics))
            
            # Store in Redis for distributed access
            if self.redis_client:
                metrics_key = f"server_metrics:{self.server_id}:{int(time.time())}"
                self.redis_client.setex(
                    metrics_key,
                    3600,  # 1 hour expiration
                    json.dumps(asdict(self.server_metrics))
                )
                
                # Update server registry
                self.redis_client.hset(
                    'server_registry',
                    self.server_id,
                    json.dumps({
                        'last_seen': datetime.utcnow().isoformat(),
                        'health_status': self.server_metrics.health_status,
                        'active_connections': self.server_metrics.active_connections
                    })
                )
            
        except Exception as e:
            logger.error(f"Error storing metrics: {str(e)}")
    
    def _cleanup_old_data(self):
        """Clean up old monitoring data"""
        try:
            if not self.redis_client:
                return
            
            # Clean up old metrics (keep 24 hours)
            cutoff_time = time.time() - (24 * 3600)
            
            for key in self.redis_client.scan_iter(match="server_metrics:*"):
                timestamp = int(key.split(':')[-1])
                if timestamp < cutoff_time:
                    self.redis_client.delete(key)
            
            # Clean up old server registry entries (remove inactive servers)
            inactive_cutoff = time.time() - 300  # 5 minutes
            server_registry = self.redis_client.hgetall('server_registry')
            
            for server_id, server_data in server_registry.items():
                data = json.loads(server_data)
                last_seen = datetime.fromisoformat(data['last_seen']).timestamp()
                
                if last_seen < inactive_cutoff:
                    self.redis_client.hdel('server_registry', server_id)
                    self.load_balancer.remove_server(server_id)
                    logger.info(f"Removed inactive server: {server_id}")
            
        except Exception as e:
            logger.error(f"Error cleaning up old data: {str(e)}")
    
    def record_message(self, message_type: str, success: bool = True, response_time: float = 0.0):
        """Record message for metrics calculation"""
        try:
            current_time = int(time.time())
            
            # Record message count
            self.message_counts[current_time] += 1
            
            # Record error if unsuccessful
            if not success:
                self.error_counts[current_time] += 1
            
            # Record response time
            if response_time > 0:
                self.connection_times.append(response_time)
            
            # Cleanup old entries
            cutoff_time = current_time - 300  # 5 minutes
            old_timestamps = [t for t in self.message_counts if t < cutoff_time]
            for timestamp in old_timestamps:
                self.message_counts.pop(timestamp, None)
                self.error_counts.pop(timestamp, None)
            
        except Exception as e:
            logger.error(f"Error recording message: {str(e)}")
    
    def get_infrastructure_status(self) -> Dict:
        """Get comprehensive infrastructure status"""
        try:
            # Get all registered servers
            server_registry = {}
            if self.redis_client:
                server_registry = self.redis_client.hgetall('server_registry')
            
            # Parse server data
            servers = {}
            for server_id, server_data in server_registry.items():
                servers[server_id] = json.loads(server_data)
            
            # Get load balancer status
            lb_status = self.load_balancer.get_status()
            
            # Get recent alerts
            recent_alerts = self._get_recent_alerts(10)
            
            return {
                'current_server': asdict(self.server_metrics),
                'all_servers': servers,
                'load_balancer': lb_status,
                'recent_alerts': recent_alerts,
                'total_servers': len(servers),
                'healthy_servers': len([s for s in servers.values() if s['health_status'] == 'healthy']),
                'thresholds': self.thresholds
            }
            
        except Exception as e:
            logger.error(f"Error getting infrastructure status: {str(e)}")
            return {'error': str(e)}
    
    def _get_recent_alerts(self, limit: int = 10) -> List[Dict]:
        """Get recent infrastructure alerts"""
        try:
            if not self.redis_client:
                return []
            
            alerts = []
            alert_items = self.redis_client.lrange('infrastructure_alerts', 0, limit - 1)
            
            for item in alert_items:
                alerts.append(json.loads(item))
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error getting recent alerts: {str(e)}")
            return []
    
    def get_performance_report(self, hours: int = 24) -> Dict:
        """Get performance report for specified time period"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            # Filter metrics history
            relevant_metrics = [
                metric for metric in self.metrics_history
                if datetime.fromisoformat(metric['last_updated']) >= cutoff_time
            ]
            
            if not relevant_metrics:
                return {'error': 'No data available for specified period'}
            
            # Calculate aggregates
            avg_cpu = sum(m['cpu_usage'] for m in relevant_metrics) / len(relevant_metrics)
            avg_memory = sum(m['memory_usage'] for m in relevant_metrics) / len(relevant_metrics)
            avg_connections = sum(m['active_connections'] for m in relevant_metrics) / len(relevant_metrics)
            avg_message_rate = sum(m['message_rate'] for m in relevant_metrics) / len(relevant_metrics)
            avg_response_time = sum(m['response_time'] for m in relevant_metrics) / len(relevant_metrics)
            
            # Get alert count
            alert_count = len([m for m in relevant_metrics if m['health_status'] != 'healthy'])
            
            return {
                'period_hours': hours,
                'data_points': len(relevant_metrics),
                'averages': {
                    'cpu_usage': avg_cpu,
                    'memory_usage': avg_memory,
                    'active_connections': avg_connections,
                    'message_rate': avg_message_rate,
                    'response_time': avg_response_time
                },
                'alert_count': alert_count,
                'current_status': asdict(self.server_metrics),
                'trends': self._calculate_trends(relevant_metrics)
            }
            
        except Exception as e:
            logger.error(f"Error generating performance report: {str(e)}")
            return {'error': str(e)}
    
    def _calculate_trends(self, metrics_data: List[Dict]) -> Dict:
        """Calculate performance trends"""
        try:
            if len(metrics_data) < 2:
                return {'trend': 'insufficient_data'}
            
            # Compare first half to second half
            mid_point = len(metrics_data) // 2
            first_half = metrics_data[:mid_point]
            second_half = metrics_data[mid_point:]
            
            first_avg_cpu = sum(m['cpu_usage'] for m in first_half) / len(first_half)
            second_avg_cpu = sum(m['cpu_usage'] for m in second_half) / len(second_half)
            
            first_avg_memory = sum(m['memory_usage'] for m in first_half) / len(first_half)
            second_avg_memory = sum(m['memory_usage'] for m in second_half) / len(second_half)
            
            first_avg_connections = sum(m['active_connections'] for m in first_half) / len(first_half)
            second_avg_connections = sum(m['active_connections'] for m in second_half) / len(second_half)
            
            cpu_trend = 'improving' if second_avg_cpu < first_avg_cpu else 'declining'
            memory_trend = 'improving' if second_avg_memory < first_avg_memory else 'declining'
            connections_trend = 'stable' if abs(second_avg_connections - first_avg_connections) < 10 else ('increasing' if second_avg_connections > first_avg_connections else 'decreasing')
            
            return {
                'cpu': cpu_trend,
                'memory': memory_trend,
                'connections': connections_trend,
                'overall': self._calculate_overall_trend(cpu_trend, memory_trend, connections_trend)
            }
            
        except Exception as e:
            logger.error(f"Error calculating trends: {str(e)}")
            return {'trend': 'error', 'error': str(e)}
    
    def _calculate_overall_trend(self, cpu_trend: str, memory_trend: str, connections_trend: str) -> str:
        """Calculate overall trend"""
        improving_count = sum(1 for trend in [cpu_trend, memory_trend] if trend == 'improving')
        
        if improving_count >= 2:
            return 'improving'
        elif improving_count == 1:
            return 'stable'
        else:
            return 'declining'
    
    def stop_monitoring(self):
        """Stop real-time monitoring"""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        
        self.load_balancer.stop()
        logger.info("Real-time monitoring stopped")

class LoadBalancer:
    """Load balancer for WebSocket servers"""
    
    def __init__(self):
        self.servers = {}
        self.current_index = 0
        self.algorithm = 'least_connections'
        self.running = False
        self.health_check_thread = None
        
    def start(self):
        """Start load balancer"""
        self.running = True
        self.health_check_thread = threading.Thread(
            target=self._health_check_loop,
            daemon=True
        )
        self.health_check_thread.start()
        logger.info("Load balancer started")
    
    def stop(self):
        """Stop load balancer"""
        self.running = False
        if self.health_check_thread:
            self.health_check_thread.join(timeout=5)
        logger.info("Load balancer stopped")
    
    def add_server(self, server_id: str, server_info: Dict):
        """Add server to load balancer"""
        self.servers[server_id] = {
            'info': server_info,
            'metrics': None,
            'healthy': True,
            'last_health_check': time.time(),
            'connection_count': 0
        }
        logger.info(f"Added server to load balancer: {server_id}")
    
    def remove_server(self, server_id: str):
        """Remove server from load balancer"""
        if server_id in self.servers:
            del self.servers[server_id]
            logger.info(f"Removed server from load balancer: {server_id}")
    
    def update_server_metrics(self, server_id: str, metrics: ServerMetrics):
        """Update server metrics"""
        if server_id in self.servers:
            self.servers[server_id]['metrics'] = metrics
            self.servers[server_id]['connection_count'] = metrics.active_connections
    
    def get_next_server(self) -> Optional[str]:
        """Get next server based on load balancing algorithm"""
        healthy_servers = [
            server_id for server_id, server_data in self.servers.items()
            if server_data['healthy']
        ]
        
        if not healthy_servers:
            return None
        
        if self.algorithm == 'round_robin':
            return self._round_robin_selection(healthy_servers)
        elif self.algorithm == 'least_connections':
            return self._least_connections_selection(healthy_servers)
        elif self.algorithm == 'weighted':
            return self._weighted_selection(healthy_servers)
        else:
            return healthy_servers[0]
    
    def _round_robin_selection(self, servers: List[str]) -> str:
        """Round-robin server selection"""
        server = servers[self.current_index % len(servers)]
        self.current_index += 1
        return server
    
    def _least_connections_selection(self, servers: List[str]) -> str:
        """Select server with least connections"""
        return min(
            servers,
            key=lambda s: self.servers[s]['connection_count']
        )
    
    def _weighted_selection(self, servers: List[str]) -> str:
        """Weighted server selection based on performance"""
        # Simple weighting based on CPU and memory usage
        def get_weight(server_id):
            server_data = self.servers[server_id]
            metrics = server_data.get('metrics')
            if not metrics:
                return 1.0
            
            # Lower CPU and memory usage = higher weight
            cpu_weight = max(0.1, 1.0 - (metrics.cpu_usage / 100.0))
            memory_weight = max(0.1, 1.0 - (metrics.memory_usage / 100.0))
            
            return cpu_weight * memory_weight
        
        return max(servers, key=get_weight)
    
    def _health_check_loop(self):
        """Health check loop for servers"""
        while self.running:
            try:
                for server_id, server_data in self.servers.items():
                    self._check_server_health(server_id)
                
                time.sleep(30)  # Health check every 30 seconds
                
            except Exception as e:
                logger.error(f"Health check error: {str(e)}")
                time.sleep(10)
    
    def _check_server_health(self, server_id: str):
        """Check health of individual server"""
        try:
            server_data = self.servers[server_id]
            metrics = server_data.get('metrics')
            
            if not metrics:
                server_data['healthy'] = False
                return
            
            # Check if server is responding
            current_time = time.time()
            last_updated = metrics.last_updated.timestamp()
            
            # Consider unhealthy if no updates for 2 minutes
            if current_time - last_updated > 120:
                server_data['healthy'] = False
                logger.warning(f"Server {server_id} marked as unhealthy (no recent updates)")
            elif metrics.health_status in ['warning', 'critical']:
                server_data['healthy'] = False
                logger.warning(f"Server {server_id} marked as unhealthy (status: {metrics.health_status})")
            else:
                server_data['healthy'] = True
            
            server_data['last_health_check'] = current_time
            
        except Exception as e:
            logger.error(f"Error checking server health for {server_id}: {str(e)}")
            self.servers[server_id]['healthy'] = False
    
    def get_status(self) -> Dict:
        """Get load balancer status"""
        healthy_servers = [
            server_id for server_id, server_data in self.servers.items()
            if server_data['healthy']
        ]
        
        return {
            'algorithm': self.algorithm,
            'total_servers': len(self.servers),
            'healthy_servers': len(healthy_servers),
            'unhealthy_servers': len(self.servers) - len(healthy_servers),
            'current_index': self.current_index,
            'servers': {
                server_id: {
                    'healthy': server_data['healthy'],
                    'connection_count': server_data['connection_count'],
                    'last_health_check': server_data['last_health_check']
                }
                for server_id, server_data in self.servers.items()
            }
        }

# Global real-time monitor instance
realtime_monitor = RealtimeMonitor()
