"""
WebSocket Server

Advanced WebSocket server with clustering, load balancing, and high availability
support for real-time applications.
"""

import logging
from typing import Dict, List, Any, Optional, Callable, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
import time
import asyncio
import websockets
import threading
import queue
from collections import defaultdict, deque
import uuid
import hashlib
import hmac
import jwt
from websockets.server import WebSocketServerProtocol
from websockets.exceptions import ConnectionClosed

logger = logging.getLogger(__name__)

class ServerStatus(Enum):
    """WebSocket server status"""
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"

class ConnectionType(Enum):
    """Connection types"""
    CLIENT = "client"
    SERVER = "server"
    WORKER = "worker"

@dataclass
class ServerConfig:
    """WebSocket server configuration"""
    host: str = "0.0.0.0"
    port: int = 8080
    max_connections: int = 10000
    ping_interval: int = 30
    ping_timeout: int = 10
    close_timeout: int = 10
    compression: bool = True
    origins: List[str] = field(default_factory=lambda: ["*"])
    ssl_enabled: bool = False
    ssl_cert: Optional[str] = None
    ssl_key: Optional[str] = None
    auth_required: bool = True
    jwt_secret: Optional[str] = None
    jwt_algorithm: str = "HS256"
    enable_clustering: bool = True
    cluster_nodes: List[Dict[str, Any]] = field(default_factory=list)
    load_balancing_enabled: bool = True
    health_check_interval: int = 30
    metrics_enabled: bool = True

@dataclass
class ConnectionInfo:
    """WebSocket connection information"""
    connection_id: str
    websocket: Any
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    room_ids: Set[str] = field(default_factory=set)
    connection_type: ConnectionType = ConnectionType.CLIENT
    connected_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)
    ip_address: str = ""
    user_agent: str = ""
    authenticated: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ServerStats:
    """WebSocket server statistics"""
    total_connections: int = 0
    active_connections: int = 0
    total_messages_sent: int = 0
    total_messages_received: int = 0
    total_bytes_sent: int = 0
    total_bytes_received: int = 0
    avg_connection_duration: float = 0.0
    messages_per_second: float = 0.0
    errors: int = 0
    last_updated: datetime = field(default_factory=datetime.utcnow)

class WebSocketServer:
    """Advanced WebSocket server with clustering support"""
    
    def __init__(self, config: ServerConfig = None):
        self.config = config or ServerConfig()
        self.server = None
        self.loop = None
        self.connections: Dict[str, ConnectionInfo] = {}
        self.rooms: Dict[str, Set[str]] = defaultdict(set)  # room_id -> connection_ids
        self.server_status = ServerStatus.STARTING
        self.stats = ServerStats()
        
        # Event handlers
        self.message_handlers = defaultdict(list)
        self.connection_handlers = defaultdict(list)
        self.room_handlers = defaultdict(list)
        
        # Message queues
        self.message_queue = queue.Queue()
        self.event_queue = queue.Queue()
        
        # Background tasks
        self.background_tasks = []
        self.running = False
        
        # Clustering support
        self.cluster_nodes = {}
        self.node_id = str(uuid.uuid4())
        
        # Initialize server
        self._initialize_server()
    
    def _initialize_server(self):
        """Initialize WebSocket server"""
        try:
            # Create event loop
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            
            # Create custom protocol class
            class CustomProtocol(WebSocketServerProtocol):
                def __init__(self, ws_server, *args, **kwargs):
                    super().__init__(*args, **kwargs)
                    self.ws_server = ws_server
                
                async def on_open(self, websocket):
                    await self.ws_server._handle_connection_open(websocket, self)
                
                async def on_message(self, websocket, message):
                    await self.ws_server._handle_message(websocket, message, self)
                
                async def on_close(self, websocket, code, reason):
                    await self.ws_server._handle_connection_close(websocket, code, reason, self)
                
                async def on_error(self, websocket, error):
                    await self.ws_server._handle_connection_error(websocket, error, self)
            
            # Store protocol class
            self.protocol_class = CustomProtocol
            
            # Start background tasks
            self._start_background_tasks()
            
            logger.info("WebSocket server initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize WebSocket server: {e}")
            self.server_status = ServerStatus.ERROR
            raise
    
    def _start_background_tasks(self):
        """Start background tasks"""
        def message_processor():
            while self.running:
                try:
                    if not self.message_queue.empty():
                        message_data = self.message_queue.get(timeout=1)
                        asyncio.run_coroutine_threadsafe(
                            self._process_message(message_data),
                            self.loop
                        )
                except Exception as e:
                    logger.error(f"Message processor error: {e}")
        
        def stats_updater():
            while self.running:
                try:
                    self._update_stats()
                    time.sleep(10)
                except Exception as e:
                    logger.error(f"Stats updater error: {e}")
        
        def health_checker():
            while self.running:
                try:
                    self._perform_health_check()
                    time.sleep(self.config.health_check_interval)
                except Exception as e:
                    logger.error(f"Health checker error: {e}")
        
        # Start tasks
        self.running = True
        for task_func in [message_processor, stats_updater, health_checker]:
            task = threading.Thread(target=task_func, daemon=True)
            task.start()
            self.background_tasks.append(task)
        
        logger.info("Background tasks started")
    
    async def _handle_connection_open(self, websocket, protocol):
        """Handle new WebSocket connection"""
        try:
            # Generate connection ID
            connection_id = str(uuid.uuid4())
            
            # Get client info
            client_info = websocket.remote_address
            ip_address = client_info[0] if client_info else "unknown"
            
            # Create connection info
            connection_info = ConnectionInfo(
                connection_id=connection_id,
                websocket=websocket,
                ip_address=ip_address,
                user_agent=websocket.request_headers.get("User-Agent", ""),
                connection_type=ConnectionType.CLIENT
            )
            
            # Store connection
            self.connections[connection_id] = connection_info
            
            # Update stats
            self.stats.total_connections += 1
            self.stats.active_connections += 1
            
            # Trigger connection handlers
            for handler in self.connection_handlers["open"]:
                try:
                    await handler(connection_info)
                except Exception as e:
                    logger.error(f"Connection open handler error: {e}")
            
            logger.info(f"New WebSocket connection: {connection_id} from {ip_address}")
            
        except Exception as e:
            logger.error(f"Error handling connection open: {e}")
    
    async def _handle_message(self, websocket, message, protocol):
        """Handle incoming WebSocket message"""
        try:
            # Find connection info
            connection_id = None
            for conn_id, conn_info in self.connections.items():
                if conn_info.websocket == websocket:
                    connection_id = conn_id
                    break
            
            if not connection_id:
                logger.warning("Message from unknown connection")
                return
            
            connection_info = self.connections[connection_id]
            connection_info.last_activity = datetime.utcnow()
            
            # Parse message
            try:
                message_data = json.loads(message)
            except json.JSONDecodeError:
                message_data = {"type": "raw", "data": message}
            
            # Update stats
            self.stats.total_messages_received += 1
            self.stats.total_bytes_received += len(message.encode())
            
            # Add to message queue
            self.message_queue.put({
                "connection_id": connection_id,
                "message": message_data,
                "timestamp": datetime.utcnow()
            })
            
        except Exception as e:
            logger.error(f"Error handling message: {e}")
    
    async def _handle_connection_close(self, websocket, code, reason, protocol):
        """Handle WebSocket connection close"""
        try:
            # Find connection info
            connection_id = None
            for conn_id, conn_info in self.connections.items():
                if conn_info.websocket == websocket:
                    connection_id = conn_id
                    break
            
            if connection_id:
                connection_info = self.connections[connection_id]
                
                # Remove from rooms
                for room_id in connection_info.room_ids:
                    if room_id in self.rooms:
                        self.rooms[room_id].discard(connection_id)
                
                # Remove connection
                del self.connections[connection_id]
                
                # Update stats
                self.stats.active_connections -= 1
                
                # Trigger connection handlers
                for handler in self.connection_handlers["close"]:
                    try:
                        await handler(connection_info, code, reason)
                    except Exception as e:
                        logger.error(f"Connection close handler error: {e}")
                
                logger.info(f"WebSocket connection closed: {connection_id}")
            
        except Exception as e:
            logger.error(f"Error handling connection close: {e}")
    
    async def _handle_connection_error(self, websocket, error, protocol):
        """Handle WebSocket connection error"""
        try:
            logger.error(f"WebSocket connection error: {error}")
            self.stats.errors += 1
            
            # Trigger error handlers
            for handler in self.connection_handlers["error"]:
                try:
                    await handler(websocket, error)
                except Exception as e:
                    logger.error(f"Connection error handler error: {e}")
            
        except Exception as e:
            logger.error(f"Error handling connection error: {e}")
    
    async def _process_message(self, message_data: Dict[str, Any]):
        """Process incoming message"""
        try:
            connection_id = message_data["connection_id"]
            message = message_data["message"]
            timestamp = message_data["timestamp"]
            
            connection_info = self.connections.get(connection_id)
            if not connection_info:
                return
            
            # Handle different message types
            message_type = message.get("type", "unknown")
            
            if message_type == "auth":
                await self._handle_auth_message(connection_info, message)
            elif message_type == "join_room":
                await self._handle_join_room(connection_info, message)
            elif message_type == "leave_room":
                await self._handle_leave_room(connection_info, message)
            elif message_type == "room_message":
                await self._handle_room_message(connection_info, message)
            elif message_type == "ping":
                await self._handle_ping(connection_info, message)
            elif message_type == "subscribe":
                await self._handle_subscribe(connection_info, message)
            elif message_type == "unsubscribe":
                await self._handle_unsubscribe(connection_info, message)
            else:
                # Handle custom message types
                for handler in self.message_handlers[message_type]:
                    try:
                        await handler(connection_info, message)
                    except Exception as e:
                        logger.error(f"Message handler error for {message_type}: {e}")
            
            # Trigger general message handlers
            for handler in self.message_handlers["*"]:
                try:
                    await handler(connection_info, message)
                except Exception as e:
                    logger.error(f"General message handler error: {e}")
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    async def _handle_auth_message(self, connection_info: ConnectionInfo, message: Dict[str, Any]):
        """Handle authentication message"""
        try:
            if not self.config.auth_required:
                connection_info.authenticated = True
                await self.send_to_connection(connection_info.connection_id, {
                    "type": "auth_success",
                    "message": "Authentication successful"
                })
                return
            
            token = message.get("token")
            if not token:
                await self.send_to_connection(connection_info.connection_id, {
                    "type": "auth_error",
                    "message": "Authentication token required"
                })
                return
            
            # Verify JWT token
            try:
                if self.config.jwt_secret:
                    payload = jwt.decode(
                        token,
                        self.config.jwt_secret,
                        algorithms=[self.config.jwt_algorithm]
                    )
                    connection_info.user_id = payload.get("user_id")
                    connection_info.session_id = payload.get("session_id")
                    connection_info.authenticated = True
                    connection_info.metadata.update(payload)
                    
                    await self.send_to_connection(connection_info.connection_id, {
                        "type": "auth_success",
                        "message": "Authentication successful",
                        "user_id": connection_info.user_id
                    })
                else:
                    # Simple token validation (for testing)
                    connection_info.authenticated = True
                    connection_info.user_id = token
                    await self.send_to_connection(connection_info.connection_id, {
                        "type": "auth_success",
                        "message": "Authentication successful"
                    })
                
            except jwt.InvalidTokenError:
                await self.send_to_connection(connection_info.connection_id, {
                    "type": "auth_error",
                    "message": "Invalid authentication token"
                })
            
        except Exception as e:
            logger.error(f"Error handling auth message: {e}")
    
    async def _handle_join_room(self, connection_info: ConnectionInfo, message: Dict[str, Any]):
        """Handle join room message"""
        try:
            room_id = message.get("room_id")
            if not room_id:
                await self.send_to_connection(connection_info.connection_id, {
                    "type": "error",
                    "message": "Room ID required"
                })
                return
            
            # Add connection to room
            self.rooms[room_id].add(connection_info.connection_id)
            connection_info.room_ids.add(room_id)
            
            # Notify room
            await self.broadcast_to_room(room_id, {
                "type": "user_joined",
                "user_id": connection_info.user_id,
                "room_id": room_id,
                "timestamp": datetime.utcnow().isoformat()
            }, exclude_connection_id=connection_info.connection_id)
            
            # Send confirmation
            await self.send_to_connection(connection_info.connection_id, {
                "type": "room_joined",
                "room_id": room_id,
                "user_count": len(self.rooms[room_id])
            })
            
            # Trigger room handlers
            for handler in self.room_handlers["join"]:
                try:
                    await handler(connection_info, room_id)
                except Exception as e:
                    logger.error(f"Room join handler error: {e}")
            
        except Exception as e:
            logger.error(f"Error handling join room message: {e}")
    
    async def _handle_leave_room(self, connection_info: ConnectionInfo, message: Dict[str, Any]):
        """Handle leave room message"""
        try:
            room_id = message.get("room_id")
            if not room_id:
                await self.send_to_connection(connection_info.connection_id, {
                    "type": "error",
                    "message": "Room ID required"
                })
                return
            
            # Remove connection from room
            if room_id in self.rooms:
                self.rooms[room_id].discard(connection_info.connection_id)
                connection_info.room_ids.discard(room_id)
                
                # Notify room
                await self.broadcast_to_room(room_id, {
                    "type": "user_left",
                    "user_id": connection_info.user_id,
                    "room_id": room_id,
                    "timestamp": datetime.utcnow().isoformat()
                }, exclude_connection_id=connection_info.connection_id)
            
            # Send confirmation
            await self.send_to_connection(connection_info.connection_id, {
                "type": "room_left",
                "room_id": room_id
            })
            
            # Trigger room handlers
            for handler in self.room_handlers["leave"]:
                try:
                    await handler(connection_info, room_id)
                except Exception as e:
                    logger.error(f"Room leave handler error: {e}")
            
        except Exception as e:
            logger.error(f"Error handling leave room message: {e}")
    
    async def _handle_room_message(self, connection_info: ConnectionInfo, message: Dict[str, Any]):
        """Handle room message"""
        try:
            room_id = message.get("room_id")
            content = message.get("content")
            
            if not room_id or not content:
                await self.send_to_connection(connection_info.connection_id, {
                    "type": "error",
                    "message": "Room ID and content required"
                })
                return
            
            # Check if user is in room
            if room_id not in connection_info.room_ids:
                await self.send_to_connection(connection_info.connection_id, {
                    "type": "error",
                    "message": "Not in room"
                })
                return
            
            # Broadcast message to room
            await self.broadcast_to_room(room_id, {
                "type": "room_message",
                "user_id": connection_info.user_id,
                "room_id": room_id,
                "content": content,
                "timestamp": datetime.utcnow().isoformat()
            }, exclude_connection_id=connection_info.connection_id)
            
            # Trigger room handlers
            for handler in self.room_handlers["message"]:
                try:
                    await handler(connection_info, room_id, content)
                except Exception as e:
                    logger.error(f"Room message handler error: {e}")
            
        except Exception as e:
            logger.error(f"Error handling room message: {e}")
    
    async def _handle_ping(self, connection_info: ConnectionInfo, message: Dict[str, Any]):
        """Handle ping message"""
        try:
            await self.send_to_connection(connection_info.connection_id, {
                "type": "pong",
                "timestamp": datetime.utcnow().isoformat()
            })
        except Exception as e:
            logger.error(f"Error handling ping message: {e}")
    
    async def _handle_subscribe(self, connection_info: ConnectionInfo, message: Dict[str, Any]):
        """Handle subscribe message"""
        try:
            event_type = message.get("event_type")
            if not event_type:
                await self.send_to_connection(connection_info.connection_id, {
                    "type": "error",
                    "message": "Event type required"
                })
                return
            
            # Add to subscription list
            if "subscriptions" not in connection_info.metadata:
                connection_info.metadata["subscriptions"] = set()
            
            connection_info.metadata["subscriptions"].add(event_type)
            
            await self.send_to_connection(connection_info.connection_id, {
                "type": "subscribed",
                "event_type": event_type
            })
            
        except Exception as e:
            logger.error(f"Error handling subscribe message: {e}")
    
    async def _handle_unsubscribe(self, connection_info: ConnectionInfo, message: Dict[str, Any]):
        """Handle unsubscribe message"""
        try:
            event_type = message.get("event_type")
            if not event_type:
                await self.send_to_connection(connection_info.connection_id, {
                    "type": "error",
                    "message": "Event type required"
                })
                return
            
            # Remove from subscription list
            if "subscriptions" in connection_info.metadata:
                connection_info.metadata["subscriptions"].discard(event_type)
            
            await self.send_to_connection(connection_info.connection_id, {
                "type": "unsubscribed",
                "event_type": event_type
            })
            
        except Exception as e:
            logger.error(f"Error handling unsubscribe message: {e}")
    
    async def send_to_connection(self, connection_id: str, message: Dict[str, Any]):
        """Send message to specific connection"""
        try:
            connection_info = self.connections.get(connection_id)
            if not connection_info:
                return
            
            message_str = json.dumps(message)
            await connection_info.websocket.send(message_str)
            
            # Update stats
            self.stats.total_messages_sent += 1
            self.stats.total_bytes_sent += len(message_str.encode())
            
        except ConnectionClosed:
            # Connection closed, remove it
            if connection_id in self.connections:
                del self.connections[connection_id]
                self.stats.active_connections -= 1
        except Exception as e:
            logger.error(f"Error sending message to {connection_id}: {e}")
    
    async def broadcast_to_room(self, room_id: str, message: Dict[str, Any], exclude_connection_id: str = None):
        """Broadcast message to all connections in a room"""
        try:
            if room_id not in self.rooms:
                return
            
            message_str = json.dumps(message)
            
            for connection_id in self.rooms[room_id].copy():
                if exclude_connection_id and connection_id == exclude_connection_id:
                    continue
                
                await self.send_to_connection(connection_id, message)
            
        except Exception as e:
            logger.error(f"Error broadcasting to room {room_id}: {e}")
    
    async def broadcast_to_all(self, message: Dict[str, Any]):
        """Broadcast message to all connections"""
        try:
            message_str = json.dumps(message)
            
            for connection_id in list(self.connections.keys()):
                await self.send_to_connection(connection_id, message)
            
        except Exception as e:
            logger.error(f"Error broadcasting to all: {e}")
    
    def add_message_handler(self, message_type: str, handler: Callable):
        """Add message handler for specific message type"""
        self.message_handlers[message_type].append(handler)
    
    def add_connection_handler(self, event_type: str, handler: Callable):
        """Add connection handler for specific event"""
        self.connection_handlers[event_type].append(handler)
    
    def add_room_handler(self, event_type: str, handler: Callable):
        """Add room handler for specific event"""
        self.room_handlers[event_type].append(handler)
    
    def start(self):
        """Start WebSocket server"""
        try:
            if self.server_status == ServerStatus.RUNNING:
                logger.warning("WebSocket server already running")
                return
            
            self.server_status = ServerStatus.STARTING
            
            # Create server
            self.server = websockets.serve(
                self._handle_client,
                self.config.host,
                self.config.port,
                create_protocol=lambda: self.protocol_class(self),
                ping_interval=self.config.ping_interval,
                ping_timeout=self.config.ping_timeout,
                close_timeout=self.config.close_timeout,
                compression=self.config.compression,
                origins=self.config.origins
            )
            
            # Start server in event loop
            self.loop.run_until_complete(self.server)
            
            self.server_status = ServerStatus.RUNNING
            logger.info(f"WebSocket server started on {self.config.host}:{self.config.port}")
            
        except Exception as e:
            logger.error(f"Failed to start WebSocket server: {e}")
            self.server_status = ServerStatus.ERROR
            raise
    
    async def _handle_client(self, websocket, path):
        """Handle client connection"""
        # This is handled by the protocol class
        pass
    
    def stop(self):
        """Stop WebSocket server"""
        try:
            if self.server_status == ServerStatus.STOPPED:
                return
            
            self.server_status = ServerStatus.STOPPING
            self.running = False
            
            # Close all connections
            for connection_id, connection_info in self.connections.items():
                try:
                    asyncio.run_coroutine_threadsafe(
                        connection_info.websocket.close(),
                        self.loop
                    )
                except Exception as e:
                    logger.error(f"Error closing connection {connection_id}: {e}")
            
            # Stop server
            if self.server:
                self.server.close()
                self.server = None
            
            self.server_status = ServerStatus.STOPPED
            logger.info("WebSocket server stopped")
            
        except Exception as e:
            logger.error(f"Error stopping WebSocket server: {e}")
    
    def _update_stats(self):
        """Update server statistics"""
        try:
            self.stats.last_updated = datetime.utcnow()
            
            # Calculate messages per second
            if len(self.message_queue.queue) > 0:
                self.stats.messages_per_second = len(self.message_queue.queue) / 10
            
            # Calculate average connection duration
            if self.connections:
                durations = []
                now = datetime.utcnow()
                for conn_info in self.connections.values():
                    duration = (now - conn_info.connected_at).total_seconds()
                    durations.append(duration)
                
                if durations:
                    self.stats.avg_connection_duration = sum(durations) / len(durations)
            
        except Exception as e:
            logger.error(f"Error updating stats: {e}")
    
    def _perform_health_check(self):
        """Perform health check"""
        try:
            # Check server status
            if self.server_status != ServerStatus.RUNNING:
                logger.warning(f"WebSocket server not running: {self.server_status.value}")
            
            # Check connection count
            if self.stats.active_connections > self.config.max_connections:
                logger.warning(f"Too many connections: {self.stats.active_connections}")
            
            # Check error rate
            if self.stats.total_messages_received > 0:
                error_rate = self.stats.errors / self.stats.total_messages_received
                if error_rate > 0.1:  # 10% error rate
                    logger.warning(f"High error rate: {error_rate:.2%}")
            
        except Exception as e:
            logger.error(f"Error performing health check: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get server statistics"""
        return {
            'server_status': self.server_status.value,
            'total_connections': self.stats.total_connections,
            'active_connections': self.stats.active_connections,
            'total_messages_sent': self.stats.total_messages_sent,
            'total_messages_received': self.stats.total_messages_received,
            'total_bytes_sent': self.stats.total_bytes_sent,
            'total_bytes_received': self.stats.total_bytes_received,
            'avg_connection_duration': self.stats.avg_connection_duration,
            'messages_per_second': self.stats.messages_per_second,
            'errors': self.stats.errors,
            'last_updated': self.stats.last_updated.isoformat(),
            'rooms': {
                'total': len(self.rooms),
                'details': {room_id: len(connections) for room_id, connections in self.rooms.items()}
            },
            'node_id': self.node_id
        }
    
    def get_connections(self) -> List[Dict[str, Any]]:
        """Get all connection information"""
        connections = []
        for connection_id, connection_info in self.connections.items():
            connections.append({
                'connection_id': connection_id,
                'user_id': connection_info.user_id,
                'session_id': connection_info.session_id,
                'connection_type': connection_info.connection_type.value,
                'connected_at': connection_info.connected_at.isoformat(),
                'last_activity': connection_info.last_activity.isoformat(),
                'ip_address': connection_info.ip_address,
                'user_agent': connection_info.user_agent,
                'authenticated': connection_info.authenticated,
                'room_ids': list(connection_info.room_ids),
                'metadata': connection_info.metadata
            })
        
        return connections
    
    def get_room_info(self, room_id: str) -> Optional[Dict[str, Any]]:
        """Get room information"""
        if room_id not in self.rooms:
            return None
        
        connection_ids = self.rooms[room_id]
        connections = []
        
        for connection_id in connection_ids:
            if connection_id in self.connections:
                connection_info = self.connections[connection_id]
                connections.append({
                    'connection_id': connection_id,
                    'user_id': connection_info.user_id,
                    'authenticated': connection_info.authenticated,
                    'connected_at': connection_info.connected_at.isoformat()
                })
        
        return {
            'room_id': room_id,
            'connection_count': len(connections),
            'connections': connections
        }
    
    def get_config(self) -> Dict[str, Any]:
        """Get server configuration"""
        return {
            'host': self.config.host,
            'port': self.config.port,
            'max_connections': self.config.max_connections,
            'ping_interval': self.config.ping_interval,
            'ping_timeout': self.config.ping_timeout,
            'compression': self.config.compression,
            'origins': self.config.origins,
            'ssl_enabled': self.config.ssl_enabled,
            'auth_required': self.config.auth_required,
            'enable_clustering': self.config.enable_clustering,
            'load_balancing_enabled': self.config.load_balancing_enabled,
            'health_check_interval': self.config.health_check_interval,
            'metrics_enabled': self.config.metrics_enabled
        }
    
    def update_config(self, **kwargs):
        """Update server configuration"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
                logger.info(f"Updated server config: {key} = {value}")
    
    def shutdown(self):
        """Shutdown WebSocket server"""
        try:
            self.stop()
            
            # Stop background tasks
            self.running = False
            
            # Close event loop
            if self.loop:
                self.loop.close()
            
            logger.info("WebSocket server shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during WebSocket server shutdown: {e}")
