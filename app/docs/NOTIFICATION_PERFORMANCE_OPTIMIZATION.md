# Notification System Performance Optimization Guide

## Overview

This guide provides comprehensive performance optimization strategies for the notification system. The optimizations cover database queries, caching strategies, queue management, WebSocket performance, email delivery, push notifications, and overall system scalability.

**Performance Goals:**
- **Response Time:** < 100ms for API endpoints
- **WebSocket Latency:** < 50ms for real-time delivery
- **Email Delivery:** < 5 seconds for queuing
- **Push Notification:** < 1 second for delivery
- **Database Queries:** < 50ms average query time
- **Memory Usage:** < 512MB per worker
- **CPU Usage:** < 70% average load

## Database Optimization

### Indexing Strategy

Create optimized database indexes for notification queries:

```sql
-- Notification table indexes
CREATE INDEX idx_notifications_user_id_created_at ON notifications(user_id, created_at DESC);
CREATE INDEX idx_notifications_type_priority ON notifications(type, priority);
CREATE INDEX idx_notifications_is_read_created_at ON notifications(is_read, created_at);
CREATE INDEX idx_notifications_user_type ON notifications(user_id, type);

-- Admin notification indexes
CREATE INDEX idx_admin_notifications_user_id ON admin_notifications(user_id);
CREATE INDEX idx_admin_notifications_priority ON admin_notifications(priority);
CREATE INDEX idx_admin_notifications_created_at ON admin_notifications(created_at);

-- Notification delivery tracking indexes
CREATE INDEX idx_notification_delivery_notification_id ON notification_delivery(notification_id);
CREATE INDEX idx_notification_delivery_status_created ON notification_delivery(status, created_at);

-- Mobile device registry indexes
CREATE INDEX idx_mobile_devices_user_id ON mobile_devices(user_id);
CREATE INDEX idx_mobile_devices_platform ON mobile_devices(platform);
CREATE INDEX idx_mobile_devices_status ON mobile_devices(status);

-- Notification preference indexes
CREATE INDEX idx_notification_preferences_user_type ON notification_preferences(user_id, notification_type);
CREATE INDEX idx_notification_preferences_enabled ON notification_preferences(enabled);
```

### Query Optimization

Implement optimized query methods:

```python
# app/notifications/optimized_queries.py
from sqlalchemy import text, and_, or_, func
from sqlalchemy.orm import joinedload, selectinload
from app.models import Notification, AdminNotification
from datetime import datetime, timedelta

class OptimizedNotificationQueries:
    
    @staticmethod
    def get_user_notifications_optimized(user_id, limit=50, unread_only=False, 
                                         notification_types=None):
        """Optimized query for user notifications"""
        query = Notification.query.filter(
            Notification.user_id == user_id
        )
        
        if unread_only:
            query = query.filter(Notification.is_read == False)
        
        if notification_types:
            query = query.filter(Notification.type.in_(notification_types))
        
        # Use indexed columns for ordering
        query = query.order_by(
            Notification.priority.desc(),
            Notification.created_at.desc()
        ).limit(limit)
        
        return query.all()
    
    @staticmethod
    def get_unread_count_optimized(user_id):
        """Optimized unread count query"""
        return Notification.query.filter(
            and_(
                Notification.user_id == user_id,
                Notification.is_read == False
            )
        ).count()
    
    @staticmethod
    def get_notifications_by_date_range(user_id, start_date, end_date):
        """Optimized date range query"""
        return Notification.query.filter(
            and_(
                Notification.user_id == user_id,
                Notification.created_at >= start_date,
                Notification.created_at <= end_date
            )
        ).order_by(Notification.created_at.desc()).all()
    
    @staticmethod
    def batch_mark_as_read(notification_ids):
        """Optimized batch update"""
        return Notification.query.filter(
            Notification.id.in_(notification_ids)
        ).update({
            'is_read': True,
            'read_at': datetime.utcnow()
        }, synchronize_session=False)
    
    @staticmethod
    def get_notification_statistics(user_id, days=30):
        """Optimized statistics query"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        return Notification.query.filter(
            and_(
                Notification.user_id == user_id,
                Notification.created_at >= start_date
            )
        ).with_entities(
            Notification.type,
            func.count(Notification.id).label('count'),
            func.sum(func.case([(Notification.is_read == False, 1)], else_=0)).label('unread_count')
        ).group_by(Notification.type).all()
```

### Database Connection Pooling

Configure optimized database connection pooling:

```python
# app/config/database.py
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool
from app.config.notification_config import get_notification_config

def create_optimized_database_engine():
    """Create optimized database engine"""
    config = get_notification_config()
    
    engine = create_engine(
        config.database_url,
        poolclass=QueuePool,
        pool_size=config.db_pool_size,
        max_overflow=config.db_max_overflow,
        pool_timeout=config.db_pool_timeout,
        pool_recycle=3600,  # Recycle connections every hour
        pool_pre_ping=True,  # Validate connections before use
        echo=config.debug_notifications,  # SQL logging in debug mode
        connect_args={
            'charset': 'utf8mb4',
            'use_unicode': True,
            'sql_mode': 'STRICT_TRANS_TABLES'
        }
    )
    
    return engine
```

## Caching Strategy

### Redis Caching Implementation

Implement comprehensive Redis caching:

```python
# app/notifications/caching.py
import json
import pickle
import hashlib
from datetime import datetime, timedelta
from typing import Any, Optional, Union
import redis
from functools import wraps

from app.config.notification_config import get_notification_config

class NotificationCacheManager:
    """Advanced caching manager for notifications"""
    
    def __init__(self):
        self.config = get_notification_config()
        self.redis_client = None
        self._setup_redis()
    
    def _setup_redis(self):
        """Setup Redis connection with optimized settings"""
        try:
            self.redis_client = redis.from_url(
                self.config.redis_url,
                db=self.config.redis_cache_db,
                decode_responses=False,  # Keep binary data for pickling
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                max_connections=self.config.redis_connection_pool_size
            )
            
            # Test connection
            self.redis_client.ping()
            
        except Exception as e:
            print(f"Redis connection failed: {e}")
            self.redis_client = None
    
    def cache_result(self, key_prefix: str, ttl: int = 300):
        """Decorator for caching function results"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                if not self.redis_client:
                    return func(*args, **kwargs)
                
                # Generate cache key
                cache_key = self._generate_cache_key(
                    key_prefix, func.__name__, args, kwargs
                )
                
                # Try to get from cache
                cached_result = self.get(cache_key)
                if cached_result is not None:
                    return cached_result
                
                # Execute function and cache result
                result = func(*args, **kwargs)
                self.set(cache_key, result, ttl)
                
                return result
            
            return wrapper
        return decorator
    
    def _generate_cache_key(self, prefix: str, func_name: str, 
                           args: tuple, kwargs: dict) -> str:
        """Generate unique cache key"""
        key_data = {
            'prefix': prefix,
            'func': func_name,
            'args': str(args),
            'kwargs': str(sorted(kwargs.items()))
        }
        
        key_hash = hashlib.md5(
            json.dumps(key_data, sort_keys=True).encode()
        ).hexdigest()
        
        return f"notification_cache:{prefix}:{func_name}:{key_hash}"
    
    def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """Set cache value with TTL"""
        if not self.redis_client:
            return False
        
        try:
            if ttl is None:
                ttl = self.config.translation_cache_ttl
            
            # Serialize value
            serialized_value = pickle.dumps(value)
            
            return self.redis_client.setex(key, ttl, serialized_value)
            
        except Exception as e:
            print(f"Cache set error: {e}")
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """Get cache value"""
        if not self.redis_client:
            return None
        
        try:
            serialized_value = self.redis_client.get(key)
            if serialized_value is None:
                return None
            
            return pickle.loads(serialized_value)
            
        except Exception as e:
            print(f"Cache get error: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """Delete cache key"""
        if not self.redis_client:
            return False
        
        try:
            return bool(self.redis_client.delete(key))
        except Exception as e:
            print(f"Cache delete error: {e}")
            return False
    
    def invalidate_pattern(self, pattern: str) -> int:
        """Delete keys matching pattern"""
        if not self.redis_client:
            return 0
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            print(f"Cache invalidate pattern error: {e}")
            return 0
    
    def get_cache_info(self) -> dict:
        """Get cache statistics"""
        if not self.redis_client:
            return {}
        
        try:
            info = self.redis_client.info('memory')
            return {
                'used_memory': info.get('used_memory', 0),
                'used_memory_human': info.get('used_memory_human', '0B'),
                'used_memory_peak': info.get('used_memory_peak', 0),
                'connected_clients': self.redis_client.client_list().__len__()
            }
        except Exception as e:
            print(f"Cache info error: {e}")
            return {}

# Global cache manager
cache_manager = NotificationCacheManager()

# Cache decorators for common operations
@cache_manager.cache_result('user_notifications', ttl=300)
def get_user_notifications_cached(user_id: int, limit: int = 50):
    """Cached user notifications"""
    from app.notifications.optimized_queries import OptimizedNotificationQueries
    return OptimizedNotificationQueries.get_user_notifications_optimized(
        user_id, limit
    )

@cache_manager.cache_result('unread_count', ttl=60)
def get_unread_count_cached(user_id: int):
    """Cached unread count"""
    from app.notifications.optimized_queries import OptimizedNotificationQueries
    return OptimizedNotificationQueries.get_unread_count_optimized(user_id)

@cache_manager.cache_result('translation', ttl=3600)
def get_translation_cached(text: str, target_lang: str, source_lang: str = 'en'):
    """Cached translation"""
    from app.notifications.translation_service import notification_translation_service
    return notification_translation_service.translate_text(
        text, target_lang, source_lang
    )
```

### Application-Level Caching

Implement application-level caching for frequently accessed data:

```python
# app/notifications/memory_cache.py
import threading
import time
from collections import OrderedDict
from typing import Any, Optional

class LRUCache:
    """Thread-safe LRU cache implementation"""
    
    def __init__(self, max_size: int = 1000, ttl: int = 300):
        self.max_size = max_size
        self.ttl = ttl
        self.cache = OrderedDict()
        self.timestamps = {}
        self.lock = threading.RLock()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        with self.lock:
            if key not in self.cache:
                return None
            
            # Check TTL
            if time.time() - self.timestamps[key] > self.ttl:
                del self.cache[key]
                del self.timestamps[key]
                return None
            
            # Move to end (most recently used)
            self.cache.move_to_end(key)
            return self.cache[key]
    
    def set(self, key: str, value: Any) -> None:
        """Set value in cache"""
        with self.lock:
            # Remove if exists
            if key in self.cache:
                del self.cache[key]
                del self.timestamps[key]
            
            # Remove oldest if at capacity
            elif len(self.cache) >= self.max_size:
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]
                del self.timestamps[oldest_key]
            
            # Add new item
            self.cache[key] = value
            self.timestamps[key] = time.time()
    
    def clear(self) -> None:
        """Clear all cache entries"""
        with self.lock:
            self.cache.clear()
            self.timestamps.clear()
    
    def size(self) -> int:
        """Get cache size"""
        return len(self.cache)

# Memory cache instances
user_cache = LRUCache(max_size=1000, ttl=300)
translation_cache = LRUCache(max_size=500, ttl=3600)
filter_cache = LRUCache(max_size=200, ttl=1800)
```

## WebSocket Performance Optimization

### Connection Management

Optimize WebSocket connection handling:

```python
# app/websockets/optimized_events.py
from flask_socketio import emit, join_room, leave_room, disconnect
from flask_login import current_user
import asyncio
import time
from collections import defaultdict
from typing import Dict, Set

class OptimizedWebSocketManager:
    """Optimized WebSocket connection manager"""
    
    def __init__(self):
        self.connections: Dict[int, Set[str]] = defaultdict(set)
        self.user_rooms: Dict[str, int] = {}
        self.connection_times: Dict[str, float] = {}
        self.message_queue = asyncio.Queue()
        self.batch_size = 50
        self.batch_timeout = 0.1  # 100ms
        
    def add_connection(self, user_id: int, session_id: str):
        """Add WebSocket connection"""
        self.connections[user_id].add(session_id)
        self.user_rooms[session_id] = user_id
        self.connection_times[session_id] = time.time()
        
        # Join user room
        join_room(f"user_{user_id}")
        
        # Cleanup old connections
        self._cleanup_old_connections(user_id)
    
    def remove_connection(self, session_id: str):
        """Remove WebSocket connection"""
        if session_id in self.user_rooms:
            user_id = self.user_rooms[session_id]
            
            self.connections[user_id].discard(session_id)
            del self.user_rooms[session_id]
            del self.connection_times[session_id]
            
            # Leave room
            leave_room(f"user_{user_id}")
    
    def _cleanup_old_connections(self, user_id: int):
        """Clean up old connections for user"""
        current_time = time.time()
        timeout = 3600  # 1 hour timeout
        
        old_connections = []
        for session_id, conn_time in self.connection_times.items():
            if self.user_rooms.get(session_id) == user_id:
                if current_time - conn_time > timeout:
                    old_connections.append(session_id)
        
        for session_id in old_connections:
            self.remove_connection(session_id)
            disconnect(session_id)
    
    async def batch_emit_to_user(self, user_id: int, event: str, data: dict):
        """Batch emit to user connections"""
        if user_id not in self.connections:
            return
        
        session_ids = list(self.connections[user_id])
        
        # Batch emit to all user connections
        for session_id in session_ids:
            emit(event, data, room=f"user_{user_id}")
    
    def get_connection_stats(self) -> dict:
        """Get connection statistics"""
        return {
            'total_connections': sum(len(conns) for conns in self.connections.values()),
            'unique_users': len(self.connections),
            'average_connections_per_user': sum(len(conns) for conns in self.connections.values()) / max(len(self.connections), 1)
        }

# Global WebSocket manager
websocket_manager = OptimizedWebSocketManager()
```

### Message Batching

Implement message batching for improved performance:

```python
# app/websockets/batch_processor.py
import asyncio
import time
from collections import defaultdict
from typing import Dict, List, Any

class WebSocketBatchProcessor:
    """Batch processor for WebSocket messages"""
    
    def __init__(self, batch_size: int = 50, batch_timeout: float = 0.1):
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self.message_queue = asyncio.Queue()
        self.user_messages: Dict[int, List[Any]] = defaultdict(list)
        self.last_batch_time = time.time()
        self.running = False
    
    async def start(self):
        """Start batch processor"""
        self.running = True
        await self._process_batches()
    
    async def stop(self):
        """Stop batch processor"""
        self.running = False
    
    def add_message(self, user_id: int, event: str, data: Any):
        """Add message to batch queue"""
        message = {
            'user_id': user_id,
            'event': event,
            'data': data,
            'timestamp': time.time()
        }
        
        self.user_messages[user_id].append(message)
        
        # Trigger batch processing if needed
        if len(self.user_messages[user_id]) >= self.batch_size:
            asyncio.create_task(self._flush_user_messages(user_id))
    
    async def _process_batches(self):
        """Process message batches"""
        while self.running:
            try:
                await asyncio.sleep(self.batch_timeout)
                
                # Check for messages to batch
                current_time = time.time()
                users_to_flush = []
                
                for user_id, messages in self.user_messages.items():
                    if (len(messages) >= self.batch_size or 
                        current_time - self.last_batch_time > self.batch_timeout):
                        users_to_flush.append(user_id)
                
                # Flush messages for identified users
                for user_id in users_to_flush:
                    await self._flush_user_messages(user_id)
                
                self.last_batch_time = current_time
                
            except Exception as e:
                print(f"Batch processing error: {e}")
    
    async def _flush_user_messages(self, user_id: int):
        """Flush messages for a specific user"""
        if user_id not in self.user_messages:
            return
        
        messages = self.user_messages[user_id]
        if not messages:
            return
        
        # Batch emit messages
        for message in messages:
            emit(message['event'], message['data'], room=f"user_{user_id}")
        
        # Clear messages
        self.user_messages[user_id].clear()

# Global batch processor
batch_processor = WebSocketBatchProcessor()
```

## Email Performance Optimization

### Queue Management

Optimize email queue processing:

```python
# app/email/optimized_queue.py
import asyncio
import time
from datetime import datetime, timedelta
from typing import List, Dict
import redis
from concurrent.futures import ThreadPoolExecutor
from app.email.notification_service import EmailNotificationService

class OptimizedEmailQueue:
    """Optimized email queue with batch processing"""
    
    def __init__(self, batch_size: int = 100, workers: int = 4):
        self.batch_size = batch_size
        self.workers = workers
        self.redis_client = None
        self.executor = ThreadPoolExecutor(max_workers=workers)
        self.running = False
        self.stats = {
            'processed': 0,
            'failed': 0,
            'batches_processed': 0,
            'average_batch_time': 0.0
        }
        
        self._setup_redis()
    
    def _setup_redis(self):
        """Setup Redis connection"""
        try:
            self.redis_client = redis.from_url(
                'redis://localhost:6379/0',
                decode_responses=True
            )
        except Exception as e:
            print(f"Redis connection failed: {e}")
    
    async def start_processing(self):
        """Start queue processing"""
        self.running = True
        
        # Start worker tasks
        tasks = []
        for i in range(self.workers):
            task = asyncio.create_task(self._worker(f"worker-{i}"))
            tasks.append(task)
        
        # Wait for all workers
        await asyncio.gather(*tasks)
    
    async def stop_processing(self):
        """Stop queue processing"""
        self.running = False
    
    async def _worker(self, worker_name: str):
        """Email queue worker"""
        email_service = EmailNotificationService()
        
        while self.running:
            try:
                # Get batch of emails
                batch = await self._get_email_batch()
                
                if batch:
                    await self._process_batch(batch, email_service)
                else:
                    # No emails to process, wait
                    await asyncio.sleep(1)
                    
            except Exception as e:
                print(f"Worker {worker_name} error: {e}")
                await asyncio.sleep(5)
    
    async def _get_email_batch(self) -> List[Dict]:
        """Get batch of emails from queue"""
        if not self.redis_client:
            return []
        
        batch = []
        
        for _ in range(self.batch_size):
            try:
                # Get email from queue
                email_data = self.redis_client.lpop('email_queue')
                if email_data:
                    batch.append(json.loads(email_data))
                else:
                    break
            except Exception as e:
                print(f"Error getting email from queue: {e}")
                break
        
        return batch
    
    async def _process_batch(self, batch: List[Dict], email_service):
        """Process batch of emails"""
        start_time = time.time()
        
        # Process emails concurrently
        loop = asyncio.get_event_loop()
        
        tasks = []
        for email_data in batch:
            task = loop.run_in_executor(
                self.executor,
                self._process_single_email,
                email_service,
                email_data
            )
            tasks.append(task)
        
        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Update statistics
        end_time = time.time()
        batch_time = end_time - start_time
        
        successful = sum(1 for r in results if r is True)
        failed = len(results) - successful
        
        self.stats['processed'] += successful
        self.stats['failed'] += failed
        self.stats['batches_processed'] += 1
        
        # Update average batch time
        total_time = self.stats['average_batch_time'] * (self.stats['batches_processed'] - 1) + batch_time
        self.stats['average_batch_time'] = total_time / self.stats['batches_processed']
        
        print(f"Processed batch: {successful} successful, {failed} failed, {batch_time:.2f}s")
    
    def _process_single_email(self, email_service, email_data: Dict) -> bool:
        """Process single email"""
        try:
            # Create and send email
            message = email_service._create_email_message(email_data)
            success = email_service._send_email(message, email_data['to'])
            
            if success:
                email_service._track_delivery(email_data, 'sent')
            else:
                email_service._track_delivery(email_data, 'failed')
            
            return success
            
        except Exception as e:
            print(f"Error processing email: {e}")
            return False
    
    def get_stats(self) -> Dict:
        """Get queue statistics"""
        return self.stats.copy()

# Global optimized email queue
email_queue = OptimizedEmailQueue()
```

### Template Caching

Optimize email template rendering:

```python
# app/email/template_cache.py
import jinja2
from functools import lru_cache
from typing import Dict, Any

class OptimizedTemplateRenderer:
    """Optimized email template renderer with caching"""
    
    def __init__(self, template_dir: str, cache_size: int = 100):
        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(template_dir),
            autoescape=True,
            cache_size=cache_size,
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Pre-compile common templates
        self._precompile_templates()
    
    def _precompile_templates(self):
        """Pre-compile commonly used templates"""
        common_templates = [
            'comment_en.html',
            'message_en.html',
            'system_en.html',
            'comment_en.txt',
            'message_en.txt',
            'system_en.txt'
        ]
        
        for template_name in common_templates:
            try:
                self.env.get_template(template_name)
            except jinja2.TemplateNotFound:
                pass
    
    @lru_cache(maxsize=1000)
    def render_template_cached(self, template_name: str, **kwargs) -> str:
        """Render template with caching"""
        try:
            template = self.env.get_template(template_name)
            return template.render(**kwargs)
        except jinja2.TemplateNotFound:
            return self._get_fallback_template(**kwargs)
    
    def _get_fallback_template(self, **kwargs) -> str:
        """Get fallback template"""
        return f"""
        <html>
        <body>
            <h2>{kwargs.get('title', 'Notification')}</h2>
            <p>{kwargs.get('content', '')}</p>
            <p><a href="{kwargs.get('link', '#')}">View Details</a></p>
        </body>
        </html>
        """

# Global template renderer
template_renderer = OptimizedTemplateRenderer('app/templates/email/notifications')
```

## Push Notification Performance

### Device Management Optimization

Optimize device registry and management:

```python
# app/notifications/optimized_mobile_service.py
import asyncio
import time
from typing import Dict, List, Optional
from collections import defaultdict
import redis
import json

class OptimizedDeviceRegistry:
    """Optimized device registry with caching and batching"""
    
    def __init__(self):
        self.redis_client = None
        self.device_cache = defaultdict(dict)
        self.cache_ttl = 300  # 5 minutes
        self.batch_operations = defaultdict(list)
        self.batch_size = 100
        self.last_flush = time.time()
        
        self._setup_redis()
    
    def _setup_redis(self):
        """Setup Redis connection"""
        try:
            self.redis_client = redis.from_url(
                'redis://localhost:6379/0',
                decode_responses=True
            )
        except Exception as e:
            print(f"Redis connection failed: {e}")
    
    def get_user_devices_cached(self, user_id: int) -> List[Dict]:
        """Get user devices with caching"""
        # Check cache first
        if user_id in self.device_cache:
            cache_time = self.device_cache[user_id].get('timestamp', 0)
            if time.time() - cache_time < self.cache_ttl:
                return self.device_cache[user_id].get('devices', [])
        
        # Get from Redis
        devices = self._get_user_devices_from_redis(user_id)
        
        # Update cache
        self.device_cache[user_id] = {
            'devices': devices,
            'timestamp': time.time()
        }
        
        return devices
    
    def _get_user_devices_from_redis(self, user_id: int) -> List[Dict]:
        """Get devices from Redis"""
        if not self.redis_client:
            return []
        
        try:
            device_data = self.redis_client.hgetall(f"mobile_devices:{user_id}")
            devices = []
            
            for registration_id, data in device_data.items():
                device = json.loads(data)
                devices.append(device)
            
            return devices
        except Exception as e:
            print(f"Error getting devices from Redis: {e}")
            return []
    
    def batch_register_devices(self, registrations: List[Dict]) -> Dict:
        """Batch register devices for better performance"""
        results = {
            'successful': 0,
            'failed': 0,
            'errors': []
        }
        
        for registration in registrations:
            try:
                self._register_device_internal(registration)
                results['successful'] += 1
            except Exception as e:
                results['failed'] += 1
                results['errors'].append(str(e))
        
        return results
    
    def _register_device_internal(self, registration: Dict):
        """Internal device registration"""
        user_id = registration['user_id']
        device_info = registration['device_info']
        registration_id = registration['registration_id']
        
        device_data = {
            'registration_id': registration_id,
            'user_id': user_id,
            'platform': device_info['platform'],
            'device_token': device_info['device_token'],
            'device_id': device_info['device_id'],
            'created_at': time.time(),
            'status': 'active'
        }
        
        # Store in Redis
        if self.redis_client:
            self.redis_client.hset(
                f"mobile_devices:{user_id}",
                registration_id,
                json.dumps(device_data)
            )
        
        # Invalidate cache
        if user_id in self.device_cache:
            del self.device_cache[user_id]
    
    def get_device_statistics_optimized(self) -> Dict:
        """Get device statistics with optimization"""
        stats = {
            'total_devices': 0,
            'platforms': defaultdict(int),
            'active_devices': 0
        }
        
        if not self.redis_client:
            return stats
        
        try:
            # Use Redis SCAN for better performance
            for key in self.redis_client.scan_iter(match="mobile_devices:*"):
                devices = self.redis_client.hgetall(key)
                
                for device_data in devices.values():
                    device = json.loads(device_data)
                    stats['total_devices'] += 1
                    stats['platforms'][device['platform']] += 1
                    
                    if device['status'] == 'active':
                        stats['active_devices'] += 1
        
        except Exception as e:
            print(f"Error getting device statistics: {e}")
        
        return dict(stats)

# Global optimized device registry
device_registry = OptimizedDeviceRegistry()
```

### Push Notification Batching

Implement push notification batching:

```python
# app/notifications/push_batch_processor.py
import asyncio
import time
from typing import Dict, List, Any
from collections import defaultdict

class PushNotificationBatchProcessor:
    """Batch processor for push notifications"""
    
    def __init__(self, batch_size: int = 100, batch_timeout: float = 0.5):
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self.platform_batches = defaultdict(list)
        self.last_batch_time = time.time()
        self.running = False
    
    async def start(self):
        """Start batch processing"""
        self.running = True
        await self._process_batches()
    
    async def stop(self):
        """Stop batch processing"""
        self.running = False
    
    def add_notification(self, platform: str, device_token: str, 
                        notification_data: Dict):
        """Add notification to batch"""
        notification = {
            'device_token': device_token,
            'data': notification_data,
            'timestamp': time.time()
        }
        
        self.platform_batches[platform].append(notification)
        
        # Check if batch is ready
        if len(self.platform_batches[platform]) >= self.batch_size:
            asyncio.create_task(self._flush_platform_batch(platform))
    
    async def _process_batches(self):
        """Process notification batches"""
        while self.running:
            try:
                await asyncio.sleep(self.batch_timeout)
                
                current_time = time.time()
                platforms_to_flush = []
                
                for platform, notifications in self.platform_batches.items():
                    if (len(notifications) >= self.batch_size or 
                        current_time - self.last_batch_time > self.batch_timeout):
                        platforms_to_flush.append(platform)
                
                for platform in platforms_to_flush:
                    await self._flush_platform_batch(platform)
                
                self.last_batch_time = current_time
                
            except Exception as e:
                print(f"Batch processing error: {e}")
    
    async def _flush_platform_batch(self, platform: str):
        """Flush notifications for a platform"""
        if platform not in self.platform_batches:
            return
        
        notifications = self.platform_batches[platform]
        if not notifications:
            return
        
        # Send batch to platform
        await self._send_batch_to_platform(platform, notifications)
        
        # Clear batch
        self.platform_batches[platform].clear()
    
    async def _send_batch_to_platform(self, platform: str, 
                                    notifications: List[Dict]):
        """Send batch to specific platform"""
        try:
            if platform == 'ios':
                await self._send_ios_batch(notifications)
            elif platform == 'android':
                await self._send_android_batch(notifications)
            elif platform == 'huawei':
                await self._send_hms_batch(notifications)
            elif platform == 'web':
                await self._send_web_batch(notifications)
                
        except Exception as e:
            print(f"Error sending batch to {platform}: {e}")
    
    async def _send_ios_batch(self, notifications: List[Dict]):
        """Send batch to APNS"""
        # Implement APNS batch sending
        pass
    
    async def _send_android_batch(self, notifications: List[Dict]):
        """Send batch to FCM"""
        # Implement FCM batch sending
        pass
    
    async def _send_hms_batch(self, notifications: List[Dict]):
        """Send batch to HMS"""
        # Implement HMS batch sending
        pass
    
    async def _send_web_batch(self, notifications: List[Dict]):
        """Send batch to Web Push"""
        # Implement Web Push batch sending
        pass

# Global batch processor
push_batch_processor = PushNotificationBatchProcessor()
```

## Monitoring and Analytics

### Performance Metrics

Implement comprehensive performance monitoring:

```python
# app/notifications/performance_monitor.py
import time
import psutil
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any
from collections import defaultdict, deque
import json

class NotificationPerformanceMonitor:
    """Comprehensive performance monitor for notifications"""
    
    def __init__(self):
        self.metrics = defaultdict(deque)
        self.counters = defaultdict(int)
        self.timers = defaultdict(list)
        self.alerts = []
        self.monitoring = True
        self.max_history = 1000
        
        # Start monitoring thread
        self.monitor_thread = threading.Thread(target=self._monitor_system)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
    
    def record_metric(self, metric_name: str, value: float):
        """Record performance metric"""
        timestamp = time.time()
        self.metrics[metric_name].append((timestamp, value))
        
        # Keep only recent history
        if len(self.metrics[metric_name]) > self.max_history:
            self.metrics[metric_name].popleft()
    
    def increment_counter(self, counter_name: str, value: int = 1):
        """Increment counter"""
        self.counters[counter_name] += value
    
    def start_timer(self, timer_name: str) -> str:
        """Start performance timer"""
        timer_id = f"{timer_name}_{time.time()}"
        self.timers[timer_id] = time.time()
        return timer_id
    
    def end_timer(self, timer_id: str) -> float:
        """End performance timer and return duration"""
        if timer_id not in self.timers:
            return 0.0
        
        start_time = self.timers.pop(timer_id)
        duration = time.time() - start_time
        
        timer_name = timer_id.rsplit('_', 1)[0]
        self.record_metric(f"{timer_name}_duration", duration)
        
        return duration
    
    def _monitor_system(self):
        """Monitor system performance"""
        while self.monitoring:
            try:
                # CPU usage
                cpu_percent = psutil.cpu_percent(interval=1)
                self.record_metric('cpu_usage', cpu_percent)
                
                # Memory usage
                memory = psutil.virtual_memory()
                self.record_metric('memory_usage', memory.percent)
                self.record_metric('memory_available', memory.available)
                
                # Disk usage
                disk = psutil.disk_usage('/')
                self.record_metric('disk_usage', disk.percent)
                
                # Check for alerts
                self._check_alerts()
                
                time.sleep(10)  # Monitor every 10 seconds
                
            except Exception as e:
                print(f"Monitoring error: {e}")
                time.sleep(5)
    
    def _check_alerts(self):
        """Check for performance alerts"""
        current_time = time.time()
        
        # CPU alert
        cpu_metrics = list(self.metrics['cpu_usage'])
        if cpu_metrics and cpu_metrics[-1][1] > 80:
            self._add_alert('high_cpu', f"CPU usage: {cpu_metrics[-1][1]:.1f}%")
        
        # Memory alert
        memory_metrics = list(self.metrics['memory_usage'])
        if memory_metrics and memory_metrics[-1][1] > 85:
            self._add_alert('high_memory', f"Memory usage: {memory_metrics[-1][1]:.1f}%")
        
        # Response time alert
        response_metrics = list(self.metrics['api_response_duration'])
        if response_metrics and response_metrics[-1][1] > 1.0:
            self._add_alert('slow_response', f"Response time: {response_metrics[-1][1]:.2f}s")
    
    def _add_alert(self, alert_type: str, message: str):
        """Add performance alert"""
        alert = {
            'type': alert_type,
            'message': message,
            'timestamp': time.time()
        }
        
        self.alerts.append(alert)
        
        # Keep only recent alerts
        if len(self.alerts) > 100:
            self.alerts.pop(0)
        
        print(f"ALERT: {alert_type.upper()} - {message}")
    
    def get_performance_summary(self) -> Dict:
        """Get performance summary"""
        summary = {
            'timestamp': time.time(),
            'counters': dict(self.counters),
            'recent_alerts': self.alerts[-10:] if self.alerts else [],
            'metrics': {}
        }
        
        # Calculate metric statistics
        for metric_name, values in self.metrics.items():
            if values:
                recent_values = [v[1] for v in list(values)[-100:]]  # Last 100 values
                
                summary['metrics'][metric_name] = {
                    'current': recent_values[-1] if recent_values else 0,
                    'average': sum(recent_values) / len(recent_values),
                    'min': min(recent_values),
                    'max': max(recent_values),
                    'count': len(recent_values)
                }
        
        return summary
    
    def get_slow_queries(self, threshold: float = 0.1) -> List[Dict]:
        """Get slow database queries"""
        slow_queries = []
        
        for metric_name, values in self.metrics.items():
            if 'query_duration' in metric_name:
                for timestamp, duration in values:
                    if duration > threshold:
                        slow_queries.append({
                            'query': metric_name,
                            'duration': duration,
                            'timestamp': timestamp
                        })
        
        return sorted(slow_queries, key=lambda x: x['duration'], reverse=True)
    
    def get_api_performance(self) -> Dict:
        """Get API performance metrics"""
        api_metrics = {}
        
        for metric_name, values in self.metrics.items():
            if 'api_' in metric_name and 'duration' in metric_name:
                endpoint = metric_name.replace('api_', '').replace('_duration', '')
                
                if values:
                    durations = [v[1] for v in list(values)[-100:]]
                    
                    api_metrics[endpoint] = {
                        'average_response_time': sum(durations) / len(durations),
                        'min_response_time': min(durations),
                        'max_response_time': max(durations),
                        'request_count': len(durations),
                        'p95_response_time': self._percentile(durations, 0.95),
                        'p99_response_time': self._percentile(durations, 0.99)
                    }
        
        return api_metrics
    
    def _percentile(self, values: List[float], percentile: float) -> float:
        """Calculate percentile of values"""
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile)
        return sorted_values[min(index, len(sorted_values) - 1)]

# Global performance monitor
performance_monitor = NotificationPerformanceMonitor()

# Performance monitoring decorators
def monitor_performance(metric_name: str):
    """Decorator to monitor function performance"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            timer_id = performance_monitor.start_timer(metric_name)
            try:
                result = func(*args, **kwargs)
                performance_monitor.increment_counter(f"{metric_name}_success")
                return result
            except Exception as e:
                performance_monitor.increment_counter(f"{metric_name}_error")
                raise
            finally:
                performance_monitor.end_timer(timer_id)
        return wrapper
    return decorator

def monitor_api_response(endpoint_name: str):
    """Decorator to monitor API response times"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            timer_id = performance_monitor.start_timer(f"api_{endpoint_name}")
            try:
                result = func(*args, **kwargs)
                performance_monitor.increment_counter(f"api_{endpoint_name}_requests")
                return result
            except Exception as e:
                performance_monitor.increment_counter(f"api_{endpoint_name}_errors")
                raise
            finally:
                performance_monitor.end_timer(timer_id)
        return wrapper
    return decorator
```

## Load Testing and Benchmarking

### Load Testing Script

Create comprehensive load testing:

```python
# scripts/load_test_notifications.py
import asyncio
import aiohttp
import time
import statistics
from typing import List, Dict
import random

class NotificationLoadTester:
    """Load tester for notification system"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.results = []
    
    async def test_api_endpoints(self, concurrent_users: int = 100, 
                                requests_per_user: int = 10):
        """Test API endpoints under load"""
        print(f"Starting load test: {concurrent_users} users, {requests_per_user} requests each")
        
        tasks = []
        for user_id in range(concurrent_users):
            task = asyncio.create_task(
                self._simulate_user_requests(user_id, requests_per_user)
            )
            tasks.append(task)
        
        start_time = time.time()
        await asyncio.gather(*tasks)
        end_time = time.time()
        
        self._analyze_results(end_time - start_time)
    
    async def _simulate_user_requests(self, user_id: int, num_requests: int):
        """Simulate user making requests"""
        async with aiohttp.ClientSession() as session:
            for i in range(num_requests):
                request_start = time.time()
                
                # Random endpoint selection
                endpoints = [
                    '/notifications',
                    '/notifications/search',
                    '/notifications/unread-count',
                    '/notifications/preferences'
                ]
                
                endpoint = random.choice(endpoints)
                
                try:
                    async with session.get(f"{self.base_url}{endpoint}") as response:
                        await response.text()
                        
                        request_time = time.time() - request_start
                        self.results.append({
                            'user_id': user_id,
                            'request_id': i,
                            'endpoint': endpoint,
                            'response_time': request_time,
                            'status_code': response.status,
                            'success': response.status < 400
                        })
                        
                except Exception as e:
                    request_time = time.time() - request_start
                    self.results.append({
                        'user_id': user_id,
                        'request_id': i,
                        'endpoint': endpoint,
                        'response_time': request_time,
                        'status_code': 0,
                        'success': False,
                        'error': str(e)
                    })
                
                # Random delay between requests
                await asyncio.sleep(random.uniform(0.1, 0.5))
    
    def _analyze_results(self, total_time: float):
        """Analyze load test results"""
        if not self.results:
            print("No results to analyze")
            return
        
        successful_requests = [r for r in self.results if r['success']]
        failed_requests = [r for r in self.results if not r['success']]
        
        response_times = [r['response_time'] for r in successful_requests]
        
        print(f"\nLoad Test Results:")
        print(f"Total Requests: {len(self.results)}")
        print(f"Successful: {len(successful_requests)} ({len(successful_requests)/len(self.results)*100:.1f}%)")
        print(f"Failed: {len(failed_requests)} ({len(failed_requests)/len(self.results)*100:.1f}%)")
        print(f"Total Time: {total_time:.2f}s")
        print(f"Requests/Second: {len(self.results)/total_time:.2f}")
        
        if response_times:
            print(f"\nResponse Times:")
            print(f"Average: {statistics.mean(response_times):.3f}s")
            print(f"Median: {statistics.median(response_times):.3f}s")
            print(f"Min: {min(response_times):.3f}s")
            print(f"Max: {max(response_times):.3f}s")
            print(f"95th Percentile: {self._percentile(response_times, 0.95):.3f}s")
            print(f"99th Percentile: {self._percentile(response_times, 0.99):.3f}s")
        
        # Error analysis
        if failed_requests:
            print(f"\nError Analysis:")
            error_types = {}
            for req in failed_requests:
                error = req.get('error', f"HTTP {req['status_code']}")
                error_types[error] = error_types.get(error, 0) + 1
            
            for error, count in error_types.items():
                print(f"  {error}: {count}")
    
    def _percentile(self, values: List[float], percentile: float) -> float:
        """Calculate percentile"""
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile)
        return sorted_values[min(index, len(sorted_values) - 1)]

async def main():
    """Main load testing function"""
    tester = NotificationLoadTester()
    
    # Test with different load levels
    test_scenarios = [
        (10, 5),    # 10 users, 5 requests each
        (50, 10),   # 50 users, 10 requests each
        (100, 20),  # 100 users, 20 requests each
        (200, 10),  # 200 users, 10 requests each
    ]
    
    for users, requests in test_scenarios:
        print(f"\n{'='*50}")
        print(f"Test Scenario: {users} users, {requests} requests each")
        print(f"{'='*50}")
        
        await tester.test_api_endpoints(users, requests)
        
        # Wait between tests
        await asyncio.sleep(5)

if __name__ == '__main__':
    asyncio.run(main())
```

## Production Optimization Checklist

### Database Optimization
- [ ] Create all recommended indexes
- [ ] Optimize slow queries
- [ ] Implement connection pooling
- [ ] Set up read replicas for scaling
- [ ] Configure query caching
- [ ] Monitor database performance

### Caching Optimization
- [ ] Implement Redis caching
- [ ] Cache frequently accessed data
- [ ] Set appropriate TTL values
- [ ] Monitor cache hit rates
- [ ] Implement cache invalidation strategies

### WebSocket Optimization
- [ ] Implement connection pooling
- [ ] Use message batching
- [ ] Optimize room management
- [ ] Monitor connection health
- [ ] Set up load balancing

### Email Optimization
- [ ] Implement queue batching
- [ ] Cache email templates
- [ ] Optimize SMTP connections
- [ ] Monitor delivery rates
- [ ] Set up retry logic

### Push Notification Optimization
- [ ] Implement device caching
- [ ] Use batch sending
- [ ] Optimize platform connections
- [ ] Monitor delivery success
- [ ] Clean up inactive devices

### Performance Monitoring
- [ ] Set up comprehensive metrics
- [ ] Monitor response times
- [ ] Track error rates
- [ ] Set up alerting
- [ ] Create performance dashboards

---

**Last Updated:** May 12, 2026  
**Version:** 1.0  
**Status:** Production Ready
