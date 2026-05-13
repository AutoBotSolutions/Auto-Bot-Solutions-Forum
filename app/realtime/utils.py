"""
Real-time Utilities

Utility functions and helpers for WebSocket session management, event processing,
streaming data handling, and real-time analytics.
"""

import json
import time
import threading
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Callable, Union
from collections import deque, defaultdict
from dataclasses import dataclass
from enum import Enum
import uuid

from app.realtime.service import get_realtime_service


class EventType(Enum):
    """Real-time event types"""
    MESSAGE = "message"
    NOTIFICATION = "notification"
    SYSTEM = "system"
    USER_ACTION = "user_action"
    STATUS_UPDATE = "status_update"
    ERROR = "error"
    WARNING = "warning"


class StreamType(Enum):
    """Stream data types"""
    USER_ACTIVITY = "user_activity"
    SYSTEM_METRICS = "system_metrics"
    CHAT = "chat"
    NOTIFICATIONS = "notifications"
    PERFORMANCE = "performance"
    ANALYTICS = "analytics"


class SessionStatus(Enum):
    """WebSocket session status"""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"


@dataclass
class WebSocketMessage:
    """WebSocket message structure"""
    event_type: str
    event_category: str
    data: Dict[str, Any]
    target_room: Optional[str] = None
    target_user: Optional[int] = None
    severity: str = "info"
    timestamp: datetime = None
    message_id: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        if self.message_id is None:
            self.message_id = str(uuid.uuid4())


class EventQueue:
    """Thread-safe event queue for real-time processing"""
    
    def __init__(self, max_size=1000):
        self.queue = deque(maxlen=max_size)
        self.lock = threading.Lock()
        self.size = 0
    
    def put(self, item):
        """Add item to queue"""
        with self.lock:
            self.queue.append(item)
            self.size = len(self.queue)
    
    def get(self):
        """Get item from queue"""
        with self.lock:
            if self.queue:
                item = self.queue.popleft()
                self.size = len(self.queue)
                return item
            return None
    
    def get_batch(self, batch_size=10):
        """Get batch of items from queue"""
        items = []
        with self.lock:
            for _ in range(min(batch_size, len(self.queue))):
                if self.queue:
                    items.append(self.queue.popleft())
            self.size = len(self.queue)
        return items
    
    def is_empty(self):
        """Check if queue is empty"""
        with self.lock:
            return len(self.queue) == 0
    
    def get_size(self):
        """Get queue size"""
        return self.size


class RoomManager:
    """Manages WebSocket rooms and user subscriptions"""
    
    def __init__(self):
        self.rooms = defaultdict(set)  # room -> set of session_ids
        self.user_rooms = defaultdict(set)  # user_id -> set of rooms
        self.session_rooms = defaultdict(set)  # session_id -> set of rooms
        self.lock = threading.Lock()
    
    def join_room(self, session_id: str, room: str, user_id: Optional[int] = None):
        """Add session to room"""
        with self.lock:
            self.rooms[room].add(session_id)
            self.session_rooms[session_id].add(room)
            if user_id:
                self.user_rooms[user_id].add(room)
    
    def leave_room(self, session_id: str, room: str, user_id: Optional[int] = None):
        """Remove session from room"""
        with self.lock:
            self.rooms[room].discard(session_id)
            self.session_rooms[session_id].discard(room)
            if user_id:
                self.user_rooms[user_id].discard(room)
            
            # Clean up empty rooms
            if not self.rooms[room]:
                del self.rooms[room]
    
    def leave_all_rooms(self, session_id: str, user_id: Optional[int] = None):
        """Remove session from all rooms"""
        with self.lock:
            rooms = list(self.session_rooms[session_id])
            for room in rooms:
                self.leave_room(session_id, room, user_id)
    
    def get_room_sessions(self, room: str) -> set:
        """Get all sessions in a room"""
        with self.lock:
            return self.rooms[room].copy()
    
    def get_user_rooms(self, user_id: int) -> set:
        """Get all rooms for a user"""
        with self.lock:
            return self.user_rooms[user_id].copy()
    
    def get_session_rooms(self, session_id: str) -> set:
        """Get all rooms for a session"""
        with self.lock:
            return self.session_rooms[session_id].copy()
    
    def get_room_stats(self) -> Dict[str, Any]:
        """Get room statistics"""
        with self.lock:
            return {
                'total_rooms': len(self.rooms),
                'total_sessions': sum(len(sessions) for sessions in self.rooms.values()),
                'rooms': {
                    room: len(sessions) for room, sessions in self.rooms.items()
                }
            }


class ConnectionPool:
    """Manages WebSocket connection pooling and load balancing"""
    
    def __init__(self, max_connections=1000):
        self.connections = {}  # session_id -> connection_info
        self.user_connections = defaultdict(set)  # user_id -> set of session_ids
        self.lock = threading.Lock()
        self.max_connections = max_connections
    
    def add_connection(self, session_id: str, user_id: Optional[int] = None,
                      ip_address: Optional[str] = None, user_agent: Optional[str] = None):
        """Add connection to pool"""
        with self.lock:
            if len(self.connections) >= self.max_connections:
                # Remove oldest inactive connection
                oldest_session = min(
                    self.connections.items(),
                    key=lambda x: x[1].get('last_activity', datetime.min)
                )[0]
                self.remove_connection(oldest_session)
            
            self.connections[session_id] = {
                'user_id': user_id,
                'ip_address': ip_address,
                'user_agent': user_agent,
                'connected_at': datetime.utcnow(),
                'last_activity': datetime.utcnow(),
                'message_count': 0,
                'bytes_sent': 0,
                'bytes_received': 0
            }
            
            if user_id:
                self.user_connections[user_id].add(session_id)
    
    def remove_connection(self, session_id: str):
        """Remove connection from pool"""
        with self.lock:
            if session_id in self.connections:
                user_id = self.connections[session_id].get('user_id')
                del self.connections[session_id]
                
                if user_id and user_id in self.user_connections:
                    self.user_connections[user_id].discard(session_id)
                    if not self.user_connections[user_id]:
                        del self.user_connections[user_id]
    
    def update_activity(self, session_id: str, message_sent=False, message_received=False,
                      bytes_sent=0, bytes_received=0):
        """Update connection activity"""
        with self.lock:
            if session_id in self.connections:
                self.connections[session_id]['last_activity'] = datetime.utcnow()
                if message_sent:
                    self.connections[session_id]['message_count'] += 1
                    self.connections[session_id]['bytes_sent'] += bytes_sent
                if message_received:
                    self.connections[session_id]['bytes_received'] += bytes_received
    
    def get_connection(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get connection info"""
        with self.lock:
            return self.connections.get(session_id)
    
    def get_user_connections(self, user_id: int) -> set:
        """Get all connections for a user"""
        with self.lock:
            return self.user_connections[user_id].copy()
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics"""
        with self.lock:
            total_connections = len(self.connections)
            unique_users = len(self.user_connections)
            
            # Calculate activity metrics
            now = datetime.utcnow()
            active_connections = sum(
                1 for conn in self.connections.values()
                if (now - conn['last_activity']).total_seconds() < 300  # 5 minutes
            )
            
            total_messages = sum(conn['message_count'] for conn in self.connections.values())
            total_bytes_sent = sum(conn['bytes_sent'] for conn in self.connections.values())
            total_bytes_received = sum(conn['bytes_received'] for conn in self.connections.values())
            
            return {
                'total_connections': total_connections,
                'unique_users': unique_users,
                'active_connections': active_connections,
                'total_messages': total_messages,
                'total_bytes_sent': total_bytes_sent,
                'total_bytes_received': total_bytes_received,
                'max_connections': self.max_connections
            }


class StreamProcessor:
    """Processes streaming data in real-time"""
    
    def __init__(self):
        self.processors = {}  # stream_type -> processor_function
        self.stream_queue = EventQueue(max_size=10000)
        self.processing_thread = None
        self.running = False
    
    def register_processor(self, stream_type: str, processor: Callable):
        """Register a processor for a stream type"""
        self.processors[stream_type] = processor
    
    def add_stream_data(self, stream_data: Dict[str, Any]):
        """Add stream data to processing queue"""
        self.stream_queue.put(stream_data)
    
    def start_processing(self):
        """Start the processing thread"""
        if not self.running:
            self.running = True
            self.processing_thread = threading.Thread(target=self._process_loop)
            self.processing_thread.daemon = True
            self.processing_thread.start()
    
    def stop_processing(self):
        """Stop the processing thread"""
        self.running = False
        if self.processing_thread:
            self.processing_thread.join()
    
    def _process_loop(self):
        """Main processing loop"""
        while self.running:
            try:
                # Get batch of stream data
                batch = self.stream_queue.get_batch(batch_size=10)
                if not batch:
                    time.sleep(0.1)  # Small delay when queue is empty
                    continue
                
                # Process each stream data item
                for stream_data in batch:
                    self._process_stream_item(stream_data)
                    
            except Exception as e:
                print(f"Error in processing loop: {e}")
                time.sleep(1)  # Delay on error
    
    def _process_stream_item(self, stream_data: Dict[str, Any]):
        """Process individual stream data item"""
        try:
            stream_type = stream_data.get('stream_type')
            if stream_type and stream_type in self.processors:
                processor = self.processors[stream_type]
                processor(stream_data)
            else:
                print(f"No processor registered for stream type: {stream_type}")
                
        except Exception as e:
            print(f"Error processing stream item: {e}")


class AnalyticsCalculator:
    """Calculates real-time analytics metrics"""
    
    def __init__(self):
        self.metrics_cache = {}
        self.cache_ttl = 60  # 60 seconds
        self.lock = threading.Lock()
    
    def calculate_active_users(self, time_window_minutes=5) -> int:
        """Calculate number of active users"""
        cache_key = f"active_users_{time_window_minutes}"
        
        with self.lock:
            if cache_key in self.metrics_cache:
                cached_data = self.metrics_cache[cache_key]
                if (datetime.utcnow() - cached_data['timestamp']).total_seconds() < self.cache_ttl:
                    return cached_data['value']
        
        # Calculate from WebSocket sessions
        from app.realtime.models import WebSocketSession
        from datetime import datetime, timedelta
        
        start_time = datetime.utcnow() - timedelta(minutes=time_window_minutes)
        active_users = WebSocketSession.query.filter(
            WebSocketSession.status == 'connected',
            WebSocketSession.last_activity >= start_time
        ).distinct(WebSocketSession.user_id).count()
        
        # Cache the result
        with self.lock:
            self.metrics_cache[cache_key] = {
                'value': active_users,
                'timestamp': datetime.utcnow()
            }
        
        return active_users
    
    def calculate_message_rate(self, time_window_minutes=5) -> float:
        """Calculate message rate per minute"""
        cache_key = f"message_rate_{time_window_minutes}"
        
        with self.lock:
            if cache_key in self.metrics_cache:
                cached_data = self.metrics_cache[cache_key]
                if (datetime.utcnow() - cached_data['timestamp']).total_seconds() < self.cache_ttl:
                    return cached_data['value']
        
        # Calculate from WebSocket sessions
        from app.realtime.models import WebSocketSession
        from datetime import datetime, timedelta
        from sqlalchemy import func
        
        start_time = datetime.utcnow() - timedelta(minutes=time_window_minutes)
        total_messages = WebSocketSession.query.filter(
            WebSocketSession.last_activity >= start_time
        ).with_entities(
            func.sum(WebSocketSession.messages_sent + WebSocketSession.messages_received)
        ).scalar() or 0
        
        message_rate = total_messages / time_window_minutes
        
        # Cache the result
        with self.lock:
            self.metrics_cache[cache_key] = {
                'value': message_rate,
                'timestamp': datetime.utcnow()
            }
        
        return message_rate
    
    def calculate_error_rate(self, time_window_minutes=5) -> float:
        """Calculate error rate percentage"""
        cache_key = f"error_rate_{time_window_minutes}"
        
        with self.lock:
            if cache_key in self.metrics_cache:
                cached_data = self.metrics_cache[cache_key]
                if (datetime.utcnow() - cached_data['timestamp']).total_seconds() < self.cache_ttl:
                    return cached_data['value']
        
        # Calculate from real-time events
        from app.realtime.models import RealTimeEvent
        from datetime import datetime, timedelta
        from sqlalchemy import func
        
        start_time = datetime.utcnow() - timedelta(minutes=time_window_minutes)
        
        total_events = RealTimeEvent.query.filter(
            RealTimeEvent.event_timestamp >= start_time
        ).count()
        
        error_events = RealTimeEvent.query.filter(
            RealTimeEvent.event_timestamp >= start_time,
            RealTimeEvent.severity == 'error'
        ).count()
        
        error_rate = (error_events / max(total_events, 1)) * 100
        
        # Cache the result
        with self.lock:
            self.metrics_cache[cache_key] = {
                'value': error_rate,
                'timestamp': datetime.utcnow()
            }
        
        return error_rate
    
    def calculate_system_health(self) -> Dict[str, Any]:
        """Calculate overall system health metrics"""
        return {
            'active_users': self.calculate_active_users(),
            'message_rate': self.calculate_message_rate(),
            'error_rate': self.calculate_error_rate(),
            'timestamp': datetime.utcnow().isoformat()
        }


class EventBroadcaster:
    """Broadcasts events to multiple targets"""
    
    def __init__(self):
        self.subscribers = defaultdict(set)  # event_type -> set of callbacks
        self.lock = threading.Lock()
    
    def subscribe(self, event_type: str, callback: Callable):
        """Subscribe to event type"""
        with self.lock:
            self.subscribers[event_type].add(callback)
    
    def unsubscribe(self, event_type: str, callback: Callable):
        """Unsubscribe from event type"""
        with self.lock:
            self.subscribers[event_type].discard(callback)
    
    def broadcast(self, event: Dict[str, Any]):
        """Broadcast event to all subscribers"""
        event_type = event.get('event_type')
        if not event_type:
            return
        
        callbacks = []
        with self.lock:
            if event_type in self.subscribers:
                callbacks = list(self.subscribers[event_type])
        
        # Call all callbacks
        for callback in callbacks:
            try:
                callback(event)
            except Exception as e:
                print(f"Error in event callback: {e}")


class WebSocketUtils:
    """WebSocket utility functions"""
    
    @staticmethod
    def parse_websocket_headers(headers: Dict[str, str]) -> Dict[str, Any]:
        """Parse WebSocket headers for security and metadata"""
        parsed = {
            'ip_address': headers.get('X-Forwarded-For', headers.get('X-Real-IP', 'Unknown')),
            'user_agent': headers.get('User-Agent', 'Unknown'),
            'origin': headers.get('Origin', 'Unknown'),
            'protocols': headers.get('Sec-WebSocket-Protocol', '').split(','),
            'version': headers.get('Sec-WebSocket-Version', 'Unknown')
        }
        
        # Parse user agent for device info
        user_agent = parsed['user_agent']
        if user_agent != 'Unknown':
            parsed['device_type'] = WebSocketUtils.detect_device_type(user_agent)
            parsed['browser'] = WebSocketUtils.detect_browser(user_agent)
            parsed['platform'] = WebSocketUtils.detect_platform(user_agent)
        
        return parsed
    
    @staticmethod
    def detect_device_type(user_agent: str) -> str:
        """Detect device type from user agent"""
        user_agent_lower = user_agent.lower()
        
        if 'mobile' in user_agent_lower or 'android' in user_agent_lower or 'iphone' in user_agent_lower:
            return 'mobile'
        elif 'tablet' in user_agent_lower or 'ipad' in user_agent_lower:
            return 'tablet'
        elif 'bot' in user_agent_lower or 'crawler' in user_agent_lower or 'spider' in user_agent_lower:
            return 'bot'
        else:
            return 'desktop'
    
    @staticmethod
    def detect_browser(user_agent: str) -> str:
        """Detect browser from user agent"""
        user_agent_lower = user_agent.lower()
        
        browsers = {
            'chrome': 'chrome' in user_agent_lower,
            'firefox': 'firefox' in user_agent_lower,
            'safari': 'safari' in user_agent_lower and 'chrome' not in user_agent_lower,
            'edge': 'edge' in user_agent_lower or 'edg' in user_agent_lower,
            'opera': 'opera' in user_agent_lower,
            'ie': 'msie' in user_agent_lower or 'trident' in user_agent_lower
        }
        
        for browser, detected in browsers.items():
            if detected:
                return browser
        
        return 'unknown'
    
    @staticmethod
    def detect_platform(user_agent: str) -> str:
        """Detect platform from user agent"""
        user_agent_lower = user_agent.lower()
        
        if 'windows' in user_agent_lower:
            return 'windows'
        elif 'mac' in user_agent_lower or 'os x' in user_agent_lower:
            return 'mac'
        elif 'linux' in user_agent_lower:
            return 'linux'
        elif 'android' in user_agent_lower:
            return 'android'
        elif 'ios' in user_agent_lower or 'iphone' in user_agent_lower or 'ipad' in user_agent_lower:
            return 'ios'
        else:
            return 'unknown'
    
    @staticmethod
    def validate_websocket_message(message: Dict[str, Any]) -> bool:
        """Validate WebSocket message format"""
        required_fields = ['event_type', 'event_category']
        
        if not isinstance(message, dict):
            return False
        
        for field in required_fields:
            if field not in message:
                return False
        
        # Validate event type
        valid_event_types = ['message', 'notification', 'system', 'user_action', 'status_update']
        if message['event_type'] not in valid_event_types:
            return False
        
        # Validate event category
        valid_event_categories = ['chat', 'alert', 'update', 'status', 'user']
        if message['event_category'] not in valid_event_categories:
            return False
        
        return True
    
    @staticmethod
    def sanitize_message_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize message data for security"""
        if not isinstance(data, dict):
            return {}
        
        sanitized = {}
        
        for key, value in data.items():
            # Remove potentially dangerous keys
            if key.startswith('__') or key in ['password', 'secret', 'token', 'key']:
                continue
            
            # Sanitize string values
            if isinstance(value, str):
                # Remove HTML tags
                import re
                value = re.sub(r'<[^>]+>', '', value)
                # Limit length
                if len(value) > 1000:
                    value = value[:1000] + '...'
            
            sanitized[key] = value
        
        return sanitized
    
    @staticmethod
    def create_session_fingerprint(user_id: int, ip_address: str, user_agent: str) -> str:
        """Create unique session fingerprint"""
        import hashlib
        fingerprint_data = f"{user_id}:{ip_address}:{user_agent}"
        return hashlib.sha256(fingerprint_data.encode()).hexdigest()
    
    @staticmethod
    def calculate_session_risk(session_data: Dict[str, Any]) -> float:
        """Calculate session risk score (0-1)"""
        risk_score = 0.0
        
        # Check for suspicious patterns
        if session_data.get('device_type') == 'bot':
            risk_score += 0.3
        
        if session_data.get('ip_address') == 'Unknown':
            risk_score += 0.2
        
        user_agent = session_data.get('user_agent', '')
        if any(suspicious in user_agent.lower() for suspicious in ['bot', 'crawler', 'scanner']):
            risk_score += 0.2
        
        # Check for multiple concurrent sessions
        if session_data.get('concurrent_sessions', 0) > 3:
            risk_score += 0.1
        
        # Check for unusual activity patterns
        if session_data.get('message_rate', 0) > 100:  # messages per minute
            risk_score += 0.2
        
        return min(risk_score, 1.0)


class StreamValidator:
    """Validates streaming data for quality and compliance"""
    
    @staticmethod
    def validate_stream_data(data: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
        """Validate stream data against schema"""
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Check required fields
        for field, field_schema in schema.items():
            if field_schema.get('required', False) and field not in data:
                validation_result['errors'].append(f"Missing required field: {field}")
                validation_result['valid'] = False
        
        # Check field types
        for field, value in data.items():
            if field in schema:
                field_schema = schema[field]
                expected_type = field_schema.get('type')
                
                if expected_type and not isinstance(value, expected_type):
                    validation_result['errors'].append(f"Field {field} has wrong type. Expected {expected_type.__name__}")
                    validation_result['valid'] = False
        
        # Check field constraints
        for field, value in data.items():
            if field in schema:
                field_schema = schema[field]
                
                # Check min/max for numbers
                if isinstance(value, (int, float)):
                    min_value = field_schema.get('min')
                    max_value = field_schema.get('max')
                    
                    if min_value is not None and value < min_value:
                        validation_result['errors'].append(f"Field {field} is below minimum value: {min_value}")
                        validation_result['valid'] = False
                    
                    if max_value is not None and value > max_value:
                        validation_result['errors'].append(f"Field {field} is above maximum value: {max_value}")
                        validation_result['valid'] = False
                
                # Check string length
                if isinstance(value, str):
                    min_length = field_schema.get('min_length')
                    max_length = field_schema.get('max_length')
                    
                    if min_length is not None and len(value) < min_length:
                        validation_result['errors'].append(f"Field {field} is too short. Minimum length: {min_length}")
                        validation_result['valid'] = False
                    
                    if max_length is not None and len(value) > max_length:
                        validation_result['errors'].append(f"Field {field} is too long. Maximum length: {max_length}")
                        validation_result['valid'] = False
        
        return validation_result
    
    @staticmethod
    def calculate_data_quality(data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate data quality scores"""
        quality_scores = {
            'completeness': 1.0,
            'accuracy': 1.0,
            'consistency': 1.0,
            'timeliness': 1.0
        }
        
        # Completeness: Check for missing or null values
        total_fields = len(data)
        non_null_fields = sum(1 for value in data.values() if value is not None and value != '')
        quality_scores['completeness'] = non_null_fields / max(total_fields, 1)
        
        # Accuracy: Check for obvious data quality issues
        accuracy_issues = 0
        for value in data.values():
            if isinstance(value, str):
                # Check for placeholder values
                if value.lower() in ['n/a', 'null', 'none', 'unknown', 'tbd']:
                    accuracy_issues += 1
                # Check for obviously invalid data
                if value.strip() == '':
                    accuracy_issues += 1
        
        quality_scores['accuracy'] = 1.0 - (accuracy_issues / max(total_fields, 1))
        
        # Consistency: Check data format consistency
        # This would require more sophisticated logic based on specific data types
        quality_scores['consistency'] = 0.9  # Placeholder
        
        # Timeliness: Check if data is recent (assuming timestamp field)
        if 'timestamp' in data:
            try:
                timestamp = data['timestamp']
                if isinstance(timestamp, str):
                    timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                
                age_minutes = (datetime.utcnow() - timestamp).total_seconds() / 60
                # Data older than 1 hour gets lower timeliness score
                if age_minutes > 60:
                    quality_scores['timeliness'] = max(0.1, 1.0 - (age_minutes / 360))
            except:
                quality_scores['timeliness'] = 0.5
        
        return quality_scores


# Global instances
room_manager = RoomManager()
connection_pool = ConnectionPool()
stream_processor = StreamProcessor()
analytics_calculator = AnalyticsCalculator()
event_broadcaster = EventBroadcaster()
