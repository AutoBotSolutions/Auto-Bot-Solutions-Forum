"""
Load Balancer

Implements load balancing strategies for API gateway with multiple algorithms
and health checking capabilities.
"""

import logging
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime, timedelta
from enum import Enum
import random
import hashlib
import time

from .gateway_manager import ServiceInstance, GatewayStatus

logger = logging.getLogger(__name__)

class LoadBalancingStrategy(Enum):
    """Load balancing strategies"""
    ROUND_ROBIN = "round_robin"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    LEAST_CONNECTIONS = "least_connections"
    LEAST_RESPONSE_TIME = "least_response_time"
    RANDOM = "random"
    HASH = "hash"
    IP_HASH = "ip_hash"

class LoadBalancer:
    """Load balancer for API gateway"""
    
    def __init__(self, strategy: LoadBalancingStrategy = LoadBalancingStrategy.ROUND_ROBIN):
        self.strategy = strategy
        self.round_robin_index = {}
        self.connection_counts = {}
        self.last_selected = {}
        self.health_check_results = {}
        
    def select_instance(self, instances: List[ServiceInstance], 
                       request_context: Dict[str, Any] = None) -> Optional[ServiceInstance]:
        """Select service instance based on load balancing strategy"""
        if not instances:
            return None
        
        # Filter healthy instances
        healthy_instances = [
            instance for instance in instances
            if instance.status == GatewayStatus.ACTIVE
        ]
        
        if not healthy_instances:
            return None
        
        # Apply load balancing strategy
        if self.strategy == LoadBalancingStrategy.ROUND_ROBIN:
            return self._round_robin_select(healthy_instances)
        elif self.strategy == LoadBalancingStrategy.WEIGHTED_ROUND_ROBIN:
            return self._weighted_round_robin_select(healthy_instances)
        elif self.strategy == LoadBalancingStrategy.LEAST_CONNECTIONS:
            return self._least_connections_select(healthy_instances)
        elif self.strategy == LoadBalancingStrategy.LEAST_RESPONSE_TIME:
            return self._least_response_time_select(healthy_instances)
        elif self.strategy == LoadBalancingStrategy.RANDOM:
            return self._random_select(healthy_instances)
        elif self.strategy == LoadBalancingStrategy.HASH:
            return self._hash_select(healthy_instances, request_context)
        elif self.strategy == LoadBalancingStrategy.IP_HASH:
            return self._ip_hash_select(healthy_instances, request_context)
        else:
            return healthy_instances[0]
    
    def _round_robin_select(self, instances: List[ServiceInstance]) -> ServiceInstance:
        """Round robin selection"""
        service_name = instances[0].url.split('/')[2] if instances else 'default'
        
        if service_name not in self.round_robin_index:
            self.round_robin_index[service_name] = 0
        
        selected_instance = instances[self.round_robin_index[service_name] % len(instances)]
        self.round_robin_index[service_name] += 1
        
        return selected_instance
    
    def _weighted_round_robin_select(self, instances: List[ServiceInstance]) -> ServiceInstance:
        """Weighted round robin selection"""
        # Create weighted list
        weighted_instances = []
        for instance in instances:
            weighted_instances.extend([instance] * instance.weight)
        
        if not weighted_instances:
            return instances[0]
        
        service_name = instances[0].url.split('/')[2] if instances else 'default'
        
        if service_name not in self.round_robin_index:
            self.round_robin_index[service_name] = 0
        
        selected_instance = weighted_instances[self.round_robin_index[service_name] % len(weighted_instances)]
        self.round_robin_index[service_name] += 1
        
        return selected_instance
    
    def _least_connections_select(self, instances: List[ServiceInstance]) -> ServiceInstance:
        """Least connections selection"""
        # Sort by connection count
        sorted_instances = sorted(
            instances,
            key=lambda x: self.connection_counts.get(x.id, 0)
        )
        
        selected_instance = sorted_instances[0]
        
        # Increment connection count
        self.connection_counts[selected_instance.id] = self.connection_counts.get(selected_instance.id, 0) + 1
        
        return selected_instance
    
    def _least_response_time_select(self, instances: List[ServiceInstance]) -> ServiceInstance:
        """Least response time selection"""
        # Sort by response time
        sorted_instances = sorted(
            instances,
            key=lambda x: x.response_time
        )
        
        return sorted_instances[0]
    
    def _random_select(self, instances: List[ServiceInstance]) -> ServiceInstance:
        """Random selection"""
        return random.choice(instances)
    
    def _hash_select(self, instances: List[ServiceInstance], 
                    request_context: Dict[str, Any] = None) -> ServiceInstance:
        """Hash-based selection"""
        if not request_context:
            return self._random_select(instances)
        
        # Create hash from request context
        hash_input = str(sorted(request_context.items()))
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
        
        selected_index = hash_value % len(instances)
        return instances[selected_index]
    
    def _ip_hash_select(self, instances: List[ServiceInstance], 
                       request_context: Dict[str, Any] = None) -> ServiceInstance:
        """IP hash selection"""
        client_ip = None
        
        if request_context:
            headers = request_context.get('headers', {})
            client_ip = headers.get('X-Forwarded-For') or headers.get('X-Real-IP')
        
        if not client_ip:
            return self._random_select(instances)
        
        # Use first IP if multiple
        client_ip = client_ip.split(',')[0].strip()
        
        # Hash IP address
        hash_value = int(hashlib.md5(client_ip.encode()).hexdigest(), 16)
        selected_index = hash_value % len(instances)
        
        return instances[selected_index]
    
    def release_connection(self, instance_id: str):
        """Release connection for least connections strategy"""
        if instance_id in self.connection_counts:
            self.connection_counts[instance_id] = max(0, self.connection_counts[instance_id] - 1)
    
    def update_instance_response_time(self, instance_id: str, response_time: float):
        """Update instance response time for least response time strategy"""
        # Find and update the instance
        # This would be called by the gateway after request completion
        pass
    
    def get_strategy_stats(self) -> Dict[str, Any]:
        """Get load balancing strategy statistics"""
        return {
            'current_strategy': self.strategy.value,
            'round_robin_indices': dict(self.round_robin_index),
            'connection_counts': dict(self.connection_counts),
            'last_selected': dict(self.last_selected)
        }
    
    def set_strategy(self, strategy: LoadBalancingStrategy):
        """Change load balancing strategy"""
        old_strategy = self.strategy
        self.strategy = strategy
        
        # Reset strategy-specific data
        if old_strategy != strategy:
            self.round_robin_index.clear()
            self.connection_counts.clear()
            self.last_selected.clear()
        
        logger.info(f"Load balancing strategy changed from {old_strategy.value} to {strategy.value}")
    
    def health_check_instances(self, instances: List[ServiceInstance], 
                             health_check_url: str = "/health") -> Dict[str, Any]:
        """Perform health check on instances"""
        results = {}
        
        for instance in instances:
            try:
                # In production, this would make actual HTTP requests
                # For now, simulate health checks
                import random
                
                start_time = time.time()
                
                # Simulate health check (95% success rate)
                if random.random() < 0.95:
                    results[instance.id] = {
                        'healthy': True,
                        'response_time': time.time() - start_time,
                        'status_code': 200,
                        'checked_at': datetime.utcnow().isoformat()
                    }
                    
                    # Update instance response time
                    instance.response_time = time.time() - start_time
                    instance.status = GatewayStatus.ACTIVE
                    instance.consecutive_failures = 0
                else:
                    results[instance.id] = {
                        'healthy': False,
                        'response_time': time.time() - start_time,
                        'status_code': 503,
                        'error': 'Service unavailable',
                        'checked_at': datetime.utcnow().isoformat()
                    }
                    
                    instance.consecutive_failures += 1
                    if instance.consecutive_failures >= instance.max_failures:
                        instance.status = GatewayStatus.ERROR
                
                instance.last_health_check = datetime.utcnow()
                
            except Exception as e:
                results[instance.id] = {
                    'healthy': False,
                    'response_time': 0,
                    'status_code': 0,
                    'error': str(e),
                    'checked_at': datetime.utcnow().isoformat()
                }
                
                instance.status = GatewayStatus.ERROR
                instance.consecutive_failures += 1
                instance.last_health_check = datetime.utcnow()
        
        return results
    
    def get_instance_health(self, instance: ServiceInstance) -> Dict[str, Any]:
        """Get health status of a single instance"""
        return {
            'id': instance.id,
            'url': instance.url,
            'status': instance.status.value,
            'weight': instance.weight,
            'response_time': instance.response_time,
            'consecutive_failures': instance.consecutive_failures,
            'max_failures': instance.max_failures,
            'last_health_check': instance.last_health_check.isoformat() if instance.last_health_check else None,
            'connection_count': self.connection_counts.get(instance.id, 0)
        }
    
    def reset_health_check_failures(self, instance_id: str):
        """Reset consecutive failures for an instance"""
        # This would be called when an instance comes back online
        if instance_id in self.connection_counts:
            self.connection_counts[instance_id] = 0
        
        logger.info(f"Reset health check failures for instance: {instance_id}")
    
    def get_load_balancing_metrics(self) -> Dict[str, Any]:
        """Get load balancing metrics"""
        total_connections = sum(self.connection_counts.values())
        
        return {
            'strategy': self.strategy.value,
            'total_connections': total_connections,
            'active_connections': len(self.connection_counts),
            'connection_distribution': dict(self.connection_counts),
            'average_connections_per_instance': (
                total_connections / len(self.connection_counts)
                if self.connection_counts else 0
            )
        }

class CircuitBreaker:
    """Circuit breaker for service instances"""
    
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_counts = {}
        self.last_failure_time = {}
        self.circuit_states = {}  # 'closed', 'open', 'half-open'
    
    def call_service(self, instance_id: str, service_call: Callable) -> Any:
        """Call service with circuit breaker protection"""
        state = self.circuit_states.get(instance_id, 'closed')
        
        if state == 'open':
            # Check if timeout has passed
            last_failure = self.last_failure_time.get(instance_id)
            if last_failure and (datetime.utcnow() - last_failure).total_seconds() > self.timeout:
                self.circuit_states[instance_id] = 'half-open'
            else:
                raise Exception(f"Circuit breaker is open for instance {instance_id}")
        
        try:
            result = service_call()
            
            # Reset failure count on success
            if instance_id in self.failure_counts:
                self.failure_counts[instance_id] = 0
            
            # Close circuit on success
            if state == 'half-open':
                self.circuit_states[instance_id] = 'closed'
            
            return result
        
        except Exception as e:
            # Increment failure count
            self.failure_counts[instance_id] = self.failure_counts.get(instance_id, 0) + 1
            self.last_failure_time[instance_id] = datetime.utcnow()
            
            # Open circuit if threshold reached
            if self.failure_counts[instance_id] >= self.failure_threshold:
                self.circuit_states[instance_id] = 'open'
            
            raise e
    
    def get_circuit_status(self, instance_id: str) -> Dict[str, Any]:
        """Get circuit breaker status for an instance"""
        return {
            'instance_id': instance_id,
            'state': self.circuit_states.get(instance_id, 'closed'),
            'failure_count': self.failure_counts.get(instance_id, 0),
            'failure_threshold': self.failure_threshold,
            'last_failure_time': (
                self.last_failure_time[instance_id].isoformat()
                if instance_id in self.last_failure_time else None
            )
        }
    
    def reset_circuit(self, instance_id: str):
        """Reset circuit breaker for an instance"""
        if instance_id in self.failure_counts:
            del self.failure_counts[instance_id]
        if instance_id in self.last_failure_time:
            del self.last_failure_time[instance_id]
        if instance_id in self.circuit_states:
            del self.circuit_states[instance_id]
        
        logger.info(f"Reset circuit breaker for instance: {instance_id}")
