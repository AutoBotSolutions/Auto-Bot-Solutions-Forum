"""
Event Streaming Infrastructure

Advanced event streaming system with publish/subscribe patterns,
event routing, filtering, and persistence for real-time applications.
"""

import logging
from typing import Dict, List, Any, Optional, Callable, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
import time
import threading
import queue
import asyncio
import uuid
from collections import defaultdict, deque
import hashlib
import pickle
import redis
from redis.cluster import RedisCluster

logger = logging.getLogger(__name__)

class EventType(Enum):
    """Event types"""
    USER_EVENT = "user_event"
    SYSTEM_EVENT = "system_event"
    ROOM_EVENT = "room_event"
    APPLICATION_EVENT = "application_event"
    CUSTOM_EVENT = "custom_event"

class EventPriority(Enum):
    """Event priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"

class PersistenceType(Enum):
    """Event persistence types"""
    NONE = "none"
    MEMORY = "memory"
    REDIS = "redis"
    DATABASE = "database"

@dataclass
class Event:
    """Event data structure"""
    event_id: str
    event_type: EventType
    priority: EventPriority = EventPriority.NORMAL
    source: str = ""
    target: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    ttl: Optional[int] = None
    persistence: PersistenceType = PersistenceType.MEMORY
    filters: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary"""
        return {
            'event_id': self.event_id,
            'event_type': self.event_type.value,
            'priority': self.priority.value,
            'source': self.source,
            'target': self.target,
            'data': self.data,
            'metadata': self.metadata,
            'timestamp': self.timestamp.isoformat(),
            'ttl': self.ttl,
            'persistence': self.persistence.value,
            'filters': self.filters
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Event':
        """Create event from dictionary"""
        return cls(
            event_id=data['event_id'],
            event_type=EventType(data['event_type']),
            priority=EventPriority(data.get('priority', 'normal')),
            source=data.get('source', ''),
            target=data.get('target', ''),
            data=data.get('data', {}),
            metadata=data.get('metadata', {}),
            timestamp=datetime.fromisoformat(data['timestamp']),
            ttl=data.get('ttl'),
            persistence=PersistenceType(data.get('persistence', 'memory')),
            filters=data.get('filters', [])
        )

@dataclass
class Subscription:
    """Event subscription"""
    subscription_id: str
    subscriber_id: str
    event_type: Optional[EventType] = None
    filters: Dict[str, Any] = field(default_factory=dict)
    callback: Optional[Callable] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    active: bool = True
    last_event: Optional[datetime] = None
    event_count: int = 0

@dataclass
class StreamConfig:
    """Event streaming configuration"""
    max_events_per_second: int = 10000
    max_queue_size: int = 100000
    persistence_enabled: bool = True
    persistence_type: PersistenceType = PersistenceType.REDIS
    redis_client: Optional[redis.Redis] = None
    redis_cluster: Optional[RedisCluster] = None
    event_ttl: int = 3600  # 1 hour
    enable_filtering: bool = True
    enable_routing: bool = True
    enable_metrics: bool = True
    batch_size: int = 100
    batch_timeout: float = 1.0
    compression_enabled: bool = True
    encryption_enabled: bool = False
    encryption_key: Optional[str] = None

class EventStreamingManager:
    """Advanced event streaming manager"""
    
    def __init__(self, config: StreamConfig = None):
        self.config = config or StreamConfig()
        self.subscriptions: Dict[str, Subscription] = {}
        self.event_queue = queue.Queue(maxsize=self.config.max_queue_size)
        self.event_history = deque(maxlen=10000)
        self.subscribers: Dict[str, Set[str]] = defaultdict(set)  # event_type -> subscription_ids
        self.filters: Dict[str, Callable] = {}
        
        # Event routing
        self.event_handlers = defaultdict(list)
        self.event_processors = []
        
        # Background tasks
        self.running = True
        self.background_tasks = []
        
        # Metrics
        self.metrics = {
            'total_events': 0,
            'processed_events': 0,
            'failed_events': 0,
            'subscriptions': 0,
            'active_subscriptions': 0,
            'events_per_second': 0.0,
            'last_event_time': None
        }
        
        # Initialize persistence
        self._initialize_persistence()
        
        # Start background tasks
        self._start_background_tasks()
    
    def _initialize_persistence(self):
        """Initialize event persistence"""
        try:
            if self.config.persistence_type == PersistenceType.REDIS:
                if self.config.redis_cluster:
                    self.redis_client = self.config.redis_cluster
                elif self.config.redis_client:
                    self.redis_client = self.config.redis_client
                else:
                    # Create default Redis client
                    self.redis_client = redis.Redis(
                        host='localhost',
                        port=6379,
                        decode_responses=True
                    )
                
                logger.info("Redis persistence initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize persistence: {e}")
            self.config.persistence_enabled = False
    
    def _start_background_tasks(self):
        """Start background tasks"""
        def event_processor():
            while self.running:
                try:
                    # Process events in batches
                    events = []
                    start_time = time.time()
                    
                    # Collect events for batch
                    while (len(events) < self.config.batch_size and 
                           time.time() - start_time < self.config.batch_timeout):
                        try:
                            event = self.event_queue.get(timeout=0.1)
                            events.append(event)
                        except queue.Empty:
                            break
                    
                    if events:
                        self._process_event_batch(events)
                    
                except Exception as e:
                    logger.error(f"Event processor error: {e}")
                    time.sleep(1)
        
        def metrics_updater():
            while self.running:
                try:
                    self._update_metrics()
                    time.sleep(10)
                except Exception as e:
                    logger.error(f"Metrics updater error: {e}")
                    time.sleep(10)
        
        def persistence_cleaner():
            while self.running:
                try:
                    self._cleanup_expired_events()
                    time.sleep(300)  # Clean every 5 minutes
                except Exception as e:
                    logger.error(f"Persistence cleaner error: {e}")
                    time.sleep(60)
        
        # Start tasks
        for task_func in [event_processor, metrics_updater, persistence_cleaner]:
            task = threading.Thread(target=task_func, daemon=True)
            task.start()
            self.background_tasks.append(task)
        
        logger.info("Event streaming background tasks started")
    
    def publish_event(self, event_type: EventType, data: Dict[str, Any], 
                      source: str = "", target: str = "", 
                      priority: EventPriority = EventPriority.NORMAL,
                      ttl: Optional[int] = None,
                      filters: List[str] = None) -> str:
        """Publish an event"""
        try:
            # Create event
            event = Event(
                event_id=str(uuid.uuid4()),
                event_type=event_type,
                priority=priority,
                source=source,
                target=target,
                data=data,
                ttl=ttl or self.config.event_ttl,
                filters=filters or []
            )
            
            # Add to queue
            self.event_queue.put(event)
            
            # Update metrics
            self.metrics['total_events'] += 1
            self.metrics['last_event_time'] = datetime.utcnow()
            
            logger.debug(f"Published event: {event.event_id} ({event_type.value})")
            return event.event_id
            
        except Exception as e:
            logger.error(f"Error publishing event: {e}")
            self.metrics['failed_events'] += 1
            raise
    
    def subscribe(self, subscriber_id: str, event_type: Optional[EventType] = None,
                 filters: Dict[str, Any] = None, 
                 callback: Optional[Callable] = None) -> str:
        """Subscribe to events"""
        try:
            subscription_id = str(uuid.uuid4())
            
            subscription = Subscription(
                subscription_id=subscription_id,
                subscriber_id=subscriber_id,
                event_type=event_type,
                filters=filters or {},
                callback=callback
            )
            
            # Store subscription
            self.subscriptions[subscription_id] = subscription
            
            # Add to subscriber index
            if event_type:
                self.subscribers[event_type.value].add(subscription_id)
            
            # Update metrics
            self.metrics['subscriptions'] += 1
            self.metrics['active_subscriptions'] += 1
            
            logger.info(f"Created subscription: {subscription_id} for {subscriber_id}")
            return subscription_id
            
        except Exception as e:
            logger.error(f"Error creating subscription: {e}")
            raise
    
    def unsubscribe(self, subscription_id: str) -> bool:
        """Unsubscribe from events"""
        try:
            if subscription_id not in self.subscriptions:
                return False
            
            subscription = self.subscriptions[subscription_id]
            
            # Remove from subscriber index
            if subscription.event_type:
                self.subscribers[subscription.event_type.value].discard(subscription_id)
            
            # Remove subscription
            del self.subscriptions[subscription_id]
            
            # Update metrics
            self.metrics['active_subscriptions'] -= 1
            
            logger.info(f"Removed subscription: {subscription_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error removing subscription: {e}")
            return False
    
    def _process_event_batch(self, events: List[Event]):
        """Process a batch of events"""
        try:
            for event in events:
                # Apply filters
                if not self._apply_filters(event):
                    continue
                
                # Store event
                self._store_event(event)
                
                # Route to subscribers
                self._route_event(event)
                
                # Trigger handlers
                self._trigger_handlers(event)
                
                # Update metrics
                self.metrics['processed_events'] += 1
            
        except Exception as e:
            logger.error(f"Error processing event batch: {e}")
            self.metrics['failed_events'] += len(events)
    
    def _apply_filters(self, event: Event) -> bool:
        """Apply filters to event"""
        try:
            if not self.config.enable_filtering:
                return True
            
            # Apply global filters
            for filter_name, filter_func in self.filters.items():
                if not filter_func(event):
                    return False
            
            # Apply subscription filters
            if event.event_type.value in self.subscribers:
                for subscription_id in self.subscribers[event.event_type.value]:
                    if subscription_id in self.subscriptions:
                        subscription = self.subscriptions[subscription_id]
                        
                        # Check subscription filters
                        if not self._check_subscription_filters(event, subscription):
                            continue
            
            return True
            
        except Exception as e:
            logger.error(f"Error applying filters: {e}")
            return True
    
    def _check_subscription_filters(self, event: Event, subscription: Subscription) -> bool:
        """Check if event matches subscription filters"""
        try:
            if not subscription.filters:
                return True
            
            # Check source filter
            if 'source' in subscription.filters:
                if subscription.filters['source'] != event.source:
                    return False
            
            # Check target filter
            if 'target' in subscription.filters:
                if subscription.filters['target'] != event.target:
                    return False
            
            # Check data filters
            if 'data' in subscription.filters:
                data_filters = subscription.filters['data']
                for key, value in data_filters.items():
                    if key not in event.data or event.data[key] != value:
                        return False
            
            # Check metadata filters
            if 'metadata' in subscription.filters:
                metadata_filters = subscription.filters['metadata']
                for key, value in metadata_filters.items():
                    if key not in event.metadata or event.metadata[key] != value:
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking subscription filters: {e}")
            return True
    
    def _store_event(self, event: Event):
        """Store event for persistence"""
        try:
            # Add to history
            self.event_history.append(event)
            
            # Store in persistence layer
            if self.config.persistence_enabled:
                if event.persistence == PersistenceType.REDIS and self.redis_client:
                    self._store_event_redis(event)
                elif event.persistence == PersistenceType.DATABASE:
                    self._store_event_database(event)
            
        except Exception as e:
            logger.error(f"Error storing event: {e}")
    
    def _store_event_redis(self, event: Event):
        """Store event in Redis"""
        try:
            # Create event key
            key = f"event:{event.event_type.value}:{event.event_id}"
            
            # Serialize event
            event_data = json.dumps(event.to_dict())
            
            # Store with TTL
            ttl = event.ttl or self.config.event_ttl
            self.redis_client.setex(key, ttl, event_data)
            
            # Add to stream
            stream_key = f"stream:{event.event_type.value}"
            self.redis_client.xadd(
                stream_key,
                {
                    'event_id': event.event_id,
                    'event_type': event.event_type.value,
                    'priority': event.priority.value,
                    'source': event.source,
                    'target': event.target,
                    'data': json.dumps(event.data),
                    'metadata': json.dumps(event.metadata),
                    'timestamp': event.timestamp.isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Error storing event in Redis: {e}")
    
    def _store_event_database(self, event: Event):
        """Store event in database"""
        # This would integrate with your database system
        # For now, just log
        logger.debug(f"Would store event in database: {event.event_id}")
    
    def _route_event(self, event: Event):
        """Route event to subscribers"""
        try:
            # Get matching subscriptions
            matching_subscriptions = []
            
            # Get all subscriptions for this event type
            if event.event_type.value in self.subscribers:
                for subscription_id in self.subscribers[event.event_type.value]:
                    if subscription_id in self.subscriptions:
                        subscription = self.subscriptions[subscription_id]
                        
                        # Check filters
                        if self._check_subscription_filters(event, subscription):
                            matching_subscriptions.append(subscription)
            
            # Route to matching subscriptions
            for subscription in matching_subscriptions:
                try:
                    # Update subscription stats
                    subscription.last_event = datetime.utcnow()
                    subscription.event_count += 1
                    
                    # Call callback if provided
                    if subscription.callback:
                        subscription.callback(event)
                    
                except Exception as e:
                    logger.error(f"Error routing event to subscription {subscription.subscription_id}: {e}")
            
        except Exception as e:
            logger.error(f"Error routing event: {e}")
    
    def _trigger_handlers(self, event: Event):
        """Trigger event handlers"""
        try:
            for handler in self.event_handlers[event.event_type.value]:
                try:
                    handler(event)
                except Exception as e:
                    logger.error(f"Error in event handler: {e}")
            
            # Trigger general handlers
            for handler in self.event_handlers["*"]:
                try:
                    handler(event)
                except Exception as e:
                    logger.error(f"Error in general event handler: {e}")
            
        except Exception as e:
            logger.error(f"Error triggering handlers: {e}")
    
    def add_event_handler(self, event_type: EventType, handler: Callable):
        """Add event handler"""
        self.event_handlers[event_type.value].append(handler)
    
    def add_general_handler(self, handler: Callable):
        """Add general event handler"""
        self.event_handlers["*"].append(handler)
    
    def add_filter(self, filter_name: str, filter_func: Callable[[Event], bool]):
        """Add event filter"""
        self.filters[filter_name] = filter_func
    
    def remove_filter(self, filter_name: str):
        """Remove event filter"""
        if filter_name in self.filters:
            del self.filters[filter_name]
    
    def get_event_history(self, event_type: Optional[EventType] = None, 
                          limit: int = 100) -> List[Dict[str, Any]]:
        """Get event history"""
        try:
            events = []
            
            for event in reversed(self.event_history):
                if event_type and event.event_type != event_type:
                    continue
                
                events.append(event.to_dict())
                
                if len(events) >= limit:
                    break
            
            return events
            
        except Exception as e:
            logger.error(f"Error getting event history: {e}")
            return []
    
    def get_subscription_info(self, subscription_id: str) -> Optional[Dict[str, Any]]:
        """Get subscription information"""
        try:
            if subscription_id not in self.subscriptions:
                return None
            
            subscription = self.subscriptions[subscription_id]
            
            return {
                'subscription_id': subscription.subscription_id,
                'subscriber_id': subscription.subscriber_id,
                'event_type': subscription.event_type.value if subscription.event_type else None,
                'filters': subscription.filters,
                'created_at': subscription.created_at.isoformat(),
                'active': subscription.active,
                'last_event': subscription.last_event.isoformat() if subscription.last_event else None,
                'event_count': subscription.event_count
            }
            
        except Exception as e:
            logger.error(f"Error getting subscription info: {e}")
            return None
    
    def get_subscriptions(self, subscriber_id: str = None) -> List[Dict[str, Any]]:
        """Get all subscriptions or subscriptions for a specific subscriber"""
        try:
            subscriptions = []
            
            for subscription in self.subscriptions.values():
                if subscriber_id and subscription.subscriber_id != subscriber_id:
                    continue
                
                subscriptions.append({
                    'subscription_id': subscription.subscription_id,
                    'subscriber_id': subscription.subscriber_id,
                    'event_type': subscription.event_type.value if subscription.event_type else None,
                    'filters': subscription.filters,
                    'created_at': subscription.created_at.isoformat(),
                    'active': subscription.active,
                    'last_event': subscription.last_event.isoformat() if subscription.last_event else None,
                    'event_count': subscription.event_count
                })
            
            return subscriptions
            
        except Exception as e:
            logger.error(f"Error getting subscriptions: {e}")
            return []
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get streaming metrics"""
        return {
            'total_events': self.metrics['total_events'],
            'processed_events': self.metrics['processed_events'],
            'failed_events': self.metrics['failed_events'],
            'subscriptions': self.metrics['subscriptions'],
            'active_subscriptions': self.metrics['active_subscriptions'],
            'events_per_second': self.metrics['events_per_second'],
            'last_event_time': (
                self.metrics['last_event_time'].isoformat()
                if self.metrics['last_event_time'] else None
            ),
            'queue_size': self.event_queue.qsize(),
            'history_size': len(self.event_history),
            'persistence_enabled': self.config.persistence_enabled,
            'persistence_type': self.config.persistence_type.value
        }
    
    def _update_metrics(self):
        """Update streaming metrics"""
        try:
            # Calculate events per second
            if len(self.event_history) > 0:
                recent_events = [
                    event for event in self.event_history
                    if (datetime.utcnow() - event.timestamp).total_seconds() < 60
                ]
                self.metrics['events_per_second'] = len(recent_events) / 60
            
        except Exception as e:
            logger.error(f"Error updating metrics: {e}")
    
    def _cleanup_expired_events(self):
        """Clean up expired events"""
        try:
            if not self.config.persistence_enabled or not self.redis_client:
                return
            
            # Clean up Redis events
            pattern = "event:*"
            
            for key in self.redis_client.scan_iter(match=pattern, count=100):
                try:
                    key_str = key[0].decode() if isinstance(key[0], bytes) else key[0]
                    ttl = self.redis_client.ttl(key_str)
                    
                    if ttl == -1:  # No expiry set
                        # Check event timestamp
                        event_data = self.redis_client.get(key_str)
                        if event_data:
                            event_dict = json.loads(event_data)
                            event_time = datetime.fromisoformat(event_dict['timestamp'])
                            
                            # Remove old events (older than TTL)
                            if (datetime.utcnow() - event_time).total_seconds() > self.config.event_ttl:
                                self.redis_client.delete(key_str)
                
                except Exception as e:
                    logger.error(f"Error cleaning up event {key}: {e}")
            
            logger.debug("Expired events cleanup completed")
            
        except Exception as e:
            logger.error(f"Error cleaning up expired events: {e}")
    
    def get_config(self) -> Dict[str, Any]:
        """Get streaming configuration"""
        return {
            'max_events_per_second': self.config.max_events_per_second,
            'max_queue_size': self.config.max_queue_size,
            'persistence_enabled': self.config.persistence_enabled,
            'persistence_type': self.config.persistence_type.value,
            'event_ttl': self.config.event_ttl,
            'enable_filtering': self.config.enable_filtering,
            'enable_routing': self.config.enable_routing,
            'enable_metrics': self.config.enable_metrics,
            'batch_size': self.config.batch_size,
            'batch_timeout': self.config.batch_timeout,
            'compression_enabled': self.config.compression_enabled,
            'encryption_enabled': self.config.encryption_enabled
        }
    
    def update_config(self, **kwargs):
        """Update streaming configuration"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
                logger.info(f"Updated streaming config: {key} = {value}")
    
    def shutdown(self):
        """Shutdown event streaming manager"""
        try:
            # Stop background tasks
            self.running = False
            
            # Clear queues
            while not self.event_queue.empty():
                try:
                    self.event_queue.get_nowait()
                except queue.Empty:
                    break
            
            # Close Redis connection
            if self.redis_client:
                self.redis_client.close()
            
            logger.info("Event streaming manager shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
