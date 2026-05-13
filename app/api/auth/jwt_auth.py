"""
JWT Authentication System
Provides JWT token authentication for API access
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import (
    JWTManager, create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, get_jwt,
    verify_jwt_in_request
)
from datetime import datetime, timedelta
import secrets
import hashlib
from functools import wraps

from app import db
from app.models import User
from .models import APIKey, APIUsage
from .services import JWTService

jwt_auth_bp = Blueprint('jwt_auth', __name__, url_prefix='/api/auth/jwt')

# Initialize JWT Manager
jwt = JWTManager()

def generate_jwt_secret():
    """Generate a secure JWT secret"""
    return secrets.token_urlsafe(64)

def hash_api_key(key):
    """Hash API key for storage"""
    return hashlib.sha256(key.encode()).hexdigest()

def generate_api_key():
    """Generate a new API key"""
    return f"ak_{secrets.token_urlsafe(32)}"

@jwt_auth_bp.route('/login', methods=['POST'])
def login():
    """Login with JWT tokens"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('username') or not data.get('password'):
            return jsonify({'error': 'Username and password required'}), 400
        
        # Authenticate user
        user = User.query.filter_by(username=data['username']).first()
        if not user or not user.check_password(data['password']):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Create JWT tokens
        additional_claims = {
            'user_id': user.id,
            'username': user.username,
            'role': user.role if hasattr(user, 'role') else 'user',
            'permissions': getattr(user, 'permissions', [])
        }
        
        access_token = create_access_token(
            identity=user.id,
            additional_claims=additional_claims,
            expires_delta=timedelta(hours=1)
        )
        
        refresh_token = create_refresh_token(
            identity=user.id,
            expires_delta=timedelta(days=30)
        )
        
        return jsonify({
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'Bearer',
            'expires_in': 3600,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': getattr(user, 'role', 'user')
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@jwt_auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh JWT token"""
    try:
        current_user_id = get_jwt_identity()
        
        # Get user
        user = User.query.get(current_user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Create new access token
        additional_claims = {
            'user_id': user.id,
            'username': user.username,
            'role': user.role if hasattr(user, 'role') else 'user',
            'permissions': getattr(user, 'permissions', [])
        }
        
        access_token = create_access_token(
            identity=user.id,
            additional_claims=additional_claims,
            expires_delta=timedelta(hours=1)
        )
        
        return jsonify({
            'access_token': access_token,
            'token_type': 'Bearer',
            'expires_in': 3600
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@jwt_auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Logout (revoke JWT token)"""
    try:
        # In a real implementation, you would add the token to a blacklist
        # For now, we'll just return success
        return jsonify({'message': 'Logged out successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@jwt_auth_bp.route('/verify', methods=['POST'])
@jwt_required()
def verify():
    """Verify JWT token"""
    try:
        current_user_id = get_jwt_identity()
        claims = get_jwt()
        
        user = User.query.get(current_user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'valid': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': getattr(user, 'role', 'user')
            },
            'claims': claims
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# API Key Management

@jwt_auth_bp.route('/api-keys', methods=['POST'])
@jwt_required()
def create_api_key():
    """Create a new API key"""
    try:
        data = request.get_json()
        current_user_id = get_jwt_identity()
        
        # Validate required fields
        if not data.get('name'):
            return jsonify({'error': 'API key name required'}), 400
        
        # Generate API key
        api_key = generate_api_key()
        key_hash = hash_api_key(api_key)
        
        # Create API key record
        api_key_record = APIKey(
            name=data['name'],
            key_hash=key_hash,
            permissions=data.get('permissions', []),
            user_id=current_user_id,
            expires_at=datetime.utcnow() + timedelta(days=365),
            created_at=datetime.utcnow()
        )
        
        db.session.add(api_key_record)
        db.session.commit()
        
        return jsonify({
            'id': api_key_record.id,
            'name': api_key_record.name,
            'api_key': api_key,  # Only show once during creation
            'expires_at': api_key_record.expires_at.isoformat(),
            'permissions': api_key_record.permissions
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@jwt_auth_bp.route('/api-keys', methods=['GET'])
@jwt_required()
def list_api_keys():
    """List user's API keys"""
    try:
        current_user_id = get_jwt_identity()
        
        api_keys = APIKey.query.filter_by(
            user_id=current_user_id,
            is_active=True
        ).order_by(APIKey.created_at.desc()).all()
        
        return jsonify([{
            'id': key.id,
            'name': key.name,
            'created_at': key.created_at.isoformat(),
            'expires_at': key.expires_at.isoformat(),
            'last_used_at': key.last_used_at.isoformat() if key.last_used_at else None,
            'usage_count': key.usage_count,
            'permissions': key.permissions
        } for key in api_keys])
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@jwt_auth_bp.route('/api-keys/<int:key_id>', methods=['DELETE'])
@jwt_required()
def revoke_api_key(key_id):
    """Revoke an API key"""
    try:
        current_user_id = get_jwt_identity()
        
        api_key = APIKey.query.filter_by(
            id=key_id,
            user_id=current_user_id,
            is_active=True
        ).first()
        
        if not api_key:
            return jsonify({'error': 'API key not found'}), 404
        
        # Revoke API key
        api_key.is_active = False
        api_key.revoked_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'message': 'API key revoked successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@jwt_auth_bp.route('/api-keys/<int:key_id>/rotate', methods=['POST'])
@jwt_required()
def rotate_api_key(key_id):
    """Rotate an API key"""
    try:
        current_user_id = get_jwt_identity()
        
        api_key = APIKey.query.filter_by(
            id=key_id,
            user_id=current_user_id,
            is_active=True
        ).first()
        
        if not api_key:
            return jsonify({'error': 'API key not found'}), 404
        
        # Generate new API key
        new_api_key = generate_api_key()
        new_key_hash = hash_api_key(new_api_key)
        
        # Update API key
        api_key.key_hash = new_key_hash
        api_key.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'id': api_key.id,
            'name': api_key.name,
            'api_key': new_api_key,  # Only show once during rotation
            'expires_at': api_key.expires_at.isoformat(),
            'permissions': api_key.permissions
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# JWT Error Handlers

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    """Handle expired JWT token"""
    return jsonify({'error': 'Token has expired'}), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    """Handle invalid JWT token"""
    return jsonify({'error': 'Invalid token'}), 401

@jwt.unauthorized_loader
def missing_token_callback(error):
    """Handle missing JWT token"""
    return jsonify({'error': 'Authorization token required'}), 401

@jwt.needs_fresh_token_loader
def token_not_fresh_callback(jwt_header, jwt_payload):
    """Handle non-fresh JWT token"""
    return jsonify({'error': 'Fresh token required'}), 401

@jwt.revoked_token_loader
def revoked_token_callback(jwt_header, jwt_payload):
    """Handle revoked JWT token"""
    return jsonify({'error': 'Token has been revoked'}), 401

# Decorators for API authentication

def api_key_required(f):
    """Decorator to require API key authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get API key from header
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return jsonify({'error': 'API key required'}), 401
        
        # Hash the key and check database
        key_hash = hash_api_key(api_key)
        key_record = APIKey.query.filter_by(
            key_hash=key_hash,
            is_active=True
        ).first()
        
        if not key_record:
            return jsonify({'error': 'Invalid API key'}), 401
        
        # Check if key is expired
        if key_record.expires_at and key_record.expires_at < datetime.utcnow():
            return jsonify({'error': 'API key expired'}), 401
        
        # Update usage statistics
        key_record.last_used_at = datetime.utcnow()
        key_record.usage_count += 1
        db.session.commit()
        
        # Record API usage
        usage = APIUsage(
            api_key_id=key_record.id,
            endpoint=request.endpoint,
            request_count=1,
            last_request=datetime.utcnow()
        )
        db.session.add(usage)
        db.session.commit()
        
        # Add user to request context
        request.current_user = key_record.user
        request.current_api_key = key_record
        
        return f(*args, **kwargs)
    
    return decorated_function

def permission_required(permission):
    """Decorator to require specific permission"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check JWT token first
            try:
                verify_jwt_in_request()
                current_user_id = get_jwt_identity()
                claims = get_jwt()
                
                # Check if user has required permission
                user_permissions = claims.get('permissions', [])
                if permission not in user_permissions:
                    return jsonify({'error': 'Insufficient permissions'}), 403
                
                # Add user to request context
                request.current_user = User.query.get(current_user_id)
                
            except Exception:
                # Check API key if JWT fails
                api_key = request.headers.get('X-API-Key')
                if api_key:
                    key_hash = hash_api_key(api_key)
                    key_record = APIKey.query.filter_by(
                        key_hash=key_hash,
                        is_active=True
                    ).first()
                    
                    if key_record and permission in key_record.permissions:
                        request.current_user = key_record.user
                        request.current_api_key = key_record
                    else:
                        return jsonify({'error': 'Insufficient permissions'}), 403
                else:
                    return jsonify({'error': 'Authentication required'}), 401
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def rate_limit_required(limit):
    """Decorator to apply rate limiting"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # This would integrate with Flask-Limiter
            # For now, we'll just pass through
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

# Initialize JWT
def init_jwt(app):
    """Initialize JWT manager"""
    jwt.init_app(app)
    
    # Set JWT configuration
    app.config['JWT_SECRET_KEY'] = app.config.get('JWT_SECRET_KEY', generate_jwt_secret())
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)
    app.config['JWT_ALGORITHM'] = 'HS256'
    app.config['JWT_BLACKLIST_ENABLED'] = True
    app.config['JWT_BLACKLIST_TOKEN_CHECKS'] = ['access', 'refresh']
