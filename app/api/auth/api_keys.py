"""
API Key Management System
Provides API key authentication and management for API access
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
import secrets
import hashlib
from functools import wraps

from app import db
from app.models import User
from .models import APIKey, APIUsage
from .services import APIKeyService

api_keys_bp = Blueprint('api_keys', __name__, url_prefix='/api/auth/keys')

def generate_api_key():
    """Generate a new API key"""
    return f"ak_{secrets.token_urlsafe(32)}"

def hash_api_key(key):
    """Hash API key for storage"""
    return hashlib.sha256(key.encode()).hexdigest()

def verify_api_key(api_key, key_hash):
    """Verify API key against hash"""
    return hashlib.sha256(api_key.encode()).hexdigest() == key_hash

@api_keys_bp.route('/', methods=['POST'])
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
        api_key_record = APIKeyService.create_key(
            name=data['name'],
            user_id=current_user_id,
            permissions=data.get('permissions', []),
            expires_in=data.get('expires_in', 365 * 24 * 60 * 60),  # 1 year default
            description=data.get('description', ''),
            rate_limit=data.get('rate_limit', 1000)  # requests per hour
        )
        
        return jsonify({
            'id': api_key_record.id,
            'name': api_key_record.name,
            'api_key': api_key,  # Only show once during creation
            'expires_at': api_key_record.expires_at.isoformat(),
            'permissions': api_key_record.permissions,
            'rate_limit': api_key_record.rate_limit,
            'created_at': api_key_record.created_at.isoformat()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api_keys_bp.route('/', methods=['GET'])
@jwt_required()
def list_api_keys():
    """List user's API keys"""
    try:
        current_user_id = get_jwt_identity()
        
        api_keys = APIKeyService.get_user_keys(
            user_id=current_user_id,
            active_only=request.args.get('active_only', 'true').lower() == 'true'
        )
        
        return jsonify([{
            'id': key.id,
            'name': key.name,
            'description': key.description,
            'created_at': key.created_at.isoformat(),
            'expires_at': key.expires_at.isoformat(),
            'last_used_at': key.last_used_at.isoformat() if key.last_used_at else None,
            'usage_count': key.usage_count,
            'permissions': key.permissions,
            'rate_limit': key.rate_limit,
            'is_active': key.is_active
        } for key in api_keys])
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_keys_bp.route('/<int:key_id>', methods=['GET'])
@jwt_required()
def get_api_key(key_id):
    """Get API key details"""
    try:
        current_user_id = get_jwt_identity()
        
        api_key = APIKeyService.get_user_key(
            user_id=current_user_id,
            key_id=key_id
        )
        
        if not api_key:
            return jsonify({'error': 'API key not found'}), 404
        
        return jsonify({
            'id': api_key.id,
            'name': api_key.name,
            'description': api_key.description,
            'created_at': api_key.created_at.isoformat(),
            'expires_at': api_key.expires_at.isoformat(),
            'last_used_at': api_key.last_used_at.isoformat() if api_key.last_used_at else None,
            'usage_count': api_key.usage_count,
            'permissions': api_key.permissions,
            'rate_limit': api_key.rate_limit,
            'is_active': api_key.is_active,
            'usage_stats': APIKeyService.get_key_usage_stats(api_key.id)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_keys_bp.route('/<int:key_id>', methods=['PUT'])
@jwt_required()
def update_api_key(key_id):
    """Update API key"""
    try:
        data = request.get_json()
        current_user_id = get_jwt_identity()
        
        api_key = APIKeyService.get_user_key(
            user_id=current_user_id,
            key_id=key_id
        )
        
        if not api_key:
            return jsonify({'error': 'API key not found'}), 404
        
        # Update allowed fields
        if 'name' in data:
            api_key.name = data['name']
        
        if 'description' in data:
            api_key.description = data['description']
        
        if 'permissions' in data:
            api_key.permissions = data['permissions']
        
        if 'rate_limit' in data:
            api_key.rate_limit = data['rate_limit']
        
        if 'expires_in' in data:
            api_key.expires_at = datetime.utcnow() + timedelta(seconds=data['expires_in'])
        
        api_key.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'id': api_key.id,
            'name': api_key.name,
            'description': api_key.description,
            'expires_at': api_key.expires_at.isoformat(),
            'permissions': api_key.permissions,
            'rate_limit': api_key.rate_limit,
            'updated_at': api_key.updated_at.isoformat()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api_keys_bp.route('/<int:key_id>', methods=['DELETE'])
@jwt_required()
def revoke_api_key(key_id):
    """Revoke an API key"""
    try:
        current_user_id = get_jwt_identity()
        
        success = APIKeyService.revoke_key(
            user_id=current_user_id,
            key_id=key_id
        )
        
        if not success:
            return jsonify({'error': 'API key not found'}), 404
        
        return jsonify({'message': 'API key revoked successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_keys_bp.route('/<int:key_id>/rotate', methods=['POST'])
@jwt_required()
def rotate_api_key(key_id):
    """Rotate an API key"""
    try:
        current_user_id = get_jwt_identity()
        
        new_api_key = APIKeyService.rotate_key(
            user_id=current_user_id,
            key_id=key_id
        )
        
        if not new_api_key:
            return jsonify({'error': 'API key not found'}), 404
        
        return jsonify({
            'id': new_api_key.id,
            'name': new_api_key.name,
            'api_key': new_api_key.api_key,  # Only show once during rotation
            'expires_at': new_api_key.expires_at.isoformat(),
            'permissions': new_api_key.permissions,
            'rate_limit': new_api_key.rate_limit,
            'rotated_at': new_api_key.updated_at.isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_keys_bp.route('/<int:key_id>/usage', methods=['GET'])
@jwt_required()
def get_api_key_usage(key_id):
    """Get API key usage statistics"""
    try:
        current_user_id = get_jwt_identity()
        
        api_key = APIKeyService.get_user_key(
            user_id=current_user_id,
            key_id=key_id
        )
        
        if not api_key:
            return jsonify({'error': 'API key not found'}), 404
        
        usage_stats = APIKeyService.get_key_usage_stats(
            key_id=key_id,
            days=request.args.get('days', 30, type=int)
        )
        
        return jsonify(usage_stats)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_keys_bp.route('/<int:key_id>/regenerate', methods=['POST'])
@jwt_required()
def regenerate_api_key(key_id):
    """Regenerate API key (same as rotate)"""
    return rotate_api_key(key_id)

# Decorators for API key authentication

def require_api_key(f):
    """Decorator to require API key authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get API key from header
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return jsonify({'error': 'API key required'}), 401
        
        # Validate API key
        key_record = APIKeyService.validate_key(api_key)
        if not key_record:
            return jsonify({'error': 'Invalid API key'}), 401
        
        # Check rate limit
        if not APIKeyService.check_rate_limit(key_record.id):
            return jsonify({'error': 'Rate limit exceeded'}), 429
        
        # Update usage statistics
        APIKeyService.update_key_usage(key_record.id, request.endpoint)
        
        # Add user and key to request context
        request.current_user = key_record.user
        request.current_api_key = key_record
        
        return f(*args, **kwargs)
    
    return decorated_function

def require_api_permission(permission):
    """Decorator to require specific API permission"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check API key permissions
            if hasattr(request, 'current_api_key'):
                if permission not in request.current_api_key.permissions:
                    return jsonify({'error': 'Insufficient permissions'}), 403
            else:
                # Check JWT permissions
                try:
                    from flask_jwt_extended import verify_jwt_in_request, get_jwt
                    verify_jwt_in_request()
                    claims = get_jwt()
                    user_permissions = claims.get('permissions', [])
                    if permission not in user_permissions:
                        return jsonify({'error': 'Insufficient permissions'}), 403
                except Exception:
                    return jsonify({'error': 'Authentication required'}), 401
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def require_api_role(role):
    """Decorator to require specific API role"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check user role
            if hasattr(request, 'current_user'):
                user_role = getattr(request.current_user, 'role', 'user')
                if user_role != role:
                    return jsonify({'error': 'Insufficient role'}), 403
            else:
                return jsonify({'error': 'Authentication required'}), 401
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

# API Key validation middleware

def validate_api_key_middleware():
    """Middleware to validate API keys"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check if API key is provided
            api_key = request.headers.get('X-API-Key')
            if api_key:
                # Validate API key
                key_record = APIKeyService.validate_key(api_key)
                if key_record:
                    # Update usage statistics
                    APIKeyService.update_key_usage(key_record.id, request.endpoint)
                    
                    # Add user and key to request context
                    request.current_user = key_record.user
                    request.current_api_key = key_record
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

# Rate limiting for API keys

def api_rate_limit(limit, per=3600):
    """Rate limiting decorator for API keys"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check if API key is available
            if hasattr(request, 'current_api_key'):
                if not APIKeyService.check_rate_limit(request.current_api_key.id, limit, per):
                    return jsonify({'error': 'Rate limit exceeded'}), 429
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

# Utility functions

def get_current_api_user():
    """Get current authenticated user from API key or JWT"""
    if hasattr(request, 'current_user'):
        return request.current_user
    return None

def get_current_api_key():
    """Get current API key"""
    if hasattr(request, 'current_api_key'):
        return request.current_api_key
    return None

def has_api_permission(permission):
    """Check if current request has API permission"""
    if hasattr(request, 'current_api_key'):
        return permission in request.current_api_key.permissions
    
    # Check JWT permissions
    try:
        from flask_jwt_extended import verify_jwt_in_request, get_jwt
        verify_jwt_in_request()
        claims = get_jwt()
        user_permissions = claims.get('permissions', [])
        return permission in user_permissions
    except Exception:
        return False

def has_api_role(role):
    """Check if current request has API role"""
    if hasattr(request, 'current_user'):
        user_role = getattr(request.current_user, 'role', 'user')
        return user_role == role
    
    return False
