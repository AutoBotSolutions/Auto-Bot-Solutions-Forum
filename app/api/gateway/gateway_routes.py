"""
Gateway API Routes

Flask routes for API gateway management and monitoring.
"""

from flask import Blueprint, jsonify, request, g
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# This would be initialized in the main app
gateway_bp = Blueprint('gateway', __name__, url_prefix='/api/gateway')

def init_gateway_routes(gateway_middleware):
    """Initialize gateway routes with middleware"""
    
    @gateway_bp.route('/health', methods=['GET'])
    def gateway_health():
        """Get gateway health status"""
        try:
            health_status = gateway_middleware.monitor.get_health_status()
            return jsonify({
                'success': True,
                'data': health_status
            })
        except Exception as e:
            logger.error(f"Error getting gateway health: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @gateway_bp.route('/stats', methods=['GET'])
    def gateway_stats():
        """Get comprehensive gateway statistics"""
        try:
            stats = gateway_middleware.get_gateway_stats()
            return jsonify({
                'success': True,
                'data': stats
            })
        except Exception as e:
            logger.error(f"Error getting gateway stats: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @gateway_bp.route('/routes', methods=['GET'])
    def list_routes():
        """List all configured routes"""
        try:
            routes = {}
            for route_key, route_config in gateway_middleware.gateway_manager.routes.items():
                path, version = route_key.split(':', 1)
                routes[route_key] = {
                    'path': path,
                    'version': version,
                    'service_name': route_config.service_name,
                    'service_url': route_config.service_url,
                    'methods': route_config.methods,
                    'weight': route_config.weight,
                    'timeout': route_config.timeout,
                    'retries': route_config.retries
                }
            
            return jsonify({
                'success': True,
                'data': {
                    'routes': routes,
                    'total': len(routes)
                }
            })
        except Exception as e:
            logger.error(f"Error listing routes: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @gateway_bp.route('/routes', methods=['POST'])
    def add_route():
        """Add a new route"""
        try:
            data = request.get_json()
            
            required_fields = ['path', 'version', 'service_name', 'service_url', 'methods']
            for field in required_fields:
                if field not in data:
                    return jsonify({
                        'success': False,
                        'error': f'Missing required field: {field}'
                    }), 400
            
            from .gateway_manager import RouteConfig
            
            route_config = RouteConfig(
                path=data['path'],
                version=data['version'],
                service_name=data['service_name'],
                service_url=data['service_url'],
                methods=data['methods'],
                weight=data.get('weight', 1),
                health_check_path=data.get('health_check_path', '/health'),
                timeout=data.get('timeout', 30),
                retries=data.get('retries', 3)
            )
            
            gateway_middleware.gateway_manager.register_route(route_config)
            
            return jsonify({
                'success': True,
                'data': {
                    'message': 'Route added successfully',
                    'route': f"{route_config.path}:{route_config.version}"
                }
            })
        except Exception as e:
            logger.error(f"Error adding route: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @gateway_bp.route('/services', methods=['GET'])
    def list_services():
        """List all services and their instances"""
        try:
            services_stats = gateway_middleware.get_all_services_stats()
            return jsonify({
                'success': True,
                'data': services_stats
            })
        except Exception as e:
            logger.error(f"Error listing services: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @gateway_bp.route('/services/<service_name>', methods=['GET'])
    def get_service_details(service_name: str):
        """Get details for a specific service"""
        try:
            service_stats = gateway_middleware.get_service_stats(service_name)
            
            if 'error' in service_stats:
                return jsonify({
                    'success': False,
                    'error': service_stats['error']
                }), 404
            
            return jsonify({
                'success': True,
                'data': service_stats
            })
        except Exception as e:
            logger.error(f"Error getting service details: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @gateway_bp.route('/services/<service_name>/instances', methods=['POST'])
    def add_service_instance(service_name: str):
        """Add an instance to a service"""
        try:
            data = request.get_json()
            
            if 'url' not in data:
                return jsonify({
                    'success': False,
                    'error': 'Instance URL is required'
                }), 400
            
            instance_id = gateway_middleware.add_service_instance(
                service_name, 
                data['url'], 
                data.get('weight', 1)
            )
            
            return jsonify({
                'success': True,
                'data': {
                    'instance_id': instance_id,
                    'message': 'Instance added successfully'
                }
            })
        except Exception as e:
            logger.error(f"Error adding service instance: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @gateway_bp.route('/services/<service_name>/instances/<instance_id>', methods=['DELETE'])
    def remove_service_instance(service_name: str, instance_id: str):
        """Remove an instance from a service"""
        try:
            gateway_middleware.remove_service_instance(service_name, instance_id)
            
            return jsonify({
                'success': True,
                'data': {
                    'message': 'Instance removed successfully'
                }
            })
        except Exception as e:
            logger.error(f"Error removing service instance: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @gateway_bp.route('/services/health-check', methods=['POST'])
    def health_check_services():
        """Perform health check on all services"""
        try:
            results = gateway_middleware.health_check_all_services()
            return jsonify({
                'success': True,
                'data': results
            })
        except Exception as e:
            logger.error(f"Error performing health check: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @gateway_bp.route('/load-balancer/strategy', methods=['GET'])
    def get_load_balancing_strategy():
        """Get current load balancing strategy"""
        try:
            strategy_stats = gateway_middleware.load_balancer.get_load_balancing_metrics()
            return jsonify({
                'success': True,
                'data': strategy_stats
            })
        except Exception as e:
            logger.error(f"Error getting load balancing strategy: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @gateway_bp.route('/load-balancer/strategy', methods=['PUT'])
    def set_load_balancing_strategy():
        """Set load balancing strategy"""
        try:
            data = request.get_json()
            
            if 'strategy' not in data:
                return jsonify({
                    'success': False,
                    'error': 'Strategy is required'
                }), 400
            
            success = gateway_middleware.set_load_balancing_strategy(data['strategy'])
            
            if success:
                return jsonify({
                    'success': True,
                    'data': {
                        'message': f'Load balancing strategy set to {data["strategy"]}'
                    }
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Invalid strategy'
                }), 400
        except Exception as e:
            logger.error(f"Error setting load balancing strategy: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @gateway_bp.route('/rate-limits', methods=['GET'])
    def get_rate_limits():
        """Get rate limiting configuration"""
        try:
            rate_limit_stats = gateway_middleware.rate_limiter.get_gateway_rate_limit_stats()
            return jsonify({
                'success': True,
                'data': rate_limit_stats
            })
        except Exception as e:
            logger.error(f"Error getting rate limits: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @gateway_bp.route('/rate-limits', methods=['PUT'])
    def configure_rate_limit():
        """Configure rate limiting"""
        try:
            data = request.get_json()
            
            required_fields = ['limit_type', 'limit', 'window']
            for field in required_fields:
                if field not in data:
                    return jsonify({
                        'success': False,
                        'error': f'Missing required field: {field}'
                    }), 400
            
            success = gateway_middleware.configure_rate_limit(
                data['limit_type'],
                data['limit'],
                data['window'],
                data.get('strategy')
            )
            
            if success:
                return jsonify({
                    'success': True,
                    'data': {
                        'message': 'Rate limit configured successfully'
                    }
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Invalid configuration'
                }), 400
        except Exception as e:
            logger.error(f"Error configuring rate limit: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @gateway_bp.route('/rate-limits/status', methods=['GET'])
    def get_rate_limit_status():
        """Get current rate limit status"""
        try:
            if not hasattr(g, 'request_context'):
                return jsonify({
                    'success': False,
                    'error': 'No request context available'
                }), 400
            
            statuses = gateway_middleware.rate_limiter.get_all_rate_limit_statuses(g.request_context)
            return jsonify({
                'success': True,
                'data': statuses
            })
        except Exception as e:
            logger.error(f"Error getting rate limit status: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @gateway_bp.route('/alerts', methods=['GET'])
    def get_alerts():
        """Get all monitoring alerts"""
        try:
            alerts = gateway_middleware.get_alerts()
            return jsonify({
                'success': True,
                'data': {
                    'alerts': alerts,
                    'total': len(alerts)
                }
            })
        except Exception as e:
            logger.error(f"Error getting alerts: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @gateway_bp.route('/alerts', methods=['POST'])
    def create_alert():
        """Create a new monitoring alert"""
        try:
            data = request.get_json()
            
            required_fields = ['alert_id', 'name', 'level', 'condition', 'threshold']
            for field in required_fields:
                if field not in data:
                    return jsonify({
                        'success': False,
                        'error': f'Missing required field: {field}'
                    }), 400
            
            success = gateway_middleware.create_alert(
                data['alert_id'],
                data['name'],
                data['level'],
                data['condition'],
                data['threshold'],
                data.get('window', 300)
            )
            
            if success:
                return jsonify({
                    'success': True,
                    'data': {
                        'message': 'Alert created successfully'
                    }
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Invalid alert configuration'
                }), 400
        except Exception as e:
            logger.error(f"Error creating alert: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @gateway_bp.route('/alerts/<alert_id>/enable', methods=['POST'])
    def enable_alert(alert_id: str):
        """Enable an alert"""
        try:
            gateway_middleware.enable_alert(alert_id)
            return jsonify({
                'success': True,
                'data': {
                    'message': f'Alert {alert_id} enabled'
                }
            })
        except Exception as e:
            logger.error(f"Error enabling alert: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @gateway_bp.route('/alerts/<alert_id>/disable', methods=['POST'])
    def disable_alert(alert_id: str):
        """Disable an alert"""
        try:
            gateway_middleware.disable_alert(alert_id)
            return jsonify({
                'success': True,
                'data': {
                    'message': f'Alert {alert_id} disabled'
                }
            })
        except Exception as e:
            logger.error(f"Error disabling alert: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @gateway_bp.route('/alerts/<alert_id>', methods=['DELETE'])
    def delete_alert(alert_id: str):
        """Delete an alert"""
        try:
            gateway_middleware.delete_alert(alert_id)
            return jsonify({
                'success': True,
                'data': {
                    'message': f'Alert {alert_id} deleted'
                }
            })
        except Exception as e:
            logger.error(f"Error deleting alert: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @gateway_bp.route('/metrics', methods=['GET'])
    def get_metrics():
        """Get monitoring metrics"""
        try:
            time_window = request.args.get('time_window', 300, type=int)
            metrics = gateway_middleware.monitor.get_metrics_summary(time_window)
            return jsonify({
                'success': True,
                'data': metrics
            })
        except Exception as e:
            logger.error(f"Error getting metrics: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @gateway_bp.route('/metrics/export', methods=['GET'])
    def export_metrics():
        """Export metrics in specified format"""
        try:
            format_type = request.args.get('format', 'json')
            
            if format_type not in ['json']:
                return jsonify({
                    'success': False,
                    'error': 'Unsupported format. Supported formats: json'
                }), 400
            
            metrics_data = gateway_middleware.export_metrics(format_type)
            
            if format_type == 'json':
                return jsonify({
                    'success': True,
                    'data': metrics_data
                })
        except Exception as e:
            logger.error(f"Error exporting metrics: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @gateway_bp.route('/config', methods=['GET'])
    def get_gateway_config():
        """Get gateway configuration"""
        try:
            config = gateway_middleware.gateway_manager.get_config()
            return jsonify({
                'success': True,
                'data': config
            })
        except Exception as e:
            logger.error(f"Error getting gateway config: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @gateway_bp.route('/config', methods=['PUT'])
    def update_gateway_config():
        """Update gateway configuration"""
        try:
            data = request.get_json()
            
            if not data:
                return jsonify({
                    'success': False,
                    'error': 'Request body is required'
                }), 400
            
            gateway_middleware.gateway_manager.update_config(**data)
            
            return jsonify({
                'success': True,
                'data': {
                    'message': 'Gateway configuration updated successfully'
                }
            })
        except Exception as e:
            logger.error(f"Error updating gateway config: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @gateway_bp.route('/cleanup', methods=['POST'])
    def cleanup_old_data():
        """Clean up old data"""
        try:
            data = request.get_json() or {}
            max_age_hours = data.get('max_age_hours', 24)
            
            results = gateway_middleware.cleanup_old_data(max_age_hours)
            
            return jsonify({
                'success': True,
                'data': results
            })
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @gateway_bp.route('/versioning/versions', methods=['GET'])
    def get_available_versions():
        """Get all available API versions"""
        try:
            versions = gateway_middleware.router.get_all_versions()
            version_info = {}
            
            for version in versions:
                version_info[version] = gateway_middleware.router.get_version_info(version)
            
            return jsonify({
                'success': True,
                'data': {
                    'versions': version_info,
                    'default_version': gateway_middleware.gateway_manager.config.default_version
                }
            })
        except Exception as e:
            logger.error(f"Error getting versions: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @gateway_bp.route('/versioning/compatibility', methods=['GET'])
    def check_version_compatibility():
        """Check version compatibility"""
        try:
            from_version = request.args.get('from_version')
            to_version = request.args.get('to_version')
            
            if not from_version or not to_version:
                return jsonify({
                    'success': False,
                    'error': 'Both from_version and to_version parameters are required'
                }), 400
            
            compatibility = gateway_middleware.router.check_version_compatibility(
                from_version, to_version
            )
            
            return jsonify({
                'success': True,
                'data': compatibility
            })
        except Exception as e:
            logger.error(f"Error checking version compatibility: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @gateway_bp.route('/versioning/migration', methods=['GET'])
    def get_migration_path():
        """Get migration path between versions"""
        try:
            from_version = request.args.get('from_version')
            to_version = request.args.get('to_version')
            
            if not from_version or not to_version:
                return jsonify({
                    'success': False,
                    'error': 'Both from_version and to_version parameters are required'
                }), 400
            
            migration_path = gateway_middleware.router.get_migration_path(
                from_version, to_version
            )
            
            return jsonify({
                'success': True,
                'data': {
                    'from_version': from_version,
                    'to_version': to_version,
                    'migration_path': migration_path
                }
            })
        except Exception as e:
            logger.error(f"Error getting migration path: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
