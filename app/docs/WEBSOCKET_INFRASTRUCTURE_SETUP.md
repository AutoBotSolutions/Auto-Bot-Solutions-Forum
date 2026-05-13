# WebSocket Infrastructure Setup Guide

## Overview

This guide provides comprehensive instructions for setting up the WebSocket infrastructure for the notification system. The WebSocket infrastructure enables real-time notification delivery to connected clients.

**Components:**
- WebSocket Server (Socket.IO)
- Notification Broadcasting System
- Connection Management
- Real-time Event Handling
- Load Balancing Support
- Monitoring and Health Checks

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Client App    │◄──►│  WebSocket      │◄──►│ Notification    │
│   (Browser)     │    │  Server         │    │  Service        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │  Redis Adapter  │
                       │  (Scaling)      │
                       └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │  Load Balancer  │
                       │  (Multiple      │
                       │   Instances)    │
                       └─────────────────┘
```

## Prerequisites

### System Requirements
- **Python 3.8+**
- **Node.js 14+** (for alternative deployment)
- **Redis 6.0+** (for scaling multiple instances)
- **Load Balancer** (nginx/HAProxy) for production

### Dependencies
```bash
# Python dependencies
pip install flask-socketio
pip install redis
pip install eventlet  # or gevent
pip install gunicorn
```

## Configuration

### Environment Variables

Create or update your `.env` file with WebSocket configuration:

```bash
# WebSocket Server Configuration
WEBSOCKET_NOTIFICATION_ENABLED=true
WEBSOCKET_NOTIFICATION_URL=ws://localhost:5003
WEBSOCKET_NOTIFICATION_HOST=localhost
WEBSOCKET_NOTIFICATION_PORT=5003
WEBSOCKET_NOTIFICATION_DEBUG=false

# WebSocket Security
WEBSOCKET_SECRET_KEY=your-websocket-secret-key-here
WEBSOCKET_CORS_ALLOWED_ORIGINS=http://localhost:5000,http://127.0.0.1:5000

# WebSocket Performance
WEBSOCKET_MAX_CONNECTIONS=1000
WEBSOCKET_HEARTBEAT_INTERVAL=25
WEBSOCKET_HEARTBEAT_TIMEOUT=60

# Redis Configuration (for scaling)
REDIS_URL=redis://localhost:6379/0
REDIS_NOTIFICATION_DB=1
REDIS_CONNECTION_POOL_SIZE=10
```

### Flask Application Setup

Update your Flask application to include WebSocket support:

```python
# app/__init__.py
from flask import Flask
from flask_socketio import SocketIO
from app.config.notification_config import get_notification_config

def create_app():
    app = Flask(__name__)
    
    # Load configuration
    config = get_notification_config()
    app.config.from_object(config)
    
    # Initialize Socket.IO
    socketio = SocketIO(
        app,
        cors_allowed_origins=config.websocket_cors_origins,
        async_mode='eventlet',  # or 'gevent'
        logger=config.websocket_debug,
        engineio_logger=config.websocket_debug
    )
    
    # Register WebSocket events
    from app.websockets import register_websocket_events
    register_websocket_events(socketio)
    
    return app, socketio
```

## WebSocket Server Implementation

### Main WebSocket Server

Create `app/websockets/server.py`:

```python
import os
from flask import Flask
from flask_socketio import SocketIO
from app.config.notification_config import get_notification_config
from app.websockets.events import register_websocket_events

def create_websocket_server():
    """Create and configure WebSocket server"""
    app = Flask(__name__)
    
    # Load configuration
    config = get_notification_config()
    
    # Configure app
    app.config['SECRET_KEY'] = config.websocket_secret_key
    app.config['DEBUG'] = config.websocket_debug
    
    # Initialize Socket.IO
    socketio = SocketIO(
        app,
        cors_allowed_origins=config.websocket_cors_origins,
        async_mode='eventlet',
        logger=config.websocket_debug,
        engineio_logger=config.websocket_debug,
        max_http_buffer_size=1e8,  # 100MB
        ping_timeout=config.websocket_heartbeat_timeout,
        ping_interval=config.websocket_heartbeat_interval
    )
    
    # Register event handlers
    register_websocket_events(socketio)
    
    return app, socketio

def run_websocket_server():
    """Run the WebSocket server"""
    app, socketio = create_websocket_server()
    config = get_notification_config()
    
    print(f"Starting WebSocket server on {config.websocket_host}:{config.websocket_port}")
    
    socketio.run(
        app,
        host=config.websocket_host,
        port=config.websocket_port,
        debug=config.websocket_debug,
        use_reloader=False,  # Disable for production
        log_output=True
    )

if __name__ == '__main__':
    run_websocket_server()
```

### Event Handlers

Update `app/websockets/events.py`:

```python
from flask_socketio import emit, join_room, leave_room
from flask_login import current_user
from app.websockets.service import NotificationWebSocketService
import logging

logger = logging.getLogger(__name__)

def register_websocket_events(socketio):
    """Register all WebSocket event handlers"""
    
    @socketio.on('connect')
    def handle_connect():
        """Handle client connection"""
        if current_user.is_authenticated:
            # Join user-specific room
            user_room = f"user_{current_user.id}"
            join_room(user_room)
            
            # Send initial unread count
            service = NotificationWebSocketService()
            service.emit_unread_count(current_user.id)
            
            logger.info(f"User {current_user.id} connected to WebSocket")
            emit('connected', {'user_id': current_user.id})
        else:
            emit('error', {'message': 'Authentication required'})
            return False
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection"""
        if current_user.is_authenticated:
            user_room = f"user_{current_user.id}"
            leave_room(user_room)
            logger.info(f"User {current_user.id} disconnected from WebSocket")
    
    @socketio.on('subscribe_notifications')
    def handle_subscribe_notifications(data):
        """Handle notification subscription"""
        if not current_user.is_authenticated:
            emit('error', {'message': 'Authentication required'})
            return
        
        user_room = f"user_{current_user.id}"
        join_room(user_room)
        
        # Send current unread count
        service = NotificationWebSocketService()
        unread_count = service.get_unread_count(current_user.id)
        
        emit('subscription_confirmed', {
            'user_id': current_user.id,
            'unread_count': unread_count
        })
    
    @socketio.on('mark_notification_read')
    def handle_mark_notification_read(data):
        """Handle marking notification as read"""
        if not current_user.is_authenticated:
            emit('error', {'message': 'Authentication required'})
            return
        
        notification_id = data.get('notification_id')
        if notification_id:
            service = NotificationWebSocketService()
            notification = service.mark_as_read(notification_id, current_user.id)
            
            if notification:
                emit_notification_read(notification_id, current_user.id, service.get_unread_count(current_user.id))
        
        logger.info(f"User {current_user.username} marked notification {notification_id} as read")
    
    @socketio.on('fetch_unread_count')
    def handle_fetch_unread_count():
        """Handle fetching unread count"""
        if not current_user.is_authenticated:
            emit('error', {'message': 'Authentication required'})
            return
        
        service = NotificationWebSocketService()
        unread_count = service.get_unread_count(current_user.id)
        
        emit('unread_count', {'count': unread_count})
    
    @socketio.on('fetch_recent_notifications')
    def handle_fetch_recent_notifications(data):
        """Handle fetching recent notifications"""
        if not current_user.is_authenticated:
            emit('error', {'message': 'Authentication required'})
            return
        
        limit = data.get('limit', 10)
        service = NotificationWebSocketService()
        notifications = service.get_recent_notifications(current_user.id, limit)
        
        emit('recent_notifications', {
            'notifications': notifications,
            'count': len(notifications)
        })

def emit_notification_read(notification_id, user_id, unread_count):
    """Emit notification read event to user room"""
    from flask import current_app
    socketio = current_app.extensions['socketio']
    
    socketio.emit(
        'notification_read',
        {
            'notification_id': notification_id,
            'user_id': user_id,
            'unread_count': unread_count
        },
        room=f"user_{user_id}"
    )

def emit_new_notification(notification):
    """Emit new notification to user"""
    from flask import current_app
    socketio = current_app.extensions['socketio']
    
    socketio.emit(
        'new_notification',
        {
            'id': notification.id,
            'type': notification.type,
            'content': notification.content,
            'link': notification.link,
            'created_at': notification.created_at.isoformat(),
            'unread_count': get_unread_count(notification.user_id)
        },
        room=f"user_{notification.user_id}"
    )
```

### WebSocket Service

Update `app/websockets/service.py`:

```python
from flask import current_app
from flask_socketio import emit
from app.notifications.service import NotificationService
import logging

logger = logging.getLogger(__name__)

class NotificationWebSocketService:
    """WebSocket service for real-time notifications"""
    
    def __init__(self):
        self.notification_service = NotificationService()
    
    def emit_unread_count(self, user_id):
        """Emit unread count to user"""
        try:
            unread_count = self.get_unread_count(user_id)
            socketio = current_app.extensions['socketio']
            
            socketio.emit(
                'unread_count',
                {'count': unread_count},
                room=f"user_{user_id}"
            )
        except Exception as e:
            logger.error(f"Error emitting unread count: {str(e)}")
    
    def get_unread_count(self, user_id):
        """Get unread notification count for user"""
        try:
            return self.notification_service.get_unread_count(user_id)
        except Exception as e:
            logger.error(f"Error getting unread count: {str(e)}")
            return 0
    
    def mark_as_read(self, notification_id, user_id):
        """Mark notification as read"""
        try:
            return self.notification_service.mark_as_read(notification_id, user_id)
        except Exception as e:
            logger.error(f"Error marking notification as read: {str(e)}")
            return None
    
    def get_recent_notifications(self, user_id, limit=10):
        """Get recent notifications for user"""
        try:
            notifications = self.notification_service.get_user_notifications(
                user_id, limit=limit, unread_only=False
            )
            
            return [
                {
                    'id': notif.id,
                    'type': notif.type,
                    'content': notif.content,
                    'link': notif.link,
                    'is_read': notif.is_read,
                    'created_at': notif.created_at.isoformat()
                }
                for notif in notifications
            ]
        except Exception as e:
            logger.error(f"Error getting recent notifications: {str(e)}")
            return []
    
    def broadcast_notification(self, notification):
        """Broadcast notification to connected user"""
        try:
            socketio = current_app.extensions['socketio']
            
            socketio.emit(
                'new_notification',
                {
                    'id': notification.id,
                    'type': notification.type,
                    'content': notification.content,
                    'link': notification.link,
                    'created_at': notification.created_at.isoformat(),
                    'unread_count': self.get_unread_count(notification.user_id)
                },
                room=f"user_{notification.user_id}"
            )
        except Exception as e:
            logger.error(f"Error broadcasting notification: {str(e)}")
    
    def emit_system_notification(self, user_id, title, message, notification_type='system'):
        """Emit system notification to user"""
        try:
            socketio = current_app.extensions['socketio']
            
            socketio.emit(
                'system_notification',
                {
                    'title': title,
                    'message': message,
                    'type': notification_type,
                    'timestamp': datetime.utcnow().isoformat()
                },
                room=f"user_{user_id}"
            )
        except Exception as e:
            logger.error(f"Error emitting system notification: {str(e)}")
```

## Deployment Options

### Option 1: Standalone WebSocket Server

Create `run_websocket.py`:

```python
#!/usr/bin/env python3
"""
Standalone WebSocket Server
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.websockets.server import run_websocket_server

if __name__ == '__main__':
    run_websocket_server()
```

Run the server:
```bash
python run_websocket.py
```

### Option 2: Gunicorn with Eventlet

Create `gunicorn_config.py`:

```python
# Gunicorn configuration for WebSocket server
bind = "0.0.0.0:5003"
workers = 1
worker_class = "eventlet"
worker_connections = 1000
timeout = 30
keepalive = 2
max_requests = 1000
max_requests_jitter = 100
preload_app = True
```

Run with Gunicorn:
```bash
gunicorn --config gunicorn_config.py app.websockets.server:app
```

### Option 3: Docker Deployment

Create `Dockerfile.websocket`:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app
USER app

# Expose WebSocket port
EXPOSE 5003

# Run WebSocket server
CMD ["gunicorn", "--config", "gunicorn_config.py", "app.websockets.server:app"]
```

Create `docker-compose.websocket.yml`:

```yaml
version: '3.8'

services:
  websocket:
    build:
      context: .
      dockerfile: Dockerfile.websocket
    ports:
      - "5003:5003"
    environment:
      - WEBSOCKET_NOTIFICATION_ENABLED=true
      - WEBSOCKET_NOTIFICATION_HOST=0.0.0.0
      - WEBSOCKET_NOTIFICATION_PORT=5003
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis
    restart: unless-stopped

  redis:
    image: redis:6-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  redis_data:
```

## Scaling with Redis

### Redis Configuration

For multiple WebSocket server instances, configure Redis as a message broker:

```python
# app/websockets/server.py
from flask_socketio import SocketIO
from redis import Redis
from flask_socketio import RedisManager

def create_websocket_server():
    app = Flask(__name__)
    config = get_notification_config()
    
    # Redis configuration
    redis_client = Redis.from_url(config.redis_url)
    
    # Initialize Socket.IO with Redis adapter
    socketio = SocketIO(
        app,
        cors_allowed_origins=config.websocket_cors_origins,
        async_mode='eventlet',
        message_queue=RedisManager(config.redis_url, channel='socketio'),
        logger=config.websocket_debug,
        engineio_logger=config.websocket_debug
    )
    
    return app, socketio
```

### Load Balancer Configuration

**nginx configuration:**

```nginx
upstream websocket_backend {
    least_conn;
    server websocket1:5003;
    server websocket2:5003;
    server websocket3:5003;
}

server {
    listen 80;
    server_name your-domain.com;
    
    location /socket.io/ {
        proxy_pass http://websocket_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 86400;
    }
}
```

## Client Integration

### JavaScript Client

Create `app/static/js/websocket-client.js`:

```javascript
class NotificationWebSocketClient {
    constructor() {
        this.socket = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
    }
    
    connect() {
        const config = window.NOTIFICATION_CONFIG || {};
        const wsUrl = config.WEBSOCKET_URL || 'ws://localhost:5003';
        
        this.socket = io(wsUrl, {
            transports: ['websocket', 'polling'],
            upgrade: true,
            rememberUpgrade: true,
            timeout: 20000,
            forceNew: true
        });
        
        this.setupEventHandlers();
    }
    
    setupEventHandlers() {
        // Connection events
        this.socket.on('connect', () => {
            console.log('Connected to WebSocket server');
            this.reconnectAttempts = 0;
            this.subscribeToNotifications();
        });
        
        this.socket.on('disconnect', () => {
            console.log('Disconnected from WebSocket server');
            this.handleReconnect();
        });
        
        this.socket.on('connect_error', (error) => {
            console.error('WebSocket connection error:', error);
            this.handleReconnect();
        });
        
        // Notification events
        this.socket.on('new_notification', (data) => {
            this.handleNewNotification(data);
        });
        
        this.socket.on('notification_read', (data) => {
            this.handleNotificationRead(data);
        });
        
        this.socket.on('unread_count', (data) => {
            this.updateUnreadCount(data.count);
        });
        
        this.socket.on('system_notification', (data) => {
            this.handleSystemNotification(data);
        });
        
        // Error handling
        this.socket.on('error', (error) => {
            console.error('WebSocket error:', error);
        });
    }
    
    subscribeToNotifications() {
        this.socket.emit('subscribe_notifications');
    }
    
    handleReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`Attempting to reconnect... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
            
            setTimeout(() => {
                this.connect();
            }, this.reconnectDelay * this.reconnectAttempts);
        } else {
            console.error('Max reconnection attempts reached');
        }
    }
    
    handleNewNotification(data) {
        // Update UI with new notification
        this.updateNotificationList(data);
        this.updateUnreadCount(data.unread_count);
        this.showBrowserNotification(data);
    }
    
    handleNotificationRead(data) {
        // Update UI when notification is marked as read
        this.markNotificationAsRead(data.notification_id);
        this.updateUnreadCount(data.unread_count);
    }
    
    handleSystemNotification(data) {
        // Handle system notifications
        this.showSystemAlert(data);
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
        this.socket.emit('fetch_recent_notifications', { limit });
    }
    
    updateUnreadCount(count) {
        // Update unread count badge
        const badge = document.querySelector('.notification-badge');
        if (badge) {
            badge.textContent = count;
            badge.style.display = count > 0 ? 'block' : 'none';
        }
    }
    
    updateNotificationList(notification) {
        // Add notification to the list
        const list = document.querySelector('.notification-list');
        if (list) {
            const item = this.createNotificationItem(notification);
            list.insertBefore(item, list.firstChild);
        }
    }
    
    markNotificationAsRead(notificationId) {
        // Mark notification as read in UI
        const item = document.querySelector(`[data-notification-id="${notificationId}"]`);
        if (item) {
            item.classList.remove('unread');
            item.classList.add('read');
        }
    }
    
    showBrowserNotification(notification) {
        if ('Notification' in window && Notification.permission === 'granted') {
            new Notification(notification.title || 'New Notification', {
                body: notification.content,
                icon: '/static/images/notification-icon.png',
                tag: notification.id
            });
        }
    }
    
    showSystemAlert(notification) {
        // Show system alert
        alert(`${notification.title}: ${notification.message}`);
    }
    
    createNotificationItem(notification) {
        const div = document.createElement('div');
        div.className = 'notification-item unread';
        div.setAttribute('data-notification-id', notification.id);
        
        div.innerHTML = `
            <div class="notification-content">
                <h4>${notification.type}</h4>
                <p>${notification.content}</p>
                <small>${new Date(notification.created_at).toLocaleString()}</small>
            </div>
            <button onclick="notificationClient.markAsRead(${notification.id})">
                Mark as Read
            </button>
        `;
        
        return div;
    }
}

// Initialize WebSocket client
const notificationClient = new NotificationWebSocketClient();

// Connect when page loads
document.addEventListener('DOMContentLoaded', () => {
    // Request notification permission
    if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission();
    }
    
    // Connect to WebSocket
    notificationClient.connect();
});

// Make client globally available
window.notificationClient = notificationClient;
```

## Monitoring and Health Checks

### Health Check Endpoint

Create `app/websockets/health.py`:

```python
from flask import Blueprint, jsonify
from flask_socketio import SocketIO
import psutil
import time

health_bp = Blueprint('websocket_health', __name__)

@health_bp.route('/health')
def health_check():
    """WebSocket server health check"""
    try:
        # Get system stats
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        
        # Get WebSocket stats (if available)
        socketio = current_app.extensions.get('socketio')
        connected_clients = 0
        
        if socketio:
            # This would need to be implemented based on your Socket.IO version
            connected_clients = get_connected_clients_count(socketio)
        
        return jsonify({
            'status': 'healthy',
            'timestamp': time.time(),
            'websocket': {
                'connected_clients': connected_clients,
                'status': 'running'
            },
            'system': {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available': memory.available
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': time.time()
        }), 500

def get_connected_clients_count(socketio):
    """Get count of connected WebSocket clients"""
    # This implementation depends on your Socket.IO version
    # For Socket.IO 5.x:
    try:
        return len(socketio.manager.get_rooms())
    except:
        return 0
```

### Monitoring Script

Create `scripts/monitor_websocket.py`:

```python
#!/usr/bin/env python3
"""
WebSocket monitoring script
"""

import requests
import time
import json
from datetime import datetime

def monitor_websocket_server():
    """Monitor WebSocket server health"""
    health_url = "http://localhost:5003/health"
    
    while True:
        try:
            response = requests.get(health_url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                print(f"[{datetime.now()}] WebSocket Status: {data['status']}")
                print(f"  Connected Clients: {data['websocket']['connected_clients']}")
                print(f"  CPU Usage: {data['system']['cpu_percent']}%")
                print(f"  Memory Usage: {data['system']['memory_percent']}%")
            else:
                print(f"[{datetime.now()}] WebSocket Status: Error (HTTP {response.status_code})")
                
        except Exception as e:
            print(f"[{datetime.now()}] WebSocket Status: Connection Error - {str(e)}")
        
        time.sleep(30)  # Check every 30 seconds

if __name__ == '__main__':
    monitor_websocket_server()
```

## Testing

### WebSocket Testing

Create `tests/test_websocket.py`:

```python
import unittest
import socketio
import time
from app.websockets.server import create_websocket_server

class TestWebSocketServer(unittest.TestCase):
    
    def setUp(self):
        """Set up test client"""
        self.app, self.socketio = create_websocket_server()
        self.client = socketio.Client()
        
    def tearDown(self):
        """Clean up"""
        if self.client.connected:
            self.client.disconnect()
    
    def test_connection(self):
        """Test WebSocket connection"""
        connected = False
        
        def on_connect():
            nonlocal connected
            connected = True
        
        self.client.on('connect', on_connect)
        self.client.connect('http://localhost:5003')
        
        # Wait for connection
        time.sleep(1)
        
        self.assertTrue(connected)
    
    def test_notification_subscription(self):
        """Test notification subscription"""
        subscribed = False
        
        def on_subscription_confirmed(data):
            nonlocal subscribed
            subscribed = True
        
        self.client.on('subscription_confirmed', on_subscription_confirmed)
        self.client.connect('http://localhost:5003')
        self.client.emit('subscribe_notifications')
        
        # Wait for response
        time.sleep(1)
        
        self.assertTrue(subscribed)
    
    def test_unread_count(self):
        """Test unread count fetching"""
        count_received = False
        
        def on_unread_count(data):
            nonlocal count_received
            count_received = True
            self.assertIn('count', data)
        
        self.client.on('unread_count', on_unread_count)
        self.client.connect('http://localhost:5003')
        self.client.emit('fetch_unread_count')
        
        # Wait for response
        time.sleep(1)
        
        self.assertTrue(count_received)

if __name__ == '__main__':
    unittest.main()
```

## Troubleshooting

### Common Issues

1. **Connection Refused**
   - Check if WebSocket server is running
   - Verify port configuration
   - Check firewall settings

2. **CORS Errors**
   - Verify CORS configuration
   - Check allowed origins list
   - Ensure client uses correct protocol (ws:// or wss://)

3. **Authentication Issues**
   - Ensure Flask-Login is properly configured
   - Check session configuration
   - Verify authentication middleware

4. **Performance Issues**
   - Monitor connection count
   - Check Redis configuration (if scaling)
   - Review server resources

### Debug Mode

Enable debug mode for detailed logging:

```bash
export WEBSOCKET_NOTIFICATION_DEBUG=true
export NOTIFICATION_DEBUG_LEVEL=DEBUG
python run_websocket.py
```

## Production Checklist

- [ ] WebSocket server configured with proper host/port
- [ ] CORS settings configured for production domains
- [ ] Redis configured for scaling (if multiple instances)
- [ ] Load balancer configured for WebSocket traffic
- [ ] SSL/TLS certificates installed (for wss://)
- [ ] Health checks implemented
- [ ] Monitoring and logging configured
- [ ] Error handling and retry logic implemented
- [ ] Connection limits and rate limiting configured
- [ ] Backup and recovery procedures documented

---

**Last Updated:** May 12, 2026  
**Version:** 1.0  
**Status:** Production Ready
