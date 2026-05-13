"""
Stream Subscriptions

Manages stream subscriptions and subscriber preferences.
"""

import logging
from typing import Dict, List, Any, Optional, Set
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
import json

logger = logging.getLogger(__name__)

class SubscriptionStatus(Enum):
    """Subscription status"""
    ACTIVE = "active"
    PAUSED = "paused"
    EXPIRED = "expired"
    CANCELLED = "cancelled"

class SubscriptionType(Enum):
    """Subscription types"""
    REAL_TIME = "real_time"
    BATCH = "batch"
    DIGEST = "digest"

@dataclass
class SubscriptionConfig:
    """Subscription configuration"""
    stream_id: str
    subscription_type: SubscriptionType
    filters: Dict[str, Any] = field(default_factory=dict)
    delivery_method: str = "websocket"  # websocket, email, webhook
    delivery_frequency: int = 1  # seconds
    max_events_per_hour: int = 1000
    auto_renew: bool = True
    expires_at: Optional[datetime] = None

@dataclass
class Subscription:
    """Stream subscription"""
    
    def __init__(self, user_id: int, config: SubscriptionConfig):
        self.subscription_id = str(uuid.uuid4())
        self.user_id = user_id
        self.config = config
        self.status = SubscriptionStatus.ACTIVE
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.last_event_at = None
        self.event_count = 0
        self.error_count = 0
        self.delivery_count = 0
        self.preferences = {
            'include_metadata': True,
            'compress_data': False,
            'retry_failed': True,
            'max_retries': 3
        }
    
    def update_activity(self):
        """Update subscription activity"""
        self.updated_at = datetime.utcnow()
        self.event_count += 1
    
    def increment_delivery(self):
        """Increment delivery count"""
        self.delivery_count += 1
    
    def increment_error(self):
        """Increment error count"""
        self.error_count += 1
    
    def is_expired(self) -> bool:
        """Check if subscription is expired"""
        if self.config.expires_at:
            return datetime.utcnow() > self.config.expires_at
        return False
    
    def is_rate_limited(self) -> bool:
        """Check if subscription is rate limited"""
        if self.config.max_events_per_hour:
            # Simple rate limiting check
            one_hour_ago = datetime.utcnow() - timedelta(hours=1)
            recent_events = self.event_count  # This would be tracked more accurately
            return recent_events >= self.config.max_events_per_hour
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert subscription to dictionary"""
        return {
            'subscription_id': self.subscription_id,
            'user_id': self.user_id,
            'stream_id': self.config.stream_id,
            'subscription_type': self.config.subscription_type.value,
            'status': self.status.value,
            'filters': self.config.filters,
            'delivery_method': self.config.delivery_method,
            'delivery_frequency': self.config.delivery_frequency,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'last_event_at': self.last_event_at.isoformat() if self.last_event_at else None,
            'event_count': self.event_count,
            'error_count': self.error_count,
            'delivery_count': self.delivery_count,
            'preferences': self.preferences,
            'expires_at': self.config.expires_at.isoformat() if self.config.expires_at else None
        }

class StreamSubscriptionManager:
    """Manages stream subscriptions"""
    
    def __init__(self, stream_manager):
        self.stream_manager = stream_manager
        self.subscriptions: Dict[str, Subscription] = {}
        self.user_subscriptions: Dict[int, Set[str]] = {}
        self.stream_subscriptions: Dict[str, Set[str]] = {}
        self.subscription_stats = {
            'total_subscriptions': 0,
            'active_subscriptions': 0,
            'expired_subscriptions': 0,
            'total_events': 0,
            'total_deliveries': 0,
            'total_errors': 0
        }
        self._start_cleanup_tasks()
    
    def create_subscription(self, user_id: int, config: SubscriptionConfig) -> str:
        """Create a new subscription"""
        subscription = Subscription(user_id, config)
        self.subscriptions[subscription.subscription_id] = subscription
        
        # Update user subscriptions mapping
        if user_id not in self.user_subscriptions:
            self.user_subscriptions[user_id] = set()
        self.user_subscriptions[user_id].add(subscription.subscription_id)
        
        # Update stream subscriptions mapping
        if config.stream_id not in self.stream_subscriptions:
            self.stream_subscriptions[config.stream_id] = set()
        self.stream_subscriptions[config.stream_id].add(subscription.subscription_id)
        
        # Update stats
        self.subscription_stats['total_subscriptions'] += 1
        self.subscription_stats['active_subscriptions'] += 1
        
        logger.info(f"Created subscription {subscription.subscription_id} for user {user_id}")
        return subscription.subscription_id
    
    def get_subscription(self, subscription_id: str) -> Optional[Subscription]:
        """Get subscription by ID"""
        return self.subscriptions.get(subscription_id)
    
    def get_user_subscriptions(self, user_id: int) -> List[Subscription]:
        """Get all subscriptions for a user"""
        if user_id not in self.user_subscriptions:
            return []
        
        subscription_ids = self.user_subscriptions[user_id]
        return [
            self.subscriptions[sub_id]
            for sub_id in subscription_ids
            if sub_id in self.subscriptions
        ]
    
    def get_stream_subscriptions(self, stream_id: str) -> List[Subscription]:
        """Get all subscriptions for a stream"""
        if stream_id not in self.stream_subscriptions:
            return []
        
        subscription_ids = self.stream_subscriptions[stream_id]
        return [
            self.subscriptions[sub_id]
            for sub_id in subscription_ids
            if sub_id in self.subscriptions
        ]
    
    def cancel_subscription(self, subscription_id: str) -> bool:
        """Cancel a subscription"""
        subscription = self.get_subscription(subscription_id)
        if not subscription:
            return False
        
        subscription.status = SubscriptionStatus.CANCELLED
        
        # Remove from mappings
        if subscription.user_id in self.user_subscriptions:
            self.user_subscriptions[subscription.user_id].discard(subscription_id)
            if not self.user_subscriptions[subscription.user_id]:
                del self.user_subscriptions[subscription.user_id]
        
        if subscription.config.stream_id in self.stream_subscriptions:
            self.stream_subscriptions[subscription.config.stream_id].discard(subscription_id)
            if not self.stream_subscriptions[subscription.config.stream_id]:
                del self.stream_subscriptions[subscription.config.stream_id]
        
        # Update stats
        self.subscription_stats['active_subscriptions'] -= 1
        
        logger.info(f"Cancelled subscription {subscription_id}")
        return True
    
    def pause_subscription(self, subscription_id: str) -> bool:
        """Pause a subscription"""
        subscription = self.get_subscription(subscription_id)
        if not subscription:
            return False
        
        subscription.status = SubscriptionStatus.PAUSED
        logger.info(f"Paused subscription {subscription_id}")
        return True
    
    def resume_subscription(self, subscription_id: str) -> bool:
        """Resume a subscription"""
        subscription = self.get_subscription(subscription_id)
        if not subscription:
            return False
        
        if subscription.status == SubscriptionStatus.CANCELLED:
            return False
        
        if subscription.status == SubscriptionStatus.EXPIRED:
            return False
        
        subscription.status = SubscriptionStatus.ACTIVE
        logger.info(f"Resumed subscription {subscription_id}")
        return True
    
    def deliver_to_subscription(self, subscription_id: str, data: Any, 
                             event_type: str = "update") -> bool:
        """Deliver data to a specific subscription"""
        subscription = self.get_subscription(subscription_id)
        if not subscription:
            return False
        
        # Check subscription status
        if subscription.status != SubscriptionStatus.ACTIVE:
            return False
        
        # Check if subscription is expired
        if subscription.is_expired():
            subscription.status = SubscriptionStatus.EXPIRED
            self.subscription_stats['active_subscriptions'] -= 1
            self.subscription_stats['expired_subscriptions'] += 1
            return False
        
        # Check rate limiting
        if subscription.is_rate_limited():
            return False
        
        # Apply filters
        if subscription.config.filters:
            if not self._passes_filters(data, subscription.config.filters):
                return False
        
        # Update activity
        subscription.update_activity()
        subscription.last_event_at = datetime.utcnow()
        
        # Deliver based on delivery method
        success = self._deliver_data(subscription, data, event_type)
        
        if success:
            subscription.increment_delivery()
            self.subscription_stats['total_deliveries'] += 1
        else:
            subscription.increment_error()
            self.subscription_stats['total_errors'] += 1
        
        self.subscription_stats['total_events'] += 1
        return success
    
    def deliver_to_stream(self, stream_id: str, data: Any, 
                         event_type: str = "update") -> int:
        """Deliver data to all subscriptions of a stream"""
        subscriptions = self.get_stream_subscriptions(stream_id)
        delivered_count = 0
        
        for subscription in subscriptions:
            if self.deliver_to_subscription(subscription.subscription_id, data, event_type):
                delivered_count += 1
        
        return delivered_count
    
    def deliver_to_user(self, user_id: int, data: Any, event_type: str = "update") -> int:
        """Deliver data to all subscriptions of a user"""
        subscriptions = self.get_user_subscriptions(user_id)
        delivered_count = 0
        
        for subscription in subscriptions:
            if self.deliver_to_subscription(subscription.subscription_id, data, event_type):
                delivered_count += 1
        
        return delivered_count
    
    def _passes_filters(self, data: Any, filters: Dict[str, Any]) -> bool:
        """Check if data passes filters"""
        # Simple filter implementation
        for filter_key, filter_value in filters.items():
            if isinstance(data, dict) and filter_key in data:
                if data[filter_key] != filter_value:
                    return False
        return True
    
    def _deliver_data(self, subscription: Subscription, data: Any, 
                      event_type: str) -> bool:
        """Deliver data based on subscription preferences"""
        try:
            # Apply preferences
            processed_data = data
            if subscription.preferences.get('compress_data', False):
                # Compress data (simplified)
                processed_data = {'compressed': True, 'data': str(data)[:100]}
            
            if subscription.preferences.get('include_metadata', True):
                processed_data = {
                    'data': processed_data,
                    'metadata': {
                        'subscription_id': subscription.subscription_id,
                        'event_type': event_type,
                        'timestamp': datetime.utcnow().isoformat()
                    }
                }
            
            # Deliver based on method
            if subscription.config.delivery_method == 'websocket':
                # WebSocket delivery would be handled by WebSocket handlers
                return True
            elif subscription.config.delivery_method == 'email':
                # Email delivery (placeholder)
                return self._deliver_via_email(subscription, processed_data)
            elif subscription.config.delivery_method == 'webhook':
                # Webhook delivery (placeholder)
                return self._deliver_via_webhook(subscription, processed_data)
            else:
                logger.warning(f"Unknown delivery method: {subscription.config.delivery_method}")
                return False
        
        except Exception as e:
            logger.error(f"Error delivering data for subscription {subscription.subscription_id}: {e}")
            return False
    
    def _deliver_via_email(self, subscription: Subscription, data: Any) -> bool:
        """Deliver data via email (placeholder)"""
        # This would integrate with email system
        logger.info(f"Email delivery for subscription {subscription.subscription_id}")
        return True
    
    def _deliver_via_webhook(self, subscription: Subscription, data: Any) -> bool:
        """Deliver data via webhook (placeholder)"""
        # This would make HTTP request to webhook URL
        logger.info(f"Webhook delivery for subscription {subscription.subscription_id}")
        return True
    
    def update_subscription(self, subscription_id: str, updates: Dict[str, Any]) -> bool:
        """Update subscription configuration"""
        subscription = self.get_subscription(subscription_id)
        if not subscription:
            return False
        
        # Update allowed fields
        if 'filters' in updates:
            subscription.config.filters.update(updates['filters'])
        
        if 'preferences' in updates:
            subscription.preferences.update(updates['preferences'])
        
        if 'expires_at' in updates:
            subscription.config.expires_at = updates['expires_at']
        
        subscription.updated_at = datetime.utcnow()
        logger.info(f"Updated subscription {subscription_id}")
        return True
    
    def get_subscription_stats(self, subscription_id: str) -> Optional[Dict[str, Any]]:
        """Get subscription statistics"""
        subscription = self.get_subscription(subscription_id)
        if not subscription:
            return None
        
        return {
            'subscription': subscription.to_dict(),
            'delivery_rate': self._calculate_delivery_rate(subscription),
            'error_rate': self._calculate_error_rate(subscription),
            'time_until_expiry': self._calculate_time_until_expiry(subscription)
        }
    
    def _calculate_delivery_rate(self, subscription: Subscription) -> float:
        """Calculate delivery rate for subscription"""
        if subscription.event_count == 0:
            return 0.0
        return subscription.delivery_count / subscription.event_count
    
    def _calculate_error_rate(self, subscription: Subscription) -> float:
        """Calculate error rate for subscription"""
        if subscription.event_count == 0:
            return 0.0
        return subscription.error_count / subscription.event_count
    
    def _calculate_time_until_expiry(self, subscription: Subscription) -> Optional[int]:
        """Calculate time until expiry in hours"""
        if not subscription.config.expires_at:
            return None
        
        time_until = subscription.config.expires_at - datetime.utcnow()
        return max(0, int(time_until.total_seconds() / 3600))
    
    def get_global_stats(self) -> Dict[str, Any]:
        """Get global subscription statistics"""
        # Update current stats
        self.subscription_stats['total_subscriptions'] = len(self.subscriptions)
        self.subscription_stats['active_subscriptions'] = len([
            s for s in self.subscriptions.values()
            if s.status == SubscriptionStatus.ACTIVE
        ])
        self.subscription_stats['expired_subscriptions'] = len([
            s for s in self.subscriptions.values()
            if s.status == SubscriptionStatus.EXPIRED
        ])
        
        return {
            'subscription_stats': self.subscription_stats.copy(),
            'user_count': len(self.user_subscriptions),
            'stream_count': len(self.stream_subscriptions),
            'avg_events_per_subscription': (
                self.subscription_stats['total_events'] / max(1, len(self.subscriptions))
            ),
            'avg_delivery_rate': self._calculate_global_delivery_rate()
        }
    
    def _calculate_global_delivery_rate(self) -> float:
        """Calculate global delivery rate"""
        total_events = self.subscription_stats['total_events']
        total_deliveries = self.subscription_stats['total_deliveries']
        
        if total_events == 0:
            return 0.0
        return total_deliveries / total_events
    
    def cleanup_expired_subscriptions(self) -> int:
        """Clean up expired subscriptions"""
        expired_count = 0
        
        for subscription_id, subscription in list(self.subscriptions.items()):
            if subscription.is_expired():
                self.cancel_subscription(subscription_id)
                expired_count += 1
        
        logger.info(f"Cleaned up {expired_count} expired subscriptions")
        return expired_count
    
    def _start_cleanup_tasks(self):
        """Start background cleanup tasks"""
        def cleanup_task():
            """Background cleanup task"""
            try:
                # Clean up expired subscriptions every hour
                self.cleanup_expired_subscriptions()
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")
        
        # This would be implemented with proper background task scheduling
        logger.info("Background cleanup task started for subscription management")
    
    def create_subscription_from_request(self, user_id: int, request_data: Dict[str, Any]) -> str:
        """Create subscription from request data"""
        # Parse request data
        stream_id = request_data.get('stream_id')
        subscription_type = request_data.get('subscription_type', 'real_time')
        filters = request_data.get('filters', {})
        delivery_method = request_data.get('delivery_method', 'websocket')
        delivery_frequency = request_data.get('delivery_frequency', 1)
        max_events_per_hour = request_data.get('max_events_per_hour', 1000)
        auto_renew = request_data.get('auto_renew', True)
        
        # Parse expires_at
        expires_at = None
        if 'expires_at' in request_data:
            try:
                expires_at = datetime.fromisoformat(request_data['expires_at'])
            except ValueError:
                logger.warning(f"Invalid expires_at format: {request_data['expires_at']}")
        
        # Create config
        config = SubscriptionConfig(
            stream_id=stream_id,
            subscription_type=SubscriptionType(subscription_type),
            filters=filters,
            delivery_method=delivery_method,
            delivery_frequency=delivery_frequency,
            max_events_per_hour=max_events_per_hour,
            auto_renew=auto_renew,
            expires_at=expires_at
        )
        
        # Create subscription
        return self.create_subscription(user_id, config)
