# WebSocket API System Documentation

## Overview

The WebSocket API System provides real-time communication capabilities with WebSocket connections, authentication, room management, and event broadcasting. This system enables live data streaming, notifications, and interactive features for the Auto Bot Solutions Forum.

## Architecture

### Core Components

1. **WebSocketManager** - Connection and room management
2. **WebSocketAuth** - Authentication and authorization
3. **WebSocketEvents** - Event handling and processing
4. **WebSocketHandlers** - Flask-SocketIO event handlers
5. **WebSocketRoutes** - Management and monitoring endpoints

### Connection Flow

```
Client Connect → Authentication → Join Rooms → Event Broadcasting → Real-time Updates
```

## Features

### Connection Management

- **WebSocket Connections**: Real-time bidirectional communication
- **Room Management**: Dynamic room creation and management
- **Connection Tracking**: Monitor active connections
- **Automatic Cleanup**: Remove inactive connections

### Authentication & Security

- **JWT Authentication**: Token-based authentication
- **API Key Authentication**: Secure key-based access
- **Session Authentication**: Traditional session support
- **Rate Limiting**: Prevent connection abuse
- **Permission-based Access**: Role-based room access

### Event System

- **Event Broadcasting**: Send messages to rooms/clients
- **Event Types**: Predefined event types for common operations
- **Custom Events**: Support for custom event handling
- **Event Validation**: Input validation and sanitization

### Real-time Features

- **Live Updates**: Real-time data updates
- **Notifications**: Instant notification delivery
- **Typing Indicators**: Show when users are typing
- **User Presence**: Online/offline status tracking

## Implementation

### File Structure

```
app/api/websockets/
├── __init__.py                 # Package initialization
├── websocket_manager.py        # Connection and room management
├── websocket_auth.py           # Authentication system
├── websocket_events.py         # Event handling
├── websocket_handlers.py       # Flask-SocketIO handlers
└── websocket_routes.py         # Management endpoints
```

### WebSocket Manager

```python
from app.api.websockets import WebSocketManager

# Initialize WebSocket manager
ws_manager = WebSocketManager(socketio)

# Create room
room = ws_manager.create_room('general', RoomType.PUBLIC)

# Join room
ws_manager.join_room(sid, 'general')

# Broadcast message
ws_manager.send_to_room('general', 'message', {'text': 'Hello!'})
```

### Authentication Integration

```python
from app.api.websockets import WebSocketAuth

# Initialize authentication
ws_auth = WebSocketAuth(app.config['JWT_SECRET_KEY'])

# Authenticate connection
auth_info = ws_auth.authenticate_connection(sid, {
    'method': 'jwt',
    'token': jwt_token
})
```

### Event Handling

```python
from app.api.websockets import WebSocketEvents

# Initialize event handlers
ws_events = WebSocketEvents(ws_manager)

# Handle post creation
ws_events.handle_post_created({
    'post_id': 123,
    'post_data': post_object
}, sid)
```

## API Endpoints

### Connection Management

- `POST /api/websocket/authenticate` - Authenticate WebSocket connection
- `POST /api/websocket/join_room` - Join a room
- `POST /api/websocket/leave_room` - Leave a room
- `GET /api/websocket/connections` - List active connections
- `GET /api/websocket/rooms` - List all rooms

### Room Management

- `GET /api/websocket/rooms/{room_name}` - Get room details
- `GET /api/websocket/rooms/{room_name}/connections` - Get room connections
- `POST /api/websocket/send_message` - Send message to room
- `POST /api/websocket/broadcast` - Broadcast to all connections

### User Management

- `GET /api/websocket/users/{user_id}/connections` - Get user connections
- `POST /api/websocket/send_notification` - Send notification to user

### System Management

- `GET /api/websocket/stats` - Get WebSocket statistics
- `GET /api/websocket/health` - System health check
- `POST /api/websocket/cleanup` - Clean up inactive connections

## Usage Examples

### Client Connection

```javascript
// Connect to WebSocket
const socket = io('ws://localhost:5000', {
    auth: {
        method: 'jwt',
        token: 'your-jwt-token'
    }
});

// Handle connection
socket.on('connect', () => {
    console.log('Connected to WebSocket');
    
    // Join room
    socket.emit('join_room', { room: 'general' });
});

// Handle messages
socket.on('message', (data) => {
    console.log('Received message:', data);
});
```

### Server Event Handling

```python
@socketio.on('message')
def handle_message(data):
    """Handle incoming messages"""
    sid = request.sid
    room = data.get('room', 'general')
    message = data.get('message')
    
    # Validate and process message
    if message:
        ws_manager.send_to_room(room, 'message', {
            'text': message,
            'sender': sid,
            'timestamp': datetime.utcnow().isoformat()
        })
```

### Real-time Notifications

```python
# Send notification to user
ws_events.send_notification(user_id, {
    'type': 'info',
    'title': 'New Message',
    'message': 'You have a new message',
    'data': {'message_id': 123}
})

# Broadcast system message
ws_events.send_system_message(
    'System maintenance in 5 minutes',
    level='warning',
    room='general'
)
```

## Configuration

### WebSocket Configuration

```python
# app/config.py
WEBSOCKET_CONFIG = {
    'cors_allowed_origins': ['http://localhost:3000'],
    'async_mode': 'threading',
    'ping_timeout': 60,
    'ping_interval': 25,
    'max_connections_per_room': 1000,
    'rate_limit_messages_per_minute': 60
}
```

### Authentication Configuration

```python
WEBSOCKET_AUTH_CONFIG = {
    'jwt_secret_key': 'your-secret-key',
    'api_key_required': False,
    'session_timeout': 3600,
    'max_concurrent_connections': 5
}
```

## Event Types

### Connection Events

- `connect` - New connection established
- `disconnect` - Connection closed
- `authenticate` - Authentication request
- `join_room` - Join room request
- `leave_room` - Leave room request

### Content Events

- `post_created` - New post created
- `post_updated` - Post updated
- `post_deleted` - Post deleted
- `comment_created` - New comment created
- `comment_updated` - Comment updated
- `comment_deleted` - Comment deleted

### User Events

- `user_online` - User came online
- `user_offline` - User went offline
- `user_joined` - User joined room
- `user_left` - User left room

### Notification Events

- `notification` - System notification
- `system_message` - System message
- `live_update` - Real-time data update

### Interaction Events

- `message` - Chat message
- `typing` - User typing indicator
- `stop_typing` - User stopped typing

## Room Types

### Public Rooms

```python
# Create public room
room = ws_manager.create_room('general', RoomType.PUBLIC)
```

### Private Rooms

```python
# Create private room
room = ws_manager.create_room('private_123', RoomType.PRIVATE)
```

### User Rooms

```python
# Create user-specific room
user_room = f"user_{user_id}"
ws_manager.create_room(user_room, RoomType.USER)
```

### Post Rooms

```python
# Create post-specific room
post_room = f"post_{post_id}"
ws_manager.create_room(post_room, RoomType.POST)
```

## Authentication Methods

### JWT Authentication

```javascript
const socket = io('ws://localhost:5000', {
    auth: {
        method: 'jwt',
        token: 'your-jwt-token'
    }
});
```

### API Key Authentication

```javascript
const socket = io('ws://localhost:5000', {
    auth: {
        method: 'api_key',
        api_key: 'your-api-key'
    }
});
```

### Session Authentication

```javascript
const socket = io('ws://localhost:5000', {
    auth: {
        method: 'session',
        session_id: 'your-session-id'
    }
});
```

## Client Integration

### JavaScript Client

```javascript
class WebSocketClient {
    constructor(url, options = {}) {
        this.socket = io(url, options);
        this.setupEventHandlers();
    }
    
    setupEventHandlers() {
        this.socket.on('connect', () => {
            console.log('Connected to WebSocket');
        });
        
        this.socket.on('message', (data) => {
            this.handleMessage(data);
        });
        
        this.socket.on('notification', (data) => {
            this.handleNotification(data);
        });
    }
    
    joinRoom(roomName) {
        this.socket.emit('join_room', { room: roomName });
    }
    
    sendMessage(roomName, message) {
        this.socket.emit('send_message', {
            room: roomName,
            message: message
        });
    }
    
    handleMessage(data) {
        console.log('Received message:', data);
    }
    
    handleNotification(data) {
        console.log('Received notification:', data);
    }
}

// Usage
const client = new WebSocketClient('ws://localhost:5000', {
    auth: {
        method: 'jwt',
        token: 'your-jwt-token'
    }
});
```

### Python Client

```python
import socketio

class WebSocketClient:
    def __init__(self, url):
        self.sio = socketio.Client()
        self.url = url
        self.setup_event_handlers()
    
    def setup_event_handlers(self):
        @self.sio.event
        def connect():
            print('Connected to WebSocket')
        
        @self.sio.event
        def message(data):
            self.handle_message(data)
        
        @self.sio.event
        def notification(data):
            self.handle_notification(data)
    
    def connect(self, auth_data):
        self.sio.connect(self.url, auth=auth_data)
    
    def join_room(self, room_name):
        self.sio.emit('join_room', {'room': room_name})
    
    def send_message(self, room_name, message):
        self.sio.emit('send_message', {
            'room': room_name,
            'message': message
        })
    
    def handle_message(self, data):
        print(f"Received message: {data}")
    
    def handle_notification(self, data):
        print(f"Received notification: {data}")

# Usage
client = WebSocketClient('http://localhost:5000')
client.connect({
    'method': 'jwt',
    'token': 'your-jwt-token'
})
```

## Monitoring and Analytics

### Connection Statistics

```python
# Get WebSocket statistics
stats = ws_manager.get_stats()
print(f"Active connections: {stats['active_connections']}")
print(f"Total rooms: {stats['total_rooms']}")
print(f"Messages sent: {stats['total_messages']}")
```

### Room Analytics

```python
# Get room information
room = ws_manager.get_room('general')
room_info = room.get_info()
print(f"Room connections: {room_info['connection_count']}")
print(f"Message history: {len(room_info['message_history'])}")
```

### Performance Metrics

```python
# Track performance
import time

start_time = time.time()
ws_manager.send_to_room('general', 'message', data)
end_time = time.time()

print(f"Message sent in {end_time - start_time:.3f} seconds")
```

## Best Practices

### Connection Management

1. **Limit Connections**: Set reasonable connection limits
2. **Cleanup Inactive**: Regular cleanup of inactive connections
3. **Rate Limiting**: Implement rate limiting for messages
4. **Error Handling**: Proper error handling and recovery

### Room Management

1. **Room Naming**: Use consistent room naming conventions
2. **Access Control**: Implement proper room access control
3. **Room Cleanup**: Clean up empty rooms
4. **Message History**: Limit message history storage

### Event Handling

1. **Event Validation**: Validate all event data
2. **Error Handling**: Handle errors gracefully
3. **Event Logging**: Log important events
4. **Performance**: Optimize event processing

### Security

1. **Authentication**: Require authentication for connections
2. **Authorization**: Implement proper authorization
3. **Input Validation**: Validate all input data
4. **Rate Limiting**: Prevent abuse with rate limiting

## Troubleshooting

### Common Issues

1. **Connection Failed**: Check authentication and network
2. **Room Not Found**: Verify room exists
3. **Permission Denied**: Check user permissions
4. **Message Not Delivered**: Check room membership

### Debug Mode

```python
# Enable WebSocket debug mode
app.config['SOCKETIO_ASYNC_MODE'] = 'threading'
app.config['SOCKETIO_DEBUG'] = True

# View WebSocket logs
import logging
logging.getLogger('socketio').setLevel(logging.DEBUG)
```

### Connection Issues

```python
# Check connection status
if ws_manager.is_connected(sid):
    print(f"Connection {sid} is active")
else:
    print(f"Connection {sid} is inactive")
```

## Security Considerations

### Authentication Security

1. **Token Validation**: Validate JWT tokens properly
2. **API Key Security**: Secure API key storage
3. **Session Security**: Secure session management
4. **Permission Checking**: Verify user permissions

### Data Security

1. **Input Sanitization**: Sanitize all input data
2. **Message Encryption**: Encrypt sensitive messages
3. **Access Control**: Implement proper access controls
4. **Audit Logging**: Log all important events

### Network Security

1. **CORS Configuration**: Configure CORS properly
2. **Rate Limiting**: Implement rate limiting
3. **Connection Limits**: Set connection limits
4. **Firewall Rules**: Configure firewall rules

## Performance Optimization

### Connection Optimization

```python
# Optimize connection handling
@socketio.on('connect')
def handle_connect():
    # Use connection pooling
    pass

# Implement connection caching
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_user_permissions(user_id):
    return user_permissions_service.get_permissions(user_id)
```

### Message Optimization

```python
# Batch message processing
def batch_messages(messages):
    """Process messages in batches"""
    batch_size = 100
    for i in range(0, len(messages), batch_size):
        batch = messages[i:i + batch_size]
        process_message_batch(batch)
```

### Memory Optimization

```python
# Limit message history
MAX_MESSAGE_HISTORY = 100

def add_message_to_history(room, message):
    if len(room.message_history) >= MAX_MESSAGE_HISTORY:
        room.message_history.pop(0)
    room.message_history.append(message)
```

## Future Enhancements

### Planned Features

1. **Message Persistence**: Persistent message storage
2. **File Transfer**: File sharing capabilities
3. **Video Streaming**: Video chat support
4. **Mobile Push**: Mobile push notifications

### Extension Points

1. **Custom Events**: Support for custom event types
2. **Middleware**: WebSocket middleware support
3. **Plugins**: Plugin system for extensions
4. **Analytics**: Enhanced analytics and reporting

---

**Last Updated**: May 12, 2026  
**Version**: 1.0  
**Status**: Production Ready
