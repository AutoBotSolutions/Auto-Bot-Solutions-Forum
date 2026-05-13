"""
Stream Manager

Manages real-time data streaming with WebSocket connections,
event broadcasting, and live data updates.
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Callable, Set
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
import uuid
import weakref

logger = logging.getLogger(__name__)

class StreamType(Enum):
    """Stream types"""
    LIVE_POSTS = "live_posts"
    LIVE_COMMENTS = "live_comments"
    LIVE_USERS = "live_users"
    LIVE_NOTIFICATIONS = "live_notifications"
    LIVE_ANALYTICS = "live_analytics"
    LIVE_ACTIVITY = "live_activity"
    CUSTOM = "custom"

class StreamStatus(Enum):
    """Stream status"""
    ACTIVE = "active"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"

@dataclass
class StreamConfig:
    """Stream configuration"""
    stream_type: StreamType
    name: str
    description: str = ""
    buffer_size: int = 100
    update_interval: int = 1  # seconds
    max_subscribers: int = 1000
    requires_auth: bool = True
    required_permissions: List[str] = field(default_factory=list)
    data_source: Optional[str] = None
    filters: Dict[str, Any] = field(default_factory=dict)

@dataclass
class StreamData:
    """Stream data packet"""
    stream_id: str
    data: Any
    timestamp: datetime
    event_type: str = "update"
    metadata: Dict[str, Any] = field(default_factory=dict)

class StreamSubscriber:
    """Stream subscriber"""
    
    def __init__(self, sid: str, stream_id: str, filters: Dict[str, Any] = None):
        self.sid = sid
        self.stream_id = stream_id
        self.filters = filters or {}
        self.subscribed_at = datetime.utcnow()
        self.last_activity = datetime.utcnow()
        self.message_count = 0
        self.is_active = True
    
    def update_activity(self):
        """Update subscriber activity"""
        self.last_activity = datetime.utcnow()
        self.message_count += 1
    
    def should_receive_data(self, data: StreamData) -> bool:
        """Check if subscriber should receive data based on filters"""
        if not self.filters:
            return True
        
        # Apply filters (simplified implementation)
        for filter_key, filter_value in self.filters.items():
            if filter_key in data.metadata:
                if data.metadata[filter_key] != filter_value:
                    return False
        
        return True

class Stream:
    """Real-time data stream"""
    
    def __init__(self, config: StreamConfig):
        self.config = config
        self.stream_id = str(uuid.uuid4())
        self.status = StreamStatus.ACTIVE
        self.created_at = datetime.utcnow()
        self.subscribers: Dict[str, StreamSubscriber] = {}
        self.data_buffer: List[StreamData] = []
        self.event_handlers: List[Callable] = []
        self.stats = {
            'total_messages': 0,
            'total_subscribers': 0,
            'peak_subscribers': 0,
            'last_broadcast': None
        }
    
    def add_subscriber(self, sid: str, filters: Dict[str, Any] = None) -> bool:
        """Add subscriber to stream"""
        if len(self.subscribers) >= self.config.max_subscribers:
            return False
        
        subscriber = StreamSubscriber(sid, self.stream_id, filters)
        self.subscribers[sid] = subscriber
        self.stats['total_subscribers'] = len(self.subscribers)
        self.stats['peak_subscribers'] = max(self.stats['peak_subscribers'], len(self.subscribers))
        
        logger.info(f"Subscriber {sid} added to stream {self.stream_id}")
        return True
    
    def remove_subscriber(self, sid: str):
        """Remove subscriber from stream"""
        if sid in self.subscribers:
            del self.subscribers[sid]
            self.stats['total_subscribers'] = len(self.subscribers)
            logger.info(f"Subscriber {sid} removed from stream {self.stream_id}")
    
    def broadcast_data(self, data: Any, event_type: str = "update", metadata: Dict[str, Any] = None):
        """Broadcast data to all subscribers"""
        stream_data = StreamData(
            stream_id=self.stream_id,
            data=data,
            timestamp=datetime.utcnow(),
            event_type=event_type,
            metadata=metadata or {}
        )
        
        # Add to buffer
        self.data_buffer.append(stream_data)
        if len(self.data_buffer) > self.config.buffer_size:
            self.data_buffer = self.data_buffer[-self.config.buffer_size:]
        
        # Broadcast to subscribers
        delivered_count = 0
        for subscriber in self.subscribers.values():
            if subscriber.is_active and subscriber.should_receive_data(stream_data):
                # This would be handled by WebSocket handlers
                subscriber.update_activity()
                delivered_count += 1
        
        # Update stats
        self.stats['total_messages'] += 1
        self.stats['last_broadcast'] = datetime.utcnow()
        
        # Call event handlers
        for handler in self.event_handlers:
            try:
                handler(stream_data)
            except Exception as e:
                logger.error(f"Error in stream event handler: {e}")
        
        return delivered_count
    
    def get_buffer(self, limit: int = 50) -> List[StreamData]:
        """Get recent data from buffer"""
        return self.data_buffer[-limit:]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get stream statistics"""
        return {
            'stream_id': self.stream_id,
            'stream_type': self.config.stream_type.value,
            'name': self.config.name,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'subscribers': len(self.subscribers),
            'buffer_size': len(self.data_buffer),
            'stats': self.stats.copy()
        }
    
    def pause(self):
        """Pause stream"""
        self.status = StreamStatus.PAUSED
        logger.info(f"Stream {self.stream_id} paused")
    
    def resume(self):
        """Resume stream"""
        self.status = StreamStatus.ACTIVE
        logger.info(f"Stream {self.stream_id} resumed")
    
    def stop(self):
        """Stop stream"""
        self.status = StreamStatus.STOPPED
        # Remove all subscribers
        self.subscribers.clear()
        logger.info(f"Stream {self.stream_id} stopped")

class StreamManager:
    """Manages all real-time data streams"""
    
    def __init__(self, websocket_manager=None):
        self.websocket_manager = websocket_manager
        self.streams: Dict[str, Stream] = {}
        self.stream_configs: Dict[str, StreamConfig] = {}
        self.global_stats = {
            'total_streams': 0,
            'active_streams': 0,
            'total_subscribers': 0,
            'total_messages': 0
        }
        self._register_default_streams()
        self._start_background_tasks()
    
    def _register_default_streams(self):
        """Register default stream configurations"""
        # Live posts stream
        self.register_stream_config(StreamConfig(
            stream_type=StreamType.LIVE_POSTS,
            name="Live Posts",
            description="Real-time updates for new and modified posts",
            buffer_size=200,
            update_interval=2,
            max_subscribers=500,
            requires_auth=True,
            data_source="posts"
        ))
        
        # Live comments stream
        self.register_stream_config(StreamConfig(
            stream_type=StreamType.LIVE_COMMENTS,
            name="Live Comments",
            description="Real-time updates for new comments",
            buffer_size=300,
            update_interval=1,
            max_subscribers=1000,
            requires_auth=True,
            data_source="comments"
        ))
        
        # Live users stream
        self.register_stream_config(StreamConfig(
            stream_type=StreamType.LIVE_USERS,
            name="Live Users",
            description="Real-time user activity updates",
            buffer_size=100,
            update_interval=5,
            max_subscribers=200,
            requires_auth=True,
            required_permissions=["admin"],
            data_source="users"
        ))
        
        # Live notifications stream
        self.register_stream_config(StreamConfig(
            stream_type=StreamType.LIVE_NOTIFICATIONS,
            name="Live Notifications",
            description="Real-time notification updates",
            buffer_size=50,
            update_interval=1,
            max_subscribers=1000,
            requires_auth=True,
            data_source="notifications"
        ))
        
        # Live analytics stream
        self.register_stream_config(StreamConfig(
            stream_type=StreamType.LIVE_ANALYTICS,
            name="Live Analytics",
            description="Real-time analytics updates",
            buffer_size=100,
            update_interval=10,
            max_subscribers=100,
            requires_auth=True,
            required_permissions=["admin"],
            data_source="analytics"
        ))
    
    def register_stream_config(self, config: StreamConfig) -> str:
        """Register stream configuration"""
        stream_id = str(uuid.uuid4())
        self.stream_configs[stream_id] = config
        return stream_id
    
    def create_stream(self, config: StreamConfig) -> Stream:
        """Create a new stream"""
        stream = Stream(config)
        self.streams[stream.stream_id] = stream
        self.global_stats['total_streams'] += 1
        self.global_stats['active_streams'] += 1
        
        logger.info(f"Created stream: {config.name} ({stream.stream_id})")
        return stream
    
    def get_stream(self, stream_id: str) -> Optional[Stream]:
        """Get stream by ID"""
        return self.streams.get(stream_id)
    
    def get_streams_by_type(self, stream_type: StreamType) -> List[Stream]:
        """Get streams by type"""
        return [
            stream for stream in self.streams.values()
            if stream.config.stream_type == stream_type
        ]
    
    def subscribe_to_stream(self, stream_id: str, sid: str, 
                          filters: Dict[str, Any] = None) -> bool:
        """Subscribe to a stream"""
        stream = self.get_stream(stream_id)
        if not stream:
            return False
        
        # Check authentication if required
        if stream.config.requires_auth:
            # This would check with WebSocket auth system
            pass
        
        # Check permissions if required
        if stream.config.required_permissions:
            # This would check user permissions
            pass
        
        return stream.add_subscriber(sid, filters)
    
    def unsubscribe_from_stream(self, stream_id: str, sid: str):
        """Unsubscribe from a stream"""
        stream = self.get_stream(stream_id)
        if stream:
            stream.remove_subscriber(sid)
    
    def unsubscribe_from_all_streams(self, sid: str):
        """Unsubscribe from all streams"""
        for stream in self.streams.values():
            stream.remove_subscriber(sid)
    
    def broadcast_to_stream(self, stream_id: str, data: Any, 
                          event_type: str = "update", metadata: Dict[str, Any] = None) -> int:
        """Broadcast data to a specific stream"""
        stream = self.get_stream(stream_id)
        if not stream:
            return 0
        
        delivered_count = stream.broadcast_data(data, event_type, metadata)
        self.global_stats['total_messages'] += delivered_count
        
        return delivered_count
    
    def broadcast_to_type(self, stream_type: StreamType, data: Any, 
                          event_type: str = "update", metadata: Dict[str, Any] = None) -> int:
        """Broadcast data to all streams of a specific type"""
        total_delivered = 0
        streams = self.get_streams_by_type(stream_type)
        
        for stream in streams:
            delivered = stream.broadcast_data(data, event_type, metadata)
            total_delivered += delivered
        
        self.global_stats['total_messages'] += total_delivered
        return total_delivered
    
    def broadcast_to_all(self, data: Any, event_type: str = "update", 
                        metadata: Dict[str, Any] = None) -> int:
        """Broadcast data to all streams"""
        total_delivered = 0
        
        for stream in self.streams.values():
            delivered = stream.broadcast_data(data, event_type, metadata)
            total_delivered += delivered
        
        self.global_stats['total_messages'] += total_delivered
        return total_delivered
    
    def get_stream_stats(self, stream_id: str) -> Optional[Dict[str, Any]]:
        """Get statistics for a specific stream"""
        stream = self.get_stream(stream_id)
        return stream.get_stats() if stream else None
    
    def get_all_stats(self) -> Dict[str, Any]:
        """Get global statistics"""
        # Update current stats
        self.global_stats['total_streams'] = len(self.streams)
        self.global_stats['active_streams'] = len([
            s for s in self.streams.values() if s.status == StreamStatus.ACTIVE
        ])
        self.global_stats['total_subscribers'] = sum(
            len(s.subscribers) for s in self.streams.values()
        )
        
        return {
            'global_stats': self.global_stats.copy(),
            'streams': {
                stream_id: stream.get_stats()
                for stream_id, stream in self.streams.items()
            },
            'stream_types': {
                stream_type.value: len(self.get_streams_by_type(stream_type))
                for stream_type in StreamType
            }
        }
    
    def cleanup_inactive_streams(self, max_inactive_hours: int = 24) -> int:
        """Clean up inactive streams"""
        cutoff_time = datetime.utcnow() - timedelta(hours=max_inactive_hours)
        
        inactive_streams = []
        for stream_id, stream in self.streams.items():
            if stream.stats['last_broadcast'] and stream.stats['last_broadcast'] < cutoff_time:
                if len(stream.subscribers) == 0:
                    inactive_streams.append(stream_id)
        
        for stream_id in inactive_streams:
            stream = self.streams[stream_id]
            stream.stop()
            del self.streams[stream_id]
            self.global_stats['active_streams'] -= 1
        
        logger.info(f"Cleaned up {len(inactive_streams)} inactive streams")
        return len(inactive_streams)
    
    def cleanup_inactive_subscribers(self, max_inactive_minutes: int = 30) -> int:
        """Clean up inactive subscribers"""
        cutoff_time = datetime.utcnow() - timedelta(minutes=max_inactive_minutes)
        
        total_cleaned = 0
        for stream in self.streams.values():
            inactive_sids = []
            for sid, subscriber in stream.subscribers.items():
                if subscriber.last_activity < cutoff_time:
                    inactive_sids.append(sid)
            
            for sid in inactive_sids:
                stream.remove_subscriber(sid)
                total_cleaned += 1
        
        logger.info(f"Cleaned up {total_cleaned} inactive subscribers")
        return total_cleaned
    
    def _start_background_tasks(self):
        """Start background tasks for stream management"""
        def background_task():
            """Background task for stream management"""
            try:
                # Clean up inactive subscribers every 5 minutes
                self.cleanup_inactive_subscribers(5)
                
                # Clean up inactive streams every hour
                self.cleanup_inactive_streams(1)
                
                # Update global stats
                self.get_all_stats()
                
            except Exception as e:
                logger.error(f"Error in background task: {e}")
        
        # This would be implemented with proper background task scheduling
        # For now, it's just a placeholder
        logger.info("Background task scheduler started for stream management")
    
    def create_custom_stream(self, name: str, description: str = "", 
                           data_source: str = None, **kwargs) -> Stream:
        """Create a custom stream"""
        config = StreamConfig(
            stream_type=StreamType.CUSTOM,
            name=name,
            description=description,
            data_source=data_source,
            **kwargs
        )
        
        return self.create_stream(config)
    
    def get_stream_buffer(self, stream_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get stream buffer data"""
        stream = self.get_stream(stream_id)
        if not stream:
            return []
        
        buffer_data = stream.get_buffer(limit)
        return [
            {
                'stream_id': data.stream_id,
                'data': data.data,
                'timestamp': data.timestamp.isoformat(),
                'event_type': data.event_type,
                'metadata': data.metadata
            }
            for data in buffer_data
        ]
    
    def pause_stream(self, stream_id: str) -> bool:
        """Pause a stream"""
        stream = self.get_stream(stream_id)
        if stream:
            stream.pause()
            return True
        return False
    
    def resume_stream(self, stream_id: str) -> bool:
        """Resume a stream"""
        stream = self.get_stream(stream_id)
        if stream:
            stream.resume()
            return True
        return False
    
    def stop_stream(self, stream_id: str) -> bool:
        """Stop a stream"""
        stream = self.get_stream(stream_id)
        if stream:
            stream.stop()
            self.global_stats['active_streams'] -= 1
            return True
        return False
