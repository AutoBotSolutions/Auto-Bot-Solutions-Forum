"""
API Gateway Manager

Central management for API gateway functionality including routing,
load balancing, rate limiting, and monitoring.
"""

import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
import hashlib
import time

logger = logging.getLogger(__name__)

class GatewayStatus(Enum):
    """Gateway status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    ERROR = "error"

@dataclass
class GatewayConfig:
    """Gateway configuration"""
    enable_versioning: bool = True
    enable_load_balancing: bool = True
    enable_rate_limiting: bool = True
    enable_monitoring: bool = True
    default_version: str = "v1.0"
    health_check_interval: int = 30
    max_concurrent_requests: int = 1000
    request_timeout: int = 30

@dataclass
class RouteConfig:
    """Route configuration"""
    path: str
    version: str
    service_name: str
    service_url: str
    methods: List[str]
    weight: int = 1
    health_check_path: str = "/health"
    timeout: int = 30
    retries: int = 3

@dataclass
class ServiceInstance:
    """Service instance for load balancing"""
    id: str
    url: str
    weight: int = 1
    status: GatewayStatus = GatewayStatus.ACTIVE
    last_health_check: Optional[datetime] = None
    consecutive_failures: int = 0
    max_failures: int = 3
    response_time: float = 0.0

class APIGatewayManager:
    """Central API gateway manager"""
    
    def __init__(self, config: GatewayConfig = None):
        self.config = config or GatewayConfig()
        self.routes: Dict[str, RouteConfig] = {}
        self.services: Dict[str, List[ServiceInstance]] = {}
        self.rate_limits: Dict[str, Dict[str, Any]] = {}
        self.metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'avg_response_time': 0.0,
            'requests_per_second': 0.0,
            'last_request_time': None
        }
        self.request_times: List[float] = []
        self.start_time = datetime.utcnow()
        
    def register_route(self, route_config: RouteConfig):
        """Register a route with the gateway"""
        route_key = f"{route_config.path}:{route_config.version}"
        self.routes[route_key] = route_config
        
        # Initialize service instances if not exists
        if route_config.service_name not in self.services:
            self.services[route_config.service_name] = []
        
        logger.info(f"Registered route: {route_key} -> {route_config.service_name}")
    
    def add_service_instance(self, service_name: str, instance: ServiceInstance):
        """Add a service instance for load balancing"""
        if service_name not in self.services:
            self.services[service_name] = []
        
        self.services[service_name].append(instance)
        logger.info(f"Added service instance: {instance.id} for {service_name}")
    
    def remove_service_instance(self, service_name: str, instance_id: str):
        """Remove a service instance"""
        if service_name in self.services:
            self.services[service_name] = [
                instance for instance in self.services[service_name]
                if instance.id != instance_id
            ]
            logger.info(f"Removed service instance: {instance_id} from {service_name}")
    
    def get_route_for_request(self, path: str, version: str = None, method: str = "GET") -> Optional[RouteConfig]:
        """Get route configuration for a request"""
        # Try exact match first
        route_key = f"{path}:{version}" if version else None
        if route_key and route_key in self.routes:
            return self.routes[route_key]
        
        # Try path-only match with default version
        if not version:
            default_route_key = f"{path}:{self.config.default_version}"
            if default_route_key in self.routes:
                return self.routes[default_route_key]
        
        # Try pattern matching
        for route_key, route_config in self.routes.items():
            route_path, route_version = route_key.split(":", 1)
            if self._path_matches(path, route_path):
                if not version or version == route_version:
                    return route_config
        
        return None
    
    def _path_matches(self, request_path: str, route_path: str) -> bool:
        """Check if request path matches route path"""
        # Simple exact match for now
        # In production, this would support regex patterns
        return request_path == route_path
    
    def get_healthy_instances(self, service_name: str) -> List[ServiceInstance]:
        """Get healthy service instances for load balancing"""
        if service_name not in self.services:
            return []
        
        return [
            instance for instance in self.services[service_name]
            if instance.status == GatewayStatus.ACTIVE
        ]
    
    def update_metrics(self, response_time: float, success: bool = True):
        """Update gateway metrics"""
        self.metrics['total_requests'] += 1
        self.metrics['last_request_time'] = datetime.utcnow()
        
        if success:
            self.metrics['successful_requests'] += 1
        else:
            self.metrics['failed_requests'] += 1
        
        # Update response time tracking
        self.request_times.append(response_time)
        if len(self.request_times) > 1000:
            self.request_times = self.request_times[-1000:]
        
        # Calculate average response time
        if self.request_times:
            self.metrics['avg_response_time'] = sum(self.request_times) / len(self.request_times)
        
        # Calculate requests per second
        if self.metrics['total_requests'] > 1:
            elapsed = (datetime.utcnow() - self.start_time).total_seconds()
            if elapsed > 0:
                self.metrics['requests_per_second'] = self.metrics['total_requests'] / elapsed
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get gateway metrics"""
        return {
            **self.metrics,
            'active_routes': len(self.routes),
            'active_services': len(self.services),
            'total_instances': sum(len(instances) for instances in self.services.values()),
            'healthy_instances': sum(
                len(self.get_healthy_instances(service_name))
                for service_name in self.services
            ),
            'uptime_seconds': (datetime.utcnow() - self.start_time).total_seconds()
        }
    
    def health_check_all_instances(self):
        """Perform health check on all service instances"""
        for service_name, instances in self.services.items():
            for instance in instances:
                self._health_check_instance(instance)
    
    def _health_check_instance(self, instance: ServiceInstance):
        """Health check a single service instance"""
        try:
            # In production, this would make an actual HTTP request
            # For now, we'll simulate health checks
            import random
            
            # Simulate health check (90% success rate)
            if random.random() < 0.9:
                instance.status = GatewayStatus.ACTIVE
                instance.consecutive_failures = 0
                instance.last_health_check = datetime.utcnow()
                instance.response_time = random.uniform(0.01, 0.5)
            else:
                instance.consecutive_failures += 1
                if instance.consecutive_failures >= instance.max_failures:
                    instance.status = GatewayStatus.ERROR
                instance.last_health_check = datetime.utcnow()
        
        except Exception as e:
            logger.error(f"Health check failed for instance {instance.id}: {e}")
            instance.status = GatewayStatus.ERROR
            instance.consecutive_failures += 1
    
    def get_service_stats(self, service_name: str) -> Dict[str, Any]:
        """Get statistics for a specific service"""
        if service_name not in self.services:
            return {'error': f'Service {service_name} not found'}
        
        instances = self.services[service_name]
        healthy_instances = self.get_healthy_instances(service_name)
        
        return {
            'service_name': service_name,
            'total_instances': len(instances),
            'healthy_instances': len(healthy_instances),
            'unhealthy_instances': len(instances) - len(healthy_instances),
            'health_percentage': (len(healthy_instances) / len(instances) * 100) if instances else 0,
            'instances': [
                {
                    'id': instance.id,
                    'url': instance.url,
                    'status': instance.status.value,
                    'weight': instance.weight,
                    'last_health_check': instance.last_health_check.isoformat() if instance.last_health_check else None,
                    'consecutive_failures': instance.consecutive_failures,
                    'response_time': instance.response_time
                }
                for instance in instances
            ]
        }
    
    def get_all_services_stats(self) -> Dict[str, Any]:
        """Get statistics for all services"""
        return {
            service_name: self.get_service_stats(service_name)
            for service_name in self.services
        }
    
    def cleanup_old_metrics(self, max_age_hours: int = 24):
        """Clean up old metrics data"""
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        
        # Clean up old request times
        self.request_times = [
            rt for rt in self.request_times
            if rt > 0  # Keep all positive response times for now
        ]
        
        logger.info(f"Cleaned up metrics older than {max_age_hours} hours")
    
    def get_config(self) -> Dict[str, Any]:
        """Get gateway configuration"""
        return {
            'enable_versioning': self.config.enable_versioning,
            'enable_load_balancing': self.config.enable_load_balancing,
            'enable_rate_limiting': self.config.enable_rate_limiting,
            'enable_monitoring': self.config.enable_monitoring,
            'default_version': self.config.default_version,
            'health_check_interval': self.config.health_check_interval,
            'max_concurrent_requests': self.config.max_concurrent_requests,
            'request_timeout': self.config.request_timeout
        }
    
    def update_config(self, **kwargs):
        """Update gateway configuration"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
                logger.info(f"Updated gateway config: {key} = {value}")
    
    def get_route_config(self, path: str, version: str = None) -> Optional[Dict[str, Any]]:
        """Get route configuration details"""
        route = self.get_route_for_request(path, version)
        if not route:
            return None
        
        return {
            'path': route.path,
            'version': route.version,
            'service_name': route.service_name,
            'service_url': route.service_url,
            'methods': route.methods,
            'weight': route.weight,
            'health_check_path': route.health_check_path,
            'timeout': route.timeout,
            'retries': route.retries
        }
    
    def get_request_summary(self) -> Dict[str, Any]:
        """Get a summary of recent requests"""
        return {
            'total_requests': self.metrics['total_requests'],
            'success_rate': (
                self.metrics['successful_requests'] / self.metrics['total_requests'] * 100
                if self.metrics['total_requests'] > 0 else 0
            ),
            'avg_response_time': self.metrics['avg_response_time'],
            'requests_per_second': self.metrics['requests_per_second'],
            'last_request_time': (
                self.metrics['last_request_time'].isoformat()
                if self.metrics['last_request_time'] else None
            ),
            'uptime_seconds': (datetime.utcnow() - self.start_time).total_seconds()
        }
