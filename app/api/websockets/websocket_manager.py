"""
WebSocket Manager

Manages WebSocket connections, rooms, and message broadcasting.
"""

import json
import asyncio
import logging
from typing import Dict, List, Set, Optional, Any, Callable
from datetime import datetime
from enum import Enum
import uuid
import weakref

from flask_socketio import SocketIO, emit, join_room, leave_room, disconnect
from flask import request

logger = logging.getLogger(__name__)

class ConnectionStatus(Enum):
    """WebSocket connection status"""
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"

class RoomType(Enum):
    """Room types for WebSocket connections"""
    USER = "user"
    POST = "post"
    FORUM = "forum"
    NOTIFICATION = "notification"
    ADMIN = "admin"

class WebSocketConnection:
    """Represents a WebSocket connection"""
    
    def __init__(self, sid: str, user_id: Optional[int] = None):
        self.sid = sid
        self.user_id = user_id
        self.status = ConnectionStatus.CONNECTING
        self.connected_at = datetime.utcnow()
        self.last_activity = datetime.utcnow()
        self.rooms: Set[str] = set()
        self.metadata: Dict[str, Any] = {}
        self.message_count = 0
        self.ip_address = None
    
    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = datetime.utcnow()
        self.message_count += 1
    
    def join_room(self, room: str):
        """Join a room"""
        self.rooms.add(room)
    
    def leave_room(self, room: str):
        """Leave a room"""
        self.rooms.discard(room)
    
    def get_info(self) -> Dict[str, Any]:
        """Get connection information"""
        return {
            'sid': self.sid,
            'user_id': self.user_id,
            'status': self.status.value,
            'connected_at': self.connected_at.isoformat(),
            'last_activity': self.last_activity.isoformat(),
            'rooms': list(self.rooms),
            'message_count': self.message_count,
            'ip_address': self.ip_address
        }

class WebSocketRoom:
    """Represents a WebSocket room"""
    
    def __init__(self, name: str, room_type: RoomType, max_connections: int = 1000):
        self.name = name
        self.room_type = room_type
        self.max_connections = max_connections
        self.connections: Set[str] = set()
        self.created_at = datetime.utcnow()
        self.metadata: Dict[str, Any] = {}
        self.message_history: List[Dict[str, Any]] = []
        self.max_history = 100
    
    def add_connection(self, sid: str):
        """Add connection to room"""
        if len(self.connections) >= self.max_connections:
            return False
        
        self.connections.add(sid)
        return True
    
    def remove_connection(self, sid: str):
        """Remove connection from room"""
        self.connections.discard(sid)
    
    def get_connection_count(self) -> int:
        """Get number of connections in room"""
        return len(self.connections)
    
    def add_message(self, message: Dict[str, Any]):
        """Add message to history"""
        self.message_history.append({
            'message': message,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        # Limit history size
        if len(self.message_history) > self.max_history:
            self.message_history = self.message_history[-self.max_history:]
    
    def get_info(self) -> Dict[str, Any]:
        """Get room information"""
        return {
            'name': self.name,
            'type': self.room_type.value,
            'connections': len(self.connections),
            'max_connections': self.max_connections,
            'created_at': self.created_at.isoformat(),
            'metadata': self.metadata
        }

class WebSocketManager:
    """Manages WebSocket connections and rooms"""
    
    def __init__(self, socketio: SocketIO):
        self.socketio = socketio
        self.connections: Dict[str, WebSocketConnection] = {}
        self.rooms: Dict[str, WebSocketRoom] = {}
        self.user_connections: Dict[int, Set[str]] = {}
        self.event_handlers: Dict[str, List[Callable]] = {}
        self.message_handlers: Dict[str, List[Callable]] = {}
        self.stats = {
            'total_connections': 0,
            'active_connections': 0,
            'total_messages': 0,
            'total_rooms': 0
        }
        
        # Register default event handlers
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """Register default event handlers"""
        self.on_event('connect', self._handle_connect)
        self.on_event('disconnect', self._handle_disconnect)
        self.on_event('join_room', self._handle_join_room)
        self.on_event('leave_room', self._handle_leave_room)
        self.on_event('message', self._handle_message)
        self.on_event('ping', self._handle_ping)
        self.on_event('pong', self._handle_pong)
    
    def get_connection(self, sid: str) -> Optional[WebSocketConnection]:
        """Get connection by SID"""
        return self.connections.get(sid)
    
    def get_user_connections(self, user_id: int) -> List[WebSocketConnection]:
        """Get all connections for a user"""
        user_sids = self.user_connections.get(user_id, set())
        return [self.connections[sid] for sid in user_sids if sid in self.connections]
    
    def get_room(self, name: str) -> Optional[WebSocketRoom]:
        """Get room by name"""
        return self.rooms.get(name)
    
    def create_room(self, name: str, room_type: RoomType, 
                    max_connections: int = 1000, **metadata) -> WebSocketRoom:
        """Create a new room"""
        if name in self.rooms:
            return self.rooms[name]
        
        room = WebSocketRoom(name, room_type, max_connections)
        room.metadata.update(metadata)
        self.rooms[name] = room
        self.stats['total_rooms'] += 1
        
        logger.info(f"Created room: {name} (type: {room_type.value})")
        return room
    
    def delete_room(self, name: str):
        """Delete a room"""
        if name in self.rooms:
            room = self.rooms[name]
            
            # Remove all connections from room
            for sid in list(room.connections):
                self.leave_room(sid, name)
            
            del self.rooms[name]
            self.stats['total_rooms'] -= 1
            
            logger.info(f"Deleted room: {name}")
    
    def join_room(self, sid: str, room_name: str) -> bool:
        """Join connection to room"""
        connection = self.get_connection(sid)
        if not connection:
            return False
        
        room = self.get_room(room_name)
        if not room:
            # Create room if it doesn't exist
            room = self.create_room(room_name, RoomType.FORUM)
        
        if not room.add_connection(sid):
            emit('error', {'message': 'Room is full'}, room=sid)
            return False
        
        connection.join_room(room_name)
        join_room(room_name, room=sid)
        
        # Update user connections mapping
        if connection.user_id:
            if connection.user_id not in self.user_connections:
                self.user_connections[connection.user_id] = set()
            self.user_connections[connection.user_id].add(sid)
        
        # Notify room
        emit('user_joined', {
            'user_id': connection.user_id,
            'sid': sid,
            'room': room_name,
            'timestamp': datetime.utcnow().isoformat()
        }, room=room_name)
        
        logger.info(f"Connection {sid} joined room {room_name}")
        return True
    
    def leave_room(self, sid: str, room_name: str):
        """Leave connection from room"""
        connection = self.get_connection(sid)
        if not connection:
            return
        
        room = self.get_room(room_name)
        if room:
            room.remove_connection(sid)
            leave_room(room_name, room=sid)
            connection.leave_room(room_name)
            
            # Update user connections mapping
            if connection.user_id and connection.user_id in self.user_connections:
                self.user_connections[connection.user_id].discard(sid)
                if not self.user_connections[connection.user_id]:
                    del self.user_connections[connection.user_id]
            
            # Notify room
            emit('user_left', {
                'user_id': connection.user_id,
                'sid': sid,
                'room': room_name,
                'timestamp': datetime.utcnow().isoformat()
            }, room=room_name)
            
            # Delete room if empty
            if room.get_connection_count() == 0:
                self.delete_room(room_name)
            
            logger.info(f"Connection {sid} left room {room_name}")
    
    def send_to_connection(self, sid: str, event: str, data: Any):
        """Send message to specific connection"""
        try:
            emit(event, data, room=sid)
            self.stats['total_messages'] += 1
        except Exception as e:
            logger.error(f"Error sending to connection {sid}: {e}")
    
    def send_to_user(self, user_id: int, event: str, data: Any):
        """Send message to all connections for a user"""
        connections = self.get_user_connections(user_id)
        for connection in connections:
            self.send_to_connection(connection.sid, event, data)
    
    def send_to_room(self, room_name: str, event: str, data: Any, 
                    include_sender: bool = True):
        """Send message to all connections in a room"""
        room = self.get_room(room_name)
        if not room:
            return
        
        try:
            if include_sender:
                emit(event, data, room=room_name)
            else:
                # Send to all except sender (would need sender SID)
                emit(event, data, room=room_name)
            
            self.stats['total_messages'] += 1
            
            # Add to room history
            room.add_message({
                'event': event,
                'data': data,
                'timestamp': datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error sending to room {room_name}: {e}")
    
    def broadcast(self, event: str, data: Any):
        """Broadcast message to all connections"""
        try:
            emit(event, data, broadcast=True)
            self.stats['total_messages'] += 1
        except Exception as e:
            logger.error(f"Error broadcasting: {e}")
    
    def on_event(self, event: str, handler: Callable):
        """Register event handler"""
        if event not in self.event_handlers:
            self.event_handlers[event] = []
        self.event_handlers[event].append(handler)
        
        # Register with SocketIO
        self.socketio.on(event, self._handle_event)
    
    def on_message(self, message_type: str, handler: Callable):
        """Register message handler"""
        if message_type not in self.message_handlers:
            self.message_handlers[message_type] = []
        self.message_handlers[message_type].append(handler)
    
    def _handle_event(self, event: str, *args, **kwargs):
        """Handle WebSocket event"""
        try:
            sid = request.sid
            
            # Update connection activity
            connection = self.get_connection(sid)
            if connection:
                connection.update_activity()
            
            # Call registered handlers
            if event in self.event_handlers:
                for handler in self.event_handlers[event]:
                    try:
                        result = handler(*args, **kwargs)
                        if result is False:
                            return  # Stop processing
                    except Exception as e:
                        logger.error(f"Error in event handler for {event}: {e}")
            
            # Handle specific message types
            if event == 'message' and args:
                message_data = args[0]
                if isinstance(message_data, dict) and 'type' in message_data:
                    message_type = message_data['type']
                    if message_type in self.message_handlers:
                        for handler in self.message_handlers[message_type]:
                            try:
                                handler(message_data, sid)
                            except Exception as e:
                                logger.error(f"Error in message handler for {message_type}: {e}")
        
        except Exception as e:
            logger.error(f"Error handling event {event}: {e}")
    
    def _handle_connect(self, *args, **kwargs):
        """Handle new connection"""
        try:
            sid = request.sid
            ip_address = request.remote_addr
            
            connection = WebSocketConnection(sid, ip_address=ip_address)
            connection.status = ConnectionStatus.CONNECTED
            self.connections[sid] = connection
            self.stats['total_connections'] += 1
            self.stats['active_connections'] += 1
            
            logger.info(f"New connection: {sid} from {ip_address}")
            
            emit('connected', {
                'sid': sid,
                'timestamp': datetime.utcnow().isoformat(),
                'server_time': datetime.utcnow().isoformat()
            }, room=sid)
            
        except Exception as e:
            logger.error(f"Error handling connect: {e}")
    
    def _handle_disconnect(self, *args, **kwargs):
        """Handle connection disconnect"""
        try:
            sid = request.sid
            connection = self.get_connection(sid)
            
            if connection:
                # Leave all rooms
                for room_name in list(connection.rooms):
                    self.leave_room(sid, room_name)
                
                # Update user connections mapping
                if connection.user_id and connection.user_id in self.user_connections:
                    self.user_connections[connection.user_id].discard(sid)
                    if not self.user_connections[connection.user_id]:
                        del self.user_connections[connection.user_id]
                
                # Remove connection
                connection.status = ConnectionStatus.DISCONNECTED
                del self.connections[sid]
                self.stats['active_connections'] -= 1
                
                logger.info(f"Connection disconnected: {sid}")
        
        except Exception as e:
            logger.error(f"Error handling disconnect: {e}")
    
    def _handle_join_room(self, data, *args, **kwargs):
        """Handle join room request"""
        try:
            sid = request.sid
            room_name = data.get('room')
            
            if room_name:
                self.join_room(sid, room_name)
            else:
                emit('error', {'message': 'Room name is required'}, room=sid)
        
        except Exception as e:
            logger.error(f"Error handling join_room: {e}")
    
    def _handle_leave_room(self, data, *args, **kwargs):
        """Handle leave room request"""
        try:
            sid = request.sid
            room_name = data.get('room')
            
            if room_name:
                self.leave_room(sid, room_name)
            else:
                emit('error', {'message': 'Room name is required'}, room=sid)
        
        except Exception as e:
            logger.error(f"Error handling leave_room: {e}")
    
    def _handle_message(self, data, *args, **kwargs):
        """Handle generic message"""
        try:
            sid = request.sid
            connection = self.get_connection(sid)
            
            if connection:
                connection.update_activity()
                
                # Broadcast to user's rooms if no specific room specified
                if not data.get('room'):
                    for room_name in connection.rooms:
                        self.send_to_room(room_name, 'message', {
                            'user_id': connection.user_id,
                            'sid': sid,
                            'message': data,
                            'timestamp': datetime.utcnow().isoformat()
                        }, include_sender=False)
        
        except Exception as e:
            logger.error(f"Error handling message: {e}")
    
    def _handle_ping(self, *args, **kwargs):
        """Handle ping message"""
        try:
            sid = request.sid
            emit('pong', {
                'timestamp': datetime.utcnow().isoformat()
            }, room=sid)
        
        except Exception as e:
            logger.error(f"Error handling ping: {e}")
    
    def _handle_pong(self, *args, **kwargs):
        """Handle pong message"""
        try:
            sid = request.sid
            connection = self.get_connection(sid)
            if connection:
                connection.update_activity()
        
        except Exception as e:
            logger.error(f"Error handling pong: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get WebSocket statistics"""
        active_rooms = len([r for r in self.rooms.values() if r.get_connection_count() > 0])
        
        return {
            **self.stats,
            'active_rooms': active_rooms,
            'total_rooms': len(self.rooms),
            'connections_per_user': {
                user_id: len(sids) for user_id, sids in self.user_connections.items()
            },
            'room_details': {
                name: room.get_info() for name, room in self.rooms.items()
            }
        }
    
    def cleanup_inactive_connections(self, max_inactive_minutes: int = 30):
        """Clean up inactive connections"""
        cutoff_time = datetime.utcnow() - timedelta(minutes=max_inactive_minutes)
        
        inactive_sids = []
        for sid, connection in self.connections.items():
            if connection.last_activity < cutoff_time:
                inactive_sids.append(sid)
        
        for sid in inactive_sids:
            logger.info(f"Cleaning up inactive connection: {sid}")
            # This will trigger the disconnect handler
            self.socketio.disconnect(sid)
        
        return len(inactive_sids)
