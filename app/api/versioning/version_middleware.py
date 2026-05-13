"""
API Version Middleware

Flask middleware for handling API versioning in requests.
"""

from flask import request, jsonify, g
from werkzeug.local import LocalProxy
from typing import Callable, Optional
import logging

from .version_manager import version_manager, VersionStatus

logger = logging.getLogger(__name__)

# Current API version for this request
current_version = LocalProxy(lambda: getattr(g, 'api_version', None))

class APIVersionMiddleware:
    """Middleware for handling API versioning"""
    
    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize middleware with Flask app"""
        app.before_request(self._before_request)
        app.after_request(self._after_request)
        
        # Add version headers to response
        @app.after_request
        def add_version_headers(response):
            if hasattr(g, 'api_version'):
                response.headers['API-Version'] = g.api_version
                
                # Add deprecation warnings if needed
                version_obj = version_manager.get_version(g.api_version)
                if version_obj and version_obj.is_deprecated():
                    response.headers['API-Deprecated'] = 'true'
                    response.headers['API-Sunset-Date'] = version_obj.sunset_date.isoformat() if version_obj.sunset_date else ''
                    response.headers['API-Deprecation-Date'] = version_obj.deprecation_date.isoformat() if version_obj.deprecation_date else ''
            
            return response
    
    def _before_request(self):
        """Handle version detection before request"""
        # Skip versioning for non-API routes
        if not request.path.startswith('/api/'):
            return
        
        # Extract version from request
        version = version_manager.get_version_from_request(
            request_headers=dict(request.headers),
            request_path=request.path
        )
        
        # Validate version
        validation = version_manager.validate_version_request(version, request.path)
        
        if not validation['valid']:
            return jsonify({
                'error': validation['error'],
                'message': 'Invalid or unsupported API version',
                'available_versions': validation.get('available_versions', []),
                'recommended_version': validation.get('recommended_version', version_manager.default_version)
            }), 400
        
        # Set version in context
        g.api_version = version
        g.version_validation = validation
        
        # Log deprecation warnings
        if validation.get('warning'):
            logger.warning(f"Deprecated API version {version} used: {validation['warning']}")
    
    def _after_request(self, response):
        """Handle version-specific response processing"""
        # Add version compatibility headers
        if hasattr(g, 'api_version'):
            compatible_versions = version_manager.get_compatible_versions(g.api_version)
            if compatible_versions:
                response.headers['API-Compatible-Versions'] = ','.join(compatible_versions)
        
        return response

class VersionErrorHandler:
    """Handles version-related errors"""
    
    @staticmethod
    def handle_version_not_found(version: str):
        """Handle version not found error"""
        available_versions = list(version_manager.versions.keys())
        
        return jsonify({
            'error': 'VersionNotFound',
            'message': f'API version {version} not found',
            'available_versions': available_versions,
            'default_version': version_manager.default_version,
            'documentation': f'/api/docs/openapi.json'
        }), 404
    
    @staticmethod
    def handle_version_deprecated(version: str, validation: dict):
        """Handle deprecated version warning"""
        return jsonify({
            'warning': 'DeprecatedVersion',
            'message': f'API version {version} is deprecated',
            'deprecation_date': validation.get('deprecation_date'),
            'sunset_date': validation.get('sunset_date'),
            'days_until_sunset': validation.get('days_until_sunset'),
            'recommended_version': validation.get('recommended_version'),
            'migration_guide': f'/api/docs/migration/{version}'
        }), 200
    
    @staticmethod
    def handle_endpoint_not_found(version: str, path: str):
        """Handle endpoint not found in version"""
        version_obj = version_manager.get_version(version)
        
        return jsonify({
            'error': 'EndpointNotFound',
            'message': f'Endpoint {path} not found in API version {version}',
            'available_endpoints': list(version_obj.endpoints.keys()) if version_obj else [],
            'version_info': version_manager.get_version_info(version) if version_obj else None,
            'documentation': f'/api/docs/openapi.json'
        }), 404

def get_current_version() -> Optional[str]:
    """Get current API version for request"""
    return getattr(g, 'api_version', None)

def is_version_deprecated() -> bool:
    """Check if current version is deprecated"""
    if not hasattr(g, 'api_version'):
        return False
    
    version_obj = version_manager.get_version(g.api_version)
    return version_obj.is_deprecated() if version_obj else False

def get_version_warning() -> Optional[dict]:
    """Get version warning if any"""
    if not hasattr(g, 'version_validation'):
        return None
    
    validation = g.version_validation
    if validation.get('warning'):
        return validation
    
    return None

def require_version(min_version: str = None, max_version: str = None, 
                   exact_version: str = None):
    """Decorator to require specific API version"""
    def decorator(f):
        def decorated_function(*args, **kwargs):
            current = get_current_version()
            
            if not current:
                return jsonify({
                    'error': 'VersionRequired',
                    'message': 'API version is required for this endpoint'
                }), 400
            
            # Check exact version
            if exact_version and current != exact_version:
                return jsonify({
                    'error': 'VersionMismatch',
                    'message': f'This endpoint requires API version {exact_version}',
                    'current_version': current,
                    'required_version': exact_version
                }), 400
            
            # Check minimum version
            if min_version and current < min_version:
                return jsonify({
                    'error': 'VersionTooOld',
                    'message': f'This endpoint requires API version {min_version} or higher',
                    'current_version': current,
                    'minimum_version': min_version
                }), 400
            
            # Check maximum version
            if max_version and current > max_version:
                return jsonify({
                    'error': 'VersionTooNew',
                    'message': f'This endpoint requires API version {max_version} or lower',
                    'current_version': current,
                    'maximum_version': max_version
                }), 400
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def version_compatible_with(target_version: str):
    """Decorator to require version compatibility"""
    def decorator(f):
        def decorated_function(*args, **kwargs):
            current = get_current_version()
            
            if not current:
                return jsonify({
                    'error': 'VersionRequired',
                    'message': 'API version is required for this endpoint'
                }), 400
            
            if not version_manager.is_version_compatible(current, target_version):
                return jsonify({
                    'error': 'VersionIncompatible',
                    'message': f'API version {current} is not compatible with required version {target_version}',
                    'current_version': current,
                    'required_version': target_version,
                    'compatible_versions': version_manager.get_compatible_versions(target_version)
                }), 400
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator
