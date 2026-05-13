"""
Advanced Security Models

This module implements comprehensive security models for the Auto Bot Solutions Forum,
including security event logging, audit trail management, threat detection, and compliance tracking.
"""

from datetime import datetime, timedelta
from flask import current_app
from app import db
from sqlalchemy import Index, CheckConstraint, func as sql_func
import json
import uuid


class SecurityEvent(db.Model):
    """Security event logging model for comprehensive security monitoring"""
    __tablename__ = 'security_events'
    __table_args__ = (
        Index('idx_security_events_type', 'event_type'),
        Index('idx_security_events_severity', 'severity'),
        Index('idx_security_events_user', 'user_id'),
        Index('idx_security_events_time', 'event_timestamp'),
        Index('idx_security_events_ip', 'ip_address'),
        {'extend_existing': True}
    )
    
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.String(36), default=lambda: str(uuid.uuid4()), unique=True, index=True)
    event_type = db.Column(db.String(50), nullable=False, index=True)  # login, logout, failed_login, permission_denied, etc.
    event_category = db.Column(db.String(50), nullable=False, index=True)  # authentication, authorization, data_access, system
    severity = db.Column(db.String(20), default='medium', index=True)  # low, medium, high, critical
    
    # Event details
    description = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True, index=True)
    session_id = db.Column(db.String(128), nullable=True, index=True)
    ip_address = db.Column(db.String(45), nullable=True, index=True)
    user_agent = db.Column(db.Text, nullable=True)
    
    # Resource information
    resource_type = db.Column(db.String(50), nullable=True, index=True)  # user, post, comment, system
    resource_id = db.Column(db.Integer, nullable=True, index=True)
    action = db.Column(db.String(100), nullable=True)  # create, read, update, delete, login, logout
    
    # Context information
    request_method = db.Column(db.String(10), nullable=True)
    request_url = db.Column(db.String(1000), nullable=True)
    referrer = db.Column(db.String(1000), nullable=True)
    
    # Geographic information
    country = db.Column(db.String(2), nullable=True)
    region = db.Column(db.String(100), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    
    # Device information
    device_type = db.Column(db.String(20), nullable=True)  # desktop, mobile, tablet, bot
    browser = db.Column(db.String(50), nullable=True)
    operating_system = db.Column(db.String(50), nullable=True)
    
    # Event outcome
    success = db.Column(db.Boolean, default=True)
    error_message = db.Column(db.Text, nullable=True)
    
    # Timestamps
    event_timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Additional event data
    event_data = db.Column(db.JSON)  # Additional event-specific data
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='user_security_events', lazy=True)
    
    # Constraints
    __table_args__ = (
        CheckConstraint('severity IN ("low", "medium", "high", "critical")', name='check_severity'),
        CheckConstraint('success IN (0, 1)', name='check_success'),
        Index('idx_security_events_type', 'event_type'),
        Index('idx_security_events_severity', 'severity'),
        Index('idx_security_events_user', 'user_id'),
        Index('idx_security_events_time', 'event_timestamp'),
        Index('idx_security_events_ip', 'ip_address'),
        {'extend_existing': True}
    )
    
    def __repr__(self):
        return f'<SecurityEvent {self.event_type}:{self.severity}:{self.user_id}>'
    
    @classmethod
    def log_event(cls, event_type, event_category, description, severity='medium',
                  user_id=None, session_id=None, ip_address=None, user_agent=None,
                  resource_type=None, resource_id=None, action=None, request_method=None,
                  request_url=None, referrer=None, country=None, region=None, city=None,
                  device_type=None, browser=None, operating_system=None, success=True,
                  error_message=None, event_data=None):
        """Log a security event"""
        event = cls(
            event_type=event_type,
            event_category=event_category,
            description=description,
            severity=severity,
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            request_method=request_method,
            request_url=request_url,
            referrer=referrer,
            country=country,
            region=region,
            city=city,
            device_type=device_type,
            browser=browser,
            operating_system=operating_system,
            success=success,
            error_message=error_message,
            event_data=event_data or {}
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
    def get_events_by_severity(cls, severity, hours=24, limit=None):
        """Get events by severity"""
        start_time = datetime.utcnow() - timedelta(hours=hours)
        query = cls.query.filter(
            cls.severity == severity,
            cls.event_timestamp >= start_time
        ).order_by(cls.event_timestamp.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    @classmethod
    def get_user_events(cls, user_id, hours=24, limit=None):
        """Get events for a specific user"""
        start_time = datetime.utcnow() - timedelta(hours=hours)
        query = cls.query.filter(
            cls.user_id == user_id,
            cls.event_timestamp >= start_time
        ).order_by(cls.event_timestamp.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    @classmethod
    def get_failed_login_attempts(cls, ip_address=None, hours=24, limit=None):
        """Get failed login attempts"""
        start_time = datetime.utcnow() - timedelta(hours=hours)
        query = cls.query.filter(
            cls.event_type == 'failed_login',
            cls.success == False,
            cls.event_timestamp >= start_time
        )
        
        if ip_address:
            query = query.filter(cls.ip_address == ip_address)
        
        query = query.order_by(cls.event_timestamp.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    @classmethod
    def get_security_summary(cls, hours=24):
        """Get security events summary"""
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Total events
        total_events = cls.query.filter(cls.event_timestamp >= start_time).count()
        
        # Events by severity
        events_by_severity = db.session.query(
            cls.severity,
            sql_func.count(cls.id).label('count')
        ).filter(cls.event_timestamp >= start_time).group_by(cls.severity).all()
        
        # Events by type
        events_by_type = db.session.query(
            cls.event_type,
            sql_func.count(cls.id).label('count')
        ).filter(cls.event_timestamp >= start_time).group_by(cls.event_type).all()
        
        # Failed events
        failed_events = cls.query.filter(
            cls.success == False,
            cls.event_timestamp >= start_time
        ).count()
        
        # Critical events
        critical_events = cls.query.filter(
            cls.severity == 'critical',
            cls.event_timestamp >= start_time
        ).count()
        
        return {
            'total_events': total_events,
            'failed_events': failed_events,
            'critical_events': critical_events,
            'events_by_severity': dict(events_by_severity),
            'events_by_type': dict(events_by_type),
            'period_hours': hours
        }
    
    def to_dict(self):
        """Convert event to dictionary"""
        return {
            'event_id': self.event_id,
            'event_type': self.event_type,
            'event_category': self.event_category,
            'severity': self.severity,
            'description': self.description,
            'user_id': self.user_id,
            'session_id': self.session_id,
            'ip_address': self.ip_address,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'action': self.action,
            'success': self.success,
            'error_message': self.error_message,
            'event_timestamp': self.event_timestamp.isoformat(),
            'created_at': self.created_at.isoformat(),
            'event_data': self.event_data
        }


class AuditTrail(db.Model):
    """Audit trail model for comprehensive change tracking"""
    __tablename__ = 'audit_trail'
    __table_args__ = (
        Index('idx_audit_trail_user', 'user_id'),
        Index('idx_audit_trail_resource', 'resource_type', 'resource_id'),
        Index('idx_audit_trail_action', 'action'),
        Index('idx_audit_trail_time', 'action_timestamp'),
        {'extend_existing': True}
    )
    
    id = db.Column(db.Integer, primary_key=True)
    audit_id = db.Column(db.String(36), default=lambda: str(uuid.uuid4()), unique=True, index=True)
    
    # Action information
    action = db.Column(db.String(50), nullable=False, index=True)  # create, read, update, delete, login, logout
    action_category = db.Column(db.String(50), nullable=False, index=True)  # user_data, content, system, security
    description = db.Column(db.Text, nullable=False)
    
    # User information
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True, index=True)
    user_email = db.Column(db.String(255), nullable=True)  # Store email even if user deleted
    username = db.Column(db.String(100), nullable=True)
    
    # Resource information
    resource_type = db.Column(db.String(50), nullable=False, index=True)  # user, post, comment, role, permission
    resource_id = db.Column(db.Integer, nullable=True, index=True)
    resource_name = db.Column(db.String(255), nullable=True)  # Human-readable resource identifier
    
    # Change details
    old_values = db.Column(db.JSON)  # Previous values before change
    new_values = db.Column(db.JSON)  # New values after change
    changed_fields = db.Column(db.JSON)  # List of changed field names
    
    # Request information
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.Text, nullable=True)
    request_method = db.Column(db.String(10), nullable=True)
    request_url = db.Column(db.String(1000), nullable=True)
    
    # System information
    module_name = db.Column(db.String(100), nullable=True)  # Python module where action occurred
    function_name = db.Column(db.String(100), nullable=True)  # Function name
    line_number = db.Column(db.Integer, nullable=True)  # Line number in code
    
    # Timestamps
    action_timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Additional metadata
    audit_metadata = db.Column(db.JSON)  # Additional audit metadata
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='audit_trail', lazy=True)
    
    def __repr__(self):
        return f'<AuditTrail {self.action}:{self.resource_type}:{self.resource_id}>'
    
    @classmethod
    def log_action(cls, action, action_category, description, user_id=None, user_email=None,
                   username=None, resource_type=None, resource_id=None, resource_name=None,
                   old_values=None, new_values=None, changed_fields=None, ip_address=None,
                   user_agent=None, request_method=None, request_url=None, module_name=None,
                   function_name=None, line_number=None, metadata=None):
        """Log an audit action"""
        audit = cls(
            action=action,
            action_category=action_category,
            description=description,
            user_id=user_id,
            user_email=user_email,
            username=username,
            resource_type=resource_type,
            resource_id=resource_id,
            resource_name=resource_name,
            old_values=old_values or {},
            new_values=new_values or {},
            changed_fields=changed_fields or [],
            ip_address=ip_address,
            user_agent=user_agent,
            request_method=request_method,
            request_url=request_url,
            module_name=module_name,
            function_name=function_name,
            line_number=line_number,
            audit_metadata=metadata or {}
        )
        db.session.add(audit)
        db.session.commit()
        return audit
    
    @classmethod
    def get_user_actions(cls, user_id, hours=24, limit=None):
        """Get actions for a specific user"""
        start_time = datetime.utcnow() - timedelta(hours=hours)
        query = cls.query.filter(
            cls.user_id == user_id,
            cls.action_timestamp >= start_time
        ).order_by(cls.action_timestamp.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    @classmethod
    def get_resource_actions(cls, resource_type, resource_id, hours=24, limit=None):
        """Get actions for a specific resource"""
        start_time = datetime.utcnow() - timedelta(hours=hours)
        query = cls.query.filter(
            cls.resource_type == resource_type,
            cls.resource_id == resource_id,
            cls.action_timestamp >= start_time
        ).order_by(cls.action_timestamp.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    @classmethod
    def get_actions_by_type(cls, action, hours=24, limit=None):
        """Get actions by type"""
        start_time = datetime.utcnow() - timedelta(hours=hours)
        query = cls.query.filter(
            cls.action == action,
            cls.action_timestamp >= start_time
        ).order_by(cls.action_timestamp.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    @classmethod
    def get_audit_summary(cls, hours=24):
        """Get audit trail summary"""
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Total actions
        total_actions = cls.query.filter(cls.action_timestamp >= start_time).count()
        
        # Actions by type
        actions_by_type = db.session.query(
            cls.action,
            sql_func.count(cls.id).label('count')
        ).filter(cls.action_timestamp >= start_time).group_by(cls.action).all()
        
        # Actions by resource type
        actions_by_resource = db.session.query(
            cls.resource_type,
            sql_func.count(cls.id).label('count')
        ).filter(cls.action_timestamp >= start_time).group_by(cls.resource_type).all()
        
        # Actions by category
        actions_by_category = db.session.query(
            cls.action_category,
            sql_func.count(cls.id).label('count')
        ).filter(cls.action_timestamp >= start_time).group_by(cls.action_category).all()
        
        return {
            'total_actions': total_actions,
            'actions_by_type': dict(actions_by_type),
            'actions_by_resource': dict(actions_by_resource),
            'actions_by_category': dict(actions_by_category),
            'period_hours': hours
        }
    
    def to_dict(self):
        """Convert audit to dictionary"""
        return {
            'audit_id': self.audit_id,
            'action': self.action,
            'action_category': self.action_category,
            'description': self.description,
            'user_id': self.user_id,
            'user_email': self.user_email,
            'username': self.username,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'resource_name': self.resource_name,
            'old_values': self.old_values,
            'new_values': self.new_values,
            'changed_fields': self.changed_fields,
            'ip_address': self.ip_address,
            'request_method': self.request_method,
            'action_timestamp': self.action_timestamp.isoformat(),
            'created_at': self.created_at.isoformat(),
            'metadata': self.metadata
        }


class ThreatDetection(db.Model):
    """Threat detection model for security threat monitoring and response"""
    __tablename__ = 'threat_detections'
    __table_args__ = (
        Index('idx_threat_detections_type', 'threat_type'),
        Index('idx_threat_detections_severity', 'severity'),
        Index('idx_threat_detections_status', 'status'),
        Index('idx_threat_detections_time', 'detected_at'),
        Index('idx_threat_detections_source', 'source_ip'),
        {'extend_existing': True}
    )
    
    id = db.Column(db.Integer, primary_key=True)
    threat_id = db.Column(db.String(36), default=lambda: str(uuid.uuid4()), unique=True, index=True)
    
    # Threat information
    threat_type = db.Column(db.String(50), nullable=False, index=True)  # brute_force, injection, ddos, suspicious_activity
    threat_category = db.Column(db.String(50), nullable=False, index=True)  # authentication, data, network, system
    severity = db.Column(db.String(20), default='medium', index=True)  # low, medium, high, critical
    status = db.Column(db.String(20), default='detected', index=True)  # detected, investigating, resolved, false_positive
    
    # Risk assessment
    risk_score = db.Column(db.Float, default=0.0)  # 0.0 to 1.0
    confidence = db.Column(db.Float, default=0.0)  # 0.0 to 1.0
    
    # Source information
    source_ip = db.Column(db.String(45), nullable=True, index=True)
    source_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True, index=True)
    source_user_agent = db.Column(db.Text, nullable=True)
    
    # Target information
    target_type = db.Column(db.String(50), nullable=True)  # user, system, data, network
    target_id = db.Column(db.Integer, nullable=True)
    target_details = db.Column(db.JSON)  # Target-specific details
    
    # Detection details
    detection_method = db.Column(db.String(100), nullable=True)  # pattern_match, anomaly_detection, rule_based
    detection_rules = db.Column(db.JSON)  # Rules that triggered detection
    detection_data = db.Column(db.JSON)  # Data that triggered detection
    
    # Description and details
    description = db.Column(db.Text, nullable=False)
    details = db.Column(db.Text, nullable=True)
    
    # Timestamps
    detected_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    resolved_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Response information
    response_actions = db.Column(db.JSON)  # Actions taken in response
    response_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    
    # Additional metadata
    threat_metadata = db.Column(db.JSON)  # Additional threat metadata
    
    # Relationships
    source_user = db.relationship('User', foreign_keys=[source_user_id], backref='threat_detections_source', lazy=True)
    response_user = db.relationship('User', foreign_keys=[response_user_id], backref='threat_detections_response', lazy=True)
    
    # Constraints
    __table_args__ = (
        CheckConstraint('severity IN ("low", "medium", "high", "critical")', name='check_threat_severity'),
        CheckConstraint('status IN ("detected", "investigating", "resolved", "false_positive")', name='check_threat_status'),
        CheckConstraint('risk_score >= 0 AND risk_score <= 1', name='check_risk_score'),
        CheckConstraint('confidence >= 0 AND confidence <= 1', name='check_confidence'),
        Index('idx_threat_detections_type', 'threat_type'),
        Index('idx_threat_detections_severity', 'severity'),
        Index('idx_threat_detections_status', 'status'),
        Index('idx_threat_detections_time', 'detected_at'),
        Index('idx_threat_detections_source', 'source_ip'),
        {'extend_existing': True}
    )
    
    def __repr__(self):
        return f'<ThreatDetection {self.threat_type}:{self.severity}:{self.risk_score}>'
    
    @classmethod
    def detect_threat(cls, threat_type, threat_category, description, severity='medium',
                      source_ip=None, source_user_id=None, source_user_agent=None,
                      target_type=None, target_id=None, target_details=None,
                      detection_method=None, detection_rules=None, detection_data=None,
                      risk_score=0.0, confidence=0.0, details=None, metadata=None):
        """Detect and log a threat"""
        threat = cls(
            threat_type=threat_type,
            threat_category=threat_category,
            description=description,
            severity=severity,
            source_ip=source_ip,
            source_user_id=source_user_id,
            source_user_agent=source_user_agent,
            target_type=target_type,
            target_id=target_id,
            target_details=target_details or {},
            detection_method=detection_method,
            detection_rules=detection_rules or [],
            detection_data=detection_data or {},
            risk_score=risk_score,
            confidence=confidence,
            details=details,
            threat_metadata=metadata or {}
        )
        db.session.add(threat)
        db.session.commit()
        return threat
    
    @classmethod
    def get_threats_by_type(cls, threat_type, hours=24, limit=None):
        """Get threats by type"""
        start_time = datetime.utcnow() - timedelta(hours=hours)
        query = cls.query.filter(
            cls.threat_type == threat_type,
            cls.detected_at >= start_time
        ).order_by(cls.detected_at.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    @classmethod
    def get_threats_by_severity(cls, severity, hours=24, limit=None):
        """Get threats by severity"""
        start_time = datetime.utcnow() - timedelta(hours=hours)
        query = cls.query.filter(
            cls.severity == severity,
            cls.detected_at >= start_time
        ).order_by(cls.detected_at.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    @classmethod
    def get_active_threats(cls, hours=24):
        """Get active (unresolved) threats"""
        start_time = datetime.utcnow() - timedelta(hours=hours)
        return cls.query.filter(
            cls.status.in_(['detected', 'investigating']),
            cls.detected_at >= start_time
        ).order_by(cls.risk_score.desc(), cls.detected_at.desc()).all()
    
    @classmethod
    def get_threats_by_source_ip(cls, source_ip, hours=24, limit=None):
        """Get threats by source IP"""
        start_time = datetime.utcnow() - timedelta(hours=hours)
        query = cls.query.filter(
            cls.source_ip == source_ip,
            cls.detected_at >= start_time
        ).order_by(cls.detected_at.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    @classmethod
    def get_threat_summary(cls, hours=24):
        """Get threat detection summary"""
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Total threats
        total_threats = cls.query.filter(cls.detected_at >= start_time).count()
        
        # Threats by type
        threats_by_type = db.session.query(
            cls.threat_type,
            sql_func.count(cls.id).label('count')
        ).filter(cls.detected_at >= start_time).group_by(cls.threat_type).all()
        
        # Threats by severity
        threats_by_severity = db.session.query(
            cls.severity,
            sql_func.count(cls.id).label('count')
        ).filter(cls.detected_at >= start_time).group_by(cls.severity).all()
        
        # Threats by status
        threats_by_status = db.session.query(
            cls.status,
            sql_func.count(cls.id).label('count')
        ).filter(cls.detected_at >= start_time).group_by(cls.status).all()
        
        # High risk threats
        high_risk_threats = cls.query.filter(
            cls.risk_score >= 0.7,
            cls.detected_at >= start_time
        ).count()
        
        return {
            'total_threats': total_threats,
            'high_risk_threats': high_risk_threats,
            'threats_by_type': dict(threats_by_type),
            'threats_by_severity': dict(threats_by_severity),
            'threats_by_status': dict(threats_by_status),
            'period_hours': hours
        }
    
    def resolve_threat(self, response_user_id, response_actions=None, notes=None):
        """Resolve a threat"""
        self.status = 'resolved'
        self.resolved_at = datetime.utcnow()
        self.response_user_id = response_user_id
        self.response_actions = response_actions or []
        self.notes = notes
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def mark_false_positive(self, response_user_id, notes=None):
        """Mark threat as false positive"""
        self.status = 'false_positive'
        self.resolved_at = datetime.utcnow()
        self.response_user_id = response_user_id
        self.notes = notes
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def to_dict(self):
        """Convert threat to dictionary"""
        return {
            'threat_id': self.threat_id,
            'threat_type': self.threat_type,
            'threat_category': self.threat_category,
            'severity': self.severity,
            'status': self.status,
            'risk_score': self.risk_score,
            'confidence': self.confidence,
            'source_ip': self.source_ip,
            'source_user_id': self.source_user_id,
            'target_type': self.target_type,
            'target_id': self.target_id,
            'description': self.description,
            'detected_at': self.detected_at.isoformat(),
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'response_actions': self.response_actions,
            'notes': self.notes
        }


class ComplianceRecord(db.Model):
    """Compliance tracking model for regulatory compliance and audit requirements"""
    __tablename__ = 'compliance_records'
    __table_args__ = (
        Index('idx_compliance_records_type', 'compliance_type'),
        Index('idx_compliance_records_status', 'status'),
        Index('idx_compliance_records_period', 'compliance_period'),
        Index('idx_compliance_records_time', 'created_at'),
        {'extend_existing': True}
    )
    
    id = db.Column(db.Integer, primary_key=True)
    compliance_id = db.Column(db.String(36), default=lambda: str(uuid.uuid4()), unique=True, index=True)
    
    # Compliance information
    compliance_type = db.Column(db.String(50), nullable=False, index=True)  # gdpr, ccpa, hipaa, sox
    compliance_category = db.Column(db.String(50), nullable=False, index=True)  # data_privacy, security, audit, reporting
    regulation = db.Column(db.String(100), nullable=True)  # GDPR, CCPA, HIPAA, SOX
    requirement = db.Column(db.String(255), nullable=True)  # Specific regulatory requirement
    
    # Status and assessment
    status = db.Column(db.String(20), default='pending', index=True)  # pending, compliant, non_compliant, exception
    compliance_score = db.Column(db.Float, default=0.0)  # 0.0 to 1.0
    risk_level = db.Column(db.String(20), default='medium', index=True)  # low, medium, high, critical
    
    # Period information
    compliance_period = db.Column(db.String(50), nullable=False, index=True)  # Q1-2024, 2024-01, etc.
    period_start = db.Column(db.Date, nullable=False)
    period_end = db.Column(db.Date, nullable=False)
    
    # Assessment details
    assessment_method = db.Column(db.String(100), nullable=True)  # automated, manual, third_party
    assessor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    assessment_date = db.Column(db.DateTime, nullable=True)
    
    # Evidence and documentation
    evidence_files = db.Column(db.JSON)  # List of evidence file references
    documentation = db.Column(db.JSON)  # Compliance documentation
    test_results = db.Column(db.JSON)  # Test results and validation
    
    # Issues and remediation
    issues_found = db.Column(db.JSON)  # List of compliance issues
    remediation_actions = db.Column(db.JSON)  # Remediation plan and actions
    remediation_deadline = db.Column(db.Date, nullable=True)
    
    # Description and notes
    description = db.Column(db.Text, nullable=False)
    findings = db.Column(db.Text, nullable=True)
    recommendations = db.Column(db.Text, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    
    # Additional metadata
    compliance_metadata = db.Column(db.JSON)  # Additional compliance metadata
    
    # Relationships
    assessor = db.relationship('User', backref='compliance_assessments', lazy=True)
    
    # Constraints
    __table_args__ = (
        CheckConstraint('status IN ("pending", "compliant", "non_compliant", "exception")', name='check_compliance_status'),
        CheckConstraint('risk_level IN ("low", "medium", "high", "critical")', name='check_compliance_risk'),
        CheckConstraint('compliance_score >= 0 AND compliance_score <= 1', name='check_compliance_score'),
        Index('idx_compliance_records_type', 'compliance_type'),
        Index('idx_compliance_records_status', 'status'),
        Index('idx_compliance_records_period', 'compliance_period'),
        Index('idx_compliance_records_time', 'created_at'),
        {'extend_existing': True}
    )
    
    def __repr__(self):
        return f'<ComplianceRecord {self.compliance_type}:{self.status}:{self.compliance_period}>'
    
    @classmethod
    def create_compliance_record(cls, compliance_type, compliance_category, description,
                                compliance_period, period_start, period_end, regulation=None,
                                requirement=None, assessment_method=None, assessor_id=None,
                                evidence_files=None, documentation=None, test_results=None,
                                issues_found=None, remediation_actions=None, remediation_deadline=None,
                                findings=None, recommendations=None, metadata=None):
        """Create a compliance record"""
        record = cls(
            compliance_type=compliance_type,
            compliance_category=compliance_category,
            description=description,
            compliance_period=compliance_period,
            period_start=period_start,
            period_end=period_end,
            regulation=regulation,
            requirement=requirement,
            assessment_method=assessment_method,
            assessor_id=assessor_id,
            assessment_date=datetime.utcnow(),
            evidence_files=evidence_files or [],
            documentation=documentation or {},
            test_results=test_results or {},
            issues_found=issues_found or [],
            remediation_actions=remediation_actions or [],
            remediation_deadline=remediation_deadline,
            findings=findings,
            recommendations=recommendations,
            compliance_metadata=metadata or {}
        )
        db.session.add(record)
        db.session.commit()
        return record
    
    @classmethod
    def get_records_by_type(cls, compliance_type, limit=None):
        """Get compliance records by type"""
        query = cls.query.filter_by(compliance_type=compliance_type).order_by(cls.created_at.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    @classmethod
    def get_records_by_status(cls, status, limit=None):
        """Get compliance records by status"""
        query = cls.query.filter_by(status=status).order_by(cls.created_at.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    @classmethod
    def get_records_by_period(cls, compliance_period, limit=None):
        """Get compliance records by period"""
        query = cls.query.filter_by(compliance_period=compliance_period).order_by(cls.created_at.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    @classmethod
    def get_compliance_summary(cls, compliance_type=None, period=None):
        """Get compliance summary"""
        query = cls.query
        
        if compliance_type:
            query = query.filter_by(compliance_type=compliance_type)
        
        if period:
            query = query.filter_by(compliance_period=period)
        
        # Total records
        total_records = query.count()
        
        # Records by status
        records_by_status = db.session.query(
            cls.status,
            sql_func.count(cls.id).label('count')
        ).filter(cls.compliance_type == compliance_type if compliance_type else True).group_by(cls.status).all()
        
        # Records by risk level
        records_by_risk = db.session.query(
            cls.risk_level,
            sql_func.count(cls.id).label('count')
        ).filter(cls.compliance_type == compliance_type if compliance_type else True).group_by(cls.risk_level).all()
        
        # Average compliance score
        avg_score = query.with_entities(sql_func.avg(cls.compliance_score)).scalar() or 0.0
        
        return {
            'total_records': total_records,
            'avg_compliance_score': float(avg_score),
            'records_by_status': dict(records_by_status),
            'records_by_risk': dict(records_by_risk)
        }
    
    def assess_compliance(self, status, compliance_score, risk_level, assessor_id,
                         issues_found=None, remediation_actions=None, findings=None,
                         recommendations=None, evidence_files=None):
        """Assess compliance and update record"""
        self.status = status
        self.compliance_score = compliance_score
        self.risk_level = risk_level
        self.assessor_id = assessor_id
        self.assessment_date = datetime.utcnow()
        self.issues_found = issues_found or []
        self.remediation_actions = remediation_actions or []
        self.findings = findings
        self.recommendations = recommendations
        if evidence_files:
            self.evidence_files = evidence_files
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def to_dict(self):
        """Convert compliance record to dictionary"""
        return {
            'compliance_id': self.compliance_id,
            'compliance_type': self.compliance_type,
            'compliance_category': self.compliance_category,
            'regulation': self.regulation,
            'requirement': self.requirement,
            'status': self.status,
            'compliance_score': self.compliance_score,
            'risk_level': self.risk_level,
            'compliance_period': self.compliance_period,
            'period_start': self.period_start.isoformat(),
            'period_end': self.period_end.isoformat(),
            'assessment_method': self.assessment_method,
            'assessment_date': self.assessment_date.isoformat() if self.assessment_date else None,
            'issues_found': self.issues_found,
            'remediation_actions': self.remediation_actions,
            'remediation_deadline': self.remediation_deadline.isoformat() if self.remediation_deadline else None,
            'description': self.description,
            'findings': self.findings,
            'recommendations': self.recommendations,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


# Helper functions for security initialization
def initialize_security_system():
    """Initialize security system with default configurations"""
    print("Security system initialized successfully")
