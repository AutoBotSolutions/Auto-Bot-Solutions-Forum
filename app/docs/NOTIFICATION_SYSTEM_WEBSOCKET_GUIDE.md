# Notification System WebSocket Guide

## Overview

The notification system uses WebSocket technology to provide real-time notification delivery to users. This guide covers WebSocket implementation, event handling, and integration patterns.

**WebSocket Server URL:** `ws://localhost:5003`  
**Protocol:** Socket.IO  
**Authentication:** Flask-Login session required

## Architecture

### WebSocket Server Setup
The WebSocket server runs on port 5003, separate from the main Flask application on port 5000. This separation allows for independent scaling and dedicated real-time processing.

### Room-Based Communication
Notifications are delivered using Socket.IO rooms with the naming convention `user_{user_id}`. This ensures that users only receive their own notifications.

### Connection Flow
```
Client → WebSocket Connect → Authenticate → Join User Room → Receive Notifications
```

## WebSocket Events

### Client to Server Events

#### subscribe_notifications
Subscribe the current user to their notification room.

**Event:** `subscribe_notifications`  
**Data:** `{}` (empty object)

**Example:**
```javascript
socket.emit('subscribe_notifications');
```

**Response Events:**
- `unread_count` - Current unread notification count
- `recent_notifications` - Recent notifications list

#### mark_notification_read
Mark a specific notification as read.

**Event:** `mark_notification_read`  
**Data:** `{ "notification_id": 123 }`

**Example:**
```javascript
socket.emit('mark_notification_read', {
    notification_id: 123
});
```

**Response Events:**
- `notification_read` - Confirmation of read status
- `unread_count` - Updated unread count

#### fetch_unread_count
Request the current unread notification count.

**Event:** `fetch_unread_count`  
**Data:** `{}` (empty object)

**Example:**
```javascript
socket.emit('fetch_unread_count');
```

**Response Event:**
- `unread_count` - Current unread count

#### fetch_recent_notifications
Request recent notifications for the current user.

**Event:** `fetch_recent_notifications`  
**Data:** `{ "limit": 10 }` (optional)

**Example:**
```javascript
socket.emit('fetch_recent_notifications', {
    limit: 10
});
```

**Response Event:**
- `recent_notifications` - List of recent notifications

### Server to Client Events

#### notification
New notification received in real-time.

**Event:** `notification`  
**Data Structure:**
```json
{
    "id": 123,
    "content": "John Doe commented on your post",
    "link": "/forum/post/456",
    "is_read": false,
    "created_at": "2026-05-12T10:30:00Z",
    "type": "comment"
}
```

#### unread_count
Updated unread notification count.

**Event:** `unread_count`  
**Data Structure:**
```json
{
    "unread_count": 5
}
```

#### recent_notifications
List of recent notifications.

**Event:** `recent_notifications`  
**Data Structure:**
```json
{
    "notifications": [
        {
            "id": 123,
            "content": "John Doe commented on your post",
            "link": "/forum/post/456",
            "is_read": false,
            "created_at": "2026-05-12T10:30:00Z",
            "type": "comment"
        }
    ]
}
```

#### notification_read
Confirmation that a notification was marked as read.

**Event:** `notification_read`  
**Data Structure:**
```json
{
    "notification_id": 123,
    "unread_count": 4,
    "status": "success"
}
```

#### all_notifications_marked_read
Broadcast when all notifications are marked as read.

**Event:** `all_notifications_marked_read`  
**Data Structure:**
```json
{
    "count": 5,
    "unread_count": 0,
    "status": "success"
}
```

## Client Implementation

### JavaScript Integration

#### Basic Connection Setup
```javascript
class NotificationWebSocket {
    constructor() {
        this.socket = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
    }
    
    connect() {
        this.socket = io('ws://localhost:5003', {
            transports: ['websocket'],
            upgrade: false,
            rememberUpgrade: false
        });
        
        this.setupEventHandlers();
    }
    
    setupEventHandlers() {
        // Connection events
        this.socket.on('connect', () => {
            console.log('Connected to WebSocket server');
            this.reconnectAttempts = 0;
            this.subscribe();
        });
        
        this.socket.on('disconnect', (reason) => {
            console.log('Disconnected from WebSocket:', reason);
            this.handleReconnect();
        });
        
        this.socket.on('connect_error', (error) => {
            console.error('WebSocket connection error:', error);
            this.handleReconnect();
        });
        
        // Notification events
        this.socket.on('notification', (data) => {
            this.handleNewNotification(data);
        });
        
        this.socket.on('unread_count', (data) => {
            this.updateUnreadCount(data.unread_count);
        });
        
        this.socket.on('recent_notifications', (data) => {
            this.displayRecentNotifications(data.notifications);
        });
        
        this.socket.on('notification_read', (data) => {
            this.markNotificationAsRead(data.notification_id);
        });
    }
    
    subscribe() {
        this.socket.emit('subscribe_notifications');
    }
    
    markAsRead(notificationId) {
        this.socket.emit('mark_notification_read', {
            notification_id: notificationId
        });
    }
    
    fetchUnreadCount() {
        this.socket.emit('fetch_unread_count');
    }
    
    fetchRecentNotifications(limit = 10) {
        this.socket.emit('fetch_recent_notifications', {
            limit: limit
        });
    }
    
    handleNewNotification(notification) {
        // Display browser notification
        if (Notification.permission === 'granted') {
            new Notification('New Notification', {
                body: notification.content,
                icon: '/static/images/notification-icon.png',
                tag: notification.id
            }).onclick = () => {
                window.location.href = notification.link;
            };
        }
        
        // Update UI
        this.updateNotificationList(notification);
        this.updateUnreadCount(this.getUnreadCount() + 1);
    }
    
    handleReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            setTimeout(() => {
                console.log(`Reconnecting... Attempt ${this.reconnectAttempts}`);
                this.connect();
            }, this.reconnectDelay * this.reconnectAttempts);
        }
    }
    
    updateUnreadCount(count) {
        // Update UI elements
        const badge = document.querySelector('.notification-badge');
        if (badge) {
            badge.textContent = count;
            badge.style.display = count > 0 ? 'block' : 'none';
        }
    }
    
    getUnreadCount() {
        const badge = document.querySelector('.notification-badge');
        return badge ? parseInt(badge.textContent) || 0 : 0;
    }
}

// Initialize WebSocket connection
const notificationWebSocket = new NotificationWebSocket();
notificationWebSocket.connect();
```

#### Advanced Features
```javascript
class AdvancedNotificationWebSocket extends NotificationWebSocket {
    constructor() {
        super();
        this.notificationQueue = [];
        this.isProcessingQueue = false;
        this.heartbeatInterval = null;
    }
    
    setupEventHandlers() {
        super.setupEventHandlers();
        
        // Add heartbeat
        this.socket.on('pong', () => {
            console.log('Heartbeat received');
        });
        
        // Add connection status monitoring
        this.socket.on('connect', () => {
            this.startHeartbeat();
        });
        
        this.socket.on('disconnect', () => {
            this.stopHeartbeat();
        });
    }
    
    startHeartbeat() {
        this.heartbeatInterval = setInterval(() => {
            this.socket.emit('ping');
        }, 30000); // 30 seconds
    }
    
    stopHeartbeat() {
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
            this.heartbeatInterval = null;
        }
    }
    
    queueNotification(notification) {
        this.notificationQueue.push(notification);
        this.processQueue();
    }
    
    processQueue() {
        if (this.isProcessingQueue || this.notificationQueue.length === 0) {
            return;
        }
        
        this.isProcessingQueue = true;
        
        while (this.notificationQueue.length > 0) {
            const notification = this.notificationQueue.shift();
            this.handleNewNotification(notification);
        }
        
        this.isProcessingQueue = false;
    }
    
    batchMarkAsRead(notificationIds) {
        notificationIds.forEach(id => {
            this.markAsRead(id);
        });
    }
    
    subscribeWithPreferences(preferences) {
        this.subscribe();
        this.socket.emit('update_preferences', preferences);
    }
}
```

### React Integration

#### React Hook for WebSocket
```javascript
import { useEffect, useState, useCallback } from 'react';
import io from 'socket.io-client';

export const useNotifications = () => {
    const [socket, setSocket] = useState(null);
    const [notifications, setNotifications] = useState([]);
    const [unreadCount, setUnreadCount] = useState(0);
    const [isConnected, setIsConnected] = useState(false);
    
    useEffect(() => {
        const newSocket = io('ws://localhost:5003');
        setSocket(newSocket);
        
        newSocket.on('connect', () => {
            setIsConnected(true);
            newSocket.emit('subscribe_notifications');
        });
        
        newSocket.on('disconnect', () => {
            setIsConnected(false);
        });
        
        newSocket.on('notification', (notification) => {
            setNotifications(prev => [notification, ...prev]);
            setUnreadCount(prev => prev + 1);
        });
        
        newSocket.on('unread_count', (data) => {
            setUnreadCount(data.unread_count);
        });
        
        newSocket.on('recent_notifications', (data) => {
            setNotifications(data.notifications);
        });
        
        return () => newSocket.close();
    }, []);
    
    const markAsRead = useCallback((notificationId) => {
        if (socket) {
            socket.emit('mark_notification_read', {
                notification_id: notificationId
            });
            
            setNotifications(prev => 
                prev.map(n => n.id === notificationId ? { ...n, is_read: true } : n)
            );
            setUnreadCount(prev => Math.max(0, prev - 1));
        }
    }, [socket]);
    
    const markAllAsRead = useCallback(() => {
        if (socket) {
            notifications.forEach(n => {
                if (!n.is_read) {
                    markAsRead(n.id);
                }
            });
        }
    }, [socket, notifications, markAsRead]);
    
    const fetchUnreadCount = useCallback(() => {
        if (socket) {
            socket.emit('fetch_unread_count');
        }
    }, [socket]);
    
    const fetchRecentNotifications = useCallback((limit = 10) => {
        if (socket) {
            socket.emit('fetch_recent_notifications', { limit });
        }
    }, [socket]);
    
    return {
        notifications,
        unreadCount,
        isConnected,
        markAsRead,
        markAllAsRead,
        fetchUnreadCount,
        fetchRecentNotifications
    };
};
```

#### React Component Example
```javascript
import React from 'react';
import { useNotifications } from './useNotifications';

const NotificationCenter = () => {
    const {
        notifications,
        unreadCount,
        isConnected,
        markAsRead,
        markAllAsRead,
        fetchUnreadCount
    } = useNotifications();
    
    useEffect(() => {
        fetchUnreadCount();
    }, [fetchUnreadCount]);
    
    return (
        <div className="notification-center">
            <div className="notification-header">
                <h3>Notifications</h3>
                <div className="connection-status">
                    {isConnected ? (
                        <span className="status-connected">Connected</span>
                    ) : (
                        <span className="status-disconnected">Disconnected</span>
                    )}
                </div>
                <div className="unread-badge">
                    {unreadCount > 0 && (
                        <span className="badge">{unreadCount}</span>
                    )}
                </div>
            </div>
            
            <div className="notification-actions">
                <button onClick={fetchUnreadCount}>
                    Refresh
                </button>
                {unreadCount > 0 && (
                    <button onClick={markAllAsRead}>
                        Mark All as Read
                    </button>
                )}
            </div>
            
            <div className="notification-list">
                {notifications.map(notification => (
                    <NotificationItem
                        key={notification.id}
                        notification={notification}
                        onMarkAsRead={markAsRead}
                    />
                ))}
            </div>
        </div>
    );
};

const NotificationItem = ({ notification, onMarkAsRead }) => {
    const handleClick = () => {
        if (!notification.is_read) {
            onMarkAsRead(notification.id);
        }
        window.location.href = notification.link;
    };
    
    return (
        <div className={`notification-item ${notification.is_read ? 'read' : 'unread'}`}>
            <div className="notification-content" onClick={handleClick}>
                <p>{notification.content}</p>
                <small className="notification-time">
                    {new Date(notification.created_at).toLocaleString()}
                </small>
            </div>
            {!notification.is_read && (
                <button
                    className="mark-read-btn"
                    onClick={() => onMarkAsRead(notification.id)}
                >
                    Mark as Read
                </button>
            )}
        </div>
    );
};
```

## Server Implementation

### WebSocket Event Handlers

#### handle_subscribe_notifications
```python
@socketio.on('subscribe_notifications')
def handle_subscribe_notifications():
    """Handle user subscription to notifications"""
    try:
        if not current_user.is_authenticated:
            emit('error', {'message': 'Authentication required'})
            return
        
        # Join user-specific room
        room = f"user_{current_user.id}"
        join_room(room)
        
        # Get unread count
        from app.models import Notification
        unread_count = Notification.query.filter_by(
            user_id=current_user.id,
            is_read=False
        ).count()
        
        # Send unread count
        emit('unread_count', {'unread_count': unread_count})
        
        # Get recent notifications
        recent_notifications = Notification.query.filter_by(
            user_id=current_user.id
        ).order_by(Notification.created_at.desc()).limit(10).all()
        
        notification_data = []
        for notification in recent_notifications:
            notification_data.append({
                'id': notification.id,
                'content': notification.content,
                'link': notification.link,
                'is_read': notification.is_read,
                'created_at': notification.created_at.isoformat(),
                'type': getattr(notification, 'type', 'system')
            })
        
        emit('recent_notifications', {'notifications': notification_data})
        
        logger.info(f"User {current_user.username} subscribed to notifications")
        
    except Exception as e:
        logger.error(f"Error in handle_subscribe_notifications: {str(e)}")
        emit('error', {'message': 'Failed to subscribe to notifications'})
```

#### handle_mark_notification_read
```python
@socketio.on('mark_notification_read')
def handle_mark_notification_read(data):
    """Handle marking notification as read"""
    try:
        if not current_user.is_authenticated:
            emit('error', {'message': 'Authentication required'})
            return
        
        notification_id = data.get('notification_id')
        
        if notification_id:
            from app.models import Notification
            notification = Notification.query.filter_by(
                id=notification_id,
                user_id=current_user.id
            ).first()
            
            if notification and not notification.is_read:
                notification.is_read = True
                db.session.commit()
                
                # Broadcast to user's room
                room = f"user_{current_user.id}"
                emit('notification_read', {
                    'notification_id': notification_id,
                    'unread_count': get_unread_count(current_user.id),
                    'status': 'success'
                }, room=room)
                
                emit('unread_count', {'unread_count': get_unread_count(current_user.id)}, room=room)
                
                logger.info(f"User {current_user.username} marked notification {notification_id} as read")
        
    except Exception as e:
        logger.error(f"Error in handle_mark_notification_read: {str(e)}")
        emit('error', {'message': 'Failed to mark notification as read'})
```

#### handle_fetch_unread_count
```python
@socketio.on('fetch_unread_count')
def handle_fetch_unread_count():
    """Handle fetching unread count"""
    try:
        if not current_user.is_authenticated:
            emit('error', {'message': 'Authentication required'})
            return
        
        from app.models import Notification
        unread_count = Notification.query.filter_by(
            user_id=current_user.id,
            is_read=False
        ).count()
        
        emit('unread_count', {'unread_count': unread_count})
        
    except Exception as e:
        logger.error(f"Error in handle_fetch_unread_count: {str(e)}")
        emit('error', {'message': 'Failed to fetch unread count'})
```

#### handle_fetch_recent_notifications
```python
@socketio.on('fetch_recent_notifications')
def handle_fetch_recent_notifications(data):
    """Handle fetching recent notifications"""
    try:
        if not current_user.is_authenticated:
            emit('error', {'message': 'Authentication required'})
            return
        
        limit = data.get('limit', 10)
        
        from app.models import Notification
        recent_notifications = Notification.query.filter_by(
            user_id=current_user.id
        ).order_by(Notification.created_at.desc()).limit(limit).all()
        
        notification_data = []
        for notification in recent_notifications:
            notification_data.append({
                'id': notification.id,
                'content': notification.content,
                'link': notification.link,
                'is_read': notification.is_read,
                'created_at': notification.created_at.isoformat(),
                'type': getattr(notification, 'type', 'system')
            })
        
        emit('recent_notifications', {'notifications': notification_data})
        
    except Exception as e:
        logger.error(f"Error in handle_fetch_recent_notifications: {str(e)}")
        emit('error', {'message': 'Failed to fetch recent notifications'})
```

### Utility Functions

#### Broadcast Notification
```python
def broadcast_notification(user_id, notification_data):
    """Broadcast notification to specific user"""
    try:
        room = f"user_{user_id}"
        
        # Prepare notification data
        broadcast_data = {
            'id': notification_data['id'],
            'content': notification_data['content'],
            'link': notification_data['link'],
            'is_read': notification_data.get('is_read', False),
            'created_at': notification_data['created_at'].isoformat(),
            'type': notification_data.get('type', 'system')
        }
        
        # Emit to user's room
        socketio.emit('notification', broadcast_data, room=room)
        
        # Update unread count
        unread_count = get_unread_count(user_id)
        socketio.emit('unread_count', {'unread_count': unread_count}, room=room)
        
        logger.info(f"Notification broadcasted to user {user_id}")
        
    except Exception as e:
        logger.error(f"Error broadcasting notification: {str(e)}")

def emit_notification_read(notification_id, user_id, unread_count):
    """Emit notification read event"""
    try:
        room = f"user_{user_id}"
        socketio.emit('notification_read', {
            'notification_id': notification_id,
            'unread_count': unread_count,
            'status': 'success'
        }, room=room)
        
        socketio.emit('unread_count', {'unread_count': unread_count}, room=room)
        
    except Exception as e:
        logger.error(f"Error emitting notification read event: {str(e)}")

def get_unread_count(user_id):
    """Get unread notification count for user"""
    try:
        from app.models import Notification
        return Notification.query.filter_by(
            user_id=user_id,
            is_read=False
        ).count()
    except Exception as e:
        logger.error(f"Error getting unread count: {str(e)}")
        return 0
```

## Performance Considerations

### Connection Management
- **Connection Limits:** Implement per-user connection limits
- **Connection Cleanup:** Remove inactive connections
- **Room Management:** Efficient room joining/leaving

### Message Optimization
- **Message Batching:** Batch multiple notifications
- **Message Compression:** Compress large payloads
- **Selective Updates:** Only send relevant data

### Scaling Considerations
- **Redis Adapter:** Use Redis for multi-server scaling
- **Load Balancing:** Distribute WebSocket connections
- **Connection Pooling:** Manage connection resources

## Security

### Authentication
- **Session Validation:** Verify Flask-Login sessions
- **Token Validation:** Support token-based auth
- **Room Security:** Ensure room isolation

### Data Validation
- **Input Sanitization:** Validate all incoming data
- **Message Size Limits:** Prevent large message attacks
- **Rate Limiting:** Limit message frequency

### Access Control
- **User Isolation:** Users only access their own data
- **Permission Checks:** Verify user permissions
- **Audit Logging:** Log all WebSocket events

## Testing

### Unit Testing
```python
import pytest
from app.websockets.events import handle_subscribe_notifications

def test_subscribe_notifications():
    """Test notification subscription"""
    with app.test_request_context():
        # Mock authenticated user
        with patch('flask_login.current_user') as mock_user:
            mock_user.is_authenticated = True
            mock_user.id = 1
            
            # Test subscription
            handle_subscribe_notifications()
            
            # Verify room join
            # Verify unread count sent
            # Verify recent notifications sent
```

### Integration Testing
```python
def test_notification_broadcast():
    """Test notification broadcasting"""
    with app.test_client() as client:
        # Create WebSocket connection
        socket = create_test_socket()
        
        # Subscribe to notifications
        socket.emit('subscribe_notifications')
        
        # Create notification
        notification = create_test_notification()
        
        # Broadcast notification
        broadcast_notification(notification.user_id, notification)
        
        # Verify notification received
        received = socket.receive('notification')
        assert received['id'] == notification.id
```

## Troubleshooting

### Common Issues

#### Connection Failures
**Problem:** WebSocket connection fails  
**Solution:** Check port 5003 availability, verify CORS configuration

#### Authentication Issues
**Problem:** User not authenticated  
**Solution:** Verify Flask-Login session, check authentication flow

#### Room Issues
**Problem:** Not receiving notifications  
**Solution:** Verify room joining, check user ID matching

#### Performance Issues
**Problem:** Slow notification delivery  
**Solution:** Check database queries, optimize message size

### Debugging Tools

#### WebSocket Debugging
```javascript
// Enable debug logging
localStorage.debug = 'socket.io-client:*';

// Monitor connection events
socket.on('connect', () => console.log('Connected'));
socket.on('disconnect', (reason) => console.log('Disconnected:', reason));
socket.on('error', (error) => console.error('Error:', error));
```

#### Server Logging
```python
# Enable debug logging
import logging
logging.getLogger('socketio').setLevel(logging.DEBUG)
logging.getLogger('engineio').setLevel(logging.DEBUG)
```

---

**WebSocket Protocol:** Socket.IO v2.x  
**Server Port:** 5003  
**Authentication:** Flask-Login  
**Last Updated:** May 12, 2026
