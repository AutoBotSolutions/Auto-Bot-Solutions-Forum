"""
Comprehensive Error Monitoring and Debugging System
Provides multiple layers of error capture and real-time display
"""

import logging
import traceback
import json
from datetime import datetime
from flask import request, g, current_app
import sys
import os

# Create comprehensive error logger
error_logger = logging.getLogger('comprehensive_error_system')
error_logger.setLevel(logging.INFO)

# Create file handler for comprehensive error logs
error_handler = logging.FileHandler('logs/comprehensive_error.log')
error_handler.setLevel(logging.INFO)
error_formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
error_handler.setFormatter(error_formatter)
error_logger.addHandler(error_handler)

# Console handler for immediate error visibility
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(error_formatter)
error_logger.addHandler(console_handler)

# In-memory error storage for real-time display
active_errors = []
MAX_ACTIVE_ERRORS = 100

class ComprehensiveErrorSystem:
    """Comprehensive error monitoring and debugging system"""
    
    @staticmethod
    def log_error_comprehensive(error, context=None, additional_data=None):
        """Log error with comprehensive information"""
        error_info = {
            'timestamp': datetime.utcnow().isoformat(),
            'error_type': type(error).__name__,
            'error_message': str(error),
            'traceback': traceback.format_exc(),
            'context': context or {},
            'additional_data': additional_data or {},
            'request_info': {},
            'system_info': {
                'python_version': sys.version,
                'flask_version': getattr(current_app, '__version__', 'unknown') if current_app else 'unknown'
            }
        }
        
        # Add request information if available
        try:
            if request:
                error_info['request_info'] = {
                    'url': request.url,
                    'method': request.method,
                    'endpoint': request.endpoint,
                    'user_agent': request.headers.get('User-Agent', 'unknown'),
                    'ip_address': request.remote_addr,
                    'form_data': dict(request.form) if request.form else {},
                    'query_params': dict(request.args) if request.args else {},
                    'json_data': request.get_json() if request.is_json else None
                }
        except Exception as req_error:
            error_info['request_info'] = {'error': f'Failed to get request info: {req_error}'}
        
        # Add to active errors
        active_errors.append(error_info)
        if len(active_errors) > MAX_ACTIVE_ERRORS:
            active_errors.pop(0)
        
        # Log to file and console
        error_logger.error(f"ERROR CAPTURED: {error_info['error_type']}: {error_info['error_message']}")
        error_logger.error(f"Full error info: {json.dumps(error_info, indent=2, default=str)}")
        
        # Also log to a separate error file for easy access
        try:
            with open('logs/latest_error.json', 'w') as f:
                json.dump(error_info, f, indent=2, default=str)
        except Exception as log_error:
            error_logger.error(f"Failed to write latest error file: {log_error}")
        
        return error_info
    
    @staticmethod
    def get_active_errors(limit=50):
        """Get recent active errors"""
        return active_errors[-limit:] if active_errors else []
    
    @staticmethod
    def get_error_count():
        """Get total active error count"""
        return len(active_errors)
    
    @staticmethod
    def clear_errors():
        """Clear all stored errors"""
        active_errors.clear()
        error_logger.info("All errors cleared from comprehensive error system")
    
    @staticmethod
    def create_error_summary():
        """Create a summary of recent errors"""
        if not active_errors:
            return {"status": "no_errors", "message": "No errors captured"}
        
        error_types = {}
        endpoints = {}
        recent_errors = active_errors[-20:]  # Last 20 errors
        
        for error in recent_errors:
            # Count by error type
            error_type = error['error_type']
            error_types[error_type] = error_types.get(error_type, 0) + 1
            
            # Count by endpoint
            endpoint = error.get('request_info', {}).get('endpoint', 'unknown')
            endpoints[endpoint] = endpoints.get(endpoint, 0) + 1
        
        return {
            "total_errors": len(active_errors),
            "recent_errors": len(recent_errors),
            "error_types": error_types,
            "endpoints": endpoints,
            "latest_error": active_errors[-1] if active_errors else None
        }

# Global error monitoring function
def monitor_error(error, context=None, additional_data=None):
    """Global function to monitor errors from anywhere"""
    return ComprehensiveErrorSystem.log_error_comprehensive(error, context, additional_data)

# Decorator for monitoring function errors
def comprehensive_error_monitor(func):
    """Decorator to monitor errors in functions"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            context = {
                'function_name': func.__name__,
                'module': func.__module__,
                'args_count': len(args),
                'kwargs_keys': list(kwargs.keys())
            }
            monitor_error(e, context=context, additional_data={'function_args': str(args), 'function_kwargs': str(kwargs)})
            raise
    return wrapper

# Flask middleware for comprehensive error monitoring
def comprehensive_error_middleware(app):
    """Add comprehensive error monitoring to Flask app"""
    
    @app.before_request
    def before_request():
        """Store request start time for monitoring"""
        g.request_start_time = datetime.utcnow()
        g.request_id = id(request)
    
    @app.teardown_request
    def teardown_request(exception):
        """Monitor request teardown for errors"""
        if exception:
            context = {
                'request_id': getattr(g, 'request_id', 'unknown'),
                'request_duration': (datetime.utcnow() - getattr(g, 'request_start_time', datetime.utcnow())).total_seconds() if hasattr(g, 'request_start_time') else None
            }
            monitor_error(exception, context=context)
    
    @app.errorhandler(Exception)
    def handle_exception(error):
        """Handle all exceptions with comprehensive logging"""
        context = {
            'error_handler': 'flask_exception_handler',
            'request_id': getattr(g, 'request_id', 'unknown')
        }
        monitor_error(error, context=context)
        
        # Let Flask handle the exception normally
        raise error
    
    @app.errorhandler(404)
    def handle_404(error):
        """Handle 404 errors with comprehensive logging"""
        context = {
            'error_handler': 'flask_404_handler',
            'request_id': getattr(g, 'request_id', 'unknown')
        }
        monitor_error(error, context=context)
        
        # Let Flask handle the 404 normally
        from flask import render_template
        return render_template('errors/404.html'), 404
    
    return app

# Add admin routes for error monitoring
def create_error_monitoring_routes(app):
    """Create routes for error monitoring and debugging"""
    
    @app.route('/admin/errors/comprehensive')
    def comprehensive_errors():
        """Comprehensive error monitoring dashboard"""
        try:
            return {
                'status': 'success',
                'error_count': ComprehensiveErrorSystem.get_error_count(),
                'active_errors': ComprehensiveErrorSystem.get_active_errors(),
                'error_summary': ComprehensiveErrorSystem.create_error_summary(),
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Error monitoring system failed: {e}',
                'timestamp': datetime.utcnow().isoformat()
            }
    
    @app.route('/admin/errors/latest')
    def latest_error():
        """Get the latest error"""
        try:
            errors = ComprehensiveErrorSystem.get_active_errors(1)
            if errors:
                return {
                    'status': 'success',
                    'latest_error': errors[-1],
                    'timestamp': datetime.utcnow().isoformat()
                }
            else:
                return {
                    'status': 'no_errors',
                    'message': 'No errors captured',
                    'timestamp': datetime.utcnow().isoformat()
                }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Failed to get latest error: {e}',
                'timestamp': datetime.utcnow().isoformat()
            }
    
    @app.route('/admin/errors/clear')
    def clear_errors():
        """Clear all errors"""
        try:
            ComprehensiveErrorSystem.clear_errors()
            return {
                'status': 'success',
                'message': 'All errors cleared',
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Failed to clear errors: {e}',
                'timestamp': datetime.utcnow().isoformat()
            }

# Initialize comprehensive error system
def init_comprehensive_error_system(app):
    """Initialize comprehensive error monitoring system"""
    app = comprehensive_error_middleware(app)
    create_error_monitoring_routes(app)
    error_logger.info("Comprehensive error monitoring system initialized")
    return app
