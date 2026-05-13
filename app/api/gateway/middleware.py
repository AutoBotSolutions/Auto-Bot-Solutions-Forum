"""
Gateway Middleware

Flask middleware for API gateway functionality including request routing,
load balancing, rate limiting, and monitoring.
"""

import logging
from typing import Dict, Any, Optional
from flask import request, g, jsonify, Response
from datetime import datetime
import time
import uuid

from .gateway_manager import APIGatewayManager, RouteConfig
from .routing import GatewayRouter
from .load_balancer import LoadBalancer, LoadBalancingStrategy
from .rate_limiter import GatewayRateLimiter
from .monitor import GatewayMonitor, AlertLevel

logger = logging.getLogger(__name__)

class GatewayMiddleware:
    """Flask middleware for API gateway functionality"""
    
    def __init__(self, gateway_manager: APIGatewayManager, app=None):
        self.gateway_manager = gateway_manager
        self.router = GatewayRouter(gateway_manager)
        self.load_balancer = LoadBalancer(LoadBalancingStrategy.ROUND_ROBIN)
        self.rate_limiter = GatewayRateLimiter()
        self.monitor = GatewayMonitor()
        self.app = app
        
        # Initialize default alerts
        self._setup_default_alerts()
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize middleware with Flask app"""
        self.app = app
        
        # Register before/after request handlers
        app.before_request(self._before_request)
        app.after_request(self._after_request)
        
        # Register error handlers
        app.errorhandler(429)(self._rate_limit_exceeded)
        app.errorhandler(503)(self._service_unavailable)
        app.errorhandler(404)(self._route_not_found)
        
        logger.info("Gateway middleware initialized")
    
    def _setup_default_alerts(self):
        """Setup default monitoring alerts"""
        # High response time alert
        self.monitor.create_alert(
            "high_response_time",
            "High Response Time",
            AlertLevel.WARNING,
            "avg_response_time",
            1.0,  # 1 second threshold
            300   # 5 minute window
        )
        
        # High error rate alert
        self.monitor.create_alert(
            "high_error_rate",
            "High Error Rate",
            AlertLevel.ERROR,
            "error_rate",
            0.05,  # 5% error rate threshold
            300   # 5 minute window
        )
        
        # Low throughput alert
        self.monitor.create_alert(
            "low_throughput",
            "Low Throughput",
            AlertLevel.WARNING,
            "throughput",
            10,   # 10 requests per second threshold
            300   # 5 minute window
        )
    
    def _before_request(self):
        """Handle before request processing"""
        # Start timing
        g.start_time = time.time()
        g.request_id = str(uuid.uuid4())
        
        # Extract request information
        request_path = request.path
        method = request.method
        headers = dict(request.headers)
        query_params = dict(request.args)
        
        # Store request context
        g.request_context = {
            'request_id': g.request_id,
            'path': request_path,
            'method': method,
            'headers': headers,
            'query_params': query_params,
            'client_ip': self._get_client_ip(),
            'user_id': self._get_user_id(),
            'start_time': g.start_time
        }
        
        # Check rate limits
        allowed, rate_limit_results = self.rate_limiter.check_rate_limits(g.request_context)
        
        if not allowed:
            g.rate_limit_exceeded = True
            g.rate_limit_results = rate_limit_results
            return self._create_rate_limit_response(rate_limit_results)
        
        # Route the request
        target_path, routing_context = self.router.route_request(
            request_path, method, headers, query_params
        )
        
        if not routing_context:
            g.route_not_found = True
            return
        
        # Store routing context
        g.routing_context = routing_context
        g.target_path = target_path
        
        # Store service name for monitoring
        g.service_name = routing_context.get('service_name')
        
        # Check if this is a gateway-managed request
        g.gateway_managed = True
    
    def _after_request(self, response: Response):
        """Handle after request processing"""
        # Skip if not gateway managed
        if not getattr(g, 'gateway_managed', False):
            return response
        
        # Calculate response time
        end_time = time.time()
        response_time = end_time - getattr(g, 'start_time', end_time)
        
        # Record metrics
        status_code = response.status_code
        endpoint = getattr(g, 'routing_context', {}).get('service_name', 'unknown')
        service_name = getattr(g, 'service_name', 'unknown')
        
        self.monitor.record_request(response_time, status_code, endpoint, service_name)
        
        # Add gateway headers
        response.headers['X-Gateway-Request-ID'] = getattr(g, 'request_id', '')
        response.headers['X-Gateway-Response-Time'] = f"{response_time:.3f}"
        
        if hasattr(g, 'routing_context'):
            response.headers['X-Gateway-Service'] = g.routing_context.get('service_name', '')
            response.headers['X-Gateway-Version'] = g.routing_context.get('detected_version', '')
        
        # Check alerts
        triggered_alerts = self.monitor.check_alerts()
        if triggered_alerts:
            logger.warning(f"Alerts triggered: {[alert.name for alert in triggered_alerts]}")
        
        return response
    
    def _get_client_ip(self) -> str:
        """Get client IP address"""
        # Check for forwarded IP
        if request.headers.get('X-Forwarded-For'):
            return request.headers.get('X-Forwarded-For').split(',')[0].strip()
        elif request.headers.get('X-Real-IP'):
            return request.headers.get('X-Real-IP')
        else:
            return request.remote_addr or 'unknown'
    
    def _get_user_id(self) -> Optional[str]:
        """Get user ID from request"""
        # Try to get user ID from various sources
        # This would integrate with your authentication system
        if hasattr(g, 'current_user') and g.current_user:
            return str(g.current_user.id)
        
        # Try JWT token
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            # This would decode JWT and extract user ID
            pass
        
        return None
    
    def _create_rate_limit_response(self, rate_limit_results):
        """Create rate limit exceeded response"""
        # Find the most restrictive limit
        most_restrictive = None
        for result in rate_limit_results:
            if not result.get('allowed', True):
                if not most_restrictive or result.get('remaining', 0) < most_restrictive.get('remaining', 0):
                    most_restrictive = result
        
        response = jsonify({
            'error': 'Rate limit exceeded',
            'message': 'Too many requests',
            'rate_limit': most_restrictive if most_restrictive else {}
        })
        
        response.status_code = 429
        response.headers['Retry-After'] = str(most_restrictive.get('reset_time', 60))
        response.headers['X-RateLimit-Limit'] = str(most_restrictive.get('limit', 100))
        response.headers['X-RateLimit-Remaining'] = str(most_restrictive.get('remaining', 0))
        response.headers['X-RateLimit-Reset'] = str(most_restrictive.get('reset_time', 0))
        
        return response
    
    def _rate_limit_exceeded(self, error):
        """Handle rate limit exceeded error"""
        return jsonify({
            'error': 'Rate limit exceeded',
            'message': str(error)
        }), 429
    
    def _service_unavailable(self, error):
        """Handle service unavailable error"""
        return jsonify({
            'error': 'Service Unavailable',
            'message': 'The requested service is currently unavailable'
        }), 503
    
    def _route_not_found(self, error):
        """Handle route not found error"""
        return jsonify({
            'error': 'Not Found',
            'message': 'The requested endpoint was not found'
        }), 404
    
    def forward_request(self, routing_context: Dict[str, Any]) -> Response:
        """Forward request to target service"""
        try:
            # Get service instances for load balancing
            service_name = routing_context['service_name']
            instances = self.gateway_manager.get_healthy_instances(service_name)
            
            if not instances:
                logger.error(f"No healthy instances available for service: {service_name}")
                return self._create_service_unavailable_response(service_name)
            
            # Select instance using load balancer
            selected_instance = self.load_balancer.select_instance(
                instances, routing_context
            )
            
            if not selected_instance:
                logger.error(f"Load balancer failed to select instance for service: {service_name}")
                return self._create_service_unavailable_response(service_name)
            
            # Forward request to selected instance
            return self._forward_to_instance(selected_instance, routing_context)
        
        except Exception as e:
            logger.error(f"Error forwarding request: {e}")
            return jsonify({
                'error': 'Internal Server Error',
                'message': 'An error occurred while processing your request'
            }), 500
    
    def _forward_to_instance(self, instance, routing_context: Dict[str, Any]) -> Response:
        """Forward request to specific service instance"""
        # This would implement actual HTTP forwarding
        # For now, return a mock response
        
        target_url = instance.url + routing_context['target_path']
        
        # In production, this would use requests or similar to forward the request
        logger.info(f"Forwarding request to: {target_url}")
        
        # Mock response
        return jsonify({
            'message': 'Request forwarded successfully',
            'service': routing_context['service_name'],
            'instance': instance.id,
            'path': routing_context['target_path'],
            'method': routing_context['method']
        })
    
    def _create_service_unavailable_response(self, service_name: str):
        """Create service unavailable response"""
        return jsonify({
            'error': 'Service Unavailable',
            'message': f'The service {service_name} is currently unavailable',
            'service': service_name
        }), 503
    
    def get_gateway_stats(self) -> Dict[str, Any]:
        """Get comprehensive gateway statistics"""
        return {
            'gateway': self.gateway_manager.get_metrics(),
            'routing': self.router.get_routing_stats(),
            'load_balancer': self.load_balancer.get_load_balancing_metrics(),
            'rate_limiter': self.rate_limiter.get_gateway_rate_limit_stats(),
            'monitor': self.monitor.get_metrics_summary(),
            'health': self.monitor.get_health_status()
        }
    
    def get_service_stats(self, service_name: str) -> Dict[str, Any]:
        """Get statistics for a specific service"""
        return self.gateway_manager.get_service_stats(service_name)
    
    def get_all_services_stats(self) -> Dict[str, Any]:
        """Get statistics for all services"""
        return self.gateway_manager.get_all_services_stats()
    
    def configure_rate_limit(self, limit_type: str, limit: int, window: int, 
                           strategy: str = None):
        """Configure rate limiting"""
        from .rate_limiter import RateLimitType, RateLimitStrategy
        
        try:
            limit_type_enum = RateLimitType(limit_type)
            strategy_enum = RateLimitStrategy(strategy) if strategy else None
            
            self.rate_limiter.configure_rate_limit(
                limit_type_enum, limit, window, strategy_enum
            )
            
            return True
        except ValueError as e:
            logger.error(f"Invalid rate limit configuration: {e}")
            return False
    
    def set_load_balancing_strategy(self, strategy: str):
        """Set load balancing strategy"""
        try:
            strategy_enum = LoadBalancingStrategy(strategy)
            self.load_balancer.set_strategy(strategy_enum)
            return True
        except ValueError as e:
            logger.error(f"Invalid load balancing strategy: {e}")
            return False
    
    def add_service_instance(self, service_name: str, instance_url: str, 
                           weight: int = 1):
        """Add a service instance"""
        from .gateway_manager import ServiceInstance, GatewayStatus
        
        instance_id = f"{service_name}_{len(self.gateway_manager.services.get(service_name, []))}"
        instance = ServiceInstance(
            id=instance_id,
            url=instance_url,
            weight=weight,
            status=GatewayStatus.ACTIVE
        )
        
        self.gateway_manager.add_service_instance(service_name, instance)
        return instance_id
    
    def remove_service_instance(self, service_name: str, instance_id: str):
        """Remove a service instance"""
        self.gateway_manager.remove_service_instance(service_name, instance_id)
    
    def health_check_all_services(self):
        """Perform health check on all services"""
        self.gateway_manager.health_check_all_instances()
        return self.gateway_manager.get_all_services_stats()
    
    def create_alert(self, alert_id: str, name: str, level: str, 
                    condition: str, threshold: float, window: int = 300):
        """Create a monitoring alert"""
        try:
            level_enum = AlertLevel(level)
            self.monitor.create_alert(alert_id, name, level_enum, condition, threshold, window)
            return True
        except ValueError as e:
            logger.error(f"Invalid alert configuration: {e}")
            return False
    
    def get_alerts(self):
        """Get all alerts"""
        return self.monitor.get_alerts()
    
    def enable_alert(self, alert_id: str):
        """Enable an alert"""
        self.monitor.enable_alert(alert_id)
    
    def disable_alert(self, alert_id: str):
        """Disable an alert"""
        self.monitor.disable_alert(alert_id)
    
    def delete_alert(self, alert_id: str):
        """Delete an alert"""
        self.monitor.delete_alert(alert_id)
    
    def export_metrics(self, format: str = 'json'):
        """Export metrics"""
        return self.monitor.export_metrics(format)
    
    def cleanup_old_data(self, max_age_hours: int = 24):
        """Clean up old data"""
        gateway_cleaned = self.gateway_manager.cleanup_old_metrics(max_age_hours)
        monitor_cleaned = self.monitor.cleanup_old_metrics(max_age_hours)
        
        return {
            'gateway_metrics_cleaned': gateway_cleaned,
            'monitor_metrics_cleaned': monitor_cleaned,
            'total_cleaned': gateway_cleaned + monitor_cleaned
        }
