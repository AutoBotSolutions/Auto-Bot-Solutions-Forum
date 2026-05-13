"""
Distributed Cache Utilities

Utility functions and helpers for Redis cluster management, cache synchronization,
failover handling, and distributed cache operations.
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

from app.distributed_cache.service import get_distributed_cache_service


class CacheShardingStrategy(Enum):
    """Cache sharding strategies"""
    HASH_SLOT = "hash_slot"
    CONSISTENT_HASH = "consistent_hash"
    MODULO = "modulo"
    RANGE = "range"
    RANDOM = "random"


class CacheReplicationStrategy(Enum):
    """Cache replication strategies"""
    MASTER_SLAVE = "master_slave"
    MULTI_MASTER = "multi_master"
    READ_WRITE_SPLIT = "read_write_split"
    EVENTUAL_CONSISTENCY = "eventual_consistency"


@dataclass
class CacheKeyInfo:
    """Cache key information for sharding and replication"""
    key: str
    hash_value: str
    shard_id: Optional[str]
    replication_nodes: List[str]
    ttl: Optional[int]
    size: int
    created_at: datetime


class CacheSharding:
    """Cache sharding utility for distributed cache"""
    
    def __init__(self, strategy=CacheShardingStrategy.HASH_SLOT):
        self.strategy = strategy
        self.shard_count = 16384  # Redis cluster default
        self.shard_nodes = {}  # shard_id -> node_id
        self.node_shards = {}  # node_id -> shard_ids
        self.lock = threading.Lock()
    
    def add_node(self, node_id: str, shard_ids: List[str]):
        """Add a node with its assigned shards"""
        with self.lock:
            self.node_shards[node_id] = shard_ids
            for shard_id in shard_ids:
                self.shard_nodes[shard_id] = node_id
    
    def remove_node(self, node_id: str):
        """Remove a node and its shards"""
        with self.lock:
            if node_id in self.node_shards:
                shard_ids = self.node_shards[node_id]
                for shard_id in shard_ids:
                    if shard_id in self.shard_nodes:
                        del self.shard_nodes[shard_id]
                del self.node_shards[node_id]
    
    def get_shard_for_key(self, key: str) -> Optional[str]:
        """Get shard ID for a key"""
        if self.strategy == CacheShardingStrategy.HASH_SLOT:
            # Redis cluster hash slot calculation
            hash_value = self._crc16(key)
            shard_id = str(hash_value % self.shard_count)
            return shard_id
        elif self.strategy == CacheShardingStrategy.CONSISTENT_HASH:
            # Consistent hashing
            return self._consistent_hash(key)
        elif self.strategy == CacheShardingStrategy.MODULO:
            # Simple modulo hashing
            hash_value = hash(key)
            return str(hash_value % self.shard_count)
        elif self.strategy == CacheShardingStrategy.RANGE:
            # Range-based sharding
            return self._range_shard(key)
        else:
            # Random sharding
            import random
            return str(random.randint(0, self.shard_count - 1))
    
    def get_node_for_key(self, key: str) -> Optional[str]:
        """Get node ID for a key"""
        shard_id = self.get_shard_for_key(key)
        if shard_id:
            return self.shard_nodes.get(shard_id)
        return None
    
    def get_shard_distribution(self) -> Dict[str, int]:
        """Get shard distribution across nodes"""
        distribution = defaultdict(int)
        for shard_id, node_id in self.shard_nodes.items():
            distribution[node_id] += 1
        return dict(distribution)
    
    def rebalance_shards(self, new_nodes: List[str]) -> Dict[str, List[str]]:
        """Rebalance shards across nodes"""
        with self.lock:
            # This is a simplified rebalancing algorithm
            all_shards = list(self.shard_nodes.keys())
            shards_per_node = len(all_shards) // len(new_nodes)
            
            new_distribution = {}
            start_index = 0
            
            for node_id in new_nodes:
                if start_index < len(all_shards):
                    end_index = min(start_index + shards_per_node, len(all_shards))
                    new_distribution[node_id] = all_shards[start_index:end_index]
                    start_index = end_index
            
            return new_distribution
    
    def _crc16(self, data: str) -> int:
        """Calculate CRC16 hash (Redis cluster algorithm)"""
        crc = 0
        for byte in data.encode('utf-8'):
            crc = ((crc << 8) & 0xFF00) | (crc >> 8)
            crc ^= byte
            crc = ((crc & 0xFF) << 8) | (crc >> 8)
            crc ^= 0x1021
        return crc & 0xFFFF
    
    def _consistent_hash(self, key: str) -> str:
        """Consistent hashing implementation"""
        # Simplified consistent hashing
        hash_value = int(hashlib.md5(key.encode()).hexdigest(), 16)
        return str(hash_value % self.shard_count)
    
    def _range_shard(self, key: str) -> str:
        """Range-based sharding"""
        # Use first character to determine range
        if not key:
            return "0"
        
        first_char = key[0].lower()
        if 'a' <= first_char <= 'f':
            return str(0)
        elif 'g' <= first_char <= 'l':
            return str(1)
        elif 'm' <= first_char <= 'r':
            return str(2)
        elif 's' <= first_char <= 'z':
            return str(3)
        else:
            return str(4)


class CacheReplication:
    """Cache replication utility for distributed cache"""
    
    def __init__(self, strategy=CacheReplicationStrategy.MASTER_SLAVE):
        self.strategy = strategy
        self.master_nodes = set()
        self.slave_nodes = defaultdict(set)  # master_id -> slave_ids
        self.replication_factor = 1
        self.lock = threading.Lock()
    
    def set_replication_factor(self, factor: int):
        """Set replication factor"""
        self.replication_factor = factor
    
    def add_master_node(self, node_id: str):
        """Add a master node"""
        with self.lock:
            self.master_nodes.add(node_id)
    
    def add_slave_node(self, master_id: str, slave_id: str):
        """Add a slave node to a master"""
        with self.lock:
            self.slave_nodes[master_id].add(slave_id)
    
    def remove_node(self, node_id: str):
        """Remove a node (master or slave)"""
        with self.lock:
            if node_id in self.master_nodes:
                self.master_nodes.remove(node_id)
                if node_id in self.slave_nodes:
                    del self.slave_nodes[node_id]
            else:
                # Remove from all slave lists
                for master_id, slaves in self.slave_nodes.items():
                    if node_id in slaves:
                        slaves.remove(node_id)
    
    def get_replication_nodes(self, key: str, operation: str = 'read') -> List[str]:
        """Get nodes for a key based on operation"""
        if self.strategy == CacheReplicationStrategy.MASTER_SLAVE:
            if operation == 'write':
                # Write to master only
                return list(self.master_nodes)
            else:
                # Read from slaves if available, otherwise master
                all_nodes = list(self.master_nodes)
                for slaves in self.slave_nodes.values():
                    all_nodes.extend(slaves)
                return all_nodes
        
        elif self.strategy == CacheReplicationStrategy.MULTI_MASTER:
            # All nodes can handle both read and write
            all_nodes = list(self.master_nodes)
            for slaves in self.slave_nodes.values():
                all_nodes.extend(slaves)
            return all_nodes
        
        elif self.strategy == CacheReplicationStrategy.READ_WRITE_SPLIT:
            if operation == 'write':
                return list(self.master_nodes)
            else:
                # Prefer slaves for reads
                read_nodes = []
                for slaves in self.slave_nodes.values():
                    read_nodes.extend(slaves)
                if not read_nodes:
                    read_nodes = list(self.master_nodes)
                return read_nodes
        
        else:
            # Default to all nodes
            all_nodes = list(self.master_nodes)
            for slaves in self.slave_nodes.values():
                all_nodes.extend(slaves)
            return all_nodes
    
    def get_master_for_slave(self, slave_id: str) -> Optional[str]:
        """Get master node for a slave"""
        for master_id, slaves in self.slave_nodes.items():
            if slave_id in slaves:
                return master_id
        return None
    
    def get_slaves_for_master(self, master_id: str) -> List[str]:
        """Get slave nodes for a master"""
        return list(self.slave_nodes.get(master_id, set()))
    
    def promote_slave_to_master(self, slave_id: str) -> bool:
        """Promote a slave to master"""
        with self.lock:
            # Find the master of this slave
            master_id = self.get_master_for_slave(slave_id)
            if master_id:
                # Remove slave from old master
                self.slave_nodes[master_id].discard(slave_id)
                
                # Promote to master
                self.master_nodes.add(slave_id)
                self.slave_nodes[slave_id] = set()
                
                # Reassign slaves to new master if needed
                if self.slave_nodes[master_id]:
                    # Move some slaves to new master
                    slaves_to_move = list(self.slave_nodes[master_id])[:self.replication_factor]
                    for slave in slaves_to_move:
                        self.slave_nodes[master_id].remove(slave)
                        self.slave_nodes[slave_id].add(slave)
                
                return True
            return False
    
    def get_replication_status(self) -> Dict[str, Any]:
        """Get replication status"""
        return {
            'strategy': self.strategy.value,
            'replication_factor': self.replication_factor,
            'master_nodes': len(self.master_nodes),
            'total_slave_nodes': sum(len(slaves) for slaves in self.slave_nodes.values()),
            'master_slave_pairs': len(self.slave_nodes)
        }


class CacheConsistencyChecker:
    """Cache consistency checker for distributed cache"""
    
    def __init__(self):
        self.inconsistency_threshold = 0.1  # 10% inconsistency threshold
        self.check_interval = 300  # 5 minutes
        self.running = False
        self.check_thread = None
    
    def start_consistency_checking(self):
        """Start consistency checking thread"""
        if not self.running:
            self.running = True
            self.check_thread = threading.Thread(target=self._consistency_check_loop)
            self.check_thread.daemon = True
            self.check_thread.start()
    
    def stop_consistency_checking(self):
        """Stop consistency checking thread"""
        self.running = False
        if self.check_thread:
            self.check_thread.join()
    
    def _consistency_check_loop(self):
        """Main consistency checking loop"""
        while self.running:
            try:
                self._check_cache_consistency()
                time.sleep(self.check_interval)
            except Exception as e:
                print(f"Error in consistency check: {e}")
                time.sleep(60)  # Wait 1 minute on error
    
    def _check_cache_consistency(self):
        """Check cache consistency across nodes"""
        try:
            from app.distributed_cache.models import CacheCluster
            
            clusters = CacheCluster.query.filter_by(status='active').all()
            
            for cluster in clusters:
                self._check_cluster_consistency(cluster)
                
        except Exception as e:
            print(f"Error checking cache consistency: {e}")
    
    def _check_cluster_consistency(self, cluster):
        """Check consistency for a specific cluster"""
        try:
            distributed_service = get_distributed_cache_service()
            redis_client = distributed_service.get_redis_client(cluster.cluster_id)
            
            if not redis_client:
                return
            
            # Get sample keys for consistency check
            sample_keys = self._get_sample_keys(redis_client, 100)
            
            inconsistencies = []
            
            for key in sample_keys:
                inconsistency = self._check_key_consistency(redis_client, key)
                if inconsistency:
                    inconsistencies.append(inconsistency)
            
            # Report inconsistencies if above threshold
            if len(inconsistencies) > len(sample_keys) * self.inconsistency_threshold:
                self._report_inconsistencies(cluster, inconsistencies)
                
        except Exception as e:
            print(f"Error checking cluster {cluster.cluster_name} consistency: {e}")
    
    def _get_sample_keys(self, redis_client, sample_size: int) -> List[str]:
        """Get sample keys for consistency check"""
        try:
            all_keys = redis_client.keys('*')
            if len(all_keys) <= sample_size:
                return all_keys
            else:
                # Random sample
                import random
                return random.sample(all_keys, sample_size)
        except Exception as e:
            print(f"Error getting sample keys: {e}")
            return []
    
    def _check_key_consistency(self, redis_client, key: str) -> Optional[Dict[str, Any]]:
        """Check consistency for a specific key"""
        try:
            # Get value and metadata
            value = redis_client.get(key)
            ttl = redis_client.ttl(key)
            
            # For cluster mode, check consistency across nodes
            # This is a simplified check - in practice would check across all nodes
            
            return None  # No inconsistency detected
            
        except Exception as e:
            return {
                'key': key,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def _report_inconsistencies(self, cluster, inconsistencies: List[Dict[str, Any]]):
        """Report cache inconsistencies"""
        try:
            print(f"Cache inconsistencies detected in cluster {cluster.cluster_name}:")
            for inconsistency in inconsistencies:
                print(f"  - Key: {inconsistency.get('key', 'unknown')}")
                print(f"    Error: {inconsistency.get('error', 'unknown')}")
            
            # Create alert or notification here
            # This could integrate with the security system or notification system
            
        except Exception as e:
            print(f"Error reporting inconsistencies: {e}")


class CachePerformanceMonitor:
    """Cache performance monitoring utility"""
    
    def __init__(self):
        self.metrics_history = deque(maxlen=1000)  # Keep last 1000 metrics
        self.alert_thresholds = {
            'hit_rate': 0.8,  # 80% hit rate threshold
            'memory_usage': 0.9,  # 90% memory usage threshold
            'response_time': 1000,  # 1 second response time threshold
            'error_rate': 0.05  # 5% error rate threshold
        }
        self.lock = threading.Lock()
    
    def record_metrics(self, cluster_id: str, metrics: Dict[str, Any]):
        """Record cache performance metrics"""
        with self.lock:
            metrics['timestamp'] = datetime.utcnow().isoformat()
            metrics['cluster_id'] = cluster_id
            self.metrics_history.append(metrics)
            
            # Check for alerts
            self._check_alerts(cluster_id, metrics)
    
    def _check_alerts(self, cluster_id: str, metrics: Dict[str, Any]):
        """Check metrics against alert thresholds"""
        alerts = []
        
        # Check hit rate
        hit_rate = metrics.get('hit_rate', 0)
        if hit_rate < self.alert_thresholds['hit_rate']:
            alerts.append({
                'type': 'hit_rate_low',
                'cluster_id': cluster_id,
                'value': hit_rate,
                'threshold': self.alert_thresholds['hit_rate'],
                'message': f"Cache hit rate too low: {hit_rate:.2%}"
            })
        
        # Check memory usage
        memory_usage = metrics.get('memory_utilization', 0)
        if memory_usage > self.alert_thresholds['memory_usage']:
            alerts.append({
                'type': 'memory_usage_high',
                'cluster_id': cluster_id,
                'value': memory_usage,
                'threshold': self.alert_thresholds['memory_usage'],
                'message': f"Memory usage too high: {memory_usage:.2%}"
            })
        
        # Check response time
        response_time = metrics.get('avg_response_time', 0)
        if response_time > self.alert_thresholds['response_time']:
            alerts.append({
                'type': 'response_time_high',
                'cluster_id': cluster_id,
                'value': response_time,
                'threshold': self.alert_thresholds['response_time'],
                'message': f"Response time too high: {response_time:.2f}ms"
            })
        
        # Handle alerts
        for alert in alerts:
            self._handle_alert(alert)
    
    def _handle_alert(self, alert: Dict[str, Any]):
        """Handle performance alert"""
        try:
            print(f"Cache performance alert: {alert['message']}")
            
            # Could integrate with notification system here
            # For now, just log the alert
            
        except Exception as e:
            print(f"Error handling alert: {e}")
    
    def get_metrics_summary(self, cluster_id: str, hours: int = 1) -> Dict[str, Any]:
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
            avg_hit_rate = sum(m.get('hit_rate', 0) for m in cluster_metrics) / len(cluster_metrics)
            avg_memory_usage = sum(m.get('memory_utilization', 0) for m in cluster_metrics) / len(cluster_metrics)
            avg_response_time = sum(m.get('avg_response_time', 0) for m in cluster_metrics) / len(cluster_metrics)
            
            return {
                'cluster_id': cluster_id,
                'period_hours': hours,
                'sample_count': len(cluster_metrics),
                'avg_hit_rate': avg_hit_rate,
                'avg_memory_usage': avg_memory_usage,
                'avg_response_time': avg_response_time,
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def get_all_metrics_summary(self, hours: int = 1) -> Dict[str, Any]:
        """Get metrics summary for all clusters"""
        with self.lock:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            recent_metrics = [
                m for m in self.metrics_history 
                if datetime.fromisoformat(m['timestamp']) >= cutoff_time
            ]
            
            # Group by cluster
            cluster_metrics = defaultdict(list)
            for metric in recent_metrics:
                cluster_id = metric.get('cluster_id')
                if cluster_id:
                    cluster_metrics[cluster_id].append(metric)
            
            summaries = {}
            for cluster_id, metrics in cluster_metrics.items():
                if metrics:
                    avg_hit_rate = sum(m.get('hit_rate', 0) for m in metrics) / len(metrics)
                    avg_memory_usage = sum(m.get('memory_utilization', 0) for m in metrics) / len(metrics)
                    avg_response_time = sum(m.get('avg_response_time', 0) for m in metrics) / len(metrics)
                    
                    summaries[cluster_id] = {
                        'avg_hit_rate': avg_hit_rate,
                        'avg_memory_usage': avg_memory_usage,
                        'avg_response_time': avg_response_time,
                        'sample_count': len(metrics)
                    }
            
            return {
                'period_hours': hours,
                'cluster_summaries': summaries,
                'total_samples': len(recent_metrics),
                'timestamp': datetime.utcnow().isoformat()
            }


class CacheKeyManager:
    """Cache key management utility"""
    
    def __init__(self):
        self.key_patterns = {}
        self.key_metadata = {}
        self.lock = threading.Lock()
    
    def register_key_pattern(self, pattern: str, description: str, ttl: Optional[int] = None):
        """Register a key pattern"""
        with self.lock:
            self.key_patterns[pattern] = {
                'description': description,
                'ttl': ttl,
                'created_at': datetime.utcnow()
            }
    
    def generate_key(self, pattern: str, **kwargs) -> str:
        """Generate a cache key from pattern"""
        try:
            # Replace placeholders in pattern
            key = pattern.format(**kwargs)
            
            # Add metadata
            with self.lock:
                self.key_metadata[key] = {
                    'pattern': pattern,
                    'kwargs': kwargs,
                    'created_at': datetime.utcnow()
                }
            
            return key
            
        except Exception as e:
            print(f"Error generating key for pattern {pattern}: {e}")
            return pattern
    
    def parse_key(self, key: str) -> Optional[Dict[str, Any]]:
        """Parse a cache key to extract metadata"""
        with self.lock:
            return self.key_metadata.get(key)
    
    def get_keys_by_pattern(self, pattern: str) -> List[str]:
        """Get all keys matching a pattern"""
        with self.lock:
            matching_keys = []
            for key, metadata in self.key_metadata.items():
                if metadata.get('pattern') == pattern:
                    matching_keys.append(key)
            return matching_keys
    
    def cleanup_expired_metadata(self, hours: int = 24):
        """Clean up expired key metadata"""
        with self.lock:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            expired_keys = [
                key for key, metadata in self.key_metadata.items()
                if metadata.get('created_at', datetime.utcnow()) < cutoff_time
            ]
            
            for key in expired_keys:
                del self.key_metadata[key]
            
            print(f"Cleaned up {len(expired_keys)} expired key metadata entries")


class CacheUtils:
    """General cache utility functions"""
    
    @staticmethod
    def serialize_value(value: Any) -> str:
        """Serialize a value for cache storage"""
        try:
            if isinstance(value, (str, int, float, bool)):
                return str(value)
            elif isinstance(value, (dict, list, tuple)):
                return json.dumps(value)
            elif hasattr(value, 'to_dict'):
                return json.dumps(value.to_dict())
            else:
                return str(value)
        except Exception as e:
            print(f"Error serializing value: {e}")
            return str(value)
    
    @staticmethod
    def deserialize_value(value: str, default_type: type = str) -> Any:
        """Deserialize a value from cache storage"""
        try:
            if default_type == str:
                return value
            elif default_type == int:
                return int(value)
            elif default_type == float:
                return float(value)
            elif default_type == bool:
                return value.lower() in ('true', '1', 'yes', 'on')
            elif default_type == dict:
                return json.loads(value)
            elif default_type == list:
                return json.loads(value)
            else:
                return value
        except Exception as e:
            print(f"Error deserializing value: {e}")
            return value
    
    @staticmethod
    def calculate_key_hash(key: str) -> str:
        """Calculate hash for a cache key"""
        return hashlib.md5(key.encode()).hexdigest()
    
    @staticmethod
    def validate_key(key: str) -> bool:
        """Validate cache key format"""
        if not key:
            return False
        
        if len(key) > 250:  # Redis key length limit
            return False
        
        # Check for invalid characters
        invalid_chars = ['\x00', '\x01', '\x02', '\x03', '\x04', '\x05', '\x06', '\x07', '\x08', '\x09', '\x0a', '\x0b', '\x0c', '\x0d', '\x0e', '\x0f']
        for char in invalid_chars:
            if char in key:
                return False
        
        return True
    
    @staticmethod
    def estimate_size(value: Any) -> int:
        """Estimate size of a value in bytes"""
        try:
            if isinstance(value, str):
                return len(value.encode('utf-8'))
            elif isinstance(value, (int, float)):
                return 8  # Approximate size
            elif isinstance(value, bool):
                return 1
            elif isinstance(value, (dict, list, tuple)):
                return len(json.dumps(value).encode('utf-8'))
            else:
                return len(str(value).encode('utf-8'))
        except Exception:
            return 100  # Default estimate
    
    @staticmethod
    def get_cache_stats(redis_client) -> Dict[str, Any]:
        """Get cache statistics from Redis client"""
        try:
            info = redis_client.info()
            
            return {
                'used_memory': info.get('used_memory', 0),
                'used_memory_human': info.get('used_memory_human', '0B'),
                'used_memory_rss': info.get('used_memory_rss', 0),
                'used_memory_peak': info.get('used_memory_peak', 0),
                'used_memory_peak_human': info.get('used_memory_peak_human', '0B'),
                'total_commands_processed': info.get('total_commands_processed', 0),
                'instantaneous_ops_per_sec': info.get('instantaneous_ops_per_sec', 0),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
                'hit_rate': info.get('keyspace_hits', 0) / max(info.get('keyspace_hits', 0) + info.get('keyspace_misses', 0), 1),
                'connected_clients': info.get('connected_clients', 0),
                'total_keys_received': info.get('total_keys_received', 0),
                'total_expires': info.get('total_expires', 0),
                'expired_keys': info.get('expired_keys', 0),
                'evicted_keys': info.get('evicted_keys', 0),
                'keyspace': info.get('keyspace', {})
            }
        except Exception as e:
            print(f"Error getting cache stats: {e}")
            return {}


# Global instances
cache_sharding = CacheSharding()
cache_replication = CacheReplication()
cache_consistency_checker = CacheConsistencyChecker()
cache_performance_monitor = CachePerformanceMonitor()
cache_key_manager = CacheKeyManager()
