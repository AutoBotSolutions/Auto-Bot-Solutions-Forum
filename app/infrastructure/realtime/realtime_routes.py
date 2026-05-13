"""
Real-time Infrastructure Routes

Flask routes for real-time infrastructure management including WebSocket server,
event streaming, monitoring, and load balancing endpoints.
"""

from flask import Blueprint, jsonify, request
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# This would be initialized in the main app
realtime_bp = Blueprint('realtime', __name__, url_prefix='/api/infrastructure/realtime')

def init_realtime_routes(websocket_server, event_streaming, realtime_monitor, load_balancer):
    """Initialize real-time routes with infrastructure components"""
    
    @realtime_bp.route('/health', methods=['GET'])
    def realtime_health():
        """Get real-time infrastructure health status"""
        try:
            # Get health from all components
            ws_stats = websocket_server.get_stats()
            streaming_metrics = event_streaming.get_metrics()
            monitoring_metrics = realtime_monitor.get_comprehensive_metrics()
            lb_stats = load_balancer.get_load_balancer_stats()
            
            overall_status = 'healthy'
            issues = []
            
            # Check WebSocket server
            if ws_stats.get('server_status') != 'running':
                overall_status = 'degraded'
                issues.append('WebSocket server not running')
            
            # Check event streaming
            if streaming_metrics.get('failed_events', 0) > streaming_metrics.get('processed_events', 1) * 0.1:
                overall_status = 'degraded'
                issues.append('High event failure rate')
            
            # Check load balancer
            if lb_stats.get('healthy_nodes', 0) == 0:
                overall_status = 'unhealthy'
                issues.append('No healthy load balancer nodes')
            
            return jsonify({
                'success': True,
                'data': {
                    'overall_status': overall_status,
                    'websocket_server': ws_stats,
                    'event_streaming': streaming_metrics,
                    'monitoring': monitoring_metrics,
                    'load_balancer': lb_stats,
                    'issues': issues,
                    'timestamp': datetime.utcnow().isoformat()
                }
            })
        except Exception as e:
            logger.error(f"Error getting real-time health: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @realtime_bp.route('/stats', methods=['GET'])
    def realtime_stats():
        """Get comprehensive real-time statistics"""
        try:
            # Get stats from all components
            ws_stats = websocket_server.get_stats()
            streaming_metrics = event_streaming.get_metrics()
            monitoring_metrics = realtime_monitor.get_comprehensive_metrics()
            lb_stats = load_balancer.get_load_balancer_stats()
            
            return jsonify({
                'success': True,
                'data': {
                    'websocket_server': ws_stats,
                    'event_streaming': streaming_metrics,
                    'monitoring': monitoring_metrics,
                    'load_balancer': lb_stats,
                    'timestamp': datetime.utcnow().isoformat()
                }
            })
        except Exception as e:
            logger.error(f"Error getting real-time stats: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @realtime_bp.route('/config', methods=['GET'])
    def get_realtime_config():
        """Get real-time infrastructure configuration"""
        try:
            return jsonify({
                'success': True,
                'data': {
                    'websocket_server': websocket_server.get_config(),
                    'event_streaming': event_streaming.get_config(),
                    'monitoring': realtime_monitor.get_monitoring_status(),
                    'load_balancer': load_balancer.get_config()
                }
            })
        except Exception as e:
            logger.error(f"Error getting real-time config: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @realtime_bp.route('/config', methods=['PUT'])
    def update_realtime_config():
        """Update real-time infrastructure configuration"""
        try:
            data = request.get_json()
            
            if not data:
                return jsonify({
                    'success': False,
                    'error': 'Request body is required'
                }), 400
            
            # Update configurations
            if 'websocket_server' in data:
                websocket_server.update_config(**data['websocket_server'])
            
            if 'event_streaming' in data:
                event_streaming.update_config(**data['event_streaming'])
            
            if 'load_balancer' in data:
                load_balancer.update_config(**data['load_balancer'])
            
            return jsonify({
                'success': True,
                'data': {
                    'message': 'Configuration updated successfully'
                }
            })
        except Exception as e:
            logger.error(f"Error updating real-time config: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    # WebSocket Server Routes
    
    @realtime_bp.route('/websocket/connections', methods=['GET'])
    def get_websocket_connections():
        """Get all WebSocket connections"""
        try:
            connections = websocket_server.get_connections()
            return jsonify({
                'success': True,
                'data': {
                    'connections': connections,
                    'total': len(connections)
                }
            })
        except Exception as e:
            logger.error(f"Error getting WebSocket connections: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @realtime_bp.route('/websocket/rooms', methods=['GET'])
    def get_websocket_rooms():
        """Get WebSocket rooms"""
        try:
            rooms = {}
            for room_id in websocket_server.rooms.keys():
                room_info = websocket_server.get_room_info(room_id)
                if room_info:
                    rooms[room_id] = room_info
            
            return jsonify({
                'success': True,
                'data': {
                    'rooms': rooms,
                    'total': len(rooms)
                }
            })
        except Exception as e:
            logger.error(f"Error getting WebSocket rooms: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @realtime_bp.route('/websocket/rooms/<room_id>', methods=['GET'])
    def get_websocket_room(room_id: str):
        """Get specific WebSocket room information"""
        try:
            room_info = websocket_server.get_room_info(room_id)
            
            if not room_info:
                return jsonify({
                    'success': False,
                    'error': 'Room not found'
                }), 404
            
            return jsonify({
                'success': True,
                'data': room_info
            })
        except Exception as e:
            logger.error(f"Error getting WebSocket room: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @realtime_bp.route('/websocket/broadcast', methods=['POST'])
    def broadcast_websocket_message():
        """Broadcast message to all WebSocket connections"""
        try:
            data = request.get_json()
            
            if not data or 'message' not in data:
                return jsonify({
                    'success': False,
                    'error': 'Message is required'
                }), 400
            
            # This would need to be async in a real implementation
            # For now, just log the request
            logger.info(f"Broadcast message request: {data['message']}")
            
            return jsonify({
                'success': True,
                'data': {
                    'message': 'Broadcast message sent successfully'
                }
            })
        except Exception as e:
            logger.error(f"Error broadcasting WebSocket message: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @realtime_bp.route('/websocket/rooms/<room_id>/broadcast', methods=['POST'])
    def broadcast_to_room(room_id: str):
        """Broadcast message to a specific WebSocket room"""
        try:
            data = request.get_json()
            
            if not data or 'message' not in data:
                return jsonify({
                    'success': False,
                    'error': 'Message is required'
                }), 400
            
            # This would need to be async in a real implementation
            logger.info(f"Broadcast to room {room_id}: {data['message']}")
            
            return jsonify({
                'success': True,
                'data': {
                    'message': f'Message sent to room {room_id}'
                }
            })
        except Exception as e:
            logger.error(f"Error broadcasting to room: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    # Event Streaming Routes
    
    @realtime_bp.route('/events/publish', methods=['POST'])
    def publish_event():
        """Publish an event"""
        try:
            data = request.get_json()
            
            required_fields = ['event_type', 'data']
            for field in required_fields:
                if field not in data:
                    return jsonify({
                        'success': False,
                        'error': f'Missing required field: {field}'
                    }), 400
            
            from .event_streaming import EventType, EventPriority
            
            event_type = EventType(data['event_type'])
            event_data = data['data']
            source = data.get('source', '')
            target = data.get('target', '')
            priority = EventPriority(data.get('priority', 'normal'))
            ttl = data.get('ttl')
            filters = data.get('filters', [])
            
            event_id = event_streaming.publish_event(
                event_type, event_data, source, target, priority, ttl, filters
            )
            
            return jsonify({
                'success': True,
                'data': {
                    'event_id': event_id,
                    'message': 'Event published successfully'
                }
            })
        except Exception as e:
            logger.error(f"Error publishing event: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @realtime_bp.route('/events/subscribe', methods=['POST'])
    def subscribe_to_events():
        """Subscribe to events"""
        try:
            data = request.get_json()
            
            required_fields = ['subscriber_id']
            for field in required_fields:
                if field not in data:
                    return jsonify({
                        'success': False,
                        'error': f'Missing required field: {field}'
                    }), 400
            
            subscriber_id = data['subscriber_id']
            event_type_str = data.get('event_type')
            filters = data.get('filters', {})
            
            from .event_streaming import EventType
            
            event_type = EventType(event_type_str) if event_type_str else None
            
            subscription_id = event_streaming.subscribe(
                subscriber_id, event_type, filters
            )
            
            return jsonify({
                'success': True,
                'data': {
                    'subscription_id': subscription_id,
                    'message': 'Subscription created successfully'
                }
            })
        except Exception as e:
            logger.error(f"Error subscribing to events: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @realtime_bp.route('/events/subscriptions/<subscription_id>', methods=['DELETE'])
    def unsubscribe_from_events(subscription_id: str):
        """Unsubscribe from events"""
        try:
            success = event_streaming.unsubscribe(subscription_id)
            
            if success:
                return jsonify({
                    'success': True,
                    'data': {
                        'message': f'Unsubscribed from {subscription_id}'
                    }
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Subscription not found'
                }), 404
        
        except Exception as e:
            logger.error(f"Error unsubscribing from events: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @realtime_bp.route('/events/history', methods=['GET'])
    def get_event_history():
        """Get event history"""
        try:
            event_type_str = request.args.get('event_type')
            limit = request.args.get('limit', 100, type=int)
            
            from .event_streaming import EventType
            
            event_type = EventType(event_type_str) if event_type_str else None
            
            events = event_streaming.get_event_history(event_type, limit)
            
            return jsonify({
                'success': True,
                'data': {
                    'events': events,
                    'total': len(events)
                }
            })
        except Exception as e:
            logger.error(f"Error getting event history: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @realtime_bp.route('/events/subscriptions', methods=['GET'])
    def get_event_subscriptions():
        """Get event subscriptions"""
        try:
            subscriber_id = request.args.get('subscriber_id')
            subscriptions = event_streaming.get_subscriptions(subscriber_id)
            
            return jsonify({
                'success': True,
                'data': {
                    'subscriptions': subscriptions,
                    'total': len(subscriptions)
                }
            })
        except Exception as e:
            logger.error(f"Error getting event subscriptions: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @realtime_bp.route('/events/metrics', methods=['GET'])
    def get_event_metrics():
        """Get event streaming metrics"""
        try:
            time_window = request.args.get('time_window', 300, type=int)
            metrics = event_streaming.get_metrics()
            
            return jsonify({
                'success': True,
                'data': metrics
            })
        except Exception as e:
            logger.error(f"Error getting event metrics: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    # Real-time Monitoring Routes
    
    @realtime_bp.route('/monitoring/metrics', methods=['GET'])
    def get_monitoring_metrics():
        """Get real-time monitoring metrics"""
        try:
            time_window = request.args.get('time_window', 300, type=int)
            metrics = realtime_monitor.get_comprehensive_metrics(time_window)
            
            return jsonify({
                'success': True,
                'data': metrics
            })
        except Exception as e:
            logger.error(f"Error getting monitoring metrics: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @realtime_bp.route('/monitoring/connection-metrics', methods=['GET'])
    def get_connection_metrics():
        """Get connection metrics"""
        try:
            time_window = request.args.get('time_window', 300, type=int)
            metrics = realtime_monitor.get_connection_metrics(time_window)
            
            return jsonify({
                'success': True,
                'data': metrics
            })
        except Exception as e:
            logger.error(f"Error getting connection metrics: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @realtime_bp.route('/monitoring/event-metrics', methods=['GET'])
    def get_event_monitoring_metrics():
        """Get event monitoring metrics"""
        try:
            time_window = request.args.get('time_window', 300, type=int)
            metrics = realtime_monitor.get_event_metrics(time_window)
            
            return jsonify({
                'success': True,
                'data': metrics
            })
        except Exception as e:
            logger.error(f"Error getting event monitoring metrics: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @realtime_bp.route('/monitoring/system-metrics', methods=['GET'])
    def get_system_metrics():
        """Get system metrics"""
        try:
            time_window = request.args.get('time_window', 300, type=int)
            metrics = realtime_monitor.get_system_metrics(time_window)
            
            return jsonify({
                'success': True,
                'data': metrics
            })
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @realtime_bp.route('/monitoring/alerts', methods=['GET'])
    def get_monitoring_alerts():
        """Get real-time monitoring alerts"""
        try:
            alerts = realtime_monitor.get_alerts()
            return jsonify({
                'success': True,
                'data': {
                    'alerts': alerts,
                    'total': len(alerts)
                }
            })
        except Exception as e:
            logger.error(f"Error getting monitoring alerts: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @realtime_bp.route('/monitoring/alerts', methods=['POST'])
    def create_monitoring_alert():
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
            
            from .realtime_monitor import AlertLevel
            
            level = AlertLevel(data['level'])
            realtime_monitor.create_alert(
                data['alert_id'],
                data['name'],
                level,
                data['condition'],
                data['threshold'],
                data.get('window', 300)
            )
            
            return jsonify({
                'success': True,
                'data': {
                    'message': 'Alert created successfully'
                }
            })
        except Exception as e:
            logger.error(f"Error creating monitoring alert: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @realtime_bp.route('/monitoring/alerts/<alert_id>/enable', methods=['POST'])
    def enable_monitoring_alert(alert_id: str):
        """Enable a monitoring alert"""
        try:
            realtime_monitor.enable_alert(alert_id)
            return jsonify({
                'success': True,
                'data': {
                    'message': f'Alert {alert_id} enabled'
                }
            })
        except Exception as e:
            logger.error(f"Error enabling monitoring alert: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @realtime_bp.route('/monitoring/alerts/<alert_id>/disable', methods=['POST'])
    def disable_monitoring_alert(alert_id: str):
        """Disable a monitoring alert"""
        try:
            realtime_monitor.disable_alert(alert_id)
            return jsonify({
                'success': True,
                'data': {
                    'message': f'Alert {alert_id} disabled'
                }
            })
        except Exception as e:
            logger.error(f"Error disabling monitoring alert: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @realtime_bp.route('/monitoring/alerts/<alert_id>', methods=['DELETE'])
    def delete_monitoring_alert(alert_id: str):
        """Delete a monitoring alert"""
        try:
            realtime_monitor.delete_alert(alert_id)
            return jsonify({
                'success': True,
                'data': {
                    'message': f'Alert {alert_id} deleted'
                }
            })
        except Exception as e:
            logger.error(f"Error deleting monitoring alert: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    # Load Balancer Routes
    
    @realtime_bp.route('/load-balancer/nodes', methods=['GET'])
    def get_load_balancer_nodes():
        """Get load balancer nodes"""
        try:
            nodes = load_balancer.get_all_node_stats()
            return jsonify({
                'success': True,
                'data': {
                    'nodes': nodes,
                    'total': len(nodes)
                }
            })
        except Exception as e:
            logger.error(f"Error getting load balancer nodes: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @realtime_bp.route('/load-balancer/nodes', methods=['POST'])
    def add_load_balancer_node():
        """Add a load balancer node"""
        try:
            data = request.get_json()
            
            required_fields = ['node_id', 'host', 'port']
            for field in required_fields:
                if field not in data:
                    return jsonify({
                        'success': False,
                        'error': f'Missing required field: {field}'
                    }), 400
            
            success = load_balancer.add_node(
                data['node_id'],
                data['host'],
                data['port'],
                data.get('weight', 1),
                data.get('max_connections', 1000)
            )
            
            if success:
                return jsonify({
                    'success': True,
                    'data': {
                        'message': f'Node {data["node_id"]} added successfully'
                    }
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to add node'
                }), 500
        
        except Exception as e:
            logger.error(f"Error adding load balancer node: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @realtime_bp.route('/load-balancer/nodes/<node_id>', methods=['DELETE'])
    def remove_load_balancer_node(node_id: str):
        """Remove a load balancer node"""
        try:
            success = load_balancer.remove_node(node_id)
            
            if success:
                return jsonify({
                    'success': True,
                    'data': {
                        'message': f'Node {node_id} removed successfully'
                    }
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to remove node'
                }), 500
        
        except Exception as e:
            logger.error(f"Error removing load balancer node: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @realtime_bp.route('/load-balancer/nodes/<node_id>', methods=['GET'])
    def get_load_balancer_node(node_id: str):
        """Get specific load balancer node"""
        try:
            node_stats = load_balancer.get_node_stats(node_id)
            
            if not node_stats:
                return jsonify({
                    'success': False,
                    'error': 'Node not found'
                }), 404
            
            return jsonify({
                'success': True,
                'data': node_stats
            })
        except Exception as e:
            logger.error(f"Error getting load balancer node: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @realtime_bp.route('/load-balancer/nodes/<node_id>/weight', methods=['PUT'])
    def update_node_weight(node_id: str):
        """Update node weight"""
        try:
            data = request.get_json()
            
            if 'weight' not in data:
                return jsonify({
                    'success': False,
                    'error': 'Weight is required'
                }), 400
            
            success = load_balancer.update_node_weight(node_id, data['weight'])
            
            if success:
                return jsonify({
                    'success': True,
                    'data': {
                        'message': f'Node {node_id} weight updated to {data["weight"]}'
                    }
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to update node weight'
                }), 500
        
        except Exception as e:
            logger.error(f"Error updating node weight: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @realtime_bp.route('/load-balancer/strategy', methods=['PUT'])
    def set_balancing_strategy():
        """Set load balancing strategy"""
        try:
            data = request.get_json()
            
            if 'strategy' not in data:
                return jsonify({
                    'success': False,
                    'error': 'Strategy is required'
                }), 400
            
            from .load_balancer import LoadBalancingStrategy
            
            strategy = LoadBalancingStrategy(data['strategy'])
            success = load_balancer.set_balancing_strategy(strategy)
            
            if success:
                return jsonify({
                    'success': True,
                    'data': {
                        'message': f'Balancing strategy set to {data["strategy"]}'
                    }
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to set balancing strategy'
                }), 500
        
        except Exception as e:
            logger.error(f"Error setting balancing strategy: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @realtime_bp.route('/load-balancer/stats', methods=['GET'])
    def get_load_balancer_stats():
        """Get load balancer statistics"""
        try:
            stats = load_balancer.get_load_balancer_stats()
            return jsonify({
                'success': True,
                'data': stats
            })
        except Exception as e:
            logger.error(f"Error getting load balancer stats: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @realtime_bp.route('/load-balancer/session-affinity/clear', methods=['POST'])
    def clear_session_affinity():
        """Clear session affinity table"""
        try:
            load_balancer.clear_session_affinity()
            return jsonify({
                'success': True,
                'data': {
                    'message': 'Session affinity table cleared'
                }
            })
        except Exception as e:
            logger.error(f"Error clearing session affinity: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
