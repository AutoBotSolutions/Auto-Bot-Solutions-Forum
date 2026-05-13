"""
WebSocket Handlers

Flask-SocketIO event handlers for WebSocket connections.
"""

import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from flask import request, g
from flask_socketio import emit, join_room, leave_room, disconnect

from .websocket_manager import WebSocketManager, ConnectionStatus, RoomType
from .websocket_auth import WebSocketAuth, WebSocketRateLimiter, ws_authenticated, ws_require_permission
from .websocket_events import WebSocketEvents, EventProcessor

logger = logging.getLogger(__name__)

class WebSocketHandlers:
    """WebSocket event handlers for Flask-SocketIO"""
    
    def __init__(self, socketio, app=None):
        self.socketio = socketio
        self.app = app
        
        # Initialize components
        self.ws_manager = WebSocketManager(socketio)
        self.ws_auth = WebSocketAuth(app.config.get('JWT_SECRET_KEY') if app else None)
        self.ws_events = WebSocketEvents(self.ws_manager)
        self.event_processor = EventProcessor()
        self.rate_limiter = WebSocketRateLimiter()
        
        # Register SocketIO handlers
        self._register_handlers()
        
        # Start cleanup tasks
        self._start_cleanup_tasks()
    
    def _register_handlers(self):
        """Register all SocketIO event handlers"""
        self.socketio.on('connect', self.handle_connect)
        self.socketio.on('disconnect', self.handle_disconnect)
        self.socketio.on('authenticate', self.handle_authenticate)
        self.socketio.on('join_room', self.handle_join_room)
        self.socketio.on('leave_room', self.handle_leave_room)
        self.socketio.on('send_message', self.handle_send_message)
        self.socketio.on('get_room_info', self.handle_get_room_info)
        self.socketio.on('get_connection_info', self.handle_get_connection_info)
        self.socketio.on('ping', self.handle_ping)
        self.socketio.on('pong', self.handle_pong)
        
        # Register message type handlers
        self.socketio.on('post_created', self.handle_post_created)
        self.socketio.on('post_updated', self.handle_post_updated)
        self.socketio.on('post_deleted', self.handle_post_deleted)
        self.socketio.on('comment_created', self.handle_comment_created)
        self.socketio.on('comment_updated', self.handle_comment_updated)
        self.socketio.on('comment_deleted', self.handle_comment_deleted)
        self.socketio.on('typing', self.handle_typing)
        self.socketio.on('stop_typing', self.handle_stop_typing)
        self.socketio.on('notification', self.handle_notification)
        self.socketio.on('live_update', self.handle_live_update)
    
    def handle_connect(self, *args, **kwargs):
        """Handle new WebSocket connection"""
        try:
            sid = request.sid
            ip_address = request.remote_addr
            
            logger.info(f"New WebSocket connection: {sid} from {ip_address}")
            
            # Store auth in context for handlers
            g.ws_auth = self.ws_auth
            g.ws_manager = self.ws_manager
            g.rate_limiter = self.rate_limiter
            
            emit('connected', {
                'sid': sid,
                'timestamp': datetime.utcnow().isoformat(),
                'server_time': datetime.utcnow().isoformat(),
                'message': 'Connected to WebSocket server'
            }, room=sid)
            
        except Exception as e:
            logger.error(f"Error in connect handler: {e}")
            disconnect()
    
    def handle_disconnect(self, *args, **kwargs):
        """Handle WebSocket disconnection"""
        try:
            sid = request.sid
            connection = self.ws_manager.get_connection(sid)
            
            if connection:
                # Send user offline notification if authenticated
                auth_info = self.ws_auth.get_connection_auth(sid)
                if auth_info:
                    self.ws_events.send_user_offline(
                        auth_info['user_id'], 
                        auth_info['username']
                    )
                
                # Logout connection
                self.ws_auth.logout_connection(sid)
            
            logger.info(f"WebSocket disconnected: {sid}")
            
        except Exception as e:
            logger.error(f"Error in disconnect handler: {e}")
    
    def handle_authenticate(self, data, *args, **kwargs):
        """Handle authentication request"""
        try:
            sid = request.sid
            
            auth_info = self.ws_auth.authenticate_connection(sid, data)
            
            if auth_info:
                # Join user-specific room
                user_room = f"user_{auth_info['user_id']}"
                self.ws_manager.join_room(sid, user_room)
                
                # Send user online notification
                self.ws_events.send_user_online(
                    auth_info['user_id'],
                    auth_info['username']
                )
                
                emit('authenticated', {
                    'success': True,
                    'user_info': auth_info,
                    'timestamp': datetime.utcnow().isoformat()
                }, room=sid)
                
                logger.info(f"WebSocket authenticated: user_id={auth_info['user_id']}, sid={sid}")
            else:
                emit('authentication_error', {
                    'success': False,
                    'message': 'Authentication failed',
                    'timestamp': datetime.utcnow().isoformat()
                }, room=sid)
                
                logger.warning(f"WebSocket authentication failed: sid={sid}")
        
        except Exception as e:
            logger.error(f"Error in authenticate handler: {e}")
            emit('authentication_error', {
                'success': False,
                'message': 'Authentication error',
                'timestamp': datetime.utcnow().isoformat()
            }, room=sid)
    
    def handle_join_room(self, data, *args, **kwargs):
        """Handle room join request"""
        try:
            sid = request.sid
            room_name = data.get('room')
            
            if not room_name:
                emit('error', {
                    'message': 'Room name is required',
                    'timestamp': datetime.utcnow().isoformat()
                }, room=sid)
                return
            
            # Check if user has permission to join room
            if room_name.startswith('admin_'):
                auth_info = self.ws_auth.get_connection_auth(sid)
                if not auth_info or not self.ws_auth.has_role(sid, 'admin'):
                    emit('error', {
                        'message': 'Admin permission required',
                        'timestamp': datetime.utcnow().isoformat()
                    }, room=sid)
                    return
            
            # Join room
            if self.ws_manager.join_room(sid, room_name):
                emit('room_joined', {
                    'room': room_name,
                    'timestamp': datetime.utcnow().isoformat()
                }, room=sid)
                
                logger.info(f"Connection {sid} joined room {room_name}")
            else:
                emit('error', {
                    'message': 'Failed to join room',
                    'timestamp': datetime.utcnow().isoformat()
                }, room=sid)
        
        except Exception as e:
            logger.error(f"Error in join_room handler: {e}")
            emit('error', {
                'message': 'Room join error',
                'timestamp': datetime.utcnow().isoformat()
            }, room=request.sid)
    
    def handle_leave_room(self, data, *args, **kwargs):
        """Handle room leave request"""
        try:
            sid = request.sid
            room_name = data.get('room')
            
            if not room_name:
                emit('error', {
                    'message': 'Room name is required',
                    'timestamp': datetime.utcnow().isoformat()
                }, room=sid)
                return
            
            self.ws_manager.leave_room(sid, room_name)
            
            emit('room_left', {
                'room': room_name,
                'timestamp': datetime.utcnow().isoformat()
            }, room=sid)
            
            logger.info(f"Connection {sid} left room {room_name}")
        
        except Exception as e:
            logger.error(f"Error in leave_room handler: {e}")
            emit('error', {
                'message': 'Room leave error',
                'timestamp': datetime.utcnow().isoformat()
            }, room=request.sid)
    
    def handle_send_message(self, data, *args, **kwargs):
        """Handle message sending"""
        try:
            sid = request.sid
            
            # Check rate limit
            if not self.rate_limiter.check_rate_limit(sid):
                emit('error', {
                    'message': 'Rate limit exceeded',
                    'timestamp': datetime.utcnow().isoformat()
                }, room=sid)
                return
            
            # Check authentication
            auth_info = self.ws_auth.get_connection_auth(sid)
            if not auth_info:
                emit('error', {
                    'message': 'Authentication required',
                    'timestamp': datetime.utcnow().isoformat()
                }, room=sid)
                return
            
            message = data.get('message', '').strip()
            room = data.get('room', 'forum')
            
            if not message:
                emit('error', {
                    'message': 'Message cannot be empty',
                    'timestamp': datetime.utcnow().isoformat()
                }, room=sid)
                return
            
            # Create message data
            message_data = {
                'message': message,
                'user_id': auth_info['user_id'],
                'username': auth_info['username'],
                'timestamp': datetime.utcnow().isoformat(),
                'sid': sid
            }
            
            # Send to room
            self.ws_manager.send_to_room(room, 'message', message_data, include_sender=False)
            
            # Send confirmation to sender
            emit('message_sent', {
                'room': room,
                'message': message,
                'timestamp': datetime.utcnow().isoformat()
            }, room=sid)
            
            logger.info(f"Message sent to room {room}: user_id={auth_info['user_id']}")
        
        except Exception as e:
            logger.error(f"Error in send_message handler: {e}")
            emit('error', {
                'message': 'Message send error',
                'timestamp': datetime.utcnow().isoformat()
            }, room=request.sid)
    
    def handle_get_room_info(self, data, *args, **kwargs):
        """Handle room info request"""
        try:
            sid = request.sid
            room_name = data.get('room')
            
            if not room_name:
                emit('error', {
                    'message': 'Room name is required',
                    'timestamp': datetime.utcnow().isoformat()
                }, room=sid)
                return
            
            room = self.ws_manager.get_room(room_name)
            if not room:
                emit('error', {
                    'message': 'Room not found',
                    'timestamp': datetime.utcnow().isoformat()
                }, room=sid)
                return
            
            room_info = room.get_info()
            room_info['user_count'] = room.get_connection_count()
            
            emit('room_info', {
                'room': room_name,
                'info': room_info,
                'timestamp': datetime.utcnow().isoformat()
            }, room=sid)
        
        except Exception as e:
            logger.error(f"Error in get_room_info handler: {e}")
            emit('error', {
                'message': 'Room info error',
                'timestamp': datetime.utcnow().isoformat()
            }, room=request.sid)
    
    def handle_get_connection_info(self, *args, **kwargs):
        """Handle connection info request"""
        try:
            sid = request.sid
            connection = self.ws_manager.get_connection(sid)
            
            if not connection:
                emit('error', {
                    'message': 'Connection not found',
                    'timestamp': datetime.utcnow().isoformat()
                }, room=sid)
                return
            
            connection_info = connection.get_info()
            
            # Add rate limiting stats
            rate_stats = self.rate_limiter.get_connection_stats(sid)
            connection_info['rate_limiting'] = rate_stats
            
            # Add authentication info
            auth_info = self.ws_auth.get_connection_auth(sid)
            if auth_info:
                connection_info['authenticated'] = True
                connection_info['user_info'] = {
                    'user_id': auth_info['user_id'],
                    'username': auth_info['username'],
                    'auth_method': auth_info['auth_method']
                }
            else:
                connection_info['authenticated'] = False
            
            emit('connection_info', {
                'info': connection_info,
                'timestamp': datetime.utcnow().isoformat()
            }, room=sid)
        
        except Exception as e:
            logger.error(f"Error in get_connection_info handler: {e}")
            emit('error', {
                'message': 'Connection info error',
                'timestamp': datetime.utcnow().isoformat()
            }, room=request.sid)
    
    def handle_ping(self, *args, **kwargs):
        """Handle ping message"""
        try:
            sid = request.sid
            
            emit('pong', {
                'timestamp': datetime.utcnow().isoformat()
            }, room=sid)
        
        except Exception as e:
            logger.error(f"Error in ping handler: {e}")
    
    def handle_pong(self, *args, **kwargs):
        """Handle pong message"""
        try:
            sid = request.sid
            connection = self.ws_manager.get_connection(sid)
            if connection:
                connection.update_activity()
        
        except Exception as e:
            logger.error(f"Error in pong handler: {e}")
    
    # Content event handlers
    def handle_post_created(self, data, *args, **kwargs):
        """Handle post creation event"""
        try:
            sid = request.sid
            
            # Check rate limit
            if not self.rate_limiter.check_rate_limit(sid):
                return
            
            # Check authentication
            auth_info = self.ws_auth.get_connection_auth(sid)
            if not auth_info:
                return
            
            # Process event
            processed_event = self.event_processor.process_event('post_created', data, sid)
            if processed_event:
                self.ws_events.handle_post_created(processed_event['data'], sid)
        
        except Exception as e:
            logger.error(f"Error in post_created handler: {e}")
    
    def handle_post_updated(self, data, *args, **kwargs):
        """Handle post update event"""
        try:
            sid = request.sid
            
            # Check rate limit
            if not self.rate_limiter.check_rate_limit(sid):
                return
            
            # Check authentication
            auth_info = self.ws_auth.get_connection_auth(sid)
            if not auth_info:
                return
            
            # Process event
            processed_event = self.event_processor.process_event('post_updated', data, sid)
            if processed_event:
                self.ws_events.handle_post_updated(processed_event['data'], sid)
        
        except Exception as e:
            logger.error(f"Error in post_updated handler: {e}")
    
    def handle_post_deleted(self, data, *args, **kwargs):
        """Handle post deletion event"""
        try:
            sid = request.sid
            
            # Check rate limit
            if not self.rate_limiter.check_rate_limit(sid):
                return
            
            # Check authentication
            auth_info = self.ws_auth.get_connection_auth(sid)
            if not auth_info:
                return
            
            # Process event
            processed_event = self.event_processor.process_event('post_deleted', data, sid)
            if processed_event:
                self.ws_events.handle_post_deleted(processed_event['data'], sid)
        
        except Exception as e:
            logger.error(f"Error in post_deleted handler: {e}")
    
    def handle_comment_created(self, data, *args, **kwargs):
        """Handle comment creation event"""
        try:
            sid = request.sid
            
            # Check rate limit
            if not self.rate_limiter.check_rate_limit(sid):
                return
            
            # Check authentication
            auth_info = self.ws_auth.get_connection_auth(sid)
            if not auth_info:
                return
            
            # Process event
            processed_event = self.event_processor.process_event('comment_created', data, sid)
            if processed_event:
                self.ws_events.handle_comment_created(processed_event['data'], sid)
        
        except Exception as e:
            logger.error(f"Error in comment_created handler: {e}")
    
    def handle_comment_updated(self, data, *args, **kwargs):
        """Handle comment update event"""
        try:
            sid = request.sid
            
            # Check rate limit
            if not self.rate_limiter.check_rate_limit(sid):
                return
            
            # Check authentication
            auth_info = self.ws_auth.get_connection_auth(sid)
            if not auth_info:
                return
            
            # Process event
            processed_event = self.event_processor.process_event('comment_updated', data, sid)
            if processed_event:
                self.ws_events.handle_comment_updated(processed_event['data'], sid)
        
        except Exception as e:
            logger.error(f"Error in comment_updated handler: {e}")
    
    def handle_comment_deleted(self, data, *args, **kwargs):
        """Handle comment deletion event"""
        try:
            sid = request.sid
            
            # Check rate limit
            if not self.rate_limiter.check_rate_limit(sid):
                return
            
            # Check authentication
            auth_info = self.ws_auth.get_connection_auth(sid)
            if not auth_info:
                return
            
            # Process event
            processed_event = self.event_processor.process_event('comment_deleted', data, sid)
            if processed_event:
                self.ws_events.handle_comment_deleted(processed_event['data'], sid)
        
        except Exception as e:
            logger.error(f"Error in comment_deleted handler: {e}")
    
    def handle_typing(self, data, *args, **kwargs):
        """Handle typing indicator"""
        try:
            sid = request.sid
            
            # Check authentication
            auth_info = self.ws_auth.get_connection_auth(sid)
            if not auth_info:
                return
            
            # Process event
            processed_event = self.event_processor.process_event('typing', data, sid)
            if processed_event:
                self.ws_events.handle_typing(processed_event['data'], sid)
        
        except Exception as e:
            logger.error(f"Error in typing handler: {e}")
    
    def handle_stop_typing(self, data, *args, **kwargs):
        """Handle stop typing indicator"""
        try:
            sid = request.sid
            
            # Check authentication
            auth_info = self.ws_auth.get_connection_auth(sid)
            if not auth_info:
                return
            
            # Process event
            processed_event = self.event_processor.process_event('stop_typing', data, sid)
            if processed_event:
                self.ws_events.handle_stop_typing(processed_event['data'], sid)
        
        except Exception as e:
            logger.error(f"Error in stop_typing handler: {e}")
    
    def handle_notification(self, data, *args, **kwargs):
        """Handle notification event"""
        try:
            sid = request.sid
            
            # Check authentication
            auth_info = self.ws_auth.get_connection_auth(sid)
            if not auth_info:
                return
            
            # Check admin permission for sending notifications
            if not self.ws_auth.has_role(sid, 'admin'):
                return
            
            # Process event
            processed_event = self.event_processor.process_event('notification', data, sid)
            if processed_event:
                self.ws_events.handle_notification(processed_event['data'], sid)
        
        except Exception as e:
            logger.error(f"Error in notification handler: {e}")
    
    def handle_live_update(self, data, *args, **kwargs):
        """Handle live update event"""
        try:
            sid = request.sid
            
            # Check authentication
            auth_info = self.ws_auth.get_connection_auth(sid)
            if not auth_info:
                return
            
            # Process event
            processed_event = self.event_processor.process_event('live_update', data, sid)
            if processed_event:
                self.ws_events.handle_live_update(processed_event['data'], sid)
        
        except Exception as e:
            logger.error(f"Error in live_update handler: {e}")
    
    def _start_cleanup_tasks(self):
        """Start background cleanup tasks"""
        def cleanup_task():
            """Background cleanup task"""
            try:
                # Clean up inactive connections
                inactive_count = self.ws_manager.cleanup_inactive_connections()
                if inactive_count > 0:
                    logger.info(f"Cleaned up {inactive_count} inactive WebSocket connections")
                
                # Clean up rate limiting data
                rate_cleanup_count = self.rate_limiter.cleanup_old_connections()
                if rate_cleanup_count > 0:
                    logger.info(f"Cleaned up rate limiting data for {rate_cleanup_count} connections")
                
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")
        
        # Schedule cleanup task every 5 minutes
        import threading
        import time
        
        def run_cleanup():
            while True:
                time.sleep(300)  # 5 minutes
                cleanup_task()
        
        cleanup_thread = threading.Thread(target=run_cleanup, daemon=True)
        cleanup_thread.start()
        
        logger.info("WebSocket cleanup task started")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get WebSocket system statistics"""
        try:
            ws_stats = self.ws_manager.get_stats()
            auth_stats = self.ws_auth.get_auth_stats()
            
            return {
                'websocket': ws_stats,
                'authentication': auth_stats,
                'timestamp': datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error getting WebSocket stats: {e}")
            return {'error': str(e)}
