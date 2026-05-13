"""
Real-time Service

Comprehensive real-time service for WebSocket session management, event processing,
streaming data handling, and real-time analytics for the Auto Bot Solutions Forum.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Callable
from flask import current_app, request
from sqlalchemy import and_, or_, desc, func
from app import db
from app.realtime.models import WebSocketSession, RealTimeEvent, StreamData, RealTimeAnalytics

logger = logging.getLogger(__name__)

class RealTimeService:
    """Comprehensive real-time service for WebSocket and event management"""
    
    def __init__(self):
        self.enabled = current_app.config.get('REALTIME_ENABLED', True)
        self.websocket_enabled = current_app.config.get('WEBSOCKET_ENABLED', True)
        self.event_processing_enabled = current_app.config.get('EVENT_PROCESSING_ENABLED', True)
        self.stream_processing_enabled = current_app.config.get('STREAM_PROCESSING_ENABLED', True)
        self.analytics_enabled = current_app.config.get('REALTIME_ANALYTICS_ENABLED', True)
    
    def create_websocket_session(self, socket_id, user_id=None, room=None, session_type='user',
                                ip_address=None, user_agent=None, country=None, region=None, city=None,
                                device_type=None, browser=None, platform=None, capabilities=None,
                                preferences=None, metadata=None):
        """Create a new WebSocket session"""
        if not self.websocket_enabled:
            return None
        
        try:
            return WebSocketSession.create_session(
                socket_id=socket_id,
                user_id=user_id,
                room=room,
                session_type=session_type,
                ip_address=ip_address,
                user_agent=user_agent,
                country=country,
                region=region,
                city=city,
                device_type=device_type,
                browser=browser,
                platform=platform,
                capabilities=capabilities,
                preferences=preferences,
                metadata=metadata
            )
        except Exception as e:
            logger.error(f"Error creating WebSocket session: {str(e)}")
            return None
    
    def get_websocket_session(self, session_id=None, socket_id=None, user_id=None):
        """Get WebSocket session by ID, socket ID, or user ID"""
        if not self.websocket_enabled:
            return None
        
        try:
            if session_id:
                return WebSocketSession.query.filter_by(session_id=session_id).first()
            elif socket_id:
                return WebSocketSession.get_session_by_socket_id(socket_id)
            elif user_id:
                sessions = WebSocketSession.get_user_sessions(user_id, status='connected')
                return sessions[0] if sessions else None
            return None
        except Exception as e:
            logger.error(f"Error getting WebSocket session: {str(e)}")
            return None
    
    def disconnect_websocket_session(self, session_id=None, socket_id=None, reason='normal'):
        """Disconnect a WebSocket session"""
        if not self.websocket_enabled:
            return None
        
        try:
            session = None
            if session_id:
                session = WebSocketSession.query.filter_by(session_id=session_id).first()
            elif socket_id:
                session = WebSocketSession.get_session_by_socket_id(socket_id)
            
            if session:
                session.disconnect(reason)
                return session
            return None
        except Exception as e:
            logger.error(f"Error disconnecting WebSocket session: {str(e)}")
            return None
    
    def update_session_activity(self, session_id, message_sent=False, message_received=False,
                              bytes_sent=0, bytes_received=0, latency_ms=None):
        """Update WebSocket session activity"""
        if not self.websocket_enabled:
            return None
        
        try:
            session = WebSocketSession.query.filter_by(session_id=session_id).first()
            if session:
                session.update_activity(
                    message_sent=message_sent,
                    message_received=message_received,
                    bytes_sent=bytes_sent,
                    bytes_received=bytes_received,
                    latency_ms=latency_ms
                )
                return session
            return None
        except Exception as e:
            logger.error(f"Error updating session activity: {str(e)}")
            return None
    
    def get_room_sessions(self, room, status='connected'):
        """Get all WebSocket sessions in a room"""
        if not self.websocket_enabled:
            return []
        
        try:
            return WebSocketSession.get_room_sessions(room, status)
        except Exception as e:
            logger.error(f"Error getting room sessions: {str(e)}")
            return []
    
    def create_realtime_event(self, event_type, event_category, source_type, source_id=None,
                             source_name=None, target_type=None, target_id=None, target_room=None,
                             severity='info', title=None, message=None, data=None, metadata=None,
                             tags=None, priority=5, expires_in_hours=None):
        """Create a new real-time event"""
        if not self.event_processing_enabled:
            return None
        
        try:
            return RealTimeEvent.create_event(
                event_type=event_type,
                event_category=event_category,
                source_type=source_type,
                source_id=source_id,
                source_name=source_name,
                target_type=target_type,
                target_id=target_id,
                target_room=target_room,
                severity=severity,
                title=title,
                message=message,
                data=data,
                metadata=metadata,
                tags=tags,
                priority=priority,
                expires_in_hours=expires_in_hours
            )
        except Exception as e:
            logger.error(f"Error creating real-time event: {str(e)}")
            return None
    
    def get_pending_events(self, limit=None):
        """Get pending real-time events for processing"""
        if not self.event_processing_enabled:
            return []
        
        try:
            return RealTimeEvent.get_pending_events(limit)
        except Exception as e:
            logger.error(f"Error getting pending events: {str(e)}")
            return []
    
    def deliver_event(self, event_id, success=True, error_message=None):
        """Mark event as delivered or failed"""
        if not self.event_processing_enabled:
            return None
        
        try:
            event = RealTimeEvent.query.filter_by(event_id=event_id).first()
            if event:
                if success:
                    event.mark_delivered()
                else:
                    event.mark_failed(error_message)
                return event
            return None
        except Exception as e:
            logger.error(f"Error delivering event: {str(e)}")
            return None
    
    def create_stream_data(self, stream_type, stream_category, data, source_id=None, source_type=None,
                           data_format='json', metadata=None, tags=None, schema_version='1.0',
                           processing_priority=5, expires_in_hours=None, quality_score=1.0,
                           completeness_score=1.0, accuracy_score=1.0):
        """Create new streaming data"""
        if not self.stream_processing_enabled:
            return None
        
        try:
            return StreamData.create_stream_data(
                stream_type=stream_type,
                stream_category=stream_category,
                data=data,
                source_id=source_id,
                source_type=source_type,
                data_format=data_format,
                metadata=metadata,
                tags=tags,
                schema_version=schema_version,
                processing_priority=processing_priority,
                expires_in_hours=expires_in_hours,
                quality_score=quality_score,
                completeness_score=completeness_score,
                accuracy_score=accuracy_score
            )
        except Exception as e:
            logger.error(f"Error creating stream data: {str(e)}")
            return None
    
    def get_pending_stream_data(self, limit=None):
        """Get pending stream data for processing"""
        if not self.stream_processing_enabled:
            return []
        
        try:
            return StreamData.get_pending_stream_data(limit)
        except Exception as e:
            logger.error(f"Error getting pending stream data: {str(e)}")
            return []
    
    def process_stream_data(self, stream_id, processing_time_ms=None, memory_usage_mb=None,
                           success=True, error_message=None, error_code=None):
        """Process stream data"""
        if not self.stream_processing_enabled:
            return None
        
        try:
            stream_data = StreamData.query.filter_by(stream_id=stream_id).first()
            if stream_data:
                if success:
                    stream_data.mark_processed(processing_time_ms, memory_usage_mb)
                else:
                    stream_data.mark_failed(error_message, error_code)
                return stream_data
            return None
        except Exception as e:
            logger.error(f"Error processing stream data: {str(e)}")
            return None
    
    def create_analytics_metric(self, metric_name, metric_type, metric_category, value,
                               aggregation_period='realtime', aggregation_method='current',
                               source_type=None, source_id=None, source_name=None,
                               min_value=None, max_value=None, avg_value=None, sum_value=None,
                               count_value=None, confidence_score=1.0, sample_size=1,
                               warning_threshold=None, critical_threshold=None, metadata=None,
                               tags=None, expires_in_hours=None):
        """Create a new real-time analytics metric"""
        if not self.analytics_enabled:
            return None
        
        try:
            return RealTimeAnalytics.create_metric(
                metric_name=metric_name,
                metric_type=metric_type,
                metric_category=metric_category,
                value=value,
                aggregation_period=aggregation_period,
                aggregation_method=aggregation_method,
                source_type=source_type,
                source_id=source_id,
                source_name=source_name,
                min_value=min_value,
                max_value=max_value,
                avg_value=avg_value,
                sum_value=sum_value,
                count_value=count_value,
                confidence_score=confidence_score,
                sample_size=sample_size,
                warning_threshold=warning_threshold,
                critical_threshold=critical_threshold,
                metadata=metadata,
                tags=tags,
                expires_in_hours=expires_in_hours
            )
        except Exception as e:
            logger.error(f"Error creating analytics metric: {str(e)}")
            return None
    
    def update_analytics_metric(self, metric_name, new_value, aggregation_period='realtime',
                               sample_size=None):
        """Update an existing analytics metric"""
        if not self.analytics_enabled:
            return None
        
        try:
            metric = RealTimeAnalytics.get_metric_by_name(metric_name, aggregation_period)
            if metric:
                metric.update_value(new_value, sample_size)
                return metric
            return None
        except Exception as e:
            logger.error(f"Error updating analytics metric: {str(e)}")
            return None
    
    def get_realtime_dashboard_data(self, hours=1):
        """Get comprehensive real-time dashboard data"""
        try:
            # WebSocket session stats
            session_stats = WebSocketSession.get_session_stats(hours)
            
            # Real-time event summary
            event_summary = RealTimeEvent.get_event_summary(hours)
            
            # Stream data summary
            stream_summary = StreamData.get_stream_summary(hours)
            
            # Analytics summary
            analytics_summary = RealTimeAnalytics.get_analytics_summary(hours)
            
            # Active sessions
            active_sessions = WebSocketSession.get_active_sessions(hours)
            
            # Pending events
            pending_events = RealTimeEvent.get_pending_events(limit=20)
            
            # Alerting metrics
            alerting_metrics = RealTimeAnalytics.get_alerting_metrics('warning', hours)
            
            return {
                'session_stats': session_stats,
                'event_summary': event_summary,
                'stream_summary': stream_summary,
                'analytics_summary': analytics_summary,
                'active_sessions': [session.to_dict() for session in active_sessions],
                'pending_events': [event.to_dict() for event in pending_events],
                'alerting_metrics': [metric.to_dict() for metric in alerting_metrics],
                'period_hours': hours
            }
            
        except Exception as e:
            logger.error(f"Error getting real-time dashboard data: {str(e)}")
            return None
    
    def get_user_realtime_data(self, user_id, hours=1):
        """Get real-time data for a specific user"""
        try:
            # User's WebSocket sessions
            user_sessions = WebSocketSession.get_user_sessions(user_id, status='connected')
            
            # User's events
            user_events = RealTimeEvent.get_events_by_source('user', user_id, hours)
            
            # User's stream data
            user_streams = StreamData.get_stream_data_by_source('user', user_id, hours)
            
            # User's analytics
            user_analytics = RealTimeAnalytics.get_metrics_by_source('user', user_id, hours)
            
            return {
                'user_id': user_id,
                'active_sessions': [session.to_dict() for session in user_sessions],
                'recent_events': [event.to_dict() for event in user_events],
                'stream_data': [stream.to_dict() for stream in user_streams],
                'analytics': [metric.to_dict() for metric in user_analytics],
                'period_hours': hours
            }
            
        except Exception as e:
            logger.error(f"Error getting user real-time data: {str(e)}")
            return None
    
    def broadcast_to_room(self, room, event_type, event_category, message, data=None,
                         source_type='system', severity='info', title=None):
        """Broadcast event to all sessions in a room"""
        if not self.event_processing_enabled:
            return None
        
        try:
            # Get all active sessions in the room
            sessions = self.get_room_sessions(room, 'connected')
            
            # Create event for each session
            events = []
            for session in sessions:
                event = self.create_realtime_event(
                    event_type=event_type,
                    event_category=event_category,
                    source_type=source_type,
                    target_type='room',
                    target_room=room,
                    severity=severity,
                    title=title,
                    message=message,
                    data=data,
                    target_id=session.user_id
                )
                if event:
                    events.append(event)
            
            return events
            
        except Exception as e:
            logger.error(f"Error broadcasting to room: {str(e)}")
            return []
    
    def send_private_message(self, from_user_id, to_user_id, message, data=None):
        """Send private message to specific user"""
        if not self.event_processing_enabled:
            return None
        
        try:
            # Get target user's active sessions
            target_sessions = WebSocketSession.get_user_sessions(to_user_id, 'connected')
            
            events = []
            for session in target_sessions:
                event = self.create_realtime_event(
                    event_type='private_message',
                    event_category='chat',
                    source_type='user',
                    source_id=from_user_id,
                    target_type='user',
                    target_id=to_user_id,
                    severity='info',
                    message=message,
                    data=data
                )
                if event:
                    events.append(event)
            
            return events
            
        except Exception as e:
            logger.error(f"Error sending private message: {str(e)}")
            return []
    
    def cleanup_expired_data(self, hours=24):
        """Clean up expired real-time data"""
        try:
            # Clean up expired events
            expired_events = RealTimeEvent.query.filter(
                RealTimeEvent.expires_at < datetime.utcnow()
            ).count()
            
            if expired_events > 0:
                RealTimeEvent.query.filter(
                    RealTimeEvent.expires_at < datetime.utcnow()
                ).delete()
                logger.info(f"Cleaned up {expired_events} expired events")
            
            # Clean up expired stream data
            expired_streams = StreamData.query.filter(
                StreamData.expires_at < datetime.utcnow()
            ).count()
            
            if expired_streams > 0:
                StreamData.query.filter(
                    StreamData.expires_at < datetime.utcnow()
                ).delete()
                logger.info(f"Cleaned up {expired_streams} expired stream data")
            
            # Clean up expired analytics
            expired_analytics = RealTimeAnalytics.query.filter(
                RealTimeAnalytics.expires_at < datetime.utcnow()
            ).count()
            
            if expired_analytics > 0:
                RealTimeAnalytics.query.filter(
                    RealTimeAnalytics.expires_at < datetime.utcnow()
                ).delete()
                logger.info(f"Cleaned up {expired_analytics} expired analytics")
            
            # Clean up old disconnected sessions
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            old_sessions = WebSocketSession.query.filter(
                WebSocketSession.status == 'disconnected',
                WebSocketSession.disconnected_at < cutoff_time
            ).count()
            
            if old_sessions > 0:
                WebSocketSession.query.filter(
                    WebSocketSession.status == 'disconnected',
                    WebSocketSession.disconnected_at < cutoff_time
                ).delete()
                logger.info(f"Cleaned up {old_sessions} old disconnected sessions")
            
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Error cleaning up expired data: {str(e)}")
            db.session.rollback()


# Global real-time service instance
realtime_service = None

def get_realtime_service():
    """Get real-time service instance (lazy initialization)"""
    global realtime_service
    if realtime_service is None:
        realtime_service = RealTimeService()
    return realtime_service


# Decorators for automatic real-time logging
def track_websocket_activity(session_id=None, message_sent=False, message_received=False):
    """Decorator to automatically track WebSocket activity"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                
                # Get session ID from decorator or function result
                current_session_id = session_id
                if not current_session_id and hasattr(result, 'session_id'):
                    current_session_id = result.session_id
                
                if current_session_id:
                    get_realtime_service().update_session_activity(
                        current_session_id,
                        message_sent=message_sent,
                        message_received=message_received
                    )
                
            except Exception as e:
                logger.error(f"Error in WebSocket activity tracking decorator: {str(e)}")
            
            return result
        return wrapper
    return decorator


def log_realtime_event(event_type, event_category, source_type='system', severity='info'):
    """Decorator to automatically log real-time events"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                # Get request context if available
                from flask import request, g
                user_id = getattr(g, 'user', {}).get('id') if hasattr(g, 'user') else None
                
                # Log the event
                get_realtime_service().create_realtime_event(
                    event_type=event_type,
                    event_category=event_category,
                    source_type=source_type,
                    source_id=user_id,
                    severity=severity,
                    description=f"Function {func.__name__} executed",
                    data={
                        'function': func.__name__,
                        'module': func.__module__,
                        'args_count': len(args),
                        'kwargs_count': len(kwargs)
                    }
                )
                
            except Exception as e:
                logger.error(f"Error in real-time event logging decorator: {str(e)}")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


def track_analytics_metric(metric_name, metric_type, metric_category, value,
                           aggregation_period='realtime', source_type='system'):
    """Decorator to automatically track analytics metrics"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = datetime.utcnow()
            try:
                result = func(*args, **kwargs)
                
                # Calculate execution time
                execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                
                # Track the metric
                get_realtime_service().create_analytics_metric(
                    metric_name=metric_name,
                    metric_type=metric_type,
                    metric_category=metric_category,
                    value=value,
                    aggregation_period=aggregation_period,
                    source_type=source_type,
                    metadata={
                        'function': func.__name__,
                        'module': func.__module__,
                        'execution_time_ms': execution_time
                    }
                )
                
                return result
                
            except Exception as e:
                logger.error(f"Error in analytics tracking decorator: {str(e)}")
                raise
        return wrapper
    return decorator
