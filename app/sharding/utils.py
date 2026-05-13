"""
Database Sharding Utilities

Utility functions and helpers for database sharding, shard management,
cross-shard queries, shard failover, and load balancing.
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

from app.sharding.service import get_database_sharding_service


class ShardingStrategy(Enum):
    """Sharding strategies for database sharding"""
    HASH = "hash"
    RANGE = "range"
    DIRECTORY = "directory"
    CONSISTENT_HASH = "consistent_hash"


class ShardStatus(Enum):
    """Shard status types"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    ERROR = "error"


class FailoverStrategy(Enum):
    """Failover strategies"""
    AUTOMATIC = "automatic"
    MANUAL = "manual"
    SCHEDULED = "scheduled"


@dataclass
class ShardInfo:
    """Shard information structure"""
    shard_id: str
    shard_name: str
    host: str
    port: int
    database: str
    username: str
    status: ShardStatus
    weight: int
    priority: int
    range_start: Optional[str] = None
    range_end: Optional[str] = None


@dataclass
class QueryPlan:
    """Query execution plan for cross-shard queries"""
    query_id: str
    target_shards: List[str]
    execution_strategy: str
    estimated_time_ms: float
    optimization_suggestions: List[str]


class ShardSelector:
    """Shard selector for intelligent shard routing"""
    
    def __init__(self):
        self.sharding_strategies = {
            ShardingStrategy.HASH: self._hash_sharding,
            ShardingStrategy.RANGE: self._range_sharding,
            ShardingStrategy.DIRECTORY: self._directory_sharding,
            ShardingStrategy.CONSISTENT_HASH: self._consistent_hash_sharding
        }
        self.shard_directory = {}  # For directory-based sharding
        self.lock = threading.Lock()
    
    def select_shard(self, shards: List[ShardInfo], sharding_key: str, sharding_strategy: ShardingStrategy,
                     shard_value: Any = None) -> Optional[ShardInfo]:
        """Select shard based on sharding strategy"""
        if not shards:
            return None
        
        strategy_func = self.sharding_strategies.get(sharding_strategy)
        if strategy_func:
            return strategy_func(shards, sharding_key, shard_value)
        else:
            return shards[0]
    
    def _hash_sharding(self, shards: List[ShardInfo], sharding_key: str, shard_value: Any) -> ShardInfo:
        """Hash-based sharding"""
        try:
            # Calculate hash value
            if shard_value is None:
                hash_value = hash(sharding_key)
            else:
                hash_value = hash(str(shard_value))
            
            # Select shard by hash
            shard_index = hash_value % len(shards)
            return shards[shard_index]
            
        except Exception as e:
            print(f"Error in hash sharding: {e}")
            return shards[0]
    
    def _range_sharding(self, shards: List[ShardInfo], sharding_key: str, shard_value: Any) -> ShardInfo:
        """Range-based sharding"""
        try:
            if shard_value is None:
                return shards[0]
            
            # Convert to string for comparison
            value_str = str(shard_value)
            
            # Find shard with matching range
            for shard in shards:
                if shard.range_start and shard.range_end:
                    if shard.range_start <= value_str <= shard.range_end:
                        return shard
            
            # Default to first shard if no range matches
            return shards[0]
            
        except Exception as e:
            print(f"Error in range sharding: {e}")
            return shards[0]
    
    def _directory_sharding(self, shards: List[ShardInfo], sharding_key: str, shard_value: Any) -> ShardInfo:
        """Directory-based sharding"""
        try:
            with self.lock:
                # Check directory for mapping
                if shard_value is not None:
                    key = str(shard_value)
                    if key in self.shard_directory:
                        shard_id = self.shard_directory[key]
                        for shard in shards:
                            if shard.shard_id == shard_id:
                                return shard
                
                # Default to hash sharding if no directory entry
                return self._hash_sharding(shards, sharding_key, shard_value)
                
        except Exception as e:
            print(f"Error in directory sharding: {e}")
            return shards[0]
    
    def _consistent_hash_sharding(self, shards: List[ShardInfo], sharding_key: str, shard_value: Any) -> ShardInfo:
        """Consistent hash-based sharding"""
        try:
            # Simplified consistent hashing
            if shard_value is None:
                hash_value = hash(sharding_key)
            else:
                hash_value = hash(str(shard_value))
            
            # Create hash ring
            hash_ring = {}
            for i, shard in enumerate(shards):
                ring_position = hash(f"{shard.shard_id}_{i}") % 1000
                hash_ring[ring_position] = shard
            
            # Find appropriate shard
            if not hash_ring:
                return shards[0]
            
            sorted_positions = sorted(hash_ring.keys())
            target_position = hash_value % 1000
            
            # Find the first position >= target
            for position in sorted_positions:
                if position >= target_position:
                    return hash_ring[position]
            
            # Wrap around to first position
            return hash_ring[sorted_positions[0]]
            
        except Exception as e:
            print(f"Error in consistent hash sharding: {e}")
            return shards[0]
    
    def update_directory(self, key: str, shard_id: str):
        """Update directory mapping"""
        with self.lock:
            self.shard_directory[key] = shard_id
    
    def remove_from_directory(self, key: str):
        """Remove key from directory"""
        with self.lock:
            if key in self.shard_directory:
                del self.shard_directory[key]


class QueryPlanner:
    """Query planner for cross-shard queries"""
    
    def __init__(self):
        self.optimization_rules = {
            'minimize_shards': True,
            'parallel_execution': True,
            'result_aggregation': True,
            'cache_results': True
        }
    
    def plan_query(self, query_text: str, cluster_id: int, target_shards: List[str] = None,
                  execution_strategy: str = 'parallel') -> QueryPlan:
        """Plan query execution"""
        try:
            # Generate query ID
            query_id = hashlib.md5(f"{query_text}_{cluster_id}_{time.time()}".encode()).hexdigest()
            
            # Determine target shards
            if target_shards:
                selected_shards = target_shards
            else:
                selected_shards = self._determine_target_shards(cluster_id, query_text)
            
            # Estimate execution time
            estimated_time = self._estimate_execution_time(query_text, selected_shards, execution_strategy)
            
            # Generate optimization suggestions
            suggestions = self._generate_optimization_suggestions(query_text, selected_shards)
            
            return QueryPlan(
                query_id=query_id,
                target_shards=selected_shards,
                execution_strategy=execution_strategy,
                estimated_time_ms=estimated_time,
                optimization_suggestions=suggestions
            )
            
        except Exception as e:
            print(f"Error planning query: {e}")
            return QueryPlan(
                query_id=hashlib.md5(query_text.encode()).hexdigest(),
                target_shards=[],
                execution_strategy='parallel',
                estimated_time_ms=0,
                optimization_suggestions=[]
            )
    
    def _determine_target_shards(self, cluster_id: int, query_text: str) -> List[str]:
        """Determine target shards for query"""
        try:
            # This would analyze the query to determine which shards are needed
            # For now, return all shards
            sharding_service = get_database_sharding_service()
            shards = Shard.get_active_shards(cluster_id)
            return [shard.shard_id for shard in shards]
            
        except Exception as e:
            print(f"Error determining target shards: {e}")
            return []
    
    def _estimate_execution_time(self, query_text: str, target_shards: List[str], execution_strategy: str) -> float:
        """Estimate query execution time"""
        try:
            # Base time per shard
            base_time_per_shard = 100  # milliseconds
            
            # Adjust based on execution strategy
            if execution_strategy == 'parallel':
                total_time = base_time_per_shard
            elif execution_strategy == 'sequential':
                total_time = base_time_per_shard * len(target_shards)
            else:  # hybrid
                total_time = base_time_per_shard * (1 + len(target_shards) * 0.5)
            
            # Adjust based on query complexity
            query_complexity = self._calculate_query_complexity(query_text)
            total_time *= query_complexity
            
            return total_time
            
        except Exception as e:
            print(f"Error estimating execution time: {e}")
            return 1000.0  # Default to 1 second
    
    def _calculate_query_complexity(self, query_text: str) -> float:
        """Calculate query complexity factor"""
        complexity = 1.0
        
        # Adjust based on query type
        query_lower = query_text.lower()
        
        if 'select' in query_lower:
            if 'join' in query_lower:
                complexity *= 2.0
            if 'group by' in query_lower:
                complexity *= 1.5
            if 'order by' in query_lower:
                complexity *= 1.3
            if 'limit' in query_lower:
                complexity *= 0.8
        
        elif 'insert' in query_lower:
            complexity *= 1.2
        
        elif 'update' in query_lower:
            complexity *= 1.3
            if 'where' in query_lower:
                complexity *= 1.2
        
        elif 'delete' in query_lower:
            complexity *= 1.4
            if 'where' in query_lower:
                complexity *= 1.2
        
        return complexity
    
    def _generate_optimization_suggestions(self, query_text: str, target_shards: List[str]) -> List[str]:
        """Generate optimization suggestions"""
        suggestions = []
        
        # Shard count optimization
        if len(target_shards) > 10:
            suggestions.append("Consider adding shard filters to reduce target shards")
        
        # Query optimization
        query_lower = query_text.lower()
        if 'select *' in query_lower:
            suggestions.append("Specify only required columns instead of SELECT *")
        
        if 'where' not in query_lower and 'select' in query_lower:
            suggestions.append("Add WHERE clause to filter results")
        
        if 'limit' not in query_lower and 'select' in query_lower:
            suggestions.append("Add LIMIT clause to limit result set")
        
        # Execution strategy optimization
        if len(target_shards) == 1:
            suggestions.append("Consider using single-shard query for better performance")
        
        return suggestions


class FailoverManager:
    """Failover manager for shard failover"""
    
    def __init__(self):
        self.failover_strategies = {
            FailoverStrategy.AUTOMATIC: self._automatic_failover,
            FailoverStrategy.MANUAL: self._manual_failover,
            FailoverStrategy.SCHEDULED: self._scheduled_failover
        }
        self.failover_history = deque(maxlen=1000)
        self.lock = threading.Lock()
    
    def execute_failover(self, cluster_id: int, failover_type: FailoverStrategy, failover_reason: str,
                       failed_shard_id: str = None, promoted_shard_id: str = None,
                       failover_config: Dict[str, Any] = None) -> bool:
        """Execute failover"""
        try:
            strategy_func = self.failover_strategies.get(failover_type)
            if strategy_func:
                return strategy_func(cluster_id, failover_reason, failed_shard_id, promoted_shard_id, failover_config)
            else:
                return False
                
        except Exception as e:
            print(f"Error executing failover: {e}")
            return False
    
    def _automatic_failover(self, cluster_id: int, failover_reason: str, failed_shard_id: str = None,
                          promoted_shard_id: str = None, failover_config: Dict[str, Any] = None) -> bool:
        """Execute automatic failover"""
        try:
            # Get cluster and shards
            from app.sharding.models import ShardCluster, Shard
            
            cluster = ShardCluster.query.get(cluster_id)
            if not cluster:
                return False
            
            # Find failed shard
            failed_shard = None
            if failed_shard_id:
                failed_shard = Shard.query.get(failed_shard_id)
            
            if not failed_shard:
                return False
            
            # Find suitable replacement shard
            available_shards = Shard.query.filter(
                Shard.cluster_id == cluster_id,
                Shard.status == 'active',
                Shard.shard_id != failed_shard_id
            ).order_by(Shard.priority.asc()).all()
            
            if not available_shards:
                return False
            
            # Select best shard
            replacement_shard = available_shards[0]
            
            # Update failed shard status
            failed_shard.update_status('inactive', 'unhealthy', 'disconnected')
            
            # Record failover
            self._record_failover(cluster_id, failover_reason, failed_shard_id, replacement_shard.shard_id)
            
            return True
            
        except Exception as e:
            print(f"Error in automatic failover: {e}")
            return False
    
    def _manual_failover(self, cluster_id: int, failover_reason: str, failed_shard_id: str = None,
                       promoted_shard_id: str = None, failover_config: Dict[str, Any] = None) -> bool:
        """Execute manual failover"""
        try:
            # Manual failover requires specific promoted shard
            if not promoted_shard_id:
                return False
            
            from app.sharding.models import Shard
            
            promoted_shard = Shard.query.get(promoted_shard_id)
            if not promoted_shard:
                return False
            
            # Update failed shard if specified
            if failed_shard_id:
                failed_shard = Shard.query.get(failed_shard_id)
                if failed_shard:
                    failed_shard.update_status('inactive', 'unhealthy', 'disconnected')
            
            # Record failover
            self._record_failover(cluster_id, failover_reason, failed_shard_id, promoted_shard_id)
            
            return True
            
        except Exception as e:
            print(f"Error in manual failover: {e}")
            return False
    
    def _scheduled_failover(self, cluster_id: int, failover_reason: str, failed_shard_id: str = None,
                          promoted_shard_id: str = None, failover_config: Dict[str, Any] = None) -> bool:
        """Execute scheduled failover"""
        try:
            # Scheduled failover is similar to manual but with preparation
            return self._manual_failover(cluster_id, failover_reason, failed_shard_id, promoted_shard_id, failover_config)
            
        except Exception as e:
            print(f"Error in scheduled failover: {e}")
            return False
    
    def _record_failover(self, cluster_id: int, reason: str, failed_shard_id: str, promoted_shard_id: str):
        """Record failover event"""
        with self.lock:
            failover_event = {
                'timestamp': datetime.utcnow().isoformat(),
                'cluster_id': cluster_id,
                'reason': reason,
                'failed_shard_id': failed_shard_id,
                'promoted_shard_id': promoted_shard_id
            }
            self.failover_history.append(failover_event)
    
    def get_failover_history(self, cluster_id: int = None, hours: int = 24) -> List[Dict[str, Any]]:
        """Get failover history"""
        with self.lock:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            history = []
            for event in self.failover_history:
                event_time = datetime.fromisoformat(event['timestamp'])
                if event_time >= cutoff_time:
                    if cluster_id is None or event['cluster_id'] == cluster_id:
                        history.append(event)
            
            return sorted(history, key=lambda x: x['timestamp'], reverse=True)


class ConnectionPool:
    """Connection pool for database shards"""
    
    def __init__(self):
        self.pools = {}  # shard_id -> connection pool
        self.pool_configs = {}  # shard_id -> pool configuration
        self.lock = threading.Lock()
    
    def create_pool(self, shard_id: str, host: str, port: int, database: str, username: str,
                   password: str, min_connections: int = 1, max_connections: int = 10,
                   connection_timeout: int = 30) -> bool:
        """Create connection pool for a shard"""
        try:
            with self.lock:
                # This would create an actual database connection pool
                # For now, simulate pool creation
                pool_info = {
                    'shard_id': shard_id,
                    'host': host,
                    'port': port,
                    'database': database,
                    'username': username,
                    'min_connections': min_connections,
                    'max_connections': max_connections,
                    'connection_timeout': connection_timeout,
                    'created_at': datetime.utcnow(),
                    'active_connections': 0,
                    'total_connections': 0
                }
                
                self.pools[shard_id] = pool_info
                return True
                
        except Exception as e:
            print(f"Error creating connection pool for shard {shard_id}: {e}")
            return False
    
    def get_connection(self, shard_id: str):
        """Get connection from pool"""
        try:
            with self.lock:
                if shard_id not in self.pools:
                    return None
                
                pool = self.pools[shard_id]
                
                # This would get an actual connection from the pool
                # For now, simulate connection retrieval
                if pool['active_connections'] < pool['max_connections']:
                    pool['active_connections'] += 1
                    return f"connection_{shard_id}_{pool['active_connections']}"
                else:
                    return None
                    
        except Exception as e:
            print(f"Error getting connection from pool {shard_id}: {e}")
            return None
    
    def release_connection(self, shard_id: str, connection):
        """Release connection back to pool"""
        try:
            with self.lock:
                if shard_id in self.pools:
                    pool = self.pools[shard_id]
                    if pool['active_connections'] > 0:
                        pool['active_connections'] -= 1
                        
        except Exception as e:
            print(f"Error releasing connection to pool {shard_id}: {e}")
    
    def get_pool_stats(self, shard_id: str) -> Dict[str, Any]:
        """Get pool statistics"""
        with self.lock:
            if shard_id not in self.pools:
                return {}
            
            pool = self.pools[shard_id]
            return {
                'shard_id': shard_id,
                'min_connections': pool['min_connections'],
                'max_connections': pool['max_connections'],
                'active_connections': pool['active_connections'],
                'total_connections': pool['total_connections'],
                'utilization': pool['active_connections'] / pool['max_connections']
            }


class ShardingUtils:
    """General sharding utility functions"""
    
    @staticmethod
    def calculate_shard_hash(shard_key: str, shard_count: int) -> int:
        """Calculate shard hash for a key"""
        try:
            hash_value = hash(shard_key)
            return hash_value % shard_count
        except Exception:
            return 0
    
    @staticmethod
    def validate_shard_config(config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate shard configuration"""
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Check required fields
        required_fields = ['host', 'port', 'database', 'username']
        for field in required_fields:
            if field not in config:
                validation_result['errors'].append(f"Missing required field: {field}")
                validation_result['valid'] = False
        
        # Check port range
        if 'port' in config:
            port = config['port']
            if not isinstance(port, int) or port < 1 or port > 65535:
                validation_result['errors'].append("Port must be an integer between 1 and 65535")
                validation_result['valid'] = False
        
        # Check connection pool settings
        if 'min_connections' in config:
            min_conn = config['min_connections']
            if not isinstance(min_conn, int) or min_conn < 0:
                validation_result['errors'].append("min_connections must be a non-negative integer")
                validation_result['valid'] = False
        
        if 'max_connections' in config:
            max_conn = config['max_connections']
            if not isinstance(max_conn, int) or max_conn < 1:
                validation_result['errors'].append("max_connections must be a positive integer")
                validation_result['valid'] = False
        
        # Check min/max consistency
        if 'min_connections' in config and 'max_connections' in config:
            if config['min_connections'] > config['max_connections']:
                validation_result['errors'].append("min_connections cannot be greater than max_connections")
                validation_result['valid'] = False
        
        return validation_result
    
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
    def generate_shard_name(base_name: str, shard_index: int) -> str:
        """Generate shard name"""
        return f"{base_name}_shard_{shard_index:03d}"
    
    @staticmethod
    def parse_connection_string(connection_string: str) -> Dict[str, Any]:
        """Parse database connection string"""
        try:
            # Simple connection string parsing: host:port/database
            parts = connection_string.split('/')
            if len(parts) != 2:
                return {}
            
            host_port = parts[0]
            database = parts[1]
            
            host_parts = host_port.split(':')
            if len(host_parts) != 2:
                return {}
            
            host = host_parts[0]
            port = int(host_parts[1])
            
            return {
                'host': host,
                'port': port,
                'database': database
            }
            
        except Exception:
            return {}
    
    @staticmethod
    def format_shard_metrics(shards: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Format shard metrics for display"""
        if not shards:
            return {}
        
        total_connections = sum(s.get('total_connections', 0) for s in shards)
        active_connections = sum(s.get('active_connections', 0) for s in shards)
        total_records = sum(s.get('total_records', 0) for s in shards)
        total_size = sum(s.get('data_size_bytes', 0) for s in shards)
        
        return {
            'shard_count': len(shards),
            'total_connections': total_connections,
            'active_connections': active_connections,
            'connection_utilization': active_connections / max(total_connections, 1),
            'total_records': total_records,
            'total_size_bytes': total_size,
            'avg_records_per_shard': total_records / len(shards) if shards else 0,
            'avg_size_per_shard': total_size / len(shards) if shards else 0
        }


# Global instances
shard_selector = ShardSelector()
query_planner = QueryPlanner()
failover_manager = FailoverManager()
connection_pool = ConnectionPool()
sharding_utils = ShardingUtils()
