"""
API Version Decorators

Decorators for handling API versioning in Flask routes.
"""

from functools import wraps
from flask import jsonify, request, g
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime

from .version_manager import version_manager, VersionStatus
from .version_middleware import get_current_version, is_version_deprecated

def api_version(*versions: str, deprecated: bool = False, 
                deprecation_date: Optional[datetime] = None,
                sunset_date: Optional[datetime] = None):
    """Decorator to specify API version(s) for endpoint"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            current = get_current_version()
            
            if not current:
                return jsonify({
                    'error': 'VersionRequired',
                    'message': 'API version is required for this endpoint'
                }), 400
            
            # Check if current version is supported
            if versions and current not in versions:
                return jsonify({
                    'error': 'UnsupportedVersion',
                    'message': f'Endpoint {request.endpoint} does not support API version {current}',
                    'supported_versions': list(versions),
                    'current_version': current
                }), 400
            
            # Handle deprecation
            if deprecated and is_version_deprecated():
                version_obj = version_manager.get_version(current)
                if version_obj:
                    return jsonify({
                        'warning': 'DeprecatedEndpoint',
                        'message': f'Endpoint {request.endpoint} is deprecated in API version {current}',
                        'deprecation_date': version_obj.deprecation_date.isoformat() if version_obj.deprecation_date else None,
                        'sunset_date': version_obj.sunset_date.isoformat() if version_obj.sunset_date else None,
                        'recommended_version': version_manager.default_version
                    }), 200
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def deprecated_endpoint(new_endpoint: str = None, 
                        removal_date: Optional[datetime] = None,
                        migration_guide: str = None):
    """Decorator to mark endpoint as deprecated"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            current = get_current_version()
            
            if not current:
                return f(*args, **kwargs)
            
            version_obj = version_manager.get_version(current)
            if version_obj and version_obj.is_deprecated():
                response_data = {
                    'warning': 'DeprecatedEndpoint',
                    'message': f'Endpoint {request.endpoint} is deprecated',
                    'api_version': current
                }
                
                if new_endpoint:
                    response_data['new_endpoint'] = new_endpoint
                
                if removal_date:
                    response_data['removal_date'] = removal_date.isoformat()
                
                if migration_guide:
                    response_data['migration_guide'] = migration_guide
                
                # Return warning with response
                result = f(*args, **kwargs)
                
                # If result is a Flask Response, add headers
                if hasattr(result, 'headers'):
                    result.headers['X-API-Deprecated'] = 'true'
                    if new_endpoint:
                        result.headers['X-API-New-Endpoint'] = new_endpoint
                    if removal_date:
                        result.headers['X-API-Removal-Date'] = removal_date.isoformat()
                
                return result
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def versioned_response(version_mapping: Dict[str, Dict[str, Any]]):
    """Decorator to provide different responses based on API version"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            current = get_current_version()
            
            if not current:
                return f(*args, **kwargs)
            
            # Get version-specific response modifications
            if current in version_mapping:
                modifications = version_mapping[current]
                
                # Call the original function
                result = f(*args, **kwargs)
                
                # Apply modifications
                if isinstance(result, dict):
                    result.update(modifications)
                elif hasattr(result, 'get_json'):
                    # Flask Response
                    json_data = result.get_json()
                    if json_data:
                        json_data.update(modifications)
                        result.data = jsonify(json_data).data
                
                return result
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def min_version(min_version: str):
    """Decorator to require minimum API version"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            current = get_current_version()
            
            if not current:
                return jsonify({
                    'error': 'VersionRequired',
                    'message': 'API version is required for this endpoint'
                }), 400
            
            if current < min_version:
                return jsonify({
                    'error': 'VersionTooOld',
                    'message': f'Endpoint {request.endpoint} requires API version {min_version} or higher',
                    'current_version': current,
                    'minimum_version': min_version,
                    'recommended_version': version_manager.default_version
                }), 400
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def max_version(max_version: str):
    """Decorator to require maximum API version"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            current = get_current_version()
            
            if not current:
                return jsonify({
                    'error': 'VersionRequired',
                    'message': 'API version is required for this endpoint'
                }), 400
            
            if current > max_version:
                return jsonify({
                    'error': 'VersionTooNew',
                    'message': f'Endpoint {request.endpoint} requires API version {max_version} or lower',
                    'current_version': current,
                    'maximum_version': max_version,
                    'recommended_version': max_version
                }), 400
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def version_incompatible_with(incompatible_versions: List[str]):
    """Decorator to mark versions as incompatible"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            current = get_current_version()
            
            if not current:
                return jsonify({
                    'error': 'VersionRequired',
                    'message': 'API version is required for this endpoint'
                }), 400
            
            if current in incompatible_versions:
                return jsonify({
                    'error': 'IncompatibleVersion',
                    'message': f'API version {current} is not compatible with this endpoint',
                    'current_version': current,
                    'incompatible_versions': incompatible_versions,
                    'recommended_version': version_manager.default_version
                }), 400
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def beta_feature(feature_name: str, available_from: str = None):
    """Decorator for beta features available in specific versions"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            current = get_current_version()
            
            if not current:
                return jsonify({
                    'error': 'VersionRequired',
                    'message': 'API version is required for this endpoint'
                }), 400
            
            # Check if feature is available in current version
            if available_from and current < available_from:
                return jsonify({
                    'error': 'FeatureNotAvailable',
                    'message': f'Feature {feature_name} is not available in API version {current}',
                    'current_version': current,
                    'available_from': available_from,
                    'recommended_version': available_from
                }), 400
            
            # Add beta warning
            result = f(*args, **kwargs)
            
            if hasattr(result, 'headers'):
                result.headers['X-API-Beta-Feature'] = feature_name
                result.headers['X-API-Beta-Version'] = current
            
            return result
        return decorated_function
    return decorator

def experimental_feature(feature_name: str):
    """Decorator for experimental features"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            current = get_current_version()
            
            if not current:
                return jsonify({
                    'error': 'VersionRequired',
                    'message': 'API version is required for this endpoint'
                }), 400
            
            # Add experimental warning
            result = f(*args, **kwargs)
            
            if hasattr(result, 'headers'):
                result.headers['X-API-Experimental-Feature'] = feature_name
                result.headers['X-API-Experimental-Version'] = current
                result.headers['X-API-Experimental-Warning'] = 'This feature is experimental and may change'
            
            return result
        return decorated_function
    return decorator

def versioned_schema(schema_mapping: Dict[str, Dict[str, Any]]):
    """Decorator to apply different schemas based on API version"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            current = get_current_version()
            
            if not current:
                return f(*args, **kwargs)
            
            # Store version-specific schema in context
            if current in schema_mapping:
                g.versioned_schema = schema_mapping[current]
            else:
                g.versioned_schema = {}
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def version_permissions(permission_mapping: Dict[str, List[str]]):
    """Decorator to apply different permissions based on API version"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            current = get_current_version()
            
            if not current:
                return f(*args, **kwargs)
            
            # Store version-specific permissions in context
            if current in permission_mapping:
                g.versioned_permissions = permission_mapping[current]
            else:
                g.versioned_permissions = []
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def version_rate_limit(rate_limit_mapping: Dict[str, str]):
    """Decorator to apply different rate limits based on API version"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            current = get_current_version()
            
            if not current:
                return f(*args, **kwargs)
            
            # Store version-specific rate limit in context
            if current in rate_limit_mapping:
                g.versioned_rate_limit = rate_limit_mapping[current]
            else:
                g.versioned_rate_limit = None
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator
