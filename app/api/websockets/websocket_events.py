"""
WebSocket Events

Defines WebSocket event types and handlers for real-time features.
"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

from flask import g
from flask_socketio import emit

from .websocket_auth import ws_authenticated, ws_require_permission

logger = logging.getLogger(__name__)

class EventType(Enum):
    """WebSocket event types"""
    # Connection events
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    JOIN_ROOM = "join_room"
    LEAVE_ROOM = "leave_room"
    
    # Message events
    MESSAGE = "message"
    TYPING = "typing"
    STOP_TYPING = "stop_typing"
    
    # Content events
    POST_CREATED = "post_created"
    POST_UPDATED = "post_updated"
    POST_DELETED = "post_deleted"
    COMMENT_CREATED = "comment_created"
    COMMENT_UPDATED = "comment_updated"
    COMMENT_DELETED = "comment_deleted"
    
    # User events
    USER_ONLINE = "user_online"
    USER_OFFLINE = "user_offline"
    USER_JOINED = "user_joined"
    USER_LEFT = "user_left"
    
    # Notification events
    NOTIFICATION = "notification"
    SYSTEM_MESSAGE = "system_message"
    
    # Real-time events
    LIVE_UPDATE = "live_update"
    STATUS_CHANGE = "status_change"

class WebSocketEvents:
    """WebSocket event handlers"""
    
    def __init__(self, websocket_manager):
        self.ws_manager = websocket_manager
        self._register_event_handlers()
    
    def _register_event_handlers(self):
        """Register all event handlers"""
        self.ws_manager.on_event('post_created', self.handle_post_created)
        self.ws_manager.on_event('post_updated', self.handle_post_updated)
        self.ws_manager.on_event('post_deleted', self.handle_post_deleted)
        self.ws_manager.on_event('comment_created', self.handle_comment_created)
        self.ws_manager.on_event('comment_updated', self.handle_comment_updated)
        self.ws_manager.on_event('comment_deleted', self.handle_comment_deleted)
        self.ws_manager.on_event('typing', self.handle_typing)
        self.ws_manager.on_event('stop_typing', self.handle_stop_typing)
        self.ws_manager.on_event('notification', self.handle_notification)
        self.ws_manager.on_event('live_update', self.handle_live_update)
    
    def handle_post_created(self, data, sid: str):
        """Handle post creation event"""
        try:
            post_id = data.get('post_id')
            post_data = data.get('post_data', {})
            
            # Send to general forum room
            self.ws_manager.send_to_room('forum', EventType.POST_CREATED.value, {
                'post_id': post_id,
                'post': post_data,
                'timestamp': datetime.utcnow().isoformat(),
                'sender_sid': sid
            })
            
            # Send to post-specific room
            post_room = f"post_{post_id}"
            self.ws_manager.send_to_room(post_room, EventType.POST_CREATED.value, {
                'post_id': post_id,
                'post': post_data,
                'timestamp': datetime.utcnow().isoformat(),
                'sender_sid': sid
            })
            
            logger.info(f"Post created event sent: post_id={post_id}")
            
        except Exception as e:
            logger.error(f"Error handling post_created: {e}")
    
    def handle_post_updated(self, data, sid: str):
        """Handle post update event"""
        try:
            post_id = data.get('post_id')
            post_data = data.get('post_data', {})
            changes = data.get('changes', [])
            
            # Send to post-specific room
            post_room = f"post_{post_id}"
            self.ws_manager.send_to_room(post_room, EventType.POST_UPDATED.value, {
                'post_id': post_id,
                'post': post_data,
                'changes': changes,
                'timestamp': datetime.utcnow().isoformat(),
                'sender_sid': sid
            })
            
            logger.info(f"Post updated event sent: post_id={post_id}")
            
        except Exception as e:
            logger.error(f"Error handling post_updated: {e}")
    
    def handle_post_deleted(self, data, sid: str):
        """Handle post deletion event"""
        try:
            post_id = data.get('post_id')
            
            # Send to post-specific room
            post_room = f"post_{post_id}"
            self.ws_manager.send_to_room(post_room, EventType.POST_DELETED.value, {
                'post_id': post_id,
                'timestamp': datetime.utcnow().isoformat(),
                'sender_sid': sid
            })
            
            # Send to general forum room
            self.ws_manager.send_to_room('forum', EventType.POST_DELETED.value, {
                'post_id': post_id,
                'timestamp': datetime.utcnow().isoformat(),
                'sender_sid': sid
            })
            
            logger.info(f"Post deleted event sent: post_id={post_id}")
            
        except Exception as e:
            logger.error(f"Error handling post_deleted: {e}")
    
    def handle_comment_created(self, data, sid: str):
        """Handle comment creation event"""
        try:
            comment_id = data.get('comment_id')
            post_id = data.get('post_id')
            comment_data = data.get('comment_data', {})
            
            # Send to post-specific room
            post_room = f"post_{post_id}"
            self.ws_manager.send_to_room(post_room, EventType.COMMENT_CREATED.value, {
                'comment_id': comment_id,
                'post_id': post_id,
                'comment': comment_data,
                'timestamp': datetime.utcnow().isoformat(),
                'sender_sid': sid
            })
            
            logger.info(f"Comment created event sent: comment_id={comment_id}, post_id={post_id}")
            
        except Exception as e:
            logger.error(f"Error handling comment_created: {e}")
    
    def handle_comment_updated(self, data, sid: str):
        """Handle comment update event"""
        try:
            comment_id = data.get('comment_id')
            post_id = data.get('post_id')
            comment_data = data.get('comment_data', {})
            changes = data.get('changes', [])
            
            # Send to post-specific room
            post_room = f"post_{post_id}"
            self.ws_manager.send_to_room(post_room, EventType.COMMENT_UPDATED.value, {
                'comment_id': comment_id,
                'post_id': post_id,
                'comment': comment_data,
                'changes': changes,
                'timestamp': datetime.utcnow().isoformat(),
                'sender_sid': sid
            })
            
            logger.info(f"Comment updated event sent: comment_id={comment_id}")
            
        except Exception as e:
            logger.error(f"Error handling comment_updated: {e}")
    
    def handle_comment_deleted(self, data, sid: str):
        """Handle comment deletion event"""
        try:
            comment_id = data.get('comment_id')
            post_id = data.get('post_id')
            
            # Send to post-specific room
            post_room = f"post_{post_id}"
            self.ws_manager.send_to_room(post_room, EventType.COMMENT_DELETED.value, {
                'comment_id': comment_id,
                'post_id': post_id,
                'timestamp': datetime.utcnow().isoformat(),
                'sender_sid': sid
            })
            
            logger.info(f"Comment deleted event sent: comment_id={comment_id}")
            
        except Exception as e:
            logger.error(f"Error handling comment_deleted: {e}")
    
    def handle_typing(self, data, sid: str):
        """Handle typing indicator"""
        try:
            post_id = data.get('post_id')
            user_id = data.get('user_id')
            username = data.get('username')
            
            if post_id:
                post_room = f"post_{post_id}"
                self.ws_manager.send_to_room(post_room, EventType.TYPING.value, {
                    'user_id': user_id,
                    'username': username,
                    'post_id': post_id,
                    'timestamp': datetime.utcnow().isoformat(),
                    'sender_sid': sid
                }, include_sender=False)
            
            logger.debug(f"Typing indicator sent: user_id={user_id}, post_id={post_id}")
            
        except Exception as e:
            logger.error(f"Error handling typing: {e}")
    
    def handle_stop_typing(self, data, sid: str):
        """Handle stop typing indicator"""
        try:
            post_id = data.get('post_id')
            user_id = data.get('user_id')
            username = data.get('username')
            
            if post_id:
                post_room = f"post_{post_id}"
                self.ws_manager.send_to_room(post_room, EventType.STOP_TYPING.value, {
                    'user_id': user_id,
                    'username': username,
                    'post_id': post_id,
                    'timestamp': datetime.utcnow().isoformat(),
                    'sender_sid': sid
                }, include_sender=False)
            
            logger.debug(f"Stop typing indicator sent: user_id={user_id}, post_id={post_id}")
            
        except Exception as e:
            logger.error(f"Error handling stop_typing: {e}")
    
    def handle_notification(self, data, sid: str):
        """Handle notification event"""
        try:
            user_id = data.get('user_id')
            notification_data = data.get('notification', {})
            notification_type = data.get('type', 'info')
            
            # Send to user-specific room
            user_room = f"user_{user_id}"
            self.ws_manager.send_to_room(user_room, EventType.NOTIFICATION.value, {
                'type': notification_type,
                'notification': notification_data,
                'timestamp': datetime.utcnow().isoformat(),
                'sender_sid': sid
            })
            
            logger.info(f"Notification sent: user_id={user_id}, type={notification_type}")
            
        except Exception as e:
            logger.error(f"Error handling notification: {e}")
    
    def handle_live_update(self, data, sid: str):
        """Handle live update event"""
        try:
            update_type = data.get('type')
            target_id = data.get('target_id')
            update_data = data.get('data', {})
            room = data.get('room', 'forum')
            
            self.ws_manager.send_to_room(room, EventType.LIVE_UPDATE.value, {
                'type': update_type,
                'target_id': target_id,
                'data': update_data,
                'timestamp': datetime.utcnow().isoformat(),
                'sender_sid': sid
            })
            
            logger.info(f"Live update sent: type={update_type}, target_id={target_id}")
            
        except Exception as e:
            logger.error(f"Error handling live_update: {e}")
    
    def send_user_online(self, user_id: int, username: str):
        """Send user online notification"""
        try:
            self.ws_manager.broadcast(EventType.USER_ONLINE.value, {
                'user_id': user_id,
                'username': username,
                'timestamp': datetime.utcnow().isoformat()
            })
            
            logger.info(f"User online notification sent: user_id={user_id}")
            
        except Exception as e:
            logger.error(f"Error sending user online: {e}")
    
    def send_user_offline(self, user_id: int, username: str):
        """Send user offline notification"""
        try:
            self.ws_manager.broadcast(EventType.USER_OFFLINE.value, {
                'user_id': user_id,
                'username': username,
                'timestamp': datetime.utcnow().isoformat()
            })
            
            logger.info(f"User offline notification sent: user_id={user_id}")
            
        except Exception as e:
            logger.error(f"Error sending user offline: {e}")
    
    def send_system_message(self, message: str, level: str = 'info', room: str = 'forum'):
        """Send system message"""
        try:
            self.ws_manager.send_to_room(room, EventType.SYSTEM_MESSAGE.value, {
                'message': message,
                'level': level,
                'timestamp': datetime.utcnow().isoformat()
            })
            
            logger.info(f"System message sent: level={level}, message={message[:50]}...")
            
        except Exception as e:
            logger.error(f"Error sending system message: {e}")
    
    def send_status_change(self, entity_type: str, entity_id: str, status: str, data: Dict[str, Any] = None):
        """Send status change notification"""
        try:
            room = f"{entity_type}_{entity_id}"
            self.ws_manager.send_to_room(room, EventType.STATUS_CHANGE.value, {
                'entity_type': entity_type,
                'entity_id': entity_id,
                'status': status,
                'data': data or {},
                'timestamp': datetime.utcnow().isoformat()
            })
            
            logger.info(f"Status change sent: {entity_type}_{entity_id} = {status}")
            
        except Exception as e:
            logger.error(f"Error sending status change: {e}")

class EventProcessor:
    """Processes and validates WebSocket events"""
    
    def __init__(self):
        self.event_validators = {}
        self.event_transformers = {}
        self._register_validators()
        self._register_transformers()
    
    def _register_validators(self):
        """Register event validators"""
        self.event_validators['post_created'] = self._validate_post_event
        self.event_validators['post_updated'] = self._validate_post_event
        self.event_validators['post_deleted'] = self._validate_post_event
        self.event_validators['comment_created'] = self._validate_comment_event
        self.event_validators['comment_updated'] = self._validate_comment_event
        self.event_validators['comment_deleted'] = self._validate_comment_event
        self.event_validators['typing'] = self._validate_typing_event
        self.event_validators['notification'] = self._validate_notification_event
    
    def _register_transformers(self):
        """Register event transformers"""
        self.event_transformers['post_created'] = self._transform_post_event
        self.event_transformers['post_updated'] = self._transform_post_event
        self.event_transformers['comment_created'] = self._transform_comment_event
        self.event_transformers['notification'] = self._transform_notification_event
    
    def process_event(self, event_type: str, data: Dict[str, Any], sid: str) -> Optional[Dict[str, Any]]:
        """Process and validate event data"""
        try:
            # Validate event
            if event_type in self.event_validators:
                if not self.event_validators[event_type](data, sid):
                    logger.warning(f"Event validation failed: {event_type}")
                    return None
            
            # Transform event
            if event_type in self.event_transformers:
                data = self.event_transformers[event_type](data, sid)
            
            # Add metadata
            processed_data = {
                'type': event_type,
                'data': data,
                'sid': sid,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            return processed_data
        
        except Exception as e:
            logger.error(f"Error processing event {event_type}: {e}")
            return None
    
    def _validate_post_event(self, data: Dict[str, Any], sid: str) -> bool:
        """Validate post-related event"""
        return 'post_id' in data and isinstance(data['post_id'], int)
    
    def _validate_comment_event(self, data: Dict[str, Any], sid: str) -> bool:
        """Validate comment-related event"""
        return ('comment_id' in data and isinstance(data['comment_id'], int) and
                'post_id' in data and isinstance(data['post_id'], int))
    
    def _validate_typing_event(self, data: Dict[str, Any], sid: str) -> bool:
        """Validate typing event"""
        return ('post_id' in data and isinstance(data['post_id'], int) and
                'user_id' in data and isinstance(data['user_id'], int))
    
    def _validate_notification_event(self, data: Dict[str, Any], sid: str) -> bool:
        """Validate notification event"""
        return ('user_id' in data and isinstance(data['user_id'], int) and
                'notification' in data and isinstance(data['notification'], dict))
    
    def _transform_post_event(self, data: Dict[str, Any], sid: str) -> Dict[str, Any]:
        """Transform post event data"""
        # Add timestamp if not present
        if 'timestamp' not in data:
            data['timestamp'] = datetime.utcnow().isoformat()
        
        # Add sender info if available
        ws_auth = g.get('ws_auth')
        if ws_auth and ws_auth.is_authenticated(sid):
            auth_info = ws_auth.get_connection_auth(sid)
            if auth_info:
                data['sender'] = {
                    'user_id': auth_info['user_id'],
                    'username': auth_info['username']
                }
        
        return data
    
    def _transform_comment_event(self, data: Dict[str, Any], sid: str) -> Dict[str, Any]:
        """Transform comment event data"""
        # Add timestamp if not present
        if 'timestamp' not in data:
            data['timestamp'] = datetime.utcnow().isoformat()
        
        # Add sender info if available
        ws_auth = g.get('ws_auth')
        if ws_auth and ws_auth.is_authenticated(sid):
            auth_info = ws_auth.get_connection_auth(sid)
            if auth_info:
                data['sender'] = {
                    'user_id': auth_info['user_id'],
                    'username': auth_info['username']
                }
        
        return data
    
    def _transform_notification_event(self, data: Dict[str, Any], sid: str) -> Dict[str, Any]:
        """Transform notification event data"""
        # Add timestamp if not present
        if 'timestamp' not in data:
            data['timestamp'] = datetime.utcnow().isoformat()
        
        # Add default type if not present
        if 'type' not in data:
            data['type'] = 'info'
        
        return data
