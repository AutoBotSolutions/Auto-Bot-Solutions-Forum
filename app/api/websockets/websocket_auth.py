"""
WebSocket Authentication

Handles authentication and authorization for WebSocket connections.
"""

import jwt
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from functools import wraps

from flask import request, g
from app.api.auth.services import APIKeyService
from app.models import User

logger = logging.getLogger(__name__)

class WebSocketAuth:
    """WebSocket authentication and authorization"""
    
    def __init__(self, secret_key: str = None):
        self.secret_key = secret_key
        self.authenticated_connections: Dict[str, Dict[str, Any]] = {}
    
    def authenticate_connection(self, sid: str, auth_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Authenticate WebSocket connection"""
        try:
            auth_method = auth_data.get('method')
            
            if auth_method == 'jwt':
                return self._authenticate_jwt(sid, auth_data)
            elif auth_method == 'api_key':
                return self._authenticate_api_key(sid, auth_data)
            elif auth_method == 'session':
                return self._authenticate_session(sid, auth_data)
            else:
                logger.warning(f"Unknown auth method: {auth_method}")
                return None
        
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return None
    
    def _authenticate_jwt(self, sid: str, auth_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Authenticate with JWT token"""
        try:
            token = auth_data.get('token')
            if not token:
                return None
            
            # Verify JWT token
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=['HS256'],
                options={'verify_exp': True}
            )
            
            user_id = payload.get('user_id')
            if not user_id:
                return None
            
            # Get user from database
            user = User.query.get(user_id)
            if not user or not user.is_active:
                return None
            
            auth_info = {
                'user_id': user_id,
                'username': user.username,
                'email': user.email,
                'roles': payload.get('roles', []),
                'permissions': payload.get('permissions', []),
                'auth_method': 'jwt',
                'authenticated_at': datetime.utcnow().isoformat()
            }
            
            # Store authentication info
            self.authenticated_connections[sid] = auth_info
            
            logger.info(f"WebSocket authenticated with JWT: user_id={user_id}, sid={sid}")
            return auth_info
        
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {e}")
            return None
        except Exception as e:
            logger.error(f"JWT authentication error: {e}")
            return None
    
    def _authenticate_api_key(self, sid: str, auth_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Authenticate with API key"""
        try:
            api_key = auth_data.get('api_key')
            if not api_key:
                return None
            
            # Validate API key
            key_record = APIKeyService.validate_key(api_key)
            if not key_record or not key_record.is_active:
                return None
            
            user = key_record.user
            if not user or not user.is_active:
                return None
            
            auth_info = {
                'user_id': user.id,
                'username': user.username,
                'email': user.email,
                'permissions': key_record.permissions,
                'api_key_id': key_record.id,
                'api_key_name': key_record.name,
                'auth_method': 'api_key',
                'authenticated_at': datetime.utcnow().isoformat()
            }
            
            # Store authentication info
            self.authenticated_connections[sid] = auth_info
            
            # Update API key usage
            APIKeyService.update_usage(key_record.id, 'websocket_connect')
            
            logger.info(f"WebSocket authenticated with API key: user_id={user.id}, sid={sid}")
            return auth_info
        
        except Exception as e:
            logger.error(f"API key authentication error: {e}")
            return None
    
    def _authenticate_session(self, sid: str, auth_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Authenticate with session"""
        try:
            session_id = auth_data.get('session_id')
            if not session_id:
                return None
            
            # This would integrate with Flask session system
            # For now, return None as session auth is not implemented
            logger.warning("Session authentication not implemented")
            return None
        
        except Exception as e:
            logger.error(f"Session authentication error: {e}")
            return None
    
    def get_connection_auth(self, sid: str) -> Optional[Dict[str, Any]]:
        """Get authentication info for connection"""
        return self.authenticated_connections.get(sid)
    
    def is_authenticated(self, sid: str) -> bool:
        """Check if connection is authenticated"""
        return sid in self.authenticated_connections
    
    def has_permission(self, sid: str, permission: str) -> bool:
        """Check if connection has specific permission"""
        auth_info = self.get_connection_auth(sid)
        if not auth_info:
            return False
        
        permissions = auth_info.get('permissions', [])
        return permission in permissions
    
    def has_role(self, sid: str, role: str) -> bool:
        """Check if connection has specific role"""
        auth_info = self.get_connection_auth(sid)
        if not auth_info:
            return False
        
        roles = auth_info.get('roles', [])
        return role in roles
    
    def logout_connection(self, sid: str):
        """Logout connection"""
        if sid in self.authenticated_connections:
            del self.authenticated_connections[sid]
            logger.info(f"WebSocket logged out: sid={sid}")
    
    def get_user_connections(self, user_id: int) -> List[str]:
        """Get all authenticated connections for a user"""
        connections = []
        for sid, auth_info in self.authenticated_connections.items():
            if auth_info.get('user_id') == user_id:
                connections.append(sid)
        return connections
    
    def get_auth_stats(self) -> Dict[str, Any]:
        """Get authentication statistics"""
        auth_methods = {}
        user_counts = {}
        
        for auth_info in self.authenticated_connections.values():
            method = auth_info.get('auth_method', 'unknown')
            auth_methods[method] = auth_methods.get(method, 0) + 1
            
            user_id = auth_info.get('user_id')
            if user_id:
                user_counts[user_id] = user_counts.get(user_id, 0) + 1
        
        return {
            'total_authenticated': len(self.authenticated_connections),
            'auth_methods': auth_methods,
            'unique_users': len(user_counts),
            'connections_per_user': user_counts
        }

def ws_authenticated(f):
    """Decorator to require WebSocket authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask_socketio import emit
        
        sid = request.sid
        ws_auth = g.get('ws_auth')
        
        if not ws_auth or not ws_auth.is_authenticated(sid):
            emit('error', {
                'message': 'Authentication required',
                'code': 'AUTH_REQUIRED'
            }, room=sid)
            return
        
        return f(*args, **kwargs)
    return decorated_function

def ws_require_permission(permission: str):
    """Decorator to require specific permission"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from flask_socketio import emit
            
            sid = request.sid
            ws_auth = g.get('ws_auth')
            
            if not ws_auth or not ws_auth.has_permission(sid, permission):
                emit('error', {
                    'message': f'Permission required: {permission}',
                    'code': 'PERMISSION_DENIED'
                }, room=sid)
                return
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def ws_require_role(role: str):
    """Decorator to require specific role"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from flask_socketio import emit
            
            sid = request.sid
            ws_auth = g.get('ws_auth')
            
            if not ws_auth or not ws_auth.has_role(sid, role):
                emit('error', {
                    'message': f'Role required: {role}',
                    'code': 'ROLE_REQUIRED'
                }, room=sid)
                return
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def ws_user_only(f):
    """Decorator to require user authentication (no admin)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask_socketio import emit
        
        sid = request.sid
        ws_auth = g.get('ws_auth')
        
        if not ws_auth or not ws_auth.is_authenticated(sid):
            emit('error', {
                'message': 'Authentication required',
                'code': 'AUTH_REQUIRED'
            }, room=sid)
            return
        
        auth_info = ws_auth.get_connection_auth(sid)
        if auth_info and ws_auth.has_role(sid, 'admin'):
            emit('error', {
                'message': 'This endpoint is for regular users only',
                'code': 'ADMIN_NOT_ALLOWED'
            }, room=sid)
            return
        
        return f(*args, **kwargs)
    return decorated_function

def ws_admin_only(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask_socketio import emit
        
        sid = request.sid
        ws_auth = g.get('ws_auth')
        
        if not ws_auth or not ws_auth.has_role(sid, 'admin'):
            emit('error', {
                'message': 'Admin role required',
                'code': 'ADMIN_REQUIRED'
            }, room=sid)
            return
        
        return f(*args, **kwargs)
    return decorated_function

class WebSocketRateLimiter:
    """Rate limiting for WebSocket connections"""
    
    def __init__(self, max_messages_per_minute: int = 60):
        self.max_messages = max_messages_per_minute
        self.message_counts: Dict[str, List[datetime]] = {}
    
    def check_rate_limit(self, sid: str) -> bool:
        """Check if connection is within rate limit"""
        now = datetime.utcnow()
        
        if sid not in self.message_counts:
            self.message_counts[sid] = []
        
        # Remove old messages (older than 1 minute)
        cutoff = now - timedelta(minutes=1)
        self.message_counts[sid] = [
            timestamp for timestamp in self.message_counts[sid] 
            if timestamp > cutoff
        ]
        
        # Check rate limit
        if len(self.message_counts[sid]) >= self.max_messages:
            return False
        
        # Add current message
        self.message_counts[sid].append(now)
        return True
    
    def get_connection_stats(self, sid: str) -> Dict[str, Any]:
        """Get rate limiting stats for connection"""
        if sid not in self.message_counts:
            return {'messages_per_minute': 0}
        
        now = datetime.utcnow()
        cutoff = now - timedelta(minutes=1)
        recent_messages = [
            timestamp for timestamp in self.message_counts[sid] 
            if timestamp > cutoff
        ]
        
        return {
            'messages_per_minute': len(recent_messages),
            'max_messages_per_minute': self.max_messages,
            'rate_limited': len(recent_messages) >= self.max_messages
        }
    
    def cleanup_old_connections(self):
        """Clean up old connection data"""
        cutoff = datetime.utcnow() - timedelta(hours=1)
        
        old_sids = []
        for sid, timestamps in self.message_counts.items():
            if timestamps and max(timestamps) < cutoff:
                old_sids.append(sid)
        
        for sid in old_sids:
            del self.message_counts[sid]
        
        return len(old_sids)
