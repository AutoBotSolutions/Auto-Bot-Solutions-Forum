"""
WebSocket Load Balancer

Advanced load balancing system for WebSocket connections with multiple
algorithms, health checking, and failover support.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
import time
import threading
import queue
import random
import hashlib
import socket
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

class LoadBalancingStrategy(Enum):
    """Load balancing strategies"""
    ROUND_ROBIN = "round_robin"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    LEAST_CONNECTIONS = "least_connections"
    LEAST_RESPONSE_TIME = "least_response_time"
    HASH_BASED = "hash_based"
    RANDOM = "random"

class NodeStatus(Enum):
    """Node status"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DRAINING = "draining"
    MAINTENANCE = "maintenance"

@dataclass
class WebSocketNode:
    """WebSocket server node"""
    node_id: str
    host: str
    port: int
    weight: int = 1
    status: NodeStatus = NodeStatus.HEALTHY
    active_connections: int = 0
    total_connections: int = 0
    avg_response_time: float = 0.0
    last_health_check: Optional[datetime] = None
    consecutive_failures: int = 0
    max_connections: int = 1000
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ConnectionInfo:
    """WebSocket connection information"""
    connection_id: str
    node_id: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    connected_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)

@dataclass
class LoadBalancerConfig:
    """Load balancer configuration"""
    strategy: LoadBalancingStrategy = LoadBalancingStrategy.ROUND_ROBIN
    health_check_interval: int = 30
    health_check_timeout: int = 5
    max_failures: int = 3
    recovery_timeout: int = 300
    enable_sticky_sessions: bool = True
    session_affinity_key: str = "user_id"
    enable_health_checks: bool = True
    enable_failover: bool = True
    enable_metrics: bool = True
    connection_timeout: int = 30
    retry_attempts: int = 3
    retry_delay: float = 1.0

class WebSocketLoadBalancer:
    """Advanced WebSocket load balancer"""
    
    def __init__(self, config: LoadBalancerConfig = None):
        self.config = config or LoadBalancerConfig()
        self.nodes: Dict[str, WebSocketNode] = {}
        self.connections: Dict[str, ConnectionInfo] = {}  # connection_id -> ConnectionInfo
        self.node_connections: Dict[str, Set[str]] = defaultdict(set)  # node_id -> connection_ids
        self.session_affinity: Dict[str, str] = {}  # session_key -> node_id
        
        # Load balancing state
        self.current_round_robin_index = 0
        self.connection_counter = 0
        
        # Health checking
        self.health_check_enabled = True
        self.health_check_thread = None
        
        # Metrics
        self.metrics = {
            'total_connections': 0,
            'active_connections': 0,
            'failed_connections': 0,
            'health_checks': 0,
            'failed_health_checks': 0,
            'balancing_decisions': 0,
            'failovers': 0
        }
        
        # Start health checking
        self._start_health_checking()
    
    def add_node(self, node_id: str, host: str, port: int, weight: int = 1, 
                 max_connections: int = 1000) -> bool:
        """Add a WebSocket server node"""
        try:
            if node_id in self.nodes:
                logger.warning(f"Node {node_id} already exists")
                return False
            
            node = WebSocketNode(
                node_id=node_id,
                host=host,
                port=port,
                weight=weight,
                max_connections=max_connections
            )
            
            self.nodes[node_id] = node
            logger.info(f"Added WebSocket node: {node_id} ({host}:{port})")
            return True
            
        except Exception as e:
            logger.error(f"Error adding node {node_id}: {e}")
            return False
    
    def remove_node(self, node_id: str) -> bool:
        """Remove a WebSocket server node"""
        try:
            if node_id not in self.nodes:
                logger.warning(f"Node {node_id} not found")
                return False
            
            node = self.nodes[node_id]
            
            # Check if node has active connections
            if node.active_connections > 0:
                logger.warning(f"Node {node_id} has {node.active_connections} active connections")
                # Mark as draining instead of removing
                node.status = NodeStatus.DRAINING
                return True
            
            # Remove node
            del self.nodes[node_id]
            
            # Clean up connections
            if node_id in self.node_connections:
                del self.node_connections[node_id]
            
            logger.info(f"Removed WebSocket node: {node_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error removing node {node_id}: {e}")
            return False
    
    def select_node(self, connection_id: str, user_id: str = None, 
                   session_id: str = None) -> Optional[str]:
        """Select a node for a new connection"""
        try:
            # Get healthy nodes
            healthy_nodes = [
                node for node in self.nodes.values()
                if node.status == NodeStatus.HEALTHY and 
                node.active_connections < node.max_connections
            ]
            
            if not healthy_nodes:
                logger.error("No healthy nodes available")
                self.metrics['failed_connections'] += 1
                return None
            
            # Check session affinity
            if self.config.enable_sticky_sessions:
                affinity_key = self._get_affinity_key(user_id, session_id)
                if affinity_key and affinity_key in self.session_affinity:
                    preferred_node_id = self.session_affinity[affinity_key]
                    if preferred_node_id in self.nodes:
                        preferred_node = self.nodes[preferred_node_id]
                        if (preferred_node.status == NodeStatus.HEALTHY and 
                            preferred_node.active_connections < preferred_node.max_connections):
                            self.metrics['balancing_decisions'] += 1
                            return preferred_node_id
            
            # Apply load balancing strategy
            selected_node = self._apply_balancing_strategy(healthy_nodes, connection_id)
            
            if selected_node:
                # Update session affinity
                if self.config.enable_sticky_sessions:
                    affinity_key = self._get_affinity_key(user_id, session_id)
                    if affinity_key:
                        self.session_affinity[affinity_key] = selected_node.node_id
                
                self.metrics['balancing_decisions'] += 1
                return selected_node.node_id
            
            return None
            
        except Exception as e:
            logger.error(f"Error selecting node: {e}")
            self.metrics['failed_connections'] += 1
            return None
    
    def _get_affinity_key(self, user_id: str = None, session_id: str = None) -> Optional[str]:
        """Get session affinity key"""
        if self.config.session_affinity_key == "user_id" and user_id:
            return f"user:{user_id}"
        elif self.config.session_affinity_key == "session_id" and session_id:
            return f"session:{session_id}"
        return None
    
    def _apply_balancing_strategy(self, nodes: List[WebSocketNode], 
                                connection_id: str) -> Optional[WebSocketNode]:
        """Apply load balancing strategy"""
        try:
            if self.config.strategy == LoadBalancingStrategy.ROUND_ROBIN:
                return self._round_robin_selection(nodes)
            elif self.config.strategy == LoadBalancingStrategy.WEIGHTED_ROUND_ROBIN:
                return self._weighted_round_robin_selection(nodes)
            elif self.config.strategy == LoadBalancingStrategy.LEAST_CONNECTIONS:
                return self._least_connections_selection(nodes)
            elif self.config.strategy == LoadBalancingStrategy.LEAST_RESPONSE_TIME:
                return self._least_response_time_selection(nodes)
            elif self.config.strategy == LoadBalancingStrategy.HASH_BASED:
                return self._hash_based_selection(nodes, connection_id)
            elif self.config.strategy == LoadBalancingStrategy.RANDOM:
                return self._random_selection(nodes)
            else:
                # Default to round robin
                return self._round_robin_selection(nodes)
                
        except Exception as e:
            logger.error(f"Error applying balancing strategy: {e}")
            return None
    
    def _round_robin_selection(self, nodes: List[WebSocketNode]) -> Optional[WebSocketNode]:
        """Round robin selection"""
        try:
            if not nodes:
                return None
            
            node = nodes[self.current_round_robin_index % len(nodes)]
            self.current_round_robin_index += 1
            return node
            
        except Exception as e:
            logger.error(f"Error in round robin selection: {e}")
            return None
    
    def _weighted_round_robin_selection(self, nodes: List[WebSocketNode]) -> Optional[WebSocketNode]:
        """Weighted round robin selection"""
        try:
            if not nodes:
                return None
            
            # Create weighted list
            weighted_nodes = []
            for node in nodes:
                weighted_nodes.extend([node] * node.weight)
            
            if not weighted_nodes:
                return None
            
            node = weighted_nodes[self.current_round_robin_index % len(weighted_nodes)]
            self.current_round_robin_index += 1
            return node
            
        except Exception as e:
            logger.error(f"Error in weighted round robin selection: {e}")
            return None
    
    def _least_connections_selection(self, nodes: List[WebSocketNode]) -> Optional[WebSocketNode]:
        """Least connections selection"""
        try:
            if not nodes:
                return None
            
            # Find node with least connections
            min_connections = float('inf')
            selected_node = None
            
            for node in nodes:
                if node.active_connections < min_connections:
                    min_connections = node.active_connections
                    selected_node = node
            
            return selected_node
            
        except Exception as e:
            logger.error(f"Error in least connections selection: {e}")
            return None
    
    def _least_response_time_selection(self, nodes: List[WebSocketNode]) -> Optional[WebSocketNode]:
        """Least response time selection"""
        try:
            if not nodes:
                return None
            
            # Find node with least response time
            min_response_time = float('inf')
            selected_node = None
            
            for node in nodes:
                if node.avg_response_time < min_response_time:
                    min_response_time = node.avg_response_time
                    selected_node = node
            
            return selected_node
            
        except Exception as e:
            logger.error(f"Error in least response time selection: {e}")
            return None
    
    def _hash_based_selection(self, nodes: List[WebSocketNode], connection_id: str) -> Optional[WebSocketNode]:
        """Hash-based selection"""
        try:
            if not nodes:
                return None
            
            # Hash connection ID
            hash_value = int(hashlib.md5(connection_id.encode()).hexdigest(), 16)
            node_index = hash_value % len(nodes)
            return nodes[node_index]
            
        except Exception as e:
            logger.error(f"Error in hash-based selection: {e}")
            return None
    
    def _random_selection(self, nodes: List[WebSocketNode]) -> Optional[WebSocketNode]:
        """Random selection"""
        try:
            if not nodes:
                return None
            
            return random.choice(nodes)
            
        except Exception as e:
            logger.error(f"Error in random selection: {e}")
            return None
    
    def register_connection(self, connection_id: str, node_id: str, 
                          user_id: str = None, session_id: str = None) -> bool:
        """Register a new connection"""
        try:
            if node_id not in self.nodes:
                logger.error(f"Node {node_id} not found")
                return False
            
            node = self.nodes[node_id]
            
            # Check node capacity
            if node.active_connections >= node.max_connections:
                logger.error(f"Node {node_id} at capacity")
                return False
            
            # Create connection info
            connection_info = ConnectionInfo(
                connection_id=connection_id,
                node_id=node_id,
                user_id=user_id,
                session_id=session_id
            )
            
            # Register connection
            self.connections[connection_id] = connection_info
            self.node_connections[node_id].add(connection_id)
            
            # Update node stats
            node.active_connections += 1
            node.total_connections += 1
            
            # Update metrics
            self.metrics['total_connections'] += 1
            self.metrics['active_connections'] += 1
            
            logger.info(f"Registered connection {connection_id} to node {node_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error registering connection: {e}")
            return False
    
    def unregister_connection(self, connection_id: str) -> bool:
        """Unregister a connection"""
        try:
            if connection_id not in self.connections:
                logger.warning(f"Connection {connection_id} not found")
                return False
            
            connection_info = self.connections[connection_id]
            node_id = connection_info.node_id
            
            # Remove connection
            del self.connections[connection_id]
            
            # Remove from node connections
            if node_id in self.node_connections:
                self.node_connections[node_id].discard(connection_id)
            
            # Update node stats
            if node_id in self.nodes:
                self.nodes[node_id].active_connections -= 1
            
            # Update metrics
            self.metrics['active_connections'] -= 1
            
            logger.info(f"Unregistered connection {connection_id} from node {node_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error unregistering connection: {e}")
            return False
    
    def get_node_for_connection(self, connection_id: str) -> Optional[str]:
        """Get node ID for a connection"""
        try:
            if connection_id in self.connections:
                return self.connections[connection_id].node_id
            return None
            
        except Exception as e:
            logger.error(f"Error getting node for connection: {e}")
            return None
    
    def get_connections_for_node(self, node_id: str) -> List[str]:
        """Get all connections for a node"""
        try:
            if node_id in self.node_connections:
                return list(self.node_connections[node_id])
            return []
            
        except Exception as e:
            logger.error(f"Error getting connections for node: {e}")
            return []
    
    def _start_health_checking(self):
        """Start health checking thread"""
        def health_check_loop():
            while self.health_check_enabled:
                try:
                    self._perform_health_checks()
                    time.sleep(self.config.health_check_interval)
                except Exception as e:
                    logger.error(f"Health check loop error: {e}")
                    time.sleep(10)
        
        self.health_check_thread = threading.Thread(target=health_check_loop, daemon=True)
        self.health_check_thread.start()
        logger.info("WebSocket load balancer health checking started")
    
    def _perform_health_checks(self):
        """Perform health checks on all nodes"""
        try:
            for node in self.nodes.values():
                self._check_node_health(node)
            
        except Exception as e:
            logger.error(f"Error performing health checks: {e}")
    
    def _check_node_health(self, node: WebSocketNode):
        """Check health of a specific node"""
        try:
            self.metrics['health_checks'] += 1
            
            # Create socket connection
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.config.health_check_timeout)
            
            try:
                # Try to connect
                result = sock.connect_ex((node.host, node.port))
                
                if result == 0:
                    # Connection successful
                    node.status = NodeStatus.HEALTHY
                    node.consecutive_failures = 0
                    node.last_health_check = datetime.utcnow()
                else:
                    # Connection failed
                    node.consecutive_failures += 1
                    node.last_health_check = datetime.utcnow()
                    
                    if node.consecutive_failures >= self.config.max_failures:
                        node.status = NodeStatus.UNHEALTHY
                        logger.warning(f"Node {node.node_id} marked as unhealthy")
                        self.metrics['failed_health_checks'] += 1
                
            finally:
                sock.close()
            
        except Exception as e:
            logger.error(f"Error checking node health for {node.node_id}: {e}")
            node.consecutive_failures += 1
            node.last_health_check = datetime.utcnow()
            
            if node.consecutive_failures >= self.config.max_failures:
                node.status = NodeStatus.UNHEALTHY
                self.metrics['failed_health_checks'] += 1
    
    def get_node_stats(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Get statistics for a specific node"""
        try:
            if node_id not in self.nodes:
                return None
            
            node = self.nodes[node_id]
            
            return {
                'node_id': node.node_id,
                'host': node.host,
                'port': node.port,
                'weight': node.weight,
                'status': node.status.value,
                'active_connections': node.active_connections,
                'total_connections': node.total_connections,
                'avg_response_time': node.avg_response_time,
                'max_connections': node.max_connections,
                'last_health_check': (
                    node.last_health_check.isoformat()
                    if node.last_health_check else None
                ),
                'consecutive_failures': node.consecutive_failures,
                'metadata': node.metadata
            }
            
        except Exception as e:
            logger.error(f"Error getting node stats: {e}")
            return None
    
    def get_all_node_stats(self) -> List[Dict[str, Any]]:
        """Get statistics for all nodes"""
        try:
            return [self.get_node_stats(node_id) for node_id in self.nodes.keys()]
            
        except Exception as e:
            logger.error(f"Error getting all node stats: {e}")
            return []
    
    def get_load_balancer_stats(self) -> Dict[str, Any]:
        """Get load balancer statistics"""
        try:
            # Calculate node distribution
            node_distribution = {}
            for node_id, connections in self.node_connections.items():
                node_distribution[node_id] = len(connections)
            
            # Calculate connection distribution
            healthy_nodes = len([n for n in self.nodes.values() if n.status == NodeStatus.HEALTHY])
            total_capacity = sum(n.max_connections for n in self.nodes.values())
            used_capacity = sum(n.active_connections for n in self.nodes.values())
            
            return {
                'total_nodes': len(self.nodes),
                'healthy_nodes': healthy_nodes,
                'unhealthy_nodes': len(self.nodes) - healthy_nodes,
                'total_connections': self.metrics['total_connections'],
                'active_connections': self.metrics['active_connections'],
                'failed_connections': self.metrics['failed_connections'],
                'total_capacity': total_capacity,
                'used_capacity': used_capacity,
                'capacity_utilization': (used_capacity / total_capacity) if total_capacity > 0 else 0,
                'node_distribution': node_distribution,
                'balancing_strategy': self.config.strategy.value,
                'health_checks': self.metrics['health_checks'],
                'failed_health_checks': self.metrics['failed_health_checks'],
                'balancing_decisions': self.metrics['balancing_decisions'],
                'failovers': self.metrics['failovers'],
                'session_affinity_entries': len(self.session_affinity)
            }
            
        except Exception as e:
            logger.error(f"Error getting load balancer stats: {e}")
            return {}
    
    def update_node_weight(self, node_id: str, weight: int) -> bool:
        """Update node weight"""
        try:
            if node_id not in self.nodes:
                logger.error(f"Node {node_id} not found")
                return False
            
            if weight <= 0:
                logger.error(f"Invalid weight: {weight}")
                return False
            
            self.nodes[node_id].weight = weight
            logger.info(f"Updated weight for node {node_id} to {weight}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating node weight: {e}")
            return False
    
    def set_node_status(self, node_id: str, status: NodeStatus) -> bool:
        """Set node status"""
        try:
            if node_id not in self.nodes:
                logger.error(f"Node {node_id} not found")
                return False
            
            self.nodes[node_id].status = status
            logger.info(f"Set status for node {node_id} to {status.value}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting node status: {e}")
            return False
    
    def set_balancing_strategy(self, strategy: LoadBalancingStrategy) -> bool:
        """Set load balancing strategy"""
        try:
            self.config.strategy = strategy
            logger.info(f"Set load balancing strategy to {strategy.value}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting balancing strategy: {e}")
            return False
    
    def clear_session_affinity(self):
        """Clear session affinity table"""
        try:
            self.session_affinity.clear()
            logger.info("Cleared session affinity table")
            
        except Exception as e:
            logger.error(f"Error clearing session affinity: {e}")
    
    def get_config(self) -> Dict[str, Any]:
        """Get load balancer configuration"""
        return {
            'strategy': self.config.strategy.value,
            'health_check_interval': self.config.health_check_interval,
            'health_check_timeout': self.config.health_check_timeout,
            'max_failures': self.config.max_failures,
            'recovery_timeout': self.config.recovery_timeout,
            'enable_sticky_sessions': self.config.enable_sticky_sessions,
            'session_affinity_key': self.config.session_affinity_key,
            'enable_health_checks': self.config.enable_health_checks,
            'enable_failover': self.config.enable_failover,
            'enable_metrics': self.config.enable_metrics,
            'connection_timeout': self.config.connection_timeout,
            'retry_attempts': self.config.retry_attempts,
            'retry_delay': self.config.retry_delay
        }
    
    def update_config(self, **kwargs):
        """Update load balancer configuration"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
                logger.info(f"Updated load balancer config: {key} = {value}")
    
    def shutdown(self):
        """Shutdown load balancer"""
        try:
            # Stop health checking
            self.health_check_enabled = False
            
            # Wait for health check thread to finish
            if self.health_check_thread:
                self.health_check_thread.join(timeout=5)
            
            logger.info("WebSocket load balancer shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during load balancer shutdown: {e}")
