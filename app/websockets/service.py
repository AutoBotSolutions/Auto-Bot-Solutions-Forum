"""
WebSocket Service for Real-time Features

This service provides WebSocket functionality for real-time features including:
- Live comment notifications
- Real-time vote count updates
- Online user presence indicators
- Real-time typing indicators
"""

from flask import current_app, request
from flask_socketio import SocketIO, emit, join_room, leave_room, disconnect
from flask_login import current_user
from datetime import datetime, timedelta, timezone
import json
import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

class WebSocketService:
    """WebSocket service for real-time features"""
    
    def __init__(self, socketio: SocketIO):
        self.socketio = socketio
        self.connected_users: Dict[str, Dict[str, Any]] = {}
        self.user_rooms: Dict[str, List[str]] = {}
        self.typing_users: Dict[str, Dict[str, datetime]] = {}
        
    def get_user_socket_id(self, user_id: int) -> Optional[str]:
        """Get socket ID for a user"""
        for socket_id, user_data in self.connected_users.items():
            if user_data.get('user_id') == user_id:
                return socket_id
        return None
    
    def get_user_room(self, user_id: int) -> str:
        """Get room name for a user"""
        return f"user_{user_id}"
    
    def get_post_room(self, post_id: int) -> str:
        """Get room name for a post"""
        return f"post_{post_id}"
    
    def get_category_room(self, category_id: int) -> str:
        """Get room name for a category"""
        return f"category_{category_id}"
    
    def add_connected_user(self, socket_id: str, user_id: int, username: str):
        """Add a connected user to the tracking system"""
        self.connected_users[socket_id] = {
            'user_id': user_id,
            'username': username,
            'connected_at': datetime.now(timezone.utc),
            'last_seen': datetime.now(timezone.utc),
            'ip_address': request.remote_addr if request else None
        }
        
        # Join user to their personal room (only if in request context)
        user_room = self.get_user_room(user_id)
        try:
            join_room(user_room)
        except RuntimeError:
            # Not in request context, skip join_room for now
            pass
        
        # Track user rooms
        if user_room not in self.user_rooms:
            self.user_rooms[user_room] = []
        self.user_rooms[user_room].append(socket_id)
        
        logger.info(f"User {username} (ID: {user_id}) connected via WebSocket")
        
        # Broadcast user online status
        self.broadcast_user_status(user_id, username, True)
    
    def remove_connected_user(self, socket_id: str):
        """Remove a connected user from the tracking system"""
        if socket_id in self.connected_users:
            user_data = self.connected_users[socket_id]
            user_id = user_data['user_id']
            username = user_data['username']
            
            # Remove from user rooms
            user_room = self.get_user_room(user_id)
            if user_room in self.user_rooms:
                if socket_id in self.user_rooms[user_room]:
                    self.user_rooms[user_room].remove(socket_id)
                if not self.user_rooms[user_room]:
                    del self.user_rooms[user_room]
                    # Broadcast user offline status
                    self.broadcast_user_status(user_id, username, False)
            
            # Remove typing indicators
            self.remove_user_typing(user_id)
            
            # Leave all rooms (only if in request context)
            try:
                leave_room(user_room)
            except RuntimeError:
                # Not in request context, skip leave_room for now
                pass
            
            del self.connected_users[socket_id]
            
            logger.info(f"User {username} (ID: {user_id}) disconnected from WebSocket")
    
    def update_user_activity(self, socket_id: str):
        """Update user's last seen timestamp"""
        if socket_id in self.connected_users:
            self.connected_users[socket_id]['last_seen'] = datetime.now(timezone.utc)
    
    def get_online_users(self) -> List[Dict[str, Any]]:
        """Get list of online users"""
        current_time = datetime.now(timezone.utc)
        online_users = []
        
        for socket_id, user_data in self.connected_users.items():
            # Check if user is still active (last seen within 5 minutes)
            if current_time - user_data['last_seen'] <= timedelta(minutes=5):
                online_users.append({
                    'user_id': user_data['user_id'],
                    'username': user_data['username'],
                    'connected_at': user_data['connected_at'],
                    'last_seen': user_data['last_seen']
                })
        
        return online_users
    
    def broadcast_user_status(self, user_id: int, username: str, is_online: bool):
        """Broadcast user online/offline status"""
        status_data = {
            'user_id': user_id,
            'username': username,
            'is_online': is_online,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        # Broadcast to all connected clients
        self.socketio.emit('user_status', status_data)
    
    def join_post_room(self, user_id: int, post_id: int):
        """Join a user to a post room"""
        post_room = self.get_post_room(post_id)
        user_room = self.get_user_room(user_id)
        
        # Get user's socket IDs
        socket_ids = self.user_rooms.get(user_room, [])
        
        for socket_id in socket_ids:
            try:
                join_room(post_room, sid=socket_id)
            except RuntimeError:
                # Not in request context, skip join_room for now
                pass
        
        logger.info(f"User {user_id} joined post room {post_room}")
    
    def leave_post_room(self, user_id: int, post_id: int):
        """Remove a user from a post room"""
        post_room = self.get_post_room(post_id)
        user_room = self.get_user_room(user_id)
        
        # Get user's socket IDs
        socket_ids = self.user_rooms.get(user_room, [])
        
        for socket_id in socket_ids:
            try:
                leave_room(post_room, sid=socket_id)
            except RuntimeError:
                # Not in request context, skip leave_room for now
                pass
        
        logger.info(f"User {user_id} left post room {post_room}")
    
    def broadcast_new_comment(self, post_id: int, comment_data: Dict[str, Any]):
        """Broadcast new comment to post room"""
        post_room = self.get_post_room(post_id)
        
        comment_notification = {
            'type': 'new_comment',
            'post_id': post_id,
            'comment': comment_data,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        self.socketio.emit('comment_notification', comment_notification, room=post_room)
        logger.info(f"Broadcasted new comment for post {post_id}")
    
    def broadcast_vote_update(self, content_type: str, content_id: int, vote_data: Dict[str, Any]):
        """Broadcast vote update to relevant rooms"""
        if content_type == 'post':
            room = self.get_post_room(content_id)
        elif content_type == 'comment':
            # For comments, broadcast to the parent post room
            room = self.get_post_room(vote_data.get('post_id', content_id))
        else:
            return
        
        vote_notification = {
            'type': 'vote_update',
            'content_type': content_type,
            'content_id': content_id,
            'vote_data': vote_data,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        self.socketio.emit('vote_update', vote_notification, room=room)
        logger.info(f"Broadcasted vote update for {content_type} {content_id}")
    
    def set_user_typing(self, user_id: int, username: str, post_id: int):
        """Set user as typing in a post"""
        typing_key = f"{user_id}_{post_id}"
        self.typing_users[typing_key] = {
            'user_id': user_id,
            'username': username,
            'post_id': post_id,
            'started_at': datetime.now(timezone.utc)
        }
        
        # Broadcast typing indicator
        post_room = self.get_post_room(post_id)
        typing_notification = {
            'type': 'user_typing',
            'user_id': user_id,
            'username': username,
            'post_id': post_id,
            'is_typing': True,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        self.socketio.emit('typing_indicator', typing_notification, room=post_room)
        logger.info(f"User {username} is typing in post {post_id}")
    
    def remove_user_typing(self, user_id: int, post_id: Optional[int] = None):
        """Remove user from typing indicators"""
        if post_id:
            typing_key = f"{user_id}_{post_id}"
        else:
            # Remove all typing indicators for this user
            keys_to_remove = []
            for key in self.typing_users:
                if key.startswith(f"{user_id}_"):
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                typing_data = self.typing_users[key]
                del self.typing_users[key]
                
                # Broadcast stop typing
                post_room = self.get_post_room(typing_data['post_id'])
                typing_notification = {
                    'type': 'user_typing',
                    'user_id': user_id,
                    'username': typing_data['username'],
                    'post_id': typing_data['post_id'],
                    'is_typing': False,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
                
                self.socketio.emit('typing_indicator', typing_notification, room=post_room)
            
            return
        
        # Remove specific typing indicator
        if typing_key in self.typing_users:
            typing_data = self.typing_users[typing_key]
            del self.typing_users[typing_key]
            
            # Broadcast stop typing
            post_room = self.get_post_room(typing_data['post_id'])
            typing_notification = {
                'type': 'user_typing',
                'user_id': user_id,
                'username': typing_data['username'],
                'post_id': typing_data['post_id'],
                'is_typing': False,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            self.socketio.emit('typing_indicator', typing_notification, room=post_room)
            logger.info(f"User {typing_data['username']} stopped typing in post {typing_data['post_id']}")
    
    def get_typing_users(self, post_id: int) -> List[Dict[str, Any]]:
        """Get list of users typing in a post"""
        current_time = datetime.now(timezone.utc)
        typing_users = []
        
        for typing_key, typing_data in self.typing_users.items():
            if (typing_data['post_id'] == post_id and 
                current_time - typing_data['started_at'] <= timedelta(seconds=10)):
                typing_users.append({
                    'user_id': typing_data['user_id'],
                    'username': typing_data['username'],
                    'started_at': typing_data['started_at']
                })
        
        return typing_users
    
    def broadcast_notification(self, user_id: int, notification_data: Dict[str, Any]):
        """Send notification to specific user"""
        user_room = self.get_user_room(user_id)
        
        notification = {
            'type': 'notification',
            'notification': notification_data,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        self.socketio.emit('notification', notification, room=user_room)
        logger.info(f"Sent notification to user {user_id}")
    
    def broadcast_system_message(self, message: str, message_type: str = 'info'):
        """Broadcast system message to all connected users"""
        system_notification = {
            'type': 'system_message',
            'message': message,
            'message_type': message_type,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        self.socketio.emit('system_message', system_notification, broadcast=True)
        logger.info(f"Broadcasted system message: {message}")
    
    def cleanup_inactive_users(self):
        """Clean up inactive users from tracking"""
        current_time = datetime.now(timezone.utc)
        inactive_threshold = timedelta(minutes=10)
        
        inactive_users = []
        for socket_id, user_data in self.connected_users.items():
            if current_time - user_data['last_seen'] > inactive_threshold:
                inactive_users.append(socket_id)
        
        for socket_id in inactive_users:
            self.remove_connected_user(socket_id)
        
        if inactive_users:
            logger.info(f"Cleaned up {len(inactive_users)} inactive WebSocket connections")
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get WebSocket connection statistics"""
        return {
            'total_connections': len(self.connected_users),
            'online_users': len(self.get_online_users()),
            'active_typing_sessions': len(self.typing_users),
            'user_rooms': len(self.user_rooms),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
