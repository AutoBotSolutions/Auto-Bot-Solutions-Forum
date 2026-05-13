"""
Real-time Data Models

This module implements real-time data models for the Auto Bot Solutions Forum,
including WebSocket session management, real-time event tracking, streaming data storage, and real-time analytics.
"""

from datetime import datetime, timedelta
from flask import current_app
from app import db
from sqlalchemy import Index, CheckConstraint, func as sql_func
import json
import uuid


class WebSocketSession(db.Model):
    """WebSocket session management model for real-time connections"""
    __tablename__ = 'websocket_sessions'
    __table_args__ = (
        Index('idx_websocket_sessions_user', 'user_id'),
        Index('idx_websocket_sessions_status', 'status'),
        Index('idx_websocket_sessions_time', 'connected_at'),
        Index('idx_websocket_sessions_room', 'room'),
        {'extend_existing': True}
    )
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(36), default=lambda: str(uuid.uuid4()), unique=True, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True, index=True)
    
    # Connection information
    socket_id = db.Column(db.String(255), nullable=False, index=True)
    connection_id = db.Column(db.String(255), nullable=True)  # For load balancer scenarios
    status = db.Column(db.String(20), default='connected', index=True)  # connected, disconnected, error
    
    # Session details
    room = db.Column(db.String(100), nullable=True, index=True)  # Chat room, notification channel, etc.
    session_type = db.Column(db.String(50), default='user')  # user, admin, system, notification
    
    # Client information
    ip_address = db.Column(db.String(45), nullable=True, index=True)
    user_agent = db.Column(db.Text, nullable=True)
    
    # Geographic information
    country = db.Column(db.String(2), nullable=True)
    region = db.Column(db.String(100), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    
    # Device information
    device_type = db.Column(db.String(20), nullable=True)  # desktop, mobile, tablet
    browser = db.Column(db.String(50), nullable=True)
    platform = db.Column(db.String(50), nullable=True)  # web, mobile, desktop
    
    # Connection metrics
    connected_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    disconnected_at = db.Column(db.DateTime, nullable=True)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    duration_seconds = db.Column(db.Integer, default=0)  # Session duration in seconds
    
    # Performance metrics
    messages_sent = db.Column(db.Integer, default=0)
    messages_received = db.Column(db.Integer, default=0)
    bytes_sent = db.Column(db.BigInteger, default=0)
    bytes_received = db.Column(db.BigInteger, default=0)
    latency_ms = db.Column(db.Float, default=0.0)  # Average latency in milliseconds
    
    # Error tracking
    error_count = db.Column(db.Integer, default=0)
    last_error = db.Column(db.Text, nullable=True)
    disconnect_reason = db.Column(db.String(100), nullable=True)  # normal, timeout, error, forced
    
    # Session metadata
    capabilities = db.Column(db.JSON)  # Supported features and capabilities
    preferences = db.Column(db.JSON)  # User preferences for real-time features
    metadata = db.Column(db.JSON)  # Additional session metadata
    
    # Relationships
    user = db.relationship('User', backref='websocket_sessions', lazy=True)
    
    # Constraints
    __table_args__ = (
        CheckConstraint('status IN ("connected", "disconnected", "error")', name='check_session_status'),
        CheckConstraint('duration_seconds >= 0', name='check_duration'),
        CheckConstraint('messages_sent >= 0', name='check_messages_sent'),
        CheckConstraint('messages_received >= 0', name='check_messages_received'),
        Index('idx_websocket_sessions_user', 'user_id'),
        Index('idx_websocket_sessions_status', 'status'),
        Index('idx_websocket_sessions_time', 'connected_at'),
        Index('idx_websocket_sessions_room', 'room'),
        {'extend_existing': True}
    )
    
    def __repr__(self):
        return f'<WebSocketSession {self.session_id}:{self.status}:{self.user_id}>'
    
    @classmethod
    def create_session(cls, socket_id, user_id=None, room=None, session_type='user',
                      ip_address=None, user_agent=None, country=None, region=None, city=None,
                      device_type=None, browser=None, platform=None, capabilities=None,
                      preferences=None, metadata=None):
        """Create a new WebSocket session"""
        session = cls(
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
            capabilities=capabilities or {},
            preferences=preferences or {},
            metadata=metadata or {}
        )
        db.session.add(session)
        db.session.commit()
        return session
    
    @classmethod
    def get_session_by_socket_id(cls, socket_id):
        """Get session by socket ID"""
        return cls.query.filter_by(socket_id=socket_id).first()
    
    @classmethod
    def get_user_sessions(cls, user_id, status='connected'):
        """Get all sessions for a user"""
        query = cls.query.filter_by(user_id=user_id)
        if status:
            query = query.filter_by(status=status)
        return query.order_by(cls.connected_at.desc()).all()
    
    @classmethod
    def get_room_sessions(cls, room, status='connected'):
        """Get all sessions in a room"""
        query = cls.query.filter_by(room=room)
        if status:
            query = query.filter_by(status=status)
        return query.order_by(cls.connected_at.desc()).all()
    
    @classmethod
    def get_active_sessions(cls, hours=1):
        """Get active sessions within time window"""
        start_time = datetime.utcnow() - timedelta(hours=hours)
        return cls.query.filter(
            cls.status == 'connected',
            cls.last_activity >= start_time
        ).order_by(cls.last_activity.desc()).all()
    
    @classmethod
    def get_session_stats(cls, hours=24):
        """Get session statistics"""
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Total sessions
        total_sessions = cls.query.filter(cls.connected_at >= start_time).count()
        
        # Active sessions
        active_sessions = cls.query.filter(
            cls.status == 'connected',
            cls.last_activity >= start_time
        ).count()
        
        # Sessions by status
        sessions_by_status = db.session.query(
            cls.status,
            sql_func.count(cls.id).label('count')
        ).filter(cls.connected_at >= start_time).group_by(cls.status).all()
        
        # Sessions by type
        sessions_by_type = db.session.query(
            cls.session_type,
            sql_func.count(cls.id).label('count')
        ).filter(cls.connected_at >= start_time).group_by(cls.session_type).all()
        
        # Average session duration
        avg_duration = db.session.query(
            sql_func.avg(cls.duration_seconds)
        ).filter(cls.connected_at >= start_time, cls.duration_seconds > 0).scalar() or 0
        
        return {
            'total_sessions': total_sessions,
            'active_sessions': active_sessions,
            'avg_duration_seconds': float(avg_duration),
            'sessions_by_status': dict(sessions_by_status),
            'sessions_by_type': dict(sessions_by_type),
            'period_hours': hours
        }
    
    def disconnect(self, reason='normal'):
        """Disconnect the session"""
        self.status = 'disconnected'
        self.disconnected_at = datetime.utcnow()
        self.disconnect_reason = reason
        
        # Calculate duration
        if self.connected_at:
            self.duration_seconds = int((self.disconnected_at - self.connected_at).total_seconds())
        
        db.session.commit()
    
    def update_activity(self, message_sent=False, message_received=False, 
                        bytes_sent=0, bytes_received=0, latency_ms=None):
        """Update session activity and metrics"""
        self.last_activity = datetime.utcnow()
        
        if message_sent:
            self.messages_sent += 1
        if message_received:
            self.messages_received += 1
        
        self.bytes_sent += bytes_sent
        self.bytes_received += bytes_received
        
        if latency_ms is not None:
            # Update average latency
            if self.latency_ms == 0:
                self.latency_ms = latency_ms
            else:
                self.latency_ms = (self.latency_ms + latency_ms) / 2
        
        db.session.commit()
    
    def log_error(self, error_message):
        """Log an error for the session"""
        self.error_count += 1
        self.last_error = error_message
        self.last_activity = datetime.utcnow()
        db.session.commit()
    
    def to_dict(self):
        """Convert session to dictionary"""
        return {
            'session_id': self.session_id,
            'user_id': self.user_id,
            'socket_id': self.socket_id,
            'status': self.status,
            'room': self.room,
            'session_type': self.session_type,
            'ip_address': self.ip_address,
            'device_type': self.device_type,
            'platform': self.platform,
            'connected_at': self.connected_at.isoformat(),
            'last_activity': self.last_activity.isoformat(),
            'duration_seconds': self.duration_seconds,
            'messages_sent': self.messages_sent,
            'messages_received': self.messages_received,
            'latency_ms': self.latency_ms,
            'error_count': self.error_count,
            'disconnect_reason': self.disconnect_reason,
            'capabilities': self.capabilities,
            'preferences': self.preferences
        }


class RealTimeEvent(db.Model):
    """Real-time event tracking model for live event processing"""
    __tablename__ = 'realtime_events'
    __table_args__ = (
        Index('idx_realtime_events_type', 'event_type'),
        Index('idx_realtime_events_source', 'source_type', 'source_id'),
        Index('idx_realtime_events_time', 'event_timestamp'),
        Index('idx_realtime_events_room', 'room'),
        {'extend_existing': True}
    )
    
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.String(36), default=lambda: str(uuid.uuid4()), unique=True, index=True)
    
    # Event information
    event_type = db.Column(db.String(50), nullable=False, index=True)  # message, notification, system, user_action
    event_category = db.Column(db.String(50), nullable=False, index=True)  # chat, alert, update, status
    severity = db.Column(db.String(20), default='info', index=True)  # info, warning, error, critical
    
    # Source information
    source_type = db.Column(db.String(50), nullable=False, index=True)  # user, system, admin, bot
    source_id = db.Column(db.Integer, nullable=True, index=True)
    source_name = db.Column(db.String(255), nullable=True)  # Human-readable source name
    
    # Target information
    target_type = db.Column(db.String(50), nullable=True)  # user, room, system, all
    target_id = db.Column(db.Integer, nullable=True)
    target_room = db.Column(db.String(100), nullable=True, index=True)  # Target room for broadcasting
    
    # Event content
    title = db.Column(db.String(255), nullable=True)
    message = db.Column(db.Text, nullable=True)
    data = db.Column(db.JSON)  # Event-specific data
    
    # Event metadata
    metadata = db.Column(db.JSON)  # Additional event metadata
    tags = db.Column(db.JSON)  # Event tags for filtering and categorization
    
    # Processing information
    priority = db.Column(db.Integer, default=5)  # 1-10 priority level
    retry_count = db.Column(db.Integer, default=0)
    max_retries = db.Column(db.Integer, default=3)
    
    # Timestamps
    event_timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    processed_at = db.Column(db.DateTime, nullable=True)
    expires_at = db.Column(db.DateTime, nullable=True)  # Event expiration time
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Delivery tracking
    delivery_status = db.Column(db.String(20), default='pending')  # pending, delivered, failed, expired
    delivery_attempts = db.Column(db.Integer, default=0)
    last_delivery_attempt = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    source_user = db.relationship('User', foreign_keys=[source_id], backref='realtime_events_source', lazy=True)
    
    # Constraints
    __table_args__ = (
        CheckConstraint('severity IN ("info", "warning", "error", "critical")', name='check_event_severity'),
        CheckConstraint('priority >= 1 AND priority <= 10', name='check_priority'),
        CheckConstraint('retry_count >= 0', name='check_retry_count'),
        CheckConstraint('delivery_status IN ("pending", "delivered", "failed", "expired")', name='check_delivery_status'),
        Index('idx_realtime_events_type', 'event_type'),
        Index('idx_realtime_events_source', 'source_type', 'source_id'),
        Index('idx_realtime_events_time', 'event_timestamp'),
        Index('idx_realtime_events_room', 'room'),
        {'extend_existing': True}
    )
    
    def __repr__(self):
        return f'<RealTimeEvent {self.event_type}:{self.severity}:{self.source_type}>'
    
    @classmethod
    def create_event(cls, event_type, event_category, source_type, source_id=None,
                      source_name=None, target_type=None, target_id=None, target_room=None,
                      severity='info', title=None, message=None, data=None, metadata=None,
                      tags=None, priority=5, expires_in_hours=None):
        """Create a new real-time event"""
        expires_at = None
        if expires_in_hours:
            expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)
        
        event = cls(
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
            data=data or {},
            metadata=metadata or {},
            tags=tags or [],
            priority=priority,
            expires_at=expires_at
        )
        db.session.add(event)
        db.session.commit()
        return event
    
    @classmethod
    def get_events_by_type(cls, event_type, hours=24, limit=None):
        """Get events by type"""
        start_time = datetime.utcnow() - timedelta(hours=hours)
        query = cls.query.filter(
            cls.event_type == event_type,
            cls.event_timestamp >= start_time
        ).order_by(cls.event_timestamp.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    @classmethod
    def get_events_by_source(cls, source_type, source_id=None, hours=24, limit=None):
        """Get events by source"""
        start_time = datetime.utcnow() - timedelta(hours=hours)
        query = cls.query.filter(
            cls.source_type == source_type,
            cls.event_timestamp >= start_time
        )
        
        if source_id:
            query = query.filter(cls.source_id == source_id)
        
        query = query.order_by(cls.event_timestamp.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    @classmethod
    def get_room_events(cls, room, hours=24, limit=None):
        """Get events for a specific room"""
        start_time = datetime.utcnow() - timedelta(hours=hours)
        query = cls.query.filter(
            cls.target_room == room,
            cls.event_timestamp >= start_time
        ).order_by(cls.event_timestamp.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    @classmethod
    def get_pending_events(cls, limit=None):
        """Get pending events for processing"""
        query = cls.query.filter_by(delivery_status='pending').order_by(cls.priority.desc(), cls.event_timestamp.asc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    @classmethod
    def get_event_summary(cls, hours=24):
        """Get event summary statistics"""
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Total events
        total_events = cls.query.filter(cls.event_timestamp >= start_time).count()
        
        # Events by type
        events_by_type = db.session.query(
            cls.event_type,
            sql_func.count(cls.id).label('count')
        ).filter(cls.event_timestamp >= start_time).group_by(cls.event_type).all()
        
        # Events by severity
        events_by_severity = db.session.query(
            cls.severity,
            sql_func.count(cls.id).label('count')
        ).filter(cls.event_timestamp >= start_time).group_by(cls.severity).all()
        
        # Events by source
        events_by_source = db.session.query(
            cls.source_type,
            sql_func.count(cls.id).label('count')
        ).filter(cls.event_timestamp >= start_time).group_by(cls.source_type).all()
        
        # Delivery status
        delivery_status = db.session.query(
            cls.delivery_status,
            sql_func.count(cls.id).label('count')
        ).filter(cls.event_timestamp >= start_time).group_by(cls.delivery_status).all()
        
        return {
            'total_events': total_events,
            'events_by_type': dict(events_by_type),
            'events_by_severity': dict(events_by_severity),
            'events_by_source': dict(events_by_source),
            'delivery_status': dict(delivery_status),
            'period_hours': hours
        }
    
    def mark_delivered(self):
        """Mark event as delivered"""
        self.delivery_status = 'delivered'
        self.processed_at = datetime.utcnow()
        self.last_delivery_attempt = datetime.utcnow()
        db.session.commit()
    
    def mark_failed(self, error_message=None):
        """Mark event as failed"""
        self.delivery_attempts += 1
        self.last_delivery_attempt = datetime.utcnow()
        
        if self.delivery_attempts >= self.max_retries:
            self.delivery_status = 'failed'
        
        if error_message:
            self.metadata = self.metadata or {}
            self.metadata['last_error'] = error_message
        
        db.session.commit()
    
    def retry_delivery(self):
        """Retry event delivery"""
        if self.delivery_attempts < self.max_retries:
            self.delivery_status = 'pending'
            self.retry_count += 1
            self.last_delivery_attempt = datetime.utcnow()
            db.session.commit()
            return True
        return False
    
    def is_expired(self):
        """Check if event is expired"""
        if self.expires_at:
            return datetime.utcnow() > self.expires_at
        return False
    
    def to_dict(self):
        """Convert event to dictionary"""
        return {
            'event_id': self.event_id,
            'event_type': self.event_type,
            'event_category': self.event_category,
            'severity': self.severity,
            'source_type': self.source_type,
            'source_id': self.source_id,
            'source_name': self.source_name,
            'target_type': self.target_type,
            'target_id': self.target_id,
            'target_room': self.target_room,
            'title': self.title,
            'message': self.message,
            'data': self.data,
            'metadata': self.metadata,
            'tags': self.tags,
            'priority': self.priority,
            'event_timestamp': self.event_timestamp.isoformat(),
            'delivery_status': self.delivery_status,
            'delivery_attempts': self.delivery_attempts,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None
        }


class StreamData(db.Model):
    """Streaming data model for real-time data streams and processing"""
    __tablename__ = 'stream_data'
    __table_args__ = (
        Index('idx_stream_data_stream', 'stream_id'),
        Index('idx_stream_data_type', 'stream_type'),
        Index('idx_stream_data_time', 'timestamp'),
        Index('idx_stream_data_status', 'processing_status'),
        {'extend_existing': True}
    )
    
    id = db.Column(db.Integer, primary_key=True)
    stream_id = db.Column(db.String(36), default=lambda: str(uuid.uuid4()), unique=True, index=True)
    
    # Stream information
    stream_type = db.Column(db.String(50), nullable=False, index=True)  # user_activity, system_metrics, chat, notifications
    stream_category = db.Column(db.String(50), nullable=False, index=True)  # real-time, batch, analytics
    source_id = db.Column(db.Integer, nullable=True, index=True)  # Source entity ID
    source_type = db.Column(db.String(50), nullable=True)  # Source entity type
    
    # Data content
    data = db.Column(db.JSON, nullable=False)  # Stream data content
    data_size = db.Column(db.Integer, default=0)  # Data size in bytes
    data_format = db.Column(db.String(20), default='json')  # json, xml, binary, text
    
    # Stream metadata
    metadata = db.Column(db.JSON)  # Stream metadata
    tags = db.Column(db.JSON)  # Stream tags for filtering
    schema_version = db.Column(db.String(20), default='1.0')  # Data schema version
    
    # Processing information
    processing_status = db.Column(db.String(20), default='pending', index=True)  # pending, processing, processed, failed
    processing_priority = db.Column(db.Integer, default=5)  # 1-10 priority level
    processing_attempts = db.Column(db.Integer, default=0)
    max_processing_attempts = db.Column(db.Integer, default=3)
    
    # Timestamps
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    received_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    processed_at = db.Column(db.DateTime, nullable=True)
    expires_at = db.Column(db.DateTime, nullable=True)  # Data expiration time
    
    # Quality metrics
    quality_score = db.Column(db.Float, default=1.0)  # Data quality score 0-1
    completeness_score = db.Column(db.Float, default=1.0)  # Data completeness score 0-1
    accuracy_score = db.Column(db.Float, default=1.0)  # Data accuracy score 0-1
    
    # Performance metrics
    processing_time_ms = db.Column(db.Float, default=0.0)  # Processing time in milliseconds
    memory_usage_mb = db.Column(db.Float, default=0.0)  # Memory usage during processing
    
    # Error handling
    error_message = db.Column(db.Text, nullable=True)
    error_code = db.Column(db.String(50), nullable=True)
    retry_after = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    source_entity = db.relationship('User', foreign_keys=[source_id], backref='stream_data_source', lazy=True)
    
    # Constraints
    __table_args__ = (
        CheckConstraint('processing_status IN ("pending", "processing", "processed", "failed")', name='check_processing_status'),
        CheckConstraint('processing_priority >= 1 AND processing_priority <= 10', name='check_processing_priority'),
        CheckConstraint('quality_score >= 0 AND quality_score <= 1', name='check_quality_score'),
        CheckConstraint('completeness_score >= 0 AND completeness_score <= 1', name='check_completeness_score'),
        CheckConstraint('accuracy_score >= 0 AND accuracy_score <= 1', name='check_accuracy_score'),
        Index('idx_stream_data_stream', 'stream_id'),
        Index('idx_stream_data_type', 'stream_type'),
        Index('idx_stream_data_time', 'timestamp'),
        Index('idx_stream_data_status', 'processing_status'),
        {'extend_existing': True}
    )
    
    def __repr__(self):
        return f'<StreamData {self.stream_type}:{self.processing_status}:{self.stream_id}>'
    
    @classmethod
    def create_stream_data(cls, stream_type, stream_category, data, source_id=None, source_type=None,
                           data_format='json', metadata=None, tags=None, schema_version='1.0',
                           processing_priority=5, expires_in_hours=None, quality_score=1.0,
                           completeness_score=1.0, accuracy_score=1.0):
        """Create new stream data"""
        expires_at = None
        if expires_in_hours:
            expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)
        
        # Calculate data size
        data_size = len(json.dumps(data)) if isinstance(data, (dict, list)) else len(str(data))
        
        stream_data = cls(
            stream_type=stream_type,
            stream_category=stream_category,
            data=data,
            data_size=data_size,
            data_format=data_format,
            source_id=source_id,
            source_type=source_type,
            metadata=metadata or {},
            tags=tags or [],
            schema_version=schema_version,
            processing_priority=processing_priority,
            expires_at=expires_at,
            quality_score=quality_score,
            completeness_score=completeness_score,
            accuracy_score=accuracy_score
        )
        db.session.add(stream_data)
        db.session.commit()
        return stream_data
    
    @classmethod
    def get_stream_data_by_type(cls, stream_type, hours=24, limit=None):
        """Get stream data by type"""
        start_time = datetime.utcnow() - timedelta(hours=hours)
        query = cls.query.filter(
            cls.stream_type == stream_type,
            cls.timestamp >= start_time
        ).order_by(cls.timestamp.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    @classmethod
    def get_stream_data_by_source(cls, source_type, source_id=None, hours=24, limit=None):
        """Get stream data by source"""
        start_time = datetime.utcnow() - timedelta(hours=hours)
        query = cls.query.filter(
            cls.source_type == source_type,
            cls.timestamp >= start_time
        )
        
        if source_id:
            query = query.filter(cls.source_id == source_id)
        
        query = query.order_by(cls.timestamp.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    @classmethod
    def get_pending_stream_data(cls, limit=None):
        """Get pending stream data for processing"""
        query = cls.query.filter_by(processing_status='pending').order_by(
            cls.processing_priority.desc(),
            cls.timestamp.asc()
        )
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    @classmethod
    def get_stream_summary(cls, hours=24):
        """Get stream data summary"""
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Total streams
        total_streams = cls.query.filter(cls.timestamp >= start_time).count()
        
        # Streams by type
        streams_by_type = db.session.query(
            cls.stream_type,
            sql_func.count(cls.id).label('count')
        ).filter(cls.timestamp >= start_time).group_by(cls.stream_type).all()
        
        # Streams by status
        streams_by_status = db.session.query(
            cls.processing_status,
            sql_func.count(cls.id).label('count')
        ).filter(cls.timestamp >= start_time).group_by(cls.processing_status).all()
        
        # Average processing time
        avg_processing_time = db.session.query(
            sql_func.avg(cls.processing_time_ms)
        ).filter(cls.timestamp >= start_time, cls.processing_time_ms > 0).scalar() or 0
        
        # Quality metrics
        avg_quality = db.session.query(
            sql_func.avg(cls.quality_score)
        ).filter(cls.timestamp >= start_time).scalar() or 0
        
        return {
            'total_streams': total_streams,
            'streams_by_type': dict(streams_by_type),
            'streams_by_status': dict(streams_by_status),
            'avg_processing_time_ms': float(avg_processing_time),
            'avg_quality_score': float(avg_quality),
            'period_hours': hours
        }
    
    def start_processing(self):
        """Start processing stream data"""
        self.processing_status = 'processing'
        self.processing_attempts += 1
        self.last_processing_attempt = datetime.utcnow()
        db.session.commit()
    
    def mark_processed(self, processing_time_ms=None, memory_usage_mb=None):
        """Mark stream data as processed"""
        self.processing_status = 'processed'
        self.processed_at = datetime.utcnow()
        
        if processing_time_ms is not None:
            self.processing_time_ms = processing_time_ms
        if memory_usage_mb is not None:
            self.memory_usage_mb = memory_usage_mb
        
        db.session.commit()
    
    def mark_failed(self, error_message=None, error_code=None, retry_after_minutes=None):
        """Mark stream data as failed"""
        self.processing_attempts += 1
        self.error_message = error_message
        self.error_code = error_code
        
        if retry_after_minutes:
            self.retry_after = datetime.utcnow() + timedelta(minutes=retry_after_minutes)
        
        if self.processing_attempts >= self.max_processing_attempts:
            self.processing_status = 'failed'
        else:
            self.processing_status = 'pending'
        
        db.session.commit()
    
    def is_expired(self):
        """Check if stream data is expired"""
        if self.expires_at:
            return datetime.utcnow() > self.expires_at
        return False
    
    def can_retry(self):
        """Check if stream data can be retried"""
        return (self.processing_status == 'failed' and 
                self.processing_attempts < self.max_processing_attempts and
                (not self.retry_after or datetime.utcnow() > self.retry_after))
    
    def to_dict(self):
        """Convert stream data to dictionary"""
        return {
            'stream_id': self.stream_id,
            'stream_type': self.stream_type,
            'stream_category': self.stream_category,
            'source_id': self.source_id,
            'source_type': self.source_type,
            'data': self.data,
            'data_size': self.data_size,
            'data_format': self.data_format,
            'metadata': self.metadata,
            'tags': self.tags,
            'schema_version': self.schema_version,
            'processing_status': self.processing_status,
            'processing_priority': self.processing_priority,
            'timestamp': self.timestamp.isoformat(),
            'received_at': self.received_at.isoformat(),
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
            'quality_score': self.quality_score,
            'completeness_score': self.completeness_score,
            'accuracy_score': self.accuracy_score,
            'processing_time_ms': self.processing_time_ms,
            'error_message': self.error_message,
            'error_code': self.error_code
        }


class RealTimeAnalytics(db.Model):
    """Real-time analytics model for live metrics and calculations"""
    __tablename__ = 'realtime_analytics'
    __table_args__ = (
        Index('idx_realtime_analytics_metric', 'metric_name'),
        Index('idx_realtime_analytics_type', 'metric_type'),
        Index('idx_realtime_analytics_time', 'timestamp'),
        Index('idx_realtime_analytics_source', 'source_type', 'source_id'),
        {'extend_existing': True}
    )
    
    id = db.Column(db.Integer, primary_key=True)
    analytics_id = db.Column(db.String(36), default=lambda: str(uuid.uuid4()), unique=True, index=True)
    
    # Metric information
    metric_name = db.Column(db.String(100), nullable=False, index=True)  # active_users, message_rate, error_rate
    metric_type = db.Column(db.String(50), nullable=False, index=True)  # counter, gauge, histogram, timer
    metric_category = db.Column(db.String(50), nullable=False, index=True)  # user, system, performance, business
    
    # Metric values
    value = db.Column(db.Float, nullable=False)  # Current metric value
    previous_value = db.Column(db.Float, nullable=True)  # Previous value for comparison
    change_percent = db.Column(db.Float, default=0.0)  # Percentage change from previous value
    
    # Aggregation information
    aggregation_period = db.Column(db.String(20), default='realtime')  # realtime, 1m, 5m, 1h, 1d
    aggregation_method = db.Column(db.String(20), default='current')  # current, avg, sum, min, max, count
    
    # Source information
    source_type = db.Column(db.String(50), nullable=True, index=True)  # websocket, stream, event, system
    source_id = db.Column(db.Integer, nullable=True, index=True)
    source_name = db.Column(db.String(255), nullable=True)
    
    # Statistical data
    min_value = db.Column(db.Float, nullable=True)
    max_value = db.Column(db.Float, nullable=True)
    avg_value = db.Column(db.Float, nullable=True)
    sum_value = db.Column(db.Float, nullable=True)
    count_value = db.Column(db.Integer, default=0)
    
    # Quality and reliability
    confidence_score = db.Column(db.Float, default=1.0)  # Confidence in metric accuracy 0-1
    sample_size = db.Column(db.Integer, default=1)  # Number of samples used for calculation
    
    # Thresholds and alerts
    warning_threshold = db.Column(db.Float, nullable=True)
    critical_threshold = db.Column(db.Float, nullable=True)
    alert_status = db.Column(db.String(20), default='normal')  # normal, warning, critical
    last_alert_at = db.Column(db.DateTime, nullable=True)
    
    # Timestamps
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)  # Metric expiration time
    
    # Additional data
    metadata = db.Column(db.JSON)  # Additional metric metadata
    tags = db.Column(db.JSON)  # Metric tags for filtering and grouping
    
    # Relationships
    source_entity = db.relationship('User', foreign_keys=[source_id], backref='realtime_analytics_source', lazy=True)
    
    # Constraints
    __table_args__ = (
        CheckConstraint('metric_type IN ("counter", "gauge", "histogram", "timer")', name='check_metric_type'),
        CheckConstraint('alert_status IN ("normal", "warning", "critical")', name='check_alert_status'),
        CheckConstraint('confidence_score >= 0 AND confidence_score <= 1', name='check_confidence_score'),
        CheckConstraint('change_percent >= -100 AND change_percent <= 1000', name='check_change_percent'),
        Index('idx_realtime_analytics_metric', 'metric_name'),
        Index('idx_realtime_analytics_type', 'metric_type'),
        Index('idx_realtime_analytics_time', 'timestamp'),
        Index('idx_realtime_analytics_source', 'source_type', 'source_id'),
        {'extend_existing': True}
    )
    
    def __repr__(self):
        return f'<RealTimeAnalytics {self.metric_name}:{self.metric_type}:{self.value}>'
    
    @classmethod
    def create_metric(cls, metric_name, metric_type, metric_category, value,
                     aggregation_period='realtime', aggregation_method='current',
                     source_type=None, source_id=None, source_name=None,
                     min_value=None, max_value=None, avg_value=None, sum_value=None,
                     count_value=None, confidence_score=1.0, sample_size=1,
                     warning_threshold=None, critical_threshold=None, metadata=None,
                     tags=None, expires_in_hours=None):
        """Create a new real-time metric"""
        expires_at = None
        if expires_in_hours:
            expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)
        
        # Get previous value for change calculation
        previous_metric = cls.query.filter_by(
            metric_name=metric_name,
            metric_type=metric_type,
            aggregation_period=aggregation_period
        ).order_by(cls.timestamp.desc()).first()
        
        previous_value = previous_metric.value if previous_metric else None
        change_percent = 0.0
        
        if previous_value is not None and previous_value != 0:
            change_percent = ((value - previous_value) / previous_value) * 100
        
        # Determine alert status
        alert_status = 'normal'
        if critical_threshold and value >= critical_threshold:
            alert_status = 'critical'
        elif warning_threshold and value >= warning_threshold:
            alert_status = 'warning'
        
        metric = cls(
            metric_name=metric_name,
            metric_type=metric_type,
            metric_category=metric_category,
            value=value,
            previous_value=previous_value,
            change_percent=change_percent,
            aggregation_period=aggregation_period,
            aggregation_method=aggregation_method,
            source_type=source_type,
            source_id=source_id,
            source_name=source_name,
            min_value=min_value,
            max_value=max_value,
            avg_value=avg_value,
            sum_value=sum_value,
            count_value=count_value or 1,
            confidence_score=confidence_score,
            sample_size=sample_size,
            warning_threshold=warning_threshold,
            critical_threshold=critical_threshold,
            alert_status=alert_status,
            expires_at=expires_at,
            metadata=metadata or {},
            tags=tags or []
        )
        db.session.add(metric)
        db.session.commit()
        return metric
    
    @classmethod
    def get_metric_by_name(cls, metric_name, aggregation_period='realtime', hours=1):
        """Get latest metric by name"""
        start_time = datetime.utcnow() - timedelta(hours=hours)
        return cls.query.filter(
            cls.metric_name == metric_name,
            cls.aggregation_period == aggregation_period,
            cls.timestamp >= start_time
        ).order_by(cls.timestamp.desc()).first()
    
    @classmethod
    def get_metrics_by_category(cls, metric_category, hours=1, limit=None):
        """Get metrics by category"""
        start_time = datetime.utcnow() - timedelta(hours=hours)
        query = cls.query.filter(
            cls.metric_category == metric_category,
            cls.timestamp >= start_time
        ).order_by(cls.timestamp.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    @classmethod
    def get_metrics_by_source(cls, source_type, source_id=None, hours=1, limit=None):
        """Get metrics by source"""
        start_time = datetime.utcnow() - timedelta(hours=hours)
        query = cls.query.filter(
            cls.source_type == source_type,
            cls.timestamp >= start_time
        )
        
        if source_id:
            query = query.filter(cls.source_id == source_id)
        
        query = query.order_by(cls.timestamp.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    @classmethod
    def get_alerting_metrics(cls, alert_status='warning', hours=1):
        """Get metrics that are triggering alerts"""
        start_time = datetime.utcnow() - timedelta(hours=hours)
        return cls.query.filter(
            cls.alert_status == alert_status,
            cls.timestamp >= start_time
        ).order_by(cls.timestamp.desc()).all()
    
    @classmethod
    def get_analytics_summary(cls, hours=1):
        """Get analytics summary"""
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Total metrics
        total_metrics = cls.query.filter(cls.timestamp >= start_time).count()
        
        # Metrics by type
        metrics_by_type = db.session.query(
            cls.metric_type,
            sql_func.count(cls.id).label('count')
        ).filter(cls.timestamp >= start_time).group_by(cls.metric_type).all()
        
        # Metrics by category
        metrics_by_category = db.session.query(
            cls.metric_category,
            sql_func.count(cls.id).label('count')
        ).filter(cls.timestamp >= start_time).group_by(cls.metric_category).all()
        
        # Alert status
        alert_status = db.session.query(
            cls.alert_status,
            sql_func.count(cls.id).label('count')
        ).filter(cls.timestamp >= start_time).group_by(cls.alert_status).all()
        
        return {
            'total_metrics': total_metrics,
            'metrics_by_type': dict(metrics_by_type),
            'metrics_by_category': dict(metrics_by_category),
            'alert_status': dict(alert_status),
            'period_hours': hours
        }
    
    def update_value(self, new_value, sample_size=None):
        """Update metric value with change calculation"""
        self.previous_value = self.value
        self.value = new_value
        
        if self.previous_value is not None and self.previous_value != 0:
            self.change_percent = ((new_value - self.previous_value) / self.previous_value) * 100
        
        if sample_size:
            self.sample_size = sample_size
        
        # Update alert status
        if self.critical_threshold and new_value >= self.critical_threshold:
            self.alert_status = 'critical'
            self.last_alert_at = datetime.utcnow()
        elif self.warning_threshold and new_value >= self.warning_threshold:
            if self.alert_status != 'critical':
                self.alert_status = 'warning'
                self.last_alert_at = datetime.utcnow()
        else:
            self.alert_status = 'normal'
        
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def is_expired(self):
        """Check if metric is expired"""
        if self.expires_at:
            return datetime.utcnow() > self.expires_at
        return False
    
    def to_dict(self):
        """Convert analytics to dictionary"""
        return {
            'analytics_id': self.analytics_id,
            'metric_name': self.metric_name,
            'metric_type': self.metric_type,
            'metric_category': self.metric_category,
            'value': self.value,
            'previous_value': self.previous_value,
            'change_percent': self.change_percent,
            'aggregation_period': self.aggregation_period,
            'aggregation_method': self.aggregation_method,
            'source_type': self.source_type,
            'source_id': self.source_id,
            'source_name': self.source_name,
            'min_value': self.min_value,
            'max_value': self.max_value,
            'avg_value': self.avg_value,
            'sum_value': self.sum_value,
            'count_value': self.count_value,
            'confidence_score': self.confidence_score,
            'sample_size': self.sample_size,
            'warning_threshold': self.warning_threshold,
            'critical_threshold': self.critical_threshold,
            'alert_status': self.alert_status,
            'last_alert_at': self.last_alert_at.isoformat() if self.last_alert_at else None,
            'timestamp': self.timestamp.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'metadata': self.metadata,
            'tags': self.tags
        }


# Helper functions for real-time system initialization
def initialize_realtime_system():
    """Initialize real-time system with default configurations"""
    print("Real-time system initialized successfully")
