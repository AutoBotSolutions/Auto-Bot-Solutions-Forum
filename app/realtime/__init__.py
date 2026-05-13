"""
Real-time Module

Real-time data management and WebSocket session management for the Auto Bot Solutions Forum.
Provides comprehensive real-time event processing, streaming data handling, and real-time analytics.
"""

from .models import WebSocketSession, RealTimeEvent, StreamData, RealTimeAnalytics
from .service import RealTimeService, get_realtime_service, track_websocket_activity, log_realtime_event, track_analytics_metric
from .utils import (
    EventType, StreamType, SessionStatus, WebSocketMessage, EventQueue, RoomManager,
    ConnectionPool, StreamProcessor, AnalyticsCalculator, EventBroadcaster, WebSocketUtils,
    StreamValidator, room_manager, connection_pool, stream_processor, analytics_calculator,
    event_broadcaster
)
from .config import (
    REALTIME_ENABLED, WEBSOCKET_ENABLED, EVENT_PROCESSING_ENABLED, STREAM_PROCESSING_ENABLED,
    REALTIME_ANALYTICS_ENABLED, WEBSOCKET_CONFIG, SESSION_CONFIG, ROOM_CONFIG,
    EVENT_PROCESSING_CONFIG, STREAM_CONFIG, ANALYTICS_CONFIG, REALTIME_SECURITY_CONFIG,
    PERFORMANCE_CONFIG, MONITORING_CONFIG, INTEGRATION_CONFIG, WEBSOCKET_EVENT_TYPES,
    STREAM_DATA_SCHEMAS, get_realtime_config, validate_realtime_config
)

__all__ = [
    # Models
    'WebSocketSession',
    'RealTimeEvent',
    'StreamData',
    'RealTimeAnalytics',
    
    # Services
    'RealTimeService',
    'get_realtime_service',
    'track_websocket_activity',
    'log_realtime_event',
    'track_analytics_metric',
    
    # Utilities
    'EventType',
    'StreamType',
    'SessionStatus',
    'WebSocketMessage',
    'EventQueue',
    'RoomManager',
    'ConnectionPool',
    'StreamProcessor',
    'AnalyticsCalculator',
    'EventBroadcaster',
    'WebSocketUtils',
    'StreamValidator',
    'room_manager',
    'connection_pool',
    'stream_processor',
    'analytics_calculator',
    'event_broadcaster',
    
    # Configuration
    'REALTIME_ENABLED',
    'WEBSOCKET_ENABLED',
    'EVENT_PROCESSING_ENABLED',
    'STREAM_PROCESSING_ENABLED',
    'REALTIME_ANALYTICS_ENABLED',
    'WEBSOCKET_CONFIG',
    'SESSION_CONFIG',
    'ROOM_CONFIG',
    'EVENT_PROCESSING_CONFIG',
    'STREAM_CONFIG',
    'ANALYTICS_CONFIG',
    'REALTIME_SECURITY_CONFIG',
    'PERFORMANCE_CONFIG',
    'MONITORING_CONFIG',
    'INTEGRATION_CONFIG',
    'WEBSOCKET_EVENT_TYPES',
    'STREAM_DATA_SCHEMAS',
    'get_realtime_config',
    'validate_realtime_config'
]
