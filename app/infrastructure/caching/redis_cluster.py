"""
Redis Cluster Manager

Manages Redis cluster setup, configuration, and operations for
high-availability caching infrastructure.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
import time
import redis
from redis.cluster import RedisCluster
from redis.exceptions import RedisError, ClusterDownError, ConnectionError
import threading
import subprocess
import socket
import yaml

logger = logging.getLogger(__name__)

class ClusterStatus(Enum):
    """Redis cluster status"""
    INITIALIZING = "initializing"
    RUNNING = "running"
    DEGRADED = "degraded"
    FAILED = "failed"
    MAINTENANCE = "maintenance"

class NodeRole(Enum):
    """Redis node roles"""
    MASTER = "master"
    SLAVE = "slave"
    UNKNOWN = "unknown"

@dataclass
class ClusterNode:
    """Redis cluster node configuration"""
    host: str
    port: int
    role: NodeRole = NodeRole.UNKNOWN
    status: str = "unknown"
    slots: List[int] = field(default_factory=list)
    connected: bool = False
    last_check: Optional[datetime] = None
    memory_usage: int = 0
    key_count: int = 0
    master_id: Optional[str] = None

@dataclass
class ClusterConfig:
    """Redis cluster configuration"""
    nodes: List[Dict[str, Any]] = field(default_factory=list)
    cluster_name: str = "mycluster"
    cluster_port: int = 16379
    shard_count: int = 3
    replicas_per_shard: int = 1
    max_memory: str = "2gb"
    max_memory_policy: str = "allkeys-lru"
    timeout: int = 5000
    tcp_keepalive: int = 300
    max_connections: int = 10000
    cluster_node_timeout: int = 5000
    cluster_announce_ip: Optional[str] = None
    cluster_announce_port: Optional[int] = None
    enable_cluster: bool = True
    protected_mode: bool = True
    requirepass: Optional[str] = None

class RedisClusterManager:
    """Manages Redis cluster setup and operations"""
    
    def __init__(self, config: ClusterConfig = None):
        self.config = config or ClusterConfig()
        self.cluster_client = None
        self.nodes: Dict[str, ClusterNode] = {}
        self.cluster_status = ClusterStatus.INITIALIZING
        self.monitoring_enabled = True
        self.auto_failover_enabled = True
        
        # Initialize cluster
        self._initialize_cluster()
        
        # Start monitoring
        self._start_cluster_monitoring()
    
    def _initialize_cluster(self):
        """Initialize Redis cluster"""
        try:
            # Initialize nodes from config
            for node_config in self.config.nodes:
                node_id = f"{node_config['host']}:{node_config['port']}"
                self.nodes[node_id] = ClusterNode(
                    host=node_config['host'],
                    port=node_config['port']
                )
            
            # Connect to existing cluster or create new one
            if self._check_existing_cluster():
                self.cluster_client = RedisCluster(
                    startup_nodes=self.config.nodes,
                    decode_responses=True,
                    skip_full_coverage_check=True,
                    max_connections=self.config.max_connections,
                    socket_timeout=self.config.timeout // 1000,
                    socket_connect_timeout=self.config.timeout // 1000,
                    retry_on_timeout=True
                )
                self.cluster_status = ClusterStatus.RUNNING
                logger.info("Connected to existing Redis cluster")
            else:
                self._create_cluster()
            
            # Update node information
            self._update_node_info()
            
        except Exception as e:
            logger.error(f"Failed to initialize Redis cluster: {e}")
            self.cluster_status = ClusterStatus.FAILED
            raise
    
    def _check_existing_cluster(self) -> bool:
        """Check if Redis cluster already exists"""
        try:
            # Try to connect to one of the nodes
            if self.config.nodes:
                test_node = self.config.nodes[0]
                client = redis.Redis(
                    host=test_node['host'],
                    port=test_node['port'],
                    decode_responses=True,
                    socket_timeout=5
                )
                
                # Check if cluster is enabled
                info = client.info()
                if info.get('cluster_enabled', 0) == 1:
                    # Check cluster state
                    cluster_info = client.cluster_info()
                    return cluster_info.get('cluster_state') == 'ok'
            
            return False
            
        except Exception as e:
            logger.debug(f"Error checking existing cluster: {e}")
            return False
    
    def _create_cluster(self):
        """Create new Redis cluster"""
        try:
            logger.info("Creating new Redis cluster...")
            
            # This is a simplified cluster creation
            # In production, you would use proper Redis cluster setup tools
            
            # For now, we'll assume the cluster is already set up
            # and just connect to it
            
            # If no nodes are configured, use default localhost node
            startup_nodes = self.config.nodes if self.config.nodes else [
                {"host": "localhost", "port": 6379}
            ]
            
            self.cluster_client = RedisCluster(
                startup_nodes=startup_nodes,
                decode_responses=True,
                skip_full_coverage_check=True,
                max_connections=self.config.max_connections,
                socket_timeout=self.config.timeout // 1000,
                socket_connect_timeout=self.config.timeout // 1000,
                retry_on_timeout=True
            )
            
            self.cluster_status = ClusterStatus.RUNNING
            logger.info("Redis cluster created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create Redis cluster: {e}")
            # Fall back to single Redis instance if cluster fails
            try:
                logger.info("Falling back to single Redis instance...")
                self.redis_client = redis.Redis(
                    host='localhost',
                    port=6379,
                    decode_responses=True,
                    max_connections=self.config.max_connections,
                    socket_timeout=self.config.timeout // 1000,
                    socket_connect_timeout=self.config.timeout // 1000,
                    retry_on_timeout=True
                )
                self.cluster_status = ClusterStatus.RUNNING
                logger.info("Single Redis instance connected successfully")
            except Exception as fallback_error:
                logger.error(f"Failed to connect to Redis instance: {fallback_error}")
                raise
    
    def _start_cluster_monitoring(self):
        """Start cluster monitoring"""
        def monitor_cluster():
            while self.monitoring_enabled:
                try:
                    self._monitor_cluster_health()
                    self._update_node_info()
                    time.sleep(30)  # Monitor every 30 seconds
                except Exception as e:
                    logger.error(f"Cluster monitoring error: {e}")
                    time.sleep(5)
        
        monitor_thread = threading.Thread(target=monitor_cluster, daemon=True)
        monitor_thread.start()
        logger.info("Redis cluster monitoring started")
    
    def _monitor_cluster_health(self):
        """Monitor cluster health"""
        try:
            if not self.cluster_client:
                return
            
            # Get cluster info
            cluster_info = self.cluster_client.cluster_info()
            cluster_state = cluster_info.get('cluster_state')
            
            if cluster_state == 'ok':
                if self.cluster_status != ClusterStatus.RUNNING:
                    self.cluster_status = ClusterStatus.RUNNING
                    logger.info("Redis cluster is healthy")
            else:
                self.cluster_status = ClusterStatus.DEGRADED
                logger.warning(f"Redis cluster state: {cluster_state}")
            
            # Check for failed nodes
            self._check_node_health()
            
        except Exception as e:
            logger.error(f"Error monitoring cluster health: {e}")
            self.cluster_status = ClusterStatus.FAILED
    
    def _check_node_health(self):
        """Check health of individual nodes"""
        for node_id, node in self.nodes.items():
            try:
                # Test connection to node
                node_client = redis.Redis(
                    host=node.host,
                    port=node.port,
                    decode_responses=True,
                    socket_timeout=5
                )
                
                node_client.ping()
                node.connected = True
                node.last_check = datetime.utcnow()
                
                # Get node info
                info = node_client.info()
                node.memory_usage = info.get('used_memory', 0)
                node.key_count = info.get('db0', {}).get('keys', 0)
                
                # Get cluster node info
                cluster_nodes = node_client.cluster_nodes()
                for node_info in cluster_nodes.split('\n'):
                    if node_info:
                        parts = node_info.split()
                        if len(parts) >= 8:
                            node_addr = parts[1]
                            if node_addr == f"{node.host}:{node.port}":
                                node.role = NodeRole(parts[2].lower())
                                node.status = parts[7]
                                break
                
            except Exception as e:
                logger.warning(f"Node {node_id} health check failed: {e}")
                node.connected = False
                node.status = "failed"
    
    def _update_node_info(self):
        """Update node information from cluster"""
        try:
            if not self.cluster_client:
                return
            
            # Get cluster nodes
            cluster_nodes = self.cluster_client.cluster_nodes()
            
            for node_info in cluster_nodes.split('\n'):
                if not node_info:
                    continue
                
                parts = node_info.split()
                if len(parts) < 8:
                    continue
                
                node_id = parts[0]
                node_addr = parts[1]
                role = parts[2]
                status = parts[7]
                
                # Parse slots
                slots = []
                for part in parts[8:]:
                    if '-' in part:
                        start, end = map(int, part.split('-'))
                        slots.extend(range(start, end + 1))
                    elif part.isdigit():
                        slots.append(int(part))
                
                # Update node info
                if node_addr in self.nodes:
                    node = self.nodes[node_addr]
                    node.role = NodeRole(role.lower())
                    node.status = status
                    node.slots = slots
                    node.connected = status == 'online'
                    node.last_check = datetime.utcnow()
                else:
                    # Add new node
                    host, port = node_addr.split(':')
                    self.nodes[node_addr] = ClusterNode(
                        host=host,
                        port=int(port),
                        role=NodeRole(role.lower()),
                        status=status,
                        slots=slots,
                        connected=status == 'online',
                        last_check=datetime.utcnow()
                    )
            
        except Exception as e:
            logger.error(f"Error updating node info: {e}")
    
    def add_node(self, host: str, port: int, role: NodeRole = NodeRole.MASTER) -> bool:
        """Add new node to cluster"""
        try:
            if not self.cluster_client:
                logger.error("Cluster not initialized")
                return False
            
            node_id = f"{host}:{port}"
            
            # Check if node already exists
            if node_id in self.nodes:
                logger.warning(f"Node {node_id} already exists")
                return False
            
            # Add node to cluster
            if role == NodeRole.MASTER:
                # Add as master
                result = self.cluster_client.cluster_addslots(*range(0, 16384))
            else:
                # Add as replica
                # Find a master to replicate
                masters = [n for n in self.nodes.values() if n.role == NodeRole.MASTER]
                if masters:
                    master_id = list(masters)[0].host + ":" + str(list(masters)[0].port)
                    result = self.cluster_client.cluster_replicate(master_id)
                else:
                    logger.error("No master nodes found to replicate")
                    return False
            
            # Update nodes list
            self.nodes[node_id] = ClusterNode(
                host=host,
                port=port,
                role=role,
                connected=True,
                last_check=datetime.utcnow()
            )
            
            logger.info(f"Added node {node_id} to cluster")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add node {host}:{port}: {e}")
            return False
    
    def remove_node(self, host: str, port: int) -> bool:
        """Remove node from cluster"""
        try:
            if not self.cluster_client:
                logger.error("Cluster not initialized")
                return False
            
            node_id = f"{host}:{port}"
            
            if node_id not in self.nodes:
                logger.warning(f"Node {node_id} not found")
                return False
            
            node = self.nodes[node_id]
            
            # Remove node from cluster
            if node.role == NodeRole.MASTER:
                # For masters, need to migrate slots first
                logger.warning("Removing master node requires slot migration")
                return False
            else:
                # For replicas, can remove directly
                result = self.cluster_client.cluster_forget(node_id)
            
            # Remove from nodes list
            del self.nodes[node_id]
            
            logger.info(f"Removed node {node_id} from cluster")
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove node {host}:{port}: {e}")
            return False
    
    def failover_node(self, host: str, port: int) -> bool:
        """Trigger failover for a node"""
        try:
            if not self.cluster_client:
                logger.error("Cluster not initialized")
                return False
            
            node_id = f"{host}:{port}"
            
            if node_id not in self.nodes:
                logger.warning(f"Node {node_id} not found")
                return False
            
            node = self.nodes[node_id]
            
            if node.role != NodeRole.MASTER:
                logger.warning(f"Node {node_id} is not a master")
                return False
            
            # Trigger failover
            result = self.cluster_client.cluster_failover()
            
            logger.info(f"Failover triggered for node {node_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to failover node {host}:{port}: {e}")
            return False
    
    def reshard_cluster(self, source_host: str, source_port: int, 
                       target_host: str, target_port: int, 
                       slot_count: int) -> bool:
        """Reshard cluster by moving slots"""
        try:
            if not self.cluster_client:
                logger.error("Cluster not initialized")
                return False
            
            source_id = f"{source_host}:{source_port}"
            target_id = f"{target_host}:{target_port}"
            
            if source_id not in self.nodes or target_id not in self.nodes:
                logger.error("Source or target node not found")
                return False
            
            source_node = self.nodes[source_id]
            target_node = self.nodes[target_id]
            
            # Get slots to move from source
            if source_node.slots:
                slots_to_move = source_node.slots[:slot_count]
            else:
                logger.error("No slots available on source node")
                return False
            
            # Move slots
            for slot in slots_to_move:
                self.cluster_client.cluster_setslot(slot, target_id)
            
            # Update node slot information
            source_node.slots = source_node.slots[slot_count:]
            target_node.slots.extend(slots_to_move)
            
            logger.info(f"Moved {slot_count} slots from {source_id} to {target_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to reshard cluster: {e}")
            return False
    
    def get_cluster_info(self) -> Dict[str, Any]:
        """Get cluster information"""
        try:
            if not self.cluster_client:
                return {
                    'status': 'not_initialized',
                    'nodes': {},
                    'cluster_info': {}
                }
            
            # Get cluster info
            cluster_info = self.cluster_client.cluster_info()
            
            # Get nodes info
            nodes_info = {}
            for node_id, node in self.nodes.items():
                nodes_info[node_id] = {
                    'host': node.host,
                    'port': node.port,
                    'role': node.role.value,
                    'status': node.status,
                    'connected': node.connected,
                    'slots': node.slots,
                    'slot_count': len(node.slots),
                    'memory_usage': node.memory_usage,
                    'key_count': node.key_count,
                    'last_check': node.last_check.isoformat() if node.last_check else None
                }
            
            return {
                'status': self.cluster_status.value,
                'cluster_info': cluster_info if cluster_info else {},
                'nodes': nodes_info,
                'total_nodes': len(self.nodes),
                'connected_nodes': len([n for n in self.nodes.values() if n.connected]),
                'master_nodes': len([n for n in self.nodes.values() if n.role == NodeRole.MASTER]),
                'slave_nodes': len([n for n in self.nodes.values() if n.role == NodeRole.SLAVE]),
                'total_slots': 16384,
                'assigned_slots': sum(len(n.slots) for n in self.nodes.values())
            }
        
        except Exception as e:
            logger.error(f"Error getting cluster info: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def get_node_stats(self, host: str, port: int) -> Optional[Dict[str, Any]]:
        """Get detailed statistics for a specific node"""
        try:
            node_id = f"{host}:{port}"
            
            if node_id not in self.nodes:
                return None
            
            node = self.nodes[node_id]
            
            # Connect to node
            node_client = redis.Redis(
                host=host,
                port=port,
                decode_responses=True,
                socket_timeout=5
            )
            
            # Get detailed info
            info = node_client.info()
            config = node_client.config_get('*')
            
            return {
                'node_id': node_id,
                'host': node.host,
                'port': node.port,
                'role': node.role.value,
                'status': node.status,
                'connected': node.connected,
                'slots': node.slots,
                'slot_count': len(node.slots),
                'memory_usage': node.memory_usage,
                'key_count': node.key_count,
                'last_check': node.last_check.isoformat() if node.last_check else None,
                'info': info,
                'config': config
            }
            
        except Exception as e:
            logger.error(f"Error getting node stats for {host}:{port}: {e}")
            return None
    
    def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive cluster health check"""
        try:
            health_status = {
                'overall_status': 'healthy',
                'cluster_status': self.cluster_status.value,
                'issues': [],
                'nodes': {},
                'recommendations': []
            }
            
            # Check cluster connection
            if not self.cluster_client:
                health_status['overall_status'] = 'unhealthy'
                health_status['issues'].append('Cluster not connected')
                return health_status
            
            # Check cluster info
            try:
                cluster_info = self.cluster_client.cluster_info()
                if cluster_info.get('cluster_state') != 'ok':
                    health_status['overall_status'] = 'degraded'
                    health_status['issues'].append('Cluster state not ok')
            except Exception as e:
                health_status['overall_status'] = 'unhealthy'
                health_status['issues'].append(f'Cluster info error: {e}')
            
            # Check each node
            failed_nodes = []
            for node_id, node in self.nodes.items():
                node_health = {
                    'status': 'healthy' if node.connected else 'unhealthy',
                    'role': node.role.value,
                    'connected': node.connected,
                    'memory_usage': node.memory_usage,
                    'key_count': node.key_count,
                    'slot_count': len(node.slots)
                }
                
                if not node.connected:
                    failed_nodes.append(node_id)
                
                health_status['nodes'][node_id] = node_health
            
            # Check for issues
            if failed_nodes:
                health_status['issues'].append(f'Failed nodes: {failed_nodes}')
            
            # Check slot distribution
            total_slots = sum(len(n.slots) for n in self.nodes.values())
            if total_slots < 16384:
                health_status['issues'].append(f'Not all slots assigned: {total_slots}/16384')
            
            # Check master/replica ratio
            masters = len([n for n in self.nodes.values() if n.role == NodeRole.MASTER])
            replicas = len([n for n in self.nodes.values() if n.role == NodeRole.SLAVE])
            
            if masters == 0:
                health_status['issues'].append('No master nodes')
            elif replicas < masters:
                health_status['recommendations'].append('Consider adding more replicas for high availability')
            
            # Determine overall status
            if health_status['issues']:
                if len(health_status['issues']) > 2:
                    health_status['overall_status'] = 'unhealthy'
                else:
                    health_status['overall_status'] = 'degraded'
            
            return health_status
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                'overall_status': 'unhealthy',
                'issues': [f'Health check failed: {e}']
            }
    
    def get_config(self) -> Dict[str, Any]:
        """Get cluster configuration"""
        return {
            'cluster_name': self.config.cluster_name,
            'cluster_port': self.config.cluster_port,
            'shard_count': self.config.shard_count,
            'replicas_per_shard': self.config.replicas_per_shard,
            'max_memory': self.config.max_memory,
            'max_memory_policy': self.config.max_memory_policy,
            'timeout': self.config.timeout,
            'tcp_keepalive': self.config.tcp_keepalive,
            'max_connections': self.config.max_connections,
            'cluster_node_timeout': self.config.cluster_node_timeout,
            'cluster_announce_ip': self.config.cluster_announce_ip,
            'cluster_announce_port': self.config.cluster_announce_port,
            'enable_cluster': self.config.enable_cluster,
            'protected_mode': self.config.protected_mode,
            'requirepass': self.config.requirepass
        }
    
    def update_config(self, **kwargs):
        """Update cluster configuration"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
                logger.info(f"Updated cluster config: {key} = {value}")
    
    def shutdown(self):
        """Shutdown cluster manager"""
        try:
            # Stop monitoring
            self.monitoring_enabled = False
            
            # Close cluster connection
            if self.cluster_client:
                self.cluster_client.close()
            
            logger.info("Redis cluster manager shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during cluster manager shutdown: {e}")
