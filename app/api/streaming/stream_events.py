"""
Stream Events

Handles real-time stream events and data processing.
"""

import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from enum import Enum
import json

from .stream_manager import StreamData, StreamType

logger = logging.getLogger(__name__)

class StreamEventType(Enum):
    """Stream event types"""
    DATA_UPDATE = "data_update"
    SUBSCRIBER_JOINED = "subscriber_joined"
    SUBSCRIBER_LEFT = "subscriber_left"
    STREAM_STARTED = "stream_started"
    STREAM_STOPPED = "stream_stopped"
    STREAM_PAUSED = "stream_paused"
    STREAM_RESUMED = "stream_resumed"
    ERROR_OCCURRED = "error_occurred"

class StreamEvent:
    """Represents a stream event"""
    
    def __init__(self, event_type: StreamEventType, stream_id: str, 
                 data: Any = None, timestamp: datetime = None):
        self.event_type = event_type
        self.stream_id = stream_id
        self.data = data or {}
        self.timestamp = timestamp or datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary"""
        return {
            'event_type': self.event_type.value,
            'stream_id': self.stream_id,
            'timestamp': self.timestamp.isoformat(),
            'data': self.data
        }

class StreamEventProcessor:
    """Processes stream events and handles event logic"""
    
    def __init__(self):
        self.event_handlers: Dict[StreamEventType, List[Callable]] = {}
        self.event_history: List[StreamEvent] = []
        self.max_history = 1000
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """Register default event handlers"""
        self.register_handler(StreamEventType.SUBSCRIBER_JOINED, self._handle_subscriber_joined)
        self.register_handler(StreamEventType.SUBSCRIBER_LEFT, self._handle_subscriber_left)
        self.register_handler(StreamEventType.STREAM_STARTED, self._handle_stream_started)
        self.register_handler(StreamEventType.STREAM_STOPPED, self._handle_stream_stopped)
        self.register_handler(StreamEventType.ERROR_OCCURRED, self._handle_error_occurred)
    
    def register_handler(self, event_type: StreamEventType, handler: Callable):
        """Register event handler"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
    
    def process_event(self, event: StreamEvent) -> bool:
        """Process a stream event"""
        try:
            # Add to history
            self.event_history.append(event)
            if len(self.event_history) > self.max_history:
                self.event_history = self.event_history[-self.max_history:]
            
            # Call registered handlers
            if event.event_type in self.event_handlers:
                for handler in self.event_handlers[event.event_type]:
                    try:
                        handler(event)
                    except Exception as e:
                        logger.error(f"Error in event handler for {event.event_type}: {e}")
            
            return True
        except Exception as e:
            logger.error(f"Error processing event: {e}")
            return False
    
    def _handle_subscriber_joined(self, event: StreamEvent):
        """Handle subscriber joined event"""
        logger.info(f"Subscriber joined stream {event.stream_id}: {event.data}")
    
    def _handle_subscriber_left(self, event: StreamEvent):
        """Handle subscriber left event"""
        logger.info(f"Subscriber left stream {event.stream_id}: {event.data}")
    
    def _handle_stream_started(self, event: StreamEvent):
        """Handle stream started event"""
        logger.info(f"Stream started: {event.stream_id}")
    
    def _handle_stream_stopped(self, event: StreamEvent):
        """Handle stream stopped event"""
        logger.info(f"Stream stopped: {event.stream_id}")
    
    def _handle_error_occurred(self, event: StreamEvent):
        """Handle error occurred event"""
        logger.error(f"Error in stream {event.stream_id}: {event.data}")
    
    def get_event_history(self, stream_id: str = None, 
                         event_type: StreamEventType = None,
                         limit: int = 100) -> List[StreamEvent]:
        """Get event history"""
        events = self.event_history
        
        # Filter by stream ID
        if stream_id:
            events = [e for e in events if e.stream_id == stream_id]
        
        # Filter by event type
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        # Limit results
        return events[-limit:] if events else []

class StreamDataSource:
    """Data source for streams"""
    
    def __init__(self, name: str, data_generator: Callable = None):
        self.name = name
        self.data_generator = data_generator
        self.last_update = None
        self.update_count = 0
    
    def generate_data(self) -> Any:
        """Generate data for stream"""
        if self.data_generator:
            try:
                data = self.data_generator()
                self.last_update = datetime.utcnow()
                self.update_count += 1
                return data
            except Exception as e:
                logger.error(f"Error generating data for source {self.name}: {e}")
                return None
        return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get data source statistics"""
        return {
            'name': self.name,
            'last_update': self.last_update.isoformat() if self.last_update else None,
            'update_count': self.update_count
        }

class StreamDataProcessor:
    """Processes and transforms stream data"""
    
    def __init__(self):
        self.transformers: Dict[str, Callable] = {}
        self.validators: Dict[str, Callable] = {}
        self.filters: Dict[str, Callable] = {}
        self._register_default_processors()
    
    def _register_default_processors(self):
        """Register default data processors"""
        self.register_transformer('json', self._transform_json)
        self.register_transformer('timestamp', self._transform_timestamp)
        self.register_transformer('sanitize', self._transform_sanitize)
        
        self.register_validator('required_fields', self._validate_required_fields)
        self.register_validator('data_type', self._validate_data_type)
        
        self.register_filter('null_values', self._filter_null_values)
        self.register_filter('empty_strings', self._filter_empty_strings)
    
    def register_transformer(self, name: str, transformer: Callable):
        """Register data transformer"""
        self.transformers[name] = transformer
    
    def register_validator(self, name: str, validator: Callable):
        """Register data validator"""
        self.validators[name] = validator
    
    def register_filter(self, name: str, filter_func: Callable):
        """Register data filter"""
        self.filters[name] = filter_func
    
    def process_data(self, data: Any, processors: List[str] = None) -> Any:
        """Process data through registered processors"""
        if not processors:
            return data
        
        processed_data = data
        
        for processor_name in processors:
            if processor_name in self.transformers:
                processed_data = self.transformers[processor_name](processed_data)
            elif processor_name in self.validators:
                if not self.validators[processor_name](processed_data):
                    raise ValueError(f"Data validation failed: {processor_name}")
            elif processor_name in self.filters:
                processed_data = self.filters[processor_name](processed_data)
        
        return processed_data
    
    def _transform_json(self, data: Any) -> Any:
        """Transform data to JSON"""
        if isinstance(data, (dict, list)):
            return json.loads(json.dumps(data))
        return data
    
    def _transform_timestamp(self, data: Any) -> Any:
        """Add timestamp to data"""
        if isinstance(data, dict):
            data['timestamp'] = datetime.utcnow().isoformat()
        return data
    
    def _transform_sanitize(self, data: Any) -> Any:
        """Sanitize data"""
        if isinstance(data, dict):
            sanitized = {}
            for key, value in data.items():
                if isinstance(value, str):
                    # Basic sanitization
                    value = value.strip()
                    # Remove potentially harmful characters
                    value = value.replace('<', '&lt;').replace('>', '&gt;')
                sanitized[key] = value
            return sanitized
        return data
    
    def _validate_required_fields(self, data: Any, required_fields: List[str] = None) -> bool:
        """Validate required fields"""
        if not required_fields:
            return True
        
        if not isinstance(data, dict):
            return False
        
        return all(field in data for field in required_fields)
    
    def _validate_data_type(self, data: Any, expected_type: type = None) -> bool:
        """Validate data type"""
        if expected_type is None:
            return True
        
        return isinstance(data, expected_type)
    
    def _filter_null_values(self, data: Any) -> Any:
        """Filter null values"""
        if isinstance(data, dict):
            return {k: v for k, v in data.items() if v is not None}
        elif isinstance(data, list):
            return [item for item in data if item is not None]
        return data
    
    def _filter_empty_strings(self, data: Any) -> Any:
        """Filter empty strings"""
        if isinstance(data, dict):
            return {k: v for k, v in data.items() if v != ''}
        elif isinstance(data, list):
            return [item for item in data if item != '']
        return data

class StreamEvents:
    """Manages stream events and data processing"""
    
    def __init__(self, stream_manager):
        self.stream_manager = stream_manager
        self.event_processor = StreamEventProcessor()
        self.data_sources: Dict[str, StreamDataSource] = {}
        self.data_processor = StreamDataProcessor()
        self._register_default_data_sources()
    
    def _register_default_data_sources(self):
        """Register default data sources"""
        # Posts data source
        self.register_data_source('posts', self._generate_posts_data)
        
        # Comments data source
        self.register_data_source('comments', self._generate_comments_data)
        
        # Users data source
        self.register_data_source('users', self._generate_users_data)
        
        # Analytics data source
        self.register_data_source('analytics', self._generate_analytics_data)
        
        # Notifications data source
        self.register_data_source('notifications', self._generate_notifications_data)
    
    def register_data_source(self, name: str, data_generator: Callable):
        """Register data source"""
        self.data_sources[name] = StreamDataSource(name, data_generator)
    
    def get_data_source(self, name: str) -> Optional[StreamDataSource]:
        """Get data source by name"""
        return self.data_sources.get(name)
    
    def generate_data_for_stream(self, stream_id: str) -> Optional[Any]:
        """Generate data for a specific stream"""
        stream = self.stream_manager.get_stream(stream_id)
        if not stream:
            return None
        
        data_source_name = stream.config.data_source
        if not data_source_name:
            return None
        
        data_source = self.get_data_source(data_source_name)
        if not data_source:
            return None
        
        return data_source.generate_data()
    
    def _generate_posts_data(self) -> Dict[str, Any]:
        """Generate posts data"""
        # This would query the database for recent posts
        # For now, return mock data
        return {
            'total_posts': 1000,
            'recent_posts': [
                {
                    'id': 1,
                    'title': 'Sample Post 1',
                    'created_at': datetime.utcnow().isoformat()
                }
            ],
            'update_time': datetime.utcnow().isoformat()
        }
    
    def _generate_comments_data(self) -> Dict[str, Any]:
        """Generate comments data"""
        return {
            'total_comments': 500,
            'recent_comments': [
                {
                    'id': 1,
                    'content': 'Sample comment',
                    'post_id': 1,
                    'created_at': datetime.utcnow().isoformat()
                }
            ],
            'update_time': datetime.utcnow().isoformat()
        }
    
    def _generate_users_data(self) -> Dict[str, Any]:
        """Generate users data"""
        return {
            'online_users': 150,
            'total_users': 10000,
            'recent_activity': [
                {
                    'user_id': 1,
                    'username': 'user1',
                    'activity': 'login',
                    'timestamp': datetime.utcnow().isoformat()
                }
            ],
            'update_time': datetime.utcnow().isoformat()
        }
    
    def _generate_analytics_data(self) -> Dict[str, Any]:
        """Generate analytics data"""
        return {
            'page_views': 5000,
            'unique_visitors': 1000,
            'bounce_rate': 0.35,
            'avg_session_duration': 300,
            'update_time': datetime.utcnow().isoformat()
        }
    
    def _generate_notifications_data(self) -> Dict[str, Any]:
        """Generate notifications data"""
        return {
            'unread_count': 25,
            'recent_notifications': [
                {
                    'id': 1,
                    'type': 'info',
                    'message': 'Sample notification',
                    'created_at': datetime.utcnow().isoformat()
                }
            ],
            'update_time': datetime.utcnow().isoformat()
        }
    
    def broadcast_data_event(self, stream_id: str, data: Any, 
                           event_type: str = "update", metadata: Dict[str, Any] = None):
        """Broadcast data event to stream"""
        try:
            # Process data if needed
            processors = metadata.get('processors', []) if metadata else []
            processed_data = self.data_processor.process_data(data, processors)
            
            # Broadcast to stream
            delivered_count = self.stream_manager.broadcast_to_stream(
                stream_id, processed_data, event_type, metadata
            )
            
            # Create event
            event = StreamEvent(
                StreamEventType.DATA_UPDATE,
                stream_id,
                {
                    'delivered_count': delivered_count,
                    'event_type': event_type,
                    'data_size': len(str(processed_data))
                }
            )
            
            self.event_processor.process_event(event)
            
            return delivered_count
        except Exception as e:
            logger.error(f"Error broadcasting data event: {e}")
            return 0
    
    def create_stream_event(self, stream_id: str, event_type: StreamEventType, 
                          data: Any = None) -> bool:
        """Create and process a stream event"""
        try:
            event = StreamEvent(event_type, stream_id, data)
            return self.event_processor.process_event(event)
        except Exception as e:
            logger.error(f"Error creating stream event: {e}")
            return False
    
    def get_stream_events(self, stream_id: str = None, 
                         event_type: StreamEventType = None,
                         limit: int = 100) -> List[Dict[str, Any]]:
        """Get stream events"""
        events = self.event_processor.get_event_history(stream_id, event_type, limit)
        return [event.to_dict() for event in events]
    
    def get_data_source_stats(self, source_name: str = None) -> Dict[str, Any]:
        """Get data source statistics"""
        if source_name:
            data_source = self.get_data_source(source_name)
            return data_source.get_stats() if data_source else {}
        else:
            return {
                name: ds.get_stats()
                for name, ds in self.data_sources.items()
            }
    
    def start_stream_data_generation(self, stream_id: str, interval: int = 5):
        """Start automatic data generation for a stream"""
        # This would be implemented with proper background task scheduling
        logger.info(f"Started data generation for stream {stream_id} with interval {interval}s")
    
    def stop_stream_data_generation(self, stream_id: str):
        """Stop automatic data generation for a stream"""
        logger.info(f"Stopped data generation for stream {stream_id}")
    
    def process_stream_data(self, stream_id: str, data: Any, 
                           processors: List[str] = None) -> Any:
        """Process stream data"""
        return self.data_processor.process_data(data, processors)
