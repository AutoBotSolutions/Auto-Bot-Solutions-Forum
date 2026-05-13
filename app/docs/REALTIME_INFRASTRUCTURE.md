# Real-time Infrastructure Documentation

## Overview

The Real-time Infrastructure system provides enterprise-grade real-time communication capabilities with WebSocket server clustering, event streaming, comprehensive monitoring, and intelligent load balancing. This system ensures high-performance real-time data delivery, scalability, and reliability for production applications.

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                   Real-time Infrastructure                        │
├─────────────────────────────────────────────────────────────────┤
│  WebSocketServer        │  EventStreamingManager │  RealtimeMonitor   │
│  - Clustering           │  - Pub/Sub patterns    │  - Metrics collection│
│  - Authentication       │  - Event routing       │  - Alerting         │
│  - Room management      │  - Persistence         │  - System monitoring │
├─────────────────────────────────────────────────────────────────┤
│  WebSocketLoadBalancer  │  RealtimeRoutes        │  Integration        │
│  - Load balancing       │  - Flask API           │  - Cross-system     │
│  - Health checking      │  - Management          │  - Event handling   │
│  - Failover support     │  - Configuration       │  - Data flow        │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
Client Connection → Load Balancer → WebSocket Server → Event Streaming → Response
        │               │               │               │
        ├─ Authentication ├─ Node Selection ├─ Room Management ├─ Event Routing
        ├─ Session Mgmt   ├─ Health Check   ├─ Message Handling ├─ Persistence
        └─ Load Balance   └─ Failover       └─ Broadcasting     └─ Monitoring
```

## Components

### WebSocketServer

Advanced WebSocket server with clustering, authentication, and room management capabilities.

#### Features
- **WebSocket Clustering**: Multi-server WebSocket clustering
- **Authentication**: JWT and session-based authentication
- **Room Management**: Dynamic room creation and management
- **Message Routing**: Intelligent message routing and filtering
- **Health Monitoring**: Real-time server health checks
- **Graceful Degradation**: Fallback mechanisms for connection failures

#### Configuration
```python
from app.infrastructure.realtime import WebSocketServer, ServerConfig

config = ServerConfig(
    host="0.0.0.0",
    port=8080,
    max_connections=10000,
    ping_interval=30,
    ping_timeout=10,
    close_timeout=10,
    compression=True,
    origins=["*"],
    ssl_enabled=False,
    auth_required=True,
    jwt_secret="your-secret-key",
    jwt_algorithm="HS256",
    enable_clustering=True,
    cluster_nodes=[
        {"host": "localhost", "port": 8080},
        {"host": "localhost", "port": 8081},
        {"host": "localhost", "port": 8082}
    ],
    load_balancing_enabled=True,
    health_check_interval=30,
    metrics_enabled=True
)

server = WebSocketServer(config)
```

#### Usage Examples

##### Basic WebSocket Operations
```python
# Start WebSocket server
server.start()

# Add message handlers
def handle_message(connection_info, message):
    print(f"Received message from {connection_info.user_id}: {message}")

server.add_message_handler("chat_message", handle_message)

# Add connection handlers
def handle_connection(connection_info):
    print(f"New connection: {connection_info.connection_id}")

server.add_connection_handler("open", handle_connection)

# Stop server
server.stop()
```

##### Room Management
```python
# Get room information
room_info = server.get_room_info("chat_room_123")

# Broadcast message to room
await server.broadcast_to_room("chat_room_123", {
    "type": "chat_message",
    "user_id": "user123",
    "message": "Hello, World!"
})

# Broadcast to all connections
await server.broadcast_to_all({
    "type": "system_message",
    "message": "Server maintenance in 5 minutes"
})
```

##### Connection Management
```python
# Get all connections
connections = server.get_connections()

# Get connections for specific user
user_connections = [
    conn for conn in connections 
    if conn['user_id'] == 'user123'
]

# Send message to specific connection
await server.send_to_connection(connection_id, {
    "type": "private_message",
    "message": "This is a private message"
})
```

### EventStreamingManager

Advanced event streaming system with publish/subscribe patterns, filtering, and persistence.

#### Features
- **Publish/Subscribe**: Event-driven architecture
- **Event Filtering**: Advanced event filtering and routing
- **Persistence**: Event persistence with Redis
- **Batch Processing**: Efficient batch event processing
- **Event Routing**: Intelligent event routing and delivery

#### Configuration
```python
from app.infrastructure.realtime import EventStreamingManager, StreamConfig

config = StreamConfig(
    max_events_per_second=10000,
    max_queue_size=100000,
    persistence_enabled=True,
    persistence_type="redis",
    redis_client=None,  # Use default Redis client
    event_ttl=3600,  # 1 hour
    enable_filtering=True,
    enable_routing=True,
    enable_metrics=True,
    batch_size=100,
    batch_timeout=1.0,
    compression_enabled=True,
    encryption_enabled=False
)

streaming_manager = EventStreamingManager(config)
```

#### Usage Examples

##### Event Publishing
```python
from app.infrastructure.realtime import EventType, EventPriority

# Publish user event
event_id = streaming_manager.publish_event(
    EventType.USER_EVENT,
    {"user_id": "user123", "action": "login"},
    source="auth_service",
    target="notification_service",
    priority=EventPriority.NORMAL,
    ttl=3600
)

# Publish system event
event_id = streaming_manager.publish_event(
    EventType.SYSTEM_EVENT,
    {"level": "info", "message": "Server started"},
    source="system",
    priority=EventPriority.HIGH
)
```

##### Event Subscription
```python
# Subscribe to user events
subscription_id = streaming_manager.subscribe(
    "notification_service",
    EventType.USER_EVENT,
    filters={"source": "auth_service"}
)

# Subscribe with custom callback
def handle_user_event(event):
    print(f"User event: {event.data}")
    # Send notification to user
    send_notification(event.data["user_id"], event.data)

subscription_id = streaming_manager.subscribe(
    "notification_handler",
    EventType.USER_EVENT,
    callback=handle_user_event
)
```

##### Event Filtering
```python
# Add custom filter
def filter_sensitive_events(event):
    return "sensitive" not in event.data

streaming_manager.add_filter("sensitive_filter", filter_sensitive_events)

# Subscribe with filters
subscription_id = streaming_manager.subscribe(
    "public_service",
    EventType.USER_EVENT,
    filters={"action": "login"}  # Only login events
)
```

### RealtimeMonitor

Comprehensive monitoring system for real-time infrastructure with metrics collection, alerting, and analytics.

#### Features
- **Real-time Metrics**: Performance metrics collection
- **System Monitoring**: CPU, memory, and network monitoring
- **Alerting System**: Configurable alerts with thresholds
- **Performance Analysis**: Response time and throughput analysis
- **Health Monitoring**: System health checks

#### Configuration
```python
from app.infrastructure.realtime import RealtimeMonitor

monitor = RealtimeMonitor(buffer_size=10000)
```

#### Usage Examples

##### Metrics Collection
```python
# Record connection metrics
monitor.record_metric("connection_active", 100)

# Record event metrics
monitor.record_metric("event_rate", 50.5)

# Record system metrics
monitor.record_metric("system_cpu", 25.0)
monitor.record_metric("system_memory", 60.0)
```

##### Alert Management
```python
from app.infrastructure.realtime import AlertLevel

# Create alert
monitor.create_alert(
    "high_connection_count",
    "High connection count detected",
    AlertLevel.WARNING,
    "connection_active",
    500,  # threshold
    300   # 5 minutes window
)

# Get alerts
alerts = monitor.get_alerts()

# Enable/disable alerts
monitor.enable_alert("high_connection_count")
monitor.disable_alert("high_connection_count")
```

##### Performance Analysis
```python
# Get connection metrics
connection_metrics = monitor.get_connection_metrics()

# Get event metrics
event_metrics = monitor.get_event_metrics()

# Get system metrics
system_metrics = monitor.get_system_metrics()

# Get comprehensive metrics
comprehensive_metrics = monitor.get_comprehensive_metrics()
```

### WebSocketLoadBalancer

Intelligent load balancer for WebSocket connections with multiple algorithms and health checking.

#### Features
- **Multiple Algorithms**: Round robin, weighted, least connections, etc.
- **Health Checking**: Real-time node health monitoring
- **Session Affinity**: Sticky sessions and connection affinity
- **Failover Support**: Automatic failover and recovery
- **Dynamic Scaling**: Dynamic node addition and removal

#### Configuration
```python
from app.infrastructure.realtime import WebSocketLoadBalancer, LoadBalancerConfig

config = LoadBalancerConfig(
    strategy=LoadBalancingStrategy.ROUND_ROBIN,
    health_check_interval=30,
    health_check_timeout=5,
    max_failures=3,
    recovery_timeout=300,
    enable_sticky_sessions=True,
    session_affinity_key="user_id",
    enable_health_checks=True,
    enable_failover=True,
    enable_metrics=True,
    connection_timeout=30,
    retry_attempts=3,
    retry_delay=1.0
)

load_balancer = WebSocketLoadBalancer(config)
```

#### Usage Examples

##### Node Management
```python
# Add nodes
load_balancer.add_node("node1", "localhost", 8001, weight=1, max_connections=100)
load_balancer.add_node("node2", "localhost", 8002, weight=2, max_connections=200)
load_balancer.add_node("node3", "localhost", 8003, weight=1, max_connections=100)

# Remove node
load_balancer.remove_node("node1")

# Update node weight
load_balancer.update_node_weight("node2", 3)
```

##### Load Balancing
```python
# Select node for new connection
node_id = load_balancer.select_node("conn123", "user123")

# Register connection
success = load_balancer.register_connection("conn123", node_id, "user123")

# Unregister connection
success = load_balancer.unregister_connection("conn123")

# Get node for connection
node_id = load_balancer.get_node_for_connection("conn123")
```

##### Strategy Management
```python
from app.infrastructure.realtime import LoadBalancingStrategy

# Change balancing strategy
load_balancer.set_balancing_strategy(LoadBalancingStrategy.LEAST_CONNECTIONS)

# Clear session affinity
load_balancer.clear_session_affinity()
```

## API Endpoints

The real-time infrastructure provides comprehensive REST API endpoints for management and monitoring.

### WebSocket Server Endpoints

#### Connection Management
```
GET /api/infrastructure/realtime/connections
GET /api/infrastructure/realtime/rooms
GET /api/infrastructure/realtime/rooms/{room_id}
POST /api/infrastructure/realtime/broadcast
POST /api/infrastructure/realtime/rooms/{room_id}/broadcast
```

### Event Streaming Endpoints

#### Event Management
```
POST /api/infrastructure/realtime/events/publish
POST /api/infrastructure/realtime/events/subscribe
DELETE /api/infrastructure/realtime/events/subscriptions/{subscription_id}
GET /api/infrastructure/realtime/events/history
GET /api/infrastructure/realtime/events/subscriptions
GET /api/infrastructure/realtime/events/metrics
```

### Monitoring Endpoints

#### Metrics and Alerts
```
GET /api/infrastructure/realtime/monitoring/metrics
GET /api/infrastructure/realtime/monitoring/connection-metrics
GET /api/infrastructure/realtime/monitoring/event-metrics
GET /api/infrastructure/realtime/monitoring/system-metrics
GET /api/infrastructure/realtime/monitoring/alerts
POST /api/infrastructure/realtime/monitoring/alerts
POST /api/infrastructure/realtime/monitoring/alerts/{alert_id}/enable
POST /api/infrastructure/realtime/monitoring/alerts/{alert_id}/disable
DELETE /api/infrastructure/realtime/monitoring/alerts/{alert_id}
```

### Load Balancer Endpoints

#### Node Management
```
GET /api/infrastructure/realtime/load-balancer/nodes
POST /api/infrastructure/realtime/load-balancer/nodes
DELETE /api/infrastructure/realtime/load-balancer/nodes/{node_id}
GET /api/infrastructure/realtime/load-balancer/nodes/{node_id}
PUT /api/infrastructure/realtime/load-balancer/nodes/{node_id}/weight
POST /api/infrastructure/realtime/load-balancer/strategy
GET /api/infrastructure/realtime/load-balancer/stats
POST /api/infrastructure/realtime/load-balancer/session-affinity/clear
```

## Configuration

### Environment Variables

```bash
# WebSocket Server Configuration
WS_HOST=0.0.0.0
WS_PORT=8080
WS_MAX_CONNECTIONS=10000
WS_AUTH_REQUIRED=true
WS_JWT_SECRET=your-secret-key
WS_ENABLE_CLUSTERING=true

# Event Streaming Configuration
EVENT_MAX_EVENTS_PER_SECOND=10000
EVENT_PERSISTENCE_ENABLED=true
EVENT_TTL=3600
EVENT_BATCH_SIZE=100

# Monitoring Configuration
MONITORING_ENABLED=true
ALERTING_ENABLED=true
HEALTH_CHECK_INTERVAL=30

# Load Balancer Configuration
LB_STRATEGY=round_robin
LB_HEALTH_CHECK_INTERVAL=30
LB_ENABLE_STICKY_SESSIONS=true
LB_SESSION_AFFINITY_KEY=user_id
```

### Application Configuration

```python
# config/realtime.py
REALTIME_CONFIG = {
    'websocket': {
        'host': os.getenv('WS_HOST', '0.0.0.0'),
        'port': int(os.getenv('WS_PORT', 8080)),
        'max_connections': int(os.getenv('WS_MAX_CONNECTIONS', 10000)),
        'auth_required': os.getenv('WS_AUTH_REQUIRED', 'true').lower() == 'true',
        'jwt_secret': os.getenv('WS_JWT_SECRET'),
        'enable_clustering': os.getenv('WS_ENABLE_CLUSTERING', 'true').lower() == 'true'
    },
    'event_streaming': {
        'max_events_per_second': int(os.getenv('EVENT_MAX_EVENTS_PER_SECOND', 10000)),
        'persistence_enabled': os.getenv('EVENT_PERSISTENCE_ENABLED', 'true').lower() == 'true',
        'ttl': int(os.getenv('EVENT_TTL', 3600)),
        'batch_size': int(os.getenv('EVENT_BATCH_SIZE', 100))
    },
    'monitoring': {
        'enabled': os.getenv('MONITORING_ENABLED', 'true').lower() == 'true',
        'alerting_enabled': os.getenv('ALERTING_ENABLED', 'true').lower() == 'true',
        'health_check_interval': int(os.getenv('HEALTH_CHECK_INTERVAL', 30))
    },
    'load_balancer': {
        'strategy': os.getenv('LB_STRATEGY', 'round_robin'),
        'health_check_interval': int(os.getenv('LB_HEALTH_CHECK_INTERVAL', 30)),
        'enable_sticky_sessions': os.getenv('LB_ENABLE_STICKY_SESSIONS', 'true').lower() == 'true',
        'session_affinity_key': os.getenv('LB_SESSION_AFFINITY_KEY', 'user_id')
    }
}
```

## Performance Optimization

### Connection Optimization

#### WebSocket Configuration
```python
# Optimize WebSocket settings
config = ServerConfig(
    ping_interval=30,      # Keep connections alive
    ping_timeout=10,       # Detect dead connections
    close_timeout=10,      # Graceful close timeout
    compression=True,       # Enable compression
    max_connections=10000   # Limit concurrent connections
)
```

#### Connection Pooling
```python
# Use connection pooling for Redis
import redis
from redis.connection import ConnectionPool

pool = ConnectionPool(
    host='localhost',
    port=6379,
    max_connections=50,
    retry_on_timeout=True
)

redis_client = redis.Redis(connection_pool=pool)
```

### Event Processing Optimization

#### Batch Processing
```python
# Increase batch size for better performance
config = StreamConfig(
    batch_size=500,        # Larger batch size
    batch_timeout=0.5,     # Shorter timeout
    max_events_per_second=20000  # Higher throughput
)
```

#### Event Filtering
```python
# Add efficient filters
def filter_important_events(event):
    # Filter out low-priority events
    return event.priority.value in ['high', 'critical']

streaming_manager.add_filter("priority_filter", filter_important_events)
```

### Load Balancing Optimization

#### Algorithm Selection
```python
# Choose optimal algorithm for your use case
from app.infrastructure.realtime import LoadBalancingStrategy

# For even distribution
load_balancer.set_balancing_strategy(LoadBalancingStrategy.ROUND_ROBIN)

# For performance-based routing
load_balancer.set_balancing_strategy(LoadBalancingStrategy.LEAST_CONNECTIONS)

# For user affinity
load_balancer.set_balancing_strategy(LoadBalancingStrategy.HASH_BASED)
```

#### Node Configuration
```python
# Configure nodes with appropriate weights
load_balancer.add_node("high_perf", "server1", 8001, weight=3, max_connections=500)
load_balancer.add_node("medium_perf", "server2", 8002, weight=2, max_connections=300)
load_balancer.add_node("low_perf", "server3", 8003, weight=1, max_connections=200)
```

## Security Considerations

### Authentication and Authorization

#### JWT Authentication
```python
import jwt
from functools import wraps

def authenticate_websocket(token):
    try:
        payload = jwt.decode(
            token,
            config.jwt_secret,
            algorithms=[config.jwt_algorithm]
        )
        return payload
    except jwt.InvalidTokenError:
        return None

# WebSocket authentication decorator
def websocket_auth_required(f):
    @wraps(f)
    async def decorated_function(connection_info, message):
        if not connection_info.authenticated:
            await server.send_to_connection(
                connection_info.connection_id,
                {"type": "auth_error", "message": "Authentication required"}
            )
            return
        return await f(connection_info, message)
    return decorated_function
```

#### Rate Limiting
```python
import time
from collections import defaultdict

class RateLimiter:
    def __init__(self, max_requests=100, window=60):
        self.max_requests = max_requests
        self.window = window
        self.requests = defaultdict(list)
    
    def is_allowed(self, user_id):
        now = time.time()
        user_requests = self.requests[user_id]
        
        # Remove old requests
        user_requests[:] = [req_time for req_time in user_requests if now - req_time < self.window]
        
        # Check if under limit
        if len(user_requests) < self.max_requests:
            user_requests.append(now)
            return True
        
        return False

# Use in WebSocket handlers
rate_limiter = RateLimiter(max_requests=100, window=60)

@websocket_auth_required
def handle_message(connection_info, message):
    if not rate_limiter.is_allowed(connection_info.user_id):
        await server.send_to_connection(
            connection_info.connection_id,
            {"type": "rate_limit_error", "message": "Rate limit exceeded"}
        )
        return
    # Process message
```

### Data Encryption

#### Message Encryption
```python
from cryptography.fernet import Fernet
import base64

class MessageEncryptor:
    def __init__(self, key):
        self.cipher = Fernet(key)
    
    def encrypt(self, message):
        if isinstance(message, dict):
            message = json.dumps(message)
        return self.cipher.encrypt(message.encode())
    
    def decrypt(self, encrypted_message):
        decrypted = self.cipher.decrypt(encrypted_message)
        return json.loads(decrypted.decode())

# Use in WebSocket handlers
encryptor = MessageEncryptor(encryption_key)

async def send_encrypted_message(connection_id, message):
    encrypted = encryptor.encrypt(message)
    await server.send_to_connection(connection_id, encrypted)
```

### Access Control

#### Room Access Control
```python
class RoomAccessControl:
    def __init__(self):
        self.room_permissions = {}
    
    def grant_access(self, user_id, room_id, permissions):
        if room_id not in self.room_permissions:
            self.room_permissions[room_id] = {}
        self.room_permissions[room_id][user_id] = permissions
    
    def check_access(self, user_id, room_id, permission):
        if room_id not in self.room_permissions:
            return False
        if user_id not in self.room_permissions[room_id]:
            return False
        return permission in self.room_permissions[room_id][user_id]

# Use in room operations
access_control = RoomAccessControl()

@websocket_auth_required
async def handle_join_room(connection_info, message):
    room_id = message.get('room_id')
    
    if not access_control.check_access(connection_info.user_id, room_id, 'join'):
        await server.send_to_connection(
            connection_info.connection_id,
            {"type": "access_denied", "message": "No access to room"}
        )
        return
    
    # Join room
    connection_info.room_ids.add(room_id)
    server.rooms[room_id].add(connection_info.connection_id)
```

## Monitoring and Alerting

### Key Metrics

#### WebSocket Metrics
- **Active Connections**: Current number of active connections
- **Connection Rate**: New connections per second
- **Message Rate**: Messages sent/received per second
- **Error Rate**: Percentage of failed operations
- **Response Time**: Average message processing time

#### Event Metrics
- **Event Rate**: Events processed per second
- **Queue Size**: Current event queue size
- **Processing Time**: Average event processing time
- **Failed Events**: Number of failed events
- **Subscription Count**: Active event subscriptions

#### System Metrics
- **CPU Usage**: System CPU utilization
- **Memory Usage**: System memory utilization
- **Network I/O**: Network input/output
- **Disk Usage**: Disk space usage
- **Thread Count**: Active thread count

### Alert Configuration

```python
# Connection count alert
monitor.create_alert(
    "high_connection_count",
    "High WebSocket connection count",
    AlertLevel.WARNING,
    "connection_active",
    8000,  # 80% of max connections
    300    # 5 minutes
)

# Event rate alert
monitor.create_alert(
    "high_event_rate",
    "High event processing rate",
    AlertLevel.WARNING,
    "event_rate",
    8000,  # 80% of max rate
    300    # 5 minutes
)

# System CPU alert
monitor.create_alert(
    "high_cpu_usage",
    "High CPU usage detected",
    AlertLevel.ERROR,
    "system_cpu",
    80.0,  # 80%
    300    # 5 minutes
)
```

### Custom Metrics

```python
# Custom metric collection
def collect_custom_metrics():
    # Application-specific metrics
    active_users = get_active_user_count()
    monitor.record_metric("active_users", active_users)
    
    room_count = len(server.rooms)
    monitor.record_metric("active_rooms", room_count)
    
    message_types = get_message_type_stats()
    for msg_type, count in message_types.items():
        monitor.record_metric(f"messages_{msg_type}", count)

# Schedule custom metrics collection
import threading
import time

def metrics_collector():
    while True:
        collect_custom_metrics()
        time.sleep(30)  # Collect every 30 seconds

metrics_thread = threading.Thread(target=metrics_collector, daemon=True)
metrics_thread.start()
```

## Troubleshooting

### Common Issues

#### WebSocket Connection Issues
```python
# Check WebSocket server status
stats = server.get_stats()
print(f"Server status: {stats['server_status']}")
print(f"Active connections: {stats['active_connections']}")

# Check connection logs
for connection in server.get_connections():
    if connection['authenticated']:
        print(f"Authenticated connection: {connection['connection_id']}")
    else:
        print(f"Unauthenticated connection: {connection['connection_id']}")
```

#### Event Processing Issues
```python
# Check event streaming metrics
metrics = streaming_manager.get_metrics()
print(f"Total events: {metrics['total_events']}")
print(f"Failed events: {metrics['failed_events']}")
print(f"Queue size: {metrics['queue_size']}")

# Check subscriptions
subscriptions = streaming_manager.get_subscriptions()
print(f"Active subscriptions: {len(subscriptions)}")
```

#### Load Balancer Issues
```python
# Check load balancer stats
stats = load_balancer.get_load_balancer_stats()
print(f"Total nodes: {stats['total_nodes']}")
print(f"Healthy nodes: {stats['healthy_nodes']}")
print(f"Active connections: {stats['active_connections']}")

# Check individual node stats
for node in load_balancer.get_all_node_stats():
    print(f"Node {node['node_id']}: {node['active_connections']} connections")
```

### Debug Tools

#### WebSocket Debugging
```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Connection debugging
def debug_connection(connection_info):
    print(f"Connection ID: {connection_info.connection_id}")
    print(f"User ID: {connection_info.user_id}")
    print(f"Room IDs: {connection_info.room_ids}")
    print(f"Connected at: {connection_info.connected_at}")
    print(f"Last activity: {connection_info.last_activity}")

# Message debugging
def debug_message(connection_info, message):
    print(f"Message from {connection_info.user_id}: {message}")
    print(f"Message type: {message.get('type')}")
    print(f"Message size: {len(str(message))}")
```

#### Event Debugging
```python
# Event debugging
def debug_event(event):
    print(f"Event ID: {event.event_id}")
    print(f"Event type: {event.event_type}")
    print(f"Event source: {event.source}")
    print(f"Event target: {event.target}")
    print(f"Event timestamp: {event.timestamp}")
    print(f"Event data: {event.data}")

# Subscription debugging
def debug_subscription(subscription):
    print(f"Subscription ID: {subscription.subscription_id}")
    print(f"Subscriber ID: {subscription.subscriber_id}")
    print(f"Event type: {subscription.event_type}")
    print(f"Filters: {subscription.filters}")
    print(f"Event count: {subscription.event_count}")
```

## Best Practices

### Connection Management
```python
# Implement connection lifecycle management
class ConnectionManager:
    def __init__(self):
        self.connections = {}
        self.user_sessions = {}
    
    def add_connection(self, connection_id, user_id):
        self.connections[connection_id] = user_id
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = []
        self.user_sessions[user_id].append(connection_id)
    
    def remove_connection(self, connection_id):
        if connection_id in self.connections:
            user_id = self.connections[connection_id]
            del self.connections[connection_id]
            if user_id in self.user_sessions:
                self.user_sessions[user_id].remove(connection_id)
                if not self.user_sessions[user_id]:
                    del self.user_sessions[user_id]
    
    def get_user_connections(self, user_id):
        return self.user_sessions.get(user_id, [])
```

### Event Design
```python
# Use consistent event structure
class EventSchema:
    REQUIRED_FIELDS = ['event_id', 'event_type', 'timestamp', 'data']
    
    @staticmethod
    def validate_event(event):
        for field in EventSchema.REQUIRED_FIELDS:
            if field not in event:
                raise ValueError(f"Missing required field: {field}")
        
        # Validate event type
        from app.infrastructure.realtime import EventType
        if event['event_type'] not in EventType:
            raise ValueError(f"Invalid event type: {event['event_type']}")
        
        return True

# Use event versioning
def create_event(event_type, data, version="1.0"):
    return {
        'event_id': str(uuid.uuid4()),
        'event_type': event_type,
        'version': version,
        'timestamp': datetime.utcnow().isoformat(),
        'data': data
    }
```

### Error Handling
```python
# Implement comprehensive error handling
class RealtimeErrorHandler:
    def __init__(self):
        self.error_counts = defaultdict(int)
        self.error_threshold = 100
    
    def handle_error(self, error, context):
        error_type = type(error).__name__
        self.error_counts[error_type] += 1
        
        # Log error
        logger.error(f"Error in {context}: {error}")
        
        # Check error threshold
        if self.error_counts[error_type] > self.error_threshold:
            self.trigger_alert(error_type, context)
    
    def trigger_alert(self, error_type, context):
        # Send alert to monitoring system
        monitor.create_alert(
            f"high_{error_type}_error_rate",
            f"High {error_type} error rate in {context}",
            AlertLevel.ERROR,
            "error_rate",
            0.1,  # 10% error rate
            300
        )

# Use error handler
error_handler = RealtimeErrorHandler()

try:
    # WebSocket operation
    await server.send_to_connection(connection_id, message)
except Exception as e:
    error_handler.handle_error(e, "websocket_send")
```

## Integration Examples

### Flask Integration
```python
from flask import Flask
from app.infrastructure.realtime import WebSocketServer, EventStreamingManager

app = Flask(__name__)

# Initialize real-time components
websocket_server = WebSocketServer()
event_streaming = EventStreamingManager()

@app.route('/api/events', methods=['POST'])
def publish_event():
    data = request.get_json()
    
    # Publish event
    event_id = event_streaming.publish_event(
        EventType.USER_EVENT,
        data,
        source="flask_api"
    )
    
    return jsonify({"event_id": event_id})

# WebSocket endpoint
@websocket_server.add_message_handler("api_request")
async def handle_api_request(connection_info, message):
    # Handle WebSocket requests from clients
    response = process_api_request(message)
    await websocket_server.send_to_connection(
        connection_info.connection_id,
        response
    )
```

### Django Integration
```python
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from app.infrastructure.realtime import EventStreamingManager

event_streaming = EventStreamingManager()

@require_POST
def publish_event(request):
    data = json.loads(request.body)
    
    # Publish event
    event_id = event_streaming.publish_event(
        EventType.USER_EVENT,
        data,
        source="django_api"
    )
    
    return JsonResponse({"event_id": event_id})

# Django channels integration
from channels.generic.websocket import AsyncWebsocketConsumer

class RealtimeConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        
        # Register with WebSocket server
        connection_id = str(uuid.uuid4())
        self.connection_id = connection_id
        
        # Add to WebSocket server
        websocket_server.register_connection(connection_id, None, self.scope["user"].id)
    
    async def disconnect(self, close_code):
        # Unregister from WebSocket server
        websocket_server.unregister_connection(self.connection_id)
    
    async def receive(self, text_data):
        message = json.loads(text_data)
        
        # Handle message
        await websocket_server.handle_message(self.connection_id, message)
```

## Testing

### Unit Testing
```python
import unittest
from unittest.mock import Mock, patch
from app.infrastructure.realtime import WebSocketServer, ServerConfig

class TestWebSocketServer(unittest.TestCase):
    def setUp(self):
        self.config = ServerConfig(auth_required=False)
        self.server = WebSocketServer(self.config)
    
    def test_server_creation(self):
        self.assertIsNotNone(self.server)
        self.assertEqual(self.server.config.host, "0.0.0.0")
        self.assertEqual(self.server.config.port, 8080)
    
    def test_message_handler(self):
        # Mock connection info
        connection_info = Mock()
        connection_info.connection_id = "test_conn"
        connection_info.user_id = "test_user"
        
        # Test message handler
        message = {"type": "test", "data": "test_data"}
        
        # Add handler
        handler_called = False
        def test_handler(conn_info, msg):
            nonlocal handler_called
            handler_called = True
            self.assertEqual(conn_info.connection_id, "test_conn")
            self.assertEqual(msg, message)
        
        self.server.add_message_handler("test", test_handler)
        
        # Trigger handler
        for handler in self.server.message_handlers["test"]:
            await handler(connection_info, message)
        
        self.assertTrue(handler_called)
```

### Integration Testing
```python
import pytest
import asyncio
from app.infrastructure.realtime import WebSocketServer, EventStreamingManager

@pytest.fixture
async def websocket_server():
    config = ServerConfig(auth_required=False, enable_clustering=False)
    server = WebSocketServer(config)
    yield server
    server.stop()

@pytest.fixture
async def event_streaming():
    config = StreamConfig(persistence_enabled=False)
    streaming = EventStreamingManager(config)
    yield streaming
    streaming.shutdown()

@pytest.mark.asyncio
async def test_websocket_connection(websocket_server):
    # Test WebSocket connection
    connection_info = Mock()
    connection_info.connection_id = "test_conn"
    connection_info.user_id = "test_user"
    
    # Add connection
    websocket_server.connections["test_conn"] = connection_info
    
    # Test connection exists
    assert "test_conn" in websocket_server.connections
    assert websocket_server.connections["test_conn"].user_id == "test_user"

@pytest.mark.asyncio
async def test_event_streaming(event_streaming):
    # Test event publishing
    from app.infrastructure.realtime import EventType
    
    event_id = event_streaming.publish_event(
        EventType.USER_EVENT,
        {"test": "data"}
    )
    
    assert event_id is not None
    
    # Test subscription
    subscription_id = event_streaming.subscribe("test_subscriber")
    
    assert subscription_id is not None
    
    # Test subscription exists
    subscriptions = event_streaming.get_subscriptions()
    assert len(subscriptions) > 0
```

## Deployment

### Docker Configuration
```dockerfile
FROM python:3.11-slim

# Install WebSocket dependencies
RUN pip install websockets psutil

# Copy application code
COPY . /app
WORKDIR /app

# Expose WebSocket port
EXPOSE 8080

# Start WebSocket server
CMD ["python", "-m", "app.infrastructure.realtime.websocket_server"]
```

### Kubernetes Configuration
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: realtime-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: realtime-service
  template:
    metadata:
      labels:
        app: realtime-service
    spec:
      containers:
      - name: realtime-service
        image: myapp/realtime-service:latest
        ports:
        - containerPort: 8080
        env:
        - name: WS_HOST
          value: "0.0.0.0"
        - name: WS_PORT
          value: "8080"
        - name: WS_MAX_CONNECTIONS
          value: "10000"
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: realtime-service
spec:
  selector:
    app: realtime-service
  ports:
  - port: 8080
    targetPort: 8080
  type: LoadBalancer
```

### Production Checklist
- [ ] WebSocket clustering configured and tested
- [ ] Event streaming with persistence enabled
- [ ] Monitoring and alerting configured
- [ ] Load balancing with health checks
- [ ] Authentication and authorization implemented
- [ ] Rate limiting and throttling in place
- [ ] SSL/TLS encryption enabled
- [ ] Backup and recovery procedures documented
- [ ] Performance testing completed
- [ ] Capacity planning and scaling strategy
- [ ] Disaster recovery plan in place
- [ ] Security audit completed

## Support

For support and questions about the Real-time Infrastructure system:

1. Check the [Troubleshooting Guide](./TROUBLESHOOTING.md)
2. Review the [Common Issues](./COMMON_ISSUES.md)
3. Consult the [API Documentation](./API_DOCUMENTATION.md)
4. Contact the infrastructure team

## Changelog

### Version 1.0.0 (May 12, 2026)
- Initial implementation of Real-time Infrastructure
- WebSocket server with clustering and authentication
- Event streaming with pub/sub patterns
- Real-time monitoring with comprehensive metrics
- Load balancing with multiple algorithms
- Production-ready error handling and security
- Full API documentation and testing
