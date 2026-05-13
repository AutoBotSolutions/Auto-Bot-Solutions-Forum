"""
Real-time Features WebSocket Module

This module provides WebSocket support for real-time features including:
- Live comment notifications
- Real-time vote count updates
- Online user presence indicators
- Real-time typing indicators
"""

from .service import WebSocketService
from .events import register_socketio_events

__all__ = ['WebSocketService', 'register_socketio_events']
