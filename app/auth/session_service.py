"""
Session Management Service

Handles Redis-based session storage, analytics, and monitoring
for the Auto Bot Solutions Forum.
"""

import json
import hashlib
from datetime import datetime, timedelta
from flask import current_app, request, session
from app import db
from app.models import User, UserSession, SessionAnalytics, SecurityEvent
import logging

logger = logging.getLogger(__name__)

class SessionManager:
    """Advanced session management service"""
    
    def __init__(self):
        self.redis_client = None
        self._init_redis()
    
    def _init_redis(self):
        """Initialize Redis client for session storage"""
        try:
            import redis
            redis_url = current_app.config.get('REDIS_SESSION_URL', 'redis://localhost:6379/1')
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            # Test connection
            self.redis_client.ping()
            logger.info("Redis session storage initialized")
        except Exception as e:
            logger.warning(f"Redis not available for session storage: {str(e)}")
            self.redis_client = None
    
    def create_session(self, user, persistent=False):
        """Create new user session with tracking"""
        # Generate session ID
        session_id = session.sid if 'sid' in session else self._generate_session_id()
        
        # Get request information
        ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        user_agent = request.headers.get('User-Agent')
        device_fingerprint = self._generate_device_fingerprint(user_agent, ip_address)
        
        # Create session in database
        db_session = user.create_session(
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent,
            device_fingerprint=device_fingerprint,
            persistent=persistent
        )
        
        # Store session data in Redis if available
        if self.redis_client:
            session_data = {
                'user_id': user.id,
                'username': user.username,
                'ip_address': ip_address,
                'user_agent': user_agent,
                'device_fingerprint': device_fingerprint,
                'persistent': persistent,
                'created_at': db_session.created_at.isoformat(),
                'expires_at': db_session.expires_at.isoformat()
            }
            self.redis_client.setex(
                f"session:{session_id}",
                int((db_session.expires_at - datetime.utcnow()).total_seconds()),
                json.dumps(session_data)
            )
        
        # Log security event
        user.add_security_event(
            event_type='login',
            severity='info',
            description=f"User logged in from {ip_address}",
            ip_address=ip_address,
            user_agent=user_agent,
            metadata={
                'session_id': session_id,
                'persistent': persistent,
                'device_fingerprint': device_fingerprint
            }
        )
        
        return db_session
    
    def get_session(self, session_id):
        """Get session information"""
        # Try Redis first
        if self.redis_client:
            session_data = self.redis_client.get(f"session:{session_id}")
            if session_data:
                return json.loads(session_data)
        
        # Fallback to database
        db_session = UserSession.query.filter_by(session_id=session_id).first()
        if db_session and db_session.is_active and not db_session.is_expired():
            return {
                'user_id': db_session.user_id,
                'session_id': db_session.session_id,
                'ip_address': db_session.ip_address,
                'user_agent': db_session.user_agent,
                'device_fingerprint': db_session.device_fingerprint,
                'persistent': db_session.is_persistent,
                'created_at': db_session.created_at.isoformat(),
                'expires_at': db_session.expires_at.isoformat() if db_session.expires_at else None
            }
        return None
    
    def update_session_activity(self, session_id):
        """Update session activity timestamp"""
        # Update database
        db_session = UserSession.query.filter_by(session_id=session_id).first()
        if db_session:
            db_session.update_activity()
        
        # Update Redis TTL
        if self.redis_client:
            session_data = self.redis_client.get(f"session:{session_id}")
            if session_data:
                data = json.loads(session_data)
                # Extend TTL by 30 minutes
                self.redis_client.expire(f"session:{session_id}", 1800)
    
    def revoke_session(self, session_id, user_id=None):
        """Revoke specific session"""
        # Update database
        query = UserSession.query.filter_by(session_id=session_id)
        if user_id:
            query = query.filter_by(user_id=user_id)
        
        db_session = query.first()
        if db_session:
            db_session.revoke()
            
            # Remove from Redis
            if self.redis_client:
                self.redis_client.delete(f"session:{session_id}")
            
            # Log security event
            if db_session.user:
                db_session.user.add_security_event(
                    event_type='session_revoked',
                    severity='info',
                    description=f"Session {session_id} revoked",
                    metadata={'session_id': session_id}
                )
            
            return True
        return False
    
    def revoke_all_user_sessions(self, user_id, except_session_id=None):
        """Revoke all sessions for a user"""
        query = UserSession.query.filter_by(user_id=user_id, is_active=True)
        if except_session_id:
            query = query.filter(UserSession.session_id != except_session_id)
        
        sessions = query.all()
        revoked_count = 0
        
        for session in sessions:
            session.revoke()
            # Remove from Redis
            if self.redis_client:
                self.redis_client.delete(f"session:{session.session_id}")
            revoked_count += 1
        
        # Log security event
        user = User.query.get(user_id)
        if user:
            user.add_security_event(
                event_type='all_sessions_revoked',
                severity='warning',
                description=f"All sessions revoked ({revoked_count} sessions)",
                metadata={'revoked_count': revoked_count, 'except_session': except_session_id}
            )
        
        return revoked_count
    
    def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        expired_sessions = UserSession.query.filter(
            UserSession.expires_at < datetime.utcnow()
        ).all()
        
        cleaned_count = 0
        for session in expired_sessions:
            db.session.delete(session)
            # Remove from Redis
            if self.redis_client:
                self.redis_client.delete(f"session:{session.session_id}")
            cleaned_count += 1
        
        db.session.commit()
        logger.info(f"Cleaned up {cleaned_count} expired sessions")
        return cleaned_count
    
    def get_session_analytics(self, date=None):
        """Get session analytics for a specific date"""
        if date is None:
            date = datetime.utcnow().date()
        
        # Get or create analytics record
        analytics = SessionAnalytics.query.filter_by(date=date).first()
        if not analytics:
            analytics = SessionAnalytics(date=date)
            db.session.add(analytics)
        
        # Calculate analytics
        total_sessions = UserSession.query.filter(
            UserSession.created_at >= date,
            UserSession.created_at < date + timedelta(days=1)
        ).count()
        
        active_sessions = UserSession.query.filter(
            UserSession.is_active == True,
            UserSession.expires_at > datetime.utcnow()
        ).count()
        
        unique_users = db.session.query(
            UserSession.user_id
        ).filter(
            UserSession.created_at >= date,
            UserSession.created_at < date + timedelta(days=1)
        ).distinct().count()
        
        # Calculate average session duration
        completed_sessions = UserSession.query.filter(
            UserSession.created_at >= date,
            UserSession.created_at < date + timedelta(days=1),
            UserSession.is_active == False
        ).all()
        
        if completed_sessions:
            durations = []
            for session in completed_sessions:
                duration = (session.updated_at - session.created_at).total_seconds() / 60
                durations.append(duration)
            avg_duration = sum(durations) / len(durations)
        else:
            avg_duration = 0
        
        # Get top devices
        devices = db.session.query(
            UserSession.user_agent,
            db.func.count(UserSession.id).label('count')
        ).filter(
            UserSession.created_at >= date,
            UserSession.created_at < date + timedelta(days=1)
        ).group_by(UserSession.user_agent).order_by(
            db.func.count(UserSession.id).desc()
        ).limit(5).all()
        
        top_devices = {device[0]: device[1] for device in devices}
        
        # Get top locations
        locations = db.session.query(
            UserSession.location,
            db.func.count(UserSession.id).label('count')
        ).filter(
            UserSession.created_at >= date,
            UserSession.created_at < date + timedelta(days=1)
        ).group_by(UserSession.location).order_by(
            db.func.count(UserSession.id).desc()
        ).limit(5).all()
        
        top_locations = {location[0]: location[1] for location in locations}
        
        # Update analytics
        analytics.total_sessions = total_sessions
        analytics.active_sessions = active_sessions
        analytics.unique_users = unique_users
        analytics.average_session_duration = avg_duration
        analytics.set_top_devices(top_devices)
        analytics.set_top_locations(top_locations)
        
        db.session.commit()
        return analytics
    
    def get_user_session_analytics(self, user_id):
        """Get session analytics for a specific user"""
        user = User.query.get(user_id)
        if not user:
            return None
        
        return user.get_session_analytics()
    
    def detect_suspicious_activity(self, session_id, user_id):
        """Detect suspicious activity in session"""
        session = self.get_session(session_id)
        if not session:
            return False
        
        user = User.query.get(user_id)
        if not user:
            return False
        
        suspicious = False
        reasons = []
        
        # Check for multiple concurrent sessions from different IPs
        user_sessions = user.get_active_sessions()
        if len(user_sessions) > 1:
            ip_addresses = set(s['ip_address'] for s in user_sessions)
            if len(ip_addresses) > 1:
                suspicious = True
                reasons.append("Multiple IPs")
        
        # Check for unusual user agent
        recent_sessions = user.get_security_events(event_type='login', limit=10)
        if recent_sessions:
            recent_agents = [event.get_metadata().get('device_fingerprint') 
                             for event in recent_sessions 
                             if event.get_metadata()]
            current_fingerprint = session.get('device_fingerprint')
            if current_fingerprint not in recent_agents:
                suspicious = True
                reasons.append("New device")
        
        # Check for rapid login attempts
        recent_logins = user.get_security_events(event_type='login', limit=5)
        if len(recent_logins) >= 5:
            time_diff = (datetime.utcnow() - recent_logins[-1].created_at).total_seconds()
            if time_diff < 300:  # 5 minutes
                suspicious = True
                reasons.append("Rapid logins")
        
        # Log suspicious activity
        if suspicious:
            user.add_security_event(
                event_type='suspicious_activity',
                severity='warning',
                description=f"Suspicious activity detected: {', '.join(reasons)}",
                ip_address=session.get('ip_address'),
                user_agent=session.get('user_agent'),
                metadata={
                    'reasons': reasons,
                    'session_id': session_id,
                    'concurrent_sessions': len(user_sessions)
                }
            )
        
        return suspicious
    
    def _generate_session_id(self):
        """Generate secure session ID"""
        import secrets
        return secrets.token_urlsafe(32)
    
    def _generate_device_fingerprint(self, user_agent, ip_address):
        """Generate device fingerprint from user agent and IP"""
        if not user_agent:
            return hashlib.md5(ip_address.encode()).hexdigest()
        
        # Extract key parts from user agent
        import re
        # Extract browser name and version
        browser_match = re.search(r'(Chrome|Firefox|Safari|Edge|Opera)[/\s]\d+', user_agent)
        browser = browser_match.group(0) if browser_match else 'Unknown'
        
        # Extract OS
        os_match = re.search(r'(Windows|Mac|Linux|Android|iOS)', user_agent)
        os = os_match.group(0) if os_match else 'Unknown'
        
        # Create fingerprint
        fingerprint_data = f"{browser}|{os}|{ip_address}"
        return hashlib.sha256(fingerprint_data.encode()).hexdigest()[:32]

# Global session manager instance
session_manager = SessionManager()
