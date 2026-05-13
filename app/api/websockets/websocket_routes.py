"""
WebSocket API Routes

Flask routes for WebSocket management and monitoring.
"""

from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# This would be initialized in the main app
websocket_bp = Blueprint('websocket', __name__, url_prefix='/api/websocket')

def init_websocket_routes(websocket_handlers):
    """Initialize WebSocket routes with handlers"""
    
    @websocket_bp.route('/stats', methods=['GET'])
    def get_websocket_stats():
        """Get WebSocket system statistics"""
        try:
            stats = websocket_handlers.get_stats()
            
            return jsonify({
                'success': True,
                'data': stats
            })
        except Exception as e:
            logger.error(f"Error getting WebSocket stats: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @websocket_bp.route('/connections', methods=['GET'])
    def get_connections():
        """Get all active WebSocket connections"""
        try:
            connections = []
            
            for sid, connection in websocket_handlers.ws_manager.connections.items():
                conn_info = connection.get_info()
                
                # Add authentication info
                auth_info = websocket_handlers.ws_auth.get_connection_auth(sid)
                if auth_info:
                    conn_info['authenticated'] = True
                    conn_info['user_info'] = {
                        'user_id': auth_info['user_id'],
                        'username': auth_info['username'],
                        'auth_method': auth_info['auth_method']
                    }
                else:
                    conn_info['authenticated'] = False
                
                # Add rate limiting info
                rate_stats = websocket_handlers.rate_limiter.get_connection_stats(sid)
                conn_info['rate_limiting'] = rate_stats
                
                connections.append(conn_info)
            
            return jsonify({
                'success': True,
                'data': {
                    'connections': connections,
                    'total': len(connections),
                    'timestamp': datetime.utcnow().isoformat()
                }
            })
        except Exception as e:
            logger.error(f"Error getting connections: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @websocket_bp.route('/rooms', methods=['GET'])
    def get_rooms():
        """Get all WebSocket rooms"""
        try:
            rooms = []
            
            for room_name, room in websocket_handlers.ws_manager.rooms.items():
                room_info = room.get_info()
                room_info['active'] = room.get_connection_count() > 0
                rooms.append(room_info)
            
            return jsonify({
                'success': True,
                'data': {
                    'rooms': rooms,
                    'total': len(rooms),
                    'active_rooms': len([r for r in rooms if r['active']]),
                    'timestamp': datetime.utcnow().isoformat()
                }
            })
        except Exception as e:
            logger.error(f"Error getting rooms: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @websocket_bp.route('/rooms/<room_name>', methods=['GET'])
    def get_room_details(room_name: str):
        """Get details for specific room"""
        try:
            room = websocket_handlers.ws_manager.get_room(room_name)
            
            if not room:
                return jsonify({
                    'success': False,
                    'error': 'Room not found',
                    'message': f'Room {room_name} does not exist'
                }), 404
            
            room_info = room.get_info()
            room_info['connections'] = [
                websocket_handlers.ws_manager.get_connection(sid).get_info()
                for sid in room.connections
                if websocket_handlers.ws_manager.get_connection(sid)
            ]
            
            # Add message history
            room_info['message_history'] = room.message_history[-10:]  # Last 10 messages
            
            return jsonify({
                'success': True,
                'data': room_info
            })
        except Exception as e:
            logger.error(f"Error getting room details: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @websocket_bp.route('/rooms/<room_name>/connections', methods=['GET'])
    def get_room_connections(room_name: str):
        """Get connections in specific room"""
        try:
            room = websocket_handlers.ws_manager.get_room(room_name)
            
            if not room:
                return jsonify({
                    'success': False,
                    'error': 'Room not found',
                    'message': f'Room {room_name} does not exist'
                }), 404
            
            connections = []
            for sid in room.connections:
                connection = websocket_handlers.ws_manager.get_connection(sid)
                if connection:
                    conn_info = connection.get_info()
                    
                    # Add authentication info
                    auth_info = websocket_handlers.ws_auth.get_connection_auth(sid)
                    if auth_info:
                        conn_info['authenticated'] = True
                        conn_info['user_info'] = {
                            'user_id': auth_info['user_id'],
                            'username': auth_info['username'],
                            'auth_method': auth_info['auth_method']
                        }
                    else:
                        conn_info['authenticated'] = False
                    
                    connections.append(conn_info)
            
            return jsonify({
                'success': True,
                'data': {
                    'room_name': room_name,
                    'connections': connections,
                    'total': len(connections),
                    'timestamp': datetime.utcnow().isoformat()
                }
            })
        except Exception as e:
            logger.error(f"Error getting room connections: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @websocket_bp.route('/users/<int:user_id>/connections', methods=['GET'])
    def get_user_connections(user_id: int):
        """Get all connections for a specific user"""
        try:
            connections = websocket_handlers.ws_manager.get_user_connections(user_id)
            
            connection_data = []
            for connection in connections:
                conn_info = connection.get_info()
                conn_info['rooms'] = list(connection.rooms)
                connection_data.append(conn_info)
            
            return jsonify({
                'success': True,
                'data': {
                    'user_id': user_id,
                    'connections': connection_data,
                    'total': len(connection_data),
                    'timestamp': datetime.utcnow().isoformat()
                }
            })
        except Exception as e:
            logger.error(f"Error getting user connections: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @websocket_bp.route('/send_message', methods=['POST'])
    def send_message_to_room():
        """Send message to WebSocket room (admin only)"""
        try:
            data = request.get_json()
            
            if not data:
                return jsonify({
                    'success': False,
                    'error': 'Request body is required'
                }), 400
            
            room_name = data.get('room')
            message = data.get('message')
            event = data.get('event', 'system_message')
            
            if not room_name or not message:
                return jsonify({
                    'success': False,
                    'error': 'Room and message are required'
                }), 400
            
            # Send message to room
            websocket_handlers.ws_events.send_system_message(message, 'info', room_name)
            
            return jsonify({
                'success': True,
                'data': {
                    'room': room_name,
                    'event': event,
                    'message': message,
                    'timestamp': datetime.utcnow().isoformat()
                }
            })
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @websocket_bp.route('/send_notification', methods=['POST'])
    def send_notification_to_user():
        """Send notification to user (admin only)"""
        try:
            data = request.get_json()
            
            if not data:
                return jsonify({
                    'success': False,
                    'error': 'Request body is required'
                }), 400
            
            user_id = data.get('user_id')
            notification = data.get('notification')
            
            if not user_id or not notification:
                return jsonify({
                    'success': False,
                    'error': 'User ID and notification are required'
                }), 400
            
            # Send notification to user
            websocket_handlers.ws_events.handle_notification({
                'user_id': user_id,
                'notification': notification,
                'type': notification.get('type', 'info')
            }, 'system')
            
            return jsonify({
                'success': True,
                'data': {
                    'user_id': user_id,
                    'notification': notification,
                    'timestamp': datetime.utcnow().isoformat()
                }
            })
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @websocket_bp.route('/broadcast', methods=['POST'])
    def broadcast_message():
        """Broadcast message to all connections (admin only)"""
        try:
            data = request.get_json()
            
            if not data:
                return jsonify({
                    'success': False,
                    'error': 'Request body is required'
                }), 400
            
            message = data.get('message')
            event = data.get('event', 'system_message')
            
            if not message:
                return jsonify({
                    'success': False,
                    'error': 'Message is required'
                }), 400
            
            # Broadcast message
            websocket_handlers.ws_manager.broadcast(event, {
                'message': message,
                'timestamp': datetime.utcnow().isoformat(),
                'source': 'admin_broadcast'
            })
            
            return jsonify({
                'success': True,
                'data': {
                    'event': event,
                    'message': message,
                    'timestamp': datetime.utcnow().isoformat()
                }
            })
        except Exception as e:
            logger.error(f"Error broadcasting message: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @websocket_bp.route('/health', methods=['GET'])
    def websocket_health():
        """Get WebSocket system health status"""
        try:
            stats = websocket_handlers.get_stats()
            websocket_stats = stats.get('websocket', {})
            
            # Calculate health metrics
            active_connections = websocket_stats.get('active_connections', 0)
            total_rooms = websocket_stats.get('total_rooms', 0)
            active_rooms = websocket_stats.get('active_rooms', 0)
            
            health_status = 'healthy'
            issues = []
            warnings = []
            
            # Check for issues
            if active_connections > 1000:
                health_status = 'warning'
                warnings.append(f"High number of active connections: {active_connections}")
            
            if active_rooms > 100:
                health_status = 'warning'
                warnings.append(f"High number of active rooms: {active_rooms}")
            
            # Check authentication
            auth_stats = stats.get('authentication', {})
            total_authenticated = auth_stats.get('total_authenticated', 0)
            
            if total_authenticated == 0 and active_connections > 0:
                health_status = 'warning'
                warnings.append("No authenticated connections found")
            
            return jsonify({
                'success': True,
                'data': {
                    'health_status': health_status,
                    'metrics': {
                        'active_connections': active_connections,
                        'total_rooms': total_rooms,
                        'active_rooms': active_rooms,
                        'authenticated_connections': total_authenticated
                    },
                    'issues': issues,
                    'warnings': warnings,
                    'timestamp': datetime.utcnow().isoformat()
                }
            })
        except Exception as e:
            logger.error(f"Error getting WebSocket health: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @websocket_bp.route('/cleanup', methods=['POST'])
    def cleanup_connections():
        """Clean up inactive connections (admin only)"""
        try:
            data = request.get_json() or {}
            max_inactive_minutes = data.get('max_inactive_minutes', 30)
            
            cleaned_count = websocket_handlers.ws_manager.cleanup_inactive_connections(max_inactive_minutes)
            
            return jsonify({
                'success': True,
                'data': {
                    'cleaned_connections': cleaned_count,
                    'max_inactive_minutes': max_inactive_minutes,
                    'timestamp': datetime.utcnow().isoformat()
                }
            })
        except Exception as e:
            logger.error(f"Error cleaning up connections: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @websocket_bp.route('/config', methods=['GET'])
    def get_websocket_config():
        """Get WebSocket configuration"""
        try:
            config = {
                'websocket': {
                    'max_connections_per_room': 1000,
                    'rate_limit_messages_per_minute': 60,
                    'cleanup_interval_minutes': 5,
                    'message_history_limit': 100
                },
                'authentication': {
                    'methods': ['jwt', 'api_key'],
                    'jwt_secret_configured': bool(websocket_handlers.ws_auth.secret_key)
                },
                'events': {
                    'supported_events': [
                        'connect', 'disconnect', 'authenticate',
                        'join_room', 'leave_room', 'message',
                        'post_created', 'post_updated', 'post_deleted',
                        'comment_created', 'comment_updated', 'comment_deleted',
                        'typing', 'stop_typing', 'notification',
                        'live_update'
                    ]
                },
                'rooms': {
                    'types': ['user', 'post', 'forum', 'notification', 'admin'],
                    'auto_cleanup': True,
                    'history_limit': 100
                }
            }
            
            return jsonify({
                'success': True,
                'data': config
            })
        except Exception as e:
            logger.error(f"Error getting WebSocket config: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
