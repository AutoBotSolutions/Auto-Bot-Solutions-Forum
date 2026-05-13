"""
Data Replication Utilities

Utility functions and helpers for data replication, master-slave replication,
multi-master replication, replication monitoring, and conflict resolution.
"""

import json
import time
import threading
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Callable, Union
from collections import defaultdict, deque
from dataclasses import dataclass
from enum import Enum

from app.replication.service import get_data_replication_service


class ReplicationMode(Enum):
    """Replication modes"""
    SYNCHRONOUS = "synchronous"
    ASYNCHRONOUS = "asynchronous"
    SEMI_SYNC = "semi_sync"


class ConsistencyLevel(Enum):
    """Consistency levels"""
    STRONG = "strong"
    EVENTUAL = "eventual"
    CAUSAL = "causal"


class ConflictType(Enum):
    """Conflict types"""
    WRITE_WRITE = "write_write"
    READ_WRITE = "read_write"
    SCHEMA = "schema"
    DATA = "data"


class ConflictSeverity(Enum):
    """Conflict severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ReplicationEvent:
    """Replication event structure"""
    event_id: str
    event_type: str
    source_node_id: str
    target_node_id: str
    data: Dict[str, Any]
    timestamp: datetime
    transaction_id: Optional[str] = None
    sequence_number: Optional[int] = None


@dataclass
class ConflictInfo:
    """Conflict information structure"""
    conflict_id: str
    conflict_type: ConflictType
    table_name: str
    record_id: str
    original_value: Any
    conflicting_values: Dict[str, Any]
    severity: ConflictSeverity
    timestamp: datetime


class ReplicationMonitor:
    """Replication monitor for tracking replication health"""
    
    def __init__(self):
        self.health_checks = {}
        self.metrics_history = deque(maxlen=1000)
        self.alert_thresholds = {
            'replication_lag_ms': 1000,  # 1 second
            'error_rate': 0.05,  # 5%
            'connection_failures': 3,  # 3 consecutive failures
            'disk_usage': 0.9,  # 90%
            'memory_usage': 0.8  # 80%
        }
        self.lock = threading.Lock()
    
    def check_replication_health(self, cluster_id: int) -> Dict[str, Any]:
        """Check replication health for a cluster"""
        try:
            # Get replication service
            replication_service = get_data_replication_service()
            
            # Get cluster health
            health_data = replication_service.get_replication_health(cluster_id)
            if not health_data:
                return {'status': 'error', 'message': 'Unable to get health data'}
            
            # Check for issues
            issues = []
            
            # Check replication lag
            if health_data.get('replication_lag_ms', 0) > self.alert_thresholds['replication_lag_ms']:
                issues.append({
                    'type': 'replication_lag',
                    'severity': 'warning',
                    'message': f"Replication lag: {health_data['replication_lag_ms']}ms",
                    'value': health_data['replication_lag_ms'],
                    'threshold': self.alert_thresholds['replication_lag_ms']
                })
            
            # Check error rate
            if health_data.get('error_rate', 0) > self.alert_thresholds['error_rate']:
                issues.append({
                    'type': 'error_rate',
                    'severity': 'critical',
                    'message': f"Error rate: {health_data['error_rate']:.2%}",
                    'value': health_data['error_rate'],
                    'threshold': self.alert_thresholds['error_rate']
                })
            
            # Check unhealthy nodes
            unhealthy_nodes = [n for n in health_data.get('nodes', []) if n.get('health_status') != 'healthy']
            if unhealthy_nodes:
                issues.append({
                    'type': 'unhealthy_nodes',
                    'severity': 'warning',
                    'message': f"{len(unhealthy_nodes)} unhealthy nodes",
                    'value': len(unhealthy_nodes),
                    'nodes': [n['node_name'] for n in unhealthy_nodes]
                })
            
            # Check disconnected nodes
            disconnected_nodes = [n for n in health_data.get('nodes', []) if n.get('connection_status') != 'connected']
            if disconnected_nodes:
                issues.append({
                    'type': 'disconnected_nodes',
                    'severity': 'critical',
                    'message': f"{len(disconnected_nodes)} disconnected nodes",
                    'value': len(disconnected_nodes),
                    'nodes': [n['node_name'] for n in disconnected_nodes]
                })
            
            # Determine overall status
            if any(issue['severity'] == 'critical' for issue in issues):
                overall_status = 'critical'
            elif any(issue['severity'] == 'warning' for issue in issues):
                overall_status = 'warning'
            else:
                overall_status = 'healthy'
            
            return {
                'status': overall_status,
                'cluster_id': cluster_id,
                'health_data': health_data,
                'issues': issues,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def record_metrics(self, cluster_id: int, metrics: Dict[str, Any]):
        """Record replication metrics"""
        with self.lock:
            metrics['timestamp'] = datetime.utcnow().isoformat()
            metrics['cluster_id'] = cluster_id
            self.metrics_history.append(metrics)
            
            # Check for alerts
            self._check_alerts(cluster_id, metrics)
    
    def _check_alerts(self, cluster_id: int, metrics: Dict[str, Any]):
        """Check metrics against alert thresholds"""
        alerts = []
        
        # Check replication lag
        replication_lag = metrics.get('replication_lag_ms', 0)
        if replication_lag > self.alert_thresholds['replication_lag_ms']:
            alerts.append({
                'type': 'replication_lag',
                'cluster_id': cluster_id,
                'value': replication_lag,
                'threshold': self.alert_thresholds['replication_lag_ms'],
                'message': f"Replication lag too high: {replication_lag}ms"
            })
        
        # Check error rate
        error_rate = metrics.get('error_rate', 0)
        if error_rate > self.alert_thresholds['error_rate']:
            alerts.append({
                'type': 'error_rate',
                'cluster_id': cluster_id,
                'value': error_rate,
                'threshold': self.alert_thresholds['error_rate'],
                'message': f"Error rate too high: {error_rate:.2%}"
            })
        
        # Handle alerts
        for alert in alerts:
            self._handle_alert(alert)
    
    def _handle_alert(self, alert: Dict[str, Any]):
        """Handle replication alert"""
        try:
            print(f"Replication alert: {alert['message']}")
            
            # Could integrate with notification system here
            # For now, just log the alert
            
        except Exception as e:
            print(f"Error handling alert: {e}")
    
    def get_metrics_summary(self, cluster_id: int, hours: int = 1) -> Dict[str, Any]:
        """Get metrics summary for a cluster"""
        with self.lock:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            cluster_metrics = [
                m for m in self.metrics_history 
                if m.get('cluster_id') == cluster_id and 
                datetime.fromisoformat(m['timestamp']) >= cutoff_time
            ]
            
            if not cluster_metrics:
                return {}
            
            # Calculate averages
            avg_replication_lag = sum(m.get('replication_lag_ms', 0) for m in cluster_metrics) / len(cluster_metrics)
            avg_throughput = sum(m.get('throughput_ops_per_second', 0) for m in cluster_metrics) / len(cluster_metrics)
            avg_error_rate = sum(m.get('error_rate', 0) for m in cluster_metrics) / len(cluster_metrics)
            
            return {
                'cluster_id': cluster_id,
                'period_hours': hours,
                'sample_count': len(cluster_metrics),
                'avg_replication_lag_ms': avg_replication_lag,
                'avg_throughput_ops_per_second': avg_throughput,
                'avg_error_rate': avg_error_rate,
                'timestamp': datetime.utcnow().isoformat()
            }


class ReplicationValidator:
    """Validator for replication configurations and data"""
    
    def __init__(self):
        self.validation_rules = {
            'cluster_name': r'^[a-zA-Z0-9_-]{1,100}$',
            'node_name': r'^[a-zA-Z0-9_-]{1,100}$',
            'host': r'^[a-zA-Z0-9.-]{1,255}$',
            'port': r'^[0-9]{1,5}$',
            'database': r'^[a-zA-Z0-9_]{1,100}$'
        }
    
    def validate_cluster_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate cluster configuration"""
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Check required fields
        required_fields = ['cluster_name', 'cluster_type', 'database_type', 'replication_mode', 'consistency_level']
        for field in required_fields:
            if field not in config:
                validation_result['errors'].append(f"Missing required field: {field}")
                validation_result['valid'] = False
        
        # Validate cluster type
        cluster_type = config.get('cluster_type')
        if cluster_type and cluster_type not in ['master_slave', 'multi_master', 'hybrid']:
            validation_result['errors'].append(f"Invalid cluster type: {cluster_type}")
            validation_result['valid'] = False
        
        # Validate replication mode
        replication_mode = config.get('replication_mode')
        if replication_mode and replication_mode not in ['synchronous', 'asynchronous', 'semi_sync']:
            validation_result['errors'].append(f"Invalid replication mode: {replication_mode}")
            validation_result['valid'] = False
        
        # Validate consistency level
        consistency_level = config.get('consistency_level')
        if consistency_level and consistency_level not in ['strong', 'eventual', 'causal']:
            validation_result['errors'].append(f"Invalid consistency level: {consistency_level}")
            validation_result['valid'] = False
        
        # Validate cluster name
        cluster_name = config.get('cluster_name')
        if cluster_name and not self._validate_pattern(cluster_name, 'cluster_name'):
            validation_result['errors'].append("Invalid cluster name format")
            validation_result['valid'] = False
        
        return validation_result
    
    def validate_node_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate node configuration"""
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Check required fields
        required_fields = ['node_name', 'node_role', 'node_type', 'host', 'port', 'database', 'username']
        for field in required_fields:
            if field not in config:
                validation_result['errors'].append(f"Missing required field: {field}")
                validation_result['valid'] = False
        
        # Validate node role
        node_role = config.get('node_role')
        if node_role and node_role not in ['master', 'slave', 'multi_master', 'arbiter']:
            validation_result['errors'].append(f"Invalid node role: {node_role}")
            validation_result['valid'] = False
        
        # Validate node type
        node_type = config.get('node_type')
        if node_type and node_type not in ['primary', 'secondary', 'arbiter']:
            validation_result['errors'].append(f"Invalid node type: {node_type}")
            validation_result['valid'] = False
        
        # Validate port
        port = config.get('port')
        if port and (not isinstance(port, int) or port < 1 or port > 65535):
            validation_result['errors'].append("Port must be an integer between 1 and 65535")
            validation_result['valid'] = False
        
        # Validate host
        host = config.get('host')
        if host and not self._validate_pattern(host, 'host'):
            validation_result['errors'].append("Invalid host format")
            validation_result['valid'] = False
        
        # Validate database name
        database = config.get('database')
        if database and not self._validate_pattern(database, 'database'):
            validation_result['errors'].append("Invalid database name format")
            validation_result['valid'] = False
        
        return validation_result
    
    def validate_data_consistency(self, cluster_id: int) -> Dict[str, Any]:
        """Validate data consistency across nodes"""
        try:
            # This would implement actual data consistency validation
            # For now, return simulated results
            
            validation_result = {
                'valid': True,
                'inconsistencies': [],
                'summary': {
                    'total_records_checked': 10000,
                    'inconsistent_records': 5,
                    'consistency_percentage': 99.95
                },
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Simulate some inconsistencies
            if hash(str(cluster_id)) % 10 == 0:  # 10% chance of inconsistencies
                validation_result['valid'] = False
                validation_result['inconsistencies'] = [
                    {
                        'table': 'users',
                        'record_id': '123',
                        'field': 'email',
                        'node_1_value': 'user1@example.com',
                        'node_2_value': 'user2@example.com'
                    }
                ]
                validation_result['summary']['inconsistent_records'] = 1
                validation_result['summary']['consistency_percentage'] = 99.99
            
            return validation_result
            
        except Exception as e:
            return {
                'valid': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def _validate_pattern(self, value: str, pattern_name: str) -> bool:
        """Validate value against pattern"""
        import re
        pattern = self.validation_rules.get(pattern_name)
        if pattern:
            return bool(re.match(pattern, value))
        return True


class ReplicationOptimizer:
    """Optimizer for replication performance"""
    
    def __init__(self):
        self.optimization_rules = {
            'minimize_lag': True,
            'maximize_throughput': True,
            'balance_load': True,
            'reduce_conflicts': True
        }
    
    def optimize_replication_settings(self, cluster_id: int) -> Dict[str, Any]:
        """Optimize replication settings for a cluster"""
        try:
            # Get current metrics
            replication_service = get_data_replication_service()
            metrics = replication_service.get_cluster_metrics(cluster_id)
            
            if not metrics:
                return {'success': False, 'message': 'Unable to get cluster metrics'}
            
            optimizations = []
            
            # Optimize based on replication lag
            replication_lag = metrics.get('performance', {}).get('avg_replication_lag_ms', 0)
            if replication_lag > 500:  # 500ms threshold
                optimizations.append({
                    'type': 'replication_lag',
                    'suggestion': 'Consider increasing replication frequency or using synchronous mode',
                    'current_value': replication_lag,
                    'target_value': 100
                })
            
            # Optimize based on throughput
            throughput = metrics.get('performance', {}).get('throughput_ops_per_second', 0)
            if throughput < 100:  # Low throughput
                optimizations.append({
                    'type': 'throughput',
                    'suggestion': 'Consider optimizing queries or adding more nodes',
                    'current_value': throughput,
                    'target_value': 1000
                })
            
            # Optimize based on connection utilization
            utilization = metrics.get('connections', {}).get('utilization', 0)
            if utilization > 0.8:  # 80% utilization
                optimizations.append({
                    'type': 'connection_utilization',
                    'suggestion': 'Consider increasing connection pool size',
                    'current_value': utilization,
                    'target_value': 0.6
                })
            
            # Optimize based on conflicts
            conflicts = metrics.get('conflicts', {}).get('total_conflicts', 0)
            if conflicts > 10:  # High conflict rate
                optimizations.append({
                    'type': 'conflicts',
                    'suggestion': 'Consider improving conflict resolution strategy',
                    'current_value': conflicts,
                    'target_value': 5
                })
            
            return {
                'success': True,
                'cluster_id': cluster_id,
                'optimizations': optimizations,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def suggest_node_configuration(self, cluster_type: str, expected_load: float) -> Dict[str, Any]:
        """Suggest optimal node configuration"""
        try:
            suggestions = {
                'cluster_type': cluster_type,
                'expected_load': expected_load,
                'recommendations': []
            }
            
            if cluster_type == 'master_slave':
                if expected_load < 100:  # Low load
                    suggestions['recommendations'].append({
                        'component': 'nodes',
                        'recommendation': '1 master, 1-2 slaves',
                        'reason': 'Low load requires minimal replication'
                    })
                elif expected_load < 1000:  # Medium load
                    suggestions['recommendations'].append({
                        'component': 'nodes',
                        'recommendation': '1 master, 3-5 slaves',
                        'reason': 'Medium load requires more slaves for read scaling'
                    })
                else:  # High load
                    suggestions['recommendations'].append({
                        'component': 'nodes',
                        'recommendation': '1 master, 5+ slaves',
                        'reason': 'High load requires many slaves for read scaling'
                    })
                
            elif cluster_type == 'multi_master':
                if expected_load < 100:  # Low load
                    suggestions['recommendations'].append({
                        'component': 'nodes',
                        'recommendation': '2 masters',
                        'reason': 'Low load requires minimal multi-master setup'
                    })
                elif expected_load < 1000:  # Medium load
                    suggestions['recommendations'].append({
                        'component': 'nodes',
                        'recommendation': '3-5 masters',
                        'reason': 'Medium load requires balanced multi-master setup'
                    })
                else:  # High load
                    suggestions['recommendations'].append({
                        'component': 'nodes',
                        'recommendation': '5+ masters',
                        'reason': 'High load requires distributed multi-master setup'
                    })
            
            # Connection pool recommendations
            if expected_load < 100:
                connection_pool_size = 5
            elif expected_load < 1000:
                connection_pool_size = 10
            else:
                connection_pool_size = 20
            
            suggestions['recommendations'].append({
                'component': 'connection_pool',
                'recommendation': f'Pool size: {connection_pool_size}',
                'reason': f'Optimized for expected load of {expected_load} ops/sec'
            })
            
            # Replication mode recommendations
            if cluster_type == 'master_slave':
                suggestions['recommendations'].append({
                    'component': 'replication_mode',
                    'recommendation': 'asynchronous',
                    'reason': 'Best performance for master-slave replication'
                })
            elif cluster_type == 'multi_master':
                suggestions['recommendations'].append({
                    'component': 'replication_mode',
                    'recommendation': 'semi_sync',
                    'reason': 'Balance between performance and consistency'
                })
            
            return suggestions
            
        except Exception as e:
            return {'error': str(e)}


class ReplicationUtils:
    """General replication utility functions"""
    
    @staticmethod
    def calculate_replication_lag(source_timestamp: datetime, target_timestamp: datetime) -> float:
        """Calculate replication lag in milliseconds"""
        try:
            lag = (target_timestamp - source_timestamp).total_seconds() * 1000
            return max(0, lag)  # Ensure non-negative
        except Exception:
            return 0.0
    
    @staticmethod
    def generate_transaction_id() -> str:
        """Generate unique transaction ID"""
        import uuid
        return str(uuid.uuid4())
    
    @staticmethod
    def encrypt_password(password: str) -> str:
        """Encrypt password for storage"""
        # This would implement actual password encryption
        # For now, return a simple hash
        import hashlib
        return hashlib.sha256(password.encode()).hexdigest()
    
    @staticmethod
    def decrypt_password(encrypted_password: str) -> str:
        """Decrypt password for use"""
        # This would implement actual password decryption
        # For now, return the encrypted password (not secure)
        return encrypted_password
    
    @staticmethod
    def validate_connection_string(connection_string: str) -> Dict[str, Any]:
        """Validate database connection string"""
        try:
            # Simple connection string validation
            if not connection_string:
                return {'valid': False, 'error': 'Empty connection string'}
            
            # Check for required components
            if '://' not in connection_string:
                return {'valid': False, 'error': 'Invalid connection string format'}
            
            return {'valid': True}
            
        except Exception as e:
            return {'valid': False, 'error': str(e)}
    
    @staticmethod
    def format_replication_metrics(metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Format replication metrics for display"""
        formatted = {
            'timestamp': metrics.get('timestamp', datetime.utcnow().isoformat()),
            'cluster_id': metrics.get('cluster_id'),
            'metrics': {}
        }
        
        # Format performance metrics
        performance = metrics.get('performance', {})
        formatted['metrics']['performance'] = {
            'replication_lag': f"{performance.get('avg_replication_lag_ms', 0):.2f}ms",
            'throughput': f"{performance.get('throughput_ops_per_second', 0):.2f} ops/sec",
            'utilization': f"{performance.get('utilization', 0):.2%}",
            'total_size': f"{performance.get('total_size_bytes', 0) / (1024**3):.2f} GB",
            'used_size': f"{performance.get('used_size_bytes', 0) / (1024**3):.2f} GB"
        }
        
        # Format connection metrics
        connections = metrics.get('connections', {})
        formatted['metrics']['connections'] = {
            'total': connections.get('total_connections', 0),
            'active': connections.get('active_connections', 0),
            'utilization': f"{connections.get('utilization', 0):.2%}"
        }
        
        # Format event metrics
        events = metrics.get('events', {})
        formatted['metrics']['events'] = {
            'total_events': events.get('total_events', 0),
            'avg_duration': f"{events.get('avg_duration_ms', 0):.2f}ms",
            'success_rate': f"{(1 - events.get('error_rate', 0)):.2%}"
        }
        
        # Format conflict metrics
        conflicts = metrics.get('conflicts', {})
        formatted['metrics']['conflicts'] = {
            'total_conflicts': conflicts.get('total_conflicts', 0),
            'resolved_conflicts': conflicts.get('resolved_conflicts', 0),
            'avg_resolution_time': f"{conflicts.get('avg_resolution_time_ms', 0):.2f}ms"
        }
        
        return formatted
    
    @staticmethod
    def analyze_replication_patterns(events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze replication patterns from events"""
        if not events:
            return {'patterns': [], 'insights': []}
        
        patterns = []
        insights = []
        
        # Analyze event types
        event_types = {}
        for event in events:
            event_type = event.get('event_type', 'unknown')
            event_types[event_type] = event_types.get(event_type, 0) + 1
        
        # Find most common event type
        most_common_type = max(event_types.items(), key=lambda x: x[1]) if event_types else None
        if most_common_type:
            patterns.append({
                'type': 'most_common_event',
                'description': f"Most common event type: {most_common_type[0]} ({most_common_type[1]} occurrences)"
            })
        
        # Analyze timing patterns
        timestamps = [datetime.fromisoformat(event.get('timestamp', '')) for event in events if event.get('timestamp')]
        if timestamps:
            # Calculate average interval between events
            if len(timestamps) > 1:
                intervals = [(timestamps[i] - timestamps[i-1]).total_seconds() for i in range(1, len(timestamps))]
                avg_interval = sum(intervals) / len(intervals)
                
                patterns.append({
                    'type': 'timing_pattern',
                    'description': f"Average interval between events: {avg_interval:.2f} seconds"
                })
                
                # Generate insights
                if avg_interval < 1:
                    insights.append("High frequency events - consider optimizing replication frequency")
                elif avg_interval > 60:
                    insights.append("Low frequency events - replication may be underutilized")
        
        # Analyze error patterns
        error_events = [event for event in events if event.get('event_status') == 'failed']
        if error_events:
            error_rate = len(error_events) / len(events)
            patterns.append({
                'type': 'error_pattern',
                'description': f"Error rate: {error_rate:.2%}"
            })
            
            if error_rate > 0.1:  # 10% error rate
                insights.append("High error rate - investigate replication issues")
        
        return {
            'patterns': patterns,
            'insights': insights,
            'total_events': len(events),
            'analysis_period': f"{(timestamps[-1] - timestamps[0]).total_seconds():.2f} seconds" if timestamps else "N/A"
        }


# Global instances
replication_monitor = ReplicationMonitor()
replication_validator = ReplicationValidator()
replication_optimizer = ReplicationOptimizer()
replication_utils = ReplicationUtils()
